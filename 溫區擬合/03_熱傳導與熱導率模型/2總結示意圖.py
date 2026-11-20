from matplotlib.pyplot import Circle, figure, savefig, show
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from matplotlib.pyplot import rcParams, savefig, show, subplots, tight_layout
from streamlit import pyplot, sidebar, text_input, radio, empty
from fontUtil2 import 配置中文
配置中文()
# ============================================================
# 建立完整物理推導與示意圖
# ============================================================
MENU, 表單=[], ['定義', '核心', '同軸線', '公式推導', 'CuNi', '鋁覆', '熱輻射', '等效熱阻', '完整', '總結']#['定義', '', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
fig = figure(figsize=(20, 28))
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  狀態=empty()
  狀態.code([])
if menu==len(表單): #
  pass
elif menu==MENU[9]: #定義
    # ============================================================
    # 區塊 10: 底部總結
    # ============================================================
    ax_sum = fig.add_axes([0.05, 0.02, 0.9, 0.10])
    ax_sum.set_xlim(0, 10)
    ax_sum.set_ylim(0, 10)
    ax_sum.axis('off')

    ax_sum.text(5, 9, '✅ 總結：修正後的物理模型', ha='center', va='top', fontsize=14, fontweight='bold')

    summary_text = """
    1. "per channel" = 整個同軸通道 (中心導體 + 外屏蔽層)，總截面積約為單根線的 3-20 倍
    2. CuNi 取代 Ag：相同熱負載下長度需增加 ~33 倍 (ρ_CuNi/ρ_Ag ≈ 32.7)
    3. Al Shielding：提供並聯熱傳導路徑，長度約為信號線的 10 倍 (因 ρ_Al << ρ_Ag)
    4. 熱輻射：300K→50K 段不可忽略 (≈ 2.6 mW)，需多層 shield (MLI) 抑制
    5. 等效熱阻長度：4K 以下 NbTi 的「線長」實為等效正常態熱阻，非實體線長
    """

    ax_sum.text(5, 4.5, summary_text, ha='center', va='center', fontsize=10, transform=ax_sum.transAxes, family='monospace', bbox=dict(boxstyle='round', facecolor='#E8F5E9', edgecolor='#4CAF50', linewidth=2))
    pyplot(fig)
elif menu==MENU[8]:
    # ============================================================
    # 區塊 9: 完整計算範例
    # ============================================================
    ax_ex = fig.add_axes([0.52, 0.14, 0.44, 0.20])
    #fig, ax4= subplots(figsize=(10, 6))
    ax_ex.set_xlim(0, 10)
    ax_ex.set_ylim(0, 10)
    ax_ex.axis('off')
    ax_ex.set_facecolor('#FFFAF0')

    rect = FancyBboxPatch((0.2, 0.3), 9.6, 9.4, boxstyle="round,pad=0.3", facecolor='#FFFAF0', edgecolor='#D2691E', linewidth=2)
    ax_ex.add_patch(rect)

    ax_ex.text(5, 9.2, '📊 完整計算範例：300K → 50K 段', ha='center', va='top', fontsize=14, fontweight='bold')

    y_pos = 8.2

    ax_ex.text(0.5, y_pos, '已知：', fontsize=11, fontweight='bold')
    y_pos -= 0.6
    ax_ex.text(0.5, y_pos, '   Q = 2.7 mW/CH, Tₕ = 300K, Tc = 50K', fontsize=10)
    y_pos -= 0.5
    ax_ex.text(0.5, y_pos, '   Channel: 中心 AWG36 + 外屏蔽 (總 A = 0.063 mm²)', fontsize=10)
    y_pos -= 0.5
    ax_ex.text(0.5, y_pos, '   ρ_Ag = 1.6×10⁻⁸ Ω·m, L₀ = 2.45×10⁻⁸ W·Ω/K²', fontsize=10)

    y_pos -= 0.9
    ax_ex.text(0.5, y_pos, '計算：', fontsize=11, fontweight='bold')
    y_pos -= 0.7
    ax_ex.text(0.5, y_pos, '   L = 2.45×10⁻⁸ × 0.063×10⁻⁶ × (300²-50²)', fontsize=9, family='monospace')
    y_pos -= 0.5
    ax_ex.text(0.5, y_pos, '       ───────────────────────────────────────', fontsize=9, family='monospace')
    y_pos -= 0.5
    ax_ex.text(0.5, y_pos, '            2 × 2.7×10⁻³ × 1.6×10⁻⁸', fontsize=9, family='monospace')
    y_pos -= 0.6
    ax_ex.text(0.5, y_pos, '   L = 1.57 m', fontsize=11, family='monospace', color='#CC0000', fontweight='bold')

    y_pos -= 0.9
    ax_ex.text(0.5, y_pos, '驗證：', fontsize=11, fontweight='bold')
    y_pos -= 0.6
    ax_ex.text(0.5, y_pos, '   若用單根 AWG36 (A=0.0127 mm²):', fontsize=10)
    y_pos -= 0.5
    ax_ex.text(0.5, y_pos, '   L = 0.31 m = 31 cm ❌ (過短)', fontsize=10, color='red')
    y_pos -= 0.6
    ax_ex.text(0.5, y_pos, '   用 Channel 總截面積:', fontsize=10)
    y_pos -= 0.5
    ax_ex.text(0.5, y_pos, '   L = 1.57 m ✅ (合理)', fontsize=10, color='green')
    pyplot(fig)

