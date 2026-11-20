import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import streamlit as st
import matplotlib.pyplot as plt
from 量傳線設計.核心.優化 import 多目標優化, SPEC_CONFIG

st.set_page_config(page_title="多目標優化", layout="wide")
st.title("多目標優化（串擾 vs 熱負載）")

spec_name = st.selectbox("規格", list(SPEC_CONFIG.keys()))
n_trials = st.slider("試驗次數", 10, 200, 50)
use_proxy = st.checkbox("使用代理模型加速", value=False)
desc = st.text_input("需求描述（LLM）", "低串擾設計")
if st.button("LLM 建議參數"):
    from 量傳線設計.核心.LLM輔助 import 生成參數
    p = 生成參數(desc, spec_name)
    st.json(p)
if st.button("開始優化"):
    with st.spinner("優化中..."):
        trials = 多目標優化(spec_name, n_trials=n_trials, use_proxy=use_proxy)
    st.success(f"完成，共 {len(trials)} 個 Pareto 解")
    xs = [t.values[0] for t in trials]
    ys = [t.values[1] for t in trials]
    fig, ax = plt.subplots()
    ax.scatter(xs, ys)
    ax.set_xlabel("串擾 (dB)"); ax.set_ylabel("熱負載 (μW/ch)")
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    # PDF 匯出
    from io import BytesIO
    pdf_buf = BytesIO()
    fig.savefig(pdf_buf, format="pdf", bbox_inches="tight")
    pdf_buf.seek(0)
    st.download_button("下載 Pareto PDF", data=pdf_buf.getvalue(), file_name="pareto.pdf",
                       mime="application/pdf")
    # 報告 PDF
    from 量傳線設計.核心.優化 import 產生報告
    report_bytes = 產生報告(trials, spec_name)
    st.download_button("下載 報告 PDF", data=report_bytes, file_name="report.pdf",
                       mime="application/pdf")
    # 平行座標圖
    import pandas as pd
    pdf = pd.DataFrame([t.params for t in trials])
    pdf["f1"] = [t.values[0] for t in trials]
    pdf["f2"] = [t.values[1] for t in trials]
    st.subheader("參數平行座標")
    st.dataframe(pdf)
    # 匯出 Pareto
    import openpyxl
    from io import BytesIO
    wb = openpyxl.Workbook()
    ws = wb.active; ws.title = "Pareto"
    ws.append(["f1 (串擾)", "f2 (熱負載)"])
    for t in trials:
        ws.append([t.values[0], t.values[1]])
    buf = BytesIO(); wb.save(buf); buf.seek(0)
    st.download_button("下載 Pareto Excel", data=buf.getvalue(), file_name="pareto.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
