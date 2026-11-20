import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

# Initialize presentation
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# Color Palette
DARK_NAVY = RGBColor(10, 25, 47)      # #0A192F
CYAN_ACCENT = RGBColor(0, 210, 255)   # Bright Cyan
WHITE = RGBColor(255, 255, 255)
LIGHT_GRAY = RGBColor(200, 210, 225)
CARD_BG = RGBColor(20, 40, 70)        # Card container background
CARD_BORDER = RGBColor(0, 150, 200)

def set_slide_background(slide, color):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_header(slide, title_text, category_text=""):
    # Header container
    tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.733), Inches(0.8))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    
    if category_text:
        p0 = tf.paragraphs[0]
        p0.text = category_text.upper()
        p0.font.size = Pt(11)
        p0.font.bold = True
        p0.font.color.rgb = CYAN_ACCENT
        p0.space_after = Pt(4)
        p1 = tf.add_paragraph()
    else:
        p1 = tf.paragraphs[0]
        
    p1.text = title_text
    p1.font.size = Pt(24)
    p1.font.bold = True
    p1.font.color.rgb = WHITE

def set_notes(slide, notes_text):
    notes_slide = slide.notes_slide
    text_frame = notes_slide.notes_text_frame
    text_frame.text = notes_text

# ==========================================
# SLIDE 1: Title Slide
# ==========================================
slide_layout = prs.slide_layouts[6] # blank
slide1 = prs.slides.add_slide(slide_layout)
set_slide_background(slide1, DARK_NAVY)

# Title box
tb1 = slide1.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.333), Inches(3.5))
tf1 = tb1.text_frame
tf1.word_wrap = True

p_sub = tf1.paragraphs[0]
p_sub.text = "QUANTUM COMPUTING OVERVIEW"
p_sub.font.size = Pt(14)
p_sub.font.bold = True
p_sub.font.color.rgb = CYAN_ACCENT
p_sub.space_after = Pt(14)

p_title = tf1.add_paragraph()
p_title.text = "量子電腦與量子硬體技術總覽"
p_title.font.size = Pt(40)
p_title.font.bold = True
p_title.font.color.rgb = WHITE
p_title.space_after = Pt(16)

p_desc = tf1.add_paragraph()
p_desc.text = "從基礎物理原理、主流技術流派、矽光子突破到後量子加密 (PQC) 全景布局"
p_desc.font.size = Pt(18)
p_desc.font.color.rgb = LIGHT_GRAY

set_notes(slide1, "各位好，今天我要為大家介紹的是被譽為下一個世代運算革命的核心技術——『量子電腦』。傳統電腦的發展已經逐漸逼近物理極限，而量子電腦的出現，並不是單純把傳統電腦的 CPU 速度變快，而是透過量子力學的奇特特性，從根本上改變了計算的本質。接下來，我們將帶大家理解這項即將顛覆世界的科技。")

# ==========================================
# SLIDE 2: Core Concept Comparison
# ==========================================
slide2 = prs.slides.add_slide(slide_layout)
set_slide_background(slide2, DARK_NAVY)
add_header(slide2, "核心概念對比：傳統位元 vs 量子位元", "Fundamental Physics")

# Left Box: Bit vs Qubit Info Card
shape_card1 = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.2))
shape_card1.fill.solid()
shape_card1.fill.fore_color.rgb = CARD_BG
shape_card1.line.color.rgb = CARD_BORDER
shape_card1.line.width = Pt(1)

tb2 = slide2.shapes.add_textbox(Inches(1.1), Inches(1.8), Inches(11.133), Inches(4.8))
tf2 = tb2.text_frame
tf2.word_wrap = True

bullets_s2 = [
    ("基本狀態", "傳統位元 (Bit) 為非 0 即 1 的確定態 (如開關)；量子位元 (Qubit) 擁有 0 與 1 的「疊加態」(如旋轉中的硬幣)。"),
    ("運算模式", "傳統位元採「序列式運算」，需逐條路徑測試；量子位元採「指數級平行運算」，能同時探索所有可能路徑。"),
    ("核心物理", "1. 量子疊加 (Superposition)：N 個 Qubit 能同時表示 2^N 個狀態，算力呈指數級暴增。\n2. 量子糾纏 (Entanglement)：微觀狀態強烈聯結，實現超高速協同平行計算。"),
    ("算力成長", "傳統電腦算力隨位元數呈「線性成長」；量子電腦隨位元數呈「指數級爆發」（約 50 個完美 Qubit 即可達成量子霸權）。")
]

