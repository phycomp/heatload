from streamlit import caption, columns, expander, info, markdown, metric, number_input, pyplot, radio, set_page_config, sidebar, slider, subheader, tabs, title, warning, checkbox
from matplotlib.pyplot import subplots, tight_layout
from numpy import arange, nan, pi
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import matplotlib.patches as mpatches

# ============================================================
# Page config
# ============================================================
set_page_config(page_title="低溫傳輸線熱負載模擬器 v2", layout="wide")

title("🔬 低溫傳輸線熱負載與長度估算模擬器 v2")
markdown("**修正版**: 正確理解 'per channel' = 整個同軸通道總熱負載，含中心導體 + 外屏蔽層")

awg_diameter = {
    "32 AWG": 0.2032e-3, "34 AWG": 0.1600e-3, "36 AWG": 0.1270e-3,
    "38 AWG": 0.1016e-3, "40 AWG": 0.0787e-3,
}
# ============================================================
# 側邊欄：核心參數設定
# ============================================================
with sidebar:
    subheader("⚙️ 核心參數設定")
    markdown("### 📐 Channel 結構設定")
    markdown("*'per channel' 指的是整個同軸通道，非單根線*")
    channel_type = radio("Channel 結構類型", ["自定義", "標準同軸線 (中心+屏蔽)", "多芯線束 (10根並聯)", "多芯線束 (50根並聯)", "銅編織帶"], index=1, horizontal=True) # Channel 結構選擇
    wire_gauge = radio("中心導體線規 (AWG)", ["36 AWG", "32 AWG", "34 AWG", "38 AWG", "40 AWG"], index=0, horizontal=True) # AWG 選擇 (中心導體)
    diameter = awg_diameter[wire_gauge]
    A_center = pi * (diameter / 2) ** 2

# 根據 channel 類型設定總截面積
if channel_type == "自定義":
    A_multiplier = slider("截面積倍數 (相對單根)", 1.0, 100.0, 5.0, 0.5)
    A_channel = A_center * A_multiplier
elif channel_type == "標準同軸線 (中心+屏蔽)":
    shield_ratio = slider("外屏蔽/中心導體截面積比", 1.0, 10.0, 4.0, 0.5)
    A_channel = A_center * (1 + shield_ratio)
    A_multiplier = 1 + shield_ratio
elif channel_type == "多芯線束 (10根並聯)":
    A_channel = A_center * 10
    A_multiplier = 10
elif channel_type == "多芯線束 (50根並聯)":
    A_channel = A_center * 50
    A_multiplier = 50
elif channel_type == "銅編織帶":
    A_channel = A_center * 20  # 編織帶約20根等效
    A_multiplier = 20

L0 = 2.45e-8  # Lorenz number
with sidebar:
    markdown(f"**中心導體截面積**: {A_center*1e6:.4f} mm²")
    markdown(f"**Channel 總截面積**: {A_channel*1e6:.4f} mm²")
    markdown(f"**相當於**: {A_multiplier:.1f} 根並聯")
    #markdown("---")
    subheader("📊 電阻率設定 (Ω·m)")
    col1, col2 = columns(2)
with col1:
    rho_Ag_300 = number_input("Ag ρ (300K)", value=1.6e-8, format="%.2e", step=1e-9)
    rho_Ag_50 = number_input("Ag ρ (50K)", value=1.5e-8, format="%.2e", step=1e-9)
    rho_Ag_4 = number_input("Ag ρ (4K)", value=1.5e-8, format="%.2e", step=1e-9)
    rho_Ag_06 = number_input("Ag ρ (0.6K)", value=1.5e-8, format="%.2e", step=1e-9)
    rho_Ag_01 = number_input("Ag ρ (0.1K)", value=1.5e-8, format="%.2e", step=1e-9)

with col2:
    rho_NbTi_4 = number_input("NbTi ρ (4K)", value=6.5e-7, format="%.2e", step=1e-8)
    rho_NbTi_06 = number_input("NbTi ρ (0.6K)", value=6.5e-7, format="%.2e", step=1e-8)
    rho_NbTi_01 = number_input("NbTi ρ (0.1K)", value=6.5e-7, format="%.2e", step=1e-8)

