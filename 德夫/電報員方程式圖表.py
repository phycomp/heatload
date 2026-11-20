
# 重新定義求解函數並生成參數研究圖表
def solve_telegrapher_fast(L, C, R, G, length, duration, nx=200, nt=500, sig_type="高斯脈衝", freq=10, amp=1):
    dz = length / nx
    dt = duration / nt
    v_wave = 1/np.sqrt(L*C) if L*C > 0 else 0
    
    z = np.linspace(0, length, nx)
    t = np.linspace(0, duration, nt)
    V = np.zeros((nt, nx))
    
    # 初始條件
    if sig_type == "高斯脈衝":
        sigma = length * 0.05
        V[0, :] = amp * np.exp(-((z - length*0.1)**2)/(2*sigma**2))
    elif sig_type == "正弦波":
        V[0, :] = amp * np.sin(2*np.pi*freq*1e6*z/v_wave) * np.exp(-z/(length*0.3))
    else:  # 方波
        V[0, :] = amp * np.where((z > length*0.05) & (z < length*0.15), 1, 0)
    
    V[1, :] = V[0, :]
    
    courant = v_wave * dt / dz
    if courant > 1:
        return z, t, V, courant, v_wave
    
    r_vec = (v_wave * dt / dz)**2
    damping = (R*C + L*G) * dt / (2*L*C) if L*C > 0 else 0
    loss = R*G * dt**2 / (L*C) if L*C > 0 else 0
    
    for n in range(1, nt-1):
        laplacian = V[n, 2:] - 2*V[n, 1:-1] + V[n, :-2]
        
        if R == 0 and G == 0:
            V[n+1, 1:-1] = 2*V[n, 1:-1] - V[n-1, 1:-1] + r_vec * laplacian
        else:
            V[n+1, 1:-1] = ((2*V[n, 1:-1] - V[n-1, 1:-1] + r_vec*laplacian - 
                           damping*(V[n, 1:-1] - V[n-1, 1:-1]) - loss*V[n, 1:-1]) / 
                          (1 + damping))
        
        # 邊界條件
        if n < nt//4:
            if sig_type == "高斯脈衝":
                V[n+1, 0] = amp * np.exp(-((t[n+1]-duration*0.05)**2)/(2*(duration*0.02)**2))
            elif sig_type == "正弦波":
                V[n+1, 0] = amp * np.sin(2*np.pi*freq*1e6*t[n+1]) * np.exp(-t[n+1]/(duration*0.3))
            else:
                V[n+1, 0] = amp if np.sin(2*np.pi*freq*1e6*t[n+1]) > 0 else -amp
        
        V[n+1, -1] = V[n+1, -2]
    
    return z, t, V, courant, v_wave

# 創建綜合比較圖表
fig, axes = plt.subplots(2, 3, figsize=(16, 10))
fig.suptitle('Telegrapher\'s Equation: Comprehensive Parameter Study', fontsize=16, fontweight='bold')

# 基礎參數
L_base, C_base = 2.5e-7, 1e-10
length, duration = 100, 1e-6
nx, nt = 200, 500

# 1. 無損耗 vs 有損耗比較
ax1 = axes[0, 0]
z, t, V_lossless, _, _ = solve_telegrapher_fast(L_base, C_base, 0, 0, length, duration, nx, nt, "高斯脈衝", 10, 1)
_, _, V_lossy, _, _ = solve_telegrapher_fast(L_base, C_base, 5, 1e-3, length, duration, nx, nt, "高斯脈衝", 10, 1)

time_snap = 250
ax1.plot(z, V_lossless[time_snap, :], 'b-', linewidth=2.5, label='Lossless (R=0, G=0)')
ax1.plot(z, V_lossy[time_snap, :], 'r--', linewidth=2.5, label='Lossy (R=5Ω/m, G=1mS/m)')
ax1.set_xlabel('Position z (m)')
ax1.set_ylabel('Voltage V (V)')
ax1.set_title('Lossless vs Lossy Transmission Line')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 2. 不同電阻值的影響
ax2 = axes[0, 1]
R_values = [0, 1, 5, 10]
colors = plt.cm.Reds(np.linspace(0.3, 1, len(R_values)))
for R_val, color in zip(R_values, colors):
    _, _, V_R, _, _ = solve_telegrapher_fast(L_base, C_base, R_val, 0, length, duration, nx, nt, "高斯脈衝", 10, 1)
    ax2.plot(z, V_R[time_snap, :], color=color, linewidth=2, label=f'R={R_val}Ω/m')
ax2.set_xlabel('Position z (m)')
ax2.set_ylabel('Voltage V (V)')
ax2.set_title('Effect of Series Resistance R')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 3. 不同電導值的影響
ax3 = axes[0, 2]
G_values = [0, 0.001, 0.01, 0.1]
colors = plt.cm.Blues(np.linspace(0.3, 1, len(G_values)))
for G_val, color in zip(G_values, colors):
    _, _, V_G, _, _ = solve_telegrapher_fast(L_base, C_base, 0, G_val, length, duration, nx, nt, "高斯脈衝", 10, 1)
    ax3.plot(z, V_G[time_snap, :], color=color, linewidth=2, label=f'G={G_val*1000:.1f}mS/m')
ax3.set_xlabel('Position z (m)')
ax3.set_ylabel('Voltage V (V)')
ax3.set_title('Effect of Shunt Conductance G')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 4. 時域衰減比較
ax4 = axes[1, 0]
times_us = t * 1e6
for R_val in [0, 2, 5, 10]:
    _, _, V_t, _, _ = solve_telegrapher_fast(L_base, C_base, R_val, 0, length, duration, nx, nt, "高斯脈衝", 10, 1)
    peaks = [np.max(V_t[i, :]) for i in range(len(t))]
    ax4.semilogy(times_us, peaks, linewidth=2, label=f'R={R_val}Ω/m')
ax4.set_xlabel('Time (μs)')
ax4.set_ylabel('Peak Voltage (V, log scale)')
ax4.set_title('Signal Attenuation over Time')
ax4.legend()
ax4.grid(True, alpha=0.3, which='both')

# 5. 不同信號類型
ax5 = axes[1, 1]
signals = ["高斯脈衝", "正弦波", "方波"]
colors = ['#2ecc71', '#e74c3c', '#9b59b6']
for sig, color in zip(signals, colors):
    _, _, V_sig, _, _ = solve_telegrapher_fast(L_base, C_base, 0, 0, length, duration, nx, nt, sig, 10, 1)
    ax5.plot(z, V_sig[time_snap, :], color=color, linewidth=2.5, label=sig)
ax5.set_xlabel('Position z (m)')
ax5.set_ylabel('Voltage V (V)')
ax5.set_title('Different Signal Types (Lossless)')
ax5.legend()
ax5.grid(True, alpha=0.3)

# 6. 二維時空演化（無損耗）
ax6 = axes[1, 2]
T_mesh, Z_mesh = np.meshgrid(t * 1e6, z)
im = ax6.contourf(T_mesh, Z_mesh, V_lossless.T, levels=30, cmap='RdBu_r', vmin=-1, vmax=1)
ax6.set_xlabel('Time (μs)')
ax6.set_ylabel('Position z (m)')
ax6.set_title('Space-Time Evolution (Lossless)')
plt.colorbar(im, ax=ax6, label='Voltage (V)')

plt.tight_layout()
plt.savefig('/mnt/kimi/output/telegrapher_parameter_study.png', dpi=150, bbox_inches='tight')
plt.show()

print("✅ 參數研究圖表已生成")
print("📁 保存位置: /mnt/kimi/output/telegrapher_parameter_study.png")
