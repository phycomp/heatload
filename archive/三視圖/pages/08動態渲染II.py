from streamlit import button, download_button, markdown, session_state, sidebar, spinner, subheader, success, slider, set_page_config, radio, pyplot, empty, columns, metric, caption, info, expander, checkbox
from matplotlib.patches import Rectangle, Circle
from matplotlib.gridspec import GridSpec
from numpy import abs, argmax, exp, linspace, sin
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.drawing.image import Image as XLImage

# ============================================================
# 1. 層結構定義 (厚度單位: um)
# ============================================================

LAYER_DEFS = [
    {'name': '保護層-底', 'thick_um': 15, 'material': 'Polyimide', 'color': '#E8D5C4', 'edge': '#A0522D', 'is_signal': False},
    {'name': '接地層-底', 'thick_um': 5, 'material': 'Ag/NbTi', 'color': '#8B9CAD', 'edge': '#4A5568', 'is_signal': False},
    {'name': '介電層-下', 'thick_um': 129, 'material': 'Polyimide', 'color': '#C4956A', 'edge': '#744210', 'is_signal': False},
    {'name': '訊號線', 'thick_um': 2, 'material': 'Ag/NbTi', 'color': '#FFD700', 'edge': '#B8860B', 'is_signal': True},
    {'name': '介電層-上', 'thick_um': 129, 'material': 'Polyimide', 'color': '#C4956A', 'edge': '#744210', 'is_signal': False},
    {'name': '接地層-上', 'thick_um': 5, 'material': 'Ag/NbTi', 'color': '#8B9CAD', 'edge': '#4A5568', 'is_signal': False},
    {'name': '保護層-上', 'thick_um': 15, 'material': 'Polyimide', 'color': '#E8D5C4', 'edge': '#A0522D', 'is_signal': False},
]

def calculate_layer_positions(layer_defs):
    """計算各層位置 (單位: mm)"""
    positions = []
    total_thick_um = sum(l['thick_um'] for l in layer_defs)
    
    # 找出Signal層索引
    signal_idx = next(i for i, l in enumerate(layer_defs) if l['is_signal'])
    signal_thick_um = layer_defs[signal_idx]['thick_um']
    
    # Signal層中心設為0
    center_from_bottom = sum(l['thick_um'] for l in layer_defs[:signal_idx]) + signal_thick_um/2
    
    cum_um = -center_from_bottom
    for layer in layer_defs:
        thick_um = layer['thick_um']
        y_bot_um = cum_um
        y_top_um = cum_um + thick_um
        positions.append({
            'y_bot_um': y_bot_um,
            'y_top_um': y_top_um,
            'y_bot_mm': y_bot_um / 1000,
            'y_top_mm': y_top_um / 1000,
            'center_mm': (y_bot_um + thick_um/2) / 1000,
            'thick_mm': thick_um / 1000,
            'thick_um': thick_um
        })
        cum_um += thick_um
    
    return positions, total_thick_um


# ============================================================
# 2. 佈局計算器 - 正確的比例計算
# ============================================================

