import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
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
# 智慧佈局管理器 - 增強版
# ============================================================

class SmartLayoutManager:
    """智慧佈局管理器 - 完整防重疊"""
    
    def __init__(self, plot_width: float, plot_height: float, n_channels: int):
        self.plot_width = plot_width
        self.plot_height = plot_height
        self.n_channels = n_channels
        self.occupied_regions = []  # (x, y, w, h)
        self.margin = 0.3
        
    def find_best_position(self, element_width: float, element_height: float,
                          preferred: str = 'auto') -> Tuple[float, float]:
        """尋找最佳標註位置"""
        
        # 根據通道數和尺寸生成候選位置
        candidates = self._generate_candidates(preferred)
        
        # 評估每個位置
        for x, y in candidates:
            if not self._check_overlap(x, y, element_width, element_height):
                # 記錄佔用區域
                self.occupied_regions.append((x - element_width/2 - 0.1, 
                                             y - element_height/2 - 0.1,
                                             element_width + 0.2, 
                                             element_height + 0.2))
                return x, y
        
        # 強制位置
        return self._force_position(element_width, element_height)
    
    def _generate_candidates(self, preferred: str) -> List[Tuple[float, float]]:
        """生成候選位置"""
        candidates = []
        w, h = self.plot_width, self.plot_height
        
        # 根據通道數調整位置
        if self.n_channels <= 4:
            # 少通道：主要放右側
            candidates.extend([
                (w + 1.5, h * 0.5),   # 右側中央
                (w + 1.5, h * 0.3),   # 右側上方
                (w + 1.5, h * 0.7),   # 右側下方
                (w * 0.5, -1.8),      # 底部中央
            ])
        elif self.n_channels <= 8:
            # 中通道：右側或底部
            candidates.extend([
                (w * 0.5, -1.8),      # 底部中央
                (w + 1.5, h * 0.5),   # 右側中央
                (w * 0.3, -1.8),      # 底部左側
                (w * 0.7, -1.8),      # 底部右側
            ])
        else:
            # 多通道：主要放底部
            candidates.extend([
                (w * 0.5, -1.8),      # 底部中央
                (w * 0.3, -1.8),      # 底部左側
                (w * 0.7, -1.8),      # 底部右側
                (w + 1.5, h * 0.5),   # 右側中央
            ])
        
        # 加入偏好調整
        if preferred == 'right':
            right_candidates = [c for c in candidates if c[0] > w]
            candidates = right_candidates + [c for c in candidates if c[0] <= w]
        elif preferred == 'bottom':
            bottom_candidates = [c for c in candidates if c[1] < 0]
            candidates = bottom_candidates + [c for c in candidates if c[1] >= 0]
        
        return candidates
    
    def _check_overlap(self, x: float, y: float, w: float, h: float) -> bool:
        """檢查是否與現有區域重疊"""
        # 邊界檢查
        if x - w/2 < -self.margin or x + w/2 > self.plot_width + 4:
            return True
        if y - h/2 < -3.0 or y + h/2 > self.plot_height + 1:
            return True
            
        # 與已佔用區域檢查
        for ox, oy, ow, oh in self.occupied_regions:
            if (abs(x - (ox + ow/2)) < (w + ow)/2 + 0.15 and
                abs(y - (oy + oh/2)) < (h + oh)/2 + 0.15):
                return True
        return False
    
    def _force_position(self, w: float, h: float) -> Tuple[float, float]:
        """強制放置位置"""
        positions = [
            (self.plot_width * 0.5, -2.2),
            (self.plot_width * 0.3, -2.2),
            (self.plot_width * 0.7, -2.2),
        ]
        
        for x, y in positions:
            if not self._check_overlap(x, y, w * 0.8, h * 0.8):
                return x, y
        
        return (self.plot_width * 0.5, -2.5)


# ============================================================
# 簡約版三視圖繪製
# ============================================================