elif menu==MENU[7]:
    # ============================================================
    # 區塊 8: 等效熱阻長度概念
    # ============================================================
    #fig, ax4= subplots(figsize=(10, 6))
    ax_therm = fig.add_axes([0.03, 0.14, 0.44, 0.20])
    ax_therm.set_xlim(0, 10)
    ax_therm.set_ylim(0, 10)
    ax_therm.axis('off')
    ax_therm.set_facecolor('#F8F8FF')

    rect = FancyBboxPatch((0.2, 0.3), 9.6, 9.4, boxstyle="round,pad=0.3", 
                           facecolor='#F8F8FF', edgecolor='#483D8B', linewidth=2)
    ax_therm.add_patch(rect)

    ax_therm.text(5, 9.2, '🔥 等效熱阻長度概念', ha='center', va='top', fontsize=14, fontweight='bold')

    y_pos = 8.2

    ax_therm.text(0.5, y_pos, '問題：4K 以下 NbTi 段計算長度僅數毫米，是否合理？', fontsize=11, fontweight='bold', color='#CC0000')
    y_pos -= 0.8

    ax_therm.text(0.5, y_pos, '實際稀釋製冷機結構：', fontsize=11, fontweight='bold')
    y_pos -= 0.6
    ax_therm.text(0.5, y_pos, '   4K Plate ──[2cm NbTi帶]── Still (0.6K)', fontsize=10, family='monospace')
    y_pos -= 0.5
    ax_therm.text(0.5, y_pos, '   Still ──[1cm NbTi帶]── Cold Plate (100mK)', fontsize=10, family='monospace')
    y_pos -= 0.5
    ax_therm.text(0.5, y_pos, '   Cold Plate ──[1cm NbTi帶]── Mixing Chamber (10mK)', fontsize=10, family='monospace')

    y_pos -= 0.9
    ax_therm.text(0.5, y_pos, '解釋：', fontsize=11, fontweight='bold')
    y_pos -= 0.7
    ax_therm.text(0.5, y_pos, '   1. NbTi 在 <9.2K 為超導態，直流電阻為零', fontsize=10)
    y_pos -= 0.6
    ax_therm.text(0.5, y_pos, '   2. 熱負載來自「正常態區域」(接頭、電流超過 Jc)', fontsize=10)
    y_pos -= 0.6
    ax_therm.text(0.5, y_pos, '   3. 圖中 NbTi 熱負載實際來自「銅穩定層」', fontsize=10)

    y_pos -= 0.9
    ax_therm.text(0.5, y_pos, '等效熱阻長度定義：', fontsize=11, fontweight='bold')
    y_pos -= 0.7
    ax_therm.text(0.5, y_pos, '   L_eff = L₀ · A · (Tₕ²-Tc²) / (2 · Q · ρ_eff)', fontsize=10, family='monospace')
    y_pos -= 0.6
    ax_therm.text(0.5, y_pos, '   其中 ρ_eff 為「等效正常態電阻率」', fontsize=10)
    y_pos -= 0.6
    ax_therm.text(0.5, y_pos, '   包含：基體銅電阻 + 接頭電阻 + 磁通流動電阻', fontsize=10)
    pyplot(fig)

