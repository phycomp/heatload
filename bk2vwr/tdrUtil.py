from pandas import DataFrame
from pathlib import Path
from fontUtil import 字型明體
from streamlit import button, columns, download_button, error, file_uploader, info, markdown, pyplot, set_page_config, sidebar, stop, success, title, warning, empty, dataframe, session_state
from matplotlib.pyplot import subplots
from numpy import arange, array, corrcoef, mean, percentile, sqrt, std
from pandas import DataFrame, ExcelWriter, read_excel, to_numeric, concat
from matplotlib.pyplot import subplots
from io import BytesIO
from base64 import b64encode
明體=字型明體()

def 下載圖表(fig, fname):
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
    buf.seek(0)
    編碼 = b64encode(buf.read()).decode()
    return f'<a href="data:file/png;base64,{編碼}" download="{fname}">下載 PNG</a>'

def 數據統計(arrays):
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

def 相似度(z, golden):
  """回傳 0-100 綜合相似度"""
  if len(z) > len(golden['mean']): z = z[:len(golden['mean'])]
  rmse = sqrt(mean((z - golden['mean'])**2))
  corr = corrcoef(z, golden['mean'])[0,1]
  score = max(0, 100 - rmse*2) * max(0, corr)
  return score, rmse, corr

def 建立標準(目錄:Path, sigma): #頻資框, 時資框, sigma
  頻狀態=empty()
  時狀態=empty()
  總頻, 總時 =DataFrame(), DataFrame()# [], []
  for 檔 in 目錄.rglob('*.xlsx'):
    #try:
    try: 總資框=session_state[檔]
    except:總資框 = session_state[檔]=read_excel(檔, sheet_name=None)    #"Data"
    頻狀態.code([總資框.keys()])    #總資框, 
    if 'Data' in 總資框:
      頻資框=總資框['Data']   #=read_excel(檔, sheet_name="Data")
      頻狀態.code(頻資框.columns)
      dataframe(頻資框)
    if 'TDR Data' in 總資框: 時資框=總資框['TDR Data']   #=read_excel(檔, sheet_name="Data")
    #dataframe(頻資框)
    if 'TDR Data' in 總資框.keys():
      時資框  = read_excel(檔, sheet_name="TDR Data")    #Time (ns)
      #dataframe(時資框)
      #時狀態.code([時資框.columns]) #時資框, 
      #頻狀態.code([頻資框.columns]) #頻資框, 
      頻欄, zf_col = 頻資框.columns[0], 頻資框.columns[1]
      時欄 = 時資框.columns[0]#, zt_col,  時資框.columns[1]
      總頻=concat([總頻, 頻資框])#.append(to_numeric(頻資框[頻欄], errors='coerce').dropna().values)
      總時=concat([總時, 時資框])#.append(to_numeric(時資框[時欄], errors='coerce').dropna().values)
        #else:
          #pass
          #時資框  = read_excel(檔, sheet_name="TDR Data")    Time (ns)
        # 取第一欄當 X，第二欄當 Y（可依實際調整）
    #except Exception as e:
        #warning(f"{檔.name} 讀取失敗：{e}")
  #總頻=DataFrame(freq_curves)
  #總時=DataFrame(tdr_curves)
  dataframe(總頻)
  dataframe(總時)
  if freq_curves and tdr_curves:
      golden_freq = 數據統計(freq_curves)
      golden_tdr  = 數據統計(tdr_curves)
      # 視覺化
      fig, (ax1,ax2) = subplots(1,2, figsize=(14,5))
      xf = arange(len(golden_freq['mean']))*0.01  # 假設 10 MHz step
      xt = arange(len(golden_tdr['mean']))*0.01   # 假設 10 ps step
      for ax, x, gold, title in [(ax1, xf, golden_freq, "頻域 Golden"), (ax2, xt, golden_tdr,  "時域 Golden")]:
          ax.plot(x, gold['mean'], 'b-', lw=2, label="Mean")
          ax.fill_between(x, gold['lower'], gold['upper'], color='red', alpha=0.2, label=f"{sigma}σ")
          ax.fill_between(x, gold['p5'], gold['p95'], color='gray', alpha=0.2, label="5-95%")
          ax.set_title(title, fontproperties=明體); ax.set_xlabel("Index"); ax.set_ylabel("Value"); ax.legend(); ax.grid(alpha=0.3)
      pyplot(fig)
      markdown(下載圖表(fig, "Golden_Standard.png"), unsafe_allow_html=True)
      # 儲存
      if button("💾 儲存 Golden 標準"):
          os.makedirs("golden", exist_ok=True)
          with open("golden/golden_freq.pkl","wb") as f: pickle.dump(golden_freq, f)
          with open("golden/golden_tdr.pkl","wb")  as f: pickle.dump(golden_tdr, f)
          success("✅ Golden 標準已儲存！")

def 對比(頻資框, 時資框):
  try:
      f_col, zf_col = 頻資框.columns[0], 頻資框.columns[1]
      t_col, zt_col = 時資框.columns[0],  時資框.columns[1]
      z_freq = to_numeric(頻資框[zf_col], errors='coerce').dropna().values
      z_tdr  = to_numeric(時資框[zt_col], errors='coerce').dropna().values
  except Exception as e:
      error(f"讀取失敗：{e}"); stop()
  # 計算分數
  score_freq, rmse_freq, corr_freq = 相似度(z_freq, golden_freq)
  score_tdr,  rmse_tdr,  corr_tdr  = 相似度(z_tdr,  golden_tdr)
  # 摘要
  col1,col2,col3,col4 = columns(4)
  col1.metric("頻域相似度", f"{score_freq:.1f}/100")
  col2.metric("頻域RMSE",  f"{rmse_freq:.2f}")
  col3.metric("時域相似度", f"{score_tdr:.1f}/100")
  col4.metric("時域RMSE",  f"{rmse_tdr:.2f}")
  # 視覺化
  fig, (ax1,ax2) = subplots(1,2, figsize=(14,5))
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
  with ExcelWriter(excel_buf, engine="openpyxl") as w:
      report.to_excel(w, sheet_name="Summary", index=False)
  excel_buf.seek(0)
  download_button("📥 下載比對報告", excel_buf, "Comparison_vs_Golden.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
