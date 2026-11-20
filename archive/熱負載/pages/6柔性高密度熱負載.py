from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.pyplot import rcParams, subplot, subplots, tight_layout
from streamlit import pyplot, sidebar, radio, text_input
from numpy import arange, argmax, ceil, pi
from matplotlib.pyplot import rcParams, savefig, show, subplots, tight_layout
from streamlit import pyplot, session_state

#import matplotlib.pyplot as plt
#import matplotlib.patches as mpatches
#import numpy as np

# 設定中文字型
rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

# ============================================================
# 參數設定 - 基於論文與 Delft Circuits 官方數據
# ============================================================
from streamlit import set_page_config
set_page_config(page_title='柔性高密度熱負載', layout='wide', initial_sidebar_state='expanded')
from streamlit import empty

MENU, 表單=[], ['熱負載', '計算瓶頸', '主動熱負載', '空間佔用比較', '綜合比較表', '最優解']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  # --- Bluefors XLD1000-SL 冰箱參數 ---
  stages = ['50K', '4K', 'Still', 'CP', 'MXC']
  stage_temps_high = [300, 50, 4, 0.7, 0.2]   # K (高溫端)
  stage_temps_low = [50, 4, 0.7, 0.2, 0.02]   # K (低溫端)
  cooling_power = [40, 2.5, 0.3, 0.04, 0.008]  # W (冷卻功率)
  cable_lengths = [0.14, 0.35, 0.13, 0.05, 0.01]  # m (每段電纜長度)

  # --- SC-086/50-SCN-CN 同軸電纜參數 (論文數據) --- 每條電纜的靜態熱負載 (mW)
  sc086_static_per_cable = [0.98, 12.7, 1.14, 2.59, 0.35]  # mW per cable per stage

  # --- Cri/oFlex 3 參數 (Delft Circuits 官方數據) ---
  # 根據 datasheet: <125 μW @ ΔT: 4-40K, L=0.4m
  # 根據 EE Times: <4 μW per channel @ 3K-0.7K
  # 根據 2026 brochure: 10x lower thermal load than Ag platform (NbTi版本)
  # 根據技術頁面: superconducting NbTi flex = 10x lower thermal load

  # Cri/oFlex 3 Ag (銀導體版本) - 每通道熱負載估算
  # 基於 datasheet 數據進行比例換算到各溫度層
  cf3_ag_heatload_per_channel = [
      80,    # 50K層: 300K→50K, 較高 (μW)
      125,   # 4K層: 50K→4K, datasheet基準值 (μW) 
      15,    # Still層: 4K→0.7K (μW)
      4,     # CP層: 0.7K→0.2K, EE Times基準 (μW)
      0.02   # MXC層: 0.2K→0.02K (μW)
  ]

  # Cri/oFlex 3 NbTi (超導版本) - 10x更低熱負載
  cf3_nbti_heatload_per_channel = [x / 10 for x in cf3_ag_heatload_per_channel]

  # --- 量子處理器佈線需求 ---
  # 100 qubits
  n_qubits_100 = 100
  channels_per_qubit_100 = 3.5  # XY + Flux + Coupler(0.5) + Readout share
  n_channels_100 = int(n_qubits_100 * channels_per_qubit_100)

  # 200 qubits
  n_qubits_200 = 200
  n_channels_200 = int(n_qubits_200 * channels_per_qubit_100)

  # Cri/oFlex 3: 8 channels per flex
  n_flexes_100 = int(ceil(n_channels_100 / 8))
  n_flexes_200 = int(ceil(n_channels_200 / 8))
狀態=empty()
if menu==len(表單): #
  pass