elif menu==MENU[6]:
    # ============================================================
    # 區塊 7: 熱輻射計算 (Stefan-Boltzmann)
    # ============================================================
    #fig, ax4= subplots(figsize=(10, 6))
    ax_rad = fig.add_axes([0.52, 0.36, 0.44, 0.20])
    ax_rad.set_xlim(0, 10)
    ax_rad.set_ylim(0, 10)
    ax_rad.axis('off')
    ax_rad.set_facecolor('#FFF5EE')

    rect = FancyBboxPatch((0.2, 0.3), 9.6, 9.4, boxstyle="round,pad=0.3", 
                           facecolor='#FFF5EE', edgecolor='#FF6347', linewidth=2)
    ax_rad.add_patch(rect)

    ax_rad.text(5, 9.2, '☀️ 熱輻射計算 (Stefan-Boltzmann)', ha='center', va='top', fontsize=14, fontweight='bold')

    y_pos = 8.2

    ax_rad.text(0.5, y_pos, '兩平行表面間的淨輻射熱流：', fontsize=11, fontweight='bold')
    y_pos -= 0.7
    ax_rad.text(0.5, y_pos, '   Q_rad = ε · σ · A_surf · (Tₕ⁴ - Tc⁴)', fontsize=11, family='monospace', color='#CC0000')

    y_pos -= 0.9
    ax_rad.text(0.5, y_pos, '參數：', fontsize=11, fontweight='bold')
    y_pos -= 0.6
    ax_rad.text(0.5, y_pos, '   • σ = 5.67×10⁻⁸ W/m²/K⁴ (Stefan-Boltzmann 常數)', fontsize=10)
    y_pos -= 0.6
    ax_rad.text(0.5, y_pos, '   • ε = 0.03 (拋光 Aluminum 發射率)', fontsize=10)
    y_pos -= 0.6
    ax_rad.text(0.5, y_pos, '   • A_surf = π · D · L (圓柱側面積)', fontsize=10)

    y_pos -= 0.9
    ax_rad.text(0.5, y_pos, '300K → 50K 段輻射熱負載估算：', fontsize=11, fontweight='bold')
    y_pos -= 0.7
    ax_rad.text(0.5, y_pos, '   Q_rad = 0.03 × 5.67×10⁻⁸ × π×0.002×0.3 × (300⁴-50⁴)', fontsize=9, family='monospace')
    y_pos -= 0.6
    ax_rad.text(0.5, y_pos, '         ≈ 2.6 mW', fontsize=10, family='monospace', color='#CC0000', fontweight='bold')

    y_pos -= 0.9
    ax_rad.text(0.5, y_pos, '關鍵發現：', fontsize=11, fontweight='bold')
    y_pos -= 0.7
    ax_rad.text(0.5, y_pos, '   • 300K→50K 段：輻射熱負載 ≈ 傳導熱負載 (2.7 mW)', fontsize=10, color='#CC6600')
    y_pos -= 0.6
    ax_rad.text(0.5, y_pos, '   • 50K→4K 段：輻射僅 ~0.01 mW，可忽略', fontsize=10)
    y_pos -= 0.6
    ax_rad.text(0.5, y_pos, '   • 多層 shield (MLI) 可將輻射降低 10⁻³~10⁻⁴', fontsize=10)
    pyplot(fig)