for title, desc in bullets_s2:
    p_t = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
    p_t.text = f"• {title}"
    p_t.font.size = Pt(18)
    p_t.font.bold = True
    p_t.font.color.rgb = CYAN_ACCENT
    p_t.space_after = Pt(2)
    
    p_d = tf2.add_paragraph()
    p_d.text = f"  {desc}"
    p_d.font.size = Pt(15)
    p_d.font.color.rgb = WHITE
    p_d.space_after = Pt(14)

set_notes(slide2, "要理解量子電腦，首先要看它與傳統電腦的差異。傳統電腦使用『位元』，就像開關一樣，不是 0 就是 1。如果我們要解開一個迷宮，傳統電腦必須一條路徑一條路徑去試，這叫序列式運算。可是量子電腦使用的是『量子位元』。它擁有『疊加態』，可以同時是 0 也是 1。這使得量子電腦可以『同時』探索迷宮的所有路徑。因此，當傳統電腦的算力呈線性成長時，量子電腦的算力卻是呈指數級暴增，只要 50 個完美的量子位元，其運算能力就能超越當前最強大的超級電腦。")

# ==========================================
# SLIDE 3: Main Hardware Approaches
# ==========================================
slide3 = prs.slides.add_slide(slide_layout)
set_slide_background(slide3, DARK_NAVY)
add_header(slide3, "三大量子硬體技術路線比較", "Hardware Implementations")

approaches = [
    ("超導量子電路", "IBM, Google, 中研院", "• 製程與傳統半導體類似\n• 技術成熟度高、控光成熟\n• 致命傷：必須在接近絕對零度 (~0.015 K) 稀釋冷卻機運作", "接近 0 K (極低溫)"),
    ("囚禁離子 (Ion Trap)", "IonQ, Quantinuum", "• 用雷射鎖住單個原子/離子\n• 量子相干時間長、出錯率極低\n• 挑戰：雷射控制系統極其龐大複雜，擴充規模較慢", "原子振動約 10 K / 室溫控制"),
    ("矽量子點 (Silicon Spin)", "Intel, 台積電合作", "• 利用電子自旋狀態\n• 高度相容現有半導體晶圓廠成熟製程\n• 挑戰：量子位元體積極小，精準控制極難", "接近 0 K (極低溫)")
]

card_w = Inches(3.64)
gap = Inches(0.4)
left_margin = Inches(0.8)

for i, (name, lead, body, temp) in enumerate(approaches):
    c_left = left_margin + i * (card_w + gap)
    card = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left, Inches(1.6), card_w, Inches(5.2))
    card.fill.solid()
    card.fill.fore_color.rgb = CARD_BG
    card.line.color.rgb = CARD_BORDER
    card.line.width = Pt(1)
    
    tb = slide3.shapes.add_textbox(c_left + Inches(0.2), Inches(1.8), card_w - Inches(0.4), Inches(4.8))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p1 = tf.paragraphs[0]
    p1.text = name
    p1.font.size = Pt(20)
    p1.font.bold = True
    p1.font.color.rgb = CYAN_ACCENT
    p1.space_after = Pt(4)
    
    p2 = tf.add_paragraph()
    p2.text = f"代表機構：{lead}"
    p2.font.size = Pt(13)
    p2.font.color.rgb = LIGHT_GRAY
    p2.space_after = Pt(14)
    
    p3 = tf.add_paragraph()
    p3.text = body
    p3.font.size = Pt(14)
    p3.font.color.rgb = WHITE
    p3.space_after = Pt(16)
    
    p4 = tf.add_paragraph()
    p4.text = f"🌡️ 工作溫度：\n{temp}"
    p4.font.size = Pt(13)
    p4.font.bold = True
    p4.font.color.rgb = CYAN_ACCENT