elif menu==MENU[5]:
  fig, ax4= subplots(figsize=(10, 6))
  # --- 圖6: 最優解方案架構 ---
  ax6 = axes[1, 2]
  ax6.set_xlim(0, 10)
  ax6.set_ylim(0, 10)
  ax6.set_aspect('equal')
  ax6.axis('off')
  ax6.set_title('圖6: 推薦最優解架構', fontsize=13, fontweight='bold', pad=20)

  # 室溫電子設備
  rt_box = FancyBboxPatch((1, 8), 8, 1.5, boxstyle="round,pad=0.1",
                                    facecolor='lightcoral', edgecolor='black', linewidth=2)
  ax6.add_patch(rt_box)
  ax6.text(5, 8.75, '室溫電子設備 (RT)', ha='center', va='center', fontsize=11, fontweight='bold')

  # 真空穿通
  vt_box = FancyBboxPatch((3, 6.5), 4, 1, boxstyle="round,pad=0.05",
                                    facecolor='lightyellow', edgecolor='black', linewidth=1.5)
  ax6.add_patch(vt_box)
  ax6.text(5, 7, 'Cri/oFlex 真空穿通 (整合)', ha='center', va='center', fontsize=10, fontweight='bold')

  # 各溫度層
  layer_y = [5.2, 4.0, 2.8, 1.6]
  layer_names = ['50K / 4K 層', 'Still 層', 'CP 層', 'MXC 層']
  layer_colors = ['#FFA500', '#FFD700', '#90EE90', '#87CEEB']

  for i, (y, name, color) in enumerate(zip(layer_y, layer_names, layer_colors)):
      rect = Rectangle((1.5, y-0.3), 7, 0.6, facecolor=color, edgecolor='black', linewidth=1.5, alpha=0.7)
      ax6.add_patch(rect)
      ax6.text(1.2, y, name, ha='right', va='center', fontsize=9, fontweight='bold')
      ax6.text(5, y, '熱夾鉗 (Thermal Clamp)', ha='center', va='center', fontsize=8)

  # 連接線 (flex)
  for x_pos in [3, 4, 6, 7]:
      ax6.plot([x_pos, x_pos], [7.5, 1.3], 'b-', linewidth=3, alpha=0.5)
      ax6.plot([x_pos, x_pos], [7.5, 1.3], 'c--', linewidth=1.5, alpha=0.8)

  # 量子處理器
  qpu_box = FancyBboxPatch((2.5, 0.2), 5, 1, boxstyle="round,pad=0.1",
                                     facecolor='lightgreen', edgecolor='black', linewidth=2)
  ax6.add_patch(qpu_box)
  ax6.text(5, 0.7, '量子處理器 (200 qubits)', ha='center', va='center', fontsize=11, fontweight='bold')

  # 註解
  annotations = [
      (8.5, 5.2, '• 整合衰減器\n• 低通濾波器\n• 紅外濾波器'),
      (8.5, 2.8, '• NbTi 超導導體\n• 熱負載降低1000x'),
      (8.5, 1.0, '• 8通道/flex\n• 0.3mm厚度')
  ]

  for x, y, text in annotations:
      ax6.text(x, y, text, ha='left', va='center', fontsize=8,
               bbox=dict(boxstyle='round', facecolor='white', edgecolor='black', alpha=0.8))

  pyplot(fig)
