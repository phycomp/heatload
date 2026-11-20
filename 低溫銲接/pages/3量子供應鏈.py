from matplotlib.pyplot import rcParams, Rectangle, savefig, show, subplots, tight_layout
from streamlit import pyplot, empty, radio, text_input, sidebar
from numpy import arange
from fontUtil2 import 配置中文
配置中文()
#import matplotlib.pyplot as plt
#import numpy as np

# 創建台灣量子供應鏈協作廠商分析圖
fig, axes = subplots(2, 2, figsize=(16, 12))
MENU, 表單=[], ['供應鏈', '試產', '關鍵廠商', '量產']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  狀態=empty()
  狀態.code([])
if menu==len(表單): #
  pass
elif menu==MENU[3]: # 4. 量產成本與良率預估 (右下)
    fig, ax4= subplots(figsize=(10, 6))
    #ax4 = axes[1, 1]

    # 量產階段
    stages_prod = ['試產\n(10套)', '小量產\n(100套)', '中量產\n(1000套)', '大量產\n(10000套)']
    x_pos = arange(len(stages_prod))

    # 單位成本 (相對值)
    cost_per_unit = [100, 65, 45, 35]
    # 良率
    yield_rate = [60, 75, 88, 95]

    # 雙Y軸
    ax4_twin = ax4.twinx()

    bars = ax4.bar(x_pos - 0.2, cost_per_unit, 0.4, color='#FF6B6B', alpha=0.8, 
                   label='Unit Cost (Relative)', edgecolor='black')
    line = ax4_twin.plot(x_pos + 0.2, yield_rate, 'o-', color='#4ECDC4', linewidth=2.5, 
                         markersize=10, label='Yield Rate (%)')

    ax4.set_xlabel('Production Stage', fontsize=11)
    ax4.set_ylabel('Relative Unit Cost', fontsize=11, color='#FF6B6B')
    ax4_twin.set_ylabel('Yield Rate (%)', fontsize=11, color='#4ECDC4')
    ax4.set_title('量產成本與良率預估', fontsize=12, fontweight='bold')
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels(stages_prod, fontsize=10)
    ax4.set_ylim(0, 120)
    ax4_twin.set_ylim(0, 100)

    # 添加數值標簽
    for bar, cost in zip(bars, cost_per_unit):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                 f'{cost}', ha='center', va='bottom', fontsize=10, fontweight='bold', color='#FF6B6B')

    for i, y in enumerate(yield_rate):
        ax4_twin.text(i + 0.2, y + 2, f'{y}%', ha='center', va='bottom', 
                      fontsize=10, fontweight='bold', color='#4ECDC4')

    ax4.legend(loc='upper left', fontsize=9)
    ax4_twin.legend(loc='upper right', fontsize=9)
    ax4.grid(True, alpha=0.3, axis='y')

    pyplot(fig)
elif menu==MENU[2]: #
    fig, ax3= subplots(figsize=(10, 6))
    # 3. 關鍵廠商能力矩陣 (左下)
    #ax3 = axes[1, 0]

    companies = ['千附精密', '進期科技', '帛江科技', '精穩科技', '慶陞工業', 
                 '申玥科技', '傑地有限公司', '台灣量子科技']
    capabilities = {
        '低溫真空\n腔體': [9, 8, 2, 2, 2, 6, 2, 3],
        '精密CNC\n加工': [8, 7, 7, 7, 7, 9, 2, 4],
        '微波連接器\n製造': [2, 2, 9, 8, 8, 3, 2, 4],
        '材料供應\n(環氧/PTFE)': [2, 2, 2, 2, 2, 2, 8, 5],
        '低溫測試\n驗證': [3, 2, 2, 2, 2, 2, 2, 6],
        '量子系統\n整合': [2, 2, 2, 2, 2, 2, 2, 8],
    }

    x = arange(len(companies))
    width = 0.12
    colors_cap = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFD700', '#96CEB4', '#C0C0C0']

    for i, (cap_name, scores) in enumerate(capabilities.items()):
        offset = (i - 2.5) * width
        bars = ax3.bar(x + offset, scores, width, label=cap_name, 
                       color=colors_cap[i], alpha=0.8, edgecolor='black', linewidth=0.5)

    ax3.set_xticks(x)
    ax3.set_xticklabels(companies, fontsize=8, rotation=30, ha='right')
    ax3.set_ylabel('Capability Score (1-10)', fontsize=11)
    ax3.set_title('協力廠商能力矩陣分析', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=8, loc='upper left', ncol=2)
    ax3.set_ylim(0, 10)
    ax3.grid(True, alpha=0.3, axis='y')

    pyplot(fig)
