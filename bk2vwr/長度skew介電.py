from streamlit import columns, dataframe, error, info, markdown, metric, multiselect, number_input, pyplot, radio, selectbox, set_page_config, sidebar, slider, success, tabs, warning
from matplotlib.pyplot import subplots, tight_layout
from numpy import ceil, linspace, sqrt
from pandas import DataFrame
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Dict, List, Tuple
from fontUtil2 import 配置中文
配置中文()

# 設定頁面配置
set_page_config(
    page_title="PCB 高速訊號長度匹配計算器",
    page_icon="🔌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義CSS樣式
markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-left: 5px solid #1E88E5;
        padding-left: 1rem;
    }
    .info-box {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1E88E5;
    }
    .warning-box {
        background-color: #FFF3E0;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #FF9800;
    }
    .success-box {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 10px 10px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E88E5;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# 定義資料類別
@dataclass
class InterfaceSpec:
    name: str
    data_rate: float  # Gbps
    ui_ps: float      # UI in ps
    intra_pair_skew: float  # ps
    inter_pair_skew: float  # ps
    max_length_mm: float
    description: str

@dataclass
class TransmissionLine:
    name: str
    epsilon_eff: float
    propagation_delay_ps_per_mm: float
    velocity_m_per_s: float
    color: str

# 定義介面規格
INTERFACE_SPECS = {
    "PCIe 3.0": InterfaceSpec(
        name="PCIe 3.0",
        data_rate=8.0,
        ui_ps=125.0,
        intra_pair_skew=5.0,   # 通常 < 0.05 UI = 6.25 ps
        inter_pair_skew=500.0, # 通常 < 4 UI = 500 ps
        max_length_mm=400.0,
        description="8 GT/s, 128b/130b 編碼"
    ),
    "PCIe 4.0": InterfaceSpec(
        name="PCIe 4.0",
        data_rate=16.0,
        ui_ps=62.5,
        intra_pair_skew=3.0,   # < 0.05 UI = 3.125 ps
        inter_pair_skew=250.0, # < 4 UI = 250 ps
        max_length_mm=300.0,
        description="16 GT/s, 更嚴格的Skew要求"
    ),
    "PCIe 5.0": InterfaceSpec(
        name="PCIe 5.0",
        data_rate=32.0,
        ui_ps=31.25,
        intra_pair_skew=1.5,   # < 0.05 UI = 1.56 ps
        inter_pair_skew=125.0, # < 4 UI = 125 ps
        max_length_mm=200.0,
        description="32 GT/s, 極嚴格Skew控制"
    ),
    "DDR4-3200": InterfaceSpec(
        name="DDR4-3200",
        data_rate=3.2,
        ui_ps=312.5,
        intra_pair_skew=10.0,  # DQS與DQ
        inter_pair_skew=25.0,  # Byte lane內
        max_length_mm=50.0,
        description="資料速率 3200 MT/s"
    ),
    "DDR5-4800": InterfaceSpec(
        name="DDR5-4800",
        data_rate=4.8,
        ui_ps=208.3,
        intra_pair_skew=5.0,
        inter_pair_skew=15.0,
        max_length_mm=40.0,
        description="資料速率 4800 MT/s"
    ),
    "USB 3.2 Gen1": InterfaceSpec(
        name="USB 3.2 Gen1",
        data_rate=5.0,
        ui_ps=200.0,
        intra_pair_skew=15.0,  # < 0.075 UI = 15 ps
        inter_pair_skew=100.0,
        max_length_mm=200.0,
        description="5 Gbps (SuperSpeed)"
    ),
    "USB 3.2 Gen2": InterfaceSpec(
        name="USB 3.2 Gen2",
        data_rate=10.0,
        ui_ps=100.0,
        intra_pair_skew=8.0,   # < 0.08 UI = 8 ps
        inter_pair_skew=50.0,
        max_length_mm=150.0,
        description="10 Gbps (SuperSpeed+)"
    ),
    "USB4": InterfaceSpec(
        name="USB4",
        data_rate=20.0,
        ui_ps=50.0,
        intra_pair_skew=4.0,
        inter_pair_skew=25.0,
        max_length_mm=100.0,
        description="20 Gbps (Thunderbolt 3相容)"
    )
}

# 光速
C_M_PER_S = 299792458
C_MM_PER_PS = C_M_PER_S / 1e9  # mm/ps

def calculate_transmission_lines(epsilon_r: float, height_mm: float, width_mm: float) -> Dict[str, TransmissionLine]:
    """計算不同傳輸線的特性"""
    
    # Microstrip 有效介電係數 (Hammerstad-Jensen)
    if width_mm / height_mm <= 1:
        e_eff_ms = (epsilon_r + 1) / 2 + ((epsilon_r - 1) / 2) * ((1 + 12 * height_mm / width_mm) ** -0.5)
    else:
        e_eff_ms = (epsilon_r + 1) / 2 + ((epsilon_r - 1) / 2) * ((1 + 12 * height_mm / width_mm) ** -0.5)
    
    # Stripline 有效介電係數 (約等於基材介電係數)
    e_eff_sl = epsilon_r
    
    # 波導 (假設為基板整合波導 SIW，主要介質為空氣)
    e_eff_wg = 1.0  # 近似空氣填充
    
    lines = {}
    
    # Microstrip
    v_ms = C_M_PER_S / sqrt(e_eff_ms)
    delay_ms = sqrt(e_eff_ms) / C_MM_PER_PS  # ps/mm
    lines["Microstrip"] = TransmissionLine(
        name="Microstrip (表層)",
        epsilon_eff=e_eff_ms,
        propagation_delay_ps_per_mm=delay_ms,
        velocity_m_per_s=v_ms,
        color="#FF6B6B"
    )
    
    # Stripline
    v_sl = C_M_PER_S / sqrt(e_eff_sl)
    delay_sl = sqrt(e_eff_sl) / C_MM_PER_PS
    lines["Stripline"] = TransmissionLine(
        name="Stripline (內層)",
        epsilon_eff=e_eff_sl,
        propagation_delay_ps_per_mm=delay_sl,
        velocity_m_per_s=v_sl,
        color="#4ECDC4"
    )
    
    # Waveguide (SIW)
    v_wg = C_M_PER_S / sqrt(e_eff_wg)
    delay_wg = sqrt(e_eff_wg) / C_MM_PER_PS
    lines["Waveguide"] = TransmissionLine(
        name="波導 SIW (空氣填充)",
        epsilon_eff=e_eff_wg,
        propagation_delay_ps_per_mm=delay_wg,
        velocity_m_per_s=v_wg,
        color="#45B7D1"
    )
    
    return lines

def calculate_length_compensation(
    target_delay_ps: float,
    lines: Dict[str, TransmissionLine]
) -> Dict[str, float]:
    """計算不同傳輸線達到相同延遲所需的物理長度"""
    lengths = {}
    for name, line in lines.items():
        length_mm = target_delay_ps / line.propagation_delay_ps_per_mm
        lengths[name] = length_mm
    return lengths

# 主標題
markdown('<h1 class="main-header">🔌 PCB 高速訊號長度匹配計算器</h1>', unsafe_allow_html=True)
markdown("<p style='text-align: center; color: #666; font-size: 1.1rem;'>支援 PCIe、DDR、USB 介面的 Skew 分析與長度匹配設計</p>", unsafe_allow_html=True)

# 側邊欄設定
with sidebar:
    markdown("## ⚙️ 基材參數設定")
    
    epsilon_r = slider(
        "基材介電係數 (εr)",
        min_value=3.0,
        max_value=5.0,
        value=4.3,
        step=0.1,
        help="FR4 通常為 4.2-4.5，高速材料如 Megtron6 約 3.6"
    )
    
    height_mm = slider(
        "介質厚度 h (mm)",
        min_value=0.05,
        max_value=0.5,
        value=0.2,
        step=0.05,
        help="銅箔到參考平面的距離"
    )
    
    width_mm = slider(
        "走線寬度 w (mm)",
        min_value=0.05,
        max_value=0.3,
        value=0.15,
        step=0.01,
        help="建議依阻抗控制調整"
    )
    
    markdown("---")
    markdown("### 📊 傳輸線特性預覽")
    
    lines = calculate_transmission_lines(epsilon_r, height_mm, width_mm)
    
    for name, line in lines.items():
        metric(
            label=f"{name}",
            value=f"{line.propagation_delay_ps_per_mm:.2f} ps/mm",
            delta=f"εeff={line.epsilon_eff:.2f}"
        )

# 主內容區
# 建立分頁
tab1, tab2, tab3, tab4 = tabs([
    "📋 介面規格總覽", 
    "🔧 長度匹配計算器", 
    "📈 Skew 視覺化分析",
    "📐 進階補償設計"
])

# Tab 1: 介面規格總覽
with tab1:
    markdown('<h2 class="sub-header">高速介面規格比較</h2>', unsafe_allow_html=True)
    
    # 建立比較表格
    spec_data = []
    for spec in INTERFACE_SPECS.values():
        spec_data.append({
            "介面": spec.name,
            "資料速率 (Gbps)": spec.data_rate,
            "UI (ps)": spec.ui_ps,
            "Intra-pair Skew (ps)": f"±{spec.intra_pair_skew}",
            "Inter-pair Skew (ps)": f"±{spec.inter_pair_skew}",
            "最大走線長度 (mm)": spec.max_length_mm,
            "說明": spec.description
        })
    
    df_specs = DataFrame(spec_data)
    dataframe(df_specs, use_container_width=True, height=400)
    
    markdown('<div class="info-box">', unsafe_allow_html=True)
    markdown("""
    **關鍵設計準則：**
    - **Intra-pair Skew**：差分對內兩條線的時間差，通常要求 < 0.05 UI (5% Unit Interval)
    - **Inter-pair Skew**：不同差分對之間的時間差，通常要求 < 4 UI (PCIe) 或依Byte lane分組 (DDR)
    - **長度匹配**：必須以「電氣長度（時間延遲）」為基準，而非物理長度
    """)
    markdown('</div>', unsafe_allow_html=True)

# Tab 2: 長度匹配計算器
with tab2:
    markdown('<h2 class="sub-header">互動式長度匹配計算</h2>', unsafe_allow_html=True)
    
    col1, col2 = columns([1, 2])
    
    with col1:
        markdown("### 選擇介面與參數")
        
        selected_interface = selectbox(
            "選擇介面標準",
            list(INTERFACE_SPECS.keys()),
            index=1  # 預設 PCIe 4.0
        )
        
        spec = INTERFACE_SPECS[selected_interface]
        
        markdown(f"""
        <div class="success-box">
        <b>已選擇：{spec.name}</b><br>
        資料速率：{spec.data_rate} Gbps<br>
        Unit Interval：{spec.ui_ps} ps<br>
        Intra-pair Skew 限制：±{spec.intra_pair_skew} ps<br>
        Inter-pair Skew 限制：±{spec.inter_pair_skew} ps
        </div>
        """, unsafe_allow_html=True)
        
        target_length = slider(
            "目標走線長度 (mm)",
            min_value=10.0,
            max_value=spec.max_length_mm,
            value=min(100.0, spec.max_length_mm),
            step=5.0
        )
        
        ref_line_type = radio(
            "參考傳輸線類型（基準）",
            ["Stripline", "Microstrip", "Waveguide"],
            index=0,
            help="以此傳輸線的物理長度為基準，計算其他類型所需長度"
        )
    
    with col2:
        markdown("### 計算結果")
        
        lines = calculate_transmission_lines(epsilon_r, height_mm, width_mm)
        
        # 計算參考線的延遲
        ref_line = lines[ref_line_type]
        target_delay = target_length * ref_line.propagation_delay_ps_per_mm
        
        # 計算各類型所需長度
        lengths = calculate_length_compensation(target_delay, lines)
        
        # 顯示結果卡片
        cols = columns(3)
        for idx, (name, line) in enumerate(lines.items()):
            with cols[idx]:
                length = lengths[name]
                delta = length - target_length
                
                markdown(f"""
                <div class="metric-card">
                    <h3>{line.name}</h3>
                    <h2>{length:.2f} mm</h2>
                    <p>延遲：{target_delay:.2f} ps</p>
                    <p>速度：{line.velocity_m_per_s/1e6:.2f} Mm/s</p>
                    <p style="font-size: 0.9rem; opacity: 0.9;">
                        {'+' if delta > 0 else ''}{delta:.2f} mm vs 參考
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        # 詳細數據表格
        markdown("### 詳細計算數據")
        
        calc_data = []
        for name, line in lines.items():
            length = lengths[name]
            calc_data.append({
                "傳輸線類型": line.name,
                "有效介電係數": f"{line.epsilon_eff:.3f}",
                "傳播速度 (Mm/s)": f"{line.velocity_m_per_s/1e6:.3f}",
                "延遲 (ps/mm)": f"{line.propagation_delay_ps_per_mm:.3f}",
                "所需物理長度 (mm)": f"{length:.3f}",
                "與參考差異 (mm)": f"{length - lengths[ref_line_type]:.3f}",
                "與參考差異 (%)": f"{((length / lengths[ref_line_type] - 1) * 100):.2f}%"
            })
        
        df_calc = DataFrame(calc_data)
        dataframe(df_calc, use_container_width=True)
        
        # Skew 檢查
        markdown("### ⚠️ Skew 容限檢查")
        
        max_length_diff = max(lengths.values()) - min(lengths.values())
        max_delay_diff = max_length_diff * ref_line.propagation_delay_ps_per_mm
        
        intra_ok = max_delay_diff < spec.intra_pair_skew
        inter_ok = max_delay_diff < spec.inter_pair_skew
        
        col_skew1, col_skew2 = columns(2)
        
        with col_skew1:
            metric(
                "最大長度差異",
                f"{max_length_diff:.3f} mm",
                f"{max_delay_diff:.2f} ps 延遲差"
            )
        
        with col_skew2:
            if intra_ok and inter_ok:
                success(f"✅ 符合 {spec.name} Skew 規格")
            elif inter_ok:
                warning(f"⚠️ 符合 Inter-pair，但不符合 Intra-pair Skew")
            else:
                error(f"❌ 超出 {spec.name} Skew 規格")

# Tab 3: Skew 視覺化分析
with tab3:
    markdown('<h2 class="sub-header">Skew 效應視覺化分析</h2>', unsafe_allow_html=True)
    
    lines = calculate_transmission_lines(epsilon_r, height_mm, width_mm)
    
    # 建立圖表
    fig, axes = subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'傳輸線特性分析 (εr={epsilon_r}, h={height_mm}mm, w={width_mm}mm)', 
                 fontsize=16, fontweight='bold')
    
    # 圖1: 傳播速度比較
    ax1 = axes[0, 0]
    names = [line.name.split()[0] for line in lines.values()]
    velocities = [line.velocity_m_per_s/1e6 for line in lines.values()]
    colors = [line.color for line in lines.values()]
    bars1 = ax1.bar(names, velocities, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('傳播速度 (Mm/s)', fontsize=11)
    ax1.set_title('訊號傳播速度比較', fontsize=12, fontweight='bold')
    ax1.axhline(y=C_M_PER_S/1e6, color='red', linestyle='--', label='光速 (真空)')
    ax1.legend()
    for bar, v in zip(bars1, velocities):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{v:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # 圖2: 延遲比較
    ax2 = axes[0, 1]
    delays = [line.propagation_delay_ps_per_mm for line in lines.values()]
    bars2 = ax2.bar(names, delays, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('延遲 (ps/mm)', fontsize=11)
    ax2.set_title('傳播延遲比較', fontsize=12, fontweight='bold')
    for bar, d in zip(bars2, delays):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{d:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # 圖3: 不同長度下的延遲累積
    ax3 = axes[1, 0]
    lengths_range = linspace(0, 200, 100)  # 0-200mm
    for name, line in lines.items():
        total_delay = lengths_range * line.propagation_delay_ps_per_mm
        ax3.plot(lengths_range, total_delay, label=line.name, 
                color=line.color, linewidth=2.5, marker='o', markersize=3, markevery=10)
    ax3.set_xlabel('物理長度 (mm)', fontsize=11)
    ax3.set_ylabel('總延遲 (ps)', fontsize=11)
    ax3.set_title('長度 vs 延遲關係', fontsize=12, fontweight='bold')
    ax3.legend(loc='upper left', fontsize=9)
    ax3.grid(True, alpha=0.3)
    
    # 圖4: Skew 累積誤差（以Stripline為基準）
    ax4 = axes[1, 1]
    ref_delay_sl = lengths_range * lines["Stripline"].propagation_delay_ps_per_mm
    for name, line in lines.items():
        if name != "Stripline":
            total_delay = lengths_range * line.propagation_delay_ps_per_mm
            skew = total_delay - ref_delay_sl
            ax4.plot(lengths_range, skew, label=f'{line.name} vs Stripline', 
                    color=line.color, linewidth=2.5, marker='s', markersize=3, markevery=10)
    
    # 加入介面Skew限制線
    for spec_name, spec in list(INTERFACE_SPECS.items())[:3]:  # 只顯示前3個避免太亂
        ax4.axhline(y=spec.intra_pair_skew, color='gray', linestyle='--', alpha=0.5)
        ax4.text(200, spec.intra_pair_skew, f'{spec_name} limit', 
                fontsize=8, va='bottom', ha='right', alpha=0.7)
    
    ax4.set_xlabel('物理長度 (mm)', fontsize=11)
    ax4.set_ylabel('Skew (ps)', fontsize=11)
    ax4.set_title('相對於 Stripline 的 Skew 累積', fontsize=12, fontweight='bold')
    ax4.legend(loc='upper left', fontsize=9)
    ax4.grid(True, alpha=0.3)
    ax4.axhline(y=0, color='black', linewidth=1)
    
    tight_layout()
    pyplot(fig)
    
    # 介面相容性分析
    markdown("### 各介面在不同長度下的層別混用風險")
    
    risk_data = []
    test_lengths = [50, 100, 150, 200]
    
    for length in test_lengths:
        ref_delay = length * lines["Stripline"].propagation_delay_ps_per_mm
        for name, line in lines.items():
            if name != "Stripline":
                actual_delay = length * line.propagation_delay_ps_per_mm
                skew = abs(actual_delay - ref_delay)
                
                for spec_name, spec in INTERFACE_SPECS.items():
                    risk_level = "✅ 安全" if skew < spec.intra_pair_skew else ("⚠️ 警告" if skew < spec.inter_pair_skew else "❌ 超規")
                    risk_data.append({
                        "長度(mm)": length,
                        "比較": f"{line.name.split()[0]} vs Stripline",
                        "介面": spec_name,
                        "Skew(ps)": f"{skew:.2f}",
                        "Intra限制(ps)": spec.intra_pair_skew,
                        "風險": risk_level
                    })
    
    df_risk = DataFrame(risk_data)
    
    # 篩選顯示
    selected_risk_iface = multiselect(
        "選擇要顯示的介面",
        list(INTERFACE_SPECS.keys()),
        default=["PCIe 4.0", "DDR4-3200", "USB 3.2 Gen2"]
    )
    
    if selected_risk_iface:
        df_filtered = df_risk[df_risk["介面"].isin(selected_risk_iface)]
        dataframe(df_filtered, use_container_width=True, height=400)

# Tab 4: 進階補償設計
with tab4:
    markdown('<h2 class="sub-header">蛇線補償設計工具</h2>', unsafe_allow_html=True)
    
    markdown("""
    <div class="info-box">
    當不同訊號需要匹配電氣長度時，較快的傳輸線（如Microstrip）需要加入蛇線（Trombone/Zig-zag）
    來增加物理長度，以匹配較慢傳輸線（如Stripline）的延遲。
    </div>
    """, unsafe_allow_html=True)
    
    col_adv1, col_adv2 = columns([1, 1])
    
    with col_adv1:
        markdown("### 補償參數設定")
        
        fast_line = selectbox(
            "較快傳輸線（需加長）",
            ["Microstrip", "Waveguide"],
            index=0
        )
        
        slow_line = selectbox(
            "較慢傳輸線（基準）",
            ["Stripline"],
            index=0
        )
        
        base_length = number_input(
            "基準走線長度 (mm)",
            min_value=10.0,
            max_value=500.0,
            value=100.0,
            step=5.0
        )
        
        serpentine_amplitude = slider(
            "蛇線振幅 (mm)",
            min_value=0.5,
            max_value=5.0,
            value=2.0,
            step=0.1,
            help="蛇線的垂直擺幅，過大會增加串擾"
        )
        
        serpentine_gap = slider(
            "蛇線間距 (mm)",
            min_value=0.2,
            max_value=2.0,
            value=0.5,
            step=0.1,
            help="蛇線平行段間距，建議 > 3倍線寬"
        )
    
    with col_adv2:
        markdown("### 計算結果")
        
        lines = calculate_transmission_lines(epsilon_r, height_mm, width_mm)
        
        fast = lines[fast_line]
        slow = lines[slow_line]
        
        # 計算所需補償
        slow_delay = base_length * slow.propagation_delay_ps_per_mm
        fast_length_needed = slow_delay / fast.propagation_delay_ps_per_mm
        length_compensation = fast_length_needed - base_length
        
        # 蛇線幾何計算
        # 簡化模型：每個週期增加 2*振幅 的長度，實際走線長度為斜邊
        period = 2 * serpentine_gap  # 一個完整週期的水平長度
        segment_length = sqrt(serpentine_amplitude**2 + (period/2)**2)
        extra_per_period = 2 * segment_length - period
        
        if extra_per_period > 0:
            periods_needed = length_compensation / extra_per_period
            horizontal_space = periods_needed * period
        else:
            periods_needed = 0
            horizontal_space = 0
        
        metric(
            "所需物理長度補償",
            f"{length_compensation:.3f} mm",
            f"總長度: {fast_length_needed:.2f} mm"
        )
        
        metric(
            "蛇線週期數",
            f"{periods_needed:.1f} 個",
            f"每週期額外長度: {extra_per_period:.3f} mm"
        )
        
        metric(
            "所需水平空間",
            f"{horizontal_space:.2f} mm",
            f"約 {horizontal_space/10:.1f} 個週期"
        )
        
        # 檢查可行性
        if horizontal_space > base_length * 0.5:
            warning("⚠️ 蛇線所需空間過大，建議：\n- 增加振幅\n- 或改用較慢層別走線")
        elif periods_needed < 1:
            info("ℹ️ 補償量極小，可能無需蛇線")
        else:
            success("✅ 設計可行")
    
    # 視覺化蛇線
    markdown("### 蛇線結構示意圖")
    
    if periods_needed > 0 and periods_needed < 100:  # 限制顯示數量
        fig_serp, ax_serp = subplots(figsize=(12, 4))
        
        # 繪製原始直線
        ax_serp.plot([0, base_length], [0, 0], 'b-', linewidth=3, label='原始走線', alpha=0.5)
        
        # 繪製蛇線
        n_periods = min(int(ceil(periods_needed)), 20)  # 最多顯示20個週期
        x_points = [0]
        y_points = [0]
        
        current_x = 0
        for i in range(n_periods):
            # 上半段
            current_x += period/2
            x_points.append(current_x)
            y_points.append(serpentine_amplitude if i % 2 == 0 else -serpentine_amplitude)
            # 下半段
            current_x += period/2
            x_points.append(current_x)
            y_points.append(0)
        
        # 如果還有剩餘長度
        remaining = fast_length_needed - current_x
        if remaining > 0:
            x_points.append(current_x + remaining)
            y_points.append(0)
        
        ax_serp.plot(x_points, y_points, 'r-', linewidth=2, label='蛇線補償後')
        ax_serp.fill_between(x_points, y_points, alpha=0.2, color='red')
        
        ax_serp.set_xlabel('長度 (mm)', fontsize=11)
        ax_serp.set_ylabel('偏移 (mm)', fontsize=11)
        ax_serp.set_title('蛇線補償結構示意 (簡化模型)', fontsize=12, fontweight='bold')
        ax_serp.legend()
        ax_serp.grid(True, alpha=0.3)
        ax_serp.axis('equal')
        
        pyplot(fig_serp)
    
    # 設計建議
    markdown("### 💡 設計建議")
    
    col_tip1, col_tip2, col_tip3 = columns(3)
    
    with col_tip1:
        markdown("""
        <div class="success-box">
        <b>層別選擇</b><br>
        • 優先統一走線層別<br>
        • 避免表層與內層混用<br>
        • 高速訊號優先使用Stripline
        </div>
        """, unsafe_allow_html=True)
    
    with col_tip2:
        markdown("""
        <div class="warning-box">
        <b>蛇線設計</b><br>
        • 振幅建議 3-5倍線寬<br>
        • 間距建議 >3倍線寬<br>
        • 避免90度轉角，使用45度
        </div>
        """, unsafe_allow_html=True)
    
    with col_tip3:
        markdown("""
        <div class="info-box">
        <b>驗證方法</b><br>
        • 使用SI模擬工具<br>
        • 測試實際板子的TDR<br>
        • 驗證眼圖與 jitter
        </div>
        """, unsafe_allow_html=True)

# 頁尾
markdown("---")
markdown("<p style='text-align: center; color: #888;'>PCB High-Speed Signal Length Matching Calculator | 基於傳輸線理論與實務設計經驗</p>", unsafe_allow_html=True)
