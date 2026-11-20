from matplotlib.pyplot import figure, rcParams, savefig, show
from numpy import linspace
from streamlit import pyplot, slider, sidebar, radio, set_page_config
from 匯出UtilII import 匯出分頁

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.gridspec import GridSpec
import matplotlib.patheffects as pe
import numpy as np
import pandas as pd

# 設定中文字體
rcParams['font.family'] = ['WenQuanYi Zen Hei', 'Noto Sans CJK JP', 'sans-serif']
rcParams['axes.unicode_minus'] = False

# ============================================================
# Cri/oFlex 3 CF3 正確 GSG 層結構（根據 IEEE/arXiv 論文）
# ============================================================
# 參考來源：
# - IEEE TAS 2026: "2 um thick silver or silver-coated NbTi signal traces,
#   polyimide laminate substrate of approximately 120 um thick"
# - arXiv 2405.09211: "polyimide protective outside layer, top and bottom 
#   silver groundplane, silver center conductors, and polyimide dielectric"
# ============================================================
set_page_config(
    page_title="E-Tube Design Analyzer",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 總厚度 0.3 mm = 300 um，以 Signal 層中心為 Y=0 對稱
# 層結構（由 Bottom 到 Top）
LAYERS = [
    # (name, thickness_um, material, color_hex, edge_hex, is_signal)
    ('Protective Coating (Polyimide)',  15, 'Polyimide',       '#E8D5C4', '#A0522D', False),
    ('Ground Plane (Ag/NbTi)',           5, 'Ag/NbTi',         '#8B9CAD', '#4A5568', False),
    ('Dielectric (Polyimide)',         129, 'Polyimide',       '#C4956A', '#744210', False),
    ('Signal Lines (Ag/NbTi)',           2, 'Ag/NbTi',         '#FFD700', '#B8860B', True),
    ('Dielectric (Polyimide)',         129, 'Polyimide',       '#C4956A', '#744210', False),
    ('Ground Plane (Ag/NbTi)',           5, 'Ag/NbTi',         '#8B9CAD', '#4A5568', False),
    ('Protective Coating (Polyimide)',  15, 'Polyimide',       '#E8D5C4', '#A0522D', False),
]

# 驗證總厚度
total_thickness_um = sum(l[1] for l in LAYERS)
assert total_thickness_um == 300

# 找到 Signal 層索引
signal_idx = [i for i, l in enumerate(LAYERS) if l[5]][0]

# 計算各層 Y 座標（以 Signal 中心為 Y=0）
signal_thick = LAYERS[signal_idx][1]
signal_center_from_bottom = sum(l[1] for l in LAYERS[:signal_idx]) + signal_thick/2

y_bottoms = []
current = -signal_center_from_bottom
for name, thick, mat, color, edge, is_sig in LAYERS:
    y_bottoms.append(current)
    current += thick

y_tops = []
for i in range(len(LAYERS)):
    if i < len(LAYERS) - 1:
        y_tops.append(y_bottoms[i+1])
    else:
        y_tops.append(current)

# ============================================================
# 繪製前視圖
# ============================================================

def 前視圖(n_channels=8, figsize=(20, 14)):
    """
    Cri/oFlex 3 CF3 正確 GSG 前視圖（7層結構，含外層保護塗層）
    """
    
    PITCH = 2.0                    # mm
    SIGNAL_WIDTH = 0.4             # mm
    TOTAL_WIDTH = n_channels * PITCH
    TOTAL_THICKNESS_MM = total_thickness_um / 1000.0  # 0.3 mm
    
    # 建立圖面
    fig = figure(figsize=figsize, facecolor='#0D1117')
    gs = GridSpec(1, 2, figure=fig, width_ratios=[3.5, 1.3],
                  left=0.06, right=0.96, top=0.90, bottom=0.08,
                  wspace=0.12)
    
    ax_main = fig.add_subplot(gs[0, 0])
    ax_main.set_facecolor('#0D1117')
    
    ax_info = fig.add_subplot(gs[0, 1])
    ax_info.set_facecolor('#161B22')
    ax_info.axis('off')
    
    fig.suptitle(
        f'Delft Circuits  Cri/oFlex(R) 3 CF3  Front View (Cross-Section A-A)\n'
        f'GSG Stripline with Protective Coating  |  {n_channels} Channels  |  Correct Layer Stack-up',
        fontsize=15, fontweight='bold', color='white', y=0.97
    )
    
    # ========== 繪製各層 ==========
    for i, (layer, y_bot_um, y_top_um) in enumerate(zip(LAYERS, y_bottoms, y_tops)):
        name, thick_um, mat, color, edge, is_signal = layer
        y_bot = y_bot_um / 1000.0  # 轉為 mm
        y_top = y_top_um / 1000.0
        thick_mm = thick_um / 1000.0
        
        if is_signal:
            # 繪製每條信號線
            for ch in range(n_channels):
                x_c = -TOTAL_WIDTH/2 + PITCH/2 + ch * PITCH
                sig = Rectangle(
                    (x_c - SIGNAL_WIDTH/2, y_bot),
                    SIGNAL_WIDTH, thick_mm,
                    facecolor=color, edgecolor=edge, linewidth=1.5, zorder=5
                )
                ax_main.add_patch(sig)
                
                # 通道編號
                if n_channels <= 12:
                    fs = 8 if n_channels <= 8 else 6
                    ax_main.text(x_c, y_bot + thick_mm/2, str(ch+1),
                                ha='center', va='center', fontsize=fs,
                                color='#333333', fontweight='bold', zorder=6)
            
            # 信號層介電底色
            bg = Rectangle(
                (-TOTAL_WIDTH/2 - 1, y_bot),
                TOTAL_WIDTH + 2, thick_mm,
                facecolor='#D4A574', edgecolor='none', alpha=0.2, zorder=1
            )
            ax_main.add_patch(bg)
            
        else:
            # 連續層
            layer_rect = Rectangle(
                (-TOTAL_WIDTH/2 - 2, y_bot),
                TOTAL_WIDTH + 4, thick_mm,
                facecolor=color, edgecolor=edge, linewidth=1.2,
                alpha=0.95, zorder=3
            )
            ax_main.add_patch(layer_rect)
            
            # Ground 層斜線紋理
            if 'Ground' in name:
                n_lines = int((TOTAL_WIDTH + 4) / 0.3)
                for j in range(n_lines):
                    x0 = -TOTAL_WIDTH/2 - 2 + j * 0.3
                    dx = thick_mm * 3.0
                    ax_main.plot([x0, x0 + dx], [y_bot, y_top],
                                color='#5A6B7D', linewidth=0.25, alpha=0.35, zorder=4)
                    ax_main.plot([x0, x0 - dx], [y_bot, y_top],
                                color='#5A6B7D', linewidth=0.25, alpha=0.35, zorder=4)
            
            # Protective Coating 點狀紋理
            if 'Protective' in name:
                n_dots_x = int((TOTAL_WIDTH + 4) / 0.8)
                n_dots_y = max(1, int(thick_mm / 0.05))
                for dx in linspace(-TOTAL_WIDTH/2 - 1.5, TOTAL_WIDTH/2 + 1.5, n_dots_x):
                    for dy in linspace(y_bot + thick_mm*0.2, y_top - thick_mm*0.2, n_dots_y):
                        ax_main.plot(dx, dy, '.', color='#A0522D', markersize=1.5, alpha=0.3, zorder=4)
        
        # ========== 層標註（左側帶背景框）==========
        label_y = (y_bot + y_top) / 2
        label_x = -TOTAL_WIDTH/2 - 6
        
        # 顯示名稱（區分上下）
        if i == 0:
            display_name = 'Protective Coating (Polyimide) - Bottom'
        elif i == 6:
            display_name = 'Protective Coating (Polyimide) - Top'
        elif i == 1:
            display_name = 'Ground Plane (Ag/NbTi) - Bottom'
        elif i == 5:
            display_name = 'Ground Plane (Ag/NbTi) - Top'
        elif i == 2:
            display_name = 'Dielectric (Polyimide) - Lower'
        elif i == 4:
            display_name = 'Dielectric (Polyimide) - Upper'
        else:
            display_name = name
        
        ax_main.text(
            label_x, label_y, display_name,
            ha='right', va='center', fontsize=9,
            color='white', fontweight='bold', zorder=10,
            bbox=dict(boxstyle='round,pad=0.35', facecolor='#0D1117',
                     edgecolor=color, linewidth=1.8, alpha=0.95)
        )
        
        # ========== 厚度標註（右側雙向箭頭）==========
        thick_x = TOTAL_WIDTH/2 + 4
        ax_main.annotate(
            '', xy=(thick_x, y_bot), xytext=(thick_x, y_top),
            arrowprops=dict(arrowstyle='<->', color='#58A6FF', lw=1.3),
            zorder=10
        )
        ax_main.text(
            thick_x + 1.2, label_y,
            f'{thick_um} um',
            ha='left', va='center', fontsize=8,
            color='#58A6FF', fontweight='bold', zorder=10
        )
        
        # 層間虛線分隔
        if i < len(LAYERS) - 1:
            ax_main.axhline(y=y_top, xmin=0.08, xmax=0.92,
                           color='white', linewidth=0.5, linestyle=':', alpha=0.3, zorder=2)
    
    # ========== 整體尺寸標註 ==========
    # 總厚度標註
    ax_main.annotate(
        '', xy=(TOTAL_WIDTH/2 + 16, -TOTAL_THICKNESS_MM/2),
        xytext=(TOTAL_WIDTH/2 + 16, TOTAL_THICKNESS_MM/2),
        arrowprops=dict(arrowstyle='<->', color='#F85149', lw=2)
    )
    ax_main.text(
        TOTAL_WIDTH/2 + 18.5, 0,
        f'Total\nt = {TOTAL_THICKNESS_MM*1000:.0f} um\n(0.3 mm)',
        ha='left', va='center', fontsize=10,
        color='#F85149', fontweight='bold'
    )
    
    # 總寬度標註
    ax_main.annotate(
        '', xy=(-TOTAL_WIDTH/2, TOTAL_THICKNESS_MM/2 + 0.04),
        xytext=(TOTAL_WIDTH/2, TOTAL_THICKNESS_MM/2 + 0.04),
        arrowprops=dict(arrowstyle='<->', color='#F85149', lw=2)
    )
    ax_main.text(
        0, TOTAL_THICKNESS_MM/2 + 0.065,
        f'W = {TOTAL_WIDTH} mm  ({n_channels} ch x {PITCH} mm)',
        ha='center', va='bottom', fontsize=10,
        color='#F85149', fontweight='bold'
    )
    
    # Pitch 標註
    if n_channels >= 2:
        p1 = -TOTAL_WIDTH/2 + PITCH/2
        p2 = p1 + PITCH
        py = TOTAL_THICKNESS_MM/2 + 0.11
        ax_main.annotate(
            '', xy=(p1, py), xytext=(p2, py),
            arrowprops=dict(arrowstyle='<->', color='#3FB950', lw=1.5)
        )
        ax_main.text(
            (p1+p2)/2, py + 0.018,
            f'Pitch = {PITCH} mm',
            ha='center', va='bottom', fontsize=9,
            color='#3FB950', fontweight='bold'
        )
    
    # 中心線
    ax_main.axhline(y=0, color='#FF6B6B', linewidth=1.5, linestyle='-.', alpha=0.6)
    ax_main.text(
        TOTAL_WIDTH/2 + 0.5, 0.008, 'Signal Center (Y=0)',
        ha='left', va='bottom', fontsize=8,
        color='#FF6B6B', style='italic', fontweight='bold'
    )
    
    # ========== 座標軸設定 ==========
    margin_x = 38
    ax_main.set_xlim(-TOTAL_WIDTH/2 - margin_x, TOTAL_WIDTH/2 + margin_x)
    ax_main.set_ylim(-TOTAL_THICKNESS_MM/2 - 0.06, TOTAL_THICKNESS_MM/2 + 0.18)
    ax_main.set_xlabel('Width (mm)', color='white', fontsize=11)
    ax_main.set_ylabel('Thickness (mm)', color='white', fontsize=11)
    ax_main.tick_params(colors='white')
    for spine in ax_main.spines.values():
        spine.set_color('#30363D')
    ax_main.set_title(
        'Corrected GSG Stack-up  |  Z0 = 50 Ohm  |  7-Layer Structure',
        fontsize=12, color='#58A6FF', fontweight='bold', pad=10
    )
    
    # ========== 右側資訊面板 ==========
    info_text = (
        f'Cri/oFlex 3 CF3 Spec (Corrected)\n'
        f'--------------------------------\n'
        f'Channels:      {n_channels}\n'
        f'Pitch:         {PITCH} mm\n'
        f'Width:         {TOTAL_WIDTH} mm\n'
        f'Thickness:     {TOTAL_THICKNESS_MM} mm (300 um)\n'
        f'Impedance:     50 Ohm\n'
        f'Frequency:     DC - 18 GHz\n'
        f'Materials:     Polyimide + Ag/NbTi\n'
        f'Line Type:     Stripline (GSG)\n\n'
        f'Layer Stack-up (Bottom to Top)\n'
        f'--------------------------------\n'
        f'1. Protective Coating  (Polyimide)   15 um\n'
        f'2. Ground Plane        (Ag/NbTi)      5 um\n'
        f'3. Dielectric          (Polyimide)  129 um\n'
        f'4. Signal Lines        (Ag/NbTi)      2 um  x {n_channels}ch\n'
        f'5. Dielectric          (Polyimide)  129 um\n'
        f'6. Ground Plane        (Ag/NbTi)      5 um\n'
        f'7. Protective Coating  (Polyimide)   15 um\n'
        f'   Total:                          300 um\n\n'
        f'References\n'
        f'--------------------------------\n'
        f'- IEEE TAS 2026 (Marting et al.)\n'
        f'- arXiv:2405.09211 (2024)\n'
        f'- Delft Circuits datasheet\n\n'
        f'Key Features\n'
        f'--------------------------------\n'
        f'- Symmetric Stripline\n'
        f'- EM fully shielded\n'
        f'  between two grounds\n'
        f'- Crosstalk < -60 dB\n'
        f'- Heat load < 4 uW/ch @ 3K'
    )
    
    ax_info.text(
        0.08, 0.97, info_text,
        transform=ax_info.transAxes,
        fontsize=9.5, color='#C9D1D9',
        va='top', ha='left',
        linespacing=1.4,
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#0D1117',
                  edgecolor='#30363D', linewidth=1.5)
    )
    
    # 圖例
    legend_items = [
        ('#E8D5C4', 'Protective Coating (Polyimide)'),
        ('#8B9CAD', 'Ground Plane (Ag/NbTi)'),
        ('#C4956A', 'Dielectric (Polyimide)'),
        ('#FFD700', f'Signal Lines (Ag/NbTi) x{n_channels}'),
    ]
    for i, (color, label) in enumerate(legend_items):
        y_leg = 0.03 - i * 0.032
        rect = Rectangle((0.08, y_leg), 0.05, 0.02,
                         facecolor=color, edgecolor='white', linewidth=0.5,
                         transform=ax_info.transAxes)
        ax_info.add_patch(rect)
        ax_info.text(0.15, y_leg + 0.01, label, transform=ax_info.transAxes, fontsize=9, color='#C9D1D9', va='center')
    
    # savefig('/mnt/agents/output/cf3_correct_front_view.png', dpi=250, facecolor='#0D1117', edgecolor='none', bbox_inches='tight')
    # show()
    # print(f"Corrected CF3 Front View ({n_channels} channels) saved!")
    return fig
