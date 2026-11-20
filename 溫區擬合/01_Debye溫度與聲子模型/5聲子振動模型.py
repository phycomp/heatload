from streamlit import cache_data, columns, dataframe, error, header, markdown, number_input, pyplot, radio, selectbox, set_page_config, sidebar, slider, subheader, success, tabs, title, warning
from matplotlib.pyplot import subplots, tight_layout
from numpy import arange, exp, logspace
from pandas import DataFrame
from fontUtil2 import 配置中文
配置中文()
#import streamlit as st
#import numpy as np
#import matplotlib.pyplot as plt
from scipy.integrate import quad
from scipy.optimize import fsolve
#import pandas as pd

set_page_config(page_title="cri/oFlex3 熱負載模擬器", layout="wide")


# ============================================================
# 物理常數與材料參數
# ============================================================

# 參考圖片中的溫度段與熱負載規格
TEMP_STAGES = {
    "300 K → 50 K": {"T_hot": 300, "T_cold": 50, "target_load": 2.7e-3, "material": "Ag"},   # 2.7 mW/CH
    "50 K → 4 K":   {"T_hot": 50,  "T_cold": 4,  "target_load": 0.8e-3, "material": "Ag"},   # 0.8 mW/CH
    "4 K → 0.6 K":  {"T_hot": 4,   "T_cold": 0.6,"target_load": 5.4e-6, "material": "NbTi"}, # 5.4 µW/CH (Ag)
    "0.6 K → 100 mK":{"T_hot": 0.6,"T_cold": 0.1,"target_load": 290e-9, "material": "NbTi"}, # 290 nW/CH (Ag) / 29 nW/CH (NbTi)
    "100 mK → 10 mK":{"T_hot": 0.1,"T_cold": 0.01,"target_load": 5.9e-9, "material": "NbTi"}, # 5.9 nW/CH (Ag) / 590 pW/CH (NbTi)
}

# 參考圖片中 NbTi 段的熱負載（藍色線）
NBTI_TARGET_LOADS = {
    "4 K → 0.6 K": 540e-9,      # 540 nW/CH
    "0.6 K → 100 mK": 29e-9,    # 29 nW/CH
    "100 mK → 10 mK": 590e-12,  # 590 pW/CH
}

# ============================================================
# 聲子熱容與邊界散射模型
# ============================================================

@cache_data
def get_material_properties():
    """
    基於聲子物理的低溫熱導率模型
    使用 Debye 模型計算聲子熱容 + Casimir 邊界散射
    """
    
    # Debye 溫度 (K)
    theta_D = {
        "Ag": 225,
        "NbTi": 280,  # NbTi 合金近似值
        "Al": 428,
    }
    
    # 聲子速度 (m/s)
    v_s = {
        "Ag": 3650,
        "NbTi": 4000,
        "Al": 6420,
    }
    
    # 晶格常數 / 特徵長度 (nm) - 用於邊界散射
    a_lat = {
        "Ag": 0.409,
        "NbTi": 0.33,
        "Al": 0.405,
    }
    
    # 材料密度 (kg/m³)
    rho_mass = {
        "Ag": 10500,
        "NbTi": 6200,
        "Al": 2700,
    }
    
    return theta_D, v_s, a_lat, rho_mass

def debye_integral(x):
    """Debye 積分: ∫₀^x t³/(e^t - 1) dt"""
    if x < 1e-10:
        return x**3 / 3
    result, _ = quad(lambda t: t**3 / (exp(t) - 1), 0, x, limit=100)
    return result

def phonon_heat_capacity(T, material):
    """
    基於 Debye 模型的聲子熱容 (J/m³·K)
    C_v = 9 * N * k_B * (T/θ_D)³ * DebyeIntegral(θ_D/T)
    其中 N 是原子數密度
    """
    theta_D, v_s, a_lat, rho_mass = get_material_properties()
    
    theta = theta_D[material]
    rho = rho_mass[material]
    
    # 原子質量 (kg)
    if material == "Ag":
        M_atom = 107.87e-3 / 6.022e23  # kg/atom
    elif material == "NbTi":
        M_atom = (0.47*92.91 + 0.53*47.87) * 1e-3 / 6.022e23
    else:  # Al
        M_atom = 26.98e-3 / 6.022e23
    
    N_density = rho / M_atom  # 原子數密度 (atoms/m³)
    
    k_B = 1.38e-23  # J/K
    
    x = theta / T
    
    # Debye 熱容公式
    C_v = 9 * N_density * k_B * (T/theta)**3 * debye_integral(x)
    
    return C_v

