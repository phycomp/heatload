import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st
from 量傳線設計.核心.低溫超導 import 模擬NbTi串擾, 繪製串擾圖, BlochGruneisen電阻率

st.set_page_config(page_title="低溫超導", layout="wide")
st.title("低溫超導 (NbTi)")

with st.sidebar:
    spec_name = st.selectbox("規格", ["CF3", "FPC", "Uleam1"], index=0)
    st.caption(f"規格: {spec_name}")
    w = st.slider("線寬 w (μm)", 10, 100, 50)
    d = st.slider("超導層厚度 d (nm)", 50, 500, 100)
    s = st.slider("線間距 s (μm)", 20, 200, 100)
    length = st.slider("線路長度 (m)", 0.1, 1.0, 0.2)
    lambda_L = st.slider("λL (nm)", 150, 300, 200)
    er = st.number_input("介電常數", value=3.4)

res = 模擬NbTi串擾(w_um=w, d_nm=d, s_um=s, length_m=length, lambda_L_nm=lambda_L, er=er)
c1, c2, c3 = st.columns(3)
c1.metric("Lk (μH/m)", f"{res['L_k']*1e6:.2f}")
c2.metric("Lgeo (μH/m)", f"{res['L_geo']*1e6:.2f}")
c3.metric("Z0 (Ω)", f"{res['Z0']:.2f}")
st.pyplot(繪製串擾圖(res))

st.subheader("Bloch-Grüneisen 電阻率")
T = st.slider("溫度 (K)", 1, 300, 10)
rho = BlochGruneisen電阻率(T, rho0=1e-8, theta_D=300)
st.write(f"ρ = {rho:.3e} Ω·m")