# CuNi option
use_CuNi = checkbox("🔁 使用 CuNi (Constantan) 替代 Ag", value=False)
if use_CuNi:
    rho_CuNi = number_input("CuNi ρ (常數)", value=4.9e-7, format="%.2e")

# ============================================================
# Aluminum Shield 參數
# ============================================================
markdown("---")
subheader("🛡️ Aluminum Shield 參數")

shield_enabled = checkbox("啟用 Aluminum Shield 計算", value=True)

if shield_enabled:
    shield_thickness = number_input("Shield 厚度 (mm)", value=0.1, min_value=0.01, max_value=5.0, step=0.01) * 1e-3
    shield_diameter = number_input("Shield 外徑 (mm)", value=2.0, min_value=0.5, max_value=50.0, step=0.1) * 1e-3

    rho_Al_300 = number_input("Al ρ (300K)", value=2.7e-8, format="%.2e")
    rho_Al_50 = number_input("Al ρ (50K)", value=2.5e-8, format="%.2e")
    rho_Al_4 = number_input("Al ρ (4K)", value=2.5e-9, format="%.2e")

    shield_inner = shield_diameter - 2 * shield_thickness
    shield_area = pi * ((shield_diameter/2)**2 - (max(shield_inner/2,0)**2)) if shield_inner > 0 else pi * (shield_diameter/2)**2

    markdown(f"**Shield 截面積**: {shield_area*1e6:.4f} mm²")

    markdown("---")
    subheader("☀️ 熱輻射參數")
    emissivity = number_input("發射率 ε", value=0.03, min_value=0.001, max_value=1.0, step=0.001)
    shield_length = number_input("Shield 段長度 (cm)", value=30.0, min_value=1.0, max_value=100.0, step=1.0) * 1e-2

    sigma = 5.67e-8

# ============================================================
# 數據定義
# ============================================================
segments = [
    {"name": "300 K → 50 K",   "Th": 300,   "Tc": 50,    "Q_Ag": 2.7e-3,  "Q_NbTi": None,    "rho_Ag": rho_Ag_300, "rho_NbTi": None,    "rho_Al": rho_Al_300 if shield_enabled else None},
    {"name": "50 K → 4 K",     "Th": 50,    "Tc": 4,     "Q_Ag": 0.8e-3,  "Q_NbTi": None,    "rho_Ag": rho_Ag_50,  "rho_NbTi": None,    "rho_Al": rho_Al_50 if shield_enabled else None},
    {"name": "4 K → 0.6 K",    "Th": 4,     "Tc": 0.6,   "Q_Ag": 5.4e-6,  "Q_NbTi": 540e-9,  "rho_Ag": rho_Ag_4,   "rho_NbTi": rho_NbTi_4, "rho_Al": rho_Al_4 if shield_enabled else None},
    {"name": "0.6 K → 100 mK", "Th": 0.6,   "Tc": 0.1,   "Q_Ag": 290e-9,  "Q_NbTi": 29e-9,   "rho_Ag": rho_Ag_06,  "rho_NbTi": rho_NbTi_06, "rho_Al": None},
    {"name": "100 mK → 10 mK", "Th": 0.1,   "Tc": 0.01,  "Q_Ag": 5.9e-9,  "Q_NbTi": 590e-12, "rho_Ag": rho_Ag_01,  "rho_NbTi": rho_NbTi_01, "rho_Al": None},
]

# ============================================================
# 計算函數
# ============================================================
def calc_length(Q, Th, Tc, rho, A, L0=2.45e-8):
    if Q is None or rho is None or Q <= 0:
        return None
    return (L0 * A * (Th**2 - Tc**2)) / (2 * Q * rho)

def calc_heatload(L, Th, Tc, rho, A, L0=2.45e-8):
    if L is None or rho is None or L <= 0:
        return None
    return (L0 * A * (Th**2 - Tc**2)) / (2 * L * rho)

def calc_radiation_heatload(Th, Tc, epsilon, area_surface, sigma=5.67e-8):
    return epsilon * sigma * area_surface * (Th**4 - Tc**4)