def phonon_mean_free_path(T, material, boundary_length_nm=100):
    """
    聲子平均自由程 (m) - 邊界散射主導
    使用 Casimir 邊界散射模型: Λ = boundary_length
    在低溫下，Umklapp 散射被凍結，邊界散射主導
    
    boundary_length_nm: 特徵邊界長度 (nm)，對應薄膜厚度或晶粒尺寸
    """
    theta_D, v_s, a_lat, rho_mass = get_material_properties()
    
    theta = theta_D[material]
    v = v_s[material]
    
    # 特徵邊界長度 (m)
    L_b = boundary_length_nm * 1e-9
    
    # 溫度相關的聲子波長
    # λ_phonon ~ h * v_s / (k_B * T)
    h = 6.626e-34
    k_B = 1.38e-23
    lambda_ph = h * v / (k_B * T)
    
    # Casimir 邊界散射: Λ = L_b (當 λ_ph << L_b)
    # 當 T 很低時，聲子波長變長，可能出現頻率相關的邊界散射
    
    # 頻率相關的邊界散射修正 (參考 Hanus et al. 模型)
    # 對於薄膜/細線，邊界散射 MFP 與幾何尺寸相關
    
    if T < theta / 10:
        # 低溫極限: 邊界散射主導，MFP 趨近於邊界長度
        mfp = L_b
    else:
        # 中溫區: Umklapp 散射開始貢獻
        # 簡化模型: 1/Λ = 1/L_b + A * T * exp(-θ/(3T))
        A_umklapp = 1e8  # 經驗參數
        mfp_inv = 1/L_b + A_umklapp * T * exp(-theta / (3*T))
        mfp = 1 / mfp_inv
    
    return mfp

def phonon_thermal_conductivity(T, material, boundary_length_nm=100):
    """
    基於聲子熱容與邊界散射的熱導率 (W/m·K)
    κ = (1/3) * C_v * v_s * Λ
    """
    C_v = phonon_heat_capacity(T, material)
    v = get_material_properties()[1][material]
    mfp = phonon_mean_free_path(T, material, boundary_length_nm)
    
    kappa = (1/3) * C_v * v * mfp
    
    return kappa

# ============================================================
# 電子熱導率 (用於 Ag 高溫段，但不使用 Wiedemann-Franz)
# ============================================================

def electronic_thermal_conductivity(T, material):
    """
    電子熱導率 - 使用獨立測量數據，不依賴 Wiedemann-Franz 定律
    基於文獻中的實驗數據擬合
    """
    if material == "Ag":
        # 純銀的低溫熱導率 (來自文獻數據擬合)
        # 高 RRR 銀: κ ~ a*T + b*T² (低溫), ~ 常數 (高溫)
        if T < 20:
            # 低溫: 電子熱導率 ~ T (雜質散射) 或 ~ T² (聲子散射)
            kappa = 400 * T + 2 * T**2  # W/m·K, 經驗擬合
        elif T < 100:
            kappa = 8000 - 40 * T  # 過渡區
        else:
            kappa = 420  # 室溫值 W/m·K
    elif material == "NbTi":
        # NbTi 超導態熱導率 (來自 Woodcraft 文獻)
        # κ_NbTi = 0.027 * (T/K)² W/m·K (超導態)
        # 正常態: 更高，但在低溫下通常處於超導態
        Tc = 10  # K, 臨界溫度
        if T < Tc:
            # 超導態 - 電子熱導率被抑制
            kappa_e = 0.027 * T**2
            # 加上聲子貢獻 (很小)
            kappa_ph = 0.001 * T**3
            kappa = kappa_e + kappa_ph
        else:
            # 正常態
            kappa = 0.5 * T  # 簡化
    elif material == "Al":
        # 鋁的熱導率
        if T < 20:
            kappa = 50 * T + 0.5 * T**3
        else:
            kappa = 237  # 室溫值
    else:
        kappa = 1.0
    
    return kappa

# ============================================================
# 總熱導率 (聲子 + 電子)
# ============================================================

