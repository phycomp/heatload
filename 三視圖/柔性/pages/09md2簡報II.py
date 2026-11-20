from streamlit import sidebar, radio, text_input
from glob import glob

MENU, 表單=[], ['麥至投影', '通用', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  MD=glob('*.md')
  麥=radio('MD檔', MD)
# parser = UniversalSlideParser()
# parser.generate_presentation(sample_markdown, "通用型解析器簡報.pptx")
if menu==len(表單):
  pass
elif menu==MENU[0]: #麥至投影
  pass
  if 麥:
    結果=麥至Slide(麥)
    # code()
    狀態.code(結果)
elif menu==MENU[1]: #
  pass
  # from 通用簡報 import UniversalSlideParser
  from 相對層級簡報III import RelativeHierarchyMarkdownToPPTXConverter #MarkdownToPPTXConverter #UniversalSlideParser
  from pathlib import Path
  # parser = UniversalSlideParser()
  if 麥:
    #"通用型解析器簡報.pptx"
    麥=Path(麥)
    新麥=麥.with_suffix('.pptx')
    # parser.generate_presentation(麥, 新麥)
    converter = RelativeHierarchyMarkdownToPPTXConverter(theme_name="dark_tech", aspect_ratio="16:9")
    內容 = converter.parse_markdown(麥.read_text())
    converter.render_presentation(內容, 新麥)

    #converter = RelativeHierarchyMarkdownToPPTXConverter(theme_name="dark_tech", aspect_ratio="16:9")
    #slides_data = converter.parse_markdown(md_content)
    #output_filename = "量子電腦全景總覽_粗體高亮簡報.pptx"
    # converter.render_presentation(slides_data, output_filename)
