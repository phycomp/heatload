from matplotlib.pyplot import figure, rcParams, savefig, show, suptitle
from streamlit import sidebar, radio, text_input, empty, pyplot
from matplotlib.pyplot import rcParams, savefig, show, subplots, tight_layout
from numpy import arange, array, exp, linspace, ones_like, pi, where
# 修正中文字體問題，重新生成圖表

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
#import numpy as np

# 設置中文字體
rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

fig = figure(figsize=(18, 14))

# 創建一個複雜的佈局
#gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

MENU, 表單=[], ['不匹配', 'CTE', '膠材質', '參數', '脆化風險', '膠層厚度', '熱循環壽命', '清單', '物理參數清單']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  狀態=empty()
  狀態.code([])
if menu==len(表單): #
  pass
elif menu==MENU[8]:
  from 軟硬板結合 import 軟硬板
  軟硬板()
elif menu==MENU[7]:
  fig, ax8= subplots(figsize=(10, 6))
  # 8. 關鍵製程檢查清單
  #ax8 = fig.add_subplot(gs[2, 2])
  ax8.set_xlim(0, 10)
  ax8.set_ylim(0, 10)
  ax8.axis('off')
  ax8.set_title('Critical Checklist', fontsize=12, fontweight='bold', pad=10)

  checklist = [
      'Surface Roughness Ra 0.3-0.8um',
      'Plasma Treatment 300W, 10min',
      'Silane Coupling Agent',
      'Glue Thickness 25+/-5um',
      'Vacuum Degas <5mmHg',
      'Initial Cure 25C, 24h',
      'Post Cure 80C, 4h',
      'Slow Cool <=1C/min',
      'C-scan No Delamination',
      'LN2 Cycle 5x Pass',
      'LHe Shear >15MPa',
      'Outgas TML <1%'
  ]

  y_pos = 9.5
  for item in checklist:
      color = '#2ca02c'
      ax8.text(0.5, y_pos, item, fontsize=9, va='top', color=color, family='monospace')
      y_pos -= 0.75

  suptitle('RO4350B + Kapton Hybrid PCB for 15mK Quantum Computing\nComplete Technical Summary', fontsize=16, fontweight='bold', y=0.98)
  pyplot(fig)

  #savefig('/mnt/agents/output/quantum_pcb_complete_summary.png', dpi=150, bbox_inches='tight')
  #show()

elif menu==MENU[6]: #不匹配
  fig, ax7= subplots(figsize=(10, 6))
  # 7. 熱循環壽命預測
  #ax7 = fig.add_subplot(gs[2, 1])
  cycles = arange(0, 101, 10)
  life_stycast = 100 * exp(-cycles/80)
  life_kb1631 = 100 * exp(-cycles/60)
  life_pi = 100 * exp(-cycles/50)

  ax7.plot(cycles, life_stycast, 'g-o', linewidth=2, markersize=6, label='Stycast 2850FT')
  ax7.plot(cycles, life_kb1631, 'b-s', linewidth=2, markersize=6, label='KB 1631')
  ax7.plot(cycles, life_pi, 'r-^', linewidth=2, markersize=6, label='PI Adhesive')
  ax7.axhline(y=80, color='gray', linestyle=':', linewidth=1, alpha=0.7)
  ax7.text(50, 82, 'Acceptable Limit', fontsize=9, color='gray')
  ax7.set_xlabel('Thermal Cycles (300K<->77K)', fontsize=10)
  ax7.set_ylabel('Remaining Integrity (%)', fontsize=10)
  ax7.set_title('Thermal Cycle Life Prediction', fontsize=12, fontweight='bold')
  ax7.legend(fontsize=8)
  ax7.grid(True, alpha=0.3)

elif menu==MENU[5]: #不匹配
  fig, ax6= subplots(figsize=(10, 6))
  # 6. 膠層厚度對應力的影響
  #ax6 = fig.add_subplot(gs[2, 0])
  thickness = array([10, 20, 25, 30, 50, 80, 100])
  stress = thickness * 0.8 + (thickness/30)**2 * 5
  ax6.plot(thickness, stress, 'b-o', linewidth=2, markersize=8)
  idx_25 = where(thickness == 25)[0][0]
  ax6.axvline(x=25, color='green', linestyle='--', linewidth=2, label='Optimal: 25um')
  ax6.axhline(y=stress[idx_25], color='green', linestyle='--', linewidth=2, alpha=0.5)
  ax6.fill_between(thickness, 0, stress, alpha=0.2, color='blue')
  ax6.set_xlabel('Glue Thickness (um)', fontsize=10)
  ax6.set_ylabel('Residual Stress (MPa)', fontsize=10)
  ax6.set_title('Stress vs Glue Thickness', fontsize=12, fontweight='bold')
  ax6.legend(fontsize=9)
  ax6.grid(True, alpha=0.3)

