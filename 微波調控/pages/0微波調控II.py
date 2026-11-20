from streamlit import button, checkbox, columns, dataframe, download_button, empty, info, markdown, progress, pyplot, selectbox, set_page_config, sidebar, slider, spinner, subheader, success, tabs
from matplotlib.pyplot import Circle, close, figure, subplots, tight_layout
from numpy import abs, angle, arange, array, column_stack, conj, cos, exp, imag, linalg, linspace, max, ones, ones_like, outer, pi, real, savetxt, sin, size, sqrt, trapezoid
from time import sleep
from scipy.integrate import solve_ivp
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import proj3d
from PIL import Image
from matplotlib.animation import FuncAnimation
from io import BytesIO, StringIO
from fontUtil2 import 配置中文
配置中文()

#import streamlit as st
#import numpy as np
#import matplotlib.pyplot as plt
#import matplotlib.patches as mpatches
#import time

# 頁面設定
set_page_config(page_title="Transmon 動畫模擬器", layout="wide")

# 自定義 CSS
markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 10px 24px;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        transition: 0.3s;
    }
    .equation-box {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #667eea;
        margin: 10px 0;
        font-family: 'Courier New', monospace;
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        margin: 10px;
    }
    .pulse-active {
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

markdown('<h1 class="main-header">🎬 Transmon 量子位元動態模擬器</h1>', unsafe_allow_html=True)

# 物理常數與運算子
sigma_x = array([[0, 1], [1, 0]], dtype=complex)
sigma_y = array([[0, -1j], [1j, 0]], dtype=complex)
sigma_z = array([[1, 0], [0, -1]], dtype=complex)
sigma_plus = array([[0, 1], [0, 0]], dtype=complex)
sigma_minus = array([[0, 0], [1, 0]], dtype=complex)

# 側邊欄控制
with sidebar:
    subheader("⚙️ 控制面板")
    
    subheader("量子位元參數")
    qubit_freq = slider("ω_q/2π (GHz)", 4.0, 8.0, 5.0, 0.1)
    anharmonicity = slider("α/2π (MHz)", -300.0, -100.0, -250.0, 10.0)
    
    subheader("微波控制")
    pulse_type = selectbox("脈衝類型", 
                             ["高斯 π-脈衝", "高斯 π/2-脈衝", "DRAG 脈衝", "方波脈衝"])
    pulse_duration = slider("脈衝長度 (ns)", 20, 200, 50, 10)
    
    subheader("動畫設定")
    animation_speed = slider("動畫速度", 0.1, 2.0, 1.0, 0.1)
    show_trajectory = checkbox("顯示軌跡", value=True)
    show_wigner = checkbox("顯示 Wigner 函數", value=False)
    
    subheader("環境雜訊")
    enable_noise = checkbox("啟用退相干", value=False)
    t1 = slider("T1 (μs)", 10, 200, 100, 10) if enable_noise else 1000
    t2 = slider("T2 (μs)", 5, 100, 50, 5) if enable_noise else 1000
    
    #run_simulation = button("🚀 開始模擬", key="run_btn")

# 脈衝函數定義
def gaussian_pulse(t, t0, sigma, amp):
    return amp * exp(-((t-t0)**2)/(2*sigma**2))

def drag_pulse(t, t0, sigma, amp, beta=0.5):
    gauss = exp(-((t-t0)**2)/(2*sigma**2))
    d_gauss = -(t-t0)/sigma**2 * gauss
    return amp * (gauss + 1j*beta*d_gauss)

def square_pulse(t, t_start, t_end, amp):
    return amp if t_start <= t <= t_end else 0.0

# 量子演化計算
def simulate_quantum_dynamics():
    # 參數設定
    omega_q = qubit_freq * 2 * pi  # 角頻率
    dt = 0.1  # 時間步長 (ns)
    total_time = pulse_duration * 2.5
    t_points = arange(0, total_time, dt)
    
    # 脈衝參數
    if "π-脈衝" in pulse_type:
        target_angle = pi
    elif "π/2-脈衝" in pulse_type:
        target_angle = pi/2
    else:
        target_angle = pi
    
    sigma = pulse_duration / 6
    # 計算所需振幅（脈衝面積 = target_angle）
    amp = target_angle / (sqrt(2*pi) * sigma)
    
    # 初始態 |0⟩
    psi = array([1, 0], dtype=complex)
    states = [psi.copy()]
    
    # 時間演化
    for i, t in enumerate(t_points[1:], 1):
        # 產生脈衝
        if "高斯" in pulse_type:
            envelope = gaussian_pulse(t, pulse_duration/2, sigma, amp)
        elif "DRAG" in pulse_type:
            envelope = real(drag_pulse(t, pulse_duration/2, sigma, amp))
        else:
            envelope = square_pulse(t, pulse_duration*0.2, pulse_duration*0.8, amp)
        
        # 有效哈密頓量（旋轉參考系）
        H_eff = array([[0, envelope/2], [envelope/2, 0]])
        
        # 簡單歐拉積分
        psi_dot = -1j * H_eff @ psi
        psi = psi + psi_dot * dt
        
        # 退相干（簡化模型）
        if enable_noise:
            gamma1 = 1/t1/1000  # 轉換到 ns^-1
            gamma2 = 1/t2/1000
            # T1 衰減
            p1 = abs(psi[1])**2
            decay = gamma1 * dt * p1
            psi[1] = psi[1] * sqrt(1 - decay)
            psi[0] = sqrt(1 - abs(psi[1])**2) * exp(1j*angle(psi[0]))
        
        # 歸一化
        psi = psi / linalg.norm(psi)
        states.append(psi.copy())
    
    states = array(states)
    
    # 計算期望值
    pop_0 = abs(states[:, 0])**2
    pop_1 = abs(states[:, 1])**2
    expect_x = 2 * real(conj(states[:, 0]) * states[:, 1])
    expect_y = 2 * imag(conj(states[:, 0]) * states[:, 1])
    expect_z = pop_0 - pop_1
    
    return t_points, states, pop_0, pop_1, expect_x, expect_y, expect_z, amp

# 主要內容區
#if run_simulation:
def 開始模擬():
    #with spinner("🔄 計算量子演化中..."):
    t_points, states, pop_0, pop_1, expect_x, expect_y, expect_z, pulse_amp = simulate_quantum_dynamics()
    
    success("✅ 模擬完成！")
    
    # 顯示關鍵指標
    cols = columns(4)
    metrics = [
        ("最終 |1⟩ 佔有率", f"{pop_1[-1]:.3f}", "🔴"),
        ("最大相干", f"{max(sqrt(expect_x**2 + expect_y**2)):.3f}", "🟢"),
        ("脈衝振幅", f"{pulse_amp:.2f} MHz", "🔵"),
        ("演化時間", f"{t_points[-1]:.0f} ns", "🟡")
    ]
    for col, (label, value, icon) in zip(cols, metrics):
        with col:
            markdown(f"""
            <div class="metric-card">
                <h3>{icon} {label}</h3>
                <h2>{value}</h2>
            </div>
            """, unsafe_allow_html=True)
    
    # 動畫分頁
    tab1, tab2, tab3 = tabs(["🎬 布洛赫球動畫", "📊 時域演化", "🔬 物理分析"])
    
    with tab1:
        subheader("即時布洛赫球演化")
        
        # 創建動畫幀
        n_frames = min(100, len(t_points))
        frame_indices = linspace(0, len(t_points)-1, n_frames, dtype=int)
        
        # 進度條
        progress_bar = progress(0)
        frame_placeholder = empty()
        
        # 動畫循環
        for idx, frame_i in enumerate(frame_indices):
            fig = figure(figsize=(10, 8), dpi=100)
            ax = fig.add_subplot(111, projection='3d')
            
            # 繪製布洛赫球
            u = linspace(0, 2 * pi, 30)
            v = linspace(0, pi, 30)
            x = outer(cos(u), sin(v))
            y = outer(sin(u), sin(v))
            z = outer(ones(size(u)), cos(v))
            ax.plot_surface(x, y, z, alpha=0.1, color='blue', edgecolor='none')
            
            # 繪製軸
            ax.plot([-1.2, 1.2], [0, 0], [0, 0], 'k-', linewidth=1, alpha=0.5)
            ax.plot([0, 0], [-1.2, 1.2], [0, 0], 'k-', linewidth=1, alpha=0.5)
            ax.plot([0, 0], [0, 0], [-1.2, 1.2], 'k-', linewidth=1, alpha=0.5)
            ax.text(1.3, 0, 0, '|+⟩', fontsize=12)
            ax.text(0, 1.3, 0, '|i+⟩', fontsize=12)
            ax.text(0, 0, 1.3, '|0⟩', fontsize=12)
            ax.text(0, 0, -1.3, '|1⟩', fontsize=12)
            
            # 軌跡
            if show_trajectory and frame_i > 0:
                ax.plot(expect_x[:frame_i], expect_y[:frame_i], expect_z[:frame_i], 
                       'r-', linewidth=2, alpha=0.6, label='軌跡')
            
            # 當前量子態向量
            x_q = expect_x[frame_i]
            y_q = expect_y[frame_i]
            z_q = expect_z[frame_i]
            
            # 繪製狀態向量（箭頭）
            ax.quiver(0, 0, 0, x_q, y_q, z_q, length=1.0, normalize=True, 
                     color='red', arrow_length_ratio=0.3, linewidth=3)
            
            # 點標記
            ax.scatter([x_q], [y_q], [z_q], color='red', s=100, depthshade=False)
            
            # 投影點
            ax.scatter([x_q], [y_q], [0], color='gray', s=50, alpha=0.5)
            ax.plot([x_q, x_q], [y_q, y_q], [0, z_q], 'k--', alpha=0.5)
            
            ax.set_xlim([-1.2, 1.2])
            ax.set_ylim([-1.2, 1.2])
            ax.set_zlim([-1.2, 1.2])
            ax.set_title(f'時間: {t_points[frame_i]:.1f} ns | |ψ⟩ = {pop_0[frame_i]:.3f}|0⟩ + {pop_1[frame_i]:.3f}|1⟩', 
                        fontsize=12, fontweight='bold')
            ax.set_box_aspect([1,1,1])
            
            tight_layout()
            
            # 顯示幀
            frame_placeholder.pyplot(fig)
            close(fig)
            
            # 更新進度
            progress_bar.progress((idx + 1) / n_frames)
            
            # 控制速度
            sleep(0.05 / animation_speed)
        
        # 最終狀態靜態圖
        subheader("最終量子態")
        fig_final = figure(figsize=(10, 8), dpi=150)
        ax_final = fig_final.add_subplot(111, projection='3d')
        
        # 完整的球體
        u = linspace(0, 2 * pi, 50)
        v = linspace(0, pi, 50)
        x = outer(cos(u), sin(v))
        y = outer(sin(u), sin(v))
        z = outer(ones(size(u)), cos(v))
        ax_final.plot_surface(x, y, z, alpha=0.1, color='lightblue', edgecolor='none')
        
        # 經線和緯線
        for phi in linspace(0, 2*pi, 8):
            ax_final.plot(cos(phi)*sin(v), sin(phi)*sin(v), cos(v), 'b-', alpha=0.2, linewidth=0.5)
        for theta in linspace(0, pi, 6):
            ax_final.plot(cos(u)*sin(theta), sin(u)*sin(theta), cos(theta)*ones_like(u), 'b-', alpha=0.2, linewidth=0.5)
        
        # 完整軌跡
        ax_final.plot(expect_x, expect_y, expect_z, 'r-', linewidth=2, alpha=0.8, label='演化軌跡')
        
        # 起點和終點
        ax_final.scatter([0], [0], [1], color='blue', s=200, marker='o', label='|0⟩', depthshade=False)
        ax_final.scatter([expect_x[-1]], [expect_y[-1]], [expect_z[-1]], color='red', s=200, marker='^', label='最終態', depthshade=False)
        
        # 最終向量
        ax_final.quiver(0, 0, 0, expect_x[-1], expect_y[-1], expect_z[-1], 
                       length=1.0, normalize=True, color='darkred', arrow_length_ratio=0.3, linewidth=4)
        
        ax_final.set_xlim([-1.2, 1.2])
        ax_final.set_ylim([-1.2, 1.2])
        ax_final.set_zlim([-1.2, 1.2])
        ax_final.set_title(f'完整演化軌跡 (保真度: {pop_1[-1]:.4f})', fontsize=14, fontweight='bold')
        ax_final.legend()
        ax_final.set_box_aspect([1,1,1])
        
        pyplot(fig_final)
        
        # 下載最終圖片
        buf = BytesIO()
        fig_final.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        download_button("📥 下載最終狀態圖", buf, "bloch_sphere_final.png", "image/png")
    
    with tab2:
        subheader("時域動態分析")
        
        # 創建子圖動畫
        fig2, axes = subplots(2, 2, figsize=(14, 10))
        
        # 脈衝形狀
        sigma = pulse_duration / 6
        t_pulse = linspace(0, pulse_duration*1.5, 500)
        if "高斯" in pulse_type:
            pulse_shape = gaussian_pulse(t_pulse, pulse_duration/2, sigma, pulse_amp)
        elif "DRAG" in pulse_type:
            pulse_shape = real(drag_pulse(t_pulse, pulse_duration/2, sigma, pulse_amp))
        else:
            pulse_shape = [square_pulse(t, pulse_duration*0.2, pulse_duration*0.8, pulse_amp) for t in t_pulse]
        
        # 動畫展示
        progress_bar2 = progress(0)
        plot_placeholder = empty()
        
        n_frames_2d = 50
        frame_indices_2d = linspace(0, len(t_points)-1, n_frames_2d, dtype=int)
        
        for idx, frame_i in enumerate(frame_indices_2d):
            fig2, axes = subplots(2, 2, figsize=(14, 10))
            
            # 1. 脈衝形狀 + 當前時間線
            ax1 = axes[0, 0]
            ax1.fill_between(t_pulse, pulse_shape, alpha=0.3, color='blue')
            ax1.plot(t_pulse, pulse_shape, 'b-', linewidth=2)
            ax1.axvline(x=t_points[frame_i], color='red', linestyle='--', linewidth=2, label='當前時間')
            ax1.set_xlabel('時間 (ns)')
            ax1.set_ylabel('振幅 (MHz)')
            ax1.set_title('微波脈衝包絡')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 2. 佈居數演化
            ax2 = axes[0, 1]
            ax2.fill_between(t_points[:frame_i], pop_0[:frame_i], alpha=0.3, color='blue', label='|0⟩')
            ax2.fill_between(t_points[:frame_i], pop_1[:frame_i], alpha=0.3, color='red', label='|1⟩')
            ax2.plot(t_points[:frame_i], pop_0[:frame_i], 'b-', linewidth=2)
            ax2.plot(t_points[:frame_i], pop_1[:frame_i], 'r-', linewidth=2)
            ax2.set_xlabel('時間 (ns)')
            ax2.set_ylabel('佔有率')
            ax2.set_title('能階佔有率演化')
            ax2.legend()
            ax2.set_ylim([0, 1])
            ax2.grid(True, alpha=0.3)
            
            # 3. 布洛赫球座標
            ax3 = axes[1, 0]
            ax3.plot(t_points[:frame_i], expect_x[:frame_i], 'r-', label='⟨σx⟩', linewidth=2)
            ax3.plot(t_points[:frame_i], expect_y[:frame_i], 'g-', label='⟨σy⟩', linewidth=2)
            ax3.plot(t_points[:frame_i], expect_z[:frame_i], 'b-', label='⟨σz⟩', linewidth=2)
            ax3.scatter([t_points[frame_i]], [expect_x[frame_i]], color='red', s=50, zorder=5)
            ax3.scatter([t_points[frame_i]], [expect_y[frame_i]], color='green', s=50, zorder=5)
            ax3.scatter([t_points[frame_i]], [expect_z[frame_i]], color='blue', s=50, zorder=5)
            ax3.set_xlabel('時間 (ns)')
            ax3.set_ylabel('期望值')
            ax3.set_title('布洛赫球座標')
            ax3.legend()
            ax3.set_ylim([-1.1, 1.1])
            ax3.grid(True, alpha=0.3)
            ax3.axhline(y=0, color='k', linestyle='-', alpha=0.2)
            
            # 4. 相位空間（X-Y 平面）
            ax4 = axes[1, 1]
            ax4.plot(expect_x[:frame_i], expect_y[:frame_i], 'purple', linewidth=2, alpha=0.7)
            ax4.scatter([expect_x[frame_i]], [expect_y[frame_i]], color='red', s=200, zorder=5, marker='o')
            circle = Circle((0, 0), 1, fill=False, color='gray', linestyle='--', alpha=0.5)
            ax4.add_patch(circle)
            ax4.set_xlabel('⟨σx⟩')
            ax4.set_ylabel('⟨σy⟩')
            ax4.set_title('X-Y 平面投影（相位）')
            ax4.set_xlim([-1.2, 1.2])
            ax4.set_ylim([-1.2, 1.2])
            ax4.set_aspect('equal')
            ax4.grid(True, alpha=0.3)
            
            tight_layout()
            plot_placeholder.pyplot(fig2)
            close(fig2)
            
            progress_bar2.progress((idx + 1) / n_frames_2d)
            sleep(0.05 / animation_speed)
        
        # 最終靜態圖
        fig2_final, axes = subplots(2, 2, figsize=(14, 10))
        
        axes[0, 0].fill_between(t_pulse, pulse_shape, alpha=0.3, color='blue')
        axes[0, 0].plot(t_pulse, pulse_shape, 'b-', linewidth=2)
        axes[0, 0].set_title('微波脈衝包絡')
        axes[0, 0].set_xlabel('時間 (ns)')
        axes[0, 0].grid(True, alpha=0.3)
        
        axes[0, 1].plot(t_points, pop_0, 'b-', label='|0⟩', linewidth=2)
        axes[0, 1].plot(t_points, pop_1, 'r-', label='|1⟩', linewidth=2)
        axes[0, 1].fill_between(t_points, pop_0, alpha=0.3, color='blue')
        axes[0, 1].fill_between(t_points, pop_1, alpha=0.3, color='red')
        axes[0, 1].set_title('Rabi 振盪')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        axes[1, 0].plot(t_points, expect_x, 'r-', label='⟨σx⟩', linewidth=2)
        axes[1, 0].plot(t_points, expect_y, 'g-', label='⟨σy⟩', linewidth=2)
        axes[1, 0].plot(t_points, expect_z, 'b-', label='⟨σz⟩', linewidth=2)
        axes[1, 0].set_title('布洛赫球座標演化')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        axes[1, 1].plot(expect_x, expect_y, 'purple', linewidth=2)
        axes[1, 1].scatter([expect_x[0]], [expect_y[0]], color='green', s=100, label='起點', zorder=5)
        axes[1, 1].scatter([expect_x[-1]], [expect_y[-1]], color='red', s=100, label='終點', zorder=5)
        circle = Circle((0, 0), 1, fill=False, color='gray', linestyle='--')
        axes[1, 1].add_patch(circle)
        axes[1, 1].set_title('相位空間軌跡')
        axes[1, 1].legend()
        axes[1, 1].set_aspect('equal')
        
        tight_layout()
        pyplot(fig2_final)
    
    with tab3:
        subheader("物理方程式與分析")
        
        col1, col2 = columns(2)
        
        with col1:
            markdown("""
            <div class="equation-box">
            <h4>📐 控制方程式</h4>
            
            <b>薛丁格方程式：</b>
            $$i\\hbar\\frac{\\partial|\\psi\\rangle}{\\partial t} = \\hat{H}(t)|\\psi\\rangle$$
            
            <b>有效哈密頓量（旋轉參考系）：</b>
            $$\\hat{H}_{eff} = \\frac{\\hbar\\Omega(t)}{2}\\hat{\\sigma}_x - \\frac{\\hbar\\Delta}{2}\\hat{\\sigma}_z$$
            
            <b>其中：</b>
            <ul>
            <li>$\\Omega(t)$: 脈衝包絡（Rabi 頻率）</li>
            <li>$\\Delta = \\omega_q - \\omega_d$: 失諧量</li>
            <li>$\\hat{\\sigma}_x, \\hat{\\sigma}_z$: 包立矩陣</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # 計算並顯示脈衝面積
            pulse_area = trapezoid(pulse_shape, t_pulse) / (2 * pi)
            info(f"""
            **脈衝面積定理**: 
            $$\\Theta = \\int_0^t \\Omega(t') dt' = {pulse_area:.3f} \\times 2\\pi$$
            
            理想 π-脈衝面積 = 0.5 × 2π
            """)
        
        with col2:
            markdown("""
            <div class="equation-box">
            <h4>🎯 量子態參數</h4>
            
            <b>布洛赫球座標：</b>
            $$\\langle\\hat{\\sigma}_x\\rangle = 2\\text{Re}(\\alpha^*\\beta)$$
            $$\\langle\\hat{\\sigma}_y\\rangle = 2\\text{Im}(\\alpha^*\\beta)$$  
            $$\\langle\\hat{\\sigma}_z\\rangle = |\\alpha|^2 - |\\beta|^2$$
            
            <b>純度：</b>
            $$\\text{Tr}(\\hat{\\rho}^2) = 1 \\text{ (純態)}$$
            
            <b>保真度（與目標態 |1⟩）：</b>
            $$F = |\\langle 1|\\psi\\rangle|^2 = {pop_1[-1]:.4f}$$
            </div>
            """)#.format(pop_1=pop_1), unsafe_allow_html=True)
        
        # 數據表格
        subheader("演化數據摘要")
        data_summary = {
            '時間 (ns)': t_points[::10],
            '|0⟩ 佔有率': pop_0[::10],
            '|1⟩ 佔有率': pop_1[::10],
            '⟨σx⟩': expect_x[::10],
            '⟨σy⟩': expect_y[::10],
            '⟨σz⟩': expect_z[::10]
        }
        dataframe(data_summary, use_container_width=True)
        
        # 下載數據
        csv_data = column_stack([t_points, pop_0, pop_1, expect_x, expect_y, expect_z])
        csv_buffer = StringIO()
        savetxt(csv_buffer, csv_data, delimiter=',', 
                  header='time_ns,pop_0,pop_1,sigma_x,sigma_y,sigma_z', comments='')
        download_button("📥 下載 CSV 數據", csv_buffer.getvalue(), "quantum_evolution_data.csv", "text/csv")

#else:
def 初始():
    # 初始畫面
    info("👈 請在左側設定參數，然後點擊「開始模擬」")
    
    # 顯示預覽圖
    fig_preview = figure(figsize=(10, 8), dpi=100)
    ax_prev = fig_preview.add_subplot(111, projection='3d')
    
    # 繪製空布洛赫球
    u = linspace(0, 2 * pi, 30)
    v = linspace(0, pi, 30)
    x = outer(cos(u), sin(v))
    y = outer(sin(u), sin(v))
    z = outer(ones(size(u)), cos(v))
    ax_prev.plot_surface(x, y, z, alpha=0.1, color='blue')
    
    # 座標軸
    ax_prev.plot([-1.2, 1.2], [0, 0], [0, 0], 'k-', linewidth=1)
    ax_prev.plot([0, 0], [-1.2, 1.2], [0, 0], 'k-', linewidth=1)
    ax_prev.plot([0, 0], [0, 0], [-1.2, 1.2], 'k-', linewidth=1)
    
    # 初始態 |0⟩
    ax_prev.scatter([0], [0], [1], color='blue', s=200, label='|0⟩')
    ax_prev.set_title("初始狀態：|0⟩（等待模擬）", fontsize=14)
    ax_prev.set_box_aspect([1,1,1])
    
    pyplot(fig_preview)
    
    markdown("""
    ### 🎮 使用說明
    
    1. **設定量子位元參數**：調整頻率與非諧性
    2. **選擇脈衝類型**：高斯脈衝（平滑）、DRAG（抑制洩漏）、方波（簡單）
    3. **調整脈衝長度**：影響 Rabi 振盪週期
    4. **啟用雜訊**：模擬真實環境的退相干效應
    5. **點擊開始**：觀看即時動畫演化
    
    ### 📚 物理背景
    
    此模擬基於**旋轉波近似（RWA）**，在與驅動場共振旋轉的參考系中，量子位元受到有效磁場：
    - **X 方向**：由微波振幅控制（Rabi 驅動）
    - **Z 方向**：由失諧量控制（相位累積）
    """)

markdown("---")
markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>🔬 <b>Quantum Dynamics Animation Simulator</b> | Powered by Matplotlib & Streamlit</p>
    <p>物理模型：Rabi 模型 + 開放量子系統（Lindbladian）</p>
</div>
""", unsafe_allow_html=True)
初始()
開始模擬()
