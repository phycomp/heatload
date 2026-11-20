# app.py
import streamlit as st, sqlite3, json, numpy as np, pandas as pd, matplotlib.pyplot as plt
import scikit_rf as rf
from datetime import date, timedelta

st.set_page_config(page_title="SNP 歷史資料查詢", layout="wide")
st.title("📡  TouchStone 歷史資料庫查詢")

DB = "snp_db.sqlite"

@st.cache_data(show_spinner=False)
def load_meta():
    conn = sqlite3.connect(DB, check_same_thread=False)
    df = pd.read_sql("SELECT id, file_name, date, n_ports FROM snp_data", conn)
    conn.close()
    return df

def fetch_selected(ids):
    conn = sqlite3.connect(DB, check_same_thread=False)
    dfs = []
    for i in ids:
        row = pd.read_sql("SELECT * FROM snp_data WHERE id=?", conn, params=(i,))
        dfs.append(row)
    conn.close()
    return pd.concat(dfs, ignore_index=True)

# ---------- 側邊欄篩選 ----------
meta = load_meta()
meta["date"] = pd.to_datetime(meta["date"]).dt.date

with st.sidebar:
    date_range = st.date_input("量測日期區間",
                                 [date.today()-timedelta(days=30), date.today()])
    ports = sorted(meta["n_ports"].unique())
    sel_ports = st.multiselect("端口數", ports, default=ports)
    keyword = st.text_input("料號關鍵字 (檔名搜尋)", "").strip().lower()

mask = (meta["date"].between(*date_range)) & (meta["n_ports"].isin(sel_ports))
if keyword:
    mask &= meta["file_name"].str.lower().str.contains(keyword)
sel_df = meta[mask]

st.info(f"符合篩選共 {len(sel_df)} 筆")
if len(sel_df)==0:
    st.stop()

sel_ids = st.multiselect("請勾選要比對的檔案",
                         options=sel_df["id"].tolist(),
                         format_func=lambda x: sel_df.set_index("id").loc[x, "file_name"])

if not sel_ids:
    st.stop()

raw_df = fetch_selected(sel_ids)

# ---------- 繪圖 ----------
unit = st.sidebar.radio("Y 軸單位", ["dB", "mag"])
p1   = st.sidebar.number_input("源端口", 1, 8, 1)
p2   = st.sidebar.number_input("目標端口", 1, 8, 2)

fig, ax = plt.subplots(figsize=(7,4))
for _, row in raw_df.iterrows():
    freq = np.array(json.loads(row["freq_list"])) / 1e9   # GHz
    s3d  = np.array(json.loads(row["s_complex"]))
    # 取對應 Sij，scikit-rf 存法 [n_freq, n_out, n_in]
    s = s3d[:, p2-1, p1-1]
    y = 20*np.log10(np.abs(s)) if unit=="dB" else np.abs(s)
    ax.plot(freq, y, label=row["file_name"])

ax.set_xlabel("Frequency (GHz)")
ax.set_ylabel(f"|S{p1}{p2}| ({unit})")
ax.legend(); ax.grid(True)
st.pyplot(fig)

# ---------- 表格 & 下載 ----------
with st.expander("檢視原始數據"):
    st.dataframe(raw_df[["file_name","date","n_ports"]])

csv = raw_df[["file_name","date","n_ports"]].to_csv(index=False)
st.download_button("下載篩選清單 CSV", csv, "snp_list.csv", mime="text/csv")
