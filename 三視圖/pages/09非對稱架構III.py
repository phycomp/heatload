from streamlit import button, caption, checkbox, code, column_config, columns, dataframe, divider, download_button, error, exception, expander, metric, radio, set_page_config, sidebar, subheader, success, text_input, title, write
from pandas import DataFrame, ExcelWriter
import streamlit as st
from re import match
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, Border, Side
from io import BytesIO

# 設定頁面配置
set_page_config(page_title="FPC 參數管理系統", layout="wide")

def 製作分頁(表單):
    """使用 DataFrame(dset, columns=[]) 建立所有資料的 DataFrame"""
    
    # ========== 分頁 1: Cable 尺寸計算 ==========
    cable_data = [
        ['1mm=1000um', 1000, '換算基準'],
        ['Ground space', 100, '接地間距'],
        ['line:W1', 65, '訊號線寬'],
        ['space:D1', 171, '訊號至地間距'],
        ['8*W1', 520, '8 倍線寬'],
        ['8*D1*2', 2736, '8 倍雙邊間距'],
        ['8W1+8*D1*2', 3256, '子總和'],
        ['9*Ground space', 900, '9 倍接地間距'],
        ['cable width(um)', 4156, '總纜線寬度'],
        ['1*W1+2*D1+GND', 507, '單組 pitch'],
        ['Pitch(SMPM)', 3560, 'SMPM 接頭 pitch']
    ]
    df_cable = DataFrame(cable_data, columns=['項目', '數值 (um)', '備註'])
    
    # ========== 分頁 2: FPC 疊構（已補齊所有資料） ==========
    stackup_data = [
        ['上覆蓋膜', 'PI', 3.2, 0.008, 25, '覆蓋膜（PI 基材）', '✅新增'],  #Top-Coverlay
        ['上膠層', 'AD', 3.3, 0.015, 25, '膠層（環氧樹脂系）', '✅新增'], #Top-Coverlay
        ['上通孔鍍層-銅', '電鍍', 17, '-', 15, '通孔鍍層（銅）', '✅新增'],  #PTH
        ['上接地層', 'NbTi', '-', '-', 0.2, '接地層（金屬）', '-'], #L1
        ['上介電層', 'PI', 3.3, '0.004-0.0077', 50, '第一層 PI（已補充厚度）', '✅新增'],
        ['上介電膠', 'PI膠', 3.5, 0.012, 12.5, '膠合層（已補充厚度及 DF）', '✅新增'],
        ['訊號層', 'NbTi', '-', '-', 0.2, '訊號層（金屬）', '-'], #L2
        ['底介電層', 'PI', 3.3, '0.004-0.0077', 50, '第二層 PI（已補充厚度）', '✅新增'],
        ['底接地層', 'NbTi', '-', '-', 0.2, '接地層（金屬）', '-'], #L3
        ['底通孔鍍層-銅', '電鍍', 17, '-', 15, '通孔鍍層（銅）', '✅新增'], #PTH
        ['底膠層', 'AD', 3.3, 0.015, 25, '底部膠層', '✅新增'], #Bot-Coverlay
        ['底覆蓋膜', 'PI', 3.2, 0.008, 25, '底部覆蓋膜', '✅新增']  #Bot-Coverlay
    ]
    df_stackup = DataFrame(
        stackup_data, 
        columns=['層別', '材料', 'DK', 'DF', '厚度 (um)', '備註', '更新標記']
    )
    
    # ========== 分頁 3: FPC 規格補充 ==========
    spec_data = [
        ['H1/H2 Ground', 62.5, '接地層高度'],
        ['Signal', 50.0, '訊號層高度'],
        ['J&T Estimated(mm)', '', '待補充']
    ]
    df_spec = DataFrame(spec_data, columns=['項目', '數值 (um)', '備註'])
    
    # ========== 分頁 4: CPW 參數 ==========
    cpw_data = [
        ['H1', 62.50, '基板 1 高度'],
        ['Er1', 3.3000, '基板 1 介電常數'],
        ['H2', 50.20, '基板 2 高度'],
        ['Er2', 3.3000, '基板 2 介電常數'],
        ['W1', 65.00, '上層訊號線寬'],
        ['W2', 44.00, '下層訊號線寬'],
        ['D1', 171.00, '地線間距'],
        ['T1', 0.20, '銅箔厚度'],
        ['T2', 0.00, '(未使用)'],
        ['阻抗 Zo', '50.46 Ω', '模擬結果']
    ]
    df_cpw = DataFrame(cpw_data, columns=['參數', '數值 (um)', '說明'])
    
    # ========== 分頁 5: 層間材料與厚度對應 ==========
    layers_data = [
        ['L3', 'NbTi', '-', 0.2, '接地層'],
        ['PI (#1)', 'PI', 3.3, 50, '介電層'],
        ['L2', 'NbTi', '-', 0.2, '訊號層'],
        ['PI glue', 'PI glue', 3.5, 12.5, '膠合層'],
        ['PI (#2)', 'PI', 3.3, 50, '介電層'],
        ['L1', 'NbTi', '-', 0.2, '接地層'],
        ['H2', '-', '-', 50.2, '總和標示'],
        ['H1', '-', '-', 62.5, '總和標示']
    ]
    df_layers = DataFrame(layers_data, columns=['層別', '材料', 'Er', '厚度 (um)', '說明'])
    
    return dict(zip(表單, [df_cable, df_stackup, df_spec, df_cpw, df_layers]))
    # return { 'Cable 尺寸計算': df_cable, 'FPC 疊構 (完整)': df_stackup, 'FPC 規格補充': df_spec, 'CPW 參數': df_cpw, '層間材料對應': df_layers }

