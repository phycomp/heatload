from streamlit import button, columns, download_button, error, file_uploader, info, markdown, pyplot, set_page_config, sidebar, stop, success, title, warning
from matplotlib.pyplot import subplots
from numpy import arange, array, corrcoef, mean, percentile, sqrt, std
from pandas import DataFrame, ExcelWriter, read_excel, to_numeric
# golden_tdr_gui.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from scipy import signal, fft
from scipy.stats import norm
from io import BytesIO
import pickle
import base64
import os, glob

set_page_config(page_title="Golden TDR & Freq 標準化", layout="wide")

# ---------- 工具 ----------
def id_col(df, key):
    """自動找欄位"""
    for c in df.columns:
        if key in str(c).lower():
            return c
    return df.columns[0]   # fallback

def calc_stats(arrays):
    """多曲線統計 → Golden dict"""
    min_len = min(len(a) for a in arrays)
    aligned = array([a[:min_len] for a in arrays])
    return {
        'mean'   : mean(aligned, axis=0),
        'std'    : std(aligned, axis=0),
        'p5'     : percentile(aligned, 5, axis=0),
        'p95'    : percentile(aligned, 95, axis=0),
        'upper'  : mean(aligned, axis=0) + 3*std(aligned, axis=0),
        'lower'  : mean(aligned, axis=0) - 3*std(aligned, axis=0),
        'n'      : len(arrays)
    }

def similarity_score(z, golden):
    """回傳 0-100 綜合相似度"""
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

# ---------- 側欄 ----------
sidebar.title("⚙️ 控制")
mode = sidebar.radio("功能", ["建立Golden","比對新檔","管理Golden"])
z0     = sidebar.number_input("特性阻抗 Z₀ (Ω)", value=50)
sigma  = sidebar.slider("容差倍數 σ", 1.0, 6.0, 3.0)

