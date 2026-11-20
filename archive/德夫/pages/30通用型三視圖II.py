from streamlit import button, caption, columns, download_button, header, info, markdown, pyplot, set_page_config, sidebar, slider, spinner, subheader, success, title, toggle, radio
from matplotlib.pyplot import close
"""
通用型三視圖繪製系統 v2.1 — Streamlit 互動版（標註佈局修正版）
功能：
  1. 側邊欄動態調整物理尺寸參數
  2. 文字標註防重疊設計（依用戶指定位置）
  3. 一鍵匯出 XLSX（含設計參數、三視圖獨立工作表）

安裝需求：
  pip install streamlit matplotlib openpyxl

執行方式：
  streamlit run crioflex3_three_view_v2.py
"""

import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from matplotlib.pyplot import subplots, tight_layout
from dataclasses import dataclass
from io import BytesIO
from typing import List, Dict

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
# 通用輔助：將單一視圖轉為 PNG BytesIO
# ============================================================

def _view_to_buffer(fig) -> BytesIO:
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)
    return buf


# ============================================================
# 前視圖 (Front View)
# ============================================================
# 修正：Layer 標註 + pitch 尺寸標註 → 同時放置於下方置中，不可重疊

def draw_front_view(geo: StriplineGeometry, pitch: float, via_enabled: bool,
                    via_diameter: float, via_density: float, n_channels: int):
    w, h, t, s = geo.w, geo.h, geo.t / 1000, pitch
    total_w = s * n_channels
    total_h = 2 * h + 3 * t
    margin = max(s * 0.35, 0.3)
    y0, y1, y2, y3, y4 = 0, t, t + h, t + h + t, t + h + t + h

    c_ag, c_ag_e = '#C9A227', '#8B6914'
    c_poly, c_poly_e = '#F5E6C8', '#D4A574'
    c_via, c_dim, c_arrow, c_layer = '#A0522D', '#E74C3C', '#2980B9', '#8E44AD'

    fig, ax = subplots(figsize=(10, 7))
    ax.set_title(
        f'前視圖 Front View (X-Z)  {n_channels}ch  w={w*1000:.0f}μm  h={h*1000:.0f}μm  t={t*1000:.0f}μm',
        fontsize=11, fontweight='bold', color='#2C3E50')
    ax.set_xlabel('Width (mm)', fontsize=9)
    ax.set_ylabel('Height (mm)', fontsize=9)
    ax.set_xlim(-margin, total_w + margin + 1.0)
    ax.set_ylim(-1.6, total_h + 0.25)
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

    # ===== 下方置中：Layer 標註文字塊 =====
    layer_text = (
        f'L5  Top GND      t={t*1000:.0f}μm\n'
        f'L4  Polyimide     h={h*1000:.0f}μm  εr=3.4\n'
        f'L3  Signal        G-S-G\n'
        f'L2  Polyimide     h={h*1000:.0f}μm  εr=3.4\n'
        f'L1  Bottom GND    t={t*1000:.0f}μm'
    )
    # 放在底部中央偏右
    label_x = total_w / 2 + 1.2
    label_y = -0.55
    ax.text(label_x, label_y, layer_text, ha='left', va='center', fontsize=8,
            color=c_layer, fontweight='bold', family='monospace',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='#F5EEF8',
                      edgecolor=c_layer, alpha=0.95, linewidth=1.5),
            linespacing=1.6)

    # 引線：從各層右邊緣 → 匯集 → 連到文字塊上方
    right_edge = total_w + margin / 2
    layer_y_centers = [y4 + t / 2, y3 + h / 2, y2 + t / 2, y1 + h / 2, y0 + t / 2]
    gather_x = label_x - 0.08
    for i, yc in enumerate(layer_y_centers):
        # 水平引線到匯集線
        ax.plot([right_edge, gather_x], [yc, yc],
                color=c_layer, lw=0.7, linestyle='--', alpha=0.5)
    # 垂直匯集線
    ax.plot([gather_x, gather_x],
            [layer_y_centers[-1], layer_y_centers[0]],
            color=c_layer, lw=0.7, linestyle='--', alpha=0.5)
    # 連到文字塊
    ax.plot([gather_x, gather_x], [layer_y_centers[0], label_y + 0.18],
            color=c_layer, lw=0.7, linestyle='--', alpha=0.5)

    # ===== 下方置中：pitch 尺寸標註（與 Layer 標註分開不重叠）=====
    pitch_x = total_w / 2 - 1.2
    ay = -0.55
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
# 側視圖 (Side View)
# ============================================================
# 修正：Layer 標註 + 總厚度標註 → 同時放置於下方置中，不可重疊