elif menu==MENU[4]: #不匹配
  fig, ax5= subplots(figsize=(10, 6))
  # 5. 脆化風險 vs 溫度
  #ax5 = fig.add_subplot(gs[1, 2])
  temps = [300, 200, 100, 77, 50, 20, 4.2, 0.015]
  risk_stycast = [10, 15, 25, 35, 45, 55, 65, 75]
  risk_kb1631 = [5, 8, 15, 20, 30, 40, 50, 60]
  risk_pi = [8, 12, 20, 28, 38, 48, 58, 68]

  ax5.plot(temps, risk_stycast, 'g-o', linewidth=2, markersize=6, label='Stycast 2850FT')
  ax5.plot(temps, risk_kb1631, 'b-s', linewidth=2, markersize=6, label='KB 1631')
  ax5.plot(temps, risk_pi, 'r-^', linewidth=2, markersize=6, label='PI Adhesive')
  ax5.axvline(x=0.015, color='purple', linestyle=':', linewidth=2)
  ax5.text(0.015, 80, '15mK', color='purple', fontsize=10, ha='left')
  ax5.set_xlabel('Temperature (K)', fontsize=10)
  ax5.set_ylabel('Embrittlement Risk Index', fontsize=10)
  ax5.set_title('Brittleness Risk vs Temperature', fontsize=12, fontweight='bold')
  ax5.set_xscale('log')
  ax5.legend(fontsize=8)
  ax5.grid(True, alpha=0.3)

elif menu==MENU[3]: #不匹配
  fig, ax4= subplots(figsize=(10, 6))
  # 4. 製程參數重要性
  #ax4 = fig.add_subplot(gs[1, 1])
  params = ['Surface\nTreatment', 'Glue\nThickness', 'Cure\nProfile', 'Post\nCure', 'Pre-\nconditioning']
  importance = [95, 90, 85, 80, 75]
  colors = ['#d62728', '#ff7f0e', '#2ca02c', '#1f77b4', '#9467bd']

  bars = ax4.barh(params, importance, color=colors, alpha=0.8, edgecolor='black')
  ax4.set_xlabel('Importance Score', fontsize=10)
  ax4.set_title('Process Parameter Priority', fontsize=12, fontweight='bold')
  ax4.set_xlim(0, 100)
  for bar, val in zip(bars, importance):
      ax4.text(val + 1, bar.get_y() + bar.get_height()/2, f'{val}%', va='center', fontsize=10, fontweight='bold')

elif menu==MENU[2]: #不匹配
  fig, ax3 = subplots(figsize=(10, 6), subplot_kw=dict(projection='polar'))

  # 3. 膠材比較雷達圖
  #ax3 = fig.add_subplot(gs[1, 0], projection='polar')
  categories = ['CTE\nMatch', 'Thermal\nCond.', 'Low T\nStrength', 'Outgassing', 'Adhesion', 'Cost']
  N = len(categories)
  angles = [n / float(N) * 2 * pi for n in range(N)]
  angles += angles[:1]

  stycast = [6, 9, 8, 9, 8, 7]
  kb1631 = [9, 9, 7, 9, 9, 5]
  pi_adhesive = [8, 3, 6, 8, 10, 6]

  stycast += stycast[:1]
  kb1631 += kb1631[:1]
  pi_adhesive += pi_adhesive[:1]

  ax3.plot(angles, stycast, 'o-', linewidth=2, label='Stycast 2850FT', color='green')
  ax3.fill(angles, stycast, alpha=0.15, color='green')
  ax3.plot(angles, kb1631, 's-', linewidth=2, label='KB 1631', color='blue')
  ax3.fill(angles, kb1631, alpha=0.15, color='blue')
  ax3.plot(angles, pi_adhesive, '^-', linewidth=2, label='PI Adhesive', color='red')
  ax3.fill(angles, pi_adhesive, alpha=0.15, color='red')

  ax3.set_xticks(angles[:-1])
  ax3.set_xticklabels(categories, fontsize=9)
  ax3.set_ylim(0, 10)
  ax3.set_title('Adhesive Comparison\n(Radar Chart)', fontsize=12, fontweight='bold', pad=20)
  ax3.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=8)

