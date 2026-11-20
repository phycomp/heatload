# 柔性線函式庫/驗證/報告匯出.py
"""驗證報告 Excel 匯出"""

from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime

from .規格基準 import 取得原廠規格, 列出非官方規格
from .電氣計算 import (計算特性阻抗, 計算傳播延遲, 計算插入損耗, 
                      計算衰減頻譜, 計算串擾)


def 匯出驗證報告(佈局, 驗證結果):
    """匯出完整驗證報告"""
    
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
    ws1 = wb.active
    ws1.title = "驗證總覽"
    
    ws1.merge_cells('A1:E1')
    cell = ws1['A1']
    cell.value = f"Delft cri/oFlex3 規格驗證報告"
    cell.font = Font(size=16, bold=True, color="FFFFFF")
    cell.fill = 標題填色
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 35
    
    # 基本資訊
    ws1['A3'] = "規格類型"
    ws1['B3'] = 佈局.規格名稱
    ws1['A4'] = "驗證時間"
    ws1['B4'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ws1['A5'] = "通道數"
    ws1['B5'] = 佈局.通道數
    ws1['A6'] = "總寬度"
    ws1['B6'] = f"{佈局.線總寬:.2f} mm"
    ws1['A7'] = "總厚度"
    ws1['B7'] = f"{佈局.總厚度um} μm"
    
    for row in range(3, 8):
        ws1[f'A{row}'].font = Font(bold=True)
    
    # 統計摘要
    ws1['A9'] = "驗證統計"
    ws1['A9'].font = Font(bold=True, size=12)
    
    # 計算統計
    全部項目 = []
    for 類別, 結果列表 in 驗證結果.items():
        for 項目 in 結果列表:
            全部項目.append(項目)
    
    通過數 = sum(1 for 項目 in 全部項目 if 項目['通過'])
    失敗數 = len(全部項目) - 通過數
    
    ws1['A10'] = "總驗證項目"
    ws1['B10'] = len(全部項目)
    ws1['A11'] = "通過"
    ws1['B11'] = 通過數
    ws1['B11'].fill = 通過填色
    ws1['A12'] = "失敗"
    ws1['B12'] = 失敗數
    ws1['B12'].fill = 失敗填色 if 失敗數 > 0 else 通過填色
    ws1['A13'] = "通過率"
    ws1['B13'] = f"{通過數/len(全部項目)*100:.1f}%" if 全部項目 else "N/A"
    
    # ===== Sheet 2: 詳細驗證結果 =====
    ws2 = wb.create_sheet("詳細驗證")
    
    row = 1
    表頭 = ["類別", "項目", "規格值", "原廠值", "單位", "公差", "差異", "結果", "官方規格"]
    for col, 標題 in enumerate(表頭, 1):
        cell = ws2.cell(row=row, column=col, value=標題)
        cell.font = 標題字型
        cell.fill = 標題填色
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = 細邊框
    row += 1
    
    # 取得原廠規格
    原廠規格 = 取得原廠規格(佈局.規格類型)
    
    for 類別, 結果列表 in 驗證結果.items():
        for 項目 in 結果列表:
            # 查詢是否為官方規格
            官方 = True
            原廠項目 = 原廠規格.get(類別, {}).get(項目['項目'], {})
            if isinstance(原廠項目, dict):
                官方 = 原廠項目.get('官方', False)
            
            values = [
                類別,
                項目['項目'],
                項目['規格值'],
                項目['原廠值'],
                項目['單位'],
                項目['公差'],
                f"{項目['差異']:+.3f}" if isinstance(項目['差異'], (int, float)) else 項目['差異'],
                "✅ 通過" if 項目['通過'] else "❌ 失敗",
                "✅ 官方" if 官方 else "⚠️ 推導值"
            ]
            for col, value in enumerate(values, 1):
                cell = ws2.cell(row=row, column=col, value=value)
                cell.border = 細邊框
                cell.alignment = Alignment(horizontal="center", vertical="center")
                
                if col == 8:  # 結果
                    cell.fill = 通過填色 if 項目['通過'] else 失敗填色
                elif col == 9 and not 官方:  # 非官方規格
                    cell.fill = 非官方填色
            row += 1
    
    # 設定列寬
    欄寬 = {'A': 12, 'B': 18, 'C': 12, 'D': 12, 'E': 10, 'F': 12, 'G': 12, 'H': 10, 'I': 12}
    for col, 寬 in 欄寬.items():
        ws2.column_dimensions[col].width = 寬
    
    # ===== Sheet 3: 電氣特性計算 =====
    ws3 = wb.create_sheet("電氣特性計算")
    
    ws3.merge_cells('A1:D1')
    cell = ws3['A1']
    cell.value = "電氣特性計算結果"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = 標題填色
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws3.row_dimensions[1].height = 30
    
    row = 3
    表頭 = ["參數", "計算值", "單位", "備註"]
    for col, 標題 in enumerate(表頭, 1):
        cell = ws3.cell(row=row, column=col, value=標題)
        cell.font = 標題字型
        cell.fill = 標題填色
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = 細邊框
    row += 1
    
    # 計算電氣特性
    Z0 = 計算特性阻抗(佈局)
    tpd = 計算傳播延遲(佈局)
    
    電氣數據 = [
        ["特性阻抗", f"{Z0:.2f}", "Ω", "帶狀線公式"],
        ["傳播延遲", f"{tpd:.3f}", "ns/m", "√εr / c"],
    ]
    
    # 衰減頻譜
    for 材料 in ['Ag', 'NbTi']:
        for 溫度, 溫標 in [(300, '300K'), (4, '4K')]:
            頻譜 = 計算衰減頻譜(佈局, 材料, 溫度)
            for f, 衰減 in 頻譜.items():
                電氣數據.append([f"插入損耗 ({材料} @{溫標})", f"{衰減:.2f}", "dB/m", f"@{f}GHz"])
    
    # 串擾
    串擾 = 計算串擾(佈局, 10, 佈局.線長度)
    電氣數據.append(["串擾", f"{串擾:.1f}", "dB", f"@10GHz, L={佈局.線長度}mm"])
    
    for 數據 in 電氣數據:
        for col, value in enumerate(數據, 1):
            cell = ws3.cell(row=row, column=col, value=value)
            cell.border = 細邊框
            cell.alignment = Alignment(horizontal="center" if col <= 3 else "left")
        row += 1
    
    欄寬 = {'A': 28, 'B': 12, 'C': 10, 'D': 25}
    for col, 寬 in 欄寬.items():
        ws3.column_dimensions[col].width = 寬
    
    # ===== Sheet 4: 非官方規格清單 =====
    ws4 = wb.create_sheet("非官方規格")
    
    ws4.merge_cells('A1:E1')
    cell = ws4['A1']
    cell.value = "非官方規格清單 (推導值/計算值)"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="8B6914", end_color="8B6914", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws4.row_dimensions[1].height = 30
    
    ws4['A2'] = "說明：以下規格未在 Delft cri/oFlex3 官方 Datasheet 中列出，為幾何推導或物理計算值。"
    ws4['A2'].font = Font(italic=True, color="8B6914")
    
    row = 4
    表頭 = ["類別", "項目", "值", "單位", "備註"]
    for col, 標題 in enumerate(表頭, 1):
        cell = ws4.cell(row=row, column=col, value=標題)
        cell.font = 標題字型
        cell.fill = 標題填色
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = 細邊框
    row += 1
    
    非官方 = 列出非官方規格(佈局.規格類型)
    for 項目 in 非官方:
        values = [項目['類別'], 項目['項目'], 項目['值'], 項目['單位'], 項目['備註']]
        for col, value in enumerate(values, 1):
            cell = ws4.cell(row=row, column=col, value=value)
            cell.border = 細邊框
            cell.alignment = Alignment(horizontal="center" if col <= 4 else "left")
            if col <= 4:
                cell.fill = 非官方填色
        row += 1
    
    欄寬 = {'A': 12, 'B': 20, 'C': 12, 'D': 10, 'E': 30}
    for col, 寬 in 欄寬.items():
        ws4.column_dimensions[col].width = 寬
    
    # 儲存
    excel_buf = BytesIO()
    wb.save(excel_buf)
    excel_buf.seek(0)
    
    return excel_buf.getvalue()
