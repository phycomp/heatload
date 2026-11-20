import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch
from matplotlib.pyplot import subplots, tight_layout
from dataclasses import dataclass
from io import BytesIO
from typing import List, Dict, Tuple, Optional
import numpy as np

# ============================================================
# 資料結構定義
# ============================================================

@dataclass
class StriplineGeometry:
    """Stripline 幾何參數"""
    w: float        # 信號線寬度 (mm)
    t: float        # 信號線厚度 (μm)
    h: float        # 介電層厚度 (mm) 上下各一層
    s: float        # 通道間距 pitch (mm)
    L: float        # 傳輸線長度 (mm)
    n_channels: int # 通道數


# ============================================================
# 動態佈局管理器
# ============================================================

class DynamicLayoutManager:
    """動態佈局管理器 - 自動偵測並避免重疊"""
    
    def __init__(self, total_width: float, total_height: float, n_channels: int, 
                 margin: float = 0.3):
        self.total_width = total_width
        self.total_height = total_height
        self.n_channels = n_channels
        self.margin = margin
        self.occupied_regions = []  # 已佔用區域列表 [(x, y, width, height)]
        
    def find_safe_position(self, element_width: float, element_height: float, 
                          preferred: str = 'auto', padding: float = 0.2) -> Tuple[float, float]:
        """尋找安全的標註位置"""
        
        # 1. 生成候選位置
        candidates = self._generate_candidates(preferred)
        
        # 2. 評估每個位置
        for x, y in candidates:
            if not self._is_overlapping(x, y, element_width, element_height, padding):
                # 記錄已佔用區域
                self.occupied_regions.append((x - element_width/2, y - element_height/2, 
                                             element_width + padding*2, element_height + padding*2))
                return x, y
        
        # 3. 如果所有位置都被佔用，強制調整
        return self._force_adjust(element_width, element_height)
    
    def _generate_candidates(self, preferred: str) -> List[Tuple[float, float]]:
        """生成候選位置"""
        candidates = []
        
        # 右側候選位置
        right_x = self.total_width + self.margin * 0.8
        candidates.extend([
            (right_x, self.total_height * 0.5),   # 右側中央
            (right_x, self.total_height * 0.3),   # 右側上方
            (right_x, self.total_height * 0.7),   # 右側下方
            (right_x + 0.5, self.total_height * 0.5),  # 更右側
        ])
        
        # 底部候選位置
        bottom_y = -1.8
        candidates.extend([
            (self.total_width * 0.5, bottom_y),   # 底部中央
            (self.total_width * 0.25, bottom_y),  # 底部左側
            (self.total_width * 0.75, bottom_y),  # 底部右側
        ])
        
        # 左上候選位置
        candidates.extend([
            (self.margin * 0.5, self.total_height * 0.8),
            (self.margin * 0.5, self.total_height * 0.2),
        ])
        
        # 根據偏好調整順序
        if preferred == 'right':
            # 將右側候選移到前面
            right_candidates = [c for c in candidates if c[0] > self.total_width]
            other_candidates = [c for c in candidates if c[0] <= self.total_width]
            candidates = right_candidates + other_candidates
        elif preferred == 'bottom':
            bottom_candidates = [c for c in candidates if c[1] < 0]
            other_candidates = [c for c in candidates if c[1] >= 0]
            candidates = bottom_candidates + other_candidates
        
        return candidates
    
    def _is_overlapping(self, x: float, y: float, width: float, height: float, 
                       padding: float) -> bool:
        """檢查是否與現有區域重疊"""
        # 檢查邊界
        if x - width/2 < -self.margin or x + width/2 > self.total_width + self.margin * 3:
            return True
        if y - height/2 < -3.0 or y + height/2 > self.total_height + 0.5:
            return True
            
        # 檢查與所有已佔用區域的重疊
        for ox, oy, ow, oh in self.occupied_regions:
            # 擴展檢查範圍（包含padding）
            if (abs(x - (ox + ow/2)) < (width + ow)/2 + padding and 
                abs(y - (oy + oh/2)) < (height + oh)/2 + padding):
                return True
        return False
    
    def _force_adjust(self, width: float, height: float) -> Tuple[float, float]:
        """強制調整位置"""
        # 嘗試放在最空曠的區域
        positions = [
            (self.total_width * 0.5, -2.5),
            (self.total_width * 0.5, self.total_height + 0.5),
            (-1.0, self.total_height * 0.5),
            (self.total_width + 2.0, self.total_height * 0.5),
        ]
        
        for x, y in positions:
            if not self._is_overlapping(x, y, width * 0.8, height * 0.8, 0.1):
                self.occupied_regions.append((x - width/2, y - height/2, width, height))
                return x, y
        
        # 最後手段：放在角落
        self.occupied_regions.append((-self.margin, -2.5, width, height))
        return -self.margin, -2.5


# ============================================================
# 通用輔助函數
# ============================================================

def _view_to_buffer(fig) -> BytesIO:
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)
    return buf

