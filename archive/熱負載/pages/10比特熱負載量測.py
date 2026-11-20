from matplotlib.pyplot import Circle, rcParams, savefig, show, subplots, tight_layout
from matplotlib.pyplot import rcParams, savefig, show, subplots, tight_layout
from streamlit import pyplot, sidebar, text_input, radio

#import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
#import numpy as np
from fontUtil2 import 配置中文
配置中文()
rcParams['font.size'] = 10

from streamlit import empty
MENU, 表單=[], ['實驗示意圖', '傳輸線比較', '脈衝序列與熱化曲線', '光子數與退相干']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  狀態=empty()
  狀態.code([])
if menu==len(表單): #
  pass
elif menu==MENU[3]: #
  fig, ax4= subplots(figsize=(10, 6))
  # ========== 圖4: 光子數與退相干關係 ==========
  #ax4 = axes[1, 1]
  ax4.set_xlim(0, 10)
  ax4.set_ylim(0, 10)
  ax4.set_aspect('equal')
  ax4.axis('off')
  ax4.set_title('圖4: 光子散粒雜訊退相干機制', fontsize=13, fontweight='bold', pad=10)

  # 繪製諧振器-量子位元系統
  # 諧振器
  resonator = FancyBboxPatch((1, 5), 3, 2.5, boxstyle="round,pad=0.1",
                              facecolor='#74b9ff', edgecolor='#0984e3', linewidth=2)
  ax4.add_patch(resonator)
  ax4.text(2.5, 6.25, 'Readout\nResonator\n(f_r = 7.458 GHz)', ha='center', va='center', 
           fontsize=9, fontweight='bold', color='#2d3436')

  # 量子位元
  qubit_box = FancyBboxPatch((6, 5), 3, 2.5, boxstyle="round,pad=0.1",
                              facecolor='#a29bfe', edgecolor='#6c5ce7', linewidth=2)
  ax4.add_patch(qubit_box)
  ax4.text(7.5, 6.25, 'Fluxonium\nQubit\n(f_q ~ 0.5 GHz)', ha='center', va='center',
           fontsize=9, fontweight='bold', color='#2d3436')

  # 耦合
  ax4.annotate('', xy=(6, 6.25), xytext=(4, 6.25),
              arrowprops=dict(arrowstyle='<->', color='#e17055', lw=2.5))
  ax4.text(5, 6.8, '色散耦合 χ/2π = -2.70 MHz', ha='center', fontsize=9, color='#e17055', fontweight='bold')

  # 光子數影響
  # 上方：光子數漲落
  photon_box = FancyBboxPatch((3.5, 8.5), 3, 1.2, boxstyle="round,pad=0.05",
                               facecolor='#fdcb6e', edgecolor='#f39c12', linewidth=1.5)
  ax4.add_patch(photon_box)
  ax4.text(5, 9.1, '平均光子數 n̄ 漲落', ha='center', va='center', fontsize=9, fontweight='bold')

  # 箭頭指向諧振器
  ax4.annotate('', xy=(2.5, 7.5), xytext=(4.5, 8.5),
              arrowprops=dict(arrowstyle='->', color='#f39c12', lw=2))

  # 關鍵公式
  formula_box = FancyBboxPatch((0.5, 1.5), 9, 3, boxstyle="round,pad=0.1",
                                facecolor='#f8f9fa', edgecolor='#2d3436', linewidth=1.5)
  ax4.add_patch(formula_box)

  ax4.text(5, 4.0, '關鍵公式', ha='center', fontsize=11, fontweight='bold')
  ax4.text(5, 3.3, r'$\Gamma_{\bar{n}} + 2\pi i \Delta f_{q,\bar{n}} = \frac{\kappa \chi}{\kappa^2 + \chi^2}(\chi + i\kappa)\bar{n}$', 
           ha='center', fontsize=11)
  ax4.text(5, 2.6, '小光子數極限 (n̄ ≲ 0.1):', ha='center', fontsize=9, style='italic')
  ax4.text(5, 2.0, r'$\Gamma_{\bar{n}} \approx \frac{\kappa \chi^2}{\kappa^2 + \chi^2} \bar{n}$  ,  $\Delta f_{q,\bar{n}} \approx \frac{\kappa^2 \chi}{\kappa^2 + \chi^2} \bar{n}$', 
           ha='center', fontsize=10)

  # 參數標註
  params = [
      'κ/2π = 4.10 MHz (諧振器帶寬)',
      'χ/2π = -2.70 MHz (色散頻移)',
      'n̄ < 3.5×10⁻³ (殘留光子數)',
      '→ 退相干率 Γ_n̄ ≈ 7-27 kHz'
  ]
  for i, p in enumerate(params):
      ax4.text(5, 1.2 - i*0.35, f'• {p}', ha='center', fontsize=8.5, 
               color='#2d3436' if i < 2 else '#e17055')

  tight_layout(rect=[0, 0, 1, 0.96])
  pyplot(fig)
