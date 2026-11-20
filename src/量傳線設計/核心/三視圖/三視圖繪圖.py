from streamlit import session_state
from matplotlib.pyplot import subplots
from .佈局計算 import LAYER_DEFS
from matplotlib.patches import Rectangle, Circle
from numpy import abs, argmax, exp, linspace, sin
from matplotlib.pyplot import close, figure, subplots, tight_layout, rcParams
# 字型=中文字型()
rcParams['font.sans-serif'] = ['AR PL UKai CN']  #, 'Segoe UI Emoji', 'sans-serif']
# rcParams['font.sans-serif'] = ['Noto Sans CJK JP']
# rcParams['axes.unicode_minus'] = False # 修正負號顯示

def 繪制三視(佈局, conductor_color=None, dielectric_color=None):
    前視圖 = 繪製前視(佈局, conductor_color=conductor_color, dielectric_color=dielectric_color)
    側視圖 = 繪製側視(佈局, conductor_color=conductor_color or '#FFD700',
                      dielectric_color=dielectric_color or '#C4956A')
    上視圖 = 繪製上視(佈局, conductor_color=conductor_color or '#FFD700',
                      dielectric_color=dielectric_color or '#C4956A')
    return 前視圖, 側視圖, 上視圖

def 切換視圖(佈局, view, conductor_color=None, dielectric_color=None):
    """視圖切換便利函式。view: '前'/'側'/'上'"""
    if view in ("前", "front", "前視圖"):
        return 繪製前視(佈局, conductor_color=conductor_color, dielectric_color=dielectric_color)
    if view in ("側", "side", "側視圖"):
        return 繪製側視(佈局, conductor_color=conductor_color or '#FFD700',
                       dielectric_color=dielectric_color or '#C4956A')
    if view in ("上", "top", "上視圖"):
        return 繪製上視(佈局, conductor_color=conductor_color or '#FFD700',
                       dielectric_color=dielectric_color or '#C4956A')
    raise ValueError(f"未知視圖: {view}")

def 繪製全部視圖(佈局, conductor_color=None, dielectric_color=None):
    """繪製全部三視圖，回傳 dict。"""
    前, 側, 上 = 繪制三視(佈局, conductor_color=conductor_color, dielectric_color=dielectric_color)
    return {"前視圖": 前, "側視圖": 側, "上視圖": 上}
# 字型=配置字型()
# rcParams['font.sans-serif'] = ['Microsoft JhengHei']
# rcParams['axes.unicode_minus'] = False # 步驟 2：修復負號顯示問題
# rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS', 'Heiti TC', 'SimHei']
# rcParams['font.sans-serif'] = ['Noto Sans CJK TC']#, 'noto-fonts-cjk'', 'sans-serif', 'AR PL UKai CN']
# rcParams['axes.unicode_minus'] = False

# ============================================================
# 3. 前視圖繪製 - 優化文字大小
# ============================================================