def _get_adaptive_font_size(total_width: float, n_channels: int) -> float:
    """根據結構密度調整字體大小"""
    base_size = 8
    if total_width > 10:
        return max(5.5, base_size - 2.5)
    elif n_channels > 10:
        return max(5.5, base_size - 2)
    elif n_channels > 6:
        return max(6, base_size - 1.5)
    elif n_channels > 4:
        return max(6.5, base_size - 1)
    return base_size

def _get_adaptive_margin(pitch: float, n_channels: int) -> float:
    """根據通道數動態調整邊距"""
    base_margin = pitch * 0.35
    if n_channels > 10:
        return max(base_margin, 0.6)
    elif n_channels > 6:
        return max(base_margin, 0.45)
    return max(base_margin, 0.3)

def _create_layer_text(t_um: float, h_um: float) -> str:
    """產生標準化的 Layer 標註文字"""
    return (
        f'L5  Top GND      t={t_um:.0f}μm\n'
        f'L4  Polyimide     h={h_um:.0f}μm  εr=3.4\n'
        f'L3  Signal        G-S-G\n'
        f'L2  Polyimide     h={h_um:.0f}μm  εr=3.4\n'
        f'L1  Bottom GND    t={t_um:.0f}μm'
    )

def _draw_smart_leader_lines(ax, layer_positions: List[float], label_x: float, 
                             label_y: float, label_width: float, label_height: float,
                             color: str, line_count: int):
    """繪製智慧引線，避免交叉和重疊"""
    
    # 計算標註框邊界
    left = label_x - label_width/2
    right = label_x + label_width/2
    top = label_y + label_height/2
    bottom = label_y - label_height/2
    
    # 決定引線方向
    if label_x > layer_positions[0]:  # 標註在右側
        connect_x = left
        for i, yc in enumerate(layer_positions):
            # 計算連接點在標註框上的 y 位置
            if line_count > 1:
                step = label_height / (line_count + 1)
                ty = bottom + step * (i + 1)
            else:
                ty = label_y
            
            # 繪製引線
            alpha_val = 0.3 + 0.15 * (i / max(len(layer_positions), 1))
            ax.plot([layer_positions[-1] + 0.1, connect_x], [yc, ty],
                    color=color, lw=0.7, linestyle='--', alpha=alpha_val)
    else:  # 標註在左側或底部
        if label_y < 0:  # 底部標註
            connect_x = layer_positions[-1] + 0.1
            # 匯集到中央垂直線
            gather_x = label_x
            for i, yc in enumerate(layer_positions):
                ax.plot([connect_x, gather_x], [yc, yc],
                        color=color, lw=0.7, linestyle='--', alpha=0.3)
            # 垂直匯集線
            ax.plot([gather_x, gather_x],
                    [layer_positions[-1], top],
                    color=color, lw=0.7, linestyle='--', alpha=0.3)
        else:  # 左側標註
            connect_x = layer_positions[-1] + 0.1
            for i, yc in enumerate(layer_positions):
                if line_count > 1:
                    step = label_height / (line_count + 1)
                    ty = bottom + step * (i + 1)
                else:
                    ty = label_y
                alpha_val = 0.3 + 0.15 * (i / max(len(layer_positions), 1))
                ax.plot([connect_x, right], [yc, ty],
                        color=color, lw=0.7, linestyle='--', alpha=alpha_val)


# ============================================================
# 優化版前視圖
# ============================================================

