import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st
from 量傳線設計.核心.規格產生器 import 產生規格書
from 量傳線設計.輸出入.excel匯出 import 試算表轉bytes
from 量傳線設計.輸出入.pdf匯出 import 圖轉pdf

st.set_page_config(page_title="規格產生器", layout="wide")
st.title("規格產生器")

with st.sidebar:
    通道數 = st.slider("通道數", 2, 16, 8, 2)
    訊號間距 = st.slider("Pitch (mm)", 0.5, 5.0, 2.0, 0.2)
    訊號寬度 = st.slider("訊號寬度 (μm)", 10, 40, 35, 5)
    線總寬 = st.slider("線總寬 (mm)", 10.0, 30.0, 17.0, 1.0)
    線長度 = st.slider("線長度 (mm)", 50.0, 500.0, 200.0, 10.0)

佈局, 試算表 = 產生規格書(通道數=通道數, 訊號間距=訊號間距, 訊號寬度=訊號寬度,
                            線總寬=線總寬, 線長度=線長度)

st.success("規格書已產生")
col1, col2 = st.columns(2)
with col1:
    st.download_button("下載 Excel", data=試算表轉bytes(試算表),
                       file_name="spec.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
