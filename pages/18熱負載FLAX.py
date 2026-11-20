import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st
import matplotlib.pyplot as plt
from 量傳線設計.核心.熱負載FLAX import compute_geometry, compute_heat_load

st.set_page_config(page_title="熱負載 FLAX", layout="wide")
st.title("FLAX 熱負載（2023）")

with st.sidebar:
    spec_name = st.selectbox("規格", ["CF3", "FPC", "Uleam1"], index=0)
    st.caption(f"規格: {spec_name}")
    d_inner = st.number_input("中心導體直徑 (mm)", value=0.127)
    d_pfa = st.number_input("PFA 外徑 (mm)", value=0.279)
    t_outer = st.number_input("外屏蔽厚度 (mm)", value=0.0254)
    pitch = st.number_input("線芯間距 (mm)", value=3.56)
    n_traces = st.number_input("線芯數", value=10, step=1)
    L = st.number_input("電纜長度 (cm)", value=30.48)
    T_cold = st.number_input("冷端 (K)", value=0.10)
    T_hot = st.number_input("熱端 (K)", value=1.0)
    k_pfa = st.number_input("PFA k_ref", value=0.08)
    pfa_exp = st.number_input("PFA exp", value=1.5)
    k_nbti = st.number_input("NbTi k_ref", value=0.007)
    nbti_exp = st.number_input("NbTi exp", value=2.0)

geo = compute_geometry(d_inner, d_pfa, t_outer, pitch, int(n_traces))
res = compute_heat_load(geo, T_cold, T_hot, L, k_pfa, pfa_exp, k_nbti, nbti_exp)

c1, c2 = st.columns(2)
c1.metric("Q_total (nW)", f"{res['Q_total_nW']:.3f}")
c2.metric("Q_single (nW)", f"{res['Q_single_nW']:.3f}")

fig, ax = plt.subplots()
mask = res['mask']
ax.plot(res['T'][mask], res['G_total'][mask])
ax.set_xlabel("T (K)"); ax.set_ylabel("G_total (W/m/K)")
ax.grid(True, alpha=0.3)
st.pyplot(fig)