elif menu==MENU[5]:
    # ============================================================
    # 區塊 6: Aluminum Shielding 熱傳導分流
    # ============================================================
    #fig, ax4= subplots(figsize=(10, 6))
    ax_al = fig.add_axes([0.03, 0.36, 0.44, 0.20])
    ax_al.set_xlim(0, 10)
    ax_al.set_ylim(0, 10)
    ax_al.axis('off')
    ax_al.set_facecolor('#F0FFF0')

    rect = FancyBboxPatch((0.2, 0.3), 9.6, 9.4, boxstyle="round,pad=0.3", 
                           facecolor='#F0FFF0', edgecolor='#228B22', linewidth=2)
    ax_al.add_patch(rect)

    ax_al.text(5, 9.2, '🛡️ Aluminum Shielding 熱傳導分流', ha='center', va='top', fontsize=14, fontweight='bold')

    y_pos = 8.2

    ax_al.text(0.5, y_pos, '模型：Shield 與 Signal Line 並聯', fontsize=11, fontweight='bold')
    y_pos -= 0.7

    # 並聯示意
    ax_al.text(0.5, y_pos, '        ┌─── Signal Line (Ag/CuNi) ───┐', fontsize=9, family='monospace')
    y_pos -= 0.5
    ax_al.text(0.5, y_pos, '   Tₕ ──┤                              ├── Tc', fontsize=9, family='monospace')
    y_pos -= 0.5
    ax_al.text(0.5, y_pos, '        └─── Al Shield ──────────────┘', fontsize=9, family='monospace')

    y_pos -= 0.9
    ax_al.text(0.5, y_pos, '並聯熱阻公式：', fontsize=11, fontweight='bold')
    y_pos -= 0.7
    ax_al.text(0.5, y_pos, '   1/R_total = 1/R_wire + 1/R_shield', fontsize=10, family='monospace')
    y_pos -= 0.6
    ax_al.text(0.5, y_pos, '   R = L / (λ·A) = 2L·ρ / [L₀·A·(Tₕ²-Tc²)]', fontsize=10, family='monospace')

    y_pos -= 0.9
    ax_al.text(0.5, y_pos, 'Shield 長度計算 (承擔全部 Q)：', fontsize=11, fontweight='bold')
    y_pos -= 0.7
    ax_al.text(0.5, y_pos, '   L_Al = L₀ · A_Al · (Tₕ²-Tc²) / (2 · Q · ρ_Al)', fontsize=10, family='monospace', color='#0066CC')

    y_pos -= 0.9
    ax_al.text(0.5, y_pos, '典型參數：', fontsize=11, fontweight='bold')
    y_pos -= 0.6
    ax_al.text(0.5, y_pos, '   • Al ρ (4K, RRR~100): 2.5×10⁻⁹ Ω·m', fontsize=10)
    y_pos -= 0.6
    ax_al.text(0.5, y_pos, '   • Shield 截面積: ~0.5 mm² (Ø2mm, t=0.1mm)', fontsize=10)
    y_pos -= 0.6
    ax_al.text(0.5, y_pos, '   • L_Al / L_Ag ≈ (A_Al/A_Ag)·(ρ_Ag/ρ_Al) ≈ 10×', fontsize=10, family='monospace', color='#CC0000')
    pyplot(fig)

elif menu==MENU[4]:
    # ============================================================
    # 區塊 5: CuNi 取代 Ag 的等效計算
    # ============================================================
    ax_cuni = fig.add_axes([0.52, 0.58, 0.44, 0.18])
    ax_cuni.set_xlim(0, 10)
    ax_cuni.set_ylim(0, 10)
    ax_cuni.axis('off')
    ax_cuni.set_facecolor('#FFF0F5')

    rect = FancyBboxPatch((0.2, 0.3), 9.6, 9.4, boxstyle="round,pad=0.3", 
                           facecolor='#FFF0F5', edgecolor='#8B4513', linewidth=2)
    ax_cuni.add_patch(rect)

    ax_cuni.text(5, 9.2, '🔁 CuNi 取代 Ag 的等效計算', ha='center', va='top', fontsize=14, fontweight='bold')

    y_pos = 8.2

    ax_cuni.text(0.5, y_pos, '已知條件：', fontsize=11, fontweight='bold')
    y_pos -= 0.7
    ax_cuni.text(0.5, y_pos, '   • 相同熱負載 Q (固定)', fontsize=10)
    y_pos -= 0.6
    ax_cuni.text(0.5, y_pos, '   • 相同溫度段 (Tₕ, Tc)', fontsize=10)
    y_pos -= 0.6
    ax_cuni.text(0.5, y_pos, '   • CuNi ρ_CuNi = 4.9×10⁻⁷ Ω·m', fontsize=10, family='monospace')
    y_pos -= 0.6
    ax_cuni.text(0.5, y_pos, '   • Ag ρ_Ag = 1.5×10⁻⁸ Ω·m', fontsize=10, family='monospace')

    y_pos -= 0.9
    ax_cuni.text(0.5, y_pos, '推導：', fontsize=11, fontweight='bold')
    y_pos -= 0.7
    ax_cuni.text(0.5, y_pos, '   L_CuNi / L_Ag = ρ_CuNi / ρ_Ag', fontsize=10, family='monospace')
    y_pos -= 0.6
    ax_cuni.text(0.5, y_pos, '                = 4.9×10⁻⁷ / 1.5×10⁻⁸', fontsize=10, family='monospace')
    y_pos -= 0.6
    ax_cuni.text(0.5, y_pos, '                ≈ 32.7', fontsize=10, family='monospace', color='#CC0000', fontweight='bold')

    y_pos -= 0.9
    ax_cuni.text(0.5, y_pos, '結論：', fontsize=11, fontweight='bold')
    y_pos -= 0.7
    ax_cuni.text(0.5, y_pos, '   相同熱負載下，CuNi 線長度需為 Ag 的 ~33 倍', fontsize=10, color='#CC0000')
    y_pos -= 0.6
    ax_cuni.text(0.5, y_pos, '   或：相同長度下，CuNi 熱負載僅為 Ag 的 ~3%', fontsize=10, color='#0066CC')
    pyplot(fig)

