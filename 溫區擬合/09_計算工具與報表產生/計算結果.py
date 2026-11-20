from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from streamlit import session_state
thin_border=session_state['thin_border']
# ============================================================
# 工作表 3: 計算結果 (核心)
# ============================================================
def 計算結果(wb):
  ws3 = wb.create_sheet("計算結果")

  ws3.column_dimensions['A'].width = 3
  ws3.column_dimensions['B'].width = 18
  ws3.column_dimensions['C'].width = 15
  ws3.column_dimensions['D'].width = 15
  ws3.column_dimensions['E'].width = 15
  ws3.column_dimensions['F'].width = 15
  ws3.column_dimensions['G'].width = 15
  ws3.column_dimensions['H'].width = 15
  ws3.column_dimensions['I'].width = 15
  ws3.column_dimensions['J'].width = 15

  # 標題
  ws3['B2'] = "📊 各溫度段熱負載與回推長度計算結果"
  ws3['B2'].font = Font(size=16, bold=True, color="1F4E78")
  ws3.merge_cells('B2:J2')
  ws3['B2'].alignment = Alignment(horizontal='center')
  ws3.row_dimensions[2].height = 30

  # 說明
  ws3['B3'] = "計算公式: L = L₀ · A_channel · (Tₕ² - Tc²) / (2 · Q · ρ)"
  ws3['B3'].font = Font(size=10, name='Consolas', color="666666")
  ws3.merge_cells('B3:J3')

  # 表頭
  headers = ["溫度段", "Th (K)", "Tc (K)", "Ag 熱負載", "Ag 回推長度", 
             "NbTi 熱負載", "NbTi 回推長度", "長度比\n(Ag/NbTi)", "合理性評估", "單根長度\n(參考)"]

  header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
  header_font = Font(size=10, bold=True, color="FFFFFF")

  for col_idx, header in enumerate(headers, start=2):
      cell = ws3.cell(row=5, column=col_idx, value=header)
      cell.fill = header_fill
      cell.font = header_font
      cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
      cell.border = thin_border

  ws3.row_dimensions[5].height = 35

  # 計算數據
  L0 = 2.45e-8
  A_ch = 0.0635e-6  # mm² to m²
  A_single = 0.0127e-6

  segments = [
      ("300K → 50K", 300, 50, 2.7e-3, 1.6e-8, None, None),
      ("50K → 4K", 50, 4, 0.8e-3, 1.5e-8, None, None),
      ("4K → 0.6K (Ag)", 4, 0.6, 5.4e-6, 1.5e-8, 540e-9, 6.5e-7),
      ("4K → 0.6K (NbTi)", 4, 0.6, None, None, 540e-9, 6.5e-7),
      ("0.6K → 100mK (Ag)", 0.6, 0.1, 290e-9, 1.5e-8, 29e-9, 6.5e-7),
      ("0.6K → 100mK (NbTi)", 0.6, 0.1, None, None, 29e-9, 6.5e-7),
      ("100mK → 10mK (Ag)", 0.1, 0.01, 5.9e-9, 1.5e-8, 590e-12, 6.5e-7),
      ("100mK → 10mK (NbTi)", 0.1, 0.01, None, None, 590e-12, 6.5e-7),
  ]

  # 顏色定義
  ok_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
  warn_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
  ag_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
  nbti_fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")

  row = 6
  for name, Th, Tc, Q_ag, rho_ag, Q_nbti, rho_nbti in segments:
      # 溫度段
      ws3[f'B{row}'] = name
      ws3[f'B{row}'].font = Font(bold=True)
      ws3[f'B{row}'].alignment = Alignment(horizontal='center', vertical='center')
      
      # Th, Tc
      ws3[f'C{row}'] = Th
      ws3[f'C{row}'].number_format = '0.0'
      ws3[f'D{row}'] = Tc
      ws3[f'D{row}'].number_format = '0.00'
      
      # Ag 計算
      if Q_ag and rho_ag:
          L_ag = (L0 * A_ch * (Th**2 - Tc**2)) / (2 * Q_ag * rho_ag)
          
          # 熱負載 (自動單位)
          if Q_ag >= 1e-3:
              ws3[f'E{row}'] = Q_ag * 1e3
              ws3[f'E{row}'].number_format = '0.00" mW"'
          elif Q_ag >= 1e-6:
              ws3[f'E{row}'] = Q_ag * 1e6
              ws3[f'E{row}'].number_format = '0.00" µW"'
          elif Q_ag >= 1e-9:
              ws3[f'E{row}'] = Q_ag * 1e9
              ws3[f'E{row}'].number_format = '0.00" nW"'
          else:
              ws3[f'E{row}'] = Q_ag * 1e12
              ws3[f'E{row}'].number_format = '0.00" pW"'
          
          # 長度 (自動單位)
          if L_ag >= 1:
              ws3[f'F{row}'] = L_ag
              ws3[f'F{row}'].number_format = '0.00" m"'
          elif L_ag >= 0.01:
              ws3[f'F{row}'] = L_ag * 100
              ws3[f'F{row}'].number_format = '0.0" cm"'
          else:
              ws3[f'F{row}'] = L_ag * 1000
              ws3[f'F{row}'].number_format = '0.0" mm"'
          
          ws3[f'E{row}'].fill = ag_fill
          ws3[f'F{row}'].fill = ag_fill
          
          # 單根長度參考
          L_single = (L0 * A_single * (Th**2 - Tc**2)) / (2 * Q_ag * rho_ag)
          if L_single >= 0.01:
              ws3[f'J{row}'] = L_single * 100
              ws3[f'J{row}'].number_format = '0.0" cm"'
          else:
              ws3[f'J{row}'] = L_single * 1000
              ws3[f'J{row}'].number_format = '0.0" mm"'
      else:
          ws3[f'E{row}'] = "—"
          ws3[f'F{row}'] = "—"
          ws3[f'J{row}'] = "—"
      
      # NbTi 計算
      if Q_nbti and rho_nbti:
          L_nbti = (L0 * A_ch * (Th**2 - Tc**2)) / (2 * Q_nbti * rho_nbti)
          
          if Q_nbti >= 1e-6:
              ws3[f'G{row}'] = Q_nbti * 1e6
              ws3[f'G{row}'].number_format = '0.00" µW"'
          elif Q_nbti >= 1e-9:
              ws3[f'G{row}'] = Q_nbti * 1e9
              ws3[f'G{row}'].number_format = '0.00" nW"'
          else:
              ws3[f'G{row}'] = Q_nbti * 1e12
              ws3[f'G{row}'].number_format = '0.00" pW"'
          
          if L_nbti >= 1:
              ws3[f'H{row}'] = L_nbti
              ws3[f'H{row}'].number_format = '0.00" m"'
          elif L_nbti >= 0.01:
              ws3[f'H{row}'] = L_nbti * 100
              ws3[f'H{row}'].number_format = '0.0" cm"'
          else:
              ws3[f'H{row}'] = L_nbti * 1000
              ws3[f'H{row}'].number_format = '0.0" mm"'
          
          ws3[f'G{row}'].fill = nbti_fill
          ws3[f'H{row}'].fill = nbti_fill
          
          # 長度比
          if Q_ag and rho_ag:
              L_ag_val = (L0 * A_ch * (Th**2 - Tc**2)) / (2 * Q_ag * rho_ag)
              ratio = L_ag_val / L_nbti
              ws3[f'I{row}'] = ratio
              ws3[f'I{row}'].number_format = '0.0"×"'
          else:
              ws3[f'I{row}'] = "—"
      else:
          ws3[f'G{row}'] = "—"
          ws3[f'H{row}'] = "—"
          ws3[f'I{row}'] = "—"
      
      # 合理性評估
      if Q_ag and rho_ag:
          L_ag_val = (L0 * A_ch * (Th**2 - Tc**2)) / (2 * Q_ag * rho_ag)
          if 0.1 <= L_ag_val <= 2.0:
              ws3[f'I{row}'] = "✅ 合理"
              ws3[f'I{row}'].fill = ok_fill
          elif L_ag_val < 0.1:
              ws3[f'I{row}'] = "⚠️ 較短"
              ws3[f'I{row}'].fill = warn_fill
          else:
              ws3[f'I{row}'] = "⚠️ 偏長"
              ws3[f'I{row}'].fill = warn_fill
      elif Q_nbti and rho_nbti:
          L_nbti_val = (L0 * A_ch * (Th**2 - Tc**2)) / (2 * Q_nbti * rho_nbti)
          if L_nbti_val < 0.05:
              ws3[f'I{row}'] = "⚠️ 等效熱阻"
              ws3[f'I{row}'].fill = warn_fill
      
      # 邊框
      for col in range(2, 11):
          ws3.cell(row=row, column=col).border = thin_border
          ws3.cell(row=row, column=col).alignment = Alignment(horizontal='center', vertical='center')
      
      row += 1

  # 累積長度
  ws3[f'B{row+1}'] = "累積長度"
  ws3[f'B{row+1}'].font = Font(bold=True, color="1F4E78")
  ws3[f'B{row+1}'].fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")

  # 計算累積
  cum_ag = sum([(L0 * A_ch * (Th**2 - Tc**2)) / (2 * Q_ag * rho_ag) 
                for name, Th, Tc, Q_ag, rho_ag, Q_nbti, rho_nbti in segments if Q_ag and rho_ag])
  cum_nbti = sum([(L0 * A_ch * (Th**2 - Tc**2)) / (2 * Q_nbti * rho_nbti) 
                  for name, Th, Tc, Q_ag, rho_ag, Q_nbti, rho_nbti in segments if Q_nbti and rho_nbti])

  ws3[f'F{row+1}'] = cum_ag
  ws3[f'F{row+1}'].number_format = '0.00" m"'
  ws3[f'F{row+1}'].font = Font(bold=True)
  ws3[f'H{row+1}'] = cum_nbti
  ws3[f'H{row+1}'].number_format = '0.000" m"'
  ws3[f'H{row+1}'].font = Font(bold=True)

  for col in ['B', 'F', 'H']:
      ws3[f'{col}{row+1}'].border = thin_border
      ws3[f'{col}{row+1}'].alignment = Alignment(horizontal='center', vertical='center')

  print("✅ 工作表 3: 計算結果 - 完成")
  return wb
