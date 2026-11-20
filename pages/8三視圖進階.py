import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st
from 量傳線設計.核心.三視圖進階 import StriplineGeometry, draw_smart_side_view

st.set_page_config(page_title="三視圖進階", layout="wide")
st.title("三視圖進階 — 智慧標註側視圖")

with st.sidebar:
    spec_name = st.selectbox("規格", ["CF3", "FPC", "Uleam1"], index=0)
    st.caption(f"規格: {spec_name}")
    channels = st.radio("通道數", [4, 8, 16], index=1, horizontal=True)
    pitch = st.slider("Pitch (mm)", 0.5, 5.0, 2.0, 0.2)
    length = st.slider("長度 (mm)", 50.0, 300.0, 200.0, 10.0)
    via = st.checkbox("Via", value=False)
    n_layers = st.slider("介電層數", 1, 5, 1, 1)

geo = StriplineGeometry(w=0.035, t=0.002, h=0.129*n_layers, s=pitch, L=length, n_channels=channels)
fig = draw_smart_side_view(geo, pitch, length, via, 0.2, 0.5, channels)
st.pyplot(fig)