class LayoutCalculator:
    """佈局計算器 - 正確的尺寸比例"""
    
    def __init__(self, n_channels: int, pitch_mm: float, signal_width_mm: float, 
                 font_scale: float = 1.0):
        self.n_channels = n_channels
        self.pitch_mm = pitch_mm
        self.signal_width_mm = signal_width_mm
        self.font_scale = font_scale
        
        # 計算層位置 (單位mm)
        self.layer_positions, self.total_thick_um = calculate_layer_positions(LAYER_DEFS)
        self.total_height_mm = self.total_thick_um / 1000  # 轉換為mm
        
        # 計算總寬度
        self.total_width_mm = n_channels * pitch_mm
        
        # 計算字型大小
        self._calculate_font_sizes()
        
        # 計算佈局邊距
        self._calculate_margins()
        
        # 計算圖形尺寸
        self._calculate_figure_size()
        
        # 計算標註位置
        self._calculate_label_positions()
    
    def _calculate_font_sizes(self):
        """計算字型大小"""
        # 基礎字型 (根據通道數)
        if self.n_channels <= 4:
            base = 12
        elif self.n_channels <= 8:
            base = 11
        elif self.n_channels <= 12:
            base = 10
        else:
            base = 9
        
        self.base_font_size = base * self.font_scale
        
        # 各層字型 (根據層間距)
        centers = [p['center_mm'] for p in self.layer_positions]
        self.layer_font_sizes = []
        
        for i in range(len(centers)):
            # 計算與相鄰層的最小間距 (mm)
            if i == 0:
                spacing = centers[i+1] - centers[i]
            elif i == len(centers) - 1:
                spacing = centers[i] - centers[i-1]
            else:
                spacing = min(centers[i] - centers[i-1], centers[i+1] - centers[i])
            
            # 根據間距調整 (間距單位mm)
            if spacing < 0.03:      # < 30um
                ratio = 0.50
            elif spacing < 0.05:    # < 50um
                ratio = 0.60
            elif spacing < 0.07:    # < 70um
                ratio = 0.70
            elif spacing < 0.10:    # < 100um
                ratio = 0.80
            elif spacing < 0.13:    # < 130um
                ratio = 0.90
            else:
                ratio = 1.0
            
            fs = self.base_font_size * ratio
            
            # 邊緣層稍大
            if i == 0 or i == len(centers) - 1:
                fs = min(self.base_font_size, fs * 1.1)
            
            # 限制範圍
            fs = max(6 * self.font_scale, min(14 * self.font_scale, fs))
            self.layer_font_sizes.append(fs)
    
    def _calculate_margins(self):
        """計算邊距 - 基於字型大小"""
        fs = self.font_scale
        self.margins = {
            'left': max(1.5, 0.8 * fs),
            'right': max(3.0, 1.5 * fs),
            'top': max(0.3, 0.2 * fs),
            'bottom': max(1.2, 0.8 * fs),
        }
    
    def _calculate_figure_size(self):
        """計算圖形尺寸"""
        total_w = self.total_width_mm
        total_h = self.total_height_mm
        margins = self.margins
        
        # 寬度: 總寬度 + 左右邊距 + 標註空間
        fig_width = total_w + margins['left'] + margins['right'] + 4 * self.font_scale
        
        # 高度: 總高度 + 上下邊距 + Pitch標註空間
        fig_height = total_h + margins['top'] + margins['bottom'] + 1.5 * self.font_scale
        
        # 確保最小尺寸
        fig_width = max(10, fig_width)
        fig_height = max(5, fig_height)
        
        self.figure_size = (fig_width, fig_height)
    
    def _calculate_label_positions(self):
        """計算標註位置 - 避免重疊"""
        total_w = self.total_width_mm
        total_h = self.total_height_mm
        fs = self.font_scale
        
        # 計算各標註的尺寸
        label_w = 2.5 * fs
        label_h = 0.8 * fs
        
        # 1. 層標註位置 (左側)
        self.layer_label_x = -total_w/2 - self.margins['left'] + 0.5
        
        # 2. 厚度標註位置 (右側)
        self.thick_label_x = total_w/2 + 2 * fs
        
        # 3. Pitch標註位置 (底部)
        self.pitch_y = -0.05 * fs
        
        # 4. 總厚度標註位置 (右側偏上)
        self.total_thick_x = total_w/2 + 3.5 * fs
        self.total_thick_y = 0
        
        # 5. 總寬度標註位置 (底部)
        self.total_width_y = -0.15 * fs
        
        # 6. Signal Center標註
        self.signal_center_x = total_w/2 + 0.3
    
    def get_font_size(self, category: str):
        """獲取各類別字型大小"""
        sizes = {
            'title': self.base_font_size * 1.2,
            'label': self.base_font_size,
            'annotation': self.base_font_size * 0.8,
            'pitch': self.base_font_size * 0.9,
        }
        return sizes.get(category, self.base_font_size)


# ============================================================
# 3. 前視圖繪製 - 正確的比例
# ============================================================