def calc_shield_conduction(Q_wire, Th, Tc, rho_Al, A_shield, L0=2.45e-8):
    if rho_Al is None or Q_wire is None or Q_wire <= 0:
        return None
    return (L0 * A_shield * (Th**2 - Tc**2)) / (2 * Q_wire * rho_Al)

# ============================================================
# 計算結果
# ============================================================
results = []
for seg in segments:
    r = seg.copy()

    # Ag / CuNi length (使用 Channel 總截面積)
    rho_ag = rho_CuNi if use_CuNi else seg["rho_Ag"]
    r["L_Ag"] = calc_length(seg["Q_Ag"], seg["Th"], seg["Tc"], rho_ag, A_channel)
    r["L_NbTi"] = calc_length(seg["Q_NbTi"], seg["Th"], seg["Tc"], seg["rho_NbTi"], A_channel)

    # 單根線長度 (用於參考)
    r["L_Ag_single"] = calc_length(seg["Q_Ag"], seg["Th"], seg["Tc"], rho_ag, A_center)
    r["L_NbTi_single"] = calc_length(seg["Q_NbTi"], seg["Th"], seg["Tc"], seg["rho_NbTi"], A_center)

    # Aluminum Shield
    if shield_enabled and seg["rho_Al"] is not None:
        if seg["Q_Ag"]:
            r["L_Al_shield"] = calc_shield_conduction(seg["Q_Ag"], seg["Th"], seg["Tc"], seg["rho_Al"], shield_area)
            r["Q_Al_shield"] = seg["Q_Ag"]

        shield_surface_area = pi * shield_diameter * shield_length
        r["Q_radiation"] = calc_radiation_heatload(seg["Th"], seg["Tc"], emissivity, shield_surface_area)
    else:
        r["L_Al_shield"] = None
        r["Q_Al_shield"] = None
        r["Q_radiation"] = None

    results.append(r)

# ============================================================
# Tab 1: 結果表格
# ============================================================
tab1, tab2, tab3, tab4, tab5 = tabs(["📋 計算結果", "📊 視覺化", "🔧 互動調整", "🏗️ 系統示意圖", "🛡️ Shield 分析"])

