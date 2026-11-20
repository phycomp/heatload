import pandas as pd
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.chart import BarChart, Reference, LineChart
import io

# ============================================================
# 建立 Excel 檔案
# ============================================================

# 建立工作簿
wb = Workbook()

# ============================================================
# 工作表 1: 封面與說明
# ============================================================
ws1 = wb.active
ws1.title = "封面說明"

# 設定欄寬
ws1.column_dimensions['A'].width = 5
ws1.column_dimensions['B'].width = 25
ws1.column_dimensions['C'].width = 60

# 標題
ws1['B2'] = "🔬 低溫傳輸線熱負載模擬計算系統"
ws1['B2'].font = Font(size=20, bold=True, color="1F4E78")
ws1.merge_cells('B2:C2')
ws1['B2'].alignment = Alignment(horizontal='center', vertical='center')
ws1.row_dimensions[2].height = 35

ws1['B4'] = "版本: v2.0 (修正版)"
ws1['B4'].font = Font(size=12, italic=True, color="666666")
ws1['B5'] = "日期: 2026-05-26"
ws1['B5'].font = Font(size=12, italic=True, color="666666")

# 核心修正說明
ws1['B7'] = "📌 核心修正"
ws1['B7'].font = Font(size=14, bold=True, color="C00000")
ws1['C7'] = "正確理解 'per channel' = 整個同軸通道 (中心導體 + 外屏蔽層)，非單根 AWG36 線"
ws1['C7'].font = Font(size=11, color="C00000")

# 工作表導航
ws1['B9'] = "📋 工作表導航"
ws1['B9'].font = Font(size=14, bold=True, color="1F4E78")

sheets_info = [
    ("計算結果", "各溫度段熱負載與回推長度計算結果"),
    ("參數設定", "可調整的物理參數與材料屬性"),
    ("CuNi比較", "CuNi 與 Ag 的等效長度比較"),
    ("Al Shield", "Aluminum Shielding 熱傳導與輻射分析"),
    ("物理推導", "Wiedemann-Franz 定律完整推導過程"),
    ("等效熱阻", "4K 以下等效熱阻長度概念說明"),
]

row = 10
for sheet_name, desc in sheets_info:
    ws1[f'B{row}'] = sheet_name
    ws1[f'B{row}'].font = Font(size=11, bold=True, color="0070C0")
    ws1[f'C{row}'] = desc
    ws1[f'C{row}'].font = Font(size=10)
    row += 1

# 公式說明
ws1['B17'] = "📐 核心公式"
ws1['B17'].font = Font(size=14, bold=True, color="1F4E78")

formulas = [
    ("Wiedemann-Franz Law", "λ = L₀ · T / ρ(T)"),
    ("熱傳導積分", "Q = (L₀·A / L·ρ) · (Tₕ² - Tc²) / 2"),
    ("反推長度", "L = L₀ · A_channel · (Tₕ² - Tc²) / (2 · Q · ρ)"),
    ("熱輻射", "Q_rad = ε · σ · A_surf · (Tₕ⁴ - Tc⁴)"),
]

row = 18
for name, formula in formulas:
    ws1[f'B{row}'] = name
    ws1[f'B{row}'].font = Font(size=10, bold=True)
    ws1[f'C{row}'] = formula
    ws1[f'C{row}'].font = Font(size=10, name='Consolas')
    row += 1

# 邊框樣式
thin_border = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)

wb.save('功能.xlsx')
print("✅ 工作表 1: 封面說明 - 完成")
