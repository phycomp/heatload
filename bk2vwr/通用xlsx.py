import streamlit as st
from streamlit import sidebar, radio
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
from glob import glob
from io import BytesIO

# 設置頁面
st.set_page_config(
    page_title="通用Excel數據分析儀表板",
    page_icon="📊",
    layout="wide"
)

st.title("📊 通用Excel數據分析儀表板")
st.markdown("---")

def clean_column_names(df):
    """清理列名中的空白字符和特殊字符"""
    df = df.copy()
    df.columns = [str(col).strip().replace('\n', ' ').replace('\r', ' ') for col in df.columns]
    return df

def detect_numeric_columns(df):
    """自動檢測數值型列"""
    numeric_columns = []
    for col in df.columns:
        # 嘗試將列轉換爲數值型
        try:
            # 先清理數據中的空白字符
            clean_series = df[col].astype(str).str.strip().replace('', np.nan)
            numeric_count = pd.to_numeric(clean_series, errors='coerce').notna().sum()
            
            # 如果超過50%的數據可以轉換爲數值，則認爲這是數值列
            if numeric_count / len(df) > 0.5:
                numeric_columns.append(col)
        except:
            continue
    return numeric_columns

def get_excel_files(directory="."):
    """獲取目錄下所有的Excel文件"""
    excel_files = glob(os.path.join(directory, "*.xlsx")) + glob(os.path.join(directory, "*.xls"))
    return [os.path.basename(f) for f in excel_files]

def analyze_sheet_structure(df, sheet_name):
    """分析sheet的數據結構"""
    analysis = {
        'sheet_name': sheet_name,
        'shape': df.shape,
        'numeric_columns': [],
        'text_columns': [],
        'has_frequency_like_data': False,
        'potential_x_column': None,
        'potential_y_columns': []
    }
    
    # 清理數據
    df_clean = clean_column_names(df)
    
    # 檢測數值列
    numeric_cols = detect_numeric_columns(df_clean)
    analysis['numeric_columns'] = numeric_cols
    
    # 檢測文本列
    analysis['text_columns'] = [col for col in df_clean.columns if col not in numeric_cols]
    
    # 尋找可能的X軸列（頻率、時間等）
    frequency_keywords = ['frequency', 'freq', 'hz', 'ghz', 'mhz', '時間', '時間點', '點', 'index', 'x']
    time_keywords = ['time', 'timestamp', '時間', '時刻']
    
    for col in df_clean.columns:
        col_lower = str(col).lower()
        
        # 檢查是否是頻率類數據
        if any(keyword in col_lower for keyword in frequency_keywords):
            analysis['has_frequency_like_data'] = True
            analysis['potential_x_column'] = col
            break
        # 檢查是否是時間類數據
        elif any(keyword in col_lower for keyword in time_keywords):
            analysis['potential_x_column'] = col
            break
    
    # 如果沒有找到明確的X軸列，使用第一列數值數據
    if not analysis['potential_x_column'] and numeric_cols:
        analysis['potential_x_column'] = numeric_cols[0]
    
    # 其他數值列作爲Y軸數據
    if analysis['potential_x_column'] and analysis['potential_x_column'] in numeric_cols:
        analysis['potential_y_columns'] = [col for col in numeric_cols if col != analysis['potential_x_column']]
    else:
        analysis['potential_y_columns'] = numeric_cols
    
    return analysis, df_clean