with tab1:
    subheader("計算結果總表")
    info(f"Channel 結構: {channel_type} | 總截面積: {A_channel*1e6:.3f} mm² | 相當於 {A_multiplier:.1f} 根 {wire_gauge} 並聯")

    material_name = "CuNi" if use_CuNi else "Ag"

    if shield_enabled:
        cols = columns([2, 2, 2, 2, 2, 2, 2])
        headers = ["溫度段", f"{material_name} 熱負載", f"{material_name} 長度", "NbTi 長度", "Al Shield", "輻射熱負載", "單根長度(參考)"]
    else:
        cols = columns([2, 2, 2, 2, 2, 2])
        headers = ["溫度段", f"{material_name} 熱負載", f"{material_name} 長度", "NbTi 長度", "單根長度(參考)", "長度比"]

    for col, h in zip(cols, headers):
        col.markdown(f"**{h}**")

    for r in results:
        if shield_enabled:
            cols = columns([2, 2, 2, 2, 2, 2, 2])
        else:
            cols = columns([2, 2, 2, 2, 2, 2])

        with cols[0]:
            markdown(f"`{r['name']}`")

        with cols[1]:
            if r["Q_Ag"]:
                if r["Q_Ag"] >= 1e-3: markdown(f"{r['Q_Ag']*1e3:.2f} mW")
                elif r["Q_Ag"] >= 1e-6: markdown(f"{r['Q_Ag']*1e6:.2f} µW")
                elif r["Q_Ag"] >= 1e-9: markdown(f"{r['Q_Ag']*1e9:.2f} nW")
                else: markdown(f"{r['Q_Ag']*1e12:.2f} pW")
            else: markdown("—")

        with cols[2]:
            if r["L_Ag"]:
                if r["L_Ag"] >= 1: markdown(f"**{r['L_Ag']:.2f} m**")
                elif r["L_Ag"] >= 0.01: markdown(f"**{r['L_Ag']*100:.1f} cm**")
                else: markdown(f"**{r['L_Ag']*1000:.1f} mm**")
            else: markdown("—")

        with cols[3]:
            if r["L_NbTi"]:
                if r["L_NbTi"] >= 1: markdown(f"**{r['L_NbTi']:.2f} m**")
                elif r["L_NbTi"] >= 0.01: markdown(f"**{r['L_NbTi']*100:.1f} cm**")
                else: markdown(f"**{r['L_NbTi']*1000:.1f} mm**")
            else: markdown("—")

        if shield_enabled:
            with cols[4]:
                if r["L_Al_shield"]:
                    if r["L_Al_shield"] >= 1: markdown(f"{r['L_Al_shield']:.2f} m")
                    elif r["L_Al_shield"] >= 0.01: markdown(f"{r['L_Al_shield']*100:.1f} cm")
                    else: markdown(f"{r['L_Al_shield']*1000:.1f} mm")
                else: markdown("—")

            with cols[5]:
                if r["Q_radiation"]:
                    if r["Q_radiation"] >= 1e-3: markdown(f"{r['Q_radiation']*1e3:.3f} mW")
                    elif r["Q_radiation"] >= 1e-6: markdown(f"{r['Q_radiation']*1e6:.3f} µW")
                    elif r["Q_radiation"] >= 1e-9: markdown(f"{r['Q_radiation']*1e9:.3f} nW")
                    else: markdown(f"{r['Q_radiation']*1e12:.3f} pW")
                else: markdown("—")

            with cols[6]:
                if r["L_Ag_single"]:
                    if r["L_Ag_single"] >= 0.01: markdown(f"{r['L_Ag_single']*100:.1f} cm")
                    else: markdown(f"{r['L_Ag_single']*1000:.1f} mm")
                else: markdown("—")
        else:
            with cols[4]:
                if r["L_Ag_single"]:
                    if r["L_Ag_single"] >= 0.01: markdown(f"{r['L_Ag_single']*100:.1f} cm")
                    else: markdown(f"{r['L_Ag_single']*1000:.1f} mm")
                else: markdown("—")

            with cols[5]:
                if r["L_Ag"] and r["L_NbTi"] and r["L_NbTi"] > 0:
                    ratio = r["L_Ag"] / r["L_NbTi"]
                    markdown(f"{ratio:.1f}×")
                else: markdown("—")