elif menu==MENU[1]: #
    fig, ax2= subplots(figsize=(10, 6))
    # 2. 試產階段甘特圖 (右上)
    #ax2 = axes[0, 1]

    phases = ['Phase 1\n材料驗證', 'Phase 2\n原型試產', 'Phase 3\n低溫測試', 
              'Phase 4\n性能優化', 'Phase 5\n小量產', 'Phase 6\n量產導入']
    partners = ['中研院/工研院', '千附精密/進期科技', '工研院量子實驗室', 
                '帛江/精穩/慶陞', '台灣量子科技', '日月光/鴻海']

    # 甘特圖數據
    gantt_data = [
        (0, 3, '#45B7D1'),   # Phase 1: 0-3月
        (2, 4, '#FF6B6B'),   # Phase 2: 2-6月
        (4, 3, '#4ECDC4'),   # Phase 3: 4-7月
        (6, 3, '#FFD700'),   # Phase 4: 6-9月
        (8, 4, '#96CEB4'),   # Phase 5: 8-12月
        (11, 6, '#C0C0C0'),  # Phase 6: 11-17月
    ]

    for i, (phase, partner) in enumerate(zip(phases, partners)):
        start, duration, color = gantt_data[i]
        ax2.barh(i, duration, left=start, height=0.6, color=color, alpha=0.8, 
                 edgecolor='black', linewidth=1)
        ax2.text(start + duration/2, i, f'{partner}', ha='center', va='center', 
                 fontsize=8, fontweight='bold')

    ax2.set_yticks(range(len(phases)))
    ax2.set_yticklabels(phases, fontsize=9)
    ax2.set_xlabel('Time (Months)', fontsize=11)
    ax2.set_title('試產→量產時程規劃 (18個月)', fontsize=12, fontweight='bold')
    ax2.set_xlim(0, 18)
    ax2.grid(True, alpha=0.3, axis='x')
    ax2.axvline(x=12, color='red', linestyle='--', alpha=0.7, label='12月裏程碑')
    ax2.legend(fontsize=9)

    pyplot(fig)
elif menu==MENU[0]: #供應鏈
    fig, ax1= subplots(figsize=(10, 6))
    fig.suptitle('台灣 NbTi 量子傳輸線黏著劑最優解\n協力廠商試產/量產策略規劃', fontsize=15, fontweight='bold', y=0.98)

    #ax1 = axes[0, 0]
    ax1.set_xlim(0, 10) # 1. 供應鏈生態圖 (左上)
    ax1.set_ylim(0, 10)
    ax1.axis('off')
    ax1.set_title('台灣量子供應鏈生態圖', fontsize=12, fontweight='bold')

    # 核心需求方
    ax1.add_patch(Rectangle((3.5, 8.5), 3, 1, fill=True, facecolor='#E8F4FD', 
                                  edgecolor='#2C3E50', linewidth=2))
    ax1.text(5, 9, '核心需求\nNbTi傳輸線+黏著劑+連接器', ha='center', va='center', 
             fontsize=9, fontweight='bold')

    # 上遊材料
    materials = [
        ('NbTi超導線材\n(西部超導/進口)', 1, 6.5, '#45B7D1'),
        ('低溫環氧樹脂\n(Stycast/傑地代理)', 5, 6.5, '#FF6B6B'),
        ('PTFE墊片\n(台灣塑膠原料)', 9, 6.5, '#4ECDC4'),
        ('銦焊料\n(純銦/進口)', 1, 4.5, '#FFD700'),
        ('不鏽鋼腔體\n(千附精密/進期)', 5, 4.5, '#C0C0C0'),
        ('微波連接器\n(帛江/精穩/慶陞)', 9, 4.5, '#96CEB4'),
    ]

    for name, x, y, color in materials:
        ax1.add_patch(Rectangle((x-0.8, y-0.4), 1.6, 0.8, fill=True, facecolor=color, 
                                      edgecolor='#2C3E50', linewidth=1.5, alpha=0.8))
        ax1.text(x, y, name, ha='center', va='center', fontsize=8, fontweight='bold')
        # 連線到核心
        ax1.annotate('', xy=(5, 8.5), xytext=(x, y+0.4),
                    arrowprops=dict(arrowstyle='->', color='gray', lw=1, alpha=0.5))

    # 下遊整合
    integrators = [
        ('中研院物理所\n(量子位元研發)', 1.5, 2),
        ('工研院量子電腦實驗室\n(低溫量測)', 5, 2),
        ('鴻海/廣達/仁寶\n(系統整合)', 8.5, 2),
    ]

    for name, x, y in integrators:
        ax1.add_patch(Rectangle((x-1, y-0.4), 2, 0.8, fill=True, facecolor='#FFFACD', 
                                      edgecolor='#2C3E50', linewidth=1.5, linestyle='--'))
        ax1.text(x, y, name, ha='center', va='center', fontsize=8, fontweight='bold')
        ax1.annotate('', xy=(x, 2.4), xytext=(5, 8.5),
                    arrowprops=dict(arrowstyle='->', color='blue', lw=1.5, alpha=0.6, 
                                  connectionstyle="arc3,rad=0.2"))
    pyplot(fig)

#tight_layout(rect=[0, 0, 1, 0.95])
#savefig('/mnt/agents/output/taiwan_quantum_supply_chain.png', dpi=150, bbox_inches='tight')
#show()
print("台灣量子供應鏈分析圖已保存")
