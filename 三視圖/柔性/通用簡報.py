import os
import re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

class UniversalSlideParser:
    def __init__(self):
        # 1. 初始化 16:9 現代簡報黃金比例
        self.prs = Presentation()
        self.prs.slide_width = Inches(13.333)
        self.prs.slide_height = Inches(7.5)
        self.blank_layout = self.prs.slide_layouts[6] # 完全空白佈局，便於精準排版

        # 2. 定義通用萬用版面配色 (科技極簡風格)
        self.COLOR_DARK_BG  = RGBColor(10, 25, 47)     # 封面深藍底色
        self.COLOR_LIGHT_BG = RGBColor(246, 248, 250)   # 內頁舒適淺灰底色
        self.COLOR_PRIMARY  = RGBColor(0, 122, 255)    # 亮藍核心標題/重點色
        self.COLOR_TEXT_MAIN = RGBColor(33, 37, 41)    # 深灰內文
        self.COLOR_TEXT_MUTED = RGBColor(100, 110, 120)# 輔助次要文字
        self.COLOR_CARD_BG   = RGBColor(255, 255, 255)  # 純白卡片底色
        self.COLOR_BORDER    = RGBColor(218, 222, 229)  # 邊框灰色
        self.COLOR_ZEBRA     = RGBColor(235, 239, 245)  # 表格斑馬紋交叉色
        self.FONT_NAME = "Microsoft JhengHei"          # 統一微軟正黑體

    def _set_font(self, run, size=14, bold=False, color=None, italic=False):
        """通用字體配置輔助器"""
        run.font.name = self.FONT_NAME
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = color if color else self.COLOR_TEXT_MAIN

    def _clean_md_line(self, line):
        """移除 Markdown 贅字與粗體符號"""
        line = re.sub(r'\*\*(.*?)\*\*', r'\1', line) # 去除 ** 粗體標籤
        return line.strip()

    def parse_markdown(self, md_content):
        """核心解析器：將 MD 文本切分成結構化的投影片清單"""
        # 依據 "Slide X" 或 "# " 進行邏輯換頁切分
        raw_slides = re.split(r'(?i)(?=Slide\s+\d+|#\s+)', md_content)
        parsed_slides = []

        for raw in raw_slides:
            if not raw.strip():
                continue
            
            lines = raw.split('\n')
            slide_data = {
                "title": "未命名投影片",
                "is_cover": False,
                "notes": "",
                "tables": [],
                "bullets": [],
                "cards": []
            }
            
            in_table = False
            current_table = []
            in_notes = False
            
            for line in lines:
                clean = line.strip()
                if not clean:
                    continue
                
                # 📢 偵測：演講者備忘錄 / 逐字稿講稿
                if "演講者備忘錄" in clean or "逐字講稿" in clean or "Notes:" in clean:
                    in_notes = True
                    in_table = False
                    continue
                if in_notes:
                    # 將接下來的所有內容都歸為備忘錄
                    slide_data["notes"] += line + "\n"
                    continue

                # 📢 偵測：投影片大標題
                if clean.startswith('#') or re.match(r'(?i)Slide\s+\d+[:：]?', clean):
                    # 判斷是否為第一頁或包含「封面」字樣
                    if "封面" in clean or len(parsed_slides) == 0:
                        slide_data["is_cover"] = True
                    title_text = re.sub(r'^(#+\s*|Slide\s+\d+[:：]?\s*)', '', clean)
                    slide_data["title"] = self._clean_md_line(title_text)
                    continue

                # 📢 偵測：表格資料 (Markdown Table 語法 '|')
                if clean.startswith('|'):
                    if '-|' in clean or '--' in clean: # 跳過分隔線
                        continue
                    in_table = True
                    row_cells = [self._clean_md_line(c) for c in clean.split('|')[1:-1]]
                    current_table.append(row_cells)
                    continue
                else:
                    if in_table and current_table:
                        slide_data["tables"].append(current_table)
                        current_table = []
                        in_table = False

                # 📢 偵測：列表清單 (Bullet Points)
                if clean.startswith('•') or clean.startswith('-') or clean.startswith('*'):
                    bullet_text = re.sub(r'^([•\-*]\s*)', '', clean)
                    # 萬用判斷：如果清單內容帶有冒號 '：'，自動升格解構為「卡片型資料」
                    if '：' in bullet_text and len(bullet_text.split('：')[0]) < 15:
                        parts = bullet_text.split('：', 1)
                        slide_data["cards"].append({"title": parts[0].strip(), "desc": parts[1].strip()})
                    else:
                        slide_data["bullets"].append(self._clean_md_line(bullet_text))
                    continue
                
                # 一般段落內文也歸入 Bullet 清單中展示
                if not in_table and not in_notes:
                    slide_data["bullets"].append(self._clean_md_line(clean))

            if in_table and current_table:
                slide_data["tables"].append(current_table)
            
            slide_data["notes"] = slide_data["notes"].strip()
            parsed_slides.append(slide_data)
            
        return parsed_slides

    def generate_presentation(self, md_content, output_filename="output_presentation.pptx"):
        """主控渲染引擎：將結構化數據自動對應到最佳簡報排版佈局"""
        slides_data = self.parse_markdown(md_content)

        for data in slides_data:
            slide = self.prs.slides.add_slide(self.blank_layout)
            
            # 1. 寫入演講者備忘錄
            if data["notes"]:
                slide.notes_slide.notes_text_frame.text = data["notes"]

            # 2. 渲染邏輯：若是封面
            if data["is_cover"]:
                bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, self.prs.slide_width, self.prs.slide_height)
                bg.fill.solid()
                bg.fill.fore_color.rgb = self.COLOR_DARK_BG
                bg.line.fill.background()
                
                tx_box = slide.shapes.add_textbox(Inches(1.0), Inches(2.8), Inches(11.333), Inches(3.0))
                tf = tx_box.text_frame
                tf.word_wrap = True
                p = tf.paragraphs[0]
                run = p.add_run()
                run.text = data["title"]
                self._set_font(run, size=44, bold=True, color=RGBColor(255,255,255))
                continue

            # 3. 渲染邏輯：一般內頁 (套用明亮背景與標準標題)
            bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, self.prs.slide_width, self.prs.slide_height)
            bg.fill.solid()
            bg.fill.fore_color.rgb = self.COLOR_LIGHT_BG
            bg.line.fill.background()

            title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.5), Inches(1.0))
            tf_title = title_box.text_frame
            tf_title.word_wrap = True
            p_title = tf_title.paragraphs[0]
            run_title = p_title.add_run()
            run_title.text = data["title"]
            self._set_font(run_title, size=28, bold=True, color=self.COLOR_DARK_BG)

            # 布局決策樹 A：如果包含表格資料 (優先展示表格)
            if data["tables"]:
                table_data = data["tables"][0]
                rows = len(table_data)
                cols = len(table_data[0]) if rows > 0 else 0
                
                if cols > 0:
                    table_shape = slide.shapes.add_table(rows, cols, Inches(0.8), Inches(1.8), Inches(11.733), Inches(4.5))
                    table = table_shape.table
                    
                    for r_idx, row in enumerate(table_data):
                        for c_idx, val in enumerate(row):
                            cell = table.cell(r_idx, c_idx)
                            cell.fill.solid()
                            if r_idx == 0:
                                cell.fill.fore_color.rgb = self.COLOR_PRIMARY
                            else:
                                cell.fill.fore_color.rgb = self.COLOR_CARD_BG if r_idx % 2 != 0 else self.COLOR_ZEBRA
                            
                            p = cell.text_frame.paragraphs[0]
                            p.alignment = PP_ALIGN.CENTER if r_idx == 0 else PP_ALIGN.LEFT
                            run = p.add_run()
                            run.text = val
                            self._set_font(run, size=13, bold=(r_idx==0 or c_idx==0), 
                                            color=RGBColor(255,255,255) if r_idx == 0 else self.COLOR_TEXT_MAIN)

            # 布局決策樹 B：如果包含卡片型資料 (橫向多欄並排版型)
            elif data["cards"]:
                card_count = len(data["cards"])
                card_width = Inches(11.733) if card_count == 1 else (Inches(11.733) - (Inches(0.4) * (card_count - 1))) / card_count
                card_height = Inches(4.5)
                
                for idx, card in enumerate(data["cards"]):
                    cx = Inches(0.8) + idx * (card_width + Inches(0.4))
                    c_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(1.8), card_width, card_height)
                    c_box.fill.solid()
                    c_box.fill.fore_color.rgb = self.COLOR_CARD_BG
                    c_box.line.color.rgb = self.COLOR_BORDER
                    
                    tf_c = c_box.text_frame
                    tf_c.word_wrap = True
                    tf_c.margin_left = Inches(0.2)
                    tf_c.margin_right = Inches(0.2)
                    tf_c.margin_top = Inches(0.3)
                    
                    p_ct = tf_c.paragraphs[0]
                    r_ct = p_ct.add_run()
                    r_ct.text = card["title"] + "\n\n"
                    self._set_font(r_ct, size=16, bold=True, color=self.COLOR_PRIMARY)
                    
                    p_cd = tf_c.add_paragraph()
                    r_cd = p_cd.add_run()
                    r_cd.text = card["desc"]
                    self._set_font(r_cd, size=13, bold=False, color=self.COLOR_TEXT_MAIN)

            # 布局決策樹 C：若只有純文字清單 (標準左側列點版型)
            elif data["bullets"]:
                tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.733), Inches(4.5))
                tf_b = tx_box.text_frame
                tf_b.word_wrap = True
                for idx, bullet in enumerate(data["bullets"]):
                  p = tf_b.paragraphs[0] if idx == 0 else tf_b.add_run().paragraph
                  p.space_after = Pt(14)
                  run = p.add_run()
                  run.text = "•  " + bullet
                  self._set_font(run, size=16, bold=False, color=self.COLOR_TEXT_MAIN)
                  self.prs.save(output_filename)
                  print(f"🎉 萬用 Parser 簡報轉換成功！已儲存為：{output_filename}")


