# 柔性線函式庫/匯出/Excel.py
"""匯出 Excel 規格書"""

from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter


def 建立規格表格(佈局):
    """建立完整規格資料表格 (與規格資框一致，約40+項)"""
    規格 = []
    
    # ===== 一般規格 =====
    一般規格 = [
        ["一般規格", "產品名稱", f"{佈局.線情境}", "U-leam UF1", "仿照 Delft Circuits", ""],
        ["一般規格", "通道數", 佈局.通道數, "ch", "並列通道", "±0.5"],
        ["一般規格", "通道間距", 佈局.訊號間距, "mm", "通道中心至中心", "±0.05"],
        ["一般規格", "總寬度", f"{佈局.線總寬:.1f}", "mm", f"{佈局.通道數-1}ch × {佈局.訊號間距}+訊號寬+2*邊緣寬", "±0.1"],
        ["一般規格", "總厚度", 佈局.總厚度um, "μm", "7層 GSG 結構", "±5"],
        ["一般規格", "線長度", 佈局.線長度, "mm", "可客製化", "±1"],
        ["一般規格", "線邊緣空白", f"{佈局.邊緣間距:.3f}", "mm", "符合5W/10H規則", ""],
        ["一般規格", "最小彎曲半徑", 5, "mm", "動態彎曲", "-0/+1"],
        ["", "", "", "", "", ""],
    ]
    規格.extend(一般規格)
    
    # ===== 電氣規格 =====
    電氣規格 = [
        ["電氣規格", "特性阻抗", 50, "Ω", "GSG 帶狀線設計", "±5"],
        ["電氣規格", "S參數掃描頻率範圍", "DC - 18", "GHz", "微波操作", ""],
        ["電氣規格", "插入損耗", "< .5", "dB/m", "@ 10GHz", ""],
        ["電氣規格", "回波損耗", "> 20", "dB", "@ 10GHz", ""],
        ["電氣規格", "串擾隔離(FEXT)", "< -60 @ 10GHz", "dB", "相鄰通道", ""],
        ["電氣規格", "串擾隔離(NEXT)", "< -60 @ 10GHz", "dB", "相鄰通道", ""],
        ["電氣規格", "傳播延遲(skew)", "15", "ps/m", f"ps@m", "±0.3"],
        ["", "", "", "", "", ""],
    ]
    規格.extend(電氣規格)
    
    # ===== 層結構規格 =====
    層結構規格 = [
        ["層結構", "保護層上", 15, "μm", "Polyimide", "±2"],
        ["層結構", "接地層上", 5, "μm", "NbTi", "±0.5"],  #Ag/
        ["層結構", "介電層上", 129, "μm", "Polyimide", "±3"],
        ["層結構", "訊號層厚度", f"{佈局.訊號厚度mm * 1000:.1f}", "μm", "NbTi", "±0.2"],  #Ag/
        ["層結構", "訊號層寬度", f"{佈局.訊號寬度mm * 1000:.0f}", "μm", "NbTi", "±2"],  #Ag/
        ["層結構", "介電層下", 129, "μm", "Polyimide", "±3"],
        ["層結構", "接地層下", 5, "μm", "NbTi", "±0.5"],  #Ag/
        ["層結構", "保護層下", 15, "μm", "Polyimide", "±2"],
        ["", "", "", "", "", ""],
    ]
    規格.extend(層結構規格)
    
    # ===== 材料規格 =====
    材料規格 = [
        ["材料規格", "導體材料", "NbTi", "-", f"比例 {佈局.鈮鈦比例}", ""], #Ag/
        ["材料規格", "介電材料", "Polyimide", "-", "低損耗", ""],
        ["材料規格", "保護層材料", "Polyimide", "-", "覆蓋層", ""],
        ["材料規格", "鈮鈦比例", 佈局.鈮鈦比例, "%", "Nb:Ti 比例", "±1"],
        ["材料規格", "鈮鈦超導相變溫度", f"{佈局.超導相變溫度}", "K", "超導相變溫度", "±0.1"],
        ["材料規格", "鈮鈦臨界電流密度", f"{佈局.超導臨界電流密度}", "A/cm²", f"@ {佈局.超導相變溫度}K, 5T", "±0.3 × 10⁵"],  #2.5 × 10⁵
        # ["材料規格", "導體電阻率 (Ag) @300K", 1.59, "μΩ·cm", "@ 300K", ""],
        # ["材料規格", "導體電阻率 (Ag) @4.2K", 0.3, "μΩ·cm", "@ 4.2K, RRR > 100", ""],
        ["材料規格", "導體電阻率 (NbTi) @300K", 50, "μΩ·cm", "@ 300K", ""],
        ["材料規格", "導體電阻率 (NbTi) @10K", 0.5, "μΩ·cm", "@ 10K, 正常態", ""],
        ["", "", "", "", "", ""],
    ]
    規格.extend(材料規格)
    
    # ===== 熱性能規格 =====
    熱性能規格 = [
        # ["熱性能", "熱負載", "< 125", "μW/ch", "@ 4-40K, L=0.2m", ""],  # (Ag)
        ["熱性能", "操作溫區", f"{佈局.操作溫區}", "K", "傳輸線操作溫區", ""],  #4K ~ 9.2K
        ["熱性能", "熱負載 (NbTi)", "≤ 20", "nW/ch", f"@{佈局.操作溫區}K, L={佈局.線長度}mm", ""], #4K-9.2
        ["熱性能", "工作溫度 (最低)", -40, "°C", "最低工作溫度", ""],
        ["熱性能", "工作溫度 (最高)", 85, "°C", "最高工作溫度", ""],
        ["", "", "", "", "", ""],
    ]
    規格.extend(熱性能規格)

    # ===== 機械規格 =====
    機械規格 = [
        # ["機械規格", "連接器類型", "SMA (f) / SMP (m)", "-", "直角/直線可選", ""],
        ["機械規格", "連接器類型", "SMPM(f)", "-", "兩端", ""],  #SMA,SMPM,SMP SMA/SMP 
        ["機械規格", "真空洩漏率", "< 10⁻⁶", "mbar·L/s", "整合式穿通", ""],
        ["機械規格", "彎曲壽命", "> 1000", "cycles", "R=5mm", ""],
        ["機械規格", "軸向拉伸強度", "> 50", "NT", "軸向拉力", ""],
        ["機械規格", "楊氏模量", 2.5, "GPa", "Polyimid", ""],
        ["機械規格", "密度", 1.42, "g/cm³", "Polyimide", ""],
    ]
    規格.extend(機械規格)
    
    return 規格


