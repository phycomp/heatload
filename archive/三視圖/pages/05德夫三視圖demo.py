import io
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, Circle
from matplotlib.gridspec import GridSpec
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.drawing.image import Image as XLImage


# ============================================================
# 共用參數（可從 st.session_state 或 UI 輸入動態取得）
# ============================================================
N_CHANNELS = st.session_state.get("n_channels", 8)
PITCH = 2.0
SIGNAL_WIDTH = 0.4
LENGTH = 400
TOTAL_THICKNESS_MM = 0.3

# GSG 7層結構（um）
LAYERS = [
    ('Protective Coating (Polyimide)',  15, 'Polyimide', '#E8D5C4', '#A0522D', False),
    ('Ground Plane (Ag/NbTi)',           5, 'Ag/NbTi',   '#8B9CAD', '#4A5568', False),
    ('Dielectric (Polyimide)',         129, 'Polyimide', '#C4956A', '#744210', False),
    ('Signal Lines (Ag/NbTi)',           2, 'Ag/NbTi',   '#FFD700', '#B8860B', True),
    ('Dielectric (Polyimide)',         129, 'Polyimide', '#C4956A', '#744210', False),
    ('Ground Plane (Ag/NbTi)',           5, 'Ag/NbTi',   '#8B9CAD', '#4A5568', False),
    ('Protective Coating (Polyimide)',  15, 'Polyimide', '#E8D5C4', '#A0522D', False),
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

def draw_front_view(n_ch=N_CHANNELS):
    """前視圖：GSG 7層橫截面"""
    total_w = n_ch * PITCH
    fig = plt.figure(figsize=(16, 10), facecolor='#0D1117')
    gs = GridSpec(1, 2, figure=fig, width_ratios=[3.2, 1.0],
                  left=0.07, right=0.95, top=0.90, bottom=0.08, wspace=0.10)
    ax_main = fig.add_subplot(gs[0, 0]); ax_main.set_facecolor('#0D1117')
    ax_info = fig.add_subplot(gs[0, 1]); ax_info.set_facecolor('#161B22'); ax_info.axis('off')
    
    fig.suptitle(f'Cri/oFlex 3 CF3  Front View  |  {n_ch} Channels  |  GSG 7-Layer',
                 fontsize=14, fontweight='bold', color='white', y=0.96)
    
    display_names = ['Protective Coating - Bottom', 'Ground Plane - Bottom', 'Dielectric - Lower',
                     f'Signal Lines (x{n_ch})', 'Dielectric - Upper', 'Ground Plane - Top',
                     'Protective Coating - Top']
    
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
                for dx in np.linspace(-total_w/2 - 1.5, total_w/2 + 1.5, int((total_w+3)/0.8)):
                    for dy in np.linspace(y_bot + thick_mm*0.2, y_top - thick_mm*0.2, max(1, int(thick_mm/0.05))):
                        ax_main.plot(dx, dy, '.', color='#A0522D', markersize=1.2, alpha=0.25, zorder=4)
        
        label_y = (y_bot + y_top) / 2
        ax_main.text(-total_w/2 - 5, label_y, display_names[i], ha='right', va='center', fontsize=8,
                    color='white', fontweight='bold', zorder=10,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#0D1117', edgecolor=color, linewidth=1.5, alpha=0.95))
        
        thick_x = total_w/2 + 3
        ax_main.annotate('', xy=(thick_x, y_bot), xytext=(thick_x, y_top),
                        arrowprops=dict(arrowstyle='<->', color='#58A6FF', lw=1.2), zorder=10)
        ax_main.text(thick_x + 1, label_y, f'{thick} um', ha='left', va='center', fontsize=7,
                    color='#58A6FF', fontweight='bold', zorder=10)
        
        if i < len(LAYERS) - 1:
            ax_main.axhline(y=y_top, xmin=0.08, xmax=0.92, color='white', linewidth=0.4, linestyle=':', alpha=0.25, zorder=2)
    
    ax_main.annotate('', xy=(total_w/2 + 14, -0.15), xytext=(total_w/2 + 14, 0.15),
                    arrowprops=dict(arrowstyle='<->', color='#F85149', lw=2))
    ax_main.text(total_w/2 + 16, 0, f'Total\nt=300 um', ha='left', va='center', fontsize=9, color='#F85149', fontweight='bold')
    ax_main.annotate('', xy=(-total_w/2, 0.16), xytext=(total_w/2, 0.16),
                    arrowprops=dict(arrowstyle='<->', color='#F85149', lw=2))
    ax_main.text(0, 0.175, f'W={total_w} mm ({n_ch}ch x {PITCH}mm)', ha='center', va='bottom', fontsize=9, color='#F85149', fontweight='bold')
    ax_main.axhline(y=0, color='#FF6B6B', linewidth=1.2, linestyle='-.', alpha=0.5)
    ax_main.text(total_w/2 + 0.5, 0.008, 'Signal Center (Y=0)', ha='left', va='bottom', fontsize=7, color='#FF6B6B', style='italic')
    
    ax_main.set_xlim(-total_w/2 - 32, total_w/2 + 32)
    ax_main.set_ylim(-0.18, 0.20)
    ax_main.set_xlabel('Width (mm)', color='white', fontsize=10)
    ax_main.set_ylabel('Thickness (mm)', color='white', fontsize=10)
    ax_main.tick_params(colors='white', labelsize=8)
    for spine in ax_main.spines.values(): spine.set_color('#30363D')
    ax_main.set_title('GSG Stripline Cross-Section | Z0 = 50 Ohm | 7-Layer', fontsize=11, color='#58A6FF', fontweight='bold', pad=8)
    
    info_txt = (f'CF3 Spec ({n_ch} ch)\n{"="*22}\nPitch: {PITCH} mm\nWidth: {total_w} mm\n'
                f'Thickness: 0.3 mm (300 um)\nImpedance: 50 Ohm\nFreq: DC-18 GHz\n'
                f'Material: Polyimide+Ag/NbTi\n\nLayer Stack-up\n{"="*22}\n'
                f'1. Protective Coating  15 um\n2. Ground Plane         5 um\n'
                f'3. Dielectric         129 um\n4. Signal Lines         2 um x{n_ch}ch\n'
                f'5. Dielectric         129 um\n6. Ground Plane         5 um\n'
                f'7. Protective Coating  15 um\n   Total:             300 um')
    ax_info.text(0.08, 0.97, info_txt, transform=ax_info.transAxes, fontsize=8.5, color='#C9D1D9',
                va='top', ha='left', linespacing=1.35,
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#0D1117', edgecolor='#30363D', linewidth=1.2))
    
    legend_items = [('#E8D5C4', 'Protective Coating'), ('#8B9CAD', 'Ground Plane'),
                    ('#C4956A', 'Dielectric'), ('#FFD700', f'Signal Lines x{n_ch}')]
    for i, (color, label) in enumerate(legend_items):
        y_leg = 0.04 - i * 0.028
        ax_info.add_patch(Rectangle((0.08, y_leg), 0.05, 0.018, facecolor=color, edgecolor='white', linewidth=0.5, transform=ax_info.transAxes))
        ax_info.text(0.15, y_leg + 0.009, label, transform=ax_info.transAxes, fontsize=8, color='#C9D1D9', va='center')
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=180, facecolor='#0D1117', edgecolor='none', bbox_inches='tight')
    buf.seek(0); plt.close(fig)
    return buf


def draw_side_view(n_ch=N_CHANNELS):
    """側視圖：長度方向輪廓"""
    total_w = n_ch * PITCH
    fig = plt.figure(figsize=(18, 8), facecolor='#0D1117')
    ax = fig.add_subplot(111); ax.set_facecolor('#0D1117')
    fig.suptitle(f'Cri/oFlex 3 CF3  Side View  |  {n_ch} Channels  |  Length {LENGTH} mm',
                 fontsize=14, fontweight='bold', color='white', y=0.96)
    
    t = np.linspace(0, LENGTH, 500)
    y_wave = 1.5 * np.sin(t / 60) * np.exp(-t / 400)
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
    
    max_curve_idx = np.argmax(np.abs(y_wave))
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
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=180, facecolor='#0D1117', edgecolor='none', bbox_inches='tight')
    buf.seek(0); plt.close(fig)
    return buf


def draw_top_view(n_ch=N_CHANNELS):
    """上視圖（俯視圖）：平面佈局"""
    total_w = n_ch * PITCH
    fig = plt.figure(figsize=(18, 10), facecolor='#0D1117')
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
    
    legend_items = [('#C4956A', 'Polyimide Substrate'), ('#FFD700', 'Signal Lines (Ag/NbTi)'),
                    ('#B87333', 'SMA/SMP Connector'), ('#4A90D9', 'Filter/Attenuator Zone')]
    for i, (color, label) in enumerate(legend_items):
        x_pos = 0.02 + i * 0.22
        ax.add_patch(Rectangle((x_pos, 0.02), 0.03, 0.025, facecolor=color, edgecolor='white', linewidth=0.5, transform=ax.transAxes))
        ax.text(x_pos + 0.035, 0.032, label, transform=ax.transAxes, fontsize=8, color='#AAAAAA', va='center')
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=180, facecolor='#0D1117', edgecolor='none', bbox_inches='tight')
    buf.seek(0); plt.close(fig)
    return buf


