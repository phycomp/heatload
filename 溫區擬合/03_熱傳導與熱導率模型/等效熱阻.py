
# ============================================================
# 工作表 7: 等效熱阻
# ============================================================
ws7 = wb.create_sheet("等效熱阻")

ws7.column_dimensions['A'].width = 3
ws7.column_dimensions['B'].width = 25
ws7.column_dimensions['C'].width = 70

# 標題
ws7['B2'] = "🔥 等效熱阻長度概念 (4K 以下 NbTi 段)"
ws7['B2'].font = Font(size=16, bold=True, color="1F4E78")
ws7.merge_cells('B2:C2')
ws7['B2'].alignment = Alignment(horizontal='center')
ws7.row_dimensions[2].height = 30

# 問題
ws7['B4'] = "問題"
ws7['B4'].font = Font(size=13, bold=True, color="C00000")
ws7['B4'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")

ws7['B5'] = "計算結果"
ws7['B5'].font = Font(bold=True)
ws7['C5'] = "4K 以下 NbTi 段回推長度僅數毫米，與實際稀釋製冷機結構不符"

ws7['B6'] = "實際結構"
ws7['B6'].font = Font(bold=True)
ws7['C6'] = "4K Plate ──[2cm NbTi帶]── Still(0.6K) ──[1cm]── Cold Plate(100mK) ──[1cm]── Mixing Chamber(10mK)"

# 解釋
ws7['B8'] = "解釋"
ws7['B8'].font = Font(size=13, bold=True, color="2E5090")
ws7['B8'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")

explanations = [
    ("超導特性", "NbTi 臨界溫度 Tc ≈ 9.2K，在 <9.2K 為超導態，直流電阻理論為零"),
    ("熱負載來源", "圖中 NbTi 熱負載實際來自銅穩定層 (Cu matrix) 的殘餘熱傳導"),
    ("接頭電阻", "超導-正常態界面 (SNAP) 產生額外熱阻"),
    ("磁通流動", "若有磁場或電流超過臨界電流 Jc，產生磁通流動電阻"),
]

row = 9
for label, content in explanations:
    ws7[f'B{row}'] = label
    ws7[f'B{row}'].font = Font(bold=True)
    ws7[f'C{row}'] = content
    row += 1

# 等效熱阻定義
ws7['B14'] = "等效熱阻長度定義"
ws7['B14'].font = Font(size=13, bold=True, color="2E5090")
ws7['B14'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")

ws7['B15'] = "公式"
ws7['B15'].font = Font(bold=True)
ws7['C15'] = "L_eff = L₀ · A · (Th² - Tc²) / (2 · Q · ρ_eff)"
ws7['C15'].font = Font(name='Consolas', size=12, color='CC0000', bold=True)

ws7['B16'] = "ρ_eff 組成"
ws7['B16'].font = Font(bold=True)
ws7['C16'] = "ρ_eff = ρ_Cu_matrix + ρ_joint + ρ_flux_flow"

ws7['B17'] = "物理意義"
ws7['B17'].font = Font(bold=True)
ws7['C17'] = "計算出的 '長度' 實為等效正常態熱阻，非實體線長。實際 NbTi 超導線很短，但等效熱阻很大"

# 計算範例
ws7['B19'] = "計算範例: 4K → 0.6K (NbTi)"
ws7['B19'].font = Font(size=13, bold=True, color="2E5090")
ws7['B19'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")

example_calc = [
    ("已知", "Q = 540 nW, Th = 4K, Tc = 0.6K, A_ch = 0.0635 mm²"),
    ("假設", "ρ_eff = 6.5×10⁻⁷ Ω·m (含銅基體等效)"),
    ("計算", "L_eff = 2.45×10⁻⁸ × 6.35×10⁻⁸ × (16-0.36) / (2 × 540×10⁻⁹ × 6.5×10⁻⁷)"),
    ("結果", "L_eff ≈ 3.5 cm (等效熱阻長度)"),
    ("實際", "實體 NbTi 線僅 ~2 cm，但接頭熱阻使等效長度增加"),
]

row = 20
for label, content in example_calc:
    ws7[f'B{row}'] = label
    ws7[f'B{row}'].font = Font(bold=True)
    ws7[f'C{row}'] = content
    if '計算' in label:
        ws7[f'C{row}'].font = Font(name='Consolas', color='0066CC')
    row += 1

# 邊框
for row_cells in ws7.iter_rows(min_row=4, max_row=ws7.max_row, min_col=2, max_col=3):
    for cell in row_cells:
        cell.border = thin_border
        cell.alignment = Alignment(vertical='center', wrap_text=True)

print("✅ 工作表 7: 等效熱阻 - 完成")
