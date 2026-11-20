# ============================================================
# 通用型三視圖繪製系統 v2.0
# 功能：
#   1. 動態適應物理尺寸參數
#   2. 文字標註防重叠設計
#   3. 支援 XLSX 獨立工作表匯出
# ============================================================

from matplotlib.pyplot import Circle, Polygon, Rectangle, subplots, tight_layout
from dataclasses import dataclass
from io import BytesIO

@dataclass
class StriplineGeometry:
    """Stripline 幾何參數"""
    w: float        # 信號線寬度 (mm)
    t: float        # 信號線厚度 (μm)
    h: float        # 介電層厚度 (mm) 上下各一層
    s: float        # 通道間距 pitch (mm)
    L: float        # 傳輸線長度 (mm)
    n_channels: int # 通道數

@dataclass
class ThermalBoundary:
    """熱邊界條件"""
    T_hot: float    # 熱端溫度 (K)
    T_cold: float   # 冷端溫度 (K)
    stage: str      # 溫度階段標識

@dataclass
class MaterialStack:
    """多層膜結構"""
    layers: List[Dict]  # [{"material": str, "thickness": float, "width": float}]


# ── 通用輔助：將單一視圖轉為 PNG BytesIO ─────────────────────
def _view_to_buffer(fig) -> BytesIO:
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)
    return buf