def create_visualizations(df_clean, analysis, sheet_name):
    """根據數據分析結果創建可視化"""
    visualizations = []
    
    if not analysis['potential_y_columns']:
        return visualizations
    
    # 1. 多曲線圖表
    if analysis['potential_x_column'] and len(analysis['potential_y_columns']) > 0:
        fig_lines = go.Figure()
        
        x_data = df_clean[analysis['potential_x_column']]
        
        for i, y_col in enumerate(analysis['potential_y_columns'][:8]):  # 限制顯示8條曲線
            y_data = pd.to_numeric(df_clean[y_col].astype(str).str.strip().replace('', np.nan), errors='coerce')
            
            fig_lines.add_trace(go.Scatter(
                x=x_data,
                y=y_data,
                name=y_col,
                mode='lines',
                opacity=0.8
            ))
        
        fig_lines.update_layout(
            title=f"{sheet_name} - 多曲線圖",
            xaxis_title=analysis['potential_x_column'],
            yaxis_title="數值",
            height=400,
            showlegend=True
        )
        visualizations.append(("多曲線圖", fig_lines))
    
    # 2. 統計摘要圖表
    if len(analysis['numeric_columns']) > 0:
        # 數值分布直方圖
        fig_hist = make_subplots(rows=1, cols=min(3, len(analysis['numeric_columns'])), subplot_titles=analysis['numeric_columns'][:3])
        
        for i, col in enumerate(analysis['numeric_columns'][:3]):
            data = pd.to_numeric(df_clean[col].astype(str).str.strip().replace('', np.nan), errors='coerce')
            fig_hist.add_trace(go.Histogram(x=data, name=col), row=1, col=i+1)
        
        fig_hist.update_layout(height=400, title_text=f"{sheet_name} - 數值分布")
        visualizations.append(("數值分布", fig_hist))
        
        # 箱線圖
        if len(analysis['numeric_columns']) > 1:
            fig_box = go.Figure()
            for col in analysis['numeric_columns'][:5]:  # 限制顯示5個箱線圖
                data = pd.to_numeric(df_clean[col].astype(str).str.strip().replace('', np.nan), errors='coerce')
                fig_box.add_trace(go.Box(y=data, name=col))
            
            fig_box.update_layout(height=400, title=f"{sheet_name} - 箱線圖")
            visualizations.append(("箱線圖", fig_box))
    
    # 3. 相關性熱力圖
    if len(analysis['numeric_columns']) > 2:
        try:
            # 創建數值數據的子集
            numeric_data = df_clean[analysis['numeric_columns']].apply(lambda x: pd.to_numeric(x.astype(str).str.strip().replace('', np.nan), errors='coerce'))
            corr_matrix = numeric_data.corr()
            
            fig_corr = px.imshow(corr_matrix, title=f"{sheet_name} - 相關性熱力圖", color_continuous_scale='RdBu_r', aspect="auto")
            visualizations.append(("相關性分析", fig_corr))
        except:
            pass
    
    return visualizations

# 主應用邏輯
st.sidebar.title("📁 文件選擇")

# 文件上傳或目錄選擇
analysis_mode = st.sidebar.radio("選擇分析模式:", ["上傳單個文件", "分析目錄下所有文件"])

if analysis_mode == "上傳單個文件":
    uploaded_file = st.sidebar.file_uploader("選擇Excel文件", type=["xlsx", "xls"])
    files_to_process = [uploaded_file] if uploaded_file else []
else:
    with sidebar:
      目錄 = radio("目錄路徑(留空使用當前目錄):", ["TDRReportRawData", 'TDR_Fail'], horizontal=True, key=0)  #st.sidebar.text_input
      #if st.sidebar.button("掃描Excel文件"):
      XLSX = get_excel_files(目錄)
      #st.code(['excel_files', excel_files])
      selected_files = radio("選擇要分析的文件:", XLSX, horizontal=True, key=1)  #st.sidebar.multiselect
      #files_to_process = excel_files    #[os.path.join(directory_path, f) for f in selected_files]

