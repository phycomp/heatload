"""
通用型三視圖繪製系統 v4.0 — 簡約精確版
原則：Neat · 精確 · 簡約 · 零重疊

安裝需求：
  pip install streamlit matplotlib openpyxl

執行方式：
  streamlit run crioflex3_three_view_v4.py
"""

import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from matplotlib.pyplot import subplots, tight_layout
from dataclasses import dataclass
from io import BytesIO

# ============================================================
# 資料結構
# ============================================================

@dataclass
class StriplineGeometry:
    w: float        # 信號線寬度 (mm)
    t: float        # 信號線厚度 (μm)
    h: float        # 介電層厚度 (mm)
    s: float        # 通道間距 pitch (mm)
    L: float        # 傳輸線長度 (mm)
    n_channels: int # 通道數


# ============================================================
# 通用輔助
# ============================================================

def _view_to_buffer(fig) -> BytesIO:
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='red')
    buf.seek(0)
    plt.close(fig)
    return buf


def _layer_text(t_um: float, h_um: float) -> str:
    return (
        f'L5  Top GND      t={t_um:.0f} μm\n'
        f'L4  Polyimide     h={h_um:.0f} μm  εr=3.4\n'
        f'L3  Signal        G-S-G\n'
        f'L2  Polyimide     h={h_um:.0f} μm  εr=3.4\n'
        f'L1  Bottom GND    t={t_um:.0f} μm'
    )


# ============================================================
# 前視圖 (Front View, X-Z)
# ============================================================
# 簡約佈局：
#   · 結構繪製於中央
#   · Layer 標註置於結構右側（固定距離，不隨通道數變動）
#   · pitch 標註置於結構正下方中央
#   · 引線從各層右邊緣水平連出，再垂直匯集到文字塊

