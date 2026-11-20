from streamlit import sidebar, radio, text_input, pyplot
from matplotlib.pyplot import figure, savefig, show, tight_layout
from numpy import array, concatenate, exp, linspace
#import numpy as np
#import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.gridspec as gridspec
from matplotlib.pyplot import rcParams, savefig, show, subplots, tight_layout

# ============================
# 熱力學計算函數
# ============================
def thermal_population(E, T):
    if T <= 0:
        return 0.0
    return exp(-E / (k_B * T))

def thermal_photon_number(f, T):
    if T <= 0:
        return 0.0
    x = h * f / (k_B * T)
    if x > 50:
        return 0.0
    return 1.0 / (exp(x) - 1.0)

with sidebar:
    # ============================
    # 物理常數與參數
    # ============================
    h = 6.626e-34
    k_B = 1.381e-23
    c = 3.0e8

    # Transmon 參數
    f01 = 5.5e9
    alpha = -250e6
    E01 = h * f01
    E12 = h * (f01 + abs(alpha))

    # 退相干閾值
    threshold_pop = 0.01
    threshold_n_th = 0.01

    # Delft cri/oFlex3 規格
    T_cold = 0.010
    T_hot = 0.350
    L_given = 0.20

    T_range = linspace(0.005, 0.400, 1000) # 計算臨界溫度
    pop_1 = array([thermal_population(E01, T) for T in T_range])
    n_th = array([thermal_photon_number(f01, T) for T in T_range])

    T_critical_pop = None
    T_critical_n_th = None
    for i, T in enumerate(T_range):
        if pop_1[i] > threshold_pop and T_critical_pop is None:
            T_critical_pop = T
        if n_th[i] > threshold_n_th and T_critical_n_th is None:
            T_critical_n_th = T

    T_crit = T_critical_pop

    # ============================
    # 回推計算
    # ============================
    L_safe = L_given * (T_crit - T_cold) / (T_hot - T_cold)#安全區域長度 (線性溫度分布)
    L_extended = 5.0 * (T_hot - T_cold) / (T_crit - T_cold)#延長傳輸線長度 (要求 5cm 安全區)
    L_anchor = 10.0 # 熱化錨點方案
from streamlit import empty
MENU, 表單=[], ['圖表能級', '熱佔據率vs溫度', '傳輸線溫度分布示意圖', '回推傳輸線長度比較', '回推推導流程圖']		#', '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
狀態=empty()
if menu==len(表單): #
  pass