def draw_optimized_front_view(geo: StriplineGeometry, pitch: float, 
                             via_enabled: bool, via_diameter: float, 
                             via_density: float, n_channels: int):
    """優化版前視圖 - 完整防重疊"""
    
    # 1. 基本參數計算
    w, h, t, s = geo.w, geo.h, geo.t / 1000, pitch
    total_w = s * n_channels
    total_h = 2 * h + 3 * t
    margin = _get_adaptive_margin(s, n_channels)
    font_size = _get_adaptive_font_size(total_w, n_channels)
    
    y0, y1, y2, y3, y4 = 0, t, t + h, t + h + t, t + h + t + h
    t_um = t * 1000
    h_um = h * 1000
    
    # 顏色定義
    c_ag, c_ag_e = '#C9A227', '#8B6914'
    c_poly, c_poly_e = '#F5E6C8', '#D4A574'
    c_via, c_dim, c_arrow, c_layer = '#A0522D', '#E74C3C', '#2980B9', '#8E44AD'
    c_background = '#F8F9FA'
    
    # 2. 創建佈局管理器
    layout_mgr = DynamicLayoutManager(total_w, total_h, n_channels, margin)
    
    # 3. 計算各元素位置
    # Layer 標註位置
    layer_pos = layout_mgr.find_safe_position(
        2.8, 1.2, 
        'right' if total_w < 5 else 'bottom'
    )
    
    # 材質圖例位置
    legend_pos = layout_mgr.find_safe_position(
        2.0, 1.0,
        'bottom' if total_w > 5 else 'right'
    )
    
    # 4. 創建圖形
    is_wide = total_w > 5 or n_channels > 6
    xlim_r = total_w + margin + (0.5 if is_wide else 3.0)
    ylim_b = -2.8 if is_wide else -1.2
    ylim_t = total_h + 0.25
    
    fig, ax = subplots(figsize=(10, 7))
    ax.set_title(
        f'前視圖 Front View (X-Z)  {n_channels}ch  w={w*1000:.0f}μm  h={h_um:.0f}μm  t={t_um:.0f}μm',
        fontsize=11, fontweight='bold', color='#2C3E50')
    ax.set_xlabel('Width (mm)', fontsize=9)
    ax.set_ylabel('Height (mm)', fontsize=9)
    ax.set_xlim(-margin, xlim_r)
    ax.set_ylim(ylim_b, ylim_t)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.12, linestyle='--')
    
    # 5. 繪製五層結構
    # Bottom GND
    ax.add_patch(Rectangle((-margin/2, y0), total_w + margin, t,
                           facecolor=c_ag, edgecolor=c_ag_e, lw=2))
    ax.text(total_w/2, y0 + t/2, 'Bottom GND', ha='center', va='center',
            fontsize=max(7, font_size-1), color='white', fontweight='bold')
    
    # 下層 Polyimide
    ax.add_patch(Rectangle((-margin/2, y1), total_w + margin, h,
                           facecolor=c_poly, edgecolor=c_poly_e, lw=2, alpha=0.85))
    
    # Signal Layer - 動態調整寬度
    signal_width = min(w, s * 0.4)
    for i in range(n_channels):
        xc = s * (i + 0.5)
        ax.add_patch(Rectangle((xc - signal_width/2, y2), signal_width, t,
                               facecolor=c_ag, edgecolor=c_ag_e, lw=2))
        
        # 信號線標註 - 根據通道數決定顯示方式
        label = f'S{i+1}'
        if n_channels > 12 and i % 2 != 0:
            label = ''
        ax.text(xc, y2 + t/2, label, ha='center', va='center',
                fontsize=max(6, font_size-1), color='white', fontweight='bold')
        
        # 接地線
        if i < n_channels - 1:
            gx = xc + s/2
            gw = min(signal_width * 0.3, s * 0.12)
            ax.add_patch(Rectangle((gx - gw/2, y2), gw, t,
                                   facecolor='#D4AF37', edgecolor=c_ag_e, lw=1.5))
            if n_channels <= 8:
                ax.text(gx, y2 + t/2, 'G', ha='center', va='center',
                        fontsize=max(5, font_size-2), color='white', fontweight='bold')
    
    # 上層 Polyimide
    ax.add_patch(Rectangle((-margin/2, y3), total_w + margin, h,
                           facecolor=c_poly, edgecolor=c_poly_e, lw=2, alpha=0.85))
    
    # Top GND
    ax.add_patch(Rectangle((-margin/2, y4), total_w + margin, t,
                           facecolor=c_ag, edgecolor=c_ag_e, lw=2))
    ax.text(total_w/2, y4 + t/2, 'Top GND', ha='center', va='center',
            fontsize=max(7, font_size-1), color='white', fontweight='bold')
    
    # 6. Via 繪製
    if via_enabled:
        vr = via_diameter / 2000
        vs = 1.0 / max(via_density, 0.1)
        if n_channels > 8:
            vs = max(vs, 1.5)
        for i in range(int(total_w / vs) + 1):
            xv = i * vs
            if xv > total_w:
                break
            ax.add_patch(Circle((xv, y0 + t/2), vr, facecolor=c_via, edgecolor='black', lw=1))
            ax.add_patch(Circle((xv, y4 + t/2), vr, facecolor=c_via, edgecolor='black', lw=1))
            ax.plot([xv, xv], [y0 + t/2 + vr, y4 + t/2 - vr], color=c_via, lw=1.8)
    
    # 7. Layer 標註
    layer_txt = _create_layer_text(t_um, h_um)
    layer_y_centers = [y4 + t/2, y3 + h/2, y2 + t/2, y1 + h/2, y0 + t/2]
    right_edge = total_w + margin/2
    
    # 使用計算出的位置
    label_x, label_y = layer_pos
    n_lines = layer_txt.count('\n') + 1
    line_height = 0.016
    label_height = n_lines * line_height + 0.03
    label_width = 2.8
    
    ax.text(label_x, label_y, layer_txt, ha='center', va='center', 
            fontsize=font_size,
            color=c_layer, fontweight='bold', family='monospace',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='#F5EEF8',
                      edgecolor=c_layer, alpha=0.95, linewidth=1.5),
            linespacing=1.6)
    
    # 繪製智慧引線
    _draw_smart_leader_lines(ax, layer_y_centers, label_x, label_y, 
                            label_width, label_height, c_layer, n_lines)
    
    # 8. Pitch 標註
    if label_y < -0.5:  # 標註在底部
        pitch_y = -0.5
    else:
        pitch_y = y0 - 0.15
    
    ax.annotate('', xy=(s * 0.5, pitch_y), xytext=(s * 1.5, pitch_y),
                arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=2))
    ax.text(s, pitch_y - 0.18, f'pitch = {s:.1f} mm', ha='center', va='top',
            fontsize=font_size+1, color=c_arrow, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#EBF5FB',
                      edgecolor=c_arrow, alpha=0.9))
    
    # 9. 外框
    ax.plot([-margin/2, total_w + margin/2, total_w + margin/2, -margin/2, -margin/2],
            [y0, y0, y4 + t, y4 + t, y0], 'k-', lw=0.6, alpha=0.35)
    
    tight_layout()
    return fig


