from streamlit import caption, columns, expander, info, markdown, metric, number_input, pyplot, radio, set_page_config, sidebar, slider, subheader, tabs, title, checkbox
from matplotlib.pyplot import subplots, tight_layout
from numpy import arange, nan, pi as π
#import streamlit as st
#import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import matplotlib.patches as mpatches
from fontUtil2 import 配置中文
配置中文()

set_page_config(page_title="低溫傳輸線熱負載模擬器", layout="wide")
awg_diameter = {
    "32 AWG": 0.2032e-3,   # mm -> m
    "34 AWG": 0.1600e-3,
    "36 AWG": 0.1270e-3,
    "38 AWG": 0.1016e-3,
    "40 AWG": 0.0787e-3,
} # 直徑 AWG to diameter mapping

with sidebar: # 側邊欄：材料參數設定
  subheader("⚙️ 材料參數設定")
  wire_gauge = radio("線規 (AWG)", ["36 AWG", "32 AWG", "34 AWG", "38 AWG", "40 AWG"], index=0, horizontal=True)

  直徑 = awg_diameter[wire_gauge]
  area = π * (直徑 / 2) ** 2
  markdown(f"**線徑**: {直徑*1e3:.3f} mm")
  markdown(f"**截面積**: {area*1e8:.3f} × 10⁻⁸ m²")
  L0 = 2.45e-8  # Lorenz number W·Ω/K²
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

use_CuNi = checkbox("🔁 使用 CuNi (Constantan) 替代 Ag", value=False) # CuNi option
if use_CuNi:
    rho_CuNi = number_input("CuNi ρ (常數)", value=4.9e-7, format="%.2e")
    info("CuNi 電阻率幾乎不隨溫度變化")

# ───────────────────────────────────────────────
# 數據定義
# ───────────────────────────────────────────────
segments = [
    {"name": "300 K → 50 K",   "Th": 300,   "Tc": 50,    "Q_Ag": 2.7e-3,  "Q_NbTi": None,    "rho_Ag": rho_Ag_300, "rho_NbTi": None},
    {"name": "50 K → 4 K",     "Th": 50,    "Tc": 4,     "Q_Ag": 0.8e-3,  "Q_NbTi": None,    "rho_Ag": rho_Ag_50,  "rho_NbTi": None},
    {"name": "4 K → 0.6 K",    "Th": 4,     "Tc": 0.6,   "Q_Ag": 5.4e-6,  "Q_NbTi": 540e-9,  "rho_Ag": rho_Ag_4,   "rho_NbTi": rho_NbTi_4},
    {"name": "0.6 K → 100 mK", "Th": 0.6,   "Tc": 0.1,   "Q_Ag": 290e-9,  "Q_NbTi": 29e-9,   "rho_Ag": rho_Ag_06,  "rho_NbTi": rho_NbTi_06},
    {"name": "100 mK → 10 mK", "Th": 0.1,   "Tc": 0.01,  "Q_Ag": 5.9e-9,  "Q_NbTi": 590e-12, "rho_Ag": rho_Ag_01,  "rho_NbTi": rho_NbTi_01},
]

# ───────────────────────────────────────────────
# 計算函數
# ───────────────────────────────────────────────
def calc_length(Q, Th, Tc, rho, A, L0=2.45e-8):
    """根據熱負載反推長度: L = L0 * A * (Th² - Tc²) / (2 * Q * rho)"""
    if Q is None or rho is None or Q <= 0:
        return None
    return (L0 * A * (Th**2 - Tc**2)) / (2 * Q * rho)

def calc_heatload(L, Th, Tc, rho, A, L0=2.45e-8):
    """根據長度計算熱負載: Q = L0 * A * (Th² - Tc²) / (2 * L * rho)"""
    if L is None or rho is None or L <= 0:
        return None
    return (L0 * A * (Th**2 - Tc**2)) / (2 * L * rho)

