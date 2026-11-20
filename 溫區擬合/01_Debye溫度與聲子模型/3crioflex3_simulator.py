from streamlit import columns, dataframe, error, markdown, number_input, pyplot, radio, set_page_config, sidebar, slider, subheader, success, tabs, title, warning
from matplotlib.pyplot import subplots, tight_layout
from numpy import arange, exp, logspace, pi
from pandas import DataFrame
from fontUtil2 import 配置中文
配置中文()
#import streamlit as st
#import numpy as np
#import matplotlib.pyplot as plt
from scipy.integrate import quad
#import pandas as pd

# ============================================================
# Delft cri/oFlex3 Cryogenic Transmission Line Thermal Simulator
# 基於聲子熱容 (Debye) + 邊界散射 (Casimir) 模型
# 不使用 Wiedemann-Franz 定律
# ============================================================

set_page_config(page_title="cri/oFlex3 熱負載模擬器", layout="wide")
# ============================================================
# 物理常數與材料參數
# ============================================================

THETA_D = {"Ag": 225, "NbTi": 280, "Al": 428, "Polyimide": 300}
V_S = {"Ag": 3650, "NbTi": 4000, "Al": 6420, "Polyimide": 2000}
RHO_MASS = {"Ag": 10500, "NbTi": 6200, "Al": 2700, "Polyimide": 1400}
M_ATOM = {
    "Ag": 107.87e-3 / 6.022e23,
    "NbTi": (0.47*92.91 + 0.53*47.87) * 1e-3 / 6.022e23,
    "Al": 26.98e-3 / 6.022e23,
    "Polyimide": 30e-3 / 6.022e23,
}
k_B = 1.38e-23

TEMP_STAGES = {
    "300 K → 50 K":   {"T_hot": 300, "T_cold": 50,  "target_load": 2.7e-3,  "material": "Ag"},
    "50 K → 4 K":     {"T_hot": 50,  "T_cold": 4,   "target_load": 0.8e-3,  "material": "Ag"},
    "4 K → 0.6 K":    {"T_hot": 4,   "T_cold": 0.6, "target_load": 5.4e-6,  "material": "Ag"},
    "0.6 K → 100 mK": {"T_hot": 0.6, "T_cold": 0.1, "target_load": 290e-9,  "material": "Ag"},
    "100 mK → 10 mK": {"T_hot": 0.1, "T_cold": 0.01,"target_load": 5.9e-9,  "material": "Ag"},
}

NBTI_LOADS = {
    "4 K → 0.6 K":    540e-9,
    "0.6 K → 100 mK": 29e-9,
    "100 mK → 10 mK": 590e-12,
}

# ============================================================
# 聲子模型函數
# ============================================================

def debye_integral(x):
    if x < 1e-10: return x**3 / 3
    if x > 100: return pi**4 / 15
    result, _ = quad(lambda t: t**3 / (exp(t) - 1), 0, x, limit=100)
    return result

def phonon_heat_capacity(T, material):
    theta = THETA_D[material]
    rho = RHO_MASS[material]
    M = M_ATOM[material]
    N_density = rho / M
    x = theta / T
    return 9 * N_density * k_B * (T/theta)**3 * debye_integral(x)

def phonon_mean_free_path(T, material, Lb_nm=100):
    theta = THETA_D[material]
    L_b = Lb_nm * 1e-9
    if T < theta / 10:
        return L_b
    else:
        mfp_inv = 1/L_b + 1e8 * T * exp(-theta / (3*T))
        return 1 / mfp_inv

def phonon_thermal_conductivity(T, material, Lb_nm=100):
    C_v = phonon_heat_capacity(T, material)
    v = V_S[material]
    mfp = phonon_mean_free_path(T, material, Lb_nm)
    return max((1/3) * C_v * v * mfp, 1e-15)