def draw_side_view(geo: StriplineGeometry, pitch: float, length: float,
                   via_enabled: bool, via_diameter: float, via_density: float, n_channels: int):
    w, h, t, s, L = geo.w, geo.h, geo.t / 1000, pitch, length
    total_h = 2 * h + 3 * t
    L_show = min(L, 80)
    margin = max(s * 0.35, 0.3)
    y0, y1, y2, y3, y4 = 0, t, t + h, t + h + t, t + h + t + h

    c_ag, c_ag_e = '#C9A227', '#8B6914'
    c_poly, c_poly_e = '#F5E6C8', '#D4A574'
    c_via, c_dim, c_arrow, c_layer = '#A0522D', '#E74C3C', '#2980B9', '#8E44AD'

    fig, ax = subplots(figsize=(10, 7))
    ax.set_title(
        f'側視圖 Side View (Y-Z)  L={L}mm  (顯示 {L_show}mm)',
        fontsize=11, fontweight='bold', color='#2C3E50')
    ax.set_xlabel('Length (mm)', fontsize=9)
    ax.set_ylabel('Height (mm)', fontsize=9)
    ax.set_xlim(-3, L_show + 4.5)
    ax.set_ylim(-1.6, total_h + 0.25)
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

    # ===== 下方置中：總厚度標註 =====
    thick_x = L_show / 2
    ax.annotate('', xy=(thick_x - 0.6, -0.35), xytext=(thick_x + 0.6, -0.35),
                arrowprops=dict(arrowstyle='<->', color=c_dim, lw=1.8))
    ax.text(thick_x, -0.55, f'Total Thickness = {total_h*1000:.0f} μm',
            ha='center', va='top', fontsize=9, color=c_dim, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDEDEC',
                      edgecolor=c_dim, alpha=0.9))

    # ===== 下方置中：Layer 標註文字塊（與總厚度分開不重叠）=====
    layer_text = (
        f'L5  Top GND      t={t*1000:.0f}μm\n'
        f'L4  Polyimide     h={h*1000:.0f}μm\n'
        f'L3  Signal        G-S-G\n'
        f'L2  Polyimide     h={h*1000:.0f}μm\n'
        f'L1  Bottom GND    t={t*1000:.0f}μm'
    )
    label_x = L_show / 2 + 2.2
    label_y = -0.55
    ax.text(label_x, label_y, layer_text, ha='left', va='center', fontsize=8,
            color=c_layer, fontweight='bold', family='monospace',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='#F5EEF8',
                      edgecolor=c_layer, alpha=0.95, linewidth=1.5),
            linespacing=1.6)

    # 引線：從各層右邊緣 → 匯集 → 連到文字塊上方
    right_edge = L_show + 0.05
    layer_y = [y4 + t / 2, y3 + h / 2, y2 + t / 2, y1 + h / 2, y0 + t / 2]
    gather_x = label_x - 0.08
    for i, yc in enumerate(layer_y):
        ax.plot([right_edge, gather_x], [yc, yc],
                color=c_layer, lw=0.7, linestyle='--', alpha=0.5)
    ax.plot([gather_x, gather_x],
            [layer_y[-1], layer_y[0]],
            color=c_layer, lw=0.7, linestyle='--', alpha=0.5)
    ax.plot([gather_x, gather_x], [layer_y[0], label_y + 0.18],
            color=c_layer, lw=0.7, linestyle='--', alpha=0.5)

    # 底部長度標註（保持不變，在底部）
    ax.annotate('', xy=(0, -1.15), xytext=(L_show, -1.15),
                arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=2))
    label_L = f'L = {L} mm' if L <= L_show else f'L = {L} mm (顯示 {L_show} mm)'
    ax.text(L_show / 2, -1.35, label_L, ha='center', va='top',
            fontsize=9, color=c_arrow, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#EBF5FB',
                      edgecolor=c_arrow, alpha=0.9))

    # 右側各層厚度標註（保持不變）
    dx = L_show + 0.4
    for yy, hh, lbl in [(y0, t, f't={t*1000:.0f}μm'),
                        (y1, h, f'h={h*1000:.0f}μm'),
                        (y3, h, f'h={h*1000:.0f}μm'),
                        (y4, t, f't={t*1000:.0f}μm')]:
        ax.annotate('', xy=(dx, yy), xytext=(dx, yy + hh),
                    arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=1.2))
        ax.text(dx + 0.15, yy + hh / 2, lbl, ha='left', va='center',
                fontsize=7, color=c_arrow)

    tight_layout()
    return fig


