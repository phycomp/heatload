from matplotlib.pyplot import rcParams, savefig, show, subplots, tight_layout
from numpy import exp, linspace, ones_like, pi
import numpy as np
import matplotlib.pyplot as plt
from streamlit import sidebar, text_input, radio, empty, pyplot
# 設置中文字體
rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False
 #  # 4. 綜合優化雷達圖 (右下)# 3. 相干時間 vs 黏著劑距離 (左下) 2. 介電損耗正切 vs 頻率 (右上) # 1. 熱導率 vs 溫度 (左上) 熱導率vs溫度
# 創建綜合優化分析圖
fig, axes = subplots(2, 2, figsize=(14, 11))
fig.suptitle('NbTi Quantum Interconnect Adhesive Optimization\n10K ~ 10mK Cryogenic System', fontsize=14, fontweight='bold', y=0.98)
MENU, 表單=[], ['熱導率vs溫度', '正切vs頻率', '相干時間vs距離', '綜合分析']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  狀態=empty()
  狀態.code([])
if menu==len(表單): #
  pass
elif menu==MENU[3]:
    fig, ax4= subplots(figsize=(10, 6))
    #ax4 = axes[1, 1]

    categories = ['Thermal\nIsolation', 'Low\nDielectric\nLoss', 'Mechanical\nStrength', 'Outgassing\nControl', 'Thermal\nCycling\nResilience', 'Ease of\nApplication']
    N = len(categories)

    # 不同黏著劑方案評分 (1-10)
    indium = [3, 10, 9, 8, 7, 6]  # 铟焊料
    stycast = [8, 4, 7, 9, 8, 7]  # Stycast環氧樹脂
    ptfe = [9, 9, 4, 9, 6, 5]  # PTFE基
    hybrid = [7, 8, 8, 9, 8, 7]  # 混合方案

    angles = linspace(0, 2 * pi, N, endpoint=False).tolist()
    angles += angles[:1]

    for data, label, color, ls in [(indium, 'Indium Solder', 'gold', '-'), (stycast, 'Cryogenic Epoxy', 'red', '--'), (ptfe, 'PTFE-based', 'green', '-.'), (hybrid, 'Hybrid (Recommended)', 'blue', '-')]:
        data += data[:1]
        ax4.plot(angles, data, linewidth=2, label=label, color=color, linestyle=ls)
        ax4.fill(angles, data, alpha=0.1, color=color)

    ax4.set_xticks(angles[:-1])
    ax4.set_xticklabels(categories, fontsize=9)
    ax4.set_ylim(0, 10)
    ax4.set_title('Adhesive Solution Comparison\n(Radar Chart)', fontsize=12, fontweight='bold')
    ax4.legend(fontsize=9, loc='upper right', bbox_to_anchor=(1.3, 1.1))
    ax4.grid(True)
    ax4.set_yticks([2, 4, 6, 8, 10])
    pyplot(fig)
elif menu==MENU[2]:
    fig, ax3= subplots(figsize=(10, 6))
    #ax3 = axes[1, 0]
    distance = linspace(0.5, 10, 200)  # mm

    # 基于參與比方法的T1限制
    # 1/T1 = ω * p_abs * tanδ_abs + Γ0
    omega = 2 * pi * 6e9  # 6 GHz transmon
    p_abs = 0.1 / (distance**2)  # 參與比隨距離平方衰減 (簡化模型)
    tan_delta = 0.05  # Stycast upper bound
    Gamma0 = 1/(10e-3)  # 其他損耗限制 10 ms

    T1_limit = 1 / (omega * p_abs * tan_delta + Gamma0) * 1000  # ms

    ax3.plot(distance, T1_limit, 'b-', linewidth=2.5)
    ax3.axhline(y=10, color='green', linestyle='--', alpha=0.7, label='Target T₁ > 10 ms')
    ax3.axvline(x=4, color='red', linestyle='--', alpha=0.7, label='Min. safe distance 4mm')
    ax3.fill_between(distance, 0, 10, alpha=0.2, color='red', label='Unacceptable region')
    ax3.fill_between(distance, 10, 50, alpha=0.2, color='green', label='Acceptable region')
    ax3.set_xlabel('Qubit-to-Adhesive Distance (mm)', fontsize=11)
    ax3.set_ylabel('Coherence Time T₁ (ms)', fontsize=11)
    ax3.set_title('Qubit Coherence Time vs Adhesive Distance\n(Stycast tanδ = 0.05)', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=9, loc='lower right')
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0, 50)
    pyplot(fig)