elif menu==MENU[4]:
  fig, ax4= subplots(figsize=(10, 6))
  # ============================================================
  # 5. 綜合比較表
  # ============================================================
  輸出+=f"\n【5. 綜合方案比較】"
  輸出+=f"\n  {'指標':<25} {'SC-086':<18} {'CF3-Ag':<18} {'CF3-NbTi (推薦)':<20}"
  輸出+="-" * 85
  輸出+=f"  {'每通道熱負載(4K層)':<25} {'~12.6 mW':<18} {'~125 μW':<18} {'~12.5 μW':<20}"
  輸出+=f"  {'熱負載降低倍數':<25} {'1x (基準)':<18} {'~100x':<18} {'~1000x':<20}"
  輸出+=f"  {'主動熱負載(Flux)':<25} {'高':<18} {'中':<18} {'極低(超導)':<20}"
  輸出+=f"  {'空間佔用':<25} {'大':<18} {'小':<18} {'小':<20}"
  輸出+=f"  {'整合衰減器/濾波器':<25} {'需額外安裝':<18} {'已整合':<18} {'已整合':<20}"
  輸出+=f"  {'安裝複雜度':<25} {'高':<18} {'低':<18} {'低':<20}"
  輸出+=f"  {'可靠性':<25} {'一般':<18} {'高':<18} {'高':<20}"
  輸出+=f"  {'單通道成本':<25} {'低':<18} {'中':<18} {'中高':<20}"
  輸出+=f"  {'200qubit可行性':<25} {'不可行':<18} {'可行':<18} {'非常可行':<20}"

  # ============================================================
  # 繪製圖表
  # ============================================================
  fig, axes = subplots(2, 3, figsize=(20, 12))

  # --- 圖1: 靜態熱負載對比 (長條圖) ---
  ax1 = axes[0, 0]
  x = arange(len(stages))
  width = 0.15

  bars1 = ax1.bar(x - 2*width, sc086_fraction, width, label='SC-086 (1008條)', color='#FF6B6B', edgecolor='black')
  bars2 = ax1.bar(x - width, cf3_ag_100_fraction, width, label='CF3-Ag (100q)', color='#FFA500', edgecolor='black')
  bars3 = ax1.bar(x, cf3_ag_200_fraction, width, label='CF3-Ag (200q)', color='#FFD700', edgecolor='black')
  bars4 = ax1.bar(x + width, cf3_nbti_100_fraction, width, label='CF3-NbTi (100q)', color='#90EE90', edgecolor='black')
  bars5 = ax1.bar(x + 2*width, cf3_nbti_200_fraction, width, label='CF3-NbTi (200q)', color='#4169E1', edgecolor='black')

  ax1.set_ylabel('熱負載 / 冷卻功率 (%)', fontsize=11)
  ax1.set_xlabel('稀釋冰箱溫度層', fontsize=11)
  ax1.set_title('圖1: 各方案靜態熱負載佔比對比', fontsize=13, fontweight='bold')
  ax1.set_xticks(x)
  ax1.set_xticklabels(stages)
  ax1.legend(fontsize=9, loc='upper left')
  ax1.axhline(y=100, color='red', linestyle='--', linewidth=2, alpha=0.7, label='100%上限')
  ax1.set_ylim(0, 110)
  ax1.grid(True, alpha=0.3)

  # --- 圖2: 100 qubits 熱負載分佈 ---
  ax2 = axes[0, 1]
  labels_pie = stages
  colors_pie = ['#FF6B6B', '#FFA500', '#FFD700', '#90EE90', '#87CEEB']

  # 使用 NbTi 200q 數據 (最嚴苛但仍可行的情況)
  explode = (0, 0, 0, 0.1, 0)  # 突出 MXC
  ax2.pie(cf3_nbti_200_fraction, labels=labels_pie, colors=colors_pie, autopct='%1.2f%%',
          startangle=90, explode=explode, textprops={'fontsize': 10})
  ax2.set_title('圖2: Cri/oFlex 3 NbTi (200q) 熱負載分佈', fontsize=13, fontweight='bold')

  # --- 圖3: 熱負載降低倍數 ---
  ax3 = axes[0, 2]
  categories = ['50K', '4K', 'Still', 'CP', 'MXC']
  # 計算相對於 SC-086 的降低倍數
  reduction_ag_100 = [sc086_fraction[i]/cf3_ag_100_fraction[i] if cf3_ag_100_fraction[i] > 0 else 999 for i in range(5)]
  reduction_nbti_200 = [sc086_fraction[i]/cf3_nbti_200_fraction[i] if cf3_nbti_200_fraction[i] > 0 else 999 for i in range(5)]

  x3 = arange(len(categories))
  width3 = 0.35
  bars_r1 = ax3.bar(x3 - width3/2, reduction_ag_100, width3, label='CF3-Ag (100q)', color='#FFA500', edgecolor='black')
  bars_r2 = ax3.bar(x3 + width3/2, reduction_nbti_200, width3, label='CF3-NbTi (200q)', color='#4169E1', edgecolor='black')

  ax3.set_ylabel('熱負載降低倍數 (相對SC-086)', fontsize=11)
  ax3.set_xlabel('溫度層', fontsize=11)
  ax3.set_title('圖3: 熱負載降低倍數', fontsize=13, fontweight='bold')
  ax3.set_xticks(x3)
  ax3.set_xticklabels(categories)
  ax3.legend(fontsize=10)
  ax3.set_yscale('log')
  ax3.grid(True, alpha=0.3)

  # 添加數值標籤
  for bar in bars_r1:
      height = bar.get_height()
      if height < 999:
          ax3.text(bar.get_x() + bar.get_width()/2., height * 1.2, f'{height:.0f}x',
                  ha='center', va='bottom', fontsize=8, fontweight='bold')

  # --- 圖4: 方案可行性雷達圖 ---
  ax4 = axes[1, 0]
  categories_radar = ['熱負載\n(低=好)', '空間效率', '安裝\n便利性', '可靠性', '信號\n完整性', '可擴展性']
  N = len(categories_radar)

  # 評分 (1-10)
  sc086_scores = [2, 3, 3, 5, 8, 2]
  cf3_ag_scores = [7, 8, 8, 8, 8, 7]
  cf3_nbti_scores = [10, 9, 9, 9, 9, 10]

  angles = [n / float(N) * 2 * pi for n in range(N)]
  angles += angles[:1]

  sc086_scores += sc086_scores[:1]
  cf3_ag_scores += cf3_ag_scores[:1]
  cf3_nbti_scores += cf3_nbti_scores[:1]

  ax4 = subplot(2, 3, 4, polar=True)
  ax4.plot(angles, sc086_scores, 'o-', linewidth=2, label='SC-086', color='#FF6B6B')
  ax4.fill(angles, sc086_scores, alpha=0.15, color='#FF6B6B')
  ax4.plot(angles, cf3_ag_scores, 's-', linewidth=2, label='CF3-Ag', color='#FFA500')
  ax4.fill(angles, cf3_ag_scores, alpha=0.15, color='#FFA500')
  ax4.plot(angles, cf3_nbti_scores, '^-', linewidth=2, label='CF3-NbTi', color='#4169E1')
  ax4.fill(angles, cf3_nbti_scores, alpha=0.15, color='#4169E1')

  ax4.set_xticks(angles[:-1])
  ax4.set_xticklabels(categories_radar, fontsize=9)
  ax4.set_ylim(0, 10)
  ax4.set_title('圖4: 方案綜合評分雷達圖', fontsize=13, fontweight='bold', pad=20)
  ax4.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=9)

  # --- 圖5: 可擴展性分析 ---
  ax5 = axes[1, 1]
  qubit_range = arange(50, 301, 10)

  # SC-086: 理論上限約 140 qubits (來自論文)
  sc086_max_qubits = 140
  sc086_heatload_vs_q = []
  for nq in qubit_range:
      ch = nq * channels_per_qubit_100
      total = sum([ch * sc086_static_per_cable[i] * 1e-3 for i in range(5)])  # mW total
      sc086_heatload_vs_q.append(total)

  # CF3-NbTi
  cf3_nbti_heatload_vs_q = []
  for nq in qubit_range:
      ch = nq * channels_per_qubit_100
      total = sum([ch * cf3_nbti_heatload_per_channel[i] * 1e-6 for i in range(5)])  # W total
      cf3_nbti_heatload_vs_q.append(total * 1000)  # mW

  ax5.plot(qubit_range, sc086_heatload_vs_q, 'r--', linewidth=2.5, label='SC-086 (理論)', alpha=0.7)
  ax5.plot(qubit_range, cf3_nbti_heatload_vs_q, 'b-', linewidth=2.5, label='Cri/oFlex 3 NbTi')
  ax5.axvline(x=sc086_max_qubits, color='red', linestyle=':', linewidth=2, alpha=0.7)
  ax5.axvline(x=140, color='gray', linestyle='--', linewidth=1.5, alpha=0.5)
  ax5.axvline(x=200, color='gray', linestyle='--', linewidth=1.5, alpha=0.5)

  ax5.set_xlabel('量子位元數', fontsize=11)
  ax5.set_ylabel('總靜態熱負載 (mW)', fontsize=11)
  ax5.set_title('圖5: 可擴展性分析', fontsize=13, fontweight='bold')
  ax5.legend(fontsize=10)
  ax5.grid(True, alpha=0.3)
  ax5.text(sc086_max_qubits + 5, max(sc086_heatload_vs_q)*0.8, 'SC-086\n極限', fontsize=9, color='red')
  pyplot(fig)
