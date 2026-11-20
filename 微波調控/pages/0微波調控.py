from streamlit import columns, header, info, markdown, metric, plotly_chart, selectbox, set_page_config, sidebar, slider, subheader, success, tabs
from numpy import abs, angle, arccos, arctan2, array, conj, cos, exp, fft, imag, linalg, linspace, ones, outer, pi, real, sin, size, zeros, zeros_like, trapezoid   #trapz, 
from plotly.graph_objects import Figure, Scatter, Scatter3d, Surface
from plotly.subplots import make_subplots
#import streamlit as st
#import numpy as np
#import matplotlib.pyplot as plt
#from scipy.integrate import odeint, solve_ivp
#from scipy.linalg import expm
#import plotly.graph_objects as go

# 頁面設定
set_page_config(page_title="Transmon 量子位元控制模擬器", layout="wide")

# 自定義 CSS 美化
markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .equation-box {
        background: black/*#f0f2f6*/;
        color: yellow;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #667eea;
        margin: 10px 0;
    }
    .parameter-card {
        background: black/*linear-gradient(135deg, #667eea 0%, #764ba2 100%)*/;
        color: yellow;
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: black/**/;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

markdown('<h1 class="main-header">🔬 Transmon 量子位元微波控制模擬器</h1>', unsafe_allow_html=True)

# 側邊欄控制參數
with sidebar:
    header("⚙️ 控制參數設定")
    
    subheader("量子位元參數")
    qubit_freq = slider("量子位元頻率 ω_q/2π (GHz)", 4.0, 8.0, 5.0, 0.1)
    anharmonicity = slider("非諧性 α/2π (MHz)", -300.0, -100.0, -250.0, 10.0)
    
    subheader("微波脈衝參數")
    pulse_type = selectbox("脈衝類型", ["高斯脈衝 (Gaussian)", "DRAG 脈衝", "方波脈衝"])
    pulse_duration = slider("脈衝長度 (ns)", 10, 500, 100, 10)
    pulse_amplitude = slider("脈衝振幅 (MHz)", 0.1, 100.0, 10.0, 0.5)
    detuning = slider("失諧量 Δ/2π (MHz)", -50.0, 50.0, 0.0, 1.0)
    
    subheader("環境參數")
    t1 = slider("T1 弛豫時間 (μs)", 10, 200, 100, 10)
    t2 = slider("T2 退相位時間 (μs)", 5, 100, 50, 5)
    
    subheader("模擬設定")
    num_points = slider("模擬點數", 100, 2000, 1000, 100)

# 物理常數與運算子
hbar = 1.0  # 自然單位制

# 包立矩陣
sigma_x = array([[0, 1], [1, 0]], dtype=complex)
sigma_y = array([[0, -1j], [1j, 0]], dtype=complex)
sigma_z = array([[1, 0], [0, -1]], dtype=complex)
sigma_plus = array([[0, 1], [0, 0]], dtype=complex)
sigma_minus = array([[0, 0], [1, 0]], dtype=complex)

# 三能級系統（考慮非諧性）
def create_hamiltonian_3level(omega_q, alpha):
    """創建三能級 Transmon 哈密頓量"""
    H0 = zeros((3, 3), dtype=complex)
    H0[1, 1] = omega_q
    H0[2, 2] = 2 * omega_q + alpha  # 考慮非諧性
    return H0

# 脈衝形狀函數
def gaussian_pulse(t, t0, sigma, amplitude):
    """高斯脈衝"""
    return amplitude * exp(-((t - t0)**2) / (2 * sigma**2))

def drag_pulse(t, t0, sigma, amplitude, beta=0.5):
    """DRAG 脈衝：高斯 + 導數項"""
    gauss = exp(-((t - t0)**2) / (2 * sigma**2))
    d_gauss = -(t - t0) / sigma**2 * gauss
    return amplitude * (gauss + 1j * beta * d_gauss)

def square_pulse(t, t_start, t_end, amplitude):
    """方波脈衝"""
    return amplitude if t_start <= t <= t_end else 0.0

# 量子態演化（薛丁格方程式）
def schrodinger_eq(t, psi, H0, pulse_func, args, drive_freq):
    """含時薛丁格方程式"""
    omega_q, = args
    
    # 旋轉波近似下的驅動項
    if pulse_type == "高斯脈衝 (Gaussian)":
        envelope = gaussian_pulse(t, pulse_duration/2, pulse_duration/6, pulse_amplitude)
    elif pulse_type == "DRAG 脈衝":
        envelope = real(drag_pulse(t, pulse_duration/2, pulse_duration/6, pulse_amplitude))
    else:
        envelope = square_pulse(t, 0, pulse_duration, pulse_amplitude)
    
    # 驅動哈密頓量 H_d = ℏ/2 * Ω(t) * (σ+ e^(-iωt) + σ- e^(iωt))
    H_drive = 0.5 * envelope * (sigma_plus * exp(-1j * drive_freq * t) + 
                                 sigma_minus * exp(1j * drive_freq * t))
    
    H_total = H0 + H_drive
    return -1j * (H_total @ psi)

# 主選單
tab1, tab2, tab3, tab4 = tabs(["📊 物理模型", "🎛️ 脈衝控制", "🔮 量子態演化", "📈 布洛赫球"])

with tab1:
    header("Transmon 量子位元物理模型")
    
    col1, col2 = columns(2)
    
    with col1:
        markdown("""
        <div class="equation-box">
        <h3>🔹 基本哈密頓量</h3>
        
        Transmon 量子位元可視為非線性 LC 振盪器：
        
        $$\\hat{H}_0 = \\hbar \\omega_q \\hat{a}^\\dagger \\hat{a} + \\frac{\\hbar \\alpha}{2} \\hat{a}^\\dagger \\hat{a}^\\dagger \\hat{a} \\hat{a}$$
        
        其中：
        - $\\omega_q$：量子位元躍遷頻率
        - $\\alpha$：非諧性（通常為負值，約 -250 MHz）
        - $\\hat{a}^\\dagger, \\hat{a}$：產生與湮滅算符
        
        <h3>🔹 微波驅動哈密頓量</h3>
        
        $$\\hat{H}_d(t) = \\hbar \\Omega(t) \\cos(\\omega_d t + \\phi) \\cdot \\hat{\\sigma}_x$$
        
        在旋轉波近似（RWA）下：
        
        $$\\hat{H}_d^{RWA}(t) = \\frac{\\hbar \\Omega(t)}{2} \\left( e^{-i\\phi} \\hat{\\sigma}_+ + e^{i\\phi} \\hat{\\sigma}_- \\right)$$
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        markdown("""
        <div class="equation-box">
        <h3>🔹 含時薛丁格方程式</h3>
        
        $$i\\hbar \\frac{\\partial}{\\partial t} |\\psi(t)\\rangle = \\hat{H}(t) |\\psi(t)\\rangle$$
        
        <h3>🔹 密度矩陣演化（Lindblad 主方程式）</h3>
        
        考慮環境雜訊時：
        
        $$\\frac{d\\hat{\\rho}}{dt} = -\\frac{i}{\\hbar}[\\hat{H}, \\hat{\\rho}] + \\gamma_1 \\mathcal{D}[\\hat{\\sigma}_-]\\hat{\\rho} + \\frac{\\gamma_\\phi}{2} \\mathcal{D}[\\hat{\\sigma}_z]\\hat{\\rho}$$
        
        其中 Lindblad 超算符：
        $$\\mathcal{D}[\\hat{L}]\\hat{\\rho} = \\hat{L}\\hat{\\rho}\\hat{L}^\\dagger - \\frac{1}{2}\\{\\hat{L}^\\dagger \\hat{L}, \\hat{\\rho}\\}$$
        
        <h3>🔹 Rabi 頻率</h3>
        
        $$\\Omega_R = \\sqrt{\\Omega^2 + \\Delta^2}$$
        
        其中失諧量 $\\Delta = \\omega_q - \\omega_d$
        </div>
        """, unsafe_allow_html=True)
    
    # 顯示參數摘要
    subheader("目前設定參數")
    cols = columns(4)
    params = [
        ("量子位元頻率", f"{qubit_freq} GHz"),
        ("非諧性", f"{anharmonicity} MHz"),
        ("脈衝長度", f"{pulse_duration} ns"),
        ("Rabi 頻率", f"{pulse_amplitude} MHz")
    ]
    for col, (name, value) in zip(cols, params):
        with col:
            markdown(f"""
            <div class="parameter-card">
                <h4>{name}</h4>
                <h2>{value}</h2>
            </div>
            """, unsafe_allow_html=True)

with tab2:
    header("微波脈衝形狀與頻譜")
    
    # 時間軸
    t = linspace(0, pulse_duration * 2, num_points)
    
    # 生成脈衝
    if pulse_type == "高斯脈衝 (Gaussian)":
        sigma = pulse_duration / 6
        pulse = gaussian_pulse(t, pulse_duration/2, sigma, pulse_amplitude)
        pulse_q = gaussian_pulse(t, pulse_duration/2, sigma, pulse_amplitude) * 0.5  # 正交分量
        
    elif pulse_type == "DRAG 脈衝":
        sigma = pulse_duration / 6
        drag = drag_pulse(t, pulse_duration/2, sigma, pulse_amplitude)
        pulse = real(drag)
        pulse_q = imag(drag)
        
    else:  # 方波
        pulse = array([square_pulse(ti, pulse_duration*0.2, pulse_duration*0.8, pulse_amplitude) for ti in t])
        pulse_q = zeros_like(pulse)
    
    # 繪製脈衝形狀
    fig_pulse = make_subplots(rows=2, cols=1, subplot_titles=("時域脈衝形狀", "頻譜分析"))
    
    fig_pulse.add_trace(
        Scatter(x=t, y=pulse, name="I (同相)", line=dict(color='#667eea', width=3)),
        row=1, col=1
    )
    fig_pulse.add_trace(
        Scatter(x=t, y=pulse_q, name="Q (正交)", line=dict(color='#764ba2', width=3)),
        row=1, col=1
    )
    
    # 計算頻譜
    freqs = fft.fftfreq(len(t), t[1]-t[0]) * 1000  # 轉換為 MHz
    spectrum = abs(fft.fft(pulse))
    spectrum_q = abs(fft.fft(pulse_q))
    
    # 只顯示正頻率
    pos_mask = freqs > 0
    fig_pulse.add_trace(
        Scatter(x=freqs[pos_mask], y=spectrum[pos_mask], name="I 頻譜", 
                  line=dict(color='#667eea', width=2), fill='tozeroy'),
        row=2, col=1
    )
    
    fig_pulse.update_xaxes(title_text="時間 (ns)", row=1, col=1)
    fig_pulse.update_yaxes(title_text="振幅 (MHz)", row=1, col=1)
    fig_pulse.update_xaxes(title_text="頻率 (MHz)", row=2, col=1, range=[0, 500])
    fig_pulse.update_yaxes(title_text="強度", row=2, col=1)
    fig_pulse.update_layout(height=600, showlegend=True, template='plotly_white')
    
    plotly_chart(fig_pulse, use_container_width=True)
    
    # 脈衝積分（脈衝面積）
    pulse_area = trapezoid(pulse, t) / (2 * pi)
    info(f"📐 **脈衝面積**: {pulse_area:.2f} × 2π (理想 π-脈衝 = 0.5 × 2π)")

with tab3:
    header("量子態實時演化")
    
    # 設定演化參數
    omega_q = qubit_freq * 2 * pi  # 轉換為角頻率
    drive_freq = omega_q + detuning * 2 * pi * 0.001  # 考慮失諧
    
    # 初始態 |0⟩
    psi0 = array([1, 0], dtype=complex)
    
    # 時間演化
    t_evolve = linspace(0, pulse_duration * 3, num_points)
    dt = t_evolve[1] - t_evolve[0]
    
    # 使用簡單的薛丁格方程式積分
    states = zeros((len(t_evolve), 2), dtype=complex)
    states[0] = psi0
    
    for i in range(1, len(t_evolve)):
        # 計算當前哈密頓量
        if pulse_type == "高斯脈衝 (Gaussian)":
            envelope = gaussian_pulse(t_evolve[i], pulse_duration/2, pulse_duration/6, pulse_amplitude)
        elif pulse_type == "DRAG 脈衝":
            envelope = real(drag_pulse(t_evolve[i], pulse_duration/2, pulse_duration/6, pulse_amplitude))
        else:
            envelope = square_pulse(t_evolve[i], 0, pulse_duration, pulse_amplitude)
        
        # 旋轉參考系下的有效哈密頓量
        H_eff = 0.5 * array([[detuning*2*pi*0.001, envelope], 
                                [envelope, -detuning*2*pi*0.001]])
        
        # 簡單的歐拉積分（實際應使用更精確的方法）
        psi_dot = -1j * H_eff @ states[i-1]
        states[i] = states[i-1] + psi_dot * dt
        
        # 歸一化
        states[i] = states[i] / linalg.norm(states[i])
    
    # 計算期望值
    pop_0 = abs(states[:, 0])**2
    pop_1 = abs(states[:, 1])**2
    
    # 布洛赫球座標
    expect_x = real(conj(states[:, 0]) * states[:, 1] + conj(states[:, 1]) * states[:, 0])
    expect_y = real(1j * (conj(states[:, 0]) * states[:, 1] - conj(states[:, 1]) * states[:, 0]))
    expect_z = pop_0 - pop_1
    
    # 繪製演化
    fig_evolution = make_subplots(
        rows=2, cols=2,
        subplot_titles=("能階佈居數", "布洛赫球座標", "相位演化", "保真度"),
        specs=[[{}, {}], [{}, {}]]
    )
    
    # 佈居數
    fig_evolution.add_trace(
        Scatter(x=t_evolve, y=pop_0, name="|0⟩ 佔有率", 
                  line=dict(color='#667eea', width=3), fill='tozeroy'),
        row=1, col=1
    )
    fig_evolution.add_trace(
        Scatter(x=t_evolve, y=pop_1, name="|1⟩ 佔有率", 
                  line=dict(color='#764ba2', width=3), fill='tozeroy'),
        row=1, col=1
    )
    
    # 布洛赫座標
    fig_evolution.add_trace(Scatter(x=t_evolve, y=expect_x, name="⟨σx⟩", line=dict(color='red')), row=1, col=2)
    fig_evolution.add_trace(Scatter(x=t_evolve, y=expect_y, name="⟨σy⟩", line=dict(color='green')), row=1, col=2)
    fig_evolution.add_trace(Scatter(x=t_evolve, y=expect_z, name="⟨σz⟩", line=dict(color='blue')), row=1, col=2)
    
    # 相位
    phase = angle(states[:, 1]) - angle(states[:, 0])
    fig_evolution.add_trace(
        Scatter(x=t_evolve, y=phase, name="相對相位", line=dict(color='orange', width=2)),
        row=2, col=1
    )
    
    # 保真度（與目標態比較，假設目標是 X 閘）
    target = array([0, 1], dtype=complex)  # |1⟩ 態
    fidelity = abs(conj(target) @ states.T)**2
    fig_evolution.add_trace(
        Scatter(x=t_evolve, y=fidelity, name="保真度", 
                  line=dict(color='purple', width=3), fill='tozeroy'),
        row=2, col=2
    )
    
    fig_evolution.update_xaxes(title_text="時間 (ns)")
    fig_evolution.update_yaxes(title_text="機率/期望值")
    fig_evolution.update_layout(height=800, showlegend=True, template='plotly_white')
    
    plotly_chart(fig_evolution, use_container_width=True)
    
    # 最終狀態資訊
    final_fidelity = fidelity[-1]
    success(f"✅ **最終保真度**: {final_fidelity:.4f} ({final_fidelity*100:.2f}%)")
    
    col_info1, col_info2, col_info3 = columns(3)
    with col_info1:
        metric("最終 |0⟩ 佔有率", f"{pop_0[-1]:.4f}")
    with col_info2:
        metric("最終 |1⟩ 佔有率", f"{pop_1[-1]:.4f}")
    with col_info3:
        metric("布洛赫球 Z 座標", f"{expect_z[-1]:.4f}")

with tab4:
    header("3D 布洛赫球視覺化")
    
    # 建立布洛赫球軌跡
    theta = arccos(expect_z)
    phi = arctan2(expect_y, expect_x)
    
    # 建立 3D 圖
    fig_bloch = Figure()
    
    # 布洛赫球表面（半透明球體）
    u = linspace(0, 2 * pi, 50)
    v = linspace(0, pi, 50)
    x_sphere = outer(cos(u), sin(v))
    y_sphere = outer(sin(u), sin(v))
    z_sphere = outer(ones(size(u)), cos(v))
    
    fig_bloch.add_trace(Surface(
        x=x_sphere, y=y_sphere, z=z_sphere,
        opacity=0.1, colorscale='Blues', showscale=False,
        name='布洛赫球'
    ))
    
    # 量子態軌跡
    x_traj = sin(theta) * cos(phi)
    y_traj = sin(theta) * sin(phi)
    z_traj = cos(theta)
    
    fig_bloch.add_trace(Scatter3d(
        x=x_traj, y=y_traj, z=z_traj,
        mode='lines',
        line=dict(color='red', width=5),
        name='演化軌跡'
    ))
    
    # 起點與終點
    fig_bloch.add_trace(Scatter3d(
        x=[0, x_traj[0]], y=[0, y_traj[0]], z=[0, z_traj[0]],
        mode='markers+lines',
        marker=dict(size=8, color='blue'),
        name='初始態 |0⟩'
    ))
    
    fig_bloch.add_trace(Scatter3d(
        x=[0, x_traj[-1]], y=[0, y_traj[-1]], z=[0, z_traj[-1]],
        mode='markers+lines',
        marker=dict(size=8, color='green'),
        name='最終態'
    ))
    
    # 座標軸
    axis_length = 1.2
    fig_bloch.add_trace(Scatter3d(x=[-axis_length, axis_length], y=[0, 0], z=[0, 0], 
                                    mode='lines', line=dict(color='black', width=2), name='X軸'))
    fig_bloch.add_trace(Scatter3d(x=[0, 0], y=[-axis_length, axis_length], z=[0, 0], 
                                    mode='lines', line=dict(color='black', width=2), name='Y軸'))
    fig_bloch.add_trace(Scatter3d(x=[0, 0], y=[0, 0], z=[-axis_length, axis_length], 
                                    mode='lines', line=dict(color='black', width=2), name='Z軸'))
    
    fig_bloch.update_layout(
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z',
            aspectmode='cube',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
        ),
        height=700,
        showlegend=True,
        title="量子態在布洛赫球上的演化軌跡"
    )
    
    plotly_chart(fig_bloch, use_container_width=True)
    
    # 顯示量子閘操作說明
    markdown("""
    <div class="equation-box">
    <h3>🎯 常見量子閘操作</h3>
    <ul>
        <li><b>X 閘 (π-pulse)</b>: 繞 X 軸旋轉 π，將 |0⟩ → |1⟩</li>
        <li><b>Y 閘</b>: 繞 Y 軸旋轉 π</li>
        <li><b>Z 閘</b>: 繞 Z 軸旋轉，改變相對相位</li>
        <li><b>Hadamard 閘</b>: 產生疊加態 (|0⟩+|1⟩)/√2</li>
    </ul>
    <p><b>目前模擬</b>: 使用 {pulse_type} 實現 X 閘操作</p>
    </div>
    """.format(pulse_type=pulse_type), unsafe_allow_html=True)

# 底部說明
markdown("---")
markdown("""
<div style="text-align: center; color: #666;">
    <p>🔬 <b>Transmon Quantum Control Simulator</b> | 基於旋轉波近似與薛丁格方程式數值解</p>
    <p>物理模型參考：Koch et al., Phys. Rev. A 76, 042319 (2007)</p>
</div>
""", unsafe_allow_html=True)
