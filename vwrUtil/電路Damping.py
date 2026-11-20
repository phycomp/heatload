# physics_simulations_patch.py
import streamlit as st
from streamlit import radio
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sympy as sp

def add_physics_simulations():
    """添加物理模擬到主應用"""
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🔬 進階物理模擬"):
        st.session_state.show_advanced_physics = True
    
    if st.session_state.get('show_advanced_physics', False):
        advanced_physics_simulations()
        
        if st.button("← 返回主應用"):
            st.session_state.show_advanced_physics = False
            st.experimental_rerun()
        
        st.stop()

def advanced_physics_simulations():
    """進階物理模擬界面"""
    st.header("🔬 進階物理模擬實驗室")
    
    simulation_type = radio( "選擇模擬類型", [ "力學阻尼系統", "RLC電路頻率響應", "阻抗匹配分析", "機械振動分析", "濾波器設計模擬" ], horizontal=True, index=0)
    
    if simulation_type == "力學阻尼系統":
        mechanical_damping_simulation()
    elif simulation_type == "RLC電路頻率響應":
        rlc_circuit_simulation()
    elif simulation_type == "阻抗匹配分析":
        impedance_matching_simulation()
    elif simulation_type == "機械振動分析":
        mechanical_vibration_simulation()
    elif simulation_type == "濾波器設計模擬":
        filter_design_simulation()

def mechanical_damping_simulation():
    """力學阻尼系統模擬"""
    st.subheader("🏗️ 力學阻尼系統分析")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 系統參數")
        
        # 質量-彈簧-阻尼系統參數
        mass = st.slider("質量 m (kg)", 0.1, 10.0, 1.0, 0.1)
        spring_constant = st.slider("彈簧常數 k (N/m)", 1.0, 100.0, 10.0, 1.0)
        damping_coefficient = st.slider("阻尼係數 c (Ns/m)", 0.0, 10.0, 0.5, 0.1)
        
        # 初始條件
        initial_displacement = st.slider("初始位移 x₀ (m)", -2.0, 2.0, 1.0, 0.1)
        initial_velocity = st.slider("初始速度 v₀ (m/s)", -5.0, 5.0, 0.0, 0.1)
        
        # 外力參數
        force_amplitude = st.slider("外力振幅 F₀ (N)", 0.0, 20.0, 0.0, 0.5)
        force_frequency = st.slider("外力頻率 ω (rad/s)", 0.1, 10.0, 2.0, 0.1)
        
        # 計算系統特性
        natural_frequency = np.sqrt(spring_constant / mass)  # 自然頻率
        damping_ratio = damping_coefficient / (2 * np.sqrt(mass * spring_constant))  # 阻尼比
        
        st.markdown("### 系統特性")
        st.write(f"自然頻率 ωₙ: {natural_frequency:.3f} rad/s")
        st.write(f"阻尼比 ζ: {damping_ratio:.3f}")
        
        if damping_ratio < 1:
            st.success("欠阻尼系統")
            damped_frequency = natural_frequency * np.sqrt(1 - damping_ratio**2)
            st.write(f"阻尼自然頻率: {damped_frequency:.3f} rad/s")
        elif damping_ratio == 1:
            st.warning("臨界阻尼系統")
        else:
            st.error("過阻尼系統")
    
    with col2:
        # 模擬時間範圍
        t = np.linspace(0, 20, 1000)
        
        # 計算系統響應
        if force_amplitude == 0:
            # 自由振動
            if damping_ratio < 1:  # 欠阻尼
                omega_d = natural_frequency * np.sqrt(1 - damping_ratio**2)
                displacement = np.exp(-damping_ratio * natural_frequency * t) * (
                    initial_displacement * np.cos(omega_d * t) + 
                    (initial_velocity + damping_ratio * natural_frequency * initial_displacement) / omega_d * np.sin(omega_d * t)
                )
            elif damping_ratio == 1:  # 臨界阻尼
                displacement = np.exp(-natural_frequency * t) * (
                    initial_displacement + (initial_velocity + natural_frequency * initial_displacement) * t
                )
            else:  # 過阻尼
                beta = natural_frequency * np.sqrt(damping_ratio**2 - 1)
                r1 = -natural_frequency * damping_ratio + beta
                r2 = -natural_frequency * damping_ratio - beta
                A = (initial_velocity - r2 * initial_displacement) / (r1 - r2)
                B = initial_displacement - A
                displacement = A * np.exp(r1 * t) + B * np.exp(r2 * t)
        else:
            # 強制振動
            # 使用數值積分求解
            def system_ode(y, t):
                x, v = y
                dxdt = v
                dvdt = (force_amplitude * np.cos(force_frequency * t) - 
                       damping_coefficient * v - spring_constant * x) / mass
                return [dxdt, dvdt]
            
            from scipy.integrate import odeint
            y0 = [initial_displacement, initial_velocity]
            solution = odeint(system_ode, y0, t)
            displacement = solution[:, 0]
        
        # 繪製位移時間圖
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=t, y=displacement, mode='lines', name='位移', line=dict(color='blue', width=2)))
        fig1.update_layout(
            title='位移-時間響應',
            xaxis_title='時間 (s)',
            yaxis_title='位移 (m)',
            height=400
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # 相位圖 (速度 vs 位移)
        if force_amplitude > 0:
            velocity = np.gradient(displacement, t)
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=displacement, y=velocity, mode='lines', 
                                    name='相位軌跡', line=dict(color='red', width=2)))
            fig2.update_layout(
                title='相位圖 (位移 vs 速度)',
                xaxis_title='位移 (m)',
                yaxis_title='速度 (m/s)',
                height=300
            )
            st.plotly_chart(fig2, use_container_width=True)

