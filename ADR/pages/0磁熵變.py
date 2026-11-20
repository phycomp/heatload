from matplotlib.pyplot import rcParams, savefig, show, subplots, tight_layout
from numpy import cos, pi, radians, random, sin
from numpy.random import seed, uniform
from streamlit import pyplot, sidebar, radio, text_input

#import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from fontUtil2 import 配置中文
配置中文()

# 設定中文字型
rcParams['font.size'] = 12
from streamlit import empty
MENU, 表單=[], ['制冷', '', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  狀態=empty()
  狀態.code([])
if menu==len(表單): #
  pass
elif menu==MENU[1]: #
  pass
elif menu==MENU[0]: #制冷
  pass

fig, axes = subplots(2, 2, figsize=(16, 14))
fig.suptitle('Adiabatic Demagnetization Refrigeration (ADR)\n絕熱去磁制冷 - 四步驟循環', fontsize=18, fontweight='bold', y=0.98)

def draw_step(ax, title, subtitle, temp_label, field_label, entropy_label, dipoles_aligned, heat_flow, color_scheme, step_num):
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # 標題
    ax.text(5, 9.5, f'步驟 {step_num}: {title}', fontsize=14, fontweight='bold', ha='center', va='center', color='#2c3e50')
    ax.text(5, 8.8, subtitle, fontsize=11, ha='center', va='center', color='#7f8c8d', style='italic')
    
    # 熱庫/樣品區域
    if heat_flow == 'out':
        # 熱量流出到熱庫
        ax.add_patch(FancyBboxPatch((0.5, 5.5), 3, 2.5, boxstyle="round,pad=0.1", facecolor='#e74c3c', alpha=0.3, edgecolor='#c0392b', linewidth=2))
        ax.text(2, 7.2, '熱庫\n(Heat Sink)', fontsize=9, ha='center', va='center', color='#c0392b')
        ax.annotate('', xy=(2, 6.5), xytext=(2, 5.8), arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=2))
        ax.text(2, 6.1, 'Qout', fontsize=9, ha='center', color='#e74c3c')
    elif heat_flow == 'in':
        # 熱量從樣品流入
        ax.add_patch(FancyBboxPatch((0.5, 5.5), 3, 2.5, boxstyle="round,pad=0.1", facecolor='#3498db', alpha=0.3, edgecolor='#2980b9', linewidth=2))
        ax.text(2, 7.2, '待冷卻樣品\n(Sample)', fontsize=9, ha='center', va='center', color='#2980b9')
        ax.annotate('', xy=(2, 5.8), xytext=(2, 6.5), arrowprops=dict(arrowstyle='->', color='#3498db', lw=2))
        ax.text(2, 6.1, 'Qin', fontsize=9, ha='center', color='#3498db')
    elif heat_flow == 'isolated':
        # 絕熱隔離
        ax.add_patch(FancyBboxPatch((0.5, 5.5), 3, 2.5, boxstyle="round,pad=0.1", facecolor='#95a5a6', alpha=0.3, edgecolor='#7f8c8d', linewidth=2))
        ax.text(2, 7.2, '絕熱隔離\n(Adiabatic)', fontsize=9, ha='center', va='center', color='#7f8c8d')
        ax.text(2, 6.5, '✕', fontsize=20, ha='center', va='center', color='#e74c3c')
        ax.text(2, 5.8, '無熱交換', fontsize=9, ha='center', color='#7f8c8d')
    
    # 順磁材料（制冷劑）
    ax.add_patch(FancyBboxPatch((4, 4), 3, 4, boxstyle="round,pad=0.15", facecolor=color_scheme, alpha=0.4, edgecolor='#2c3e50', linewidth=2.5))
    ax.text(5.5, 7.5, '順磁材料\n(Paramagnet)', fontsize=10, ha='center', va='center', fontweight='bold', color='#2c3e50')
    
    # 磁矩示意
    center_x, center_y = 5.5, 5.5
    if dipoles_aligned == 'high':
        # 高度排列
        for i in range(-1, 2):
            for j in range(-1, 2):
                ax.annotate('', xy=(center_x + i*0.6 + 0.1, center_y + j*0.6 + 0.4), xytext=(center_x + i*0.6 - 0.1, center_y + j*0.6 - 0.4), arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=2))
    elif dipoles_aligned == 'low':
        # 部分排列
        angles = [0, 45, -30, 60, -45, 15, -60, 30, 0]
        for idx, (i, j) in enumerate([(-1,-1), (-1,0), (-1,1), (0,-1), (0,0), (0,1), (1,-1), (1,0), (1,1)]):
            angle = radians(angles[idx])
            dx, dy = 0.3 * sin(angle), 0.3 * cos(angle)
            ax.annotate('', xy=(center_x + i*0.6 + dx, center_y + j*0.6 + dy), xytext=(center_x + i*0.6 - dx, center_y + j*0.6 - dy), arrowprops=dict(arrowstyle='->', color='#3498db', lw=2))
    else:  # random
        # 隨機方向
        seed(42)
        for i in range(-1, 2):
            for j in range(-1, 2):
                angle = uniform(0, 2*pi)
                dx, dy = 0.3 * sin(angle), 0.3 * cos(angle)
                ax.annotate('', xy=(center_x + i*0.6 + dx, center_y + j*0.6 + dy), xytext=(center_x + i*0.6 - dx, center_y + j*0.6 - dy), arrowprops=dict(arrowstyle='->', color='#9b59b6', lw=2))
    
    # 磁場指示
    if field_label == '強磁場 B↑':
        ax.annotate('', xy=(7.5, 5.5), xytext=(7.5, 8), arrowprops=dict(arrowstyle='->', color='#e67e22', lw=3))
        ax.text(7.8, 6.8, 'B↑', fontsize=14, fontweight='bold', color='#e67e22', rotation=90)
        # 磁場線
        for y in [5, 6, 7]:
            ax.plot([7.2, 7.8], [y, y], color='#e67e22', lw=1.5, alpha=0.5)
    elif field_label == '弱磁場 B↓':
        ax.annotate('', xy=(7.5, 6.5), xytext=(7.5, 7.5), arrowprops=dict(arrowstyle='->', color='#e67e22', lw=1.5))
        ax.text(7.8, 7, 'B↓', fontsize=12, color='#e67e22', rotation=90)
    else:
        ax.text(7.8, 6.8, 'B=0', fontsize=12, color='#95a5a6', rotation=90)
    
    # 溫度指示
    ax.add_patch(FancyBboxPatch((8.2, 4), 1.5, 1.5, boxstyle="round,pad=0.1", facecolor='#ecf0f1', edgecolor='#34495e', linewidth=1.5))
    ax.text(8.95, 5.2, '🌡️', fontsize=16, ha='center')
    ax.text(8.95, 4.5, temp_label, fontsize=10, ha='center', fontweight='bold', color='#34495e')
    
    # 熵變化指示
    ax.text(5.5, 3.2, f'熵變: {entropy_label}', fontsize=10, ha='center', fontweight='bold', color='#8e44ad', bbox=dict(boxstyle='round,pad=0.3', facecolor='#f5eef8', edgecolor='#8e44ad'))

# 繪製四個步驟
draw_step(axes[0,0], '等溫磁化', 'Isothermal Magnetization', 'T = T0\n(常溫)', '強磁場 B↑', '磁熵↓ 晶格熵↑', 'high', 'out', '#fadbd8', 1)

draw_step(axes[0,1], '絕熱退磁', 'Adiabatic Demagnetization', 'T << T0\n(極低溫!)', '弱磁場 B↓', '磁熵↑ 晶格熵↓', 'low', 'isolated', '#d4efdf', 2)

draw_step(axes[1,0], '等溫吸熱', 'Isothermal Heat Absorption', 'T = T_low\n(維持低溫)', '弱磁場 B≈0', '磁熵↑ 吸收熱量', 'random', 'in', '#d6eaf8', 3)

draw_step(axes[1,1], '絕熱再磁化', 'Adiabatic Remagnetization', 'T ↑\n(回升)', '強磁場 B↑', '磁熵↓ 準備下一循環', 'high', 'isolated', '#fef9e7', 4)
tight_layout(rect=[0, 0, 1, 0.96])
pyplot(fig)
#savefig('/mnt/agents/output/ADR_cycle_diagram.png', dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
#show()
#print("圖1已保存")
