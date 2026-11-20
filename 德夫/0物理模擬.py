from streamlit import button, cache_data, columns, dataframe, download_button, header, info, markdown, metric, number_input, plotly_chart, pyplot, radio, set_page_config, sidebar, slider, subheader, success, tabs, warning
from fontUtil2 import 配置中文
from matplotlib.pyplot import subplots
from numpy import array, clip, cos, linspace, log, log10, meshgrid, ones_like, pi, sin, sqrt
from pandas import DataFrame
from plotly.graph_objects import Bar, Figure, Scatter
from scipy.constants import k, h, c, epsilon_0, mu_0
from matplotlib.patches import Rectangle, Circle
from plotly.subplots import make_subplots
"""
傳輸線物理模擬器 - Transmission Line Physics Simulator
適用於量子計算低溫 I/O 纜線設計與分析
"""
配置中文()

#import streamlit as st
#import numpy as np
#import matplotlib.pyplot as plt
#import pandas as pd
#import  as go

# 頁面設定
set_page_config(
    page_title="傳輸線物理模擬器",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 樣式
def local_css():
    markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF4B4B;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #FF4B4B;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: black;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

# 標題
markdown('<div class="main-header">⚡ 傳輸線物理模擬器</div>', unsafe_allow_html=True)
markdown("**量子計算低溫 I/O 纜線設計與分析工具** | Cryogenic RF Transmission Line Simulator")

# 側邊欄 - 參數設定
with sidebar:
    header("⚙️ 參數設定")
    subheader("材料選擇") # 材料選擇
    conductor_material=radio("導體材料", ["Silver (Ag)", "Niobium-Titanium (NbTi)", "Copper (Cu)", "Aluminum (Al)"], index=0, horizontal=True)
    
    dielectric_material = radio("介電材料", ["Kapton (Polyimide)", "Teflon (PTFE)", "Alumina (Al2O3)"], index=0, horizontal=True)
    
    subheader("📐 幾何參數") # 幾何參數
    
    col1, col2 = columns(2)
    with col1:
        line_width = number_input("線寬 (μm)", value=100.0, min_value=10.0, max_value=500.0)
        dielectric_thickness = number_input("介電厚度 (μm)", value=50.0, min_value=10.0, max_value=200.0)
    with col2:
        conductor_thickness = number_input("導體厚度 (μm)", value=5.0, min_value=1.0, max_value=20.0)
        cable_length = number_input("纜線長度 (m)", value=0.2, min_value=0.01, max_value=2.0)
    
    # 溫度設定
    subheader("🌡️ 溫度設定")
    temperature = slider("操作溫度 (K)", min_value=0.01, max_value=300.0, value=4.0, step=0.1)
    
    # 頻率範圍
    subheader("📊 頻率範圍")
    freq_min = number_input("最低頻率 (GHz)", value=0.1, min_value=0.01, max_value=100.0)
    freq_max = number_input("最高頻率 (GHz)", value=20.0, min_value=1.0, max_value=100.0)
    
    # 計算按鈕
    markdown("---")
    calculate_btn = button("🚀 開始計算", use_container_width=True)

# 材料參數資料庫
@cache_data
def get_material_properties():
    return {
        "Silver (Ag)": {
            "rho_300k": 1.6e-8,
            "rho_4k": 0.02e-8,
            "tc": None,
            "k_300k": 430,
            "k_4k": 1500,
            "alpha": 0.0038,
            "color": "#C0C0C0"
        },
        "Niobium-Titanium (NbTi)": {
            "rho_300k": 5e-7,
            "rho_4k": 0,
            "tc": 9.2,
            "bc2": 14.5,
            "jc": 3000,
            "k_300k": 10,
            "k_4k": 1.0,
            "alpha": 0,
            "color": "#FF6B6B"
        },
        "Copper (Cu)": {
            "rho_300k": 1.7e-8,
            "rho_4k": 0.03e-8,
            "tc": None,
            "k_300k": 400,
            "k_4k": 1200,
            "alpha": 0.0039,
            "color": "#B87333"
        },
        "Aluminum (Al)": {
            "rho_300k": 2.7e-8,
            "rho_4k": 0.01e-8,
            "tc": 1.2,
            "k_300k": 237,
            "k_4k": 800,
            "alpha": 0.0043,
            "color": "#A8A8A8"
        },
        "Kapton (Polyimide)": {
            "epsilon_r": 3.4,
            "tan_delta": 0.002,
            "k": 0.015,
            "color": "#FFD700"
        },
        "Teflon (PTFE)": {
            "epsilon_r": 2.1,
            "tan_delta": 0.0002,
            "k": 0.25,
            "color": "#F0F0F0"
        },
        "Alumina (Al2O3)": {
            "epsilon_r": 9.8,
            "tan_delta": 0.0001,
            "k": 30,
            "color": "#E6E6FA"
        }
    }

# 計算函數
def calculate_resistivity(material, temp):
    """計算電阻率隨溫度變化"""
    props = get_material_properties()[material]
    
    if material == "Niobium-Titanium (NbTi)":
        if temp < props["tc"]:
            return 1e-18  # 超導態
        else:
            return props["rho_300k"] * (temp / 300)
    
    # Bloch-Grüneisen 近似
    rho_0 = props["rho_4k"]
    rho_300 = props["rho_300k"]
    
    if temp < 20:
        return rho_0
    else:
        return rho_0 + (rho_300 - rho_0) * (temp / 300) ** 5

def calculate_thermal_conductivity(material, temp):
    """計算熱導率隨溫度變化"""
    props = get_material_properties()[material]
    
    if material == "Niobium-Titanium (NbTi)":
        # 聲子主導，T^3 依賴
        return props["k_4k"] * (temp / 4.2) ** 3 if temp < props["tc"] else props["k_300k"]
    elif material in ["Silver (Ag)", "Copper (Cu)", "Aluminum (Al)"]:
        # 電子主導，低溫下與 T 成正比
        if temp < 20:
            return props["k_4k"] * (temp / 4.2)
        else:
            return props["k_300k"]
    else:
        return props["k"]

def calculate_characteristic_impedance(w, h, epsilon_r):
    """計算微帶線特性阻抗"""
    w_eff = w / 1e6  # 轉換為米
    h_eff = h / 1e6
    
    # Hammerstad-Jensen 公式
    if w_eff / h_eff <= 1:
        z0 = (60 / sqrt(epsilon_r)) * log(8 * h_eff / w_eff + w_eff / (4 * h_eff))
    else:
        z0 = (120 * pi) / (sqrt(epsilon_r) * (w_eff / h_eff + 1.393 + 0.667 * log(w_eff / h_eff + 1.444)))
    
    return z0

def calculate_effective_dielectric_constant(w, h, epsilon_r):
    """計算有效介電常數"""
    w_eff = w / 1e6
    h_eff = h / 1e6
    
    a = 1 + (1 / 49) * log((w_eff / h_eff) ** 4 + (w_eff / (52 * h_eff)) ** 2) / ((w_eff / h_eff) ** 4 + 0.432)
    b = 1 + (1 / 18.7) * log(1 + (w_eff / (18.1 * h_eff)) ** 3)
    
    epsilon_eff = (epsilon_r + 1) / 2 + ((epsilon_r - 1) / 2) * (1 + 10 * h_eff / w_eff) ** (-a * b)
    
    return epsilon_eff

def calculate_attenuation(freq, material, temp, w, h, t, epsilon_r):
    """計算衰減常數 (dB/m)"""
    rho = calculate_resistivity(material, temp)
    
    if rho < 1e-10:  # 超導態
        return 0.001 + 0.0001 * freq ** 2
    
    # 集膚深度
    mu = 4 * pi * 1e-7
    delta_s = sqrt(rho / (pi * freq * 1e9 * mu))
    
    # 表面電阻
    Rs = rho / delta_s
    
    # 導體損耗
    z0 = calculate_characteristic_impedance(w, h, epsilon_r)
    alpha_c = (Rs / (z0 * w * 1e-6)) * 8.686  # 轉換為 dB/m
    
    # 介電損耗
    tan_delta = get_material_properties()[dielectric_material]["tan_delta"]
    alpha_d = (pi * freq * 1e9 * sqrt(epsilon_r) * tan_delta / c) * 8.686
    
    return alpha_c + alpha_d

def calculate_heat_load(material, temp_stages, length):
    """計算各溫度級熱負載"""
    props = get_material_properties()[material]
    heat_loads = []
    
    for i in range(len(temp_stages) - 1):
        T_hot = temp_stages[i]
        T_cold = temp_stages[i + 1]
        
        # 簡化熱傳導計算
        k_avg = (calculate_thermal_conductivity(material, T_hot) + 
                 calculate_thermal_conductivity(material, T_cold)) / 2
        
        # 假設截面積 1e-6 m² (1 mm²)
        A = 1e-6
        Q = k_avg * A * (T_hot - T_cold) / length
        heat_loads.append(Q * 1e6)  # 轉換為 μW
    
    return heat_loads

# 主內容區
tab1, tab2, tab3, tab4 = tabs(["📈 S參數分析", "🔥 熱學分析", "⚡ 電磁場分佈", "📋 設計報告"])

with tab1:
    header("S參數與頻率響應分析")
    
    if calculate_btn or True:  # 預設顯示
        freq = linspace(freq_min, freq_max, 500)
        
        # 計算 S 參數
        z0 = calculate_characteristic_impedance(line_width, dielectric_thickness, 
                                               get_material_properties()[dielectric_material]["epsilon_r"])
        
        # 假設負載阻抗
        zl = 40 + 5j
        gamma = (zl - z0) / (zl + z0)
        s11 = 20 * log10(abs(gamma)) * ones_like(freq)
        
        # S21 計算
        alpha = array([calculate_attenuation(f, conductor_material, temperature, 
                                               line_width, dielectric_thickness, 
                                               conductor_thickness,
                                               get_material_properties()[dielectric_material]["epsilon_r"]) 
                         for f in freq])
        s21 = -alpha * cable_length + 20 * log10(1 - abs(gamma)**2)
        
        # 繪圖
        col1, col2 = columns(2)
        
        with col1:
            fig1 = Figure()
            fig1.add_trace(Scatter(x=freq, y=s11, mode='lines', name='S11 (反射)', 
                                     line=dict(color='red', width=2)))
            fig1.add_trace(Scatter(x=freq, y=s21, mode='lines', name='S21 (傳輸)', 
                                     line=dict(color='blue', width=2)))
            fig1.add_hline(y=-10, line_dash="dash", line_color="gray", 
                          annotation_text="-10 dB 閾值")
            fig1.update_layout(
                title="S參數 vs 頻率",
                xaxis_title="頻率 (GHz)",
                yaxis_title="幅度 (dB)",
                height=400,
                template="plotly_white"
            )
            plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # 史密斯圓圖 (簡化)
            theta = linspace(0, 2*pi, 100)
            fig2, ax = subplots(figsize=(6, 6))
            ax.plot(cos(theta), sin(theta), 'k-', linewidth=2)
            ax.axhline(y=0, color='k', linewidth=0.5)
            ax.axvline(x=0, color='k', linewidth=0.5)
            
            # 標記點
            ax.plot(0, 0, 'go', markersize=10, label=f'匹配點 (Z={z0:.1f}Ω)')
            ax.plot(gamma.real, gamma.imag, 'ro', markersize=10, label=f'負載點')
            
            ax.set_xlim(-1.2, 1.2)
            ax.set_ylim(-1.2, 1.2)
            ax.set_aspect('equal')
            ax.set_xlabel('Real(Γ)')
            ax.set_ylabel('Imag(Γ)')
            ax.set_title('史密斯圓圖 (阻抗匹配)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            pyplot(fig2)
        
        # 關鍵指標
        subheader("關鍵射頻指標")
        cols = columns(4)
        with cols[0]:
            metric("特性阻抗", f"{z0:.2f} Ω", "目標: 50Ω")
        with cols[1]:
            vswr = (1 + abs(gamma)) / (1 - abs(gamma))
            metric("VSWR", f"{vswr:.2f}", "良好" if vswr < 1.5 else "需改善")
        with cols[2]:
            metric("回波損耗", f"{s11[0]:.1f} dB", "良好" if s11[0] < -10 else "需改善")
        with cols[3]:
            metric("插入損耗 @6GHz", f"{alpha[len(alpha)//2]*cable_length:.2f} dB", 
                     "低損耗" if alpha[len(alpha)//2]*cable_length < 3 else "高損耗")

with tab2:
    header("熱學分析與熱負載計算")
    
    # 溫度級定義
    temp_stages = [300, 50, 4, 1, 0.1, 0.01]
    stage_names = ['300K', '50K', '4K', '1K', '100mK', '10mK']
    
    col1, col2 = columns(2)
    
    with col1:
        subheader("熱導率 vs 溫度")
        
        temps = linspace(0.1, 300, 100)
        k_values = [calculate_thermal_conductivity(conductor_material, t) for t in temps]
        
        fig3 = Figure()
        fig3.add_trace(Scatter(x=temps, y=k_values, mode='lines', 
                                 name=conductor_material,
                                 line=dict(width=2)))
        fig3.update_layout(
            xaxis_title="溫度 (K)",
            yaxis_title="熱導率 (W/m·K)",
            yaxis_type="log",
            height=400,
            template="plotly_white"
        )
        plotly_chart(fig3, use_container_width=True)
    
    with col2:
        subheader("各溫度級熱負載")
        
        heat_loads = calculate_heat_load(conductor_material, temp_stages, cable_length)
        
        fig4 = Figure()
        fig4.add_trace(Bar(x=stage_names[:-1], y=heat_loads, 
                             marker_color='#FF6B6B',
                             name='熱負載'))
        fig4.update_layout(
            xaxis_title="溫度級",
            yaxis_title="熱負載 (μW)",
            yaxis_type="log",
            height=400,
            template="plotly_white"
        )
        plotly_chart(fig4, use_container_width=True)
    
    # 熱負載表格
    subheader("詳細熱負載數據")
    heat_data = DataFrame({
        '溫度級': [f"{stage_names[i]} → {stage_names[i+1]}" for i in range(len(stage_names)-1)],
        '熱負載 (μW)': [f"{q:.2f}" for q in heat_loads],
        '累積熱負載 (μW)': [f"{sum(heat_loads[:i+1]):.2f}" for i in range(len(heat_loads))]
    })
    dataframe(heat_data, use_container_width=True)

with tab3:
    header("電磁場分佈模擬")
    
    col1, col2 = columns([2, 1])
    
    with col1:
        subheader("微帶線截面電場分佈")
        
        fig5, ax = subplots(figsize=(10, 6))
        
        # 繪製結構
        ax.add_patch(Rectangle((0, 6), 10, 1.5, facecolor='#A0A0A0', edgecolor='black', linewidth=2))
        ax.text(5, 6.75, 'Ground Plane', ha='center', va='center', fontsize=10, fontweight='bold')
        
        ax.add_patch(Rectangle((0, 2.5), 10, 3.5, facecolor='#FFE4B5', edgecolor='black', 
                               linewidth=1, alpha=0.5))
        
        # 信號線
        signal_width = line_width / 100  # 縮放顯示
        ax.add_patch(Rectangle((5 - signal_width/2, 4.5), signal_width, 0.5, 
                               facecolor='#4169E1', edgecolor='black', linewidth=2))
        
        ax.add_patch(Rectangle((0, 1), 10, 1.5, facecolor='#A0A0A0', edgecolor='black', linewidth=2))
        
        # 電場等高線
        x = linspace(0, 10, 50)
        y = linspace(2.5, 6, 30)
        X, Y = meshgrid(x, y)
        
        # 電場模型
        E = 1 / sqrt((X - 5)**2 + (Y - 4.75)**2 + 0.1)
        E = clip(E, 0, 2)
        
        contour = ax.contour(X, Y, E, levels=10, colors='red', alpha=0.6, linewidths=1)
        ax.clabel(contour, inline=True, fontsize=8, fmt='%1.1f')
        
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 8)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title('電場強度分佈 (歸一化)', fontsize=12, pad=10)
        
        pyplot(fig5)
    
    with col2:
        subheader("場分佈參數")
        
        epsilon_eff = calculate_effective_dielectric_constant(
            line_width, dielectric_thickness,
            get_material_properties()[dielectric_material]["epsilon_r"]
        )
        
        v_phase = c / sqrt(epsilon_eff)
        
        metric("有效介電常數", f"{epsilon_eff:.3f}")
        metric("相速度", f"{v_phase/1e8:.2f} × 10⁸ m/s")
        metric("波長 @6GHz", f"{v_phase/(6e9)*1000:.2f} mm")
        
        # 電場模式說明
        markdown("""
        **電場特性：**
        - **E-field**: 垂直於導體表面
        - **H-field**: 平行於導體表面
        - **傳播模式**: TEM 準 TEM 模式
        - **邊緣效應**: 線寬/厚度比 < 1 時顯著
        """)

with tab4:
    header("設計報告與優化建議")
    
    # 生成報告
    subheader("📊 設計參數總結")
    
    report_data = {
        "參數": [
            "導體材料", "介電材料", "線寬", "介電厚度", "導體厚度",
            "操作溫度", "纜線長度", "特性阻抗", "有效介電常數",
            "相速度", "衰減 @6GHz", "總熱負載 @10mK"
        ],
        "數值": [
            conductor_material, dielectric_material, f"{line_width} μm", 
            f"{dielectric_thickness} μm", f"{conductor_thickness} μm",
            f"{temperature} K", f"{cable_length} m", 
            f"{z0:.2f} Ω", f"{epsilon_eff:.3f}",
            f"{v_phase:.2e} m/s", f"{alpha[len(alpha)//2]:.3f} dB/m",
            f"{sum(heat_loads):.2f} μW"
        ],
        "狀態": [
            "✅", "✅", "✅", "✅", "✅",
            "✅" if temperature < 10 else "⚠️",
            "✅", 
            "✅" if 45 < z0 < 55 else "⚠️",
            "✅",
            "✅",
            "✅" if alpha[len(alpha)//2] < 2 else "⚠️",
            "✅" if sum(heat_loads) < 1000 else "⚠️"
        ]
    }
    
    report_df = DataFrame(report_data)
    dataframe(report_df, use_container_width=True, hide_index=True)
    
    # 優化建議
    subheader("💡 優化建議")
    
    suggestions = []
    
    if z0 < 45 or z0 > 55:
        suggestions.append(f"⚠️ 特性阻抗偏離 50Ω (目前 {z0:.1f}Ω)。建議調整線寬至 {line_width * (z0/50):.0f} μm")
    
    if alpha[len(alpha)//2] > 2:
        suggestions.append(f"⚠️ 衰減較高。考慮使用 NbTi 超導材料或增加導體厚度")
    
    if temperature > 10 and conductor_material == "Niobium-Titanium (NbTi)":
        suggestions.append(f"⚠️ NbTi 在 {temperature}K 處於常態，建議降低溫度至 9.2K 以下以發揮超導優勢")
    
    if sum(heat_loads) > 1000:
        suggestions.append(f"⚠️ 熱負載較高。建議縮短纜線長度或改用 NbTi 材料")
    
    if not suggestions:
        success("✅ 所有參數均在合理範圍內，設計良好！")
    else:
        for suggestion in suggestions:
            warning(suggestion)
    
    # 匯出按鈕
    markdown("---")
    col1, col2 = columns(2)
    with col1:
        if button("📥 匯出 CSV 報告", use_container_width=True):
            csv = report_df.to_csv(index=False)
            download_button(
                label="下載 CSV",
                data=csv,
                file_name=f"TL_Report_{conductor_material.replace(' ', '_')}.csv",
                mime="text/csv"
            )
    with col2:
        if button("📄 生成 PDF 報告", use_container_width=True):
            info("PDF 匯出功能開發中...")

# 頁腳
markdown("---")
markdown("""
<div style="text-align: center; color: #666;">
    <small>
    傳輸線物理模擬器 v1.0 | 基於 Cri/oFlex 技術規格 | 
    適用於量子計算低溫 I/O 設計
    </small>
</div>
""", unsafe_allow_html=True)
