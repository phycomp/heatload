from streamlit import dataframe, download_button, file_uploader, pyplot, set_page_config, sidebar, stop, success, tabs, title, subheader
from matplotlib.pyplot import subplots
from numpy import abs, angle, log10
from pandas import DataFrame, concat
# app_chx_viewer.py
import streamlit as st
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from chx_reader import chx_to_network
import psycopg
from io import BytesIO
import pickle

set_page_config(page_title="Anritsu Switch Cal Viewer", layout="wide")
MENU, 表單=[], ['校正', '參數', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
if menu==len(表單): #
  pass
elif menu==MENU[1]: #
  pass
elif menu==MENU[0]: #校正
  pass
  with sidebar:
    subheader("🔧  Anritsu Switch Calibration Viewer（.chx）")
    uploaded = file_uploader("選擇 Cal_CHxx.chx", type=['chx'], accept_multiple_files=True)
    if not uploaded: stop()

# ---------- 解析 ----------
  nets = []
  for f in uploaded:
      net = chx_to_network(BytesIO(f.getvalue()))   # 支援 BytesIO
      net.name = f.name
      nets.append(net)

# ---------- 控制項 ----------
  with sidebar:
    unit = radio("Y 軸", ["dB", "mag"])
    p1   = number_input("源端口", 1, 2, 1)
    p2   = number_input("目標端口", 1, 2, 2)

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
          from skplotting import smith
          smith(s, ax=ax, label=net.name)
      ax.legend()
      pyplot(fig)

  with tab3:
      df_all = []
      for net in nets:
          s = net.s[:, p2-1, p1-1]
          tmp = DataFrame({
              "File": net.name,
              "Freq_Hz": net.f,
              "Mag": abs(s),
              "Phase_rad": angle(s),
              "dB": 20*log10(abs(s))
          })
          df_all.append(tmp)
      df = concat(df_all, ignore_index=True)
      dataframe(df)
      csv = df.to_csv(index=False)
      download_button("📥 下載 CSV", csv, f"Cal_S{p1}{p2}.csv", mime="text/csv")

  # ---------- 可選：一鍵存 DB ----------
  if button("💾 存入 astbk（pickle）"):
      with psycopg.connect(DSN) as conn:
          with conn.cursor() as cur:
              for net in nets:
                  pkl = pickle.dumps(net)
                  cur.execute(
                      "INSERT INTO snp皮可(檔, 皮可) VALUES (%s,%s) ON CONFLICT (檔) DO NOTHING",
                      (net.name, pkl)
                  )
          conn.commit()
      success("已存入資料庫！")