# ============================================================
# 優化版側視圖
# ============================================================

def draw_optimized_side_view(geo: StriplineGeometry, pitch: float, length: float,
                            via_enabled: bool, via_diameter: float, 
                            via_density: float, n_channels: int):
    """優化版側視圖"""
    
    w, h, t, s, L = geo.w, geo.h, geo.t / 1000, pitch, length
    total_h = 2 * h + 3 * t
    L_show = min(L, 80)
    margin = _get_adaptive_margin(s, n_channels)
    font_size = _get_adaptive_font_size(L_show, n_channels)
    
    y0, y1, y2, y3, y4 = 0, t, t + h, t + h + t, t + h + t + h
    t_um = t * 1000
    h_um = h * 1000
    
    c_ag, c_ag_e = '#C9A227', '#8B6914'
    c_poly, c_poly_e = '#F5E6C8', '#D4A574'
    c_via, c_dim, c_arrow, c_layer = '#A0522D', '#E74C3C', '#2980B9', '#8E44AD'
    
    # 創建佈局管理器
    layout_mgr = DynamicLayoutManager(L_show, total_h, n_channels, margin)
    
    # 計算標註位置
    is_long = L_show > 35 or n_channels > 6
    layer_pos = layout_mgr.find_safe_position(
        2.8, 1.2,
        'right' if not is_long else 'bottom'
    )
    
    # 創建圖形
    xlim_r = L_show + (1.5 if is_long else 5.0)
    ylim_b = -2.8 if is_long else -1.5
    ylim_t = total_h + 0.25
    
    fig, ax = subplots(figsize=(10, 7))
    ax.set_title(
        f'側視圖 Side View (Y-Z)  L={L}mm  (顯示 {L_show}mm)',
        fontsize=11, fontweight='bold', color='#2C3E50')
    ax.set_xlabel('Length (mm)', fontsize=9)
    ax.set_ylabel('Height (mm)', fontsize=9)
    ax.set_xlim(-3, xlim_r)
    ax.set_ylim(ylim_b, ylim_t)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.12, linestyle='--')
    
    # 繪製結構
    # Bottom GND
    ax.add_patch(Rectangle((0, y0), L_show, t, facecolor=c_ag, edgecolor=c_ag_e, lw=2))
    ax.text(L_show/2, y0 + t/2, 'Bottom GND', ha='center', va='center',
            fontsize=max(7, font_size-1), color='white', fontweight='bold')
    
    # 下層 Polyimide
    ax.add_patch(Rectangle((0, y1), L_show, h, facecolor=c_poly, edgecolor=c_poly_e, lw=2, alpha=0.85))
    
    # Signal Layer
    ax.add_patch(Rectangle((0, y2), L_show, t, facecolor=c_ag, edgecolor=c_ag_e, lw=2))
    ax.text(L_show/2, y2 + t/2, 'Signal Layer', ha='center', va='center',
            fontsize=max(7, font_size-1), color='white', fontweight='bold')
    
    # 上層 Polyimide
    ax.add_patch(Rectangle((0, y3), L_show, h, facecolor=c_poly, edgecolor=c_poly_e, lw=2, alpha=0.85))
    
    # Top GND
    ax.add_patch(Rectangle((0, y4), L_show, t, facecolor=c_ag, edgecolor=c_ag_e, lw=2))
    ax.text(L_show/2, y4 + t/2, 'Top GND', ha='center', va='center',
            fontsize=max(7, font_size-1), color='white', fontweight='bold')
    
    # Via
    if via_enabled:
        vs = 1.0 / max(via_density, 0.1)
        if n_channels > 8:
            vs = max(vs, 1.5)
        for i in range(int(L_show / vs) + 1):
            xv = i * vs
            if xv > L_show:
                break
            ax.plot([xv, xv], [y0, y4 + t], color=c_via, lw=2.2, alpha=0.6)
            ax.add_patch(Circle((xv, y0), via_diameter/2000,
                                facecolor=c_via, edgecolor='black', lw=1))
            ax.add_patch(Circle((xv, y4 + t), via_diameter/2000,
                                facecolor=c_via, edgecolor='black', lw=1))
    
    # Layer 標註
    layer_txt = _create_layer_text(t_um, h_um)
    layer_y = [y4 + t/2, y3 + h/2, y2 + t/2, y1 + h/2, y0 + t/2]
    
    label_x, label_y = layer_pos
    n_lines = layer_txt.count('\n') + 1
    line_height = 0.016
    label_height = n_lines * line_height + 0.03
    label_width = 2.8
    
    ax.text(label_x, label_y, layer_txt, ha='center', va='center', 
            fontsize=font_size,
            color=c_layer, fontweight='bold', family='monospace',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='#F5EEF8',
                      edgecolor=c_layer, alpha=0.95, linewidth=1.5),
            linespacing=1.6)
    
    _draw_smart_leader_lines(ax, layer_y, label_x, label_y, 
                            label_width, label_height, c_layer, n_lines)
    
    # 總厚度標註
    if label_y < 0:
        thick_y = -0.5
    else:
        thick_y = -0.35
    
    ax.annotate('', xy=(L_show/2 - 0.6, thick_y), xytext=(L_show/2 + 0.6, thick_y),
                arrowprops=dict(arrowstyle='<->', color=c_dim, lw=1.8))
    ax.text(L_show/2, thick_y - 0.2, f'Total Thickness = {total_h*1000:.0f} μm',
            ha='center', va='top', fontsize=font_size+1, color=c_dim, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDEDEC',
                      edgecolor=c_dim, alpha=0.9))
    
    # 長度標註
    len_y = -1.2 if is_long else -1.0
    ax.annotate('', xy=(0, len_y), xytext=(L_show, len_y),
                arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=2))
    label_L = f'L = {L} mm' if L <= L_show else f'L = {L} mm (顯示 {L_show} mm)'
    ax.text(L_show/2, len_y - 0.18, label_L, ha='center', va='top',
            fontsize=font_size+1, color=c_arrow, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#EBF5FB',
                      edgecolor=c_arrow, alpha=0.9))
    
    # 各層厚度標註
    dx = L_show + 0.4
    for yy, hh, lbl in [(y0, t, f't={t_um:.0f}μm'),
                        (y1, h, f'h={h_um:.0f}μm'),
                        (y3, h, f'h={h_um:.0f}μm'),
                        (y4, t, f't={t_um:.0f}μm')]:
        ax.annotate('', xy=(dx, yy), xytext=(dx, yy + hh),
                    arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=1.2))
        ax.text(dx + 0.15, yy + hh/2, lbl, ha='left', va='center',
                fontsize=7, color=c_arrow)
    
    tight_layout()
    return fig