elif menu==MENU[3]:
  fig, ax4= subplots(figsize=(10, 6))
  # ============================================================
  # 4. 
  # ============================================================
  輸出=f"\n【4. 空間佔用比較】"

  # SC-086 外徑: 0.86 mm
  sc086_diameter = 0.86  # mm
  sc086_area_per_cable = pi * (sc086_diameter/2)**2  # mm²

  # Cri/oFlex 3: 0.3 mm厚, 8通道, 1mm間距
  # 假設寬度約 10 mm (8通道 * 1mm + 邊距)
  cf3_width = 10  # mm
  cf3_thickness = 0.3  # mm
  cf3_area_per_flex = cf3_width * cf3_thickness  # mm² (截面積)
  cf3_area_per_channel = cf3_area_per_flex / 8

  # 100 qubits
  sc086_total_area_100 = n_channels_100 * sc086_area_per_cable
  cf3_total_area_100 = n_flexes_100 * cf3_area_per_flex

  # 200 qubits
  sc086_total_area_200 = n_channels_200 * sc086_area_per_cable
  cf3_total_area_200 = n_flexes_200 * cf3_area_per_flex

  輸出+=f"\n  SC-086 每條截面積: {sc086_area_per_cable:.2f} mm²"
  輸出+=f"  Cri/oFlex 3 每條flex截面積: {cf3_area_per_flex:.2f} mm²"
  輸出+=f"  Cri/oFlex 3 每通道截面積: {cf3_area_per_channel:.2f} mm²"
  輸出+=f"\n  100 qubits:"
  輸出+=f"    SC-086 總佔用面積: {sc086_total_area_100:.1f} mm²"
  輸出+=f"    Cri/oFlex 3 總佔用面積: {cf3_total_area_100:.1f} mm²"
  輸出+=f"    空間節省: {(1 - cf3_total_area_100/sc086_total_area_100)*100:.1f}%"
  輸出+=f"\n  200 qubits:"
  輸出+=f"    SC-086 總佔用面積: {sc086_total_area_200:.1f} mm²"
  輸出+=f"    Cri/oFlex 3 總佔用面積: {cf3_total_area_200:.1f} mm²"
  輸出+=f"    空間節省: {(1 - cf3_total_area_200/sc086_total_area_200)*100:.1f}%"
  狀態.code(輸出)
  #pyplot(fig)