def total_thermal_conductivity(T, material, boundary_length_nm=100, phonon_fraction=0.5):
    """
    總熱導率 = 聲子貢獻 + 電子貢獻
    phonon_fraction: 聲子貢獻的比例 (用於調節)
    """
    kappa_ph = phonon_thermal_conductivity(T, material, boundary_length_nm)
    kappa_e = electronic_thermal_conductivity(T, material)
    
    # 對於金屬，高溫下電子主導；低溫下聲子可能重要
    # 使用加權組合
    if material == "Ag":
        # 銀: 高溫電子主導，低溫也是電子主導 (純金屬)
        if T > 50:
            kappa_total = kappa_e * 0.95 + kappa_ph * 0.05
        else:
            kappa_total = kappa_e * 0.8 + kappa_ph * 0.2
    elif material == "NbTi":
        # NbTi: 超導態電子被抑制，聲子貢獻相對重要
        if T < 10:
            kappa_total = kappa_e * 0.3 + kappa_ph * 0.7
        else:
            kappa_total = kappa_e * 0.7 + kappa_ph * 0.3
    else:  # Al
        kappa_total = kappa_e * 0.5 + kappa_ph * 0.5
    
    return max(kappa_total, 1e-6)  # 避免零值

# ============================================================
# 熱流計算
# ============================================================

def thermal_conductance_integral(T1, T2, material, boundary_length_nm=100, A=1e-6):
    """
    計算熱導 G = ∫ κ(T) dT / ΔT
    返回熱導 (W/K)
    """
    def integrand(T):
        return total_thermal_conductivity(T, material, boundary_length_nm)
    
    integral, _ = quad(integrand, T1, T2, limit=100)
    
    # G = (A/L) * ∫ κ dT / ΔT, 這裡先計算單位長度的
    # 返回 ∫ κ dT (W/m)
    return integral

def calculate_heat_load(T_hot, T_cold, length, A, material, boundary_length_nm=100):
    """
    計算熱負載 Q = (A/L) * ∫_{T_cold}^{T_hot} κ(T) dT
    """
    integral = thermal_conductance_integral(T_cold, T_hot, material, boundary_length_nm, A)
    Q = (A / length) * integral
    return Q

def solve_length_for_heatload(T_hot, T_cold, target_Q, A, material, boundary_length_nm=100):
    """
    回推計算所需長度 L = (A / Q) * ∫ κ dT
    """
    integral = thermal_conductance_integral(T_cold, T_hot, material, boundary_length_nm, A)
    L = (A / target_Q) * integral
    return L

# ============================================================
# Streamlit UI
# ============================================================
with sidebar:
    subheader("⚙️ 模擬參數設定")
    subheader("傳輸線幾何") # 材料幾何參數
    col1, col2 = columns(2)
    with col1:
        width_um = number_input("線寬 (µm)", value=100, min_value=10, max_value=500)
        thickness_um = number_input("線厚 (µm)", value=3., min_value=.3, max_value=50.)
    with col2:
        shield_thickness_um = number_input("Shield厚 (µm)", value=10, min_value=1, max_value=100)
        n_channels = number_input("通道數", value=8, min_value=1, max_value=256)

    # 聲子模型參數
    subheader("聲子模型參數")
    boundary_length = slider("邊界散射長度 (nm)", 10, 500, 100, help="Casimir 邊界散射的特徵長度，對應薄膜厚度或晶粒尺寸")
    phonon_fraction = slider("聲子貢獻比例", 0.0, 1.0, 0.3, help="聲子熱導率佔總熱導率的比例")

    # 計算截面積
    A_wire = (width_um * 1e-6) * (thickness_um * 1e-6)  # m²
    A_shield = (width_um * 2 * 1e-6) * (shield_thickness_um * 1e-6)  # 簡化 Shield 面積
    markdown(f"**單通道截面積**: {A_wire*1e12:.2f} µm²")
    markdown(f"**Shield 截面積**: {A_shield*1e12:.2f} µm²")

# ============================================================
# 主要顯示區域
# ============================================================

tab1, tab2, tab3, tab4 = tabs(["📊 溫度段熱負載", "📈 熱導率曲線", "🔧 長度回推", "📋 規格比較"])

# ============================================================
# Tab 1: 溫度段熱負載計算
# ============================================================