# ============================================================
# 優化版上視圖
# ============================================================

def draw_optimized_top_view(geo: StriplineGeometry, pitch: float, length: float,
                           via_enabled: bool, via_diameter: float, 
                           via_density: float, n_channels: int):
    """優化版上視圖"""
    
    w, h, t, s, L = geo.w, geo.h, geo.t / 1000, pitch, length
    total_w = s * n_channels
    total_h = 2 * h + 3 * t
    L_show = min(L, 80)
    margin = _get_adaptive_margin(s, n_channels)
    font_size = _get_adaptive_font_size(total_w, n_channels)
    
    c_ag, c_ag_e = '#C9A227', '#8B6914'
    c_poly, c_poly_e = '#F5E6C8', '#D4A574'
    c_via, c_dim, c_arrow = '#A0522D', '#E74C3C', '#2980B9'
    
    # 創建佈局管理器
    layout_mgr = DynamicLayoutManager(total_w, L_show, n_channels, margin)
    
    # 計算標註位置
    is_wide = total_w > 5 or n_channels > 6
    info_pos = layout_mgr.find_safe_position(2.5, 1.5, 'right')
    legend_pos = layout_mgr.find_safe_position(2.0, 1.2, 'bottom')
    
    # 創建圖形
    xlim_r = total_w + margin + (4.5 if is_wide else 3.5)
    
    fig, ax = subplots(figsize=(10, 7))
    ax.set_title(
        f'上視圖 Top View (X-Y)  {n_channels}ch  pitch={s:.1f}mm  w={w*1000:.0f}μm',
        fontsize=11, fontweight='bold', color='#2C3E50')
    ax.set_xlabel('Width (mm)', fontsize=9)
    ax.set_ylabel('Length (mm)', fontsize=9)
    ax.set_xlim(-margin, xlim_r)
    ax.set_ylim(-3.5, L_show + 2.5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.12, linestyle='--')
    
    # Top GND Layer
    ax.add_patch(Rectangle((-margin/2, 0), total_w + margin, L_show,
                           facecolor=c_ag, edgecolor=c_ag_e, lw=2, alpha=0.25))
    ax.text(total_w/2, L_show + 1.2, 'Top GND Layer', ha='center', va='bottom',
            fontsize=9, color=c_ag_e, fontweight='bold')
    
    # 信號線
    signal_width = min(w, s * 0.4)
    for i in range(n_channels):
        xc = s * (i + 0.5)
        ax.add_patch(Rectangle((xc - signal_width/2, 0), signal_width, L_show,
                               facecolor='none', edgecolor=c_ag, lw=2, linestyle='--', alpha=0.7))
        label = f'S{i+1}'
        if n_channels > 12 and i % 2 != 0:
            label = ''
        ax.text(xc, -0.9, label, ha='center', va='top',
                fontsize=max(7, font_size-1), color='#2C3E50', fontweight='bold')
    
    # 接地線
    for i in range(n_channels - 1):
        gx = s * (i + 1)
        gw = min(signal_width * 0.3, s * 0.12)
        ax.add_patch(Rectangle((gx - gw/2, 0), gw, L_show,
                               facecolor='none', edgecolor='#D4AF37', lw=1.5, linestyle=':', alpha=0.5))
    
    # Via
    if via_enabled:
        vr = via_diameter / 2000
        vs = 1.0 / max(via_density, 0.1)
        if n_channels > 8:
            vs = max(vs, 1.5)
        max_via_x = min(int(total_w / vs) + 1, 20)
        max_via_y = min(int(L_show / vs) + 1, 20)
        for ix in range(max_via_x):
            for iy in range(max_via_y):
                xv, yv = ix * vs, iy * vs
                if xv > total_w or yv > L_show:
                    continue
                ax.add_patch(Circle((xv, yv), vr, facecolor=c_via,
                                    edgecolor='black', lw=0.8, alpha=0.8))
    
    # 右側資訊面板
    info_x, info_y = info_pos
    
    # 總厚度
    ax.text(info_x, info_y,
            f'總厚度 Total Thickness\n{total_h*1000:.0f} μm',
            ha='center', va='center', fontsize=font_size+1, color=c_dim, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDEDEC',
                      edgecolor=c_dim, alpha=0.9))
    
    # Pitch
    ax.text(info_x, info_y - 0.8,
            f'通道間距 Pitch\n{s:.1f} mm ({n_channels} ch)',
            ha='center', va='center', fontsize=font_size+1, color=c_arrow, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#EBF5FB',
                      edgecolor=c_arrow, alpha=0.9))
    
    # 材質圖例
    legend_x, legend_y = legend_pos
    legend_items = [
        (c_ag, 'Ag/NbTi Conductor'),
        (c_poly, 'Polyimide (εr=3.4)'),
        (c_via, 'GND Via')
    ]
    
    legend_box_h = len(legend_items) * 0.15 + 0.2
    ax.add_patch(Rectangle((legend_x - 1.0, legend_y - legend_box_h/2),
                           2.0, legend_box_h,
                           facecolor='white', edgecolor='gray', lw=1, alpha=0.92))
    ax.text(legend_x, legend_y + legend_box_h/2 + 0.1,
            'Material Legend', ha='center', va='bottom',
            fontsize=8, color='#2C3E50', fontweight='bold')
    
    for i, (color, label) in enumerate(legend_items):
        ly = legend_y + (len(legend_items)/2 - 0.5 - i) * 0.15
        if label == 'GND Via':
            ax.add_patch(Circle((legend_x - 0.5, ly), 0.04,
                                facecolor=color, edgecolor='black', lw=1))
        else:
            ax.add_patch(Rectangle((legend_x - 0.6, ly - 0.04),
                                   0.2, 0.08,
                                   facecolor=color, edgecolor='black', lw=1.5))
        ax.text(legend_x - 0.25, ly, label, ha='left', va='center',
                fontsize=max(7, font_size-1), color='#2C3E50')
    
    # 底部標註
    center_x = total_w / 2
    w_offset = 1.4 + (n_channels > 8) * 0.3
    
    # w 標註
    ax.annotate('', xy=(center_x - signal_width/2, -w_offset), 
                xytext=(center_x + signal_width/2, -w_offset),
                arrowprops=dict(arrowstyle='<->', color=c_dim, lw=2))
    ax.text(center_x, -w_offset - 0.25, f'w = {signal_width*1000:.0f} μm', 
            ha='center', va='top',
            fontsize=font_size+1, color=c_dim, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                      edgecolor=c_dim, alpha=0.9))
    
    # 總寬度標註
    total_w_offset = w_offset + 0.75
    ax.annotate('', xy=(0, -total_w_offset), xytext=(total_w, -total_w_offset),
                arrowprops=dict(arrowstyle='<->', color=c_dim, lw=1.8))
    ax.text(total_w/2, -total_w_offset - 0.25,
            f'Total Width = {total_w:.1f} mm',
            ha='center', va='top', fontsize=font_size+1, color=c_dim, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#FDEDEC',
                      edgecolor=c_dim, alpha=0.9))
    
    # 長度標註
    length_offset = margin * 0.3
    ax.annotate('', xy=(total_w + length_offset, 0),
                xytext=(total_w + length_offset, L_show),
                arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=2))
    ax.text(total_w + length_offset + 0.25, L_show/2, f'L = {L} mm',
            ha='left', va='center', fontsize=font_size+1, color=c_arrow, fontweight='bold',
            rotation=90, rotation_mode='anchor',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#EBF5FB',
                      edgecolor=c_arrow, alpha=0.9))
    
    tight_layout()
    return fig


