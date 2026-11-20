from matplotlib.pyplot import figure, rcParams, savefig, show
from streamlit import pyplot, sidebar, slider, set_page_config

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.gridspec import GridSpec
import matplotlib.patheffects as pe
import numpy as np

# 設定中文字體
#plt.rcParams['font.family'] = ['WenQuanYi Zen Hei', 'Noto Sans CJK JP', 'sans-serif']
#plt.rcParams['axes.unicode_minus'] = False
from fontUtil2 import 配置中文
配置中文()

def 前視圖(通道數=8, figsize=(18, 12)):
    """
    Cri/oFlex 3 CF3 GSG 前視圖（橫截面）最終版
    以 Signal 層為中心 (Y=0)，對稱 GSG 結構
    """
    
    # ========== 規格參數 ==========
    PITCH = 2.0                    # mm, 通道間距
    TOTAL_THICKNESS = 0.3          # mm, 總厚度
    SIGNAL_WIDTH = 0.4             # mm, 單條信號線寬度
    TOTAL_WIDTH = 通道數 * PITCH
    
    # GSG 層厚度（由 Bottom 到 Top，與 Y 軸方向一致）
    # 以 Signal 中心為 Y=0，對稱分佈
    LAYERS_BOTTOM_TO_TOP = [
        {'name': 'Ground Plane (Ag/NbTi)', 'thick':.025, 'label': 'Ground Plane (Ag/NbTi) - Bottom'},
        {'name': 'Dielectric (Polyimide)', 'thick':.100, 'label': 'Dielectric (Polyimide) - Lower'},
        {'name': 'Signal Lines',           'thick':.050, 'label': f'Signal Lines (x{通道數})'},
        {'name': 'Dielectric (Polyimide)', 'thick':.100, 'label': 'Dielectric (Polyimide) - Upper'},
        {'name': 'Ground Plane (Ag/NbTi)', 'thick':.025, 'label': 'Ground Plane (Ag/NbTi) - Top'},
    ]
    
    assert abs(sum(l['thick'] for l in LAYERS_BOTTOM_TO_TOP) - TOTAL_THICKNESS) < 1e-9
    
    # 色彩
    COLORS = {
        'Ground Plane (Ag/NbTi)': '#8B9CAD',
        'Dielectric (Polyimide)': '#C4956A',
        'Signal Lines': '#E6B800',
    }
    EDGE_COLORS = {
        'Ground Plane (Ag/NbTi)': '#4A5568',
        'Dielectric (Polyimide)': '#744210',
        'Signal Lines': '#B7791F',
    }
    
    # ========== 計算各層 Y 座標（Signal 中心為 Y=0）==========
    # 先找 signal 層索引
    signal_idx = 2
    signal_thick = LAYERS_BOTTOM_TO_TOP[signal_idx]['thick']
    
    # 計算每層的 bottom Y
    y_bottoms = []
    # 從 signal 往下算
    y = -signal_thick / 2
    for i in range(signal_idx, -1, -1):
        y_bottoms.insert(0, y)
        y += LAYERS_BOTTOM_TO_TOP[i]['thick']
    
    # 從 signal 往上算
    y = signal_thick / 2
    for i in range(signal_idx + 1, len(LAYERS_BOTTOM_TO_TOP)):
        y_bottoms.append(y)
        y += LAYERS_BOTTOM_TO_TOP[i]['thick']
    
    y_tops = []
    for i in range(len(y_bottoms)):
        if i < len(y_bottoms) - 1:
            y_tops.append(y_bottoms[i + 1])
        else:
            y_tops.append(y)
    
    # ========== 建立圖面 ==========
    fig = plt.figure(figsize=figsize, facecolor='#0D1117')
    gs = GridSpec(1, 2, figure=fig, width_ratios=[3.5, 1.2],
                  left=0.06, right=0.96, top=0.90, bottom=0.08,
                  wspace=0.12)
    
    ax_main = fig.add_subplot(gs[0, 0])
    ax_main.set_facecolor('#0D1117')
    
    ax_info = fig.add_subplot(gs[0, 1])
    ax_info.set_facecolor('#161B22')
    ax_info.axis('off')
    
    fig.suptitle(f'''
        Delft Circuits  Cri/oFlex(R) 3 CF3  Front View (Cross-Section A-A)
        GSG Stripline Structure  |  {通道數} Channels  |  Centered at Signal Layer''', fontsize=15, fontweight='bold', color='white', y=0.97
    )
    
    # ========== 繪製各層（由 Bottom 到 Top）==========
    for i, (layer, y_bot, y_top) in enumerate(zip(LAYERS_BOTTOM_TO_TOP, y_bottoms, y_tops)):
        thick = y_top - y_bot
        name = layer['name']
        label = layer['label']
        color = COLORS[name]
        edge = EDGE_COLORS[name]
        
        if name == 'Signal Lines':
            # 繪製每條信號線
            for ch in range(通道數):
                x_c = -TOTAL_WIDTH/2 + PITCH/2 + ch * PITCH
                sig = Rectangle(
                    (x_c - SIGNAL_WIDTH/2, y_bot),
                    SIGNAL_WIDTH, thick,
                    facecolor=color, edgecolor=edge, linewidth=1.5, zorder=5
                )
                ax_main.add_patch(sig)
                
                # 通道編號
                if 通道數 <= 12:
                    fs = 8 if 通道數 <= 8 else 6
                    ax_main.text(x_c, y_bot + thick/2, str(ch+1),
                                ha='center', va='center', fontsize=fs,
                                color='#333333', fontweight='bold', zorder=6)
            
            # 信號層介電底色
            bg = Rectangle(
                (-TOTAL_WIDTH/2 - 1, y_bot),
                TOTAL_WIDTH + 2, thick,
                facecolor='#D4A574', edgecolor='none', alpha=0.25, zorder=1
            )
            ax_main.add_patch(bg)
            
        else:
            # 連續層（Ground 或 Dielectric）
            layer_rect = Rectangle(
                (-TOTAL_WIDTH/2 - 2, y_bot),
                TOTAL_WIDTH + 4, thick,
                facecolor=color, edgecolor=edge, linewidth=1.5,
                alpha=0.95, zorder=3
            )
            ax_main.add_patch(layer_rect)
            
            # 接地層斜線紋理（金屬質感）
            if 'Ground' in name:
                n_lines = int((TOTAL_WIDTH + 4) / 0.35)
                for j in range(n_lines):
                    x0 = -TOTAL_WIDTH/2 - 2 + j * 0.35
                    # 斜率讓線條跨過整個層厚度
                    dx = thick * 2.5
                    ax_main.plot([x0, x0 + dx],
                                [y_bot, y_top],
                                color='#5A6B7D', linewidth=0.35, alpha=0.4, zorder=4)
                    ax_main.plot([x0, x0 - dx],
                                [y_bot, y_top],
                                color='#5A6B7D', linewidth=0.35, alpha=0.4, zorder=4)
        
        # ========== 層標註（左側帶背景框）==========
        label_y = (y_bot + y_top) / 2
        label_x = -TOTAL_WIDTH/2 - 5
        
        ax_main.text(
            label_x, label_y, label,
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
            f'{thick*1000:.0f} um',
            ha='left', va='center', fontsize=8,
            color='#58A6FF', fontweight='bold', zorder=10
        )
        
        # 層間虛線分隔
        if i < len(LAYERS_BOTTOM_TO_TOP) - 1:
            ax_main.axhline(y=y_top, xmin=0.08, xmax=0.92,
                           color='white', linewidth=0.6, linestyle=':', alpha=0.35, zorder=2)
    
    # ========== 整體尺寸標註 ==========
    # 總厚度標註（右側大箭頭）
    ax_main.annotate(
        '', xy=(TOTAL_WIDTH/2 + 14, -TOTAL_THICKNESS/2),
        xytext=(TOTAL_WIDTH/2 + 14, TOTAL_THICKNESS/2),
        arrowprops=dict(arrowstyle='<->', color='#F85149', lw=2)
    )
    ax_main.text(
        TOTAL_WIDTH/2 + 16.5, 0,
        f'Total\nt = {TOTAL_THICKNESS*1000:.0f} um',
        ha='left', va='center', fontsize=10,
        color='#F85149', fontweight='bold'
    )
    
    # 總寬度標註（上方）
    ax_main.annotate(
        '', xy=(-TOTAL_WIDTH/2, TOTAL_THICKNESS/2 + 0.04),
        xytext=(TOTAL_WIDTH/2, TOTAL_THICKNESS/2 + 0.04),
        arrowprops=dict(arrowstyle='<->', color='#F85149', lw=2)
    )
    ax_main.text(
        0, TOTAL_THICKNESS/2 + 0.065,
        f'W = {TOTAL_WIDTH} mm  ({通道數} ch x {PITCH} mm)',
        ha='center', va='bottom', fontsize=10,
        color='#F85149', fontweight='bold'
    )
    
    # Pitch 標註
    if 通道數 >= 2:
        p1 = -TOTAL_WIDTH/2 + PITCH/2
        p2 = p1 + PITCH
        py = TOTAL_THICKNESS/2 + 0.11
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
    
    # 中心線（Signal Center Y=0）
    ax_main.axhline(y=0, color='#FF6B6B', linewidth=1.5, linestyle='-.', alpha=0.6)
    ax_main.text(
        TOTAL_WIDTH/2 + 0.5, 0.008, 'Signal Center (Y=0)',
        ha='left', va='bottom', fontsize=8,
        color='#FF6B6B', style='italic', fontweight='bold'
    )
    
    # ========== 座標軸設定 ==========
    margin_x = 35
    ax_main.set_xlim(-TOTAL_WIDTH/2 - margin_x, TOTAL_WIDTH/2 + margin_x)
    ax_main.set_ylim(-TOTAL_THICKNESS/2 - 0.06, TOTAL_THICKNESS/2 + 0.18)
    ax_main.set_xlabel('Width (mm)', color='white', fontsize=11)
    ax_main.set_ylabel('Thickness (mm)', color='white', fontsize=11)
    ax_main.tick_params(colors='white')
    for spine in ax_main.spines.values():
        spine.set_color('#30363D')
    ax_main.set_title(
        'GSG Stripline Cross-Section  |  Z0 = 50 Ohm  |  Symmetric Structure',
        fontsize=12, color='#58A6FF', fontweight='bold', pad=10
    )
    
    # ========== 右側資訊面板 ==========
    info_text = f'''
        Cri/oFlex 3 CF3 Spec
        ------------------------
        Channels:     {通道數}
        Pitch:        {PITCH} mm
        Width:        {TOTAL_WIDTH} mm
        Thickness:    {TOTAL_THICKNESS} mm
        Impedance:    50 Ohm
        Frequency:    DC - 18 GHz
        Material:     Polyimide + Ag/NbTi
        Line Type:    Stripline (GSG)
        GSG Stack-up (Bottom to Top)
        ------------------------
        1. Ground Plane  (Ag/NbTi)   25 um
        2. Dielectric    (Polyimide) 100 um
        3. Signal Lines  (Ag/NbTi)  50 um x {通道數}ch
        4. Dielectric    (Polyimide) 100 um
        5. Ground Plane  (Ag/NbTi)   25 um
        Key Features
        ------------------------
        - Symmetric Stripline
        - EM fully shielded
          between two grounds
        - Crosstalk < -60 dB
        - Heat load < 4 uW/ch @ 3K'
    '''
    
    ax_info.text(
        0.08, 0.97, info_text,
        transform=ax_info.transAxes,
        fontsize=10, color='#C9D1D9',
        va='top', ha='left',
        linespacing=1.45,
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#0D1117',
                  edgecolor='#30363D', linewidth=1.5)
    )
    
    # 圖例
    legend_items = [
        (COLORS['Ground Plane (Ag/NbTi)'], 'Ground Plane (Ag/NbTi)'),
        (COLORS['Dielectric (Polyimide)'], 'Dielectric (Polyimide)'),
        (COLORS['Signal Lines'], f'Signal Lines (x{通道數})'),
    ]
    for i, (color, label) in enumerate(legend_items):
        y_leg = 0.04 - i * 0.035
        rect = Rectangle((0.08, y_leg), 0.05, 0.022,
                         facecolor=color, edgecolor='white', linewidth=0.5,
                         transform=ax_info.transAxes)
        ax_info.add_patch(rect)
        ax_info.text(0.15, y_leg + 0.011, label,
                    transform=ax_info.transAxes, fontsize=9,
                    color='#C9D1D9', va='center')
    
    # plt.savefig('/mnt/agents/output/cf3_gsg_front_view_final.png', dpi=250, facecolor='#0D1117', edgecolor='none', bbox_inches='tight')
    # plt.show()
    # print(f"CF3 GSG Front View ({通道數} channels) saved!")
    return fig

set_page_config( page_title="動態通道數", page_icon="📡", layout="wide", initial_sidebar_state="expanded")

with sidebar:
# ========== 執行：預設 8 通道 ==========
  通道數 = slider("通道數", 2, 16, 8, 2)
fig = 前視圖(通道數=通道數)
pyplot(fig)