def 建立層疊表格(佈局):
    """建立層疊結構資料 (供預覽與匯出使用)"""
    from 核心.層 import 層定義
    
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
    
    # ============================================================
    # Sheet 1: 規格表 (完整規格，約40+項)
    # ============================================================
    ws1 = wb.active
    ws1.title = "規格表"
    
    # 標題
    ws1.merge_cells('A1:G1')
    cell = ws1['A1']
    cell.value = f"U-leam UF1 柔性傳輸線{佈局.線情境}規格書"
    cell.font = Font(size=16, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 35
    
    # 子標題
    ws1.merge_cells('A2:G2')
    cell = ws1['A2']
    cell.value = (f"通道數: {佈局.通道數}ch | 間距: {佈局.訊號間距}mm | "
                  f"總寬: {佈局.線總寬:.2f}mm | 邊緣間距: {佈局.邊緣間距*1000:.0f}um | "
                  f"鈮鈦比例: {佈局.鈮鈦比例}")
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
    
    # 填入完整規格 (使用建立規格表格函數)
    規格資料 = 建立規格表格(佈局)
    for 項目 in 規格資料:
        values = [項目[0], 項目[1], 項目[2], 項目[3], 項目[4], 項目[5]]
        for col, value in enumerate(values, 1):
            cell = ws1.cell(row=row, column=col, value=value)
            cell.border = 細邊框
            cell.alignment = Alignment(horizontal="center" if col <= 2 else "left", 
                                      vertical="center", wrap_text=True)
            if col == 1 and value:
                cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
                cell.font = Font(bold=True)
        row += 1
    
    # 設定列寬
    欄寬 = {'A': 14, 'B': 22, 'C': 18, 'D': 12, 'E': 35, 'F': 12}
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
    cell.value = f"GSG 7層疊構 | 材料: NbTi ({佈局.鈮鈦比例}) | 寬度: {佈局.線總寬:.2f}mm"  #Ag/
    cell.font = Font(size=10, italic=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[2].height = 25
    
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
    cell.value = f"七層疊構詳述 (NbTi {佈局.鈮鈦比例})"   #Ag/
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
