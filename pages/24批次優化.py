import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from 量傳線設計.核心.優化 import 批次優化, SPEC_CONFIG
from 量傳線設計.輸出入.excel匯出 import 試算表轉bytes
import openpyxl
from io import BytesIO

st.set_page_config(page_title="批次優化", layout="wide")
st.title("批次優化（多規格比較）")

specs = st.multiselect("規格", list(SPEC_CONFIG.keys()), default=list(SPEC_CONFIG.keys()))
n_trials = st.slider("每規格試驗次數", 10, 100, 30)
if st.button("開始批次優化"):
    with st.spinner("優化中..."):
        result = 批次優化(specs, n_trials=n_trials)
    fig, ax = plt.subplots()
    for name, trials in result.items():
        xs = [t.values[0] for t in trials]
        ys = [t.values[1] for t in trials]
        ax.scatter(xs, ys, label=name)
    ax.set_xlabel("串擾 (dB)"); ax.set_ylabel("熱負載")
    ax.legend(); ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    # 平行座標表
    import pandas as pd
    rows = []
    for name, trials in result.items():
        for t in trials:
            rows.append({"spec": name, **t.params, "f1": t.values[0], "f2": t.values[1]})
    st.subheader("參數平行座標")
    st.dataframe(pd.DataFrame(rows))
    # PDF 匯出
    pdf_buf = BytesIO()
    fig.savefig(pdf_buf, format="pdf", bbox_inches="tight")
    pdf_buf.seek(0)
    st.download_button("下載 Pareto PDF", data=pdf_buf.getvalue(), file_name="pareto_batch.pdf",
                       mime="application/pdf")
    # 匯出 Excel
    wb = openpyxl.Workbook()
    for name, trials in result.items():
        ws = wb.create_sheet(name)
        ws.append(["f1 (串擾)", "f2 (熱負載)"])
        for t in trials:
            ws.append([t.values[0], t.values[1]])
    if "Sheet" in wb.sheetnames:
        del wb["Sheet"]
    buf = BytesIO(); wb.save(buf); buf.seek(0)
    st.download_button("下載 Pareto Excel", data=buf.getvalue(), file_name="pareto.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