elif menu==MENU[2]: #
  fig, ax3= subplots(figsize=(10, 6))
  # ========== 圖3: 脈衝序列與熱化曲線 ==========
  #ax3 = axes[1, 0]
  ax3.set_xlim(0, 10)
  ax3.set_ylim(0, 10)
  ax3.set_aspect('equal')
  ax3.axis('off')
  ax3.set_title('圖3: 衰減器熱化時間測量脈衝序列', fontsize=13, fontweight='bold', pad=10)

  # 時間軸
  ax3.annotate('', xy=(9, 1), xytext=(1, 1),
              arrowprops=dict(arrowstyle='->', color='black', lw=2))
  ax3.text(9.2, 1, '時間', fontsize=10, va='center')

  # DC加熱脈衝
  pulse_y = 3
  ax3.plot([1.5, 1.5, 2.5, 2.5, 1.5], [pulse_y, pulse_y+1.5, pulse_y+1.5, pulse_y, pulse_y], 
           'r-', linewidth=2.5)
  ax3.fill_between([1.5, 2.5], [pulse_y, pulse_y], [pulse_y+1.5, pulse_y+1.5], 
                    color='red', alpha=0.3)
  ax3.text(2.0, pulse_y+2.0, 'DC加熱脈衝\n(0.5V, 0.4mW)', ha='center', fontsize=9, color='red', fontweight='bold')
  ax3.text(2.0, pulse_y-0.5, 't_heat', ha='center', fontsize=9)

  # 等待時間
  cool_y = 3
  ax3.annotate('', xy=(5.5, cool_y+0.75), xytext=(2.5, cool_y+0.75),
              arrowprops=dict(arrowstyle='<->', color='blue', lw=2))
  ax3.text(4.0, cool_y+1.3, 't_cool (可變等待時間)', ha='center', fontsize=9, color='blue')

  # Ramsey序列
  ramsey_y = 6
  # π/2脈衝
  for x in [6.0, 8.0]:
      ax3.plot([x, x], [ramsey_y, ramsey_y+1.2], 'g-', linewidth=3)
      ax3.plot([x-0.15, x+0.15], [ramsey_y+1.2, ramsey_y+1.2], 'g-', linewidth=2)
  ax3.text(7.0, ramsey_y+1.8, 'Ramsey序列 (π/2 - 等待 - π/2)', ha='center', fontsize=9, color='green', fontweight='bold')

  # 讀出脈衝
  readout_y = 8.5
  ax3.plot([8.2, 8.2, 9.2, 9.2, 8.2], [readout_y, readout_y+1.0, readout_y+1.0, readout_y, readout_y],
           'purple', linewidth=2.5)
  ax3.fill_between([8.2, 9.2], [readout_y, readout_y], [readout_y+1.0, readout_y+1.0],
                    color='purple', alpha=0.3)
  ax3.text(8.7, readout_y+1.5, '讀出', ha='center', fontsize=9, color='purple', fontweight='bold')

  # 循環間隔
  ax3.plot([9.2, 9.2, 10.0, 10.0, 9.2], [pulse_y, pulse_y+0.5, pulse_y+0.5, pulse_y, pulse_y],
           'gray', linewidth=1.5, linestyle='--')
  ax3.text(9.6, pulse_y-0.5, '2ms\n間隔', ha='center', fontsize=8, color='gray')

  # 熱化公式
  formula_text = '熱化模型:\nT(t_cool) = T₀ + ΔT·exp(-t_cool/τ_cool)\n\nτ_cool = 0.28 ms (柔性帶狀線)\nτ_cool = 0.55 ms (同軸電纜)'
  props3 = dict(boxstyle='round', facecolor='#dff9fb', alpha=0.9, edgecolor='#22a6b3')
  ax3.text(0.5, 8.5, formula_text, fontsize=9, verticalalignment='top', bbox=props3, linespacing=1.5)
  pyplot(fig)

