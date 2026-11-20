# -*- coding: utf-8 -*-
import re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from streamlit import code

THEMES = {
    "dark_tech": {
        "bg_color": RGBColor(10, 25, 47),        # 深藍背景
        "title_color": RGBColor(255, 255, 255),   # 白色主標
        "accent_color": RGBColor(0, 210, 255),   # 螢光青藍
        "text_color": RGBColor(240, 240, 240),    # 淺灰內文
        "card_bg": RGBColor(20, 40, 70),          # 卡片底色
        "card_border": RGBColor(0, 150, 200),     # 框線
    },
    "light_clean": {
        "bg_color": RGBColor(250, 250, 250),      # 淺灰背景
        "title_color": RGBColor(30, 30, 30),      # 深黑主標
        "accent_color": RGBColor(0, 102, 204),    # 典雅藍
        "text_color": RGBColor(50, 50, 50),       # 深灰內文
        "card_bg": RGBColor(235, 240, 245),       # 卡片底色
        "card_border": RGBColor(180, 200, 220),   # 框線
    }
}

class RelativeHierarchyMarkdownToPPTXConverter:
    def __init__(self, theme_name="dark_tech", aspect_ratio="16:9"):
        self.prs = Presentation()
        if aspect_ratio == "16:9":
            self.prs.slide_width = Inches(13.333)
            self.prs.slide_height = Inches(7.5)
        else:
            self.prs.slide_width = Inches(10)
            self.prs.slide_height = Inches(7.5)
            
        self.theme = THEMES.get(theme_name, THEMES["dark_tech"])
        self.blank_layout = self.prs.slide_layouts[6]

    def _set_background(self, slide):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = self.theme["bg_color"]

    def _add_header(self, slide, title_text):
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.733), Inches(1.0))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.size = Pt(26)
        p.font.bold = True
        p.font.color.rgb = self.theme["title_color"]

    def parse_markdown(self, md_content):
        lines = md_content.split('\n')
        
        # 1. 掃描最高層級標題 (Min Level)
        min_level = 999
        for line in lines:
            match = re.match(r'^(#{1,6})\s+', line.strip())
            if match:
                level = len(match.group(1))
                if level < min_level:
                    min_level = level

        if min_level == 999:
            min_level = 1

        slides_data = []
        current_slide = None
        
        for line in lines:
            line_str = line.strip()
            match = re.match(r'^(#{1,6})\s+(.*)', line_str)
            
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                
                # 若標題層級 <= (最高層級 + 1)，表示觸發新簡報頁面 (Slide)
                # 例如：最高層級是 # (1)，則 # (1) 為封面，## (2) 為各頁 Slide
                # 例如：最高層級是 ### (3)，則 ### (3) 為封面，#### (4) 為各頁 Slide
                if level <= min_level + 1:
                    if current_slide:
                        slides_data.append(current_slide)
                    
                    current_slide = {
                        "title": title,
                        "content": [],
                        "notes": [],
                        "is_main_title": (level == min_level)
                    }
                    continue
            
            if current_slide is not None:
                if re.match(r'^(?:演講者備忘錄|講稿|Notes?|Presenter Notes)[:：]', line_str, re.I):
                    current_slide["is_notes"] = True
                    continue
                
                if current_slide.get("is_notes", False):
                    current_slide["notes"].append(line)
                else:
                    current_slide["content"].append(line)

        if current_slide:
            slides_data.append(current_slide)

        # 整理內容格式
        for s in slides_data:
            s["notes"] = '\n'.join(s["notes"]).strip()
            
        return slides_data

    def render_presentation(self, slides_data, output_filepath):
        for i, sdata in enumerate(slides_data):
            slide = self.prs.slides.add_slide(self.blank_layout)
            self._set_background(slide)
            
            if sdata.get("is_main_title") or (i == 0 and len(slides_data) > 1):
                # 簡報總標題 (封面頁)
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
                p_desc.text = '\n'.join([l.strip() for l in sdata["content"] if l.strip()])[:200]
                p_desc.font.size = Pt(16)
                p_desc.font.color.rgb = self.theme["text_color"]
            else:
                # 內容頁 (各頁 Slide)
                self._add_header(slide, sdata["title"])
                
                card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.3))
                card.fill.solid()
                card.fill.fore_color.rgb = self.theme["card_bg"]
                card.line.color.rgb = self.theme["card_border"]
                card.line.width = Pt(1)
                
                tb = slide.shapes.add_textbox(Inches(1.1), Inches(1.8), Inches(11.133), Inches(4.9))
                tf = tb.text_frame
                tf.word_wrap = True
                
                for line in sdata["content"]:
                    line_str = line.strip()
                    if not line_str:
                        continue
                        
                    p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
                    
                    if line_str.startswith('#') or line_str.startswith('**'):
                        p.text = re.sub(r'^[#\*]+|\*+$', '', line_str).strip()
                        p.font.size = Pt(18)
                        p.font.bold = True
                        p.font.color.rgb = self.theme["accent_color"]
                        p.space_after = Pt(4)
                    elif line_str.startswith('-') or line_str.startswith('•'):
                        p.text = "• " + line_str.lstrip('-• ').strip()
                        p.font.size = Pt(15)
                        p.font.color.rgb = self.theme["text_color"]
                        p.space_after = Pt(6)
                    else:
                        p.text = line_str
                        p.font.size = Pt(15)
                        p.font.color.rgb = self.theme["text_color"]
                        p.space_after = Pt(8)
            
            if sdata["notes"]:
                notes_slide = slide.notes_slide
                notes_slide.notes_text_frame.text = sdata["notes"]
                
        self.prs.save(output_filepath)
        code(f"✅ 簡報已成功匯出至：{output_filepath}")