# ───────────────────────────────────────────────
# 計算結果
# ───────────────────────────────────────────────
results = []
for seg in segments:
    r = seg.copy()
    
    # Ag / CuNi length
    rho_ag = rho_CuNi if use_CuNi else seg["rho_Ag"]
    r["L_Ag"] = calc_length(seg["Q_Ag"], seg["Th"], seg["Tc"], rho_ag, area)
    r["L_NbTi"] = calc_length(seg["Q_NbTi"], seg["Th"], seg["Tc"], seg["rho_NbTi"], area)
    
    # 反向驗證
    if r["L_Ag"]:
        r["Q_check_Ag"] = calc_heatload(r["L_Ag"], seg["Th"], seg["Tc"], rho_ag, area)
    if r["L_NbTi"]:
        r["Q_check_NbTi"] = calc_heatload(r["L_NbTi"], seg["Th"], seg["Tc"], seg["rho_NbTi"], area)
    
    results.append(r)

# ───────────────────────────────────────────────
# Tab 1: 結果表格
# ───────────────────────────────────────────────
tab1, tab2, tab3, tab4 = tabs(["📋 計算結果", "📊 視覺化", "🔧 互動調整", "🏗️ 系統示意圖"])

with tab1:
    subheader("計算結果總表")
    
    material_name = "CuNi" if use_CuNi else "Ag"
    
    cols = columns([2, 2, 2, 2, 2, 2])
    headers = ["溫度段", f"{material_name} 熱負載", f"{material_name} 長度", "NbTi 熱負載", "NbTi 長度", "長度比 (Ag/NbTi)"]
    for col, h in zip(cols, headers):
        col.markdown(f"**{h}**")
    
    for r in results:
        cols = columns([2, 2, 2, 2, 2, 2])
        
        with cols[0]:
            markdown(f"`{r['name']}`")
        
        with cols[1]:
            if r["Q_Ag"]:
                if r["Q_Ag"] >= 1e-3:
                    markdown(f"{r['Q_Ag']*1e3:.2f} mW")
                elif r["Q_Ag"] >= 1e-6:
                    markdown(f"{r['Q_Ag']*1e6:.2f} µW")
                elif r["Q_Ag"] >= 1e-9:
                    markdown(f"{r['Q_Ag']*1e9:.2f} nW")
                else:
                    markdown(f"{r['Q_Ag']*1e12:.2f} pW")
            else:
                markdown("—")
        
        with cols[2]:
            if r["L_Ag"]:
                if r["L_Ag"] >= 0.01:
                    markdown(f"**{r['L_Ag']*100:.2f} cm**")
                else:
                    markdown(f"**{r['L_Ag']*1000:.2f} mm**")
            else:
                markdown("—")
        
        with cols[3]:
            if r["Q_NbTi"]:
                if r["Q_NbTi"] >= 1e-6:
                    markdown(f"{r['Q_NbTi']*1e6:.2f} µW")
                elif r["Q_NbTi"] >= 1e-9:
                    markdown(f"{r['Q_NbTi']*1e9:.2f} nW")
                else:
                    markdown(f"{r['Q_NbTi']*1e12:.2f} pW")
            else:
                markdown("—")
        
        with cols[4]:
            if r["L_NbTi"]:
                if r["L_NbTi"] >= 0.01:
                    markdown(f"**{r['L_NbTi']*100:.2f} cm**")
                else:
                    markdown(f"**{r['L_NbTi']*1000:.2f} mm**")
            else:
                markdown("—")
        
        with cols[5]:
            if r["L_Ag"] and r["L_NbTi"] and r["L_NbTi"] > 0:
                ratio = r["L_Ag"] / r["L_NbTi"]
                markdown(f"{ratio:.1f}×")
            else:
                markdown("—")

