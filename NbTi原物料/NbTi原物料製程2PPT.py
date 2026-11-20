import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# 建立簡報
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# 定義顏色
DARK_BLUE = RGBColor(0x0D, 0x1B, 0x2A)
LIGHT_BLUE = RGBColor(0x1B, 0x4F, 0x72)
ACCENT = RGBColor(0x00, 0xA8, 0xE8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GRAY = RGBColor(0xCC, 0xCC, 0xCC)

def add_title_slide(prs, title, subtitle, reporter):
    blank_layout = prs.slide_layouts[6]  # blank
    slide = prs.slides.add_slide(blank_layout)
    
    # 背景
    background = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    background.fill.solid()
    background.fill.fore_color.rgb = DARK_BLUE
    background.line.fill.background()
    
    # 標題
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(2.0), Inches(11.7), Inches(1.5))
    tf = title_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(40)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER
    
    # 副標題
    sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(3.6), Inches(11.7), Inches(1.0))
    tf = sub_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = subtitle
    p.font.size = Pt(22)
    p.font.color.rgb = ACCENT
    p.alignment = PP_ALIGN.CENTER
    
    # 報告人
    rep_box = slide.shapes.add_textbox(Inches(0.8), Inches(5.2), Inches(11.7), Inches(0.6))
    tf = rep_box.text_frame
    p = tf.paragraphs[0]
    p.text = reporter
    p.font.size = Pt(18)
    p.font.color.rgb = GRAY
    p.alignment = PP_ALIGN.CENTER
    
    return slide

def add_content_slide(prs, title, bullets, img_path=None, img_pos=None, img_size=None):
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    
    # 背景
    background = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    background.fill.solid()
    background.fill.fore_color.rgb = DARK_BLUE
    background.line.fill.background()
    
    # 標題區塊
    title_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.1))
    title_shape.fill.solid()
    title_shape.fill.fore_color.rgb = LIGHT_BLUE
    title_shape.line.fill.background()
    
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.25), Inches(12.3), Inches(0.7))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = WHITE
    
    # 內文區塊
    content_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.4), Inches(7.5), Inches(5.8))
    tf = content_box.text_frame
    tf.word_wrap = True
    
    for i, bullet in enumerate(bullets):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = bullet
        p.font.size = Pt(18)
        p.font.color.rgb = WHITE
        p.space_before = Pt(12)
        p.level = 0
    
    # 插入圖片
    if img_path and os.path.exists(img_path):
        if img_pos is None:
            img_pos = (Inches(8.3), Inches(1.4))
        if img_size is None:
            img_size = (Inches(4.5), Inches(5.5))
        try:
            pic = slide.shapes.add_picture(img_path, img_pos[0], img_pos[1])
            # 等比例縮放至指定寬度
            if img_size:
                pic.width = img_size[0]
        except Exception as e:
            print(f"圖片插入失敗: {img_path}, {e}")
    
    return slide

# === Slide 1: 封面 ===
add_title_slide(prs,
    "鈮鈦（NbTi）低溫量子傳輸柔性線材完整製程與設備規劃",
    "類 Delft Cri/oFlex 3 標準之高密度多通道超導帶狀線開發專案",
    "報告人：Josh / Uleam")

# === Slide 2: 專案目標與產品定義 ===
img_path_s2 = "/mnt/agents/images/10_Superconducting_quantum_computers.png"
add_content_slide(prs, "Slide 1: 專案目標與產品定義（Product Definition）",
    [
        "🎯 開發標竿：Delft Circuits Cri/oFlex® 3 (CF3)",
        "📐 幾何尺寸：總厚度約 0.3 mm，最小彎曲半徑 R = 5 mm",
        "🔌 通道設計：高密度、多通道（標準 8 通道）柔性微波帶狀線",
        "❄️ 低溫極限：滿足稀釋冷凍機 mK 等級（< 20 mK）極低溫運作",
        "📡 微波性能：4–8 GHz 量子讀取頻段，特性阻抗維持 50 Ω ± 2 Ω"
    ],
    img_path=img_path_s2, img_pos=(Inches(8.0), Inches(1.3)), img_size=(Inches(4.8), Inches(5.5))
)