# ============================================================
# XLSX 匯出功能
# ============================================================

def export_optimized_xlsx(geo: StriplineGeometry, pitch: float, length: float,
                         via_enabled: bool, via_diameter: float, via_density: float,
                         n_channels: int, sig_width: float, dielectric_thickness: float,
                         sig_thickness: float):
    """優化版 XLSX 匯出功能"""
    import openpyxl
    from openpyxl.drawing.image import Image as XLImage
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils.dataframe import dataframe_to_rows
    import pandas as pd

    wb = openpyxl.Workbook()
    header_fill = PatternFill(start_color="1F77B4", end_color="1F77B4", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=11)
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                         top=Side(style='thin'), bottom=Side(style='thin'))

    # --- Sheet 1: 設計參數 ---
    ws1 = wb.active
    ws1.title = "設計參數"
    
    params = [
        ["參數名稱", "數值", "單位"],
        ["信號線寬度 (w)", sig_width, "μm"],
        ["信號線厚度 (t)", sig_thickness, "μm"],
        ["介電層厚度 (h)", dielectric_thickness, "μm"],
        ["通道間距 (pitch)", pitch, "mm"],
        ["傳輸線長度 (L)", length, "mm"],
        ["通道數", n_channels, "ch"],
        ["Via 啟用", "是" if via_enabled else "否", ""],
        ["Via 直徑", via_diameter, "μm"],
        ["Via 密度", via_density, "個/mm"],
        ["總寬度", f"{pitch * n_channels:.2f}", "mm"],
        ["總厚度", f"{2*dielectric_thickness + 3*sig_thickness:.0f}", "μm"],
        ["介電常數", "3.4", ""],
        ["導體材料", "Ag/NbTi", ""],
        ["介電材料", "Polyimide", ""]
    ]
    
    for row in params:
        ws1.append(row)

    # --- Sheet 2: 計算結果 ---
    ws2 = wb.create_sheet("計算結果")
    total_w = pitch * n_channels
    total_h = 2 * dielectric_thickness + 3 * sig_thickness
    
    calculations = [
        ["計算項目", "公式", "結果", "單位"],
        ["總寬度", f"{pitch} × {n_channels}", f"{total_w:.2f}", "mm"],
        ["總厚度", f"2×{dielectric_thickness} + 3×{sig_thickness}", f"{total_h:.0f}", "μm"],
        ["特性阻抗 (近似)", "60/√εr × ln(4h/πw)", "≈50", "Ω"],
        ["延遲時間", "√εr / c", "≈5.68", "ns/m"],
    ]
    
    for row in calculations:
        ws2.append(row)

    # --- Sheet 3: 三視圖 ---
    views = [
        ("前視圖", draw_optimized_front_view),
        ("側視圖", draw_optimized_side_view),
        ("上視圖", draw_optimized_top_view)
    ]
    
    for name, draw_func in views:
        ws = wb.create_sheet(name)
        ws.append([f"{name} {n_channels}ch | w={sig_width}μm | h={dielectric_thickness}μm"])
        
        # 繪製圖形
        if name == "前視圖":
            fig = draw_func(geo, pitch, via_enabled, via_diameter, via_density, n_channels)
        elif name == "側視圖":
            fig = draw_func(geo, pitch, length, via_enabled, via_diameter, via_density, n_channels)
        else:  # 上視圖
            fig = draw_func(geo, pitch, length, via_enabled, via_diameter, via_density, n_channels)
        
        buf = _view_to_buffer(fig)
        img = XLImage(buf)
        img.width = 700
        img.height = 480
        ws.add_image(img, "A3")
        
        # 設定列寬
        ws.column_dimensions['A'].width = 35
        ws.column_dimensions['B'].width = 40

    # 格式化所有工作表
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                cell.border = thin_border
                cell.alignment = Alignment(vertical='center', wrap_text=True)
        
        # 設定標題行
        if ws.title != "前視圖" and ws.title != "側視圖" and ws.title != "上視圖":
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # 設定列寬
            ws.column_dimensions['A'].width = 20
            ws.column_dimensions['B'].width = 30
            ws.column_dimensions['C'].width = 15

    xlsx_buf = BytesIO()
    wb.save(xlsx_buf)
    xlsx_buf.seek(0)
    return xlsx_buf.getvalue()