# ───────────────────────────────────────────────
# Tab 2: 視覺化
# ───────────────────────────────────────────────
with tab2:
    subheader("熱負載與長度視覺化")
    
    fig, axes = subplots(2, 2, figsize=(14, 10))
    
    # 準備數據
    seg_names = [r["name"] for r in results]
    x_pos = arange(len(seg_names))
    
    # 1. 熱負載對數圖
    ax1 = axes[0, 0]
    Q_Ag_vals = [r["Q_Ag"]*1e12 if r["Q_Ag"] else 0 for r in results]  # pW
    Q_NbTi_vals = [r["Q_NbTi"]*1e12 if r["Q_NbTi"] else 0 for r in results]
    
    # 轉換到合適單位顯示
    Q_Ag_display = []
    for r in results:
        if r["Q_Ag"] is None:
            Q_Ag_display.append(0)
        elif r["Q_Ag"] >= 1e-3:
            Q_Ag_display.append(r["Q_Ag"]*1e3)  # mW
        elif r["Q_Ag"] >= 1e-6:
            Q_Ag_display.append(r["Q_Ag"]*1e6)  # µW
        elif r["Q_Ag"] >= 1e-9:
            Q_Ag_display.append(r["Q_Ag"]*1e9)  # nW
        else:
            Q_Ag_display.append(r["Q_Ag"]*1e12) # pW
    
    width = 0.35
    bars1 = ax1.bar(x_pos - width/2, [q if q else nan for q in Q_Ag_display], width, 
                     label=f'{material_name}', color='#D4A843', alpha=0.85)
    bars2 = ax1.bar(x_pos + width/2, [r["Q_NbTi"]*1e9 if r["Q_NbTi"] else nan for r in results], width,
                     label='NbTi', color='#4A90A4', alpha=0.85)
    
    ax1.set_ylabel("熱負載 (nW / µW / mW)")
    ax1.set_title("各溫度段熱負載 (原始值)")
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(seg_names, rotation=15, ha='right')
    ax1.legend()
    ax1.set_yscale('log')
    ax1.grid(True, alpha=0.3)
    
    # 2. 長度比較
    ax2 = axes[0, 1]
    L_Ag_cm = [r["L_Ag"]*100 if r["L_Ag"] else 0 for r in results]
    L_NbTi_cm = [r["L_NbTi"]*100 if r["L_NbTi"] else 0 for r in results]
    
    bars3 = ax2.bar(x_pos - width/2, [l if l else nan for l in L_Ag_cm], width,
                     label=f'{material_name}', color='#D4A843', alpha=0.85)
    bars4 = ax2.bar(x_pos + width/2, [l if l else nan for l in L_NbTi_cm], width,
                     label='NbTi', color='#4A90A4', alpha=0.85)
    
    ax2.set_ylabel("長度 (cm)")
    ax2.set_title("估算傳輸線長度")
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(seg_names, rotation=15, ha='right')
    ax2.legend()
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3)
    
    # 3. 溫度-熱負載瀑布圖
    ax3 = axes[1, 0]
    temps = [300, 50, 4, 0.6, 0.1, 0.01]
    temp_labels = ['300K', '50K', '4K', '0.6K', '100mK', '10mK']
    
    # 繪製溫度階梯
    for i, (t, tl) in enumerate(zip(temps, temp_labels)):
        ax3.axhline(y=t, color='gray', linestyle='--', alpha=0.3)
        ax3.text(0.02, t*1.3, tl, fontsize=9, va='bottom')
    
    # 繪製熱流
    colors_flow = ['#D4A843', '#D4A843', '#D4A843', '#4A90A4', '#4A90A4']
    y_positions = [300, 50, 4, 0.6, 0.1]
    
    for i, r in enumerate(results):
        y = (r["Th"] + r["Tc"]) / 2
        if r["Q_Ag"]:
            ax3.annotate('', xy=(0.3, r["Tc"]), xytext=(0.3, r["Th"]),
                        arrowprops=dict(arrowstyle='->', color='#D4A843', lw=2))
        if r["Q_NbTi"]:
            ax3.annotate('', xy=(0.7, r["Tc"]), xytext=(0.7, r["Th"]),
                        arrowprops=dict(arrowstyle='->', color='#4A90A4', lw=2))
    
    ax3.set_xlim(0, 1)
    ax3.set_ylim(0.005, 500)
    ax3.set_yscale('log')
    ax3.set_title("溫度階梯與熱流方向")
    ax3.set_xticks([])
    ax3.set_ylabel("溫度 (K)")
    
    # 4. 長度累積圖
    ax4 = axes[1, 1]
    
    # 計算累積長度
    cumsum_Ag = []
    cumsum_NbTi = []
    cum_Ag = 0
    cum_NbTi = 0
    
    for r in results:
        if r["L_Ag"]:
            cum_Ag += r["L_Ag"]
        if r["L_NbTi"]:
            cum_NbTi += r["L_NbTi"]
        cumsum_Ag.append(cum_Ag * 100)  # cm
        cumsum_NbTi.append(cum_NbTi * 100)
    
    ax4.plot(seg_names, cumsum_Ag, 'o-', color='#D4A843', linewidth=2, markersize=8, label=f'{material_name} 累積')
    ax4.plot(seg_names, cumsum_NbTi, 's-', color='#4A90A4', linewidth=2, markersize=8, label='NbTi 累積')
    ax4.fill_between(seg_names, cumsum_Ag, alpha=0.2, color='#D4A843')
    ax4.fill_between(seg_names, cumsum_NbTi, alpha=0.2, color='#4A90A4')
    ax4.set_ylabel("累積長度 (cm)")
    ax4.set_title("傳輸線累積長度")
    ax4.set_xticklabels(seg_names, rotation=15, ha='right')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    tight_layout()
    pyplot(fig)
    
    # 顯示總長度
    markdown("---")
    col1, col2 = columns(2)
    with col1:
        metric(f"{material_name} 總長度", f"{cumsum_Ag[-1]:.2f} cm")
    with col2:
        metric("NbTi 總長度", f"{cumsum_NbTi[-1]:.2f} cm")