set_notes(slide3, "目前科學界要如何做出一個硬體量子位元呢？主要有三大流派。第一個是『超導量子電路』，這是目前 IBM、Google 以及台灣中研院最主要的研發方向，它的好處是製程與傳統半導體類似，但致命傷是必須在接近絕對零度的稀釋冷凍機裡運作。第二個是『囚禁離子』，用雷射鎖住單個原子，準確度極高，但系統龐大複雜。第三個是『矽量子點』，如果成功就能直接用現有晶圓廠大量製造。各流派都在克服各自的物理限制。")

# ==========================================
# SLIDE 4: Photonic Architecture
# ==========================================
slide4 = prs.slides.add_slide(slide_layout)
set_slide_background(slide4, DARK_NAVY)
add_header(slide4, "下一代硬體革命：矽光子量子電腦架構", "Photonic QC Revolution")

tb4 = slide4.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.733), Inches(1.5))
tf4 = tb4.text_frame
tf4.word_wrap = True
p = tf4.paragraphs[0]
p.text = "• 光的連結與運算：利用積體光路 (PIC) 將光纖微縮至晶片內部，直接以「光子」作為量子位元。\n• 顛覆性優勢：大頻寬、低功耗，最關鍵的是能突破超導流派的低溫物理限制，具備「常溫運作」與高容錯 (Fault-tolerant) 潛力。"
p.font.size = Pt(16)
p.font.color.rgb = WHITE

steps = [
    ("步驟一：雷射光源輸入", "Continuous Laser\n• 持續射出穩定光子流\n• 作為量子位元載體"),
    ("步驟二：PIC 光學晶格微型渠道", "Silicon Waveguide\n• 光子分流、交會與干涉\n• 執行疊加與糾纏等邏輯閘"),
    ("步驟三：單光子偵測讀出", "Single-Photon Detector\n• 光子抵達終點讀出數據\n• 轉化為運算結果")
]

step_w = Inches(3.64)
for i, (stitle, sdesc) in enumerate(steps):
    s_left = left_margin + i * (step_w + gap)
    scard = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, s_left, Inches(3.2), step_w, Inches(2.5))
    scard.fill.solid()
    scard.fill.fore_color.rgb = CARD_BG
    scard.line.color.rgb = CARD_BORDER
    
    stb = slide4.shapes.add_textbox(s_left + Inches(0.2), Inches(3.4), step_w - Inches(0.4), Inches(2.1))
    stf = stb.text_frame
    stf.word_wrap = True
    
    sp1 = stf.paragraphs[0]
    sp1.text = stitle
    sp1.font.size = Pt(16)
    sp1.font.bold = True
    sp1.font.color.rgb = CYAN_ACCENT
    sp1.space_after = Pt(8)
    
    sp2 = stf.add_paragraph()
    sp2.text = sdesc
    sp2.font.size = Pt(14)
    sp2.font.color.rgb = WHITE

# Highlight Box
hcard = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(6.0), Inches(11.733), Inches(0.9))
hcard.fill.solid()
hcard.fill.fore_color.rgb = RGBColor(0, 80, 120)
hcard.line.color.rgb = CYAN_ACCENT

htb = slide4.shapes.add_textbox(Inches(1.0), Inches(6.1), Inches(11.333), Inches(0.7))
htf = htb.text_frame
hp = htf.paragraphs[0]
hp.text = "💡 核心價值：光量子電腦可在室溫下穩定運作，免除龐大 -273℃ 極低溫冷凍設備，是實現大規模量產與容錯運算的大熱門。"
hp.font.size = Pt(15)
hp.font.bold = True
hp.font.color.rgb = WHITE

set_notes(slide4, "在看完傳統三大流派後，我們必須關注矽光子量子電腦架構。傳統超導量子晶片必須鎖在昂貴的冷凍機裡。而矽光子技術是將光學元件微縮整合在矽晶片上，直接用光子作為量子位元。這帶來了顛覆性特點——光子量子電腦有機會在常溫下運作，不需要龐大的冷凍設備，這讓 PsiQuantum 和 Xanadu 等國際大廠脫穎而出。")