elif menu==MENU[1]: #
  fig, ax2= subplots(figsize=(10, 6))
  pass
  # ========== 圖2: 兩種傳輸線比較 ==========
  #ax2 = axes[0, 1]
  ax2.set_xlim(0, 10)
  ax2.set_ylim(0, 10)
  ax2.set_aspect('equal')
  ax2.axis('off')
  ax2.set_title('圖2: 兩種微波輸入線比較', fontsize=13, fontweight='bold', pad=10)

  # Setup A: 同軸電纜
  ax2.text(2.5, 9.2, 'Setup A: 傳統同軸電纜', fontsize=11, fontweight='bold', ha='center', color='#5f27cd')

  # 繪製同軸電纜截面示意
  coax_outer = Circle((2.5, 7.5), 1.2, facecolor='#c8d6e5', edgecolor='black', linewidth=2)
  ax2.add_patch(coax_outer)
  coax_inner = Circle((2.5, 7.5), 0.4, facecolor='#8395a7', edgecolor='black', linewidth=1.5)
  ax2.add_patch(coax_inner)
  ax2.text(2.5, 7.5, 'Cu', ha='center', va='center', fontsize=8, color='white', fontweight='bold')
  ax2.text(2.5, 6.0, 'SMA接頭衰減器\n+ 銅編織散熱', ha='center', fontsize=8, linespacing=1.4)

  # Setup B: 柔性帶狀線
  ax2.text(7.5, 9.2, 'Setup B: 柔性帶狀線 (Cri/oFlex®)', fontsize=11, fontweight='bold', ha='center', color='#10ac84')

  # 繪製帶狀線截面
  strip_rect = FancyBboxPatch((6.0, 6.8), 3.0, 1.4, boxstyle="round,pad=0.05",
                               facecolor='#feca57', edgecolor='black', linewidth=2)
  ax2.add_patch(strip_rect)
  # 中心導體
  ax2.plot([6.5, 8.5], [7.5, 7.5], 'k-', linewidth=6)
  ax2.plot([6.5, 8.5], [7.5, 7.5], '#ff9f43', linewidth=3)
  # 接地層
  ax2.plot([6.0, 9.0], [6.9, 6.9], '#576574', linewidth=3)
  ax2.plot([6.0, 9.0], [8.1, 8.1], '#576574', linewidth=3)
  ax2.text(7.5, 6.3, '整合式5dB單元衰減器\n+ 客製化熱夾具', ha='center', fontsize=8, linespacing=1.4)

  # 比較表格
  comparison_data = [
      ['項目', '同軸電纜', '柔性帶狀線'],
      ['熱化時間 τ_cool', '0.55 ms', '0.28 ms'],
      ['量子位元溫度 T_q', '30.4 ± 1.4 mK', '26.4 ± 2.0 mK'],
      ['殘留光子數 n̄', '~6.5×10⁻³', '< 3.5×10⁻³'],
      ['線纜密度', '基準', '提升10倍以上'],
      ['整合度', '離散式衰減器', '整合式單元'],
  ]

  table_y = 4.5
  for i, row in enumerate(comparison_data):
      for j, cell in enumerate(row):
          bg_color = '#dfe6e9' if i == 0 else ('#ffeaa7' if j == 2 and i > 0 else 'white')
          weight = 'bold' if i == 0 else 'normal'
          rect = FancyBboxPatch((0.5 + j*3.0, table_y - i*0.7), 2.8, 0.6,
                                 boxstyle="round,pad=0.02", facecolor=bg_color, 
                                 edgecolor='black', linewidth=0.5)
          ax2.add_patch(rect)
          ax2.text(0.5 + j*3.0 + 1.4, table_y - i*0.7 + 0.3, cell, 
                  ha='center', va='center', fontsize=8, fontweight=weight)

  # 結論
  ax2.text(5, 0.5, '結論: 柔性帶狀線熱化更快、溫度更低，且不影響量子位元性能', 
           ha='center', fontsize=10, fontweight='bold', color='#10ac84',
           bbox=dict(boxstyle='round', facecolor='#c8f7c5', alpha=0.9))
  pyplot(fig)
