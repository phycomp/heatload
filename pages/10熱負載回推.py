import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st
import matplotlib.pyplot as plt
from 量傳線設計.核心.熱負載回推 import 回推模型比較, 溫度分布

st.set_page_config(page_title="熱負載回推", layout="wide")
st.title("熱負載回推模型比較")

with st.sidebar:
    spec_name = st.selectbox("規格", ["CF3", "FPC", "Uleam1"], index=0)
    st.caption(f"規格: {spec_name}")

L0 = st.slider("原始長度 L0 (cm)", 5.0, 50.0, 20.0)
T_cold = st.slider("冷端 (mK)", 1, 50, 10)
T_hot = st.slider("熱端 (mK)", 200, 400, 350)
T_crit = st.slider("臨界 (mK)", 30, 100, 58)

models, lengths = 回推模型比較(L0=L0, T_cold=T_cold, T_hot=T_hot, T_crit=T_crit)
fig, ax = plt.subplots()
bars = ax.bar(models, lengths, color=['#E63946','#06D6A0','#118AB2','#FFD166','#999'], edgecolor='black')
ax.set_ylabel("Length (cm)")
ax.set_title("Transmission Line Length Comparison")
for b, v in zip(bars, lengths):
    ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.3, f"{v:.1f}", ha='center', fontweight='bold')
st.pyplot(fig)

st.subheader("溫度分布")
x, T = 溫度分布(L0, T_cold, T_hot)
fig2, ax2 = plt.subplots()
ax2.plot(x, T)
ax2.set_xlabel("x (cm)"); ax2.set_ylabel("T (mK)"); ax2.grid(True, alpha=0.3)
st.pyplot(fig2)
