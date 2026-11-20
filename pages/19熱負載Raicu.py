import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st
import matplotlib.pyplot as plt
from 量傳線設計.核心.熱負載Raicu import (DEFAULT_STAGES, calc_static_heat_single,
                                       calc_active_heat_flux_line_simple, calc_processor_lines,
                                       calc_total_heat)

st.set_page_config(page_title="熱負載 Raicu", layout="wide")
st.title("Raicu 同軸熱負載")

with st.sidebar:
    spec_name = st.selectbox("規格", ["CF3", "FPC", "Uleam1"], index=0)
    st.caption(f"規格: {spec_name}")

st.subheader("靜態熱負載（單條）")
stage = st.selectbox("溫度級", list(DEFAULT_STAGES.keys()))
sp = DEFAULT_STAGES[stage]
res = calc_static_heat_single(sp, stage)
st.json(res)

st.subheader("各級靜態熱負載")
stages_names = list(DEFAULT_STAGES.keys())
static_vals = [calc_static_heat_single(DEFAULT_STAGES[n], n)["total"] for n in stages_names]
fig2, ax2 = plt.subplots()
ax2.bar(stages_names, static_vals)
ax2.set_ylabel("Q_static (W)")
ax2.set_title("Static Heat Load per Stage")
st.pyplot(fig2)

st.subheader("處理器線數")
n_qubits = st.number_input("qubit 數", value=100, step=1)
df_rows = calc_processor_lines([n_qubits])
st.dataframe(df_rows)

st.subheader("總熱負載")
nq = st.number_input("處理器 qubits", value=100, step=1, key="nq")
tot = calc_total_heat(DEFAULT_STAGES, nq)
if tot:
    names = list(tot["total"].keys())
    vals = [tot["total"][n]["total"] for n in names]
    fig, ax = plt.subplots()
    ax.bar(names, vals)
    ax.set_ylabel("Heat (W)")
    ax.set_title("Total Heat Load per Stage")
    st.pyplot(fig)
    st.json({n: {"total": tot["total"][n]["total"], "fraction": tot["total"][n]["fraction"]} for n in names})