# ── 前視圖 (Front View) ─────────────────────────────────────
def 前視圖(geo: StriplineGeometry, pitch: float, via_enabled: bool, via_diameter: float, via_density: float, n_channels: int): #draw_front_view
    w, h, t, s = geo.w, geo.h, geo.t/1000, pitch
    #n_draw = min(n_channels, 6)
    total_w = s * n_channels
    total_h = 2*h + 3*t
    margin = max(s*0.35, 0.3)
    y0, y1, y2, y3, y4 = 0, t, t+h, t+h+t, t+h+t+h

    c_ag, c_ag_e = '#C9A227', '#8B6914'
    c_poly, c_poly_e = '#F5E6C8', '#D4A574'
    c_via, c_dim, c_arrow, c_layer = '#A0522D', '#E74C3C', '#2980B9', '#8E44AD'

    fig, ax = subplots(figsize=(10, 7))
    ax.set_title(f'前視圖 Front View (X-Z)  {n_channels}ch  w={w*1000:.0f}μm  h={h*1000:.0f}μm  t={t*1000:.0f}μm',
                 fontsize=11, fontweight='bold', color='#2C3E50')
    ax.set_xlabel('Width (mm)', fontsize=9)
    ax.set_ylabel('Height (mm)', fontsize=9)
    ax.set_xlim(-margin, total_w + margin + 3.0)
    ax.set_ylim(-0.10, total_h + 0.18)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.12, linestyle='--')

    # 五層結構
    ax.add_patch(Rectangle((-margin/2, y0), total_w+margin, t, facecolor=c_ag, edgecolor=c_ag_e, lw=2))
    ax.text(total_w/2, y0+t/2, 'Bottom GND', ha='center', va='center', fontsize=8, color='white', fontweight='bold')

    ax.add_patch(Rectangle((-margin/2, y1), total_w+margin, h, facecolor=c_poly, edgecolor=c_poly_e, lw=2, alpha=0.85))

    for i in range(n_channels):
        xc = s*(i+0.5)
        ax.add_patch(Rectangle((xc-w/2, y2), w, t, facecolor=c_ag, edgecolor=c_ag_e, lw=2))
        ax.text(xc, y2+t/2, f'S{i+1}', ha='center', va='center', fontsize=8, color='white', fontweight='bold')
        if i < n_channels-1:
            gx = xc+s/2; gw = w*0.3
            ax.add_patch(Rectangle((gx-gw/2, y2), gw, t, facecolor='#D4AF37', edgecolor=c_ag_e, lw=1.5))
            ax.text(gx, y2+t/2, 'G', ha='center', va='center', fontsize=7, color='white', fontweight='bold')

    ax.add_patch(Rectangle((-margin/2, y3), total_w+margin, h, facecolor=c_poly, edgecolor=c_poly_e, lw=2, alpha=0.85))

    ax.add_patch(Rectangle((-margin/2, y4), total_w+margin, t, facecolor=c_ag, edgecolor=c_ag_e, lw=2))
    ax.text(total_w/2, y4+t/2, 'Top GND', ha='center', va='center', fontsize=8, color='white', fontweight='bold')

    # Via
    if via_enabled:
        vr = via_diameter/2000; vs = 1.0/max(via_density, 0.1)
        for i in range(int(total_w/vs)+1):
            xv = i*vs
            if xv > total_w: break
            ax.add_patch(Circle((xv, y0+t/2), vr, facecolor=c_via, edgecolor='black', lw=1))
            ax.add_patch(Circle((xv, y4+t/2), vr, facecolor=c_via, edgecolor='black', lw=1))
            ax.plot([xv, xv], [y0+t/2+vr, y4+t/2-vr], color=c_via, lw=1.8)

    # 右側 Layer 標註：合併為單一垂直文字塊，置於結構右側
    layer_text = (
        f'L5  Top GND      t={t*1000:.0f}μm\n'
        f'L4  Polyimide     h={h*1000:.0f}μm  εr=3.4\n'
        f'L3  Signal        G-S-G\n'
        f'L2  Polyimide     h={h*1000:.0f}μm  εr=3.4\n'
        f'L1  Bottom GND    t={t*1000:.0f}μm'
    )
    label_x = total_w + margin*0.5
    ax.text(label_x, total_h/2, layer_text, ha='left', va='center', fontsize=8,
            color=c_layer, fontweight='bold', family='monospace',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='#F5EEF8', edgecolor=c_layer, alpha=0.95, linewidth=1.5),
            linespacing=1.6)

    # 引線：從各層右邊緣連到文字塊
    right_edge = total_w + margin/2
    layer_y_centers = [y4+t/2, y3+h/2, y2+t/2, y1+h/2, y0+t/2]
    text_top = total_h/2 + 2*0.016
    step = 0.016
    for i, yc in enumerate(layer_y_centers):
        ty = text_top - i*step
        ax.plot([right_edge, label_x-0.06], [yc, ty], color=c_layer, lw=0.7, linestyle='--', alpha=0.5)

    # 底部 pitch 標註（唯一尺寸標註）
    ay = y0 - 0.04
    ax.annotate('', xy=(s*0.5, ay), xytext=(s*1.5, ay), arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=2))
    ax.text(s, ay-0.025, f'pitch = {s:.1f} mm', ha='center', va='top', fontsize=9, color=c_arrow, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#EBF5FB', edgecolor=c_arrow, alpha=0.9))

    ax.plot([-margin/2, total_w+margin/2, total_w+margin/2, -margin/2, -margin/2],
            [y0, y0, y4+t, y4+t, y0], 'k-', lw=0.6, alpha=0.35)
    tight_layout()
    return fig


# ── 側視圖 (Side View) ──────────────────────────────────────
def 側視圖(geo: StriplineGeometry, pitch: float, length: float, via_enabled: bool, via_diameter: float, via_density: float, n_channels: int): #draw_side_view
    w, h, t, s, L = geo.w, geo.h, geo.t/1000, pitch, length
    #n_draw = min(n_channels, 6)
    total_h = 2*h + 3*t
    L_show = min(L, 80)
    margin = max(s*0.35, 0.3)
    y0, y1, y2, y3, y4 = 0, t, t+h, t+h+t, t+h+t+h

    c_ag, c_ag_e = '#C9A227', '#8B6914'
    c_poly, c_poly_e = '#F5E6C8', '#D4A574'
    c_via, c_dim, c_arrow, c_layer = '#A0522D', '#E74C3C', '#2980B9', '#8E44AD'

    fig, ax = subplots(figsize=(10, 7))
    ax.set_title(f'側視圖 Side View (Y-Z)  L={L}mm  (顯示 {L_show}mm)',
                 fontsize=11, fontweight='bold', color='#2C3E50')
    ax.set_xlabel('Length (mm)', fontsize=9)
    ax.set_ylabel('Height (mm)', fontsize=9)
    ax.set_xlim(-3, L_show + 5.0)
    ax.set_ylim(-0.10, total_h + 0.18)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.12, linestyle='--')

    ax.add_patch(Rectangle((0, y0), L_show, t, facecolor=c_ag, edgecolor=c_ag_e, lw=2))
    ax.text(L_show/2, y0+t/2, 'Bottom GND', ha='center', va='center', fontsize=8, color='white', fontweight='bold')

    ax.add_patch(Rectangle((0, y1), L_show, h, facecolor=c_poly, edgecolor=c_poly_e, lw=2, alpha=0.85))

    ax.add_patch(Rectangle((0, y2), L_show, t, facecolor=c_ag, edgecolor=c_ag_e, lw=2))
    ax.text(L_show/2, y2+t/2, 'Signal Layer', ha='center', va='center', fontsize=8, color='white', fontweight='bold')

    ax.add_patch(Rectangle((0, y3), L_show, h, facecolor=c_poly, edgecolor=c_poly_e, lw=2, alpha=0.85))

    ax.add_patch(Rectangle((0, y4), L_show, t, facecolor=c_ag, edgecolor=c_ag_e, lw=2))
    ax.text(L_show/2, y4+t/2, 'Top GND', ha='center', va='center', fontsize=8, color='white', fontweight='bold')

    if via_enabled:
        vs = 1.0/max(via_density, 0.1)
        for i in range(int(L_show/vs)+1):
            xv = i*vs
            if xv > L_show: break
            ax.plot([xv, xv], [y0, y4+t], color=c_via, lw=2.2, alpha=0.6)
            ax.add_patch(Circle((xv, y0), via_diameter/2000, facecolor=c_via, edgecolor='black', lw=1))
            ax.add_patch(Circle((xv, y4+t), via_diameter/2000, facecolor=c_via, edgecolor='black', lw=1))

    # 左側總厚度標註
    ax.annotate('', xy=(-2.0, y0), xytext=(-2.0, y4+t), arrowprops=dict(arrowstyle='<->', color=c_dim, lw=1.8))
    ax.text(-2.5, total_h/2, f'Total\n{total_h*1000:.0f}μm', ha='right', va='center', fontsize=9, color=c_dim, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDEDEC', edgecolor=c_dim, alpha=0.9))

    # 底部長度標註
    ax.annotate('', xy=(0, -0.05), xytext=(L_show, -0.05), arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=2))
    label_L = f'L = {L} mm' if L <= L_show else f'L = {L} mm (顯示 {L_show} mm)'
    ax.text(L_show/2, -0.08, label_L, ha='center', va='top', fontsize=9, color=c_arrow, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#EBF5FB', edgecolor=c_arrow, alpha=0.9))

    # 右側各層厚度標註
    dx = L_show + 0.4
    for yy, hh, lbl in [(y0, t, f't={t*1000:.0f}μm'), (y1, h, f'h={h*1000:.0f}μm'),
                        (y3, h, f'h={h*1000:.0f}μm'), (y4, t, f't={t*1000:.0f}μm')]:
        ax.annotate('', xy=(dx, yy), xytext=(dx, yy+hh), arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=1.2))
        ax.text(dx+0.15, yy+hh/2, lbl, ha='left', va='center', fontsize=7, color=c_arrow)

    # 右側 Layer 標註：合併為單一垂直文字塊
    layer_text = (
        f'L5  Top GND      t={t*1000:.0f}μm\n'
        f'L4  Polyimide     h={h*1000:.0f}μm\n'
        f'L3  Signal        G-S-G\n'
        f'L2  Polyimide     h={h*1000:.0f}μm\n'
        f'L1  Bottom GND    t={t*1000:.0f}μm'
    )
    label_x = dx + 1.3
    ax.text(label_x, total_h/2, layer_text, ha='left', va='center', fontsize=8,
            color=c_layer, fontweight='bold', family='monospace',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='#F5EEF8', edgecolor=c_layer, alpha=0.95, linewidth=1.5),
            linespacing=1.6)

    # 引線
    right_edge = dx + 0.05
    layer_y = [y4+t/2, y3+h/2, y2+t/2, y1+h/2, y0+t/2]
    text_top = total_h/2 + 2*0.016
    step = 0.016
    for i, yc in enumerate(layer_y):
        ty = text_top - i*step
        ax.plot([right_edge, label_x-0.06], [yc, ty], color=c_layer, lw=0.7, linestyle='--', alpha=0.5)

    tight_layout()
    return fig


