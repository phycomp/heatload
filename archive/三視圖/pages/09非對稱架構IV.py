import streamlit as st
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
import io

# 設定頁面配置
st.set_page_config(page_title="FPC 參數管理系統", layout="wide")
st.title("📊 FPC 參數管理系統（完整版）")

def create_all_dataframes():
    """使用 pd.DataFrame(dset, columns=[]) 建立所有資料的 DataFrame"""
    
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
    df_cable = pd.DataFrame(cable_data, columns=['項目', '數值 (um)', '備註'])
    
    # ========== 分頁 2: FPC 疊構（已補齊所有資料） ==========
    stackup_data = [
        ['Top-Coverlay', 'PI', 3.2, 0.008, 25, '覆蓋膜（PI 基材）', '✅新增'],
        ['Top-Coverlay', 'AD', 3.3, 0.015, 25, '膠層（環氧樹脂系）', '✅新增'],
        ['PTH', '電鍍', 17, '-', 15, '通孔鍍層（銅）', '✅新增'],
        ['L1', 'NbTi', '-', '-', 0.2, '接地層（金屬）', '-'],
        ['介電層', 'PI', 3.3, '0.004-0.0077', 50, '第一層 PI（已補充厚度）', '✅新增'],
        ['介電層', 'PI glue', 3.5, 0.012, 12.5, '膠合層（已補充厚度及 DF）', '✅新增'],
        ['L2', 'NbTi', '-', '-', 0.2, '訊號層（金屬）', '-'],
        ['介電層', 'PI', 3.3, '0.004-0.0077', 50, '第二層 PI（已補充厚度）', '✅新增'],
        ['L3', 'NbTi', '-', '-', 0.2, '接地層（金屬）', '-'],
        ['PTH', '電鍍', 17, '-', 15, '通孔鍍層（銅）', '✅新增'],
        ['Bot-Coverlay', 'AD', 3.3, 0.015, 25, '底部膠層', '✅新增'],
        ['Bot-Coverlay', 'PI', 3.2, 0.008, 25, '底部覆蓋膜', '✅新增']
    ]
    df_stackup = pd.DataFrame(
        stackup_data, 
        columns=['層別', '材料', 'DK', 'DF', '厚度 (um)', '備註', '更新標記']
    )
    
    # ========== 分頁 3: FPC 規格補充 ==========
    spec_data = [
        ['H1/H2 Ground', 62.5, '接地層高度'],
        ['Signal', 50.0, '訊號層高度'],
        ['J&T Estimated(mm)', '', '待補充']
    ]
    df_spec = pd.DataFrame(spec_data, columns=['項目', '數值 (um)', '備註'])
    
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
    df_cpw = pd.DataFrame(cpw_data, columns=['參數', '數值 (um)', '說明'])
    
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
    df_layers = pd.DataFrame(layers_data, columns=['層別', '材料', 'Er', '厚度 (um)', '說明'])
    
    return {
        'Cable 尺寸計算': df_cable,
        'FPC 疊構 (完整)': df_stackup,
        'FPC 規格補充': df_spec,
        'CPW 參數': df_cpw,
        '層間材料對應': df_layers
    }


# 建立所有 DataFrame
dataframes = create_all_dataframes()

# ========== 頁面 1: 建立 DataFrame ==========
st.header("1️⃣ 建立 DataFrame（使用 pd.DataFrame(dset, columns=[])）")

# 顯示程式碼範例
with st.expander("📝 查看程式碼範例", expanded=False):
    st.code("""
# 使用 pd.DataFrame(dset, columns=[]) 建立 DataFrame 範例
stackup_data = [
    ['Top-Coverlay', 'PI', 3.2, 0.008, 25, '覆蓋膜（PI 基材）', '✅新增'],
    ['Top-Coverlay', 'AD', 3.3, 0.015, 25, '膠層（環氧樹脂系）', '✅新增'],
    # ... 更多資料
]
df_stackup = pd.DataFrame(
    stackup_data, 
    columns=['層別', '材料', 'DK', 'DF', '厚度 (um)', '備註', '更新標記']
)
    """, language="python")

# 顯示所有 DataFrame 名稱
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("總資料表數", len(dataframes))
with col2:
    st.metric("Cable 參數", f"{len(dataframes['Cable 尺寸計算'])} 筆")
with col3:
    st.metric("FPC 疊構", f"{len(dataframes['FPC 疊構 (完整)'])} 筆 ✅")
with col4:
    st.metric("CPW 參數", f"{len(dataframes['CPW 參數'])} 筆")
with col5:
    st.metric("層間對應", f"{len(dataframes['層間材料對應'])} 筆")

# ========== 頁面 2: 資料預覽 ==========
st.header("2️⃣ 資料預覽")