def 繪製前視(layout: LayoutCalculator, 字型=None, conductor_color=None, dielectric_color=None): #
    """繪製前視圖 - 左右錯置解決標註重疊"""

    n_ch = layout.通道數
    total_w = layout.線總寬
    total_h = layout.線厚度m
    layer_positions = layout.層位置
    font_sizes = layout.layer_font_sizes
    margins = layout.margins
    fig_size = layout.figure_size

    # 創建圖形
    fig, ax = subplots(figsize=fig_size, facecolor='#0D1117') #
    ax.set_facecolor('#0D1117')

    # 標題
    title_fs = layout.get_font_size('title')
    fig.suptitle(f'U-leam UF1 前視 | {n_ch} 通道數 | GSG 7層疊構', fontsize=title_fs, fontweight='bold', color='white', y=0.96) #fontproperties=字型, Cri/oFlex3 CF3

    # 顯示名稱
    display_names_full = ['保護層-底', '接地層-底', '介電層-下', f'訊號線(x{n_ch})', '介電層-上', '接地層-上', '保護層-上']
    display_names_short = ['保護-底', 'GND-底', '介電-下', f'訊號', '介電-上', 'GND-上', '保護-上']

    # 計算各層中心位置
    layer_centers = [p['center_mm'] for p in layer_positions]
    layer_thicks = [p['thick_mm'] for p in layer_positions]

    # ===== 檢測標註重疊並決定左右位置 =====
    label_positions = []  # (y_position, side)  side: 'left' or 'right'

    for i in range(len(layer_positions)):
        center_y = layer_centers[i]
        thick = layer_thicks[i]
        fs = font_sizes[i]

        # 計算標註高度
        label_height = fs * 0.035

        # 預設為左側
        side = 'left'
        adjusted_y = center_y

        # 檢查與相鄰層的重疊
        overlap_detected = False
        overlap_with = []

        # 檢查上一層
        if i > 0:
            prev_center = layer_centers[i-1]
            prev_fs = font_sizes[i-1]
            prev_label_height = prev_fs * 0.035
            gap = center_y - prev_center

            if gap < (label_height + prev_label_height) * 1.3:
                overlap_detected = True
                overlap_with.append(i-1)

        # 檢查下一層
        if i < len(layer_positions) - 1:
            next_center = layer_centers[i+1]
            next_fs = font_sizes[i+1]
            next_label_height = next_fs * 0.035
            gap = next_center - center_y

            if gap < (label_height + next_label_height) * 1.3:
                overlap_detected = True
                overlap_with.append(i+1)

        # 如果檢測到重疊，進行左右錯置
        if overlap_detected:
            # 對於薄層（保護層、接地層），使用左右錯置
            if thick < 0.02:  # < 20um
                # 檢查相鄰層的標註側
                neighbor_sides = []
                for neighbor_idx in overlap_with:
                    if neighbor_idx < len(label_positions):
                        neighbor_sides.append(label_positions[neighbor_idx][1])

                # 如果相鄰層在左側，則此層放到右側
                if 'left' in neighbor_sides:
                    side = 'right'
                    # 調整Y位置稍微偏移
                    if i < len(layer_positions) // 2:
                        adjusted_y = center_y + thick * 0.2
                    else:
                        adjusted_y = center_y - thick * 0.2
                else:
                    side = 'left'
                    if i < len(layer_positions) // 2:
                        adjusted_y = center_y + thick * 0.2
                    else:
                        adjusted_y = center_y - thick * 0.2
            else:
                # 厚層保持左側
                side = 'left'
                adjusted_y = center_y
        else:
            side = 'left'
            adjusted_y = center_y

        label_positions.append((adjusted_y, side))

    # 繪製各層
    for i, (layer_def, pos, fs, (label_y, side)) in enumerate(zip(LAYER_DEFS, layer_positions, font_sizes, label_positions)):
        y_bot = pos['y_bot_mm']
        y_top = pos['y_top_mm']
        thick_mm = pos['thick_mm']
        color = layer_def['color']
        edge = layer_def['edge']
        is_signal = layer_def['is_signal']
        if is_signal and conductor_color:
            color = conductor_color
        elif '介電' in layer_def['name'] and dielectric_color:
            color = dielectric_color

        if is_signal:
            # 信號線
            signal_w = min(layout.訊號寬度, layout.訊號間距 * 0.35)
            for ch in range(n_ch):
                x_c = -total_w/2 + layout.訊號間距/2 + ch * layout.訊號間距
                ax.add_patch(Rectangle((x_c - signal_w/2, y_bot), signal_w, thick_mm,
                                      facecolor=color, edgecolor=edge, linewidth=1.5, zorder=5))
                if n_ch <= 12:
                    ch_fs = max(7, fs * 0.7)
                    ax.text(x_c, y_bot + thick_mm/2, str(ch+1), ha='center', va='center',
                           fontsize=ch_fs, color='#333', fontweight='bold', zorder=6)

            ax.add_patch(Rectangle((-total_w/2 - 1, y_bot), total_w + 2, thick_mm,
                                  facecolor='#D4A574', edgecolor='none', alpha=0.2, zorder=1))
        else:
            ax.add_patch(Rectangle((-total_w/2 - 2, y_bot), total_w + 4, thick_mm,
                                  facecolor=color, edgecolor=edge, linewidth=1.2, alpha=0.95, zorder=3))

            if '接地' in layer_def['name']:
                for j in range(int((total_w + 4) / 0.3)):
                    x0 = -total_w/2 - 2 + j * 0.3
                    ax.plot([x0, x0 + thick_mm*3], [y_bot, y_top],
                           color='#5A6B7D', linewidth=0.25, alpha=0.35, zorder=4)

            if '保護' in layer_def['name']:
                for dx in linspace(-total_w/2 - 1.5, total_w/2 + 1.5, int((total_w+3)/0.8)):
                    for dy in linspace(y_bot + thick_mm*0.2, y_top - thick_mm*0.2, max(1, int(thick_mm/0.05))):
                        ax.plot(dx, dy, '.', color='#A0522D', markersize=1.2, alpha=0.25, zorder=4)

        # ===== 層標註 - 根據側邊決定位置 =====
        if fs <= 10:
            display_name = display_names_short[i]
        else:
            display_name = display_names_full[i]

        # BBox padding
        if fs >= 14:
            padding = 0.35
        elif fs >= 11:
            padding = 0.28
        else:
            padding = 0.2

        # 根據側邊決定標註位置
        if side == 'left':
            # 左側標註
            x_pos = layout.layer_label_x
            ha = 'right'
            # 添加指示線 (從層到標註)
            ax.plot([-total_w/2 - 1.5, x_pos + 0.5], [label_y, label_y],
                   color=color, linewidth=0.5, linestyle=':', alpha=0.3, zorder=8)
        else:
            # 右側標註 (與厚度標註同側)
            x_pos = layout.thick_label_x + 2.0
            ha = 'left'
            # 添加指示線 (從層到標註)
            ax.plot([total_w/2 + 1.5, x_pos - 0.5], [label_y, label_y],
                   color=color, linewidth=0.5, linestyle=':', alpha=0.3, zorder=8)

        # 繪製標註
        ax.text(x_pos, label_y, display_name,
               ha=ha, va='center',
               fontsize=fs,
               color='white',
               fontweight='bold',
               zorder=10,
               bbox=dict(boxstyle='round,pad=' + str(padding),
                        facecolor='#0D1117',
                        edgecolor=color,
                        linewidth=1.8,
                        alpha=0.95))

        # ===== 厚度標註 (右側) =====
        if side == 'left':
            # 只有左側標註時，厚度標註在右側
            thick_x = layout.thick_label_x
            arrow_lw = 1.2 * layout.字型縮放
            ax.annotate('', xy=(thick_x, y_bot), xytext=(thick_x, y_top),
                       arrowprops=dict(arrowstyle='<->', color='#58A6FF',
                                     lw=arrow_lw), zorder=10)

            thick_fs = max(8, fs - 2)
            ax.text(thick_x + 1.0, label_y, f'{pos["thick_um"]}um',
                   ha='left', va='center',
                   fontsize=thick_fs,
                   color='#58A6FF',
                   fontweight='bold',
                   zorder=10)

        # 層間分隔線
        if i < len(LAYER_DEFS) - 1:
            ax.axhline(y=y_top, xmin=0.08, xmax=0.92, color='white',
                      linewidth=0.4, linestyle=':', alpha=0.25, zorder=2)

    # ===== Pitch標註 =====
    if n_ch >= 2:
        x1 = -total_w/2 + layout.訊號間距/2
        x2 = -total_w/2 + layout.訊號間距/2 + layout.訊號間距

        pitch_fs = layout.get_font_size('pitch')
        arrow_lw = 2.0 * layout.字型縮放

        ax.annotate('', xy=(x1, layout.pitch_y), xytext=(x2, layout.pitch_y),
                   arrowprops=dict(arrowstyle='<->', color='#F85149',
                                 lw=arrow_lw,
                                 shrinkA=0, shrinkB=0,
                                 connectionstyle="arc3,rad=0.0"), zorder=20)

        marker_size = max(5, 4 * layout.字型縮放)
        ax.plot(x1, layout.pitch_y, 'o', color='#F85149', markersize=marker_size, zorder=20)
        ax.plot(x2, layout.pitch_y, 'o', color='#F85149', markersize=marker_size, zorder=20)

        ax.plot([x1, x1], [0.002, layout.pitch_y + 0.005],
               color='#F85149', linestyle=':', linewidth=1.0 * layout.字型縮放,
               alpha=0.4, zorder=15)
        ax.plot([x2, x2], [0.002, layout.pitch_y + 0.005],
               color='#F85149', linestyle=':', linewidth=1.0 * layout.字型縮放,
               alpha=0.4, zorder=15)

        ax.text((x1 + x2) / 2, layout.pitch_y + 0.02 * layout.字型縮放,
               f'Pitch = {layout.訊號間距} mm',
               ha='center', va='bottom',
               fontsize=pitch_fs,
               color='#F85149',
               fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.2',
                        facecolor='#0D1117',
                        edgecolor='#F85149',
                        alpha=0.95,
                        linewidth=1.5 * layout.字型縮放),
               zorder=20)

    # ===== 總厚度標註 =====
    annotate_fs = layout.get_font_size('annotation')
    arrow_lw = 1.8 * layout.字型縮放

    # 檢查總厚度標註是否與右側標註重疊
    right_labels = [pos for pos in label_positions if pos[1] == 'right']
    if right_labels:
        # 如果有右側標註，將總厚度標註移到更右側
        thick_x_offset = 3.0 * layout.字型縮放
    else:
        thick_x_offset = 1.8 * layout.字型縮放

    ax.annotate('', xy=(layout.total_thick_x, -total_h/2 * 0.5),
                xytext=(layout.total_thick_x, total_h/2 * 0.5),
               arrowprops=dict(arrowstyle='<->', color='#F85149',
                             lw=arrow_lw))

    ax.text(layout.total_thick_x + thick_x_offset, layout.total_thick_y,
           f'Total\nt={layout.線厚度μ}um',
           ha='left', va='center',
           fontsize=annotate_fs + 1,
           color='#F85149',
           fontweight='bold')

    # ===== 總寬度標註 =====
    width_y = layout.total_width_y
    ax.annotate('', xy=(-total_w/2, width_y), xytext=(total_w/2, width_y),
               arrowprops=dict(arrowstyle='<->', color='#F85149',
                             lw=arrow_lw))

    ax.text(0, width_y - 0.025 * layout.字型縮放,
           f'W={total_w:.1f}mm ({n_ch}ch x {layout.訊號間距}mm)',
           ha='center', va='top',
           fontsize=annotate_fs + 1,
           color='#F85149',
           fontweight='bold')

    # ===== Signal Center =====
    ax.axhline(y=0, color='#FF6B6B', linewidth=1.2, linestyle='-.', alpha=0.5)
    ax.text(layout.signal_center_x, 0.008 * layout.字型縮放,
           'Signal Center (Y=0)',
           ha='left', va='bottom',
           fontsize=annotate_fs,
           color='#FF6B6B',
           style='italic')

    # ===== 軸設定 =====
    y_min = min(p['y_bot_mm'] for p in layer_positions) - 0.04
    y_max = max(p['y_top_mm'] for p in layer_positions) + 0.04

    # 如果有右側標註，增加右邊距
    right_margin_extra = 2.5 * layout.字型縮放 if any(s == 'right' for _, s in label_positions) else 0

    x_min = -total_w/2 - margins['left'] - 0.5
    x_max = total_w/2 + margins['right'] + 2.5 * layout.字型縮放 + right_margin_extra

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min - 0.05, y_max + 0.03)
    ax.set_aspect('auto')

    label_fs = layout.get_font_size('label')
    ax.set_xlabel('寬度(mm)', color='white', fontsize=label_fs)
    ax.set_ylabel('厚度(mm)', color='white', fontsize=label_fs)
    ax.tick_params(colors='white', labelsize=label_fs - 2)

    for spine in ax.spines.values():
        spine.set_color('#30363D')

    ax.set_title('GSG Stripline Cross-Section | Z0 = 50 Ohm | 7-Layer',
                fontsize=label_fs, color='#58A6FF', fontweight='bold', pad=8)

    # Y軸刻度
    y_ticks = [p['center_mm'] for p in layer_positions]
    y_labels = [f'{p["center_mm"]*1000:.0f}um' for p in layer_positions]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels, color='white', fontsize=label_fs - 2)

    return fig
