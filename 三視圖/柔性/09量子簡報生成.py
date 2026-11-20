# -*- coding: utf-8 -*-
"""
超導量子晶片系統技術提案 — 可套版 PPT 生成器
需要: pip install python-pptx
"""
from streamlit import code, empty
狀態=empty()

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
import os

# =========================================================
# ★★★ CONFIG：所有可套版設定都集中在這裏 ★★★
# =========================================================

CONFIG = {
    # ---------- 輸出 ----------
    "output_file": "超導量子晶片系統技術提案.pptx",
    "slide_width_inch": 13.333,      # 16:9
    "slide_height_inch": 7.5,

    # ---------- 品牌顏色（RGB 十六進制） ----------
    "color_primary":   "#0B2E59",    # 主色：標題列、封面背景
    "color_secondary": "#1F6FB2",    # 輔色：強調、箭頭
    "color_accent":    "#C0392B",    # 強調色：上行、重點
    "color_text":      "#333333",    # 內文
    "color_text_light":"#FFFFFF",    # 深底上的文字
    "color_bg_light":  "#F2F2F2",    # 淺底

    # ---------- 字體 ----------
    "font_title":  "Microsoft JhengHei",   # 標題字體（微軟正黑）
    "font_body":   "Microsoft JhengHei",   # 內文字體
    "font_size_title": 26,
    "font_size_body":  18,
    "font_size_small": 14,

    # ---------- Logo ----------
    "logo_path": None,               # 例："./logo.png"；None 表示不放
    "logo_position": "top-right",    # top-right / top-left / bottom-right
    "logo_width_inch": 1.2,

    # ---------- 頁尾 ----------
    "show_page_number": True,
    "footer_text": "",               # 例："© 2026 Your Company"

    # ---------- 版面 ----------
    "title_bar_height_inch": 1.0,
    "content_left_inch": 0.7,
    "content_top_inch": 1.3,
    "content_width_inch": 12.0,
    "content_height_inch": 5.8,
}

# =========================================================
# 以下爲引擎，通常不需修改
# =========================================================

def hex_to_rgb(h):
    h = h.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

C_PRIMARY    = hex_to_rgb(CONFIG["color_primary"])
C_SECONDARY  = hex_to_rgb(CONFIG["color_secondary"])
C_ACCENT     = hex_to_rgb(CONFIG["color_accent"])
C_TEXT       = hex_to_rgb(CONFIG["color_text"])
C_TEXT_LIGHT = hex_to_rgb(CONFIG["color_text_light"])
C_BG_LIGHT   = hex_to_rgb(CONFIG["color_bg_light"])

FONT_TITLE = CONFIG["font_title"]
FONT_BODY  = CONFIG["font_body"]

prs = Presentation()
prs.slide_width  = Inches(CONFIG["slide_width_inch"])
prs.slide_height = Inches(CONFIG["slide_height_inch"])
BLANK = prs.slide_layouts[6]


def apply_font(run, font_name, size, bold=False, color=None):
    run.font.name = font_name
    run.font.size = Pt(size)
    run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color
    # 讓中文字體也套用
    rPr = run._r.get_or_add_rPr()
    from pptx.oxml.ns import qn
    ea = rPr.makeelement(qn('a:ea'), {'typeface': font_name})
    rPr.append(ea)


