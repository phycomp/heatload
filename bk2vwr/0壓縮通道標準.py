from streamlit import dataframe, download_button, error, file_uploader, markdown, plotly_chart, progress, pyplot, radio, set_page_config, sidebar, stop, subheader, success, title, warning, text_input, slider
from pathlib import Path
# diff_ilrl_golden_zip.py
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from 黃金Util import 建立標準, 繪圖
from io import BytesIO
import zipfile
import tempfile
import os
import glob
import base64

set_page_config(page_title="Diff-IL/RL Golden vs ZIP", layout="wide")

# ---------- 工具 ----------
# ---------- Sidebar ----------
MENU, 表單=[], ['建立標準', '壓縮', '圖表']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  #title("⚙️ 控制")
  sigma = slider("容差倍數 σ", 1.0, 6.0, 3.0)
  title("🧠 Diff-IL / Diff-RL Golden Standard vs ZIP-批次比對")
  subheader("🏗️ 1. 建立 Golden Standard（上傳 ≥3 個合格檔）") # 1️⃣ 建立 Golden ── 上傳「多張工作表」
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
if menu==len(表單): #
  pass
elif menu==MENU[2]: #
  golden_files = file_uploader("合格檔案（可多選）", accept_multiple_files=True, type=["xlsx"])
elif menu==MENU[1]: #
  golden_files = file_uploader("合格檔案（可多選）", accept_multiple_files=True, type=["xlsx"])
elif menu==MENU[1]: #
  pass
  with sidebar:
    subheader("📁 2. 上傳 ZIP 測試檔（內含多個 xlsx）")
elif menu==MENU[0]: #建立標準
  with sidebar:
    目錄=radio('目錄夾', ['SMPlug2PlugCable80mm', 'TDR_Fail', 'DC120S_GR', 'SN_1106'], horizontal=True)

  根=Path(目錄)
  黃金=建立標準(根)
  #黃金
  for 通道,金 in 黃金.items():
    #金
    繪圖(通道, 金, sigma)
# 2️⃣ 上傳 ZIP 測試檔
