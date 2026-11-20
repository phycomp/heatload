import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st
import matplotlib.pyplot as plt
from numpy import linspace
from 量傳線設計.核心.其它 import (calculate_microstrip_width, calculate_effective_dielectric_constant,
                              calculate_guided_wavelength, 電報員電壓, 波導截止頻率, 簡單串擾)

st.set_page_config(page_title="其它", layout="wide")
st.title("其它功能")

with st.sidebar:
    spec_name = st.selectbox("規格", ["CF3", "FPC", "Uleam1"], index=0)
    st.caption(f"規格: {spec_name}")

tab = st.tabs(["微帶線寬", "電報員", "波導", "串擾"])
with tab[0]:
    Z0 = st.number_input("Z0 (Ω)", value=50.0)
    er = st.number_input("er", value=4.4)
    h = st.number_input("h (mm)", value=1.6)
    W = calculate_microstrip_width(Z0, er, h)
    st.metric("線寬 W (mm)", f"{W:.3f}")
    ee = calculate_effective_dielectric_constant(er, W, h)
    st.write(f"有效介電常數: {ee:.3f}")
    st.write(f"導波波長 @1GHz: {calculate_guided_wavelength(1.0, ee):.2f} mm")

with tab[1]:
    L = st.slider("長度 (m)", 0.1, 5.0, 1.0)
    f = st.slider("頻率 (MHz)", 1, 1000, 100) * 1e6
    z, V = 電報員電壓(L, f)
    fig, ax = plt.subplots()
    ax.plot(z, V)
    ax.set_xlabel("z (m)"); ax.set_ylabel("V")
    st.pyplot(fig)

with tab[2]:
    a = st.number_input("a (m)", value=0.02286)
    b = st.number_input("b (m)", value=0.01016)
    fc = 波導截止頻率(a, b, m=1, n=0)
    st.metric("截止頻率 (GHz)", f"{fc/1e9:.3f}")

with tab[3]:
    f = st.slider("頻率 (GHz)", 0.1, 20.0, 5.0)
    L = st.slider("長度 (m)", 0.01, 1.0, 0.2)
    val = 簡單串擾(f, L)
    st.metric("串擾 (dB)", f"{val:.2f}")
