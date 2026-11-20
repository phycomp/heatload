from matplotlib.pyplot import rcParams
from numpy import exp, linspace, pi, sin, sqrt, zeros

#import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.integrate import odeint
import warnings
warnings.filterwarnings('ignore')

# 設定中文字型
rcParams['font.sans-serif'] = ['DejaVu Sans']
rcParams['axes.unicode_minus'] = False

def solve_telegrapher_equation(L, C, R, G, length, duration, nx, nt, source_type='pulse'): # 電報員方程式數值求解 - 有限差分法
    """
    求解電報員方程式
    ∂²V/∂z² = LC ∂²V/∂t² + (RC+LG) ∂V/∂t + RGV
    """
    dz = length / nx
    dt = duration / nt
    
    # Courant條件檢查
    v = 1/sqrt(L*C)
    courant = v * dt / dz
    if courant > 1:
        print(f"警告: Courant數 {courant:.2f} > 1, 數值不穩定")
    
    # 初始化電壓和電流陣列
    V = zeros((nt, nx))
    I = zeros((nt, nx))
    
    # 空間網格
    z = linspace(0, length, nx)
    t = linspace(0, duration, nt)
    
    # 初始條件：高斯脈衝或正弦波
    if source_type == 'pulse':
        V[0, :] = exp(-((z - length*0.1)**2) / (2*(length*0.05)**2))
        V[1, :] = V[0, :]  # 初始速度為零
    elif source_type == 'sine':
        V[0, :] = sin(2*pi*z/length*5) * exp(-z/(length*0.3))
        V[1, :] = V[0, :]
    
    # 時間迭代 (Leap-frog方法)
    for n in range(1, nt-1):
        # 內部點更新
        for i in range(1, nx-1):
            # 電報員方程的離散形式
            d2V_dz2 = (V[n, i+1] - 2*V[n, i] + V[n, i-1]) / dz**2
            dV_dt = (V[n, i] - V[n-1, i]) / dt
            
            # 完整電報員方程
            if R == 0 and G == 0:
                # 無損耗情況：簡單波動方程
                V[n+1, i] = 2*V[n, i] - V[n-1, i] + (v**2 * dt**2 / dz**2) * (V[n, i+1] - 2*V[n, i] + V[n, i-1])
            else:
                # 有損耗情況
                damping = (R*C + L*G) * dt / (2*L*C)
                loss = R*G * dt**2 / (L*C)
                
                V[n+1, i] = (2*V[n, i] - V[n-1, i] + 
                            (v**2 * dt**2 / dz**2) * (V[n, i+1] - 2*V[n, i] + V[n, i-1]) -
                            damping * (V[n, i] - V[n-1, i]) -
                            loss * V[n, i])
        
        # 邊界條件：吸收邊界 (簡單處理)
        V[n+1, 0] = V[n+1, 1]  # 左邊界
        V[n+1, -1] = V[n+1, -2]  # 右邊界
        
        # 持續注入信號
        if n < nt//4:
            if source_type == 'pulse':
                V[n+1, 0] = exp(-((t[n+1] - duration*0.05)**2) / (2*(duration*0.02)**2))
            elif source_type == 'sine':
                V[n+1, 0] = sin(2*pi*3*t[n+1]/duration) * exp(-t[n+1]/(duration*0.2))
    
    return z, t, V, I

# 測試模擬
print("測試電報員方程式求解...")

# 參數設定
L, C = 2.5e-7, 1e-10  # 電感和電容 (典型同軸電纜值)
R_lossless, G_lossless = 0, 0  # 無損耗
R_lossy, G_lossy = 5, 1e-3  # 有損耗

length = 100  # 傳輸線長度 (m)
duration = 1e-6  # 模擬時間 (s)
nx, nt = 200, 500

# 求解無損耗情況
z, t, V_lossless, _ = solve_telegrapher_equation(
    L, C, R_lossless, G_lossless, length, duration, nx, nt, 'pulse'
)

# 求解有損耗情況
_, _, V_lossy, _ = solve_telegrapher_equation(
    L, C, R_lossy, G_lossy, length, duration, nx, nt, 'pulse'
)

print(f"波速 v = {1/sqrt(L*C):.2e} m/s")
print(f"特性阻抗 Z0 = {sqrt(L/C):.2f} Ω")
print(f"模擬完成，時間步數: {nt}, 空間格點: {nx}")
