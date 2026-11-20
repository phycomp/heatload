from typing import List, Tuple
from matplotlib.patches import Rectangle, Circle
from matplotlib.pyplot import subplots, tight_layout
from dataclasses import dataclass

@dataclass
class StriplineGeometry:
    w: float = 0.0
    t: float = 0.0
    h: float = 0.0
    s: float = 0.0
    L: float = 0.0
    n_channels: int = 8
# ============================================================
# 側視圖 - 智慧標註放置系統
# ============================================================

class LabelPlacementDetector:
    """標註位置偵測器 - 找出視圖中的空白區域"""
    
    def __init__(self, plot_width: float, plot_height: float, n_channels: int):
        self.plot_width = plot_width
        self.plot_height = plot_height
        self.n_channels = n_channels
        self.structure_regions = []  # 傳輸線結構佔用區域
        
    def add_structure_region(self, x: float, y: float, w: float, h: float):
        """記錄傳輸線結構佔用區域"""
        self.structure_regions.append((x, y, w, h))
    
    def find_empty_spaces(self, label_width: float, label_height: float) -> List[Tuple[float, float]]:
        """找出視圖中的空白區域"""
        empty_spaces = []
        margin = 0.3
        
        # 定義候選區域（避開傳輸線結構）
        candidates = [
            # 右側區域
            (self.plot_width + margin, self.plot_height * 0.5, 'right-center'),
            (self.plot_width + margin, self.plot_height * 0.25, 'right-top'),
            (self.plot_width + margin, self.plot_height * 0.75, 'right-bottom'),
            # 底部區域
            (self.plot_width * 0.5, -1.8, 'bottom-center'),
            (self.plot_width * 0.3, -1.8, 'bottom-left'),
            (self.plot_width * 0.7, -1.8, 'bottom-right'),
            # 左側區域
            (-margin - 0.5, self.plot_height * 0.5, 'left-center'),
            # 上方區域
            (self.plot_width * 0.5, self.plot_height + margin, 'top-center'),
        ]
        
        # 評估每個候選位置
        for x, y, position in candidates:
            if self._is_empty_space(x, y, label_width, label_height):
                empty_spaces.append((x, y, position))
        
        # 如果沒有找到合適位置，使用強制位置
        if not empty_spaces:
            empty_spaces.append((self.plot_width * 0.5, -2.2, 'forced'))
        
        return empty_spaces
    
    def _is_empty_space(self, x: float, y: float, w: float, h: float) -> bool:
        """檢查該區域是否為空白"""
        # 檢查邊界
        if x - w/2 < -1.0 or x + w/2 > self.plot_width + 4:
            return False
        if y - h/2 < -3.0 or y + h/2 > self.plot_height + 1.0:
            return False
        
        # 檢查是否與結構重疊
        for sx, sy, sw, sh in self.structure_regions:
            # 擴展檢查範圍（增加安全距離）
            padding = 0.2
            if (abs(x - (sx + sw/2)) < (w + sw)/2 + padding and
                abs(y - (sy + sh/2)) < (h + sh)/2 + padding):
                return False
        
        return True
    
    def find_best_label_position(self, label_width: float, label_height: float, 
                                 preferred: str = 'auto') -> Tuple[float, float]:
        """尋找最佳標註位置"""
        empty_spaces = self.find_empty_spaces(label_width, label_height)
        
        if not empty_spaces:
            # 強制位置
            return (self.plot_width * 0.5, -2.2)
        
        # 根據偏好排序
        if preferred == 'right':
            right_spaces = [s for s in empty_spaces if 'right' in s[2]]
            if right_spaces:
                return (right_spaces[0][0], right_spaces[0][1])
        elif preferred == 'bottom':
            bottom_spaces = [s for s in empty_spaces if 'bottom' in s[2]]
            if bottom_spaces:
                return (bottom_spaces[0][0], bottom_spaces[0][1])
        elif preferred == 'left':
            left_spaces = [s for s in empty_spaces if 'left' in s[2]]
            if left_spaces:
                return (left_spaces[0][0], left_spaces[0][1])
        
        # 返回第一個可用位置
        return (empty_spaces[0][0], empty_spaces[0][1])


