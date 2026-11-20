from matplotlib.pyplot import figure, savefig, show, subplot, tight_layout
from numpy import abs, linspace, log10, maximum, pi, sin, sqrt
#import matplotlib.pyplot as plt
#import numpy as np
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle
import matplotlib.patches as mpatches
from scipy.constants import c as 光速
from streamlit import pyplot

fig = figure(figsize=(16, 10))

# 1. 耦合微帶線結構與等效電路
ax1 = subplot(2, 3, 1)
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 10)
ax1.axis('off')
ax1.set_title('Coupled Microstrip Structure\n& Equivalent Circuit', fontsize=12, fontweight='bold', pad=15)

# 繪製耦合線結構 (側視圖)
ax1.add_patch(Rectangle((1, 3), 8, 4, facecolor='#FFE4B5', edgecolor='black', alpha=0.5))
ax1.add_patch(Rectangle((2, 6.5), 1.5, 0.3, facecolor='red', edgecolor='black'))
ax1.add_patch(Rectangle((5, 6.5), 1.5, 0.3, facecolor='blue', edgecolor='black'))
ax1.add_patch(Rectangle((1, 3), 8, 0.3, facecolor='#A0A0A0', edgecolor='black'))

ax1.text(2.75, 7.2, 'Line 1', fontsize=9, ha='center', color='red', fontweight='bold')
ax1.text(5.75, 7.2, 'Line 2', fontsize=9, ha='center', color='blue', fontweight='bold')
ax1.text(5, 3.5, 'Ground', fontsize=9, ha='center', fontweight='bold')

ax1.annotate('', xy=(5, 6.2), xytext=(3.5, 6.2),
            arrowprops=dict(arrowstyle='<->', color='green', lw=2))
ax1.text(4.25, 5.8, 's', fontsize=10, ha='center', color='green', fontweight='bold')

ax1.annotate('', xy=(8.5, 6.5), xytext=(8.5, 3.3),
            arrowprops=dict(arrowstyle='<->', color='purple', lw=2))
ax1.text(8.8, 5, 'h', fontsize=10, color='purple', fontweight='bold', rotation=90)

ax1.text(5, 2, 'Equivalent Circuit Model:', fontsize=10, ha='center', fontweight='bold')
ax1.text(5, 1.2, 'L  Lm  L', fontsize=11, ha='center', family='monospace')
ax1.text(5, 0.8, '|--nn--|--nn--|', fontsize=11, ha='center', family='monospace')
ax1.text(5, 0.4, 'C  Cm  C', fontsize=11, ha='center', family='monospace')

# 2. 耦合係數 vs 間距/高度比
ax2 = subplot(2, 3, 2)
s_h_ratio = linspace(0.1, 5, 100)
w_h = 2
k_approx = 0.5 * (w_h / (w_h + s_h_ratio)) ** 1.5
coupling_db = 20 * log10(k_approx)

