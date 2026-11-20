"""
通用型三視圖繪製系統 v3.0 — 普適通用版（動態防重疊 + 全局參數集中）
功能：
  1. 依通道數/尺寸動態偵測並避開傳輸線重疊
  2. 全局參數（總厚度、pitch、Legend）集中於上視圖右側空白處
  3. 三視圖各自獨立標註 Layers 與尺寸

安裝需求：
  pip install streamlit matplotlib openpyxl

執行方式：
  streamlit run crioflex3_three_view_v3.py
"""

import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from matplotlib.pyplot import subplots, tight_layout
from dataclasses import dataclass
from io import BytesIO
from typing import List, Dict, Tuple

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
# 通用輔助
# ============================================================

def _view_to_buffer(fig) -> BytesIO:
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)
    return buf


def _layer_text(t_um: float, h_um: float) -> str:
    """產生統一格式的 Layer 標註文字"""
    return (
        f'L5  Top GND      t={t_um:.0f}μm\n'
        f'L4  Polyimide     h={h_um:.0f}μm  εr=3.4\n'
        f'L3  Signal        G-S-G\n'
        f'L2  Polyimide     h={h_um:.0f}μm  εr=3.4\n'
        f'L1  Bottom GND    t={t_um:.0f}μm'
    )


# ============================================================
# 前視圖 (Front View) — 動態佈局
# ============================================================
# 策略：
#   - n_channels ≤ 4（結構較窄）：Layer 標註放右側中央，pitch 放底部中央
#   - n_channels > 4（結構較寬）：Layer 標註放底部中央偏右，pitch 放底部中央偏左
#   - 引線自動跟隨標註位置

