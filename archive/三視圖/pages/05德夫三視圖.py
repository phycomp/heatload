from streamlit import button, download_button, markdown, session_state, sidebar, spinner, subheader, success, slider, set_page_config
from matplotlib.pyplot import close, figure
from numpy import abs, argmax, exp, linspace, sin
from io import BytesIO
# import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, Circle
from matplotlib.gridspec import GridSpec
# import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.drawing.image import Image as XLImage
# from 間距標記 import 前視間距
from streamlit import empty, pyplot
狀態=empty()
# ============================================================
# 共用參數（可從 session_state 或 UI 輸入動態取得）
# ============================================================

# GSG 7層結構（um）
LAYERS = [
    ('保護層厚度(Polyimide)',  15, 'Polyimide', '#E8D5C4', '#A0522D', False), #Protective Coating
    ('接地層厚度(Ag/NbTi)',           5, 'Ag/NbTi',   '#8B9CAD', '#4A5568', False), #Ground Plane
    ('介電層厚度(Polyimide)',         129, 'Polyimide', '#C4956A', '#744210', False), #Dielectric
    ('訊號線厚度(Ag/NbTi)',           2, 'Ag/NbTi',   '#FFD700', '#B8860B', True),  #Signal Lines
    ('介電層厚度(Polyimide)',         129, 'Polyimide', '#C4956A', '#744210', False), #Dielectric
    ('接地層厚度(Ag/NbTi)',           5, 'Ag/NbTi',   '#8B9CAD', '#4A5568', False), #Ground Plane
    ('保護層厚度(Polyimide)',  15, 'Polyimide', '#E8D5C4', '#A0522D', False), #Protective Coating
]

# 計算 Y 座標（Signal 中心為 0）
signal_idx = 3
signal_thick = LAYERS[signal_idx][1]
center_from_bottom = sum(l[1] for l in LAYERS[:signal_idx]) + signal_thick/2
y_bottoms = []
cum = -center_from_bottom
for _, thick, _, _, _, _ in LAYERS:
    y_bottoms.append(cum)
    cum += thick
y_tops = y_bottoms[1:] + [cum]


# ============================================================
# 三視圖繪製函式（回傳 BytesIO PNG）
# ============================================================
# ============================================================
# 前視圖 - 加入 Pitch 間距標註
# ============================================================