elif menu==MENU[3]:
    # ============================================================
    # 區塊 4: Wiedemann-Franz 定律推導
    # ============================================================
    ax_wf = fig.add_axes([0.03, 0.58, 0.44, 0.18])
    ax_wf.set_xlim(0, 10)
    ax_wf.set_ylim(0, 10)
    ax_wf.axis('off')
    ax_wf.set_facecolor('#F5F5F5')

    rect = FancyBboxPatch((0.2, 0.3), 9.6, 9.4, boxstyle="round,pad=0.3", 
                           facecolor='#F5F5F5', edgecolor='#333333', linewidth=2)
    ax_wf.add_patch(rect)

    ax_wf.text(5, 9.2, '📐 Wiedemann-Franz 定律推導', ha='center', va='top', fontsize=14, fontweight='bold')

    y_pos = 8.2
    line_height = 0.85

    ax_wf.text(0.5, y_pos, 'Step 1: Wiedemann-Franz Law', fontsize=11, fontweight='bold', color='#2E5090')
    y_pos -= line_height * 0.6
    ax_wf.text(0.5, y_pos, '   熱導率 λ 與電導率 σ 的關係：', fontsize=10)
    y_pos -= line_height * 0.5
    ax_wf.text(0.5, y_pos, '   λ = L₀ · T · σ = L₀ · T / ρ(T)', fontsize=10, family='monospace', color='#0066CC')

    y_pos -= line_height
    ax_wf.text(0.5, y_pos, 'Step 2: 熱傳導積分 (沿線方向)', fontsize=11, fontweight='bold', color='#2E5090')
    y_pos -= line_height * 0.6
    ax_wf.text(0.5, y_pos, '   Q = (A/L) · ∫λ(T)dT = (A/L) · ∫[L₀·T/ρ]dT', fontsize=10, family='monospace')
    y_pos -= line_height * 0.5
    ax_wf.text(0.5, y_pos, '   假設 ρ ≈ 常數 (段內)：', fontsize=10)
    y_pos -= line_height * 0.5
    ax_wf.text(0.5, y_pos, '   Q = (L₀·A / L·ρ) · (Tₕ² - Tc²) / 2', fontsize=10, family='monospace', color='#0066CC')

    y_pos -= line_height
    ax_wf.text(0.5, y_pos, 'Step 3: 反推長度 (已知 Q, 求 L)', fontsize=11, fontweight='bold', color='#2E5090')
    y_pos -= line_height * 0.6
    ax_wf.text(0.5, y_pos, '   L = L₀ · A_channel · (Tₕ² - Tc²) / (2 · Q · ρ)', fontsize=11, family='monospace', color='#CC0000', fontweight='bold')

    y_pos -= line_height * 0.8
    ax_wf.text(0.5, y_pos, '⚠️ 關鍵：A_channel 是「整個通道」的有效截面積，非單根線！', fontsize=10, color='#CC6600', fontweight='bold')
    pyplot(fig)

elif menu==MENU[2]:
    # ============================================================
    # 區塊 3: 同軸線截面結構示意圖
    # ============================================================
    #fig, ax4= subplots(figsize=(10, 6))
    ax_cross = fig.add_axes([0.52, 0.78, 0.44, 0.13])
    ax_cross.set_xlim(-3, 3)
    ax_cross.set_ylim(-3, 3)
    ax_cross.set_aspect('equal')
    ax_cross.axis('off')
    ax_cross.set_facecolor('#F0F8FF')

    # 外護套 (不鏽鋼)
    circle_outer = plt.Circle((0, 0), 2.8, color='#888888', alpha=0.3, label='Outer Jacket')
    ax_cross.add_patch(circle_outer)

    # 外屏蔽 (CuNi 編織)
    circle_shield = plt.Circle((0, 0), 2.2, color='#4A90A4', alpha=0.5, label='CuNi Shield')
    ax_cross.add_patch(circle_shield)

    # 介電層 (PTFE)
    circle_dielectric = plt.Circle((0, 0), 1.5, color='#FFE4B5', alpha=0.6, label='PTFE Dielectric')
    ax_cross.add_patch(circle_dielectric)

    # 中心導體 (AWG36 CuNi/Ag)
    circle_center = plt.Circle((0, 0), 0.4, color='#D4A843', alpha=0.9, label='Center Conductor')
    ax_cross.add_patch(circle_center)

    # 標註
    ax_cross.annotate('外護套\n(不鏽鋼)', xy=(2.5, 1.5), fontsize=8, ha='center')
    ax_cross.annotate('外屏蔽\n(CuNi)', xy=(1.8, -1.2), fontsize=8, ha='center', color='#4A90A4')
    ax_cross.annotate('介電層\n(PTFE)', xy=(0.8, 0.8), fontsize=8, ha='center')
    ax_cross.annotate('中心導體\n(AWG36)', xy=(0, 0), fontsize=7, ha='center', va='center', fontweight='bold')

    ax_cross.set_title('同軸線截面結構 (Cross-section)', fontsize=12, fontweight='bold', pad=10)

    # 圖例
    legend_elements = [mpatches.Patch(color='#D4A843', label='Center Conductor (Ag/CuNi)'),
                       mpatches.Patch(color='#FFE4B5', label='Dielectric (PTFE)'),
                       mpatches.Patch(color='#4A90A4', label='Outer Shield (CuNi)'),
                       mpatches.Patch(color='#888888', label='Jacket (Stainless)')]
    ax_cross.legend(handles=legend_elements, loc='lower right', fontsize=8)
    pyplot(fig)

