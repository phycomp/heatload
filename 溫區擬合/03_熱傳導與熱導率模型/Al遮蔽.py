
# ============================================================
# 工作表 5: Al Shield 分析
# ============================================================
ws5 = wb.create_sheet("Al Shield")

ws5.column_dimensions['A'].width = 3
ws5.column_dimensions['B'].width = 20
ws5.column_dimensions['C'].width = 18
ws5.column_dimensions['D'].width = 18
ws5.column_dimensions['E'].width = 18
ws5.column_dimensions['F'].width = 18
ws5.column_dimensions['G'].width = 25

# 標題
ws5['B2'] = "🛡️ Aluminum Shielding 熱傳導與輻射分析"
ws5['B2'].font = Font(size=16, bold=True, color="1F4E78")
ws5.merge_cells('B2:G2')
ws5['B2'].alignment = Alignment(horizontal='center')
ws5.row_dimensions[2].height = 30

# 並聯模型說明
ws5['B4'] = "並聯熱傳導模型"
ws5['B4'].font = Font(size=13, bold=True, color="C00000")
ws5['B4'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")

model_text = [
    ("電路類比", "Signal Line 與 Al Shield 並聯分流熱負載"),
    ("", ""),
    ("公式", "1/R_total = 1/R_wire + 1/R_shield"),
    ("", "R = L / (λ·A) = 2L·ρ / [L₀·A·(Th²-Tc²)]"),
    ("", ""),
    ("Shield 長度", "L_Al = L₀ · A_Al · (Th²-Tc²) / (2 · Q · ρ_Al)"),
    ("", ""),
    ("典型參數", "Al ρ (4K, RRR~100) = 2.5×10⁻⁹ Ω·m"),
    ("", "Shield 截面積 = 0.597 mm² (Ø2mm, t=0.1mm)"),
    ("", "L_Al / L_Ag ≈ (A_Al/A_Ag) · (ρ_Ag/ρ_Al) ≈ 10×"),
]

row = 5
for label, content in model_text:
    ws5[f'B{row}'] = label
    ws5[f'B{row}'].font = Font(bold=True if label else False)
    ws5[f'C{row}'] = content
    if '公式' in label or 'L_Al' in content or 'R_' in content:
        ws5[f'C{row}'].font = Font(name='Consolas', color='0066CC')
    row += 1

# Shield 計算表格
ws5['B16'] = "各溫度段 Shield 分析"
ws5['B16'].font = Font(size=13, bold=True, color="C00000")
ws5['B16'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")

shield_headers = ["溫度段", "Wire Q", "Shield 長度", "Shield Q", "輻射 Q", "總熱負載", "輻射佔比"]
for col_idx, header in enumerate(shield_headers, start=2):
    cell = ws5.cell(row=17, column=col_idx, value=header)
    cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    cell.font = Font(size=10, bold=True, color="FFFFFF")
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    cell.border = thin_border

ws5.row_dimensions[17].height = 30

# Shield 參數
A_al = 0.597e-6  # mm² to m²
shield_d = 2.0e-3
shield_L = 0.3
sigma = 5.67e-8
epsilon = 0.03

shield_segments = [
    ("300K → 50K", 300, 50, 2.7e-3, 1.6e-8, rho_Al_300 := 2.7e-8),
    ("50K → 4K", 50, 4, 0.8e-3, 1.5e-8, rho_Al_50 := 2.5e-8),
    ("4K → 0.6K", 4, 0.6, 5.4e-6, 1.5e-8, rho_Al_4 := 2.5e-9),
]

row = 18
for name, Th, Tc, Q, rho_wire, rho_al in shield_segments:
    # Shield 長度
    L_al = (L0 * A_al * (Th**2 - Tc**2)) / (2 * Q * rho_al) if rho_al else None
    
    # 輻射熱負載
    A_surf = np.pi * shield_d * shield_L
    Q_rad = epsilon * sigma * A_surf * (Th**4 - Tc**4)
    
    ws5[f'B{row}'] = name
    ws5[f'B{row}'].alignment = Alignment(horizontal='center')
    
    # Wire Q
    ws5[f'C{row}'] = Q * 1e3
    ws5[f'C{row}'].number_format = '0.00" mW"'
    
    # Shield 長度
    if L_al:
        if L_al >= 1:
            ws5[f'D{row}'] = L_al
            ws5[f'D{row}'].number_format = '0.00" m"'
        else:
            ws5[f'D{row}'] = L_al * 100
            ws5[f'D{row}'].number_format = '0.0" cm"'
    else:
        ws5[f'D{row}'] = "N/A"
    
    # Shield Q (假設承擔全部)
    ws5[f'E{row}'] = Q * 1e3
    ws5[f'E{row}'].number_format = '0.00" mW"'
    
    # 輻射 Q
    if Q_rad >= 1e-3:
        ws5[f'F{row}'] = Q_rad * 1e3
        ws5[f'F{row}'].number_format = '0.00" mW"'
    elif Q_rad >= 1e-6:
        ws5[f'F{row}'] = Q_rad * 1e6
        ws5[f'F{row}'].number_format = '0.00" µW"'
    else:
        ws5[f'F{row}'] = Q_rad * 1e9
        ws5[f'F{row}'].number_format = '0.00" nW"'
    
    # 總熱負載
    Q_total = Q + Q_rad
    ws5[f'G{row}'] = Q_total * 1e3
    ws5[f'G{row}'].number_format = '0.00" mW"'
    
    # 輻射佔比
    ratio_rad = Q_rad / Q_total * 100
    ws5[f'H{row}'] = ratio_rad
    ws5[f'H{row}'].number_format = '0.0"%"'
    if ratio_rad > 50:
        ws5[f'H{row}'].font = Font(color='C00000', bold=True)
    
    for col in range(2, 9):
        ws5.cell(row=row, column=col).border = thin_border
        ws5.cell(row=row, column=col).alignment = Alignment(horizontal='center', vertical='center')
    
    row += 1

# 輻射分析說明
ws5['B22'] = "輻射熱負載分析"
ws5['B22'].font = Font(size=13, bold=True, color="C00000")
ws5['B22'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")

rad_analysis = [
    ("公式", "Q_rad = ε · σ · A_surf · (Th⁴ - Tc⁴)"),
    ("", ""),
    ("300K→50K", "Q_rad ≈ 2.6 mW ≈ 傳導熱負載 (2.7 mW) → 不可忽略"),
    ("50K→4K", "Q_rad ≈ 0.01 mW << 傳導 (0.8 mW) → 可忽略"),
    ("4K以下", "Q_rad < 1 µW → 完全可忽略"),
    ("", ""),
    ("抑制方法", "多層 Shield (MLI): 輻射降低 10⁻³~10⁻⁴"),
]

row = 23
for label, content in rad_analysis:
    ws5[f'B{row}'] = label
    ws5[f'B{row}'].font = Font(bold=True if label else False)
    ws5[f'C{row}'] = content
    if '公式' in label:
        ws5[f'C{row}'].font = Font(name='Consolas', color='0066CC')
    row += 1

print("✅ 工作表 5: Al Shield - 完成")
