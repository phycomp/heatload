import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st
import matplotlib.pyplot as plt
from 量傳線設計.核心.閉環量傳線 import evaluate_stripline, simulate_network

st.set_page_config(page_title="閉環量傳線", layout="wide")
st.title("閉環量傳線（Loop Engineering）")

with st.sidebar:
    spec_name = st.selectbox("規格", ["CF3", "FPC", "Uleam1"], index=0)
    st.caption(f"規格: {spec_name}")
    w = st.slider("線寬 (μm)", 5.0, 40.0, 15.0, 0.5)
    trench = st.slider("Kapton 挖空率", 0.0, 0.95, 0.0, 0.05)
    T = st.slider("溫度 (K)", 0.01, 9.0, 0.1, 0.1)
    target_z0 = st.slider("目標 Z0 (Ω)", 40.0, 60.0, 50.0, 0.5)

z0, qi, alpha, beta = evaluate_stripline(w, trench, 7e9, T)
c1, c2 = st.columns(2)
c1.metric("Z0 @7GHz (Ω)", f"{z0:.2f}")
c2.metric("Qi", f"{qi:.2e}")

net = simulate_network(w, trench, T)
fig, ax = plt.subplots()
ax.plot(net.frequency.f / 1e9, abs(net.s[:, 0, 0]))
ax.set_xlabel("Freq (GHz)"); ax.set_ylabel("|S11|")
ax.grid(True, alpha=0.3)
st.pyplot(fig)
