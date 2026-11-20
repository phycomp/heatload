from pandas import DataFrame, ExcelFile, ExcelWriter, read_excel, to_numeric
from streamlit import success, empty, pyplot
from numpy import arange, array, corrcoef, mean, sqrt, std
from matplotlib.pyplot import subplots
from fontUtil import 字型明體
明體=字型明體()

def 繪圖(通道, 金, sigma, step=100):
  fig, ax = subplots(figsize=(10,4))
  #x_new  =z_new= arange(10/step)*0.01 #len(z_new) 假設 10 MHz/step
  x_golden=x_new=z_new=arange(len(金['mean']))*.01
  ax.plot(x_golden, 金['mean'], 'b-', lw=2, label="Golden Mean")
  ax.fill_between(x_golden, 金['lower'], 金['upper'], color='gray', alpha=0.2, label=f"{sigma}σ")
  ax.plot(x_new, z_new, 'g-', lw=2, label=f"New: {通道}")
  ax.set_title(f"{通道}疊圖", fontproperties=明體); ax.set_xlabel("Index (×10 MHz/step)"); ax.set_ylabel("Magnitude (dB)")    #{通道}
  ax.legend(); ax.grid(alpha=.3)
  pyplot(fig)

def 上傳():
  zip_file = file_uploader("ZIP 檔案", type=["zip"])
  if zip_file and 黃金標準:
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
                  xl = ExcelFile(fp)
                  for sheet in xl.sheet_names:
                      df = xl.parse(sheet)
                      for col in df.columns:
                          if 'CH(' in str(col) and ('Diff IL' in str(col) or 'Diff RL' in str(col)):
                              param = 'Diff-IL' if 'Diff IL' in str(col) else 'Diff-RL'
                              key   = (sheet, col, param)
                              if key not in 黃金標準: continue   # 只比對已存在 Golden
                              z     = to_numeric(df[col], errors='coerce').dropna().values
                              score, rmse, corr = similarity_score(z, 黃金標準[key])
                              report.append({
                                  "檔案": fname,
                                  "工作表": sheet,
                                  "通道": col,
                                  "參數": param,
                                  "相似度": score,
                                  "RMSE": rmse,
                                  "判定": "PASS" if score>=85 else ("CONDITIONAL" if score>=70 else "FAIL")
                              })
              except Exception as e:
                  report.append({"檔案": fname, "工作表": "-", "通道": "-", "參數": "-", "相似度": None, "RMSE": None, "判定": str(e)})
              progress.progress((idx+1)/len(xlsx_list))
          
          # 3️⃣ 結果視覺化
          df_report = DataFrame(report)
          dataframe(df_report)
          # Bar
          fig_bar = px.bar(df_report, x="檔案", y="相似度", color="判定", title="各檔案-通道-參數 vs Golden 相似度", height=400, color_discrete_map={"PASS":"green","CONDITIONAL":"orange","FAIL":"red"})
          fig_bar.update_layout(xaxis_tickangle=-45)
          plotly_chart(fig_bar, use_container_width=True)
          # Scatter
          fig_scatter = px.scatter(df_report, x="RMSE", y="相似度", color="判定", hover_data=["檔案","通道","參數"], title="RMSE vs 相似度分佈")
          plotly_chart(fig_scatter, use_container_width=True)
          
          # 4️⃣ 下載報告
          excel_buf = BytesIO()
          with ExcelWriter(excel_buf, engine="openpyxl") as w:
              df_report.to_excel(w, sheet_name="Summary", index=False)
          excel_buf.seek(0)
          download_button("📥 下載完整報告", excel_buf, "Diff_ILRL_ZIP_Comparison_Report.xlsx",
                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
          
          # 5️⃣ 單檔-單通道疊圖檢視
          markdown("---")
          subheader("📈 詳細疊圖檢視")
          sel_file  = radio("選擇檔案", df_report["檔案"].unique(), horizontal=True)
          sel_sheet = radio("選擇工作表", df_report[df_report["檔案"]==sel_file]["工作表"].unique(), horizontal=True)
          sel_ch    = radio("選擇通道", df_report[(df_report["檔案"]==sel_file)&(df_report["工作表"]==sel_sheet)]["通道"].unique(), horizontal=True)
          sel_param = df_report[(df_report["檔案"]==sel_file)&(df_report["工作表"]==sel_sheet)&(df_report["通道"]==sel_ch)]["參數"].iloc[0]
          fp_sel = [p for p in xlsx_list if os.path.basename(p)==sel_file][0]
          df_sel = read_excel(fp_sel, sheet_name=sel_sheet)
          z_new  = to_numeric(df_sel[sel_ch], errors='coerce').dropna().values
          golden = 黃金標準[(sel_sheet, sel_ch, sel_param)]
          fig, ax = subplots(figsize=(10,4))
          x_new  = arange(len(z_new))*0.01   # 假設 10 MHz/step
          x_golden = arange(len(golden['mean']))*0.01
          ax.plot(x_golden, golden['mean'], 'b-', lw=2, label="Golden Mean")
          ax.fill_between(x_golden, golden['lower'], golden['upper'], color='gray', alpha=0.2, label=f"{sigma}σ")
          ax.plot(x_new, z_new, 'g-', lw=2, label=f"New: {sel_file}")
          ax.set_title(f"{sel_ch}  {sel_param} 疊圖"); ax.set_xlabel("Index (×10 MHz/step)"); ax.set_ylabel("Magnitude (dB)")
          ax.legend(); ax.grid(alpha=0.3)
          pyplot(fig)
          markdown(fig_to_png_link(fig, f"Compare_{sel_file}_{sel_sheet}_{sel_ch}_{sel_param}.png"), unsafe_allow_html=True)

def 統計數據(arrays):
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

def 建立標準(目錄):
  金狀態=empty()
  黃金標準 = {}   # 儲存每通道的 golden
  #if golden_files and len(golden_files)>=3:
  collect = {}  # key: (sheet, channel, param) -> list[z]
  for f in 目錄.rglob('*.xlsx'):    #golden_files # 收集所有檔案的「相同通道」數據
    #try:
    xl = ExcelFile(f)
    for sheet in xl.sheet_names:
      df = xl.parse(sheet)
      # 掃描所有 CH(*) 欄位
      for col in df.columns:
        if 'CH(' in str(col) and ('Diff IL' in str(col) or 'Diff RL' in str(col)):
          param = 'Diff-IL' if 'Diff IL' in str(col) else 'Diff-RL'
          key   = '|'.join([sheet, col, param])
          z     = to_numeric(df[col], errors='coerce').dropna().values
          collect.setdefault(key, []).append(z)
    #except Exception as e: error(f"{f.name} 讀取失敗：{e}")
  for key, z_list in collect.items():
      黃金標準[key] = 統計數據(z_list) # 建立每 (sheet, channel, param) 的 Golden
  金狀態.code(黃金標準.keys())
  success(f"✅ 已建立 {len(黃金標準)} 組 Golden（每通道-每參數）")
  return 黃金標準
