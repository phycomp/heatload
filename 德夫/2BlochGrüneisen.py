from matplotlib.pyplot import figure, savefig, show, tight_layout
from numpy import linspace
from streamlit import pyplot
import numpy as np
from scipy import integrate
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.gridspec import GridSpec

# 設置繪圖風格
rcParams['font.size'] = 11
rcParams['axes.linewidth'] = 1.2

# ==================== 創建綜合分析圖 ====================

fig = figure(figsize=(14, 10))
gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.25)

# 顏色方案
color_main = '#2E86AB'      # 主線條：藍色
color_low = '#A23B72'       # 低溫擬合：紫紅色
color_high = '#F18F01'      # 高溫擬合：橙色
color_ref = '#C73E1D'       # 參考線：紅色
from 電阻率 import T_full, rho_full, rho_0, theta_D, C
# ---------- 圖1: 完整溫度範圍的電阻率曲線 ----------
ax1 = fig.add_subplot(gs[0, :])

ax1.semilogy(T_full, rho_full, '-', color=color_main, linewidth=2.5, label='Bloch-Grüneisen Model')
ax1.axhline(y=rho_0, color='gray', linestyle='--', alpha=0.7, label=f'Residual Resistivity $\\rho_0$ = {rho_0} μΩ·cm')
ax1.axvline(x=theta_D, color=color_ref, linestyle=':', alpha=0.8, label=f'Debye Temperature $\\Theta_D$ = {theta_D} K')

ax1.set_xlabel('Temperature T (K)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Resistivity ρ (μΩ·cm)', fontsize=12, fontweight='bold')
ax1.set_title('Bloch-Grüneisen Resistivity Model: Full Temperature Range', fontsize=14, fontweight='bold', pad=15)
ax1.legend(loc='lower right', fontsize=10, framealpha=0.9)
ax1.grid(True, alpha=0.3, which='both')
ax1.set_xlim([0, 1000])
ax1.set_ylim([0.015, 1])

# 添加溫度區域標註
ax1.axvspan(0, theta_D/3, alpha=0.1, color=color_low, label='Low-T region')
ax1.axvspan(theta_D/3, 3*theta_D, alpha=0.1, color='green')
ax1.axvspan(3*theta_D, 1000, alpha=0.1, color=color_high)
ax1.text(50, 0.6, 'Low-T\n$\\rho \\propto T^5$', fontsize=10, ha='center', color=color_low, fontweight='bold')
ax1.text(400, 0.6, 'Transition', fontsize=10, ha='center', color='green', fontweight='bold')
ax1.text(700, 0.6, 'High-T\n$\\rho \\propto T$', fontsize=10, ha='center', color=color_high, fontweight='bold')

# ---------- 圖2: 低溫區詳細分析 (T^5 行為) ----------
ax2 = fig.add_subplot(gs[1, 0])

# 低溫數據
T_low_plot = T_full[T_full <= 100]
rho_low_plot = rho_full[T_full <= 100]
delta_rho_low = rho_low_plot - rho_0

ax2.loglog(T_low_plot, delta_rho_low, 'o', color=color_main, markersize=4, alpha=0.7, label='BG Model')

# T^5 擬合線
T_fit_low = linspace(1, 50, 100)
# 在低溫極限，積分趨向常數 124.4 (純數)
const_integral_lowtemp = 124.4
rho_fit_low = C * (T_fit_low / theta_D)**5 * const_integral_lowtemp
ax2.loglog(T_fit_low, rho_fit_low, '--', color=color_low, linewidth=2, label='$\\propto T^5$ Law')

ax2.set_xlabel('Temperature T (K)', fontsize=11, fontweight='bold')
ax2.set_ylabel('$\\rho - \\rho_0$ (μΩ·cm)', fontsize=11, fontweight='bold')
ax2.set_title('Low-Temperature Region: $\\rho \\propto T^5$ Behavior', fontsize=12, fontweight='bold')
ax2.legend(loc='lower right', fontsize=9)
ax2.grid(True, alpha=0.3, which='both')

# 添加指數標註
ax2.text(10, 1e-5, 'Slope = 5', fontsize=10, color=color_low, fontweight='bold',
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# ---------- 圖3: 高溫區線性分析 ----------
ax3 = fig.add_subplot(gs[1, 1])

# 高溫數據 (減去殘餘電阻率)
T_high_mask = T_full >= 200
delta_rho_high = rho_full[T_high_mask] - rho_0

ax3.plot(T_full[T_high_mask], delta_rho_high, 'o', color=color_main, markersize=4, alpha=0.7, label='BG Model')

# 線性擬合 (高溫極限)
# 高溫時積分 ≈ (T/Θ_D) * (Θ_D/T)^6 / 6 = ... 實際上趨向 (Θ_D/T) 的線性行為
T_fit_high = linspace(300, 1000, 100)
# 高溫近似：ρ - ρ₀ ≈ (C/4) * (T/Θ_D) 當 T >> Θ_D
slope_approx = C / (4 * theta_D) * theta_D  # 簡化
rho_fit_high = slope_approx * (T_fit_high - theta_D/2)  # 近似線性

# 更好的方法：直接擬合高溫數據
from scipy.optimize import curve_fit
linear_func = lambda T, a, b: a * T + b
popt, _ = curve_fit(linear_func, T_full[T_full > 400], rho_full[T_full > 400])
ax3.plot(T_fit_high, popt[0] * T_fit_high + popt[1] - rho_0, '--', color=color_high, 
         linewidth=2, label=f'Linear Fit: slope = {popt[0]:.4f}')

ax3.set_xlabel('Temperature T (K)', fontsize=11, fontweight='bold')
ax3.set_ylabel('$\\rho - \\rho_0$ (μΩ·cm)', fontsize=11, fontweight='bold')
ax3.set_title('High-Temperature Region: $\\rho \\propto T$ Behavior', fontsize=12, fontweight='bold')
ax3.legend(loc='lower right', fontsize=9)
ax3.grid(True, alpha=0.3)

ax3.text(700, 0.15, 'Slope ≈ constant\n(Linear behavior)', fontsize=10, color=color_high, fontweight='bold', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)) # 添加線性標註
tight_layout()
pyplot(fig)
#savefig('/mnt/kimi/output/bloch_gruneisen_analysis.png', dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
#show()

#print("\n圖表已保存至: /mnt/kimi/output/bloch_gruneisen_analysis.png")
