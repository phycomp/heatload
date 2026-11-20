from streamlit import image as stImage, sidebar, text_input, radio
from PIL import Image, ImageDraw, ImageFont
import os

# Create a large canvas for the industrial R2R sputtering process diagram
width, height = 1600, 2400
img = Image.new('RGB', (width, height), color='#080c14')
draw = ImageDraw.Draw(img)

# Try to load fonts
try:
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
    font_header = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
    font_text = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    font_cn_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    font_cn = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 32)
    font_cn_header = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 24)
    font_cn_text = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 20)
    font_cn_small = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 16)
except:
    font_title = ImageFont.load_default()
    font_header = ImageFont.load_default()
    font_text = ImageFont.load_default()
    font_cn_small = ImageFont.load_default()
    font_cn = ImageFont.load_default()
    font_cn_header = ImageFont.load_default()
    font_cn_text = ImageFont.load_default()
    font_cn_small = ImageFont.load_default()

# Colors
COLOR_BG = '#080c14'
COLOR_TITLE = '#00e5ff'
COLOR_SUBTITLE = '#ffaa33'
COLOR_STEP_BG = '#0f1a2e'
COLOR_STEP_BORDER = '#00e5ff'
COLOR_ARROW = '#00ff88'
COLOR_TEXT = '#e0e8f0'
COLOR_WARN = '#ff4444'
COLOR_OK = '#00ff88'
COLOR_ACCENT = '#ffcc00'

# Layer colors
COLOR_CU = '#b87333'
COLOR_TI = '#7a7a7a'
COLOR_NBTI = '#4a6fa5'
COLOR_CAP = '#2a5a8a'
COLOR_PR = '#ff6b9d'
COLOR_PCB = '#2d5a3d'

# Helper
def draw_rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
from streamlit import empty
MENU, 表單=[], ['NbTi濺鍍', '物理參數', '基底選項', '晶格結構', 'R2R挑戰']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  狀態=empty()
  狀態.code([])
if menu==len(表單): #
  pass