def add_title_bar(slide, title_text):
    bar = slide.shapes.add_shape(
        1, 0, 0, prs.slide_width, Inches(CONFIG["title_bar_height_inch"])
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = C_PRIMARY
    bar.line.fill.background()

    tf = bar.text_frame
    tf.margin_left = Inches(0.5)
    tf.margin_top = Inches(0.15)
    p = tf.paragraphs[0]
    p.text = title_text
    apply_font(p.runs[0] if p.runs else p.add_run(), FONT_TITLE,
               CONFIG["font_size_title"], bold=True, color=C_TEXT_LIGHT)
    p.alignment = PP_ALIGN.LEFT


def add_bullets(slide, bullets):
    tb = slide.shapes.add_textbox(
        Inches(CONFIG["content_left_inch"]),
        Inches(CONFIG["content_top_inch"]),
        Inches(CONFIG["content_width_inch"]),
        Inches(CONFIG["content_height_inch"]),
    )
    tf = tb.text_frame
    tf.word_wrap = True

    first = True
    for item in bullets:
        level, text = item if isinstance(item, tuple) else (0, item)
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.text = ("  " * level) + ("• " if level == 0 else "– ") + text
        size = CONFIG["font_size_body"] - level * 2
        apply_font(p.runs[0], FONT_BODY, size, color=C_TEXT)
        p.space_after = Pt(6)


def add_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def add_logo(slide):
    if not CONFIG["logo_path"] or not os.path.exists(CONFIG["logo_path"]):
        return
    w = Inches(CONFIG["logo_width_inch"])
    margin = Inches(0.3)
    if CONFIG["logo_position"] == "top-right":
        left = prs.slide_width - w - margin
        top = margin
    elif CONFIG["logo_position"] == "top-left":
        left = margin
        top = margin
    else:
        left = prs.slide_width - w - margin
        top = prs.slide_height - Inches(0.9)
    slide.shapes.add_picture(CONFIG["logo_path"], left, top, width=w)


def add_footer(slide, page_num, total):
    if not CONFIG["show_page_number"] and not CONFIG["footer_text"]:
        return
    tb = slide.shapes.add_textbox(
        Inches(CONFIG["slide_width_inch"] - 2.0),
        Inches(CONFIG["slide_height_inch"] - 0.5),
        Inches(1.8), Inches(0.4),
    )
    tf = tb.text_frame
    p = tf.paragraphs[0]
    parts = []
    if CONFIG["footer_text"]:
        parts.append(CONFIG["footer_text"])
    if CONFIG["show_page_number"]:
        parts.append(f"{page_num} / {total}")
    p.text = "  |  ".join(parts)
    apply_font(p.runs[0], FONT_BODY, 11, color=C_SECONDARY)
    p.alignment = PP_ALIGN.RIGHT


def new_slide(title=None, with_bar=True):
    s = prs.slides.add_slide(BLANK)
    if with_bar and title:
        add_title_bar(s, title)
    return s


# =========================================================
# 內容定義（改這裏就能換內容）
# =========================================================

TOTAL = 10

SLIDES = [
    # 1 封面
    {
        "type": "cover",
        "title": "超導量子晶片系統技術提案",
        "subtitle": "從 Qubit 物理到低溫驅動與訊號完整性",
        "lines": [
            "Qubit 原理 · Topology 與驅動 · SCQuit 系統 · Shielded Twist-Pair",
            "核心定位：可擴展、低雜訊的超導量子晶片控制與讀取系統",
        ],
        "notes": "本次簡報面向具工程／物理背景但不熟悉量子硬體的聽衆，以及量子晶片領域的專家。"
                 "我們將從 Qubit 物理出發，依序討論連接拓撲、驅動方式、低溫系統整合，最後聚焦訊號完整性問題。",
    },
    # 2
    {
        "title": "四個層次，一條主線：從 Qubit 到系統",
        "bullets": [
            "系統方塊圖（橫向流程）：",
            (1, "Qubit 物理 → Topology 與驅動 → SCQuit 低溫系統 → Shielded Twist-Pair 訊號鏈"),
            "四個核心問題：",
            (1, "Qubit 如何運作？"),
            (1, "如何連接與驅動？"),
            (1, "低溫系統如何整合？"),
            (1, "訊號爲何需要屏蔽雙絞線？"),
            "提案主張預告：訊號完整性與低溫整合，是可擴展性的真正瓶頸",
        ],
        "notes": "這張圖是整個簡報的骨架。Shielded Twist-Pair 看似只是線材問題，"
                 "但在數百甚至數千 qubit 的系統中，布線的電磁干擾與串擾會直接吃掉 gate fidelity。",
    },
    # 3
    {
        "title": "Qubit：用超導電路做出的人造二能階系統",
        "bullets": [
            "古典 bit vs. Qubit：|ψ⟩ = α|0⟩ + β|1⟩",
            "關鍵量子特性：叠加 · 糾纏 · 量測塌縮",
            "超導 Qubit 核心：Josephson Junction",
            (1, "提供非線性電感 → 能階不等距 → 可選定二能階作爲 qubit"),
            (1, "Transmon 爲當前最主流設計"),
            "三大類型：Transmon / Flux qubit / Phase qubit",
        ],
        "notes": "超導 qubit 的本質是一個人造原子。Josephson Junction 的非線性特性讓能階間距不再等距。",
    },
    # 4
    {
        "title": "T1/T2 與 Gate Fidelity：量子資訊能存活多久？",
        "bullets": [
            "T1（能量松弛時間）：|1⟩ → |0⟩ 的衰減時間",
            "T2（相位相干時間）：叠加態相位關系的維持時間，T2 ≤ 2T1",
            "影響因素：材料損耗、介面缺陷、熱雜訊、電磁干擾",
            "Gate Fidelity：與 T1/T2、crosstalk、控制精度直接相關",
            "核心邏輯：T1/T2 越長 → 可操作次數越多；Fidelity 越高 → 演算法越可靠",
        ],
        "notes": "T1 和 T2 是超導 qubit 的壽命指標。低溫布線的雜訊、驅動訊號的串擾都會直接劣化這兩個指標。",
    },
    # 5
    {
        "title": "Topology：連接方式決定互動能力與可擴展性",
        "bullets": [
            "常見拓樸：Linear chain / 2D Grid / Heavy-Hex / All-to-all",
            "Heavy-Hex 設計邏輯：降低連接數 → 減少頻率碰撞與 crosstalk",
            "取捨：連接度高 → 雙量子閘可用性高，但 crosstalk 風險大",
            "取捨：連接度低 → 佈線簡化，但需更多 SWAP 路由",
            "關鍵句：Topology 是「連接能力」與「雜訊控制」之間的工程取捨",
        ],
        "notes": "Heavy-Hex 是 IBM 目前的主力方案。核心洞察是降低連接數換取更低的串擾和更高的 gate fidelity。",
    },
    # 6
    {
        "title": "微波、Flux 與 Coupler：如何精準控制 Qubit",
        "bullets": [
            "XY 控制（微波驅動）：改變 qubit 狀態，實現 Rabi 振蕩與單量子閘",
            "Z 控制（Flux bias）：調整共振頻率，實現相位閘",
            "Coupler：可調耦合強度，閒置時關閉以降低 crosstalk",
            "驅動訊號需求：低雜訊、低串擾、精準時序、低溫衰減與濾波",
            "驅動精度直接決定 Gate Fidelity",
        ],
        "notes": "驅動是 qubit 的操作介面。每一路控制線都是一條潛在的雜訊入侵路徑。",
    },
    # 7
    {
        "title": "從室溫到毫開爾文：超導量子晶片系統的完整訊號鏈",
        "bullets": [
            "系統三層：室溫層 / 低溫層（稀釋冷凍機）/ 量子層（~10 mK）",
            "下行路徑：室溫脈衝 → 同軸線 → 衰減器／濾波器 → 量子晶片",
            "上行路徑：微弱讀取訊號 → TWPA → HEMT（4K）→ 室溫數位化",
            "低溫關鍵：熱雜訊抑制、訊號衰減與濾波",
        ],
        "notes": "注意下行路徑的漸進式衰減：4K / Still / MXC 各 20 dB，共 60 dB。"
                 "上行第一級放大必須盡可能靠近量子晶片。",
    },
    # 8
    {
        "title": "爲什麼是屏蔽雙絞線？抗 EMI 與降低 Crosstalk 的佈線方案",
        "bullets": [
            "Twist-Pair：兩線絞合 → 共模耦合 → 差動訊號抵銷共模雜訊",
            "Shield：金屬屏蔽層阻隔外部 EMI，防止內部訊號向外輻射",
            "量子系統特殊需求：",
            (1, "Qubit 訊號極微弱，易受雜訊干擾"),
            (1, "多控制線并行 → crosstalk 降低 fidelity"),
            (1, "低損耗、可控阻抗、低熱傳導"),
            "實測配置：manganin 內導體 + 不鏽鋼毛細管屏蔽",
        ],
        "notes": "Shielded Twist-Pair 在量子系統中有兩個角色：雙絞結構抵銷共模雜訊，"
                 "屏蔽層阻隔 EMI。內導體用 manganin 是爲了降低熱傳導。",
    },
    # 9
    {
        "title": "從元件到系統的四大瓶頸",
        "bullets": [
            "Crosstalk：Topology + 驅動 + 佈線三者交叉影響",
            "熱負載：布線密度增加 → 漏熱增加 → 冷凍機負載上升",
            "訊號完整性：EMI、阻抗匹配、衰減配置、接頭品質",
            "可擴展性：Qubit 數量增加 → 控制線線性增長 → 熱預算不可持續",
            "對策：進階 Topology、Cryo-CMOS、Shielded Twist-Pair + RC 濾波、光纖訊號傳輸",
        ],
        "notes": "當 qubit 數量從幾十個增加到幾千個，每一根控制線的漏熱都會累積。光纖方案是有前景的替代路徑。",
    },
    # 10 結論
    {
        "type": "closing",
        "title": "打造可擴展、低雜訊的超導量子晶片系統",
        "table": {
            "headers": ["主題", "關鍵挑戰", "提案價值"],
            "rows": [
                ["Qubit 原理", "T1/T2、Fidelity", "掌握量子資訊基本單位"],
                ["Topology", "Crosstalk vs. 連接度", "優化連接與雜訊的平衡"],
                ["驅動", "精準控制、低雜訊", "提升 Gate Fidelity"],
                ["SCQuit 系統", "熱負載、訊號鏈整合", "低溫系統垂直整合能力"],
                ["Shielded Twist-Pair", "EMI、Crosstalk、熱傳導", "訊號完整性保障"],
            ],
        },
        "closing_lines": [
            "提案主張：",
            "• 以訊號完整性爲核心的系統設計",
            "• 從 Qubit 物理到低溫佈線的垂直整合",
            "• 可擴展至高 qubit 數量的控制與讀取架構",
            "下一步：原型驗證 · Pilot Run · 技術合作",
        ],
        "notes": "超導量子計算的瓶頸已經從能不能做出 qubit，轉移到能不能把成千上萬個 qubit 有效連接和控制。",
    },
]


# =========================================================
# 渲染
# =========================================================

for idx, sd in enumerate(SLIDES, start=1):
    stype = sd.get("type", "content")

    # ---- 封面 ----
    if stype == "cover":
        s = new_slide(with_bar=False)
        bg = s.shapes.add_shape(1, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = C_PRIMARY
        bg.line.fill.background()

        tb = s.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.3), Inches(1.5))
        tf = tb.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]; p.text = sd["title"]; p.alignment = PP_ALIGN.CENTER
        apply_font(p.runs[0], FONT_TITLE, 40, bold=True, color=C_TEXT_LIGHT)

        tb2 = s.shapes.add_textbox(Inches(1.0), Inches(3.8), Inches(11.3), Inches(1.0))
        tf2 = tb2.text_frame; tf2.word_wrap = True
        p2 = tf2.paragraphs[0]; p2.text = sd["subtitle"]; p2.alignment = PP_ALIGN.CENTER
        apply_font(p2.runs[0], FONT_BODY, 22, color=hex_to_rgb("#BFD7EE"))

        tb3 = s.shapes.add_textbox(Inches(1.0), Inches(5.2), Inches(11.3), Inches(1.2))
        tf3 = tb3.text_frame; tf3.word_wrap = True
        for i, line in enumerate(sd["lines"]):
            p3 = tf3.paragraphs[0] if i == 0 else tf3.add_paragraph()
            p3.text = line; p3.alignment = PP_ALIGN.CENTER
            apply_font(p3.runs[0], FONT_BODY, 14, color=hex_to_rgb("#A8C4DE"))

    # ---- 結論頁（含表格）----
    elif stype == "closing":
        s = new_slide(sd["title"])
        tbl_data = sd["table"]
        rows = len(tbl_data["rows"]) + 1
        cols = len(tbl_data["headers"])
        shape = s.shapes.add_table(
            rows, cols,
            Inches(CONFIG["content_left_inch"]),
            Inches(CONFIG["content_top_inch"]),
            Inches(CONFIG["content_width_inch"]),
            Inches(3.0),
        )
        table = shape.table
        for j, h in enumerate(tbl_data["headers"]):
            c = table.cell(0, j); c.text = h
            for p in c.text_frame.paragraphs:
                apply_font(p.runs[0], FONT_TITLE, 14, bold=True, color=C_TEXT_LIGHT)
        for i, row in enumerate(tbl_data["rows"], start=1):
            for j, val in enumerate(row):
                c = table.cell(i, j); c.text = val
                for p in c.text_frame.paragraphs:
                    apply_font(p.runs[0], FONT_BODY, 13, color=C_TEXT)

        tb = s.shapes.add_textbox(
            Inches(CONFIG["content_left_inch"]),
            Inches(4.6),
            Inches(CONFIG["content_width_inch"]),
            Inches(2.2),
        )
        tf = tb.text_frame; tf.word_wrap = True
        for i, line in enumerate(sd["closing_lines"]):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = line
            apply_font(p.runs[0], FONT_BODY, 17,
                       bold=(i == 0),
                       color=C_PRIMARY if i == 0 else C_TEXT)
            p.space_after = Pt(4)

    # ---- 一般內容頁 ----
    else:
        s = new_slide(sd["title"])
        add_bullets(s, sd["bullets"])

    add_notes(s, sd.get("notes", ""))
    add_logo(s)
    add_footer(s, idx, TOTAL)


# =========================================================
# 儲存
# =========================================================
prs.save(CONFIG["output_file"])
狀態.code(f"已生成：{CONFIG['output_file']}")
