# 修复 Wheeler Stripline 公式: k 和 k' 定义反了
# 正确: k = tanh(πw/2b), k' = sech(πw/2b)
# 同时修正厚度修正方向

"""
PCB 传输线阻抗经典公式库
Phase 1: Microstrip (Hammerstad-Jensen) + Stripline (Wheeler 精确椭圆积分公式)
"""
import numpy as np
from numpy import log as ln
from numpy import sqrt, pi
from scipy.special import ellipk


def microstrip_z0(w, h, t, er, freq_ghz=0.0):
    """
    Hammerstad-Jensen 公式计算 Microstrip 特性阻抗
    参数:
        w, h, t: 单位 mm
        er: 相对介电常数
        freq_ghz: 频率 (GHz), 0 表示静态
    返回:
        (Z0_ohm, epsilon_eff)
    """
    w = float(w)
    h = float(h)
    t = float(t)
    er = float(er)

    # --- 厚度修正 (Wheeler) ---
    if t > 0 and w > 0:
        if w / h <= 1.0 / (2 * pi):
            w_eff = w + (t / pi) * (1.0 + ln(4.0 * pi * w / t))
        else:
            w_eff = w + (t / pi) * (1.0 + ln(2.0 * h / t))
    else:
        w_eff = w

    w_eff = max(w_eff, 1e-9)

    # --- 静态有效介电常数 ---
    if w_eff / h <= 1.0:
        F = (1.0 + 12.0 * h / w_eff) ** (-0.5)
        e_eff = (er + 1.0) / 2.0 + (er - 1.0) / 2.0 * (
            F + 0.04 * (1.0 - w_eff / h) ** 2
        )
    else:
        F = (1.0 + 12.0 * h / w_eff) ** (-0.5)
        e_eff = (er + 1.0) / 2.0 + (er - 1.0) / 2.0 * F

    # --- 静态特性阻抗 ---
    if w_eff / h <= 1.0:
        z0 = (60.0 / sqrt(e_eff)) * ln(
            8.0 * h / w_eff + w_eff / (4.0 * h)
        )
    else:
        z0 = (120.0 * pi / sqrt(e_eff)) / (
            w_eff / h + 1.393 + 0.667 * ln(w_eff / h + 1.444)
        )

    # --- 频率色散修正 (Hammerstad-Jensen dispersion) ---
    if freq_ghz > 0.0:
        mu0 = 4.0 * pi * 1e-7          # H/m
        h_m = h * 1e-3                 # 转为 m
        fp = z0 / (2.0 * mu0 * h_m)    # Hz
        f_hz = freq_ghz * 1e9
        G = 0.6 + 0.009 * z0
        ratio = f_hz / max(fp, 1e-6)
        e_eff_f = er - (er - e_eff) / (1.0 + G * ratio ** 2)
        e_eff_f = max(e_eff_f, 1.0)
        z0_f = z0 * sqrt(e_eff / e_eff_f)
        return z0_f, e_eff_f

    return z0, e_eff


def stripline_z0(w, h, t, er, freq_ghz=0.0):
    """
    Wheeler 精确公式计算对称 Stripline 特性阻抗 (椭圆积分)
    参数:
        w: 线宽 (mm)
        h: 上下接地平面总间距 b (mm)
        t: 铜厚 (mm)
        er: 相对介电常数
        freq_ghz: 频率 (GHz), Stripline TEM 模式下频率依赖性极弱，Phase 1 忽略
    返回:
        (Z0_ohm, epsilon_eff)   # epsilon_eff 理论上等于 er
    引用:
        H. A. Wheeler, "Transmission-Line Properties of Parallel Strips Separated
        by a Dielectric Sheet", IEEE Trans. Microwave Theory Tech., 1965.
        B. C. Wadell, "Transmission Line Design Handbook", Artech House, 1991.
    """
    w = float(w)
    h = float(h)
    t = float(t)
    er = float(er)

    # --- 厚度修正 (Wheeler: 增加有效宽度，降低阻抗) ---
    if t > 0 and w > 0:
        dw = (t / pi) * ln(2.0)
        we = w + dw
    else:
        we = w

    we = max(we, 1e-9)

    # --- Wheeler 精确公式 (椭圆积分) ---
    # k = tanh(π * we / (2 * b))
    # k' = sech(π * we / (2 * b)) = 1 / cosh(π * we / (2b))
    # Z0 = (30π / √εr) * K(k') / K(k)
    # 其中 K 是第一类完全椭圆积分
    
    arg = pi * we / (2.0 * h)
    k = np.tanh(arg)
    k_prime = 1.0 / np.cosh(arg)   # sech
    
    # 避免 k=1 时 ellipk 发散
    k = min(k, 0.9999999999)
    
    K_k = ellipk(k**2)
    K_kp = ellipk(k_prime**2)
    
    z0 = (30.0 * pi / sqrt(er)) * (K_kp / K_k)

    # Stripline 为 TEM 模式，有效介电常数等于材料介电常数
    return z0, er

#with open("/mnt/agents/output/pcb_calc_app/modules/impedance/formulas.py", "w", encoding="utf-8") as f:
#    f.write(formulas_final)
#
#print("✅ formulas.py 最终修复: k=tanh, k'=sech, 厚度修正方向修正")