# ==========================================
# SLIDE 5: Disruptive Applications
# ==========================================
slide5 = prs.slides.add_slide(slide_layout)
set_slide_background(slide5, DARK_NAVY)
add_header(slide5, "破壞性應用場景", "Transformative Impact")

apps = [
    ("💊 新藥與材料開發", "分子與化學反應模擬", "• 精準模擬複雜分子軌域與化學反應\n• 將長達 10 年的新藥篩選與新型電池材料研發縮短至數天"),
    ("🔒 資安與密碼學", "破解傳統 RSA/ECC", "• Shor 演算法可在數分鐘內破解傳統大數分解加密\n• 促使全球加速轉向後量子加密 (PQC)"),
    ("🧠 最佳化與 AI 加速", "巨量組合最優解", "• 解決物流航線最佳排程、金融資產配置與蒙地卡羅模擬\n• 成倍加速 AI 大模型矩陣訓練與機器學習")
]

for i, (atitle, asub, adesc) in enumerate(apps):
    a_left = left_margin + i * (card_w + gap)
    acard = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, a_left, Inches(1.6), card_w, Inches(5.2))
    acard.fill.solid()
    acard.fill.fore_color.rgb = CARD_BG
    acard.line.color.rgb = CARD_BORDER
    acard.line.width = Pt(1)
    
    atb = slide5.shapes.add_textbox(a_left + Inches(0.2), Inches(1.8), card_w - Inches(0.4), Inches(4.8))
    atf = atb.text_frame
    atf.word_wrap = True
    
    ap1 = atf.paragraphs[0]
    ap1.text = atitle
    ap1.font.size = Pt(20)
    ap1.font.bold = True
    ap1.font.color.rgb = CYAN_ACCENT
    ap1.space_after = Pt(4)
    
    ap2 = atf.add_paragraph()
    ap2.text = asub
    ap2.font.size = Pt(14)
    ap2.font.color.rgb = LIGHT_GRAY
    ap2.space_after = Pt(14)
    
    ap3 = atf.add_paragraph()
    ap3.text = adesc
    ap3.font.size = Pt(15)
    ap3.font.color.rgb = WHITE

set_notes(slide5, "量子電腦能幫人類解決三個破壞性的問題。第一是新藥與材料開發，能精準模擬分子結構，將研發時間從十年縮短到幾天。第二是資安與密碼學，Shor 演算法能破解 RSA 機制，迫使全球轉向 PQC。第三是最佳化與 AI，不管是物流排程、金融風險計算還是加速 AI 模型訓練，都能給出傳統超級電腦算不出的最優解。")

# ==========================================
# SLIDE 6: Post-Quantum Cryptography (PQC)
# ==========================================
slide6 = prs.slides.add_slide(slide_layout)
set_slide_background(slide6, DARK_NAVY)
add_header(slide6, "量子盾牌：後量子加密 (PQC) 防禦布局", "Cybersecurity Defense")

# Table layout for CBOM & PQC Standards
rows, cols = 5, 4
left, top, width, height = Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.2)
table_shape = slide6.shapes.add_table(rows, cols, left, top, width, height)
table = table_shape.table

# Set Column Widths
table.columns[0].width = Inches(2.8)
table.columns[1].width = Inches(2.5)
table.columns[2].width = Inches(3.4)
table.columns[3].width = Inches(3.033)

headers = ["系統 / 應用範疇", "現有密碼學 (受威脅)", "量子威脅暴露", "NIST PQC 建議標準"]
data = [
    ("網銀登入與金鑰交換", "RSA-2048 / ECC", "易被 Shor 演算法瞬間破解", "ML-KEM (Crystals-Kyber)"),
    ("數位簽章 / 身分憑證", "RSA / ECDSA", "簽章可遭偽造，身分防線失守", "ML-DSA (Crystals-Dilithium)"),
    ("資料庫靜態加密", "AES-256", "Grover 演算法可削弱一半強度", "維持 AES-256 / 升級 AES-512"),
    ("韌體更新與程式碼簽章", "RSA-4096", "惡意韌體植入與篡改風險", "SLH-DSA (無狀態雜湊簽章)")
]

