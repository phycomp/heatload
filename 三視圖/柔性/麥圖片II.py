from os.path import basename, exists
from io import BytesIO
from re import I, findall, match as reMatch, sub
import os
import re
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

THEMES = {
    "dark_tech": {
        "bg_color": RGBColor(10, 25, 47),
        "title_color": RGBColor(255, 255, 255),
        "accent_color": RGBColor(0, 210, 255),
        "text_color": RGBColor(240, 240, 240),
        "card_bg": RGBColor(20, 40, 70),
        "card_border": RGBColor(0, 150, 200),
    }
}


class 簡報圖片:

  def __init__(self, theme_key="dark_tech", aspect_ratio="16:9"):
    self.prs = Presentation()
    self.aspect_ratio = aspect_ratio
    if aspect_ratio == "16:9":
      self.prs.slide_width = Inches(13.333)
      self.prs.slide_height = Inches(7.5)
    else:
      self.prs.slide_width = Inches(10)
      self.prs.slide_height = Inches(7.5)

    self.theme = THEMES.get(theme_key, THEMES["dark_tech"])
    self.blank_layout = self.prs.slide_layouts[6]

  def _fetch_image(self, img_path):
    """只讀取同目錄或指定路徑下的本機圖片檔案，不存取網路"""
    try:
      # 取得純檔名（例如：dilution_fridge.png）
      clean_filename = os.path.basename(img_path)

      # 優先檢查當前目錄下是否存在該檔案
      if os.path.exists(clean_filename):
        return clean_filename
      elif os.path.exists(img_path) and not img_path.startswith(
          ("http://", "https://")
      ):
        return img_path
      else:
        print(f"⚠️ 找不到本機圖片檔案: {clean_filename}")
    except Exception as e:
      print(f"⚠️ 載入本機圖片失敗: {img_path} ({e})")
    return None

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
    parts = re.split(r"(\*\*.*?\*\*)", text)
    for part in parts:
      if not part:
        continue
      run = paragraph.add_run()
      run.font.size = Pt(font_size)
      if part.startswith("**") and part.endswith("**"):
        run.text = part[2:-2]
        run.font.bold = True
        run.font.color.rgb = self.theme["accent_color"]
      else:
        run.text = part
        run.font.bold = False
        run.font.color.rgb = default_color

  def parse_markdown(self, md_content):
    lines = md_content.split("\n")
    min_level = 999
    for line in lines:
      匹配 = reMatch(r"^(#{1,6})\s+", line.strip())
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
      if not line_str or line_str.startswith("---"):
        continue

      匹配 = reMatch(r"^(#{1,6})\s+(.*)", line_str)

      if 匹配:
        level = len(匹配.group(1))
        raw_title = 匹配.group(2).strip()

        clean_title = re.sub(r"^\*\*|\*\*$", "", raw_title).strip()
        clean_title = re.sub(
            r"^(?:第\s*\d+\s*頁|Slide\s*\d+|標題)\s*[:：]\s*",
            "",
            clean_title,
            flags=re.I,
        ).strip()

        if level <= min_level + 1:
          if current_slide:
            slides_data.append(current_slide)

          current_slide = {
              "title": clean_title,
              "content": [],
              "images": [],  # 解析到的圖片連結
              "notes": [],
              "is_main_title": (level == min_level),
          }
          continue

      if current_slide is not None:
        if reMatch(
            r"^(?:演講者備忘錄|講稿|Notes?|Presenter Notes)[:：]", line_str, re.I
        ):
          current_slide["is_notes"] = True
          continue

        if current_slide.get("is_notes", False):
          current_slide["notes"].append(line)
        else:
          # 提取 Markdown 與 HTML 圖片語法
          img_match_md = re.findall(r"!\[.*?\]\((.*?)\)", line_str)
          img_match_html = re.findall(
              r'<img\s+[^>]*src=["\'](.*?)["\']', line_str, re.I
          )
          all_imgs = img_match_md + img_match_html

          if all_imgs:
            current_slide["images"].extend(all_imgs)
            clean_line = re.sub(r"!\[.*?\]\(.*?\)", "", line_str)
            clean_line = re.sub(
                r'<img\s+[^>]*src=["\'].*?["\'].*?>', "", clean_line, flags=re.I
            ).strip()
            if clean_line:
              current_slide["content"].append(clean_line)
          else:
            current_slide["content"].append(line)

    if current_slide:
      slides_data.append(current_slide)

    for s in slides_data:
      s["notes"] = "\n".join(s["notes"]).strip()

    return slides_data

  def generate_pptx_bytes(self, slides_data, 檔名=None):
    for i, sdata in enumerate(slides_data):
      slide = self.prs.slides.add_slide(self.blank_layout)
      self._set_background(slide)

      total_width = self.prs.slide_width
      has_images = len(sdata["images"]) > 0

      if sdata.get("is_main_title") or (i == 0 and len(slides_data) > 1):
        # 封面頁
        card_left = Inches(0.8)
        card_width = total_width - Inches(1.6)

        tb = slide.shapes.add_textbox(
            card_left, Inches(2.0), card_width, Inches(4.5)
        )
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
        desc_text = "\n".join(
            [l.strip() for l in sdata["content"] if l.strip()]
        )[:300]
        self._add_formatted_text(
            p_desc,
            desc_text,
            font_size=15,
            default_color=self.theme["text_color"],
        )

      else:
        self._add_header(slide, sdata["title"])

        # 根據是否有圖片與簡報比例動態規劃版面
        if has_images:
          if self.aspect_ratio == "16:9":
            card_width = Inches(7.2)
            img_left = Inches(8.3)
            img_width = Inches(4.2)
          else:
            card_width = Inches(5.2)
            img_left = Inches(6.3)
            img_width = Inches(2.9)

          card_left = Inches(0.8)
          card_top = Inches(1.6)
          card_height = Inches(5.3)

          card = slide.shapes.add_shape(
              MSO_SHAPE.ROUNDED_RECTANGLE,
              card_left,
              card_top,
              card_width,
              card_height,
          )
          card.fill.solid()
          card.fill.fore_color.rgb = self.theme["card_bg"]
          card.line.color.rgb = self.theme["card_border"]
          card.line.width = Pt(1)

          tb = slide.shapes.add_textbox(
              card_left + Inches(0.3),
              Inches(1.8),
              card_width - Inches(0.6),
              Inches(4.9),
          )
          tf = tb.text_frame
          tf.word_wrap = True

          # 右側放置本機圖片
          img_top = Inches(1.6)
          max_imgs = min(len(sdata["images"]), 2)
          for idx, img_path in enumerate(sdata["images"][:max_imgs]):
            img_file = self._fetch_image(img_path)
            if img_file:
              curr_top = (
                  img_top + idx * Inches(2.7) if max_imgs > 1 else img_top
              )
              try:
                slide.shapes.add_picture(
                    img_file, img_left, curr_top, width=img_width
                )
              except Exception as e:
                print(f"⚠️ 插入圖片失敗: {e}")
        else:
          card_left = Inches(0.8)
          card_width = total_width - Inches(1.6)
          card_top = Inches(1.6)
          card_height = Inches(5.3)

          card = slide.shapes.add_shape(
              MSO_SHAPE.ROUNDED_RECTANGLE,
              card_left,
              card_top,
              card_width,
              card_height,
          )
          card.fill.solid()
          card.fill.fore_color.rgb = self.theme["card_bg"]
          card.line.color.rgb = self.theme["card_border"]
          card.line.width = Pt(1)

          tb = slide.shapes.add_textbox(
              card_left + Inches(0.3),
              Inches(1.8),
              card_width - Inches(0.6),
              Inches(4.9),
          )
          tf = tb.text_frame
          tf.word_wrap = True

        for line in sdata["content"]:
          line_str = line.strip()
          if not line_str:
            continue

          p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
          indent_level = (len(line) - len(line.lstrip())) // 2

          if line_str.startswith("#"):
            clean_title = re.sub(r"^[#]+\s*", "", line_str).strip()
            p.space_after = Pt(4)
            self._add_formatted_text(
                p,
                clean_title,
                font_size=18,
                default_color=self.theme["accent_color"],
            )
          elif (
              line_str.startswith("-")
              or line_str.startswith("*")
              or re.match(r"^\d+\.", line_str)
          ):
            clean_item = re.sub(r"^[-*•\d\.]+\s*", "", line_str).strip()
            p.space_after = Pt(4)

            bullet_prefix = (
                "  " * indent_level + "• " if indent_level > 0 else "• "
            )
            font_size = 14 if indent_level > 0 else 15

            bullet_run = p.add_run()
            bullet_run.text = bullet_prefix
            bullet_run.font.size = Pt(font_size)
            bullet_run.font.color.rgb = self.theme["text_color"]

            self._add_formatted_text(
                p,
                clean_item,
                font_size=font_size,
                default_color=self.theme["text_color"],
            )
          else:
            p.space_after = Pt(6)
            self._add_formatted_text(
                p,
                line_str,
                font_size=15,
                default_color=self.theme["text_color"],
            )

      if sdata["notes"]:
        notes_slide = slide.notes_slide
        notes_slide.notes_text_frame.text = sdata["notes"]
    if not 檔名:
      output = BytesIO()
      self.prs.save(output)
      output.seek(0)
      return output
    else:
      self.prs.save(檔名)
      return None