def draw_front_view(geo: StriplineGeometry, pitch: float, via_enabled: bool,
                    via_diameter: float, via_density: float, n_channels: int):
    w, h, t, s = geo.w, geo.h, geo.t / 1000, pitch
    total_w = s * n_channels
    total_h = 2 * h + 3 * t
    margin = max(s * 0.35, 0.3)
    y0, y1, y2, y3, y4 = 0, t, t + h, t + h + t, t + h + t + h
    t_um = t * 1000
    h_um = h * 1000

    c_ag, c_ag_e = '#C9A227', '#8B6914'
    c_poly, c_poly_e = '#F5E6C8', '#D4A574'
    c_via, c_dim, c_arrow, c_layer = '#A0522D', '#E74C3C', '#2980B9', '#8E44AD'

    # ===== 動態佈局決策 =====
    # 結構寬度門檻：超過 6mm 視為「寬結構」，標註改放下方
    WIDE_THRESHOLD = 6.0
    is_wide = total_w > WIDE_THRESHOLD

    if is_wide:
        # 寬結構：標註放下方，需要更大的底部空間
        xlim_r = total_w + margin + 0.5
        ylim_b = -2.2
        ylim_t = total_h + 0.25
    else:
        # 窄結構：標註放右側，底部空間較小
        xlim_r = total_w + margin + 3.0
        ylim_b = -0.8
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

    # 五層結構
    ax.add_patch(Rectangle((-margin / 2, y0), total_w + margin, t,
                           facecolor=c_ag, edgecolor=c_ag_e, lw=2))
    ax.text(total_w / 2, y0 + t / 2, 'Bottom GND', ha='center', va='center',
            fontsize=8, color='white', fontweight='bold')

    ax.add_patch(Rectangle((-margin / 2, y1), total_w + margin, h,
                           facecolor=c_poly, edgecolor=c_poly_e, lw=2, alpha=0.85))

    for i in range(n_channels):
        xc = s * (i + 0.5)
        ax.add_patch(Rectangle((xc - w / 2, y2), w, t,
                               facecolor=c_ag, edgecolor=c_ag_e, lw=2))
        ax.text(xc, y2 + t / 2, f'S{i+1}', ha='center', va='center',
                fontsize=8, color='white', fontweight='bold')
        if i < n_channels - 1:
            gx = xc + s / 2
            gw = w * 0.3
            ax.add_patch(Rectangle((gx - gw / 2, y2), gw, t,
                                   facecolor='#D4AF37', edgecolor=c_ag_e, lw=1.5))
            ax.text(gx, y2 + t / 2, 'G', ha='center', va='center',
                    fontsize=7, color='white', fontweight='bold')

    ax.add_patch(Rectangle((-margin / 2, y3), total_w + margin, h,
                           facecolor=c_poly, edgecolor=c_poly_e, lw=2, alpha=0.85))

    ax.add_patch(Rectangle((-margin / 2, y4), total_w + margin, t,
                           facecolor=c_ag, edgecolor=c_ag_e, lw=2))
    ax.text(total_w / 2, y4 + t / 2, 'Top GND', ha='center', va='center',
            fontsize=8, color='white', fontweight='bold')

    # Via
    if via_enabled:
        vr = via_diameter / 2000
        vs = 1.0 / max(via_density, 0.1)
        for i in range(int(total_w / vs) + 1):
            xv = i * vs
            if xv > total_w:
                break
            ax.add_patch(Circle((xv, y0 + t / 2), vr, facecolor=c_via, edgecolor='black', lw=1))
            ax.add_patch(Circle((xv, y4 + t / 2), vr, facecolor=c_via, edgecolor='black', lw=1))
            ax.plot([xv, xv], [y0 + t / 2 + vr, y4 + t / 2 - vr], color=c_via, lw=1.8)

    # ===== Layer 標註 + 引線（動態位置）=====
    layer_txt = _layer_text(t_um, h_um)
    layer_y_centers = [y4 + t / 2, y3 + h / 2, y2 + t / 2, y1 + h / 2, y0 + t / 2]
    right_edge = total_w + margin / 2

    if not is_wide:
        # 窄結構：標註放右側中央
        label_x = total_w + margin * 0.6
        label_y = total_h / 2
        ax.text(label_x, label_y, layer_txt, ha='left', va='center', fontsize=8,
                color=c_layer, fontweight='bold', family='monospace',
                bbox=dict(boxstyle='round,pad=0.35', facecolor='#F5EEF8',
                          edgecolor=c_layer, alpha=0.95, linewidth=1.5),
                linespacing=1.6)
        # 引線：從各層右邊緣 → 文字塊
        text_top = label_y + 2 * 0.016
        step = 0.016
        for i, yc in enumerate(layer_y_centers):
            ty = text_top - i * step
            ax.plot([right_edge, label_x - 0.06], [yc, ty],
                    color=c_layer, lw=0.7, linestyle='--', alpha=0.5)
        # pitch 放底部中央
        ay = y0 - 0.15
        ax.annotate('', xy=(s * 0.5, ay), xytext=(s * 1.5, ay),
                    arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=2))
        ax.text(s, ay - 0.18, f'pitch = {s:.1f} mm', ha='center', va='top',
                fontsize=9, color=c_arrow, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#EBF5FB',
                          edgecolor=c_arrow, alpha=0.9))
    else:
        # 寬結構：標註放底部中央偏右
        label_x = total_w / 2 + 1.5
        label_y = -0.85
        ax.text(label_x, label_y, layer_txt, ha='left', va='center', fontsize=8,
                color=c_layer, fontweight='bold', family='monospace',
                bbox=dict(boxstyle='round,pad=0.35', facecolor='#F5EEF8',
                          edgecolor=c_layer, alpha=0.95, linewidth=1.5),
                linespacing=1.6)
        # 引線：從各層右邊緣 → 匯集 → 文字塊上方
        gather_x = label_x - 0.08
        for i, yc in enumerate(layer_y_centers):
            ax.plot([right_edge, gather_x], [yc, yc],
                    color=c_layer, lw=0.7, linestyle='--', alpha=0.5)
        ax.plot([gather_x, gather_x],
                [layer_y_centers[-1], layer_y_centers[0]],
                color=c_layer, lw=0.7, linestyle='--', alpha=0.5)
        ax.plot([gather_x, gather_x], [layer_y_centers[0], label_y + 0.18],
                color=c_layer, lw=0.7, linestyle='--', alpha=0.5)
        # pitch 放底部中央偏左
        pitch_x = total_w / 2 - 1.5
        ay = -0.85
        ax.annotate('', xy=(pitch_x - s / 2, ay), xytext=(pitch_x + s / 2, ay),
                    arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=2))
        ax.text(pitch_x, ay - 0.18, f'pitch = {s:.1f} mm', ha='center', va='top',
                fontsize=9, color=c_arrow, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#EBF5FB',
                          edgecolor=c_arrow, alpha=0.9))

    # 外框
    ax.plot([-margin / 2, total_w + margin / 2, total_w + margin / 2, -margin / 2, -margin / 2],
            [y0, y0, y4 + t, y4 + t, y0], 'k-', lw=0.6, alpha=0.35)
    tight_layout()
    return fig