# ───────────────────────────────────────────────
# Tab 3: 互動調整
# ───────────────────────────────────────────────
with tab3:
    subheader("🔧 互動長度調整與熱負載反算")
    
    selected_seg = radio("選擇溫度段", [r["name"] for r in results], horizontal=True)
    seg_idx = [r["name"] for r in results].index(selected_seg)
    seg = results[seg_idx]
    
    col1, col2 = columns(2)
    
    with col1:
        markdown(f"### {material_name} 線")
        if seg["L_Ag"]:
            L_Ag_input = slider(
                f"{material_name} 長度 (cm)", 
                min_value=0.01, 
                max_value=max(seg["L_Ag"]*300, 5.0), 
                value=seg["L_Ag"]*100,
                step=0.01,
                key=f"ag_slider_{seg_idx}"
            )
            
            rho_ag = rho_CuNi if use_CuNi else seg["rho_Ag"]
            Q_calc_Ag = calc_heatload(L_Ag_input/100, seg["Th"], seg["Tc"], rho_ag, area)
            
            markdown(f"**原始熱負載**: {seg['Q_Ag']*1e6:.3f} µW" if seg['Q_Ag'] and seg['Q_Ag'] < 1e-3 else f"**原始熱負載**: {seg['Q_Ag']*1e3:.3f} mW")
            
            if Q_calc_Ag >= 1e-3:
                markdown(f"**調整後熱負載**: {Q_calc_Ag*1e3:.4f} mW")
            elif Q_calc_Ag >= 1e-6:
                markdown(f"**調整後熱負載**: {Q_calc_Ag*1e6:.4f} µW")
            elif Q_calc_Ag >= 1e-9:
                markdown(f"**調整後熱負載**: {Q_calc_Ag*1e9:.4f} nW")
            else:
                markdown(f"**調整後熱負載**: {Q_calc_Ag*1e12:.4f} pW")
            
            # 顯示變化百分比
            if seg["Q_Ag"]:
                pct = (Q_calc_Ag / seg["Q_Ag"] - 1) * 100
                markdown(f"變化: **{pct:+.1f}%**")
        else:
            info("此溫度段無 Ag 線")
    
    with col2:
        markdown("### NbTi 線")
        if seg["L_NbTi"]:
            L_NbTi_input = slider(
                "NbTi 長度 (mm)", 
                min_value=0.1, 
                max_value=max(seg["L_NbTi"]*3000, 50.0), 
                value=seg["L_NbTi"]*1000,
                step=0.1,
                key=f"nbti_slider_{seg_idx}"
            )
            
            Q_calc_NbTi = calc_heatload(L_NbTi_input/1000, seg["Th"], seg["Tc"], seg["rho_NbTi"], area)
            
            if seg["Q_NbTi"] >= 1e-6:
                markdown(f"**原始熱負載**: {seg['Q_NbTi']*1e6:.3f} µW")
            elif seg["Q_NbTi"] >= 1e-9:
                markdown(f"**原始熱負載**: {seg['Q_NbTi']*1e9:.3f} nW")
            else:
                markdown(f"**原始熱負載**: {seg['Q_NbTi']*1e12:.3f} pW")
            
            if Q_calc_NbTi >= 1e-6:
                markdown(f"**調整後熱負載**: {Q_calc_NbTi*1e6:.4f} µW")
            elif Q_calc_NbTi >= 1e-9:
                markdown(f"**調整後熱負載**: {Q_calc_NbTi*1e9:.4f} nW")
            else:
                markdown(f"**調整後熱負載**: {Q_calc_NbTi*1e12:.4f} pW")
            
            if seg["Q_NbTi"]:
                pct = (Q_calc_NbTi / seg["Q_NbTi"] - 1) * 100
                markdown(f"變化: **{pct:+.1f}%**")
        else:
            info("此溫度段無 NbTi 線")

