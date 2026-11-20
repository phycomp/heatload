from matplotlib.pyplot import figure, savefig, show, subplot, tight_layout
from numpy import arange, diff, exp, linspace, log10, logspace, pi, sin, sqrt, sum, zeros_like
# 生成一個靜態的預覽圖，展示模擬器的主要功能
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.patches as mpatches
from fontUtil2 import 配置中文
配置中文()
fig = figure(figsize=(20, 14))
from matplotlib.pyplot import rcParams, savefig, show, subplots, tight_layout
from streamlit import pyplot, sidebar, radio, text_input, empty
fig.suptitle('PCB N-Channel Trace Skew 互動式模擬器 - 功能預覽', fontsize=20, fontweight='bold', y=0.98)

MENU, 表單=[], ['幾何形狀', '延遲圖', 'Dk頻率響應', 'Df頻率響應', 'Skew對比頻率', '插入損耗', '趨膚深度', '總覽']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12']
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  freq = logspace(-1, 2, 200)
  狀態=empty()
  狀態.code([])
if menu==len(表單): #
  pass
elif menu==MENU[7]: #
  # ========== 子圖 9: 功能總覽 ==========
  fig, ax9= subplots(figsize=(10, 6))
  #ax9 = subplot(3, 3, 9)
  ax9.axis('off')

  features = [
      "✅ N-Channel Trace 幾何視覺化",
      "✅ 6種 Trace 形狀 (直線/蛇形/手風琴/階梯/波浪/螺旋)",
      "✅ 即時傳播延遲計算 (ps)",
      "✅ Skew 閾值檢查與合格判定",
      "✅ 蛇形繞線補償計算",
      "✅ 頻率相關 Dk/Df 色散分析",
      "✅ 8種 PCB 材料參數資料庫",
      "✅ 溫度效應修正 (TCDk/TCDf)",
      "✅ 多材料並行比較",
      "✅ 插入損耗頻譜分析",
      "✅ 趨膚深度計算",
      "✅ 核心物理公式展示"
  ]

  y_pos = 0.95
  for feat in features:
      ax9.text(0.05, y_pos, feat, fontsize=10, transform=ax9.transAxes,
              bbox=dict(boxstyle='round,pad=0.4', facecolor='#e8f4f8', edgecolor='#3498db', alpha=0.9))
      y_pos -= 0.075

  ax9.text(0.05, 0.05, '📥 下載 pcb_skew_simulator.py\n執行: streamlit run pcb_skew_simulator.py', 
          fontsize=11, fontweight='bold', transform=ax9.transAxes, color='#c0392b',
          bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffeaa7', edgecolor='#fdcb6e'))

  tight_layout(rect=[0, 0, 1, 0.96])
  pyplot(fig)
elif menu==MENU[6]: #
  fig, ax8= subplots(figsize=(10, 6))
  # ========== 子圖 8: 趨膚深度 ==========
  #ax8 = subplot(3, 3, 8)

  mu0 = 4*pi*1e-7
  sigma_fr4 = 2*pi*freq*1e9 * 4.3 * 8.854e-12 * 0.02
  skin_fr4 = sqrt(2/(mu0*sigma_fr4)) * 1000

  ax8.semilogx(freq, skin_fr4, 'purple', linewidth=2.5)
  ax8.fill_between(freq, skin_fr4, alpha=0.2, color='purple')

  for kf in [1, 5, 10, 25]:
      if 0.1 <= kf <= 100:
          sigma = 2*pi*kf*1e9 * 4.3 * 8.854e-12 * 0.02
          sd = sqrt(2/(mu0*sigma)) * 1000
          ax8.annotate(f'{sd:.3f}mm', xy=(kf, sd), xytext=(kf*2, sd*1.3),
                      fontsize=8, arrowprops=dict(arrowstyle='->', color='gray'))

  ax8.set_xlabel('頻率 (GHz)', fontsize=11)
  ax8.set_ylabel('趨膚深度 (mm)', fontsize=11)
  ax8.set_title('🔬 Tab 5: 趨膚深度分析', fontsize=13, fontweight='bold', pad=10)
  ax8.grid(True, alpha=0.3, which='both')

  pyplot(fig)
elif menu==MENU[5]: #
  fig, ax7= subplots(figsize=(10, 6))
  # ========== 子圖 7: 材料比較 - 插入損耗 ==========
  #ax7 = subplot(3, 3, 7)

  att_fr4 = [20*log10(exp((pi*f*1e9*sqrt(4.3)*0.02)/3e8 * 0.1)) for f in freq]
  att_meg = [20*log10(exp((pi*f*1e9*sqrt(3.7)*0.002)/3e8 * 0.1)) for f in freq]
  att_rog = [20*log10(exp((pi*f*1e9*sqrt(3.48)*0.0037)/3e8 * 0.1)) for f in freq]

  ax7.semilogx(freq, att_fr4, 'b-', linewidth=2.5, label='FR-4')
  ax7.semilogx(freq, att_meg, 'g-', linewidth=2.5, label='Megtron 6')
  ax7.semilogx(freq, att_rog, 'r-', linewidth=2.5, label='Rogers')

  ax7.set_xlabel('頻率 (GHz)', fontsize=11)
  ax7.set_ylabel('插入損耗 (dB/100mm)', fontsize=11)
  ax7.set_title('📊 Tab 4: 插入損耗比較', fontsize=13, fontweight='bold', pad=10)
  ax7.legend(fontsize=9)
  ax7.grid(True, alpha=0.3, which='both')

  pyplot(fig)
elif menu==MENU[4]: #
  fig, ax5= subplots(figsize=(10, 6))

  # ========== 子圖 5: Skew vs 頻率 ==========
  #ax5 = subplot(3, 3, 6)

  # 模擬不同通道在不同頻率下的 Skew
  for i in range(4):
      base_skew = [0, 7.7, 5.3, 1.6][i]
      skew_freq = base_skew * (1 + 0.02 * log10(freq/10 + 0.1))
      ax5.semilogx(freq, skew_freq, color=colors[i], linewidth=2, label=f'Ch{i+1}')

  ax5.axhline(y=5, color='red', linestyle='--', linewidth=2, label='閾值: 5 ps')
  ax5.fill_between(freq, -5, 5, alpha=0.1, color='green')

  ax5.set_xlabel('頻率 (GHz)', fontsize=11)
  ax5.set_ylabel('Skew (ps)', fontsize=11)
  ax5.set_title('📈 Tab 3: 頻率相關 Skew', fontsize=13, fontweight='bold', pad=10)
  ax5.legend(fontsize=8, loc='upper left')
  ax5.grid(True, alpha=0.3, which='both')

  pyplot(fig)
elif menu==MENU[3]: #
  fig, ax4= subplots(figsize=(10, 6))
  # ========== 子圖 4: Df 頻率響應 ==========
  #ax4 = subplot(3, 3, 5)

  Df_fr4 = 0.020 * (1 + 0.002 * log10(freq + 0.1))
  Df_meg = 0.002 * (1 + 0.0005 * log10(freq + 0.1))
  Df_rog = 0.0037 * (1 + 0.0003 * log10(freq + 0.1))

  ax4.semilogx(freq, Df_fr4, 'b-', linewidth=2.5, label='FR-4')
  ax4.semilogx(freq, Df_meg, 'g-', linewidth=2.5, label='Megtron 6')
  ax4.semilogx(freq, Df_rog, 'r-', linewidth=2.5, label='Rogers')

  ax4.set_xlabel('頻率 (GHz)', fontsize=11)
  ax4.set_ylabel('Df', fontsize=11)
  ax4.set_title('📈 Tab 3: Df 頻率響應 (損耗)', fontsize=13, fontweight='bold', pad=10)
  ax4.legend(fontsize=9)
  ax4.grid(True, alpha=0.3, which='both')
  pyplot(fig)

elif menu==MENU[2]: #
  fig, ax3= subplots(figsize=(10, 6))

  # ========== 子圖 3: Dk 頻率響應 ==========
  #ax3 = subplot(3, 3, 4)

  Dk_fr4 = 4.3 * (1 - 0.015 * log10(freq + 0.1))
  Dk_meg = 3.7 * (1 - 0.010 * log10(freq + 0.1))
  Dk_rog = 3.48 * (1 - 0.005 * log10(freq + 0.1))

  ax3.semilogx(freq, Dk_fr4, 'b-', linewidth=2.5, label='FR-4 (標準)')
  ax3.semilogx(freq, Dk_meg, 'g-', linewidth=2.5, label='Megtron 6')
  ax3.semilogx(freq, Dk_rog, 'r-', linewidth=2.5, label='Rogers RO4350B')
  ax3.fill_between(freq, Dk_fr4, alpha=0.1, color='blue')
  ax3.fill_between(freq, Dk_meg, alpha=0.1, color='green')

  ax3.set_xlabel('頻率 (GHz)', fontsize=11)
  ax3.set_ylabel('Dk', fontsize=11)
  ax3.set_title('📈 Tab 3: Dk 頻率響應 (色散)', fontsize=13, fontweight='bold', pad=10)
  ax3.legend(fontsize=9)
  ax3.grid(True, alpha=0.3, which='both')

  pyplot(fig)
elif menu==MENU[1]: #
  fig, ax2= subplots(figsize=(10, 6))
  pass
  # ========== 子圖 2: 延遲條形圖 ==========
  #ax2 = subplot(3, 3, 3)

  delays = [726.5, 734.2, 731.8, 728.1]
  x_pos = arange(4)
  bars = ax2.bar(x_pos, delays, color=colors, alpha=0.75, edgecolor='black', linewidth=1.5)

  for bar, delay in zip(bars, delays):
      ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
              f'{delay:.1f} ps', ha='center', va='bottom', fontsize=10, fontweight='bold')

  ax2.axhline(y=730, color='red', linestyle='--', linewidth=2, label='Skew 閾值: 5 ps')
  ax2.annotate('最大 Skew: 7.7 ps', xy=(3, 734.2), xytext=(2.5, 740),
              fontsize=11, fontweight='bold', color='red',
              arrowprops=dict(arrowstyle='->', color='red', lw=2))

  ax2.set_ylabel('傳播延遲 (ps)', fontsize=11)
  ax2.set_title('⏱️ Tab 2: Skew 分析', fontsize=13, fontweight='bold', pad=10)
  ax2.set_xticks(x_pos)
  ax2.set_xticklabels(['Ch1', 'Ch2', 'Ch3', 'Ch4'])
  ax2.legend(fontsize=9)
  ax2.grid(True, alpha=0.3, axis='y')
  pyplot(fig)