# ============================================================
# 4. 側視圖
# ============================================================

def 繪製側視(layout: LayoutCalculator, conductor_color='#FFD700', dielectric_color='#C4956A'):
    """繪製側視圖 - 優化文字清晰度"""

    n_ch = layout.通道數
    total_w = layout.線總寬
    LENGTH = 400

    fig_width = max(14, 10 + layout.字型縮放 * 2)
    fig_height = max(7, 5 + layout.字型縮放 * 1.5)

    fig = figure(figsize=(fig_width, fig_height), facecolor='#0D1117')
    ax = fig.add_subplot(111)
    ax.set_facecolor('#0D1117')

    title_fs = layout.get_font_size('title')
    fig.suptitle(f'Cri/oFlex 3 CF3 Side View | {n_ch} Channels | Length {LENGTH} mm',
                fontsize=title_fs, fontweight='bold', color='white', y=0.96)

    t = linspace(0, LENGTH, 500)
    y_wave = 1.5 * sin(t / 60) * exp(-t / 400)
    half_t = layout.線厚度m / 2

    ax.fill_between(t, y_wave + half_t, y_wave - half_t,
                   color=dielectric_color, alpha=0.85, edgecolor='white', linewidth=1, zorder=2)
    ax.plot(t, y_wave + half_t - 0.015, 'w--', linewidth=0.6, alpha=0.5, zorder=3)
    ax.plot(t, y_wave - half_t + 0.015, 'w--', linewidth=0.6, alpha=0.5, zorder=3)
    ax.plot(t, y_wave, color=conductor_color, linewidth=1.2, alpha=0.9, zorder=4)

    conn_len, conn_dia = 12, 6
    ax.add_patch(Rectangle((-conn_len, -conn_dia/2), conn_len, conn_dia,
                          facecolor='#B87333', edgecolor='white', linewidth=1.5, zorder=5))
    for j in range(4):
        ax.plot([-conn_len + 2 + j*2.2, -conn_len + 2 + j*2.2],
               [-conn_dia/2, conn_dia/2], 'w-', linewidth=0.8, alpha=0.7, zorder=6)
    ax.add_patch(Rectangle((-conn_len - 3, -0.15), 3, 0.3,
                          facecolor='#C0C0C0', edgecolor='white', zorder=5))

    ax.add_patch(Rectangle((LENGTH, -conn_dia/2), conn_len, conn_dia,
                          facecolor='#B87333', edgecolor='white', linewidth=1.5, zorder=5))
    for j in range(4):
        ax.plot([LENGTH + j*2.2, LENGTH + j*2.2],
               [-conn_dia/2, conn_dia/2], 'w-', linewidth=0.8, alpha=0.7, zorder=6)
    ax.add_patch(Rectangle((LENGTH + conn_len, -0.15), 3, 0.3,
                          facecolor='#C0C0C0', edgecolor='white', zorder=5))

    max_curve_idx = argmax(abs(y_wave))
    mc_x, mc_y = t[max_curve_idx], y_wave[max_curve_idx]
    ax.add_patch(Circle((mc_x - 5, mc_y), 5, fill=False, edgecolor='#FF6B6B',
                       linewidth=1.5, linestyle='--', zorder=7))
    annotate_fs = layout.get_font_size('annotation')
    ax.annotate(f'R >= 5 mm', xy=(mc_x - 5, mc_y + 6),
               fontsize=annotate_fs, color='#FF6B6B', ha='center', fontweight='bold')

    label_fs = layout.get_font_size('label')
    arrow_lw = 1.8 * layout.字型縮放

    ax.annotate('', xy=(0, -conn_dia/2 - 4), xytext=(LENGTH, -conn_dia/2 - 4),
               arrowprops=dict(arrowstyle='<->', color='#F85149',
                             lw=arrow_lw))
    ax.text(LENGTH/2, -conn_dia/2 - 6, f'L = {LENGTH} mm',
           ha='center', va='top', fontsize=label_fs, color='#F85149', fontweight='bold')

    ax.annotate('', xy=(LENGTH + conn_len + 10, -half_t),
               xytext=(LENGTH + conn_len + 10, half_t),
               arrowprops=dict(arrowstyle='<->', color='#58A6FF',
                             lw=1.5 * layout.字型縮放))
    ax.text(LENGTH + conn_len + 14, 0,
           f't = {layout.線厚度μ:.0f}um',
           ha='left', va='center', fontsize=annotate_fs + 1,
           color='#58A6FF', fontweight='bold', rotation=90)

    pitch_fs = layout.get_font_size('pitch')
    ax.text(LENGTH/2, conn_dia/2 + 4,
           f'{n_ch} Channels | Pitch {layout.訊號間距} mm | Total Width {total_w} mm',
           ha='center', va='bottom', fontsize=pitch_fs,
           color='white', fontweight='bold',
           bbox=dict(boxstyle='round,pad=0.4', facecolor='#161B22',
                    edgecolor='#58A6FF', linewidth=1.5))

    ax.set_xlim(-20, LENGTH + conn_len + 30)
    ax.set_ylim(-conn_dia/2 - 12, conn_dia/2 + 12)
    ax.set_aspect('equal')
    ax.set_xlabel('Length (mm)', color='white', fontsize=label_fs)
    ax.set_ylabel('Height (mm)', color='white', fontsize=label_fs)
    ax.tick_params(colors='white', labelsize=label_fs - 2)

    for spine in ax.spines.values():
        spine.set_color('#30363D')

    ax.set_title('Flexible Stripline Profile | Bend Radius >= 5 mm | Connector: SMA/SMP',
                fontsize=label_fs, color='#58A6FF', fontweight='bold', pad=10)
    ax.legend(loc='upper right', facecolor='#161B22', edgecolor='#444466',
             labelcolor='white', fontsize=annotate_fs)

    return fig