def rlc_circuit_simulation():
    """RLC電路頻率響應模擬"""
    st.subheader("⚡ RLC電路頻率響應分析")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 電路參數")
        
        # RLC串聯電路參數
        resistance = st.slider("電阻 R (Ω)", 1.0, 1000.0, 100.0, 10.0)
        inductance = st.slider("電感 L (H)", 0.001, 1.0, 0.1, 0.001)
        capacitance = st.slider("電容 C (F)", 1e-6, 100e-6, 10e-6, 1e-6)
        
        # 輸入信號
        input_voltage = st.slider("輸入電壓 V_in (V)", 1.0, 20.0, 10.0, 0.5)
        
        # 計算電路特性
        resonant_frequency = 1 / (2 * np.pi * np.sqrt(inductance * capacitance))
        quality_factor = (1 / resistance) * np.sqrt(inductance / capacitance)
        bandwidth = resonant_frequency / quality_factor
        
        st.markdown("### 電路特性")
        st.write(f"共振頻率: {resonant_frequency:.2f} Hz")
        st.write(f"品質因數 Q: {quality_factor:.2f}")
        st.write(f"帶寬: {bandwidth:.2f} Hz")
        
        # 選擇輸出量
        output_type = st.selectbox("觀察的響應", 
                                 ["阻抗幅度", "阻抗相位", "電流響應", "電壓增益"])
    
    with col2:
        # 頻率範圍
        f_min = max(0.1, resonant_frequency / 10)
        f_max = resonant_frequency * 10
        frequencies = np.logspace(np.log10(f_min), np.log10(f_max), 1000)
        omega = 2 * np.pi * frequencies
        
        # 計算阻抗
        Z_R = resistance
        Z_L = 1j * omega * inductance
        Z_C = 1 / (1j * omega * capacitance)
        Z_total = Z_R + Z_L + Z_C
        
        # 計算各種響應
        if output_type == "阻抗幅度":
            response = np.abs(Z_total)
            y_label = "阻抗幅度 |Z| (Ω)"
        elif output_type == "阻抗相位":
            response = np.angle(Z_total, deg=True)
            y_label = "阻抗相位 (度)"
        elif output_type == "電流響應":
            I = input_voltage / Z_total
            response = np.abs(I)
            y_label = "電流幅度 (A)"
        elif output_type == "電壓增益":
            # 電容電壓增益
            V_C = (Z_C / Z_total) * input_voltage
            response = np.abs(V_C) / input_voltage
            y_label = "電壓增益 |V_C/V_in|"
        
        # 繪製頻率響應
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=frequencies, y=response, mode='lines', 
                               line=dict(color='green', width=3)))
        
        # 標記共振頻率
        fig.add_vline(x=resonant_frequency, line_dash="dash", 
                     line_color="red", annotation_text="共振頻率")
        
        fig.update_layout(
            title=f'RLC電路 {output_type} 頻率響應',
            xaxis_title='頻率 (Hz)',
            yaxis_title=y_label,
            xaxis_type='log',
            height=500
        )
        
        if output_type != "阻抗相位":
            fig.update_yaxis(type='log')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 顯示阻抗信息
        st.markdown("### 阻抗分析")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            Z_at_resonance = resistance  # 在共振時阻抗最小，等於電阻
            st.metric("共振時阻抗", f"{Z_at_resonance:.2f} Ω")
        
        with col2:
            st.metric("電感抗 at ω₀", f"{2 * np.pi * resonant_frequency * inductance:.2f} Ω")
        
        with col3:
            st.metric("電容抗 at ω₀", f"{1/(2 * np.pi * resonant_frequency * capacitance):.2f} Ω")

