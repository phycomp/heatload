from pandas import read_csv, to_numeric
from streamlit import metric, columns, subheader, dataframe, radio, color_picker, pyplot, write, download_button, button
from matplotlib.pyplot import subplots, tight_layout

def 安全頻率(df, col_idx=0):
    """回傳字串；容許 NaN / 非數字"""
    ser = to_numeric(df.iloc[:, col_idx], errors='coerce').dropna()
    return f"{ser.min():.4f} - {ser.max():.4f} GHz" if not ser.empty else "無效資料"

# 使用
def csv2Plot(df):
  #df = read_csv(uploaded_file)
  
  # 顯示數據基本信息
  dataframe(df)
  subheader("數據概覽")
  col1, col2, col3 = columns(3)
  
  with col1:
      metric("數據點數", len(df))
  
  with col2:
      #freq_col = df.iloc[:, 0]
      #freq_num = to_numeric(freq_col, errors='coerce').dropna() # 若含有空字串或非數字，先用 to_numeric 強制轉換，invalid 會變 NaN
      pass
      #dataframe(df.iloc[:, 0])
      #metric("頻率範圍", f"{df.iloc[:, 0].min():.4f} - {df.iloc[:, 0].max():.4f} GHz")
      metric("頻率範圍", 安全頻率(df))
  
  with col3:
    pass
      #metric("頻率間隔", f"{(df.iloc[1, 0] - df.iloc[0, 0]):.6f} GHz")
  
  # 顯示數據預覽
  subheader("數據預覽")
  dataframe(df.head(10), use_container_width=True)
  
  # 可視化選項
  subheader("可視化設置")
  
  col1, col2 = columns(2)
  
  with col1:
      plot_type = radio( "選擇圖表類型", ["折線圖", "散點圖", "直方圖", "面積圖"], horizontal=True, index=0)
      
  with col2:
      color = color_picker("選擇線條顏色", "#1f77b4")
  
  # 創建圖表
  fig, ax = subplots(figsize=(12, 6))
  
  frequency_data = df.iloc[:, 2]
  
  if plot_type == "折線圖":
      ax.plot(frequency_data, marker='o', markersize=2, linewidth=1, color=color)
      ax.set_title('頻率數據 - 折線圖', fontsize=14, fontweight='bold')
      
  elif plot_type == "散點圖":
      ax.scatter(range(len(frequency_data)), frequency_data, s=10, color=color, alpha=0.6)
      ax.set_title('頻率數據 - 散點圖', fontsize=14, fontweight='bold')
      
  elif plot_type == "直方圖":
      ax.hist(frequency_data, bins=50, color=color, alpha=0.7, edgecolor='black')
      ax.set_title('頻率數據分布 - 直方圖', fontsize=14, fontweight='bold')
      ax.set_xlabel('頻率 (GHz)')
      ax.set_ylabel('頻數')
      
  elif plot_type == "面積圖":
      ax.fill_between(range(len(frequency_data)), frequency_data, alpha=0.5, color=color)
      ax.plot(frequency_data, color=color, linewidth=1)
      ax.set_title('頻率數據 - 面積圖', fontsize=14, fontweight='bold')
  
  if plot_type != "直方圖":
      ax.set_xlabel('數據點索引')
      ax.set_ylabel('頻率 (GHz)')
  
  ax.grid(True, alpha=0.3)
  tight_layout()
  
  subheader("數據可視化")
  pyplot(fig)
  
  # 統計信息
  subheader("統計分析")
  
  col1, col2, col3, col4 = columns(4)
  
  with col1:
      metric("平均值", f"{frequency_data.mean():.6f} GHz")
  
  with col2:
      metric("標準差", f"{frequency_data.std():.6f} GHz")
  
  with col3:
      metric("最小值", f"{frequency_data.min():.6f} GHz")
  
  with col4:
      metric("最大值", f"{frequency_data.max():.6f} GHz")
  
  # 數據下載
  subheader("數據處理")
  
  col1, col2 = columns(2)
  
  with col1:
      # 轉換爲DataFrame供下載
      csv = df.to_csv(index=False)
      download_button(
          label="下載處理後的CSV文件",
          data=csv,
          file_name="processed_frequency_data.csv",
          mime="text/csv"
      )
  
  with col2:
      # 顯示數據統計摘要
      if button("顯示詳細統計信息"):
          write(frequency_data.describe())
  
#except Exception as e:
#  error(f"處理文件時出錯: {str(e)}")
#  info("請確保上傳的文件格式正確，包含頻率數據。")

#else:
#info("👆 請上傳CSV文件開始分析")

# 顯示示例數據
subheader("數據格式示例")
write("""
預期的CSV文件格式應該包含頻率數據，例如：
- 頻率單位：GHz
- 數據格式：單列數值數據
- 文件結構：
  ```
  Frequency (GHz)
  0.0
  0.0013013013013
  0.0026026026026
  ...
  ```
""")