def draw_front_view(layout: LayoutCalculator):
    """繪製前視圖 - 正確的尺寸比例"""
    
    n_ch = layout.n_channels
    total_w = layout.total_width_mm
    total_h = layout.total_height_mm
    layer_positions = layout.layer_positions
    font_sizes = layout.layer_font_sizes
    margins = layout.margins
    fig_size = layout.figure_size
    
    # 創建圖形
    fig, ax = subplots(figsize=fig_size, facecolor='#0D1117')
    ax.set_facecolor('#0D1117')
    
    # 標題
    title_fs = layout.get_font_size('title')
    fig.suptitle(f'Cri/oFlex3 CF3 前視 | {n_ch} 通道數 | GSG 7-Layer',
                fontsize=title_fs, fontweight='bold', color='white', y=0.96)
    
    display_names = ['保護層-底', '接地層-底', '介電層-下', f'訊號線(x{n_ch})',
                    '介電層-上', '接地層-上', '保護層-上']
    
    # 繪製各層
    for i, (layer_def, pos, fs) in enumerate(zip(LAYER_DEFS, layer_positions, font_sizes)):
        y_bot = pos['y_bot_mm']
        y_top = pos['y_top_mm']
        thick_mm = pos['thick_mm']
        color = layer_def['color']
        edge = layer_def['edge']
        is_signal = layer_def['is_signal']
        
        if is_signal:
            # 信號線
            signal_w = min(layout.signal_width_mm, layout.pitch_mm * 0.35)
            for ch in range(n_ch):
                x_c = -total_w/2 + layout.pitch_mm/2 + ch * layout.pitch_mm
                ax.add_patch(Rectangle((x_c - signal_w/2, y_bot), signal_w, thick_mm,
                                      facecolor=color, edgecolor=edge, linewidth=1.5, zorder=5))
                if n_ch <= 12:
                    ch_fs = max(5, fs * 0.7)
                    ax.text(x_c, y_bot + thick_mm/2, str(ch+1), ha='center', va='center',
                           fontsize=ch_fs, color='#333', fontweight='bold', zorder=6)
            
            # 信號層背景
            ax.add_patch(Rectangle((-total_w/2 - 1, y_bot), total_w + 2, thick_mm,
                                  facecolor='#D4A574', edgecolor='none', alpha=0.2, zorder=1))
        else:
            # 其他層
            ax.add_patch(Rectangle((-total_w/2 - 2, y_bot), total_w + 4, thick_mm,
                                  facecolor=color, edgecolor=edge, linewidth=1.2, alpha=0.95, zorder=3))
            
            # 接地層紋理
            if '接地' in layer_def['name']:
                for j in range(int((total_w + 4) / 0.3)):
                    x0 = -total_w/2 - 2 + j * 0.3
                    ax.plot([x0, x0 + thick_mm*3], [y_bot, y_top],
                           color='#5A6B7D', linewidth=0.25, alpha=0.35, zorder=4)
            
            # 保護層紋理
            if '保護' in layer_def['name']:
                for dx in linspace(-total_w/2 - 1.5, total_w/2 + 1.5, int((total_w+3)/0.8)):
                    for dy in linspace(y_bot + thick_mm*0.2, y_top - thick_mm*0.2, max(1, int(thick_mm/0.05))):
                        ax.plot(dx, dy, '.', color='#A0522D', markersize=1.2, alpha=0.25, zorder=4)
        
        # 層標註 (左側)
        label_y = (y_bot + y_top) / 2
        
        # 根據字型大小調整名稱
        display_name = display_names[i]
        if fs <= 8 * layout.font_scale:
            if '保護' in display_name:
                display_name = '保護' if '底' in display_name else '保護-上'
            elif '接地' in display_name:
                display_name = 'GND' if '底' in display_name else 'GND-上'
            elif '介電' in display_name:
                display_name = '介電' if '下' in display_name else '介電-上'
            elif '訊號' in display_name:
                display_name = f'Signal x{n_ch}'
        
        # 調整padding
        padding = 0.3 if fs >= 10 * layout.font_scale else 0.2
        if fs <= 8 * layout.font_scale:
            padding = 0.15
        
        # 繪製標註
        ax.text(layout.layer_label_x, label_y, display_name,
               ha='right', va='center',
               fontsize=fs,
               color='white',
               fontweight='bold',
               zorder=10,
               bbox=dict(boxstyle='round,pad=' + str(padding),
                        facecolor='#0D1117',
                        edgecolor=color,
                        linewidth=1.5,
                        alpha=0.95))
        
        # 厚度標註 (右側)
        ax.annotate('', xy=(layout.thick_label_x, y_bot), xytext=(layout.thick_label_x, y_top),
                   arrowprops=dict(arrowstyle='<->', color='#58A6FF',
                                 lw=1.0 * layout.font_scale), zorder=10)
        
        thick_fs = max(5, fs - 2)
        ax.text(layout.thick_label_x + 0.8, label_y, f'{pos["thick_um"]}um',
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
        x1 = -total_w/2 + layout.pitch_mm/2
        x2 = -total_w/2 + layout.pitch_mm/2 + layout.pitch_mm
        
        # 箭頭
        ax.annotate('', xy=(x1, layout.pitch_y), xytext=(x2, layout.pitch_y),
                   arrowprops=dict(arrowstyle='<->', color='#F85149',
                                 lw=2.0 * layout.font_scale,
                                 shrinkA=0, shrinkB=0,
                                 connectionstyle="arc3,rad=0.0"), zorder=20)
        
        # 端點
        marker_size = 4 * layout.font_scale
        ax.plot(x1, layout.pitch_y, 'o', color='#F85149', markersize=marker_size, zorder=20)
        ax.plot(x2, layout.pitch_y, 'o', color='#F85149', markersize=marker_size, zorder=20)
        
        # 輔助線
        ax.plot([x1, x1], [0.002, layout.pitch_y + 0.005],
               color='#F85149', linestyle=':', linewidth=0.8 * layout.font_scale,
               alpha=0.4, zorder=15)
        ax.plot([x2, x2], [0.002, layout.pitch_y + 0.005],
               color='#F85149', linestyle=':', linewidth=0.8 * layout.font_scale,
               alpha=0.4, zorder=15)
        
        # Pitch文字
        pitch_fs = layout.get_font_size('pitch')
        ax.text((x1 + x2) / 2, layout.pitch_y + 0.015 * layout.font_scale,
               f'Pitch = {layout.pitch_mm} mm',
               ha='center', va='bottom',
               fontsize=pitch_fs,
               color='#F85149',
               fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.15',
                        facecolor='#0D1117',
                        edgecolor='#F85149',
                        alpha=0.95,
                        linewidth=1.2 * layout.font_scale),
               zorder=20)
    
    # ===== 總厚度標註 =====
    annotate_fs = layout.get_font_size('annotation')
    ax.annotate('', xy=(layout.total_thick_x, -total_h/2 * 0.5), 
                xytext=(layout.total_thick_x, total_h/2 * 0.5),
               arrowprops=dict(arrowstyle='<->', color='#F85149',
                             lw=1.5 * layout.font_scale))
    ax.text(layout.total_thick_x + 1.5 * layout.font_scale, layout.total_thick_y,
           f'Total\nt={layout.total_thick_um}um',
           ha='left', va='center',
           fontsize=annotate_fs,
           color='#F85149',
           fontweight='bold')
    
    # ===== 總寬度標註 =====
    width_y = layout.total_width_y
    ax.annotate('', xy=(-total_w/2, width_y), xytext=(total_w/2, width_y),
               arrowprops=dict(arrowstyle='<->', color='#F85149',
                             lw=1.5 * layout.font_scale))
    ax.text(0, width_y - 0.02 * layout.font_scale,
           f'W={total_w:.1f}mm ({n_ch}ch x {layout.pitch_mm}mm)',
           ha='center', va='top',
           fontsize=annotate_fs,
           color='#F85149',
           fontweight='bold')
    
    # ===== Signal Center =====
    ax.axhline(y=0, color='#FF6B6B', linewidth=1.0, linestyle='-.', alpha=0.5)
    ax.text(layout.signal_center_x, 0.006 * layout.font_scale,
           'Signal Center (Y=0)',
           ha='left', va='bottom',
           fontsize=annotate_fs - 1,
           color='#FF6B6B',
           style='italic')
    
    # ===== 軸設定 - 正確的比例 =====
    # 計算Y軸範圍 (保留一些邊距)
    y_min = min(p['y_bot_mm'] for p in layer_positions) - 0.03
    y_max = max(p['y_top_mm'] for p in layer_positions) + 0.03
    
    # 計算X軸範圍
    x_min = -total_w/2 - margins['left'] - 0.5
    x_max = total_w/2 + margins['right'] + 2 * layout.font_scale
    
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min - 0.05, y_max + 0.02)
    
    # 確保Y軸比例正確 (保持縱橫比)
    ax.set_aspect('auto')
    
    label_fs = layout.get_font_size('label')
    ax.set_xlabel('寬度(mm)', color='white', fontsize=label_fs)
    ax.set_ylabel('厚度(mm)', color='white', fontsize=label_fs)
    ax.tick_params(colors='white', labelsize=label_fs - 3)
    
    for spine in ax.spines.values():
        spine.set_color('#30363D')
    
    ax.set_title('GSG Stripline Cross-Section | Z0 = 50 Ohm | 7-Layer',
                fontsize=label_fs, color='#58A6FF', fontweight='bold', pad=8)
    
    # 顯示正確的Y軸刻度
    y_ticks = [p['center_mm'] for p in layer_positions]
    y_labels = [f'{p["center_mm"]*1000:.0f}um' for p in layer_positions]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels, color='white', fontsize=label_fs - 4)
    
    return fig