# ============================================================
# 側視圖 (Side View) — 動態佈局
# ============================================================
# 策略：
#   - L_show ≤ 40mm（結構較短）：Layer 標註放右側中央，總厚度放底部中央
#   - L_show > 40mm（結構較長）：Layer 標註放底部中央偏右，總厚度放底部中央偏左

def draw_side_view(geo: StriplineGeometry, pitch: float, length: float,
                   via_enabled: bool, via_diameter: float, via_density: float, n_channels: int):
    w, h, t, s, L = geo.w, geo.h, geo.t / 1000, pitch, length
    total_h = 2 * h + 3 * t
    L_show = min(L, 80)
    margin = max(s * 0.35, 0.3)
    y0, y1, y2, y3, y4 = 0, t, t + h, t + h + t, t + h + t + h
    t_um = t * 1000
    h_um = h * 1000

    c_ag, c_ag_e = '#C9A227', '#8B6914'
    c_poly, c_poly_e = '#F5E6C8', '#D4A574'
    c_via, c_dim, c_arrow, c_layer = '#A0522D', '#E74C3C', '#2980B9', '#8E44AD'

    # ===== 動態佈局決策 =====
    LONG_THRESHOLD = 40.0
    is_long = L_show > LONG_THRESHOLD

    if is_long:
        xlim_r = L_show + 1.5
        ylim_b = -2.2
        ylim_t = total_h + 0.25
    else:
        xlim_r = L_show + 5.0
        ylim_b = -1.2
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

    ax.add_patch(Rectangle((0, y0), L_show, t, facecolor=c_ag, edgecolor=c_ag_e, lw=2))
    ax.text(L_show / 2, y0 + t / 2, 'Bottom GND', ha='center', va='center',
            fontsize=8, color='white', fontweight='bold')

    ax.add_patch(Rectangle((0, y1), L_show, h, facecolor=c_poly, edgecolor=c_poly_e, lw=2, alpha=0.85))

    ax.add_patch(Rectangle((0, y2), L_show, t, facecolor=c_ag, edgecolor=c_ag_e, lw=2))
    ax.text(L_show / 2, y2 + t / 2, 'Signal Layer', ha='center', va='center',
            fontsize=8, color='white', fontweight='bold')

    ax.add_patch(Rectangle((0, y3), L_show, h, facecolor=c_poly, edgecolor=c_poly_e, lw=2, alpha=0.85))

    ax.add_patch(Rectangle((0, y4), L_show, t, facecolor=c_ag, edgecolor=c_ag_e, lw=2))
    ax.text(L_show / 2, y4 + t / 2, 'Top GND', ha='center', va='center',
            fontsize=8, color='white', fontweight='bold')

    if via_enabled:
        vs = 1.0 / max(via_density, 0.1)
        for i in range(int(L_show / vs) + 1):
            xv = i * vs
            if xv > L_show:
                break
            ax.plot([xv, xv], [y0, y4 + t], color=c_via, lw=2.2, alpha=0.6)
            ax.add_patch(Circle((xv, y0), via_diameter / 2000,
                                facecolor=c_via, edgecolor='black', lw=1))
            ax.add_patch(Circle((xv, y4 + t), via_diameter / 2000,
                                facecolor=c_via, edgecolor='black', lw=1))

    # ===== 動態標註佈局 =====
    layer_txt = _layer_text(t_um, h_um)
    layer_y = [y4 + t / 2, y3 + h / 2, y2 + t / 2, y1 + h / 2, y0 + t / 2]
    right_edge = L_show + 0.05

    if not is_long:
        # 短結構：Layer 放右側中央
        label_x = L_show + 1.3
        label_y = total_h / 2
        ax.text(label_x, label_y, layer_txt, ha='left', va='center', fontsize=8, color=c_layer, fontweight='bold', family='monospace', bbox=dict(boxstyle='round,pad=0.35', facecolor='#F5EEF8', edgecolor=c_layer, alpha=0.95, linewidth=1.5), linespacing=1.6)
        # 引線
        text_top = label_y + 2 * 0.016
        step = 0.016
        for i, yc in enumerate(layer_y):
            ty = text_top - i * step
            ax.plot([right_edge, label_x - 0.06], [yc, ty],
                    color=c_layer, lw=0.7, linestyle='--', alpha=0.5)
        # 總厚度放底部中央
        thick_x = L_show / 2
        ax.annotate('', xy=(thick_x - 0.6, -0.35), xytext=(thick_x + 0.6, -0.35),
                    arrowprops=dict(arrowstyle='<->', color=c_dim, lw=1.8))
        ax.text(thick_x, -0.55, f'Total Thickness = {total_h*1000:.0f} μm',
                ha='center', va='top', fontsize=9, color=c_dim, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDEDEC',
                          edgecolor=c_dim, alpha=0.9))
    else:
        # 長結構：Layer 放底部中央偏右
        label_x = L_show / 2 + 2.0
        label_y = -0.85
        #ax.text(label_x, label_y, layer_txt, ha='left', va='center', fontsize=8, color=c_layer, fontweight='bold', family='monospace', bbox=dict(boxstyle='round,pad=0.35', facecolor='#F5EEF8', edgecolor=c_layer, alpha=0.95, linewidth=1.5), linespacing=1.6)
        # 引線
        gather_x = label_x - 0.08
        for i, yc in enumerate(layer_y):
            ax.plot([right_edge, gather_x], [yc, yc],
                    color=c_layer, lw=0.7, linestyle='--', alpha=0.5)
        ax.plot([gather_x, gather_x],
                [layer_y[-1], layer_y[0]],
                color=c_layer, lw=0.7, linestyle='--', alpha=0.5)
        ax.plot([gather_x, gather_x], [layer_y[0], label_y + 0.18],
                color=c_layer, lw=0.7, linestyle='--', alpha=0.5)
        # 總厚度放底部中央偏左
        thick_x = L_show / 2 - 2.0
        ax.annotate('', xy=(thick_x - 0.6, -0.35), xytext=(thick_x + 0.6, -0.35),
                    arrowprops=dict(arrowstyle='<->', color=c_dim, lw=1.8))
        ax.text(thick_x, -0.55, f'Total Thickness = {total_h*1000:.0f} μm',
                ha='center', va='top', fontsize=9, color=c_dim, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDEDEC',
                          edgecolor=c_dim, alpha=0.9))

    # 底部長度標註（始終在最底部）
    len_y = -1.55 if is_long else -1.0
    ax.annotate('', xy=(0, len_y), xytext=(L_show, len_y),
                arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=2))
    label_L = f'L = {L} mm' if L <= L_show else f'L = {L} mm (顯示 {L_show} mm)'
    ax.text(L_show / 2, len_y - 0.18, label_L, ha='center', va='top',
            fontsize=9, color=c_arrow, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#EBF5FB',
                      edgecolor=c_arrow, alpha=0.9))

    # 右側各層厚度標註（始終保留）
    dx = L_show + 0.4
    for yy, hh, lbl in [(y0, t, f't={t_um:.0f}μm'),
                        (y1, h, f'h={h_um:.0f}μm'),
                        (y3, h, f'h={h_um:.0f}μm'),
                        (y4, t, f't={t_um:.0f}μm')]:
        ax.annotate('', xy=(dx, yy), xytext=(dx, yy + hh),
                    arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=1.2))
        ax.text(dx + 0.15, yy + hh / 2, lbl, ha='left', va='center',
                fontsize=7, color=c_arrow)

    tight_layout()
    return fig