elif menu==MENU[4]: #
    fig, ax4= subplots(figsize=(10, 6))
    # --- 子圖 5: 回推推導流程圖 ---
    #ax4 = fig.add_subplot(gs[2, :])
    ax4.set_xlim(0, 10)
    ax4.set_ylim(0, 10)
    ax4.axis('off')
    ax4.set_title('Back-Calculation Derivation Flowchart', fontsize=14, fontweight='bold', pad=10)

    # 繪製流程圖框
    boxes = [
        {'pos': (0.5, 7.5), 'size': (2.2, 1.5), 'text': 'Delft cri/oFlex3\nSpec: 10mK→350mK\nL = 20 cm', 'color': '#ffcccc'},
        {'pos': (3.5, 7.5), 'size': (2.2, 1.5), 'text': 'Transmon Params\n$f_{01} = 5.5 GHz$\nα = -250 MHz', 'color': '#ccccff'},
        {'pos': (6.5, 7.5), 'size': (2.2, 1.5), 'text': 'Decoherence\nThreshold\nP < 1%, n_th < 0.01', 'color': '#ccffcc'},
        {'pos': (1.5, 4.5), 'size': (2.5, 1.5), 'text': f'Thermal Population\nP = exp(-hf01/k_BT)\n→ T_crit = {T_crit*1000:.1f} mK', 'color': '#ffe6cc'},
        {'pos': (5.5, 4.5), 'size': (2.5, 1.5), 'text': 'Linear T Profile\nT(x) = 10 + 340·x/20\nSafe zone: x < 2.8 cm', 'color': '#e6ffcc'},
        {'pos': (3.5, 1.5), 'size': (3.0, 1.5), 'text': f'Back-Calculated Lengths\n• Extended: ~{L_extended:.1f} cm (lower gradient)\n• Thermal Anchor: ~{L_anchor:.0f} cm (mid-cooling)\n• Max safe: {L_safe*100:.1f} cm (no mitigation)', 'color': '#ccffff'},
    ]

    for box in boxes:
        x, y = box['pos']
        w, h = box['size']
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1", 
                              facecolor=box['color'], edgecolor='black', linewidth=2, alpha=0.8)
        ax4.add_patch(rect)
        ax4.text(x + w/2, y + h/2, box['text'], fontsize=10, ha='center', va='center', 
                 fontweight='bold', wrap=True)

    # 繪製箭頭
    arrow_props = dict(arrowstyle='->', color='black', lw=2)
    ax4.annotate('', xy=(3.5, 8.25), xytext=(2.7, 8.25), arrowprops=arrow_props)
    ax4.annotate('', xy=(6.5, 8.25), xytext=(5.7, 8.25), arrowprops=arrow_props)
    ax4.annotate('', xy=(7.6, 6.0), xytext=(7.6, 7.5), arrowprops=arrow_props)
    ax4.annotate('', xy=(6.5, 5.25), xytext=(7.6, 6.0), arrowprops=dict(arrowstyle='->', color='black', lw=2, connectionstyle="arc3,rad=0.3"))
    ax4.annotate('', xy=(2.75, 6.0), xytext=(2.75, 7.5), arrowprops=arrow_props)
    ax4.annotate('', xy=(3.5, 3.0), xytext=(2.75, 4.5), arrowprops=arrow_props)
    ax4.annotate('', xy=(5.0, 3.0), xytext=(5.0, 4.5), arrowprops=arrow_props)

    # 添加公式
    ax4.text(5, 0.3, 
             r'$P_{|1\rangle} = \exp\left(-\frac{hf_{01}}{k_B T}\right) < 0.01 \Rightarrow T_{crit} = \frac{hf_{01}}{k_B \ln(100)} \approx 57.6$ mK' + '\n' +
             r'$L_{safe} = L_{given} \times \frac{T_{crit} - T_{cold}}{T_{hot} - T_{cold}} = 20 \times \frac{47.6}{340} \approx 2.8$ cm',
             fontsize=11, ha='center', va='bottom', style='italic',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.5, edgecolor='gray'))

    #tight_layout()
    #savefig('/mnt/agents/output/qubit_temperature_backcalculation.png', dpi=200, bbox_inches='tight')
    #show()

    #輸出+="✅ 示意圖已儲存"
    輸出=f"\n關鍵數值:"
    輸出+=f"  T_crit = {T_crit*1000:.1f} mK"
    輸出+=f"  L_safe (原始 20cm) = {L_safe*100:.1f} cm"
    輸出+=f"  L_extended (5cm 安全區) = {L_extended:.1f} cm"
    狀態.code(輸出)
    pyplot(fig)
