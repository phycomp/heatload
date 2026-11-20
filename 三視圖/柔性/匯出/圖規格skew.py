# 柔性線函式庫/匯出/Excel.py
"""匯出 Excel 規格書 - 含全規格、Skew、Clearance"""

from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter

from 核心.層FPC import 全層, 計算CableWidth
from 驗證.規格基準 import 取得原廠規格
from 驗證.電氣計算skew import 計算Skew, 計算Clearance


def 全規格(佈局, 規格類型):
    """建立完整規格表格 (仿照 CF3)"""
    規格 = []
    # 原廠規格 = 取得原廠規格(佈局.規格類型)

    # ===== 一般規格 =====
    一般規格 = [
        ["一般規格", "產品名稱", "U-leam FPC", "", "仿照 Delft Circuits", ""],
        ["一般規格", "規格類型", 佈局.規格名稱, "", "", ""],
        ["一般規格", "通道數", 佈局.通道數, "ch", "並列通道", "±0.5"],
        # ["一般規格", "訊號間距", 佈局.訊號間距um, "μm", "標準設計", "±0.05"],
        ["一般規格", "總寬度", f"{佈局.線總寬:.3f}", "mm", '8×W1 + 8×D1×2 + 9×GND', "±0.1"],  #f"{佈局.通道數}ch × {佈局.訊號間距um}um"
        ["一般規格", "總厚度", f"{佈局.線總厚um:.1f}", "μm", f"{len(佈局.規格層)}層結構", "±5"],
        ["一般規格", "線長度", 佈局.線總長, "mm", "可客製化", "±1"],
        ["一般規格", "訊號寬度", 佈局.訊號寬度um, "μm", "W1", "±2"],
        ["一般規格", "訊號間距", 佈局.訊號間距um, "μm", "訊號中心與訊號中心距離", "±2"],
        ["一般規格", "最小彎曲半徑", 5., "mm", "動態彎曲", "-0/+1"],  #if 規格類型 == 'FPC' else 5
    ]
    規格.extend(一般規格)

    # ===== FPC 專屬：Cable Width =====
    if 規格類型 == 'FPC':
        cw = 計算CableWidth()
        規格.extend([
            ["Cable Width", "Ground Space", cw['GroundSpace'], "μm", "接地間距", "±5"],
            ["Cable Width", "W1", cw['W1'], "μm", "訊號寬度", "±2"],  # (訊號寬度)
            ["Cable Width", "D1", cw['D1'], "μm", "訊號單側間距", "±5"],  # (訊號單側間距)
            # ["Cable Width", "Cable Width", f"{cw['cable_width_mm']:.3f}", "mm", "8×W1 + 8×D1×2 + 9×GND", "±0.1"],
            ["Cable Width", "Pitch (SMPM)", f"{cw['Pitch_SMPM_mm']:.3f}", "mm", "連接器間距", "±0.05"],
        ])

    # ===== 層結構 =====
    for 層 in 佈局.規格層:
        規格.append(["層結構", 層['名稱'], 層['厚度um'], "μm", 層['材料'], "±2"])

    # ===== FPC 專屬：H1/H2 =====
    if 規格類型 == 'FPC':
        pass
        #規格.extend([
        #    ["層結構", "H1 (L1→L2)", f"{佈局.H1:.1f}", "μm", "L1 到 L2 中心距離", "±2"],
        #    ["層結構", "H2 (L2→L3)", f"{佈局.H2:.1f}", "μm", "L2 到 L3 中心距離", "±2"],
        #])

    # ===== 電氣規格 =====
    材料 = 'NbTi' if 規格類型 == 'FPC' else 'Ag'
    IL2G=1.5 if 規格類型 == 'FPC' else 2.0  #"插入損耗 @2GHz",
    IL6G=3.0 if 規格類型 == 'FPC' else 5.0  #"插入損耗 @6GHz",
    IL12G=5.0 if 規格類型 == 'FPC' else 9.0 #"插入損耗 @12GHz",
    IL18G=8.0 if 規格類型 == 'FPC' else 16.0  #"插入損耗 @18GHz",
    #頻率	α (dB/m)	總損耗 (dB) @ 150mm
    #2 GHz	0.52	0.078 dB
    #6 GHz	1.56	0.234 dB
    #12 GHz	3.13	0.470 dB
    #18 GHz	4.69	0.704 dB
    #RL2G=.52 #"回波損耗 @2GHz",
    #RL6G=1.56 #"回波損耗 @6GHz",
    #RL12G=3.13 #"回波損耗 @12GHz",
    #RL18G=4.69 #"回波損耗 @18GHz",
    總線長=佈局.線總長/1000
    電氣規格 = [
        ["電氣規格", "特性阻抗", 50, "Ω", "帶狀線設計", "±5"],
        ["電氣規格", "工作頻率", "DC ~ 10", "GHz", "微波操作", ""],
        #["電氣規格", "插入損耗 @2GHz", 1.5 if 規格類型 == 'FPC' else 2.0, "dB/m", f"{材料} @4K", "±0.5"],
        #["電氣規格", "插入損耗 @6GHz", 3.0 if 規格類型 == 'FPC' else 5.0, "dB/m", f"{材料} @4K", "±1"],
        #["電氣規格", "插入損耗 @12GHz", 5.0 if 規格類型 == 'FPC' else 9.0, "dB/m", f"{材料} @4K", "±1.5"],
        #["電氣規格", "插入損耗 @18GHz", 8.0 if 規格類型 == 'FPC' else 16.0, "dB/m", f"{材料} @4K", "±2"],
        ["電氣規格", "插入損耗 @2GHz", f'{IL2G*總線長:.01f}', 'dB', f"{IL2G} dB/m|{材料} @4K", "±0.5"],
        ["電氣規格", "插入損耗 @6GHz", f'{IL6G*總線長:.01f}', 'dB', f"{IL6G} dB/m|{材料} @4K", "±1"],
        ["電氣規格", "插入損耗 @12GHz", f'{IL12G*總線長:.01f}', 'dB', f"{IL12G} dB/m|{材料} @4K", "±1.5"],
        ["電氣規格", "插入損耗 @18GHz", f'{IL18G*總線長:.01f}', 'dB', f"{IL18G} dB/m|{材料} @4K", "±2"],
        ["電氣規格", "遠端串擾", -60 if 規格類型 == 'FPC' else -40, "dB", f"L={佈局.線總長:.0f}mm", ""],
        #["電氣規格", "回波損耗 @2GHz", f'{RL2G*總線長:.02f}', "dB", f"{RL2G} dB/m|{材料} @4K", "SPMP"],
        #["電氣規格", "回波損耗 @6GHz", f'{RL6G*總線長:.02f}', "dB", f"{RL6G} dB/m|{材料} @4K", "SPMP"],
        #["電氣規格", "回波損耗 @12GHz", f'{RL12G*總線長:.02f}', "dB", f"{RL12G} dB/m|{材料} @4K", "SPMP"],
        #["電氣規格", "回波損耗 @18GHz", f'{RL18G*總線長:.02f}', "dB", f"{RL18G} dB/m|{材料} @4K", "SPMP"],
        ["電氣規格", "傳播延遲", 5.6, "ns/m", "√εᵣ / c₀", "±0.3"],
        ["電氣規格", "相位匹配", 10 if 規格類型 == 'FPC' else 15, "ps", "< 10/15", ""],
    ]
    # Skew 計算
    skew = 計算Skew(佈局, 10, 佈局.線總長)
    電氣規格.append(["電氣規格", "Skew (通道間)", f"{skew['計算結果'].replace(' ps', '')}", "ps", "< 5", ""])

    規格.extend(電氣規格)

    # ===== 熱性能 =====
    熱性能 = [
        ["熱性能", "工作溫區", "100 ~ 40", "K", "從100K至40K", ""],
        # ["熱性能", "熱負載 (Ag)", "< 125", "μW/ch", "@ΔT 10-350mK, L=0.2m", ""],
        ["熱性能", "熱負載 (NbTi)", "~ 20", "nW/ch", f"@ΔT 100K-40K, L={佈局.線總長:.0f}mm", ""],
        ["熱性能", "熱導率 (PI)", 0.12, "W/m·K", "@300K", "±0.02"],
        ["熱性能", "熱膨脹係數 (PI)", 20, "ppm/K", "CTE", "±5"],
    ]
    規格.extend(熱性能)

    # ===== 機械規格 =====
    機械規格 = [
        ["機械規格", "連接器", "SMPM", "-", "兩端", ""],
        ["機械規格", "最大拉伸力", "> 50", "N", "軸向拉力", ""], #if 規格類型 == 'GSG' else "> 30"
        ["機械規格", "真空洩漏率", "< 10⁻⁹", "mbar·L/s", "整合式穿通", ""],
        ["機械規格", "彎曲壽命", "> 1000", "cycles", "R=5mm", ""],  # if 規格類型 == 'FPC' else "R=3mm"
        ["機械規格", "楊氏模量 (PI)", 2.5, "GPa", "", ""],
        ["機械規格", "密度 (PI)", 1.42, "g/cm³", "", ""],
    ]
    規格.extend(機械規格)

    # ===== 材質規格 =====
    材質規格 = [
        ["材質規格", "導體材料", "NbTi" if 規格類型 == 'FPC' else "Ag/NbTi", "-", f"比例 {佈局.鈮鈦比例}", ""],
        ["材質規格", "介電材料", "PI / PI glue" if 規格類型 == 'FPC' else "Polyimide", "-", "低損耗", ""],
        ["材質規格", "保護層材料", "PI / AD" if 規格類型 == 'FPC' else "Polyimide", "-", "覆蓋層", ""],
        ["材質規格", "鈮鈦比例", 佈局.鈮鈦比例, "%", "Nb:Ti 比例", "±1"],
        ["材質規格", "PI DK", 3.3, "-", "介電常數", "±0.1"],
        ["材質規格", "PI DF", ".004-.0077", "-", "損耗正切", ""],
        ["材質規格", "PI glue DK", 3.5, "-", "介電常數", "±.1"],
        ["材質規格", "PI glue DF", .005, "-", "損耗正切", "±.001"],
        ["材質規格", "AD DK", 3.5, "-", "介電常數", "±.2"],
        ["材質規格", "AD DF", .01, "-", "損耗正切", "±.002"],
    ]
    規格.extend(材質規格)

    # ===== 間隙規格 (Clearance) =====
    # clearance = 計算Clearance(佈局, 規格類型)
    # for 項目, 值 in clearance.items():
        # 規格.append(["間隙規格", 項目, 值, "μm" if isinstance(值, (int, float)) else "", "", ""])
    間隙規格=[
        ["間隙規格", 'Ground space', 100, "μm", '', ''],
        ["間隙規格", 'D1 (訊號單側間距)', 171, "μm", '', ''],
        ["間隙規格", '線邊緣空白', 100, "μm", '', ''],
        ["間隙規格", '層間隙 (H1)', 62.5, "μm", '', ''],
        ["間隙規格", '層間隙 (H2)', 50.2, "μm", '', ''],
        ["間隙規格", 'PTH 直徑', 15, "μm",  '10~20', ''],
    ]
    規格.extend(間隙規格)

    return 規格


