import streamlit as st
from streamlit import radio, sidebar, code
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import glob
from pathlib import Path

def load_and_merge_csv_files(directory_path): # 查找所有CSV文件
    目錄=Path(directory_path)
    csv_files = 目錄.glob("*.csv")
    
    if not csv_files:
        st.error("在指定目錄下未找到CSV文件")
        return None
    
    st.info(f"找到 {len(list(csv_files))} 個CSV文件")
    
    all_data = []
    
    for file_path in list(csv_files):
        #try:
            # 讀取CSV文件
        code(['file_path', file_path])
        df = pd.read_csv(file_path)
        
        # 獲取文件名（不含擴展名）
        file_name = Path(file_path).stem
        
        # 添加文件名作爲標識列
        df['source_file'] = file_name
        
        all_data.append(df)
        
        st.success(f"成功加載: {file_name} (數據行數: {len(df)})")
            
        #except Exception as e:
        #    st.error(f"讀取文件 {file_path} 時出錯: {str(e)}")
    
    if not all_data:
        st.error("未能成功加載任何CSV文件")
        return None
    
    # 合并所有數據
    merged_data = pd.concat(all_data, ignore_index=True)
    st.success(f"合并後總數據行數: {len(merged_data)}")
    
    return merged_data

def get_common_columns(df):
    """
    獲取數據框中數值類型的列名
    """
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
    return numeric_columns

def create_overlapped_legend_name(full_name, max_length=30):
    """
    如果文件名過長，創建重叠顯示的圖例名稱
    """
    if len(full_name) <= max_length:
        return full_name
    
    # 保留前一部分和後一部分，中間用...連接
    prefix_length = max_length // 3
    suffix_length = max_length - prefix_length - 3  # 3個點占位
    
    prefix = full_name[:prefix_length]
    suffix = full_name[-suffix_length:] if suffix_length > 0 else ""
    
    return f"{prefix}...{suffix}"

def plot_curves_with_overlapped_legend(df, x_column, y_columns, file_column='source_file'):
    """
    使用Plotly繪制曲線圖，處理過長的圖例名稱
    """
    fig = go.Figure()
    
    # 獲取所有文件
    files = df[file_column].unique()
    
    # 生成顏色序列
    colors = px.colors.qualitative.Set1 + px.colors.qualitative.Set2 + px.colors.qualitative.Set3
    
    for i, file_name in enumerate(files):
        file_data = df[df[file_column] == file_name]
        
        # 處理圖例名稱
        legend_name = create_overlapped_legend_name(file_name)
        
        color = colors[i % len(colors)]
        
        for y_column in y_columns:
            # 爲每個y列創建一條曲線
            fig.add_trace(go.Scatter(
                x=file_data[x_column],
                y=file_data[y_column],
                mode='lines',
                name=f"{legend_name} - {y_column}",
                line=dict(color=color, width=2),
                hovertemplate=f"文件: {file_name}<br>{x_column}: %{{x}}<br>{y_column}: %{{y}}<extra></extra>"
            ))
    
    # 更新布局
    fig.update_layout(
        title="CSV文件數據曲線圖",
        xaxis_title=x_column,
        yaxis_title="數值",
        legend=dict(
            title="文件 - 數據列",
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='black',
            borderwidth=1
        ),
        hovermode='closest',
        width=1000,
        height=600
    )
    
    return fig

