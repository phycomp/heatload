from numpy import exp, linspace, log, sqrt
from matplotlib.pyplot import figure, subplot
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle, FancyArrowPatch
import matplotlib.patches as mpatches
from matplotlib.collections import LineCollection

fig = figure(figsize=(18, 12))
def 優化(): # 6. Cri/oFlex 優化建議
  ax6 = subplot(2, 3, 6)
  ax6.set_xlim(0, 10)
  ax6.set_ylim(0, 10)
  ax6.axis('off')
  ax6.set_title('Cri/oFlex Optimization Roadmap\nfor 1000+ Qubit Systems', fontsize=12, fontweight='bold', pad=15)

  # 當前 vs 目標
  comparison = [
      ("Parameter", "Current", "Target", "Solution"),
      ("Channel Pitch", "1 mm", "0.3 mm", "Stripline + 3D stacking"),
      ("Crosstalk", "-40 dB", "-60 dB", "Nb ground shield + differential"),
      ("Density", "256 ch", "1024 ch", "Multi-layer flex + TSV"),
      ("Heat Load", "4 μW/ch", "1 μW/ch", "NbTi + optimized thermalization"),
      ("Bandwidth", "8 GHz", "20 GHz", "Lower εr substrate"),
  ]

  y_pos = 9
  for i, row in enumerate(comparison):
      if i == 0:
          # 標題
          for j, text in enumerate(row):
              x = 1.2 + j * 2.2
              ax6.text(x, y_pos, text, fontsize=10, fontweight='bold', ha='center')
          y_pos -= 0.8
          ax6.plot([0, 10], [y_pos+0.3, y_pos+0.3], 'k-', linewidth=2)
      else:
          # 數據行
          colors = ['black', '#3498DB', '#E74C3C', '#27AE60']
          for j, text in enumerate(row):
              x = 1.2 + j * 2.2
              color = colors[j] if j < len(colors) else 'black'
              weight = 'bold' if j in [1, 2] else 'normal'
              ax6.text(x, y_pos, text, fontsize=9, ha='center', color=color, fontweight=weight)
          y_pos -= 0.7

  # 3D 整合示意
  ax6.add_patch(FancyBboxPatch((0.5, 0.5), 9, 3, boxstyle="round,pad=0.1",
                               facecolor='#F8F9FA', edgecolor='#333', linewidth=2))
  ax6.text(5, 3, '3D Integration Concept', fontsize=11, ha='center', fontweight='bold')

  # 繪製 3D 堆疊示意
  layers = [
      ("Layer 1: Signal", 2.5, '#FFE4E1'),
      ("Layer 2: GND", 1.8, '#E8F5E9'),
      ("Layer 3: Signal", 1.1, '#FFE4E1'),
      ("Layer 4: GND", 0.4, '#E8F5E9'),
  ]
  for label, y, color in layers:
      ax6.add_patch(Rectangle((1, y), 8, 0.5, facecolor=color, edgecolor='black', linewidth=1))
      ax6.text(5, y+0.25, label, fontsize=9, ha='center', va='center')
  #return fig
def 串擾抑制(): # 5. 高密度串擾抑制技術
  ax5 = subplot(2, 3, 5)
  ax5.set_xlim(0, 10)
  ax5.set_ylim(0, 10)
  ax5.axis('off')
  ax5.set_title('Crosstalk Reduction Techniques\nfor High-Density Scaling', fontsize=12, fontweight='bold', pad=15)

  techniques = [
      ("1. Ground Shielding", "Add ground plane between lines", "-20 to -40 dB", "#3498DB"),
      ("2. Differential Signaling", "Twisted pair / CPS", "-30 to -50 dB", "#E74C3C"),
      ("3. Guard Rings", "Floating potential barriers", "-15 to -25 dB", "#2ECC71"),
      ("4. Staggered Routing", "Alternating signal/ground", "-10 to -20 dB", "#F39C12"),
      ("5. Frequency Separation", "Checkerboard frequency layout", "-20 to -30 dB", "#9B59B6"),
      ("6. Absorptive Material", "Lossy dielectric coating", "-10 to -15 dB", "#1ABC9C"),
  ]

  y_pos = 9
  for title, desc, effect, color in techniques:
      # 技術框
      box = FancyBboxPatch((0.3, y_pos-0.7), 9.4, 1.2, boxstyle="round,pad=0.05",
                           facecolor=color, edgecolor='black', linewidth=1.5, alpha=0.7)
      ax5.add_patch(box)
      
      ax5.text(1, y_pos-0.2, title, fontsize=10, fontweight='bold', color='white')
      ax5.text(4.5, y_pos-0.2, desc, fontsize=9, color='white')
      ax5.text(8.5, y_pos-0.2, effect, fontsize=9, ha='center', 
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.9),
               fontweight='bold')
      
      y_pos -= 1.4