def 前視圖(n_ch=None):
    """前視圖：GSG 7層橫截面"""
    total_w = n_ch * PITCH
    fig, ax_main = subplots(figsize=(16, 10), facecolor='#0D1117')
    ax_main.set_facecolor('#0D1117')

    fig.suptitle(f'Cri/oFlex3 CF3 前視 | {n_ch} 通道數  |  GSG 7-Layer', fontsize=14, fontweight='bold', color='white', y=0.96)

    display_names = ['保護層-底', '接地層-底', '介電層-下', f'訊號線(x{n_ch})', '介電層-上', '接地層-上', '保護層-上']

    # ===== 動態字型大小計算 =====
    # 計算各層厚度和位置，判斷是否有足夠空間
    layer_heights = []  # 儲存各層高度 (mm)
    layer_positions = []  # 儲存各層中心位置

    for i, (layer, yb, yt) in enumerate(zip(LAYERS, y_bottoms, y_tops)):
        name, thick, mat, color, edge, is_sig = layer
        y_bot, y_top, thick_mm = yb/1000, yt/1000, thick/1000
        layer_heights.append(thick_mm)
        layer_positions.append((y_bot + y_top) / 2)

    狀態.code(['層位置', layer_positions, layer_heights])
    # 計算最小層間距
    min_spacing = float('inf')
    for i in range(len(layer_positions) - 1):
        spacing = layer_positions[i+1] - layer_positions[i]
        if spacing < min_spacing:
            min_spacing = spacing

    # 根據層間距動態調整字型大小
    def 動態字型(spacing, layer_index):
        """根據層間距和層索引動態計算字型大小"""
        # 基礎字型大小
        base_size = 16

        # 根據層間距調整
        if spacing < 0.04:  # 間距小於 0.04mm (40um)
            return 8
        elif spacing < 0.06:  # 間距小於 0.06mm (60um)
            return 9
        elif spacing < 0.08:  # 間距小於 0.08mm (80um)
            return 10
        elif spacing < 0.10:  # 間距小於 0.10mm (100um)
            return 11
        else:
            return base_size

        # 根據層位置調整 (靠近邊緣的可以稍微大一點)
        if layer_index == 0 or layer_index == len(layer_positions) - 1:
            # 第一層和最後一層可以稍大
            return min(base_size, font_size + 1)

        return font_size

    # 計算每層的字型大小
    font_sizes = []
    for i in range(len(layer_positions)):
        # 檢查與相鄰層的間距
        if i == 0:
            spacing = layer_positions[i+1] - layer_positions[i]
        elif i == len(layer_positions) - 1:
            spacing = layer_positions[i] - layer_positions[i-1]
        else:
            spacing = min(layer_positions[i] - layer_positions[i-1],
                         layer_positions[i+1] - layer_positions[i])

        font_size = 動態字型(spacing, i)
        font_sizes.append(font_size)

    # 如果層數多於6層，整體縮小
    if len(layer_positions) > 6:
        font_sizes = [max(8, fs - 1) for fs in font_sizes]

    # ===== 繪製各層 =====
    for i, (layer, yb, yt) in enumerate(zip(LAYERS, y_bottoms, y_tops)):
        name, thick, mat, color, edge, is_sig = layer
        y_bot, y_top, thick_mm = yb/1000, yt/1000, thick/1000

        if is_sig:
            for ch in range(n_ch):
                x_c = -total_w/2 + PITCH/2 + ch * PITCH
                ax_main.add_patch(Rectangle((x_c - SIGNAL_WIDTH/2, y_bot), SIGNAL_WIDTH, thick_mm,
                                            facecolor=color, edgecolor=edge, linewidth=1.5, zorder=5))
                if n_ch <= 12:
                    fs = 7 if n_ch > 8 else 8
                    ax_main.text(x_c, y_bot + thick_mm/2, str(ch+1), ha='center', va='center',
                                fontsize=fs, color='#333', fontweight='bold', zorder=6)
            ax_main.add_patch(Rectangle((-total_w/2 - 1, y_bot), total_w + 2, thick_mm,
                                        facecolor='#D4A574', edgecolor='none', alpha=0.2, zorder=1))
        else:
            ax_main.add_patch(Rectangle((-total_w/2 - 2, y_bot), total_w + 4, thick_mm,
                                        facecolor=color, edgecolor=edge, linewidth=1.2, alpha=0.95, zorder=3))
            if 'Ground' in name:
                for j in range(int((total_w + 4) / 0.3)):
                    x0 = -total_w/2 - 2 + j * 0.3
                    ax_main.plot([x0, x0 + thick_mm*3], [y_bot, y_top],
                                color='#5A6B7D', linewidth=0.25, alpha=0.35, zorder=4)
            if 'Protective' in name:
                for dx in linspace(-total_w/2 - 1.5, total_w/2 + 1.5, int((total_w+3)/0.8)):
                    for dy in linspace(y_bot + thick_mm*0.2, y_top - thick_mm*0.2, max(1, int(thick_mm/0.05))):
                        ax_main.plot(dx, dy, '.', color='#A0522D', markersize=1.2, alpha=0.25, zorder=4)

        # ===== 動態字型標註 =====
        label_y = (y_bot + y_top) / 2
        font_size = font_sizes[i]

        # 根據字型大小動態調整 bbox padding
        padding = 0.3 if font_size >= 10 else 0.2
        if font_size <= 8:
            padding = 0.15

        # 計算是否需要縮短顯示名稱
        display_name = display_names[i]
        if font_size <= 8 and len(display_name) > 8:
            # 字型太小時縮短名稱
            if '保護層' in display_name:
                display_name = '保護層' if '底' in display_name else '保護層-上'
            elif '接地層' in display_name:
                display_name = 'GND' if '底' in display_name else 'GND-上'
            elif '介電層' in display_name:
                display_name = '介電' if '下' in display_name else '介電-上'
            elif '訊號線' in display_name:
                display_name = f'Signal x{n_ch}'

        # 繪製標註文字 (使用動態字型大小)
        ax_main.text(-total_w/2 - 5, label_y, display_name,
                    ha='right', va='center',
                    fontsize=font_size,
                    color='white',
                    fontweight='bold',
                    zorder=10,
                    bbox=dict(boxstyle='round,pad=' + str(padding),
                             facecolor='#0D1117',
                             edgecolor=color,
                             linewidth=1.5,
                             alpha=0.95))

        # 厚度標註 (也使用動態字型)
        thick_x = total_w/2 + 3
        ax_main.annotate('', xy=(thick_x, y_bot), xytext=(thick_x, y_top),
                        arrowprops=dict(arrowstyle='<->', color='#58A6FF', lw=1.2), zorder=10)

        # 厚度文字字型大小 (比標籤小1-2號)
        thick_font_size = max(6, font_size - 2)
        ax_main.text(thick_x + 1, label_y, f'{thick} um',
                    ha='left', va='center',
                    fontsize=thick_font_size,
                    color='#58A6FF',
                    fontweight='bold',
                    zorder=10)

        if i < len(LAYERS) - 1:
            ax_main.axhline(y=y_top, xmin=0.08, xmax=0.92, color='white', linewidth=0.4, linestyle=':', alpha=0.25, zorder=2)

    # ===== PITCH 間距標註 =====
    if n_ch >= 2:
        pitch_bottom = -0.04
        x1 = -total_w/2 + PITCH/2
        x2 = -total_w/2 + PITCH/2 + PITCH

        ax_main.annotate('', xy=(x1, pitch_bottom), xytext=(x2, pitch_bottom),
                        arrowprops=dict(
                            arrowstyle='<->',
                            color='#F85149',
                            lw=2.5,
                            shrinkA=0,
                            shrinkB=0,
                            connectionstyle="arc3,rad=0.0"
                        ), zorder=20)

        ax_main.plot(x1, pitch_bottom, 'o', color='#F85149', markersize=5, zorder=20)
        ax_main.plot(x2, pitch_bottom, 'o', color='#F85149', markersize=5, zorder=20)

        ax_main.plot([x1, x1], [0.002, pitch_bottom + 0.005],
                    color='#F85149', linestyle=':', linewidth=1, alpha=0.4, zorder=15)
        ax_main.plot([x2, x2], [0.002, pitch_bottom + 0.005],
                    color='#F85149', linestyle=':', linewidth=1, alpha=0.4, zorder=15)

        pitch_label_y = pitch_bottom + 0.015
        ax_main.text((x1 + x2) / 2, pitch_label_y,
                    f'Pitch = {PITCH} mm',
                    ha='center', va='bottom',
                    fontsize=10,
                    color='#F85149',
                    fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.2',
                             facecolor='#0D1117',
                             edgecolor='#F85149',
                             alpha=0.95,
                             linewidth=1.5),
                    zorder=20)

        #if n_ch > 2:
        #    x3 = -total_w/2 + PITCH/2 + 2 * PITCH
        #    if x3 <= total_w/2:
        #        ax_main.annotate('', xy=(x2, pitch_bottom - 0.03), xytext=(x3, pitch_bottom - 0.03),
        #                        arrowprops=dict(
        #                            arrowstyle='<->',
        #                            color='#F85149',
        #                            lw=1.5,
        #                            alpha=0.4,
        #                            shrinkA=0,
        #                            shrinkB=0,
        #                            connectionstyle="arc3,rad=0.0"
        #                        ), zorder=19)
        #        ax_main.plot(x2, pitch_bottom - 0.03, 'o', color='#F85149', markersize=3, alpha=0.4, zorder=19)
        #        ax_main.plot(x3, pitch_bottom - 0.03, 'o', color='#F85149', markersize=3, alpha=0.4, zorder=19)

        #        ax_main.text((x2 + x3) / 2, pitch_bottom - 0.045,
        #                    '...',
        #                    ha='center', va='top',
        #                    fontsize=10,
        #                    color='#F85149',
        #                    alpha=0.5,
        #                    zorder=19)

    # 總厚度標註
    ax_main.annotate('', xy=(total_w/2 + 14, -0.15), xytext=(total_w/2 + 14, 0.15),
                    arrowprops=dict(arrowstyle='<->', color='#F85149', lw=2))
    ax_main.text(total_w/2 + 16, 0, f'Total\nt=300 um', ha='left', va='center', fontsize=9, color='#F85149', fontweight='bold')

    # 總寬度標註
    ax_main.annotate('', xy=(-total_w/2, 0.16), xytext=(total_w/2, 0.16),
                    arrowprops=dict(arrowstyle='<->', color='#F85149', lw=2))
    ax_main.text(0, 0.175, f'W={total_w} mm ({n_ch}ch x {PITCH}mm)', ha='center', va='bottom', fontsize=9, color='#F85149', fontweight='bold')

    # Signal Center 標註
    ax_main.axhline(y=0, color='#FF6B6B', linewidth=1.2, linestyle='-.', alpha=0.5)
    ax_main.text(total_w/2 + 0.5, 0.008, 'Signal Center (Y=0)', ha='left', va='bottom', fontsize=7, color='#FF6B6B', style='italic')

    # 設置軸範圍
    ax_main.set_xlim(-total_w/2 - 32, total_w/2 + 32)
    ax_main.set_ylim(-0.18, 0.20)
    ax_main.set_xlabel('寬度(mm)', color='white', fontsize=12)
    ax_main.set_ylabel('厚度(mm)', color='white', fontsize=12)
    ax_main.tick_params(colors='white', labelsize=8)
    for spine in ax_main.spines.values(): spine.set_color('#30363D')
    ax_main.set_title('GSG Stripline Cross-Section | Z0 = 50 Ohm | 7-Layer', fontsize=11, color='#58A6FF', fontweight='bold', pad=8)

    return fig