def draw_front_view(geo: StriplineGeometry, pitch: float, via_enabled: bool,
                    via_diameter: float, via_density: float, n_channels: int):
    w, h, t, s = geo.w, geo.h, geo.t / 1000, pitch
    total_w = s * n_channels
    total_h = 2 * h + 3 * t
    margin = 0.5
    y0, y1, y2, y3, y4 = 0, t, t + h, t + h + t, t + h + t + h
    t_um, h_um = t * 1000, h * 1000

    c_ag, c_ag_e = '#C9A227', '#8B6914'
    c_poly, c_poly_e = '#F5E6C8', '#D4A574'
    c_via = '#A0522D'
    c_layer, c_arrow = '#8E44AD', '#2980B9'

    fig, ax = subplots(figsize=(10, 6))
    ax.set_title(
        f'前視圖 Front View (X-Z)  {n_channels}ch  w={w*1000:.0f} μm  h={h_um:.0f} μm  t={t_um:.0f} μm',
        fontsize=12, fontweight='bold', color='#2C3E50', pad=12)
    ax.set_xlabel('Width (mm)', fontsize=10)
    ax.set_ylabel('Height (mm)', fontsize=10)
    ax.set_xlim(-margin, total_w + margin + 3.2)
    ax.set_ylim(-0.8, total_h + 0.3)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.08, linestyle='--')
    ax.set_facecolor('#FAFAFA')

    # --- 五層結構 ---
    ax.add_patch(Rectangle((0, y0), total_w, t, facecolor=c_ag, edgecolor=c_ag_e, lw=1.5))
    ax.text(total_w / 2, y0 + t / 2, 'Bottom GND', ha='center', va='center',
            fontsize=8, color='red', fontweight='bold')

    ax.add_patch(Rectangle((0, y1), total_w, h, facecolor=c_poly, edgecolor=c_poly_e, lw=1.5, alpha=0.8))

    for i in range(n_channels):
        xc = s * (i + 0.5)
        ax.add_patch(Rectangle((xc - w / 2, y2), w, t, facecolor=c_ag, edgecolor=c_ag_e, lw=1.5))
        ax.text(xc, y2 + t / 2, f'S{i+1}', ha='center', va='center',
                fontsize=8, color='red', fontweight='bold')
        if i < n_channels - 1:
            gx = xc + s / 2
            gw = w * 0.3
            ax.add_patch(Rectangle((gx - gw / 2, y2), gw, t,
                                   facecolor='#D4AF37', edgecolor=c_ag_e, lw=1.2))
            ax.text(gx, y2 + t / 2, 'G', ha='center', va='center',
                    fontsize=7, color='red', fontweight='bold')

    ax.add_patch(Rectangle((0, y3), total_w, h, facecolor=c_poly, edgecolor=c_poly_e, lw=1.5, alpha=0.8))

    ax.add_patch(Rectangle((0, y4), total_w, t, facecolor=c_ag, edgecolor=c_ag_e, lw=1.5))
    ax.text(total_w / 2, y4 + t / 2, 'Top GND', ha='center', va='center',
            fontsize=8, color='red', fontweight='bold')

    # --- Via ---
    if via_enabled:
        vr = via_diameter / 2000
        vs = 1.0 / max(via_density, 0.1)
        for i in range(int(total_w / vs) + 1):
            xv = i * vs
            if xv > total_w: break
            ax.add_patch(Circle((xv, y0 + t / 2), vr, facecolor=c_via, edgecolor='black', lw=0.8))
            ax.add_patch(Circle((xv, y4 + t / 2), vr, facecolor=c_via, edgecolor='black', lw=0.8))
            ax.plot([xv, xv], [y0 + t / 2 + vr, y4 + t / 2 - vr], color=c_via, lw=1.5)

    # --- 右側 Layer 標註（固定位置，絕不重疊）---
    label_x = total_w + 0.8
    label_y = total_h / 2
    ax.text(label_x, label_y, _layer_text(t_um, h_um),
            ha='left', va='center', fontsize=9,
            color=c_layer, fontweight='bold', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#F5EEF8',
                      edgecolor=c_layer, alpha=0.95, linewidth=1.2),
            linespacing=1.7)

    # 引線：各層右邊緣 → 垂直匯集線 → 文字塊
    right_edge = total_w + 0.05
    gather_x = label_x - 0.15
    layer_yc = [y4 + t / 2, y3 + h / 2, y2 + t / 2, y1 + h / 2, y0 + t / 2]
    for yc in layer_yc:
        ax.plot([right_edge, gather_x], [yc, yc], color=c_layer, lw=0.6, linestyle='--', alpha=0.4)
    ax.plot([gather_x, gather_x], [layer_yc[-1], layer_yc[0]], color=c_layer, lw=0.6, linestyle='--', alpha=0.4)
    ax.plot([gather_x, gather_x], [layer_yc[0], label_y + 0.22], color=c_layer, lw=0.6, linestyle='--', alpha=0.4)

    # --- 底部 pitch 標註（置中，不進入結構區）---
    ay = -0.35
    ax.annotate('', xy=(s * 0.5, ay), xytext=(s * 1.5, ay),
                arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=1.8))
    ax.text(s, ay - 0.18, f'pitch = {s:.1f} mm', ha='center', va='top',
            fontsize=10, color=c_arrow, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#EBF5FB',
                      edgecolor=c_arrow, alpha=0.9))

    # 外框
    ax.plot([0, total_w, total_w, 0, 0], [y0, y0, y4 + t, y4 + t, y0],
            'k-', lw=0.5, alpha=0.3)
    tight_layout()
    return fig


# ============================================================
# 側視圖 (Side View, Y-Z)
# ============================================================
# 簡約佈局：
#   · 結構繪製於中央
#   · 左側：總厚度雙箭頭標註
#   · 底部：長度 L 標註
#   · 右側：Layer 標註文字塊

