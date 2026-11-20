from matplotlib.pyplot import Rectangle, savefig, show, subplots, tight_layout
from numpy import arange, linspace, pi
from streamlit import sidebar, radio, text_input, empty

import numpy as np
import matplotlib.pyplot as plt
from streamlit import pyplot

# 創建詳細的材料比較和優化方案分析
#fig, axes = plt.subplots(2, 2, figsize=(15, 12))
from streamlit import set_page_config
set_page_config(page_title='熱錨定', layout='wide', initial_sidebar_state='expanded')
MENU, 表單=[], ['熱阻網絡', '負載錨定', '相干時間', '混合架構']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  狀態=empty()
  狀態.code([])
if menu==len(表單): #
  pass
elif menu==MENU[3]: # 4. 推薦的混合方案架構 (右下)
    fig, ax4= subplots(figsize=(10, 6))
    #ax4 = axes[1, 1]
    ax4.set_xlim(0, 10)
    ax4.set_ylim(0, 10)
    ax4.axis('off')
    ax4.set_title('Recommended Hybrid Architecture', fontsize=12, fontweight='bold')

    # 繪制架構示意圖
    # 量子比特芯片
    rect_qubit = plt.Rectangle((1, 7), 2, 1.5, fill=True, facecolor='#E8F4FD', 
                               edgecolor='#2C3E50', linewidth=2)
    ax4.add_patch(rect_qubit)
    ax4.text(2, 7.75, 'Qubit Chip\n(10mK)', ha='center', va='center', fontsize=10, fontweight='bold')

    # 傳輸線
    rect_line = plt.Rectangle((3, 7.5), 3, 0.5, fill=True, facecolor='#45B7D1', 
                              edgecolor='#2C3E50', linewidth=1.5)
    ax4.add_patch(rect_line)
    ax4.text(4.5, 7.75, 'NbTi Cable', ha='center', va='center', fontsize=9, color='white', fontweight='bold')

    # 铟熱錨定
    rect_indium = plt.Rectangle((6, 7.2), 0.8, 1.1, fill=True, facecolor='#FFD700', 
                                edgecolor='#2C3E50', linewidth=1.5)
    ax4.add_patch(rect_indium)
    ax4.text(6.4, 7.75, 'In\nAnchor', ha='center', va='center', fontsize=8, fontweight='bold')

    # 環氧樹脂機械固定 (遠離量子比特)
    rect_epoxy = plt.Rectangle((7, 7.3), 1.5, 0.9, fill=True, facecolor='#FF6B6B', 
                               edgecolor='#2C3E50', linewidth=1.5, linestyle='--')
    ax4.add_patch(rect_epoxy)
    ax4.text(7.75, 7.75, 'Epoxy\nMechanical', ha='center', va='center', fontsize=8, fontweight='bold')

    # 連接器
    rect_conn = plt.Rectangle((8.5, 7.2), 1, 1.1, fill=True, facecolor='#C0C0C0', 
                              edgecolor='#2C3E50', linewidth=1.5)
    ax4.add_patch(rect_conn)
    ax4.text(9, 7.75, 'NbTi\nCoating\nConnector', ha='center', va='center', fontsize=8, fontweight='bold')

    # 熱屏蔽層
    for i, (temp, color, y) in enumerate([(50, '#FF9999', 5.5), (4, '#99CCFF', 4), (1, '#99FF99', 2.5)]):
        rect_shield = plt.Rectangle((0.5, y), 9, 0.8, fill=True, facecolor=color, 
                                    edgecolor='#2C3E50', linewidth=1, alpha=0.6)
        ax4.add_patch(rect_shield)
        ax4.text(5, y+0.4, f'Thermal Shield {temp}K', ha='center', va='center', 
                 fontsize=9, fontweight='bold')

    # 熱流箭頭
    ax4.annotate('', xy=(6.4, 7.2), xytext=(6.4, 6.3),
                arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax4.text(6.8, 6.7, 'Heat Flow\n→ 50K Stage', fontsize=8, color='red', fontweight='bold')

    # 微波信號
    ax4.annotate('', xy=(8.5, 7.75), xytext=(3, 7.75),
                arrowprops=dict(arrowstyle='->', color='blue', lw=2, linestyle='--'))
    ax4.text(5.5, 8.3, 'Microwave Signal', fontsize=9, color='blue', fontweight='bold', ha='center')

    # 關鍵參數標注
    info_text = """
    Key Design Parameters:
    • Qubit-to-epoxy distance: >5mm
    • Indium thermal anchor at 50K/4K stages
    • Epoxy: Stycast 1266 or 2850FT (mechanical only)
    • Minimize adhesive near qubit E-field
    • Vacuum gap or PTFE spacer at 10mK
    """
    ax4.text(5, 1.2, info_text, ha='center', va='center', fontsize=9,
            bbox=dict(boxstyle='round', facecolor='#FFFACD', edgecolor='#2C3E50', linewidth=1.5))
    pyplot(fig)
elif menu==MENU[2]: # 3. 量子比特相干時間限制分析 (左下)
    fig, ax3= subplots(figsize=(10, 6))
    #ax3 = axes[1, 0]

    # 不同黏著劑距離下的T1限制
    # 基于: 1/T1 = ω * p * tanδ + Γ_other
    # p = 參與比, 與幾何相關

    distances = np.linspace(0.5, 15, 200)  # mm
    omega = 2 * np.pi * 6e9  # 6 GHz

    # 不同黏著劑介電損耗
    tan_deltas = {
        'Stycast 2850FT (0.05)': 0.05,
        'Polyimide (0.008)': 0.008,
        'PTFE (0.0002)': 0.0002,
        'HR Silicon (1e-5)': 1e-5,
        'Ideal (1e-6)': 1e-6,
    }

    # 參與比模型: p = C * (w/d)^2, w=線寬, d=距離
    # 假設 w = 0.1mm
    def participation_ratio(d, w=0.1e-3):
        return 0.5 * (w/d)**2  # 簡化模型

    for label, tan_delta in tan_deltas.items():
        p = participation_ratio(distances * 1e-3)
        Gamma_adhesive = omega * p * tan_delta
        Gamma_total = Gamma_adhesive + 1/(15e-3)  # 其他損耗限制15ms
        T1 = 1 / Gamma_total * 1000  # ms
        
        linestyle = '-' if tan_delta > 0.001 else '--'
        linewidth = 2.5 if tan_delta > 0.001 else 2
        ax3.semilogy(distances, T1, linestyle, linewidth=linewidth, label=label)

    ax3.axhline(y=10, color='green', linestyle='--', alpha=0.7, linewidth=2)
    ax3.axhline(y=1, color='orange', linestyle='--', alpha=0.7, linewidth=2)
    ax3.axhline(y=0.1, color='red', linestyle='--', alpha=0.7, linewidth=2)

    ax3.fill_between(distances, 10, 100, alpha=0.15, color='green')
    ax3.fill_between(distances, 1, 10, alpha=0.15, color='yellow')
    ax3.fill_between(distances, 0.01, 1, alpha=0.15, color='red')

    ax3.set_xlabel('Qubit-to-Adhesive Distance (mm)', fontsize=11)
    ax3.set_ylabel('T₁ Coherence Time (ms)', fontsize=11)
    ax3.set_title('Qubit T₁ Limit vs Adhesive Distance\n(6 GHz Transmon)', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=8, loc='upper right')
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0.01, 100)

    # 添加區域標注
    ax3.text(12, 30, 'Excellent\n(>10ms)', fontsize=9, color='green', fontweight='bold', ha='center')
    ax3.text(12, 3, 'Marginal\n(1-10ms)', fontsize=9, color='orange', fontweight='bold', ha='center')
    ax3.text(12, 0.3, 'Poor\n(<1ms)', fontsize=9, color='red', fontweight='bold', ha='center')

    pyplot(fig)
