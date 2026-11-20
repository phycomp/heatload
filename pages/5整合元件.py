import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st
import pandas as pd
from 量傳線設計.核心.整合元件 import 元件表

st.set_page_config(page_title="整合元件", layout="wide")
st.title("整合元件")

with st.sidebar:
    spec_name = st.selectbox("規格", ["CF3", "FPC", "Uleam1"], index=0)
    st.caption(f"規格: {spec_name}")

df = pd.DataFrame(元件表(), columns=["名稱", "類型", "規格", "數量"])
st.dataframe(df, use_container_width=True)