def electronic_thermal_conductivity(T, material):
    if material == "Ag":
        if T < 20: return 200 * T + 5 * T**2
        elif T < 100: return 2000 + 40 * T
        elif T < 150: return 4000 - 10 * T
        else: return 420
    elif material == "NbTi":
        if T < 10: return 0.027 * T**2 + 0.005 * T**3
        else: return 0.3 * T
    elif material == "Al":
        if T < 20: return 30 * T + 0.3 * T**3
        elif T < 50: return 300 + 5 * T
        else: return 237
    elif material == "Polyimide":
        return 0.1 * T**2 + 0.01 * T**3
    return 1e-15

def total_thermal_conductivity(T, material, Lb_nm=100):
    k_ph = phonon_thermal_conductivity(T, material, Lb_nm)
    k_e = electronic_thermal_conductivity(T, material)
    if material == "Ag": return k_e * 0.92 + k_ph * 0.08
    elif material == "NbTi": return (k_e * 0.4 + k_ph * 0.6) if T < 10 else (k_e * 0.7 + k_ph * 0.3)
    elif material == "Al": return k_e * 0.6 + k_ph * 0.4
    elif material == "Polyimide": return k_ph
    return max(k_e * 0.5 + k_ph * 0.5, 1e-15)

def thermal_integrate(T1, T2, material, Lb_nm=100):
    integral, _ = quad(lambda T: total_thermal_conductivity(T, material, Lb_nm), T1, T2, limit=100)
    return integral

def solve_length(T_hot, T_cold, target_Q, A, material, Lb_nm=100):
    integral = thermal_integrate(T_cold, T_hot, material, Lb_nm)
    if integral < 1e-30 or target_Q < 1e-30: return 1e-6
    return max((A / target_Q) * integral, 1e-6)

def calc_heat_load(T_hot, T_cold, length, A, material, Lb_nm=100):
    integral = thermal_integrate(T_cold, T_hot, material, Lb_nm)
    return (A / length) * integral

# ============================================================
# Streamlit UI
# ============================================================

with sidebar:
    subheader("⚙️ 模擬參數設定")
    subheader("傳輸線幾何")
    c1, c2 = columns(2)
    with c1:
        ag_w = number_input("Ag 線寬 (µm)", value=50, min_value=10, max_value=200)
        ag_t = number_input("Ag 線厚 (µm)", value=3., min_value=.5, max_value=20.)
    with c2:
        nbti_w = number_input("NbTi 線寬 (µm)", value=30, min_value=5, max_value=100)
        nbti_t = number_input("NbTi 線厚 (µm)", value=2., min_value=.5, max_value=10.)

    sh_w = number_input("Shield 寬度 (µm)", value=100, min_value=20, max_value=500)
    sh_t = number_input("Shield 厚度 (µm)", value=3, min_value=1, max_value=50)

    subheader("聲子模型")
    Lb = slider("邊界散射長度 (nm)", 10, 500, 100, help="Casimir 邊界散射特徵長度")

    A_Ag = ag_w * 1e-6 * ag_t * 1e-6
    A_NbTi = nbti_w * 1e-6 * nbti_t * 1e-6
    A_Al = sh_w * 1e-6 * sh_t * 1e-6

    markdown(f"**Ag**: {A_Ag*1e12:.0f} µm² | **NbTi**: {A_NbTi*1e12:.0f} µm² | **Al**: {A_Al*1e12:.0f} µm²")

# ============================================================
# Tabs
# ============================================================

tab1, tab2, tab3, tab4 = tabs(["📊 溫度段熱負載", "📈 熱導率曲線", "🔧 長度回推", "📋 規格比較"])