elif menu==MENU[2]: #
  fig, ax4= subplots(figsize=(10, 6))
  # ============================================================
  # 3. 主動熱負載估算
  # ============================================================
  輸出=f"\n【3. 主動熱負載估算】"

  # 通量偏置線: 每條約 0.4 mA DC
  I_flux = 0.4e-3  # A
  # Cri/oFlex 3 內導體電阻 (低溫下 NbTi 為超導態, R≈0)
  # Ag版本在低溫仍有殘餘電阻
  R_cf3_ag_per_m = 0.5  # Ω/m (估算)
  R_cf3_nbti_per_m = 0.0  # Ω/m (超導態)

  # 各層電纜長度總和
  total_length = sum(cable_lengths)

  # Ag版本主動熱負載
  P_active_ag_per_channel = I_flux**2 * R_cf3_ag_per_m * total_length
  # 假設 30% 的線為 flux bias (持續電流)
  n_flux_lines_100 = int(n_channels_100 * 0.3)
  n_flux_lines_200 = int(n_channels_200 * 0.3)

  P_active_ag_100 = n_flux_lines_100 * P_active_ag_per_channel
  P_active_ag_200 = n_flux_lines_200 * P_active_ag_per_channel

  # NbTi版本主動熱負載 (超導, 幾乎為0)
  P_active_nbti_100 = 0  # 超導態無歐姆損耗
  P_active_nbti_200 = 0

  輸出+=f"\n  通量偏置線電流: {I_flux*1e3:.1f} mA"
  輸出+=f"  Ag版本每通道主動熱負載: {P_active_ag_per_channel*1e6:.2f} μW"
  輸出+=f"  NbTi版本每通道主動熱負載: ~0 μW (超導態)"
  輸出+=f"\n  100 qubits - Ag版本總主動熱負載: {P_active_ag_100*1e6:.1f} μW"
  輸出+=f"  200 qubits - Ag版本總主動熱負載: {P_active_ag_200*1e6:.1f} μW"

  狀態.code(輸出)
  #pyplot(fig)
