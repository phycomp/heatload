# 修复 sweep.py：加入 t_um 的单位转换
"""
参数扫描引擎
"""
import numpy as np
import pandas as pd
from .solver import forward_calc

_PARAM_MAP = {
    "w_mm": "w",
    "h_mm": "h",
    "t_um": "t",
    "er": "er"
}


def param_sweep(tline_type, sweep_param, sweep_vals, fixed_params):
    """
    单参数扫描
    sweep_param: 'w_mm', 'h_mm', 't_um', 'er'
    sweep_vals:  扫描值数组
    fixed_params: dict {w, h, t, er, freq_ghz}
    返回 DataFrame
    """
    key = _PARAM_MAP.get(sweep_param, sweep_param)
    results = []
    for val in sweep_vals:
        p = dict(fixed_params)
        # 单位转换: t_um -> mm
        if key == "t":
            val = val / 1000.0
        p[key] = val
        z0, e_eff = forward_calc(
            tline_type, p["w"], p["h"], p["t"], p["er"], p.get("freq_ghz", 0.0)
        )
        results.append({
            sweep_param: val * (1000.0 if key == "t" else 1.0),  # 显示时转回 μm
            "Z0": z0,
            "e_eff": e_eff
        })
    return pd.DataFrame(results)


def freq_sweep(tline_type, w, h, t, er, freqs_ghz):
    """
    频率扫描
    freqs_ghz: 频率数组 (GHz)
    返回 DataFrame
    """
    results = []
    for f in freqs_ghz:
        z0, e_eff = forward_calc(tline_type, w, h, t, er, f)
        results.append({
            "freq_ghz": f,
            "Z0": z0,
            "e_eff": e_eff
        })
    return pd.DataFrame(results)