def _get_font_size(n_channels: int) -> float:
    """根據通道數獲取字體大小"""
    if n_channels <= 4:
        return 9
    elif n_channels <= 8:
        return 8
    else:
        return 7

def _get_signal_width(w: float, s: float, n_channels: int) -> float:
    """計算信號線寬度"""
    max_width = s * 0.35
    if n_channels > 8:
        return min(w, max_width * 0.8)
    return min(w, max_width)

def draw_simple_front_view(geo: StriplineGeometry, pitch: float, 
                          via_enabled: bool, via_diameter: float, 
                          via_density: float, n_channels: int):
    """簡約版前視圖"""
    
    w, h, t, s = geo.w, geo.h, geo.t / 1000, pitch
    total_w = s * n_channels
    total_h = 2 * h + 3 * t
    margin = 0.3
    font_size = _get_font_size(n_channels)
    
    y0, y1, y2, y3, y4 = 0, t, t + h, t + h + t, t + h + t + h
    t_um = t * 1000
    h_um = h * 1000
    
    # 顏色
    c_gnd = '#D4A017'
    c_gnd_edge = '#8B6914'
    c_poly = '#F5E6C8'
    c_poly_edge = '#D4A574'
    c_signal = '#2ECC71'
    c_via = '#A0522D'
    c_text = '#2C3E50'
    
    # 創建佈局管理器
    layout_mgr = SmartLayoutManager(total_w, total_h, n_channels)
    
    # 計算標註位置
    if n_channels <= 4:
        layer_pos = layout_mgr.find_best_position(2.5, 1.0, 'right')
    else:
        layer_pos = layout_mgr.find_best_position(2.5, 1.0, 'bottom')
    
    fig, ax = subplots(figsize=(10, 6))
    ax.set_title(
        f'前視圖 Front View (X-Z)  {n_channels}ch  w={w*1000:.0f}μm  h={h_um:.0f}μm  t={t_um:.0f}μm',
        fontsize=11, fontweight='bold')
    ax.set_xlabel('Width (mm)', fontsize=9)
    ax.set_ylabel('Height (mm)', fontsize=9)
    ax.set_xlim(-margin, total_w + margin + 2.5)
    ax.set_ylim(-2.2, total_h + 0.2)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.1, linestyle='--')
    
    # 1. Bottom GND
    ax.add_patch(Rectangle((-margin/2, y0), total_w + margin, t,
                           facecolor=c_gnd, edgecolor=c_gnd_edge, lw=1.5))
    ax.text(total_w/2, y0 + t/2, 'GND', ha='center', va='center',
            fontsize=font_size, color='red', fontweight='bold')
    
    # 2. 下層介電
    ax.add_patch(Rectangle((-margin/2, y1), total_w + margin, h,
                           facecolor=c_poly, edgecolor=c_poly_edge, lw=1.5, alpha=0.8))
    
    # 3. Signal Layer (簡約)
    signal_w = _get_signal_width(w, s, n_channels)
    for i in range(n_channels):
        xc = s * (i + 0.5)
        # 信號線
        ax.add_patch(Rectangle((xc - signal_w/2, y2), signal_w, t,
                               facecolor=c_signal, edgecolor='#1A7A3A', lw=1.5))
        
        # 簡約標註：只標示部分通道
        if n_channels <= 8 or i % 2 == 0:
            label = f'S{i+1}'
            ax.text(xc, y2 + t/2, label, ha='center', va='center',
                    fontsize=font_size-1, color='red', fontweight='bold')
        
        # GND 線
        if i < n_channels - 1:
            gx = xc + s/2
            gw = signal_w * 0.25
            ax.add_patch(Rectangle((gx - gw/2, y2), gw, t,
                                   facecolor='#F39C12', edgecolor=c_gnd_edge, lw=1))
            if n_channels <= 6:
                ax.text(gx, y2 + t/2, 'G', ha='center', va='center',
                        fontsize=font_size-2, color='red', fontweight='bold')
    
    # 4. 上層介電
    ax.add_patch(Rectangle((-margin/2, y3), total_w + margin, h,
                           facecolor=c_poly, edgecolor=c_poly_edge, lw=1.5, alpha=0.8))
    
    # 5. Top GND
    ax.add_patch(Rectangle((-margin/2, y4), total_w + margin, t,
                           facecolor=c_gnd, edgecolor=c_gnd_edge, lw=1.5))
    ax.text(total_w/2, y4 + t/2, 'GND', ha='center', va='center',
            fontsize=font_size, color='red', fontweight='bold')
    
    # Via (簡約)
    if via_enabled:
        vr = via_diameter / 2000
        step = max(1.0 / via_density, 1.0)
        for i in range(int(total_w / step) + 1):
            xv = i * step
            if xv > total_w:
                break
            ax.add_patch(Circle((xv, y0 + t/2), vr, facecolor=c_via, edgecolor='black', lw=0.8))
            ax.add_patch(Circle((xv, y4 + t/2), vr, facecolor=c_via, edgecolor='black', lw=0.8))
            ax.plot([xv, xv], [y0 + t/2 + vr, y4 + t/2 - vr], color=c_via, lw=1.5, alpha=0.6)
    
    # Layer 標註 - 使用計算位置
    label_x, label_y = layer_pos
    layer_txt = (
        f'Top GND  t={t_um:.0f}μm\n'
        f'Polyimide  h={h_um:.0f}μm  εr=3.4\n'
        f'Signal  G-S-G\n'
        f'Polyimide  h={h_um:.0f}μm  εr=3.4\n'
        f'Bottom GND  t={t_um:.0f}μm'
    )
    
    ax.text(label_x, label_y, layer_txt, ha='center', va='center',
            fontsize=font_size, color='#8E44AD', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#F5EEF8',
                      edgecolor='#8E44AD', alpha=0.95, linewidth=1.5),
            linespacing=1.5)
    
    # Pitch 標註
    pitch_y = -0.5 if label_y < -0.5 else -0.15
    ax.annotate('', xy=(s * 0.5, pitch_y), xytext=(s * 1.5, pitch_y),
                arrowprops=dict(arrowstyle='<->', color='#2980B9', lw=1.5))
    ax.text(s, pitch_y - 0.15, f'pitch={s:.1f}mm', ha='center', va='top',
            fontsize=font_size, color='#2980B9', fontweight='bold')
    
    tight_layout()
    return fig