# ───────────────────────────────────────────────
# Tab 4: 系統示意圖
# ───────────────────────────────────────────────
with tab4:
    subheader("🏗️ 低溫傳輸線系統示意圖")
    
    fig2, ax = subplots(figsize=(10, 14))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 16)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # 溫度層
    stages = [
        (15.5, "300 K", "#FF6B6B", 2.7e-3, None, "Ag"),
        (12.5, "50 K", "#4ECDC4", 0.8e-3, None, "Ag"),
        (9.5, "4 K", "#45B7D1", 5.4e-6, 540e-9, "Ag+NbTi"),
        (6.5, "0.6 K", "#96CEB4", 290e-9, 29e-9, "Ag+NbTi"),
        (3.5, "100 mK", "#DDA0DD", 5.9e-9, 590e-12, "Ag+NbTi"),
        (0.5, "10 mK", "#B0C4DE", None, None, "終端"),
    ]
    
    for y, label, color, q_ag, q_nbti, mat in stages:
        # 繪製溫度層
        rect = FancyBboxPatch((0.5, y-0.3), 9, 0.6, 
                               boxstyle="round,pad=0.05", 
                               facecolor=color, edgecolor='black', alpha=0.7)
        ax.add_patch(rect)
        ax.text(5, y, label, ha='center', va='center', fontsize=12, fontweight='bold')
        
        # 熱負載標註
        if q_ag:
            unit = "mW" if q_ag >= 1e-3 else "µW" if q_ag >= 1e-6 else "nW" if q_ag >= 1e-9 else "pW"
            val = q_ag*1e3 if q_ag >= 1e-3 else q_ag*1e6 if q_ag >= 1e-6 else q_ag*1e9 if q_ag >= 1e-9 else q_ag*1e12
            ax.text(8.5, y+0.1, f"Ag: {val:.1f} {unit}", ha='right', va='center', fontsize=8, color='#D4A843')
        
        if q_nbti:
            unit = "µW" if q_nbti >= 1e-6 else "nW" if q_nbti >= 1e-9 else "pW"
            val = q_nbti*1e6 if q_nbti >= 1e-6 else q_nbti*1e9 if q_nbti >= 1e-9 else q_nbti*1e12
            ax.text(8.5, y-0.15, f"NbTi: {val:.1f} {unit}", ha='right', va='center', fontsize=8, color='#4A90A4')
    
    # 繪製傳輸線
    for i in range(len(stages)-1):
        y1 = stages[i][0] - 0.3
        y2 = stages[i+1][0] + 0.3
        mid_y = (y1 + y2) / 2
        
        # Ag 線 (右側)
        if results[i]["L_Ag"]:
            L_cm = results[i]["L_Ag"] * 100
            ax.plot([6.5, 6.5], [y1, y2], color='#D4A843', linewidth=4, solid_capstyle='round')
            ax.text(6.8, mid_y, f"{L_cm:.2f} cm", ha='left', va='center', fontsize=8, 
                   color='#D4A843', rotation=90 if abs(y1-y2) > 1 else 0)
        
        # NbTi 線 (左側)
        if results[i]["L_NbTi"]:
            L_mm = results[i]["L_NbTi"] * 1000
            ax.plot([3.5, 3.5], [y1, y2], color='#4A90A4', linewidth=4, solid_capstyle='round')
            ax.text(3.2, mid_y, f"{L_mm:.1f} mm", ha='right', va='center', fontsize=8,
                   color='#4A90A4', rotation=90 if abs(y1-y2) > 1 else 0)
    
    # 熱流箭頭
    for i in range(len(stages)-1):
        y1 = stages[i][0] - 0.3
        y2 = stages[i+1][0] + 0.3
        # 向下箭頭表示熱流
        ax.annotate('', xy=(5, y2+0.1), xytext=(5, y1-0.1),
                   arrowprops=dict(arrowstyle='->', color='red', lw=1.5, alpha=0.5))
    
    # 圖例
    ag_patch = mpatches.Patch(color='#D4A843', label=f'{material_name} wire')
    nbti_patch = mpatches.Patch(color='#4A90A4', label='NbTi wire')
    ax.legend(handles=[ag_patch, nbti_patch], loc='upper left', fontsize=10)
    
    ax.set_title("低溫傳輸線系統結構示意圖", fontsize=14, fontweight='bold', pad=20)
    
    pyplot(fig2)
    
    markdown("""
    **圖例說明**:
    - 🟡 金色線: Ag (或 CuNi) 傳輸線
    - 🔵 藍色線: NbTi 傳輸線
    - 🔴 紅色箭頭: 熱流方向 (高溫 → 低溫)
    - 每段標註為估算長度
    """)

