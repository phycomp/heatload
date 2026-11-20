# st_4p_auto.py
import streamlit as st
from io import BytesIO
import skrf as rf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="4P Auto Viewer", layout="wide")
st.title("🔍  S11/S12/S21/S22 自動 Subplots（2-Port）")

# ---------- 上傳 ----------
uploaded = st.file_uploader("選擇 .sNp", type=['s1p','s2p','s3p','s4p','snp'], accept_multiple_files=True)
if not uploaded:
    st.stop()

# ---------- 控制項 ----------
unit   = st.sidebar.radio("Y 軸", ["dB", "mag"])
show_multi = st.sidebar.checkbox("疊圖（多檔同軸）", value=True)

# ---------- 解析 ----------
nets = []
for f in uploaded:
    buf = BytesIO(f.getvalue())
    buf.name = f.name
    net = rf.Network(buf)
    nets.append(net)

# 只處理 2-Port（固定 4 張子圖）
if nets[0].nports != 2:
    st.error("本範例僅支援 2-Port 檔案"); st.stop()

# ---------- 繪圖 ----------
fig, axes = plt.subplots(2, 2, figsize=(10, 8), constrained_layout=True)
s_params = ["S11", "S12", "S21", "S22"]
for idx, (sp, ax) in enumerate(zip(s_params, axes.flatten())):
    p_out, p_in = int(sp[1]), int(sp[2])
    for net in nets:
        s    = net.s[:, p_out-1, p_in-1]
        freq = net.f / 1e9
        y    = 20*np.log10(np.abs(s)) if unit=="dB" else np.abs(s)
        lbl  = None if show_multi else net.name
        ax.plot(freq, y, label=lbl)
    ax.set_title(sp)
    ax.set_xlabel("Freq (GHz)")
    ax.set_ylabel(f"Mag ({unit})")
    ax.grid(True)
    if show_multi:
        ax.legend()

st.pyplot(fig)

# ---------- 下載 ----------
csv_all = []
for net in nets:
    for sp in s_params:
        p_out, p_in = int(sp[1]), int(sp[2])
        s = net.s[:, p_out-1, p_in-1]
        tmp = pd.DataFrame({
            "File": net.name,
            "S_Param": sp,
            "Freq_Hz": net.f,
            "Mag": np.abs(s),
            "Phase_rad": np.angle(s),
            "dB": 20*np.log10(np.abs(s))
        })
        csv_all.append(tmp)
df_csv = pd.concat(csv_all, ignore_index=True)
st.download_button("📥 下載 4P 統整 CSV", df_csv.to_csv(index=False),
                  file_name="S_Param_4P.csv", mime="text/csv")
