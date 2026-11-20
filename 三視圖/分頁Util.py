# ============================================================
# Excel 匯出功能 - 完整規格與放大圖形
# ============================================================
from 佈局計算 import LayoutCalculator, calculate_layer_positions, LAYER_DEFS
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.dimensions import DimensionHolder
from openpyxl.utils.cell import coordinate_from_string
from io import BytesIO

def 分頁(layout: LayoutCalculator, 前視圖, 側視圖, 上視圖):
    """匯出至Excel - 包含完整規格和放大三視圖"""
    
    wb = Workbook()
    
    # 定義樣式
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=14)
    sub_header_fill = PatternFill(start_color="2E5C8A", end_color="2E5C8A", fill_type="solid")
    sub_header_font = Font(color="FFFFFF", bold=True, size=12)
    thin_border = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )
    
    # ============================================================
    # Sheet 1: Delft cri/oFlex3 CF3 規格欄位
    # ============================================================
    
    ws1 = wb.active
    ws1.title = "CF3 Specifications"
    
    # 標題
    ws1.merge_cells('A1:F1')
    cell = ws1['A1']
    cell.value = "Delft cri/oFlex3 CF3 - Complete Specifications"
    cell.font = Font(size=16, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 35
    
    # 子標題
    ws1.merge_cells('A2:F2')
    cell = ws1['A2']
    cell.value = f"Channel Configuration: {layout.n_channels} Channels | Pitch: {layout.pitch_mm}mm | Total Width: {layout.total_width_mm:.2f}mm"
    cell.font = Font(size=11, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="2E5C8A", end_color="2E5C8A", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[2].height = 28
    
    # 規格表格標題
    row = 4
    headers = ["類別", "參數", "規格值", "單位", "備註", "公差"]
    for col, header in enumerate(headers, 1):
        cell = ws1.cell(row=row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    
    ws1.row_dimensions[row].height = 25
    row += 1
    
    # 規格數據
    from 分頁預覽 import 規格資框
    資框規格=規格資框(layout)
    # 填入規格數據
    for spec_row in 資框規格:
        for col, value in enumerate(spec_row, 1):
            cell = ws1.cell(row=row, column=col, value=value)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="left" if col > 1 else "center", 
                                      vertical="center", wrap_text=True)
            
            # 類別欄位背景色
            if col == 1 and value:
                cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
                cell.font = Font(bold=True)
        
        # 空行分隔
        if not spec_row[0] and not spec_row[1]:
            row += 1
        
        row += 1
    
    # 設定列寬
    column_widths = {'A': 14, 'B': 22, 'C': 18, 'D': 12, 'E': 32, 'F': 12}
    for col, width in column_widths.items():
        ws1.column_dimensions[col].width = width
    
    # ============================================================
    # Sheet 2: 前視圖 (放大)
    # ============================================================
    
    ws2 = wb.create_sheet("前視圖") #Front View
    
    # 標題
    ws2.merge_cells('A1:E1')
    cell = ws2['A1']
    cell.value = f"前視截面圖－({layout.n_channels} Channels)"
    # cell.value = f"Front View - Cross Section ({layout.n_channels} Channels)"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 30
    
    # 子標題
    ws2.merge_cells('A2:E2')
    cell = ws2['A2']
    cell.value = f"GSG七層帶狀線 | 寬度: {layout.total_width_mm:.2f}mm | 厚度: {layout.total_thick_um}um | 間距: {layout.pitch_mm}mm"
    cell.font = Font(size=10, italic=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[2].height = 25
    
    # 將前視圖放大插入 (調整尺寸)
    front_buf = BytesIO()
    前視圖.savefig(front_buf, format='png', dpi=200, facecolor='#0D1117', 
                     edgecolor='none', bbox_inches='tight')
    front_buf.seek(0)
    
    img_front = XLImage(front_buf)
    # 放大圖形 (根據通道數調整)
    if layout.n_channels <= 4:
        img_front.width = 800
        img_front.height = 500
    elif layout.n_channels <= 8:
        img_front.width = 1024
        img_front.height = 768
    else:
        img_front.width = 1280
        img_front.height =1024
    
    ws2.add_image(img_front, 'A4')
    
    # 設定列寬和行高
    for col in range(1, 6):
        ws2.column_dimensions[get_column_letter(col)].width = 20
    ws2.row_dimensions[3].height = 10
    
    # ============================================================
    # Sheet 3: 側視圖 (放大)
    # ============================================================
    
    ws3 = wb.create_sheet("側視圖") #Side View
    
    # 標題
    ws3.merge_cells('A1:E1')
    cell = ws3['A1']
    cell.value = f"側視圖-長度規格 ({layout.n_channels} Channels)"
    # cell.value = f"Side View - Length Profile ({layout.n_channels} Channels)"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws3.row_dimensions[1].height = 30
    
    # 子標題
    ws3.merge_cells('A2:E2')
    cell = ws3['A2']
    cell.value = f"長度: 400mm | 彎曲半徑: 5mm | 連接器類型: SMA/SMP"
    # cell.value = f"Length: 400mm | Bend Radius: 5mm | Connector: SMA/SMP"
    cell.font = Font(size=14, italic=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws3.row_dimensions[2].height = 25
    
    # 側視圖放大插入
    side_buf = BytesIO()
    側視圖.savefig(side_buf, format='png', dpi=200, facecolor='#0D1117', 
                    edgecolor='none', bbox_inches='tight')
    side_buf.seek(0)
    
    img_side = XLImage(side_buf)
    img_side.width = 900
    img_side.height = 420
    
    ws3.add_image(img_side, 'A4')
    
    for col in range(1, 6):
        ws3.column_dimensions[get_column_letter(col)].width = 20
    ws3.row_dimensions[3].height = 10
    
    # ============================================================
    # Sheet 4: 上視圖 (放大)
    # ============================================================
    
    ws4 = wb.create_sheet("上視圖") #Top View
    
    # 標題
    ws4.merge_cells('A1:E1')
    cell = ws4['A1']
    cell.value = f"Top View - Plan Layout ({layout.n_channels} Channels)"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws4.row_dimensions[1].height = 30
    
    # 子標題
    ws4.merge_cells('A2:E2')
    cell = ws4['A2']
    cell.value = f"Width: {layout.total_width_mm:.2f}mm | Pitch: {layout.pitch_mm}mm | Integrated Filtering"
    cell.font = Font(size=14, italic=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws4.row_dimensions[2].height = 25
    
    # 上視圖放大插入
    top_buf = BytesIO()
    上視圖.savefig(top_buf, format='png', dpi=200, facecolor='#0D1117', 
                   edgecolor='none', bbox_inches='tight')
    top_buf.seek(0)
    
    img_top = XLImage(top_buf)
    img_top.width = 900
    img_top.height = 500
    
    ws4.add_image(img_top, 'A4')
    
    for col in range(1, 6):
        ws4.column_dimensions[get_column_letter(col)].width = 20
    ws4.row_dimensions[3].height = 10
    
    # ============================================================
    # Sheet 5: Layer Stack-up
    # ============================================================
    
    ws5 = wb.create_sheet("Layer Stack-up")
    
    # 標題
    ws5.merge_cells('A1:F1')
    cell = ws5['A1']
    cell.value = "Layer Stack-up Detail"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws5.row_dimensions[1].height = 30
    
    # 表格標題
    row = 3
    headers = ["Layer No.", "Layer Name", "Material", "Thickness (um)", "Thickness (mm)", "Function"]
    for col, header in enumerate(headers, 1):
        cell = ws5.cell(row=row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws5.row_dimensions[row].height = 25
    row += 1
    
    # 層數據
    layer_functions = [
        'Mechanical protection',
        'EM shielding / Return path',
        'Dielectric isolation',
        f'Signal ({layout.n_channels} channels)',
        'Dielectric isolation',
        'EM shielding / Return path',
        'Mechanical protection'
    ]
    
    layer_colors = {
        '保護層': 'E8D5C4',
        '接地層': '8B9CAD',
        '介電層': 'C4956A',
        '訊號線': 'FFD700'
    }
    
    layer_positions, _ = calculate_layer_positions(LAYER_DEFS)
    
    for i, (layer_def, pos) in enumerate(zip(LAYER_DEFS, layer_positions), 1):
        # 確定層類別
        layer_type = '介電層'
        if '保護' in layer_def['name']:
            layer_type = '保護層'
        elif '接地' in layer_def['name']:
            layer_type = '接地層'
        elif '訊號' in layer_def['name']:
            layer_type = '訊號線'
        
        data = [
            i,
            layer_def['name'],
            layer_def['material'],
            layer_def['thick_um'],
            round(layer_def['thick_um'] / 1000, 4),
            layer_functions[i-1]
        ]
        
        for col, value in enumerate(data, 1):
            cell = ws5.cell(row=row, column=col, value=value)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center" if col <= 4 else "left", 
                                      vertical="center", wrap_text=True)
            
            # 根據層類型著色
            if layer_type in layer_colors:
                cell.fill = PatternFill(start_color=layer_colors[layer_type], 
                                       end_color=layer_colors[layer_type], 
                                       fill_type="solid")
        
        row += 1
    
    # 總計行
    total_row = row
    ws5.merge_cells(start_row=total_row, start_column=1, end_row=total_row, end_column=2)
    cell = ws5.cell(row=total_row, column=1, value="TOTAL")
    cell.font = Font(bold=True)
    cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = thin_border
    
    cell = ws5.cell(row=total_row, column=3, value="")
    cell.border = thin_border
    
    cell = ws5.cell(row=total_row, column=4, value=layout.total_thick_um)
    cell.font = Font(bold=True)
    cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = thin_border
    
    cell = ws5.cell(row=total_row, column=5, value=round(layout.total_thick_um / 1000, 4))
    cell.font = Font(bold=True)
    cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = thin_border
    
    cell = ws5.cell(row=total_row, column=6, value="")
    cell.border = thin_border
    
    # 設定列寬
    column_widths = {'A': 12, 'B': 28, 'C': 18, 'D': 18, 'E': 16, 'F': 35}
    for col, width in column_widths.items():
        ws5.column_dimensions[col].width = width
    
    # 儲存Excel
    excel_buf = BytesIO()
    wb.save(excel_buf)
    excel_buf.seek(0)
    
    return excel_buf.getvalue()