for col_idx, text in enumerate(headers):
    cell = table.cell(0, col_idx)
    cell.fill.solid()
    cell.fill.fore_color.rgb = RGBColor(0, 100, 150)
    p = cell.text_frame.paragraphs[0]
    p.text = text
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER

for row_idx, row_data in enumerate(data, start=1):
    for col_idx, text in enumerate(row_data):
        cell = table.cell(row_idx, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = CARD_BG
        p = cell.text_frame.paragraphs[0]
        p.text = text
        p.font.size = Pt(13)
        p.font.color.rgb = CYAN_ACCENT if col_idx == 3 else WHITE

set_notes(slide6, "面對量子破密威脅，解答就是『後量子加密 (PQC)』。PQC 不需要量子電腦才能運作，它是透過更複雜的抗量子數學難題（如格點密碼學），直接部署在現有伺服器與金融系統中。目前美國 NIST 已正式定案核心標準，全球企業正開始進行密碼資產清單 (CBOM) 盤點與系統遷移。")

# ==========================================
# SLIDE 7: Taiwan's Strategic Positioning
# ==========================================
slide7 = prs.slides.add_slide(slide_layout)
set_slide_background(slide7, DARK_NAVY)
add_header(slide7, "台灣在全球量子與抗量子產業的定位", "Taiwan Ecosystem & Advantage")

tw_nodes = [
    ("🏛️ 中研院國家隊突破", "研發端", "• 成功自主研發並發表台灣首台 5 位元超導量子電腦\n• 連線雲端開放學研測試\n• 資訊所積極投入國際 PQC演算法與資安布局"),
    ("🏭 半導體與矽光子鏈", "製造與封裝端", "• 擁有台積電等全球最頂級晶圓製造實力\n• 先進封裝與共封裝光學模組 (CPO) 技術\n• 為光量子電腦與超導極低溫封裝提供絕對護城河"),
    ("🤝 安全與硬體生態系", "產業應用端", "• 工研院與資安聯盟聯手\n• 推動 PQC 抗量子技術結合硬體信任根 (Root of Trust)\n• 打造 PUF 抗量子安全防禦晶片")
]

for i, (ntitle, ntag, ndesc) in enumerate(tw_nodes):
    n_left = left_margin + i * (card_w + gap)
    ncard = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, n_left, Inches(1.6), card_w, Inches(5.2))
    ncard.fill.solid()
    ncard.fill.fore_color.rgb = CARD_BG
    ncard.line.color.rgb = CARD_BORDER
    ncard.line.width = Pt(1)
    
    ntb = slide7.shapes.add_textbox(n_left + Inches(0.2), Inches(1.8), card_w - Inches(0.4), Inches(4.8))
    ntf = ntb.text_frame
    ntf.word_wrap = True
    
    np1 = ntf.paragraphs[0]
    np1.text = ntitle
    np1.font.size = Pt(18)
    np1.font.bold = True
    np1.font.color.rgb = CYAN_ACCENT
    np1.space_after = Pt(4)
    
    np2 = ntf.add_paragraph()
    np2.text = f"定位：{ntag}"
    np2.font.size = Pt(13)
    np2.font.color.rgb = LIGHT_GRAY
    np2.space_after = Pt(14)
    
    np3 = ntf.add_paragraph()
    np3.text = ndesc
    np3.font.size = Pt(14)
    np3.font.color.rgb = WHITE

set_notes(slide7, "最後看台灣的機會。台灣中研院已成功打造自製 5 位元超導量子晶片。更重要的是，不論全球哪一個量子流派勝出，或者是走向最新的矽光子架構，都需要極端微小的半導體製程與先進封裝 (CPO)，這正是台積電等台灣供應鏈的絕對強項。透過整合半導體與 PQC 資安，台灣能無縫將優勢延伸到下一代量子帝國。謝謝大家。")

# Save file
output_path = "量子電腦硬體簡介.pptx"
prs.save(output_path)
print(f"Presentation saved successfully as '{output_path}'.")

