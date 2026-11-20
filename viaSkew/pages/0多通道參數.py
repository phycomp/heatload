from streamlit import columns, dataframe, expander, info, markdown, metric, multiselect, number_input, pyplot, radio, set_page_config, sidebar, slider, tabs
from matplotlib.pyplot import cm, subplots, tight_layout
from numpy import arange, cos, diff, exp, linspace, log10, logspace, mean, pi, random, sin, sqrt, std, sum, zeros_like
#import streamlit as st
from fontUtil2 import 配置中文, 羅列字型  #, 配置字型
配置中文()
羅列字型()
#配置字型()
from numpy.random import normal
#import numpy as np
#import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import matplotlib.patches as mpatches
from io import BytesIO
set_page_config(page_title="PCB Trace Skew 模擬器", layout="wide")

# ========== 自定義 CSS ==========
markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1a1a2e;
        text-align: center;
        margin-bottom: 10px;
    }
    .subtitle {
        font-size: 1rem;
        color: #555;
        text-align: center;
        margin-bottom: 30px;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 15px;
        color: white;
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.85rem;
        opacity: 0.9;
    }
    .section-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: yellow;
        border-left: 4px solid #667eea;
        padding-left: 10px;
        margin-top: 20px;
        margin-bottom: 15px;
    }
    .info-box {
        background-color: black;
        border-radius: 8px;
        padding: 12px;
        border-left: 3px solid #667eea;
    }
    .warning-box {
        background-color: black;
        border-radius: 8px;
        padding: 12px;
        border-left: 3px solid #ffc107;
    }
    .success-box {
        background-color: #d4edda;
        border-radius: 8px;
        padding: 12px;
        border-left: 3px solid #28a745;
    }
    .danger-box {
        background-color: black;
        border-radius: 8px
        color: red;
        padding: 12px;
        border-left: 3px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# ========== 材料參數資料庫 ==========
MATERIALS = {
    "FR-4 (標準)": {"Dk": 4.3, "Df": 0.020, "TCDk": -0.015, "TCDf": 0.002, "cost": 1.0, "max_freq": 5},
    "FR-4 (低損耗)": {"Dk": 4.2, "Df": 0.010, "TCDk": -0.012, "TCDf": 0.001, "cost": 1.5, "max_freq": 10},
    "Megtron 6": {"Dk": 3.7, "Df": 0.002, "TCDk": -0.010, "TCDf": 0.0005, "cost": 3.0, "max_freq": 50},
    "Rogers RO4350B": {"Dk": 3.48, "Df": 0.0037, "TCDk": -0.005, "TCDf": 0.0003, "cost": 4.0, "max_freq": 30},
    "Rogers RO4003C": {"Dk": 3.38, "Df": 0.0027, "TCDk": -0.005, "TCDf": 0.0002, "cost": 4.5, "max_freq": 40},
    "Nelco N4000-13": {"Dk": 3.7, "Df": 0.009, "TCDk": -0.008, "TCDf": 0.0008, "cost": 2.5, "max_freq": 15},
    "Panasonic M6NE": {"Dk": 3.4, "Df": 0.001, "TCDk": -0.008, "TCDf": 0.0003, "cost": 3.5, "max_freq": 56},
    "Tachyon 100G": {"Dk": 3.0, "Df": 0.001, "TCDk": -0.005, "TCDf": 0.0002, "cost": 5.0, "max_freq": 100},
}

# ========== 預設 Trace 形狀 ==========
def generate_trace_shape(shape_type, length_mm, n_points=200):
    """生成不同幾何形狀的 trace 座標"""
    x = linspace(0, length_mm, n_points)
    
    if shape_type == "直線":
        y = zeros_like(x)
    elif shape_type == "蛇形 (Serpentine)":
        amplitude = 2.0  # mm
        period = 10.0    # mm
        y = amplitude * sin(2 * pi * x / period)
    elif shape_type == "手風琴 (Accordion)":
        amplitude = 1.5
        period = 8.0
        y = amplitude * sin(2 * pi * x / period)
    elif shape_type == "階梯":
        y = zeros_like(x)
        step_size = length_mm / 8
        for i in range(1, 8):
            mask = (x >= i * step_size) & (x < (i + 0.5) * step_size)
            y[mask] = 2.0 if i % 2 == 1 else -2.0
    elif shape_type == "波浪":
        amplitude = 1.0
        period = 5.0
        y = amplitude * sin(2 * pi * x / period) + 0.5 * amplitude * sin(4 * pi * x / period)
    elif shape_type == "螺旋":
        t = linspace(0, 4 * pi, n_points)
        r = linspace(0, length_mm / (2 * pi), n_points)
        x = r * cos(t)
        y = r * sin(t)
    else:
        y = zeros_like(x)
    
    return x, y

def calculate_trace_length(x, y):
    """計算 trace 實際長度"""
    dx = diff(x)
    dy = diff(y)
    return sum(sqrt(dx**2 + dy**2))

# ========== 物理計算 ==========
def propagation_speed(Dk, c=299.792458):  # c in mm/ns
    """信號傳播速度 mm/ns"""
    return c / sqrt(Dk)

def propagation_delay(length_mm, Dk):
    """傳播延遲 ps"""
    v = propagation_speed(Dk)  # mm/ns
    return (length_mm / v) * 1000  # ps

def frequency_dependent_Dk(Dk_1GHz, freq_GHz, TCDk):
    """頻率相關 Dk (簡化模型)"""
    return Dk_1GHz * (1 + TCDk * log10(freq_GHz + 0.1))

def frequency_dependent_Df(Df_1GHz, freq_GHz, TCDf):
    """頻率相關 Df"""
    return Df_1GHz * (1 + TCDf * log10(freq_GHz + 0.1))

def attenuation_db(length_mm, freq_GHz, Dk, Df):
    """插入損耗 dB (簡化模型)"""
    # 簡化: alpha ≈ (π * f * sqrt(Dk) * Df) / c
    c = 3e8  # m/s
    f = freq_GHz * 1e9
    alpha = (pi * f * sqrt(Dk) * Df) / c  # Np/m
    length_m = length_mm / 1000
    return 20 * log10(exp(alpha * length_m))  # dB

def skin_depth(freq_GHz, Dk, Df):
    """趨膚深度 mm"""
    mu0 = 4 * pi * 1e-7
    sigma = 2 * pi * freq_GHz * 1e9 * Dk * 8.854e-12 * Df
    return sqrt(2 / (mu0 * sigma)) * 1000  # mm

# ========== 側邊欄控制面板 ==========
with sidebar:
    markdown("## ⚙️ 控制面板")
    
    # --- 通道數量 ---
    markdown("### 📡 通道配置")
    n_channels = slider("通道數量 (N)", 2, 16, 4)
    
    # --- 材料選擇 ---
    markdown("### 🧪 基板材料")
    material_name = radio("選擇材料", list(MATERIALS.keys()), horizontal=True)
    mat = MATERIALS[material_name]
    
    col1, col2 = columns(2)
    with col1:
        Dk = number_input("Dk (1GHz)", 1.0, 10.0, mat["Dk"], 0.01)
    with col2:
        Df = number_input("Df (1GHz)", 0.0001, 0.100, mat["Df"], 0.0001, format="%.4f")
    
    col3, col4 = columns(2)
    with col3:
        TCDk = number_input("TCDk", -0.05, 0.05, mat["TCDk"], 0.001)
    with col4:
        TCDf = number_input("TCDf", 0.0, 0.01, mat["TCDf"], 0.0001)
    
    # --- 環境參數 ---
    markdown("### 🌡️ 環境參數")
    temperature = slider("溫度 (°C)", -40, 150, 25)
    
    # --- 頻率範圍 ---
    markdown("### 📊 頻率範圍")
    freq_min = number_input("最小頻率 (GHz)", 0.01, 100.0, 0.1, 0.1)
    freq_max = number_input("最大頻率 (GHz)", 0.1, 200.0, 50.0, 0.1)
    
    # --- Skew 閾值 ---
    markdown("### 🎯 Skew 規格")
    skew_threshold_ps = number_input("Skew 閾值 (ps)", 0.1, 100.0, 5.0, 0.1)
    
    # --- 各通道設定 ---
    markdown("### 🛤️ 各通道 Trace 設定")
    
    channel_configs = []
    for i in range(n_channels):
        with expander(f"通道 {i+1} 設定", expanded=(i==0)):
            shape = radio(
                f"形狀 {i+1}", 
                ["直線", "蛇形 (Serpentine)", "手風琴 (Accordion)", "階梯", "波浪", "螺旋"],
                key=f"shape_{i}"
            , horizontal=True)
            length = slider(f"目標長度 {i+1} (mm)", 10, 500, 100 + i*5, key=f"len_{i}")
            width = slider(f"線寬 {i+1} (mil)", 1, 20, 5, key=f"width_{i}")
            layer = radio(f"層別 {i+1}", ["Top", "Inner1", "Inner2", "Bottom"], key=f"layer_{i}", horizontal=True)
            channel_configs.append({"shape": shape, "length": length, "width": width, "layer": layer})

# ========== 溫度修正 Dk/Df ==========
Dk_temp = Dk * (1 + TCDk * (temperature - 25))
Df_temp = Df * (1 + TCDf * (temperature - 25))

# ========== 主畫面 ==========

# --- 頂部指標卡 ---
col1, col2, col3, col4, col5 = columns(5)

v_prop = propagation_speed(Dk_temp)
with col1:
    markdown(f'''<div class="metric-card">
        <div class="metric-value">{v_prop:.1f}</div>
        <div class="metric-label">傳播速度 (mm/ns)</div>
    </div>''', unsafe_allow_html=True)

with col2:
    markdown(f'''<div class="metric-card">
        <div class="metric-value">{Dk_temp:.3f}</div>
        <div class="metric-label">Dk @ {temperature}°C</div>
    </div>''', unsafe_allow_html=True)

with col3:
    markdown(f'''<div class="metric-card">
        <div class="metric-value">{Df_temp:.4f}</div>
        <div class="metric-label">Df @ {temperature}°C</div>
    </div>''', unsafe_allow_html=True)

with col4:
    markdown(f'''<div class="metric-card">
        <div class="metric-value">{n_channels}</div>
        <div class="metric-label">通道數量</div>
    </div>''', unsafe_allow_html=True)

with col5:
    markdown(f'''<div class="metric-card">
        <div class="metric-value">{skew_threshold_ps:.1f} ps</div>
        <div class="metric-label">Skew 閾值</div>
    </div>''', unsafe_allow_html=True)

markdown("---")

# ========== Tab 分頁 ==========
tab1, tab2, tab3, tab4, tab5 = tabs([
    "📐 Trace 幾何視覺化", 
    "⏱️ Skew 分析", 
    "📈 頻段色散分析",
    "📊 材料比較",
    "🔬 進階參數"
])

# ========== Tab 1: Trace 幾何視覺化 ==========
with tab1:
    markdown('<div class="section-title">N-Channel Trace 幾何形狀與長度分析</div>', unsafe_allow_html=True)
    
    fig, axes = subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
    
    colors = cm.tab10(linspace(0, 1, n_channels))
    trace_data = []
    
    # 上圖: Trace 形狀
    ax1 = axes[0]
    max_y = 0
    
    for i, config in enumerate(channel_configs):
        x, y_base = generate_trace_shape(config["shape"], config["length"])
        # 垂直偏移各通道
        y_offset = i * 8
        y = y_base + y_offset
        
        actual_length = calculate_trace_length(x, y)
        delay = propagation_delay(actual_length, Dk_temp)
        
        trace_data.append({
            "channel": i+1,
            "shape": config["shape"],
            "target_length": config["length"],
            "actual_length": actual_length,
            "delay_ps": delay,
            "x": x,
            "y": y,
            "color": colors[i]
        })
        
        ax1.plot(x, y, color=colors[i], linewidth=2, label=f'Ch{i+1}: {config["shape"]} ({actual_length:.1f} mm)')
        ax1.fill_between(x, y - 0.3, y + 0.3, color=colors[i], alpha=0.15)
        
        # 標註長度
        mid_idx = len(x) // 2
        ax1.annotate(f'{actual_length:.1f}mm\n{delay:.1f}ps', 
                    xy=(x[mid_idx], y[mid_idx]), 
                    fontsize=8, ha='center', va='center',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=colors[i], alpha=0.8))
        
        max_y = max(max_y, y_offset + 5)
    
    ax1.set_xlabel('X (mm)', fontsize=12)
    ax1.set_ylabel('Y (mm, 通道偏移)', fontsize=12)
    ax1.set_title('N-Channel Trace 幾何形狀 (垂直偏移顯示)', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(-3, max_y + 3)
    
    # 下圖: 長度與延遲條形圖
    ax2 = axes[1]
    ch_labels = [f'Ch{i+1}' for i in range(n_channels)]
    lengths = [d["actual_length"] for d in trace_data]
    delays = [d["delay_ps"] for d in trace_data]
    
    x_pos = arange(n_channels)
    bars = ax2.bar(x_pos, delays, color=colors, alpha=0.7, edgecolor='black', linewidth=1)
    
    # 標註數值
    for bar, delay, length in zip(bars, delays, lengths):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{delay:.1f} ps\n({length:.1f} mm)',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Skew 閾值線
    ax2.axhline(y=skew_threshold_ps, color='red', linestyle='--', linewidth=2, label=f'Skew 閾值: {skew_threshold_ps} ps')
    
    # 標註最大 Skew
    max_delay = max(delays)
    min_delay = min(delays)
    max_skew = max_delay - min_delay
    ax2.annotate(f'最大 Skew: {max_skew:.1f} ps', 
                xy=(n_channels-1, max_delay), 
                xytext=(n_channels-0.5, max_delay + 20),
                fontsize=11, fontweight='bold', color='red',
                arrowprops=dict(arrowstyle='->', color='red', lw=2))
    
    ax2.set_xlabel('通道', fontsize=12)
    ax2.set_ylabel('傳播延遲 (ps)', fontsize=12)
    ax2.set_title('各通道傳播延遲比較', fontsize=14, fontweight='bold')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(ch_labels)
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    tight_layout()
    pyplot(fig)
    
    # Skew 狀態判斷
    if max_skew <= skew_threshold_ps:
        markdown(f'<div class="success-box">✅ <b>Skew 合格</b>：最大 Skew = {max_skew:.2f} ps ≤ 閾值 {skew_threshold_ps:.1f} ps</div>', unsafe_allow_html=True)
    else:
        markdown(f'<div class="danger-box">❌ <b>Skew 超標</b>：最大 Skew = {max_skew:.2f} ps > 閾值 {skew_threshold_ps:.1f} ps（需調整 {max_skew - skew_threshold_ps:.2f} ps）</div>', unsafe_allow_html=True)
    
    # 詳細數據表
    markdown("<br>", unsafe_allow_html=True)
    markdown('<div class="section-title">通道詳細數據</div>', unsafe_allow_html=True)
    
    df_data = []
    for d in trace_data:
        df_data.append({
            "通道": f"Ch{d['channel']}",
            "形狀": d['shape'],
            "目標長度 (mm)": f"{d['target_length']:.1f}",
            "實際長度 (mm)": f"{d['actual_length']:.2f}",
            "傳播延遲 (ps)": f"{d['delay_ps']:.2f}",
            "與最長通道差 (ps)": f"{max(delays) - d['delay_ps']:.2f}",
            "狀態": "✅" if (max(delays) - d['delay_ps']) <= skew_threshold_ps else "❌"
        })
    
    dataframe(df_data, width='stretch', hide_index=True)

# ========== Tab 2: Skew 分析 ==========
with tab2:
    markdown('<div class="section-title">Skew 深度分析與蛇形繞線補償建議</div>', unsafe_allow_html=True)
    
    col_left, col_right = columns([1, 1])
    
    with col_left:
        markdown("#### Skew 來源分析")
        
        # 計算各種 Skew 貢獻
        max_len = max([d["actual_length"] for d in trace_data])
        skew_sources = []
        
        for d in trace_data:
            len_diff = max_len - d["actual_length"]
            len_skew = propagation_delay(len_diff, Dk_temp) if len_diff > 0 else 0
            skew_sources.append({
                "通道": f"Ch{d['channel']}",
                "長度差 (mm)": len_diff,
                "長度 Skew (ps)": len_skew,
                "需要補償": len_diff > 0
            })
        
        dataframe(skew_sources, width='stretch', hide_index=True)
        
        # 蛇形繞線補償計算
        markdown("#### 🐍 蛇形繞線補償計算")
        
        serpentine_amp = slider("蛇形振幅 (mm)", 0.5, 5.0, 2.0, 0.1)
        serpentine_period = slider("蛇形週期 (mm)", 2.0, 20.0, 8.0, 0.5)
        
        # 計算蛇形繞線的額外長度效率
        # 一個完整週期的額外長度 ≈ 4 * amplitude (近似)
        extra_per_period = 4 * serpentine_amp  # mm
        
        compensation_data = []
        for d in trace_data:
            len_diff = max_len - d["actual_length"]
            if len_diff > 0:
                n_periods_needed = len_diff / extra_per_period
                compensation_length = n_periods_needed * serpentine_period
                
                compensation_data.append({
                    "通道": f"Ch{d['channel']}",
                    "需補償長度 (mm)": f"{len_diff:.2f}",
                    "蛇形週期數": f"{n_periods_needed:.1f}",
                    "蛇形段總長 (mm)": f"{compensation_length:.1f}",
                    "建議位置": "Source 端"
                })
        
        if compensation_data:
            dataframe(compensation_data, width='stretch', hide_index=True)
        else:
            info("所有通道長度已匹配，無需蛇形繞線補償")
    
    with col_right:
        markdown("#### Skew 分佈圖")
        
        fig_skew, ax_skew = subplots(figsize=(8, 6))
        
        delays = [d["delay_ps"] for d in trace_data]
        labels = [f"Ch{d['channel']}" for d in trace_data]
        
        # 箱型圖 + 散點
        bp = ax_skew.boxplot([delays], positions=[1], widths=0.3, patch_artist=True,
                             boxprops=dict(facecolor='lightblue', alpha=0.7),
                             medianprops=dict(color='red', linewidth=2))
        
        # 散點
        jitter = normal(0, 0.05, n_channels)
        ax_skew.scatter([1 + jitter[i] for i in range(n_channels)], delays, 
                       c=colors, s=100, zorder=5, edgecolors='black', linewidth=1)
        
        # 標註每個點
        for i, (label, delay) in enumerate(zip(labels, delays)):
            ax_skew.annotate(label, xy=(1 + jitter[i], delay), 
                           xytext=(1.25, delay), fontsize=10,
                           arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))
        
        ax_skew.axhline(y=mean(delays), color='green', linestyle='--', linewidth=1, label=f'平均: {mean(delays):.1f} ps')
        ax_skew.axhline(y=mean(delays) + skew_threshold_ps/2, color='orange', linestyle=':', linewidth=1, label=f'+{skew_threshold_ps/2:.1f} ps')
        ax_skew.axhline(y=mean(delays) - skew_threshold_ps/2, color='orange', linestyle=':', linewidth=1, label=f'-{skew_threshold_ps/2:.1f} ps')
        
        ax_skew.set_ylabel('傳播延遲 (ps)', fontsize=12)
        ax_skew.set_title('N-Channel Skew 分佈', fontsize=14, fontweight='bold')
        ax_skew.set_xticks([1])
        ax_skew.set_xticklabels(['所有通道'])
        ax_skew.legend(loc='upper left')
        ax_skew.grid(True, alpha=0.3)
        
        tight_layout()
        pyplot(fig_skew)
        
        # 統計資訊
        markdown("<br>", unsafe_allow_html=True)
        markdown("#### 📊 Skew 統計")
        
        col_s1, col_s2, col_s3 = columns(3)
        with col_s1:
            metric("平均延遲", f"{mean(delays):.2f} ps")
        with col_s2:
            metric("標準差", f"{std(delays):.2f} ps")
        with col_s3:
            metric("變異係數", f"{std(delays)/mean(delays)*100:.2f}%")