# Tab 1
with tab1:
    subheader("各溫度段熱負載計算")
    sel = radio("選擇溫度段", list(TEMP_STAGES.keys()), horizontal=True)
    info = TEMP_STAGES[sel]
    Th, Tc, tgt, mat = info["T_hot"], info["T_cold"], info["target_load"], info["material"]

    col1, col2 = columns(2)
    with col1:
        subheader("溫度段資訊")
        markdown(f"**溫度**: {Th} K → {Tc} K")
        markdown(f"**材料**: {mat}")
        unit = "µW" if tgt >= 1e-6 else "nW" if tgt >= 1e-9 else "pW"
        val = tgt * 1e6 if tgt >= 1e-6 else tgt * 1e9 if tgt >= 1e-9 else tgt * 1e12
        markdown(f"**目標**: {val:.1f} {unit}/CH")

        L_mm = slider("長度 (mm)", 1, 500, 200)
        L_m = L_mm * 1e-3
        A_w = A_Ag if mat == "Ag" else A_NbTi
        Q_w = calc_heat_load(Th, Tc, L_m, A_w, mat, Lb)
        Q_s = calc_heat_load(Th, Tc, L_m, A_Al, "Al", Lb)
        Q_tot = Q_w + Q_s

        markdown("---")
        def fmt_q(Q):
            if Q >= 1e-3: return f"{Q*1e3:.2f} mW"
            elif Q >= 1e-6: return f"{Q*1e6:.3f} µW"
            elif Q >= 1e-9: return f"{Q*1e9:.2f} nW"
            else: return f"{Q*1e12:.2f} pW"
        markdown(f"**計算熱負載**:")
        markdown(f"- {mat} 線芯: {fmt_q(Q_w)}")
        markdown(f"- Al Shield: {fmt_q(Q_s)}")
        markdown(f"- **總計**: {fmt_q(Q_tot)}")
        ratio = Q_tot / tgt
        markdown(f"**與目標比值**: {ratio:.2f}x")
        if ratio > 1.5: error("⚠️ 計算值遠高於目標")
        elif ratio < 0.5: warning("⚠️ 計算值遠低於目標")
        else: success("✅ 計算值與目標接近")

    with col2:
        subheader("全溫度段總覽")
        results = []
        for stage, inf in TEMP_STAGES.items():
            Th_, Tc_, mat_, tgt_ = inf["T_hot"], inf["T_cold"], inf["material"], inf["target_load"]
            A_w_ = A_Ag if mat_ == "Ag" else A_NbTi
            Q_w_ = calc_heat_load(Th_, Tc_, L_m, A_w_, mat_, Lb)
            Q_s_ = calc_heat_load(Th_, Tc_, L_m, A_Al, "Al", Lb)
            results.append({"溫度段": stage, "材料": mat_, "目標": tgt_, "計算": Q_w_ + Q_s_, "比值": (Q_w_+Q_s_)/tgt_})
        df = DataFrame(results)
        disp = df.copy()
        def fmt_w(x):
            if x >= 1e-3: return f"{x*1e3:.2f} mW"
            elif x >= 1e-6: return f"{x*1e6:.2f} µW"
            elif x >= 1e-9: return f"{x*1e9:.1f} nW"
            else: return f"{x*1e12:.1f} pW"
        disp["目標"] = disp["目標"].apply(fmt_w)
        disp["計算值"] = disp["計算"].apply(fmt_w)
        disp["比值"] = disp["比值"].apply(lambda x: f"{x:.2f}x")
        dataframe(disp[["溫度段", "材料", "目標", "計算值", "比值"]], use_container_width=True)

        fig, ax = subplots(figsize=(10, 5))
        x_pos = arange(len(df))
        ax.bar(x_pos - 0.175, df["目標"]*1e6, 0.35, label='目標值', alpha=0.8, color='#FF6B6B')
        ax.bar(x_pos + 0.175, df["計算"]*1e6, 0.35, label='計算值', alpha=0.8, color='#4ECDC4')
        ax.set_xlabel('溫度段')
        ax.set_ylabel('熱負載 (µW)')
        ax.set_title(f'熱負載比較 (L={L_mm}mm)')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(df["溫度段"], rotation=45, ha='right')
        ax.legend()
        ax.set_yscale('log')
        ax.grid(True, alpha=0.3)
        pyplot(fig)