with tab1:
    header("各溫度段熱負載計算")
    markdown("基於圖片中的 cri/oFlex3 規格，計算不同溫度段的熱負載")
    
    # 選擇溫度段
    selected_stage = selectbox("選擇溫度段", list(TEMP_STAGES.keys()))
    stage_info = TEMP_STAGES[selected_stage]
    
    T_hot = stage_info["T_hot"]
    T_cold = stage_info["T_cold"]
    target_load = stage_info["target_load"]
    material = stage_info["material"]
    
    col1, col2 = columns(2)
    
    with col1:
        subheader("溫度段資訊")
        markdown(f"**溫度範圍**: {T_hot} K → {T_cold} K")
        markdown(f"**參考材料**: {material}")
        markdown(f"**目標熱負載**: {target_load*1e3:.3f} mW/CH" if target_load >= 1e-6 else f"**目標熱負載**: {target_load*1e9:.1f} nW/CH")
        
        # 輸入長度
        length_mm = slider("傳輸線長度 (mm)", 10, 1000, 400, key="tab1_length")
        length_m = length_mm * 1e-3
        
        # 計算熱負載
        Q_wire = calculate_heat_load(T_hot, T_cold, length_m, A_wire, material, boundary_length)
        Q_shield = calculate_heat_load(T_hot, T_cold, length_m, A_shield, "Al", boundary_length)
        Q_total = Q_wire + Q_shield
        
        markdown("---")
        markdown(f"**計算熱負載 (單通道)**:")
        markdown(f"- {material} 線芯: {Q_wire*1e9:.2f} nW")
        markdown(f"- Al Shield: {Q_shield*1e9:.2f} nW")
        markdown(f"- **總計**: {Q_total*1e9:.2f} nW ({Q_total*1e6:.3f} µW)")
        
        # 與目標比較
        ratio = Q_total / target_load
        markdown(f"**與目標比值**: {ratio:.2f}x")
        
        if ratio > 1.5:
            error("⚠️ 計算值遠高於目標，可能需要調整長度或截面積")
        elif ratio < 0.5:
            warning("⚠️ 計算值遠低於目標，模型可能需要調整")
        else:
            success("✅ 計算值與目標接近")
    
    with col2:
        subheader("全溫度段總覽")
        
        results = []
        for stage_name, info in TEMP_STAGES.items():
            Th = info["T_hot"]
            Tc = info["T_cold"]
            mat = info["material"]
            tgt = info["target_load"]
            
            Q_w = calculate_heat_load(Th, Tc, length_m, A_wire, mat, boundary_length)
            Q_s = calculate_heat_load(Th, Tc, length_m, A_shield, "Al", boundary_length)
            Q_tot = Q_w + Q_s
            
            results.append({
                "溫度段": stage_name,
                "材料": mat,
                "目標 (W)": tgt,
                "計算 (W)": Q_tot,
                "比值": Q_tot / tgt,
                "線芯 (W)": Q_w,
                "Shield (W)": Q_s,
            })
        
        df = DataFrame(results)
        
        # 格式化顯示
        display_df = df.copy()
        display_df["目標"] = display_df["目標 (W)"].apply(lambda x: f"{x*1e9:.1f} nW" if x < 1e-6 else f"{x*1e6:.2f} µW" if x < 1e-3 else f"{x*1e3:.2f} mW")
        display_df["計算值"] = display_df["計算 (W)"].apply(lambda x: f"{x*1e9:.1f} nW" if x < 1e-6 else f"{x*1e6:.2f} µW" if x < 1e-3 else f"{x*1e3:.2f} mW")
        display_df["比值"] = display_df["比值"].apply(lambda x: f"{x:.2f}x")
        
        dataframe(display_df[["溫度段", "材料", "目標", "計算值", "比值"]], use_container_width=True)
        
        # 視覺化比較
        fig, ax = subplots(figsize=(10, 5))
        x_pos = arange(len(df))
        width = 0.35
        
        targets = df["目標 (W)"].values * 1e9  # nW
        calculated = df["計算 (W)"].values * 1e9  # nW
        
        ax.bar(x_pos - width/2, targets, width, label='目標值', alpha=0.8, color='#FF6B6B')
        ax.bar(x_pos + width/2, calculated, width, label='計算值', alpha=0.8, color='#4ECDC4')
        
        ax.set_xlabel('溫度段')
        ax.set_ylabel('熱負載 (nW)')
        ax.set_title(f'各溫度段熱負載比較 (L={length_mm}mm)')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(df["溫度段"], rotation=45, ha='right')
        ax.legend()
        ax.set_yscale('log')
        ax.grid(True, alpha=0.3)
        
        pyplot(fig)