# ============================================================
# Tab 2: 視覺化
# ============================================================
with tab2:
    subheader("熱負載與長度視覺化")

    fig, axes = subplots(2, 3, figsize=(18, 10))

    seg_names = [r["name"] for r in results]
    x_pos = arange(len(seg_names))
    width = 0.35

    # 1. 熱負載
    ax1 = axes[0, 0]
    Q_Ag_display = []
    for r in results:
        if r["Q_Ag"] is None: Q_Ag_display.append(0)
        elif r["Q_Ag"] >= 1e-3: Q_Ag_display.append(r["Q_Ag"]*1e3)
        elif r["Q_Ag"] >= 1e-6: Q_Ag_display.append(r["Q_Ag"]*1e6)
        elif r["Q_Ag"] >= 1e-9: Q_Ag_display.append(r["Q_Ag"]*1e9)
        else: Q_Ag_display.append(r["Q_Ag"]*1e12)

    ax1.bar(x_pos - width/2, [q if q else nan for q in Q_Ag_display], width, label=material_name, color='#D4A843', alpha=0.85)
    ax1.bar(x_pos + width/2, [r["Q_NbTi"]*1e9 if r["Q_NbTi"] else nan for r in results], width, label='NbTi', color='#4A90A4', alpha=0.85)
    ax1.set_ylabel("熱負載")
    ax1.set_title("各溫度段熱負載")
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(seg_names, rotation=15, ha='right')
    ax1.legend()
    ax1.set_yscale('log')
    ax1.grid(True, alpha=0.3)

    # 2. Channel 長度
    ax2 = axes[0, 1]
    L_Ag_m = [r["L_Ag"] if r["L_Ag"] else 0 for r in results]
    L_NbTi_m = [r["L_NbTi"] if r["L_NbTi"] else 0 for r in results]
    ax2.bar(x_pos - width/2, [l if l else nan for l in L_Ag_m], width, label=material_name, color='#D4A843', alpha=0.85)
    ax2.bar(x_pos + width/2, [l if l else nan for l in L_NbTi_m], width, label='NbTi', color='#4A90A4', alpha=0.85)
    ax2.set_ylabel("長度 (m)")
    ax2.set_title("Channel 估算長度")
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(seg_names, rotation=15, ha='right')
    ax2.legend()
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3)

    # 3. 單根線長度對比
    ax3 = axes[0, 2]
    L_Ag_single_cm = [r["L_Ag_single"]*100 if r["L_Ag_single"] else 0 for r in results]
    L_Ag_channel_cm = [r["L_Ag"]*100 if r["L_Ag"] else 0 for r in results]
    ax3.bar(x_pos - width/2, [l if l else nan for l in L_Ag_single_cm], width, label='單根', color='#FF9999', alpha=0.85)
    ax3.bar(x_pos + width/2, [l if l else nan for l in L_Ag_channel_cm], width, label='Channel', color='#D4A843', alpha=0.85)
    ax3.set_ylabel("長度 (cm)")
    ax3.set_title("單根 vs Channel 長度對比")
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(seg_names, rotation=15, ha='right')
    ax3.legend()
    ax3.set_yscale('log')
    ax3.grid(True, alpha=0.3)

    # 4. 溫度階梯
    ax4 = axes[1, 0]
    temps = [300, 50, 4, 0.6, 0.1, 0.01]
    temp_labels = ['300K', '50K', '4K', '0.6K', '100mK', '10mK']
    for i, (t, tl) in enumerate(zip(temps, temp_labels)):
        ax4.axhline(y=t, color='gray', linestyle='--', alpha=0.3)
        ax4.text(0.02, t*1.3, tl, fontsize=9, va='bottom')
    for i, r in enumerate(results):
        if r["Q_Ag"]: ax4.annotate('', xy=(0.3, r["Tc"]), xytext=(0.3, r["Th"]), arrowprops=dict(arrowstyle='->', color='#D4A843', lw=2))
        if r["Q_NbTi"]: ax4.annotate('', xy=(0.7, r["Tc"]), xytext=(0.7, r["Th"]), arrowprops=dict(arrowstyle='->', color='#4A90A4', lw=2))
    ax4.set_xlim(0, 1)
    ax4.set_ylim(0.005, 500)
    ax4.set_yscale('log')
    ax4.set_title("溫度階梯與熱流方向")
    ax4.set_xticks([])
    ax4.set_ylabel("溫度 (K)")

    # 5. 累積長度
    ax5 = axes[1, 1]
    cumsum_Ag = []
    cumsum_NbTi = []
    cum_Ag = 0
    cum_NbTi = 0
    for r in results:
        if r["L_Ag"]: cum_Ag += r["L_Ag"]
        if r["L_NbTi"]: cum_NbTi += r["L_NbTi"]
        cumsum_Ag.append(cum_Ag)
        cumsum_NbTi.append(cum_NbTi)

    ax5.plot(seg_names, cumsum_Ag, 'o-', color='#D4A843', linewidth=2, markersize=8, label=f'{material_name} 累積')
    ax5.plot(seg_names, cumsum_NbTi, 's-', color='#4A90A4', linewidth=2, markersize=8, label='NbTi 累積')
    ax5.fill_between(seg_names, cumsum_Ag, alpha=0.2, color='#D4A843')
    ax5.fill_between(seg_names, cumsum_NbTi, alpha=0.2, color='#4A90A4')
    ax5.set_ylabel("累積長度 (m)")
    ax5.set_title("傳輸線累積長度")
    ax5.set_xticklabels(seg_names, rotation=15, ha='right')
    ax5.legend()
    ax5.grid(True, alpha=0.3)

    # 6. Shield 長度
    ax6 = axes[1, 2]
    if shield_enabled:
        L_Al_m = [r["L_Al_shield"] if r["L_Al_shield"] else 0 for r in results]
        ax6.bar(x_pos, [l if l else nan for l in L_Al_m], width*1.5, label='Al Shield', color='#C0C0C0', alpha=0.85)
        ax6.set_ylabel("長度 (m)")
        ax6.set_title("Al Shield 估算長度")
    else:
        ax6.text(0.5, 0.5, "Shield 未啟用", ha='center', va='center', transform=ax6.transAxes, fontsize=14)
    ax6.set_xticks(x_pos)
    ax6.set_xticklabels(seg_names, rotation=15, ha='right')
    ax6.legend()
    ax6.set_yscale('log')
    ax6.grid(True, alpha=0.3)

    tight_layout()
    pyplot(fig)

    markdown("---")
    col1, col2, col3 = columns(3)
    with col1: metric(f"{material_name} 總長度", f"{cumsum_Ag[-1]:.2f} m")
    with col2: metric("NbTi 總長度", f"{cumsum_NbTi[-1]:.3f} m")
    if shield_enabled:
        with col3:
            total_Al = sum([r["L_Al_shield"] for r in results if r["L_Al_shield"]])
            metric("Al Shield 總長度", f"{total_Al:.2f} m")