def draw_simple_side_view(geo: StriplineGeometry, pitch: float, length: float,
                         via_enabled: bool, via_diameter: float, 
                         via_density: float, n_channels: int):
    """簡約版側視圖 - 完全防重疊"""
    
    w, h, t, s, L = geo.w, geo.h, geo.t / 1000, pitch, length
    total_h = 2 * h + 3 * t
    L_show = min(L, 60)  # 顯示長度
    font_size = _get_font_size(n_channels)
    
    y0, y1, y2, y3, y4 = 0, t, t + h, t + h + t, t + h + t + h
    t_um = t * 1000
    h_um = h * 1000
    
    # 顏色
    c_gnd = '#D4A017'
    c_gnd_edge = '#8B6914'
    c_poly = '#F5E6C8'
    c_poly_edge = '#D4A574'
    c_signal = '#2ECC71'
    c_via = '#A0522D'
    c_text = '#2C3E50'
    
    # 創建佈局管理器
    layout_mgr = SmartLayoutManager(L_show, total_h, n_channels)
    
    # 計算所有標註位置 - 確保不重疊
    # 1. Layer 標註
    if n_channels <= 4:
        layer_pos = layout_mgr.find_best_position(2.5, 0.9, 'right')
    else:
        layer_pos = layout_mgr.find_best_position(2.5, 0.9, 'bottom')
    
    # 2. 總厚度標註 - 放在與 Layer 標註不同的位置
    thick_pos = layout_mgr.find_best_position(2.0, 0.4, 'bottom')
    
    # 3. 長度標註
    len_pos = layout_mgr.find_best_position(1.5, 0.3, 'bottom')
    
    fig, ax = subplots(figsize=(10, 6))
    ax.set_title(
        f'側視圖 Side View (Y-Z)  L={L}mm  (顯示 {L_show}mm)',
        fontsize=11, fontweight='bold')
    ax.set_xlabel('Length (mm)', fontsize=9)
    ax.set_ylabel('Height (mm)', fontsize=9)
    ax.set_xlim(-0.5, L_show + 3.5)
    ax.set_ylim(-2.8, total_h + 0.2)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.1, linestyle='--')
    
    # 繪製結構
    # Bottom GND
    ax.add_patch(Rectangle((0, y0), L_show, t, facecolor=c_gnd, edgecolor=c_gnd_edge, lw=1.5))
    ax.text(L_show/2, y0 + t/2, 'GND', ha='center', va='center',
            fontsize=font_size, color='red', fontweight='bold')
    
    # 下層介電
    ax.add_patch(Rectangle((0, y1), L_show, h, facecolor=c_poly, edgecolor=c_poly_edge, lw=1.5, alpha=0.8))
    
    # Signal
    ax.add_patch(Rectangle((0, y2), L_show, t, facecolor=c_signal, edgecolor='#1A7A3A', lw=1.5))
    ax.text(L_show/2, y2 + t/2, 'Signal', ha='center', va='center', fontsize=font_size, color='red', fontweight='bold')
    
    # 上層介電
    ax.add_patch(Rectangle((0, y3), L_show, h, facecolor=c_poly, edgecolor=c_poly_edge, lw=1.5, alpha=0.8))
    
    # Top GND
    ax.add_patch(Rectangle((0, y4), L_show, t, facecolor=c_gnd, edgecolor=c_gnd_edge, lw=1.5))
    ax.text(L_show/2, y4 + t/2, 'GND', ha='center', va='center', fontsize=font_size, color='red', fontweight='bold')
    
    # Via
    if via_enabled:
        step = max(1.0 / via_density, 1.5)
        for i in range(int(L_show / step) + 1):
            xv = i * step
            if xv > L_show:
                break
            ax.plot([xv, xv], [y0, y4 + t], color=c_via, lw=1.5, alpha=0.5)
            ax.add_patch(Circle((xv, y0), via_diameter/2000, facecolor=c_via, edgecolor='black', lw=0.8))
            ax.add_patch(Circle((xv, y4 + t), via_diameter/2000, facecolor=c_via, edgecolor='black', lw=0.8))
    
    # Layer 標註 - 使用計算位置
    label_x, label_y = layer_pos
    layer_txt = (
        f'Top GND  t={t_um:.0f}μm\n'
        f'Polyimide  h={h_um:.0f}μm\n'
        f'Signal Layer\n'
        f'Polyimide  h={h_um:.0f}μm\n'
        f'Bottom GND  t={t_um:.0f}μm'
    )
    
    #ax.text(label_x, label_y, layer_txt, ha='center', va='center', fontsize=font_size, color='#8E44AD', fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#F5EEF8', edgecolor='#8E44AD', alpha=0.95, linewidth=1.5), linespacing=1.5)
    
    # 總厚度標註 - 使用計算位置（避免與 Layer 標註重疊）
    thick_x, thick_y = thick_pos
    # 確保厚度標註與 Layer 標註保持距離
    if abs(thick_x - label_x) < 1.5 and abs(thick_y - label_y) < 0.8:
        thick_x = L_show * 0.5
        thick_y = -1.0
    
    ax.annotate('', xy=(thick_x - 0.5, -0.3), xytext=(thick_x + 0.5, -0.3),
                arrowprops=dict(arrowstyle='<->', color='#E74C3C', lw=1.5))
    ax.text(thick_x, -0.5, f'Total={total_h*1000:.0f}μm',
            ha='center', va='top', fontsize=font_size, color='#E74C3C', fontweight='bold')
    
    # 長度標註 - 使用計算位置
    len_x, len_y = len_pos
    # 確保長度標註與其他標註不重疊
    if abs(len_x - label_x) < 1.5 and abs(len_y - label_y) < 0.8:
        len_x = L_show * 0.5
        len_y = -1.8
    if abs(len_x - thick_x) < 1.0 and abs(len_y - thick_y) < 0.5:
        len_x = L_show * 0.5
        len_y = -1.8
    
    ax.annotate('', xy=(0, len_y), xytext=(L_show, len_y),
                arrowprops=dict(arrowstyle='<->', color='#2980B9', lw=1.5))
    label = f'L={L}mm' if L <= L_show else f'L={L}mm (show {L_show}mm)'
    ax.text(L_show/2, len_y - 0.15, label, ha='center', va='top',
            fontsize=font_size, color='#2980B9', fontweight='bold')
    
    # 右側厚度標註（簡約）
    dx = L_show + 0.3
    for yy, hh, lbl in [(y0, t, f'{t_um:.0f}'),
                        (y1, h, f'{h_um:.0f}'),
                        (y3, h, f'{h_um:.0f}'),
                        (y4, t, f'{t_um:.0f}')]:
        if yy < total_h - 0.1:  # 避免重疊
            ax.annotate('', xy=(dx, yy), xytext=(dx, yy + hh),
                        arrowprops=dict(arrowstyle='<->', color='#95A5A6', lw=1))
            ax.text(dx + 0.15, yy + hh/2, lbl, ha='left', va='center',
                    fontsize=font_size-1, color='#7F8C8D')
    
    tight_layout()
    return fig