def 儲存前視圖(fig):
    # 狀態.code(fig)
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=180, facecolor='#0D1117', edgecolor='none', bbox_inches='tight')
    buf.seek(0)#; close(fig)
    return buf

def 側視圖(n_ch=None):
    """側視圖：長度方向輪廓"""
    total_w = n_ch * PITCH
    fig = figure(figsize=(18, 8), facecolor='#0D1117')
    ax = fig.add_subplot(111); ax.set_facecolor('#0D1117')
    fig.suptitle(f'Cri/oFlex 3 CF3  Side View  |  {n_ch} Channels  |  Length {LENGTH} mm',
                 fontsize=14, fontweight='bold', color='white', y=0.96)

    t = linspace(0, LENGTH, 500)
    y_wave = 1.5 * sin(t / 60) * exp(-t / 400)
    half_t = TOTAL_THICKNESS_MM / 2

    ax.fill_between(t, y_wave + half_t, y_wave - half_t, color='#C4956A', alpha=0.85, edgecolor='white', linewidth=1, zorder=2)
    ax.plot(t, y_wave + half_t - 0.015, 'w--', linewidth=0.6, alpha=0.5, zorder=3, label='Ground Plane')
    ax.plot(t, y_wave - half_t + 0.015, 'w--', linewidth=0.6, alpha=0.5, zorder=3)
    ax.plot(t, y_wave, color='#FFD700', linewidth=1.2, alpha=0.9, zorder=4, label='Signal Center')

    conn_len, conn_dia = 12, 6
    ax.add_patch(Rectangle((-conn_len, -conn_dia/2), conn_len, conn_dia, facecolor='#B87333', edgecolor='white', linewidth=1.5, zorder=5))
    for j in range(4):
        ax.plot([-conn_len + 2 + j*2.2, -conn_len + 2 + j*2.2], [-conn_dia/2, conn_dia/2], 'w-', linewidth=0.8, alpha=0.7, zorder=6)
    ax.add_patch(Rectangle((-conn_len - 3, -0.15), 3, 0.3, facecolor='#C0C0C0', edgecolor='white', zorder=5))

    ax.add_patch(Rectangle((LENGTH, -conn_dia/2), conn_len, conn_dia, facecolor='#B87333', edgecolor='white', linewidth=1.5, zorder=5))
    for j in range(4):
        ax.plot([LENGTH + j*2.2, LENGTH + j*2.2], [-conn_dia/2, conn_dia/2], 'w-', linewidth=0.8, alpha=0.7, zorder=6)
    ax.add_patch(Rectangle((LENGTH + conn_len, -0.15), 3, 0.3, facecolor='#C0C0C0', edgecolor='white', zorder=5))

    max_curve_idx = argmax(abs(y_wave))
    mc_x, mc_y = t[max_curve_idx], y_wave[max_curve_idx]
    ax.add_patch(Circle((mc_x - 5, mc_y), 5, fill=False, edgecolor='#FF6B6B', linewidth=1.5, linestyle='--', zorder=7))
    ax.annotate(f'R >= 5 mm', xy=(mc_x - 5, mc_y + 6), fontsize=9, color='#FF6B6B', ha='center', fontweight='bold')

    ax.annotate('', xy=(0, -conn_dia/2 - 4), xytext=(LENGTH, -conn_dia/2 - 4), arrowprops=dict(arrowstyle='<->', color='#F85149', lw=2))
    ax.text(LENGTH/2, -conn_dia/2 - 6, f'L = {LENGTH} mm', ha='center', va='top', fontsize=10, color='#F85149', fontweight='bold')
    ax.annotate('', xy=(LENGTH + conn_len + 10, -half_t), xytext=(LENGTH + conn_len + 10, half_t), arrowprops=dict(arrowstyle='<->', color='#58A6FF', lw=1.5))
    ax.text(LENGTH + conn_len + 14, 0, f't = {TOTAL_THICKNESS_MM*1000:.0f} um', ha='left', va='center', fontsize=9, color='#58A6FF', fontweight='bold', rotation=90)
    ax.text(LENGTH/2, conn_dia/2 + 4, f'{n_ch} Channels  |  Pitch {PITCH} mm  |  Total Width {total_w} mm',
            ha='center', va='bottom', fontsize=10, color='white', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#161B22', edgecolor='#58A6FF', linewidth=1.5))

    ax.set_xlim(-20, LENGTH + conn_len + 30)
    ax.set_ylim(-conn_dia/2 - 12, conn_dia/2 + 12)
    ax.set_aspect('equal')
    ax.set_xlabel('Length (mm)', color='white', fontsize=11)
    ax.set_ylabel('Height (mm)', color='white', fontsize=11)
    ax.tick_params(colors='white')
    for spine in ax.spines.values(): spine.set_color('#30363D')
    ax.set_title('Flexible Stripline Profile | Bend Radius >= 5 mm | Connector: SMA/SMP', fontsize=11, color='#58A6FF', fontweight='bold', pad=10)
    ax.legend(loc='upper right', facecolor='#161B22', edgecolor='#444466', labelcolor='white', fontsize=9)

    return fig
def 儲存側視圖(fig):
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=180, facecolor='#0D1117', edgecolor='none', bbox_inches='tight')
    buf.seek(0)#; close(fig)
    return buf