# ============================================================
# Tab 3: 互動調整
# ============================================================
with tab3:
    subheader("🔧 互動長度調整與熱負載反算")

    selected_seg = radio("選擇溫度段", [r["name"] for r in results], horizontal=True)
    seg_idx = [r["name"] for r in results].index(selected_seg)
    seg = results[seg_idx]

    col1, col2 = columns(2)

    with col1:
        markdown(f"### {material_name} Channel")
        if seg["L_Ag"]:
            max_val = max(seg["L_Ag"]*3, 2.0)
            L_Ag_input = slider(f"{material_name} 長度 (m)", min_value=0.01, max_value=max_val, value=seg["L_Ag"], step=0.01, key=f"ag_slider_{seg_idx}")

            rho_ag = rho_CuNi if use_CuNi else seg["rho_Ag"]
            Q_calc_Ag = calc_heatload(L_Ag_input, seg["Th"], seg["Tc"], rho_ag, A_channel)

            markdown(f"**原始熱負載**: {seg['Q_Ag']*1e3:.3f} mW" if seg['Q_Ag'] and seg['Q_Ag'] >= 1e-3 else f"**原始熱負載**: {seg['Q_Ag']*1e6:.3f} µW")

            if Q_calc_Ag >= 1e-3: markdown(f"**調整後**: {Q_calc_Ag*1e3:.4f} mW")
            elif Q_calc_Ag >= 1e-6: markdown(f"**調整後**: {Q_calc_Ag*1e6:.4f} µW")
            elif Q_calc_Ag >= 1e-9: markdown(f"**調整後**: {Q_calc_Ag*1e9:.4f} nW")
            else: markdown(f"**調整後**: {Q_calc_Ag*1e12:.4f} pW")

            if seg["Q_Ag"]:
                pct = (Q_calc_Ag / seg["Q_Ag"] - 1) * 100
                markdown(f"變化: **{pct:+.1f}%**")

    with col2:
        markdown("### NbTi Channel")
        if seg["L_NbTi"]:
            max_val = max(seg["L_NbTi"]*3, 0.5)
            L_NbTi_input = slider("NbTi 長度 (m)", min_value=0.001, max_value=max_val, value=seg["L_NbTi"], step=0.001, key=f"nbti_slider_{seg_idx}")

            Q_calc_NbTi = calc_heatload(L_NbTi_input, seg["Th"], seg["Tc"], seg["rho_NbTi"], A_channel)

            if seg["Q_NbTi"] >= 1e-6: markdown(f"**原始**: {seg['Q_NbTi']*1e6:.3f} µW")
            elif seg["Q_NbTi"] >= 1e-9: markdown(f"**原始**: {seg['Q_NbTi']*1e9:.3f} nW")
            else: markdown(f"**原始**: {seg['Q_NbTi']*1e12:.3f} pW")

            if Q_calc_NbTi >= 1e-6: markdown(f"**調整後**: {Q_calc_NbTi*1e6:.4f} µW")
            elif Q_calc_NbTi >= 1e-9: markdown(f"**調整後**: {Q_calc_NbTi*1e9:.4f} nW")
            else: markdown(f"**調整後**: {Q_calc_NbTi*1e12:.4f} pW")

            if seg["Q_NbTi"]:
                pct = (Q_calc_NbTi / seg["Q_NbTi"] - 1) * 100
                markdown(f"變化: **{pct:+.1f}%**")