# 選擇要預覽的資料表
sheet_name = st.selectbox("選擇要預覽的資料表", list(dataframes.keys()))

# 顯示所選資料表
df_selected = dataframes[sheet_name]
st.subheader(f"📋 {sheet_name}")

# 顯示資料表
st.dataframe(
    df_selected,
    use_container_width=True,
    height=400,
    column_config={
        "數值 (um)": st.column_config.NumberColumn("數值 (um)", format="%.2f"),
        "厚度 (um)": st.column_config.TextColumn("厚度 (um)"),
    }
)

# 顯示更新對照（僅針對 FPC 疊構）
if sheet_name == 'FPC 疊構 (完整)':
    st.subheader("🔄 更新項目對照（僅顯示有變更的欄位）")
    
    # 分離更新和未更新的資料
    df_changes = df_selected[df_selected['更新標記'] == '✅新增']
    
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
        
        df_comparison = pd.DataFrame(
            comparison_data,
            columns=['層別', '材料', 'DK (更新)', 'DF (更新)', '厚度 (更新)', '備註']
        )
        
        st.dataframe(df_comparison, use_container_width=True)
        st.caption(f"✅ 共更新 {len(df_changes)} 筆資料")
    else:
        st.write("無需更新的資料")

# 顯示基本統計資訊
with st.expander("📊 資料統計資訊"):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**列數:** {len(df_selected)}")
    with col2:
        st.write(f"**欄數:** {len(df_selected.columns)}")
    with col3:
        # 計算數值型欄位的統計
        numeric_cols = df_selected.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            st.write(f"**數值欄位:** {', '.join(numeric_cols)}")
    
    # 顯示數值統計
    if len(numeric_cols) > 0:
        st.write("數值欄位統計:")
        st.dataframe(df_selected[numeric_cols].describe())

# ========== 頁面 3: 匯出 Excel ==========
st.header("3️⃣ 匯出至 Excel（可調整字型大小）")

# 匯出選項
col1, col2, col3 = st.columns(3)

with col1:
    file_name = st.text_input("檔案名稱", value="FPC_Parameters_Complete.xlsx")

with col2:
    # 一般字型大小選擇
    font_size = st.selectbox(
        "一般儲存格字型大小 (pt)",
        options=[9, 10, 11, 12, 13, 14, 16],
        index=2  # 預設 11pt
    )

with col3:
    # 標題字型大小選擇
    header_font_size = st.selectbox(
        "標題列字型大小 (pt)",
        options=[10, 11, 12, 13, 14, 16, 18],
        index=2  # 預設 12pt
    )

# 其他選項
col1, col2 = st.columns(2)
with col1:
    include_changelog = st.checkbox("加入更新紀錄分頁", value=True)
with col2:
    st.write(f"📝 預覽字型大小: 一般 {font_size}pt / 標題 {header_font_size}pt")

# 匯出按鈕
if st.button("📥 匯出 Excel 檔案", type="primary", use_container_width=True):
    try:
        # 匯出 Excel
        excel_file = export_to_excel(
            dataframes=dataframes,
            file_name=file_name,
            font_size=font_size,
            header_font_size=header_font_size,
            include_changelog=include_changelog
        )
        
        st.success(f"✅ Excel 檔案建立成功！(字型: 一般 {font_size}pt / 標題 {header_font_size}pt)")
        
        st.download_button(
            label="💾 下載 Excel 檔案",
            data=excel_file,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"❌ 匯出失敗: {str(e)}")
        st.exception(e)

# ========== 側邊欄：匯出設定摘要 ==========
with st.sidebar:
    st.header("📌 匯出設定")
    
    st.write("**目前字型設定:**")
    st.write(f"- 一般儲存格: **{font_size}pt** (若已選擇)")
    st.write(f"- 標題列: **{header_font_size}pt** (若已選擇)")
    
    st.divider()
    
    st.write("**Excel 格式設定:**")
    st.write("""
    - ✅ 自動調整欄寬
    - ✅ 標題列粗體 + 灰色背景
    - ✅ 所有儲存格置中對齊
    - ✅ 所有儲存格加入邊框
    - ✅ 支援中文字型顯示
    """)
    
    st.divider()
    
    st.header("✅ 更新摘要")
    st.write("""
    **FPC 疊構補充項目：**
    - Top-Coverlay PI: DK=3.2, DF=0.008
    - Top-Coverlay AD: DK=3.3, DF=0.015
    - PTH 電鍍: DK=17 (銅)
    - 介電層 PI: 厚度=50um
    - PI glue: DF=0.012, 厚度=12.5um
    - Bot-Coverlay: 同 Top-Coverlay
    """)
    
    st.divider()
    st.caption("FPC 參數管理系統 v2.0")

st.success("✅ 系統已就緒！可調整字型大小後匯出 Excel。")
