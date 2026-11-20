import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import streamlit as st
import matplotlib.pyplot as plt
from 量傳線設計.核心.代理模型 import 生成訓練資料, 訓練代理模型, 預測

st.set_page_config(page_title="代理模型+LLM", layout="wide")
st.title("代理模型 + LLM 輔助")

spec_name = st.selectbox("規格", ["CF3", "FPC"])
desc = st.text_input("需求描述", "低串擾設計")
if st.button("生成初始參數"):
    from 量傳線設計.核心.LLM輔助 import 生成參數
    p = 生成參數(desc, spec_name)
    st.json(p)
    samples = 生成訓練資料(spec_name, n=20)
    if len(samples) >= 5:
        model = 訓練代理模型(samples)
        f1, f2 = 預測(model, p)
        st.metric("預測串擾 (dB)", f"{f1:.2f}")
        st.metric("預測熱負載", f"{f2:.4f}")
        # 代理 vs 實際比較
        actual_f1 = [r[1][0] for r in samples]
        pred_f1 = [預測(model, r[0])[0] for r in samples]
        fig, ax = plt.subplots()
        ax.scatter(actual_f1, pred_f1)
        ax.plot([min(actual_f1), max(actual_f1)], [min(actual_f1), max(actual_f1)], 'r--')
        ax.set_xlabel("實際串擾 (dB)"); ax.set_ylabel("代理預測 (dB)")
        ax.set_title("代理模型 vs 實際")
        st.pyplot(fig)
