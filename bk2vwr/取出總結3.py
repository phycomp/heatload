from streamlit import code, columns, dataframe, download_button, error, expander, header, info, markdown, metric, plotly_chart, set_page_config, sidebar, subheader, tabs, text_area, title, warning, write, radio, slider, file_uploader, empty, pyplot, session_state, number_input
from numpy import nan
from pandas import DataFrame, ExcelFile, read_excel, to_numeric
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from io import BytesIO
import json
from tdrUtil import *
from bkUtil import rcrsvFiles, 讀取文件
from 時域分析 import TDRAnalyzer  #TDR_Analysis_Report

set_page_config( page_title="通用Excel數據分析儀表板", page_icon="📊", layout="wide") # 設置頁面
MENU, 表單=[], ["上傳單個文件", "分析目錄下所有文件", '智能', '時域分析']

for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  subheader("📊 通用Excel數據分析儀表板")
  #title("⚙️ 控制")
  menu=radio("選擇分析模式:", MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  #本益比=slider("最高本益比(PE)", 0, 100, 25)
  #srch=text_input('搜尋', '')
  mode = radio("功能", ["建立Golden","比對新檔","管理Golden"], horizontal=True)
  z0     = number_input("特性阻抗 Z₀ (Ω)", value=50)
  sigma  = slider("容差倍數 σ", 1.0, 6.0, 3.0)

if menu==len(表單): #
  pass
elif menu==MENU[3]: #
  總資框=session_state['總資框']
  試算表=list(總資框.keys())
  #表狀態=empty()
  with sidebar:
    工表 = radio("📄 選擇工作表", 試算表, horizontal=True, index=0) #['checkout', 'cycle', 'pulse', 'heater']
  if 工表: #'checkout' ---- 讀檔 & 篩選 ----
    資框=總資框[工表]
  資框
  狀態=empty()
  #根=Path('DC120S_GR/HS')
  #with sidebar:
  #  檔案=radio('檔案', 根.glob('*.xlsx'), horizontal=True)
  #if 檔案:
  時資框=總資框['TDR Data']
  頻資框=總資框['Data']
  建立標準(頻資框, 時資框, sigma)#時頻域視覺
  #analyzer=TDRAnalyzer(資框) # 創建分析器實例
  #狀態.code(analyzer.load_data())
  #if analyzer.load_data():  加載數據
  #fig=analyzer.generate_visualization()#'TDR_Analysis_Report.png') # 生成視覺化報告
  #pyplot(fig)
elif menu==MENU[2]: #
  #from 參數智能 import SParameterAnalyzer
  with sidebar:
    目錄=radio('目錄夾', ['SMPlug2PlugCable80mm', 'TDR_Fail', 'DC120S_GR', 'SN_1106'], horizontal=True)
  #根=Path(目錄)
  #黃金=
  建立標準(Path(目錄), sigma)
  #with sidebar:
  #  檔案=radio('檔案', 根.rglob('*.xlsx'), horizontal=True)
  #if 檔案:
  #  try:總資框=session_state[檔案]
  #  except:總資框=session_state[檔案]=read_excel(檔案, sheet_name=None)
  #  #總資框=DataFrame([dset])
  #  總資框
  #試算表=list(總資框.keys())
  #表狀態=empty()
  with sidebar:
    工表 = radio("📄 選擇工作表", 試算表, horizontal=True, index=0) #['checkout', 'cycle', 'pulse', 'heater']
  if 工表: #'checkout' ---- 讀檔 & 篩選 ----
    資框=總資框[工表]
  資框
  狀態=empty()
  #根=Path('DC120S_GR/HS')
  #with sidebar:
  #  檔案=radio('檔案', 根.glob('*.xlsx'), horizontal=True)
  #if 檔案:
  時資框=總資框['TDR Data']
  頻資框=總資框['Data']
  from tdrUtil import *
  建立標準(頻資框, 時資框, sigma)#時頻域視覺
elif menu==MENU[1]: #
  #directory_path = sidebar.text_input("目錄路徑(留空使用當前目錄):", ".")
  #if sidebar.button("掃描Excel文件"):
      #excel_files = get_excel_files(directory_path)
      #文件 = sidebar.multiselect("選擇要分析的文件:", excel_files)
      #files_to_process = [os.path.join(directory_path, f) for f in 文件]
  #with sidebar:
  #  目錄=radio("目錄路徑(留空使用當前目錄):", ["TDRReportRawData", 'TDR_Fail', 'SMPlug2PlugCable80mm', 'SN_1106'], horizontal=True, key=0)  #sidebar.text_input
  #  #process_directory_files(visualizer, PureWindowsPath(xlsx))#.as_posix())
  #  XLSX = rcrsvFiles(目錄)
  #  #code(['XLSX', XLSX])
  #  文件 = radio("選擇要分析的文件:", XLSX, horizontal=True, key=1)  #sidebar.multiselect

  #if 文件:
  #  總資框=session_state[文件]=read_excel(文件, sheet_name=None)#ExcelFile(文件)
  #  #總資框['TDR Data']
  #  讀取文件(總資框)
    
    # 創建標簽頁用于不同文件
    #xlsxTAB=list(map(lambda x:x.name, XLSX))
    #分頁 = tabs(xlsxTAB)
    #for ndx, file_path in enumerate(XLSX):
    #    #fullPath=f'{file_path}'
    #    with 分頁[ndx]:
    #        try:
                # 讀取Excel文件
  根=Path('DC120S_GR/HS')
  with sidebar:
    檔案=radio('檔案', 根.glob('*/*.xlsx'), horizontal=True)
  if 檔案:
    try:總資框=session_state[檔案]=session_state['總資框']
    except:總資框=session_state[檔案]=session_state['總資框']=read_excel(檔案, sheet_name=None)
    讀取文件(總資框)
    #總資框=DataFrame([dset])
    #總資框
    #試算表=list(總資框.keys())
  # #表狀態=empty()
    #with sidebar:
    #  工表 = radio("📄 選擇工作表", 試算表, horizontal=True, index=0) #['checkout', 'cycle', 'pulse', 'heater']
    #if 工表: #'checkout' ---- 讀檔 & 篩選 ----
    #  資框=總資框[工表]
    #  資框#=切克(資框)
elif menu==MENU[0]: #
  with sidebar:
    uploaded_file = file_uploader("選擇Excel文件", type=["xlsx", "xls"])
    files_to_process = [uploaded_file] if uploaded_file else []
    XLSX=None
