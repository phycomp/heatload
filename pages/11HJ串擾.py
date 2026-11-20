import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st
from 量傳線設計.核心.HJ串擾 import 優化, 串擾抑制, 近遠場, 串擾機制, 頻率色散, HJ模型

st.set_page_config(page_title="HJ 串擾模型", layout="wide")
st.title("HJ 串擾模型")

with st.sidebar:
    spec_name = st.selectbox("規格", ["CF3", "FPC", "Uleam1"], index=0)
    st.caption(f"規格: {spec_name}")

選項 = {
    "HJ模型": HJ模型,
    "頻率色散": 頻率色散,
    "串擾機制": 串擾機制,
    "近遠場": 近遠場,
    "串擾抑制": 串擾抑制,
    "優化": 優化,
}
import matplotlib.pyplot as plt
name = st.radio("選擇圖表", list(選項.keys()), horizontal=True)
選項[name]()
fig = plt.gcf()
st.pyplot(fig)