def 近遠場(): # 4. 近場 vs 遠場串擾
  ax4 = subplot(2, 3, 4)
  ax4.set_xlim(0, 10)
  ax4.set_ylim(0, 10)
  ax4.axis('off')
  ax4.set_title('Near-Field vs Far-Field Crosstalk', fontsize=12, fontweight='bold', pad=15)

  # 距離軸
  distance = linspace(0.1, 10, 100)  # mm

  # 近場 (感應場) ~ 1/d³
  near_field = 1 / distance**3
  # 遠場 (輻射場) ~ 1/d
  far_field = 0.01 / distance
  # 過渡區
  transition = exp(-(distance - 2)**2 / 0.5)

  # 繪製示意圖
  ax4.plot([1, 9], [8, 8], 'k-', linewidth=3)
  ax4.plot([1, 1], [7.5, 8.5], 'k-', linewidth=2)
  ax4.plot([9, 9], [7.5, 8.5], 'k-', linewidth=2)

  # 標註區域
  ax4.text(2, 9, 'Near-Field\n(Inductive/Capacitive)', fontsize=10, ha='center', 
           bbox=dict(boxstyle='round', facecolor='#FFE4E1'))
  ax4.text(7, 9, 'Far-Field\n(Radiative)', fontsize=10, ha='center',
           bbox=dict(boxstyle='round', facecolor='#E1F5FE'))

  # 衰減曲線
  ax4_twin = ax4.figure.add_axes([0.35, 0.25, 0.2, 0.15])
  ax4_twin.semilogy(distance, near_field, 'r-', linewidth=2, label='Near-field ~1/d³')
  ax4_twin.semilogy(distance, far_field, 'b-', linewidth=2, label='Far-field ~1/d')
  ax4_twin.axvline(x=2, color='gray', linestyle='--', alpha=0.5)
  ax4_twin.set_xlabel('Distance (mm)', fontsize=8)
  ax4_twin.set_ylabel('Coupling (dB)', fontsize=8)
  ax4_twin.legend(fontsize=7)
  ax4_twin.grid(True, alpha=0.3)

  # 量子傳輸線設計要點
  points = [
      ("間距 s < λ/20", "近場主導", "控制 Cm, Lm"),
      ("s > λ/20", "遠場出現", "屏蔽與吸收"),
      ("Cri/oFlex s=1mm", "@6GHz λ=50mm", "s/λ = 0.02 << 0.05"),
  ]

  y_start = 6
  for i, (condition, field, solution) in enumerate(points):
      y = y_start - i * 1.5
      ax4.text(0.5, y, condition, fontsize=9, fontweight='bold')
      ax4.text(3.5, y, field, fontsize=9, color='blue')
      ax4.text(6, y, solution, fontsize=9, color='green', fontweight='bold')