elif menu==MENU[1]:
    # ============================================================
    # 區塊 2: 核心問題 - "per channel" 正確理解
    # ============================================================
    #fig, ax4= subplots(figsize=(10, 6))
    ax_ch = fig.add_axes([0.03, 0.78, 0.44, 0.13])
    ax_ch.set_xlim(0, 10)
    ax_ch.set_ylim(0, 10)
    ax_ch.axis('off')
    ax_ch.set_facecolor('#FFF8DC')

    # 背景框
    rect = FancyBboxPatch((0.2, 0.5), 9.6, 9, boxstyle="round,pad=0.3", 
                           facecolor='#FFF8DC', edgecolor='#D4A843', linewidth=2)
    ax_ch.add_patch(rect)

    ax_ch.text(5, 8.5, '❌ 錯誤理解 vs ✅ 正確理解', ha='center', va='top', fontsize=14, fontweight='bold')

    # 錯誤理解
    ax_ch.text(2.5, 6.5, '❌ 錯誤：', ha='center', va='top', fontsize=11, color='red', fontweight='bold')
    ax_ch.text(2.5, 5.5, '"per channel" = 單根 AWG36', ha='center', va='top', fontsize=10)
    ax_ch.text(2.5, 4.5, 'A = π×(0.0635mm)²', ha='center', va='top', fontsize=9, family='monospace')
    ax_ch.text(2.5, 3.5, '= 0.0127 mm²', ha='center', va='top', fontsize=9, family='monospace')
    ax_ch.text(2.5, 2.2, '→ 回推長度僅數公分', ha='center', va='top', fontsize=9, color='red')

    # 正確理解
    ax_ch.text(7.5, 6.5, '✅ 正確：', ha='center', va='top', fontsize=11, color='green', fontweight='bold')
    ax_ch.text(7.5, 5.5, '"per channel" = 整個同軸通道', ha='center', va='top', fontsize=10)
    ax_ch.text(7.5, 4.5, 'A_total = A_center + A_shield', ha='center', va='top', fontsize=9, family='monospace')
    ax_ch.text(7.5, 3.5, '≈ 0.06 ~ 0.25 mm²', ha='center', va='top', fontsize=9, family='monospace')
    ax_ch.text(7.5, 2.2, '→ 回推長度數十公分~數米', ha='center', va='top', fontsize=9, color='green')

    # 箭頭
    ax_ch.annotate('', xy=(5.5, 5), xytext=(4.5, 5),
                  arrowprops=dict(arrowstyle='->', color='black', lw=2))
    pyplot(fig)

elif menu==MENU[0]:

    # ============================================================
    # 區塊 1: 標題與問題定義
    # ============================================================
    #fig, ax4= subplots(figsize=(10, 6))
    ax_title = fig.add_axes([0.05, 0.92, 0.9, 0.07])
    ax_title.axis('off')
    ax_title.text(0.5, 0.5, '低溫傳輸線熱負載物理推導與 Aluminum Shielding 分析', ha='center', va='center', fontsize=22, fontweight='bold', transform=ax_title.transAxes)
    pyplot(fig)

#plt.savefig('/mnt/agents/output/physics_derivation.png', dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
#plt.show()

#print("✅ 物理推導示意圖已保存