# ============================================================
# Tab 2: 熱導率曲線
# ============================================================

with tab2:
    header("熱導率溫度依賴曲線")
    markdown("聲子熱導率 κ(T) 與總熱導率的溫度依賴關係")
    
    T_range = logspace(-2, 2.5, 200)  # 0.01 K 到 300 K
    
    materials = ["Ag", "NbTi", "Al"]
    colors = {"Ag": "#FFD700", "NbTi": "#4169E1", "Al": "#C0C0C0"}
    
    fig, axes = subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: 聲子熱導率
    ax1 = axes[0, 0]
    for mat in materials:
        kappa_ph = [phonon_thermal_conductivity(T, mat, boundary_length) for T in T_range]
        ax1.loglog(T_range, kappa_ph, label=f'{mat} (Phonon)', color=colors[mat], linewidth=2)
    ax1.set_xlabel('溫度 (K)')
    ax1.set_ylabel('聲子熱導率 κ_ph (W/m·K)')
    ax1.set_title('聲子熱導率 (Debye + Casimir 邊界散射)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.axvline(x=10, color='red', linestyle='--', alpha=0.5, label='NbTi Tc')
    
    # Plot 2: 電子熱導率
    ax2 = axes[0, 1]
    for mat in materials:
        kappa_e = [electronic_thermal_conductivity(T, mat) for T in T_range]
        ax2.loglog(T_range, kappa_e, label=f'{mat} (Electronic)', color=colors[mat], linewidth=2)
    ax2.set_xlabel('溫度 (K)')
    ax2.set_ylabel('電子熱導率 κ_e (W/m·K)')
    ax2.set_title('電子熱導率 (文獻實驗數據)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.axvline(x=10, color='red', linestyle='--', alpha=0.5)
    
    # Plot 3: 總熱導率
    ax3 = axes[1, 0]
    for mat in materials:
        kappa_total = [total_thermal_conductivity(T, mat, boundary_length, phonon_fraction) for T in T_range]
        ax3.loglog(T_range, kappa_total, label=f'{mat} (Total)', color=colors[mat], linewidth=2)
    ax3.set_xlabel('溫度 (K)')
    ax3.set_ylabel('總熱導率 κ_total (W/m·K)')
    ax3.set_title('總熱導率 (聲子 + 電子)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.axvline(x=10, color='red', linestyle='--', alpha=0.5)
    
    # Plot 4: 聲子熱容
    ax4 = axes[1, 1]
    for mat in materials:
        C_v = [phonon_heat_capacity(T, mat) for T in T_range]
        ax4.loglog(T_range, C_v, label=f'{mat}', color=colors[mat], linewidth=2)
    ax4.set_xlabel('溫度 (K)')
    ax4.set_ylabel('聲子熱容 C_v (J/m³·K)')
    ax4.set_title('聲子熱容 (Debye 模型)')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    tight_layout()
    pyplot(fig)
    
    # 顯示特定溫度點的數值
    subheader("特定溫度點熱導率")
    test_temps = [0.01, 0.1, 0.6, 4, 50, 300]
    kappa_data = []
    for T in test_temps:
        row = {"溫度 (K)": T}
        for mat in materials:
            k_ph = phonon_thermal_conductivity(T, mat, boundary_length)
            k_e = electronic_thermal_conductivity(T, mat)
            k_tot = total_thermal_conductivity(T, mat, boundary_length, phonon_fraction)
            row[f"{mat}_ph"] = k_ph
            row[f"{mat}_e"] = k_e
            row[f"{mat}_tot"] = k_tot
        kappa_data.append(row)
    
    kappa_df = DataFrame(kappa_data)
    dataframe(kappa_df, use_container_width=True)

# ============================================================
# Tab 3: 長度回推
# ============================================================

with tab3:
    header("由目標熱負載回推所需長度")
    markdown("給定目標熱負載，計算所需的傳輸線長度")
    
    # 選擇溫度段進行回推
    selected_stage_rev = selectbox("選擇溫度段 (回推)", list(TEMP_STAGES.keys()), key="rev_stage")
    stage_rev = TEMP_STAGES[selected_stage_rev]
    
    T_h = stage_rev["T_hot"]
    T_c = stage_rev["T_cold"]
    mat_rev = stage_rev["material"]
    
    col1, col2 = columns(2)
    
    with col1:
        subheader("輸入參數")
        
        # 目標熱負載輸入
        target_unit = radio("目標單位", ["mW", "µW", "nW", "pW"], index=1)
        target_val = number_input(f"目標熱負載 ({target_unit})", value=5.4, min_value=0.001)
        
        # 轉換為瓦特
        unit_conversion = {"mW": 1e-3, "µW": 1e-6, "nW": 1e-9, "pW": 1e-12}
        target_Q = target_val * unit_conversion[target_unit]
        
        # 使用與 Tab1 相同的截面積
        A_rev = A_wire
        
        # 計算長度
        L_calc = solve_length_for_heatload(T_h, T_c, target_Q, A_rev, mat_rev, boundary_length)
        L_mm = L_calc * 1e3
        
        markdown("---")
        markdown(f"**回推結果**:")
        markdown(f"- 所需長度: **{L_mm:.1f} mm**")
        markdown(f"- 所需長度: **{L_mm/10:.1f} cm**")
        
        # 驗證計算
        Q_verify = calculate_heat_load(T_h, T_c, L_calc, A_rev, mat_rev, boundary_length)
        markdown(f"- 驗證熱負載: {Q_verify*1e9:.2f} nW")
        
    with col2:
        subheader("全溫度段長度回推表")
        
        length_results = []
        for stage_name, info in TEMP_STAGES.items():
            Th = info["T_hot"]
            Tc = info["T_cold"]
            mat = info["material"]
            tgt = info["target_load"]
            
            L = solve_length_for_heatload(Th, Tc, tgt, A_wire, mat, boundary_length)
            
            length_results.append({
                "溫度段": stage_name,
                "材料": mat,
                "目標熱負載 (W)": tgt,
                "回推長度 (mm)": L * 1e3,
                "回推長度 (cm)": L * 1e2,
            })
        
        len_df = DataFrame(length_results)
        
        # 格式化
        display_len = len_df.copy()
        display_len["目標熱負載"] = display_len["目標熱負載 (W)"].apply(
            lambda x: f"{x*1e12:.0f} pW" if x < 1e-9 else f"{x*1e9:.1f} nW" if x < 1e-6 else f"{x*1e6:.2f} µW" if x < 1e-3 else f"{x*1e3:.2f} mW"
        )
        display_len["回推長度"] = display_len["回推長度 (mm)"].apply(lambda x: f"{x:.1f} mm")
        
        dataframe(display_len[["溫度段", "材料", "目標熱負載", "回推長度"]], use_container_width=True)
        
        # 長度比較圖
        fig, ax = subplots(figsize=(10, 5))
        colors_stage = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        
        stages = len_df["溫度段"].tolist()
        lengths = len_df["回推長度 (mm)"].tolist()
        
        bars = ax.barh(stages, lengths, color=colors_stage)
        ax.set_xlabel('回推長度 (mm)')
        ax.set_title('各溫度段達成目標熱負載所需長度')
        ax.set_xlim(0, max(lengths) * 1.2)
        
        # 添加數值標籤
        for bar, length in zip(bars, lengths):
            ax.text(bar.get_width() + max(lengths)*0.02, bar.get_y() + bar.get_height()/2,
                   f'{length:.1f} mm', va='center', fontsize=10)
        
        pyplot(fig)

# ============================================================
# Tab 4: 規格比較
# ============================================================

with tab4:
    header("cri/oFlex3 規格比較表")
    markdown("與官方數據表的比較")
    
    # 官方數據 (來自搜尋結果)
    official_specs = {
        "參數": ["通道數", "厚度", "材料", "傳輸線類型", "阻抗", "頻率範圍", "彎曲半徑", 
                "熱負載 (4-40K, L=0.4m)", "熱負載 (10-350mK, L=0.2m)", "真空洩漏率"],
        "官方規格": ["8", "0.3 mm", "Polyimide + Ag/NbTi", "Stripline", "50 Ω", "DC - 18 GHz", "5 mm",
                    "< 125 µW/CH", "~ 20 nW/CH", "< 10⁻⁶ mbar·L/s"],
        "模擬參數": [f"{n_channels}", f"{thickness_um} µm", f"Ag/NbTi + Al Shield", "Stripline", "50 Ω", "DC - 18 GHz", "5 mm",
                   "計算中", "計算中", "< 10⁻⁶ mbar·L/s"],
    }
    
    spec_df = DataFrame(official_specs)
    dataframe(spec_df, use_container_width=True, hide_index=True)
    
    markdown("---")
    subheader("與其他低溫電纜的比較")
    
    comparison_data = {
        "電纜類型": ["cri/oFlex3 (Ag)", "cri/oFlex3 (NbTi)", "SC-086/50-SCN-CN", "ULT-01 (SUS304)", "ULT-30 (SUS304)"],
        "熱導率 @ 4K (µW·cm/K)": ["~325", "~0.027*T²", "~210", "~2.39", "~39"],
        "主要應用": ["量子計算 I/O", "量子計算 I/O", "一般低溫 RF", "極低熱傳導", "超薄低溫"],
        "優勢": ["超導 + 低熱載", "超導態極低熱載", "標準化", "最低熱載", "最小尺寸"],
    }
    
    comp_df = DataFrame(comparison_data)
    dataframe(comp_df, use_container_width=True, hide_index=True)
    
    # 熱負載累積圖
    subheader("多通道累積熱負載")
    
    channel_counts = [1, 8, 16, 32, 64, 128, 256]
    total_loads_4K = []
    total_loads_mK = []
    
    # 使用 4K→0.6K 段和 0.6K→100mK 段
    Q_per_ch_4K = TEMP_STAGES["4 K → 0.6 K"]["target_load"]
    Q_per_ch_mK = TEMP_STAGES["0.6 K → 100 mK"]["target_load"]
    
    for n in channel_counts:
        total_loads_4K.append(Q_per_ch_4K * n * 1e6)  # µW
        total_loads_mK.append(Q_per_ch_mK * n * 1e9)  # nW
    
    fig, (ax1, ax2) = subplots(1, 2, figsize=(14, 5))
    
    ax1.plot(channel_counts, total_loads_4K, 'o-', color='#FF6B6B', linewidth=2, markersize=8)
    ax1.set_xlabel('通道數')
    ax1.set_ylabel('總熱負載 (µW)')
    ax1.set_title('4K 段累積熱負載')
    ax1.set_xscale('log')
    ax1.set_yscale('log')
    ax1.grid(True, alpha=0.3)
    
    ax2.plot(channel_counts, total_loads_mK, 'o-', color='#4ECDC4', linewidth=2, markersize=8)
    ax2.set_xlabel('通道數')
    ax2.set_ylabel('總熱負載 (nW)')
    ax2.set_title('mK 段累積熱負載')
    ax2.set_xscale('log')
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3)
    
    tight_layout()
    pyplot(fig)

# ============================================================
# 底部說明
# ============================================================

with sidebar:
    markdown(r"""
### 📖 模型說明

**聲子熱容模型 (Debye Model)**:
- 使用 Debye 近似計算聲子熱容 $C_v = 9Nk_B(T/\theta_D)^3 \int_0^{\theta_D/T} \frac{t^3}{e^t-1}dt$
- 考慮不同材料的 Debye 溫度差異

**邊界散射模型 (Casimir Limit)**:
- 低溫下聲子平均自由程受邊界限制: $\Lambda = L_b$ (邊界長度)
- 對於薄膜/細線結構，邊界散射主導低溫熱傳導
- 熱導率: $\kappa = \frac{1}{3} C_v v_s \Lambda$

**材料特性**:
- **Ag**: 高溫段使用，電子熱導主導，但包含聲子修正
- **NbTi**: 超導態 (T < 10K) 電子熱導被抑制，聲子貢獻相對重要
- **Al Shield**: 提供電磁屏蔽，同時貢獻額外熱負載

**參考來源**:
- Delft Circuits cri/oFlex3 數據表
- Woodcraft et al., "Thermal conductance at millikelvin temperatures of woven ribbon cables" (NbTi 熱導率)
- NIST/文獻中的純銀低溫熱導率數據
""")
    markdown("<div style='text-align: center; color: gray;'> cri/oFlex3 熱負載模擬器 | 基於聲子物理模型 </div>", unsafe_allow_html=True)
# ============================================================
# Delft cri/oFlex3 Cryogenic Transmission Line Thermal Simulator
# Using Phonon Heat Capacity & Boundary Scattering Model
# ============================================================
    title("🔬 Delft cri/oFlex3 低溫傳輸線熱負載模擬器")
    markdown("**基於聲子熱容與邊界散射模型 | Ag/NbTi + Aluminum Shield**")
