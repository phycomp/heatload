# cf3_excel_export.py
# Excel 匯出模組

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.drawing.image import Image as XLImage
from io import BytesIO
import pandas as pd


def 匯出規格(calc, front_fig, side_fig, top_fig, filename="CF3_Specification.xlsx"):
    """
    匯出 CF3 完整規格書至 Excel
    
    Args:
        calc: LayoutCalculator 實例
        front_fig: 前視圖 Figure
        side_fig: 側視圖 Figure
        top_fig: 上視圖 Figure
        filename: 輸出檔案名稱
    """
    wb = openpyxl.Workbook()
    
    # 定義樣式
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=12)
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # ===== Sheet 1: 規格總表 =====
    ws1 = wb.active
    ws1.title = "CF3 Specifications"
    
    # 標題
    ws1.merge_cells('A1:F1')
    ws1['A1'] = "Delft cri/oFlex3 CF3 - Complete Specifications"
    ws1['A1'].font = Font(size=16, bold=True, color="FFFFFF")
    ws1['A1'].fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    ws1['A1'].alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 35
    
    # 參數表
    params = [
        ["參數", "數值", "單位", "備註"],
        ["通道數", calc.n_channels, "ch", ""],
        ["通道間距 (Pitch)", calc.pitch_mm, "mm", ""],
        ["訊號線寬度", calc.signal_width_um, "μm", "50Ω 設計"],
        ["總寬度", calc.target_total_width_mm, "mm", ""],
        ["總厚度", calc.total_thickness_um, "μm", ""],
        ["介電層厚度", calc.dielectric_thickness_um, "μm", "上下各一層"],
        ["訊號層厚度", calc.signal_layer['thickness_um'], "μm", ""],
        ["邊緣 Clearance", calc.edge_margin_mm, "mm", f"10H = {calc.clearance_10h:.3f}mm"],
        ["通道間間距", calc.channel_gap_mm, "mm", f"5W = {calc.gap_5w:.3f}mm"],
        ["特性阻抗", calc.impedance['z0_ohm'], "Ω", f"目標: {calc.target_impedance}Ω"],
        ["估算串擾", calc.estimated_crosstalk_db, "dB", ""],
        ["估算插入損耗", calc.estimated_il_db_per_m, "dB/m", "@ 6GHz"],
        ["傳播延遲", calc.propagation_delay_ns_per_m, "ns/m", ""],
        ["截止頻率", calc.cutoff_frequency_ghz, "GHz", ""],
    ]
    
    row = 3
    for p in params:
        for col, val in enumerate(p, 1):
            ws1.cell(row=row, column=col, value=val)
            ws1.cell(row=row, column=col).border = thin_border
        row += 1
    
    # ===== Sheet 2: 層疊結構 =====
    ws2 = wb.create_sheet("Layer Stack-up")
    ws2.merge_cells('A1:F1')
    ws2['A1'] = "Layer Stack-up Detail"
    ws2['A1'].font = Font(size=14, bold=True, color="FFFFFF")
    ws2['A1'].fill = header_fill
    ws2['A1'].alignment = Alignment(horizontal="center", vertical="center")
    
    headers = ["層號", "層名稱", "材料", "厚度 (μm)", "厚度 (mm)", "功能"]
    for col, h in enumerate(headers, 1):
        cell = ws2.cell(row=3, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    row = 4
    for pos in calc.layer_positions:
        data = [
            pos['index'] + 1,
            pos['name'],
            pos['material'],
            pos['thickness_um'],
            pos['thickness_mm'],
            "Signal" if pos['is_signal'] else "Ground" if pos['is_ground'] else "Dielectric/Protection"
        ]
        for col, val in enumerate(data, 1):
            ws2.cell(row=row, column=col, value=val)
            ws2.cell(row=row, column=col).border = thin_border
            ws2.cell(row=row, column=col).alignment = Alignment(horizontal="center", vertical="center")
        row += 1
    
    # ===== Sheet 3-5: 三視圖 =====
    views = [
        ("Front View", front_fig),
        ("Side View", side_fig),
        ("Top View", top_fig)
    ]
    
    for view_name, fig in views:
        ws = wb.create_sheet(view_name)
        ws.merge_cells('A1:E1')
        ws['A1'] = f"CF3 {view_name}"
        ws['A1'].font = Font(size=14, bold=True, color="FFFFFF")
        ws['A1'].fill = header_fill
        ws['A1'].alignment = Alignment(horizontal="center", vertical="center")
        
        # 儲存圖形
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        buf.seek(0)
        
        img = XLImage(buf)
        img.width = 700
        img.height = 450
        ws.add_image(img, 'A3')
    
    # 儲存 Excel
    wb.save(filename)
    print(f"✅ Excel 規格書已儲存: {filename}")
