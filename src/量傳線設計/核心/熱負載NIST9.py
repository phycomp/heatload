"""NIST 9-係數 (c0..c8) 熱負載計算整合模組。

依賴 heatload-coff-nist 技能腳本作為單一真相來源 (D4=A):
  /home/sam/.opencode/skills/heatload-coff-nist/scripts/{coeff_data,thermal_load}.py

提供：
- 材料/係數查詢 (54 材料，含來源與有效範圍)
- κ(T) 評估、溫區積分、多溫區穩態熱負載 (Q_solid + Q_rf)
- κ(T)/積分曲線資料、材料比較、參數掃描/模擬
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

__all__ = [
    "SKILL_SCRIPTS",
    "MIL2_TO_M2",
    "DEFAULT_STAGES",
    "list_materials",
    "get_material",
    "resolve_material",
    "k_of_T",
    "integrate_kappa",
    "calculate_thermal_load",
    "k_curve",
    "integral_curve",
    "compare_materials",
    "sweep_parameter",
    "sweep_materials_heatload",
]


def list_materials(kind: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出材料。kind: 'k(T)' | 'rho(T)' | None(全部)。回傳 [{'name',...meta}]."""
    names = coeff_data.list_materials()
    out = []
    for name in names:
        rec = coeff_data.get_material(name)
        item = {"name": name}
        item.update(rec)
        if kind and rec.get("category") != kind:
            continue
        out.append(item)
    return out


def get_material(name: str) -> Dict[str, Any]:
    key = coeff_data.resolve(name)
    rec = dict(coeff_data.get_material(key))
    rec["name"] = key
    return rec


def resolve_material(
    material: Optional[str] = None,
    coeffs: Optional[Sequence[float]] = None,
    equation_type: Optional[str] = None,
):
    """回傳 (name, coeffs, equation_type, t_low, t_high, meta)。"""
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
    if material is None:
        raise ValueError("需指定 material 或 coeffs")
    key = coeff_data.resolve(material)
    rec = coeff_data.get_material(key)
    if rec.get("coeffs") is None:
        raise ValueError(f"材料 {key!r} 無固定 9 係數: {rec.get('source', '')}")
    eq = equation_type or rec.get("equation_type") or "log_polynomial"
    meta = {"name": key}
    meta.update(rec)
    return (key, list(rec["coeffs"]), eq, rec.get("t_low"), rec.get("t_high"), meta)


def k_of_T(
    T: Union[float, Sequence[float]],
    coeffs: Sequence[float],
    equation_type: str = "log_polynomial",
    t_low: Optional[float] = None,
    t_high: Optional[float] = None,
    extrapolate: bool = False,
):
    """κ(T) 評估。若給 t_low/t_high 則套用範圍遮罩/外推(對齊 thermal_load 行為)。"""
    if t_low is None and t_high is None and not extrapolate:
        return thermal_load.k_of_T(T, list(coeffs), equation_type=equation_type)
    # apply mask similar to _kappa_effective
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
                thermal_load.k_of_T(t_low, list(coeffs), equation_type=equation_type)
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
    T_cold: float,
    T_hot: float,
    coeffs: Sequence[float],
    equation_type: str = "log_polynomial",
    t_low: Optional[float] = None,
    t_high: Optional[float] = None,
    extrapolate: bool = False,
    n_points: int = 2000,
) -> float:
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
    material: Optional[str] = None,
    coeffs: Optional[Sequence[float]] = None,
    stages: Optional[Sequence] = None,
    geometry: Optional[Dict[str, Any]] = None,
    attenuation: Union[float, Sequence[float], None] = None,
    pin: float = 0.0,
    equation_type: Optional[str] = None,
    extrapolate_low_t: bool = False,
    n_points: int = 2000,
) -> Dict[str, Any]:
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


def _logspace(a: float, b: float, n: int) -> List[float]:
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
    material: Optional[str] = None,
    coeffs: Optional[Sequence[float]] = None,
    equation_type: Optional[str] = None,
    t_min: Optional[float] = None,
    t_max: Optional[float] = None,
    n: int = 300,
    extrapolate: bool = False,
) -> Dict[str, Any]:
    """回傳 κ(T) 曲線資料（log-spaced T）。"""
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
    material: Optional[str] = None,
    coeffs: Optional[Sequence[float]] = None,
    equation_type: Optional[str] = None,
    t_cold: float = 4.0,
    t_hot: float = 300.0,
    n: int = 200,
    extrapolate: bool = False,
) -> Dict[str, Any]:
    """回傳 ∫_{T_cold}^{T} κ(T)dT 隨 T 的累積曲線。"""
    mname, cfs, eq, tl, th, meta = resolve_material(
        material=material, coeffs=coeffs, equation_type=equation_type
    )
    T = _logspace(max(t_cold, 1e-6), t_hot, n)
    I = [
        0.0
        if t <= t_cold
        else float(integrate_kappa(t_cold, t, cfs, eq, tl, th, extrapolate=extrapolate))
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


def compare_materials(
    materials: Sequence[str],
    t_min: Optional[float] = None,
    t_max: Optional[float] = None,
    n: int = 300,
    extrapolate: bool = False,
) -> List[Dict[str, Any]]:
    out = []
    for m in materials:
        try:
            out.append(
                k_curve(
                    material=m, t_min=t_min, t_max=t_max, n=n, extrapolate=extrapolate
                )
            )
        except Exception as e:
            out.append({"material": m, "error": str(e)})
    return out


def sweep_parameter(
    base: Dict[str, Any], param: str, values: Sequence[Any]
) -> List[Dict[str, Any]]:
    """對 calculate_thermal_load 的單一參數做掃描。支援 param: length,width,thickness,pin,attenuation,material 等。"""
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
            results.append({"_sweep_param": param, "_sweep_value": v, "error": str(e)})
    return results


def sweep_materials_heatload(
    materials: Sequence[str], **calc_kwargs
) -> List[Dict[str, Any]]:
    """固定幾何/溫區/衰減，掃描材料比較熱負載。"""
    out = []
    for m in materials:
        try:
            res = calculate_thermal_load(material=m, **calc_kwargs)
            res["_sweep_material"] = m
            out.append(res)
        except Exception as e:
            out.append({"_sweep_material": m, "error": str(e)})
    return out
