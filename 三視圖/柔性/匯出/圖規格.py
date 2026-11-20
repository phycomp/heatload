# 柔性線函式庫/匯出/Excel.py
"""匯出 Excel 規格書"""
from 核心.層 import 層定義
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter


def 建立規格表格(佈局):
    """建立規格資料表格"""
    規格 = [
        {'類別': '一般規格', '參數': '通道數', '規格值': 佈局.通道數, '單位': 'ch', '備註': '-', '公差': '±0.5'},
        {'類別': '一般規格', '參數': '總寬度', '規格值': f'{佈局.線總寬:.2f}', '單位': 'mm', '備註': '-', '公差': '±0.1'},
        {'類別': '一般規格', '參數': '總厚度', '規格值': 佈局.總厚度um, '單位': 'μm', '備註': '-', '公差': '±5'},
        {'類別': '一般規格', '參數': '線長度', '規格值': 佈局.線長度, '單位': 'mm', '備註': '標準長度', '公差': '±1'},
        {'類別': '一般規格', '參數': '訊號間距', '規格值': 佈局.訊號間距, '單位': 'mm', '備註': '-', '公差': '±0.05'},
        {'類別': '一般規格', '參數': '訊號寬度', '規格值': 佈局.訊號寬度mm * 1000, '單位': 'μm', '備註': '-', '公差': '±2'},
        {'類別': '一般規格', '參數': '彎曲半徑', '規格值': 5, '單位': 'mm', '備註': '最小', '公差': '-0/+1'},
        {'類別': '電氣規格', '參數': '特性阻抗', '規格值': 50, '單位': 'Ω', '備註': '單端', '公差': '±5'},
        {'類別': '電氣規格', '參數': '傳播延遲', '規格值': 5.5, '單位': 'ns/m', '備註': '-', '公差': '±0.3'},
        {'類別': '材料規格', '參數': '導體材料', '規格值': 'Ag/NbTi', '單位': '-', '備註': f'比例 {佈局.鈮鈦比例}', '公差': '-'},
        {'類別': '材料規格', '參數': '介電材料', '規格值': 'Polyimide', '單位': '-', '備註': '低損耗', '公差': '-'},
        {'類別': '材料規格', '參數': '保護層材料', '規格值': 'Polyimide', '單位': '-', '備註': '覆蓋層', '公差': '-'},
        {'類別': '熱性能', '參數': '工作溫度', '規格值': -40, '單位': '°C', '備註': '最低', '公差': '-'},
        {'類別': '熱性能', '參數': '工作溫度', '規格值': 85, '單位': '°C', '備註': '最高', '公差': '-'},
        {'類別': '機械規格', '參數': '連接器', '規格值': 'SMA/SMP', '單位': '-', '備註': '兩端', '公差': '-'},
    ]
    return 規格


def 建立層疊表格(佈局):
    """建立層疊結構資料"""
    
    層疊 = []
    for i, 層 in enumerate(層定義, 1):
        層疊.append({
            '層號': i,
            '層名稱': 層['名稱'],
            '材料': 層['材料'],
            '厚度um': 層['厚度um'],
            '厚度mm': 層['厚度um'] / 1000,
            '功能': '訊號傳輸' if 層['是訊號層'] else ('接地/屏蔽' if '接地' in 層['名稱'] else '絕緣/保護')
        })
    
    # 加入總計
    總厚度um = sum(層['厚度um'] for 層 in 層定義)
    層疊.append({
        '層號': '總計',
        '層名稱': '-',
        '材料': '-',
        '厚度um': 總厚度um,
        '厚度mm': 總厚度um / 1000,
        '功能': '-'
    })
    return 層疊