# ── 上視圖 (Top View) ───────────────────────────────────────
def 上視圖(geo: StriplineGeometry, pitch: float, length: float, via_enabled: bool, via_diameter: float, via_density: float, n_channels: int): #draw_top_view
    w, h, t, s, L = geo.w, geo.h, geo.t/1000, pitch, length
    channels = min(n_channels, 6)
    total_w = s * n_channels
    L_show = min(L, 80)
    margin = max(s*0.35, 0.3)

    c_ag, c_ag_e = '#C9A227', '#8B6914'
    c_poly, c_poly_e = '#F5E6C8', '#D4A574'
    c_via, c_dim, c_arrow = '#A0522D', '#E74C3C', '#2980B9'

    fig, ax = subplots(figsize=(10, 7))
    ax.set_title(f'上視圖 Top View (X-Y)  {n_channels}ch  pitch={s:.1f}mm  w={w*1000:.0f}μm',
                 fontsize=11, fontweight='bold', color='#2C3E50')
    ax.set_xlabel('Width (mm)', fontsize=9)
    ax.set_ylabel('Length (mm)', fontsize=9)
    ax.set_xlim(-margin, total_w + margin + 1.2)
    ax.set_ylim(-2.5, L_show + 2.5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.12, linestyle='--')

    ax.add_patch(Rectangle((-margin/2, 0), total_w+margin, L_show, facecolor=c_ag, edgecolor=c_ag_e, lw=2, alpha=0.25))
    ax.text(total_w/2, L_show+1.2, 'Top GND Layer', ha='center', va='bottom', fontsize=9, color=c_ag_e, fontweight='bold')

    for i in range(n_channels):
        xc = s*(i+0.5)
        ax.add_patch(Rectangle((xc-w/2, 0), w, L_show, facecolor='none', edgecolor=c_ag, lw=2, linestyle='--', alpha=0.7))
        ax.text(xc, -0.9, f'S{i+1}', ha='center', va='top', fontsize=9, color='#2C3E50', fontweight='bold')
    for i in range(n_channels-1):
        gx = s*(i+1); gw = w*0.3
        ax.add_patch(Rectangle((gx-gw/2, 0), gw, L_show, facecolor='none', edgecolor='#D4AF37', lw=1.5, linestyle=':', alpha=0.5))

    if via_enabled:
        vr = via_diameter/2000; vs = 1.0/max(via_density, 0.1)
        for ix in range(int(total_w/vs)+1):
            for iy in range(int(L_show/vs)+1):
                xv, yv = ix*vs, iy*vs
                if xv > total_w or yv > L_show: continue
                ax.add_patch(Circle((xv, yv), vr, facecolor=c_via, edgecolor='black', lw=0.8, alpha=0.8))

    # 底部 w / pitch 標註
    ax.annotate('', xy=(s*0.5-w/2, -1.6), xytext=(s*0.5+w/2, -1.6), arrowprops=dict(arrowstyle='<->', color=c_dim, lw=2))
    ax.text(s*0.5, -1.9, f'w = {w*1000:.0f} μm', ha='center', va='top', fontsize=9, color=c_dim, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=c_dim, alpha=0.9))
    ax.annotate('', xy=(s*0.5, -1.6), xytext=(s*1.5, -1.6), arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=2))
    ax.text(s, -1.9, f'pitch = {s:.1f} mm', ha='center', va='top', fontsize=9, color=c_arrow, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=c_arrow, alpha=0.9))

    # 右側長度標註
    ax.annotate('', xy=(total_w+margin*0.3, 0), xytext=(total_w+margin*0.3, L_show), arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=2))
    ax.text(total_w+margin*0.3+0.25, L_show/2, f'L = {L} mm', ha='left', va='center', fontsize=9, color=c_arrow, fontweight='bold',
            rotation=90, rotation_mode='anchor',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#EBF5FB', edgecolor=c_arrow, alpha=0.9))

    # 頂部總寬度標註
    ax.annotate('', xy=(0, L_show+0.6), xytext=(total_w, L_show+0.6), arrowprops=dict(arrowstyle='<->', color=c_dim, lw=1.8))
    ax.text(total_w/2, L_show+0.85, f'Total Width = {total_w:.1f} mm ({n_channels} ch)', ha='center', va='bottom', fontsize=9,
            color=c_dim, fontweight='bold', bbox=dict(boxstyle='round,pad=0.25', facecolor='#FDEDEC', edgecolor=c_dim, alpha=0.9))

    # Legend 置於左上角，避免與傳輸線/Via 重疊
    legend_elements = [
        Rectangle((0,0),1,1, facecolor=c_ag, edgecolor=c_ag_e, lw=2, label='Ag/NbTi Conductor'),
        Rectangle((0,0),1,1, facecolor=c_poly, edgecolor=c_poly_e, lw=2, alpha=0.85, label='Polyimide (εr=3.4)'),
        Circle((0,0), 0.1, facecolor=c_via, edgecolor='black', label='GND Via')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=8, framealpha=0.92,
              bbox_to_anchor=(0.02, 0.98), edgecolor='gray')

    tight_layout()
    return fig

def 匯出試算表():
# ============================================================
# XLSX 匯出：三視圖各為獨立工作表
# 替換 MENU[4] 的 XLSX 匯出區域
# ============================================================

  subheader("📥 匯出 XLSX 規格檔")
  info("匯出內容：設計參數、性能指標、公式推導、逐步計算、前視圖、側視圖、上視圖")

  import openpyxl
  from openpyxl.drawing.image import Image as XLImage
  from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

  wb = openpyxl.Workbook()
  header_fill = PatternFill(start_color="1F77B4", end_color="1F77B4", fill_type="solid")
  header_font = Font(color="FFFFFF", bold=True, size=11)
  thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                       top=Side(style='thin'), bottom=Side(style='thin'))

  # --- Sheet 1~4: 設計參數 / 性能指標 / 公式推導 / 逐步計算（沿用既有）---

  # --- Sheet 5: 前視圖 ---
  ws5 = wb.create_sheet("前視圖")
  ws5.append([f"前視圖 Front View (X-Z) | {n_channels}ch | w={sig_width}μm | h={dielectric_thickness}μm | t={sig_thickness}μm", ""])
  buf_f = _view_to_buffer(前視圖(geo, pitch, via_enabled, via_diameter, via_density, n_channels))
  img_f = XLImage(buf_f); img_f.width = 720; img_f.height = 500
  ws5.add_image(img_f, "A3")

  # --- Sheet 6: 側視圖 ---
  ws6 = wb.create_sheet("側視圖")
  ws6.append([f"側視圖 Side View (Y-Z) | L={length}mm | h={dielectric_thickness}μm | t={sig_thickness}μm", ""])
  buf_s = _view_to_buffer(側視圖(geo, pitch, length, via_enabled, via_diameter, via_density, n_channels))
  img_s = XLImage(buf_s); img_s.width = 720; img_s.height = 500
  ws6.add_image(img_s, "A3")

  # --- Sheet 7: 上視圖 ---
  ws7 = wb.create_sheet("上視圖")
  ws7.append([f"上視圖 Top View (X-Y) | {n_channels}ch | pitch={pitch}mm | w={sig_width}μm", ""])
  buf_t = _view_to_buffer(上視圖(geo, pitch, length, via_enabled, via_diameter, via_density, n_channels))
  img_t = XLImage(buf_t); img_t.width = 720; img_t.height = 500
  ws7.add_image(img_t, "A3")

  # 三視圖工作表樣式
  for ws in [ws5, ws6, ws7]:
      for row in ws.iter_rows():
          for cell in row:
              cell.border = thin_border
              cell.alignment = Alignment(vertical='center', wrap_text=True)
      ws.column_dimensions['A'].width = 32
      ws.column_dimensions['B'].width = 40

  xlsx_buf = BytesIO()
  wb.save(xlsx_buf)
  xlsx_buf.seek(0)

  download_button(
      label="📥 下載 XLSX 規格檔 (含單位/公式/三視圖)",
      data=xlsx_buf.getvalue(),
      file_name=f"crioflex3_spec_{length}mm_{n_channels}ch.xlsx",
      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
  )