# ============================================================
# 上視圖 (Top View) — 全局參數集中 + 動態防重疊
# ============================================================
# 策略：
#   - 全局參數（總厚度、pitch、材質 Legend）集中於右側空白處
#   - 當結構較寬（total_w > 6mm）時，右側空間壓縮，自動調整 xlim
#   - 底部 w / 總寬度 標註置於下圖置中，垂直分開不重叠

def draw_top_view(geo: StriplineGeometry, pitch: float, length: float,
                  via_enabled: bool, via_diameter: float, via_density: float, n_channels: int):
    w, h, t, s, L = geo.w, geo.h, geo.t / 1000, pitch, length
    total_w = s * n_channels
    total_h = 2 * h + 3 * t
    L_show = min(L, 80)
    margin = max(s * 0.35, 0.3)
    t_um = t * 1000
    h_um = h * 1000

    c_ag, c_ag_e = '#C9A227', '#8B6914'
    c_poly, c_poly_e = '#F5E6C8', '#D4A574'
    c_via, c_dim, c_arrow = '#A0522D', '#E74C3C', '#2980B9'

    # 動態 xlim：根據結構寬度調整，確保右側有足夠空間放全局參數
    WIDE_THRESHOLD = 6.0
    is_wide = total_w > WIDE_THRESHOLD
    xlim_r = total_w + margin + (4.5 if is_wide else 3.5)

    fig, ax = subplots(figsize=(10, 7))
    ax.set_title(
        f'上視圖 Top View (X-Y)  {n_channels}ch  pitch={s:.1f}mm  w={w*1000:.0f}μm',
        fontsize=11, fontweight='bold', color='#2C3E50')
    ax.set_xlabel('Width (mm)', fontsize=9)
    ax.set_ylabel('Length (mm)', fontsize=9)
    ax.set_xlim(-margin, xlim_r)
    ax.set_ylim(-3.0, L_show + 2.5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.12, linestyle='--')

    # 結構繪製
    ax.add_patch(Rectangle((-margin / 2, 0), total_w + margin, L_show,
                           facecolor=c_ag, edgecolor=c_ag_e, lw=2, alpha=0.25))
    ax.text(total_w / 2, L_show + 1.2, 'Top GND Layer', ha='center', va='bottom',
            fontsize=9, color=c_ag_e, fontweight='bold')

    for i in range(n_channels):
        xc = s * (i + 0.5)
        ax.add_patch(Rectangle((xc - w / 2, 0), w, L_show,
                               facecolor='none', edgecolor=c_ag, lw=2, linestyle='--', alpha=0.7))
        ax.text(xc, -0.9, f'S{i+1}', ha='center', va='top',
                fontsize=9, color='#2C3E50', fontweight='bold')
    for i in range(n_channels - 1):
        gx = s * (i + 1)
        gw = w * 0.3
        ax.add_patch(Rectangle((gx - gw / 2, 0), gw, L_show,
                               facecolor='none', edgecolor='#D4AF37', lw=1.5, linestyle=':', alpha=0.5))

    if via_enabled:
        vr = via_diameter / 2000
        vs = 1.0 / max(via_density, 0.1)
        for ix in range(int(total_w / vs) + 1):
            for iy in range(int(L_show / vs) + 1):
                xv, yv = ix * vs, iy * vs
                if xv > total_w or yv > L_show:
                    continue
                ax.add_patch(Circle((xv, yv), vr, facecolor=c_via,
                                    edgecolor='black', lw=0.8, alpha=0.8))

    # ===== 右側置中：全局參數區 =====
    right_x = total_w + margin + 0.3
    global_y_start = L_show * 0.75
    global_dy = L_show * 0.10

    # 1. 總厚度
    ax.text(right_x, global_y_start,
            f'總厚度 Total Thickness\n{total_h*1000:.0f} μm',
            ha='left', va='center', fontsize=9, color=c_dim, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDEDEC',
                      edgecolor=c_dim, alpha=0.9))

    # 2. Pitch 間距
    ax.text(right_x, global_y_start - global_dy,
            f'通道間距 Pitch\n{s:.1f} mm ({n_channels} ch)',
            ha='left', va='center', fontsize=9, color=c_arrow, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#EBF5FB',
                      edgecolor=c_arrow, alpha=0.9))

    # 3. 材質 Legend（手動繪製，置於右側）
    legend_y = global_y_start - 2 * global_dy
    legend_items = [
        (c_ag, c_ag_e, 'Ag/NbTi Conductor'),
        (c_poly, c_poly_e, 'Polyimide (εr=3.4)'),
        (c_via, 'black', 'GND Via')
    ]
    legend_box_h = len(legend_items) * 0.06 * L_show + 0.02 * L_show
    ax.add_patch(Rectangle((right_x - 0.05, legend_y - legend_box_h / 2),
                           2.8, legend_box_h,
                           facecolor='white', edgecolor='gray', lw=1, alpha=0.92))
    ax.text(right_x + 1.3, legend_y + legend_box_h / 2 + 0.02 * L_show,
            'Material Legend', ha='center', va='bottom',
            fontsize=8, color='#2C3E50', fontweight='bold')
    for i, (fc, ec, label) in enumerate(legend_items):
        ly = legend_y + (len(legend_items) / 2 - 0.5 - i) * 0.06 * L_show
        if label == 'GND Via':
            ax.add_patch(Circle((right_x + 0.2, ly), 0.025 * L_show,
                                facecolor=fc, edgecolor=ec, lw=1))
        else:
            ax.add_patch(Rectangle((right_x + 0.1, ly - 0.02 * L_show),
                                   0.2, 0.04 * L_show,
                                   facecolor=fc, edgecolor=ec, lw=1.5))
        ax.text(right_x + 0.45, ly, label, ha='left', va='center',
                fontsize=8, color='#2C3E50')

    # ===== 底部置中：w 標註（上方）=====
    center_x = total_w / 2
    ax.annotate('', xy=(center_x - w / 2, -1.4), xytext=(center_x + w / 2, -1.4),
                arrowprops=dict(arrowstyle='<->', color=c_dim, lw=2))
    ax.text(center_x, -1.65, f'w = {w*1000:.0f} μm', ha='center', va='top',
            fontsize=9, color=c_dim, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                      edgecolor=c_dim, alpha=0.9))

    # ===== 底部置中：總寬度標註（下方，與 w 垂直分開不重叠）=====
    ax.annotate('', xy=(0, -2.15), xytext=(total_w, -2.15),
                arrowprops=dict(arrowstyle='<->', color=c_dim, lw=1.8))
    ax.text(total_w / 2, -2.4,
            f'Total Width = {total_w:.1f} mm',
            ha='center', va='top', fontsize=9, color=c_dim, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#FDEDEC',
                      edgecolor=c_dim, alpha=0.9))

    # 右側長度標註
    ax.annotate('', xy=(total_w + margin * 0.3, 0),
                xytext=(total_w + margin * 0.3, L_show),
                arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=2))
    ax.text(total_w + margin * 0.3 + 0.25, L_show / 2, f'L = {L} mm',
            ha='left', va='center', fontsize=9, color=c_arrow, fontweight='bold',
            rotation=90, rotation_mode='anchor',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#EBF5FB',
                      edgecolor=c_arrow, alpha=0.9))

    tight_layout()
    return fig


