# -*- coding: utf-8 -*-
import io
import os
import re
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

# 1. 多主題色彩系統 (Theme System)
# 風格=["dark_tech", "light_clean", "corporate_blue", "emerald_nature", "warm_warmth"]
ASPECT_RATIOS = ["16:9", "4:3"]
THEMES = {
    "dark_tech": {
        "name": "深藍科技風 (Dark Tech)",
        "bg_color": RGBColor(10, 25, 47),  # #0A192F
        "title_color": RGBColor(255, 255, 255),  # 白色
        "accent_color": RGBColor(0, 210, 255),  # 螢光青藍
        "text_color": RGBColor(240, 240, 240),  # 淺灰
        "card_bg": RGBColor(20, 40, 70),  # 深藍卡片
        "card_border": RGBColor(0, 150, 200),  # 青藍邊框
    },
    "light_clean": {
        "name": "淺色極簡風 (Light Clean)",
        "bg_color": RGBColor(250, 250, 250),
        "title_color": RGBColor(30, 30, 30),
        "accent_color": RGBColor(0, 102, 204),
        "text_color": RGBColor(50, 50, 50),
        "card_bg": RGBColor(235, 240, 245),
        "card_border": RGBColor(180, 200, 220),
    },
    "corporate_blue": {
        "name": "商務經典藍 (Corporate Blue)",
        "bg_color": RGBColor(245, 247, 250),
        "title_color": RGBColor(15, 42, 74),  # 深藍標題
        "accent_color": RGBColor(217, 83, 79),  # 珊瑚紅點綴
        "text_color": RGBColor(40, 50, 60),
        "card_bg": RGBColor(255, 255, 255),  # 純白卡片
        "card_border": RGBColor(200, 215, 230),
    },
    "emerald_nature": {
        "name": "翡翠自然綠 (Emerald Nature)",
        "bg_color": RGBColor(242, 247, 244),
        "title_color": RGBColor(18, 53, 36),  # 森林深綠
        "accent_color": RGBColor(40, 167, 69),  # 翡翠綠
        "text_color": RGBColor(45, 55, 50),
        "card_bg": RGBColor(255, 255, 255),
        "card_border": RGBColor(185, 215, 195),
    },
    "warm_warmth": {
        "name": "暖色大地風 (Warm Warmth)",
        "bg_color": RGBColor(253, 250, 245),
        "title_color": RGBColor(74, 44, 23),  # 暖深棕
        "accent_color": RGBColor(224, 123, 57),  # 暖橘
        "text_color": RGBColor(60, 50, 45),
        "card_bg": RGBColor(255, 255, 255),
        "card_border": RGBColor(230, 210, 190),
    },
}

# 統一字型設定
FONT_FAMILY = "Microsoft JhengHei"

# 風格=list(THEMES./eys())

