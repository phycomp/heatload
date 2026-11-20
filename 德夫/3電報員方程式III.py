from streamlit import button, columns, dataframe, empty, expander, header, markdown, metric, number_input, plotly_chart, pyplot, selectbox, set_page_config, sidebar, slider, spinner, subheader, success, tabs, warning
from matplotlib.pyplot import close, cm, colorbar, subplots, tight_layout
from numpy import abs, exp, linspace, max, maximum, meshgrid, pi, real, sin, sqrt, where, zeros
from time import sleep
from plotly.graph_objects import Figure, Frame, Scatter

# 創建完整的Streamlit應用程式代碼
#import streamlit as st
#import numpy as np
#import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import plotly.graph_objects as go
from plotly.subplots import make_subplots
#import time

# 頁面設定
set_page_config(
    page_title="電報員方程式模擬器",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS樣式美化
markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .parameter-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .equation-box {
        background: black;
        /*border-left: 5px solid #1f77b4;*/
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 10px 10px 0;
        font-family: 'Courier New', monospace;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# 標題
markdown('<div class="main-header">📡 電報員方程式模擬器</div>', unsafe_allow_html=True)
markdown('<div class="sub-header">Telegrapher\'s Equation Simulation: 從Maxwell方程到傳輸線波動</div>', unsafe_allow_html=True)

# 側邊欄 - 參數控制
with sidebar:
    header("⚙️ 傳輸線參數設定")
    
    subheader("基本參數")
    col1, col2 = columns(2)
    with col1:
        L = number_input("電感 L (μH/m)", value=0.25, min_value=0.01, max_value=10.0, step=0.01)
        R = number_input("電阻 R (Ω/m)", value=0.0, min_value=0.0, max_value=100.0, step=0.1)
    with col2:
        C = number_input("電容 C (pF/m)", value=100.0, min_value=1.0, max_value=1000.0, step=1.0)
        G = number_input("電導 G (mS/m)", value=0.0, min_value=0.0, max_value=10.0, step=0.01)
    
    # 單位轉換
    L = L * 1e-6
    C = C * 1e-12
    G = G * 1e-3
    
    subheader("幾何與時間參數")
    length = slider("傳輸線長度 (m)", 10, 500, 100)
    duration = slider("模擬時間 (μs)", 0.1, 10.0, 1.0) * 1e-6
    
    subheader("信號源設定")
    source_type = selectbox(
        "信號類型",
        ["高斯脈衝", "正弦波", "方波", "三角波"]
    )
    
    freq = slider("頻率 (MHz)", 0.1, 100.0, 10.0) * 1e6
    amplitude = slider("振幅 (V)", 0.1, 10.0, 1.0)
    
    subheader("數值參數")
    nx = slider("空間格點數", 50, 500, 200)
    nt = slider("時間步數", 100, 2000, 500)

# 計算衍生參數
v = 1 / sqrt(L * C) if L*C > 0 else 0
Z0 = sqrt(L / C) if L*C > 0 else 0
alpha = (R * sqrt(C/L) + G * sqrt(L/C)) / 2 if Z0 > 0 else 0  # 衰減常數

# 顯示關鍵指標
col1, col2, col3, col4 = columns(4)
with col1:
    metric("波速 v", f"{v/1e6:.2f} Mm/s", f"{v/299792458:.2%} c")
with col2:
    metric("特性阻抗 Z₀", f"{Z0:.1f} Ω")
with col3:
    metric("衰減常數 α", f"{alpha:.3f} Np/m")
with col4:
    wavelength = v / freq if freq > 0 else 0
    metric("波長 λ", f"{wavelength:.2f} m")

# 顯示電報員方程式
markdown("""
    ### 📐 電報員方程式 (Telegrapher's Equations)

    - $$\\frac{\\partial^2 V}{\\partial z^2} = LC\\frac{\\partial^2 V}{\\partial t^2} + (RC+LG)\\frac{\\partial V}{\\partial t} + RGV$$
    - $LC\\frac{\\partial^2 V}{\\partial t^2}$：波動項（電磁波傳播）<br>
    - $(RC+LG)\\frac{\\partial V}{\\partial t}$：耗散項（歐姆損耗與介質損耗）
    - $RGV$：靜態耦合項
""", unsafe_allow_html=True)

# 數值求解函數
def solve_telegrapher(L, C, R, G, length, duration, nx, nt, source_type, freq, amp):
    dz = length / nx
    dt = duration / nt
    
    # Courant條件
    courant = v * dt / dz if v > 0 else 0
    
    z = linspace(0, length, nx)
    t = linspace(0, duration, nt)
    V = zeros((nt, nx))
    
    # 初始條件
    if source_type == "高斯脈衝":
        sigma = length * 0.05
        V[0, :] = amp * exp(-((z - length*0.1)**2) / (2*sigma**2))
    elif source_type == "正弦波":
        V[0, :] = amp * sin(2*pi*freq*z/v) * exp(-z/(length*0.3))
    elif source_type == "方波":
        V[0, :] = amp * where((z > length*0.05) & (z < length*0.15), 1, 0)
    elif source_type == "三角波":
        center = length * 0.1
        width = length * 0.1
        V[0, :] = amp * maximum(0, 1 - abs(z - center)/width)
    
    V[1, :] = V[0, :]
    
    # 時間迭代
    for n in range(1, nt-1):
        # 內部點
        for i in range(1, nx-1):
            if R == 0 and G == 0:
                # 無損耗 - 簡單波動方程
                V[n+1, i] = (2*V[n, i] - V[n-1, i] + 
                           (v*dt/dz)**2 * (V[n, i+1] - 2*V[n, i] + V[n, i-1]))
            else:
                # 有損耗 - 完整電報員方程
                damping = (R*C + L*G) * dt / (2*L*C)
                loss = R*G * dt**2 / (L*C)
                wave_term = (v*dt/dz)**2 * (V[n, i+1] - 2*V[n, i] + V[n, i-1])
                
                V[n+1, i] = ((2*V[n, i] - V[n-1, i] + wave_term - 
                            damping*(V[n, i] - V[n-1, i]) - loss*V[n, i]) / 
                           (1 + damping))
        
        # 邊界條件：持續注入信號
        if n < nt//3:
            t_norm = t[n+1] / (duration/3)
            if source_type == "高斯脈衝":
                V[n+1, 0] = amp * exp(-((t[n+1] - duration*0.05)**2) / (2*(duration*0.02)**2))
            elif source_type == "正弦波":
                V[n+1, 0] = amp * sin(2*pi*freq*t[n+1]) * exp(-t[n+1]/(duration*0.3))
            elif source_type == "方波":
                V[n+1, 0] = amp if sin(2*pi*freq*t[n+1]) > 0 else -amp
            elif source_type == "三角波":
                phase = (freq * t[n+1]) % 1.0
                V[n+1, 0] = amp * (2 * abs(2*phase - 1) - 1)
        
        # 右邊界：吸收邊界條件（簡化）
        V[n+1, -1] = V[n+1, -2]
    
    return z, t, V, courant

# 執行模擬
if button("🚀 開始模擬", type="primary", use_container_width=True):
    with spinner("正在求解電報員方程式..."):
        z, t, V, courant = solve_telegrapher(L, C, R, G, length, duration, nx, nt, source_type, freq, amplitude)
        
        if courant > 1:
            warning(f"⚠️ Courant數 = {courant:.2f} > 1，數值可能不穩定")
        else:
            success(f"✅ Courant數 = {courant:.2f}，數值穩定")
        
        # 創建分頁顯示
        tab1, tab2, tab3 = tabs(["📊 靜態分析", "🎬 動畫模擬", "📈 頻譜分析"])
        
        with tab1:
            subheader("多時間點波形比較")
            
            fig, axes = subplots(2, 2, figsize=(14, 10))
            
            # 選擇時間點
            time_points = [int(nt*0.1), int(nt*0.3), int(nt*0.5), int(nt*0.7), int(nt*0.9)]
            colors = cm.plasma(linspace(0, 1, len(time_points)))
            
            # 空間分佈
            ax1 = axes[0, 0]
            for tp, color in zip(time_points, colors):
                ax1.plot(z, V[tp, :], color=color, linewidth=2.5, 
                        label=f't={t[tp]*1e6:.2f}μs')
            ax1.set_xlabel('Position z (m)', fontsize=12)
            ax1.set_ylabel('Voltage V (V)', fontsize=12)
            ax1.set_title('Wave Propagation along Transmission Line', fontsize=13, fontweight='bold')
            ax1.legend(loc='upper right')
            ax1.grid(True, alpha=0.3)
            
            # 時域波形 - 多位置
            ax2 = axes[0, 1]
            positions = [int(nx*0.2), int(nx*0.5), int(nx*0.8)]
            for pos in positions:
                ax2.plot(t*1e6, V[:, pos], linewidth=2, label=f'z={z[pos]:.1f}m')
            ax2.set_xlabel('Time (μs)', fontsize=12)
            ax2.set_ylabel('Voltage V (V)', fontsize=12)
            ax2.set_title('Time Domain Signals at Fixed Positions', fontsize=13, fontweight='bold')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # 2D時空圖
            ax3 = axes[1, 0]
            T_mesh, Z_mesh = meshgrid(t*1e6, z)
            im = ax3.contourf(T_mesh, Z_mesh, V.T, levels=50, cmap='RdBu_r')
            ax3.set_xlabel('Time (μs)', fontsize=12)
            ax3.set_ylabel('Position z (m)', fontsize=12)
            ax3.set_title('Space-Time Diagram (z vs t)', fontsize=13, fontweight='bold')
            colorbar(im, ax=ax3, label='Voltage (V)')
            
            # 衰減分析
            ax4 = axes[1, 1]
            peak_voltages = [max(V[i, :]) for i in range(nt)]
            ax4.semilogy(t*1e6, peak_voltages, 'b-', linewidth=2, label='Peak Voltage')
            if R > 0 or G > 0:
                # 理論衰減曲線
                theoretical = amplitude * exp(-alpha * v * t)
                ax4.semilogy(t*1e6, theoretical, 'r--', linewidth=2, label=f'Theory: exp(-αvt)')
            ax4.set_xlabel('Time (μs)', fontsize=12)
            ax4.set_ylabel('Peak Voltage (V, log scale)', fontsize=12)
            ax4.set_title('Signal Attenuation Analysis', fontsize=13, fontweight='bold')
            ax4.legend()
            ax4.grid(True, alpha=0.3, which='both')
            
            tight_layout()
            pyplot(fig)
            
            # 顯示數據表格
            with expander("📋 查看模擬數據"):
                data_dict = {
                    '時間 (μs)': t[::10]*1e6,
                    '輸入電壓 (V)': V[::10, 0],
                    '中點電壓 (V)': V[::10, nx//2],
                    '輸出電壓 (V)': V[::10, -1]
                }
                dataframe(data_dict, use_container_width=True)
        
        with tab2:
            subheader("即時動畫模擬")
            
            # 使用Plotly創建互動式動畫
            frames = []
            n_frames = min(50, nt)  # 限制幀數
            frame_indices = linspace(0, nt-1, n_frames, dtype=int)
            
            for idx in frame_indices:
                frames.append(Frame(
                    data=[Scatter(
                        x=z, 
                        y=V[idx, :],
                        mode='lines',
                        line=dict(color='#1f77b4', width=3),
                        fill='tozeroy',
                        fillcolor='rgba(31, 119, 180, 0.3)'
                    )],
                    name=f'frame{idx}'
                ))
            
            fig_anim = Figure(
                data=[Scatter(
                    x=z, 
                    y=V[0, :],
                    mode='lines',
                    line=dict(color='#1f77b4', width=3),
                    fill='tozeroy',
                    fillcolor='rgba(31, 119, 180, 0.3)'
                )],
                frames=frames
            )
            
            fig_anim.update_layout(
                title="Transmission Line Voltage Propagation",
                xaxis_title="Position z (m)",
                yaxis_title="Voltage V (V)",
                yaxis=dict(range=[-amplitude*1.2, amplitude*1.2]),
                updatemenus=[{
                    "type": "buttons",
                    "direction": "left",
                    "buttons": [
                        {
                            "label": "▶️ Play",
                            "method": "animate",
                            "args": [None, {"frame": {"duration": 50, "redraw": True}, 
                                          "fromcurrent": True, "mode": "immediate"}]
                        },
                        {
                            "label": "⏸️ Pause",
                            "method": "animate",
                            "args": [[None], {"frame": {"duration": 0, "redraw": False}, 
                                            "mode": "immediate", "transition": {"duration": 0}}]
                        }
                    ],
                    "pad": {"r": 10, "t": 10},
                    "showactive": True,
                    "x": 0.1,
                    "xanchor": "right",
                    "y": 0,
                    "yanchor": "top"
                }],
                sliders=[{
                    "active": 0,
                    "yanchor": "top",
                    "xanchor": "left",
                    "currentvalue": {
                        "font": {"size": 16},
                        "prefix": "Time: ",
                        "visible": True,
                        "xanchor": "right"
                    },
                    "transition": {"duration": 50, "easing": "cubic-in-out"},
                    "pad": {"b": 10, "t": 50},
                    "len": 0.9,
                    "x": 0.1,
                    "y": 0,
                    "steps": [
                        {
                            "args": [[f"frame{f}"], {"frame": {"duration": 50, "redraw": True},
                                                     "mode": "immediate", "transition": {"duration": 50}}],
                            "label": f"{t[f]*1e6:.2f}μs",
                            "method": "animate"
                        } for f in frame_indices
                    ]
                }]
            )
            
            plotly_chart(fig_anim, use_container_width=True)
            
            # 進度條動畫
            subheader("模擬進度視覺化")
            progress_placeholder = empty()
            chart_placeholder = empty()
            
            if button("▶️ 播放簡易動畫", key="simple_anim"):
                for i in range(0, nt, 5):
                    progress = (i + 1) / nt
                    progress_placeholder.progress(progress, 
                        text=f"模擬時間: {t[i]*1e6:.2f} μs / {duration*1e6:.2f} μs")
                    
                    fig_temp, ax = subplots(figsize=(10, 4))
                    ax.plot(z, V[i, :], 'b-', linewidth=2)
                    ax.fill_between(z, V[i, :], alpha=0.3)
                    ax.set_xlim(0, length)
                    ax.set_ylim(-amplitude*1.2, amplitude*1.2)
                    ax.set_xlabel('Position z (m)')
                    ax.set_ylabel('Voltage V (V)')
                    ax.set_title(f'Time = {t[i]*1e6:.2f} μs')
                    ax.grid(True, alpha=0.3)
                    chart_placeholder.pyplot(fig_temp)
                    close()
                    sleep(0.02)
                
                progress_placeholder.empty()
                chart_placeholder.empty()
        
        with tab3:
            subheader("頻譜與色散分析")
            
            # FFT分析
            from scipy.fft import fft, fftfreq
            
            # 選擇分析位置
            pos_fft = selectbox("選擇FFT分析位置", 
                                  [f"z={z[i]:.1f}m (位置{i})" for i in [0, nx//4, nx//2, 3*nx//4, nx-1]])
            pos_idx = [0, nx//4, nx//2, 3*nx//4, nx-1][
                [f"z={z[i]:.1f}m (位置{i})" for i in [0, nx//4, nx//2, 3*nx//4, nx-1]].index(pos_fft)
            ]
            
            signal = V[:, pos_idx]
            N = len(signal)
            yf = fft(signal)
            xf = fftfreq(N, t[1]-t[0])[:N//2]
            
            fig_fft, axes = subplots(2, 2, figsize=(14, 8))
            
            # 時域信號
            axes[0, 0].plot(t*1e6, signal, 'b-', linewidth=1.5)
            axes[0, 0].set_xlabel('Time (μs)')
            axes[0, 0].set_ylabel('Voltage (V)')
            axes[0, 0].set_title(f'Time Domain Signal at {pos_fft}')
            axes[0, 0].grid(True, alpha=0.3)
            
            # 頻譜
            magnitude = 2.0/N * abs(yf[0:N//2])
            axes[0, 1].semilogy(xf/1e6, magnitude, 'r-', linewidth=1.5)
            axes[0, 1].set_xlabel('Frequency (MHz)')
            axes[0, 1].set_ylabel('Magnitude')
            axes[0, 1].set_title('Frequency Spectrum')
            axes[0, 1].set_xlim(0, 100)
            axes[0, 1].grid(True, alpha=0.3, which='both')
            
            # 相位速度分析
            if R > 0 or G > 0:
                # 有損耗線的色散關係
                omega = 2 * pi * xf
                beta = sqrt((omega**2 * L * C + R * G) / 2 + 
                              sqrt(((omega**2 * L * C - R * G)**2 + omega**2 * (R * C + L * G)**2) / 4))
                v_phase = omega / beta
                
                axes[1, 0].plot(xf[1:]/1e6, real(v_phase[1:])/1e6, 'g-', linewidth=2)
                axes[1, 0].axhline(y=v/1e6, color='r', linestyle='--', label='Lossless phase velocity')
                axes[1, 0].set_xlabel('Frequency (MHz)')
                axes[1, 0].set_ylabel('Phase Velocity (Mm/s)')
                axes[1, 0].set_title('Dispersion Relation')
                axes[1, 0].legend()
                axes[1, 0].grid(True, alpha=0.3)
            else:
                axes[1, 0].text(0.5, 0.5, '無損耗線無色散\\n相位速度為常數', 
                               ha='center', va='center', transform=axes[1, 0].transAxes, fontsize=14)
                axes[1, 0].set_title('Dispersion Relation (Lossless)')
            
            # 衰減常數 vs 頻率
            if R > 0 or G > 0:
                alpha_f = sqrt((R * sqrt(C/L) + G * sqrt(L/C)) / 2 * omega + 
                                 (R * G - omega**2 * L * C) / 2 + 
                                 sqrt(((R * G - omega**2 * L * C)**2 + omega**2 * (R * C + L * G)**2) / 4))
                axes[1, 1].semilogy(xf[1:]/1e6, alpha_f[1:], 'm-', linewidth=2)
                axes[1, 1].set_xlabel('Frequency (MHz)')
                axes[1, 1].set_ylabel('Attenuation Constant α (Np/m)')
                axes[1, 1].set_title('Frequency-Dependent Attenuation')
                axes[1, 1].grid(True, alpha=0.3, which='both')
            else:
                axes[1, 1].text(0.5, 0.5, '無損耗線\\nα = 0', 
                               ha='center', va='center', transform=axes[1, 1].transAxes, fontsize=14)
                axes[1, 1].set_title('Attenuation (Lossless)')
            
            tight_layout()
            pyplot(fig_fft)

# 理論說明區塊
with expander("📚 理論推導與物理意義", expanded=False):
    markdown("""
    ### 從Maxwell方程到電報員方程式
    
    #### 1. 傳輸線近似
    對於平行雙導體或同軸結構，假設TEM模式傳播，Maxwell方程簡化為一維形式：
    
    $$-\\frac{\\partial V}{\\partial z} = RI + L\\frac{\\partial I}{\\partial t} \quad \text{(KVL)}$$
    $$-\\frac{\\partial I}{\\partial z} = GV + C\\frac{\\partial V}{\\partial t} \quad \text{(KCL)}$$
    
    #### 2. 推導過程
    對第一式求z偏導，第二式求t偏導，消去電流I，得到電壓V的電報員方程式：
    
    $$\\frac{\\partial^2 V}{\\partial z^2} = LC\\frac{\\partial^2 V}{\\partial t^2} + (RC+LG)\\frac{\\partial V}{\\partial t} + RGV$$
    
    #### 3. 各項物理意義
    - **$LC\\frac{\\partial^2 V}{\\partial t^2}$**：波動項，決定電磁波傳播速度 $v = 1/\\sqrt{LC}$
    - **$(RC+LG)\\frac{\\partial V}{\\partial t}$**：耗散項，導致信號衰減和失真
    - **$RGV$**：靜態耦合項，低頻時的主導損耗機制
    
    #### 4. 特殊情況
    - **無損耗線** ($R=0, G=0$)：簡化為標準波動方程，無色散無衰減
    - **無失真線** ($R/L = G/C$)：Heaviside條件，雖有損耗但無波形失真
    - **低頻近似**：忽略電容，退化為擴散方程（RC線）
    """)

# 頁尾
markdown("---")
markdown("<div style='text-align: center; color: #666;'>電報員方程式模擬器 v1.0 | 基於有限差分法數值求解</div>", unsafe_allow_html=True)

## 保存代碼到文件
#with open('/mnt/kimi/output/telegrapher_streamlit_app.py', 'w', encoding='utf-8') as f:
#    f.write(streamlit_code)
#
#print("✅ Streamlit應用程式已生成！")
#print("📁 文件位置: /mnt/kimi/output/telegrapher_streamlit_app.py")
#print("\n🚀 運行方式:")
#print("   streamlit run telegrapher_streamlit_app.py")
#print("\n📦 所需套件:")
#print("   pip install streamlit numpy matplotlib plotly scipy")