elif menu==MENU[3]: #
    fig, ax3= subplots(figsize=(10, 6))
    # --- 子圖 4: 回推傳輸線長度比較 ---
    #ax3 = fig.add_subplot(gs[1, 1])

    # 三種方案的溫度分布
    x_orig = linspace(0, 20, 200)
    T_orig = 10 + 340 * x_orig / 20

    x_ext = linspace(0, L_extended, 200)
    T_ext = 10 + 340 * x_ext / L_extended

    # 熱化錨點方案
    L_anch = 10.0
    x_anch1 = linspace(0, L_anch/2, 100)
    T_anch1 = 350 - 270 * x_anch1 / (L_anch/2)
    x_anch2 = linspace(L_anch/2, L_anch, 100)
    T_anch2 = 80 - 70 * (x_anch2 - L_anch/2) / (L_anch/2)

    ax3.plot(x_orig, T_orig, color='#e74c3c', linewidth=3, label=f'cri/oFlex3 (20 cm)')
    ax3.plot(x_ext, T_ext, color='#3498db', linewidth=3, linestyle='--', label=f'Extended ({L_extended:.1f} cm)')
    ax3.plot(concatenate([x_anch1, x_anch2]), concatenate([T_anch1, T_anch2]), 
             color='#2ecc71', linewidth=3, linestyle='-.', label=f'Thermal Anchor ({L_anch:.0f} cm)')

    ax3.axhline(y=T_crit*1000, color='green', linestyle='--', linewidth=2.5, alpha=0.8, label=f'$T_{{crit}}$ = {T_crit*1000:.1f} mK')

    # 量子比特位置
    ax3.scatter([0], [10], color='blue', s=200, zorder=5, marker='o', edgecolors='white', linewidth=2)
    ax3.annotate('Qubit', xy=(0, 10), xytext=(-1, 40), fontsize=10, color='blue', fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color='blue'))

    ax3.set_xlabel('Distance from Qubit (cm)', fontsize=12)
    ax3.set_ylabel('Temperature (mK)', fontsize=12)
    ax3.set_title('Back-Calculated Transmission Line Lengths\nfor Transmon Decoherence Avoidance', 
                  fontsize=13, fontweight='bold')
    ax3.legend(fontsize=9, loc='upper left')
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim([-2, 40])
    ax3.set_ylim([0, 400])

    # 添加方案說明
    ax3.text(0.98, 0.95, 
             'Extended: Lower gradient\n→ larger safe zone\n\nThermal Anchor:\nMid-point forced\nthermalization', 
             transform=ax3.transAxes, fontsize=9, ha='right', va='top',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow', alpha=0.6, edgecolor='gray'))

    pyplot(fig)
elif menu==MENU[2]: #
    fig, ax2= subplots(figsize=(10, 6))
    # --- 子圖 3: 傳輸線溫度分布示意圖 (cri/oFlex3 原始) ---
    #ax2 = fig.add_subplot(gs[1, 0])

    # 原始 20cm 傳輸線
    line_width = 20
    x_line = linspace(0, line_width, 200)
    T_line = 10 + (350 - 10) * x_line / line_width

    # 繪製溫度分布
    ax2.fill_between(x_line, 0, T_line, alpha=0.3, color='orange')
    ax2.plot(x_line, T_line, 'darkorange', linewidth=3, label='Temperature profile (linear)')

    # 臨界溫度線
    ax2.axhline(y=T_crit*1000, color='green', linestyle='--', linewidth=2.5, alpha=0.8, label=f'$T_{{crit}}$ = {T_crit*1000:.1f} mK')

    # 安全區域標註
    x_safe_end = line_width * (T_crit*1000 - 10) / (350 - 10)
    ax2.axvline(x=x_safe_end, color='green', linestyle=':', linewidth=2, alpha=0.7)
    ax2.fill_between([0, x_safe_end], 0, T_crit*1000, alpha=0.2, color='green')
    ax2.fill_between([x_safe_end, line_width], 0, 400, alpha=0.1, color='red')

    # 量子比特位置
    ax2.scatter([0], [10], color='blue', s=200, zorder=5, marker='o', edgecolors='white', linewidth=2)
    ax2.annotate('Qubit\n(10 mK)', xy=(0, 10), xytext=(-2, 50), fontsize=10, color='blue', 
                 fontweight='bold', ha='center',
                 arrowprops=dict(arrowstyle='->', color='blue', lw=1.5))

    # 熱端位置
    ax2.scatter([line_width], [350], color='red', s=200, zorder=5, marker='s', edgecolors='white', linewidth=2)
    ax2.annotate('Hot end\n(350 mK)', xy=(line_width, 350), xytext=(line_width+1, 300), fontsize=10, 
                 color='red', fontweight='bold', ha='left',
                 arrowprops=dict(arrowstyle='->', color='red', lw=1.5))

    # 安全區域標註
    ax2.annotate(f'Safe zone\n~{x_safe_end:.1f} cm', xy=(x_safe_end/2, T_crit*1000/2), fontsize=11, 
                 color='green', fontweight='bold', ha='center', va='center',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.4, edgecolor='green'))

    ax2.annotate(f'Decoherence\nrisk zone\n~{line_width - x_safe_end:.1f} cm', xy=(x_safe_end + (line_width-x_safe_end)/2, 200), 
                 fontsize=11, color='darkred', fontweight='bold', ha='center', va='center',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='lightsalmon', alpha=0.4, edgecolor='red'))

    ax2.set_xlabel('Distance from Qubit (cm)', fontsize=12)
    ax2.set_ylabel('Temperature (mK)', fontsize=12)
    ax2.set_title(f'cri/oFlex3 Original Design (L = {line_width:.0f} cm)\nLinear Temperature Profile', 
                  fontsize=13, fontweight='bold')
    ax2.legend(fontsize=9, loc='upper left')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim([-3, 25])
    ax2.set_ylim([0, 400])

    pyplot(fig)