elif menu==MENU[1]: # 2. 熱負載 vs 熱錨定效率 (右上)
    fig, ax2= subplots(figsize=(10, 6))
    #ax2 = axes[0, 1]

    stages = ['300K', '50K', '4K', '1K', '100mK', '10mK'] # 熱負載從300K到10mK的典型值
    stage_temps = [300, 50, 4, 1, 0.1, 0.01]

    # 不同方案的熱負載 (W)
    # 方案A: 純環氧樹脂連接
    heat_load_A = [1.0, 0.1, 0.01, 0.001, 5e-5, 1e-6]
    # 方案B: 铟焊料熱錨定 + 環氧樹脂機械固定
    heat_load_B = [0.8, 0.08, 0.008, 0.0008, 2e-5, 5e-7]
    # 方案C: 混合方案 (推薦)
    heat_load_C = [0.9, 0.09, 0.009, 0.0009, 3e-5, 8e-7]

    x = np.arange(len(stages))
    width = 0.25

    bars1 = ax2.bar(x - width, heat_load_A, width, label='Pure Epoxy', color='#FF6B6B', alpha=0.8)
    bars2 = ax2.bar(x, heat_load_B, width, label='Indium Thermal Anchor', color='#FFD700', alpha=0.8)
    bars3 = ax2.bar(x + width, heat_load_C, width, label='Hybrid (Recommended)', color='#4ECDC4', alpha=0.8)

    ax2.set_yscale('log')
    ax2.set_ylabel('Heat Load (W)', fontsize=11)
    ax2.set_title('Heat Load at Each Cooling Stage', fontsize=12, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(stages, fontsize=10)
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3, axis='y')

    # 添加10mK基線
    ax2.axhline(y=1e-6, color='red', linestyle='--', alpha=0.5, label='10mK limit')

    pyplot(fig)