# ==========================================
# 2. 核心轉檔與排版引擎 (Converter Engine)
# ==========================================
class 簡報圖片: #ModularPresentationConverter

  def __init__(self, theme_key="dark_tech", aspect_ratio="16:9"):
    self.prs = Presentation()
    self.aspect_ratio = aspect_ratio

    # 設定投影片寬高
    if aspect_ratio == "16:9":
      self.prs.slide_width = Inches(13.333)
      self.prs.slide_height = Inches(7.5)
    else:  # 4:3
      self.prs.slide_width = Inches(10)
      self.prs.slide_height = Inches(7.5)

    self.theme = THEMES.get(theme_key, THEMES["dark_tech"])
    self.blank_layout = self.prs.slide_layouts[6]

  def _set_background(self, slide):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = self.theme["bg_color"]

  def _add_header(self, slide, title_text):
    left = Inches(0.8)
    top = Inches(0.5)
    width = self.prs.slide_width - Inches(1.6)
    height = Inches(0.9)

    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p = tf.paragraphs[0]
    p.text = title_text
    p.font.name = FONT_FAMILY
    p.font.size = Pt(26)  # 內容頁標題：26 Pt
    p.font.bold = True
    p.font.color.rgb = self.theme["title_color"]

  def _add_formatted_text(self, paragraph, text, font_size, default_color):
    """解析 **粗體** 並加上統一字型與顏色"""
    parts = re.split(r"(\*\*.*?\*\*)", text)
    for part in parts:
      if not part:
        continue
      run = paragraph.add_run()
      run.font.name = FONT_FAMILY
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
      match = re.match(r"^(#{1,6})\s+", line.strip())
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
      if not line_str or line_str.startswith("---"):
        continue

      match = re.match(r"^(#{1,6})\s+(.*)", line_str)

      if match:
        level = len(match.group(1))
        raw_title = match.group(2).strip()

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
              "images": [],  # 格式: [{"path": ..., "alt": ...}]
              "notes": [],
              "is_main_title": (level == min_level),
          }
          continue

      if current_slide is not None:
        if re.match(
            r"^(?:演講者備忘錄|講稿|Notes?|Presenter Notes)[:：]", line_str, re.I
        ):
          current_slide["is_notes"] = True
          continue

        if current_slide.get("is_notes", False):
          current_slide["notes"].append(line)
        else:
          # 解析圖片與 Alt 文字 ![alt](path)
          img_matches = re.findall(r"!\[(.*?)\]\((.*?)\)", line_str)
          if img_matches:
            for alt_text, img_path in img_matches:
              current_slide["images"].append(
                  {"path": img_path.strip(), "alt": alt_text.strip()}
              )

            clean_line = re.sub(r"!\[.*?\]\(.*?\)", "", line_str).strip()
            if clean_line:
              current_slide["content"].append(clean_line)
          else:
            current_slide["content"].append(line)

    if current_slide:
      slides_data.append(current_slide)

    for s in slides_data:
      s["notes"] = "\n".join(s["notes"]).strip()

    return slides_data

  def _check_local_image(self, img_path):
    """驗證本機圖片是否存在"""
    try:
      clean_filename = os.path.basename(img_path)
      if os.path.exists(clean_filename):
        return clean_filename
      elif os.path.exists(img_path) and not img_path.startswith(
          ("http://", "https://")
      ):
        return img_path
    except Exception:
      pass
    return None

  def _draw_placeholder_box(self, slide, left, top, width, height, alt_text):
    """詰問 4 決策 B：當圖片遺失時生成 Placeholder Box"""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = self.theme["card_bg"]
    shape.line.color.rgb = self.theme["accent_color"]
    shape.line.width = Pt(1.5)

    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = f"🖼️ [圖片遺失]\n{alt_text if alt_text else '請放置對應圖片檔案'}"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(12)
    p.font.color.rgb = self.theme["accent_color"]

  def _render_images_grid(self, slide, img_list, img_area_left, img_width_total):
    """詰問 2 決策 B：網格矩陣排列 (2x2 Grid) 圖片引擎"""
    count = len(img_list)
    if count == 0:
      return

    top_base = Inches(1.6)
    max_height = Inches(5.3)

    if count == 1:
      # 單張圖片：獨佔全高
      img_info = img_list[0]
      valid_path = self._check_local_image(img_info["path"])
      if valid_path:
        try:
          slide.shapes.add_picture(
              valid_path,
              img_area_left,
              top_base,
              width=img_width_total,
          )
        except Exception:
          self._draw_placeholder_box(
              slide,
              img_area_left,
              top_base,
              img_width_total,
              max_height,
              img_info["alt"],
          )
      else:
        self._draw_placeholder_box(
            slide,
            img_area_left,
            top_base,
            img_width_total,
            max_height,
            img_info["alt"],
        )

    elif count == 2:
      # 兩張圖片：上下排列
      each_height = Inches(2.5)
      gap = Inches(0.3)
      for idx, img_info in enumerate(img_list[:2]):
        curr_top = top_base + idx * (each_height + gap)
        valid_path = self._check_local_image(img_info["path"])
        if valid_path:
          try:
            slide.shapes.add_picture(
                valid_path, img_area_left, curr_top, width=img_width_total
            )
          except Exception:
            self._draw_placeholder_box(
                slide,
                img_area_left,
                curr_top,
                img_width_total,
                each_height,
                img_info["alt"],
            )
        else:
          self._draw_placeholder_box(
              slide,
              img_area_left,
              curr_top,
              img_width_total,
              each_height,
              img_info["alt"],
          )

    else:
      # 3~4 張圖片：2x2 矩陣網格排列
      cell_w = (img_width_total - Inches(0.2)) / 2
      cell_h = Inches(2.5)
      gap_x = Inches(0.2)
      gap_y = Inches(0.3)

      for idx, img_info in enumerate(img_list[:4]):
        row = idx // 2
        col = idx % 2
        curr_left = img_area_left + col * (cell_w + gap_x)
        curr_top = top_base + row * (cell_h + gap_y)

        valid_path = self._check_local_image(img_info["path"])
        if valid_path:
          try:
            slide.shapes.add_picture(
                valid_path, curr_left, curr_top, width=cell_w
            )
          except Exception:
            self._draw_placeholder_box(
                slide, curr_left, curr_top, cell_w, cell_h, img_info["alt"]
            )
        else:
          self._draw_placeholder_box(
              slide, curr_left, curr_top, cell_w, cell_h, img_info["alt"]
          )

  # def generate_pptx_bytes(self, slides_data):
  def generate_pptx_bytes(self, slides_data, 檔名=None):
    for i, sdata in enumerate(slides_data):
      slide = self.prs.slides.add_slide(self.blank_layout)
      self._set_background(slide)

      total_width = self.prs.slide_width
      has_images = len(sdata["images"]) > 0

      # ----------------------------------------------------
      # Layout：首頁 (Title Slide)
      # ----------------------------------------------------
      if sdata.get("is_main_title") or (i == 0 and len(slides_data) > 1):
        card_left = Inches(0.8)
        card_width = total_width - Inches(1.6)

        tb = slide.shapes.add_textbox(
            card_left, Inches(2.0), card_width, Inches(4.5)
        )
        tf = tb.text_frame
        tf.word_wrap = True

        # 首頁分類/標語 (14 Pt)
        p_sub = tf.paragraphs[0]
        p_sub.text = "TECHNICAL PRESENTATION"
        p_sub.font.name = FONT_FAMILY
        p_sub.font.size = Pt(14)
        p_sub.font.bold = True
        p_sub.font.color.rgb = self.theme["accent_color"]
        p_sub.space_after = Pt(14)

        # 首頁大標題 (38 Pt)
        p_title = tf.add_paragraph()
        p_title.text = sdata["title"]
        p_title.font.name = FONT_FAMILY
        p_title.font.size = Pt(38)
        p_title.font.bold = True
        p_title.font.color.rgb = self.theme["title_color"]
        p_title.space_after = Pt(16)

        # 首頁摘要文字 (15 Pt)
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

      # ----------------------------------------------------
      # Layout A & B：內容頁 (Content Slide)
      # ----------------------------------------------------
      else:
        self._add_header(slide, sdata["title"])

        # 計算佈局座標 (根據 aspect_ratio & 是否有圖)
        card_left = Inches(0.8)
        card_top = Inches(1.6)
        card_height = Inches(5.3)

        if has_images:
          # Layout A：左文字、右圖片網格
          if self.aspect_ratio == "16:9":
            card_width = Inches(7.2)
            img_left = Inches(8.3)
            img_width = Inches(4.2)
          else:  # 4:3
            card_width = Inches(5.2)
            img_left = Inches(6.3)
            img_width = Inches(2.9)
        else:
          # Layout B：純文字滿版
          card_width = total_width - Inches(1.6)

        # 建立左側文字卡片
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

        # 若有圖片，渲染右側圖片網格 (Layout A)
        if has_images:
          self._render_images_grid(
              slide, sdata["images"], img_left, img_width
          )

        # 填入內容條列文字
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
            font_size = (
                14 if indent_level > 0 else 16
            )  # 大項 16 Pt, 次縮排項 14 Pt

            bullet_run = p.add_run()
            bullet_run.text = bullet_prefix
            bullet_run.font.name = FONT_FAMILY
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
                font_size=16,
                default_color=self.theme["text_color"],
            )

      # 備忘錄 / 講稿
      if sdata["notes"]:
        slide.notes_slide.notes_text_frame.text = sdata["notes"]

    #output = io.BytesIO()
    #self.prs.save(output)
    #output.seek(0)
    #return output
    if not 檔名:
      output = BytesIO()
      self.prs.save(output)
      output.seek(0)
      return output
    else:
      self.prs.save(檔名)
      return None