# Tab 2
with tab2:
    subheader("熱導率溫度依賴曲線")
    T_range = logspace(-2, 2.5, 200)
    materials = ["Ag", "NbTi", "Al"]
    colors = {"Ag": "#FFD700", "NbTi": "#4169E1", "Al": "#C0C0C0"}

    fig, axes = subplots(2, 2, figsize=(14, 10))

    ax1 = axes[0, 0]
    for mat in materials:
        kappa = [total_thermal_conductivity(T, mat, Lb) for T in T_range]
        ax1.loglog(T_range, kappa, label=mat, color=colors[mat], linewidth=2)
    ax1.axvline(x=10, color='red', linestyle='--', alpha=0.5, label='NbTi Tc')
    ax1.set_xlabel('溫度 (K)')
    ax1.set_ylabel('κ (W/m·K)')
    ax1.set_title('總熱導率')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2 = axes[0, 1]
    for mat in materials:
        kappa = [phonon_thermal_conductivity(T, mat, Lb) for T in T_range]
        ax2.loglog(T_range, kappa, label=mat, color=colors[mat], linewidth=2)
    ax2.set_xlabel('溫度 (K)')
    ax2.set_ylabel('κ_ph (W/m·K)')
    ax2.set_title('聲子熱導率')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    ax3 = axes[1, 0]
    for mat in materials:
        Cv = [phonon_heat_capacity(T, mat) for T in T_range]
        ax3.loglog(T_range, Cv, label=mat, color=colors[mat], linewidth=2)
    ax3.set_xlabel('溫度 (K)')
    ax3.set_ylabel('C_v (J/m³·K)')
    ax3.set_title('聲子熱容 (Debye)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    ax4 = axes[1, 1]
    for mat in materials:
        mfp = [phonon_mean_free_path(T, mat, Lb) * 1e9 for T in T_range]
        ax4.semilogx(T_range, mfp, label=mat, color=colors[mat], linewidth=2)
    ax4.axhline(y=Lb, color='red', linestyle='--', alpha=0.5, label=f'L_b = {Lb} nm')
    ax4.set_xlabel('溫度 (K)')
    ax4.set_ylabel('MFP (nm)')
    ax4.set_title('聲子平均自由程')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    tight_layout()
    pyplot(fig)

# Tab 3
with tab3:
    subheader("由目標熱負載回推所需長度")
    sel_rev = radio("選擇溫度段", list(TEMP_STAGES.keys()), key="rev", horizontal=True)
    inf_rev = TEMP_STAGES[sel_rev]
    Th_r, Tc_r, mat_r = inf_rev["T_hot"], inf_rev["T_cold"], inf_rev["material"]

    col1, col2 = columns(2)
    with col1:
        subheader("輸入參數")
        unit_r = radio("單位", ["mW", "µW", "nW", "pW"], index=1, horizontal=True)
        val_r = number_input(f"目標熱負載 ({unit_r})", value=5.4, min_value=0.001)
        conv = {"mW": 1e-3, "µW": 1e-6, "nW": 1e-9, "pW": 1e-12}
        target_Q = val_r * conv[unit_r]
        A_r = A_Ag if mat_r == "Ag" else A_NbTi
        L_calc = solve_length(Th_r, Tc_r, target_Q, A_r, mat_r, Lb)
        markdown("---")
        markdown(f"**所需長度: {L_calc*1e3:.2f} mm**")
        Q_v = calc_heat_load(Th_r, Tc_r, L_calc, A_r, mat_r, Lb)
        markdown(f"驗證: {Q_v*1e9:.2f} nW")

    with col2:
        subheader("全溫度段回推表")
        len_res = []
        for stage, inf in TEMP_STAGES.items():
            Th_, Tc_, mat_, tgt_ = inf["T_hot"], inf["T_cold"], inf["material"], inf["target_load"]
            A_w_ = A_Ag if mat_ == "Ag" else A_NbTi
            L_ = solve_length(Th_, Tc_, tgt_, A_w_, mat_, Lb)
            len_res.append({"溫度段": stage, "材料": mat_, "目標": tgt_, "長度_mm": L_*1e3})
        for stage, tgt in NBTI_LOADS.items():
            inf = TEMP_STAGES[stage]
            L_ = solve_length(inf["T_hot"], inf["T_cold"], tgt, A_NbTi, "NbTi", Lb)
            len_res.append({"溫度段": stage+" (NbTi)", "材料": "NbTi", "目標": tgt, "長度_mm": L_*1e3})

        len_df = DataFrame(len_res)
        disp_len = len_df.copy()
        disp_len["目標熱負載"] = disp_len["目標"].apply(fmt_w)
        disp_len["回推長度"] = disp_len["長度_mm"].apply(lambda x: f"{x:.2f} mm")
        dataframe(disp_len[["溫度段", "材料", "目標熱負載", "回推長度"]], use_container_width=True)

        fig, ax = subplots(figsize=(10, 5))
        stages = len_df["溫度段"].tolist()
        lengths = len_df["長度_mm"].tolist()
        cols = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#45B7D1', '#96CEB4', '#FFEAA7']
        bars = ax.barh(stages, lengths, color=cols[:len(stages)])
        ax.set_xlabel('回推長度 (mm)')
        ax.set_title('各溫度段達成目標所需長度')
        ax.set_xlim(0, max(lengths) * 1.2)
        for bar, length in zip(bars, lengths):
            ax.text(bar.get_width() + max(lengths)*0.02, bar.get_y() + bar.get_height()/2,
                   f'{length:.2f} mm', va='center', fontsize=9)
        pyplot(fig)

# Tab 4
with tab4:
    subheader("cri/oFlex3 規格比較")
    specs = {
        "參數": ["通道數", "總厚度", "材料", "線型", "阻抗", "頻率", "彎曲半徑", "熱負載(3K-0.7K)", "熱負載(10-350mK)"],
        "官方規格": ["8", "0.3 mm", "Polyimide+Ag/NbTi", "Stripline", "50 Ω", "DC-18 GHz", "5 mm", "< 4 µW/CH", "~ 20 nW/CH"],
        "模擬參數": ["8", f"{ag_t+nbti_t+sh_t} µm", "Ag/NbTi+Al", "Stripline", "50 Ω", "DC-18 GHz", "5 mm", "計算中", "計算中"],
    }
    dataframe(DataFrame(specs), use_container_width=True, hide_index=True)

    subheader("多通道累積熱負載")
    ch_counts = [1, 8, 16, 32, 64, 128, 256]
    loads_4K = [TEMP_STAGES["4 K → 0.6 K"]["target_load"] * n * 1e6 for n in ch_counts]
    loads_mK = [TEMP_STAGES["0.6 K → 100 mK"]["target_load"] * n * 1e9 for n in ch_counts]

    fig, (ax1, ax2) = subplots(1, 2, figsize=(14, 5))
    ax1.loglog(ch_counts, loads_4K, 'o-', color='#FF6B6B', lw=2, ms=8)
    ax1.set_xlabel('通道數'); ax1.set_ylabel('總熱負載 (µW)'); ax1.set_title('4K 段累積')
    ax1.grid(True, alpha=0.3)
    ax2.loglog(ch_counts, loads_mK, 'o-', color='#4ECDC4', lw=2, ms=8)
    ax2.set_xlabel('通道數'); ax2.set_ylabel('總熱負載 (nW)'); ax2.set_title('mK 段累積')
    ax2.grid(True, alpha=0.3)
    tight_layout()
    pyplot(fig)

with sidebar:
    title("🔬 Delft cri/oFlex3 低溫傳輸線熱負載模擬器")
    markdown("**基於聲子熱容與邊界散射模型 | Ag/NbTi + Aluminum Shield**")
    #markdown("---")
    markdown(r"""
### 📖 模型說明

**聲子熱容 (Debye Model)**: $C_v = 9Nk_B(T/\theta_D)^3 \int_0^{\theta_D/T} \frac{t^3}{e^t-1}dt$

**邊界散射 (Casimir)**: 低溫下 $\Lambda = L_b$，熱導率 $\kappa = \frac{1}{3} C_v v_s \Lambda$

**材料特性**:
- **Ag**: 電子熱導主導 (~92%)，聲子修正
- **NbTi**: 超導態 $T_c \approx 10$K，電子熱導被抑制，$\kappa \approx 0.027T^2$ W/mK
- **Al Shield**: 電磁屏蔽 + 額外熱負載貢獻

**參考來源**:
- Delft Circuits cri/oFlex3 數據表 (cryocoax.com)
- Woodcraft et al., "Thermal conductance at millikelvin temperatures of woven ribbon cables"
- 純銀低溫熱導率文獻數據
""")