def draw_smart_side_view(geo: StriplineGeometry, pitch: float, length: float,
                         via_enabled: bool, via_diameter: float, 
                         via_density: float, n_channels: int):
    """智慧型側視圖 - 主動偵測空白區域放置標註"""
    
    w, h, t, s, L = geo.w, geo.h, geo.t / 1000, pitch, length
    total_h = 2 * h + 3 * t
    L_show = min(L, 60)
    font_size = _get_font_size(n_channels)
    
    y0, y1, y2, y3, y4 = 0, t, t + h, t + h + t, t + h + t + h
    t_um = t * 1000
    h_um = h * 1000
    
    # 顏色定義
    c_gnd = '#D4A017'
    c_gnd_edge = '#8B6914'
    c_poly = '#F5E6C8'
    c_poly_edge = '#D4A574'
    c_signal = '#2ECC71'
    c_via = '#A0522D'
    c_text = '#2C3E50'
    
    # 1. 計算傳輸線結構佔用區域
    structure_regions = []
    
    # Bottom GND
    structure_regions.append((0, y0, L_show, t))
    # 下層介電
    structure_regions.append((0, y1, L_show, h))
    # Signal
    structure_regions.append((0, y2, L_show, t))
    # 上層介電
    structure_regions.append((0, y3, L_show, h))
    # Top GND
    structure_regions.append((0, y4, L_show, t))
    
    # 2. 創建標註位置偵測器
    detector = LabelPlacementDetector(L_show, total_h, n_channels)
    for region in structure_regions:
        detector.add_structure_region(*region)
    
    # 3. 尋找各個標註的最佳位置
    # Layer 標註 (較大)
    layer_pos = detector.find_best_label_position(2.8, 1.0, 
                                                  'right' if n_channels <= 4 else 'bottom')
    
    # 總厚度標註 (中等)
    thick_pos = detector.find_best_label_position(2.0, 0.4, 'bottom')
    # 確保不與 Layer 標註重疊
    if abs(thick_pos[0] - layer_pos[0]) < 1.5 and abs(thick_pos[1] - layer_pos[1]) < 0.8:
        thick_pos = (L_show * 0.3, -0.8)
    
    # 長度標註 (較小)
    len_pos = detector.find_best_label_position(1.5, 0.3, 'bottom')
    # 確保不與其他標註重疊
    if (abs(len_pos[0] - layer_pos[0]) < 1.5 and abs(len_pos[1] - layer_pos[1]) < 0.8) or \
       (abs(len_pos[0] - thick_pos[0]) < 1.0 and abs(len_pos[1] - thick_pos[1]) < 0.5):
        len_pos = (L_show * 0.7, -2.0)
    
    # 4. 創建圖形
    fig, ax = subplots(figsize=(10, 6))
    ax.set_title(
        f'側視圖 Side View (Y-Z)  L={L}mm  (顯示 {L_show}mm)',
        fontsize=11, fontweight='bold')
    ax.set_xlabel('Length (mm)', fontsize=9)
    ax.set_ylabel('Height (mm)', fontsize=9)
    ax.set_xlim(-0.5, L_show + 3.5)
    ax.set_ylim(-2.8, total_h + 0.2)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.08, linestyle='--')
    
    # 5. 繪製傳輸線結構
    # Bottom GND
    ax.add_patch(Rectangle((0, y0), L_show, t, facecolor=c_gnd, edgecolor=c_gnd_edge, lw=1.5))
    ax.text(L_show/2, y0 + t/2, 'Bottom GND', ha='center', va='center',
            fontsize=font_size, color='white', fontweight='bold')
    
    # 下層介電
    ax.add_patch(Rectangle((0, y1), L_show, h, facecolor=c_poly, edgecolor=c_poly_edge, lw=1.5, alpha=0.85))
    
    # Signal
    ax.add_patch(Rectangle((0, y2), L_show, t, facecolor=c_signal, edgecolor='#1A7A3A', lw=1.5))
    ax.text(L_show/2, y2 + t/2, 'Signal Layer', ha='center', va='center',
            fontsize=font_size, color='white', fontweight='bold')
    
    # 上層介電
    ax.add_patch(Rectangle((0, y3), L_show, h, facecolor=c_poly, edgecolor=c_poly_edge, lw=1.5, alpha=0.85))
    
    # Top GND
    ax.add_patch(Rectangle((0, y4), L_show, t, facecolor=c_gnd, edgecolor=c_gnd_edge, lw=1.5))
    ax.text(L_show/2, y4 + t/2, 'Top GND', ha='center', va='center',
            fontsize=font_size, color='white', fontweight='bold')
    
    # Via
    if via_enabled:
        step = max(1.0 / via_density, 1.5)
        vr = via_diameter / 2000
        for i in range(int(L_show / step) + 1):
            xv = i * step
            if xv > L_show:
                break
            ax.plot([xv, xv], [y0, y4 + t], color=c_via, lw=1.5, alpha=0.5)
            ax.add_patch(Circle((xv, y0), vr, facecolor=c_via, edgecolor='black', lw=0.8))
            ax.add_patch(Circle((xv, y4 + t), vr, facecolor=c_via, edgecolor='black', lw=0.8))
    
    # 6. Layer 標註 - 使用偵測到的位置
    label_x, label_y = layer_pos
    layer_txt = (
        f'Top GND  t={t_um:.0f}μm\n'
        f'Polyimide  h={h_um:.0f}μm\n'
        f'Signal Layer\n'
        f'Polyimide  h={h_um:.0f}μm\n'
        f'Bottom GND  t={t_um:.0f}μm'
    )
    
    # 計算標註框大小
    lines = layer_txt.split('\n')
    max_line_len = max(len(line) for line in lines)
    label_width = min(max_line_len * 0.12, 2.8)
    label_height = len(lines) * 0.035 + 0.05
    
    # 檢查標註是否與結構重疊（額外安全檢查）
    label_x, label_y = _ensure_no_overlap_with_structure(
        label_x, label_y, label_width, label_height, 
        structure_regions, L_show, total_h
    )
    
    ax.text(label_x, label_y, layer_txt, ha='center', va='center',
            fontsize=font_size, color='#8E44AD', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#F5EEF8',
                      edgecolor='#8E44AD', alpha=0.95, linewidth=1.5),
            linespacing=1.5)
    
    # 繪製引線（從標註到各層）
    layer_y_positions = [y4 + t/2, y3 + h/2, y2 + t/2, y1 + h/2, y0 + t/2]
    _draw_smart_leader_lines(ax, layer_y_positions, label_x, label_y, 
                            label_width, label_height, '#8E44AD')
    
    # 7. 總厚度標註 - 使用偵測到的位置
    thick_x, thick_y = thick_pos
    # 確保總厚度標註在合理位置
    if thick_y < -2.5 or thick_y > 0:
        thick_y = -1.0
    
    ax.annotate('', xy=(thick_x - 0.5, -0.3), xytext=(thick_x + 0.5, -0.3),
                arrowprops=dict(arrowstyle='<->', color='#E74C3C', lw=1.5))
    ax.text(thick_x, -0.5, f'總厚度 = {total_h*1000:.0f} μm',
            ha='center', va='top', fontsize=font_size, color='#E74C3C', fontweight='bold')
    
    # 8. 長度標註 - 使用偵測到的位置
    len_x, len_y = len_pos
    # 確保長度標註在合理位置
    if len_y < -2.8:
        len_y = -2.0
    
    ax.annotate('', xy=(0, len_y), xytext=(L_show, len_y),
                arrowprops=dict(arrowstyle='<->', color='#2980B9', lw=1.5))
    label = f'L = {L} mm' if L <= L_show else f'L = {L} mm (顯示 {L_show} mm)'
    ax.text(L_show/2, len_y - 0.15, label, ha='center', va='top',
            fontsize=font_size, color='#2980B9', fontweight='bold')
    
    # 9. 右側各層厚度標註（簡約）
    dx = L_show + 0.3
    thickness_labels = [
        (y0, t, f'{t_um:.0f}'),
        (y1, h, f'{h_um:.0f}'),
        (y3, h, f'{h_um:.0f}'),
        (y4, t, f'{t_um:.0f}')
    ]
    
    for yy, hh, lbl in thickness_labels:
        if yy < total_h - 0.1:
            ax.annotate('', xy=(dx, yy), xytext=(dx, yy + hh),
                        arrowprops=dict(arrowstyle='<->', color='#95A5A6', lw=1))
            ax.text(dx + 0.15, yy + hh/2, lbl + 'μm', ha='left', va='center',
                    fontsize=font_size-1, color='#7F8C8D')
    
    tight_layout()
    return fig