# ============================================================
# Tab 4: 系統示意圖
# ============================================================
with tab4:
    subheader("🏗️ 低溫傳輸線系統示意圖")

    fig2, ax = subplots(figsize=(12, 16))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 18)
    ax.set_aspect('equal')
    ax.axis('off')

    stages = [
        (17.5, "300 K", "#FF6B6B", 2.7e-3, None),
        (14.0, "50 K", "#4ECDC4", 0.8e-3, None),
        (10.5, "4 K", "#45B7D1", 5.4e-6, 540e-9),
        (7.0, "0.6 K", "#96CEB4", 290e-9, 29e-9),
        (3.5, "100 mK", "#DDA0DD", 5.9e-9, 590e-12),
        (0.5, "10 mK", "#B0C4DE", None, None),
    ]

    for y, label, color, q_ag, q_nbti in stages:
        rect = FancyBboxPatch((0.5, y-0.3), 11, 0.6, boxstyle="round,pad=0.05", facecolor=color, edgecolor='black', alpha=0.7)
        ax.add_patch(rect)
        ax.text(6, y, label, ha='center', va='center', fontsize=13, fontweight='bold')

        if q_ag:
            unit = "mW" if q_ag >= 1e-3 else "µW" if q_ag >= 1e-6 else "nW"
            val = q_ag*1e3 if q_ag >= 1e-3 else q_ag*1e6 if q_ag >= 1e-6 else q_ag*1e9
            ax.text(10.5, y+0.1, f"Ag: {val:.1f} {unit}", ha='right', va='center', fontsize=8, color='#D4A843')

        if q_nbti:
            unit = "µW" if q_nbti >= 1e-6 else "nW" if q_nbti >= 1e-9 else "pW"
            val = q_nbti*1e6 if q_nbti >= 1e-6 else q_nbti*1e9 if q_nbti >= 1e-9 else q_nbti*1e12
            ax.text(10.5, y-0.15, f"NbTi: {val:.1f} {unit}", ha='right', va='center', fontsize=8, color='#4A90A4')

    for i in range(len(stages)-1):
        y1 = stages[i][0] - 0.3
        y2 = stages[i+1][0] + 0.3
        mid_y = (y1 + y2) / 2

        if results[i]["L_Ag"]:
            L_m = results[i]["L_Ag"]
            ax.plot([7.5, 7.5], [y1, y2], color='#D4A843', linewidth=5, solid_capstyle='round')
            ax.text(7.8, mid_y, f"{L_m:.2f} m", ha='left', va='center', fontsize=9, color='#D4A843', rotation=90 if abs(y1-y2) > 2 else 0)

        if results[i]["L_NbTi"]:
            L_m = results[i]["L_NbTi"]
            ax.plot([4.5, 4.5], [y1, y2], color='#4A90A4', linewidth=5, solid_capstyle='round')
            ax.text(4.2, mid_y, f"{L_m:.3f} m", ha='right', va='center', fontsize=9, color='#4A90A4', rotation=90 if abs(y1-y2) > 2 else 0)

        if shield_enabled and results[i]["L_Al_shield"]:
            L_Al = results[i]["L_Al_shield"]
            ax.plot([1.5, 1.5], [y1, y2], color='#C0C0C0', linewidth=7, solid_capstyle='round', linestyle='--')
            ax.text(1.2, mid_y, f"Al: {L_Al:.2f}m", ha='right', va='center', fontsize=8, color='#888888', rotation=90 if abs(y1-y2) > 2 else 0)

    for i in range(len(stages)-1):
        y1 = stages[i][0] - 0.3
        y2 = stages[i+1][0] + 0.3
        ax.annotate('', xy=(6, y2+0.1), xytext=(6, y1-0.1), arrowprops=dict(arrowstyle='->', color='red', lw=1.5, alpha=0.5))

    legend_patches = [mpatches.Patch(color='#D4A843', label=f'{material_name} Channel'),
                      mpatches.Patch(color='#4A90A4', label='NbTi Channel')]
    if shield_enabled: legend_patches.append(mpatches.Patch(color='#C0C0C0', label='Al Shield'))
    ax.legend(handles=legend_patches, loc='upper left', fontsize=10)
    ax.set_title("低溫傳輸線系統結構示意圖 (修正版)", fontsize=15, fontweight='bold', pad=20)

    pyplot(fig2)

