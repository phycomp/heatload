# -*- coding: utf-8 -*-
# from streamlit import columns, divider, download_button, header, info, markdown, radio, set_page_config, sidebar, subheader, text_area, title
from streamlit import columns, divider, download_button, header, info, markdown, radio, set_page_config, sidebar, subheader, text_area, title, radio, text_input, code
from glob import glob
# from re import match, sub
from re import I, match, split, sub
# import re
# import streamlit as st
from 相對層級簡報III import 簡報, THEMES #MarkdownToPPTXConverter #UniversalSlideParser
from pathlib import Path

# 設定 Streamlit 頁面
set_page_config(page_title="Markdown 轉 PPTX 簡報預覽工具", layout="wide", page_icon="📊")

# Streamlit UI
title("📊 Markdown 轉 PPTX 簡報預覽與展示工具")
markdown("輸入 Markdown 文字，系統將自動依據**相對標題層級**切分簡報，並即時渲染模擬呈現每一張 Slide 的畫面與講稿！")

# 側邊欄：主題設定
with sidebar:
    header("⚙️ 簡報主題設定")
    theme_choice = radio("選擇簡報視覺主題", options=list(THEMES.keys()), format_func=lambda x: THEMES[x]["name"], horizontal=True)
    aspect_ratio = radio("簡報比例", ["16:9", "4:3"], horizontal=True, index=1)
    theme_cfg = THEMES[theme_choice]

# 輸入區域
# input_md = text_area("✍️ 編輯 Markdown 簡報內容", value=default_md, height=280)
MENU, 表單=[], ['通用', 'FPC簡報', '圖片']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  MD=glob('*.md')
  麥=radio('MD檔', MD)
from streamlit import empty, pyplot
狀態=empty()
態狀=empty()
if menu==len(表單):
  pass
elif menu==MENU[0]: #
  # parser = UniversalSlideParser()
  if 麥:
    #"通用型解析器簡報.pptx"
    麥=Path(麥)
    新麥=麥.with_suffix('.pptx')
    # parser.generate_presentation(麥, 新麥)
    # converter = 簡報(theme_name="dark_tech", aspect_ratio="16:9")
    # 內容 = converter.parse_markdown(麥.read_text())
    # converter.render_presentation(內容, 新麥)
# if input_md:
    converter = 簡報(theme_key=theme_choice, aspect_ratio=aspect_ratio)
    內容=麥.read_text()
    態狀.code(內容)
    slides_data = converter.parse_markdown(內容)
    # 狀態.code(slides_data)
    
    col_head1, col_head2 = columns([3, 1])
    # 狀態.code(slides_data)
    with col_head1:
        # for 頁 in slides_data:
          # code(頁)
        subheader(f"🖼️ 簡報內容即時預覽 (共 {len(slides_data)} 頁)")
    with col_head2:
        # 下載 PPTX 按鈕
        pptx_bytes = converter.render_presentation(slides_data, 新麥) #generate_pptx_bytes, "markdown_presentation.pptx")
        download_button(
            label="📥 匯出 PPTX 簡報檔",
            data=pptx_bytes,
            file_name=f"{新麥}",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
    
    divider()

    from 簡報內容 import 簡報內容
    簡報內容(slides_data)
        # divider()
elif menu==MENU[1]: #
  from FPC簡報 import 簡報FPC, THEMES
  # theme_cfg = THEMES[theme_choice]
  converter = 簡報FPC(theme_key="dark_tech", aspect_ratio="16:9")
  if 麥:
    #"通用型解析器簡報.pptx"
    麥=Path(麥)
    新麥=麥.with_suffix('.pptx')
    # parser.generate_presentation(麥, 新麥)
    # converter = 簡報(theme_name="dark_tech", aspect_ratio="16:9")
    # 內容 = converter.parse_markdown(麥.read_text())
    # converter.render_presentation(內容, 新麥)
# if input_md:
    converter = 簡報(theme_key=theme_choice, aspect_ratio=aspect_ratio)
    內容=麥.read_text()
    態狀.code(內容)
    slides_data = converter.parse_markdown(內容)
  converter.render_presentation(slides_data, 新麥)

  #code(["Parsed slide count:", len(slides_data)])
  #for i, s in enumerate(slides_data):
  #    code(f"Slide {i+1}: {s['title']}")
  from 簡報內容 import 簡報內容
  簡報內容(slides_data, theme_cfg)
  pptx_bytes = converter.render_presentation(slides_data, 新麥) #generate_pptx_bytes, "markdown_presentation.pptx")
  download_button( label="📥 匯出 PPTX 簡報檔", data=pptx_bytes, file_name=f"{新麥}", mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")
elif menu==MENU[2]:
  from 麥圖片II import 簡報圖片, THEMES
  # theme_cfg = THEMES[theme_choice]
  if 麥:
    麥=Path(麥)
    新麥=麥.with_suffix('.pptx')
    # parser.generate_presentation(麥, 新麥)
    # converter = 簡報(theme_name="dark_tech", aspect_ratio="16:9")
    # converter.render_presentation(內容, 新麥)
# if input_md:
    converter = 簡報圖片(theme_key=theme_choice, aspect_ratio=aspect_ratio)
    內容 = converter.parse_markdown(麥.read_text())
    # 內容=麥.read_text()
    # 態狀.code(內容)
  狀態.code(內容)
  pptx_bytes = converter.generate_pptx_bytes(內容) #generate_pptx_bytes, "markdown_presentation.pptx")
  download_button( label="📥 匯出 PPTX 簡報檔", data=pptx_bytes, file_name=f"{新麥}", mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")
