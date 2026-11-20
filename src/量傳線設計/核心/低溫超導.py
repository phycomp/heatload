"""低溫超導（NbTi）相關計算。"""
from numpy import abs as np_abs, exp, linspace, log10, pi, sqrt
from matplotlib.figure import Figure
from matplotlib.pyplot import subplots

def 模擬NbTi串擾(w_um=50, d_nm=100, s_um=100, length_m=0.2,
                   lambda_L_nm=200, er=3.4):
    """回傳串擾分析結果 dict。"""
    f = linspace(0.1, 20, 200)
    omega = 2 * pi * f * 1e9
    mu0 = 4 * pi * 1e-7
    e0 = 8.854e-12
    L_geo = mu0 * 0.5
    L_k = (mu0 * (lambda_L_nm*1e-9)**2) / ((w_um*1e-6) * (d_nm*1e-9))
    L_total = L_geo + L_k
    C = (e0 * er * (w_um*1e-6)) / (10e-6)
    coupling_factor = exp(-s_um / 50)
    L_m = L_geo * 0.1 * coupling_factor
    C_m = C * 0.1 * coupling_factor
    Z0 = sqrt(L_total / C)
    v = 1 / sqrt(L_total * C)
    next_mag = (omega * length_m / (2 * Z0)) * (L_m + C_m * Z0**2)
    next_db = 20 * log10(next_mag + 1e-12)
    fext_coef = (1 / (2 * v)) * (C_m / C - L_m / L_total)
    fext_mag = omega * length_m * fext_coef
    fext_db = 20 * log10(np_abs(fext_mag) + 1e-12)
    return {
        "f": f, "next_db": next_db, "fext_db": fext_db,
        "L_k": L_k, "L_geo": L_geo, "Z0": Z0,
    }

def 繪製串擾圖(結果):
    fig, ax = subplots(figsize=(10, 5))
    ax.plot(結果["f"], 結果["next_db"], label='NEXT (Near-End)', color='#FF4B4B', linewidth=2)
    ax.plot(結果["f"], 結果["fext_db"], label='FEXT (Far-End)', color='#1C83E1', linestyle='--', linewidth=2)
    ax.set_title("Crosstalk Analysis for NbTi @ 20mK", fontsize=14)
    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("Crosstalk Magnitude (dB)")
    ax.set_ylim([-100, -10])
    ax.grid(True, alpha=0.3)
    ax.legend()
    return fig

def BlochGruneisen電阻率(T, rho0, theta_D, n=5):
    """簡化 Bloch-Grüneisen 電阻率模型。"""
    from numpy import power
    if T <= 0:
        return rho0
    x = theta_D / T
    # 近似：rho = rho0 * (T/theta_D)^n * integral... 這裡用簡化 power law
    return rho0 * (T / theta_D) ** n if T < theta_D else rho0 * (T / theta_D)