# ============================================================
# Excel 生成函式（四個分頁：三視圖 + 規格總表）
# ============================================================

def generate_cf3_three_view_excel(n_ch=N_CHANNELS):
    total_w = n_ch * PITCH
    
    # 繪製三視圖
    front_buf = draw_front_view(n_ch)
    side_buf = draw_side_view(n_ch)
    top_buf = draw_top_view(n_ch)
    
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
    
    # ---------- Sheet 1: Front_View ----------
    ws1 = wb.active; ws1.title = "Front_View"
    make_title(ws1, f"Cri/oFlex 3 CF3  Front View (Cross-Section)  |  {n_ch} Channels")
    make_subtitle(ws1, f"GSG 7-Layer Stripline  |  Width: {total_w} mm  |  Thickness: 0.3 mm")
    
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
    
    # ---------- Sheet 2: Side_View ----------
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
    
    # ---------- Sheet 3: Top_View ----------
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
    
    # ---------- Sheet 4: Specifications ----------
    ws4 = wb.create_sheet("Specifications")
    make_title(ws4, "Cri/oFlex 3 CF3 - Complete Specifications")
    make_subtitle(ws4, "General / Electrical / Thermal / Mechanical parameters")
    
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
    
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


# ============================================================
# Streamlit UI 側邊欄下載區
# ============================================================

with st.sidebar:
    st.markdown("---")
    st.subheader("📥 Export Three-View Drawing")
    
    n_ch = st.session_state.get("n_channels", 8)
    
    if st.button("📊 Generate Three-View Excel", use_container_width=True):
        with st.spinner("Generating Front / Side / Top views + Specifications..."):
            excel_bytes = generate_cf3_three_view_excel(n_ch=n_ch)
            st.session_state["three_view_excel"] = excel_bytes
            st.success("Three-View Excel ready!")
    
    if "three_view_excel" in st.session_state:
        st.download_button(
            label="⬇️ Download CF3_ThreeView_Spec.xlsx",
            data=st.session_state["three_view_excel"],
            file_name=f"CF3_ThreeView_Spec_{n_ch}ch.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
