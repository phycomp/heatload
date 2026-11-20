import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

def 匯出分頁(n_channels: int = 8, pitch_mm: float = 2.0,
                         signal_width_mm: float = 0.4) -> bytes:
    """
    產生 Cri/oFlex 3 CF3 前視圖與規格的 Excel 位元組流
    分頁：Layer_Stackup / Specifications / Channel_Dimensions
    """
    total_width = n_channels * pitch_mm
    
    # === 正確 GSG 7 層結構（單位：um）===
    layers = [
        ('Protective Coating (Polyimide)',  15, 'Polyimide', 'Mechanical protection'),
        ('Ground Plane (Ag/NbTi)',           5, 'Ag/NbTi',   'EM shielding / Return path'),
        ('Dielectric (Polyimide)',         129, 'Polyimide', 'Dielectric isolation'),
        ('Signal Lines (Ag/NbTi)',           2, 'Ag/NbTi',   f'Signal ({n_channels} ch)'),
        ('Dielectric (Polyimide)',         129, 'Polyimide', 'Dielectric isolation'),
        ('Ground Plane (Ag/NbTi)',           5, 'Ag/NbTi',   'EM shielding / Return path'),
        ('Protective Coating (Polyimide)',  15, 'Polyimide', 'Mechanical protection'),
    ]
    
    # 計算 Y 座標（Signal 中心為 0）
    signal_idx = 3
    cum = 0
    y_coords = []
    for i, (name, thick, mat, func) in enumerate(layers):
        y_coords.append(cum)
        cum += thick
    y_tops = y_coords[1:] + [cum]
    # 以 Signal 中心為原點平移
    center = sum(l[1] for l in layers[:signal_idx]) + layers[signal_idx][1] / 2
    y_bottoms = [y - center for y in y_coords]
    y_tops    = [y - center for y in y_tops]
    
    wb = Workbook()
    
    # ---------- Sheet 1: Layer_Stackup ----------
    ws1 = wb.active
    ws1.title = "外層結構"  #Layer_Stackup
    ws1.append(["Cri/oFlex 3 CF3 - Layer Stack-up (Front View Cross-Section)"])
    ws1.merge_cells("A1:H1")
    ws1["A1"].font = Font(size=14, bold=True, color="FFFFFF")
    ws1["A1"].fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    ws1["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 28
    
    ws1.append([f"Config: {n_channels} ch | Pitch {pitch_mm} mm | Width {total_width} mm | Thickness 0.3 mm"])
    ws1.merge_cells("A2:H2")
    ws1["A2"].alignment = Alignment(horizontal="center")
    
    headers = ["Layer No.", "Layer Name", "Material", "Thickness (um)", "Thickness (mm)",
               "Y-Bottom (um)", "Y-Top (um)", "Function"]
    ws1.append(headers)
    for cell in ws1[4]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    color_map = {
        "Protective": "E8D5C4", "Ground": "8B9CAD",
        "Dielectric": "C4956A", "Signal": "FFD700"
    }
    for i, ((name, thick, mat, func), yb, yt) in enumerate(zip(layers, y_bottoms, y_tops), 1):
        row = [i, name, mat, thick, round(thick/1000, 3), round(yb, 1), round(yt, 1), func]
        ws1.append(row)
        fill_key = next((k for k in color_map if k in name), "FFFFFF")
        for cell in ws1[ws1.max_row]:
            cell.fill = PatternFill(start_color=color_map[fill_key], end_color=color_map[fill_key], fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")
    
    # 總計
    ws1.append(["", "TOTAL", "", 300, 0.3, "", "", ""])
    for cell in ws1[ws1.max_row]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    for col, w in zip("ABCDEFGH", [12, 36, 16, 16, 16, 16, 16, 35]):
        ws1.column_dimensions[col].width = w
    
    # ---------- Sheet 2: Specifications ----------
    ws2 = wb.create_sheet("規格") #Specifications
    ws2.append(["Cri/oFlex 3 CF3 - General Specifications"])
    ws2.merge_cells("A1:D1")
    ws2["A1"].font = Font(size=14, bold=True, color="FFFFFF")
    ws2["A1"].fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    ws2["A1"].alignment = Alignment(horizontal="center", vertical="center")
    
    specs = [
        ("參數", "值", "單位", "備註"), #Parameter Value Unit Notes
        ("通道", n_channels, "ch", "每條"), #Channels | Per flex cable
        ("間距", pitch_mm, "mm", "通道至通道"), #Pitch  |  Channel-to-channel
        ("總寬度", total_width, "mm", f"{n_channels} ch × {pitch_mm} mm"),  #Total Width
        ("總厚度", .3, "mm", "300 μm (七層7-layer GSG)"),  #Total Thickness
        ("訊號線寬度", signal_width_mm, "mm", "Center conductor"),  #Signal Line Width
        ("訊號線厚度", 2, "μm", "Ag/NbTi薄膜"), #Signal Line Thickness |  thin film
        ("介電質厚度", 129, "μm", "訊號層兩側"), #Dielectric Thickness  | Each side of signal
        ("接地層厚度", 5, "μm", "Ag/NbTi單側"),  #Ground Plane Thickness| , each side
        ("保護層厚度", 15, "μm", "Polyimide單側"), #Protective Coating|, each side
        ("特徵阻抗", 50, "Ω", "帶線設計"),  #Characteristic Impedance|Stripline design
        ("頻率波段", "DC – 18", "GHz", "微波波段"),  #Frequency Range   Microwave operation
        ("彎曲半徑", 5, "mm", "最小"), #Bend Radius Minimum
        ("熱負載Heat Load (Ag)", "< 125", "μW/ch", "@ 4–40 K, L=0.4 m"),
        ("熱負載Heat Load (NbTi)", "~ 20", "nW/ch", "@ 10–350 mK, L=0.2 m"),
        ("串擾", "< –60", "dB", "典型"), #Crosstalk|Typical
        ("連接器", "SMA (f) / SMP (m)", "", "直角"),  #Connector|Right-angle / Straight
    ]
    for row in specs:
        ws2.append(row)
    # 表頭格式
    for cell in ws2[4]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    # 隔行填色
    for r in range(5, ws2.max_row + 1):
        if r % 2 == 0:
            for cell in ws2[r]:
                cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        for cell in ws2[r]:
            cell.alignment = Alignment(horizontal="center", vertical="center")
    
    for col, w in zip("ABCD", [28, 22, 12, 32]):
        ws2.column_dimensions[col].width = w
    
    # ---------- Sheet 3: Channel_Dimensions ----------
    ws3 = wb.create_sheet("Channel_Dimensions")
    ws3.append([f"Cri/oFlex 3 CF3 - Channel Layout ({n_channels} Channels)"])
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
    
    for ch in range(n_channels):
        x_c = -total_width/2 + pitch_mm/2 + ch * pitch_mm
        gap = round(pitch_mm - signal_width_mm, 3) if ch < n_channels - 1 else "N/A (edge)"
        ws3.append([
            f"CH{ch+1}", round(x_c, 2),
            round(x_c - signal_width_mm/2, 3),
            round(x_c + signal_width_mm/2, 3),
            signal_width_mm, gap
        ])
        if ch % 2 == 0:
            for cell in ws3[ws3.max_row]:
                cell.fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
        for cell in ws3[ws3.max_row]:
            cell.alignment = Alignment(horizontal="center", vertical="center")
    
    # Summary
    ws3.append(["SUMMARY", f"Total Width = {total_width} mm", "", "", f"Pitch = {pitch_mm} mm", ""])
    for cell in ws3[ws3.max_row]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    for col, w in zip("ABCDEF", [12, 16, 16, 16, 18, 18]):
        ws3.column_dimensions[col].width = w
    
    # 輸出位元組
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()