# ========== Tab 3: 頻段色散分析 ==========
with tab3:
    markdown('<div class="section-title">頻率相關 Dk/Df 與色散分析</div>', unsafe_allow_html=True)
    
    freq_range = logspace(log10(freq_min), log10(freq_max), 200)
    
    # 計算頻率相關參數
    Dk_freq = [frequency_dependent_Dk(Dk, f, TCDk) for f in freq_range]
    Df_freq = [frequency_dependent_Df(Df, f, TCDf) for f in freq_range]
    v_freq = [propagation_speed(dk) for dk in Dk_freq]
    
    # 取第一個通道的長度作為基準
    ref_length = trace_data[0]["actual_length"]
    delay_freq = [propagation_delay(ref_length, dk) for dk in Dk_freq]
    
    # 各通道在不同頻率下的延遲差（Skew）
    fig_freq, axes_freq = subplots(2, 2, figsize=(14, 10))
    
    # 圖1: Dk vs 頻率
    ax = axes_freq[0, 0]
    ax.semilogx(freq_range, Dk_freq, 'b-', linewidth=2)
    ax.fill_between(freq_range, Dk_freq, alpha=0.2, color='blue')
    ax.set_xlabel('頻率 (GHz)', fontsize=11)
    ax.set_ylabel('Dk', fontsize=11)
    ax.set_title(f'Dk 頻率響應 ({material_name})', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, which='both')
    ax.axvline(x=1, color='red', linestyle='--', alpha=0.5, label='1 GHz')
    ax.legend()
    
    # 圖2: Df vs 頻率
    ax = axes_freq[0, 1]
    ax.semilogx(freq_range, Df_freq, 'r-', linewidth=2)
    ax.fill_between(freq_range, Df_freq, alpha=0.2, color='red')
    ax.set_xlabel('頻率 (GHz)', fontsize=11)
    ax.set_ylabel('Df', fontsize=11)
    ax.set_title(f'Df 頻率響應 (損耗因子)', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, which='both')
    ax.axvline(x=1, color='blue', linestyle='--', alpha=0.5, label='1 GHz')
    ax.legend()
    
    # 圖3: 傳播速度 vs 頻率
    ax = axes_freq[1, 0]
    ax.semilogx(freq_range, v_freq, 'g-', linewidth=2)
    ax.fill_between(freq_range, v_freq, alpha=0.2, color='green')
    ax.set_xlabel('頻率 (GHz)', fontsize=11)
    ax.set_ylabel('傳播速度 (mm/ns)', fontsize=11)
    ax.set_title('傳播速度頻率響應', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, which='both')
    
    # 圖4: 各通道 Skew vs 頻率
    ax = axes_freq[1, 1]
    
    # 計算每個通道相對於最長通道的 Skew
    for i, d in enumerate(trace_data):
        channel_delay_freq = [propagation_delay(d["actual_length"], dk) for dk in Dk_freq]
        ref_delay_freq = [propagation_delay(max([td["actual_length"] for td in trace_data]), dk) for dk in Dk_freq]
        skew_vs_freq = [ref - ch for ref, ch in zip(ref_delay_freq, channel_delay_freq)]
        
        ax.semilogx(freq_range, skew_vs_freq, color=colors[i], linewidth=2, 
                   label=f'Ch{d["channel"]}')
    
    ax.axhline(y=skew_threshold_ps, color='red', linestyle='--', linewidth=2, label=f'閾值: {skew_threshold_ps} ps')
    ax.axhline(y=-skew_threshold_ps, color='red', linestyle='--', linewidth=2)
    ax.fill_between(freq_range, -skew_threshold_ps, skew_threshold_ps, alpha=0.1, color='green')
    
    ax.set_xlabel('頻率 (GHz)', fontsize=11)
    ax.set_ylabel('Skew (ps)', fontsize=11)
    ax.set_title('頻率相關 Skew 分析', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, which='both')
    ax.legend(loc='upper left', fontsize=8)
    
    tight_layout()
    pyplot(fig_freq)
    
    # 色散分析文字說明
    markdown("<br>", unsafe_allow_html=True)
    
    # 計算色散指標
    dk_variation = (max(Dk_freq) - min(Dk_freq)) / Dk_freq[0] * 100
    
    col_d1, col_d2 = columns(2)
    with col_d1:
        markdown(f'<div class="info-box">📌 <b>色散程度</b>：Dk 在 {freq_min}-{freq_max} GHz 範圍變化 {dk_variation:.2f}%<br>• 低色散材料 (Df&lt;0.005) 適合 &gt;10 GHz 設計<br>• 標準 FR-4 在 &gt;5 GHz 會有顯著色散</div>', unsafe_allow_html=True)
    
    with col_d2:
        # 找出 Skew 最差的頻率點
        max_skew_freq = 0
        worst_freq = freq_range[0]
        for f_idx, f in enumerate(freq_range):
            dk = Dk_freq[f_idx]
            delays_at_f = [propagation_delay(d["actual_length"], dk) for d in trace_data]
            skew_at_f = max(delays_at_f) - min(delays_at_f)
            if skew_at_f > max_skew_freq:
                max_skew_freq = skew_at_f
                worst_freq = f
        
        markdown(f'<div class="warning-box">⚠️ <b>最差 Skew 頻率點</b>：{worst_freq:.2f} GHz<br>• 該頻率下最大 Skew = {max_skew_freq:.2f} ps<br>• 建議在此頻段加強長度匹配精度</div>', unsafe_allow_html=True)