elif menu==MENU[0]: #熱阻網絡 1. 熱阻網絡分析 (左上)
    fig, ax1= subplots(figsize=(10, 6))
    #ax1 = axes[0, 0]

    # 熱阻網絡示意圖 - 使用熱阻模型
    # R_th = L / (k * A)
    # 假設: 連接長度 L = 5mm, 截面積 A = 1mm²

    L = 5e-3  # m
    A = 1e-6  # m²

    # 不同材料的熱阻
    materials = {
        'Indium Solder': {'k': 80, 'color': '#FFD700', 'R': L/(80*A)/1e6},  # ~0.06 K/W (normalized)
        'Aluminum': {'k': 5000, 'color': '#C0C0C0', 'R': L/(5000*A)/1e6},
        'Stycast 2850FT': {'k': 0.03, 'color': '#FF6B6B', 'R': L/(0.03*A)/1e6},
        'PTFE': {'k': 0.2, 'color': '#4ECDC4', 'R': L/(0.2*A)/1e6},
        'NbTi (SC)': {'k': 0.1, 'color': '#45B7D1', 'R': L/(0.1*A)/1e6},
        'Vacuum Gap': {'k': 0.001, 'color': '#96CEB4', 'R': L/(0.001*A)/1e6},
    }

    names = list(materials.keys())
    R_values = [materials[m]['R'] for m in names]
    colors = [materials[m]['color'] for m in names]

    bars = ax1.barh(names, R_values, color=colors, edgecolor='black', alpha=0.8)
    ax1.set_xlabel('Normalized Thermal Resistance (relative units)', fontsize=11)
    ax1.set_title('Thermal Resistance Comparison\n(L=5mm, A=1mm²)', fontsize=12, fontweight='bold')
    ax1.set_xscale('log')
    ax1.grid(True, alpha=0.3, axis='x')

    # 添加數值標簽
    for bar, val in zip(bars, R_values):
        ax1.text(val*1.5, bar.get_y() + bar.get_height()/2, f'{val:.2f}', 
                 va='center', fontsize=9, fontweight='bold')
    fig.suptitle('NbTi Quantum Interconnect: Detailed Adhesive Optimization\n10K → 10mK Dilution Refrigerator', fontsize=14, fontweight='bold', y=0.98)
    pyplot(fig)


#plt.tight_layout(rect=[0, 0, 1, 0.95])
#plt.savefig('/mnt/agents/output/nbti_adhesive_detailed.png', dpi=150, bbox_inches='tight')
#plt.show()
#print("詳細分析圖表已保存")