elif menu==MENU[1]:
  fig, ax4= subplots(figsize=(10, 6))
  # ============================================================
  # 2. 
  # ============================================================
  輸出=f"\n【2. 熱負載瓶頸分析】"

  def find_bottleneck(fractions, name, 輸出):
      max_idx = argmax(fractions)
      輸出+=f"\n  {name}:"
      輸出+=f"    最大熱負載層: {stages[max_idx]} ({fractions[max_idx]:.2f}%)"
      輸出+=f"    各層佔比: "
      for i, s in enumerate(stages):
          輸出+=f"{s}={fractions[i]:.2f}%"
      return max_idx, 輸出

  sc086_fraction=session_state['sc086_fraction']
  cf3_ag_100_fraction=session_state['cf3_ag_100_fraction']
  cf3_ag_200_fraction=session_state['cf3_ag_200_fraction']
  cf3_nbti_100_fraction=session_state['cf3_nbti_100_fraction']
  cf3_nbti_200_fraction=session_state['cf3_nbti_200_fraction']
  bottleneck_sc086, 輸出 = find_bottleneck(sc086_fraction, "SC-086/50-SCN-CN (1008條)", 輸出)
  bottleneck_cf3_ag_100, 輸出 = find_bottleneck(cf3_ag_100_fraction, "Cri/oFlex 3 Ag (100 qubits)", 輸出)
  bottleneck_cf3_ag_200, 輸出 = find_bottleneck(cf3_ag_200_fraction, "Cri/oFlex 3 Ag (200 qubits)", 輸出)
  bottleneck_cf3_nbti_100, 輸出 = find_bottleneck(cf3_nbti_100_fraction, "Cri/oFlex 3 NbTi (100 qubits)", 輸出)
  bottleneck_cf3_nbti_200, 輸出 = find_bottleneck(cf3_nbti_200_fraction, "Cri/oFlex 3 NbTi (200 qubits)", 輸出)
  狀態.code(輸出)

  #pyplot(fig)
