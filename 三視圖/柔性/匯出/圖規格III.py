# 柔性線函式庫/匯出/Excel.py
"""匯出 Excel 規格書"""

from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter
from 核心.層II import 取得層定義


def 建立層疊表格(佈局, 規格類型='GSG'):
    """建立層疊結構資料 (根據規格類型)"""
    層定義 = 取得層定義(規格類型)
    
    層疊 = []
    for i, 層 in enumerate(層定義, 1):
        功能 = '訊號傳輸' if 層['是訊號層'] else ('接地/屏蔽' if '接地' in 層['名稱'] else '絕緣/保護')
        層疊.append({
            '層號': i,
            '層名稱': 層['名稱'],
            '材料': 層['材料'],
            '厚度um': 層['厚度um'],
            '厚度mm': 層['厚度um'] / 1000,
            '功能': 功能
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
    
    # ===== Sheet 1: 規格表 =====
    # ... (規格表保持不變，但使用佈局.規格類型)
    
    # ===== Sheet 5: 層疊結構 =====
    ws5 = wb.create_sheet("層疊結構")
    ws5.merge_cells('A1:F1')
    cell = ws5['A1']
    cell.value = f"{佈局.規格名稱} (Ag/NbTi {佈局.鈮鈦比例})"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws5.row_dimensions[1].height = 30
    
    # ... (其餘程式碼保持不變)
    
    return excel_buf.getvalue()