def 串擾機制(): # 3. 串擾機制與分類
  ax3 = subplot(2, 3, 3)
  ax3.set_xlim(0, 10)
  ax3.set_ylim(0, 10)
  ax3.axis('off')
  ax3.set_title('Crosstalk Mechanisms in High-Density TL', fontsize=12, fontweight='bold', pad=15)

  # 繪製兩條耦合線
  # 攻擊線 (Aggressor)
  ax3.add_patch(Rectangle((1, 6), 8, 0.3, facecolor='red', edgecolor='black', alpha=0.7))
  ax3.text(5, 6.5, 'Aggressor (dV/dt)', fontsize=10, ha='center', color='white', fontweight='bold')

  # 受害線 (Victim)
  ax3.add_patch(Rectangle((1, 4), 8, 0.3, facecolor='blue', edgecolor='black', alpha=0.7))
  ax3.text(5, 3.5, 'Victim', fontsize=10, ha='center', color='white', fontweight='bold')

  # 耦合路徑
  # 電容耦合 (電場)
  for i in range(5):
      x = 2 + i * 1.5
      ax3.annotate('', xy=(x, 5.7), xytext=(x, 4.6),
                  arrowprops=dict(arrowstyle='<->', color='orange', lw=2, alpha=0.7))
  ax3.text(5, 5.15, 'Cm (Mutual Capacitance)', fontsize=9, ha='center', color='orange', fontweight='bold')

  # 電感耦合 (磁場)
  for i in range(3):
      x = 2.5 + i * 2
      circle = Circle((x, 5.15), 0.3, fill=False, edgecolor='purple', linewidth=2, linestyle='--')
      ax3.add_patch(circle)
  ax3.text(5, 2.5, 'Lm (Mutual Inductance)', fontsize=9, ha='center', color='purple', fontweight='bold')

  # 串擾類型說明
  crosstalk_types = [
      ("NEXT (Near-End)", "S31", "電容+電感同向", 1.5),
      ("FEXT (Far-End)", "S41", "電容-電感反向", 0.5),
  ]

  for name, param, mechanism, y_offset in crosstalk_types:
      ax3.text(1, y_offset, f"{name}: {param}", fontsize=10, fontweight='bold')
      ax3.text(4, y_offset, mechanism, fontsize=9, style='italic')

def 頻率色散(): # 2. 頻率限制與色散效應
  ax2 = subplot(2, 3, 2)
  freq = linspace(0.1, 100, 500)  # GHz

  # 微帶線色散：有效介電常數隨頻率增加
  epsilon_r = 3.4
  h = 50e-6  # 50 μm
  w = 100e-6  # 100 μm

  # Kirschning-Jansen 色散公式 (更精確)
  f_GHz = freq
  P1 = 0.27488 + (0.6315 + 0.525/(1+0.0157*f_GHz)**20) * (w/h) - 0.065683*exp(-8.7513*w/h)
  P2 = 0.33622 * (1 - exp(-0.03442*epsilon_r))
  P3 = 0.0363 * exp(-4.6*w/h) * (1 - exp(-(f_GHz/38.7)**4.97))
  P4 = 1 + 2.751 * (1 - exp(-(epsilon_r/15.916)**8))

  # 靜態有效介電常數 (Hammerstad-Jensen)
  if w/h <= 1:
      a = 1 + (1/49)*log((w/h)**4 + (w/(52*h))**2) / ((w/h)**4 + 0.432)
      b = 1 + (1/18.7)*log(1 + (w/(18.1*h))**3)
  else:
      a = 1
      b = 1

  epsilon_eff_static = (epsilon_r + 1)/2 + ((epsilon_r - 1)/2) * (1 + 10*h/w)**(-a*b)

  # 頻率相依有效介電常數
  epsilon_eff = epsilon_r - (epsilon_r - epsilon_eff_static) / (1 + P1*P2)

  # 特性阻抗變化
  Z0_static = 50  # 假設設計在 50Ω
  Z0_freq = Z0_static * sqrt(epsilon_eff_static / epsilon_eff)

  ax2.plot(freq, epsilon_eff, 'b-', linewidth=2.5, label='εeff(f) - Dispersive')
  ax2.axhline(y=epsilon_eff_static, color='b', linestyle='--', alpha=0.5, label='εeff(static)')
  ax2_twin = ax2.twinx()
  ax2_twin.plot(freq, Z0_freq, 'r-', linewidth=2.5, label='Z0(f)')
  ax2_twin.axhline(y=50, color='r', linestyle='--', alpha=0.5, label='Z0(target)')

  ax2.set_xlabel('Frequency (GHz)', fontsize=11, fontweight='bold')
  ax2.set_ylabel('Effective Dielectric Constant', fontsize=11, fontweight='bold', color='blue')
  ax2_twin.set_ylabel('Characteristic Impedance (Ω)', fontsize=11, fontweight='bold', color='red')
  ax2.set_title('Frequency Dispersion Effects', fontsize=12, fontweight='bold')
  ax2.legend(loc='upper left', fontsize=9)
  ax2_twin.legend(loc='upper right', fontsize=9)
  ax2.grid(True, alpha=0.3)
  ax2.set_xlim(0, 100)

  # 標註量子計算頻段
  ax2.axvspan(4, 8, alpha=0.2, color='green', label='Qubit band')
  ax2.text(6, 2.5, 'Qubit\nControl', fontsize=9, ha='center', color='green', fontweight='bold')
  #return fig

