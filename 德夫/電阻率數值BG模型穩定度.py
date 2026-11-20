from numpy import atleast_1d, concatenate, exp, linspace, log10, logspace, sort, unique, zeros_like

import numpy as np
from scipy import integrate
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 改進數值穩定性

def bloch_gruneisen_integrand_stable(x):
    """數值穩定的被積函數版本"""
    if x < 1e-10:
        return 0
    # 對於大 x，使用漸近展開避免溢出
    if x > 100:
        # 當 x >> 1，e^x >> 1，所以 e^x/(e^x-1)^2 ≈ e^(-x)
        return x**5 * np.exp(-x)
    
    ex = np.exp(x)
    # 使用對數空間計算避免溢出
    if ex > 1e300:
        return x**5 * np.exp(-x)  # 近似
    
    return x**5 * ex / (ex - 1)**2

def bloch_gruneisen_integral_stable(y_max):
    """數值穩定的積分計算"""
    if y_max < 1e-10:
        return 0
    
    # 分段積分以提高精度
    if y_max <= 100:
        result, err = integrate.quad(bloch_gruneisen_integrand_stable, 0, y_max, 
                                      limit=200, epsabs=1e-12, epsrel=1e-12)
    else:
        # 對於大 y_max，分段處理
        result1, _ = integrate.quad(bloch_gruneisen_integrand_stable, 0, 100, limit=200)
        result2, _ = integrate.quad(bloch_gruneisen_integrand_stable, 100, y_max, limit=200)
        result = result1 + result2
    
    return result

def resistivity_bg_stable(T, rho_0, C, theta_D):
    """計算 Bloch-Gruneisen 電阻率 - 向量化版本"""
    T = np.atleast_1d(T)
    rho = np.zeros_like(T, dtype=float)
    
    for i, t in enumerate(T):
        if t < 1e-6:
            rho[i] = rho_0
        else:
            y_max = theta_D / t
            integral = bloch_gruneisen_integral_stable(y_max)
            rho_bg = C * (t / theta_D)**5 * integral
            rho[i] = rho_0 + rho_bg
    
    return rho if len(rho) > 1 else rho[0]

# ==================== 重新計算 ====================

# 物理參數（以銅為例）
rho_0 = 0.02       # 殘餘電阻率 μΩ·cm
C = 0.5            # 材料常數 μΩ·cm  
theta_D = 315      # Debye 溫度 K

# 生成溫度點（對數間隔以更好展示低溫行為）
T_low = np.logspace(-1, np.log10(50), 300)      # 0.1 - 50 K
T_mid = np.linspace(50, 315, 200)                # 50 - 315 K
T_high = np.linspace(315, 1000, 200)           # 315 - 1000 K
T_full = np.sort(np.unique(np.concatenate([T_low, T_mid, T_high])))

# 計算
rho_full = resistivity_bg_stable(T_full, rho_0, C, theta_D)

# 驗證極限行為
print("=== Bloch-Gruneisen 模型驗證 ===")
print(f"參數: ρ₀ = {rho_0} μΩ·cm, C = {C} μΩ·cm, Θ_D = {theta_D} K\n")

# 低溫極限 (T << Θ_D): ρ ∝ T^5
T_check_low = 20  # K
rho_at_20K = resistivity_bg_stable(T_check_low, rho_0, C, theta_D)
print(f"低溫區 (T = {T_check_low} K << Θ_D):")
print(f"  電阻率 ρ = {rho_at_20K:.6f} μΩ·cm")
print(f"  偏離殘餘值 Δρ = {rho_at_20K - rho_0:.6f} μΩ·cm")

# 高溫極限 (T >> Θ_D): ρ ∝ T
T_check_high = 800  # K
rho_at_800K = resistivity_bg_stable(T_check_high, rho_0, C, theta_D)
print(f"\n高溫區 (T = {T_check_high} K >> Θ_D):")
print(f"  電阻率 ρ = {rho_at_800K:.4f} μΩ·cm")

# 檢查線性行為
T_ref = 400
rho_ref = resistivity_bg_stable(T_ref, rho_0, C, theta_D)
ratio = (rho_at_800K - rho_0) / (rho_ref - rho_0)
print(f"  相對於 {T_ref}K 的比值: {ratio:.3f} (理想線性應為 {800/T_ref:.3f})")

# 計算 Debye 溫度處的值
rho_at_theta = resistivity_bg_stable(theta_D, rho_0, C, theta_D)
print(f"\n在 Debye 溫度處 (T = Θ_D = {theta_D} K):")
print(f"  電阻率 ρ = {rho_at_theta:.4f} μΩ·cm")