elif menu==MENU[4]: #
  # ============ R2R PROCESS CHALLENGES ============
  y = 1730
  box_h = 300

  draw_rounded_rect(draw, (50, y, width-50, y+box_h), 20, '#1a0a0a', '#ff4444', 2)
  draw.text((width//2, y+15), "⚠️ R2R 大面積製程挑戰 │ R2R Scale-Up Challenges", fill=COLOR_WARN, font=font_cn_header, anchor="mm")

  challenges = [
      ("薄膜均勻性", "寬度方向 ±5% → R2R 需 < ±3%", "磁控靶設計 + 基材移動補償"),
      ("應力控制", "Cu/NbTi CTE 差異導致捲曲", "張力控制 + 溫度梯度管理"),
      ("界面污染", "大面積暴露增加氧化風險", "多腔體隔離 + 負載鎖 (Load Lock)"),
      ("臨界厚度", "錯配應力導致島狀生長 (S-K mode)", "Ti 緩衝層 + 低溫沉積"),
      ("光刻兼容性", "PCB 基材不耐高溫", "低溫製程 < 150°C 或改用 LTCC"),
      ("量子特性保持", "大面積缺陷密度增加", "潔淨室等級 + 即時監控"),
  ]

  for i, (issue, problem, solution) in enumerate(challenges):
      cx = 80 + (i%2)*750
      cy = y+55 + (i//2)*110
      draw_rounded_rect(draw, (cx, cy, cx+720, cy+95), 10, '#2a0a0a', '#ff6666', 1)
      draw.text((cx+15, cy+12), f"▸ {issue}", fill=COLOR_WARN, font=font_cn_small)
      draw.text((cx+25, cy+35), f"問題: {problem}", fill='#ffcccc', font=font_cn_small)
      draw.text((cx+25, cy+58), f"對策: {solution}", fill='#88ffaa', font=font_cn_small)

  # ============ PROCESS FLOW ============
  y = 2100
  box_h = 120

  draw_rounded_rect(draw, (50, y, width-50, y+box_h), 20, '#0a1a0a', '#00ff88', 2)
  draw.text((width//2, y+12), "工業級 R2R 製程流程 │ Industrial R2R Process Flow", fill=COLOR_OK, font=font_cn_header, anchor="mm")

  flow = ["放卷", "電漿清洗", "Ti 附著層", "NbTi 主層", "保護層", "冷卻", "張力調整", "收卷", "AOI 檢測", "電性測試"]
  for i, item in enumerate(flow):
      fx = 80 + i*145
      draw.rounded_rectangle((fx, y+45, fx+130, y+90), radius=8, fill='#0a2a1a', outline='#00ff88', width=1)
      draw.text((fx+65, y+67), item, fill='#ccffcc', font=font_cn_small, anchor="mm")
      if i < len(flow)-1:
          draw.text((fx+138, y+67), "→", fill=COLOR_ARROW, font=font_cn_small)

  # Bottom
  draw.text((width//2, height-25), "工業級 R2R NbTi 超導薄膜製程 │ 版本 2.0 │ 2026-05-14", fill='#446688', font=font_cn_small, anchor="mm")

  stImage(img)
  # Save
  #output_path = '/mnt/agents/output/R2R_NbTi_Industrial_Process_Diagram.png'
  #img.save(output_path, quality=95)
  #print(f"✅ 圖片已儲存: {output_path}")
  #print(f"尺寸: {width}x{height}")
  #img

elif menu==MENU[3]: #
  # ============ CRYSTAL LATTICE SECTION ============
  y = 1330
  box_h = 380

  draw_rounded_rect(draw, (50, y, width-50, y+box_h), 20, '#0f1a2e', '#00e5ff', 2)
  draw.text((width//2, y+15), "晶格結構與外延關係 │ Crystal Lattice & Epitaxy", fill=COLOR_TITLE, font=font_cn_header, anchor="mm")

  # Draw crystal structures
  # Cu FCC
  cx1, cy1 = 200, y+120
  draw.text((cx1, y+50), "Cu 基材 (FCC)", fill=COLOR_CU, font=font_cn_text, anchor="mm")
  # Draw FCC unit cell schematic
  for i in range(4):
      for j in range(4):
          x_pos = cx1 - 60 + i*40
          y_pos = cy1 - 60 + j*40
          draw.ellipse((x_pos-8, y_pos-8, x_pos+8, y_pos+8), fill=COLOR_CU, outline='white', width=1)
  # Face-centered atoms
  draw.ellipse((cx1-28, cy1-28, cx1+28, cy1+28), fill=COLOR_CU, outline='white', width=1)
  draw.text((cx1, cy1+80), "a = 3.615 Å", fill='#ffcc88', font=font_cn_small, anchor="mm")
  draw.text((cx1, cy1+100), "(111) 密排面", fill='#88aacc', font=font_cn_small, anchor="mm")

  # Arrow
  draw.text((cx1+130, cy1), "→", fill=COLOR_ARROW, font=font_title)

  # Ti layer (HCP)
  cx2, cy2 = cx1+260, cy1
  draw.text((cx2, y+50), "Ti 緩衝層 (HCP)", fill=COLOR_TI, font=font_cn_text, anchor="mm")
  for i in range(3):
      for j in range(3):
          x_pos = cx2 - 45 + i*45
          y_pos = cy2 - 45 + j*45
          draw.ellipse((x_pos-8, y_pos-8, x_pos+8, y_pos+8), fill=COLOR_TI, outline='white', width=1)
  draw.ellipse((cx2-20, cy2-20, cx2+20, cy2+20), fill=COLOR_TI, outline='white', width=1)
  draw.text((cx2, cy2+80), "a = 2.95 Å, c = 4.68 Å", fill='#ffcc88', font=font_cn_small, anchor="mm")
  draw.text((cx2, cy2+100), "(0001) 基面", fill='#88aacc', font=font_cn_small, anchor="mm")

  # Arrow
  draw.text((cx2+130, cy2), "→", fill=COLOR_ARROW, font=font_title)

  # NbTi BCC
  cx3, cy3 = cx2+260, cy2
  draw.text((cx3, y+50), "NbTi 薄膜 (BCC)", fill=COLOR_NBTI, font=font_cn_text, anchor="mm")
  for i in range(3):
      for j in range(3):
          x_pos = cx3 - 45 + i*45
          y_pos = cy3 - 45 + j*45
          draw.ellipse((x_pos-8, y_pos-8, x_pos+8, y_pos+8), fill=COLOR_NBTI, outline='white', width=1)
  draw.ellipse((cx3-20, cy3-20, cx3+20, cy3+20), fill=COLOR_NBTI, outline='white', width=1)
  draw.text((cx3, cy3+80), "a ≈ 3.3 Å", fill='#ffcc88', font=font_cn_small, anchor="mm")
  draw.text((cx3, cy3+100), "(110) 優選取向", fill='#88aacc', font=font_cn_small, anchor="mm")

  # Epitaxy relationship on right
  rel_x = cx3 + 180
  draw.text((rel_x, y+60), "外延關係 Epitaxy:", fill=COLOR_ACCENT, font=font_cn_header)
  draw.text((rel_x, y+95), "Cu(111) // Ti(0001) // NbTi(110)", fill=COLOR_TEXT, font=font_cn_small)
  draw.text((rel_x, y+120), "Cu[1̄10] // Ti[11̄20] // NbTi[001]", fill=COLOR_TEXT, font=font_cn_small)
  draw.text((rel_x, y+155), "晶格錯配: NbTi/Cu = 8.3%", fill=COLOR_WARN, font=font_cn_small)
  draw.text((rel_x, y+180), "臨界厚度 (hc): ~10 nm (Matthews-Blakeslee)", fill=COLOR_TEXT, font=font_cn_small)
  draw.text((rel_x, y+205), "Ti 緩衝層作用: 降低錯配應力", fill=COLOR_OK, font=font_cn_small)
  draw.text((rel_x, y+230), "應力狀態: 壓應力 → 張應力轉變", fill=COLOR_TEXT, font=font_cn_small)
  draw.text((rel_x, y+255), "位錯機制: 60° 位錯 + 刃位錯", fill=COLOR_TEXT, font=font_cn_small)
elif menu==MENU[2]: #
  # ============ SUBSTRATE SECTION ============
  y = 930
  box_h = 380

  draw_rounded_rect(draw, (50, y, width-50, y+box_h), 20, '#0f1a2e', '#ffaa33', 2)
  draw.text((width//2, y+15), "光刻電路板基材選擇 │ Photolithography PCB Substrate Selection", fill=COLOR_SUBTITLE, font=font_cn_header, anchor="mm")

  # Substrate options table
  sub_x = 80
  sub_y = y+55
  row_h = 70

  # Header
  draw.rectangle((sub_x, sub_y, sub_x+200, sub_y+30), fill='#2a3a5a', outline='white', width=1)
  draw.rectangle((sub_x+200, sub_y, sub_x+450, sub_y+30), fill='#2a3a5a', outline='white', width=1)
  draw.rectangle((sub_x+450, sub_y, sub_x+750, sub_y+30), fill='#2a3a5a', outline='white', width=1)
  draw.rectangle((sub_x+750, sub_y, sub_x+1050, sub_y+30), fill='#2a3a5a', outline='white', width=1)
  draw.rectangle((sub_x+1050, sub_y, width-80, sub_y+30), fill='#2a3a5a', outline='white', width=1)

  draw.text((sub_x+100, sub_y+15), "基材類型", fill='white', font=font_cn_small, anchor="mm")
  draw.text((sub_x+325, sub_y+15), "熱穩定性", fill='white', font=font_cn_small, anchor="mm")
  draw.text((sub_x+600, sub_y+15), "介電損耗 (tan δ)", fill='white', font=font_cn_small, anchor="mm")
  draw.text((sub_x+900, sub_y+15), "熱膨脹係數", fill='white', font=font_cn_small, anchor="mm")
  draw.text((sub_x+1225, sub_y+15), "適用性評估", fill='white', font=font_cn_small, anchor="mm")

  # Data rows
  substrates = [
      ("FR-4 (標準PCB)", "< 130°C", "0.02 @ 1 GHz", "14-17 ppm/K", "❌ 熱穩定性不足"),
      ("高 Tg FR-4", "< 170°C", "0.015 @ 1 GHz", "14-17 ppm/K", "△ 邊緣可用"),
      ("聚醯亞胺 PI", "< 300°C", "0.003 @ 1 GHz", "50 ppm/K", "△ 熱膨脹過大"),
      ("PTFE (鐵氟龍)", "< 260°C", "0.0002 @ 1 GHz", "100 ppm/K", "△ 低損耗但CTE大"),
      ("藍寶石 (Al₂O₃)", "> 1000°C", "< 10⁻⁹ @ 10 GHz", "5-6 ppm/K", "✅ 最佳但成本高"),
      ("石英 (SiO₂)", "> 1000°C", "< 10⁻⁹ @ 10 GHz", "0.5 ppm/K", "✅ 理想但脆性大"),
      ("LTCC (低溫共燒陶瓷)", "< 900°C", "0.001 @ 1 GHz", "5-7 ppm/K", "✅ 推薦方案"),
  ]

  for i, (name, thermal, loss, cte, assess) in enumerate(substrates):
      ry = sub_y+30+i*row_h
      colors = ['#1a2a3a', '#1a2a3a', '#1a2a3a', '#1a2a3a', '#1a2a3a']
      if "✅" in assess:
          colors = ['#0a2a1a', '#0a2a1a', '#0a2a1a', '#0a2a1a', '#0a2a1a']
      elif "❌" in assess:
          colors = ['#2a0a0a', '#2a0a0a', '#2a0a0a', '#2a0a0a', '#2a0a0a']
      
      draw.rectangle((sub_x, ry, sub_x+200, ry+row_h), fill=colors[0], outline='#444444', width=1)
      draw.rectangle((sub_x+200, ry, sub_x+450, ry+row_h), fill=colors[1], outline='#444444', width=1)
      draw.rectangle((sub_x+450, ry, sub_x+750, ry+row_h), fill=colors[2], outline='#444444', width=1)
      draw.rectangle((sub_x+750, ry, sub_x+1050, ry+row_h), fill=colors[3], outline='#444444', width=1)
      draw.rectangle((sub_x+1050, ry, width-80, ry+row_h), fill=colors[4], outline='#444444', width=1)
      
      draw.text((sub_x+100, ry+row_h//2), name, fill=COLOR_TEXT, font=font_cn_small, anchor="mm")
      draw.text((sub_x+325, ry+row_h//2), thermal, fill=COLOR_TEXT, font=font_cn_small, anchor="mm")
      draw.text((sub_x+600, ry+row_h//2), loss, fill=COLOR_TEXT, font=font_cn_small, anchor="mm")
      draw.text((sub_x+900, ry+row_h//2), cte, fill=COLOR_TEXT, font=font_cn_small, anchor="mm")
      
      assess_color = COLOR_OK if "✅" in assess else (COLOR_WARN if "❌" in assess else '#ffcc88')
      draw.text((sub_x+1225, ry+row_h//2), assess, fill=assess_color, font=font_cn_small, anchor="mm")

elif menu==MENU[1]: #
  # ============ PHYSICAL PARAMETERS SECTION ============
  y = 390
  box_h = 520

  draw_rounded_rect(draw, (50, y, width-50, y+box_h), 20, COLOR_STEP_BG, COLOR_STEP_BORDER, 2)
  draw.text((width//2, y+15), "物理參數模擬 │ Physical Parameter Simulation", fill=COLOR_TITLE, font=font_cn_header, anchor="mm")

  # Three columns of parameters
  col_w = (width-140)//3
  col1_x = 70
  col2_x = col1_x + col_w + 20
  col3_x = col2_x + col_w + 20

  # Column 1: Thermal Parameters
  draw.text((col1_x, y+50), "【熱力學參數】", fill=COLOR_OK, font=font_cn_header)
  params_thermal = [
      ("濺鍍溫度 (Ts)", "室溫 - 300°C", "影響晶粒尺寸與應力"),
      ("基材溫度 (Tsub)", "< 150°C (PCB限制)", "避免基材熱損傷"),
      ("熱膨脹係數 α", "Cu: 16.5, NbTi: 8.5", "ppm/K - 低溫應力源"),
      ("熱導率 κ", "Cu: 400, NbTi: ~20", "W/m·K - 散熱設計"),
      ("比熱容 Cp", "溫度依賴性強", "mK 熱負載計算"),
      ("熱界面電阻", "Rbd < 10⁻⁴ K·m²/W", "薄膜/基材界面"),
  ]
  for i, (param, value, note) in enumerate(params_thermal):
      py = y+85+i*65
      draw.text((col1_x, py), f"▸ {param}", fill=COLOR_ACCENT, font=font_cn_small)
      draw.text((col1_x+20, py+20), f"   {value}", fill=COLOR_TEXT, font=font_cn_small)
      draw.text((col1_x+20, py+38), f"   → {note}", fill='#88aacc', font=font_cn_small)

  # Column 2: Structural Parameters
  draw.text((col2_x, y+50), "【晶格結構參數】", fill=COLOR_OK, font=font_cn_header)
  params_struct = [
      ("晶格常數 a", "NbTi BCC: ~3.3 Å", "與 Cu (FCC: 3.6Å) 錯配"),
      ("晶格錯配度 δ", "~8.3% (NbTi/Cu)", "臨界厚度 ~10 nm"),
      ("晶粒尺寸 D", "10-100 nm (依 Ts)", "Hall-Petch 關係"),
      ("優選取向", "(110) 或 (200)", "影響超導各向異性"),
      ("位錯密度 ρ", "10¹⁴-10¹⁶ m⁻²", "影響臨界電流 Jc"),
      ("應力狀態 σ", "壓應力 / 張應力", "熱膨脹 + 濺鍍應力"),
  ]
  for i, (param, value, note) in enumerate(params_struct):
      py = y+85+i*65
      draw.text((col2_x, py), f"▸ {param}", fill=COLOR_ACCENT, font=font_cn_small)
      draw.text((col2_x+20, py+20), f"   {value}", fill=COLOR_TEXT, font=font_cn_small)
      draw.text((col2_x+20, py+38), f"   → {note}", fill='#88aacc', font=font_cn_small)

  # Column 3: Sputtering Parameters
  draw.text((col3_x, y+50), "【濺鍍動力學參數】", fill=COLOR_OK, font=font_cn_small)
  params_sput = [
      ("濺鍍壓力 P", "2-10 mTorr", "影響薄膜緻密度"),
      ("Ar 流量 Q", "50-200 sccm", "決定工作壓力"),
      ("DC 功率密度", "1-5 W/cm²", "沉積速率控制"),
      ("沉積速率 R", "1-10 nm/s", "工業級產能關鍵"),
      ("靶基距 d", "50-150 mm", "均勻性 vs 速率"),
      ("磁場強度 B", "200-800 Gauss", "電離效率與均勻性"),
  ]
  for i, (param, value, note) in enumerate(params_sput):
      py = y+85+i*65
      draw.text((col3_x, py), f"▸ {param}", fill=COLOR_ACCENT, font=font_cn_small)
      draw.text((col3_x+20, py+20), f"   {value}", fill=COLOR_TEXT, font=font_cn_small)
      draw.text((col3_x+20, py+38), f"   → {note}", fill='#88aacc', font=font_cn_small)

elif menu==MENU[0]: #NbTi濺鍍
    # ============ TITLE ============
    draw.text((width//2, 40), "工業級大面積 R2R 超導 NbTi 濺鍍製程", fill=COLOR_TITLE, font=font_cn, anchor="mm")
    draw.text((width//2, 85), "Industrial-Scale Roll-to-Roll Superconducting NbTi Sputtering Process", fill='#88aacc', font=font_text, anchor="mm")
    draw.text((width//2, 115), "光刻電路板基材 │ 物理參數全模擬 │ 晶格結構分析", fill=COLOR_SUBTITLE, font=font_cn_small, anchor="mm")

    # ============ R2R SYSTEM SCHEMATIC ============
    y = 160
    box_h = 200

    draw_rounded_rect(draw, (50, y, width-50, y+box_h), 20, '#0a1525', '#00e5ff', 3)
    draw.text((width//2, y+12), "R2R 濺鍍系統架構 │ R2R Sputtering System Architecture", fill=COLOR_TITLE, font=font_cn_header, anchor="mm")

    # Draw R2R schematic
    cx, cy = 150, y+110
    # Unroll roller
    draw.ellipse((cx-30, cy-30, cx+30, cy+30), fill='#333333', outline='#888888', width=2)
    draw.text((cx, cy), "放卷\nUnwind", fill='white', font=font_cn_small, anchor="mm")

    # Tension control
    cx += 80
    draw.rectangle((cx-20, cy-15, cx+20, cy+15), fill='#444444', outline='#888888', width=1)
    draw.text((cx, cy), "張力\n控制", fill='#ffcc88', font=font_cn_small, anchor="mm")

    # Pre-treatment (plasma)
    cx += 80
    draw.rectangle((cx-25, cy-20, cx+25, cy+20), fill='#2a1a3a', outline='#ff6b9d', width=2)
    draw.text((cx, cy), "電漿\n預處理", fill='#ffcc88', font=font_cn_small, anchor="mm")

    # Ti sputtering chamber
    cx += 90
    draw.rectangle((cx-35, cy-30, cx+35, cy+30), fill='#1a1a2e', outline=COLOR_TI, width=2)
    draw.text((cx, cy-10), "Ti 濺鍍", fill='white', font=font_cn_small, anchor="mm")
    draw.text((cx, cy+10), "2-5 nm", fill='#ffcc88', font=font_cn_small, anchor="mm")

    # NbTi sputtering chamber
    cx += 90
    draw.rectangle((cx-40, cy-30, cx+40, cy+30), fill='#1a1a2e', outline=COLOR_NBTI, width=2)
    draw.text((cx, cy-10), "NbTi 濺鍍", fill='white', font=font_cn_small, anchor="mm")
    draw.text((cx, cy+10), "150 nm", fill='#ffcc88', font=font_cn_small, anchor="mm")

    # Cap layer
    cx += 90
    draw.rectangle((cx-30, cy-20, cx+30, cy+20), fill='#1a1a2e', outline=COLOR_CAP, width=2)
    draw.text((cx, cy), "保護層\n5-10 nm", fill='white', font=font_cn_small, anchor="mm")

    # Cooling
    cx += 80
    draw.rectangle((cx-25, cy-15, cx+25, cy+15), fill='#1a2a3a', outline='#00ff88', width=1)
    draw.text((cx, cy), "冷卻", fill='#00ff88', font=font_cn_small, anchor="mm")

    # Rewind
    cx += 80
    draw.ellipse((cx-30, cy-30, cx+30, cy+30), fill='#333333', outline='#888888', width=2)
    draw.text((cx, cy), "收卷\nRewind", fill='white', font=font_cn_small, anchor="mm")

    # Web path line
    draw.line((150, cy, cx, cy), fill='#00e5ff', width=2)

    # System parameters on right
    param_x = cx + 60
    draw.text((param_x, y+50), "▸ 基材寬度: 300-1500 mm", fill=COLOR_TEXT, font=font_cn_small)
    draw.text((param_x, y+75), "▸ 走帶速度: 0.1-10 m/min", fill=COLOR_TEXT, font=font_cn_small)
    draw.text((param_x, y+100), "▸ 張力控制: 50-500 N", fill=COLOR_TEXT, font=font_cn_small)
    draw.text((param_x, y+125), "▸ 腔體數: 3-5 個獨立真空室", fill=COLOR_TEXT, font=font_cn_small)
    draw.text((param_x, y+150), "▸ 靶材配置: 平面磁控靶 / 旋轉靶", fill=COLOR_TEXT, font=font_cn_small)
stImage(img)
