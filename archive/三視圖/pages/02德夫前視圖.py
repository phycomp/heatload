from matplotlib.pyplot import figure, rcParams, savefig, show
from streamlit import pyplot

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle
from matplotlib.gridspec import GridSpec
import matplotlib.patheffects as pe
import numpy as np

# ============================================================
# Cri/oFlex 3 CF3 GSG 前視圖 — 動態通道數
# ============================================================

from fontUtil2 import 配置中文
配置中文()
# 設定中文字體
# plt.rcParams['font.family'] = ['WenQuanYi Zen Hei', 'Noto Sans CJK JP', 'sans-serif']
# plt.rcParams['axes.unicode_minus'] = False

def 前視圖(n_channels=8, figsize=(16, 10)):
    """
    繪製 Cri/oFlex 3 CF3 傳輸線 GSG 前視圖（橫截面）

    Parameters:

    n_channels : int
        通道數量，預設 8（可動態調整為 4, 8, 16 等）
    figsize : tuple
        圖面尺寸
    """

    # ========== 規格參數 ==========
    PITCH = 2.0                    # mm, 通道間距
    TOTAL_THICKNESS = 0.3          # mm, 總厚度

    # GSG 層厚度分配（以 Signal 層為中心對稱）
    # Ground | Dielectric | Signal | Dielectric | Ground
    LAYER_THICKNESSES = {
        'Ground Plane (Ag/NbTi)': 0.025,
        'Dielectric (Polyimide)': 0.1,
        'Signal Lines': 0.05,      # 信號層厚度
        'Dielectric (Polyimide)_lower': 0.1,
        'Ground Plane (Ag/NbTi)_lower': 0.025,
    }

    # 驗證總厚度
    assert abs(sum([
        0.025, 0.1, 0.05, 0.1, 0.025
    ]) - TOTAL_THICKNESS) < 1e-6, "Thickness mismatch!"

    SIGNAL_WIDTH = 0.4             # mm, 單條信號線寬度
    TOTAL_WIDTH = n_channels * PITCH  # mm, 總寬度

    # 色彩定義
    COLORS = {
        'Ground Plane (Ag/NbTi)': '#A8B5C4',      # 銀灰色
        'Dielectric (Polyimide)': '#D4A574',       # 聚醯亞胺棕色
        'Signal Lines': '#FFD700',                  # 金色信號線
    }

    EDGE_COLORS = {
        'Ground Plane (Ag/NbTi)': '#5A6B7D',
        'Dielectric (Polyimide)': '#8B6914',
        'Signal Lines': '#B8860B',
    }

    # ========== 建立圖面 ==========
    fig = plt.figure(figsize=figsize, facecolor='#0D1117')
    gs = GridSpec(1, 2, figure=fig, width_ratios=[3, 1],
                  left=0.08, right=0.95, top=0.92, bottom=0.08,
                  wspace=0.15)

    ax_main = fig.add_subplot(gs[0, 0])
    ax_main.set_facecolor('#0D1117')

    ax_info = fig.add_subplot(gs[0, 1])
    ax_info.set_facecolor('#161B22')
    ax_info.axis('off')

    # 主標題
    fig.suptitle(
        f'Delft Circuits  Cri/oFlex® 3 CF3  Front View (Cross-Section A-A)\n'
        f'GSG Stripline Structure  —  {n_channels} Channels  —  Dynamic Layout',
        fontsize=15, fontweight='bold', color='white', y=0.97
    )

    # ========== 計算各層 Y 座標（以 Signal 層中心為 Y=0）==========
    # 從下到上計算
    layer_names = [
        'Ground Plane (Ag/NbTi)',      # 下接地層
        'Dielectric (Polyimide)',       # 下介電層
        'Signal Lines',                 # 信號層（中心）
        'Dielectric (Polyimide)',       # 上介電層
        'Ground Plane (Ag/NbTi)',       # 上接地層
    ]

    layer_thicknesses = [0.025, 0.1, 0.05, 0.1, 0.025]

    # 計算各層的 bottom 和 top Y 座標
    # 以信號層中心為原點
    signal_center_idx = 2
    signal_thickness = layer_thicknesses[signal_center_idx]

    # 先計算信號層的 bottom
    y_bottom_signal = -signal_thickness / 2

    # 從信號層往下推
    y_positions = []
    current_y = y_bottom_signal
    for i in range(signal_center_idx, -1, -1):
        y_positions.insert(0, current_y)
        current_y += layer_thicknesses[i]

    # 從信號層往上推
    current_y = y_bottom_signal + signal_thickness
    for i in range(signal_center_idx + 1, len(layer_thicknesses)):
        y_positions.append(current_y)
        current_y += layer_thicknesses[i]

    # y_positions 現在是每層的 bottom Y 座標
    # 加上最頂層的 top
    y_tops = y_positions[1:] + [current_y]

    # ========== 繪製各層 ==========
    for i, (name, y_bot, y_top) in enumerate(zip(layer_names, y_positions, y_tops)):
        thickness = y_top - y_bot

        # 判斷顯示名稱（處理重複名稱）
        display_name = name
        if i == 0:
            display_name = 'Ground Plane (Ag/NbTi) — Bottom'
        elif i == 4:
            display_name = 'Ground Plane (Ag/NbTi) — Top'
        elif i == 1:
            display_name = 'Dielectric (Polyimide) — Lower'
        elif i == 3:
            display_name = 'Dielectric (Polyimide) — Upper'

        color = COLORS.get(name, '#CCCCCC')
        edge = EDGE_COLORS.get(name, '#888888')

        if name == 'Signal Lines':
            # 信號層：繪製 n_channels 條獨立信號線
            for ch in range(n_channels):
                x_center = -TOTAL_WIDTH/2 + PITCH/2 + ch * PITCH
                sig_rect = Rectangle(
                    (x_center - SIGNAL_WIDTH/2, y_bot),
                    SIGNAL_WIDTH, thickness,
                    facecolor=color, edgecolor=edge, linewidth=1.2,
                    zorder=5
                )
                ax_main.add_patch(sig_rect)

                # 通道編號（只在圖面空間足夠時顯示）
                if n_channels <= 16:
                    ax_main.text(
                        x_center, y_bot + thickness/2, f'CH{ch+1}',
                        ha='center', va='center', fontsize=6 if n_channels > 8 else 8,
                        color='#333333', fontweight='bold', zorder=6
                    )

            # 信號層背景（介電層底色）
            bg_rect = Rectangle(
                (-TOTAL_WIDTH/2 - 1, y_bot),
                TOTAL_WIDTH + 2, thickness,
                facecolor='#E8D5C4', edgecolor='none', alpha=0.3, zorder=1
            )
            ax_main.add_patch(bg_rect)

        else:
            # 接地層與介電層：連續矩形
            layer_rect = Rectangle(
                (-TOTAL_WIDTH/2 - 2, y_bot),
                TOTAL_WIDTH + 4, thickness,
                facecolor=color, edgecolor=edge, linewidth=1.5,
                alpha=0.95, zorder=3
            )
            ax_main.add_patch(layer_rect)

            # 添加層內紋理效果（接地層加斜線）
            if 'Ground' in name:
                # 繪製斜線紋理表示金屬層
                n_lines = int((TOTAL_WIDTH + 4) / 0.5)
                for j in range(n_lines):
                    x_start = -TOTAL_WIDTH/2 - 2 + j * 0.5
                    ax_main.plot(
                        [x_start, x_start + thickness * 0.8],
                        [y_bot, y_top],
                        color='#7A8B9D', linewidth=0.3, alpha=0.4, zorder=4
                    )

        # ========== 層標註文字 ==========
        # 左側標註
        label_x = -TOTAL_WIDTH/2 - 8
        label_y = (y_bot + y_top) / 2

        # 背景框
        bbox_props = dict(
            boxstyle='round,pad=0.3',
            facecolor='#161B22',
            edgecolor=color,
            linewidth=1.5,
            alpha=0.95
        )

        ax_main.text(
            label_x, label_y, display_name,
            ha='right', va='center', fontsize=9,
            color='white', fontweight='bold',
            bbox=bbox_props, zorder=10
        )

        # 厚度標註（右側）
        thick_x = TOTAL_WIDTH/2 + 6
        ax_main.annotate(
            '', xy=(thick_x, y_bot), xytext=(thick_x, y_top),
            arrowprops=dict(arrowstyle='<->', color='#58A6FF', lw=1.2),
            zorder=10
        )
        ax_main.text(
            thick_x + 2, label_y, f'{thickness*1000:.0f} μm',
            ha='left', va='center', fontsize=8,
            color='#58A6FF', fontweight='bold', zorder=10
        )

        # 層間分隔線（虛線）
        if i < len(layer_names) - 1:
            ax_main.axhline(y=y_top, color='white', linewidth=0.5,
                           linestyle='--', alpha=0.3, zorder=2)

    # ========== 整體尺寸標註 ==========
    # 總厚度標註
    ax_main.annotate(
        '', xy=(TOTAL_WIDTH/2 + 18, -TOTAL_THICKNESS/2),
        xytext=(TOTAL_WIDTH/2 + 18, TOTAL_THICKNESS/2),
        arrowprops=dict(arrowstyle='<->', color='#F85149', lw=2)
    )
    ax_main.text(
        TOTAL_WIDTH/2 + 22, 0,
        f'Total\nt = {TOTAL_THICKNESS*1000:.0f} μm',
        ha='left', va='center', fontsize=10,
        color='#F85149', fontweight='bold'
    )

    # 總寬度標註
    ax_main.annotate(
        '', xy=(-TOTAL_WIDTH/2, TOTAL_THICKNESS/2 + 5),
        xytext=(TOTAL_WIDTH/2, TOTAL_THICKNESS/2 + 5),
        arrowprops=dict(arrowstyle='<->', color='#F85149', lw=2)
    )
    ax_main.text(
        0, TOTAL_THICKNESS/2 + 8,
        f'W = {TOTAL_WIDTH} mm  ({n_channels} ch x {PITCH} mm pitch)',
        ha='center', va='bottom', fontsize=10,
        color='#F85149', fontweight='bold'
    )

    # Pitch 標註（放大區域）
    if n_channels >= 2:
        p1_x = -TOTAL_WIDTH/2 + PITCH/2
        p2_x = p1_x + PITCH
        pitch_y = TOTAL_THICKNESS/2 + 12
        ax_main.annotate(
            '', xy=(p1_x, pitch_y), xytext=(p2_x, pitch_y),
            arrowprops=dict(arrowstyle='<->', color='#3FB950', lw=1.5)
        )
        ax_main.text(
            (p1_x + p2_x)/2, pitch_y + 1.5,
            f'Pitch = {PITCH} mm',
            ha='center', va='bottom', fontsize=9,
            color='#3FB950', fontweight='bold'
        )

    # ========== 中心線 ==========
    ax_main.axhline(y=0, color='#FF6B6B', linewidth=1, linestyle='-.', alpha=0.6)
    ax_main.text(
        TOTAL_WIDTH/2 + 2, 0.5, 'Signal Center',
        ha='left', va='bottom', fontsize=8,
        color='#FF6B6B', style='italic'
    )

    # ========== 設定座標軸 ==========
    margin_x = 35
    margin_y = 20
    ax_main.set_xlim(-TOTAL_WIDTH/2 - margin_x, TOTAL_WIDTH/2 + margin_x)
    ax_main.set_ylim(-TOTAL_THICKNESS/2 - 8, TOTAL_THICKNESS/2 + 18)
    ax_main.set_aspect('equal')
    ax_main.set_xlabel('Width (mm)', color='white', fontsize=11)
    ax_main.set_ylabel('Thickness (mm)', color='white', fontsize=11)
    ax_main.tick_params(colors='white')
    for spine in ax_main.spines.values():
        spine.set_color('#30363D')
    ax_main.set_title(
        f'GSG Stripline Cross-Section  |  Z₀ = 50 Ω',
        fontsize=12, color='#58A6FF', fontweight='bold', pad=10
    )

    # ========== 右側資訊面板 ==========
    info_text = '''
        ▌ Cri/oFlex® 3 CF3 規格
        ─────────────────────
          通道數量: {n_channels}
          通道間距: {PITCH} mm
          總寬度:   {TOTAL_WIDTH} mm
          總厚度:   {TOTAL_THICKNESS} mm
          阻抗:     50 Ω
          頻率:     DC – 18 GHz
          材料:     Polyimide + Ag/NbTi
          線型:     Stripline (GSG)
        ▌ GSG 層結構（由上至下）
        ─────────────────────
          ① Ground Plane  (Ag/NbTi)
             25 μm
          ② Dielectric    (Polyimide)
             100 μm
          ③ Signal Lines  (Ag/NbTi)
             50 μm  x {n_channels} ch
          ④ Dielectric    (Polyimide)
             100 μm
          ⑤ Ground Plane  (Ag/NbTi)
             25 μm
        ▌ 特性說明
        ─────────────────────
          • 對稱 Stripline 結構
          • 電磁場完全屏蔽於
            兩接地層之間
          • 串擾 <-60 dB (typ.)
          • 熱負載 < 4 μW/ch @ 3K'''

    ax_info.text(.08, .97, info_text, transform=ax_info.transAxes, fontsize=10, color='#C9D1D9', va='top', ha='left', linespacing=1.5, family='monospace', bbox=dict(boxstyle='round,pad=0.5', facecolor='#0D1117', edgecolor='#30363D', linewidth=1.5)
    )

    # 圖例
    legend_items = [
        (COLORS['Ground Plane (Ag/NbTi)'], 'Ground Plane (Ag/NbTi)'),
        (COLORS['Dielectric (Polyimide)'], 'Dielectric (Polyimide)'),
        (COLORS['Signal Lines'], f'Signal Lines (x{n_channels})'),
    ]
    for i, (color, label) in enumerate(legend_items):
        y_leg = 0.08 - i * 0.04
        rect = Rectangle((0.08, y_leg), 0.06, 0.025,
                         facecolor=color, edgecolor='white',
                         transform=ax_info.transAxes)
        ax_info.add_patch(rect)
        ax_info.text(0.16, y_leg + 0.012, label,
                    transform=ax_info.transAxes, fontsize=9,
                    color='#C9D1D9', va='center')

    # plt.savefig('/mnt/agents/output/cf3_gsg_front_view.png', dpi=250, facecolor='#0D1117', edgecolor='none', bbox_inches='tight')
    # plt.show()
    # print(f"✓ CF3 Front View ({n_channels} channels) saved!")
    return fig

# ========== 執行繪製：預設 8 通道 ==========
fig = 前視圖(n_channels=8)
pyplot(fig)
