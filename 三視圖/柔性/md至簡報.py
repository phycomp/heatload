from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
import re
import io

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


class RelativeHierarchyMarkdownToPPTXConverter:
    def __init__(self, theme_key="dark_tech", aspect_ratio="16:9"):
        self.prs = Presentation()
        if aspect_ratio == "16:9":
            self.prs.slide_width = Inches(13.333)
            self.prs.slide_height = Inches(7.5)
        else:
            self.prs.slide_width = Inches(10)
            self.prs.slide_height = Inches(7.5)
            
        self.theme_key = theme_key
        self.theme = THEMES.get(theme_key, THEMES["dark_tech"])
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

    def _add_formatted_text(self, paragraph, text, font_size, default_color):
        parts = re.split(r'(\*\*.*?\*\*)', text)
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
        lines = md_content.split()
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
            if not line_str or line_str.startswith('---'):
                continue

            match = re.match(r'^(#{1,6})\s+(.*)', line_str)
            
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                title_clean = re.sub(r'^\*\*|\*\*$', '', title)
                
                if level <= min_level + 1:
                    if current_slide:
                        slides_data.append(current_slide)
                    
                    current_slide = {
                        "title": title_clean,
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

        for s in slides_data:
            s["notes"] = ' '.join(s["notes"]).strip()
            
        return slides_data

    def generate_pptx_bytes(self, slides_data):
        for i, sdata in enumerate(slides_data):
            slide = self.prs.slides.add_slide(self.blank_layout)
            self._set_background(slide)
            
            if sdata.get("is_main_title") or (i == 0 and len(slides_data) > 1):
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
                desc_text = ' '.join([l.strip() for l in sdata["content"] if l.strip()])[:200]
                self._add_formatted_text(p_desc, desc_text, font_size=16, default_color=self.theme["text_color"])
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
                    
                    if line_str.startswith('#'):
                        clean_title = re.sub(r'^[#]+\s*', '', line_str).strip()
                        p.space_after = Pt(4)
                        self._add_formatted_text(p, clean_title, font_size=18, default_color=self.theme["accent_color"])
                    elif line_str.startswith('-') or line_str.startswith('*') or re.match(r'^\d+\.', line_str):
                        clean_item = re.sub(r'^[-*•\d\.]+\s*', '', line_str).strip()
                        p.space_after = Pt(6)
                        bullet_run = p.add_run()
                        bullet_run.text = "• "
                        bullet_run.font.size = Pt(15)
                        bullet_run.font.color.rgb = self.theme["text_color"]
                        self._add_formatted_text(p, clean_item, font_size=15, default_color=self.theme["text_color"])
                    else:
                        p.space_after = Pt(8)
                        self._add_formatted_text(p, line_str, font_size=15, default_color=self.theme["text_color"])
            
            if sdata["notes"]:
                notes_slide = slide.notes_slide
                notes_slide.notes_text_frame.text = sdata["notes"]
                
        output = io.BytesIO()
        self.prs.save(output)
        output.seek(0)
        return output