# === Slide 3: 技術路線決策樹 ===
img_path_s3 = "/mnt/agents/images/5_High_density_superconducting_interconnect.png"
add_content_slide(prs, "Slide 2: 技術路線決策樹（Decision Tree Summary）",
    [
        "🌳 核心製程節點：",
        "• 材料配比：Nb-47 wt% Ti 經典超導比例（Tc ≈ 9.2 K）",
        "• 鍍膜工藝：真空感應熔煉單靶 → 高真空磁控濺鍍（Sputtering）",
        "• 基材選擇：商業級 Kapton 薄膜 + 表面 Ar 電漿活化",
        "• 結構堆疊：全單面多層順序沉積（Sequential Deposition）",
        "• 介電層 & 圖案化：液態 PI 塗佈 + 氟基氣體反應離子蝕刻（RIE）",
        "• 終端封裝：無焊式集成微型連接器（彈簧壓接觸點）"
    ],
    img_path=img_path_s3, img_pos=(Inches(8.0), Inches(1.3)), img_size=(Inches(4.8), Inches(5.5))
)

# === Slide 4: 剖面結構與製程堆疊順序 ===
img_path_s4 = "/mnt/agents/images/6_Effects_of_the_thin_film_thickness.png"
add_content_slide(prs, "Slide 3: 剖面結構與製程堆疊順序（Layer Stack）",
    [
        "📐 帶狀線（Stripline）由下至上順序：",
        "1. 上接地層 (Top Ground)：NbTi 超導薄膜 (~150 nm)",
        "2. 第二介電層 (Dielectric 2)：液態聚醯亞胺 PI (~數微米)",
        "3. 中間訊號線 (Signal Line)：NbTi 超導薄膜 (~150 nm)",
        "   — 黃光 + RIE 圖案化",
        "4. 第一介電層 (Dielectric 1)：液態 PI（含層間互連導通孔 Via）",
        "5. 下接地層 (Bottom Ground)：NbTi 超導薄膜 (~150 nm)",
        "6. 核心基底 (Substrate)：商用不銹鋼/陶瓷載板上的 Kapton 柔性薄膜"
    ],
    img_path=img_path_s4, img_pos=(Inches(8.0), Inches(1.3)), img_size=(Inches(4.8), Inches(5.5))
)

# === Slide 5: 階段一：前端 NbTi 合金靶材製備 ===
img_path_s5 = "/mnt/agents/images/7_Superconducting_phase_transitions.png"
add_content_slide(prs, "Slide 4: 階段一：前端 NbTi 合金靶材製備",
    [
        "🏭 工藝流程：",
        "• 真空感應熔煉（VIM）：高純度 Nb/Ti 塊材（≥99.99%）",
        "  依 53:47 原子比重複熔煉 3–5 次，確保無 Ti 偏析",
        "• 熱鍛與軋製：消除鑄態粗大晶粒，細化晶粒以提升後續濺鍍薄膜均勻度",
        "• 靶材繫結：精密機加工至目標尺寸，真空銦焊（Indium Bonding）至無氧銅背板",
        "",
        "🛠️ 台灣潛在合作設備/材料商：",
        "• 材料加工：榮剛材料（GMTC）、精剛精密科技"
    ],
    img_path=img_path_s5, img_pos=(Inches(8.0), Inches(1.3)), img_size=(Inches(4.8), Inches(5.5))
)

# === Slide 6: 階段二：基材前處理與底層沉積 ===
img_path_s6 = "/mnt/agents/images/3_Plasma_surface_treatment_process.png"
add_content_slide(prs, "Slide 5: 階段二：基材前處理與底層沉積",
    [
        "⚡ 解決低溫剝落的核心關鍵：",
        "• 真空脫水烘烤：Kapton 薄膜於真空置入前烘烤，徹底移除高分子吸附水氣",
        "• In-situ 電漿轟擊（關鍵）：在濺鍍腔體內以 Ar 電漿原位轟擊 Kapton 表面，",
        "  打斷聚合物鍵結，大幅提升 NbTi 與塑料介面的原子級附著力",
        "• 下接地層濺鍍：沉積 100–200 nm 鈮鈦薄膜，控制基板溫度避免 PI 變形",
        "",
        "🛠️ 台灣對應設備商（磁控濺鍍機）：",
        "• PVD 設備：凌嘉科技、友威科技、北儒精密"
    ],
    img_path=img_path_s6, img_pos=(Inches(8.0), Inches(1.3)), img_size=(Inches(4.8), Inches(5.5))
)