elif menu==MENU[0]: #幾何形狀
  fig, ax1= subplots(figsize=(10, 6))
  pass
  # ========== 子圖 1: Trace 幾何形狀 ==========
  #ax1 = subplot(3, 3, (1, 2))

  # 生成 4 條不同形狀的 trace
  shapes_data = []
  shapes = [("直線", lambda x: zeros_like(x)),
            ("蛇形", lambda x: 2*sin(2*pi*x/10)),
            ("手風琴", lambda x: 1.5*sin(2*pi*x/8)),
            ("波浪", lambda x: sin(2*pi*x/5) + 0.5*sin(4*pi*x/5))]


  for i, (name, func) in enumerate(shapes):
      x = linspace(0, 100, 200)
      y_base = func(x)
      y = y_base + i * 8
      
      dx = diff(x)
      dy = diff(y_base)
      actual_len = sum(sqrt(dx**2 + dy**2))
      delay = actual_len / (299.79/sqrt(4.3)) * 1000
      
      ax1.plot(x, y, color=colors[i], linewidth=2.5, label=f'Ch{i+1}: {name} ({actual_len:.1f}mm, {delay:.1f}ps)')
      ax1.fill_between(x, y - 0.4, y + 0.4, color=colors[i], alpha=0.12)
      
      mid = len(x)//2
      ax1.annotate(f'{actual_len:.1f}mm\n{delay:.1f}ps', 
                  xy=(x[mid], y[mid]), fontsize=8, ha='center', va='center',
                  bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=colors[i], alpha=0.9))

  ax1.set_xlabel('X (mm)', fontsize=11)
  ax1.set_ylabel('Y (mm, 通道偏移)', fontsize=11)
  ax1.set_title('📐 Tab 1: N-Channel Trace 幾何形狀', fontsize=13, fontweight='bold', pad=10)
  ax1.legend(loc='upper right', fontsize=9)
  ax1.grid(True, alpha=0.3)
  ax1.set_ylim(-3, 35)
  pyplot(fig)
#savefig('/mnt/agents/output/pcb_skew_preview.png', dpi=150, bbox_inches='tight', facecolor='white')
#show()
#print("✅ 預覽圖已儲存")