# ========== Tab 4: 材料比較 ==========
with tab4:
    markdown('<div class="section-title">多材料 Dk/Df 比較分析</div>', unsafe_allow_html=True)
    
    # 選擇要比較的材料
    selected_materials = multiselect(
        "選擇要比較的材料",
        list(MATERIALS.keys()),
        default=["FR-4 (標準)", "Megtron 6", "Rogers RO4350B"],
        max_selections=6
    )
    
    if selected_materials:
        fig_mat, axes_mat = subplots(2, 2, figsize=(14, 10))
        
        mat_colors = cm.Set2(linspace(0, 1, len(selected_materials)))
        
        for idx, mat_name in enumerate(selected_materials):
            mat_data = MATERIALS[mat_name]
            dk_base = mat_data["Dk"]
            df_base = mat_data["Df"]
            tcdk = mat_data["TCDk"]
            tcdf = mat_data["TCDf"]
            
            dk_f = [frequency_dependent_Dk(dk_base, f, tcdk) for f in freq_range]
            df_f = [frequency_dependent_Df(df_base, f, tcdf) for f in freq_range]
            v_f = [propagation_speed(dk) for dk in dk_f]
            
            # Dk 比較
            axes_mat[0, 0].semilogx(freq_range, dk_f, color=mat_colors[idx], linewidth=2, label=mat_name)
            # Df 比較
            axes_mat[0, 1].semilogx(freq_range, df_f, color=mat_colors[idx], linewidth=2, label=mat_name)
            # 速度比較
            axes_mat[1, 0].semilogx(freq_range, v_f, color=mat_colors[idx], linewidth=2, label=mat_name)
            # 損耗比較 (以 100mm trace 為例)
            att_f = [attenuation_db(100, f, dk, df) for f, dk, df in zip(freq_range, dk_f, df_f)]
            axes_mat[1, 1].semilogx(freq_range, att_f, color=mat_colors[idx], linewidth=2, label=mat_name)
        
        axes_mat[0, 0].set_xlabel('頻率 (GHz)'); axes_mat[0, 0].set_ylabel('Dk')
        axes_mat[0, 0].set_title('Dk 比較'); axes_mat[0, 0].legend(); axes_mat[0, 0].grid(True, alpha=0.3, which='both')
        
        axes_mat[0, 1].set_xlabel('頻率 (GHz)'); axes_mat[0, 1].set_ylabel('Df')
        axes_mat[0, 1].set_title('Df 比較'); axes_mat[0, 1].legend(); axes_mat[0, 1].grid(True, alpha=0.3, which='both')
        
        axes_mat[1, 0].set_xlabel('頻率 (GHz)'); axes_mat[1, 0].set_ylabel('速度 (mm/ns)')
        axes_mat[1, 0].set_title('傳播速度比較'); axes_mat[1, 0].legend(); axes_mat[1, 0].grid(True, alpha=0.3, which='both')
        
        axes_mat[1, 1].set_xlabel('頻率 (GHz)'); axes_mat[1, 1].set_ylabel('插入損耗 (dB/100mm)')
        axes_mat[1, 1].set_title('插入損耗比較 (100mm trace)'); axes_mat[1, 1].legend(); axes_mat[1, 1].grid(True, alpha=0.3, which='both')
        
        tight_layout()
        pyplot(fig_mat)
        
        # 材料推薦表
        markdown("<br>", unsafe_allow_html=True)
        markdown("#### 📋 材料特性總覽")
        
        mat_summary = []
        for mat_name in selected_materials:
            mat_data = MATERIALS[mat_name]
            mat_summary.append({
                "材料": mat_name,
                "Dk (1GHz)": f"{mat_data['Dk']:.2f}",
                "Df (1GHz)": f"{mat_data['Df']:.4f}",
                "適用頻率 (GHz)": f"≤{mat_data['max_freq']}",
                "相對成本": f"{mat_data['cost']:.1f}x",
                "推薦應用": "高頻/低損耗" if mat_data['Df'] < 0.005 else "一般高速" if mat_data['Df'] < 0.01 else "一般數位"
            })
        
        dataframe(mat_summary, width='stretch', hide_index=True)

