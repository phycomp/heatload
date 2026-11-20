from re import I, match as reMatch, split as reSplit, sub
# import re
from io import BytesIO
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
# from streamlit import code

# Markdown Content from the user prompt

THEMES = {
    "dark_tech": {
        "name": "深藍科技風 (Dark Tech)",
        "bg_color": RGBColor(10, 25, 47),
        "title_color": RGBColor(255, 255, 255),
        "accent_color": RGBColor(0, 210, 255),
        "text_color": RGBColor(240, 240, 240),
        "card_bg": RGBColor(20, 40, 70),
        "card_border": RGBColor(0, 150, 200),
        "hex_bg": "#0A192F",
        "hex_card": "#142846",
        "hex_title": "#FFFFFF",
        "hex_accent": "#00D2FF",
        "hex_text": "#F0F0F0"
    },
    "light_clean": {
        "name": "淺色極簡風 (Light Clean)",
        "bg_color": RGBColor(250, 250, 250),
        "title_color": RGBColor(30, 30, 30),
        "accent_color": RGBColor(0, 102, 204),
        "text_color": RGBColor(50, 50, 50),
        "card_bg": RGBColor(235, 240, 245),
        "card_border": RGBColor(180, 200, 220),
        "hex_bg": "#FAFAFA",
        "hex_card": "#EBF0F5",
        "hex_title": "#1E1E1E",
        "hex_accent": "#0066CC",
        "hex_text": "#323232"
    }
}