# ============================================================
# 5. 上視圖
# ============================================================

def 繪製上視(layout: LayoutCalculator, conductor_color='#FFD700', dielectric_color='#C4956A'):
    """繪製上視圖 - 優化文字清晰度"""

    n_ch = layout.通道數
    total_w = layout.線總寬
    LENGTH = 400

    fig_width = max(14, 10 + layout.字型縮放 * 2)
    fig_height = max(8, 6 + layout.字型縮放 * 1.5)

    fig = figure(figsize=(fig_width, fig_height), facecolor='#0D1117')
    ax = fig.add_subplot(111)
    ax.set_facecolor('#0D1117')

    title_fs = layout.get_font_size('title')
    fig.suptitle(f'Cri/oFlex 3 CF3 Top View | {n_ch} Channels | Length {LENGTH} mm',
                fontsize=title_fs, fontweight='bold', color='white', y=0.96)

    conn_len, conn_dia = 12, 6
    label_fs = layout.get_font_size('label')
    annotate_fs = layout.get_font_size('annotation')
    pitch_fs = layout.get_font_size('pitch')

    ax.add_patch(Rectangle((conn_len, -total_w/2), LENGTH, total_w,
                          facecolor=dielectric_color, edgecolor='white',
                          linewidth=1.5, alpha=0.9, zorder=2))

    signal_w = min(layout.訊號寬度, layout.訊號間距 * 0.35)
    for i in range(n_ch):
        y = -total_w/2 + layout.訊號間距/2 + i * layout.訊號間距
        ax.add_patch(Rectangle((conn_len + 5, y - signal_w/2), LENGTH - 10, signal_w,
                              facecolor=conductor_color, edgecolor='#B8860B',
                              linewidth=0.5, alpha=0.85, zorder=3))
        ch_fs = max(8, annotate_fs)
        ax.text(conn_len + LENGTH/2, y, f'CH{i+1}',
               ha='center', va='center', fontsize=ch_fs,
               color='#333', fontweight='bold', zorder=4)

    for i in range(n_ch):
        y = -total_w/2 + layout.訊號間距/2 + i * layout.訊號間距

        ax.add_patch(Rectangle((0, y - conn_dia/2), conn_len, conn_dia,
                              facecolor='#B87333', edgecolor='white', linewidth=1, zorder=5))
        for j in range(3):
            ax.plot([conn_len - 4 + j*2, conn_len - 4 + j*2],
                   [y - conn_dia/2, y + conn_dia/2], 'w-', linewidth=0.5, zorder=6)
        ax.add_patch(Rectangle((-3, y - 0.15), 3, 0.3,
                              facecolor='#C0C0C0', edgecolor='white', zorder=5))

        ax.add_patch(Rectangle((conn_len + LENGTH, y - conn_dia/2), conn_len, conn_dia,
                              facecolor='#B87333', edgecolor='white', linewidth=1, zorder=5))
        for j in range(3):
            ax.plot([conn_len + LENGTH + j*2, conn_len + LENGTH + j*2],
                   [y - conn_dia/2, y + conn_dia/2], 'w-', linewidth=0.5, zorder=6)
        ax.add_patch(Rectangle((conn_len + LENGTH + conn_len, y - 0.15), 3, 0.3,
                              facecolor='#C0C0C0', edgecolor='white', zorder=5))

    ax.add_patch(Rectangle((conn_len + LENGTH*0.3, -total_w/2 - 1), LENGTH*0.15, total_w + 2,
                          facecolor='#4A90D9', edgecolor='cyan', linewidth=1.5,
                          linestyle='--', alpha=0.25, zorder=1))
    ax.text(conn_len + LENGTH*0.375, total_w/2 + 3,
           'Integrated Filters\n& Attenuators',
           ha='center', va='bottom', fontsize=annotate_fs,
           color='cyan', style='italic')

    arrow_lw = 1.8 * layout.字型縮放
    ax.annotate('', xy=(conn_len, total_w/2 + 8), xytext=(conn_len + LENGTH, total_w/2 + 8),
               arrowprops=dict(arrowstyle='<->', color='#F85149', lw=arrow_lw))
    ax.text(conn_len + LENGTH/2, total_w/2 + 10, f'L = {LENGTH} mm',
           ha='center', va='bottom', color='#F85149', fontsize=label_fs)

    ax.annotate('', xy=(conn_len + LENGTH + conn_len + 8, -total_w/2),
               xytext=(conn_len + LENGTH + conn_len + 8, total_w/2),
               arrowprops=dict(arrowstyle='<->', color='#F85149', lw=arrow_lw))
    ax.text(conn_len + LENGTH + conn_len + 12, 0,
           f'W = {total_w:.1f} mm\n({n_ch} ch x {layout.訊號間距} mm)',
           ha='left', va='center', color='#F85149',
           fontsize=annotate_fs + 1, rotation=90)

    if n_ch >= 2:
        y1 = -total_w/2 + layout.訊號間距/2
        y2 = -total_w/2 + layout.訊號間距/2 + layout.訊號間距
        ax.annotate('', xy=(conn_len + LENGTH/2, y1),
                   xytext=(conn_len + LENGTH/2, y2),
                   arrowprops=dict(arrowstyle='<->', color='#3FB950', lw=arrow_lw))
        ax.text(conn_len + LENGTH/2 + 3, (y1 + y2)/2,
               f'Pitch = {layout.訊號間距} mm',
               ha='left', va='center', color='#3FB950', fontsize=pitch_fs)

    margin_right = 35 + 5 * layout.字型縮放
    ax.set_xlim(-15, conn_len + LENGTH + conn_len + margin_right)
    ax.set_ylim(-total_w/2 - 15, total_w/2 + 18)
    ax.set_aspect('equal')
    ax.set_xlabel('Length (mm)', color='white', fontsize=label_fs)
    ax.set_ylabel('Width (mm)', color='white', fontsize=label_fs)
    ax.tick_params(colors='white', labelsize=label_fs - 2)

    for spine in ax.spines.values():
        spine.set_color('#30363D')

    ax.set_title('Plan View | Parallel Stripline | Integrated Filtering',
                fontsize=label_fs, color='#58A6FF', fontweight='bold', pad=10)

    legend_items = [('#C4956A', 'Polyimide Substrate'),
                   ('#FFD700', 'Signal Lines (Ag/NbTi)'),
                   ('#B87333', 'SMA/SMP Connector'),
                   ('#4A90D9', 'Filter/Attenuator Zone')]
    for i, (color, label) in enumerate(legend_items):
        x_pos = 0.02 + i * 0.22
        ax.add_patch(Rectangle((x_pos, 0.02), 0.03, 0.025,
                              facecolor=color, edgecolor='white',
                              linewidth=0.5, transform=ax.transAxes))
        ax.text(x_pos + 0.035, 0.032, label, transform=ax.transAxes,
               fontsize=annotate_fs, color='#AAAAAA', va='center')

    return fig