def impedance_matching_simulation():
    """阻抗匹配分析模擬"""
    st.subheader("🎯 阻抗匹配分析")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 源阻抗和負載阻抗")
        
        # 源阻抗 (複數)
        st.markdown("#### 源阻抗 Zₛ")
        Rs = st.slider("源電阻 Rₛ (Ω)", 1.0, 1000.0, 50.0, 10.0)
        Ls = st.slider("源電感 Lₛ (H)", 0.0, 1e-3, 0.0, 1e-6)
        
        # 負載阻抗 (複數)
        st.markdown("#### 負載阻抗 Zₗ")
        Rl = st.slider("負載電阻 Rₗ (Ω)", 1.0, 1000.0, 75.0, 10.0)
        Ll = st.slider("負載電感 Lₗ (H)", 0.0, 1e-3, 0.0, 1e-6)
        Cl = st.slider("負載電容 Cₗ (F)", 0.0, 1e-6, 0.0, 1e-9)
        
        # 工作頻率
        frequency = st.slider("工作頻率 f (Hz)", 1e3, 100e6, 1e6, 1e3)
        omega = 2 * np.pi * frequency
        
        # 匹配網絡類型
        matching_network = st.selectbox("匹配網絡類型", 
                                      ["L型網絡", "π型網絡", "T型網絡", "變壓器匹配"])
    
    with col2:
        # 計算阻抗
        Z_source = Rs + 1j * omega * Ls
        Z_load = Rl + 1j * omega * Ll - 1j / (omega * Cl) if Cl > 0 else Rl + 1j * omega * Ll
        
        # 計算反射係數和駐波比
        gamma = (Z_load - Z_source.conjugate()) / (Z_load + Z_source.conjugate())
        vswr = (1 + abs(gamma)) / (1 - abs(gamma)) if abs(gamma) < 1 else float('inf')
        
        # 計算功率傳輸效率
        P_available = 1.0  # 假設可用功率為1W
        P_delivered = 1 - abs(gamma)**2
        
        st.markdown("### 匹配性能")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("反射係數 |Γ|", f"{abs(gamma):.4f}")
        
        with col2:
            st.metric("駐波比 VSWR", f"{vswr:.4f}")
        
        with col3:
            st.metric("功率傳輸效率", f"{P_delivered*100:.2f}%")
        
        # 史密斯圖
        st.markdown("### 史密斯圖")
        fig = create_smith_chart(Z_source, Z_load, frequency)
        st.plotly_chart(fig, use_container_width=True)
        
        # 顯示匹配建議
        st.markdown("### 匹配網絡設計")
        if matching_network == "L型網絡":
            display_l_matching_design(Z_source, Z_load, frequency)
        elif matching_network == "π型網絡":
            display_pi_matching_design(Z_source, Z_load, frequency)
        elif matching_network == "T型網絡":
            display_t_matching_design(Z_source, Z_load, frequency)
        elif matching_network == "變壓器匹配":
            display_transformer_matching(Z_source, Z_load)

def create_smith_chart(Z_source, Z_load, frequency):
    """創建史密斯圖"""
    # 簡化的史密斯圖實現
    fig = go.Figure()
    
    # 添加阻抗點
    Z0 = 50  # 特性阻抗
    
    # 計算歸一化阻抗
    z_load = Z_load / Z0
    z_source = Z_source / Z0
    
    # 計算反射係數
    gamma_load = (z_load - 1) / (z_load + 1)
    gamma_source = (z_source - 1) / (z_source + 1)
    
    # 添加阻抗點
    fig.add_trace(go.Scatter(
        x=[gamma_load.real], y=[gamma_load.imag],
        mode='markers+text',
        marker=dict(size=15, color='red'),
        text=['Z_load'],
        textposition="top center",
        name='負載阻抗'
    ))
    
    fig.add_trace(go.Scatter(
        x=[gamma_source.real], y=[gamma_source.imag],
        mode='markers+text',
        marker=dict(size=15, color='blue'),
        text=['Z_source'],
        textposition="top center",
        name='源阻抗'
    ))
    
    fig.update_layout(
        title='史密斯圖',
        xaxis_title='實部',
        yaxis_title='虛部',
        xaxis=dict(range=[-1, 1]),
        yaxis=dict(range=[-1, 1]),
        height=500,
        showlegend=True
    )
    
    return fig

