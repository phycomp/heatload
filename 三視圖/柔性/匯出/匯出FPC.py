# 柔性線函式庫/驗證/報告匯出.py
"""驗證報告 Excel 匯出 - 含物理推導與設計建議"""

from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime

from 驗證.規格基準 import 取得原廠規格, 列出非官方規格
from 驗證.電氣計算 import 計算特性阻抗, 計算傳播延遲, 計算插入損耗, 計算衰減頻譜, 計算串擾
from 驗證.物理推導 import 取得所有推導
from 驗證.設計建議 import 產生設計建議報告


def 匯出驗證報告(佈局, 驗證結果, 工作溫度=300):
    """匯出完整驗證報告 (含物理推導與設計建議)"""
    
    wb = openpyxl.Workbook()
    
    # 樣式
    標題填色 = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    標題字型 = Font(color="FFFFFF", bold=True, size=12)
    通過填色 = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    失敗填色 = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    非官方填色 = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    細邊框 = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )
    
    # ===== Sheet 1: 驗證總覽 =====
    # ... (保持不變)
    
    # ===== Sheet 2: 詳細驗證 =====
    # ... (保持不變)
    
    # ===== Sheet 3: 電氣特性 =====
    # ... (保持不變)
    
    # ===== Sheet 4: 物理推導 =====
    ws4 = wb.create_sheet("物理推導")
    
    ws4.merge_cells('A1:D1')
    cell = ws4['A1']
    cell.value = "電性與熱負載物理推導"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = 標題填色
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws4.row_dimensions[1].height = 30
    
    材料 = 'NbTi' if 佈局.規格類型 == 'FPC' else 'Ag'
    推導結果 = 取得所有推導(佈局, 材料, 工作溫度)
    
    row = 3
    for 名稱, 推導 in 推導結果.items():
        # 標題行
        ws4.merge_cells(f'A{row}:D{row}')
        cell = ws4.cell(row=row, column=1, value=f"【{名稱}】")
        cell.font = Font(bold=True, size=12, color="1F4E79")
        cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        row += 1
        
        # 公式
        ws4.cell(row=row, column=1, value="公式").font = Font(bold=True)
        ws4.cell(row=row, column=2, value=推導['公式'])
        row += 1
        
        # 參數
        for 參數名, 參數值 in 推導['參數'].items():
            ws4.cell(row=row, column=2, value=參數名)
            ws4.cell(row=row, column=3, value=參數值)
            row += 1
        
        # 結果
        if '計算結果' in 推導:
            ws4.cell(row=row, column=1, value="計算結果").font = Font(bold=True)
            ws4.cell(row=row, column=2, value=推導['計算結果'])
            row += 1
        
        # 物理意義
        ws4.cell(row=row, column=1, value="物理意義").font = Font(bold=True)
        ws4.cell(row=row, column=2, value=推導['物理意義'])
        row += 1
        
        # 設計建議
        ws4.cell(row=row, column=1, value="設計建議").font = Font(bold=True)
        ws4.cell(row=row, column=2, value=推導['設計建議'])
        row += 2
    
    ws4.column_dimensions['A'].width = 14
    ws4.column_dimensions['B'].width = 50
    ws4.column_dimensions['C'].width = 20
    
    # ===== Sheet 5: 設計建議 =====
    ws5 = wb.create_sheet("設計建議")
    
    ws5.merge_cells('A1:D1')
    cell = ws5['A1']
    cell.value = "失敗原因分析與設計建議"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="8B4513", end_color="8B4513", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws5.row_dimensions[1].height = 30
    
    失敗報告 = 產生設計建議報告(驗證結果, 佈局)
    
    if not 失敗報告:
        ws5['A3'] = "🎉 所有驗證項目通過，無需調整設計。"
        ws5['A3'].font = Font(size=12, color="006100")
    else:
        row = 3
        表頭 = ["類別", "項目", "失敗原因", "物理推導", "設計方向"]
        for col, 標題 in enumerate(表頭, 1):
            cell = ws5.cell(row=row, column=col, value=標題)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = 細邊框
        row += 1
        
        for 建議 in 失敗報告:
            設計方向 = "\n".join(f"• {d}" for d in 建議['設計方向'])
            values = [建議['類別'], 建議['項目'], 建議['失敗原因'], 建議['物理推導'], 設計方向]
            for col, value in enumerate(values, 1):
                cell = ws5.cell(row=row, column=col, value=value)
                cell.border = 細邊框
                cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
                if col == 1:
                    cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            row += 1
        
        欄寬 = {'A': 10, 'B': 18, 'C': 35, 'D': 35, 'E': 45}
        for col, 寬 in 欄寬.items():
            ws5.column_dimensions[col].width = 寬
    
    # ===== Sheet 6: 非官方規格 =====
    ws6 = wb.create_sheet("非官方規格")
    # ... (保持不變)
    
    # 儲存
    excel_buf = BytesIO()
    wb.save(excel_buf)
    excel_buf.seek(0)
    
    return excel_buf.getvalue()