if XLSX:
    # 創建標簽頁用于不同文件
    #XLSX=files_to_process#[os.path.basename(f.name) if hasattr(f, 'name') else os.path.basename(f) for f in files_to_process]
    #st.code(['XLSX', XLSX])
    分頁 = st.tabs(XLSX)
    
    for file_idx, file_path in enumerate(XLSX):
        fullPath=f'{目錄}/{file_path}'
        with 分頁[file_idx]:
            try:
                # 讀取Excel文件
                if hasattr(file_path, 'getvalue'):  # 上傳的文件
                    excel_file = pd.ExcelFile(fullPath)
                    file_name = file_path.name
                else:  # 本地文件
                    excel_file = pd.ExcelFile(fullPath)
                    file_name = os.path.basename(file_path)
                
                sheet_names = excel_file.sheet_names
                
                st.header(f"文件: {file_name}")
                st.write(f"包含 {len(sheet_names)} 個工作表: {', '.join(sheet_names)}")
                
                # 爲每個sheet創建子標簽頁
                sheet_tabs = st.tabs([f"📊 {sheet}" for sheet in sheet_names])
                
                for sheet_idx, sheet_name in enumerate(sheet_names):
                    with sheet_tabs[sheet_idx]:
                        try:
                            # 讀取sheet數據
                            df = pd.read_excel(excel_file, sheet_name=sheet_name)
                            
                            if df.empty:
                                st.warning(f"工作表 '{sheet_name}' 爲空")
                                continue
                            
                            # 分析數據結構
                            analysis, df_clean = analyze_sheet_structure(df, sheet_name)
                            
                            # 顯示基本信息
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("行數", analysis['shape'][0])
                            with col2:
                                st.metric("列數", analysis['shape'][1])
                            with col3:
                                st.metric("數值列", len(analysis['numeric_columns']))
                            with col4:
                                st.metric("文本列", len(analysis['text_columns']))
                            
                            # 顯示數據結構信息
                            with st.expander("數據結構詳情"):
                                st.write("**數值列:**", analysis['numeric_columns'])
                                st.write("**文本列:**", analysis['text_columns'])
                                if analysis['potential_x_column']:
                                    st.write("**建議X軸:**", analysis['potential_x_column'])
                                if analysis['potential_y_columns']:
                                    st.write("**建議Y軸:**", analysis['potential_y_columns'])
                            
                            # 創建可視化
                            visualizations = create_visualizations(df_clean, analysis, sheet_name)
                            
                            if visualizations:
                                # 爲每個可視化創建子標簽頁
                                viz_tabs = st.tabs([viz[0] for viz in visualizations])
                                
                                for viz_idx, (viz_name, viz_fig) in enumerate(visualizations):
                                    with viz_tabs[viz_idx]:
                                        st.plotly_chart(viz_fig, use_container_width=True, width='stretch')
                            else:
                                st.info("未找到足夠的數據創建可視化圖表")
                            
                            # 顯示數據預覽
                            with st.expander("數據預覽"):
                                st.dataframe(df_clean.head(20), use_container_width=True, width='stretch')
                                
                                # 數據統計
                                st.subheader("數據統計")
                                if analysis['numeric_columns']:
                                    numeric_stats = df_clean[analysis['numeric_columns']].apply(
                                        lambda x: pd.to_numeric(x.astype(str).str.strip().replace('', np.nan), errors='coerce')
                                    ).describe()
                                    st.dataframe(numeric_stats, use_container_width=True, width='stretch')
                            
                            # 數據下載
                            st.subheader("數據導出")
                            csv_data = df_clean.to_csv(index=False).encode('utf-8')
                            
                            st.download_button(
                                label=f"📥 下載 {sheet_name} 數據爲CSV",
                                data=csv_data,
                                file_name=f"{file_name}_{sheet_name}.csv",
                                mime="text/csv"
                            )
                            
                        except Exception as e:
                            st.error(f"處理工作表 '{sheet_name}' 時出錯: {str(e)}")
                
            except Exception as e:
                st.error(f"讀取文件時出錯: {str(e)}")

else:
    # 顯示使用說明
    st.info("👆 請選擇要分析的Excel文件")
    
    with st.expander("📖 使用說明"):
        st.markdown("""
        ### 🎯 功能特性：
        
        **通用性設計**:
        - 支持任意名稱的Excel文件和工作表
        - 自動檢測數值型和文本型數據
        - 智能識別頻率、時間等X軸數據
        
        **數據處理能力**:
        - 自動清理列名和數據的空白字符
        - 處理包含空值的數值數據
        - 自動識別可繪制的數據列
        
        **可視化功能**:
        - 多曲線圖表
        - 數據分布直方圖
        - 箱線圖分析
        - 相關性熱力圖
        
        **批量處理**:
        - 支持分析目錄下多個Excel文件
        - 每個文件和工作表獨立分析
        - 數據導出功能
        
        ### 📊 支持的數據類型：
        - 頻率響應數據
        - 時間序列數據
        - 測試測量數據
        - 任意數值型數據表格
        
        ### 🔧 技術特點：
        - 自動數據類型檢測
        - 容錯處理機制
        - 交互式圖表展示
        - 響應式布局設計
        """)

    # 顯示示例數據格式
    with st.expander("📋 推薦的數據格式"):
        st.markdown("""
        ### 推薦的數據格式：
        
        **頻率響應數據格式**:
        ```
        Frequency (GHz) | Channel1_IL | Channel1_RL | Channel2_IL | Channel2_RL
        ---------------|-------------|-------------|-------------|-------------
        0.01           | -0.1        | -35.2       | -0.2        | -34.8
        0.02           | -0.15       | -34.5       | -0.25       | -34.1
        ```
        
        **時間序列數據格式**:
        ```
        Time | Value1 | Value2 | Value3
        -----|--------|--------|--------
        0    | 1.2    | 2.3    | 3.4
        1    | 1.3    | 2.4    | 3.5
        ```
        
        **通用表格格式**:
        ```
        Parameter | Test1 | Test2 | Test3
        ----------|-------|-------|-------
        Temp      | 25.1  | 25.3  | 25.0
        Voltage   | 3.3   | 3.29  | 3.31
        Current   | 1.2   | 1.19  | 1.21
        ```
        """)