# ============================================================
# 4. 側視圖
# ============================================================

def draw_side_view(layout: LayoutCalculator):
    """繪製側視圖"""
    
    n_ch = layout.n_channels
    total_w = layout.total_width_mm
    LENGTH = 400
    
    fig_width = max(14, 10 + layout.font_scale * 2)
    fig_height = max(7, 5 + layout.font_scale * 1.5)
    
    fig = figure(figsize=(fig_width, fig_height), facecolor='#0D1117')
    ax = fig.add_subplot(111)
    ax.set_facecolor('#0D1117')
    
    title_fs = layout.get_font_size('title')
    fig.suptitle(f'Cri/oFlex 3 CF3 Side View | {n_ch} Channels | Length {LENGTH} mm',
                fontsize=title_fs, fontweight='bold', color='white', y=0.96)
    
    t = linspace(0, LENGTH, 500)
    y_wave = 1.5 * sin(t / 60) * exp(-t / 400)
    half_t = layout.total_height_mm / 2
    
    ax.fill_between(t, y_wave + half_t, y_wave - half_t,
                   color='#C4956A', alpha=0.85, edgecolor='white', linewidth=1, zorder=2)
    ax.plot(t, y_wave + half_t - 0.015, 'w--', linewidth=0.6, alpha=0.5, zorder=3)
    ax.plot(t, y_wave - half_t + 0.015, 'w--', linewidth=0.6, alpha=0.5, zorder=3)
    ax.plot(t, y_wave, color='#FFD700', linewidth=1.2, alpha=0.9, zorder=4)
    
    # 連接器
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
    
    # 彎曲半徑
    max_curve_idx = argmax(abs(y_wave))
    mc_x, mc_y = t[max_curve_idx], y_wave[max_curve_idx]
    ax.add_patch(Circle((mc_x - 5, mc_y), 5, fill=False, edgecolor='#FF6B6B',
                       linewidth=1.5, linestyle='--', zorder=7))
    annotate_fs = layout.get_font_size('annotation')
    ax.annotate(f'R >= 5 mm', xy=(mc_x - 5, mc_y + 6),
               fontsize=annotate_fs, color='#FF6B6B', ha='center', fontweight='bold')
    
    # 標註
    label_fs = layout.get_font_size('label')
    ax.annotate('', xy=(0, -conn_dia/2 - 4), xytext=(LENGTH, -conn_dia/2 - 4),
               arrowprops=dict(arrowstyle='<->', color='#F85149',
                             lw=1.5 * layout.font_scale))
    ax.text(LENGTH/2, -conn_dia/2 - 6, f'L = {LENGTH} mm',
           ha='center', va='top', fontsize=label_fs, color='#F85149', fontweight='bold')
    
    ax.annotate('', xy=(LENGTH + conn_len + 10, -half_t),
               xytext=(LENGTH + conn_len + 10, half_t),
               arrowprops=dict(arrowstyle='<->', color='#58A6FF',
                             lw=1.2 * layout.font_scale))
    ax.text(LENGTH + conn_len + 14, 0,
           f't = {layout.total_thick_um:.0f}um',
           ha='left', va='center', fontsize=annotate_fs,
           color='#58A6FF', fontweight='bold', rotation=90)
    
    pitch_fs = layout.get_font_size('pitch')
    ax.text(LENGTH/2, conn_dia/2 + 4,
           f'{n_ch} Channels | Pitch {layout.pitch_mm} mm | Total Width {total_w} mm',
           ha='center', va='bottom', fontsize=pitch_fs,
           color='white', fontweight='bold',
           bbox=dict(boxstyle='round,pad=0.4', facecolor='#161B22',
                    edgecolor='#58A6FF', linewidth=1.5))
    
    ax.set_xlim(-20, LENGTH + conn_len + 30)
    ax.set_ylim(-conn_dia/2 - 12, conn_dia/2 + 12)
    ax.set_aspect('equal')
    ax.set_xlabel('Length (mm)', color='white', fontsize=label_fs)
    ax.set_ylabel('Height (mm)', color='white', fontsize=label_fs)
    ax.tick_params(colors='white', labelsize=label_fs - 3)
    
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

