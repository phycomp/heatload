from streamlit import dataframe, download_button, error, file_uploader, markdown, plotly_chart, progress, pyplot, selectbox, set_page_config, sidebar, stop, subheader, success, title, warning
from matplotlib.pyplot import subplots
from numpy import arange, array, corrcoef, mean, sqrt, std
from pandas import DataFrame, ExcelWriter, read_excel, to_numeric
# zip_golden_cmp.py
from matplotlib.pyplot import subplots
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from scipy import signal
from io import BytesIO
import zipfile
import tempfile
import os
import base64

set_page_config(page_title="Golden vs ZIP-測試檔 比對", layout="wide")

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
z0   = sidebar.number_input("特性阻抗 Z₀ (Ω)", value=50)
sigma = sidebar.slider("容差倍數 σ", 1.0, 6.0, 3.0)

# ---------- 主畫面 ----------
title("🧠 Golden Standard vs ZIP-測試檔 智慧比對")
markdown("---")

# 1️⃣ 上傳 Golden 參考檔
subheader("📁 1. 上傳 Golden 參考檔（單一 xlsx）")
golden_file = file_uploader("Golden 檔案", type=["xlsx"])
golden_freq, golden_tdr = None, None
if golden_file:
    try:
        df_g_freq = read_excel(golden_file, sheet_name="Excel Data")
        df_g_tdr  = read_excel(golden_file, sheet_name="TDR Data")
        # 自動抓第一欄當 X，第二欄當 Y
        xgf, ygf = df_g_freq.columns[0], df_g_freq.columns[1]
        xgt, ygt = df_g_tdr.columns[0],  df_g_tdr.columns[1]
        zg_freq = to_numeric(df_g_freq[ygf], errors='coerce').dropna().values
        zg_tdr  = to_numeric(df_g_tdr[ygt], errors='coerce').dropna().values
        golden_freq = calc_stats([zg_freq])
        golden_tdr  = calc_stats([zg_tdr])
        success("✅ Golden 建立完成")
    except Exception as e:
        error(f"Golden 讀取失敗：{e}")

# 2️⃣ 上傳 ZIP 測試檔
subheader("📁 2. 上傳 ZIP 測試檔（內含多個 xlsx）")
zip_file = file_uploader("ZIP 檔案", type=["zip"])
if zip_file and golden_freq is not None:
    # 解壓到暫存
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
                df_freq = read_excel(fp, sheet_name="Excel Data")
                df_tdr  = read_excel(fp, sheet_name="TDR Data")
                xf, yf = df_freq.columns[0], df_freq.columns[1]
                xt, yt = df_tdr.columns[0],  df_tdr.columns[1]
                z_freq = to_numeric(df_freq[yf], errors='coerce').dropna().values
                z_tdr  = to_numeric(df_tdr[yt], errors='coerce').dropna().values
                score_f, rmse_f, corr_f = similarity_score(z_freq, golden_freq)
                score_t, rmse_t, corr_t = similarity_score(z_tdr,  golden_tdr)
                report.append({
                    "檔案": fname,
                    "頻域Score": score_f,
                    "頻域RMSE": rmse_f,
                    "時域Score": score_t,
                    "時域RMSE": rmse_t,
                    "判定": "PASS"  if (score_f>=85 and score_t>=85) else
                           ("CONDITIONAL" if (score_f>=70 and score_t>=70) else "FAIL")
                })
            except Exception as e:
                report.append({"檔案": fname, "頻域Score": None, "頻域RMSE": None,
                               "時域Score": None, "時域RMSE": None, "判定": f"讀取失敗:{e}"})
            progress.progress((idx+1)/len(xlsx_list))
        
        # 3️⃣ 結果視覺化
        df_report = DataFrame(report)
        dataframe(df_report)
        # 長條圖
        fig_bar = px.bar(df_report, x="檔案", y=["頻域Score","時域Score"],
                         title="各檔案 vs Golden 相似度", height=400,
                         color_continuous_scale="RdYlGn", text_auto=True)
        fig_bar.update_layout(xaxis_tickangle=-45)
        plotly_chart(fig_bar, use_container_width=True)
        # 分佈圖
        fig_scatter = px.scatter(df_report, x="頻域RMSE", y="時域RMSE",
                                 color="判定", size_max=10,
                                 color_discrete_map={"PASS":"green","CONDITIONAL":"orange","FAIL":"red"},
                                 hover_data=["檔案"], title="RMSE 分佈（越低越好）")
        plotly_chart(fig_scatter, use_container_width=True)
        
        # 4️⃣ 下載報告
        excel_buf = BytesIO()
        with ExcelWriter(excel_buf, engine="openpyxl") as w:
            df_report.to_excel(w, sheet_name="Summary", index=False)
        excel_buf.seek(0)
        download_button("📥 下載完整報告", excel_buf, "ZIP_Comparison_Report.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        # 5️⃣ Golden vs 任一檔互動疊圖（選檔下拉）
        markdown("---")
        subheader("📈 詳細疊圖檢視")
        sel_file = selectbox("選擇要比對的檔案", df_report["檔案"])
        fp_sel = [p for p in xlsx_list if os.path.basename(p)==sel_file][0]
        df_f = read_excel(fp_sel, sheet_name="Excel Data")
        df_t = read_excel(fp_sel, sheet_name="TDR Data")
        zf_new = to_numeric(df_f[df_f.columns[1]], errors='coerce').dropna().values
        zt_new = to_numeric(df_t[df_t.columns[1]], errors='coerce').dropna().values
        fig, (ax1,ax2) = subplots(1,2, figsize=(14,5))
        xf = arange(len(zf_new))*0.01; xt = arange(len(zt_new))*0.01
        # 頻域
        ax1.plot(xf, golden_freq['mean'], 'b-', lw=2, label="Golden Mean")
        ax1.fill_between(xf, golden_freq['lower'], golden_freq['upper'], color='gray', alpha=0.2, label=f"{sigma}σ")
        ax1.plot(xf, zf_new, 'g-', lw=2, label=f"New: {sel_file}")
        ax1.set_title("Frequency Domain"); ax1.legend(); ax1.grid(alpha=0.3)
        # 時域
        ax2.plot(xt, golden_tdr['mean'], 'b-', lw=2, label="Golden Mean")
        ax2.fill_between(xt, golden_tdr['lower'], golden_tdr['upper'], color='gray', alpha=0.2, label=f"{sigma}σ")
        ax2.plot(xt, zt_new, 'g-', lw=2, label=f"New: {sel_file}")
        ax2.set_title("TDR Domain"); ax2.legend(); ax2.grid(alpha=0.3)
        pyplot(fig)
        markdown(fig_to_png_link(fig, f"Compare_{sel_file}.png"), unsafe_allow_html=True)
