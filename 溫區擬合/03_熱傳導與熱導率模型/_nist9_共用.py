"""共用：熱負載/pages 目錄使用 heatload-coff-nist (NIST 9 係數) 引擎。
保留原檔策略下新增的共用層 (D5=A, D4=A)。

優先載入新平台核心 `src/量傳線設計/核心/熱負載NIST9.py`（以檔案路徑載入，避免套件 __init__ 副作用）；
失敗則直接使用技能腳本並提供最小相容封裝。
"""

from __future__ import annotations
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

SKILL_SCRIPTS = Path("/home/sam/.opencode/skills/heatload-coff-nist/scripts")
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

import coeff_data  # noqa: E402
import thermal_load  # noqa: E402

MIL2_TO_M2 = coeff_data.MIL2_TO_M2
DEFAULT_STAGES = list(thermal_load.DEFAULT_STAGES)


def _load_core():
    root = Path(__file__).resolve().parents[2]  # .../量傳線
    core_path = root / "src" / "量傳線設計" / "核心" / "熱負載NIST9.py"
    if not core_path.exists():
        return None
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("熱負載NIST9_core", core_path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


_core = _load_core()
if _core is not None:
    list_materials = _core.list_materials
    get_material = _core.get_material
    resolve_material = _core.resolve_material
    k_of_T = _core.k_of_T
    integrate_kappa = _core.integrate_kappa
    calculate_thermal_load = _core.calculate_thermal_load
    k_curve = _core.k_curve
    integral_curve = _core.integral_curve
    compare_materials = _core.compare_materials
    sweep_parameter = _core.sweep_parameter
    sweep_materials_heatload = _core.sweep_materials_heatload
else:

    def list_materials(kind: Optional[str] = None) -> List[Dict[str, Any]]:
        out = []
        for name in coeff_data.list_materials():
            rec = dict(coeff_data.get_material(name))
            rec["name"] = name
            if kind and rec.get("category") != kind:
                continue
            out.append(rec)
        return out

    def get_material(name: str) -> Dict[str, Any]:
        key = coeff_data.resolve(name)
        rec = dict(coeff_data.get_material(key))
        rec["name"] = key
        return rec

    def resolve_material(material=None, coeffs=None, equation_type=None):
        if coeffs is not None:
            cfs = list(coeffs)
            eq = equation_type or "log_polynomial"
            return (
                material or "custom",
                cfs,
                eq,
                None,
                None,
                {"name": material or "custom", "coeffs": cfs, "equation_type": eq},
            )
        key = coeff_data.resolve(material)
        rec = coeff_data.get_material(key)
        if rec.get("coeffs") is None:
            raise ValueError(f"材料 {key!r} 無固定 9 係數: {rec.get('source', '')}")
        eq = equation_type or rec.get("equation_type") or "log_polynomial"
        meta = {"name": key}
        meta.update(rec)
        return (key, list(rec["coeffs"]), eq, rec.get("t_low"), rec.get("t_high"), meta)

    def k_of_T(
        T,
        coeffs,
        equation_type="log_polynomial",
        t_low=None,
        t_high=None,
        extrapolate=False,
    ):
        if t_low is None and t_high is None and not extrapolate:
            return thermal_load.k_of_T(T, list(coeffs), equation_type=equation_type)
        is_seq = hasattr(T, "__len__") and not isinstance(T, (str, bytes))
        vals = list(T) if is_seq else [float(T)]
        out = []
        for t in vals:
            t = float(t)
            if t_low is not None and t < t_low:
                if not extrapolate:
                    out.append(0.0)
                    continue
                k_min = float(
                    thermal_load.k_of_T(
                        t_low, list(coeffs), equation_type=equation_type
                    )
                )
                alpha = math.log10(max(k_min, 1e-300)) / math.log10(float(t_low))
                out.append(t**alpha)
                continue
            if t_high is not None and t > t_high:
                out.append(0.0)
                continue
            out.append(
                float(thermal_load.k_of_T(t, list(coeffs), equation_type=equation_type))
            )
        return out if is_seq else out[0]

    def integrate_kappa(
        T_cold,
        T_hot,
        coeffs,
        equation_type="log_polynomial",
        t_low=None,
        t_high=None,
        extrapolate=False,
        n_points=2000,
    ):
        return float(
            thermal_load.integrate_kappa(
                float(T_cold),
                float(T_hot),
                list(coeffs),
                equation_type,
                t_low,
                t_high,
                extrapolate=extrapolate,
                n_points=n_points,
            )
        )

    def calculate_thermal_load(
        material=None,
        coeffs=None,
        stages=None,
        geometry=None,
        attenuation=None,
        pin=0.0,
        equation_type=None,
        extrapolate_low_t=False,
        n_points=2000,
    ):
        return thermal_load.calculate_thermal_load(
            material=material,
            coeffs=coeffs,
            stages=stages,
            geometry=geometry,
            attenuation=attenuation,
            pin=pin,
            equation_type=equation_type,
            extrapolate_low_t=extrapolate_low_t,
            n_points=n_points,
        )

    def _logspace(a, b, n):
        if n <= 1:
            return [float(a)]
        a = float(a)
        b = float(b)
        if a <= 0 or b <= 0:
            step = (b - a) / (n - 1)
            return [a + i * step for i in range(n)]
        la, lb = math.log10(a), math.log10(b)
        return [10 ** (la + (lb - la) * i / (n - 1)) for i in range(n)]

    def k_curve(
        material=None,
        coeffs=None,
        equation_type=None,
        t_min=None,
        t_max=None,
        n=300,
        extrapolate=False,
    ):
        mname, cfs, eq, tl, th, meta = resolve_material(
            material=material, coeffs=coeffs, equation_type=equation_type
        )
        lo = t_min if t_min is not None else (tl if tl else 1.0)
        hi = t_max if t_max is not None else (th if th else 300.0)
        if lo <= 0:
            lo = max(1e-3, hi / 1000.0)
        T = _logspace(lo, hi, n)
        kvals = [float(k_of_T(t, cfs, eq, tl, th, extrapolate=extrapolate)) for t in T]
        return {
            "material": mname,
            "equation_type": eq,
            "t_low": tl,
            "t_high": th,
            "T": T,
            "k": kvals,
            "meta": meta,
        }

    def integral_curve(
        material=None,
        coeffs=None,
        equation_type=None,
        t_cold=4.0,
        t_hot=300.0,
        n=200,
        extrapolate=False,
    ):
        mname, cfs, eq, tl, th, meta = resolve_material(
            material=material, coeffs=coeffs, equation_type=equation_type
        )
        T = _logspace(max(t_cold, 1e-6), t_hot, n)
        I = [
            0.0
            if t <= t_cold
            else float(
                integrate_kappa(t_cold, t, cfs, eq, tl, th, extrapolate=extrapolate)
            )
            for t in T
        ]
        return {
            "material": mname,
            "equation_type": eq,
            "T": T,
            "integral": I,
            "t_cold": t_cold,
            "t_hot": t_hot,
            "meta": meta,
        }

    def compare_materials(materials, t_min=None, t_max=None, n=300, extrapolate=False):
        out = []
        for m in materials:
            try:
                out.append(
                    k_curve(
                        material=m,
                        t_min=t_min,
                        t_max=t_max,
                        n=n,
                        extrapolate=extrapolate,
                    )
                )
            except Exception as e:
                out.append({"material": m, "error": str(e)})
        return out

    def sweep_parameter(base, param, values):
        results = []
        for v in values:
            kw = json.loads(json.dumps(base))
            geo = dict(kw.get("geometry") or {})
            if param in ("length", "width", "thickness", "area_units"):
                geo[param] = v
                kw["geometry"] = geo
            elif param in (
                "pin",
                "attenuation",
                "material",
                "coeffs",
                "stages",
                "equation_type",
                "extrapolate_low_t",
                "n_points",
            ):
                kw[param] = v
            else:
                geo[param] = v
                kw["geometry"] = geo
            try:
                res = calculate_thermal_load(**kw)
                res["_sweep_param"] = param
                res["_sweep_value"] = v
                results.append(res)
            except Exception as e:
                results.append(
                    {"_sweep_param": param, "_sweep_value": v, "error": str(e)}
                )
        return results

    def sweep_materials_heatload(materials, **calc_kwargs):
        out = []
        for m in materials:
            try:
                res = calculate_thermal_load(material=m, **calc_kwargs)
                res["_sweep_material"] = m
                out.append(res)
            except Exception as e:
                out.append({"_sweep_material": m, "error": str(e)})
        return out