def draw_top_view(layout: LayoutCalculator):
    """繪製上視圖"""
    
    n_ch = layout.n_channels
    total_w = layout.total_width_mm
    LENGTH = 400
    
    fig_width = max(14, 10 + layout.font_scale * 2)
    fig_height = max(8, 6 + layout.font_scale * 1.5)
    
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
    
    # 主體
    ax.add_patch(Rectangle((conn_len, -total_w/2), LENGTH, total_w,
                          facecolor='#C4956A', edgecolor='white',
                          linewidth=1.5, alpha=0.9, zorder=2))
    
    # 信號線
    signal_w = min(layout.signal_width_mm, layout.pitch_mm * 0.35)
    for i in range(n_ch):
        y = -total_w/2 + layout.pitch_mm/2 + i * layout.pitch_mm
        ax.add_patch(Rectangle((conn_len + 5, y - signal_w/2), LENGTH - 10, signal_w,
                              facecolor='#FFD700', edgecolor='#B8860B',
                              linewidth=0.5, alpha=0.85, zorder=3))
        ch_fs = max(6, annotate_fs - 1)
        ax.text(conn_len + LENGTH/2, y, f'CH{i+1}',
               ha='center', va='center', fontsize=ch_fs,
               color='#333', fontweight='bold', zorder=4)
    
    # 連接器
    for i in range(n_ch):
        y = -total_w/2 + layout.pitch_mm/2 + i * layout.pitch_mm
        
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
    
    # 濾波器區域
    ax.add_patch(Rectangle((conn_len + LENGTH*0.3, -total_w/2 - 1), LENGTH*0.15, total_w + 2,
                          facecolor='#4A90D9', edgecolor='cyan', linewidth=1.5,
                          linestyle='--', alpha=0.25, zorder=1))
    ax.text(conn_len + LENGTH*0.375, total_w/2 + 3,
           'Integrated Filters\n& Attenuators',
           ha='center', va='bottom', fontsize=annotate_fs,
           color='cyan', style='italic')
    
    # 尺寸標註
    arrow_lw = 1.5 * layout.font_scale
    ax.annotate('', xy=(conn_len, total_w/2 + 8), xytext=(conn_len + LENGTH, total_w/2 + 8),
               arrowprops=dict(arrowstyle='<->', color='#F85149', lw=arrow_lw))
    ax.text(conn_len + LENGTH/2, total_w/2 + 10, f'L = {LENGTH} mm',
           ha='center', va='bottom', color='#F85149', fontsize=label_fs)
    
    ax.annotate('', xy=(conn_len + LENGTH + conn_len + 8, -total_w/2),
               xytext=(conn_len + LENGTH + conn_len + 8, total_w/2),
               arrowprops=dict(arrowstyle='<->', color='#F85149', lw=arrow_lw))
    ax.text(conn_len + LENGTH + conn_len + 12, 0,
           f'W = {total_w:.1f} mm\n({n_ch} ch x {layout.pitch_mm} mm)',
           ha='left', va='center', color='#F85149',
           fontsize=annotate_fs, rotation=90)
    
    # Pitch標註
    if n_ch >= 2:
        y1 = -total_w/2 + layout.pitch_mm/2
        y2 = -total_w/2 + layout.pitch_mm/2 + layout.pitch_mm
        ax.annotate('', xy=(conn_len + LENGTH/2, y1),
                   xytext=(conn_len + LENGTH/2, y2),
                   arrowprops=dict(arrowstyle='<->', color='#3FB950', lw=arrow_lw))
        ax.text(conn_len + LENGTH/2 + 3, (y1 + y2)/2,
               f'Pitch = {layout.pitch_mm} mm',
               ha='left', va='center', color='#3FB950', fontsize=pitch_fs)
    
    # 軸設定
    margin_right = 35 + 5 * layout.font_scale
    ax.set_xlim(-15, conn_len + LENGTH + conn_len + margin_right)
    ax.set_ylim(-total_w/2 - 15, total_w/2 + 18)
    ax.set_aspect('equal')
    ax.set_xlabel('Length (mm)', color='white', fontsize=label_fs)
    ax.set_ylabel('Width (mm)', color='white', fontsize=label_fs)
    ax.tick_params(colors='white', labelsize=label_fs - 3)
    
    for spine in ax.spines.values():
        spine.set_color('#30363D')
    
    ax.set_title('Plan View | Parallel Stripline | Integrated Filtering',
                fontsize=label_fs, color='#58A6FF', fontweight='bold', pad=10)
    
    # 圖例
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
               fontsize=annotate_fs - 1, color='#AAAAAA', va='center')
    
    return fig


