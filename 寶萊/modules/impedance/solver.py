# 5. modules/impedance/solver.py
# 正向 / 反向阻抗求解器
from scipy.optimize import brentq
from .formulas import microstrip_z0, stripline_z0

FORMULA_MAP = {
    "Microstrip": microstrip_z0,
    "Stripline": stripline_z0,
}


def forward_calc(tline_type, w, h, t, er, freq_ghz=0.0):
    """
    正向计算: 给定几何参数 -> Z0, epsilon_eff
    """
    func = FORMULA_MAP[tline_type]
    return func(w, h, t, er, freq_ghz)


def _z0_error(w_guess, tline_type, target_z0, h, t, er, freq_ghz):
    """用于 brentq 的误差函数"""
    z0, _ = forward_calc(tline_type, w_guess, h, t, er, freq_ghz)
    return z0 - target_z0


def inverse_calc(tline_type, target_z0, h, t, er, freq_ghz=0.0):
    """
    反向计算: 给定目标 Z0 -> 反推线宽 w (mm)
    失败返回 None
    """
    w_min = 1e-3      # 1 μm
    w_max = 20.0      # 20 mm

    try:
        # 先检查边界，必要时扩展
        z0_at_min, _ = forward_calc(tline_type, w_min, h, t, er, freq_ghz)
        z0_at_max, _ = forward_calc(tline_type, w_max, h, t, er, freq_ghz)

        # 确保目标在搜索范围内
        if target_z0 > z0_at_min:
            # 目标阻抗高于最窄线能达到的阻抗，需要更窄
            w_min = 1e-4
            z0_at_min, _ = forward_calc(tline_type, w_min, h, t, er, freq_ghz)
        if target_z0 < z0_at_max:
            # 目标阻抗低于最宽线能达到的阻抗，需要更宽
            w_max = 100.0
            z0_at_max, _ = forward_calc(tline_type, w_max, h, t, er, freq_ghz)

        # 最终检查
        z0_low, _ = forward_calc(tline_type, w_min, h, t, er, freq_ghz)
        z0_high, _ = forward_calc(tline_type, w_max, h, t, er, freq_ghz)

        if (z0_low - target_z0) * (z0_high - target_z0) > 0:
            # 目标不在范围内
            return None

        w_opt = brentq(
            _z0_error,
            w_min,
            w_max,
            args=(tline_type, target_z0, h, t, er, freq_ghz),
            xtol=1e-7,
            maxiter=100
        )
        return float(w_opt)

    except Exception:
        return None