elif menu==MENU[0]:
  #fig, ax1= subplots(figsize=(10, 6))
  輸出="Cri/oFlex 3 高密度佈線熱負載分析\n"
  輸出+="=" * 70
  輸出+=f"\n【系統配置】"
  輸出+=f"  量子位元數: 100 - 200 qubits\n"
  輸出+=f"  每量子位元通道數: ~{channels_per_qubit_100}\n"
  輸出+=f"  100 qubits 總通道數: {n_channels_100}\n"
  輸出+=f"  200 qubits 總通道數: {n_channels_200}\n"
  輸出+=f"  Cri/oFlex 3 每條 flex 通道數: 8\n"
  輸出+=f"  100 qubits 所需 flex 數: {n_flexes_100}\n"
  輸出+=f"  200 qubits 所需 flex 數: {n_flexes_200}\n"

  # ============================================================
  # 1. 計算熱負載
  # ============================================================

  def calculate_heatload(n_channels, heatload_per_channel, cooling_power):
      """計算總熱負載與佔冷卻功率比例"""
      total_heatload = [n_channels * h * 1e-6 for h in heatload_per_channel]  # W
      fraction = [total_heatload[i] / cooling_power[i] * 100 for i in range(len(stages))]
      return total_heatload, fraction

  # SC-086/50-SCN-CN (1008條 = 參考基準)
  sc086_total, sc086_fraction = calculate_heatload(1008, sc086_static_per_cable, cooling_power)

  # Cri/oFlex 3 Ag - 100 qubits
  cf3_ag_100_total, cf3_ag_100_fraction = calculate_heatload(n_channels_100, cf3_ag_heatload_per_channel, cooling_power)

  # Cri/oFlex 3 Ag - 200 qubits
  cf3_ag_200_total, cf3_ag_200_fraction = calculate_heatload(n_channels_200, cf3_ag_heatload_per_channel, cooling_power)

  # Cri/oFlex 3 NbTi - 100 qubits
  cf3_nbti_100_total, cf3_nbti_100_fraction = calculate_heatload(n_channels_100, cf3_nbti_heatload_per_channel, cooling_power)

  # Cri/oFlex 3 NbTi - 200 qubits
  cf3_nbti_200_total, cf3_nbti_200_fraction = calculate_heatload(n_channels_200, cf3_nbti_heatload_per_channel, cooling_power)

  輸出+=f"\n【1. 靜態熱負載計算結果】"
  輸出+=f"\n  {'層級':<8} {'冷卻功率':<12} {'SC-086(1008條)':<18} {'CF3-Ag(100q)':<16} {'CF3-Ag(200q)':<16} {'CF3-NbTi(100q)':<16} {'CF3-NbTi(200q)':<16}"
  輸出+=f"  {'':8} {'[W]':<12} {'[%佔比]':<18} {'[%佔比]':<16} {'[%佔比]':<16} {'[%佔比]':<16} {'[%佔比]':<16}"
  輸出+="-" * 110
  session_state['sc086_fraction']=sc086_fraction
  session_state['cf3_ag_100_fraction']=cf3_ag_100_fraction
  session_state['cf3_ag_200_fraction']=cf3_ag_200_fraction
  session_state['cf3_nbti_100_fraction']=cf3_nbti_100_fraction
  session_state['cf3_nbti_200_fraction']=cf3_nbti_200_fraction
  session_state['cf3_ag_heatload_per_channel']=cf3_ag_100_fraction
  for i, stage in enumerate(stages):
      輸出+=f"  {stage:<8} {cooling_power[i]:<12.4f} {sc086_fraction[i]:<18.2f} {cf3_ag_100_fraction[i]:<16.4f} {cf3_ag_200_fraction[i]:<16.4f} {cf3_nbti_100_fraction[i]:<16.4f} {cf3_nbti_200_fraction[i]:<16.4f}"

  輸出+="-" * 110
  狀態.code(輸出)
  #pyplot(fig)


#tight_layout(pad=3.0)
#savefig('/mnt/agents/output/cf3_analysis.png', dpi=150, bbox_inches='tight', facecolor='white')
#pyplot(fig)

#print("\n\n圖表已保存至 /mnt/agents/output/cf3_analysis.png")
