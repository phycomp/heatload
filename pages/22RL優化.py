import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import streamlit as st
from 量傳線設計.核心.RL代理 import 訓練RL

st.set_page_config(page_title="RL 優化", layout="wide")
st.title("RL 閉環優化（PPO）")
spec_name = st.selectbox("規格", ["CF3", "FPC"])
timesteps = st.slider("訓練步數", 1000, 50000, 5000)
if st.button("開始訓練"):
    with st.spinner("訓練中..."):
        model, rewards = 訓練RL(spec_name, total_timesteps=timesteps)
    st.success("訓練完成")
    # 獎勵曲線
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.plot(rewards)
    ax.set_xlabel("Step"); ax.set_ylabel("Reward")
    ax.set_title("訓練獎勵曲線")
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
