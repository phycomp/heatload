from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

thin_border = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)
# ============================================================
# 工作表 2: 參數設定
# ============================================================
def 參數設定(wb):
  ws2 = wb.create_sheet("參數設定")

  ws2.column_dimensions['A'].width = 5
  ws2.column_dimensions['B'].width = 30
  ws2.column_dimensions['C'].width = 20
  ws2.column_dimensions['D'].width = 20
  ws2.column_dimensions['E'].width = 40

  # 標題
  ws2['B2'] = "⚙️ 參數設定"
  ws2['B2'].font = Font(size=16, bold=True, color="1F4E78")
  ws2.merge_cells('B2:E2')
  ws2['B2'].alignment = Alignment(horizontal='center')
  ws2.row_dimensions[2].height = 30

  # 通用常數
  ws2['B4'] = "通用常數"
  ws2['B4'].font = Font(size=13, bold=True, color="C00000")
  ws2['B4'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")

  constants = [
      ("Lorenz 數 L₀", 2.45e-8, "W·Ω/K²", "普適常數"),
      ("Stefan-Boltzmann σ", 5.67e-8, "W/m²/K⁴", "輻射常數"),
  ]

  row = 5
  for name, val, unit, note in constants:
      ws2[f'B{row}'] = name
      ws2[f'C{row}'] = val
      ws2[f'C{row}'].number_format = '0.00E+00'
      ws2[f'D{row}'] = unit
      ws2[f'E{row}'] = note
      row += 1

  # Channel 結構
  ws2['B8'] = "Channel 結構"
  ws2['B8'].font = Font(size=13, bold=True, color="C00000")
  ws2['B8'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")

  channel_params = [
      ("中心導體線規", "36 AWG", "", "可選 32/34/36/38/40"),
      ("中心導體直徑", 0.127, "mm", "36 AWG 標準值"),
      ("中心導體截面積 A_center", 0.0127, "mm²", "π×(d/2)²"),
      ("外屏蔽/中心比", 4.0, "倍", "典型同軸線值"),
      ("Channel 總截面積 A_ch", 0.0635, "mm²", "A_center × (1 + 屏蔽比)"),
      ("等效並聯數", 5.0, "根", "總截面積/單根截面積"),
  ]

  row = 9
  for name, val, unit, note in channel_params:
      ws2[f'B{row}'] = name
      if isinstance(val, (int, float)):
          ws2[f'C{row}'] = val
          if isinstance(val, float) and val < 1:
              ws2[f'C{row}'].number_format = '0.0000'
          else:
              ws2[f'C{row}'].number_format = '0.0'
      else:
          ws2[f'C{row}'] = val
      ws2[f'D{row}'] = unit
      ws2[f'E{row}'] = note
      row += 1

  # 電阻率參數
  ws2['B16'] = "電阻率參數 (Ω·m)"
  ws2['B16'].font = Font(size=13, bold=True, color="C00000")
  ws2['B16'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")

  resistivity = [
      ("Ag ρ (300K)", 1.6e-8, "室溫純銀"),
      ("Ag ρ (50K-0.1K)", 1.5e-8, "低溫高 RRR 銀"),
      ("NbTi ρ (正常態)", 6.5e-7, "含銅穩定層等效"),
      ("CuNi ρ (Constantan)", 4.9e-7, "幾乎不隨溫度變化"),
      ("Al ρ (300K)", 2.7e-8, "純鋁"),
      ("Al ρ (50K)", 2.5e-8, "中溫"),
      ("Al ρ (4K, RRR~100)", 2.5e-9, "低溫高純鋁"),
  ]

  row = 17
  for name, val, note in resistivity:
      ws2[f'B{row}'] = name
      ws2[f'C{row}'] = val
      ws2[f'C{row}'].number_format = '0.00E+00'
      ws2[f'E{row}'] = note
      row += 1

  # Aluminum Shield 參數
  ws2['B25'] = "Aluminum Shield 參數"
  ws2['B25'].font = Font(size=13, bold=True, color="C00000")
  ws2['B25'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")

  shield_params = [
      ("Shield 厚度", 0.1, "mm", ""),
      ("Shield 外徑", 2.0, "mm", ""),
      ("Shield 內徑", 1.8, "mm", "外徑 - 2×厚度"),
      ("Shield 截面積", 0.597, "mm²", "π×(R²-r²)"),
      ("發射率 ε", 0.03, "", "拋光鋁表面"),
      ("Shield 段長度", 30.0, "cm", "輻射計算用"),
  ]

  row = 26
  for name, val, unit, note in shield_params:
      ws2[f'B{row}'] = name
      ws2[f'C{row}'] = val
      if val < 1:
          ws2[f'C{row}'].number_format = '0.000'
      else:
          ws2[f'C{row}'].number_format = '0.0'
      ws2[f'D{row}'] = unit
      ws2[f'E{row}'] = note
      row += 1

  # 套用邊框
  for row_cells in ws2.iter_rows(min_row=4, max_row=ws2.max_row, min_col=2, max_col=5):
      for cell in row_cells:
          cell.border = thin_border
          cell.alignment = Alignment(vertical='center')

  print("✅ 工作表 2: 參數設定 - 完成")
  return wb