ax2.plot(s_h_ratio, coupling_db, 'b-', linewidth=2.5, label='Coupling Coefficient')
ax2.axhline(y=-20, color='red', linestyle='--', alpha=0.7, label='-20 dB target')
ax2.axhline(y=-40, color='green', linestyle='--', alpha=0.7, label='-40 dB target')
ax2.axvspan(0.5, 2, alpha=0.2, color='yellow', label='Cri/oFlex range')
ax2.text(1.25, -15, 's=1mm, h=50um\ns/h=20', fontsize=9, ha='center', 
         bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

ax2.set_xlabel('Spacing/Height Ratio (s/h)', fontsize=11, fontweight='bold')
ax2.set_ylabel('Coupling Coefficient (dB)', fontsize=11, fontweight='bold')
ax2.set_title('Coupling vs Normalized Spacing', fontsize=12, fontweight='bold')
ax2.legend(loc='lower right', fontsize=9)
ax2.grid(True, alpha=0.3)
ax2.set_ylim(-50, -5)

# 3. 頻率對串擾的影響
ax3 = subplot(2, 3, 3)
freq = linspace(0.1, 20, 200)
lengths = [0.01, 0.05, 0.1, 0.2]
k = 0.01

for L in lengths:
    electrical_length = pi * freq * 1e9 * sqrt(2.5) * L / 光速
    fext = 20 * log10(abs(k * sin(electrical_length)))
    fext = maximum(fext, -60)
    ax3.plot(freq, fext, linewidth=2, label=f'L = {L*100:.0f} cm')

ax3.set_xlabel('Frequency (GHz)', fontsize=11, fontweight='bold')
ax3.set_ylabel('FEXT (dB)', fontsize=11, fontweight='bold')
ax3.set_title('Far-End Crosstalk vs Frequency', fontsize=12, fontweight='bold')
ax3.legend(loc='lower left', fontsize=9)
ax3.grid(True, alpha=0.3)
ax3.set_ylim(-60, -20)

# 4. 屏蔽技術比較
ax4 = subplot(2, 3, 4)
ax4.set_xlim(0, 10)
ax4.set_ylim(0, 10)
ax4.axis('off')
ax4.set_title('Shielding Techniques Comparison', fontsize=12, fontweight='bold', pad=15)

shielding_methods = [
    ("No Shielding", "-20 dB", "Baseline", 8.5, '#FFCCCC'),
    ("Ground Strip\n(single)", "-35 dB", "-15 dB", 7, '#FFE5CC'),
    ("Double Ground\nPlane", "-45 dB", "-25 dB", 5.5, '#FFFFCC'),
    ("Coaxial\nStructure", "-60 dB", "-40 dB", 4, '#E5FFCC'),
    ("Superconducting\nShield (Nb)", "-80 dB", "-60 dB", 2.5, '#CCFFCC'),
]

for method, performance, improvement, y, color in shielding_methods:
    ax4.text(1, y, method, fontsize=10, fontweight='bold', va='center')
    bar_length = (abs(float(performance.split()[0])) - 20) / 60 * 6
    ax4.add_patch(Rectangle((3, y-0.2), bar_length, 0.4, 
                           facecolor=color, edgecolor='black', linewidth=1))
    ax4.text(3 + bar_length/2, y, performance, fontsize=9, ha='center', va='center', fontweight='bold')
    ax4.text(8.5, y, improvement, fontsize=9, va='center', style='italic', color='green')

ax4.plot([0, 10], [1.5, 1.5], 'k-', linewidth=1)
ax4.text(1, 1, "Method", fontsize=9, fontweight='bold')
ax4.text(5, 1, "Crosstalk Level", fontsize=9, fontweight='bold')
ax4.text(8.5, 1, "Improvement", fontsize=9, fontweight='bold')

# 5. 3D 整合架構
ax5 = subplot(2, 3, 5)
ax5.set_xlim(0, 10)
ax5.set_ylim(0, 10)
ax5.axis('off')
ax5.set_title('3D High-Density Integration\nfor 1000+ Qubits', fontsize=12, fontweight='bold', pad=15)

layers = [
    ("Signal Layer 1", 8, '#FFE4E1', '256 ch'),
    ("Ground Shield", 6.8, '#E8F5E9', 'Nb film'),
    ("Signal Layer 2", 5.6, '#FFE4E1', '256 ch'),
    ("Ground Shield", 4.4, '#E8F5E9', 'Nb film'),
    ("Signal Layer 3", 3.2, '#FFE4E1', '256 ch'),
    ("Ground Shield", 2, '#E8F5E9', 'Nb film'),
    ("Signal Layer 4", 0.8, '#FFE4E1', '256 ch'),
]

for label, y, color, detail in layers:
    ax5.add_patch(Rectangle((2, y), 6, 0.8, facecolor=color, edgecolor='black', linewidth=2))
    ax5.add_patch(Rectangle((8, y-0.2), 0.5, 0.8, facecolor=color, edgecolor='black', linewidth=1, alpha=0.7))
    ax5.add_patch(Rectangle((2.2, y+0.8), 6, 0.2, facecolor=color, edgecolor='black', linewidth=1, alpha=0.8))
    ax5.text(5, y+0.4, label, fontsize=9, ha='center', va='center', fontweight='bold')
    ax5.text(8.7, y+0.2, detail, fontsize=8, ha='left', va='center', style='italic')

for y in [6.4, 5.2, 4, 2.8, 1.6]:
    ax5.plot([5, 5], [y, y+0.8], 'b--', linewidth=2, alpha=0.5)
    ax5.plot([5], [y+0.4], 'bo', markersize=6)

ax5.text(5, 0.2, 'TSV Interconnects', fontsize=10, ha='center', color='blue', fontweight='bold')
ax5.text(5, 9.5, 'Total: 1024 Channels', fontsize=12, ha='center', 
         bbox=dict(boxstyle='round', facecolor='#FFD700', alpha=0.8),
         fontweight='bold')

# 6. 優化策略總結
ax6 = subplot(2, 3, 6)
ax6.set_xlim(0, 10)
ax6.set_ylim(0, 10)
ax6.axis('off')
ax6.set_title('Optimization Strategy Summary\nfor Scale-Up to 1000+ Qubits', fontsize=12, fontweight='bold', pad=15)

strategies = [
    ("1. Material Innovation", 
     "• NbTi superconducting shield\n• Low-εr substrate (εr < 2.5)\n• Magnetic shielding layer",
     "-30 dB", "#3498DB"),
    ("2. Geometry Optimization", 
     "• Stripline vs microstrip\n• s/h > 3 for isolation\n• Tapered transitions",
     "-20 dB", "#E74C3C"),
    ("3. 3D Integration", 
     "• Multi-layer stacking\n• TSV vertical interconnect\n• Ground plane between layers",
     "-25 dB", "#2ECC71"),
    ("4. Signal Processing", 
     "• Differential signaling\n• Frequency domain multiplexing\n• Active cancellation",
     "-15 dB", "#F39C12"),
    ("5. Layout Strategy", 
     "• Checkerboard frequency\n• Orthogonal routing\n• Guard ring isolation",
     "-20 dB", "#9B59B6"),
]

y_pos = 9
for title, details, effect, color in strategies:
    title_box = FancyBboxPatch((0.3, y_pos-0.4), 9.4, 0.5, boxstyle="round,pad=0.02",
                               facecolor=color, edgecolor='black', linewidth=1.5, alpha=0.9)
    ax6.add_patch(title_box)
    ax6.text(1, y_pos-0.15, title, fontsize=10, fontweight='bold', color='white')
    ax6.text(8.5, y_pos-0.15, effect, fontsize=10, ha='center', 
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.9),
             fontweight='bold')
    
    y_pos -= 0.6
    ax6.text(0.8, y_pos-0.3, details, fontsize=8, va='top', family='monospace')
    y_pos -= 1.2

ax6.add_patch(FancyBboxPatch((0.5, 0.2), 9, 0.8, boxstyle="round,pad=0.1",
                             facecolor='#27AE60', edgecolor='black', linewidth=2))
ax6.text(5, 0.6, 'Total Improvement: -110 dB (cumulative)', fontsize=11, 
         ha='center', color='white', fontweight='bold')

pyplot(fig)
#tight_layout()
#savefig('/mnt/kimi/output/crosstalk_mitigation_strategies.png', dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
#show()

#print("串擾抑制策略詳細分析圖已生成")
