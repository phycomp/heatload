
# ============================================================
# 工作表 6: 物理推導
# ============================================================
ws6 = wb.create_sheet("物理推導")

ws6.column_dimensions['A'].width = 3
ws6.column_dimensions['B'].width = 25
ws6.column_dimensions['C'].width = 70

# 標題
ws6['B2'] = "📐 Wiedemann-Franz 定律完整推導"
ws6['B2'].font = Font(size=16, bold=True, color="1F4E78")
ws6.merge_cells('B2:C2')
ws6['B2'].alignment = Alignment(horizontal='center')
ws6.row_dimensions[2].height = 30

# Step 1
ws6['B4'] = "Step 1: Wiedemann-Franz Law"
ws6['B4'].font = Font(size=13, bold=True, color="2E5090")
ws6['B4'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")

ws6['B5'] = "物理意義"
ws6['B5'].font = Font(bold=True)
ws6['C5'] = "金屬的熱導率 λ 與電導率 σ 成正比，比例係數為 Lorenz 數 L₀ 與溫度 T 的乘積"

ws6['B6'] = "公式"
ws6['B6'].font = Font(bold=True)
ws6['C6'] = "λ = L₀ · T · σ = L₀ · T / ρ(T)"
ws6['C6'].font = Font(name='Consolas', size=12, color='0066CC')

ws6['B7'] = "參數說明"
ws6['B7'].font = Font(bold=True)
ws6['C7'] = "L₀ = 2.45×10⁻⁸ W·Ω/K² (普適常數) | T = 絕對溫度 (K) | ρ(T) = 電阻率 (Ω·m)"

# Step 2
ws6['B9'] = "Step 2: 熱傳導積分"
ws6['B9'].font = Font(size=13, bold=True, color="2E5090")
ws6['B9'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")

ws6['B10'] = "傅立葉定律"
ws6['B10'].font = Font(bold=True)
ws6['C10'] = "Q = -λ · A · dT/dx  (一維熱傳導)"
ws6['C10'].font = Font(name='Consolas')

ws6['B11'] = "積分形式"
ws6['B11'].font = Font(bold=True)
ws6['C11'] = "Q = (A/L) · ∫[Tc→Th] λ(T) dT"
ws6['C11'].font = Font(name='Consolas')

ws6['B12'] = "代入 WF Law"
ws6['B12'].font = Font(bold=True)
ws6['C12'] = "Q = (A/L) · ∫[Tc→Th] (L₀·T/ρ) dT"
ws6['C12'].font = Font(name='Consolas')

ws6['B13'] = "假設 ρ≈常數"
ws6['B13'].font = Font(bold=True)
ws6['C13'] = "Q = (L₀·A / L·ρ) · (Th² - Tc²) / 2"
ws6['C13'].font = Font(name='Consolas', size=12, color='CC0000', bold=True)

# Step 3
ws6['B15'] = "Step 3: 反推長度"
ws6['B15'].font = Font(size=13, bold=True, color="2E5090")
ws6['B15'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")

ws6['B16'] = "整理公式"
ws6['B16'].font = Font(bold=True)
ws6['C16'] = "L = L₀ · A · (Th² - Tc²) / (2 · Q · ρ)"
ws6['C16'].font = Font(name='Consolas', size=14, color='CC0000', bold=True)

ws6['B17'] = "關鍵修正"
ws6['B17'].font = Font(bold=True)
ws6['C17'] = "A = A_channel (整個同軸通道有效截面積)，非單根線截面積！"
ws6['C17'].font = Font(color='C00000', bold=True)

# Step 4
ws6['B19'] = "Step 4: 熱輻射推導"
ws6['B19'].font = Font(size=13, bold=True, color="2E5090")
ws6['B19'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")

ws6['B20'] = "Stefan-Boltzmann"
ws6['B20'].font = Font(bold=True)
ws6['C20'] = "Q_rad = ε · σ · A_surf · (Th⁴ - Tc⁴)"
ws6['C20'].font = Font(name='Consolas', size=12, color='0066CC')

ws6['B21'] = "參數"
ws6['B21'].font = Font(bold=True)
ws6['C21'] = "σ = 5.67×10⁻⁸ W/m²/K⁴ | ε = 發射率 (拋光Al: 0.03) | A_surf = π·D·L"

# 邊框
for row_cells in ws6.iter_rows(min_row=4, max_row=ws6.max_row, min_col=2, max_col=3):
    for cell in row_cells:
        cell.border = thin_border
        cell.alignment = Alignment(vertical='center', wrap_text=True)

print("✅ 工作表 6: 物理推導 - 完成")