def 上視圖(n_ch=None):
    """上視圖（俯視圖）：平面佈局"""
    total_w = n_ch * PITCH
    fig = figure(figsize=(18, 10), facecolor='#0D1117')
    ax = fig.add_subplot(111); ax.set_facecolor('#0D1117')
    fig.suptitle(f'Cri/oFlex 3 CF3  Top View  |  {n_ch} Channels  |  Length {LENGTH} mm',
                 fontsize=14, fontweight='bold', color='white', y=0.96)

    conn_len, conn_dia = 12, 6
    ax.add_patch(Rectangle((conn_len, -total_w/2), LENGTH, total_w, facecolor='#C4956A', edgecolor='white', linewidth=1.5, alpha=0.9, zorder=2))

    for i in range(n_ch):
        y = -total_w/2 + PITCH/2 + i * PITCH
        ax.add_patch(Rectangle((conn_len + 5, y - SIGNAL_WIDTH/2), LENGTH - 10, SIGNAL_WIDTH,
                                facecolor='#FFD700', edgecolor='#B8860B', linewidth=0.5, alpha=0.85, zorder=3))
        ax.text(conn_len + LENGTH/2, y, f'CH{i+1}', ha='center', va='center', fontsize=7, color='#333', fontweight='bold', zorder=4)

    for i in range(n_ch):
        y = -total_w/2 + PITCH/2 + i * PITCH
        ax.add_patch(Rectangle((0, y - conn_dia/2), conn_len, conn_dia, facecolor='#B87333', edgecolor='white', linewidth=1, zorder=5))
        for j in range(3):
            ax.plot([conn_len - 4 + j*2, conn_len - 4 + j*2], [y - conn_dia/2, y + conn_dia/2], 'w-', linewidth=0.5, zorder=6)
        ax.add_patch(Rectangle((-3, y - 0.15), 3, 0.3, facecolor='#C0C0C0', edgecolor='white', zorder=5))

    for i in range(n_ch):
        y = -total_w/2 + PITCH/2 + i * PITCH
        ax.add_patch(Rectangle((conn_len + LENGTH, y - conn_dia/2), conn_len, conn_dia, facecolor='#B87333', edgecolor='white', linewidth=1, zorder=5))
        for j in range(3):
            ax.plot([conn_len + LENGTH + j*2, conn_len + LENGTH + j*2], [y - conn_dia/2, y + conn_dia/2], 'w-', linewidth=0.5, zorder=6)
        ax.add_patch(Rectangle((conn_len + LENGTH + conn_len, y - 0.15), 3, 0.3, facecolor='#C0C0C0', edgecolor='white', zorder=5))

    ax.add_patch(Rectangle((conn_len + LENGTH*0.3, -total_w/2 - 1), LENGTH*0.15, total_w + 2,
                            facecolor='#4A90D9', edgecolor='cyan', linewidth=1.5, linestyle='--', alpha=0.25, zorder=1))
    ax.text(conn_len + LENGTH*0.375, total_w/2 + 3, 'Integrated Filters\n& Attenuators', ha='center', va='bottom', fontsize=8, color='cyan', style='italic')

    ax.annotate('', xy=(conn_len, total_w/2 + 8), xytext=(conn_len + LENGTH, total_w/2 + 8), arrowprops=dict(arrowstyle='<->', color='#F85149', lw=1.5))
    ax.text(conn_len + LENGTH/2, total_w/2 + 10, f'L = {LENGTH} mm', ha='center', va='bottom', color='#F85149', fontsize=9)
    ax.annotate('', xy=(conn_len + LENGTH + conn_len + 8, -total_w/2), xytext=(conn_len + LENGTH + conn_len + 8, total_w/2), arrowprops=dict(arrowstyle='<->', color='#F85149', lw=1.5))
    ax.text(conn_len + LENGTH + conn_len + 12, 0, f'W = {total_w} mm\n({n_ch} ch x {PITCH} mm)', ha='left', va='center', color='#F85149', fontsize=9, rotation=90)
    ax.annotate('', xy=(conn_len + LENGTH/2, -total_w/2 + PITCH/2), xytext=(conn_len + LENGTH/2, -total_w/2 + PITCH/2 + PITCH), arrowprops=dict(arrowstyle='<->', color='#3FB950', lw=1.2))
    ax.text(conn_len + LENGTH/2 + 3, -total_w/2 + PITCH, f'Pitch = {PITCH} mm', ha='left', va='center', color='#3FB950', fontsize=8)

    ax.set_xlim(-15, conn_len + LENGTH + conn_len + 35)
    ax.set_ylim(-total_w/2 - 15, total_w/2 + 18)
    ax.set_aspect('equal')
    ax.set_xlabel('Length (mm)', color='white', fontsize=11)
    ax.set_ylabel('Width (mm)', color='white', fontsize=11)
    ax.tick_params(colors='white')
    for spine in ax.spines.values(): spine.set_color('#30363D')
    ax.set_title('Plan View | 8-Channel Parallel Stripline | Integrated Filtering', fontsize=11, color='#58A6FF', fontweight='bold', pad=10)

    legend_items = [('#C4956A', 'Polyimide Substrate'), ('#FFD700', 'Signal Lines (Ag/NbTi)'), ('#B87333', 'SMA/SMP Connector'), ('#4A90D9', 'Filter/Attenuator Zone')]
    for i, (color, label) in enumerate(legend_items):
        x_pos = 0.02 + i * 0.22
        ax.add_patch(Rectangle((x_pos, 0.02), 0.03, 0.025, facecolor=color, edgecolor='white', linewidth=0.5, transform=ax.transAxes))
        ax.text(x_pos + 0.035, 0.032, label, transform=ax.transAxes, fontsize=8, color='#AAAAAA', va='center')

    return fig

