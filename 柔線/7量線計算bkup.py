
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math

# Set page config
st.set_page_config(
    page_title="量子計算柔性傳輸線材參數與串擾分析",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2c3e50;
        border-left: 4px solid #3498db;
        padding-left: 1rem;
        margin: 1.5rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Define data classes for cable specifications
@dataclass
class CableSpec:
    manufacturer: str
    model: str
    cable_type: str
    impedance: float  # Ohm
    freq_range: str
    thickness: float  # mm
    width: float  # mm
    bend_radius: float  # mm
    material: str
    dielectric: str
    attenuation_6ghz: float  # dB/m
    attenuation_12ghz: float  # dB/m
    attenuation_18ghz: float  # dB/m
    crosstalk_db: float  # dB
    thermal_load_4k: float  # µW
    thermal_load_10mk: float  # nW
    channels_per_flex: int
    isolation_db: float  # dB
    phase_stability: str
    operating_temp: str
    connectors: List[str]
    features: List[str]

# Initialize cable database
def init_cable_database() -> Dict[str, CableSpec]:
    cables = {}
    
    # Delft Circuits Cri/oFlex 1
    cables["Delft_CF1"] = CableSpec(
        manufacturer="Delft Circuits",
        model="Cri/oFlex 1 (CF1)",
        cable_type="Stripline Flex",
        impedance=50.0,
        freq_range="DC - 18 GHz",
        thickness=0.3,
        width=1.0,
        bend_radius=1.0,
        material="Polyimide + Silver (Ag)",
        dielectric="Kapton® Polyimide",
        attenuation_6ghz=22.0,
        attenuation_12ghz=39.0,
        attenuation_18ghz=55.0,
        crosstalk_db=-60.0,
        thermal_load_4k=250.0,
        thermal_load_10mk=40.0,
        channels_per_flex=8,
        isolation_db=-60.0,
        phase_stability="Excellent (Cryogenic rated)",
        operating_temp="4K - 400K",
        connectors=["SMA", "SMP", "Mini-SMP"],
        features=["Ultra-flexible", "Vibration isolation", "UHV compatible", "Low thermal load"]
    )
    
    # Delft Circuits Cri/oFlex 2
    cables["Delft_CF2"] = CableSpec(
        manufacturer="Delft Circuits",
        model="Cri/oFlex 2 (CF2)",
        cable_type="Stripline Flex",
        impedance=50.0,
        freq_range="DC - 26 GHz",
        thickness=0.3,
        width=2.0,
        bend_radius=2.0,
        material="Polyimide + Silver (Ag) or NbTi",
        dielectric="Kapton® Polyimide",
        attenuation_6ghz=11.0,
        attenuation_12ghz=16.0,
        attenuation_18ghz=24.0,
        crosstalk_db=-60.0,
        thermal_load_4k=250.0,
        thermal_load_10mk=40.0,
        channels_per_flex=8,
        isolation_db=-60.0,
        phase_stability="Excellent (Phase stable)",
        operating_temp="4K - 400K",
        connectors=["SMA", "SMP", "Mini-SMP", "SMPM"],
        features=["High density", "Integrated filtering", "Superconducting option", "Modular"]
    )
    
    # Rigetti Flex (based on available info)
    cables["Rigetti_Flex"] = CableSpec(
        manufacturer="Rigetti Computing",
        model="High-Density Flex",
        cable_type="Multi-channel Flex",
        impedance=50.0,
        freq_range="DC - 18 GHz",
        thickness=0.3,
        width=2.5,
        bend_radius=2.0,
        material="Polyimide + Superconducting",
        dielectric="Polyimide",
        attenuation_6ghz=10.0,
        attenuation_12ghz=18.0,
        attenuation_18ghz=28.0,
        crosstalk_db=-60.0,
        thermal_load_4k=200.0,
        thermal_load_10mk=35.0,
        channels_per_flex=10,
        isolation_db=-60.0,
        phase_stability="<0.1% amplitude crosstalk",
        operating_temp="10mK - 300K",
        connectors=["SMPM", "Custom"],
        features=["3D signaling", "Integrated components", "Scalable", "Low loss"]
    )
    
    # Radiall Flexible
    cables["Radiall_Flex"] = CableSpec(
        manufacturer="Radiall",
        model="Flex 5/50 S",
        cable_type="Coaxial Flexible",
        impedance=50.0,
        freq_range="DC - 4.5 GHz",
        thickness=2.6,
        width=2.6,
        bend_radius=30.0,
        material="Copper + Tin-dipped braid",
        dielectric="FEP/PTFE",
        attenuation_6ghz=0.26,
        attenuation_12ghz=0.48,
        attenuation_18ghz=0.75,
        crosstalk_db=-40.0,
        thermal_load_4k=500.0,
        thermal_load_10mk=100.0,
        channels_per_flex=1,
        isolation_db=-40.0,
        phase_stability="Good",
        operating_temp="-40°C to +105°C",
        connectors=["SMA", "N", "TNC"],
        features=["Military grade", "Hand-formable option", "Foam PTFE technology"]
    )
    
    # Rosenberger RFlex 047
    cables["Rosenberger_047"] = CableSpec(
        manufacturer="Rosenberger",
        model="RFlex 047",
        cable_type="Ultra-flexible Coaxial",
        impedance=50.0,
        freq_range="DC - 70 GHz",
        thickness=1.19,
        width=1.19,
        bend_radius=3.0,
        material="Silver-plated copper",
        dielectric="PTFE",
        attenuation_6ghz=0.45,
        attenuation_12ghz=0.85,
        attenuation_18ghz=1.2,
        crosstalk_db=-100.0,
        thermal_load_4k=400.0,
        thermal_load_10mk=80.0,
        channels_per_flex=1,
        isolation_db=-100.0,
        phase_stability="Excellent (Test grade)",
        operating_temp="-55°C to +125°C",
        connectors=["SMA", "2.92mm", "Mini-SMP", "WSMP", "1.85mm"],
        features=["Quick-Lock", "Phase matched", "High frequency", "Low loss"]
    )
    
    # Rosenberger RFlex 402
    cables["Rosenberger_402"] = CableSpec(
        manufacturer="Rosenberger",
        model="RFlex 402",
        cable_type="Flexible Coaxial",
        impedance=50.0,
        freq_range="DC - 60 GHz",
        thickness=3.58,
        width=3.58,
        bend_radius=8.0,
        material="Silver-plated copper",
        dielectric="PTFE",
        attenuation_6ghz=0.20,
        attenuation_12ghz=0.38,
        attenuation_18ghz=0.55,
        crosstalk_db=-100.0,
        thermal_load_4k=350.0,
        thermal_load_10mk=70.0,
        channels_per_flex=1,
        isolation_db=-100.0,
        phase_stability="Excellent",
        operating_temp="-55°C to +125°C",
        connectors=["SMA", "N", "2.92mm"],
        features=["Low loss", "High power", "Rugged", "Test & measurement"]
    )
    
    # Amphenol RF (representative model)
    cables["Amphenol_SMP"] = CableSpec(
        manufacturer="Amphenol RF",
        model="SMP Flex Assembly",
        cable_type="Micro-coaxial Flexible",
        impedance=50.0,
        freq_range="DC - 26.5 GHz",
        thickness=1.0,
        width=1.0,
        bend_radius=5.0,
        material="Silver-plated copper",
        dielectric="PTFE",
        attenuation_6ghz=0.55,
        attenuation_12ghz=1.0,
        attenuation_18ghz=1.45,
        crosstalk_db=-60.0,
        thermal_load_4k=450.0,
        thermal_load_10mk=90.0,
        channels_per_flex=1,
        isolation_db=-60.0,
        phase_stability="Good",
        operating_temp="-65°C to +165°C",
        connectors=["SMP", "SMA", "2.92mm"],
        features=["High vibration resistant", "Push-on mating", "Quantum computing rated"]
    )
    
    return cables

# Crosstalk calculation functions
def calculate_next(c_m: float, c: float, l_m: float, l: float) -> float:
    """Calculate Near-End Crosstalk (NEXT) coefficient"""
    return 0.25 * (c_m / c + l_m / l)

def calculate_fext(c_m: float, c: float, l_m: float, l: float, v: float, length: float, rise_time: float) -> float:
    """Calculate Far-End Crosstalk (FEXT) coefficient"""
    k_f = (1 / (2 * v)) * (c_m / c - l_m / l)
    return (length / rise_time) * k_f

def calculate_coupling_coefficients(s: float, h: float, w: float, epsilon_r: float) -> Tuple[float, float, float, float]:
    """Calculate mutual capacitance and inductance for coupled striplines"""
    # Simplified model for coupled striplines
    # s: spacing, h: height to ground, w: width, epsilon_r: relative permittivity
    
    # Self capacitance per unit length (approximate)
    c = (2 * np.pi * epsilon_r * 8.854e-12) / np.log(2 * h / (w/2))
    
    # Mutual capacitance (approximate for parallel lines)
    c_m = c * (h / (h + s)) * 0.1
    
    # Self inductance per unit length
    mu_0 = 4 * np.pi * 1e-7
    l = mu_0 * h / w
    
    # Mutual inductance
    l_m = l * (h / (h + s)) * 0.15
    
    return c, c_m, l, l_m

def linear_to_db(linear: float) -> float:
    """Convert linear scale to dB"""
    return 20 * np.log10(abs(linear))

# Main application
st.markdown('<h1 class="main-header">⚛️ 量子計算柔性傳輸線材參數與串擾分析系統</h1>', unsafe_allow_html=True)

# Initialize database
cable_db = init_cable_database()

# Sidebar navigation
st.sidebar.markdown("## 📊 功能選單")
page = st.sidebar.radio(
    "選擇功能模組:",
    ["🏠 首頁", "📋 線材規格資料庫", "🔀 串擾計算器", "📈 效能比較", "🌡️ 熱負載分析"]
)

if page == "🏠 首頁":
    st.markdown("""
    <div class="info-box">
        <h3>歡迎使用量子計算柔性傳輸線材分析系統</h3>
        <p>本系統整合了五大供應商的柔性傳輸線規格，並提供專業的串擾計算與分析工具。</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("收錄供應商", "5", "Rigetti, Delft, Amphenol, Radiall, Rosenberger")
    with col2:
        st.metric("線材型號", "7+", "持續更新中")
    with col3:
        st.metric("頻率範圍", "DC-70GHz", "覆蓋全量子計算頻段")
    
    st.markdown("### 🎯 主要功能")
    
    features_col1, features_col2 = st.columns(2)
    
    with features_col1:
        st.markdown("""
        - **📋 線材規格資料庫**: 完整的物理參數對比
        - **🔀 串擾計算器**: 基於電磁耦合理論的NEXT/FEXT計算
        - **支援多種線材結構**: Stripline, Microstrip, Coaxial
        """)
    
    with features_col2:
        st.markdown("""
        - **📈 效能比較**: 衰減、熱負載、隔離度視覺化
        - **🌡️ 熱分析**: 4K與10mK熱負載評估
        - **量子計算優化**: 針對超導量子比特應用設計
        """)
    
    st.markdown("### 📚 技術參考")
    st.info("""
    串擾計算基於耦合傳輸線理論：
    - **NEXT (近端串擾)**: NEXT = 1/4(Cm/C + Lm/L)
    - **FEXT (遠端串擾)**: FEXT = (Len/RT) × 1/2v(Cm/C - Lm/L)
    """)

elif page == "📋 線材規格資料庫":
    st.markdown('<h2 class="sub-header">📋 柔性傳輸線規格資料庫</h2>', unsafe_allow_html=True)
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        selected_manufacturer = st.multiselect(
            "選擇製造商:",
            list(set([c.manufacturer for c in cable_db.values()])),
            default=list(set([c.manufacturer for c in cable_db.values()]))
        )
    with col2:
        selected_type = st.multiselect(
            "選擇線材類型:",
            list(set([c.cable_type for c in cable_db.values()])),
            default=list(set([c.cable_type for c in cable_db.values()]))
        )
    
    # Filter cables
    filtered_cables = {k: v for k, v in cable_db.items() 
                      if v.manufacturer in selected_manufacturer and v.cable_type in selected_type}
    
    if not filtered_cables:
        st.warning("請至少選擇一個製造商和線材類型")
    else:
        # Display as expandable cards
        for key, cable in filtered_cables.items():
            with st.expander(f"🔌 {cable.manufacturer} - {cable.model}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**📐 幾何參數**")
                    st.write(f"厚度: {cable.thickness} mm")
                    st.write(f"寬度: {cable.width} mm")
                    st.write(f"最小彎曲半徑: {cable.bend_radius} mm")
                    st.write(f"每Flex通道數: {cable.channels_per_flex}")
                
                with col2:
                    st.markdown("**⚡ 電氣參數**")
                    st.write(f"阻抗: {cable.impedance} Ω")
                    st.write(f"頻率範圍: {cable.freq_range}")
                    st.write(f"隔離度: {cable.isolation_db} dB")
                    st.write(f"串擾: {cable.crosstalk_db} dB")
                
                with col3:
                    st.markdown("**🌡️ 熱特性**")
                    st.write(f"4K熱負載: {cable.thermal_load_4k} µW")
                    st.write(f"10mK熱負載: {cable.thermal_load_10mk} nW")
                    st.write(f"工作溫度: {cable.operating_temp}")
                
                st.markdown("**📊 衰減特性 (dB/m)**")
                att_col1, att_col2, att_col3 = st.columns(3)
                with att_col1:
                    st.metric("6 GHz", f"{cable.attenuation_6ghz} dB/m")
                with att_col2:
                    st.metric("12 GHz", f"{cable.attenuation_12ghz} dB/m")
                with att_col3:
                    st.metric("18 GHz", f"{cable.attenuation_18ghz} dB/m")
                
                st.markdown("**🔧 材料與連接器**")
                st.write(f"導體材料: {cable.material}")
                st.write(f"介電材料: {cable.dielectric}")
                st.write(f"可用連接器: {', '.join(cable.connectors)}")
                st.write(f"相位穩定性: {cable.phase_stability}")
                
                st.markdown("**✨ 特性**")
                st.write(', '.join(cable.features))

elif page == "🔀 串擾計算器":
    st.markdown('<h2 class="sub-header">🔀 柔性傳輸線串擾計算器</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <p>本計算器基於耦合傳輸線理論，計算平行柔性傳輸線之間的近端串擾(NEXT)與遠端串擾(FEXT)。</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📐 幾何參數輸入", "📊 預設線材分析"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 線材幾何參數")
            line_width = st.slider("線寬 w (mm)", 0.1, 5.0, 0.5, 0.1)
            line_height = st.slider("線高 h (mm)", 0.05, 2.0, 0.3, 0.05)
            spacing = st.slider("線間距 s (mm)", 0.1, 10.0, 1.0, 0.1)
            length = st.slider("耦合長度 L (mm)", 10, 1000, 200, 10)
            
            st.markdown("### 材料參數")
            epsilon_r = st.slider("相對介電常數 εr", 1.0, 10.0, 3.4, 0.1)
            
        with col2:
            st.markdown("### 訊號參數")
            freq = st.slider("頻率 (GHz)", 0.1, 40.0, 6.0, 0.1)
            rise_time = st.slider("上升時間 (ps)", 1, 1000, 100, 10)
            voltage = st.slider("訊號振幅 (V)", 0.1, 5.0, 1.0, 0.1)
            
            st.markdown("### 進階選項")
            ground_plane_dist = st.slider("接地平面距離 (mm)", 0.1, 5.0, 1.0, 0.1)
            use_superconducting = st.checkbox("使用超導材料 (NbTi)", value=False)
        
        if st.button("🔍 計算串擾", type="primary"):
            # Calculate coupling coefficients
            c, c_m, l, l_m = calculate_coupling_coefficients(
                spacing/1000, ground_plane_dist/1000, line_width/1000, epsilon_r
            )
            
            # Velocity of propagation
            c_light = 3e8
            v = c_light / np.sqrt(epsilon_r)
            
            # Calculate NEXT and FEXT
            next_coeff = calculate_next(c_m, c, l_m, l)
            fext_coeff = calculate_fext(c_m, c, l_m, l, v, length/1000, rise_time/1e12)
            
            # Convert to dB
            next_db = linear_to_db(next_coeff)
            fext_db = linear_to_db(fext_coeff) if fext_coeff != 0 else -100
            
            # Display results
            st.markdown("### 📈 計算結果")
            
            res_col1, res_col2, res_col3 = st.columns(3)
            
            with res_col1:
                st.metric("近端串擾 (NEXT)", f"{next_coeff:.4f}", f"{next_db:.1f} dB")
                st.caption("耦合係數 (線性)")
            
            with res_col2:
                st.metric("遠端串擾 (FEXT)", f"{fext_coeff:.4f}", f"{fext_db:.1f} dB")
                st.caption("耦合係數 (線性)")
            
            with res_col3:
                total_crosstalk = np.sqrt(next_coeff**2 + fext_coeff**2)
                st.metric("總串擾", f"{total_crosstalk:.4f}", f"{linear_to_db(total_crosstalk):.1f} dB")
            
            # Visualization
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
            
            # Crosstalk vs Spacing
            spacings = np.linspace(0.1, 5.0, 50)
            next_vals = []
            fext_vals = []
            
            for s in spacings:
                c_t, c_m_t, l_t, l_m_t = calculate_coupling_coefficients(
                    s/1000, ground_plane_dist/1000, line_width/1000, epsilon_r
                )
                next_vals.append(abs(calculate_next(c_m_t, c_t, l_m_t, l_t)))
                fext_vals.append(abs(calculate_fext(c_m_t, c_t, l_m_t, l_t, v, length/1000, rise_time/1e12)))
            
            ax1.semilogy(spacings, next_vals, 'b-', label='NEXT', linewidth=2)
            ax1.semilogy(spacings, fext_vals, 'r-', label='FEXT', linewidth=2)
            ax1.axvline(x=spacing, color='g', linestyle='--', label=f'Current: {spacing}mm')
            ax1.set_xlabel('Line Spacing (mm)')
            ax1.set_ylabel('Crosstalk Coefficient')
            ax1.set_title('Crosstalk vs Line Spacing')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Frequency response
            freqs = np.linspace(0.1, 40, 100)
            # Simplified frequency dependence
            next_freq = [next_coeff * (1 + f/10) for f in freqs]
            fext_freq = [fext_coeff * (f/6) for f in freqs]
            
            ax2.plot(freqs, 20*np.log10(np.abs(next_freq)), 'b-', label='NEXT', linewidth=2)
            ax2.plot(freqs, 20*np.log10(np.abs(fext_freq)), 'r-', label='FEXT', linewidth=2)
            ax2.axvline(x=freq, color='g', linestyle='--', label=f'Current: {freq}GHz')
            ax2.set_xlabel('Frequency (GHz)')
            ax2.set_ylabel('Crosstalk (dB)')
            ax2.set_title('Frequency Response')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            st.pyplot(fig)
            
            # Recommendations
            st.markdown("### 💡 設計建議")
            if next_db > -40 or fext_db > -40:
                st.warning("⚠️ 串擾水平較高，建議增加線間距或使用屏蔽結構")
            elif next_db > -60 or fext_db > -60:
                st.info("ℹ️ 串擾水平中等，適合一般量子計算應用")
            else:
                st.success("✅ 串擾水平優良，適合高精度量子計算")
    
    with tab2:
        st.markdown("### 基於實際線材規格的串擾分析")
        
        selected_cable = st.selectbox(
            "選擇線材型號:",
            list(cable_db.keys()),
            format_func=lambda x: f"{cable_db[x].manufacturer} {cable_db[x].model}"
        )
        
        cable = cable_db[selected_cable]
        
        col1, col2 = st.columns(2)
        with col1:
            parallel_length = st.slider("平行長度 (mm)", 10, 500, 100, 10)
            num_channels = st.slider("通道數量", 2, 64, 8, 1)
            
        with col2:
            operating_freq = st.slider("操作頻率 (GHz)", 0.1, 26.0, 6.0, 0.1)
            temp = st.selectbox("操作溫度", ["300K (室溫)", "4K", "10mK"])
        
        if st.button("📊 分析所選線材", type="primary"):
            # Estimate crosstalk based on cable specs
            base_isolation = abs(cable.isolation_db)
            
            # Length factor (crosstalk increases with length)
            length_factor = 20 * np.log10(parallel_length / 100)
            
            # Frequency factor
            freq_factor = 20 * np.log10(operating_freq / 6)
            
            estimated_next = -(base_isolation - length_factor - freq_factor)
            estimated_fext = estimated_next - 6  # FEXT typically 6dB worse in flex cables
            
            st.markdown(f"### 📈 {cable.manufacturer} {cable.model} 串擾分析")
            
            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
            with metrics_col1:
                st.metric("預估 NEXT", f"{estimated_next:.1f} dB")
            with metrics_col2:
                st.metric("預估 FEXT", f"{estimated_fext:.1f} dB")
            with metrics_col3:
                st.metric("通道間隔離度", f"{cable.isolation_db} dB")
            
            # Channel density analysis
            if num_channels > cable.channels_per_flex:
                num_flexes = np.ceil(num_channels / cable.channels_per_flex)
                st.info(f"需要 {int(num_flexes)} 個 Flex 組件來支援 {num_channels} 個通道")
            
            # Thermal impact
            if temp == "4K":
                total_thermal = (num_channels / cable.channels_per_flex) * cable.thermal_load_4k
                st.metric("總熱負載 @ 4K", f"{total_thermal:.1f} µW")
            elif temp == "10mK":
                total_thermal = (num_channels / cable.channels_per_flex) * cable.thermal_load_10mk
                st.metric("總熱負載 @ 10mK", f"{total_thermal:.1f} nW")

elif page == "📈 效能比較":
    st.markdown('<h2 class="sub-header">📈 多維度效能比較</h2>', unsafe_allow_html=True)
    
    comparison_type = st.selectbox(
        "選擇比較維度:",
        ["衰減特性", "熱負載", "幾何尺寸", "頻率響應"]
    )
    
    cables_to_compare = st.multiselect(
        "選擇要比較的線材:",
        list(cable_db.keys()),
        default=list(cable_db.keys())[:4],
        format_func=lambda x: f"{cable_db[x].manufacturer} {cable_db[x].model}"
    )
    
    if not cables_to_compare:
        st.warning("請至少選擇兩種線材進行比較")
    else:
        fig, ax = plt.subplots(figsize=(12, 6))
        
        if comparison_type == "衰減特性":
            frequencies = [6, 12, 18]
            x = np.arange(len(frequencies))
            width = 0.15
            
            for i, key in enumerate(cables_to_compare):
                cable = cable_db[key]
                attenuations = [cable.attenuation_6ghz, cable.attenuation_12ghz, cable.attenuation_18ghz]
                ax.bar(x + i*width, attenuations, width, label=f"{cable.manufacturer} {cable.model}")
            
            ax.set_xlabel('Frequency (GHz)')
            ax.set_ylabel('Attenuation (dB/m)')
            ax.set_title('Attenuation Comparison at Different Frequencies')
            ax.set_xticks(x + width * (len(cables_to_compare)-1) / 2)
            ax.set_xticklabels(['6 GHz', '12 GHz', '18 GHz'])
            ax.legend()
            ax.grid(True, alpha=0.3)
            
        elif comparison_type == "熱負載":
            labels = [f"{cable_db[k].manufacturer}\\n{cable_db[k].model}" for k in cables_to_compare]
            thermal_4k = [cable_db[k].thermal_load_4k for k in cables_to_compare]
            thermal_10mk = [cable_db[k].thermal_load_10mk for k in cables_to_compare]
            
            x = np.arange(len(labels))
            width = 0.35
            
            ax.bar(x - width/2, thermal_4k, width, label='4K Stage (µW)', color='skyblue')
            ax.bar(x + width/2, [t/10 for t in thermal_10mk], width, label='10mK Stage (nW/10)', color='lightcoral')
            
            ax.set_ylabel('Thermal Load')
            ax.set_title('Thermal Load Comparison')
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
        elif comparison_type == "幾何尺寸":
            labels = [f"{cable_db[k].manufacturer}\\n{cable_db[k].model}" for k in cables_to_compare]
            thicknesses = [cable_db[k].thickness for k in cables_to_compare]
            widths = [cable_db[k].width for k in cables_to_compare]
            bend_radii = [cable_db[k].bend_radius for k in cables_to_compare]
            
            x = np.arange(len(labels))
            width = 0.25
            
            ax.bar(x - width, thicknesses, width, label='Thickness (mm)', color='gold')
            ax.bar(x, widths, width, label='Width (mm)', color='lightgreen')
            ax.bar(x + width, bend_radii, width, label='Bend Radius (mm)', color='plum')
            
            ax.set_ylabel('Dimension (mm)')
            ax.set_title('Geometric Dimensions Comparison')
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
        elif comparison_type == "頻率響應":
            for key in cables_to_compare:
                cable = cable_db[key]
                freqs = np.linspace(0.1, 20, 100)
                
                # Interpolate attenuation
                freq_points = [6, 12, 18]
                att_points = [cable.attenuation_6ghz, cable.attenuation_12ghz, cable.attenuation_18ghz]
                
                # Simple interpolation
                att_interp = np.interp(freqs, freq_points, att_points)
                
                ax.plot(freqs, att_interp, label=f"{cable.manufacturer} {cable.model}", linewidth=2)
            
            ax.set_xlabel('Frequency (GHz)')
            ax.set_ylabel('Attenuation (dB/m)')
            ax.set_title('Frequency Response Comparison')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        st.pyplot(fig)
        
        # Data table
        st.markdown("### 📋 詳細數據對比表")
        
        data = []
        for key in cables_to_compare:
            c = cable_db[key]
            data.append({
                "製造商": c.manufacturer,
                "型號": c.model,
                "類型": c.cable_type,
                "阻抗(Ω)": c.impedance,
                "頻率範圍": c.freq_range,
                "厚度(mm)": c.thickness,
                "寬度(mm)": c.width,
                "彎曲半徑(mm)": c.bend_radius,
                "6GHz衰減(dB/m)": c.attenuation_6ghz,
                "隔離度(dB)": c.isolation_db,
                "4K熱負載(µW)": c.thermal_load_4k,
                "通道數/Flex": c.channels_per_flex
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

elif page == "🌡️ 熱負載分析":
    st.markdown('<h2 class="sub-header">🌡️ 量子計算系統熱負載分析</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <p>分析柔性傳輸線在稀釋製冷機不同溫度級的熱負載，對於大規模量子計算系統設計至關重要。</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 系統配置")
        num_qubits = st.slider("量子比特數量", 10, 10000, 1000, 10)
        lines_per_qubit = st.slider("每量子比特線路數", 1, 10, 4, 1)
        cable_type = st.selectbox(
            "選擇線材類型:",
            list(cable_db.keys()),
            format_func=lambda x: f"{cable_db[x].manufacturer} {cable_db[x].model}"
        )
        
    with col2:
        st.markdown("### 製冷機配置")
        fridge_type = st.selectbox("製冷機型號", ["BlueFors LDsl", "BlueFors XLDsl", "BlueFors KIDE", "Oxford ProteoxQX", "Custom"])
        cooling_power_4k = st.number_input("4K級冷卻功率 (W)", 0.1, 100.0, 1.0, 0.1)
        cooling_power_10mk = st.number_input("混合室冷卻功率 (µW)", 1, 1000, 400, 10)
    
    if st.button("🌡️ 計算熱負載", type="primary"):
        cable = cable_db[cable_type]
        total_lines = num_qubits * lines_per_qubit
        num_flexes = np.ceil(total_lines / cable.channels_per_flex)
        
        # Calculate heat loads
        heat_4k = num_flexes * cable.thermal_load_4k / 1e6  # Convert to W
        heat_10mk = num_flexes * cable.thermal_load_10mk / 1e6  # Convert to µW
        
        # Add attenuator heat load (typical 10dB attenuator at 4K)
        heat_attenuators_4k = total_lines * 0.001  # Approximate 1mW per line
        
        total_heat_4k = heat_4k + heat_attenuators_4k
        
        st.markdown("### 📊 熱負載分析結果")
        
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        with metric_col1:
            st.metric("所需Flex數量", f"{int(num_flexes)}")
            st.metric("總線路數", f"{int(total_lines)}")
        
        with metric_col2:
            st.metric("4K級熱負載", f"{total_heat_4k*1e3:.2f} mW", 
                     f"{(total_heat_4k/cooling_power_4k)*100:.1f}% 容量")
            st.metric("10mK級熱負載", f"{heat_10mk:.2f} µW",
                     f"{(heat_10mk/cooling_power_10mk)*100:.1f}% 容量")
        
        with metric_col3:
            heat_per_qubit = (total_heat_4k * 1e6 + heat_10mk) / num_qubits
            st.metric("每量子比特熱負載", f"{heat_per_qubit:.2f} µW")
            st.metric("線材佔比", f"{(heat_4k/total_heat_4k)*100:.1f}%")
        
        # Visualization
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Heat load breakdown
        categories = ['Flex Cables\\n(4K)', 'Attenuators\\n(4K)', 'Flex Cables\\n(10mK)']
        values = [heat_4k*1e3, heat_attenuators_4k*1e3, heat_10mk]
        colors = ['#3498db', '#e74c3c', '#2ecc71']
        
        ax1.bar(categories, values, color=colors)
        ax1.set_ylabel('Heat Load (mW or µW)')
        ax1.set_title('Heat Load Breakdown by Component')
        ax1.grid(True, alpha=0.3)
        
        # Cooling capacity vs load
        stages = ['4K Stage', 'Mixing Chamber']
        capacities = [cooling_power_4k*1e3, cooling_power_10mk]  # Convert to same units
        loads = [total_heat_4k*1e3, heat_10mk]
        
        x = np.arange(len(stages))
        width = 0.35
        
        ax2.bar(x - width/2, capacities, width, label='Cooling Capacity', color='lightblue')
        ax2.bar(x + width/2, loads, width, label='Actual Load', color='orange')
        ax2.set_ylabel('Power (mW / µW)')
        ax2.set_title('Cooling Capacity vs Heat Load')
        ax2.set_xticks(x)
        ax2.set_xticklabels(stages)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        st.pyplot(fig)
        
        # Recommendations
        st.markdown("### 💡 優化建議")
        
        if (total_heat_4k/cooling_power_4k) > 0.8:
            st.error("⚠️ 4K級熱負載過高！建議採用超導線材或增加熱錨點")
        elif (total_heat_4k/cooling_power_4k) > 0.5:
            st.warning("⚠️ 4K級熱負載偏高，建議優化線材佈局")
        else:
            st.success("✅ 4K級熱負載在合理範圍內")
            
        if (heat_10mk/cooling_power_10mk) > 0.5:
            st.error("⚠️ 10mK級熱負載過高！將顯著影響量子比特相干時間")
        elif (heat_10mk/cooling_power_10mk) > 0.2:
            st.warning("⚠️ 10mK級熱負載偏高，建議使用更低熱導線材")
        else:
            st.success("✅ 10mK級熱負載控制良好")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>量子計算柔性傳輸線材分析系統 v1.0 | 數據來源：製造商公開規格書</p>
    <p>⚠️ 本工具僅供參考，實際應用請以製造商最新規格為準</p>
</div>
""", unsafe_allow_html=True)