def draw_simple_top_view(geo: StriplineGeometry, pitch: float, length: float,
                        via_enabled: bool, via_diameter: float, 
                        via_density: float, n_channels: int):
    """簡約版上視圖"""
    
    w, h, t, s, L = geo.w, geo.h, geo.t / 1000, pitch, length
    total_w = s * n_channels
    total_h = 2 * h + 3 * t
    L_show = min(L, 60)
    font_size = _get_font_size(n_channels)
    
    c_gnd = '#D4A017'
    c_gnd_edge = '#8B6914'
    c_signal = '#2ECC71'
    c_via = '#A0522D'
    c_text = '#2C3E50'
    
    # 創建佈局管理器
    layout_mgr = SmartLayoutManager(total_w, L_show, n_channels)
    
    # 計算資訊面板位置
    info_pos = layout_mgr.find_best_position(2.5, 1.2, 'right')
    
    fig, ax = subplots(figsize=(10, 6))
    ax.set_title(
        f'上視圖 Top View (X-Y)  {n_channels}ch  pitch={s:.1f}mm  w={w*1000:.0f}μm',
        fontsize=11, fontweight='bold')
    ax.set_xlabel('Width (mm)', fontsize=9)
    ax.set_ylabel('Length (mm)', fontsize=9)
    ax.set_xlim(-0.5, total_w + 4.0)
    ax.set_ylim(-2.5, L_show + 1.5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.1, linestyle='--')
    
    # Top GND (半透明)
    ax.add_patch(Rectangle((-0.2, 0), total_w + 0.4, L_show,
                           facecolor=c_gnd, edgecolor=c_gnd_edge, lw=1.5, alpha=0.2))
    ax.text(total_w/2, L_show + 0.8, 'Top GND Layer', ha='center', va='bottom',
            fontsize=font_size, color=c_gnd_edge, fontweight='bold')
    
    # 信號線
    signal_w = _get_signal_width(w, s, n_channels)
    for i in range(n_channels):
        xc = s * (i + 0.5)
        ax.add_patch(Rectangle((xc - signal_w/2, 0), signal_w, L_show,
                               facecolor='none', edgecolor=c_signal, lw=1.5, linestyle='--', alpha=0.6))
        # 簡約標註
        if n_channels <= 8 or i % 2 == 0:
            label = f'S{i+1}'
            ax.text(xc, -0.6, label, ha='center', va='top',
                    fontsize=font_size-1, color=c_text, fontweight='bold')
    
    # Via
    if via_enabled:
        vr = via_diameter / 2000
        step = max(1.0 / via_density, 1.5)
        for ix in range(int(total_w / step) + 1):
            for iy in range(int(L_show / step) + 1):
                xv, yv = ix * step, iy * step
                if xv > total_w or yv > L_show:
                    continue
                ax.add_patch(Circle((xv, yv), vr, facecolor=c_via,
                                    edgecolor='black', lw=0.5, alpha=0.6))
    
    # 右側資訊面板
    info_x, info_y = info_pos
    info_text = (
        f'通道數: {n_channels} ch\n'
        f'總寬度: {total_w:.1f} mm\n'
        f'總厚度: {total_h*1000:.0f} μm\n'
        f'Pitch: {s:.1f} mm'
    )
    
    ax.text(info_x, info_y, info_text, ha='center', va='center',
            fontsize=font_size, color='#2C3E50', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#EBF5FB',
                      edgecolor='#2980B9', alpha=0.95, linewidth=1.5),
            linespacing=1.5)
    
    # 底部標註 - 簡約
    # w 標註
    ax.annotate('', xy=(total_w/2 - signal_w/2, -1.2), 
                xytext=(total_w/2 + signal_w/2, -1.2),
                arrowprops=dict(arrowstyle='<->', color='#E74C3C', lw=1.5))
    ax.text(total_w/2, -1.4, f'w={signal_w*1000:.0f}μm', 
            ha='center', va='top', fontsize=font_size, color='#E74C3C')
    
    # 總寬度
    ax.annotate('', xy=(0, -1.9), xytext=(total_w, -1.9),
                arrowprops=dict(arrowstyle='<->', color='#E74C3C', lw=1.5))
    ax.text(total_w/2, -2.1, f'Total={total_w:.1f}mm',
            ha='center', va='top', fontsize=font_size, color='#E74C3C')
    
    # 長度標註
    ax.annotate('', xy=(total_w + 0.3, 0), xytext=(total_w + 0.3, L_show),
                arrowprops=dict(arrowstyle='<->', color='#2980B9', lw=1.5))
    ax.text(total_w + 0.6, L_show/2, f'L={L}mm',
            ha='left', va='center', fontsize=font_size, color='#2980B9')
    
    tight_layout()
    return fig


