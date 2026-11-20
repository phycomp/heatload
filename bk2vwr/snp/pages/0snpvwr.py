from streamlit import caption, columns, dataframe, expander, file_uploader, pyplot, radio, selectbox, set_page_config, sidebar, slider, stop, success, title, text_input, empty, subheader
from matplotlib.pyplot import subplots
from pathlib import Path
from numpy import abs, log10
from pandas import DataFrame
# snp_viewer.py
import numpy as np
from skrf import Network
from skrf.plotting import smith
from re import findall

狀態=empty()
def 讀取(內容):
  net = Network(檔) #StringIO(內容))
  #狀態.code(檔.stem)
  #Tx3+_Rx3+_Tx3-_Rx3-_Ch3_Tr1_SDD21_Diff IL_THRU_3
  if 符合:=findall('.*?_(Ch\d+)_(Tr\d+)_(SDD\d+)_(.*?)_\d+', 檔.stem):
    頻道,徑,S參數,差動=符合[0]
    #狀態.code([頻道,徑,S參數,差動])
    資訊='|'.join([頻道,徑,S參數,差動])
    #success(f"讀入成功：{資訊}")    |  端口數：{net.nports}  |  頻率點：{net.frequency.npoints}")
  return 資訊, net
set_page_config(page_title="SNP Viewer", layout="wide")
MENU, 表單=[], ['snp格式', '', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  subheader("📈  TouchStone (sNp) 參數可視化")
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
if menu==len(表單): #
  pass
elif menu==MENU[1]: #
  uploaded = file_uploader("請上傳 .s1p / .s2p / .sNp 文件", type=['s1p','s2p','s3p','s4p','snp']) # ---------- 1. 文件上傳 ----------
  if uploaded is None:
    stop()
  內容= uploaded.read().decode(errors='ignore')
elif menu==MENU[0]: #snp格式
  根=Path('FAIL__20251230_141506_13cm')
  with sidebar:
    檔=radio('snp格式', 根.rglob('*.s4p'))
  if 檔:
    #檔=Path(檔)
    #with open(檔) as fin:
    #內容=檔.read_text()
    資訊, net=讀取(檔)    #內容

  # ---------- 2. 讀入 Network ----------
  # 用 StringIO 把 Bytes 轉成文件句柄
  with sidebar:
    ports = list(range(1, net.nports+1))
    p1 = selectbox("源端口", ports, 0)
    p2 = selectbox("目標端口", ports, 1 if net.nports>1 else 0)
    unit = radio("縱軸單位", ["dB", "mag"])
    f_unit = radio("頻率單位", ["GHz", "MHz", "Hz"])
    f_range = slider("頻率範圍 (GHz)", float(net.frequency.f_scaled[0]), float(net.frequency.f_scaled[-1]), (float(net.frequency.f_scaled[0]), float(net.frequency.f_scaled[-1])))

  # ---------- 4. 數據準備 ----------
  s = net.s[:, p1-1, p2-1] # 取 S 矩陣裏對應的一列
  freq = net.frequency.f   # Hz
  if f_unit == "GHz": freq = freq/1e9
  elif f_unit == "MHz": freq = freq/1e6
  #狀態.code(資訊)
  mask = (freq>=f_range[0]) & (freq<=f_range[1])
  freq, s = freq[mask], s[mask]
  y = 20*log10(abs(s)) if unit == "dB" else abs(s)

  # ---------- 5. 繪圖 ----------
  col1, col2 = columns(2)

  with col1:
      fig, ax = subplots(figsize=(5,3.5))
      ax.plot(freq, y)
      ax.set_title(資訊)
      ax.set_xlabel(f"Frequency ({f_unit})")
      ax.set_ylabel(f"|S{p1}{p2}| ({unit})")
      ax.grid(True)
      pyplot(fig)

  with col2:
      fig2, ax2 = subplots(figsize=(5,3.5))
      #smith(s, ax=ax2)#, label=f'S{p1}{p2}')
      r_max = abs(s).max()          # 最大反射係數
      smithR = max(1., float(r_max)*1.05)   # 至少 1，留 5 % 邊界
      smith(ax=ax2, smithR=smithR)
      #smith(smithR: Number = 1, chart_type: str = 'z', draw_labels: bool = False, border: bool = False, ax: plt.Axes | None = None, ref_imm: float = 1.0, draw_vswr: list | bool | None = None):
      #smith(s, ax=ax2, smithR=1.0)  #label=f'S{p1}{p2}', 
      ax2.set_title(資訊)
      ax2.legend()
      pyplot(fig2)

  # ---------- 6. 數據表格 ----------
  with expander("查看原始數據"):
      df = DataFrame({'Frequency': freq, f'S{p1}{p2}': s})
      dataframe(df)

caption("Powered by scikit-rf & Streamlit")
