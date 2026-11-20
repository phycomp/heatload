from streamlit import sidebar, slider, text_input, radio, session_state, dataframe, pyplot, empty
from pathlib import Path
from pandas import read_excel, DataFrame
from openpyxl import load_workbook

MENU, 表單=[], ['智能', '參數', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
if menu==len(表單): #
  pass
elif menu==MENU[1]: #
  from 時域分析 import TDRAnalyzer  #TDR_Analysis_Report
  狀態=empty()
  根=Path('DC120S_GR/HS')
  with sidebar:
    檔案=radio('檔案', 根.glob('*.xlsx'), horizontal=True)
  if 檔案:
    analyzer = TDRAnalyzer(檔案) # 創建分析器實例
    狀態.code(analyzer.load_data())
    #if analyzer.load_data():  加載數據
    fig=analyzer.generate_visualization('TDR_Analysis_Report.png') # 生成視覺化報告
    pyplot(fig)
        #analyzer.generate_excel_report('TDR_Analysis_Report.xlsx') # 生成Excel報告
elif menu==MENU[0]: #智能