def 匯出分頁(佈局, 前視圖, 側視圖, 上視圖, 字型縮放=1.0):
    """匯出完整 Excel 規格書"""
    
    wb = openpyxl.Workbook()
    
    # 定義樣式
    標題填色 = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    標題字型 = Font(color="FFFFFF", bold=True, size=12)
    子標題填色 = PatternFill(start_color="2E5C8A", end_color="2E5C8A", fill_type="solid")
    子標題字型 = Font(color="FFFFFF", bold=True, size=11)
    細邊框 = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )
    
    # ============================================================
    # Sheet 1: 規格表
    # ============================================================
    ws1 = wb.active
    ws1.title = "規格表"
    
    # 標題
    ws1.merge_cells('A1:G1')
    cell = ws1['A1']
    cell.value = f"U-leam UF1 柔性傳輸線規格書"
    cell.font = Font(size=16, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 35
    
    # 子標題
    ws1.merge_cells('A2:G2')
    cell = ws1['A2']
    cell.value = f"通道數: {佈局.通道數}ch | 間距: {佈局.訊號間距}mm | 總寬: {佈局.線總寬:.2f}mm | 鈮鈦比例: {佈局.鈮鈦比例}"
    cell.font = Font(size=11, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="2E5C8A", end_color="2E5C8A", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[2].height = 28
    
    # 表頭
    row = 4
    表頭 = ["類別", "參數", "規格值", "單位", "備註", "公差"]
    for col, 標題 in enumerate(表頭, 1):
        cell = ws1.cell(row=row, column=col, value=標題)
        cell.font = 標題字型
        cell.fill = 標題填色
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = 細邊框
    ws1.row_dimensions[row].height = 25
    row += 1
    
    # 填入規格
    規格資料 = 建立規格表格(佈局)
    for 項目 in 規格資料:
        values = [項目["類別"], 項目["參數"], 項目["規格值"], 
                  項目["單位"], 項目["備註"], 項目["公差"]]
        for col, value in enumerate(values, 1):
            cell = ws1.cell(row=row, column=col, value=value)
            cell.border = 細邊框
            cell.alignment = Alignment(horizontal="center" if col <= 2 else "left", 
                                      vertical="center", wrap_text=True)
            if col == 1:
                cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
                cell.font = Font(bold=True)
        row += 1
    
    # 設定列寬
    欄寬 = {'A': 14, 'B': 20, 'C': 18, 'D': 12, 'E': 30, 'F': 12}
    for col, 寬 in 欄寬.items():
        ws1.column_dimensions[col].width = 寬
    
    # ============================================================
    # Sheet 2: 前視圖
    # ============================================================
    ws2 = wb.create_sheet("前視圖")
    ws2.merge_cells('A1:E1')
    cell = ws2['A1']
    cell.value = f"前視截面 ({佈局.通道數} 通道)"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 30
    
    ws2.merge_cells('A2:E2')
    cell = ws2['A2']
    cell.value = f"GSG 7層疊構 | 材料: Ag/NbTi ({佈局.鈮鈦比例}) | 寬度: {佈局.線總寬:.2f}mm"
    cell.font = Font(size=10, italic=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[2].height = 25
    
    # 插入圖片
    front_buf = BytesIO()
    前視圖.savefig(front_buf, format='png', dpi=150, facecolor='#0D1117', 
                  edgecolor='none', bbox_inches='tight')
    front_buf.seek(0)
    
    img_front = XLImage(front_buf)
    if 佈局.通道數 <= 4:
        img_front.width = 700
        img_front.height = 450
    elif 佈局.通道數 <= 8:
        img_front.width = 800
        img_front.height = 500
    else:
        img_front.width = 900
        img_front.height = 560
    
    ws2.add_image(img_front, 'A4')
    
    for col in range(1, 6):
        ws2.column_dimensions[get_column_letter(col)].width = 20
    
    # ============================================================
    # Sheet 3: 側視圖
    # ============================================================
    ws3 = wb.create_sheet("側視圖")
    ws3.merge_cells('A1:E1')
    cell = ws3['A1']
    cell.value = f"側視圖 ({佈局.通道數} 通道)"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws3.row_dimensions[1].height = 30
    
    ws3.merge_cells('A2:E2')
    cell = ws3['A2']
    cell.value = f"長度: {佈局.線長度}mm | 彎曲半徑: 5mm | 連接器: SMA/SMP"
    cell.font = Font(size=10, italic=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws3.row_dimensions[2].height = 25
    
    side_buf = BytesIO()
    側視圖.savefig(side_buf, format='png', dpi=150, facecolor='#0D1117', 
                  edgecolor='none', bbox_inches='tight')
    side_buf.seek(0)
    
    img_side = XLImage(side_buf)
    img_side.width = 800
    img_side.height = 380
    ws3.add_image(img_side, 'A4')
    
    for col in range(1, 6):
        ws3.column_dimensions[get_column_letter(col)].width = 20
    
    # ============================================================
    # Sheet 4: 上視圖
    # ============================================================
    ws4 = wb.create_sheet("上視圖")
    ws4.merge_cells('A1:E1')
    cell = ws4['A1']
    cell.value = f"上視圖 ({佈局.通道數} 通道)"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws4.row_dimensions[1].height = 30
    
    ws4.merge_cells('A2:E2')
    cell = ws4['A2']
    cell.value = f"寬度: {佈局.線總寬:.2f}mm | Pitch: {佈局.訊號間距}mm | 鈮鈦比例: {佈局.鈮鈦比例}"
    cell.font = Font(size=10, italic=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws4.row_dimensions[2].height = 25
    
    top_buf = BytesIO()
    上視圖.savefig(top_buf, format='png', dpi=150, facecolor='#0D1117', 
                  edgecolor='none', bbox_inches='tight')
    top_buf.seek(0)
    
    img_top = XLImage(top_buf)
    img_top.width = 800
    img_top.height = 450
    ws4.add_image(img_top, 'A4')
    
    for col in range(1, 6):
        ws4.column_dimensions[get_column_letter(col)].width = 20
    
    # ============================================================
    # Sheet 5: 層疊結構
    # ============================================================
    ws5 = wb.create_sheet("層疊結構")
    ws5.merge_cells('A1:F1')
    cell = ws5['A1']
    cell.value = f"七層疊構詳述 (Ag/NbTi {佈局.鈮鈦比例})"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws5.row_dimensions[1].height = 30
    
    row = 3
    表頭 = ["層號", "層名稱", "材料", "厚度 (μm)", "厚度 (mm)", "功能"]
    for col, 標題 in enumerate(表頭, 1):
        cell = ws5.cell(row=row, column=col, value=標題)
        cell.font = 標題字型
        cell.fill = 標題填色
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = 細邊框
    ws5.row_dimensions[row].height = 25
    row += 1
    
    # 顏色對照
    層顏色 = {
        '保護層下': 'E8D5C4',
        '保護層上': 'E8D5C4',
        '接地層下': '8B9CAD',
        '接地層上': '8B9CAD',
        '介電層下': 'C4956A',
        '介電層上': 'C4956A',
        '訊號線': 'FFD700',
    }
    
    層疊資料 = 建立層疊表格(佈局)
    for 項目 in 層疊資料:
        if 項目["層號"] == "總計":
            for col, value in enumerate([項目["層號"], "", "", 項目["厚度um"], 項目["厚度mm"], ""], 1):
                cell = ws5.cell(row=row, column=col, value=value)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = 細邊框
        else:
            顏色 = 層顏色.get(項目["層名稱"], 'FFFFFF')
            for col, value in enumerate([項目["層號"], 項目["層名稱"], 項目["材料"],
                                         項目["厚度um"], 項目["厚度mm"], 項目["功能"]], 1):
                cell = ws5.cell(row=row, column=col, value=value)
                cell.border = 細邊框
                cell.alignment = Alignment(horizontal="center" if col <= 5 else "left", 
                                          vertical="center", wrap_text=True)
                if 顏色 != 'FFFFFF':
                    cell.fill = PatternFill(start_color=顏色, end_color=顏色, fill_type="solid")
        row += 1
    
    # 設定列寬
    欄寬 = {'A': 12, 'B': 18, 'C': 18, 'D': 16, 'E': 16, 'F': 30}
    for col, 寬 in 欄寬.items():
        ws5.column_dimensions[col].width = 寬
    
    # 儲存 Excel
    excel_buf = BytesIO()
    wb.save(excel_buf)
    excel_buf.seek(0)
    
    return excel_buf.getvalue()