elif menu==MENU[1]: #
  pass
  fig, ax2= subplots(figsize=(10, 6))
  # 2. CTE 溫度依賴性
  #ax2 = fig.add_subplot(gs[0, 2])
  T = linspace(0.015, 300, 100)
  ro4350b_cte = 10 * (T/300)**0.5 + 2
  kapton_cte = 20 * (T/300)**0.3 + 3
  stycast_cte = 35 * ones_like(T)

  ax2.semilogy(T, ro4350b_cte, 'b-', linewidth=2, label='RO4350B')
  ax2.semilogy(T, kapton_cte, 'r-', linewidth=2, label='Kapton')
  ax2.semilogy(T, stycast_cte, 'g--', linewidth=2, label='Stycast 2850FT')
  ax2.axvline(x=0.015, color='purple', linestyle=':', linewidth=2, label='15mK')
  ax2.set_xlabel('Temperature (K)', fontsize=10)
  ax2.set_ylabel('CTE (ppm/degC)', fontsize=10)
  ax2.set_title('CTE vs Temperature', fontsize=12, fontweight='bold')
  ax2.legend(fontsize=8)
  ax2.grid(True, alpha=0.3)
elif menu==MENU[0]: #不匹配
  fig, ax1= subplots(figsize=(10, 6))
  #ax1 = fig.add_subplot(gs[0, :2]) # 1. 熱膨脹不匹配示意圖
  ax1.set_xlim(0, 10)
  ax1.set_ylim(0, 5)
  ax1.axis('off')
  ax1.set_title('RO4350B + Kapton Thermal Mismatch (300K -> 15mK)', fontsize=14, fontweight='bold', pad=20)

  # 繪製室溫狀態
  rect1_rt = mpatches.FancyBboxPatch((0.5, 3.5), 3, 1, boxstyle="round,pad=0.1", facecolor='lightblue', edgecolor='blue', linewidth=2)
  rect2_rt = mpatches.FancyBboxPatch((0.5, 2.2), 3, 1, boxstyle="round,pad=0.1", facecolor='lightyellow', edgecolor='orange', linewidth=2)
  ax1.add_patch(rect1_rt)
  ax1.add_patch(rect2_rt)
  ax1.text(2, 4, 'RO4350B (Rigid)\nRoom Temp 300K', ha='center', va='center', fontsize=11, fontweight='bold')
  ax1.text(2, 2.7, 'Kapton (Flex)\nRoom Temp 300K', ha='center', va='center', fontsize=11, fontweight='bold')
  ax1.annotate('', xy=(4.5, 3.8), xytext=(4.5, 2.5), arrowprops=dict(arrowstyle='<->', color='green', lw=2))
  ax1.text(4.8, 3.15, 'Glue\n25-50um', ha='left', va='center', fontsize=10, color='green')

  # 繪製低溫狀態
  rect1_cryo = mpatches.FancyBboxPatch((6, 3.7), 2.5, 0.8, boxstyle="round,pad=0.1", facecolor='lightblue', edgecolor='blue', linewidth=2)
  rect2_cryo = mpatches.FancyBboxPatch((6, 2.0), 2.7, 1.2, boxstyle="round,pad=0.1", facecolor='lightyellow', edgecolor='orange', linewidth=2)
  ax1.add_patch(rect1_cryo)
  ax1.add_patch(rect2_cryo)
  ax1.text(7.25, 4.1, 'RO4350B\nShrink 0.20%', ha='center', va='center', fontsize=10, fontweight='bold')
  ax1.text(7.35, 2.6, 'Kapton\nShrink 0.40%', ha='center', va='center', fontsize=10, fontweight='bold')
  ax1.annotate('', xy=(5.5, 3.5), xytext=(5.5, 2.5), arrowprops=dict(arrowstyle='->', color='red', lw=3))
  ax1.text(5.5, 3, 'Cool to 15mK', ha='center', va='center', fontsize=11, color='red', fontweight='bold', rotation=90)

  # 顯示不匹配
  ax1.annotate('', xy=(8.8, 4.1), xytext=(8.8, 3.2), arrowprops=dict(arrowstyle='<->', color='red', lw=2))
  ax1.text(9.1, 3.65, 'd = 0.20%\nStress!', ha='left', va='center', fontsize=10, color='red', fontweight='bold')
pyplot(fig)

#print("\nChart saved to: /mnt/agents/output/quantum_pcb_complete_summary.png")
