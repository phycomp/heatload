from matplotlib.pyplot import close, figure
from numpy import linspace

import io
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
from matplotlib.gridspec import GridSpec
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.drawing.image import Image as XLImage

def 前視圖(通道數=8, pitch_mm=2.0, signal_width_mm=0.4):
    """
    繪製動態前視圖，回傳 matplotlib Figure 與 BytesIO PNG buffer
    """
    # === 正確 GSG 7 層結構（單位：um）===
    layers = [
        ('保護層(Polyimide)',  15, 'Polyimide', '#E8D5C4', '#A0522D', False), #Protective Coating 
        ('接地層(Ag/NbTi)',           5, 'Ag/NbTi',   '#8B9CAD', '#4A5568', False), #Ground Plane 
        ('介電層(Polyimide)',         129, 'Polyimide', '#C4956A', '#744210', False), #Dielectric 
        ('訊號層(Ag/NbTi)',           2, 'Ag/NbTi',   '#FFD700', '#B8860B', True),  #Signal Lines 
        ('介電層(Polyimide)',         129, 'Polyimide', '#C4956A', '#744210', False), #Dielectric 
        ('接地層(Ag/NbTi)',           5, 'Ag/NbTi',   '#8B9CAD', '#4A5568', False), #Ground Plane 
        ('保護層(Polyimide)',  15, 'Polyimide', '#E8D5C4', '#A0522D', False), #Protective Coating 
    ]
    
    total_thickness_um = sum(l[1] for l in layers)
    signal_idx = 3
    signal_thick = layers[signal_idx][1]
    center_from_bottom = sum(l[1] for l in layers[:signal_idx]) + signal_thick/2
    
    y_bottoms = []
    cum = -center_from_bottom
    for _, thick, _, _, _, _ in layers:
        y_bottoms.append(cum)
        cum += thick
    y_tops = y_bottoms[1:] + [cum]
    
    total_width = 通道數 * pitch_mm
    
    # 繪圖
    fig = plt.figure(figsize=(16, 10), facecolor='#0D1117')
    gs = GridSpec(1, 2, figure=fig, width_ratios=[3.2, 1.0],
                  left=0.07, right=0.95, top=0.90, bottom=0.08, wspace=0.10)
    ax_main = fig.add_subplot(gs[0, 0])
    ax_main.set_facecolor('#0D1117')
    ax_info = fig.add_subplot(gs[0, 1])
    ax_info.set_facecolor('#161B22')
    ax_info.axis('off')
    
    fig.suptitle(
        f'Cri/oFlex 3 CF3 Front View  |  {通道數} Channels  |  GSG 7-Layer Stack-up',
        fontsize=14, fontweight='bold', color='white', y=0.96
    )
    
    # 繪製各層
    for i, (layer, yb, yt) in enumerate(zip(layers, y_bottoms, y_tops)):
        name, thick, mat, color, edge, is_sig = layer
        y_bot = yb / 1000.0
        y_top = yt / 1000.0
        thick_mm = thick / 1000.0
        
        if is_sig:
            for ch in range(通道數):
                x_c = -total_width/2 + pitch_mm/2 + ch * pitch_mm
                sig = Rectangle((x_c - signal_width_mm/2, y_bot), signal_width_mm, thick_mm,
                                facecolor=color, edgecolor=edge, linewidth=1.5, zorder=5)
                ax_main.add_patch(sig)
                if 通道數 <= 12:
                    fs = 7 if 通道數 > 8 else 8
                    ax_main.text(x_c, y_bot + thick_mm/2, str(ch+1),
                                ha='center', va='center', fontsize=fs, color='#333', fontweight='bold', zorder=6)
            bg = Rectangle((-total_width/2 - 1, y_bot), total_width + 2, thick_mm,
                           facecolor='#D4A574', edgecolor='none', alpha=0.2, zorder=1)
            ax_main.add_patch(bg)
        else:
            layer_rect = Rectangle((-total_width/2 - 2, y_bot), total_width + 4, thick_mm,
                                     facecolor=color, edgecolor=edge, linewidth=1.2, alpha=0.95, zorder=3)
            ax_main.add_patch(layer_rect)
            if 'Ground' in name:
                for j in range(int((total_width + 4) / 0.3)):
                    x0 = -total_width/2 - 2 + j * 0.3
                    ax_main.plot([x0, x0 + thick_mm*3], [y_bot, y_top],
                                color='#5A6B7D', linewidth=0.25, alpha=0.35, zorder=4)
            if 'Protective' in name:
                for dx in np.linspace(-total_width/2 - 1.5, total_width/2 + 1.5, int((total_width+3)/0.8)):
                    for dy in np.linspace(y_bot + thick_mm*0.2, y_top - thick_mm*0.2, max(1, int(thick_mm/0.05))):
                        ax_main.plot(dx, dy, '.', color='#A0522D', markersize=1.2, alpha=0.25, zorder=4)
        
        # 層標註
        display_names = [
            'Protective Coating - Bottom', 'Ground Plane - Bottom', 'Dielectric - Lower',
            f'Signal Lines (x{通道數})', 'Dielectric - Upper', 'Ground Plane - Top',
            'Protective Coating - Top'
        ]
        label_y = (y_bot + y_top) / 2
        ax_main.text(-total_width/2 - 5, label_y, display_names[i],
                    ha='right', va='center', fontsize=8, color='white', fontweight='bold', zorder=10,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#0D1117', edgecolor=color, linewidth=1.5, alpha=0.95))
        
        # 厚度標註
        thick_x = total_width/2 + 3
        ax_main.annotate('', xy=(thick_x, y_bot), xytext=(thick_x, y_top),
                        arrowprops=dict(arrowstyle='<->', color='#58A6FF', lw=1.2), zorder=10)
        ax_main.text(thick_x + 1, label_y, f'{thick} um', ha='left', va='center', fontsize=7,
                    color='#58A6FF', fontweight='bold', zorder=10)
        
        if i < len(layers) - 1:
            ax_main.axhline(y=y_top, xmin=0.08, xmax=0.92, color='white', linewidth=0.4, linestyle=':', alpha=0.25, zorder=2)
    
    # 整體尺寸
    ax_main.annotate('', xy=(total_width/2 + 14, -0.15), xytext=(total_width/2 + 14, 0.15),
                    arrowprops=dict(arrowstyle='<->', color='#F85149', lw=2))
    ax_main.text(total_width/2 + 16, 0, f'Total\nt=300 um', ha='left', va='center', fontsize=9, color='#F85149', fontweight='bold')
    
    ax_main.annotate('', xy=(-total_width/2, 0.16), xytext=(total_width/2, 0.16),
                    arrowprops=dict(arrowstyle='<->', color='#F85149', lw=2))
    ax_main.text(0, 0.175, f'W={total_width} mm ({通道數}ch x {pitch_mm}mm)', ha='center', va='bottom', fontsize=9, color='#F85149', fontweight='bold')
    
    ax_main.axhline(y=0, color='#FF6B6B', linewidth=1.2, linestyle='-.', alpha=0.5)
    ax_main.text(total_width/2 + 0.5, 0.008, 'Signal Center (Y=0)', ha='left', va='bottom', fontsize=7, color='#FF6B6B', style='italic')
    
    ax_main.set_xlim(-total_width/2 - 32, total_width/2 + 32)
    ax_main.set_ylim(-0.18, 0.20)
    ax_main.set_xlabel('Width (mm)', color='white', fontsize=10)
    ax_main.set_ylabel('厚度(mm)', color='white', fontsize=10)  #Thickness 
    ax_main.tick_params(colors='white', labelsize=8)
    for spine in ax_main.spines.values(): spine.set_color('#30363D')
    ax_main.set_title('GSG Stripline Cross-Section | Z0 = 50 Ohm | 7-Layer', fontsize=11, color='#58A6FF', fontweight='bold', pad=8)
    
    # 右側資訊
    info_txt = (
        f'CF3 Spec ({通道數} ch)\n{"="*22}\n'
        f'Pitch:     {pitch_mm} mm\nWidth:     {total_width} mm\n'
        f'Thickness: 0.3 mm (300 um)\nImpedance: 50 Ohm\n'
        f'Freq:      DC-18 GHz\nMaterial:  Polyimide+Ag/NbTi\n\n'
        f'Layer Stack-up\n{"="*22}\n'
        f'1. Protective Coating  15 um\n2. Ground Plane         5 um\n'
        f'3. Dielectric         129 um\n4. Signal Lines         2 um x{通道數}ch\n'
        f'5. Dielectric         129 um\n6. Ground Plane         5 um\n'
        f'7. Protective Coating  15 um\n   Total:             300 um'
    )
    ax_info.text(0.08, 0.97, info_txt, transform=ax_info.transAxes, fontsize=8.5, color='#C9D1D9',
                va='top', ha='left', linespacing=1.35,
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#0D1117', edgecolor='#30363D', linewidth=1.2))
    
    legend_items = [('#E8D5C4', 'Protective Coating'), ('#8B9CAD', 'Ground Plane'),
                    ('#C4956A', 'Dielectric'), ('#FFD700', f'Signal Lines x{通道數}')]
    for i, (color, label) in enumerate(legend_items):
        y_leg = 0.04 - i * 0.028
        rect = Rectangle((0.08, y_leg), 0.05, 0.018, facecolor=color, edgecolor='white', linewidth=0.5,
                         transform=ax_info.transAxes)
        ax_info.add_patch(rect)
        ax_info.text(0.15, y_leg + 0.009, label, transform=ax_info.transAxes, fontsize=8, color='#C9D1D9', va='center')
    
    # 輸出到 buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=200, facecolor='#0D1117', edgecolor='none', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf


def 匯出分頁(通道數=8, pitch_mm=2.0, signal_width_mm=0.4):
    """
    產生含前視圖的 Excel：Layer_Stackup 分頁同時包含圖片 + 表格
    """
    total_width = 通道數 * pitch_mm
    
    # === 7 層結構 ===
    layers = [
        ('Protective Coating (Polyimide)',  15, 'Polyimide', 'Mechanical protection'),
        ('Ground Plane (Ag/NbTi)',           5, 'Ag/NbTi',   'EM shielding / Return path'),
        ('Dielectric (Polyimide)',         129, 'Polyimide', 'Dielectric isolation'),
        ('Signal Lines (Ag/NbTi)',           2, 'Ag/NbTi',   f'Signal ({通道數} ch)'),
        ('Dielectric (Polyimide)',         129, 'Polyimide', 'Dielectric isolation'),
        ('Ground Plane (Ag/NbTi)',           5, 'Ag/NbTi',   'EM shielding / Return path'),
        ('Protective Coating (Polyimide)',  15, 'Polyimide', 'Mechanical protection'),
    ]
    
    signal_idx = 3
    cum = 0
    y_coords = [0]
    for _, thick, _, _ in layers:
        cum += thick
        y_coords.append(cum)
    center = sum(l[1] for l in layers[:signal_idx]) + layers[signal_idx][1] / 2
    y_bottoms = [y - center for y in y_coords[:-1]]
    y_tops    = [y - center for y in y_coords[1:]]
    
    wb = Workbook()
    
    # ==================== Sheet 1: Layer_Stackup（含圖片） ====================
    ws1 = wb.active
    ws1.title = "多層結構"  #Layer_Stackup
    
    # 標題列
    ws1.append([f"Cri/oFlex 3 CF3 前視 + 多層結構  |  {通道數} Channels"])  #Front View | Layer Stack-up
    ws1.merge_cells("A1:H1")
    ws1["A1"].font = Font(size=14, bold=True, color="FFFFFF")
    ws1["A1"].fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    ws1["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 28
    
    # === 插入前視圖圖片 ===
    img_buf = 前視圖(通道數, pitch_mm, signal_width_mm)
    img = XLImage(img_buf)
    img.width = 1024
    img.height = 850
    ws1.add_image(img, "A3")
    
    table_start_row = 45 # 預留圖片空間後，從第 45 行開始放表格
    
    ws1.cell(row=table_start_row, column=1, value="多層疊構圖") #Layer Detail Table
    ws1.merge_cells(start_row=table_start_row, start_column=1, end_row=table_start_row, end_column=8)
    ws1.cell(row=table_start_row, column=1).font = Font(size=12, bold=True, color="FFFFFF")
    ws1.cell(row=table_start_row, column=1).fill = PatternFill(start_color="2E5C8A", end_color="2E5C8A", fill_type="solid")
    ws1.cell(row=table_start_row, column=1).alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[table_start_row].height = 24
    
    # 表頭
    headers = ["層級", "層名", "材質", "厚度(um)", "厚度(mm)", #Layer No.|Layer Name|Material|Thickness | Thickness 
               "往下+(um)", "往上+(um)", "功能"]  #Y-Bottom |Y-Top |Function
    for col, header in enumerate(headers, 1):
        cell = ws1.cell(row=table_start_row + 1, column=col, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    color_map = {"Protective": "E8D5C4", "Ground": "8B9CAD", "Dielectric": "C4956A", "Signal": "FFD700"}
    for i, ((name, thick, mat, func), yb, yt) in enumerate(zip(layers, y_bottoms, y_tops), 1):
        row = table_start_row + 1 + i
        ws1.append([i, name, mat, thick, round(thick/1000, 3), round(yb, 1), round(yt, 1), func])
        fill_key = next((k for k in color_map if k in name), "FFFFFF")
        for cell in ws1[row]:
            cell.fill = PatternFill(start_color=color_map[fill_key], end_color=color_map[fill_key], fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")
    
    # 總計
    total_row = table_start_row + 2 + len(layers)
    ws1.append(["", "TOTAL", "", 300, 0.3, "", "", ""])
    for cell in ws1[total_row]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    for col, w in zip("ABCDEFGH", [12, 36, 16, 16, 16, 16, 16, 35]):
        ws1.column_dimensions[col].width = w
    
    # ==================== Sheet 2: Specifications ====================
    ws2 = wb.create_sheet("規格") #Specifications
    ws2.append(["Cri/oFlex 3 CF3 - 規格"])  #General Specifications
    ws2.merge_cells("A1:D1")
    ws2["A1"].font = Font(size=14, bold=True, color="FFFFFF")
    ws2["A1"].fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    ws2["A1"].alignment = Alignment(horizontal="center", vertical="center")
    
    specs = [
        #("Parameter", "Value", "Unit", "Notes"),
        #("Channels", 通道數, "ch", "Per flex cable"),
        #("Pitch", pitch_mm, "mm", "Channel-to-channel"),
        #("Total Width", total_width, "mm", f"{通道數} ch x {pitch_mm} mm"),
        #("Total Thickness", 0.3, "mm", "300 um (7-layer GSG)"),
        #("Signal Line Width", signal_width_mm, "mm", "Center conductor"),
        #("Signal Line Thickness", 2, "um", "Ag/NbTi thin film"),
        #("Dielectric Thickness", 129, "um", "Each side of signal"),
        #("Ground Plane Thickness", 5, "um", "Ag/NbTi, each side"),
        #("Protective Coating", 15, "um", "Polyimide, each side"),
        #("Characteristic Impedance", 50, "Ohm", "Stripline design"),
        #("Frequency Range", "DC - 18", "GHz", "Microwave operation"),
        #("Bend Radius", 5, "mm", "Minimum"),
        #("Heat Load (Ag)", "< 125", "uW/ch", "@ 4-40K, L=0.4m"),
        #("Heat Load (NbTi)", "~ 20", "nW/ch", "@ 10-350mK, L=0.2m"),
        #("Crosstalk", "< -60", "dB", "Typical"),
        #("Connector", "SMA (f) / SMP (m)", "", "Right-angle / Straight"),
        ("參數", "值", "單位", "備註"), #Parameter Value Unit Notes
        ("通道", 通道數, "ch", "每條"), #Channels | Per flex cable
        ("間距", pitch_mm, "mm", "通道至通道"), #Pitch  |  Channel-to-channel
        ("總寬度", total_width, "mm", f"{通道數} ch × {pitch_mm} mm"),  #Total Width
        ("總厚度", .3, "mm", "300 μm (七層7-layer GSG)"),  #Total Thickness
        ("訊號線寬度", signal_width_mm, "mm", "Center conductor"),  #Signal Line Width
        ("訊號線厚度", 2, "μm", "Ag/NbTi薄膜"), #Signal Line Thickness |  thin film
        ("介電質厚度", 129, "μm", "訊號層兩側"), #Dielectric Thickness  | Each side of signal
        ("接地層厚度", 5, "μm", "Ag/NbTi單側"),  #Ground Plane Thickness| , each side
        ("保護層厚度", 15, "μm", "Polyimide單側"), #Protective Coating|, each side
        ("特徵阻抗", 50, "Ω", "帶線設計"),  #Characteristic Impedance|Stripline design
        ("頻率波段", "DC – 18", "GHz", "微波波段"),  #Frequency Range   Microwave operation
        ("彎曲半徑", 5, "mm", "最小"), #Bend Radius Minimum
        ("熱負載(Ag)", "< 125", "μW/ch", "@ 4–40 K, L=0.4 m"),  #Heat Load 
        ("熱負載(NbTi)", "~ 20", "nW/ch", "@ 10–350 mK, L=0.2 m"),  #Heat Load 
        ("串擾", "< –60", "dB", "典型"), #Crosstalk|Typical
        ("連接器", "SMA (f) / SMP (m)", "", "直角"),  #Connector|Right-angle / Straight
    ]
    for row in specs:
        ws2.append(row)
    for cell in ws2[4]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for r in range(5, ws2.max_row + 1):
        if r % 2 == 0:
            for cell in ws2[r]:
                cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        for cell in ws2[r]:
            cell.alignment = Alignment(horizontal="center", vertical="center")
    for col, w in zip("ABCD", [28, 22, 12, 32]):
        ws2.column_dimensions[col].width = w
    
    # ==================== Sheet 3: Channel_Dimensions ====================
    ws3 = wb.create_sheet("通道尺寸") #Channel_Dimensions
    ws3.append([f"Cri/oFlex 3 CF3 - 通道佈局({通道數} Channels)"])  #Channel Layout 
    ws3.merge_cells("A1:F1")
    ws3["A1"].font = Font(size=14, bold=True, color="FFFFFF")
    ws3["A1"].fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    ws3["A1"].alignment = Alignment(horizontal="center", vertical="center")
    
    ch_headers = ["Channel", "Center X (mm)", "Left Edge (mm)", "Right Edge (mm)",
                  "Signal Width (mm)", "Gap to Next (mm)"]
    ws3.append(ch_headers)
    for cell in ws3[3]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    for ch in range(通道數):
        x_c = -total_width/2 + pitch_mm/2 + ch * pitch_mm
        gap = round(pitch_mm - signal_width_mm, 3) if ch < 通道數 - 1 else "N/A (edge)"
        ws3.append([f"CH{ch+1}", round(x_c, 2), round(x_c - signal_width_mm/2, 3),
                    round(x_c + signal_width_mm/2, 3), signal_width_mm, gap])
        if ch % 2 == 0:
            for cell in ws3[ws3.max_row]:
                cell.fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
        for cell in ws3[ws3.max_row]:
            cell.alignment = Alignment(horizontal="center", vertical="center")
    
    ws3.append(["SUMMARY", f"Total Width = {total_width} mm", "", "", f"Pitch = {pitch_mm} mm", ""])
    for cell in ws3[ws3.max_row]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    for col, w in zip("ABCDEF", [12, 16, 16, 16, 18, 18]):
        ws3.column_dimensions[col].width = w
    
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()
