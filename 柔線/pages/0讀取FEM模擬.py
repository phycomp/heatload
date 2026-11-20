from streamlit import columns, dataframe, divider, download_button, subheader, info, markdown, metric, plotly_chart, pyplot, radio, session_state, set_page_config, sidebar, slider, tabs, text_input
from matplotlib.pyplot import Line2D, subplots
from numpy import ceil, cos, exp, eye, linspace, max, mean, ndarray, pi, random, round, sin, std, zeros, zeros_like
from numpy.random import normal
from json import dumps
from pandas import DataFrame
from plotly.graph_objects import Bar, Figure, Heatmap, Scatter

#import streamlit as st
#import numpy as np
#import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrowPatch
from matplotlib.collections import LineCollection
#import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import json

# 設定頁面配置
set_page_config(
    page_title="通用型量子比特讀取架構模擬器",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義 CSS 樣式
markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .quantum-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: rgba(255,255,255,0.05);
        color:white;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 資料結構定義 ====================

@dataclass
class QubitConfig:
    """量子比特配置"""
    qubit_type: str  # "superconducting", "photonic", "ion_trap", "spin"
    frequency: float  # GHz
    anharmonicity: float  # MHz
    coherence_time_t1: float  # μs
    coherence_time_t2: float  # μs
    readout_frequency: float  # GHz
    coupling_strength: float  # MHz
    position: Tuple[float, float]  # (x, y) 位置

@dataclass
class ReadoutChannel:
    """讀取通道配置"""
    channel_id: int
    center_frequency: float  # GHz
    bandwidth: float  # MHz
    noise_temperature: float  # K
    amplification_chain: List[str]  # 放大器鏈
    multiplexing_scheme: str  # "FDM", "TDM", "CDM", "DDM"

@dataclass
class MultiplexingConfig:
    """多工配置"""
    scheme: str
    num_qubits_per_channel: int
    frequency_spacing: float  # MHz
    crosstalk_matrix: ndarray

# ==================== 量子系統模擬核心 ====================

class QuantumSystemSimulator:
    """通用量子系統模擬器"""

    def __init__(self, system_type: str, num_qubits: int):
        self.system_type = system_type
        self.num_qubits = num_qubits
        self.qubits = []
        self.channels = []
        self.time_points = linspace(0, 10, 1000)  # μs

    def initialize_superconducting_qubits(self, base_freq: float = 5.0):
        """初始化超導量子比特陣列"""
        for i in range(self.num_qubits):
            qubit = QubitConfig(
                qubit_type="superconducting",
                frequency=base_freq + i * 0.1,  # 100 MHz 間隔
                anharmonicity=-250.0,
                coherence_time_t1=100.0,
                coherence_time_t2=150.0,
                readout_frequency=base_freq + i * 0.1 + 0.2,
                coupling_strength=50.0,
                position=(i % 4, i // 4)
            )
            self.qubits.append(qubit)

    def initialize_photonic_qubits(self, wavelength: float = 1550.0):
        """初始化光量子比特陣列"""
        for i in range(self.num_qubits):
            qubit = QubitConfig(
                qubit_type="photonic",
                frequency=299792.458 / wavelength,  # 轉換為 THz
                anharmonicity=0.0,
                coherence_time_t1=1000.0,
                coherence_time_t2=2000.0,
                readout_frequency=299792.458 / wavelength,
                coupling_strength=1.0,
                position=(cos(2*pi*i/self.num_qubits), 
                         sin(2*pi*i/self.num_qubits))
            )
            self.qubits.append(qubit)

    def initialize_ion_trap_qubits(self, trap_frequency: float = 1.0):
        """初始化離子阱量子比特陣列"""
        for i in range(self.num_qubits):
            qubit = QubitConfig(
                qubit_type="ion_trap",
                frequency=12.6,  # Yb+ 時鐘躍遷
                anharmonicity=0.0,
                coherence_time_t1=10000.0,
                coherence_time_t2=5000.0,
                readout_frequency=369.5,  # 雷射冷卻/讀取
                coupling_strength=0.1,
                position=(i * 5.0, 0.0)  # 線性離子鏈
            )
            self.qubits.append(qubit)

    def setup_multiplexing_readout(self, scheme: str, qubits_per_channel: int = 4):
        """設定多工讀取架構"""
        num_channels = int(ceil(self.num_qubits / qubits_per_channel))

        for ch in range(num_channels):
            if scheme == "FDM":
                # 頻分多工
                center_freq = mean([q.readout_frequency 
                                      for q in self.qubits[ch*qubits_per_channel:(ch+1)*qubits_per_channel]])
            elif scheme == "TDM":
                # 時分多工
                center_freq = self.qubits[ch*qubits_per_channel].readout_frequency
            else:
                center_freq = 5.0

            channel = ReadoutChannel(
                channel_id=ch,
                center_frequency=center_freq,
                bandwidth=qubits_per_channel * 50,  # 50 MHz per qubit
                noise_temperature=0.02,  # 20 mK
                amplification_chain=["JPA", "HEMT", "Room Temp Amp"],
                multiplexing_scheme=scheme
            )
            self.channels.append(channel)

    def simulate_readout_signal(self, qubit_states: List[int]) -> Dict:
        """模擬讀取訊號"""
        signals = {}

        for ch in self.channels:
            # 生成 IQ 訊號
            t = self.time_points
            i_signal = zeros_like(t)
            q_signal = zeros_like(t)

            # 加入各量子比特的貢獻
            start_idx = ch.channel_id * 4
            end_idx = min(start_idx + 4, self.num_qubits)

            for i, q_idx in enumerate(range(start_idx, end_idx)):
                if q_idx < len(qubit_states):
                    state = qubit_states[q_idx]
                    freq = self.qubits[q_idx].readout_frequency
                    amp = 1.0 if state == 1 else 0.3
                    phase = pi/4 if state == 1 else -pi/4

                    # 加入衰減和雜訊
                    decay = exp(-t / self.qubits[q_idx].coherence_time_t1)
                    noise = normal(0, 0.05, len(t))

                    i_signal += amp * cos(2*pi*freq*t + phase) * decay + noise
                    q_signal += amp * sin(2*pi*freq*t + phase) * decay + noise

            signals[ch.channel_id] = {
                'I': i_signal,
                'Q': q_signal,
                'time': t,
                'frequency': ch.center_frequency
            }

        return signals

    def calculate_fidelity(self, snr_db: float = 20.0) -> float:
        """計算讀取保真度"""
        snr_linear = 10**(snr_db/10)
        fidelity = 1 - 0.5 * exp(-snr_linear/2)
        return fidelity

    def get_crosstalk_matrix(self) -> ndarray:
        """計算串擾矩陣"""
        n = self.num_qubits
        crosstalk = zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i != j:
                    freq_diff = abs(self.qubits[i].frequency - self.qubits[j].frequency)
                    crosstalk[i, j] = 0.01 / (1 + (freq_diff/0.1)**2)  # 簡化模型

        return crosstalk

# ==================== 視覺化函數 ====================

def plot_quantum_chip_layout(simulator: QuantumSystemSimulator):
    """繪製量子晶片佈局"""
    fig, ax = subplots(figsize=(10, 8))

    colors = {
        'superconducting': '#FF6B6B',
        'photonic': '#4ECDC4',
        'ion_trap': '#45B7D1',
        'spin': '#96CEB4'
    }

    # 繪製量子比特
    for i, qubit in enumerate(simulator.qubits):
        x, y = qubit.position
        color = colors.get(qubit.qubit_type, '#FFEAA7')

        # 量子比特圓圈
        circle = Circle((x, y), 0.3, color=color, ec='white', linewidth=2, zorder=3)
        ax.add_patch(circle)

        # 標籤
        ax.text(x, y, f'Q{i}', ha='center', va='center', 
                fontsize=10, fontweight='bold', color='white')

        # 頻率標註
        ax.text(x, y-0.5, f'{qubit.frequency:.2f}', ha='center', 
                fontsize=8, color='gray')

    # 繪製讀取線
    for ch in simulator.channels:
        start_idx = ch.channel_id * 4
        end_idx = min(start_idx + 4, len(simulator.qubits))

        if start_idx < len(simulator.qubits):
            x_vals = [simulator.qubits[i].position[0] for i in range(start_idx, end_idx)]
            y_vals = [simulator.qubits[i].position[1] for i in range(start_idx, end_idx)]

            # 讀取線
            ax.plot(x_vals, y_vals, 'w--', alpha=0.5, linewidth=2, zorder=1)

            # 讀取諧振器
            mid_x = mean(x_vals) if len(x_vals) > 0 else 0
            mid_y = mean(y_vals) if len(y_vals) > 0 else 0

            rect = FancyBboxPatch((mid_x-0.4, mid_y-0.2), 0.8, 0.4,
                                  boxstyle="round,pad=0.02", 
                                  facecolor='purple', alpha=0.6, zorder=2)
            ax.add_patch(rect)
            ax.text(mid_x, mid_y, f'R{ch.channel_id}', ha='center', va='center',
                   fontsize=9, color='white', fontweight='bold')

    ax.set_xlim(-1, 5)
    ax.set_ylim(-1, 4)
    ax.set_aspect('equal')
    ax.set_facecolor('#1a1a2e')
    fig.patch.set_facecolor('#1a1a2e')
    ax.axis('off')

    # 圖例
    legend_elements = [Line2D([0], [0], marker='o', color='w', 
                                  markerfacecolor=color, markersize=10, label=qtype)
                      for qtype, color in colors.items()]
    ax.legend(handles=legend_elements, loc='upper right', facecolor='#1a1a2e', 
              edgecolor='white', labelcolor='white')

    return fig

def plot_iq_plane(signals: Dict, qubit_states: List[int]):
    """繪製 IQ 平面散點圖"""
    fig = Figure()

    colors = ['#FF6B6B' if s == 1 else '#4ECDC4' for s in qubit_states]

    for ch_id, signal in signals.items():
        # 計算每個時間點的 IQ 值
        i_avg = mean(signal['I'])
        q_avg = mean(signal['Q'])

        # 繪製軌跡
        fig.add_trace(Scatter(
            x=signal['I'],
            y=signal['Q'],
            mode='lines',
            name=f'Channel {ch_id}',
            line=dict(width=2),
            opacity=0.6
        ))

        # 繪製中心點
        fig.add_trace(Scatter(
            x=[i_avg],
            y=[q_avg],
            mode='markers',
            marker=dict(size=15, color='yellow', symbol='star'),
            name=f'CH{ch_id} Center'
        ))

    fig.update_layout(
        title='IQ 平面讀取訊號',
        xaxis_title='I 分量 (a.u.)',
        yaxis_title='Q 分量 (a.u.)',
        plot_bgcolor='rgba(26,26,46,1)',
        paper_bgcolor='rgba(26,26,46,1)',
        font=dict(color='white'),
        showlegend=True
    )

    return fig

def plot_frequency_spectrum(simulator: QuantumSystemSimulator):
    """繪製頻譜配置圖"""
    fig = Figure()

    # 量子比特頻率
    qubit_freqs = [q.frequency for q in simulator.qubits]
    qubit_types = [q.qubit_type for q in simulator.qubits]

    colors_map = {
        'superconducting': '#FF6B6B',
        'photonic': '#4ECDC4',
        'ion_trap': '#45B7D1'
    }

    for i, (freq, qtype) in enumerate(zip(qubit_freqs, qubit_types)):
        fig.add_trace(Scatter(
            x=[freq],
            y=[i],
            mode='markers',
            marker=dict(size=15, color=colors_map.get(qtype, '#FFEAA7')),
            name=f'Q{i} ({qtype})',
            text=f'Q{i}: {freq:.3f} GHz',
            hoverinfo='text'
        ))

    # 讀取通道頻帶
    for ch in simulator.channels:
        fig.add_vrect(
            x0=ch.center_frequency - ch.bandwidth/2000,
            x1=ch.center_frequency + ch.bandwidth/2000,
            fillcolor="rgba(255,255,255,0.1)",
            layer="below",
            line_width=0,
        )
        fig.add_vline(x=ch.center_frequency, line_dash="dash", 
                     line_color="white", opacity=0.5)

    fig.update_layout(
        title='頻率配置與多工頻帶',
        xaxis_title='頻率 (GHz)',
        yaxis_title='量子比特索引',
        plot_bgcolor='rgba(26,26,46,1)',
        paper_bgcolor='rgba(26,26,46,1)',
        font=dict(color='white')
    )

    return fig

def plot_crosstalk_heatmap(simulator: QuantumSystemSimulator):
    """繪製串擾熱力圖"""
    crosstalk = simulator.get_crosstalk_matrix()

    fig = Figure(data=Heatmap(
        z=crosstalk,
        colorscale='Viridis',
        showscale=True,
        text=round(crosstalk, 4),
        texttemplate='%{text}',
        textfont={"size": 8}
    ))

    fig.update_layout(
        title='量子比特間串擾矩陣',
        xaxis_title='目標量子比特',
        yaxis_title='控制量子比特',
        plot_bgcolor='rgba(26,26,46,1)',
        paper_bgcolor='rgba(26,26,46,1)',
        font=dict(color='white')
    )

    return fig

def plot_pulse_sequence(simulator: QuantumSystemSimulator):
    """繪製讀取脈衝序列"""
    fig = make_subplots(rows=len(simulator.channels), cols=1,
                       shared_xaxes=True,
                       subplot_titles=[f'Channel {ch.channel_id}' for ch in simulator.channels])

    t = linspace(0, 1000, 1000)  # ns

    for i, ch in enumerate(simulator.channels):
        # 生成讀取脈衝
        pulse = exp(-((t - 200)**2) / (2 * 50**2)) * cos(2*pi*ch.center_frequency*t)

        fig.add_trace(
            Scatter(x=t, y=pulse, mode='lines', 
                      line=dict(color='#667eea', width=2),
                      name=f'CH{ch.channel_id}'),
            row=i+1, col=1
        )

        fig.update_yaxes(title_text='振幅', row=i+1, col=1)

    fig.update_xaxes(title_text='時間 (ns)', row=len(simulator.channels))
    fig.update_layout(
        height=200 * len(simulator.channels),
        showlegend=False,
        plot_bgcolor='rgba(26,26,46,1)',
        paper_bgcolor='rgba(26,26,46,1)',
        font=dict(color='white')
    )

    return fig

# ==================== 主要應用界面 ====================

MENU, 表單=[], ['串擾', '', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
if menu==len(表單): #
  pass
elif menu==MENU[1]: #
  pass
elif menu==MENU[0]: #串擾
    markdown('<h1 class="main-header">⚛️ 通用型量子比特讀取架構模擬器</h1>', unsafe_allow_html=True)

    # 側邊欄配置
    with sidebar:
        subheader("🔧 系統配置")

        system_type = radio("量子系統類型", ["superconducting", "photonic", "ion_trap"], format_func=lambda x: {"superconducting":"超導量子比特", "photonic":"光量子比特", "ion_trap":"離子阱量子比特"}[x], horizontal=True)
        num_qubits = slider("量子比特數量", 2, 32, 8)
        multiplexing_scheme = radio("多工方案", ["FDM", "TDM", "CDM", "Hybrid"], format_func=lambda x: {"FDM":"頻分多工 (FDM)", "TDM":"時分多工 (TDM)", "CDM":"碼分多工 (CDM)", "Hybrid":"混合多工" }[x], horizontal=True)

        qubits_per_channel = slider("每通道量子比特數", 1, 8, 4)

        divider()

        subheader("📊 模擬參數")

        snr_db = slider("訊噪比 (dB)", 0, 40, 20)

        # 量子比特狀態設定
        subheader("量子比特狀態")
        qubit_states = []
        cols = columns(4)
        for i in range(num_qubits):
            with cols[i % 4]:
                state = radio(f"Q{i}", [0, 1], key=f"qubit_{i}", horizontal=True)
                qubit_states.append(state)

    # 初始化模擬器
    if 'simulator' not in session_state or session_state.get('config_changed', False):
        simulator = QuantumSystemSimulator(system_type, num_qubits)

        if system_type == "superconducting":
            simulator.initialize_superconducting_qubits()
        elif system_type == "photonic":
            simulator.initialize_photonic_qubits()
        elif system_type == "ion_trap":
            simulator.initialize_ion_trap_qubits()

        simulator.setup_multiplexing_readout(multiplexing_scheme, qubits_per_channel)
        session_state['simulator'] = simulator
        session_state['config_changed'] = False
    else:
        simulator = session_state['simulator']

    # 執行模擬
    signals = simulator.simulate_readout_signal(qubit_states)
    fidelity = simulator.calculate_fidelity(snr_db)

    # 主要內容區域
    tab1, tab2, tab3, tab4, tab5 = tabs([
        "📐 架構佈局", 
        "📡 讀取訊號", 
        "📶 頻譜分析",
        "🔥 串擾分析",
        "⚙️ 系統效能"
    ])

    with tab1:
        col1, col2 = columns([2, 1])

        with col1:
            subheader("量子晶片佈局")
            fig_layout = plot_quantum_chip_layout(simulator)
            pyplot(fig_layout)

        with col2:
            subheader("系統資訊")

            info_data = {
                "系統類型": system_type,
                "量子比特數": num_qubits,
                "讀取通道數": len(simulator.channels),
                "多工方案": multiplexing_scheme,
                "平均T1": f"{mean([q.coherence_time_t1 for q in simulator.qubits]):.1f} μs",
                "平均T2": f"{mean([q.coherence_time_t2 for q in simulator.qubits]):.1f} μs"
            }

            for key, value in info_data.items():
                metric(key, value)

            divider()

            subheader("量子比特詳情")
            qubit_df = DataFrame([
                {
                    "ID": i,
                    "類型": q.qubit_type,
                    "頻率(GHz)": round(q.frequency, 3),
                    "讀取頻(GHz)": round(q.readout_frequency, 3),
                    "T1(μs)": q.coherence_time_t1,
                    "耦合(MHz)": q.coupling_strength
                }
                for i, q in enumerate(simulator.qubits)
            ])
            dataframe(qubit_df, use_container_width=True)

    with tab2:
        col1, col2 = columns(2)

        with col1:
            subheader("IQ 平面散點圖")
            fig_iq = plot_iq_plane(signals, qubit_states)
            plotly_chart(fig_iq, use_container_width=True)

        with col2:
            subheader("時域訊號")

            # 選擇通道
            selected_ch = radio("選擇通道", range(len(simulator.channels)), horizontal=True)

            if selected_ch in signals:
                sig = signals[selected_ch]

                fig_time = Figure()
                fig_time.add_trace(Scatter(
                    x=sig['time'], y=sig['I'],
                    mode='lines', name='I 分量',
                    line=dict(color='#667eea')
                ))
                fig_time.add_trace(Scatter(
                    x=sig['time'], y=sig['Q'],
                    mode='lines', name='Q 分量',
                    line=dict(color='#f093fb')
                ))
                fig_time.update_layout(
                    xaxis_title='時間 (μs)',
                    yaxis_title='振幅',
                    plot_bgcolor='rgba(26,26,46,1)',
                    paper_bgcolor='rgba(26,26,46,1)',
                    font=dict(color='white')
                )
                plotly_chart(fig_time, use_container_width=True)

                # 顯示訊號統計
                col_stat1, col_stat2 = columns(2)
                with col_stat1:
                    metric("I 平均值", f"{mean(sig['I']):.3f}")
                    metric("I 標準差", f"{std(sig['I']):.3f}")
                with col_stat2:
                    metric("Q 平均值", f"{mean(sig['Q']):.3f}")
                    metric("Q 標準差", f"{std(sig['Q']):.3f}")

    with tab3:
        subheader("頻率配置與多工頻帶")
        fig_spec = plot_frequency_spectrum(simulator)
        plotly_chart(fig_spec, use_container_width=True)

        divider()

        subheader("讀取脈衝序列")
        fig_pulse = plot_pulse_sequence(simulator)
        plotly_chart(fig_pulse, use_container_width=True)

    with tab4:
        col1, col2 = columns(2)

        with col1:
            subheader("串擾熱力圖")
            fig_xtalk = plot_crosstalk_heatmap(simulator)
            plotly_chart(fig_xtalk, use_container_width=True)

        with col2:
            subheader("串擾統計")

            crosstalk = simulator.get_crosstalk_matrix()
            mask = ~eye(crosstalk.shape[0], dtype=bool)
            off_diag = crosstalk[mask]

            metric("最大串擾", f"{max(off_diag):.4f}")
            metric("平均串擾", f"{mean(off_diag):.4f}")
            metric("串擾標準差", f"{std(off_diag):.4f}")

            divider()

            subheader("串擾抑制建議")
            if multiplexing_scheme == "FDM":
                info("""
                **FDM 串擾抑制：**
                - 增加頻率間隔至 > 50 MHz
                - 使用更陡峭的濾波器
                - 優化讀取脈衝形狀
                """)
            elif multiplexing_scheme == "TDM":
                info("""
                **TDM 串擾抑制：**
                - 縮短讀取時間 < 100 ns
                - 增加開關隔離度
                - 優化時序控制
                """)

    with tab5:
        subheader("系統效能儀表板")

        # 關鍵指標
        col1, col2, col3, col4 = columns(4)

        with col1:
            markdown(f"""
            <div class="metric-card">
                <h3>讀取保真度</h3>
                <h2>{fidelity:.4f}</h2>
                <p>SNR: {snr_db} dB</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            throughput = len(simulator.channels) * qubits_per_channel / 10  # 簡化計算
            markdown(f"""
            <div class="metric-card">
                <h3>讀取吞吐量</h3>
                <h2>{throughput:.1f}</h2>
                <p>Qubits/μs</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            efficiency = fidelity * throughput
            markdown(f"""
            <div class="metric-card">
                <h3>綜合效率</h3>
                <h2>{efficiency:.2f}</h2>
                <p>Fidelity × Throughput</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            resource = num_qubits / len(simulator.channels)
            markdown(f"""
            <div class="metric-card">
                <h3>資源利用率</h3>
                <h2>{resource:.1f}</h2>
                <p>Qubits/Channel</p>
            </div>
            """, unsafe_allow_html=True)

        divider()

        # 效能比較圖表
        subheader("多工方案比較")

        schemes = ["FDM", "TDM", "CDM", "Hybrid"]
        fidelities = [0.95, 0.92, 0.88, 0.96]
        throughputs = [8.5, 6.2, 4.8, 9.1]
        scalabilities = [0.7, 0.85, 0.9, 0.95]

        fig_compare = Figure()

        fig_compare.add_trace(Bar(
            name='保真度',
            x=schemes,
            y=fidelities,
            marker_color='#667eea'
        ))

        fig_compare.add_trace(Bar(
            name='吞吐量',
            x=schemes,
            y=[t/10 for t in throughputs],
            marker_color='#f093fb'
        ))

        fig_compare.add_trace(Bar(
            name='可擴展性',
            x=schemes,
            y=scalabilities,
            marker_color='#4facfe'
        ))

        fig_compare.update_layout(
            barmode='group',
            xaxis_title='多工方案',
            yaxis_title='效能指標',
            plot_bgcolor='rgba(26,26,46,1)',
            paper_bgcolor='rgba(26,26,46,1)',
            font=dict(color='white'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )

        plotly_chart(fig_compare, use_container_width=True)

        divider()

        # 導出配置
        subheader("導出配置")

        config = {
            "system_type": system_type,
            "num_qubits": num_qubits,
            "multiplexing_scheme": multiplexing_scheme,
            "qubits_per_channel": qubits_per_channel,
            "snr_db": snr_db,
            "qubit_states": qubit_states,
            "qubit_configs": [
                {
                    "id": i,
                    "frequency": q.frequency,
                    "readout_frequency": q.readout_frequency,
                    "t1": q.coherence_time_t1,
                    "t2": q.coherence_time_t2
                }
                for i, q in enumerate(simulator.qubits)
            ]
        }

        config_json = json.dumps(config, indent=2)
        download_button(
            label="下載 JSON 配置",
            data=config_json,
            file_name="quantum_readout_config.json",
            mime="application/json"
        )

#if __name__ == "__main__": main()