elif menu==MENU[1]:
    fig, ax2= subplots(figsize=(10, 6))
    #ax2 = axes[0, 1]
    freq = linspace(1, 10, 100)  # GHz

    # 不同材料的介電損耗正切
    tan_delta_stycast = .05 * ones_like(freq)  # Stycast IR absorber upper bound
    tan_delta_ptfe = .0002 * ones_like(freq)  # PTFE
    tan_delta_silicon = .00001 * ones_like(freq)  # High-resistivity Si
    tan_delta_polyimide = .008 * ones_like(freq)  # Polyimide

    ax2.semilogy(freq, tan_delta_stycast, 'r-', linewidth=2.5, label='Stycast Epoxy (0.05)')
    ax2.semilogy(freq, tan_delta_polyimide, 'orange', linewidth=2, label='Polyimide (0.008)')
    ax2.semilogy(freq, tan_delta_ptfe, 'g-', linewidth=2, label='PTFE (0.0002)')
    ax2.semilogy(freq, tan_delta_silicon, 'b-', linewidth=2, label='HR Silicon (1e-5)')
    ax2.axhline(y=1e-4, color='gray', linestyle='--', alpha=0.5, label='Target < 1e-4')
    ax2.set_xlabel('Frequency (GHz)', fontsize=11)
    ax2.set_ylabel('Dielectric Loss Tangent (tan δ)', fontsize=11)
    ax2.set_title('Dielectric Loss Tangent vs Frequency', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=9, loc='upper right')
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(1e-6, 0.1)
    pyplot(fig)
elif menu==MENU[0]:
    fig, ax1= subplots(figsize=(10, 6))
    #ax1 = axes[0, 0]
    T = linspace(0.01, 10, 500)  # K

    # 不同材料的熱導率近似數據
    # NbTi 超導體 (超導態)
    k_nbti_sc = 0.1 + 0.4 * exp(-T/2)  # W/mK, 超導態下極低
    # 典型低溫環氧樹脂 (Stycast 2850FT)
    k_epoxy = 0.01 + 0.05 * exp(-T/1.5)  # W/mK
    # 铟焊料
    k_indium = 80 * (T/10)**1.5  # W/mK (低溫下仍較高)
    # 鋁
    k_al = 5000 * (T/10)**2.5  # W/mK

    ax1.semilogy(T, k_nbti_sc, 'b-', linewidth=2.5, label='NbTi (Superconducting)')
    ax1.semilogy(T, k_epoxy, 'r--', linewidth=2.5, label='Cryogenic Epoxy')
    ax1.semilogy(T, k_indium, 'g-.', linewidth=2, label='Indium Solder')
    ax1.semilogy(T, k_al, 'm:', linewidth=2, label='Aluminum')
    ax1.axvline(x=0.01, color='gray', linestyle='--', alpha=0.5)
    ax1.axvline(x=9.3, color='blue', linestyle='--', alpha=0.3, label='NbTi Tc ≈ 9.3K')
    ax1.set_xlabel('Temperature (K)', fontsize=11)
    ax1.set_ylabel('Thermal Conductivity (W/m·K)', fontsize=11)
    ax1.set_title('Thermal Conductivity vs Temperature', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=9, loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0.01, 10)
    pyplot(fig)

#tight_layout(rect=[0, 0, 1, 0.95])
#savefig('/mnt/agents/output/nbti_adhesive_optimization.png', dpi=150, bbox_inches='tight')
#show()
print("圖表已保存")