# ============================================================
# XLSX 匯出功能
# ============================================================

def export_xlsx(geo: StriplineGeometry, pitch: float, length: float,
                via_enabled: bool, via_diameter: float, via_density: float,
                n_channels: int, sig_width: float, dielectric_thickness: float,
                sig_thickness: float):
    import openpyxl
    from openpyxl.drawing.image import Image as XLImage
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

    wb = openpyxl.Workbook()
    header_fill = PatternFill(start_color="1F77B4", end_color="1F77B4", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=11)
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                         top=Side(style='thin'), bottom=Side(style='thin'))

    # --- Sheet 1: 設計參數 ---
    ws1 = wb.active
    ws1.title = "設計參數"
    ws1.append(["參數名稱", "數值", "單位"])
    ws1.append(["信號線寬度 (w)", sig_width, "μm"])
    ws1.append(["信號線厚度 (t)", sig_thickness, "μm"])
    ws1.append(["介電層厚度 (h)", dielectric_thickness, "μm"])
    ws1.append(["通道間距 (pitch)", pitch, "mm"])
    ws1.append(["傳輸線長度 (L)", length, "mm"])
    ws1.append(["通道數", n_channels, "ch"])
    ws1.append(["Via 啟用", "是" if via_enabled else "否", ""])
    ws1.append(["Via 直徑", via_diameter, "μm"])
    ws1.append(["Via 密度", via_density, "個/mm"])

    # --- Sheet 2: 性能指標 ---
    ws2 = wb.create_sheet("性能指標")
    ws2.append(["指標", "數值", "單位"])
    total_w = pitch * n_channels
    total_h = 2 * geo.h + 3 * (geo.t / 1000)
    ws2.append(["總寬度", f"{total_w:.2f}", "mm"])
    ws2.append(["總厚度", f"{total_h*1000:.0f}", "μm"])
    ws2.append(["介電常數", "3.4", ""])
    ws2.append(["導體材料", "Ag/NbTi", ""])
    ws2.append(["介電材料", "Polyimide", ""])

    # --- Sheet 3: 公式推導 ---
    ws3 = wb.create_sheet("公式推導")
    ws3.append(["公式名稱", "公式內容"])
    ws3.append(["總寬度", "Total Width = pitch × n_channels"])
    ws3.append(["總厚度", "Total Height = 2h + 3t (μm)"])
    ws3.append(["特性阻抗 (近似)", "Z0 ≈ 60/√εr × ln(4h/πw)"])
    ws3.append(["延遲時間", "td = √(εr) / c"])

    # --- Sheet 4: 逐步計算 ---
    ws4 = wb.create_sheet("逐步計算")
    ws4.append(["步驟", "計算式", "結果"])
    ws4.append(["1", f"總寬度 = {pitch} × {n_channels}", f"{total_w:.2f} mm"])
    ws4.append(["2", f"總厚度 = 2×{dielectric_thickness} + 3×{sig_thickness}", f"{total_h*1000:.0f} μm"])
    ws4.append(["3", f"信號層位置 = t + h", f"{geo.t/1000 + geo.h:.4f} mm"])

    # --- Sheet 5~7: 三視圖 ---
    ws5 = wb.create_sheet("前視圖")
    ws5.append([f"前視圖 Front View (X-Z) | {n_channels}ch | w={sig_width}μm | h={dielectric_thickness}μm | t={sig_thickness}μm", ""])
    buf_f = _view_to_buffer(draw_front_view(geo, pitch, via_enabled, via_diameter, via_density, n_channels))
    img_f = XLImage(buf_f); img_f.width = 720; img_f.height = 500
    ws5.add_image(img_f, "A3")

    ws6 = wb.create_sheet("側視圖")
    ws6.append([f"側視圖 Side View (Y-Z) | L={length}mm | h={dielectric_thickness}μm | t={sig_thickness}μm", ""])
    buf_s = _view_to_buffer(draw_side_view(geo, pitch, length, via_enabled, via_diameter, via_density, n_channels))
    img_s = XLImage(buf_s); img_s.width = 720; img_s.height = 500
    ws6.add_image(img_s, "A3")

    ws7 = wb.create_sheet("上視圖")
    ws7.append([f"上視圖 Top View (X-Y) | {n_channels}ch | pitch={pitch}mm | w={sig_width}μm", ""])
    buf_t = _view_to_buffer(draw_top_view(geo, pitch, length, via_enabled, via_diameter, via_density, n_channels))
    img_t = XLImage(buf_t); img_t.width = 720; img_t.height = 500
    ws7.add_image(img_t, "A3")

    for ws in [ws5, ws6, ws7]:
        for row in ws.iter_rows():
            for cell in row:
                cell.border = thin_border
                cell.alignment = Alignment(vertical='center', wrap_text=True)
        ws.column_dimensions['A'].width = 32
        ws.column_dimensions['B'].width = 40

    for ws in [ws1, ws2, ws3, ws4]:
        for row in ws.iter_rows():
            for cell in row:
                cell.border = thin_border
                cell.alignment = Alignment(vertical='center', wrap_text=True)
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 12
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')

    xlsx_buf = BytesIO()
    wb.save(xlsx_buf)
    xlsx_buf.seek(0)
    return xlsx_buf.getvalue()