def 匯出分頁(佈局, 規格類型, 前視圖, 側視圖, 上視圖, 字型縮放=1.0):
    """匯出完整 Excel 規格書"""

    wb = openpyxl.Workbook()

    # 定義樣式
    標題填色 = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    標題字型 = Font(color="FFFFFF", bold=True, size=12)
    細邊框 = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )

    # ===== Sheet 1: 全規格表 =====
    ws1 = wb.active
    ws1.title = "全規格表"

    ws1.merge_cells('A1:F1')
    cell = ws1['A1']
    cell.value = f"U-leam UF1 柔性讀取傳輸線全規格書 - {佈局.規格名稱}"
    cell.font = Font(size=16, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 35

    ws1.merge_cells('A2:F2')
    cell = ws1['A2']
    #cell.value = (f"通道數: {佈局.通道數}ch | 訊號間距: {佈局.訊號間距um}μm | "
    #              f"總寬: {佈局.線總寬um:.3f}μm | 總厚度: {佈局.線總厚um:.1f}μm")
    cell.value =(f"通道數: {佈局.通道數}ch | 訊號間距: {佈局.訊號間距um}μm | 線總寬: {佈局.線總寬um:.3f}μm | 線總厚: {佈局.線總厚um:.1f}μm")
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

    from streamlit import empty, pyplot
    狀態=empty()
    # 填入全規格
    規格資料 = 全規格(佈局, 規格類型)
    for 項目 in 規格資料:
        狀態.code(項目)
        values = [項目[0], 項目[1], 項目[2], 項目[3], 項目[4], 項目[5]]
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
    欄寬 = {'A': 14, 'B': 22, 'C': 18, 'D': 12, 'E': 35, 'F': 12}
    for col, 寬 in 欄寬.items():
        ws1.column_dimensions[col].width = 寬

    # ===== Sheet 2: 前視圖 =====
    ws2 = wb.create_sheet("前視圖")
    ws2.merge_cells('A1:E1')
    cell = ws2['A1']
    cell.value = f"前視截面 ({佈局.通道數} 通道) - {佈局.規格名稱}"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 30

    ws2.merge_cells('A2:E2')
    cell = ws2['A2']
    cell.value = f"{len(佈局.規格層)}層疊構 | 材料: {'NbTi' if 規格類型 == 'FPC' else 'Ag/NbTi'} ({佈局.鈮鈦比例}) | 寬度: {佈局.線總寬:.3f}mm"
    cell.font = Font(size=10, italic=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[2].height = 25

    front_buf = BytesIO()
    前視圖.savefig(front_buf, format='png', dpi=150, facecolor='#0D1117', edgecolor='none', bbox_inches='tight')
    front_buf.seek(0)

    #img_front = XLImage(front_buf)
    #img_front.width = 900
    #img_front.height = 600
    #ws2.add_image(img_front, 'A4')

    for col in range(1, 6):
        ws2.column_dimensions[get_column_letter(col)].width = 20

    # ===== Sheet 3: 側視圖 =====
    ws3 = wb.create_sheet("側視圖")
    ws3.merge_cells('A1:E1')
    cell = ws3['A1']
    cell.value = f"側視圖 ({佈局.通道數} 通道) - {佈局.規格名稱}"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws3.row_dimensions[1].height = 30

    ws3.merge_cells('A2:E2')
    cell = ws3['A2']
    cell.value = f"長度: {佈局.線總長}mm | 彎曲半徑: {5 if 規格類型 == 'GSG' else 3}mm | 連接器: SMA/SMP"
    cell.font = Font(size=10, italic=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws3.row_dimensions[2].height = 25

    side_buf = BytesIO()
    側視圖.savefig(side_buf, format='png', dpi=150, facecolor='#0D1117',
                  edgecolor='none', bbox_inches='tight')
    side_buf.seek(0)

    img_side = XLImage(side_buf)
    img_side.width = 900
    img_side.height = 450
    ws3.add_image(img_side, 'A4')

    for col in range(1, 6):
        ws3.column_dimensions[get_column_letter(col)].width = 20

    # ===== Sheet 4: 上視圖 =====
    ws4 = wb.create_sheet("上視圖")
    ws4.merge_cells('A1:E1')
    cell = ws4['A1']
    cell.value = f"上視圖 ({佈局.通道數} 通道) - {佈局.規格名稱}"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws4.row_dimensions[1].height = 30

    ws4.merge_cells('A2:E2')
    cell = ws4['A2']
    cell.value = f"寬度: {佈局.線總寬:.3f}mm | Pitch: {佈局.訊號間距um}μm | 鈮鈦比例: {佈局.鈮鈦比例}"
    cell.font = Font(size=10, italic=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws4.row_dimensions[2].height = 25

    top_buf = BytesIO()
    上視圖.savefig(top_buf, format='png', dpi=150, facecolor='#0D1117',
                  edgecolor='none', bbox_inches='tight')
    top_buf.seek(0)

    img_top = XLImage(top_buf)
    img_top.width = 900
    img_top.height = 500
    ws4.add_image(img_top, 'A4')

    for col in range(1, 6):
        ws4.column_dimensions[get_column_letter(col)].width = 20

    # ===== Sheet 5: 層疊結構 =====
    ws5 = wb.create_sheet("層疊結構")
    ws5.merge_cells('A1:F1')
    cell = ws5['A1']
    cell.value = f"{len(佈局.規格層)}層疊構詳述 - {佈局.規格名稱}"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws5.row_dimensions[1].height = 30

    row = 3
    表頭 = ["層號", "層名稱", "材料", "DK", "DF", "厚度 (μm)", "功能"]
    for col, 標題 in enumerate(表頭, 1):
        cell = ws5.cell(row=row, column=col, value=標題)
        cell.font = 標題字型
        cell.fill = 標題填色
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = 細邊框
    ws5.row_dimensions[row].height = 25
    row += 1

    層顏色 = {
        '保護': 'E8D5C4', 'Coverlay': 'E8D5C4',
        '接地': '8B9CAD', 'L1': '8B9CAD', 'L3': '8B9CAD',
        '介電': 'C4956A', 'PI': 'C4956A',
        '訊號': 'FFD700', 'L2': 'FFD700',
        'PTH': 'B87333',
    }

    for i, 層 in enumerate(佈局.規格層, 1):
        功能 = '訊號傳輸' if 層['是訊號層'] else ('接地/屏蔽' if '接地' in 層['名稱'] or 'L1' in 層['名稱'] or 'L3' in 層['名稱'] else '絕緣/保護')

        # 判斷顏色
        顏色 = 'FFFFFF'
        for key, val in 層顏色.items():
            if key in 層['名稱']:
                顏色 = val
                break

        values = [i, 層['名稱'], 層['材料'], 層.get('DK', '-'), 層.get('DF', '-'), 層['厚度um'], 功能]
        for col, value in enumerate(values, 1):
            cell = ws5.cell(row=row, column=col, value=value)
            cell.border = 細邊框
            cell.alignment = Alignment(horizontal="center" if col <= 5 else "left",
                                      vertical="center", wrap_text=True)
            if 顏色 != 'FFFFFF' and col <= 3:
                cell.fill = PatternFill(start_color=顏色, end_color=顏色, fill_type="solid")
        row += 1

    # 總計
    總厚度 = sum(層['厚度um'] for 層 in 佈局.規格層)
    values = ["總計", "-", "-", "-", "-", 總厚度, "-"]
    for col, value in enumerate(values, 1):
        cell = ws5.cell(row=row, column=col, value=value)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = 細邊框

    欄寬 = {'A': 8, 'B': 22, 'C': 12, 'D': 8, 'E': 12, 'F': 12, 'G': 20}
    for col, 寬 in 欄寬.items():
        ws5.column_dimensions[col].width = 寬

    # ===== Sheet 6: Cable Width (FPC 專屬) =====
    if 規格類型 == 'FPC':
        ws6 = wb.create_sheet("Cable Width")
        ws6.merge_cells('A1:D1')
        cell = ws6['A1']
        cell.value = "Cable Width 計算明細"
        cell.font = Font(size=14, bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        ws6.row_dimensions[1].height = 30

        cw = 計算CableWidth()

        row = 3
        表頭 = ["項目", "計算式", "數值 (μm)", "備註"]
        for col, 標題 in enumerate(表頭, 1):
            cell = ws6.cell(row=row, column=col, value=標題)
            cell.font = 標題字型
            cell.fill = 標題填色
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = 細邊框
        row += 1

        calc_items = [
            ["Ground Space", "-", cw['GroundSpace'], "接地間距"],
            ["line: W1", "-", cw['W1'], "訊號線寬度"],
            ["space: D1", "-", cw['D1'], "相鄰通道間距"],
            ["8 × W1", "8 × W1", cw['8*W1'], "8條線寬總和"],
            ["8 × D1 × 2", "8 × D1 × 2", cw['8*D1*2'], "8個間距×2"],
            ["8W1 + 8×D1×2", "520 + 2736", cw['8*W1'] + cw['8*D1*2'], "線寬+間距"],
            ["9 × Ground space", "9 × GND", cw['9*Ground space'], "9個接地間距"],
            ["Cable Width", "3256 + 900", cw['cable_width_um'], "總寬度"],
            ["1×W1 + 2×D1 + GND", "65 + 342 + 100", cw['W1'] + 2*cw['D1'] + cw['GroundSpace'], "單通道寬度"],
            ["Pitch (SMPM)", "-", cw['Pitch_SMPM_um'], "連接器間距"],
        ]

        for item in calc_items:
            for col, value in enumerate(item, 1):
                cell = ws6.cell(row=row, column=col, value=value)
                cell.border = 細邊框
                cell.alignment = Alignment(horizontal="center" if col <= 3 else "left")
                if item[0] == "Cable Width":
                    cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                    cell.font = Font(bold=True)
            row += 1

        欄寬 = {'A': 22, 'B': 20, 'C': 15, 'D': 20}
        for col, 寬 in 欄寬.items():
            ws6.column_dimensions[col].width = 寬

    # 儲存
    excel_buf = BytesIO()
    wb.save(excel_buf)
    excel_buf.seek(0)

    return excel_buf.getvalue()


def 建立層疊表格(佈局, 規格類型='GSG'):
    """建立層疊結構資料"""
    # 層定義 = 取得層定義(規格類型)
    層定義=佈局.規格層

    層疊 = []
    for i, 層 in enumerate(層定義, 1):
        功能 = '訊號傳輸' if 層['是訊號層'] else ('接地/屏蔽' if '接地' in 層['名稱'] or 'L1' in 層['名稱'] or 'L3' in 層['名稱'] else '絕緣/保護')
        層疊.append({
            '層號': i,
            '層名稱': 層['名稱'],
            '材料': 層['材料'],
            'DK': 層.get('DK', '-'),
            'DF': 層.get('DF', '-'),
            '厚度um': 層['厚度um'],
            '厚度mm': 層['厚度um'] / 1000,
            '功能': 功能
        })

    總厚度um = sum(層['厚度um'] for 層 in 層定義)
    層疊.append({
        '層號': '總計', '層名稱': '-', '材料': '-', 'DK': '-', 'DF': '-',
        '厚度um': 總厚度um, '厚度mm': 總厚度um / 1000, '功能': '-'
    })
    return 層疊
