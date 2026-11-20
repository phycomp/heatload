from matplotlib.pyplot import savefig, show, subplots, tight_layout
from numpy import cos, pi, random, sin
from numpy.random import seed, uniform
from streamlit import pyplot, sidebar, radio, text_input, empty
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

#import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
#import numpy as np

MENU, 表單=[], ['物理機制', '晶格熵', '關鍵公式']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  狀態=empty()
  狀態.code([])
if menu==len(表單): #
  pass
elif menu==MENU[2]: #
  fig, ax = subplots(figsize=(14, 10))
  # ===== 底部：關鍵公式 =====
  ax.text(7, 0.8, '核心公式', fontsize=12, fontweight='bold', ha='center', color='#2c3e50')

  formulas = [
      'dS = dQ_rev / T   (熵的定義)',
      'dU = TdS - MdB    (熱力學第一定律)',
      'ΔT = -T(∂M/∂T)_B · ΔB / C_B   (溫度變化)'
  ]

  for ndx, 公式 in enumerate(formulas):
      ax.text(7, 0.4 - ndx*0.35, 公式, fontsize=10, ha='center', color='#34495e', bbox=dict(boxstyle='round,pad=0.2', facecolor='#ecf0f1', edgecolor='#bdc3c7'))

  #tight_layout()
  pyplot(fig)
elif menu==MENU[1]: #
  pass
  fig, ax = subplots(figsize=(24, 10))
  # ===== 右側：宏觀熱力學層面 =====
  ax.text(10.5, 8.3, '宏觀層面：熵與溫度', fontsize=13, fontweight='bold', ha='center', color='#2c3e50')
  ax.add_patch(FancyBboxPatch((8, 5.5), 5, 2.5, boxstyle="round,pad=0.1", facecolor='#fef9e7', edgecolor='#f39c12', linewidth=2)) # 熵的組成示意
  ax.text(10.5, 7.7, '總熵 S = 磁熵 S_m + 晶格熵 S_l', fontsize=10, ha='center', fontweight='bold', color='#d35400')

  ax.add_patch(patches.Rectangle((8.3, 6.5), 1.5, 0.4, facecolor='#9b59b6', alpha=0.7)) # 磁熵條
  ax.text(9.05, 6.7, 'S_m', fontsize=9, ha='center', color='white', fontweight='bold')
  ax.text(9.05, 6.2, '磁熵', fontsize=8, ha='center', color='#9b59b6')
  ax.add_patch(patches.Rectangle((10, 6.5), 2.5, 0.4, facecolor='#e67e22', alpha=0.7)) # 晶格熵條
  ax.text(11.25, 6.7, 'S_l', fontsize=9, ha='center', color='white', fontweight='bold')
  ax.text(11.25, 6.2, '晶格熵', fontsize=8, ha='center', color='#e67e22')
  ax.text(10.5, 5.8, '絕熱過程: S_total = 常數', fontsize=10, ha='center', color='#2c3e50', bbox=dict(boxstyle='round,pad=0.2', facecolor='#d5f5e3', edgecolor='#27ae60'))

  # ===== 下方：能量轉換流程 =====
  ax.text(7, 4.8, '能量轉換流程', fontsize=13, fontweight='bold', ha='center', color='#2c3e50')

  steps = [
      ('1. 磁化', '磁場做功\nW = ∫M·dB', '#fadbd8', 1.5),
      ('2. 退磁', '絕熱: dQ=0\n磁功→內能', '#d4efdf', 4.5),
      ('3. 吸熱', '從樣品吸熱\nQ = TΔS', '#d6eaf8', 7.5),
      ('4. 再磁化', '斷開熱接觸\n準備循環', '#fef9e7', 10.5)
  ] # 步驟框

  for name, desc, color, x in steps:
      ax.add_patch(FancyBboxPatch((x-1, 2.5), 2.2, 1.8, boxstyle="round,pad=0.1", facecolor=color, edgecolor='#2c3e50', linewidth=1.5))
      ax.text(x+0.1, 3.9, name, fontsize=10, ha='center', fontweight='bold', color='#2c3e50')
      ax.text(x+0.1, 3.2, desc, fontsize=8, ha='center', color='#2c3e50', linespacing=1.3)

  for x in [2.7, 5.7, 8.7]: # 連接箭頭
      ax.annotate('', xy=(x+0.8, 3.4), xytext=(x, 3.4), arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=1.5))

  # 循環回到起點的箭頭
  ax.annotate('', xy=(1.5, 2.3), xytext=(11.7, 2.3), arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=2, connectionstyle="arc3,rad=-0.3"))
  ax.text(6.5, 1.6, '循環重複', fontsize=9, ha='center', color='#e74c3c', fontweight='bold')
elif menu==MENU[0]: #物理機制
  fig, ax = subplots(figsize=(14, 10))
  ax.set_xlim(0, 14)
  ax.set_ylim(0, 10)
  ax.axis('off')

  # ===== 標題 =====
  ax.text(7, 9.5, 'ADR 物理機制示意圖', fontsize=18, fontweight='bold', ha='center', color='#2c3e50')
  ax.text(7, 9.0, 'Adiabatic Demagnetization Refrigeration - Physical Mechanism', 
          fontsize=12, ha='center', color='#7f8c8d', style='italic')

  # ===== 左側：微觀磁矩層面 =====
  ax.text(3.5, 8.3, '微觀層面：磁矩排列', fontsize=13, fontweight='bold', ha='center', color='#2c3e50')

  # 無磁場狀態（高熵）
  ax.add_patch(FancyBboxPatch((0.5, 5.5), 3, 2.5, boxstyle="round,pad=0.1", 
                               facecolor='#eaf2f8', edgecolor='#2980b9', linewidth=2))
  ax.text(2, 7.7, '無磁場 (B = 0)', fontsize=10, ha='center', fontweight='bold', color='#2980b9')
  ax.text(2, 7.3, '高磁熵', fontsize=9, ha='center', color='#2980b9')

  # 隨機箭頭
  seed(1)
  for _ in range(12):
      x, y = uniform(0.8, 3.2), uniform(5.8, 7.0)
      angle = uniform(0, 2*pi)
      dx, dy = 0.25 * cos(angle), 0.25 * sin(angle)
      ax.annotate('', xy=(x+dx, y+dy), xytext=(x-dx, y-dy),
                 arrowprops=dict(arrowstyle='->', color='#9b59b6', lw=1.5))

  # 有磁場狀態（低熵）
  ax.add_patch(FancyBboxPatch((4, 5.5), 3, 2.5, boxstyle="round,pad=0.1", 
                               facecolor='#fdedec', edgecolor='#e74c3c', linewidth=2))
  ax.text(5.5, 7.7, '強磁場 (B ↑)', fontsize=10, ha='center', fontweight='bold', color='#e74c3c')
  ax.text(5.5, 7.3, '低磁熵', fontsize=9, ha='center', color='#e74c3c')

  # 排列箭頭
  for i in range(4):
      for j in range(3):
          x = 4.3 + i * 0.6
          y = 5.8 + j * 0.5
          ax.annotate('', xy=(x, y+0.2), xytext=(x, y-0.2),
                     arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=1.5))

  # 連接箭頭
  ax.annotate('', xy=(4, 6.75), xytext=(3.5, 6.75),
             arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=2))
  ax.text(3.75, 6.4, '加磁場', fontsize=9, ha='center', color='#2c3e50')
  pyplot(fig)

#savefig('/mnt/agents/output/ADR_mechanism_diagram.png', dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
#show()
#print("圖2已保存")