# ============================================================
# XLSX 匯出
# ============================================================

def export_simple_xlsx(geo: StriplineGeometry, pitch: float, length: float,
                      via_enabled: bool, via_diameter: float, via_density: float,
                      n_channels: int, sig_width: float, dielectric_thickness: float,
                      sig_thickness: float):
    """簡約版 XLSX 匯出"""
    import openpyxl
    from openpyxl.drawing.image import Image as XLImage
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

    wb = openpyxl.Workbook()
    header_fill = PatternFill(start_color="2ECC71", end_color="2ECC71", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=11)
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                         top=Side(style='thin'), bottom=Side(style='thin'))

    # 設計參數
    ws1 = wb.active
    ws1.title = "設計參數"
    params = [
        ["參數", "數值", "單位"],
        ["信號線寬度 (w)", sig_width, "μm"],
        ["信號線厚度 (t)", sig_thickness, "μm"],
        ["介電層厚度 (h)", dielectric_thickness, "μm"],
        ["通道間距 (pitch)", pitch, "mm"],
        ["傳輸線長度 (L)", length, "mm"],
        ["通道數", n_channels, "ch"],
        ["Via 啟用", "是" if via_enabled else "否", ""],
        ["Via 直徑", via_diameter, "μm"],
        ["Via 密度", via_density, "個/mm"],
    ]
    for row in params:
        ws1.append(row)

    # 計算結果
    ws2 = wb.create_sheet("計算結果")
    total_w = pitch * n_channels
    total_h = 2 * dielectric_thickness + 3 * sig_thickness
    results = [
        ["項目", "結果", "單位"],
        ["總寬度", f"{total_w:.1f}", "mm"],
        ["總厚度", f"{total_h:.0f}", "μm"],
        ["特性阻抗 (近似)", "≈50", "Ω"],
    ]
    for row in results:
        ws2.append(row)

    # 三視圖
    views = [
        ("前視圖", draw_simple_front_view),
        ("側視圖", draw_simple_side_view),
        ("上視圖", draw_simple_top_view)
    ]
    
    for name, draw_func in views:
        ws = wb.create_sheet(name)
        ws.append([f"{name} - {n_channels}ch"])
        
        if name == "前視圖":
            fig = draw_func(geo, pitch, via_enabled, via_diameter, via_density, n_channels)
        elif name == "側視圖":
            fig = draw_func(geo, pitch, length, via_enabled, via_diameter, via_density, n_channels)
        else:
            fig = draw_func(geo, pitch, length, via_enabled, via_diameter, via_density, n_channels)
        
        buf = _view_to_buffer(fig)
        img = XLImage(buf)
        img.width = 700
        img.height = 450
        ws.add_image(img, "A3")
        ws.column_dimensions['A'].width = 35

    # 格式化
    for ws in [ws1, ws2]:
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 15

    xlsx_buf = BytesIO()
    wb.save(xlsx_buf)
    xlsx_buf.seek(0)
    return xlsx_buf.getvalue()