class 簡報:
    def __init__(self, theme_key="dark_tech", aspect_ratio="16:9"):
        self.prs = Presentation()
        if aspect_ratio == "16:9":
            self.prs.slide_width = Inches(13.333)
            self.prs.slide_height = Inches(7.5)
        else:
            self.prs.slide_width = Inches(10)
            self.prs.slide_height = Inches(7.5)

        self.theme = THEMES.get(theme_key, THEMES["dark_tech"])
        self.blank_layout = self.prs.slide_layouts[6]
        # code(self.blank_layout.__dict__)
        #{'_element': <CT_Presentation '<p:presentation>' at 0x75adb0f7bd70>, '_part': <pptx.parts.presentation.PresentationPart object at 0x75ae17bc2490>}
        #{'_element': <CT_Presentation '<p:presentation>' at 0x75adb0f78890>, '_part': <pptx.parts.presentation.PresentationPart object at 0x75ae17bc2cb0>, 'slide_masters': <pptx.slide.SlideMasters object at 0x75adb07d10d0>}

    def _set_background(self, slide):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = self.theme["bg_color"]

    def _add_header舊(self, slide, title_text):
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.733), Inches(1.0))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.size = Pt(26)
        p.font.bold = True
        p.font.color.rgb = self.theme["title_color"]
    def _add_header(self, slide, title_text):
        # 左邊界 0.8 英吋
        left = Inches(0.8)
        top = Inches(0.5)
        # 動態計算寬度：總寬度 - 左右邊界 (0.8 * 2 = 1.6 英吋)
        width = self.prs.slide_width - Inches(1.6)
        height = Inches(1.0)

        tb = slide.shapes.add_textbox(left, top, width, height)
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p = tf.paragraphs[0]
        p.text = title_text
        p.font.size = Pt(26)
        p.font.bold = True
        p.font.color.rgb = self.theme["title_color"]

    def _add_formatted_text(self, paragraph, text, font_size, default_color):
        """解析 **粗體** 文字並新增至段落 Run 中，保持粗體效果"""
        parts = reSplit(r'(\*\*.*?\*\*)', text)
        for part in parts:
            if not part:
                continue
            run = paragraph.add_run()
            run.font.size = Pt(font_size)
            if part.startswith('**') and part.endswith('**'):
                run.text = part[2:-2]
                run.font.bold = True
                run.font.color.rgb = self.theme["accent_color"]
            else:
                run.text = part
                run.font.bold = False
                run.font.color.rgb = default_color

    def parse_markdown(self, md_content):
        lines = md_content.split('\n')

        # 1. 掃描最高層級標題 (Min Level)
        min_level = 999
        for line in lines:
            匹配 = reMatch(r'^(#{1,6})\s+', line.strip())
            if 匹配:
                level = len(匹配.group(1))
                if level < min_level:
                    min_level = level

        if min_level == 999:
            min_level = 1

        slides_data = []
        current_slide = None

        for line in lines:
            line_str = line.strip()
            if not line_str or line_str.startswith('---'):
                continue

            匹配 = reMatch(r'^(#{1,6})\s+(.*)', line_str)

            if 匹配:
                level = len(匹配.group(1))
                title = 匹配.group(2).strip()
                title_clean = sub(r'^\*\*|\*\*$', '', title)

                if level <= min_level + 1:
                    if current_slide:
                        slides_data.append(current_slide)
                    # title_clean = sub(r'^Slide\s*\d+\s*[:：]\s*|^第\s*\d+\s*頁[:：]\s*', '', title_clean, flags=I).strip()
                    title_clean = sub(r'^Slide\s*\d+\s*[:：]\s*|^第\s*\d+\s*頁[:：]\s*', '', title_clean, flags=I).strip()
                    current_slide = {
                        "title": title_clean,
                        "content": [],
                        "notes": [],
                        "is_main_title": (level == min_level)
                    }
                    continue
            #if match:
            #    raw_title = match.group(2).strip()
            #    clean_title = sub(r'^\*\*|\*\*$', '', raw_title).strip() # 1. 移除 Markdown 星號
            #    clean_title = sub(r'^Slide\s*\d+\s*[:：]\s*', '', clean_title, flags=I).strip() # 2. 自動去除 "Slide 數字：" 前綴
            #    current_slide = {
            #        "title": clean_title,  # 清洗後的乾淨標題
            #        "content": [],
            #        "notes": []
            #    }
            if current_slide is not None:
                if reMatch(r'^(?:演講者備忘錄|講稿|Notes?|Presenter Notes)[:：]', line_str, I):
                    current_slide["is_notes"] = True
                    continue

                if current_slide.get("is_notes", False):
                    current_slide["notes"].append(line)
                else:
                    current_slide["content"].append(line)

        if current_slide:
            slides_data.append(current_slide)

        for s in slides_data:
            s["notes"] = '\n'.join(s["notes"]).strip()

        return slides_data

    def render_presentation(self, slides_data, output_filepath):
        for i, sdata in enumerate(slides_data):
            slide = self.prs.slides.add_slide(self.blank_layout)
            self._set_background(slide)

            if sdata.get("is_main_title") or (i == 0 and len(slides_data) > 1):
                # 封面頁
                tb = slide.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.333), Inches(4.0))
                tf = tb.text_frame
                tf.word_wrap = True

                p_sub = tf.paragraphs[0]
                p_sub.text = "PRESENTATION"
                p_sub.font.size = Pt(14)
                p_sub.font.bold = True
                p_sub.font.color.rgb = self.theme["accent_color"]
                p_sub.space_after = Pt(14)

                p_title = tf.add_paragraph()
                p_title.text = sdata["title"]
                p_title.font.size = Pt(38)
                p_title.font.bold = True
                p_title.font.color.rgb = self.theme["title_color"]
                p_title.space_after = Pt(16)

                p_desc = tf.add_paragraph()
                desc_text = '\n'.join([l.strip() for l in sdata["content"] if l.strip()])[:200]
                self._add_formatted_text(p_desc, desc_text, font_size=22, default_color=self.theme["text_color"])
            else:
                # 各頁簡報
                self._add_header(slide, sdata["title"])

                # card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.3))
                # 動態計算卡片寬度 (留出左右邊界各 0.8)
                card_left = Inches(0.8)
                card_top = Inches(1.6)
                card_width = self.prs.slide_width - Inches(1.6)
                card_height = Inches(5.3)

                card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, card_left, card_top, card_width, card_height)
                card.fill.solid()
                card.fill.fore_color.rgb = self.theme["card_bg"]
                card.line.color.rgb = self.theme["card_border"]
                card.line.width = Pt(1)

                # tb = slide.shapes.add_textbox(Inches(1.1), Inches(1.8), Inches(11.133), Inches(4.9))
                # 動態計算卡片內文字方塊寬度 (卡片內 padding 各留 0.3)
                tb_left = card_left + Inches(0.3)
                tb_top = Inches(1.8)
                tb_width = card_width - Inches(0.6)
                tb_height = Inches(4.9)

                tb = slide.shapes.add_textbox(tb_left, tb_top, tb_width, tb_height)
                tf = tb.text_frame
                tf.word_wrap = True

                for line in sdata["content"]:
                    line_str = line.strip()
                    if not line_str:
                        continue

                    p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]

                    if line_str.startswith('#'):
                        clean_title = sub(r'^[#]+\s*', '', line_str).strip() #標題
                        # clean_title=sub(r'Slide \d.', '', clean_title)
                        p.space_after = Pt(4)
                        self._add_formatted_text(p, clean_title, font_size=24, default_color=self.theme["accent_color"])
                    elif line_str.startswith('-') or line_str.startswith('*') or reMatch(r'^\d+\.', line_str):
                        clean_item = sub(r'^[-*•\d\.]+\s*', '', line_str).strip()  #bulletin內文
                        p.space_after = Pt(6)
                        bullet_run = p.add_run()
                        bullet_run.text = "• "
                        bullet_run.font.size = Pt(15)
                        bullet_run.font.color.rgb = self.theme["text_color"]
                        self._add_formatted_text(p, clean_item, font_size=22, default_color=self.theme["text_color"])
                    else:
                        p.space_after = Pt(8)
                        self._add_formatted_text(p, line_str, font_size=22, default_color=self.theme["text_color"])

            if sdata["notes"]:
                notes_slide = slide.notes_slide
                notes_slide.notes_text_frame.text = sdata["notes"]

        output = BytesIO()
        self.prs.save(output)
        output.seek(0)
        return output
        # self.prs.save(output_filepath)
        # code(f"✅ 簡報已成功匯出至：{output_filepath}")