def draw_side_view(geo: StriplineGeometry, pitch: float, length: float,
                   via_enabled: bool, via_diameter: float, via_density: float, n_channels: int):
    w, h, t, s, L = geo.w, geo.h, geo.t / 1000, pitch, length
    total_h = 2 * h + 3 * t
    L_show = min(L, 80)
    y0, y1, y2, y3, y4 = 0, t, t + h, t + h + t, t + h + t + h
    t_um, h_um = t * 1000, h * 1000

    c_ag, c_ag_e = '#C9A227', '#8B6914'
    c_poly, c_poly_e = '#F5E6C8', '#D4A574'
    c_via = '#A0522D'
    c_layer, c_dim, c_arrow = '#8E44AD', '#E74C3C', '#2980B9'

    fig, ax = subplots(figsize=(10, 6))
    ax.set_title(
        f'側視圖 Side View (Y-Z)  L={L} mm  (顯示 {L_show} mm)',
        fontsize=12, fontweight='bold', color='#2C3E50', pad=12)
    ax.set_xlabel('Length (mm)', fontsize=10)
    ax.set_ylabel('Height (mm)', fontsize=10)
    ax.set_xlim(-3.5, L_show + 4.5)
    ax.set_ylim(-1.2, total_h + 0.3)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.08, linestyle='--')
    ax.set_facecolor('#FAFAFA')

    # --- 五層結構 ---
    ax.add_patch(Rectangle((0, y0), L_show, t, facecolor=c_ag, edgecolor=c_ag_e, lw=1.5))
    ax.text(L_show / 2, y0 + t / 2, 'Bottom GND', ha='center', va='center',
            fontsize=8, color='red', fontweight='bold')

    ax.add_patch(Rectangle((0, y1), L_show, h, facecolor=c_poly, edgecolor=c_poly_e, lw=1.5, alpha=0.8))

    ax.add_patch(Rectangle((0, y2), L_show, t, facecolor=c_ag, edgecolor=c_ag_e, lw=1.5))
    ax.text(L_show / 2, y2 + t / 2, 'Signal', ha='center', va='center',
            fontsize=8, color='red', fontweight='bold')

    ax.add_patch(Rectangle((0, y3), L_show, h, facecolor=c_poly, edgecolor=c_poly_e, lw=1.5, alpha=0.8))

    ax.add_patch(Rectangle((0, y4), L_show, t, facecolor=c_ag, edgecolor=c_ag_e, lw=1.5))
    ax.text(L_show / 2, y4 + t / 2, 'Top GND', ha='center', va='center',
            fontsize=8, color='red', fontweight='bold')

    # --- Via ---
    if via_enabled:
        vs = 1.0 / max(via_density, 0.1)
        for i in range(int(L_show / vs) + 1):
            xv = i * vs
            if xv > L_show: break
            ax.plot([xv, xv], [y0, y4 + t], color=c_via, lw=2, alpha=0.5)
            ax.add_patch(Circle((xv, y0), via_diameter / 2000, facecolor=c_via, edgecolor='black', lw=0.8))
            ax.add_patch(Circle((xv, y4 + t), via_diameter / 2000, facecolor=c_via, edgecolor='black', lw=0.8))

    # --- 左側：總厚度標註 ---
    ax.annotate('', xy=(-2.2, y0), xytext=(-2.2, y4 + t),
                arrowprops=dict(arrowstyle='<->', color=c_dim, lw=1.5))
    ax.text(-2.7, total_h / 2, f'{total_h*1000:.0f} μm',
            ha='right', va='center', fontsize=10, color=c_dim, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDEDEC',
                      edgecolor=c_dim, alpha=0.9))

    # --- 底部：長度標註 ---
    ax.annotate('', xy=(0, -0.55), xytext=(L_show, -0.55),
                arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=1.8))
    label_L = f'L = {L} mm' if L <= L_show else f'L = {L} mm (顯示 {L_show} mm)'
    ax.text(L_show / 2, -0.75, label_L, ha='center', va='top',
            fontsize=10, color=c_arrow, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#EBF5FB',
                      edgecolor=c_arrow, alpha=0.9))

    # --- 右側：Layer 標註 ---
    label_x = L_show + 0.8
    label_y = total_h / 2
    ax.text(label_x, label_y, _layer_text(t_um, h_um),
            ha='left', va='center', fontsize=9,
            color=c_layer, fontweight='bold', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#F5EEF8',
                      edgecolor=c_layer, alpha=0.95, linewidth=1.2),
            linespacing=1.7)

    # 引線
    right_edge = L_show + 0.05
    gather_x = label_x - 0.15
    layer_yc = [y4 + t / 2, y3 + h / 2, y2 + t / 2, y1 + h / 2, y0 + t / 2]
    for yc in layer_yc:
        ax.plot([right_edge, gather_x], [yc, yc], color=c_layer, lw=0.6, linestyle='--', alpha=0.4)
    ax.plot([gather_x, gather_x], [layer_yc[-1], layer_yc[0]], color=c_layer, lw=0.6, linestyle='--', alpha=0.4)
    ax.plot([gather_x, gather_x], [layer_yc[0], label_y + 0.22], color=c_layer, lw=0.6, linestyle='--', alpha=0.4)

    # --- 右側：各層獨立厚度標註（精確尺寸）---
    dx = L_show + 0.35
    for yy, hh, lbl in [(y0, t, f'{t_um:.0f} μm'),
                        (y1, h, f'{h_um:.0f} μm'),
                        (y3, h, f'{h_um:.0f} μm'),
                        (y4, t, f'{t_um:.0f} μm')]:
        ax.annotate('', xy=(dx, yy), xytext=(dx, yy + hh),
                    arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=1))
        ax.text(dx + 0.12, yy + hh / 2, lbl, ha='left', va='center',
                fontsize=8, color=c_arrow)

    tight_layout()
    return fig