# ============================================================
# Streamlit 主程式
# ============================================================

def main():
    st.set_page_config(
        page_title="智慧型三視圖繪製系統 v4.0",
        page_icon="📐",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("📐 智慧型三視圖繪製系統 v4.0")
    st.markdown("*動態佈局 · 智慧防重疊 · 完整匯出*")
    st.markdown("---")

    # ── 側邊欄 ──
    with st.sidebar:
        st.header("⚙️ 物理尺寸參數")
        st.markdown("---")

        sig_width = st.slider("信號線寬度 w (μm)", 50, 500, 200, step=10)
        sig_thickness = st.slider("信號線厚度 t (μm)", 1, 20, 5, step=1)
        dielectric_thickness = st.slider("介電層厚度 h (μm)", 10, 200, 50, step=5)
        pitch = st.slider("通道間距 pitch (mm)", 0.5, 5.0, 1.5, step=0.1)
        length = st.slider("傳輸線長度 L (mm)", 10, 200, 50, step=5)
        n_channels = st.slider("通道數", 2, 16, 8, step=2)

        st.markdown("---")
        st.header("🔩 Via 設定")
        via_enabled = st.toggle("啟用 Via", value=True)
        via_diameter = st.slider("Via 直徑 (μm)", 50, 500, 200, step=10,
                                  disabled=not via_enabled)
        via_density = st.slider("Via 密度 (個/mm)", 0.5, 5.0, 2.0, step=0.1,
                                 disabled=not via_enabled)

        st.markdown("---")
        total_w = pitch * n_channels
        total_h_um = 2 * dielectric_thickness + 3 * sig_thickness
        st.info(f"""
        **即時預覽：**
        - 總寬度：{total_w:.1f} mm
        - 總厚度：{total_h_um:.0f} μm
        - 通道數：{n_channels} ch
        - 佈局模式：{'寬結構' if total_w > 5 else '窄結構'}
        """)

    # 建立幾何參數
    geo = StriplineGeometry(
        w=sig_width / 1000,
        t=sig_thickness,
        h=dielectric_thickness / 1000,
        s=pitch,
        L=length,
        n_channels=n_channels
    )

    # ── 主面板 ──
    tabs = st.tabs(["📐 前視圖", "📐 側視圖", "📐 上視圖", "📥 匯出 XLSX"])

    # 前視圖
    with tabs[0]:
        st.subheader("🔲 前視圖 Front View (X-Z)")
        col1, col2 = st.columns([3, 1])
        with col1:
            with st.spinner("繪製前視圖..."):
                fig = draw_optimized_front_view(geo, pitch, via_enabled, 
                                                via_diameter, via_density, n_channels)
                st.pyplot(fig)
        with col2:
            st.markdown("**圖例說明**")
            st.markdown("""
            - 🟨 **金色**：Ag/NbTi 導體
            - 🟫 **米色**：Polyimide 介電層
            - 🟤 **棕色**：GND Via
            - **S1, S2...**：信號線
            - **G**：接地線
            """)
            st.caption(f"通道數: {n_channels}ch | 總寬度: {total_w:.1f}mm")

    # 側視圖
    with tabs[1]:
        st.subheader("🔲 側視圖 Side View (Y-Z)")
        with st.spinner("繪製側視圖..."):
            fig = draw_optimized_side_view(geo, pitch, length, via_enabled,
                                          via_diameter, via_density, n_channels)
            st.pyplot(fig)
        st.caption(f"傳輸線長度: {length}mm | 總厚度: {total_h_um:.0f}μm")

    # 上視圖
    with tabs[2]:
        st.subheader("🔲 上視圖 Top View (X-Y)")
        with st.spinner("繪製上視圖..."):
            fig = draw_optimized_top_view(geo, pitch, length, via_enabled,
                                         via_diameter, via_density, n_channels)
            st.pyplot(fig)
        st.caption(f"通道數: {n_channels}ch | Pitch: {pitch}mm | 線寬: {sig_width}μm")

    # 匯出 XLSX
    with tabs[3]:
        st.subheader("📥 匯出 XLSX 規格檔")
        st.markdown("""
        ### 匯出內容包含：
        1. **設計參數** — 所有物理尺寸與設定值
        2. **計算結果** — 總寬度、總厚度、特性阻抗等
        3. **前視圖** — 含 PNG 圖片
        4. **側視圖** — 含 PNG 圖片  
        5. **上視圖** — 含 PNG 圖片
        """)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📥 產生並下載 XLSX 規格檔", type="primary", use_container_width=True):
                with st.spinner("正在產生 XLSX 檔案，請稍候..."):
                    xlsx_data = export_optimized_xlsx(
                        geo, pitch, length, via_enabled, via_diameter, via_density,
                        n_channels, sig_width, dielectric_thickness, sig_thickness
                    )
                
                st.download_button(
                    label="⬇️ 下載 XLSX 規格檔",
                    data=xlsx_data,
                    file_name=f"stripline_spec_{length}mm_{n_channels}ch.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                st.success("✅ XLSX 檔案已產生！")

    st.markdown("---")
    st.caption("智慧型三視圖繪製系統 v4.0 | 動態佈局 · 智慧防重疊 | Powered by Streamlit + Matplotlib + OpenPyXL")


if __name__ == "__main__":
    main()
