from streamlit import caption, checkbox, columns, dataframe, divider, error, expander, info, markdown, metric, number_input, plotly_chart, selectbox, set_page_config, sidebar, slider, subheader, success, warning, radio
from numpy import ceil, cumsum, linspace, log10
from pandas import DataFrame
from plotly.graph_objects import Bar, Figure, Scatter, Scatterpolar
from plotly.subplots import make_subplots
#import streamlit as st
#import numpy as np
#import pandas as pd
#import plotly.graph_objects as go
#import plotly.express as px

# 設定頁面配置
set_page_config(
    page_title="量子讀取架構模擬器 | Quantum Readout Architecture Simulator",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義 CSS 樣式
markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 1rem;
        border-radius: 5px;
    }
    .info-box {
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
        padding: 1rem;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

with sidebar: # 標題
    markdown('<div class="main-header">🔬 量子讀取架構模擬器</div>', unsafe_allow_html=True)
    markdown('<div class="sub-header">Quantum Readout Architecture Simulator | 高密度傳輸線熱管理與串擾分析</div>', unsafe_allow_html=True)

# 側邊欄 - 系統配置
#with sidebar:
    subheader("⚙️ 系統配置")
    
    # 稀釋製冷機溫度級
    subheader("溫度級配置 (K)")
    t_50k = number_input("50K 級 (PT2)", value=50.0, min_value=4.0, max_value=100.0)
    t_4k = number_input("4K 級 (Still)", value=4.0, min_value=1.0, max_value=10.0)
    t_1k = number_input("1K 級 (Cold Plate)", value=1.0, min_value=0.1, max_value=2.0)
    t_100mk = number_input("100mK 級 (MC)", value=0.1, min_value=0.01, max_value=0.5, step=0.01, format="%.2f")
    t_10mk = number_input("10mK 級 (QPU)", value=0.01, min_value=0.005, max_value=0.05, step=0.001, format="%.3f")
    
    temps = [300, t_50k, t_4k, t_1k, t_100mk, t_10mk]
    temp_labels = ['300K', '50K', '4K', '1K', '100mK', '10mK']
    
    divider()
    
    # 量子位元數量
    subheader("量子位元配置")
    n_qubits = slider("量子位元數量", min_value=10, max_value=1000, value=100, step=10)
    readout_type = radio("讀取類型", [" dispersive readout (1線/量子位)", "multiplexing (1線/4-8量子位)"], horizontal=True)
    
    if "multiplexing" in readout_type:
        mux_factor = slider("多工因子", min_value=2, max_value=16, value=4)
        n_channels = max(1, n_qubits // mux_factor)
    else:
        n_channels = n_qubits
    
    info(f"總通道數: **{n_channels}**")
    
    divider()
    
    # 傳輸線配置
    subheader("傳輸線配置")
    cable_type = radio("傳輸線類型", ["Delft Cri/oFlex® (Ag/Polyimide)", "Maybell FLAX (NbTi)", "CryoCoax SC-086 (CuNi)", "CryoCoax SC-086 (NbTi-NbTi)", "Rosenberger 半剛性 (SS)", "Rosenberger 半剛性 (NbTi)"], horizontal=True)
    
    cable_length = slider("單段長度 (m)", min_value=0.1, max_value=1.0, value=0.3, step=0.1)
    
    divider()
    
    # 顯示選項
    subheader("顯示選項")
    show_thermal = checkbox("顯示熱負載分析", value=True)
    show_crosstalk = checkbox("顯示串擾分析", value=True)
    show_signal = checkbox("顯示訊號完整性", value=True)

# 材料資料庫
線材庫 = {
    "Delft Cri/oFlex® (Ag/Polyimide)": {
        "thermal_conductivity": lambda T: 0.5 if T < 10 else (2 if T < 100 else 10),  # mW/K·cm, 近似
        "resistance": lambda T: 0.1 if T > 10 else 0.01,  # Ohm/m
        "attenuation": lambda T, f: 0.5 + 0.01*f,  # dB/m @ GHz
        "crosstalk": -60,  # dB
        "flexible": True,
        "superconducting": False,
        "density": 256,  # channels per bundle
        "heat_load_per_channel": 4e-6,  # W @ 3K-0.7K
    },
    "Maybell FLAX (NbTi)": {
        "thermal_conductivity": lambda T: 0.01 if T < 9.2 else 0.1,  # mW/K·cm, 超導態極低
        "resistance": lambda T: 0.001 if T < 9.2 else 10,  # Ohm/m, 超導轉變
        "attenuation": lambda T, f: 0.1 if T < 9.2 else (1.5 + 0.05*f),  # dB/m
        "crosstalk": -40,  # dB
        "flexible": True,
        "superconducting": True,
        "tc": 9.2,  # K
        "density": 128,
        "heat_load_per_channel": 5e-9,  # W @ 1K-100mK (1ft)
    },
    "CryoCoax SC-086 (CuNi)": {
        "thermal_conductivity": lambda T: 0.15 if T < 10 else (1.5 if T < 100 else 20),  # mW/K·cm
        "resistance": lambda T: 0.5,  # Ohm/m
        "attenuation": lambda T, f: 0.8 + 0.02*f,  # dB/m
        "crosstalk": -50,  # dB
        "flexible": False,
        "superconducting": False,
        "density": 32,
        "heat_load_per_channel": 10e-9,  # W
    },
    "CryoCoax SC-086 (NbTi-NbTi)": {
        "thermal_conductivity": lambda T: 0.005 if T < 9.2 else 0.05,
        "resistance": lambda T: 0.0001 if T < 9.2 else 5,
        "attenuation": lambda T, f: 0.05 if T < 9.2 else (1.0 + 0.03*f),
        "crosstalk": -45,
        "flexible": False,
        "superconducting": True,
        "tc": 9.2,
        "density": 32,
        "heat_load_per_channel": 2e-9,
    },
    "Rosenberger 半剛性 (SS)": {
        "thermal_conductivity": lambda T: 0.009 if T < 10 else (0.1 if T < 100 else 1.2),
        "resistance": lambda T: 1.0,
        "attenuation": lambda T, f: 1.0 + 0.03*f,
        "crosstalk": -55,
        "flexible": False,
        "superconducting": False,
        "density": 16,
        "heat_load_per_channel": 50e-9,
    },
    "Rosenberger 半剛性 (NbTi)": {
        "thermal_conductivity": lambda T: 0.008 if T < 9.2 else 0.08,
        "resistance": lambda T: 0.0001 if T < 9.2 else 3,
        "attenuation": lambda T, f: 0.08 if T < 9.2 else (0.8 + 0.02*f),
        "crosstalk": -50,
        "flexible": False,
        "superconducting": True,
        "tc": 9.2,
        "density": 16,
        "heat_load_per_channel": 8e-9,
    }
}

# 計算函數
def calculate_thermal_load(material, temps, length, n_channels):
    """計算各溫度級的熱負載"""
    mat = 線材庫[material]
    heat_loads = []
    
    for i in range(len(temps)-1):
        T_hot = temps[i]
        T_cold = temps[i+1]
        T_avg = (T_hot + T_cold) / 2
        
        # 簡化熱傳導計算: Q = k * A * ΔT / L
        # 這裡使用經驗公式基於材料熱導率
        k = mat["thermal_conductivity"](T_avg)
        
        # 根據材料特性調整
        if mat.get("superconducting", False) and T_cold < mat.get("tc", 9.2):
            # 超導態熱負載極低
            base_load = mat["heat_load_per_channel"] * (T_hot - T_cold) / 10
        else:
            base_load = mat["heat_load_per_channel"] * (T_hot - T_cold) / 0.1
        
        # 考慮通道數量密度
        bundle_factor = ceil(n_channels / mat["density"])
        total_load = base_load * n_channels * length * bundle_factor
        
        heat_loads.append(max(total_load, 1e-12))  # 避免零值
    
    return heat_loads

def calculate_crosstalk(material, n_channels, density, frequency=6):
    """計算鄰近通道串擾"""
    mat = 線材庫[material]
    base_crosstalk = mat["crosstalk"]
    
    # 通道密度越高，串擾越嚴重
    density_factor = n_channels / density
    crosstalk_db = base_crosstalk - 10 * log10(max(density_factor, 1))
    
    # 頻率影響
    freq_factor = frequency / 6  # 相對於 6 GHz
    crosstalk_db -= 10 * log10(freq_factor)
    
    return crosstalk_db

def calculate_signal_integrity(material, temps, length, frequency=6):
    """計算訊號完整性指標"""
    mat = 線材庫[material]
    T_qpu = temps[-1]
    
    # 衰減
    att = mat["attenuation"](T_qpu, frequency) * length
    
    # 雜訊溫度 (簡化模型)
    T_noise = T_qpu * (1 + 0.1 * att)
    
    # SNR 估算 (簡化)
    SNR = 20 - att - 10 * log10(T_noise / 0.01)
    
    return {
        "attenuation_db": att,
        "noise_temp_K": T_noise,
        "SNR_db": SNR
    }

# 主內容區域
col1, col2, col3 = columns([2, 1, 1])

with col1:
    subheader("📊 系統概覽")
    
    # 計算數據
    heat_loads = calculate_thermal_load(cable_type, temps, cable_length, n_channels)
    crosstalk = calculate_crosstalk(cable_type, n_channels, 線材庫[cable_type]["density"])
    signal_info = calculate_signal_integrity(cable_type, temps, cable_length)
    
    # 關鍵指標
    metric_cols = columns(4)
    with metric_cols[0]:
        metric(
            label="總熱負載 @ 10mK",
            value=f"{heat_loads[-1]*1e9:.1f} nW",
            delta=f"{heat_loads[-1]/1e-9:.2f} vs 1nW 基準"
        )
    with metric_cols[1]:
        metric(
            label="鄰近通道串擾",
            value=f"{crosstalk:.1f} dB",
            delta="優良" if crosstalk < -50 else "需改善"
        )
    with metric_cols[2]:
        metric(
            label="訊號衰減 @ 6GHz",
            value=f"{signal_info['attenuation_db']:.2f} dB",
            delta=f"SNR: {signal_info['SNR_db']:.1f} dB"
        )
    with metric_cols[3]:
        bundles = ceil(n_channels / 線材庫[cable_type]["density"])
        metric(
            label="所需線纜束數",
            value=f"{int(bundles)}",
            delta=f"{n_channels} 通道"
        )

# 熱負載分析
if show_thermal:
    markdown("---")
    subheader("🌡️ 熱負載分析 (Thermal Load Analysis)")
    
    fig_thermal = make_subplots(
        rows=1, cols=2,
        subplot_titles=("各溫度級熱負載分佈", "累積熱負載 vs 溫度"),
        specs=[[{"type": "bar"}, {"type": "scatter"}]]
    )
    
    # 條形圖
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
    fig_thermal.add_trace(
        Bar(
            x=temp_labels[1:],
            y=[h*1e9 for h in heat_loads],
            marker_color=colors,
            text=[f"{h*1e9:.2f}" for h in heat_loads],
            textposition='auto',
            name="熱負載 (nW)"
        ),
        row=1, col=1
    )
    
    # 累積圖
    cumulative = cumsum(heat_loads)
    fig_thermal.add_trace(
        Scatter(
            x=temps[1:],
            y=[c*1e9 for c in cumulative],
            mode='lines+markers',
            line=dict(color='#E74C3C', width=3),
            marker=dict(size=10),
            name="累積熱負載 (nW)"
        ),
        row=1, col=2
    )
    
    fig_thermal.update_xaxes(title_text="溫度級", row=1, col=1)
    fig_thermal.update_xaxes(title_text="溫度 (K)", type="log", row=1, col=2)
    fig_thermal.update_yaxes(title_text="熱負載 (nW)", type="log", row=1, col=1)
    fig_thermal.update_yaxes(title_text="累積熱負載 (nW)", type="log", row=1, col=2)
    
    fig_thermal.update_layout(height=500, showlegend=False)
    plotly_chart(fig_thermal, use_container_width=True)
    
    # 熱負載詳細數據
    with expander("查看詳細熱負載數據"):
        df_thermal = DataFrame({
            "溫度級": temp_labels[1:],
            "熱端溫度 (K)": temps[:-1],
            "冷端溫度 (K)": temps[1:],
            "溫差 (K)": [temps[i] - temps[i+1] for i in range(len(temps)-1)],
            "熱負載 (nW)": [h*1e9 for h in heat_loads],
            "累積熱負載 (nW)": [c*1e9 for c in cumulative]
        })
        dataframe(df_thermal, use_container_width=True)

# 串擾分析
if show_crosstalk:
    markdown("---")
    subheader("📡 高密度串擾分析 (High-Density Crosstalk Analysis)")
    
    col_xtalk1, col_xtalk2 = columns([2, 1])
    
    with col_xtalk1:
        # 通道密度 vs 串擾
        densities = [16, 32, 64, 128, 256, 512]
        crosstalk_values = []
        
        for d in densities:
            ct = calculate_crosstalk(cable_type, n_channels, d, frequency=6)
            crosstalk_values.append(ct)
        
        fig_xtalk = Figure()
        
        # 添加不同頻率的曲線
        for freq in [2, 6, 10, 20]:
            ct_freq = [calculate_crosstalk(cable_type, n_channels, d, frequency=freq) for d in densities]
            fig_xtalk.add_trace(Scatter(
                x=densities,
                y=ct_freq,
                mode='lines+markers',
                name=f'{freq} GHz',
                line=dict(width=3)
            ))
        
        # 標記當前選擇
        current_density = 線材庫[cable_type]["density"]
        fig_xtalk.add_vline(x=current_density, line_dash="dash", line_color="red",
                           annotation_text="當前選擇")
        
        fig_xtalk.update_layout(
            title="通道密度 vs 串擾 (不同頻率)",
            xaxis_title="通道密度 (channels/bundle)",
            yaxis_title="串擾 (dB)",
            xaxis_type="log",
            height=500
        )
        
        plotly_chart(fig_xtalk, use_container_width=True)
    
    with col_xtalk2:
        info("""
        **串擾分析說明**
        
        - **-60 dB**: 極佳，量子計算可接受
        - **-50 dB**: 良好，需適當屏蔽
        - **-40 dB**: 邊緣，可能需要額外濾波
        - **<-40 dB**: 過高，不建議用於量子讀取
        
        **影響因素**:
        1. 通道間距 (pitch)
        2. 頻率 (越高越差)
        3. 屏蔽效能
        4. 接地品質
        """)
        
        # 當前狀態
        metric("當前串擾", f"{crosstalk:.1f} dB")
        if crosstalk < -50:
            success("✅ 串擾水準良好")
        elif crosstalk < -40:
            warning("⚠️ 串擾水準邊緣")
        else:
            error("❌ 串擾過高，建議降低密度或增加屏蔽")

# 訊號完整性
if show_signal:
    markdown("---")
    subheader("📶 訊號完整性分析 (Signal Integrity)")
    
    col_sig1, col_sig2 = columns([3, 2])
    
    with col_sig1:
        # 頻率響應
        frequencies = linspace(0.1, 20, 100)  # GHz
        
        fig_sig = Figure()
        
        # 不同溫度下的衰減
        for temp_label, temp_val in [('10mK', t_10mk), ('100mK', t_100mk), ('1K', t_1k), ('4K', t_4k)]:
            att_vals = [線材庫[cable_type]["attenuation"](temp_val, f) * cable_length for f in frequencies]
            fig_sig.add_trace(Scatter(
                x=frequencies,
                y=att_vals,
                mode='lines',
                name=f'{temp_label} ({temp_val*1000:.0f} mK)' if temp_val < 1 else f'{temp_label}',
                line=dict(width=2)
            ))
        
        # 標記 6 GHz 讀取頻率
        fig_sig.add_vline(x=6, line_dash="dash", line_color="red", 
                         annotation_text="典型讀取頻率")
        
        fig_sig.update_layout(
            title="頻率響應 vs 溫度",
            xaxis_title="頻率 (GHz)",
            yaxis_title="總衰減 (dB)",
            height=500
        )
        
        plotly_chart(fig_sig, use_container_width=True)
    
    with col_sig2:
        info("""
        **訊號完整性關鍵指標**
        
        **衰減 (Attenuation)**:
        - 目標: < 1 dB @ 6 GHz
        - 超導 NbTi: 極低損耗 (< 0.1 dB)
        - 常規導體: 0.5-2 dB
        
        **雜訊溫度**:
        - 理想: T_noise ≈ T_physical
        - 實際: T_noise = T_physical × (1 + L/10)
        
        **SNR 要求**:
        - 量子態分辨: SNR > 10 dB
        - 高保真讀取: SNR > 20 dB
        """)
        
        # 當前指標
        metric("@ 6 GHz", f"{signal_info['attenuation_db']:.2f} dB")
        metric("雜訊溫度", f"{signal_info['noise_temp_K']*1e3:.1f} mK")
        metric("估算 SNR", f"{signal_info['SNR_db']:.1f} dB")

# 比較模式
markdown("---")
subheader("🔍 多方案比較 (Technology Comparison)")

compare_all = checkbox("啟用多技術比較模式", value=False)

if compare_all:
    comparison_data = []
    
    for mat_name in 線材庫.keys():
        hl = calculate_thermal_load(mat_name, temps, cable_length, n_channels)
        ct = calculate_crosstalk(mat_name, n_channels, 線材庫[mat_name]["density"])
        si = calculate_signal_integrity(mat_name, temps, cable_length)
        
        comparison_data.append({
            "技術方案": mat_name,
            "熱負載@10mK (nW)": hl[-1] * 1e9,
            "串擾 (dB)": ct,
            "衰減@6GHz (dB)": si['attenuation_db'],
            "SNR (dB)": si['SNR_db'],
            "柔性": "✓" if 線材庫[mat_name]["flexible"] else "✗",
            "超導": "✓" if 線材庫[mat_name]["superconducting"] else "✗",
            "最大密度": 線材庫[mat_name]["density"]
        })
    
    df_compare = DataFrame(comparison_data)
    
    # 雷達圖比較
    categories = ['低熱負載', '低串擾', '低衰減', '高SNR', '高密度']
    
    fig_radar = Figure()
    
    for idx, row in df_compare.iterrows():
        # 正規化到 0-1 範圍 (越高越好)
        values = [
            1 - min(row['熱負載@10mK (nW)'] / 100, 1),  # 熱負載越低越好
            1 - min(abs(row['串擾 (dB)']) / 60, 1),     # 串擾絕對值越大越好
            1 - min(row['衰減@6GHz (dB)'] / 5, 1),      # 衰減越低越好
            min(max(row['SNR (dB)'], 0) / 30, 1),       # SNR 越高越好
            min(row['最大密度'] / 256, 1)               # 密度越高越好
        ]
        values += values[:1]  # 閉合
        
        fig_radar.add_trace(Scatterpolar(
            r=values,
            theta=categories + [categories[0]],
            fill='toself',
            name=row['技術方案'].split('(')[0].strip()
        ))
    
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        height=600
    )
    
    plotly_chart(fig_radar, use_container_width=True)
    
    # 詳細比較表
    dataframe(df_compare.style.highlight_min(subset=['熱負載@10mK (nW)', '衰減@6GHz (dB)'], color='green')
                             .highlight_max(subset=['串擾 (dB)', 'SNR (dB)'], color='green'),
                 use_container_width=True)

# 建議與警告
markdown("---")
subheader("💡 設計建議與自動診斷")

checks = []

# 熱負載檢查
if heat_loads[-1] > 1e-9:
    checks.append(("⚠️", "熱負載警告", f"10mK級熱負載為 {heat_loads[-1]*1e9:.1f} nW，可能影響基底溫度。建議使用超導NbTi線纜。", "warning"))
else:
    checks.append(("✅", "熱負載良好", f"10mK級熱負載僅 {heat_loads[-1]*1e9:.1f} nW，符合量子計算要求。", "success"))

# 串擾檢查
if crosstalk > -40:
    checks.append(("❌", "串擾過高", f"串擾為 {crosstalk:.1f} dB，建議降低通道密度或增加屏蔽。", "error"))
elif crosstalk > -50:
    checks.append(("⚠️", "串擾邊緣", f"串擾為 {crosstalk:.1f} dB，建議評估對量子位元相干時間的影響。", "warning"))
else:
    checks.append(("✅", "串擾良好", f"串擾為 {crosstalk:.1f} dB，符合高密度佈線要求。", "success"))

# SNR 檢查
if signal_info['SNR_db'] < 10:
    checks.append(("❌", "SNR不足", f"SNR僅 {signal_info['SNR_db']:.1f} dB，無法可靠分辨量子態。", "error"))
elif signal_info['SNR_db'] < 20:
    checks.append(("⚠️", "SNR邊緣", f"SNR為 {signal_info['SNR_db']:.1f} dB，建議優化讀取功率或降低衰減。", "warning"))
else:
    checks.append(("✅", "SNR良好", f"SNR為 {signal_info['SNR_db']:.1f} dB，支援高保真量子態讀取。", "success"))

# 密度檢查
if n_channels > 1000 and not 線材庫[cable_type]["flexible"]:
    checks.append(("⚠️", "佈線挑戰", f"{n_channels} 通道使用剛性線纜，佈線難度極高。建議改用柔性帶狀線纜。", "warning"))

for icon, title, message, level in checks:
    if level == "error":
        error(f"**{icon} {title}**: {message}")
    elif level == "warning":
        warning(f"**{icon} {title}**: {message}")
    else:
        success(f"**{icon} {title}**: {message}")

# 頁尾
markdown("---")
caption("""
**資料來源**: Delft Circuits, Rosenberger, Maybell Quantum, CryoCoax, Ardent Concepts, Amphenol Aerospace, Quantum Microwave 官方技術規格  
**模型假設**: 簡化熱傳導模型，實際性能可能因具體實現而異。建議參考廠商完整數據表進行詳細設計。  
**版本**: v1.0 | 2026-03-11
""")