# ============================================================
# 上視圖 (Top View, X-Y)
# ============================================================
# 簡約佈局：
#   · 結構繪製於中央
#   · 底部：w 標註（上）+ Total Width 標註（下），垂直分開
#   · 右側：總寬度文字 + 材質 Legend（簡單列表，不進入結構區）
#   · 右側：長度 L 標註

def draw_top_view(geo: StriplineGeometry, pitch: float, length: float,
                  via_enabled: bool, via_diameter: float, via_density: float, n_channels: int):
    w, h, t, s, L = geo.w, geo.h, geo.t / 1000, pitch, length
    total_w = s * n_channels
    total_h = 2 * h + 3 * t
    L_show = min(L, 80)
    margin = 0.5
    t_um = t * 1000

    c_ag, c_ag_e = '#C9A227', '#8B6914'
    c_poly, c_poly_e = '#F5E6C8', '#D4A574'
    c_via, c_dim, c_arrow = '#A0522D', '#E74C3C', '#2980B9'

    fig, ax = subplots(figsize=(10, 6))
    ax.set_title(
        f'上視圖 Top View (X-Y)  {n_channels}ch  pitch={s:.1f} mm  w={w*1000:.0f} μm',
        fontsize=12, fontweight='bold', color='#2C3E50', pad=12)
    ax.set_xlabel('Width (mm)', fontsize=10)
    ax.set_ylabel('Length (mm)', fontsize=10)
    ax.set_xlim(-margin, total_w + margin + 3.5)
    ax.set_ylim(-2.8, L_show + 2.0)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.08, linestyle='--')
    ax.set_facecolor('#FAFAFA')

    # --- 結構 ---
    ax.add_patch(Rectangle((0, 0), total_w, L_show,
                           facecolor=c_ag, edgecolor=c_ag_e, lw=1.5, alpha=0.2))
    ax.text(total_w / 2, L_show + 0.8, 'Top GND', ha='center', va='bottom',
            fontsize=9, color=c_ag_e, fontweight='bold')

    for i in range(n_channels):
        xc = s * (i + 0.5)
        ax.add_patch(Rectangle((xc - w / 2, 0), w, L_show,
                               facecolor='none', edgecolor=c_ag, lw=1.5, linestyle='--', alpha=0.6))
        ax.text(xc, -0.6, f'S{i+1}', ha='center', va='top',
                fontsize=9, color='#2C3E50', fontweight='bold')
    for i in range(n_channels - 1):
        gx = s * (i + 1)
        gw = w * 0.3
        ax.add_patch(Rectangle((gx - gw / 2, 0), gw, L_show,
                               facecolor='none', edgecolor='#D4AF37', lw=1.2, linestyle=':', alpha=0.4))

    if via_enabled:
        vr = via_diameter / 2000
        vs = 1.0 / max(via_density, 0.1)
        for ix in range(int(total_w / vs) + 1):
            for iy in range(int(L_show / vs) + 1):
                xv, yv = ix * vs, iy * vs
                if xv > total_w or yv > L_show: continue
                ax.add_patch(Circle((xv, yv), vr, facecolor=c_via,
                                    edgecolor='black', lw=0.6, alpha=0.7))

    # --- 底部：w 標註（上方，不進結構區）---
    cx = total_w / 2
    ax.annotate('', xy=(cx - w / 2, -1.3), xytext=(cx + w / 2, -1.3),
                arrowprops=dict(arrowstyle='<->', color=c_dim, lw=1.8))
    ax.text(cx, -1.55, f'w = {w*1000:.0f} μm', ha='center', va='top',
            fontsize=10, color=c_dim, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='red',
                      edgecolor=c_dim, alpha=0.9))

    # --- 底部：Total Width 標註（下方，與 w 垂直分開）---
    ax.annotate('', xy=(0, -2.05), xytext=(total_w, -2.05),
                arrowprops=dict(arrowstyle='<->', color=c_dim, lw=1.5))
    ax.text(total_w / 2, -2.3, f'Total Width = {total_w:.1f} mm',
            ha='center', va='top', fontsize=10, color=c_dim, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#FDEDEC',
                      edgecolor=c_dim, alpha=0.9))

    # --- 右側：總寬度文字（簡潔）---
    rx = total_w + margin + 0.3
    ax.text(rx, L_show * 0.82,
            f'總寬度  {total_w:.1f} mm\n總厚度  {total_h*1000:.0f} μm\n通道數  {n_channels} ch',
            ha='left', va='center', fontsize=9, color='#2C3E50', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='#F8F9F9',
                      edgecolor='#BDC3C7', alpha=0.95, linewidth=1),
            linespacing=1.6)

    # --- 右側：Legend（簡單列表，不進結構區）---
    legend_items = [
        (c_ag, c_ag_e, 'Ag/NbTi Conductor'),
        (c_poly, c_poly_e, 'Polyimide (εr=3.4)'),
        (c_via, 'black', 'GND Via')
    ]
    ly = L_show * 0.58
    ax.text(rx + 0.8, ly + 0.06 * L_show, 'Legend', ha='center', va='bottom',
            fontsize=9, color='#2C3E50', fontweight='bold')
    for i, (fc, ec, label) in enumerate(legend_items):
        y_item = ly + (1 - i) * 0.055 * L_show
        if label == 'GND Via':
            ax.add_patch(Circle((rx + 0.15, y_item), 0.02 * L_show,
                                facecolor=fc, edgecolor=ec, lw=0.8))
        else:
            ax.add_patch(Rectangle((rx + 0.05, y_item - 0.015 * L_show),
                                   0.2, 0.03 * L_show,
                                   facecolor=fc, edgecolor=ec, lw=1.2))
        ax.text(rx + 0.35, y_item, label, ha='left', va='center',
                fontsize=8, color='#2C3E50')

    # --- 右側：長度 L 標註 ---
    ax.annotate('', xy=(total_w + margin * 0.2, 0),
                xytext=(total_w + margin * 0.2, L_show),
                arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=1.8))
    ax.text(total_w + margin * 0.2 + 0.2, L_show / 2, f'L = {L} mm',
            ha='left', va='center', fontsize=10, color=c_arrow, fontweight='bold',
            rotation=90, rotation_mode='anchor',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#EBF5FB',
                      edgecolor=c_arrow, alpha=0.9))

    tight_layout()
    return fig