# 建立所有 DataFrame
MENU, 表單=[], ['Cable尺寸計算', 'FPC疊構', 'FPC規格補充', 'CPW參數', '層間材料對應', '匯出']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  subheader("📊 FPC 參數管理系統（完整版）")
  menu=radio('表單', MENU, horizontal=True, index=0)
資框 = 製作分頁(表單)
if '匯出' in menu:
    subheader("3️⃣ 匯出至 Excel")
    subheader("1️⃣ 建立 DataFrame（使用 DataFrame(dset, columns=[])）")
    from 匯出UtilIII import 匯出表單
    檔名, 字型, 表頭字型="FPC完整_Parameters.xlsx", 16, 16
    excel_file = 匯出表單(dataframes=資框, file_name=檔名, font_size=字型, header_font_size=表頭字型, include_changelog=True)
    download_button(label="💾 下載 Excel 檔案", data=excel_file, file_name=檔名, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
elif match(r'\d', menu):
  分頁=menu[1:]
  # 資框[分頁]
  分頁資框 = 資框[分頁]
  metric(分頁, f"{len(分頁資框)} 筆")
  # subheader(f"📋 {sheet_name}")

  dataframe(分頁資框, use_container_width=True, height=400, column_config={ "數值 (um)": column_config.NumberColumn("數值 (um)", format="%.2f"), "厚度 (um)": column_config.TextColumn("厚度 (um)"), }) # 顯示資料表
  col1, col2, col3 = columns(3)
  with col1:
      write(f"**列數:** {len(分頁資框)}")
  with col2:
      write(f"**欄數:** {len(分頁資框.columns)}")
  with col3:
      # 計算數值型欄位的統計
      numeric_cols = 分頁資框.select_dtypes(include=['float64', 'int64']).columns
      if len(numeric_cols) > 0:
          write(f"**數值欄位:** {', '.join(numeric_cols)}")
  
  # 顯示數值統計
  if len(numeric_cols) > 0:
      write("數值欄位統計:")
      dataframe(分頁資框[numeric_cols].describe())

# ========== 頁面 1: 建立 DataFrame ==========

# 顯示程式碼範例
#with expander("📝 查看程式碼範例", expanded=False):
#    code("""
## 使用 DataFrame(dset, columns=[]) 建立 DataFrame 範例
#stackup_data = [
#    ['Top-Coverlay', 'PI', 3.2, 0.008, 25, '覆蓋膜（PI 基材）', '✅新增'],
#    ['Top-Coverlay', 'AD', 3.3, 0.015, 25, '膠層（環氧樹脂系）', '✅新增'],
#    ['PTH', '電鍍', 17, '-', 15, '通孔鍍層（銅）', '✅新增'],
#    # ... 更多資料
#]
#df_stackup = DataFrame(
#    stackup_data, 
#    columns=['層別', '材料', 'DK', 'DF', '厚度 (um)', '備註', '更新標記']
#)
#    """, language="python")

# 顯示所有 DataFrame 名稱
#col1, col2, col3, col4, col5 = columns(5)
#with col1:
#    metric("總資料表數", len(資框))
#with col2:
#    metric("Cable 參數", f"{len(資框['Cable 尺寸計算'])} 筆")
#with col3:
#    metric("FPC 疊構", f"{len(資框['FPC 疊構 (完整)'])} 筆 ✅")
#with col4:
#    metric("CPW 參數", f"{len(資框['CPW 參數'])} 筆")
#with col5:
#    metric("層間對應", f"{len(資框['層間材料對應'])} 筆")

# ========== 頁面 2: 資料預覽 ==========
# subheader("2️⃣ 資料預覽")

# 選擇要預覽的資料表
# sheet_name = radio("選擇要預覽的資料表", list(資框.keys()), horizontal=True)

# 顯示所選資料表

# 顯示更新對照（僅針對 FPC 疊構）
else:
  if sheet_name == 'FPC 疊構 (完整)':
    subheader("🔄 更新項目對照（僅顯示有變更的欄位）")
    
    # 分離更新和未更新的資料
    df_changes = 分頁資框[df_selected['更新標記'] == '✅新增']
    
    if len(df_changes) > 0:
        # 建立對照表
        comparison_data = []
        for _, row in df_changes.iterrows():
            comparison_data.append([
                row['層別'],
                row['材料'],
                row['DK'],
                row['DF'],
                row['厚度 (um)'],
                row['備註']
            ])
        
        df_comparison = DataFrame(
            comparison_data,
            columns=['層別', '材料', 'DK (更新)', 'DF (更新)', '厚度 (更新)', '備註']
        )
        
        dataframe(df_comparison, use_container_width=True)
        caption(f"✅ 共更新 {len(df_changes)} 筆資料")
    else:
        write("無需更新的資料")

# 顯示基本統計資訊
# with expander("📊 資料統計資訊"):

# ========== 頁面 3: 匯出 Excel ==========

# ========== 側邊欄：資料結構檢視 ==========
with sidebar:
    subheader("📌 資料結構")
    
    # 顯示每個 DataFrame 的結構
    for name, df in 資框.items():
        with expander(f"📋 {name}"):
            write(f"**形狀:** {df.shape}")
            write(f"**欄位:** {', '.join(df.columns.tolist())}")
            # write("**前 2 筆資料:**")
            dataframe(df, use_container_width=True, hide_index=True)
            #.head(2)
    
    divider()
    
    # 顯示更新摘要
    subheader("✅ 更新摘要")
    write("""
    **FPC 疊構補充項目：**
    - Top-Coverlay PI: DK=3.2, DF=0.008
    - Top-Coverlay AD: DK=3.3, DF=0.015
    - PTH 電鍍: DK=17 (銅)
    - 介電層 PI: 厚度=50um
    - PI glue: DF=0.012, 厚度=12.5um
    - Bot-Coverlay: 同 Top-Coverlay
    """)
    
    divider()
    caption("FPC 參數管理系統 v2.0")

# success("✅ 系統已就緒！所有 DataFrame 均使用 DataFrame(dset, columns=[]) 建立。")