def _view_to_buffer(fig) -> BytesIO:
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)
    return buf


# ============================================================
# Streamlit 主程式
# ============================================================

def main():
    st.set_page_config(
        page_title="簡約三視圖繪製系統",
        page_icon="📐",
        layout="wide"
    )

    st.title("📐 簡約三視圖繪製系統")
    st.markdown("*智慧防重疊 · 簡約清晰*")
    st.markdown("---")

    with st.sidebar:
        st.header("⚙️ 參數設定")
        
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
        total_h = 2 * dielectric_thickness + 3 * sig_thickness
        st.info(f"""
        **即時資訊**
        - 總寬度：{total_w:.1f} mm
        - 總厚度：{total_h:.0f} μm
        - 通道數：{n_channels} ch
        """)

    geo = StriplineGeometry(
        w=sig_width / 1000,
        t=sig_thickness,
        h=dielectric_thickness / 1000,
        s=pitch,
        L=length,
        n_channels=n_channels
    )

    tabs = st.tabs(["📐 前視圖", "📐 側視圖", "📐 上視圖", "📥 匯出"])

    with tabs[0]:
        st.subheader("前視圖 Front View")
        fig = draw_simple_front_view(geo, pitch, via_enabled, via_diameter, via_density, n_channels)
        st.pyplot(fig)

    with tabs[1]:
        st.subheader("側視圖 Side View")
        fig = draw_simple_side_view(geo, pitch, length, via_enabled, via_diameter, via_density, n_channels)
        st.pyplot(fig)

    with tabs[2]:
        st.subheader("上視圖 Top View")
        fig = draw_simple_top_view(geo, pitch, length, via_enabled, via_diameter, via_density, n_channels)
        st.pyplot(fig)

    with tabs[3]:
        st.subheader("📥 匯出 XLSX")
        if st.button("產生並下載 XLSX", type="primary"):
            with st.spinner("產生中..."):
                xlsx_data = export_simple_xlsx(
                    geo, pitch, length, via_enabled, via_diameter, via_density,
                    n_channels, sig_width, dielectric_thickness, sig_thickness
                )
            st.download_button(
                label="⬇️ 下載",
                data=xlsx_data,
                file_name=f"stripline_{length}mm_{n_channels}ch.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.success("✅ 完成！")

    st.markdown("---")
    st.caption("簡約三視圖系統 | 智慧防重疊")


if __name__ == "__main__":
    main()