# ============================================================
# XLSX 匯出
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

    # Sheet 1: 設計參數
    ws1 = wb.active
    ws1.title = "設計參數"
    ws1.append(["參數", "數值", "單位"])
    for k, v, u in [
        ("信號線寬度 w", sig_width, "μm"),
        ("信號線厚度 t", sig_thickness, "μm"),
        ("介電層厚度 h", dielectric_thickness, "μm"),
        ("通道間距 pitch", pitch, "mm"),
        ("傳輸線長度 L", length, "mm"),
        ("通道數", n_channels, "ch"),
        ("Via 啟用", "是" if via_enabled else "否", ""),
        ("Via 直徑", via_diameter, "μm"),
        ("Via 密度", via_density, "個/mm"),
    ]:
        ws1.append([k, v, u])

    # Sheet 2: 性能指標
    ws2 = wb.create_sheet("性能指標")
    ws2.append(["指標", "數值", "單位"])
    total_w = pitch * n_channels
    total_h = 2 * geo.h + 3 * (geo.t / 1000)
    ws2.append(["總寬度", f"{total_w:.2f}", "mm"])
    ws2.append(["總厚度", f"{total_h*1000:.0f}", "μm"])
    ws2.append(["介電常數", "3.4", ""])
    ws2.append(["導體", "Ag/NbTi", ""])
    ws2.append(["介電質", "Polyimide", ""])

    # Sheet 3: 三視圖
    for name, draw_fn, extra in [
        ("前視圖", draw_front_view, ()),
        ("側視圖", draw_side_view, (length,)),
        ("上視圖", draw_top_view, (length,)),
    ]:
        ws = wb.create_sheet(name)
        ws.append([f"{name} | {n_channels}ch | w={sig_width}μm | h={dielectric_thickness}μm | t={sig_thickness}μm", ""])
        if name == "前視圖":
            buf = _view_to_buffer(draw_fn(geo, pitch, via_enabled, via_diameter, via_density, n_channels))
        else:
            buf = _view_to_buffer(draw_fn(geo, pitch, *extra, via_enabled, via_diameter, via_density, n_channels))
        img = XLImage(buf)
        img.width = 720
        img.height = 480
        ws.add_image(img, "A3")
        for row in ws.iter_rows():
            for cell in row:
                cell.border = thin_border
                cell.alignment = Alignment(vertical='center', wrap_text=True)
        ws.column_dimensions['A'].width = 32
        ws.column_dimensions['B'].width = 40

    for ws in [ws1, ws2]:
        for row in ws.iter_rows():
            for cell in row:
                cell.border = thin_border
                cell.alignment = Alignment(vertical='center', wrap_text=True)
        ws.column_dimensions['A'].width = 18
        ws.column_dimensions['B'].width = 14
        ws.column_dimensions['C'].width = 10
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
        page_title="通用型三視圖 v4.0",
        page_icon="📐",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("📐 通用型三視圖繪製系統 v4.0")
    st.caption("Neat · 精確 · 簡約 · 零重疊")
    st.markdown("---")

    with st.sidebar:
        st.header("⚙️ 物理參數")
        sig_width = st.slider("信號線寬度 w (μm)", 50, 500, 200, step=10)
        sig_thickness = st.slider("信號線厚度 t (μm)", 1, 20, 5, step=1)
        dielectric_thickness = st.slider("介電層厚度 h (μm)", 10, 200, 50, step=5)
        pitch = st.slider("通道間距 pitch (mm)", 0.5, 5.0, 1.5, step=0.1)
        length = st.slider("傳輸線長度 L (mm)", 10, 200, 50, step=5)
        n_channels = st.slider("通道數", 2, 16, 8, step=2)

        st.divider()
        st.header("🔩 Via")
        via_enabled = st.toggle("啟用 Via", value=True)
        via_diameter = st.slider("直徑 (μm)", 50, 500, 200, step=10, disabled=not via_enabled)
        via_density = st.slider("密度 (個/mm)", 0.5, 5.0, 2.0, step=0.1, disabled=not via_enabled)

    geo = StriplineGeometry(
        w=sig_width / 1000,
        t=sig_thickness,
        h=dielectric_thickness / 1000,
        s=pitch,
        L=length,
        n_channels=n_channels
    )

    c1, c2, c3 = st.tabs(['前視圖', '側視圖', '上視圖'])
    with c1:
        st.subheader("前視圖 Front View")
        st.pyplot(draw_front_view(geo, pitch, via_enabled, via_diameter, via_density, n_channels))
    with c2:
        st.subheader("側視圖 Side View")
        st.pyplot(draw_side_view(geo, pitch, length, via_enabled, via_diameter, via_density, n_channels))
    with c3:
        st.subheader("上視圖 Top View")
        st.pyplot(draw_top_view(geo, pitch, length, via_enabled, via_diameter, via_density, n_channels))

    st.divider()
    st.subheader("📥 匯出 XLSX")
    if st.button("產生並下載規格檔", type="primary", use_container_width=True):
        with st.spinner("產生中..."):
            data = export_xlsx(geo, pitch, length, via_enabled, via_diameter, via_density,
                               n_channels, sig_width, dielectric_thickness, sig_thickness)
        st.download_button(
            label="⬇️ 下載 XLSX",
            data=data,
            file_name=f"spec_{length}mm_{n_channels}ch.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    st.caption("v4.0 | Streamlit + Matplotlib + OpenPyXL")


if __name__ == "__main__":
    main()