# ========== Tab 5: 進階參數 ==========
with tab5:
    markdown('<div class="section-title">進階物理參數與趨膚效應</div>', unsafe_allow_html=True)
    
    col_a1, col_a2 = columns(2)
    
    with col_a1:
        markdown("#### 趨膚深度分析")
        
        # 計算各頻率的趨膚深度
        skin_depths = [skin_depth(f, Dk_temp, Df_temp) for f in freq_range]
        
        fig_skin, ax_skin = subplots(figsize=(8, 5))
        ax_skin.semilogx(freq_range, skin_depths, 'purple', linewidth=2)
        ax_skin.fill_between(freq_range, skin_depths, alpha=0.2, color='purple')
        ax_skin.set_xlabel('頻率 (GHz)', fontsize=12)
        ax_skin.set_ylabel('趨膚深度 (mm)', fontsize=12)
        ax_skin.set_title('趨膚深度 vs 頻率', fontsize=14, fontweight='bold')
        ax_skin.grid(True, alpha=0.3, which='both')
        
        # 標註一些關鍵點
        key_freqs = [1, 5, 10, 25, 50]
        for kf in key_freqs:
            if freq_min <= kf <= freq_max:
                sd = skin_depth(kf, Dk_temp, Df_temp)
                ax_skin.annotate(f'{sd:.3f}mm @ {kf}GHz', 
                               xy=(kf, sd), xytext=(kf*2, sd*1.5),
                               fontsize=9, arrowprops=dict(arrowstyle='->', color='gray'))
        
        tight_layout()
        pyplot(fig_skin)
    
    with col_a2:
        markdown("#### 插入損耗頻譜")
        
        # 計算各通道的插入損耗
        fig_att, ax_att = subplots(figsize=(8, 5))
        
        for i, d in enumerate(trace_data):
            att_channel = [attenuation_db(d["actual_length"], f, 
                          frequency_dependent_Dk(Dk_temp, f, TCDk),
                          frequency_dependent_Df(Df_temp, f, TCDf)) 
                          for f in freq_range]
            ax_att.semilogx(freq_range, att_channel, color=colors[i], linewidth=2,
                          label=f'Ch{d["channel"]} ({d["actual_length"]:.0f}mm)')
        
        ax_att.set_xlabel('頻率 (GHz)', fontsize=12)
        ax_att.set_ylabel('插入損耗 (dB)', fontsize=12)
        ax_att.set_title('各通道插入損耗', fontsize=14, fontweight='bold')
        ax_att.legend(fontsize=9)
        ax_att.grid(True, alpha=0.3, which='both')
        
        tight_layout()
        pyplot(fig_att)
    
    # 物理公式說明
    markdown("<br>", unsafe_allow_html=True)
    markdown("#### 📐 核心物理公式")
    
    markdown(r"""
    <div class="info-box">
    <b>1. 傳播速度</b>：$v = \frac{c}{\sqrt{D_k}}$，其中 $c = 299.79$ mm/ns<br><br>
    <b>2. 傳播延遲</b>：$t_d = \frac{L}{v} = \frac{L \cdot \sqrt{D_k}}{c}$ (ps)<br><br>
    <b>3. 頻率相關 Dk</b>：$D_k(f) = D_{k,1GHz} \cdot (1 + TCD_k \cdot \log_{10}f)$<br><br>
    <b>4. 插入損耗</b>：$\alpha \approx \frac{\pi f \sqrt{D_k} \cdot D_f}{c}$ (Np/m)<br><br>
    <b>5. 趨膚深度</b>：$\delta = \sqrt{\frac{2}{\omega \mu_0 \sigma}}$ (mm)
    </div>
    """, unsafe_allow_html=True)

with sidebar:
  # ========== 底部 ==========
  markdown("---")
  markdown("<div style='text-align:center; color:#888; font-size:0.85rem;'>PCB Trace Skew Simulator v1.0 | 基於傳輸線理論與材料電磁參數模型</div>", unsafe_allow_html=True)

# ============================================================
# Streamlit PCB Skew 互動式模擬界面
# ============================================================
# ========== 標題 ==========
  markdown('<div class="subtitle">🔧 PCB N-Channel Trace Skew 互動式模擬器</div>', unsafe_allow_html=True)
  markdown('<div class="subtitle">多通道信號傳播延遲、頻段色散與材料參數 Dk/Df 即時分析</div>', unsafe_allow_html=True)