def _ensure_no_overlap_with_structure(x: float, y: float, w: float, h: float,
                                      structure_regions: List[Tuple], 
                                      plot_width: float, plot_height: float) -> Tuple[float, float]:
    """確保標註不與結構重疊"""
    
    # 檢查是否與結構重疊
    for sx, sy, sw, sh in structure_regions:
        if (abs(x - (sx + sw/2)) < (w + sw)/2 and
            abs(y - (sy + sh/2)) < (h + sh)/2):
            # 有重疊，調整位置
            # 嘗試右側
            new_x = sx + sw + 0.5
            if new_x + w/2 < plot_width + 3:
                return (new_x, y)
            # 嘗試左側
            new_x = sx - 0.5
            if new_x - w/2 > -1:
                return (new_x, y)
            # 嘗試底部
            new_y = -1.8
            if new_y - h/2 > -3:
                return (x, new_y)
            # 強制位置
            return (plot_width * 0.5, -2.2)
    
    return (x, y)


def _draw_smart_leader_lines(ax, layer_positions: List[float], label_x: float, 
                             label_y: float, label_width: float, label_height: float,
                             color: str):
    """繪製智慧引線"""
    
    # 決定引線方向
    if label_x > layer_positions[-1] + 0.5:  # 標註在右側
        connect_x = label_x - label_width/2
        n_layers = len(layer_positions)
        for i, yc in enumerate(layer_positions):
            if n_layers > 1:
                step = label_height / (n_layers + 1)
                ty = label_y - label_height/2 + step * (i + 1)
            else:
                ty = label_y
            
            alpha_val = 0.3 + 0.15 * (i / max(n_layers, 1))
            ax.plot([layer_positions[-1] + 0.1, connect_x], [yc, ty],
                    color=color, lw=0.7, linestyle='--', alpha=alpha_val)
    else:  # 標註在底部
        connect_x = layer_positions[-1] + 0.1
        gather_x = label_x
        
        # 水平線
        for i, yc in enumerate(layer_positions):
            ax.plot([connect_x, gather_x], [yc, yc],
                    color=color, lw=0.7, linestyle='--', alpha=0.3)
        
        # 垂直匯集線
        top = label_y + label_height/2
        ax.plot([gather_x, gather_x],
                [layer_positions[-1], top],
                color=color, lw=0.7, linestyle='--', alpha=0.3)


def _get_font_size(n_channels: int) -> float:
    """根據通道數獲取字體大小"""
    if n_channels <= 4:
        return 9
    elif n_channels <= 8:
        return 8
    else:
        return 7


# ============================================================
# 主程式 - 使用智慧型側視圖
# ============================================================

