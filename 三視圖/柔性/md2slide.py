# -*- coding: utf-8 -*-
import re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

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

class MarkdownToPPTXConverter:
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

    def _add_header(self, slide, title_text, category_text=""):
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.733), Inches(1.0))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        if category_text:
            p0 = tf.paragraphs[0]
            p0.text = category_text.upper()
            p0.font.size = Pt(11)
            p0.font.bold = True
            p0.font.color.rgb = self.theme["accent_color"]
            p0.space_after = Pt(4)
            p1 = tf.add_paragraph()
        else:
            p1 = tf.paragraphs[0]
            
        p1.text = title_text
        p1.font.size = Pt(26)
        p1.font.bold = True
        p1.font.color.rgb = self.theme["title_color"]

    def parse_markdown(self, md_content):
        slides_data = []
        raw_slides = re.split(r'(?m)(?=^(?:#|##|Slide\s+\d+[:：]))', md_content)
        
        for raw in raw_slides:
            raw = raw.strip()
            if not raw:
                continue
                
            lines = raw.split('\n')
            first_line = lines[0].strip()
            title = re.sub(r'^(?:#+|Slide\s+\d+[:：])\s*', '', first_line).strip()
            
            content_lines = []
            notes_lines = []
            is_notes = False
            
            for line in lines[1:]:
                if re.match(r'^(?:演講者備忘錄|講稿|Notes?|Presenter Notes)[:：]', line, re.I):
                    is_notes = True
                    continue
                
                if is_notes:
                    notes_lines.append(line)
                else:
                    content_lines.append(line)
                    
            slides_data.append({
                "title": title,
                "content": content_lines,
                "notes": '\n'.join(notes_lines).strip()
            })
            
        return slides_data

    def render_presentation(self, slides_data, output_filepath):
        for i, sdata in enumerate(slides_data):
            slide = self.prs.slides.add_slide(self.blank_layout)
            self._set_background(slide)
            
            if i == 0 and len(slides_data) > 1:
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
                p_desc.text = '\n'.join([l for l in sdata["content"] if l.strip()])[:200]
                p_desc.font.size = Pt(16)
                p_desc.font.color.rgb = self.theme["text_color"]
            else:
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
                    
                    if line_str.startswith('###') or line_str.startswith('**'):
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
        print(f"✅ 簡報已成功匯出至：{output_filepath}")
