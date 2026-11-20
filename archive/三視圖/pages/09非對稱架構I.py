from streamlit import button, caption, checkbox, column_config, columns, dataframe, divider, download_button, error, exception, expander, subheader, metric, radio, set_page_config, sidebar, success, text_input, title, write
from pandas import DataFrame, ExcelWriter, Series
# import streamlit as st
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, Border, Side
import io

# 設定頁面配置
set_page_config(page_title="FPC 參數管理系統", layout="wide")

# 定義所有資料
def 製作分頁():
    """建立所有資料的 DataFrame"""
    
    # 分頁 1: cable 尺寸計算
    df_cable = DataFrame({
        '項目': [
            '1mm=1000um', 'Ground space', 'line:W1', 'space:D1',
            '8*W1', '8*D1*2', '8W1+8*D1*2', '9*Ground space',
            'cable width(um)', '1*W1+2*D1+GND', 'Pitch(SMPM)'
        ],
        '數值 (um)': [1000, 100, 65, 171, 520, 2736, 3256, 900, 4156, 507, 3560],
        '備註': [
            '換算基準', '接地間距', '訊號線寬', '訊號至地間距',
            '8 倍線寬', '8 倍雙邊間距', '子總和', '9 倍接地間距',
            '總纜線寬度', '單組 pitch', 'SMPM 接頭 pitch'
        ]
    })
    
    # 分頁 2: FPC 疊構
    df_stackup = DataFrame({
        '層別': [
            'Top-Coverlay', 'Top-Coverlay', 'PTH', 'L1', '介電層',
            '介電層', 'L2', '介電層', 'L3', 'PTH', 'Bot-Coverlay', 'Bot-Coverlay'
        ],
        '材料': ['PI', 'AD', '電鍍', 'NbTi', 'PI', 'PI glue', 'NbTi', 'PI', 'NbTi', '電鍍', 'AD', 'PI'],
        'DK': ['?', '?', '?', '?', 3.3, 3.5, '?', 3.3, '?', '?', '?', '?'],
        'DF': ['?', '?', '?', '?', '0.004-0.0077', '?', '?', '0.004-0.0077', '?', '?', '?', '?'],
        '厚度 (um)': [25, 25, 15, 0.2, '?', '?', 0.2, '?', 0.2, 15, 25, 25],
        '備註': [
            '覆蓋膜', '膠層', '通孔鍍層', '接地層', '第一層 PI',
            '膠合層', '訊號層', '第二層 PI', '接地層', '通孔鍍層',
            '底部膠層', '底部覆蓋膜'
        ]
    })
    
    # 補充規格
    df_spec = DataFrame({
        '項目': ['H1/H2 Ground', 'Signal', 'J&T Estimated(mm)'],
        '數值 (um)': [62.5, 50.0, ''],
        '備註': ['接地層高度', '訊號層高度', '待補充']
    })
    
    # 分頁 3: Offset Coplanar Waveguide 參數
    df_cpw = DataFrame({
        '參數': ['H1', 'Er1', 'H2', 'Er2', 'W1', 'W2', 'D1', 'T1', 'T2', '阻抗 Zo'],
        '數值 (um)': [62.50, 3.3000, 50.20, 3.3000, 65.00, 44.00, 171.00, 0.20, 0.00, '50.46 Ω'],
        '說明': [
            '基板 1 高度', '基板 1 介電常數', '基板 2 高度', '基板 2 介電常數',
            '上層訊號線寬', '下層訊號線寬', '地線間距', '銅箔厚度',
            '(未使用)', '模擬結果'
        ]
    })
    
    # 分頁 4: 層間材料與厚度對應
    df_layers = DataFrame({
        '層別': ['L3', 'PI (#1)', 'L2', 'PI glue', 'PI (#2)', 'L1', 'H2', 'H1'],
        '材料': ['NbTi', 'PI', 'NbTi', 'PI glue', 'PI', 'NbTi', '-', '-'],
        'Er': ['-', 3.3, '-', 3.5, 3.3, '-', '-', '-'],
        '厚度 (um)': [0.2, 50, 0.2, 12.5, 50, 0.2, 50.2, 62.5],
        '說明': [
            '接地層', '介電層', '訊號層', '膠合層',
            '介電層', '接地層', '總和標示', '總和標示'
        ]
    })
    return df_cable, df_stackup, df_spec, df_cpw, df_layers
    # return zip(表單, [df_cable, df_stackup, df_spec, df_cpw, df_layers])
    
    return {
        'Cable尺寸計算': df_cable,
        'FPC疊構': df_stackup,
        'FPC規格補充': df_spec,
        'CPW參數': df_cpw,
        '層間材料對應': df_layers
    }

# 建立所有 DataFrame

MENU, 表單=[], ['Cable尺寸計算', 'FPC疊構', 'FPC規格補充', 'CPW參數', '層間材料對應']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  # 本益比=slider("最高本益比(PE)", 0, 100, 25)
  # srch=text_input('搜尋', '')