elif menu==MENU[1]: #
    fig, ax1= subplots(figsize=(10, 6))
    # --- 子圖 2: 熱佔據率 vs 溫度 (關鍵區域放大) ---
    #ax1 = fig.add_subplot(gs[0, 1])
    T_zoom = linspace(0.010, 0.120, 500)
    pop_1_zoom = array([thermal_population(E01, T) for T in T_zoom])
    n_th_zoom = array([thermal_photon_number(f01, T) for T in T_zoom])

    ax1.semilogy(T_zoom * 1000, pop_1_zoom, 'b-', linewidth=2.5, label='$|1\\rangle$ population')
    ax1.semilogy(T_zoom * 1000, n_th_zoom, 'purple', linewidth=2, linestyle='--', label='$n_{th}$')
    ax1.axhline(y=0.01, color='red', linestyle=':', linewidth=2, label='1% / $n_{th}$=0.01 threshold')
    ax1.axvline(x=T_crit*1000, color='green', linestyle='--', alpha=0.8, linewidth=2.5)

    # 填充安全區和風險區
    ax1.fill_between(T_zoom * 1000, 1e-8, 0.01, where=(T_zoom * 1000 < T_crit*1000), 
                     alpha=0.15, color='green', label='Safe zone (T < T_crit)')
    ax1.fill_between(T_zoom * 1000, 1e-8, 0.01, where=(T_zoom * 1000 >= T_crit*1000), 
                     alpha=0.15, color='red', label='Decoherence risk (T > T_crit)')

    ax1.set_xlabel('Temperature (mK)', fontsize=12)
    ax1.set_ylabel('Thermal Population / Photon Number', fontsize=12)
    ax1.set_title(f'Critical Temperature Determination\n($f_{{01}}$ = {f01/1e9:.1f} GHz, $T_{{crit}}$ = {T_crit*1000:.1f} mK)', 
                  fontsize=13, fontweight='bold')
    ax1.legend(fontsize=9, loc='lower right')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([10, 120])
    ax1.set_ylim([1e-8, 0.5])

    ax1.annotate(f'$T_{{crit}}$ = {T_crit*1000:.1f} mK', xy=(T_crit*1000, 0.01), xytext=(T_crit*1000 + 15, 0.03),
                fontsize=11, color='green', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='green', lw=1.5))

    pyplot(fig)
elif menu==MENU[0]: #
    fig, ax0= subplots(figsize=(10, 6))
    # ============================
    # 創建圖表
    # ============================
    #fig = figure(figsize=(18, 14))
    #gs = gridspec.GridSpec(3, 2, height_ratios=[1, 1.2, 1], hspace=0.35, wspace=0.3)

    # --- 子圖 1: Transmon 能級圖 ---
    #ax0 = fig.add_subplot(gs[0, 0])
    ax0.set_xlim(-0.5, 5)
    ax0.set_ylim(-0.3, 6.5)
    ax0.axis('off')
    ax0.set_title('Transmon Energy Level Diagram', fontsize=14, fontweight='bold', pad=10)

    levels_y = [0, 5.5, 5.75] # 能級線
    labels_level = ['|0〉', '|1〉', '|2〉']
    colors_level = ['#1a5276', '#922b21', '#b9770e']
    energy_labels = ['$E_0 = 0$', '$E1 = hf_{01}$', '$E2 = h(2f_{01} + α)$']

    for i, (y, label, color, elabel) in enumerate(zip(levels_y, labels_level, colors_level, energy_labels)):
        ax0.hlines(y, 0.5, 3.5, colors=color, linewidth=4, alpha=0.8)
        ax0.text(3.7, y, f'{label}   {elabel}', fontsize=12, va='center', color=color, fontweight='bold')

    ax0.annotate('', xy=(1.5, 5.5), xytext=(1.5, 0), arrowprops=dict(arrowstyle='<->', color='#1a5276', lw=2.5)) # 躍遷箭頭
    ax0.text(1.7, 2.75, f'f01 = {f01/1e9:.1f} GHz\n$E01/k_B$ = {h*f01/k_B*1000:.0f} mK', fontsize=10, color='#1a5276', rotation=90, va='center', fontweight='bold')

    ax0.annotate('', xy=(2.5, 5.75), xytext=(2.5, 5.5), arrowprops=dict(arrowstyle='<->', color='#922b21', lw=2.5))
    ax0.text(2.7, 5.625, f'α = {alpha/1e6:.0f} MHz\n(Anharmonicity)', fontsize=10, color='#922b21', rotation=90, va='center', fontweight='bold')

    ax0.text(2, -0.15, 'Weakly-anharmonic oscillator (Transmon)', fontsize=11, ha='center', style='italic', color='#555')

    ax0.text(0.1, 6.2, f'T_crit = {T_crit*1000:.1f} mK\n(thermal pop < 1%)', fontsize=10, color='green', fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.3, edgecolor='green')) # 添加臨界溫度標註
    pyplot(fig)