# ============================================================
# Tab 5: Shield 分析
# ============================================================
with tab5:
    subheader("🛡️ Aluminum Shield 詳細分析")
    if not shield_enabled:
        warning("請在側邊欄啟用 Aluminum Shield 計算")
    else:
        markdown("""
        ### Aluminum Shield 作用原理
        1. **熱傳導分流**: 與信號線並聯，提供額外熱傳導路徑
        2. **熱輻射屏蔽**: 降低層間輻射熱負載  
        3. **電磁屏蔽**: 減少外部 EMI 干擾
        """)

        markdown("### Shield 熱傳導分析")
        shield_cols = columns([2, 2, 2, 2, 2])
        for col, h in zip(shield_cols, ["溫度段", "Wire Q", "Shield 長度", "Shield Q", "輻射 Q"]):
            col.markdown(f"**{h}**")

        for r in results:
            if r["rho_Al"] is not None:
                shield_cols = columns([2, 2, 2, 2, 2])
                with shield_cols[0]: markdown(f"`{r['name']}`")
                with shield_cols[1]:
                    if r["Q_Ag"] >= 1e-3: markdown(f"{r['Q_Ag']*1e3:.2f} mW")
                    elif r["Q_Ag"] >= 1e-6: markdown(f"{r['Q_Ag']*1e6:.2f} µW")
                    else: markdown(f"{r['Q_Ag']*1e9:.2f} nW")
                with shield_cols[2]:
                    if r["L_Al_shield"]:
                        if r["L_Al_shield"] >= 1: markdown(f"**{r['L_Al_shield']:.2f} m**")
                        else: markdown(f"**{r['L_Al_shield']*100:.1f} cm**")
                    else: markdown("—")
                with shield_cols[3]:
                    if r["Q_Ag"]: markdown(f"≈ {r['Q_Ag']*1e3:.2f} mW" if r['Q_Ag'] >= 1e-3 else f"≈ {r['Q_Ag']*1e6:.2f} µW")
                    else: markdown("—")
                with shield_cols[4]:
                    if r["Q_radiation"]:
                        if r["Q_radiation"] >= 1e-3: markdown(f"{r['Q_radiation']*1e3:.3f} mW")
                        elif r["Q_radiation"] >= 1e-6: markdown(f"{r['Q_radiation']*1e6:.3f} µW")
                        else: markdown(f"{r['Q_radiation']*1e9:.3f} nW")
                    else: markdown("—")

# ============================================================
# 底部說明
# ============================================================
markdown("---")
with expander("📐 計算公式與修正說明"):
    markdown(r"""
    ### 重要修正說明

    **v1 版問題**: 使用單根 AWG36 截面積計算，回推長度僅數公分，與實際不符。

    **v2 版修正**: 
    - 正確理解 "per channel" = 整個同軸通道的總熱負載
    - Channel 包含：中心導體 + 外屏蔽層 + 介電層
    - 總有效截面積約為單根線的 3-20 倍

    ### Wiedemann-Franz 定律

    $$\lambda = \frac{L_0 \cdot T}{\rho(T)}$$

    ### 反推長度

    $$L = \frac{L_0 \cdot A_{channel} \cdot (T_h^2 - T_c^2)}{2 \cdot Q \cdot \rho}$$

    其中 $A_{channel}$ 為整個通道的有效導熱截面積，非單根線截面積。

    ### 典型 Channel 結構參考

    | 結構類型 | 等效並聯數 | 總截面積 (mm²) |
    |----------|-----------|----------------|
    | 單根 AWG36 | 1 | 0.0127 |
    | 標準同軸線 | ~5 | ~0.06 |
    | 多芯線束 (10根) | 10 | ~0.13 |
    | 銅編織帶 | ~20 | ~0.25 |
    """)

markdown("---")
caption("v2 修正版: 正確處理 'per channel' = 整個同軸通道總熱負載。模型基於 Wiedemann-Franz 定律，假設電阻率在每個溫度段內為常數。")