def 儲存上視圖(fig):
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=180, facecolor='#0D1117', edgecolor='none', bbox_inches='tight')
    buf.seek(0)   #; close(fig)
    return buf


# ============================================================
# Excel 生成函式（四個分頁：三視圖 + 規格總表）
# ============================================================

def 匯出(n_ch=None, 前視=None, 側視=None, 上視=None):
    total_w = n_ch * PITCH

    # 繪製三視圖
    front_buf = 儲存前視圖(前視)
    side_buf = 儲存側視圖(側視)
    top_buf = 儲存上視圖(上視)

    wb = Workbook()

    def make_title(ws, text):
        ws.append([text])
        ws.merge_cells("A1:H1")
        ws["A1"].font = Font(size=14, bold=True, color="FFFFFF")
        ws["A1"].fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 28

    def make_subtitle(ws, text, row=2):
        ws.cell(row=row, column=1, value=text)
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=8)
        ws.cell(row=row, column=1).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=1).font = Font(size=10, italic=True)

    # ---------- Sheet 1: Front_View
    ws1 = wb.active; ws1.title = "Front_View"
    make_title(ws1, f"Cri/oFlex 3 CF3  Front View (Cross-Section)  |  {n_ch} Channels")
    make_subtitle(ws1, f"GSG 7-Layer Stripline  |  Width: {total_w} mm  |  厚度: .3 mm")

    img_front = XLImage(front_buf); img_front.width = 720; img_front.height = 440
    ws1.add_image(img_front, "A4")

    table_start = 30
    ws1.cell(row=table_start, column=1, value="Layer Stack-up Detail")
    ws1.merge_cells(start_row=table_start, start_column=1, end_row=table_start, end_column=8)
    ws1.cell(row=table_start, column=1).font = Font(size=12, bold=True, color="FFFFFF")
    ws1.cell(row=table_start, column=1).fill = PatternFill(start_color="2E5C8A", end_color="2E5C8A", fill_type="solid")
    ws1.cell(row=table_start, column=1).alignment = Alignment(horizontal="center", vertical="center")

    headers = ["Layer No.", "Layer Name", "Material", "Thickness (um)", "Thickness (mm)", "Y-Bottom (um)", "Y-Top (um)", "Function"]
    for col, h in enumerate(headers, 1):
        cell = ws1.cell(row=table_start+1, column=col, value=h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    color_map = {"Protective": "E8D5C4", "Ground": "8B9CAD", "Dielectric": "C4956A", "Signal": "FFD700"}
    layer_funcs = ['Mechanical protection', 'EM shielding / Return path', 'Dielectric isolation',
                   f'Signal ({n_ch} ch)', 'Dielectric isolation', 'EM shielding / Return path', 'Mechanical protection']

    for i, ((name, thick, mat, color, edge, is_sig), yb, yt, func) in enumerate(zip(LAYERS, y_bottoms, y_tops, layer_funcs), 1):
        row = table_start + 1 + i
        ws1.append([i, name, mat, thick, round(thick/1000, 3), round(yb, 1), round(yt, 1), func])
        fill_key = next((k for k in color_map if k in name), "FFFFFF")
        for cell in ws1[row]:
            cell.fill = PatternFill(start_color=color_map[fill_key], end_color=color_map[fill_key], fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")

    total_row = table_start + 2 + len(LAYERS)
    ws1.append(["", "TOTAL", "", 300, 0.3, "", "", ""])
    for cell in ws1[total_row]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for col, w in zip("ABCDEFGH", [12, 36, 16, 16, 16, 16, 16, 35]):
        ws1.column_dimensions[col].width = w

    # ---------- Sheet 2: Side_View
    ws2 = wb.create_sheet("Side_View")
    make_title(ws2, f"Cri/oFlex 3 CF3  Side View (Profile)  |  {n_ch} Channels")
    make_subtitle(ws2, f"Length: {LENGTH} mm  |  Bend Radius >= 5 mm  |  Connector: SMA/SMP")

    img_side = XLImage(side_buf); img_side.width = 720; img_side.height = 340
    ws2.add_image(img_side, "A4")

    table_start = 24
    ws2.cell(row=table_start, column=1, value="Side View Dimensions & Specifications")
    ws2.merge_cells(start_row=table_start, start_column=1, end_row=table_start, end_column=6)
    ws2.cell(row=table_start, column=1).font = Font(size=12, bold=True, color="FFFFFF")
    ws2.cell(row=table_start, column=1).fill = PatternFill(start_color="2E5C8A", end_color="2E5C8A", fill_type="solid")
    ws2.cell(row=table_start, column=1).alignment = Alignment(horizontal="center", vertical="center")

    side_specs = [
        ["Parameter", "Value", "Unit", "Description"],
        ["Total Length", LENGTH, "mm", "Flex cable length (customizable 200-1000 mm)"],
        ["Total Thickness", 0.3, "mm", "Cross-section thickness (300 um)"],
        ["Bend Radius", 5, "mm", "Minimum allowable bend radius"],
        ["Connector Length", 12, "mm", "SMA/SMP connector body length"],
        ["Connector Diameter", 6, "mm", "SMA/SMP connector outer diameter"],
        ["Channels", n_ch, "ch", f"Parallel signal channels (Pitch {PITCH} mm)"],
        ["Total Width", total_w, "mm", f"{n_ch} ch x {PITCH} mm"],
        ["Flexibility", "High", "", "Polyimide substrate allows non-LOS routing"],
    ]
    for row_data in side_specs:
        ws2.append(row_data)
    for cell in ws2[table_start+1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for r in range(table_start+2, ws2.max_row+1):
        if r % 2 == 0:
            for cell in ws2[r]:
                cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        for cell in ws2[r]:
            cell.alignment = Alignment(horizontal="center", vertical="center")
    for col, w in zip("ABCD", [28, 16, 12, 50]):
        ws2.column_dimensions[col].width = w

    # ---------- Sheet 3: Top_View
    ws3 = wb.create_sheet("Top_View")
    make_title(ws3, f"Cri/oFlex 3 CF3  Top View (Plan View)  |  {n_ch} Channels")
    make_subtitle(ws3, f"Length: {LENGTH} mm  |  Width: {total_w} mm  |  Pitch: {PITCH} mm")

    img_top = XLImage(top_buf); img_top.width = 720; img_top.height = 400
    ws3.add_image(img_top, "A4")

    table_start = 28
    ws3.cell(row=table_start, column=1, value="Channel Layout (Top View)")
    ws3.merge_cells(start_row=table_start, start_column=1, end_row=table_start, end_column=6)
    ws3.cell(row=table_start, column=1).font = Font(size=12, bold=True, color="FFFFFF")
    ws3.cell(row=table_start, column=1).fill = PatternFill(start_color="2E5C8A", end_color="2E5C8A", fill_type="solid")
    ws3.cell(row=table_start, column=1).alignment = Alignment(horizontal="center", vertical="center")

    ch_headers = ["Channel", "Center X (mm)", "Left Edge (mm)", "Right Edge (mm)", "Signal Width (mm)", "Gap to Next (mm)"]
    for col, h in enumerate(ch_headers, 1):
        cell = ws3.cell(row=table_start+1, column=col, value=h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for ch in range(n_ch):
        x_c = -total_w/2 + PITCH/2 + ch * PITCH
        gap = round(PITCH - SIGNAL_WIDTH, 3) if ch < n_ch - 1 else "N/A (edge)"
        ws3.append([f"CH{ch+1}", round(x_c, 2), round(x_c - SIGNAL_WIDTH/2, 3),
                    round(x_c + SIGNAL_WIDTH/2, 3), SIGNAL_WIDTH, gap])
        if ch % 2 == 0:
            for cell in ws3[ws3.max_row]:
                cell.fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
        for cell in ws3[ws3.max_row]:
            cell.alignment = Alignment(horizontal="center", vertical="center")

    ws3.append(["SUMMARY", f"Total Width = {total_w} mm", "", "", f"Pitch = {PITCH} mm", ""])
    for cell in ws3[ws3.max_row]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for col, w in zip("ABCDEF", [12, 16, 16, 16, 18, 18]):
        ws3.column_dimensions[col].width = w

    # ---------- Sheet 4: Specifications
    ws4 = wb.create_sheet("Specifications")
    make_title(ws4, "Cri/oFlex 3 CF3 - Complete Specifications")
    make_subtitle(ws4, "General / Electrical / Thermal / Mechanical parameters")

    """
    specs = [
        ["Category", "Parameter", "Value", "Unit", "Notes"],
        ["General", "Product Name", "Cri/oFlex 3 (CF3)", "", "Delft Circuits"],
        ["General", "Channels", n_ch, "ch", "Per flex cable"],
        ["General", "Channel-to-Channel Pitch", PITCH, "mm", "Standard spacing"],
        ["General", "Total Width", total_w, "mm", f"{n_ch} ch x {PITCH} mm"],
        ["General", "Total Thickness", 0.3, "mm", "300 um (7-layer GSG)"],
        ["General", "Length Range", "200 - 1000", "mm", "Customizable"],
        ["General", "Bend Radius", 5, "mm", "Minimum"],
        ["", "", "", "", ""],
        ["Electrical", "Characteristic Impedance", 50, "Ohm", "Stripline design"],
        ["Electrical", "Frequency Range", "DC - 18", "GHz", "Microwave operation"],
        ["Electrical", "Signal Line Width", SIGNAL_WIDTH, "mm", "Center conductor"],
        ["Electrical", "Signal Line Thickness", 2, "um", "Ag/NbTi thin film"],
        ["Electrical", "Dielectric Thickness", 129, "um", "Each side (Polyimide)"],
        ["Electrical", "Ground Plane Thickness", 5, "um", "Ag/NbTi, each side"],
        ["Electrical", "Protective Coating", 15, "um", "Polyimide, each side"],
        ["Electrical", "Crosstalk", "< -60", "dB", "Typical adjacent channels"],
        ["", "", "", "", ""],
        ["Thermal", "Heat Load (Ag)", "< 125", "uW/ch", "@ 4-40K, L=0.4m"],
        ["Thermal", "Heat Load (NbTi)", "~ 20", "nW/ch", "@ 10-350mK, L=0.2m"],
        ["Thermal", "Operating Temperature", "10^-3 ~ 400", "K", "mK to room temp"],
        ["", "", "", "", ""],
        ["Mechanical", "Substrate Material", "Polyimide (Kapton)", "", "Flexible dielectric"],
        ["Mechanical", "Conductor Material", "Ag / NbTi", "", "Silver or superconducting"],
        ["Mechanical", "Connector Type", "SMA (f) / SMP (m)", "", "Right-angle or straight"],
        ["Mechanical", "Vacuum Leak Rate", "< 10^-6", "mbar L/s", "Integrated feedthrough"],
        ["Mechanical", "Flexibility", "High", "", "Non-LOS port routing"],
    ]
    """
    specs = [
        ["類別", "參數", "值", "單位", "備註"],
        ["一般性", "產品名", "Cri/oFlex 3 (CF3)", "", "Delft Circuits"],
        ["一般性", "通道數", n_ch, "ch", "Per flex cable"],
        ["一般性", "間距", PITCH, "mm", "標準距"],
        ["一般性", "總寬度", total_w, "mm", f"{n_ch}通道數x{PITCH}間距 mm"],
        ["一般性", "總厚度", 0.3, "mm", "300 um (7-layer GSG)"],
        ["一般性", "總長度", "200 - 1000", "mm", "客製化"],
        ["一般性", "彎曲半徑", 5, "mm", "Minimum"],
        ["", "", "", "", ""],
        ["電性", "特性阻抗", 50, "Ohm", "Stripline design"],
        ["電性", "頻率範圍", "DC - 18", "GHz", "微波波段"],
        ["電性", "訊號線寬度", SIGNAL_WIDTH, "mm", "Center conductor"],
        ["電性", "訊號線厚度", 2, "um", "Ag/NbTi薄膜"],
        ["電性", "介電層厚度", 129, "um", "每邊(Polyimide)"],
        ["電性", "接地層厚度", 5, "um", "Ag/NbTi 每邊"],
        ["電性", "保護層覆體", 15, "um", "Polyimide 每邊"],
        ["電性", "串擾", "< -60", "dB", "Typical adjacent channels"],
        ["", "", "", "", ""],
        ["熱性", "熱負載(Ag)", "< 125", "uW/ch", "@ 4-40K, L=0.4m"],
        ["熱性", "熱負載(NbTi)", "~ 20", "nW/ch", "@ 10-350mK, L=0.2m"],
        ["熱性", "操作溫度", "10^-3 ~ 400", "K", "mK室溫"],
        ["", "", "", "", ""],
        ["機構", "基底材質", "Polyimide (Kapton)", "", "柔性介電"],
        ["機構", "導體材質", "Ag / NbTi", "", "銀或超導"],
        ["機構", "連接器類型", "SMA (f) / SMP (m)", "", "直角/筆直"],
        ["機構", "真空逸出率", "< 10^-6", "mbar L/s", "Integrated feedthrough"],
        ["機構", "柔性", "High", "", "Non-LOS port routing"],
    ]
    for row_data in specs:
        ws4.append(row_data)
    for cell in ws4[4]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for r in range(5, ws4.max_row + 1):
        if ws4.cell(row=r, column=1).value == "":
            for cell in ws4[r]:
                cell.fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
        elif r % 2 == 0:
            for cell in ws4[r]:
                cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        for cell in ws4[r]:
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for col, w in zip("ABCDE", [18, 30, 20, 12, 40]):
        ws4.column_dimensions[col].width = w

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


# ============================================================
# Streamlit UI 側邊欄下載區
# ============================================================

from streamlit import sidebar, radio, text_input, empty
MENU, 表單=[], ['前視圖', '側視圖', '上視圖', '匯出表']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  subheader("📥 Export Three-View Drawing")
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  # srch=text_input('搜尋', '預設值', placeholder='搜尋')
  # N_CHANNELS = session_state.get("n_channels", 8)
  # n_ch = session_state.get("n_channels", 8)
  PITCH = 2.
  SIGNAL_WIDTH = .4
  LENGTH = 400
  TOTAL_THICKNESS_MM = .3
  通道數 = slider("通道數", 2, 16, 8, 2)
狀態=empty()
# 狀態.code([])
def 繪制三視():
  try:
    前視=session_state['前視圖']
  except:
    前視=session_state['前視圖']=前視圖(n_ch=通道數)
    # 前視=session_state['前視圖']=前視間距(n_ch=通道數)
  try:
    側視=session_state['側視圖']
  except:
    側視=session_state['側視圖']=側視圖(n_ch=通道數)
  try:
    上視=session_state['上視圖']
  except:
    上視=session_state['上視圖']=上視圖(n_ch=通道數)
  return 前視, 側視, 上視
set_page_config( page_title="動態通道數", page_icon="📡", layout="wide", initial_sidebar_state="expanded")
from matplotlib.pyplot import rcParams, savefig, show, subplots, tight_layout
from streamlit import pyplot
前視, 側視, 上視=繪制三視()
if menu==len(表單):
  pass
elif menu==MENU[0]: #前視圖
  pyplot(前視)
elif menu==MENU[1]: #
  # 側視buf=session_state['側視']=儲存側視圖(fig)
  pyplot(側視)
elif menu==MENU[2]: #
  # 上視buf=session_state['上視']=儲存上視圖(fig)
  pyplot(上視)
elif menu==MENU[3]: #
    # if button("📊 Generate Three-View Excel", use_container_width=True):
        # with spinner("Generating Front / Side / Top views + Specifications..."):
    前視圖=session_state['前視圖']
    側視圖=session_state['側視圖']
    上視圖=session_state['上視圖']
    excel_bytes = 匯出(n_ch=通道數, 前視=前視圖, 側視=側視圖, 上視=上視圖)
    session_state["three_view_excel"] = excel_bytes
    success("Three-View Excel ready!")

    # if "three_view_excel" in session_state:
    download_button(
        label="⬇️ Download CF3_ThreeView_Spec.xlsx",
        data=session_state["three_view_excel"],
        file_name=f"CF3_ThreeView_Spec_{通道數}ch.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