def HJ模型(): # 1. Hammerstad-Jensen 模型適用性分析
  ax1 = subplot(2, 3, 1)
  ax1.set_xlim(0, 10)
  ax1.set_ylim(0, 10)
  ax1.axis('off')
  ax1.set_title('Hammerstad-Jensen Model Applicability\nfor Cryogenic Quantum TL', fontsize=12, fontweight='bold', pad=15)

# 模型假設 vs 低溫量子傳輸線現實
  assumptions = [
      ("Model Assumption", "Cryogenic Reality", "Validity"),
      ("TEM/quasi-TEM mode", "True for w/h < 10", "✅ Valid"),
      ("εr constant", "εr↓ ~5-10% @4K", "⚠️ Correction needed"),
      ("Lossless dielectric", "tanδ ~0.002", "✅ Negligible effect on Z0"),
      ("Perfect conductor", "Rs finite", "⚠️ Use surface impedance"),
      ("Isotropic substrate", "Kapton anisotropic", "✅ Minor effect"),
      ("Room temp dimensions", "Thermal contraction", "⚠️ Scale by α·ΔT"),
  ]

  y_pos = 9
  for i, (assumption, reality, validity) in enumerate(assumptions):
      if i == 0:
          # 標題行
          ax1.text(1.5, y_pos, assumption, fontsize=10, fontweight='bold', ha='center')
          ax1.text(5, y_pos, reality, fontsize=10, fontweight='bold', ha='center')
          ax1.text(8.5, y_pos, validity, fontsize=10, fontweight='bold', ha='center')
          y_pos -= 0.8
          ax1.plot([0, 10], [y_pos+0.3, y_pos+0.3], 'k-', linewidth=2)
      else:
          color = '#E8F8F5' if '✅' in validity else '#FFF3E0'
          ax1.add_patch(FancyBboxPatch((0.2, y_pos-0.3), 9.6, 0.6, 
                                       boxstyle="round,pad=0.02",
                                       facecolor=color, edgecolor='gray', alpha=0.5))
          ax1.text(1.5, y_pos, assumption, fontsize=9, ha='center', va='center')
          ax1.text(5, y_pos, reality, fontsize=9, ha='center', va='center')
          ax1.text(8.5, y_pos, validity, fontsize=9, ha='center', va='center', 
                  fontweight='bold', color='green' if '✅' in validity else 'orange')
          y_pos -= 0.7

# 結論框
  ax1.add_patch(FancyBboxPatch((0.5, 0.5), 9, 1.5, boxstyle="round,pad=0.1",
                               facecolor='#D5F4E6', edgecolor='#27AE60', linewidth=2))
  ax1.text(5, 1.5, 'Conclusion: H-J model valid with corrections:', 
           fontsize=10, ha='center', fontweight='bold')
  ax1.text(5, 0.9, '• εr_eff(T) = εr(300K) × [1 - 0.08×(1 - T/300)]', 
           fontsize=9, ha='center')
  ax1.text(5, 0.5, '• Dimensions: L(T) = L₀ × [1 - α·(300-T)]', 
           fontsize=9, ha='center')
  #return fig