# ───────────────────────────────────────────────
# 底部公式說明
# ───────────────────────────────────────────────
markdown("---")
with expander("📐 計算公式與參數說明"):
    markdown(r"""
    ### Wiedemann-Franz 定律
    
    對於金屬傳輸線，熱導率與電導率的關係為:
    
    $$\lambda = \frac{L_0 \cdot T}{\rho(T)}$$
    
    其中 $L_0 = 2.45 \times 10^{-8}$ W·Ω/K² 為 Lorenz 數。
    
    ### 熱傳導積分
    
    通過傳輸線的熱流:
    
    $$Q = \frac{A}{L} \int_{T_c}^{T_h} \lambda(T) \, dT = \frac{L_0 \cdot A}{L \cdot \rho} \cdot \frac{T_h^2 - T_c^2}{2}$$
    
    ### 反推長度
    
    $$L = \frac{L_0 \cdot A \cdot (T_h^2 - T_c^2)}{2 \cdot Q \cdot \rho}$$
    
    ### 參數
    | 參數 | 符號 | 數值 |
    |------|------|------|
    | Lorenz 數 | $L_0$ | $2.45 \times 10^{-8}$ W·Ω/K² |
    | 線截面積 | $A$ | $\pi (d/2)^2$ m² |
    | 高溫端 | $T_h$ | K |
    | 低溫端 | $T_c$ | K |
    | 電阻率 | $\rho$ | Ω·m |
    | 熱負載 | $Q$ | W |
    """)
with sidebar:
  #markdown("---")
  caption("模擬器基於 Wiedemann-Franz 定律，假設電阻率在每個溫度段內為常數。實際值可能因 RRR、磁場、接觸電阻等因素而異。")
  title("🔬 低溫傳輸線熱負載與長度估算模擬器")
  markdown("模擬圖片中 NbTi / Ag 傳輸線在不同溫度段的熱傳導與長度估算")
