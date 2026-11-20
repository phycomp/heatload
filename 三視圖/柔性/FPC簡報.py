from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

THEMES = {
    "dark_tech": {
        "bg_color": RGBColor(10, 25, 47),        # 深藍背景 (#0A192F)
        "title_color": RGBColor(255, 255, 255),   # 白色主標
        "accent_color": RGBColor(0, 210, 255),   # 螢光青藍
        "text_color": RGBColor(240, 240, 240),    # 淺灰內文
        "card_bg": RGBColor(20, 40, 70),          # 卡片底色
        "card_border": RGBColor(0, 150, 200),     # 框線
    }
}

class 簡報FPC:
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
        left = Inches(0.8)
        top = Inches(0.5)
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
        lines = md_content.split('\n')
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
                raw_title = match.group(2).strip()
                
                # 1. 移除前後粗體標記與 Markdown 記號
                clean_title = re.sub(r'^\*\*|\*\*$', '', raw_title).strip()
                # 2. 自動去除 "第 X 頁：" 或 "Slide X：" 前綴或 "標題：" 前綴
                clean_title = re.sub(r'^(?:第\s*\d+\s*頁|Slide\s*\d+|標題)\s*[:：]\s*', '', clean_title, flags=re.I).strip()
                
                if level <= min_level + 1:
                    if current_slide:
                        slides_data.append(current_slide)
                    
                    current_slide = {
                        "title": clean_title,
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
            s["notes"] = '\n'.join(s["notes"]).strip()
            
        return slides_data

    def render_presentation(self, slides_data, output_filepath):
        for i, sdata in enumerate(slides_data):
            slide = self.prs.slides.add_slide(self.blank_layout)
            self._set_background(slide)
            
            card_left = Inches(0.8)
            card_width = self.prs.slide_width - Inches(1.6)
            
            if sdata.get("is_main_title") or (i == 0 and len(slides_data) > 1):
                # 封面頁
                tb = slide.shapes.add_textbox(card_left, Inches(2.0), card_width, Inches(4.5))
                tf = tb.text_frame
                tf.word_wrap = True
                
                p_sub = tf.paragraphs[0]
                p_sub.text = "TECHNICAL PRESENTATION"
                p_sub.font.size = Pt(14)
                p_sub.font.bold = True
                p_sub.font.color.rgb = self.theme["accent_color"]
                p_sub.space_after = Pt(14)
                
                p_title = tf.add_paragraph()
                p_title.text = sdata["title"]
                p_title.font.size = Pt(32)
                p_title.font.bold = True
                p_title.font.color.rgb = self.theme["title_color"]
                p_title.space_after = Pt(16)
                
                p_desc = tf.add_paragraph()
                desc_text = '\n'.join([l.strip() for l in sdata["content"] if l.strip()])[:300]
                self._add_formatted_text(p_desc, desc_text, font_size=15, default_color=self.theme["text_color"])
            else:
                # 內容頁
                self._add_header(slide, sdata["title"])
                
                card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, card_left, Inches(1.6), card_width, Inches(5.3))
                card.fill.solid()
                card.fill.fore_color.rgb = self.theme["card_bg"]
                card.line.color.rgb = self.theme["card_border"]
                card.line.width = Pt(1)
                
                tb = slide.shapes.add_textbox(card_left + Inches(0.3), Inches(1.8), card_width - Inches(0.6), Inches(4.9))
                tf = tb.text_frame
                tf.word_wrap = True
                
                for line in sdata["content"]:
                    line_str = line.strip()
                    if not line_str:
                        continue
                        
                    p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
                    
                    indent_level = (len(line) - len(line.lstrip())) // 2
                    
                    if line_str.startswith('#'):
                        clean_title = re.sub(r'^[#]+\s*', '', line_str).strip()
                        p.space_after = Pt(4)
                        self._add_formatted_text(p, clean_title, font_size=18, default_color=self.theme["accent_color"])
                    elif line_str.startswith('-') or line_str.startswith('*') or re.match(r'^\d+\.', line_str):
                        clean_item = re.sub(r'^[-*•\d\.]+\s*', '', line_str).strip()
                        p.space_after = Pt(4)
                        
                        bullet_prefix = "  " * indent_level + "• " if indent_level > 0 else "• "
                        font_size = 14 if indent_level > 0 else 15
                        
                        bullet_run = p.add_run()
                        bullet_run.text = bullet_prefix
                        bullet_run.font.size = Pt(font_size)
                        bullet_run.font.color.rgb = self.theme["text_color"]
                        
                        self._add_formatted_text(p, clean_item, font_size=font_size, default_color=self.theme["text_color"])
                    else:
                        p.space_after = Pt(6)
                        self._add_formatted_text(p, line_str, font_size=15, default_color=self.theme["text_color"])
            
            if sdata["notes"]:
                notes_slide = slide.notes_slide
                notes_slide.notes_text_frame.text = sdata["notes"]
                
        self.prs.save(output_filepath)
        print(f"✅ 簡報已成功匯出至：{output_filepath}")
