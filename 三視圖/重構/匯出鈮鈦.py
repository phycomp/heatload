from io import BytesIO
# ============================================================
# 更新 Excel 匯出 - 加入鈮鈦比例欄位
# ============================================================

def 匯出分頁(佈局: LayoutCalculator, front_fig, side_fig, top_fig, 規格=None, 層疊=None):
    """匯出至Excel - 加入鈮鈦比例"""
    
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.drawing.image import Image as XLImage
    from openpyxl.utils import get_column_letter
    
    wb = openpyxl.Workbook()
    
    # 定義樣式
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=12)
    sub_header_fill = PatternFill(start_color="2E5C8A", end_color="2E5C8A", fill_type="solid")
    sub_header_font = Font(color="FFFFFF", bold=True, size=11)
    thin_border = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )
    
    # ============================================================
    # Sheet 1: Delft cri/oFlex3 CF3 規格欄位
    # ============================================================
    # NbTi=佈局.鈮鈦比例 #f'{100-佈局.鈦比例}:{佈局.鈦比例}'
    ws1 = wb.active
    ws1.title = "規格" #UF1完整規格
    
    # 標題
    ws1.merge_cells('A1:G1')
    cell = ws1['A1']
    cell.value = "U-leam UF1-柔性傳輸線規格書 for Readout"
    cell.font = Font(size=16, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 35
    
    # 子標題
    ws1.merge_cells('A2:G2')
    cell = ws1['A2']
    cell.value = f"傳輸線組態: {佈局.通道數} 通道數 | 間距: {佈局.訊號間距}mm | 總寬度: {佈局.線總寬:.2f}mm"
    cell.font = Font(size=11, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="2E5C8A", end_color="2E5C8A", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[2].height = 28
    
    # 規格表格標題
    row = 4
    headers = ["類別", "參數", "規格值", "單位", "備註", "公差", "材料比例"]
    for col, header in enumerate(headers, 1):
        cell = ws1.cell(row=row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    
    ws1.row_dimensions[row].height = 25
    row += 1
    
    # 使用DataFrame填入規格數據
    # spec_df = create_specification_dataframe(佈局)
    
    for _, spec_row in 規格.iterrows():
        # 判斷是否為NbTi相關規格，加入材料比例
        material_ratio = ""
        if "鈮鈦" in str(spec_row["參數"]) or "NbTi" in str(spec_row["參數"]):
            material_ratio = 佈局.鈮鈦比例 #f"{鈮比例}:{鈦比例}"
        elif "Ag/NbTi" in str(spec_row["規格值"]):
            material_ratio = 佈局.鈮鈦比例 #f"{鈮比例}:{鈦比例}"
        
        values = [spec_row["類別"], spec_row["參數"], spec_row["規格值"], 
                  spec_row["單位"], spec_row["備註"], spec_row["公差"], material_ratio]
        for col, value in enumerate(values, 1):
            cell = ws1.cell(row=row, column=col, value=value)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="left" if col > 1 else "center", 
                                      vertical="center", wrap_text=True)
            
            # 類別欄位背景色
            if col == 1 and value:
                cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
                cell.font = Font(bold=True)
            
            # 鈮鈦相關標記
            if material_ratio and col == 7:
                cell.fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
                cell.font = Font(bold=True, color="8B4513")
        
        row += 1
    
    # 設定列寬
    column_widths = {'A': 14, 'B': 22, 'C': 18, 'D': 12, 'E': 32, 'F': 12, 'G': 14}
    for col, width in column_widths.items():
        ws1.column_dimensions[col].width = width
    
    # ============================================================
    # Sheet 2: 前視圖 (放大)
    # ============================================================
    
    ws2 = wb.create_sheet("前視圖")
    
    ws2.merge_cells('A1:E1')
    cell = ws2['A1']
    cell.value = f"前視截面({佈局.通道數}通道數)"
    # cell.value = f"Front View - Cross Section ({佈局.通道數} Channels)"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 30
    
    ws2.merge_cells('A2:E2')
    cell = ws2['A2']
    cell.value = f"GSG 7層疊構| 材料:Ag/NbTi ({佈局.鈮鈦比例}) | 寬度:{佈局.線總寬:.2f}mm" #-Layer Stripline | Material | Width  #{鈮比例}:{鈦比例}
    cell.font = Font(size=10, italic=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[2].height = 25
    
    front_buf = BytesIO()
    front_fig.savefig(front_buf, format='png', dpi=200, facecolor='#0D1117', edgecolor='none', bbox_inches='tight')
    front_buf.seek(0)
    
    img_front = XLImage(front_buf)
    if 佈局.通道數 <= 4:
        img_front.width = 800
        img_front.height = 500
    elif 佈局.通道數 <= 8:
        img_front.width = 900
        img_front.height = 560
    else:
        img_front.width = 1000
        img_front.height = 620
    
    ws2.add_image(img_front, 'A4')
    
    for col in range(1, 6):
        ws2.column_dimensions[get_column_letter(col)].width = 20
    ws2.row_dimensions[3].height = 10
    
    # ============================================================
    # Sheet 3: 側視圖 (放大)
    # ============================================================
    
    ws3 = wb.create_sheet("側視圖")
    
    ws3.merge_cells('A1:E1')
    cell = ws3['A1']
    cell.value = f"側視圖({佈局.通道數} 通道)"  #Side View - Length Profile 
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws3.row_dimensions[1].height = 30
    
    ws3.merge_cells('A2:E2')
    cell = ws3['A2']
    cell.value = f"長度: 400mm | 彎曲半徑: 5mm | 連接器: SMA/SMP | NbTi: {佈局.鈮鈦比例}"
    cell.font = Font(size=10, italic=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws3.row_dimensions[2].height = 25
    
    side_buf = BytesIO()
    side_fig.savefig(side_buf, format='png', dpi=200, facecolor='#0D1117', 
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
    
    ws4 = wb.create_sheet("上視圖")
    
    ws4.merge_cells('A1:E1')
    cell = ws4['A1']
    cell.value = f"上視圖佈局({佈局.通道數} Channels)"  #Top View - Plan Layout 
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws4.row_dimensions[1].height = 30
    
    ws4.merge_cells('A2:E2')
    cell = ws4['A2']
    cell.value = f"寬度:{佈局.線總寬:.2f}mm | Pitch:{佈局.訊號間距}mm | NbTi: {佈局.鈮鈦比例}"  #{100-佈局.鈦比例}:{佈局.鈦比例}
    cell.font = Font(size=10, italic=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws4.row_dimensions[2].height = 25
    
    top_buf = BytesIO()
    top_fig.savefig(top_buf, format='png', dpi=200, facecolor='#0D1117', 
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
    
    ws5 = wb.create_sheet("外層疊構") #Layer Stack-up
    
    ws5.merge_cells('A1:G1')
    cell = ws5['A1']
    cell.value = f"七層疊構詳述 (Ag/NbTi {佈局.鈮鈦比例})"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws5.row_dimensions[1].height = 30
    
    row = 3
    headers = ["層號", "層名稱", "材料", "材料比例", "厚度 (um)", "厚度 (mm)", "功能"]
    for col, header in enumerate(headers, 1):
        cell = ws5.cell(row=row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws5.row_dimensions[row].height = 25
    row += 1
    
    # 使用DataFrame填入層疊數據
    # layer_df = create_layer_stackup_dataframe(佈局)
    
    layer_colors = {
        '保護層': 'E8D5C4',
        '接地層': '8B9CAD',
        '介電層': 'C4956A',
        '訊號線': 'FFD700'
    }
    
    for _, layer_row in 層疊.iterrows():
        if layer_row["層號"] == "總計":
            # 總計行
            for col, value in enumerate([layer_row["層號"], "", "", "", layer_row["厚度 (um)"], layer_row["厚度 (mm)"], ""], 1):
                cell = ws5.cell(row=row, column=col, value=value)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = thin_border
        else:
            # 判斷層類型
            layer_type = '介電層'
            if '保護' in layer_row["層名稱"]:
                layer_type = '保護層'
            elif '接地' in layer_row["層名稱"]:
                layer_type = '接地層'
            elif '訊號' in layer_row["層名稱"]:
                layer_type = '訊號線'
            
            # 判斷是否為NbTi材料
            if 'Ag/NbTi' in layer_row["材料"]:
                material_ratio = 佈局.鈮鈦比例  #'47:53'
            else:
                material_ratio = '-'
            
            for col, value in enumerate([layer_row["層號"], layer_row["層名稱"], layer_row["材料"], material_ratio,
                                        layer_row["厚度 (um)"], layer_row["厚度 (mm)"], 
                                        layer_row["功能"]], 1):
                cell = ws5.cell(row=row, column=col, value=value)
                cell.border = thin_border
                cell.alignment = Alignment(horizontal="center" if col <= 5 else "left", 
                                          vertical="center", wrap_text=True)
                
                if layer_type in layer_colors:
                    cell.fill = PatternFill(start_color=layer_colors[layer_type], 
                                           end_color=layer_colors[layer_type], 
                                           fill_type="solid")
                
                # NbTi材料標記
                if material_ratio in 佈局.鈮鈦比例 and col == 4:  #== '47:53'
                    cell.font = Font(bold=True, color="8B4513")
                    cell.fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
        row += 1
    
    # 設定列寬
    column_widths = {'A': 12, 'B': 28, 'C': 18, 'D': 16, 'E': 18, 'F': 16, 'G': 35}
    for col, width in column_widths.items():
        ws5.column_dimensions[col].width = width
    
    # 儲存Excel
    excel_buf = BytesIO()
    wb.save(excel_buf)
    excel_buf.seek(0)
    
    return excel_buf.getvalue()