# === Slide 7: 階段三：微細加工與多層順序沉積 ===
img_path_s7 = "/mnt/agents/images/8_Modifying_wetting_properties_of_PI.png"
add_content_slide(prs, "Slide 6: 階段三：微細加工與多層順序沉積",
    [
        "🌀 介電層與訊號線循環：",
        "• 介電層塗佈與固化：旋塗液態 PI 膜，嚴格控溫烘烤，",
        "  確保咪唑化（Imidization）程度 99% 以降低低溫介電損耗（tan δ）",
        "• 訊號線黃光微影：塗佈光阻、精密對準曝光、顯影出 8 通道微波線路",
        "• 氟基乾式蝕刻（RIE）：通入 SF₆ / O₂ 或 CF₄ / O₂ 進行反應離子蝕刻，",
        "  獲取高陡峭度、無毛邊的微米級超導線路",
        "",
        "🛠️ 台灣對應設備商：",
        "• 塗佈/烘烤：志聖工業、億尚科技",
        "• 黃光/蝕刻機（RIE）：辛耘企業、弘塑科技、東捷科技"
    ],
    img_path=img_path_s7, img_pos=(Inches(8.0), Inches(1.3)), img_size=(Inches(4.8), Inches(5.5))
)

# === Slide 8: 階段四：雷射切單與終端無焊封裝 ===
img_path_s8 = "/mnt/agents/images/4_Precision_polymer_cutting_with_femtosecond.png"
add_content_slide(prs, "Slide 7: 階段四：雷射切單與終端無焊封裝",
    [
        "🏁 後段加工與低溫驗證：",
        "• 超快雷射切單：利用皮秒/飛秒不發熱雷射，將大面積 Kapton 板",
        "  精準裁切為 0.3 mm 寬度帶狀線，邊緣不碳化",
        "• 無焊連接器集成：線材末端設計裸露焊墊（Pad），",
        "  裝配非磁性（鈹銅/鈦）微型彈簧夾具，實現與稀釋冷凍機線路的可重複插拔壓接",
        "• 低溫微波測試：置入 < 20 mK 冷凍機，使用 VNA 量測 S 參數，",
        "  驗證阻抗（50 Ω）與高頻內部品質因子（Qi）",
        "",
        "🛠️ 台灣對應設備商：",
        "• 雷射切割機：鈦昇科技、均豪精密、東捷科技"
    ],
    img_path=img_path_s8, img_pos=(Inches(8.0), Inches(1.3)), img_size=(Inches(4.8), Inches(5.5))
)

# === Slide 9: 專案三大核心風險與控管機制 ===
img_path_s9 = "/mnt/agents/images/2_NEW_Additions_to_FormFactor_Cryogenics.png"
add_content_slide(prs, "Slide 8: 專案三大核心風險與控管機制",
    [
        "⚠️ 實作控制點：",
        "",
        "1. 低溫熱應力開裂（CTE Mismatch）",
        "   → 對策：製程中調整濺鍍氣壓與功率，使 NbTi 薄膜帶有輕微「壓應力」，",
        "      抵消低溫收縮的拉應力",
        "",
        "2. 介電損耗與量子雜訊",
        "   → 對策：嚴格執行 PI 固化曲線，避免殘留溶劑；製程環境維持高潔淨度",
        "",
        "3. 特性阻抗偏移",
        "   → 對策：利用 RIE 確保蝕刻線寬變異數 < ±5%，動態微調介電層塗佈厚度"
    ],
    img_path=img_path_s9, img_pos=(Inches(8.0), Inches(1.3)), img_size=(Inches(4.8), Inches(5.5))
)

# 儲存
output_path = "./NbTi_Cryogenic_Flex_Cable_製程規劃.pptx"
prs.save(output_path)
print(f"PPT 已儲存至: {output_path}")
print(f"總投影片數: {len(prs.slides)}")