# ============================================================
# 6. Streamlit UI
# ============================================================

def main():
    set_page_config(page_title="智慧三視圖 - 正確比例", page_icon="📐",
                   layout="wide", initial_sidebar_state="expanded")
    
    subheader("📐 智慧三視圖系統 - 正確尺寸比例")
    markdown("*從字型和通道數開始計算 · 自動防重疊*")
    # markdown("---")
    
    with sidebar:
        subheader("⚙️ 參數設定")
        
        n_channels = slider("通道數", 2, 16, 8, 2)
        pitch_mm = slider("Pitch (mm)", 0.5, 5.0, 2.0, 0.1)
        signal_width = slider("信號線寬度 (mm)", 0.1, 1.0, 0.4, 0.05)
        
        markdown("---")
        subheader("🔤 字型控制")
        font_scale = slider("字型縮放比例", 0.5, 2.0, 1.0, 0.1)
        
        markdown("---")
        total_w = n_channels * pitch_mm
        info(f"""
        **尺寸資訊**
        - 總寬度: {total_w:.2f} mm
        - 總厚度: 300 um (0.3 mm)
        - 通道數: {n_channels} ch
        - Pitch: {pitch_mm:.1f} mm
        """)
    
    # 創建佈局計算器
    layout = LayoutCalculator(n_channels, pitch_mm, signal_width, font_scale)
    
    # 菜單
    MENU = ['📐 前視圖', '📐 側視圖', '📐 上視圖']
    menu = radio('選擇視圖', MENU, horizontal=True, index=0)
    
    # 繪製
    if menu == MENU[0]:
        subheader("🔲 前視圖 Front View")
        caption(f"總寬度: {layout.total_width_mm:.2f}mm | 總厚度: {layout.total_thick_um}um | 字型縮放: {font_scale:.1f}x")
        fig = draw_front_view(layout)
    elif menu == MENU[1]:
        subheader("🔲 側視圖 Side View")
        fig = draw_side_view(layout)
    else:
        subheader("🔲 上視圖 Top View")
        fig = draw_top_view(layout)
    
    pyplot(fig)
    
    # markdown("---")
    cols = columns(4)
    with cols[0]:
        caption(f"📐 通道數: {n_channels}")
    with cols[1]:
        caption(f"📏 Pitch: {pitch_mm:.1f}mm")
    with cols[2]:
        caption(f"📐 總寬度: {total_w:.2f}mm")
    with cols[3]:
        caption(f"📏 總厚度: 300um")


if __name__ == "__main__":
    main()
