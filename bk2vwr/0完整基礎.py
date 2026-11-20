from streamlit import caption, columns, error, subheader, number_input, pyplot, radio, sidebar, slider, stop
from matplotlib.pyplot import subplots
from numpy import abs, e, exp, fft, linspace, log, log10, ones_like, pi, sin, sqrt
from scipy.fft import ifft, fftfreq

# -------------------- 材料資料庫 --------------------
MAT_DB = {
    "Rogers 4350B": {"er": 3.48, "tanD": 0.004, "sigma": 5.8e7},
    "FR-4":         {"er": 4.20, "tanD": 0.020, "sigma": 5.8e7},
    "BCB":          {"er": 2.40, "tanD": 0.007, "sigma": 5.8e7},
    "Megtron6":     {"er": 3.40, "tanD": 0.002, "sigma": 5.8e7},
    "PTFE":         {"er": 2.10, "tanD": 0.0002,"sigma": 5.8e7},
}
c0 = 299792458
mu0 = 4e-7*pi

# -------------------- SE vs Diff 阻抗 & 衰減 --------------------
def microstrip_Z0_SE_diff(w_um, h_um, t_um, er, s_um):
    """
    回傳 (Zse, Zdiff, er_eff)
    s_um: 差動對內間距 (僅 Diff 模式會用到)
    """
    w, h, t, s = w_um*1e-6, h_um*1e-6, t_um*1e-6, s_um*1e-6
    # SE 模型
    a = 1 + log((w/h + 1.1)/2.7) / log(2.7)
    er_eff = (er + 1)/2 + (er - 1)/2 * (1 + 10*h/w)**(-a)
    Zse = 120*pi / (sqrt(er_eff)*(w/h + 1.98*(w/h)**0.85))
    # Diff 模型（簡化：Zdiff ≈ 2*Zse·(1-0.37*exp(-2*s/w))）
    Zdiff = 2 * Zse * (1 - 0.37 * exp(-2 * s / w))
    return Zse, Zdiff, er_eff

# -------------------- 側邊欄 ------------------------
with sidebar:
    subheader("幾何與材料")
    struct   = radio("結構", ["microstrip", "stripline", "coplanar", "coaxial"], horizontal=True)
    sub      = radio("基板", list(MAT_DB.keys()), horizontal=True)
    sig_type = radio("訊號種類", ["Single-End", "Differential"], horizontal=True)
    L_cm     = slider("線長 (cm)", 1, 50, 10)
    w_um     = slider("線寬 w (µm)", 25, 500, 400)
    d_um     = slider("線距 d (µm)", 25, 500, 100)   # 對地或對鄰線
    h_um     = slider("基板厚 h (µm)", 50, 600, 200)
    t_um     = slider("銅厚 t (µm)", 17, 70, 35)
    alpha_1GHz_dB = slider("衰減常數 α (dB/m@1 GHz)", 0.1, 5.0, 1.0, 0.1)

    c1, c2 = columns(2)
    with c1:
        f_start = number_input("起始頻率 (GHz)", 5.0, 110.0, 10.0, 1.0)
    with c2:
        f_stop  = number_input("終止頻率 (GHz)", 10.0, 120.0, 60.0, 1.0)
    if f_stop <= f_start:
        error("終止頻率必須 > 起始頻率"); stop()

er   = MAT_DB[sub]["er"]
tanD = MAT_DB[sub]["tanD"]
sig  = MAT_DB[sub]["sigma"]

# -------------------- 頻率向量 --------------------
f_GHz = linspace(f_start, f_stop, 401)
f_Hz  = f_GHz * 1e9

# -------------------- 阻抗 & 衰減 ------------------
# 差動內間距先用 d_um 當近似
Zse, Zdiff, er_eff = microstrip_Z0_SE_diff(w_um, h_um, t_um, er, d_um)
Z0     = Zse if sig_type == "Single-End" else Zdiff
alpha_Np_1GHz = alpha_1GHz_dB / 20 * log(10)
alpha_total = alpha_Np_1GHz * sqrt(f_GHz / 1.0)
beta = 2*pi*f_Hz / c0 * sqrt(er_eff)

# -------------------- S 參數 --------------------------
L_m = L_cm / 100
S21 = exp(-alpha_total * L_m - 1j*beta * L_m)
S11 = (Z0 - 50)/(Z0 + 50) * ones_like(f_GHz)

# -------------------- 串音（快速公式） -----------------
# 差動模式：Cm/Lm 再乘 0.6 經驗係數（弱耦合近似）
ratio = 1.0 if sig_type == "Single-End" else 0.6
Cm = ratio * 0.035 * ((w_um/h_um)**0.8 * (d_um/h_um)**-1.2 * sqrt(er))**1.25 * exp(-0.9*d_um/w_um)
Lm = ratio * 0.002 * log(1 + (2*h_um/d_um)**1.5) * (w_um/h_um)**-0.3 * 1e3
beta_c = 2*pi*f_GHz*1e9 / c0 * sqrt(er_eff)
NEXT = 0.5*(Cm*Z0 + Lm/Z0) * f_Hz * 1e-12 * 20*log10(e)
FEXT = 0.5*(Cm*Z0 - Lm/Z0) * f_Hz * 1e-12 * 20*log10(e) * sin(beta_c*L_m)/(beta_c*L_m)

# -------------------- 時域脈衝 -----------------------
df = f_GHz[1] - f_GHz[0]
t  = fft.fftfreq(len(f_GHz), df)
pulse = ifft(S21)

# -------------------- 繪圖 ---------------------------
col1, col2 = columns(2)
mode_tag = "(SE)" if sig_type == "Single-End" else "(Diff)"
with col1:
    fig, ax = subplots(figsize=(5,3))
    ax.plot(f_GHz, 20*log10(abs(S11)), label='S11 '+mode_tag)
    ax.plot(f_GHz, 20*log10(abs(S21)), label='S21 '+mode_tag)
    ax.plot(f_GHz, NEXT, label='NEXT', ls='--')
    ax.plot(f_GHz, FEXT, label='FEXT', ls=':')
    ax.set_xlabel("Freq (GHz)")
    ax.set_ylabel("Magnitude (dB)")
    ax.set_title(f"α @ 1 GHz = {alpha_1GHz_dB:.2f} dB/m {mode_tag}")
    ax.legend(); ax.grid()
    pyplot(fig)

with col2:
    fig, ax = subplots(figsize=(5,3))
    ax.plot(t*1e9, abs(pulse))
    ax.set_xlabel("Time (ns)")
    ax.set_ylabel("|h(t)|")
    ax.set_title(f"α @ 1 GHz = {alpha_1GHz_dB:.2f} dB/m {mode_tag}")
    ax.grid()
    pyplot(fig)

caption("左：頻域（含 NEXT/FEXT）；右：時域脈衝響應")