# ========== 頁面 1: 建立 DataFrame ==========
subheader("📊 FPC 參數管理系統")
subheader("1️⃣ 建立 DataFrame")
write("已建立以下資料表：")
分頁資料 = 製作分頁()
資框=DataFrame([分頁資料], columns=表單)
# 資框=DataFrame([分頁資料], columns=表單)
# 資框=dict(zip(表單, 分頁資料))
# 資框=DataFrame([分頁資料], columns=表單)
資框
# 顯示所有 DataFrame 名稱
#col1, col2, col3, col4, col5 = columns(5)
#with col1:
#    metric("總資料表數", len(資框))
#with col2:
#    metric("Cable 參數", f"{len(資框['Cable 尺寸計算'])} 筆")
#with col3:
#    metric("FPC 疊構", f"{len(資框['FPC 疊構'])} 筆")
#with col4:
#    metric("CPW 參數", f"{len(資框['CPW 參數'])} 筆")
#with col5:
#    metric("層間對應", f"{len(資框['層間材料對應'])} 筆")

# ========== 頁面 2: 預覽 ==========
subheader("2️⃣ 資料預覽")

# 選擇要預覽的資料表
# sheet_name = radio("選擇要預覽的資料表", list(資框.keys()), horizontal=True)

# 顯示所選資料表
if menu:
  框資 = 資框[menu[1:]]
  subheader(f"📋 {menu[1:]}")

  # 顯示資料表
  框資
  dataframe(
      df_selected,
      use_container_width=True,
      height=400,
      column_config={
          "數值 (um)": column_config.NumberColumn("數值 (um)", format="%.2f"),
          "厚度 (um)": column_config.TextColumn("厚度 (um)"),
      }
  )

# 顯示基本統計資訊
with expander("📊 資料統計資訊"):
    col1, col2, col3 = columns(3)
    with col1:
        write(f"**列數:** {len(df_selected)}")
    with col2:
        write(f"**欄數:** {len(df_selected.columns)}")
    with col3:
        # 計算數值型欄位的統計
        numeric_cols = df_selected.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            write(f"**數值欄位:** {', '.join(numeric_cols)}")
    
    # 顯示數值統計
    if len(numeric_cols) > 0:
        write("數值欄位統計:")
        dataframe(df_selected[numeric_cols].describe())

# ========== 頁面 3: 匯出 Excel ==========
subheader("3️⃣ 匯出至 Excel")

# 匯出選項
col1, col2 = columns(2)

with col1:
    file_name = text_input("檔案名稱", value="FPC_Parameters.xlsx")

with col2:
    include_stats = checkbox("加入統計資訊分頁", value=True)

# 匯出按鈕
if button("📥 匯出 Excel 檔案", type="primary", use_container_width=True):
    try:
        # 建立 Excel 檔案
        output = io.BytesIO()
        
        with ExcelWriter(output, engine='openpyxl') as writer:
            # 寫入所有資料表
            for sheet_name, df in 資框.items():
                # 將所有欄位轉為字串，避免數值格式問題
                df_copy = df.copy()
                for col in df_copy.columns:
                    if df_copy[col].dtype == 'object':
                        df_copy[col] = df_copy[col].astype(str)
                df_copy.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # 調整欄寬
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 30)  # 限制最大寬度
                    worksheet.column_dimensions[column_letter].width = adjusted_width
                
                # 設定標題列格式
                for cell in worksheet[1]:
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # 加入統計資訊分頁
            if include_stats:
                stats_data = []
                for sheet_name, df in 資框.items():
                    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
                    stats_data.append({
                        '資料表': sheet_name,
                        '列數': len(df),
                        '欄數': len(df.columns),
                        '數值欄位': ', '.join(numeric_cols) if len(numeric_cols) > 0 else '無'
                    })
                
                df_stats = DataFrame(stats_data)
                df_stats.to_excel(writer, sheet_name='統計資訊', index=False)
                
                # 調整統計資訊欄寬
                worksheet = writer.sheets['統計資訊']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 30)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # 提供下載
        output.seek(0)
        success("✅ Excel 檔案建立成功！")
        
        download_button(
            label="💾 下載 Excel 檔案",
            data=output,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    except Exception as e:
        error(f"❌ 匯出失敗: {str(e)}")
        exception(e)

# ========== 側邊欄：快速檢視 ==========
with sidebar:
    subheader("📌 快速檢視")
    
    # 顯示所有資料表名稱和筆數
    write("**資料表清單:**")
    for name, df in 資框.items():
        write(f"- {name}: {len(df)} 筆資料")
    
    divider()
    
    # 顯示範例資料
    write("**範例資料 (前 3 筆):**")
    preview_sheet = radio("選擇預覽資料表", list(資框.keys()), key="preview_sidebar", horizontal=True)
    dataframe(
        資框[preview_sheet].head(3),
        use_container_width=True,
        hide_index=True
    )
    
    divider()
    
    # 使用說明
    write("**使用說明:**")
    write("""
    1. 在「資料預覽」頁面查看各資料表
    2. 選擇要匯出的檔案名稱
    3. 點擊「匯出 Excel 檔案」下載
    4. 所有分頁會自動調整欄寬
    """)
    
    divider()
    caption("FPC 參數管理系統 v1.0")

# 顯示成功訊息
success("✅ 系統已就緒！請使用上方功能進行操作。")