from streamlit import button, download_button, markdown, session_state, sidebar, spinner, subheader, success, radio, text_input, empty
MENU, 表單=[], ['前視圖', '匯出', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  狀態=empty()
  狀態.code([])
if menu==len(表單):
  pass
elif menu==MENU[0]: #前視圖
  pass
# 執行繪製
  fig = 前視圖(n_channels=8)
  pyplot(fig)

elif menu==MENU[1]: #
# ============================================
# 放在側邊欄：Excel 匯出與下載
# ============================================
    # markdown("---")
    subheader("📥 Export & Download")
    
    # 取得目前使用者選擇的通道數（假設您已有 n_channels 變數）
    n_ch = session_state.get("n_channels", 8)  # 或從 slider 取得
    
    #if button("📊 Generate Excel Spec", use_container_width=True):
    #    with spinner("Generating Excel..."):
    excel_bytes = 匯出分頁(通道數=n_ch)
    session_state["excel_bytes"] = excel_bytes
    success("Excel generated!")
    
    # if "excel_bytes" in session_state:
    download_button( label="⬇️ Download CF3_Spec.xlsx", data=session_state["excel_bytes"], file_name=f"CF3前視規格{n_ch}ch.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    
    # markdown("---")
    # 前視圖 PNG 下載（假設您已將 fig 存入 session_state["front_view_fig"]）
    #if "front_view_fig" in session_state:
    #    fig = session_state["front_view_fig"]
    #    buf = io.BytesIO()
    #    fig.savefig(buf, format="png", dpi=250, facecolor="#0D1117", bbox_inches="tight")
    #    buf.seek(0)
    #    download_button(
    #        label="⬇️ Download Front View PNG",
    #        data=buf,
    #        file_name=f"CF3_FrontView_{n_ch}ch.png",
    #        mime="image/png",
    #        use_container_width=True
    #    )
