from streamlit import dataframe, download_button, error, file_uploader, markdown, plotly_chart, progress, pyplot, selectbox, set_page_config, sidebar, stop, subheader, success, title, warning
from matplotlib.pyplot import subplots
from numpy import arange, array, corrcoef, mean, sqrt, std
from pandas import DataFrame, ExcelWriter, read_excel, to_numeric
# channel_golden_zip.py
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO
import zipfile
import tempfile
import os
import glob
import base64

set_page_config(page_title="CH-Golden vs ZIP-批次比對", layout="wide")

# ---------- 工具 ----------
def calc_stats(arrays):
    min_len = min(len(a) for a in arrays)
    aligned = array([a[:min_len] for a in arrays])
    return {
        'mean'  : mean(aligned, axis=0),
        'std'   : std(aligned, axis=0),
        'upper' : mean(aligned, axis=0) + 3*std(aligned, axis=0),
        'lower' : mean(aligned, axis=0) - 3*std(aligned, axis=0),
        'n'     : len(arrays)
    }

def similarity_score(z, golden):
    if len(z) > len(golden['mean']): z = z[:len(golden['mean'])]
    rmse = sqrt(mean((z - golden['mean'])**2))
    corr = corrcoef(z, golden['mean'])[0,1]
    score = max(0, 100 - rmse*2) * max(0, corr)
    return score, rmse, corr

def fig_to_png_link(fig, fname):
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    return f'<a href="data:file/png;base64,{b64}" download="{fname}">下載 PNG</a>'

# ---------- Sidebar ----------
sidebar.title("⚙️ 控制")
sigma = sidebar.slider("容差倍數 σ", 1.0, 6.0, 3.0)

# ---------- 主畫面 ----------
title("🧠 CH-Golden Standard vs ZIP-批次比對")
markdown("---")

# 1️⃣ 上傳 Golden 參考檔
subheader("📁 1. 上傳 Golden 參考檔（單一 xlsx）")
golden_file = file_uploader("Golden 檔案", type=["xlsx"])
golden_dict = {}   # 儲存每通道的 golden
if golden_file:
    try:
        df_g = read_excel(golden_file, sheet_name="TDR Data")  # 時域工作表
        time_col = 'Time (ns)'   # 固定第一欄
        t_golden = to_numeric(df_g[time_col], errors='coerce').dropna().values
        # 掃描所有 CH(*) impedance 欄位
        imp_cols = [c for c in df_g.columns if 'CH(' in str(c) and 'impedance' in str(c).lower()]
        if not imp_cols:
            error("找不到任何 CH(xx) impedance 欄位"); stop()
        success(f"✅ 已發現 {len(imp_cols)} 組阻抗通道")
        # 逐通道建立 Golden
        for ch in imp_cols:
            z_g = to_numeric(df_g[ch], errors='coerce').dropna().values
            golden_dict[ch] = calc_stats([z_g])
        success("✅ 所有通道 Golden 建立完成")
    except Exception as e:
        error(f"Golden 讀取失敗：{e}")

# 2️⃣ 上傳 ZIP 測試檔
subheader("📁 2. 上傳 ZIP 測試檔（內含多個 xlsx）")
zip_file = file_uploader("ZIP 檔案", type=["zip"])
if zip_file and golden_dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_file, 'r') as zf:
            zf.extractall(tmpdir)
        xlsx_list = [f for f in glob.glob(os.path.join(tmpdir, "**/*.xlsx"), recursive=True)]
        if not xlsx_list:
            warning("壓縮檔內無 xlsx 檔案"); stop()
        
        # 逐檔比對
        report = []
        progress = progress(0)
        for idx, fp in enumerate(xlsx_list):
            fname = os.path.basename(fp)
            try:
                df = read_excel(fp, sheet_name="TDR Data")
                t = to_numeric(df['Time (ns)'], errors='coerce').dropna().values
                # 只比對「Golden 已存在的通道」
                for ch in golden_dict.keys():
                    if ch not in df.columns: continue
                    z = to_numeric(df[ch], errors='coerce').dropna().values
                    score, rmse, corr = similarity_score(z, golden_dict[ch])
                    report.append({
                        "檔案": fname,
                        "通道": ch,
                        "相似度": score,
                        "RMSE": rmse,
                        "判定": "PASS" if score>=85 else ("CONDITIONAL" if score>=70 else "FAIL")
                    })
            except Exception as e:
                report.append({"檔案": fname, "通道": "讀取失敗", "相似度": None, "RMSE": None, "判定": str(e)})
            progress.progress((idx+1)/len(xlsx_list))
        
        # 3️⃣ 結果視覺化
        df_report = DataFrame(report)
        dataframe(df_report)
        # Bar
        fig_bar = px.bar(df_report, x="檔案", y="相似度", color="判定",
                         title="各檔案-通道 vs Golden 相似度", height=400,
                         color_discrete_map={"PASS":"green","CONDITIONAL":"orange","FAIL":"red"})
        fig_bar.update_layout(xaxis_tickangle=-45)
        plotly_chart(fig_bar, use_container_width=True)
        # Scatter
        fig_scatter = px.scatter(df_report, x="RMSE", y="相似度", color="判定",
                                 hover_data=["檔案","通道"], title="RMSE vs 相似度分佈")
        plotly_chart(fig_scatter, use_container_width=True)
        
        # 4️⃣ 下載報告
        excel_buf = BytesIO()
        with ExcelWriter(excel_buf, engine="openpyxl") as w:
            df_report.to_excel(w, sheet_name="Summary", index=False)
        excel_buf.seek(0)
        download_button("📥 下載完整報告", excel_buf, "ZIP_CH_Comparison_Report.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        # 5️⃣ 單檔-單通道疊圖檢視
        markdown("---")
        subheader("📈 詳細疊圖檢視")
        sel_file = selectbox("選擇檔案", df_report["檔案"].unique())
        sel_ch   = selectbox("選擇通道", df_report[df_report["檔案"]==sel_file]["通道"].unique())
        fp_sel   = [p for p in xlsx_list if os.path.basename(p)==sel_file][0]
        df_sel   = read_excel(fp_sel, sheet_name="TDR Data")
        t_new    = to_numeric(df_sel['Time (ns)'], errors='coerce').dropna().values
        z_new    = to_numeric(df_sel[sel_ch], errors='coerce').dropna().values
        golden   = golden_dict[sel_ch]
        fig, ax = subplots(figsize=(10,4))
        x_new = arange(len(z_new))*0.01   # 假設 10 ps/step
        x_golden = arange(len(golden['mean']))*0.01
        ax.plot(x_golden, golden['mean'], 'b-', lw=2, label="Golden Mean")
        ax.fill_between(x_golden, golden['lower'], golden['upper'], color='gray', alpha=0.2, label=f"{sigma}σ")
        ax.plot(x_new, z_new, 'g-', lw=2, label=f"New: {sel_file}")
        ax.set_title(f"{sel_ch} 疊圖"); ax.set_xlabel("Time (ns)"); ax.set_ylabel("Impedance (Ω)")
        ax.legend(); ax.grid(alpha=0.3)
        pyplot(fig)
        markdown(fig_to_png_link(fig, f"Compare_{sel_file}_{sel_ch}.png"), unsafe_allow_html=True)
