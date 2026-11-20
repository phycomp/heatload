"""其它功能：串擾、電報員方程式、矩形波導、低通濾波器（簡化）。"""
from numpy import array, cos, exp, linspace, pi, sin, sqrt
from numpy import log as nplog

# --- 低通濾波器（微帶） ---
def calculate_microstrip_width(Z0, er, h, t=0):
    A = (Z0 / 60) * sqrt((er + 1) / 2) + ((er - 1) / (er + 1)) * (0.23 + 0.11 / er)
    if (Z0 > (60 - 36 * ((er - 1) / (er + 1)))):
        W_h = (8 * exp(A)) / (exp(2 * A) - 2)
    else:
        B = (377 * pi) / (2 * Z0 * sqrt(er))
        W_h = (2 / pi) * (B - 1 - nplog(2 * B - 1) +
               ((er - 1) / (2 * er)) * (nplog(B - 1) + 0.39 - 0.61 / er))
    return W_h * h

def calculate_effective_dielectric_constant(er, W, h):
    W_h = W / h
    F = 1 / sqrt(1 + 12 * h / W)
    e_eff = (er + 1) / 2 + ((er - 1) / 2) * F
    return e_eff

def calculate_guided_wavelength(f, e_eff):
    c = 3e8
    lambda0 = c / (f * 1e9) * 1000
    lambda_g = lambda0 / sqrt(e_eff)
    return lambda_g

# --- 電報員方程式（無損傳輸線電壓/電流） ---
def 電報員電壓(長度, 頻率, 相速=2e8, 衰減=0.0):
    """回傳沿線電壓幅度（簡化）。"""
    beta = 2 * pi * 頻率 / 相速
    z = linspace(0, 長度, 200)
    V = exp(-衰減 * z) * cos(beta * z)
    return z, V

# --- 矩形波導截止頻率 ---
def 波導截止頻率(a_m, b_m, m=1, n=0):
    c = 3e8
    fc = (c / 2) * sqrt((m / a_m) ** 2 + (n / b_m) ** 2)
    return fc

# --- 串擾（簡化 NEXT） ---
def 簡單串擾(頻率, 長度, 耦合係數=0.01):
    from numpy import log10
    omega = 2 * pi * 頻率 * 1e9
    mag = omega * 長度 * 耦合係數
    return 20 * log10(mag + 1e-12)