def display_l_matching_design(Z_source, Z_load, frequency):
    """顯示L型匹配網絡設計"""
    omega = 2 * np.pi * frequency
    Z0 = 50  # 假設特性阻抗為50Ω
    
    st.write("L型匹配網絡設計:")
    
    # 簡單的L匹配計算
    if Z_load.real > Z0:
        # 需要降阻抗
        Q = np.sqrt(Z_load.real / Z0 - 1)
        Xs = Z0 * Q
        Xp = Z_load.real / Q
        
        st.write(f"- 串聯電抗: {Xs:.2f} Ω")
        st.write(f"- 並聯電抗: {Xp:.2f} Ω")
        
        if Xs > 0:
            L_series = Xs / omega
            st.write(f"- 串聯電感: {L_series*1e6:.2f} μH")
        else:
            C_series = -1 / (omega * Xs)
            st.write(f"- 串聯電容: {C_series*1e12:.2f} pF")
            
        if Xp > 0:
            L_parallel = Xp / omega
            st.write(f"- 並聯電感: {L_parallel*1e6:.2f} μH")
        else:
            C_parallel = -1 / (omega * Xp)
            st.write(f"- 並聯電容: {C_parallel*1e12:.2f} pF")
    
    else:
        st.info("使用相反的L型網絡結構")

def display_pi_matching_design(Z_source, Z_load, frequency):
    """顯示π型匹配網絡設計"""
    st.info("π型網絡適用於需要低通濾波特性的匹配")
    # 實際實現需要更複雜的計算
    pass

def display_t_matching_design(Z_source, Z_load, frequency):
    """顯示T型匹配網絡設計"""
    st.info("T型網絡適用於需要高通濾波特性的匹配")
    # 實際實現需要更複雜的計算
    pass

def display_transformer_matching(Z_source, Z_load):
    """顯示變壓器匹配設計"""
    turn_ratio = np.sqrt(Z_load.real / Z_source.real)
    st.write(f"變壓器匝數比: 1:{turn_ratio:.3f}")
    st.write("適用於純電阻性阻抗匹配")

