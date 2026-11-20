import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st
import pandas as pd
from 量傳線設計.核心.傳輸線規格 import 全部規格, 規格轉dict

st.set_page_config(page_title="傳輸線規格", layout="wide")
st.title("三種傳輸線規格 (CF3 / FPC / Uleam1)")

specs = 全部規格()
for name, spec in specs.items():
    with st.expander(name):
        st.json(規格轉dict(spec))

df = pd.DataFrame([規格轉dict(s) for s in specs.values()])
st.dataframe(df, use_container_width=True)
