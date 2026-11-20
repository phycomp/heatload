from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from streamlit import session_state
thin_border=session_state['thin_border']

def CuNi比較(wb):
# ============================================================
# 工作表 4: CuNi 比較
# ============================================================
  ws4 = wb.create_sheet("CuNi比較")

  ws4.column_dimensions['A'].width = 3
  ws4.column_dimensions['B'].width = 20
  ws4.column_dimensions['C'].width = 18
  ws4.column_dimensions['D'].width = 18
  ws4.column_dimensions['E'].width = 18
  ws4.column_dimensions['F'].width = 18
  ws4.column_dimensions['G'].width = 25

  # 標題
  ws4['B2'] = "🔁 CuNi (Constantan) 取代 Ag 等效計算"
  ws4['B2'].font = Font(size=16, bold=True, color="1F4E78")
  ws4.merge_cells('B2:G2')
  ws4['B2'].alignment = Alignment(horizontal='center')
  ws4.row_dimensions[2].height = 30

  # 推導說明
  ws4['B4'] = "推導過程"
  ws4['B4'].font = Font(size=13, bold=True, color="C00000")
  ws4['B4'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")

  derivation = [
      ("已知條件", "相同熱負載 Q，相同溫度段 (Th, Tc)"),
      ("", ""),
      ("Step 1", "L = L₀ · A · (Th² - Tc²) / (2 · Q · ρ)"),
      ("", "對於相同 Q, A, Th, Tc："),
      ("Step 2", "L_CuNi / L_Ag = ρ_CuNi / ρ_Ag"),
      ("", ""),
      ("代入數值", "ρ_CuNi = 4.9 × 10⁻⁷ Ω·m"),
      ("", "ρ_Ag = 1.5 × 10⁻⁸ Ω·m"),
      ("", ""),
      ("Step 3", "L_CuNi / L_Ag = 4.9×10⁻⁷ / 1.5×10⁻⁸ = 32.7"),
      ("", ""),
      ("結論", "相同熱負載下，CuNi 長度需為 Ag 的 ~33 倍"),
      ("", "或：相同長度下，CuNi 熱負載僅為 Ag 的 ~3%"),
  ]

  row = 5
  for label, content in derivation:
      ws4[f'B{row}'] = label
      ws4[f'B{row}'].font = Font(bold=True if label else False)
      ws4[f'C{row}'] = content
      ws4[f'C{row}'].font = Font(name='Consolas' if '×' in content or 'ρ' in content or 'L_' in content else 'Calibri')
      if label in ['Step 1', 'Step 2', 'Step 3']:
          ws4[f'C{row}'].font = Font(name='Consolas', color='0066CC')
      if label == '結論':
          ws4[f'C{row}'].font = Font(color='C00000', bold=True)
      row += 1

  # 比較表格
  ws4['B19'] = "各溫度段長度比較"
  ws4['B19'].font = Font(size=13, bold=True, color="C00000")
  ws4['B19'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")

  comp_headers = ["溫度段", "Ag 長度", "CuNi 長度", "比值", "CuNi 熱負載\n(同長度)", "應用建議"]
  for col_idx, header in enumerate(comp_headers, start=2):
      cell = ws4.cell(row=20, column=col_idx, value=header)
      cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
      cell.font = Font(size=10, bold=True, color="FFFFFF")
      cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
      cell.border = thin_border

  ws4.row_dimensions[20].height = 30

  segments_cuni = [
      ("300K → 50K", 300, 50, 2.7e-3, 1.6e-8),
      ("50K → 4K", 50, 4, 0.8e-3, 1.5e-8),
      ("4K → 0.6K", 4, 0.6, 5.4e-6, 1.5e-8),
      ("0.6K → 100mK", 0.6, 0.1, 290e-9, 1.5e-8),
      ("100mK → 10mK", 0.1, 0.01, 5.9e-9, 1.5e-8),
  ]

  rho_cuni = 4.9e-7

  row = 21
  for name, Th, Tc, Q, rho_ag in segments_cuni:
      L_ag = (L0 * A_ch * (Th**2 - Tc**2)) / (2 * Q * rho_ag)
      L_cuni = (L0 * A_ch * (Th**2 - Tc**2)) / (2 * Q * rho_cuni)
      ratio = L_cuni / L_ag
      
      # 同長度下 CuNi 熱負載
      Q_cuni_same_L = (L0 * A_ch * (Th**2 - Tc**2)) / (2 * L_ag * rho_cuni)
      
      ws4[f'B{row}'] = name
      ws4[f'B{row}'].alignment = Alignment(horizontal='center')
      
      # Ag 長度
      if L_ag >= 1:
          ws4[f'C{row}'] = L_ag
          ws4[f'C{row}'].number_format = '0.00" m"'
      else:
          ws4[f'C{row}'] = L_ag * 100
          ws4[f'C{row}'].number_format = '0.0" cm"'
      
      # CuNi 長度
      if L_cuni >= 1:
          ws4[f'D{row}'] = L_cuni
          ws4[f'D{row}'].number_format = '0.0" m"'
      else:
          ws4[f'D{row}'] = L_cuni * 100
          ws4[f'D{row}'].number_format = '0.0" cm"'
      
      # 比值
      ws4[f'E{row}'] = ratio
      ws4[f'E{row}'].number_format = '0.0"×"'
      ws4[f'E{row}'].font = Font(bold=True, color='C00000')
      
      # CuNi 同長度熱負載
      if Q_cuni_same_L >= 1e-6:
          ws4[f'F{row}'] = Q_cuni_same_L * 1e6
          ws4[f'F{row}'].number_format = '0.00" µW"'
      else:
          ws4[f'F{row}'] = Q_cuni_same_L * 1e9
          ws4[f'F{row}'].number_format = '0.00" nW"'
      
      # 應用建議
      if Th >= 50:
          ws4[f'G{row}'] = "熱隔離段首選"
      else:
          ws4[f'G{row}'] = "低溫熱隔離"
      
      for col in range(2, 8):
          ws4.cell(row=row, column=col).border = thin_border
          ws4.cell(row=row, column=col).alignment = Alignment(horizontal='center', vertical='center')
      
      row += 1

  # 邊框
  for row_cells in ws4.iter_rows(min_row=4, max_row=18, min_col=2, max_col=3):
      for cell in row_cells:
          cell.border = thin_border

  print("✅ 工作表 4: CuNi比較 - 完成")
  return wb