def mechanical_vibration_simulation():
    """機械振動分析"""
    st.subheader("📊 機械振動模態分析")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 系統參數")
        
        # 多自由度系統
        num_masses = st.slider("質量塊數量", 1, 5, 2)
        
        masses = []
        springs = []
        dampers = []
        
        for i in range(num_masses):
            st.write(f"#### 質量塊 {i+1}")
            masses.append(st.slider(f"質量 m{i+1} (kg)", 0.1, 5.0, 1.0, 0.1, key=f"mass_{i}"))
            springs.append(st.slider(f"彈簧 k{i+1} (N/m)", 1.0, 100.0, 10.0, 1.0, key=f"spring_{i}"))
            if i < num_masses - 1:
                dampers.append(st.slider(f"阻尼 c{i+1} (Ns/m)", 0.0, 10.0, 0.5, 0.1, key=f"damper_{i}"))
    
    with col2:
        # 建立質量矩陣和剛度矩陣
        M = np.diag(masses)
        K = np.zeros((num_masses, num_masses))
        
        for i in range(num_masses):
            if i == 0:
                K[i,i] = springs[i]
                if num_masses > 1:
                    K[i,i+1] = -springs[i]
            elif i == num_masses - 1:
                K[i,i] = springs[i-1] + springs[i] if i > 0 else springs[i]
                K[i,i-1] = -springs[i-1]
            else:
                K[i,i] = springs[i-1] + springs[i]
                K[i,i-1] = -springs[i-1]
                K[i,i+1] = -springs[i]
        
        # 計算固有頻率和模態
        try:
            eigenvalues, eigenvectors = np.linalg.eig(np.linalg.solve(M, K))
            natural_frequencies = np.sqrt(eigenvalues)
            
            st.markdown("### 模態分析結果")
            for i, freq in enumerate(natural_frequencies):
                st.write(f"模態 {i+1}: {freq:.3f} rad/s")
                
            # 繪製模態形狀
            fig = go.Figure()
            for i in range(num_masses):
                mode_shapes = eigenvectors[:, i]
                fig.add_trace(go.Scatter(
                    x=list(range(1, num_masses + 1)),
                    y=mode_shapes,
                    mode='lines+markers',
                    name=f'模態 {i+1}'
                ))
            
            fig.update_layout(
                title='模態形狀',
                xaxis_title='質量塊編號',
                yaxis_title='模態幅度',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
        except np.linalg.LinAlgError:
            st.error("矩陣計算錯誤，請檢查參數")

def filter_design_simulation():
    """濾波器設計模擬"""
    st.subheader("📶 濾波器設計與分析")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 濾波器參數")
        
        filter_type = st.selectbox("濾波器類型", 
                                 ["低通", "高通", "帶通", "帶阻"])
        
        if filter_type in ["低通", "高通"]:
            cutoff_freq = st.slider("截止頻率 (Hz)", 10, 10000, 1000, 10)
            order = st.slider("濾波器階數", 1, 8, 2)
        else:
            low_freq = st.slider("低端截止頻率 (Hz)", 10, 5000, 500, 10)
            high_freq = st.slider("高端截止頻率 (Hz)", low_freq + 10, 10000, 2000, 10)
            order = st.slider("濾波器階數", 1, 8, 2)
        
        filter_design = st.selectbox("設計方法", 
                                   ["巴特沃斯", "切比雪夫", "貝塞爾"])
    
    with col2:
        # 設計濾波器
        if filter_type == "低通":
            b, a = signal.butter(order, cutoff_freq, 'low', analog=True)
            w, h = signal.freqs(b, a)
            title = f'{order}階{filter_design}低通濾波器'
        elif filter_type == "高通":
            b, a = signal.butter(order, cutoff_freq, 'high', analog=True)
            w, h = signal.freqs(b, a)
            title = f'{order}階{filter_design}高通濾波器'
        elif filter_type == "帶通":
            b, a = signal.butter(order, [low_freq, high_freq], 'band', analog=True)
            w, h = signal.freqs(b, a)
            title = f'{order}階{filter_design}帶通濾波器'
        else:  # 帶阻
            b, a = signal.butter(order, [low_freq, high_freq], 'bandstop', analog=True)
            w, h = signal.freqs(b, a)
            title = f'{order}階{filter_design}帶阻濾波器'
        
        frequencies = w / (2 * np.pi)
        
        # 繪製頻率響應
        fig = make_subplots(rows=2, cols=1, 
                          subplot_titles=('幅度響應', '相位響應'))
        
        # 幅度響應
        fig.add_trace(
            go.Scatter(x=frequencies, y=20 * np.log10(np.abs(h)), 
                      mode='lines', name='幅度'),
            row=1, col=1
        )
        
        # 相位響應
        phase = np.angle(h, deg=True)
        fig.add_trace(
            go.Scatter(x=frequencies, y=phase, 
                      mode='lines', name='相位', line=dict(color='red')),
            row=2, col=1
        )
        
        fig.update_xaxes(title_text="頻率 (Hz)", type="log", row=2, col=1)
        fig.update_xaxes(title_text="頻率 (Hz)", type="log", row=1, col=1)
        fig.update_yaxes(title_text="增益 (dB)", row=1, col=1)
        fig.update_yaxes(title_text="相位 (度)", row=2, col=1)
        
        fig.update_layout(height=600, title_text=title)
        st.plotly_chart(fig, use_container_width=True)
        
        # 顯示濾波器係數
        st.markdown("### 濾波器係數")
        col1, col2 = st.columns(2)
        with col1:
            st.write("分子係數 (b):")
            st.code(f"{b}")
        with col2:
            st.write("分母係數 (a):")
            st.code(f"{a}")

# 在主應用中使用這個補丁
def add_physics_to_main_app():
    """將物理模擬添加到主應用"""
    # 在物理模擬頁面中添加進階模擬選項
    if st.session_state.page == "物理模擬":
        st.sidebar.markdown("---")
        if st.sidebar.button("🔬 進階物理模擬"):
            st.session_state.show_advanced_physics = True
        
        if st.session_state.get('show_advanced_physics', False):
            advanced_physics_simulations()
            
            if st.button("← 返回基礎模擬"):
                st.session_state.show_advanced_physics = False
                st.experimental_rerun()
            
            # 阻止繼續執行基礎模擬代碼
            st.stop()

# 使用方法：
# 在主要的物理模擬頁面中調用 add_physics_to_main_app()