# ---------- 主畫面 ----------
if mode == "建立Golden":
    title("🏗️ 建立 Golden Standard")
    info("請上傳 ≥3 個『合格品』檔案，系統會分別讀取「Excel Data」(頻域) 與「TDR Data」(時域) 工作表，建立雙重 Golden。")
    files = file_uploader("上傳基準檔案", accept_multiple_files=True, type=["xlsx"])
    if files and len(files)>=3:
        freq_curves, tdr_curves = [], []
        for f in files:
            try:
                頻資框 = read_excel(f, sheet_name="Data")
                時資框  = read_excel(f, sheet_name="TDR Data")
                # 取第一欄當 X，第二欄當 Y（可依實際調整）
                f_col, zf_col = 頻資框.columns[0], 頻資框.columns[1]
                t_col, zt_col = 時資框.columns[0],  時資框.columns[1]
                freq_curves.append(to_numeric(頻資框[zf_col], errors='coerce').dropna().values)
                tdr_curves.append(to_numeric(時資框[zt_col], errors='coerce').dropna().values)
            except Exception as e:
                warning(f"{f.name} 讀取失敗：{e}")
        if freq_curves and tdr_curves:
            golden_freq = calc_stats(freq_curves)
            golden_tdr  = calc_stats(tdr_curves)
            # 視覺化
            fig, (ax1,ax2) = plt.subplots(1,2, figsize=(14,5))
            xf = arange(len(golden_freq['mean']))*0.01  # 假設 10 MHz step
            xt = arange(len(golden_tdr['mean'))*0.01   # 假設 10 ps step
            for ax, x, gold, title in [(ax1, xf, golden_freq, "頻域 Golden"),
                                       (ax2, xt, golden_tdr,  "時域 Golden")]:
                ax.plot(x, gold['mean'], 'b-', lw=2, label="Mean")
                ax.fill_between(x, gold['lower'], gold['upper'], color='red', alpha=0.2, label=f"{sigma}σ")
                ax.fill_between(x, gold['p5'], gold['p95'], color='gray', alpha=0.2, label="5-95%")
                ax.set_title(title); ax.set_xlabel("Index"); ax.set_ylabel("Value"); ax.legend(); ax.grid(alpha=0.3)
            pyplot(fig)
            markdown(fig_to_png_link(fig, "Golden_Standard.png"), unsafe_allow_html=True)
            # 儲存
            if button("💾 儲存 Golden 標準"):
                os.makedirs("golden", exist_ok=True)
                with open("golden/golden_freq.pkl","wb") as f: pickle.dump(golden_freq, f)
                with open("golden/golden_tdr.pkl","wb")  as f: pickle.dump(golden_tdr, f)
                success("✅ Golden 標準已儲存！")

elif mode == "比對新檔":
    title("🔬 比對新樣品")
    if not (os.path.exists("golden/golden_freq.pkl") and os.path.exists("golden/golden_tdr.pkl")):
        error("❌ 尚未建立 Golden 標準，請先至『建立Golden』完成"); stop()
    golden_freq = pickle.load(open("golden/golden_freq.pkl","rb"))
    golden_tdr  = pickle.load(open("golden/golden_tdr.pkl","rb"))
    uploaded = file_uploader("上傳待測檔案", type=["xlsx"])
    if uploaded:
        try:
            頻資框 = read_excel(uploaded, sheet_name="Excel Data")
            時資框  = read_excel(uploaded, sheet_name="TDR Data")
            f_col, zf_col = 頻資框.columns[0], 頻資框.columns[1]
            t_col, zt_col = 時資框.columns[0],  時資框.columns[1]
            z_freq = to_numeric(頻資框[zf_col], errors='coerce').dropna().values
            z_tdr  = to_numeric(時資框[zt_col], errors='coerce').dropna().values
        except Exception as e:
            error(f"讀取失敗：{e}"); stop()
        # 計算分數
        score_freq, rmse_freq, corr_freq = similarity_score(z_freq, golden_freq)
        score_tdr,  rmse_tdr,  corr_tdr  = similarity_score(z_tdr,  golden_tdr)
        # 摘要
        col1,col2,col3,col4 = columns(4)
        col1.metric("頻域相似度", f"{score_freq:.1f}/100")
        col2.metric("頻域RMSE",  f"{rmse_freq:.2f}")
        col3.metric("時域相似度", f"{score_tdr:.1f}/100")
        col4.metric("時域RMSE",  f"{rmse_tdr:.2f}")
        # 視覺化
        fig, (ax1,ax2) = plt.subplots(1,2, figsize=(14,5))
        xf = arange(len(z_freq))*0.01; xt = arange(len(z_tdr))*0.01
        # 頻域
        ax1.plot(xf, golden_freq['mean'], 'b-', lw=2, label="Golden Mean")
        ax1.fill_between(xf, golden_freq['lower'], golden_freq['upper'], color='gray', alpha=0.2)
        ax1.plot(xf, z_freq, 'g-', lw=2, label="New Sample")
        ax1.set_title("Freq Domain vs Golden"); ax1.legend(); ax1.grid(alpha=0.3)
        # 時域
        ax2.plot(xt, golden_tdr['mean'], 'b-', lw=2, label="Golden Mean")
        ax2.fill_between(xt, golden_tdr['lower'], golden_tdr['upper'], color='gray', alpha=0.2)
        ax2.plot(xt, z_tdr, 'g-', lw=2, label="New Sample")
        ax2.set_title("TDR vs Golden"); ax2.legend(); ax2.grid(alpha=0.3)
        pyplot(fig)
        # 判定
        markdown("---")
        if score_freq>=85 and score_tdr>=85:
            success("✅ PASS – 雙域皆符合 Golden 規格")
        elif score_freq>=70 and score_tdr>=70:
            warning("⚠️ CONDITIONAL – 建議加強監控")
        else:
            error("❌ FAIL – 超出 Golden 容差")
        # 下載報告
        report = DataFrame([{"Domain":"Frequency","Score":score_freq,"RMSE":rmse_freq,"Corr":corr_freq},
                               {"Domain":"TDR","Score":score_tdr,"RMSE":rmse_tdr,"Corr":corr_tdr}])
        excel_buf = BytesIO()
        vith ExcelWriter(excel_buf, engine="openpyxl") as w:
            report.to_excel(w, sheet_name="Summary", index=False)
        excel_buf.seek(0)
        download_button("📥 下載比對報告", excel_buf, "Comparison_vs_Golden.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

elif mode == "管理Golden":
    title("🗃️ 管理 Golden 檔案")
    if button("🗑️ 刪除現有 Golden"):
        for f in ["golden/golden_freq.pkl", "golden/golden_tdr.pkl"]:
            if os.path.exists(f): os.remove(f)
        success("已刪除，可重新建立")
    if os.path.exists("golden/golden_freq.pkl"):
        info("✅ Golden 檔案存在"); 
    else:
        info("❌ Golden 檔案不存在")