elif menu==MENU[0]: #實驗示意圖
  fig, ax1= subplots(figsize=(10, 6))
  # 設定中文字型

  #fig, axes = subplots(2, 2, figsize=(16, 14))
  fig.suptitle('Thermalization of Flexible Microwave Stripline - 示意圖解說', fontsize=16, fontweight='bold', y=0.98)

  # ========== 圖1: 實驗概念示意圖 ==========
  #ax1 = axes[0, 0]
  ax1.set_xlim(0, 10)
  ax1.set_ylim(0, 10)
  ax1.set_aspect('equal')
  ax1.axis('off')
  ax1.set_title('圖1: 實驗概念與熱化測量原理', fontsize=13, fontweight='bold', pad=10)

  # 繪製溫度層級
  stages = [
      (8.5, '300 K\n(室溫)', '#ff6b6b'),
      (7.0, '80 K', '#ff9f43'),
      (5.5, '4 K', '#feca57'),
      (4.0, '200 mK', '#48dbfb'),
      (2.5, '20 mK\n(稀釋機)', '#1dd1a1'),
  ]

  for y, label, color in stages:
      rect = FancyBboxPatch((1, y-0.4), 3, 0.8, boxstyle="round,pad=0.05", 
                             facecolor=color, edgecolor='black', linewidth=1.5, alpha=0.8)
      ax1.add_patch(rect)
      ax1.text(2.5, y, label, ha='center', va='center', fontsize=9, fontweight='bold')

  # 繪製傳輸線
  ax1.plot([4.5, 4.5], [2.5, 8.5], 'k-', linewidth=4)
  ax1.plot([4.7, 4.7], [2.5, 8.5], 'gray', linewidth=2, linestyle='--')

  # 衰減器標記
  att_positions = [7.0, 5.5, 4.0, 2.5]
  for pos in att_positions:
      att = FancyBboxPatch((4.3, pos-0.15), 0.6, 0.3, boxstyle="round,pad=0.02",
                            facecolor='#ff4757', edgecolor='darkred', linewidth=1.5)
      ax1.add_patch(att)
      ax1.text(5.2, pos, f'{20 if pos != 7.0 else 10} dB', fontsize=8, va='center')

  # 熱輻射箭頭
  for i, pos in enumerate(att_positions[:-1]):
      arrow = FancyArrowPatch((4.5, pos), (4.5, att_positions[i+1]+0.2),
                              arrowstyle='->', mutation_scale=15, 
                              color='red', linewidth=2, alpha=0.6)
      ax1.add_patch(arrow)

  # 量子位元裝置
  qubit = Circle((7.5, 2.5), 0.6, facecolor='#5f27cd', edgecolor='black', linewidth=2)
  ax1.add_patch(qubit)
  ax1.text(7.5, 2.5, 'Qubit\n+\nResonator', ha='center', va='center', fontsize=8, color='white', fontweight='bold')

  # 熱輻射到量子位元
  arrow = FancyArrowPatch((4.5, 2.8), (6.9, 2.5),
                          arrowstyle='->', mutation_scale=20,
                          color='red', linewidth=2.5, linestyle='--')
  ax1.add_patch(arrow)
  ax1.text(5.5, 3.2, '熱輻射\n(光子雜訊)', fontsize=9, color='red', fontweight='bold', ha='center')

  # 說明文字框
  textstr = '測量原理:\n• 衰減器吸收微波功率產生局部加熱\n• 熱輻射傳向諧振器-量子位元系統\n• 光子數漲落導致量子位元退相干\n• 通過退相干率推算殘留光子數'
  props = dict(boxstyle='round', facecolor='lightyellow', alpha=0.9, edgecolor='orange')
  ax1.text(0.5, 1.0, textstr, fontsize=9, verticalalignment='top', bbox=props, linespacing=1.6)
  pyplot(fig)


#savefig('/mnt/agents/output/paper_diagrams.png', dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
#show()
#print("圖片已儲存")