# ============================================================
# Streamlit 主程式
# ============================================================

def main():
    st.set_page_config(
        page_title="通用型三視圖繪製系統 v3.0",
        page_icon="📐",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("📐 通用型三視圖繪製系統 v3.0")
    st.markdown("*動態防重疊 · 全局參數集中 · 普適通用*")
    st.markdown("---")

    # ── 側邊欄：物理尺寸參數動態調整 ──
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
        - 佈局模式：{'寬結構' if total_w > 6 else '窄結構'} / {'長結構' if min(length, 80) > 40 else '短結構'}
        """)

    # 建立幾何參數物件
    geo = StriplineGeometry(
        w=sig_width / 1000,
        t=sig_thickness,
        h=dielectric_thickness / 1000,
        s=pitch,
        L=length,
        n_channels=n_channels
    )
    全視圖=["📐 前視圖", "📐 側視圖", "📐 上視圖", '匯出xlsx']
    視圖=st.radio('三視圖', 全視圖, horizontal=True)

    if 視圖==全視圖[0]:

    # ── 三視圖並排顯示 ──
    #col1, col2, col3 = st.columns(3)

    #with col1:
        st.subheader("🔲 前視圖 Front View (X-Z)")
        fig_front = draw_front_view(geo, pitch, via_enabled, via_diameter, via_density, n_channels)
        st.pyplot(fig_front)

    #with col2:
    elif 視圖==全視圖[1]:
        st.subheader("🔲 側視圖 Side View (Y-Z)")
        fig_side = draw_side_view(geo, pitch, length, via_enabled, via_diameter, via_density, n_channels)
        st.pyplot(fig_side)

    #with col3:
    elif 視圖==全視圖[2]:
        st.subheader("🔲 上視圖 Top View (X-Y)")
        fig_top = draw_top_view(geo, pitch, length, via_enabled, via_diameter, via_density, n_channels)
        st.pyplot(fig_top)

    # ── XLSX 匯出區域 ──
    st.markdown("---")
    st.subheader("📥 匯出 XLSX 規格檔")
    st.markdown("""
    匯出內容包含以下 **7 個獨立工作表**：
    1. **設計參數** — 所有物理尺寸與設定值
    2. **性能指標** — 總寬度、總厚度等計算結果
    3. **公式推導** — 設計相關公式說明
    4. **逐步計算** — 詳細計算步驟
    5. **前視圖** — 含 PNG 圖片
    6. **側視圖** — 含 PNG 圖片
    7. **上視圖** — 含 PNG 圖片
    """)

    if st.button("📥 產生並下載 XLSX 規格檔", type="primary", use_container_width=True):
        with st.spinner("正在產生 XLSX 檔案，請稍候..."):
            xlsx_data = export_xlsx(
                geo, pitch, length, via_enabled, via_diameter, via_density,
                n_channels, sig_width, dielectric_thickness, sig_thickness
            )
        st.download_button(
            label="⬇️ 下載 XLSX 規格檔",
            data=xlsx_data,
            file_name=f"crioflex3_spec_{length}mm_{n_channels}ch.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        st.success("✅ XLSX 檔案已產生！")

    st.markdown("---")
    st.caption("通用型三視圖繪製系統 v3.0 | 動態防重疊 · 全局參數集中 | Powered by Streamlit + Matplotlib + OpenPyXL")


if __name__ == "__main__":
    main()