def plot_simple_curves(df, x_column, y_columns, file_column='source_file'):
    """
    簡化版曲線圖 - 每個文件一種顏色，不區分數據列
    """
    fig = go.Figure()
    
    files = df[file_column].unique()
    colors = px.colors.qualitative.Set1 + px.colors.qualitative.Set2
    
    for i, file_name in enumerate(files):
        file_data = df[df[file_column] == file_name]
        
        legend_name = create_overlapped_legend_name(file_name)
        color = colors[i % len(colors)]
        
        # 只繪制第一個y列（簡化顯示）
        if y_columns:
            y_column = y_columns[0]
            fig.add_trace(go.Scatter(
                x=file_data[x_column],
                y=file_data[y_column],
                mode='lines',
                name=legend_name,
                line=dict(color=color, width=2),
                hovertemplate=f"文件: {file_name}<br>{x_column}: %{{x}}<br>{y_column}: %{{y}}<extra></extra>"
            ))
    
    fig.update_layout(
        title="CSV文件數據曲線圖 (簡化版)",
        xaxis_title=x_column,
        yaxis_title=y_columns[0] if y_columns else "數值",
        legend=dict(
            title="文件名",
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        width=1000,
        height=600
    )
    
    return fig

def main():
    st.set_page_config(page_title="CSV數據可視化", layout="wide")
    
    st.title("📊 CSV文件數據合并與可視化")
    st.markdown("將目錄下的所有CSV文件合并，并用Plotly繪制交互式曲線圖")
    
    # 側邊欄配置
    
    # 目錄輸入
    with sidebar:
      directory_path = radio("CSV文件目錄路徑:", ["./TDRReportRawData/PASS__20251114_153309", "./TDRReportRawData/FAIL__20251113_163346", "./TDRReportRawData/PASS__20251113_163441"], horizontal=True, index=0)
    
    # 加載數據按鈕
    #if st.sidebar.button("加載并合并CSV文件"):
    if directory_path:
        with st.spinner("正在加載CSV文件..."):
            df = load_and_merge_csv_files(directory_path)
            if df is not None:
                st.session_state['merged_data'] = df
                st.session_state['data_loaded'] = True
    else:
        st.error("指定的目錄不存在！")
    
    # 檢查是否有加載的數據
    if 'data_loaded' not in st.session_state or not st.session_state['data_loaded']:
        st.info("請在側邊欄輸入CSV文件目錄路徑，然後點擊'加載并合并CSV文件'按鈕")
        return
    
    df = st.session_state['merged_data']
    
    # 顯示數據基本信息
    st.subheader("數據概覽")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("總數據行數", len(df))
    with col2:
        st.metric("文件數量", df['source_file'].nunique())
    with col3:
        st.metric("數據列數", len(df.columns) - 1)  # 減去source_file列
    
    # 顯示前幾行數據
    with st.expander("查看數據前幾行"):
        st.dataframe(df.head())
    
    # 獲取數值列
    numeric_columns = get_common_columns(df)
    
    if not numeric_columns:
        st.error("未找到數值類型的列用于繪圖")
        return
    
    # 繪圖配置
    st.subheader("繪圖配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # X軸選擇
        x_column = st.selectbox(
            "選擇X軸數據列:",
            options=numeric_columns,
            index=0
        )
    
    with col2:
        # Y軸選擇（多選）
        default_y_columns = [col for col in numeric_columns if col != x_column][:2]
        y_columns = st.multiselect(
            "選擇Y軸數據列:",
            options=[col for col in numeric_columns if col != x_column],
            default=default_y_columns
        )
    
    # 繪圖選項
    col3, col4 = st.columns(2)
    
    with col3:
        plot_type = st.radio(
            "圖表類型:",
            ["詳細圖例", "簡化圖例"]
        )
    
    with col4:
        show_data_table = st.checkbox("顯示數據統計表")
    
    # 繪制圖表
    if not y_columns:
        st.warning("請至少選擇一個Y軸數據列")
        return
    
    st.subheader("交互式曲線圖")
    
    if plot_type == "詳細圖例":
        fig = plot_curves_with_overlapped_legend(df, x_column, y_columns)
    else:
        fig = plot_simple_curves(df, x_column, y_columns)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 顯示數據統計表
    if show_data_table:
        st.subheader("數據統計")
        
        # 按文件分組統計
        stats = df.groupby('source_file')[numeric_columns].describe()
        st.dataframe(stats)
    
    # 下載合并後的數據
    st.subheader("數據導出")
    
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="下載合并後的CSV文件",
        data=csv_data,
        file_name="merged_data.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()
