from streamlit import dataframe, download_button, pyplot, set_page_config, sidebar, stop, tabs, title, radio, number_input, text_input, empty
from pathlib import Path
from matplotlib.pyplot import subplots
from numpy import abs, angle, log10
from pandas import DataFrame, concat
from skrf import Network
from skrf.plotting import smith
from io import BytesIO

set_page_config(page_title="TouchStone Viewer", layout="wide")
title("📈  TouchStone Viewer（免資料庫）")

# ---------- 左側上傳 ----------

# ---------- 控制項 ----------
unit = radio("Y 軸單位", ["dB", "mag"])
p1   = number_input("源端口", 1, 8, 1)
p2   = number_input("目標端口", 1, 8, 2)

MENU, 表單=[], ['清單', '', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
if menu==len(表單): #
  pass
elif menu==MENU[2]: #
  uploaded = file_uploader(
      "選擇 TouchStone 檔案",
      type=['s1p','s2p','s3p','s4p','snp'],
      accept_multiple_files=True
  )
  if not uploaded: stop()
elif menu==MENU[1]: #
  pass
elif menu==MENU[0]: #清單
  nets = []
  狀態=empty()
  根=Path("~/Desktop/bk2測試/FAIL__20260106_153324")
  for 檔 in 根.expanduser().rglob('*.s*p'):
      #buf = BytesIO(f.read_bytes())
      #buf.name = f.name          # 避開 AttributeError
      net = Network(檔)
      nets.append(net)
  狀態.code(net.__dict__)
# ---------- 繪圖區 ----------
tab1, tab2, tab3 = tabs(["線圖","Smith","數據/下載"])

with tab1:
    fig, ax = subplots(figsize=(7,4))
    for net in nets:
        freq = net.f / 1e9
        s    = net.s[:, p2-1, p1-1]
        y    = 20*log10(abs(s)) if unit=="dB" else abs(s)
        ax.plot(freq, y, label=net.name)
    ax.set_xlabel("Freq (GHz)")
    ax.set_ylabel(f"S{p1}{p2} ({unit})")
    ax.legend(); ax.grid(True)
    pyplot(fig)

with tab2:
    fig, ax = subplots(figsize=(5,5))
    for net in nets:
      s = net.s[:, p2-1, p1-1]
      r_max = abs(s).max()
      smithR = max(1., r_max*1.05)
      smith(smithR=smithR, ax=ax)#, label=net.name)
      ax.legend()
      pyplot(fig)

with tab3:
    # 彙整所有檔案資料
    資框 = []
    狀態=empty()
    狀態.code(nets)
    for net in nets:
        s = net.s[:, p2-1, p1-1]
        tmp = DataFrame({
            "File": net.name,
            "Freq_Hz": net.f,
            "Mag": abs(s),
            "Phase_rad": angle(s),
            "dB": 20*log10(abs(s))
        })
        資框.append(tmp)
    if 資框:
      全資框 = concat(資框, ignore_index=True)
      全資框
      csv = 全資框.to_csv(index=False)
      download_button("📥 下載 CSV", 全資框, f"S{p1}{p2}.csv", mime="text/csv")