# ============================================================
# 上視圖 (Top View)
# ============================================================
# 修正：
#   a. Total Width + 材質 Legend → 右側置中
#   b. 底部 w + pitch 標註 → 下圖置中處，不可重疊

def draw_top_view(geo: StriplineGeometry, pitch: float, length: float,
                  via_enabled: bool, via_diameter: float, via_density: float, n_channels: int):
    w, h, t, s, L = geo.w, geo.h, geo.t / 1000, pitch, length
    total_w = s * n_channels
    L_show = min(L, 80)
    margin = max(s * 0.35, 0.3)

    c_ag, c_ag_e = '#C9A227', '#8B6914'
    c_poly, c_poly_e = '#F5E6C8', '#D4A574'
    c_via, c_dim, c_arrow = '#A0522D', '#E74C3C', '#2980B9'

    fig, ax = subplots(figsize=(10, 7))
    ax.set_title(
        f'上視圖 Top View (X-Y)  {n_channels}ch  pitch={s:.1f}mm  w={w*1000:.0f}μm',
        fontsize=11, fontweight='bold', color='#2C3E50')
    ax.set_xlabel('Width (mm)', fontsize=9)
    ax.set_ylabel('Length (mm)', fontsize=9)
    ax.set_xlim(-margin, total_w + margin + 3.5)
    ax.set_ylim(-3.2, L_show + 2.5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.12, linestyle='--')

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

    # ===== 右側置中：Total Width 標註 =====
    right_x = total_w + margin + 0.4
    ax.text(right_x, L_show * 0.72,
            f'Total Width = {total_w:.1f} mm\n({n_channels} channels)',
            ha='left', va='center', fontsize=9, color=c_dim, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDEDEC',
                      edgecolor=c_dim, alpha=0.9))

    # ===== 右側置中：材質 Legend（手動繪製避免重疊）=====
    legend_items = [
        (c_ag, c_ag_e, 'Ag/NbTi Conductor'),
        (c_poly, c_poly_e, 'Polyimide (εr=3.4)'),
        (c_via, 'black', 'GND Via')
    ]
    legend_y_start = L_show * 0.52
    legend_dy = L_show * 0.09
    for i, (fc, ec, label) in enumerate(legend_items):
        ly = legend_y_start - i * legend_dy
        if label == 'GND Via':
            ax.add_patch(Circle((right_x + 0.15, ly), 0.025 * L_show,
                                facecolor=fc, edgecolor=ec, lw=1))
        else:
            ax.add_patch(Rectangle((right_x + 0.05, ly - 0.02 * L_show),
                                   0.2, 0.04 * L_show,
                                   facecolor=fc, edgecolor=ec, lw=1.5))
        ax.text(right_x + 0.35, ly, label, ha='left', va='center',
                fontsize=8, color='#2C3E50', fontweight='bold')

    # ===== 下圖置中：w 標註（上方）=====
    center_x = total_w / 2
    ax.annotate('', xy=(center_x - w / 2, -1.6), xytext=(center_x + w / 2, -1.6),
                arrowprops=dict(arrowstyle='<->', color=c_dim, lw=2))
    ax.text(center_x, -1.85, f'w = {w*1000:.0f} μm', ha='center', va='top',
            fontsize=9, color=c_dim, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                      edgecolor=c_dim, alpha=0.9))

    # ===== 下圖置中：pitch 標註（下方，與 w 分開不重叠）=====
    ax.annotate('', xy=(center_x - s / 2, -2.35), xytext=(center_x + s / 2, -2.35),
                arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=2))
    ax.text(center_x, -2.6, f'pitch = {s:.1f} mm', ha='center', va='top',
            fontsize=9, color=c_arrow, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                      edgecolor=c_arrow, alpha=0.9))

    # 右側長度標註（保持不變）
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

    # --- Sheet 5: 前視圖 ---
    ws5 = wb.create_sheet("前視圖")
    ws5.append([f"前視圖 Front View (X-Z) | {n_channels}ch | w={sig_width}μm | h={dielectric_thickness}μm | t={sig_thickness}μm", ""])
    buf_f = _view_to_buffer(draw_front_view(geo, pitch, via_enabled, via_diameter, via_density, n_channels))
    img_f = XLImage(buf_f)
    img_f.width = 720
    img_f.height = 500
    ws5.add_image(img_f, "A3")

    # --- Sheet 6: 側視圖 ---
    ws6 = wb.create_sheet("側視圖")
    ws6.append([f"側視圖 Side View (Y-Z) | L={length}mm | h={dielectric_thickness}μm | t={sig_thickness}μm", ""])
    buf_s = _view_to_buffer(draw_side_view(geo, pitch, length, via_enabled, via_diameter, via_density, n_channels))
    img_s = XLImage(buf_s)
    img_s.width = 720
    img_s.height = 500
    ws6.add_image(img_s, "A3")

    # --- Sheet 7: 上視圖 ---
    ws7 = wb.create_sheet("上視圖")
    ws7.append([f"上視圖 Top View (X-Y) | {n_channels}ch | pitch={pitch}mm | w={sig_width}μm", ""])
    buf_t = _view_to_buffer(draw_top_view(geo, pitch, length, via_enabled, via_diameter, via_density, n_channels))
    img_t = XLImage(buf_t)
    img_t.width = 720
    img_t.height = 500
    ws7.add_image(img_t, "A3")

    # 三視圖工作表樣式
    for ws in [ws5, ws6, ws7]:
        for row in ws.iter_rows():
            for cell in row:
                cell.border = thin_border
                cell.alignment = Alignment(vertical='center', wrap_text=True)
        ws.column_dimensions['A'].width = 32
        ws.column_dimensions['B'].width = 40

    # 參數工作表樣式
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
        page_title="通用型三視圖繪製系統 v2.1",
        page_icon="📐",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("📐 通用型三視圖繪製系統 v2.1")
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
        n_channels = st.slider("通道數", 1, 16, 4, step=1)

        st.markdown("---")
        st.header("🔩 Via 設定")
        via_enabled = st.toggle("啟用 Via", value=True)
        via_diameter = st.slider("Via 直徑 (μm)", 50, 500, 200, step=10,
                                  disabled=not via_enabled)
        via_density = st.slider("Via 密度 (個/mm)", 0.5, 5.0, 2.0, step=0.1,
                                 disabled=not via_enabled)

        st.markdown("---")
        st.info(f"""
        **即時預覽參數：**
        - 總寬度：{pitch * n_channels:.1f} mm
        - 總厚度：{2 * dielectric_thickness + 3 * sig_thickness:.0f} μm
        - 長寬比：{length / (pitch * n_channels):.2f}
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

    # ── 三視圖並排顯示 ──
    #col1, col2, col3 = st.columns(3)
    全視圖=["📐 前視圖", "📐 側視圖", "📐 上視圖", '匯出xlsx']
    視圖=radio('三視圖', 全視圖, horizontal=True)

    if 視圖==全視圖[0]:

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

    else:
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
      st.caption("通用型三視圖繪製系統 v2.1 | Powered by Streamlit + Matplotlib + OpenPyXL")


if __name__ == "__main__":
    main()
