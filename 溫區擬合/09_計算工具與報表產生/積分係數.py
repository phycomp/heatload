import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# 1. 建立活頁簿並設定工作表
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Thermal Calculator"

# 強制開啟網格線顯示
ws.views.sheetView[0].showGridLines = True

# 2. 定義設計樣式與調色盤 (經典商務深藍)
NAVY_HEADER = "1F4E78"
ICE_BLUE = "D9E1F2"
LIGHT_GRAY = "F2F2F2"

font_title = Font(name="Calibri", size=16, bold=True, color="1F4E78")
font_section = Font(name="Calibri", size=12, bold=True, color="000000")
font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
font_body = Font(name="Calibri", size=11)
font_body_bold = Font(name="Calibri", size=11, bold=True)

fill_header = PatternFill(start_color=NAVY_HEADER, end_color=NAVY_HEADER, fill_type="solid")
fill_input = PatternFill(start_color=ICE_BLUE, end_color=ICE_BLUE, fill_type="solid")
fill_zebra = PatternFill(start_color=LIGHT_GRAY, end_color=LIGHT_GRAY, fill_type="solid")

align_right = Alignment(horizontal="right", vertical="center")
align_center = Alignment(horizontal="center", vertical="center")

thin_side = Side(border_style="thin", color="D9D9D9")
thick_bottom = Side(border_style="medium", color="000000")
border_cell = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
border_header = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thick_bottom)

# 3. 寫入大標題
ws["A1"] = "量子微波傳輸線熱負載與長度回推計算機 (Cri/oFlex 3 - 96 CH)"
ws["A1"].font = font_title
ws.row_dimensions[1].height = 25

# 4. 寫入區段一：核心幾何參數輸入
ws["A2"] = "核心幾何參數輸入"
ws["A2"].font = font_section

inputs = [
    ("基板總厚度 (mm)", 0.3),
    ("單通道分攤間距 Pitch (mm)", 1.0),
    ("內部導體層厚度 (um)", 2.0),
    ("內部導體線寬 (mm)", 0.1),
    ("通道總數 (Channels)", 96)
]

for idx, (label, val) in enumerate(inputs, start=3):
    ws[f"A{idx}"] = label
    ws[f"A{idx}"].font = font_body
    ws[f"B{idx}"] = val
    ws[f"B{idx}"].font = font_body_bold
    ws[f"B{idx}"].fill = fill_input
    ws[f"B{idx}"].alignment = align_right
    ws[f"A{idx}"].border = border_cell
    ws[f"B{idx}"].border = border_cell

# 5. 寫入區段二：截面積自動聯動公式
ws["A9"] = "Polyimide 截面積 A_poly (m^2)"
ws["A9"].font = font_body
ws["B9"] = "=B3/1000*B4/1000"
ws["B9"].font = font_body_bold
ws["B9"].alignment = align_right
ws["B9"].number_format = '0.00E+00'
ws["A9"].border = border_cell
ws["B9"].border = border_cell

ws["A10"] = "金屬導體截面積 A_cond (m^2)"
ws["A10"].font = font_body
ws["B10"] = "=B5/1000000*B6/1000"
ws["B10"].font = font_body_bold
ws["B10"].alignment = align_right
ws["B10"].number_format = '0.00E+00'
ws["A10"].border = border_cell
ws["B10"].border = border_cell

# 6. 寫入區段三：主要熱傳導模型表格
ws["A12"] = "各溫區熱傳導與物理長度回推模型"
ws["A12"].font = font_section

headers = [
    "溫度區段 (Th -> Tl)", "圖中熱負載 P (W/CH)", "材質型號", 
    "Polyimide 積分 (W/m)", "導體層積分 (W/m)", 
    "等效導熱因子 (W/K)", "回推物理長度 L (cm)", "96CH 總靜態熱負載 (W)"
]

for col_idx, text in enumerate(headers, start=1):
    cell = ws.cell(row=13, column=col_idx, value=text)
    cell.font = font_header
    cell.fill = fill_header
    cell.alignment = align_center
    cell.border = border_header
ws.row_dimensions[13].height = 25

# 各溫層底層數據庫資料
# 格式: (溫區標籤, 圖中熱負載瓦特值, 材質名稱, 基材定積分值, 導體定積分值, 是否填斑馬紋)
table_data = [
    ("300K -> 50K", 0.0027, "純銀 (Ag)", 27.91, 95000, False),
    ("50K -> 4K", 0.0008, "純銀 (Ag)", 1.91, 17493.6, True),
    ("4K -> 0.6K (Still)", 0.0000054, "純銀 (Ag)", 0.0357, 6.256, False),
    ("4K -> 0.6K (Still)", 0.00000054, "鈮鈦 (NbTi)", 0.0357, 0.051, True),
    ("0.6K -> 0.1K (Cold)", 0.00000029, "純銀 (Ag)", 0.000599, 0.14, False),
    ("0.6K -> 0.1K (Cold)", 0.000000029, "鈮鈦 (NbTi)", 0.000599, 0.000172, True),
    ("100mK -> 10mK (MXC)", 0.0000000059, "純銀 (Ag)", 0.00000487, 0.00396, False),
    ("100mK -> 10mK (MXC)", 0.00000000059, "鈮鈦 (NbTi)", 0.00000487, 0.000000799, True),
]

for i, row_data in enumerate(table_data, start=14):
    ws.cell(row=i, column=1, value=row_data[0]).alignment = align_center
    
    p_cell = ws.cell(row=i, column=2, value=row_data[1])
    p_cell.number_format = '0.00E+00'
    p_cell.alignment = align_right
    
    ws.cell(row=i, column=3, value=row_data[2]).alignment = align_center
    
    poly_cell = ws.cell(row=i, column=4, value=row_data[3])
    poly_cell.number_format = '0.00E+00'
    poly_cell.alignment = align_right
    
    cond_cell = ws.cell(row=i, column=5, value=row_data[4])
    cond_cell.number_format = '0.00E+00'
    cond_cell.alignment = align_right
    
    # 填入內置運算公式
    f_cell = ws.cell(row=i, column=6, value=f"=($B$9*D{i})+($B$10*E{i})")
    f_cell.number_format = '0.00E+00'
    f_cell.alignment = align_right
    
    l_cell = ws.cell(row=i, column=7, value=f"=F{i}/B{i}*100")
    l_cell.number_format = '0.0'
    l_cell.alignment = align_right
    
    tot_cell = ws.cell(row=i, column=8, value=f"=B{i}*$B$7")
    tot_cell.number_format = '0.00E+00'
    tot_cell.alignment = align_right
    
    # 整體儲存格基礎樣式優化
    for col_idx in range(1, 9):
        c = ws.cell(row=i, column=col_idx)
        c.font = font_body
        c.border = border_cell
        if row_data[5]:
            c.fill = fill_zebra

# 7. 自適應動態調配欄寬 (避免文字截斷或出現 ###)
ws.column_dimensions['A'].width = 32
ws.column_dimensions['B'].width = 22
ws.column_dimensions['C'].width = 15
ws.column_dimensions['D'].width = 22
ws.column_dimensions['E'].width = 22
ws.column_dimensions['F'].width = 22
ws.column_dimensions['G'].width = 22
ws.column_dimensions['H'].width = 24

# 8. 儲存成品
file_name = "Quantum_Microwave_Stripline_Thermal_Calculator.xlsx"
wb.save(file_name)
print(f"成功匯出！檔案已儲存為: {file_name}")
