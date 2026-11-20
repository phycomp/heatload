import streamlit as st
import math
import numpy as np
import matplotlib.pyplot as plt
# 物理模擬函數
def display_mechanics_simulation():
    st.subheader("力學模擬: 拋體運動")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        initial_velocity = st.slider("初始速度 (m/s)", 1, 100, 50)
        launch_angle = st.slider("發射角度 (度)", 0, 90, 45)
        gravity = st.slider("重力加速度 (m/s²)", 1.0, 20.0, 9.8)
        
        # 計算拋體運動
        angle_rad = math.radians(launch_angle)
        vx = initial_velocity * math.cos(angle_rad)
        vy = initial_velocity * math.sin(angle_rad)
        t_total = 2 * vy / gravity
        t = np.linspace(0, t_total, 100)
        x = vx * t
        y = vy * t - 0.5 * gravity * t**2
        
        st.write(f"最大高度: {(vy**2)/(2*gravity):.2f} m")
        st.write(f"射程: {vx * t_total:.2f} m")
        st.write(f"飛行時間: {t_total:.2f} s")
    
    with col2:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(x, y, 'b-', linewidth=2, label='軌跡')
        ax.set_xlabel('水平距離 (m)')
        ax.set_ylabel('高度 (m)')
        ax.set_title('拋體運動軌跡')
        ax.grid(True, alpha=0.3)
        ax.legend()
        st.pyplot(fig)

def display_electromagnetism_simulation():
    st.subheader("電磁學模擬: 電場分布")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        charge1 = st.slider("電荷1 (μC)", -10.0, 10.0, 5.0)
        charge2 = st.slider("電荷2 (μC)", -10.0, 10.0, -5.0)
        distance = st.slider("電荷間距 (m)", 0.5, 5.0, 2.0)
    
    with col2:
        # 創建網格
        x = np.linspace(-3, 3, 50)
        y = np.linspace(-3, 3, 50)
        X, Y = np.meshgrid(x, y)
        
        # 計算電勢
        k = 8.99e9
        r1 = np.sqrt((X + distance/2)**2 + Y**2)
        r2 = np.sqrt((X - distance/2)**2 + Y**2)
        V = k * charge1 * 1e-6 / r1 + k * charge2 * 1e-6 / r2
        
        fig, ax = plt.subplots(figsize=(10, 8))
        contour = ax.contourf(X, Y, V, levels=50, cmap='viridis')
        plt.colorbar(contour, ax=ax, label='電勢 (V)')
        
        # 標記電荷位置
        ax.plot(-distance/2, 0, 'ro', markersize=10, label=f'電荷1: {charge1}μC')
        ax.plot(distance/2, 0, 'bo', markersize=10, label=f'電荷2: {charge2}μC')
        
        ax.set_xlabel('x (m)')
        ax.set_ylabel('y (m)')
        ax.set_title('電場電勢分布')
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)

def display_optics_simulation():
    st.subheader("光學模擬: 光的折射")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        n1 = st.slider("介質1折射率", 1.0, 3.0, 1.0)
        n2 = st.slider("介質2折射率", 1.0, 3.0, 1.5)
        incident_angle = st.slider("入射角 (度)", 0, 90, 45)
        
        # 計算折射角
        incident_rad = math.radians(incident_angle)
        try:
            refracted_rad = math.asin((n1/n2) * math.sin(incident_rad))
            refracted_angle = math.degrees(refracted_rad)
        except:
            refracted_angle = 90
        
        st.write(f"折射角: {refracted_angle:.2f}°")
    
    with col2:
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # 繪製介質邊界
        ax.axhline(y=0, color='k', linestyle='-', linewidth=2)
        ax.text(-2.5, 0.5, f'n₁ = {n1}', fontsize=12)
        ax.text(-2.5, -0.5, f'n₂ = {n2}', fontsize=12)
        
        # 繪製入射光
        x_incident = [-2, 0]
        y_incident = [2 * math.tan(incident_rad), 0]
        ax.plot(x_incident, y_incident, 'r-', linewidth=2, label='入射光')
        
        # 繪製折射光
        if incident_angle <= 90:
            x_refracted = [0, 2]
            y_refracted = [0, -2 * math.tan(refracted_rad)]
            ax.plot(x_refracted, y_refracted, 'b-', linewidth=2, label='折射光')
        
        # 繪製法線
        ax.axvline(x=0, color='gray', linestyle='--', alpha=0.7, label='法線')
        
        ax.set_xlim(-3, 3)
        ax.set_ylim(-2, 2)
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_title('光的折射')
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)

def display_thermodynamics_simulation():
    st.subheader("熱力學模擬: 理想氣體")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        pressure = st.slider("壓力 (atm)", 0.5, 5.0, 1.0)
        volume = st.slider("體積 (L)", 1.0, 50.0, 22.4)
        temperature = st.slider("溫度 (K)", 100, 500, 273)
        
        # 計算氣體摩爾數
        R = 0.0821
        n = (pressure * volume) / (R * temperature)
        st.write(f"氣體摩爾數: {n:.2f} mol")
    
    with col2:
        volumes = np.linspace(1, 50, 100)
        pressures = n * R * temperature / volumes
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(volumes, pressures, 'b-', linewidth=2)
        ax.set_xlabel('體積 (L)')
        ax.set_ylabel('壓力 (atm)')
        ax.set_title('理想氣體 PV 圖')
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)

def display_quantum_simulation():
    st.subheader("量子物理模擬: 波函數")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        n = st.slider("量子數 n", 1, 5, 1)
        L = st.slider("勢阱寬度 (nm)", 0.1, 2.0, 1.0)
        
        st.write("一維無限深勢阱中的波函數")
    
    with col2:
        x = np.linspace(0, L, 1000)
        psi = np.sqrt(2/L) * np.sin(n * np.pi * x / L)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(x, psi, 'b-', linewidth=2, label=f'ψ_{n}(x)')
        ax.set_xlabel('位置 (nm)')
        ax.set_ylabel('波函數 ψ(x)')
        ax.set_title(f'一維無限深勢阱中的波函數 (n={n})')
        ax.grid(True, alpha=0.3)
        ax.legend()
        st.pyplot(fig)
