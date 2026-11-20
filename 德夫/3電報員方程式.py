from matplotlib.pyplot import cm, colorbar, savefig, show, subplots, tight_layout
from numpy import linspace, meshgrid
from streamlit import empty, pyplot
from 電報員Util import z, t, V_lossless, length, V_lossy, nx, nt
# 創建靜態視覺化 - 多時間點比較
fig, axes = subplots(2, 3, figsize=(15, 8))
fig.suptitle('Telegrapher\'s Equation Simulation - Pulse Propagation', fontsize=14, fontweight='bold')

time_indices = [50, 150, 250, 350, 450]  # 不同時間點
colors = cm.viridis(linspace(0, 1, len(time_indices)))

# 無損耗傳輸線
ax1 = axes[0, 0]
for idx, color in zip(time_indices, colors):
    ax1.plot(z, V_lossless[idx, :], color=color, label=f't={t[idx]*1e6:.2f}μs', linewidth=2)
ax1.set_title('Lossless Transmission Line (R=0, G=0)\nWave Propagation without Attenuation', fontsize=11)
ax1.set_xlabel('Position z (m)')
ax1.set_ylabel('Voltage V (V)')
ax1.legend(loc='upper right', fontsize=8)
ax1.grid(True, alpha=0.3)
ax1.set_xlim(0, length)

# 有損耗傳輸線
ax2 = axes[0, 1]
for idx, color in zip(time_indices, colors):
    ax2.plot(z, V_lossy[idx, :], color=color, label=f't={t[idx]*1e6:.2f}μs', linewidth=2)
ax2.set_title('Lossy Transmission Line (R=5Ω/m, G=1mS/m)\nWave Propagation with Attenuation', fontsize=11)
ax2.set_xlabel('Position z (m)')
ax2.set_ylabel('Voltage V (V)')
ax2.legend(loc='upper right', fontsize=8)
ax2.grid(True, alpha=0.3)
ax2.set_xlim(0, length)

# 衰減比較
ax3 = axes[0, 2]
ax3.plot(z, V_lossless[250, :], 'b-', linewidth=2.5, label='Lossless (t=0.5μs)')
ax3.plot(z, V_lossy[250, :], 'r--', linewidth=2.5, label='Lossy (t=0.5μs)')
ax3.set_title('Comparison at t=0.5μs\nAttenuation Effect', fontsize=11)
ax3.set_xlabel('Position z (m)')
ax3.set_ylabel('Voltage V (V)')
ax3.legend()
ax3.grid(True, alpha=0.3)
ax3.set_xlim(0, length)

# 時域波形 - 固定位置觀察
positions = [20, 50, 80]  # 三個觀察點
ax4 = axes[1, 0]
for pos in positions:
    idx = int(pos / length * nx)
    ax4.plot(t*1e6, V_lossless[:, idx], linewidth=2, label=f'z={pos}m')
ax4.set_title('Time Domain at Fixed Positions\n(Lossless Line)', fontsize=11)
ax4.set_xlabel('Time (μs)')
ax4.set_ylabel('Voltage V (V)')
ax4.legend()
ax4.grid(True, alpha=0.3)

ax5 = axes[1, 1]
for pos in positions:
    idx = int(pos / length * nx)
    ax5.plot(t*1e6, V_lossy[:, idx], linewidth=2, label=f'z={pos}m')
ax5.set_title('Time Domain at Fixed Positions\n(Lossy Line)', fontsize=11)
ax5.set_xlabel('Time (μs)')
ax5.set_ylabel('Voltage V (V)')
ax5.legend()
ax5.grid(True, alpha=0.3)

# 2D時空圖
ax6 = axes[1, 2]
T, Z = meshgrid(t*1e6, z)
im = ax6.contourf(T, Z, V_lossless.T, levels=50, cmap='RdBu_r', vmin=-1, vmax=1)
ax6.set_title('Space-Time Diagram\n(Lossless Line)', fontsize=11)
ax6.set_xlabel('Time (μs)')
ax6.set_ylabel('Position z (m)')
colorbar(im, ax=ax6, label='Voltage (V)')

tight_layout()
pyplot(fig)
#savefig('/mnt/kimi/output/telegrapher_simulation_static.png', dpi=150, bbox_inches='tight')
#show()

#print("靜態視覺化已生成")
