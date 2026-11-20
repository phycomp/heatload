import streamlit as st
from pathlib import PureWindowsPath
import pandas as pd
from streamlit import radio, sidebar, title, warning, code
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import os
import io
import base64
from typing import Dict, List, Tuple, Optional
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 頁面配置
st.set_page_config(
    page_title="Excel 數據可視化分析器",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class ExcelVisualizer:
    def __init__(self):
        self.uploaded_files = []
        
    def find_excel_files(self, directory: str) -> List[Path]:
        """遞歸查找所有xlsx文件"""
        directory_path = Path(directory)
        pattern = "**/*.xlsx"
        excel_files = list(directory_path.glob(pattern))
        return excel_files
    
    def read_excel_sheets(self, file_content: bytes, file_name: str) -> Dict:
        """讀取Excel文件的所有工作表"""
        try:
            sheets_dict = pd.read_excel(io.BytesIO(file_content), sheet_name=None)
            return sheets_dict
        except Exception as e:
            st.error(f"讀取文件 {file_name} 時出錯: {e}")
            return {}
    
    def analyze_sheet_structure(self, df: pd.DataFrame) -> Dict:
        """分析工作表結構"""
        structure_info = {
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': df.dtypes.to_dict(),
            'has_numeric': False,
            'numeric_columns': [],
            'categorical_columns': [],
            'missing_values': df.isnull().sum().sum(),
            'memory_usage': df.memory_usage(deep=True).sum() / 1024  # KB
        }
        
        # 檢查數值列
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            structure_info['has_numeric'] = True
            structure_info['numeric_columns'] = list(numeric_cols)
            
        # 檢查分類列
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        structure_info['categorical_columns'] = list(categorical_cols)
        
        return structure_info
    
    def create_data_overview_plotly(self, file_name: str, sheet_name: str, df: pd.DataFrame, structure: Dict):
        """使用Plotly創建數據概覽"""
        # 創建子圖
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['數據基本信息', '缺失值統計', '數據類型分布', '數據預覽'],
            specs=[[{"type": "table"}, {"type": "bar"}],
                   [{"type": "pie"}, {"type": "table"}]]
        )
        
        # 1. 數據基本信息表格
        info_data = [
            ["屬性", "值"],
            ["文件名稱", file_name],
            ["工作表", sheet_name],
            ["數據形狀", f"{structure['shape']}"],
            ["行數", f"{structure['shape'][0]}"],
            ["列數", f"{structure['shape'][1]}"],
            ["數值列數", f"{len(structure['numeric_columns'])}"],
            ["分類列數", f"{len(structure['categorical_columns'])}"],
            ["缺失值總數", f"{structure['missing_values']}"],
            ["內存使用", f"{structure['memory_usage']:.2f} KB"]
        ]
        
        fig.add_trace(
            go.Table(
                header=dict(values=info_data[0], fill_color='paleturquoise', align='left'),
                cells=dict(values=[row[1] for row in info_data[1:]], align='left')
            ),
            row=1, col=1
        )
        
        # 2. 缺失值統計
        missing_data = df.isnull().sum()
        missing_data = missing_data[missing_data > 0]
        if len(missing_data) > 0:
            fig.add_trace(
                go.Bar(x=missing_data.index, y=missing_data.values, name='缺失值'),
                row=1, col=2
            )
        else:
            fig.add_trace(
                go.Bar(x=['無缺失值'], y=[1], name='缺失值'),
                row=1, col=2
            )
        
        # 3. 數據類型分布
        dtypes_count = df.dtypes.value_counts()
        fig.add_trace(
            go.Pie(labels=[str(dtype) for dtype in dtypes_count.index], 
                  values=dtypes_count.values, name='數據類型'),
            row=2, col=1
        )
        
        # 4. 數據預覽
        preview_data = [df.columns.tolist()] + df.head(5).values.tolist()
        fig.add_trace(
            go.Table(
                header=dict(values=df.columns.tolist(), fill_color='lightgray', align='left'),
                cells=dict(values=[df[col].head(5) for col in df.columns], align='left')
            ),
            row=2, col=2
        )
        
        fig.update_layout(height=800, title_text=f"{file_name} - {sheet_name} 數據概覽", showlegend=False)
        return fig
    
    def create_numeric_analysis_plotly(self, file_name: str, sheet_name: str, df: pd.DataFrame, structure: Dict):
        """使用Plotly創建數值分析"""
        numeric_cols = structure['numeric_columns']
        if not numeric_cols:
            return None
            
        n_cols = min(2, len(numeric_cols))
        n_rows = (len(numeric_cols) + n_cols - 1) // n_cols
        
        fig = make_subplots(
            rows=n_rows, cols=n_cols,
            subplot_titles=[f'{col} 分析' for col in numeric_cols]
        )
        
        for i, col in enumerate(numeric_cols):
            row = (i // n_cols) + 1
            col_idx = (i % n_cols) + 1
            
            # 直方圖
            fig.add_trace(
                go.Histogram(x=df[col], name=col, nbinsx=20),
                row=row, col=col_idx
            )
            
            # 添加箱線圖
            fig.add_trace(
                go.Box(x=df[col], name=f'{col} 箱線圖'),
                row=row, col=col_idx
            )
        
        fig.update_layout(height=400 * n_rows, title_text=f"{file_name} - {sheet_name} 數值分析")
        return fig
    
    def create_correlation_heatmap_plotly(self, file_name: str, sheet_name: str, df: pd.DataFrame, structure: Dict):
        """使用Plotly創建相關性熱力圖"""
        numeric_cols = structure['numeric_columns']
        if len(numeric_cols) < 2:
            return None
            
        corr_matrix = df[numeric_cols].corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale='RdBu',
            zmin=-1,
            zmax=1,
            hoverongaps=False,
            text=corr_matrix.round(2).values,
            texttemplate="%{text}",
            textfont={"size": 12}
        ))
        
        fig.update_layout(
            title=f"{file_name} - {sheet_name} 相關性熱力圖",
            xaxis_title="變量",
            yaxis_title="變量",
            height=600
        )
        
        return fig
    
    def create_categorical_analysis_plotly(self, file_name: str, sheet_name: str, df: pd.DataFrame, structure: Dict):
        """使用Plotly創建分類分析"""
        categorical_cols = []
        for col in df.columns:
            if col not in structure['numeric_columns']:
                unique_count = df[col].nunique()
                if 1 < unique_count <= 15:
                    categorical_cols.append(col)
        
        if not categorical_cols:
            return None
            
        n_cols = min(2, len(categorical_cols))
        n_rows = (len(categorical_cols) + n_cols - 1) // n_cols
        
        fig = make_subplots(
            rows=n_rows, cols=n_cols,
            subplot_titles=[f'{col} 分布' for col in categorical_cols],
            specs=[[{"type": "bar"} for _ in range(n_cols)] for _ in range(n_rows)]
        )
        
        for i, col in enumerate(categorical_cols):
            row = (i // n_cols) + 1
            col_idx = (i % n_cols) + 1
            
            value_counts = df[col].value_counts().head(10)  # 只顯示前10個
            
            fig.add_trace(
                go.Bar(x=value_counts.index.astype(str), y=value_counts.values, name=col),
                row=row, col=col_idx
            )
        
        fig.update_layout(height=400 * n_rows, title_text=f"{file_name} - {sheet_name} 分類分析")
        return fig

def main():
    st.title("📊 Excel 數據可視化分析器")
    st.markdown("上傳Excel文件或選擇目錄進行遞歸分析，自動生成數據可視化圖表")
    
    # 初始化可視化器
    visualizer = ExcelVisualizer()
    
    # 側邊欄配置
    with sidebar:
      title("配置選項")
      analysis_mode = radio( "選擇分析模式:", ["上傳文件", "目錄掃描"], index=1) # 文件上傳方式選擇
    
    if analysis_mode == "上傳文件":
        # 文件上傳
        uploaded_files = st.sidebar.file_uploader(
            "選擇Excel文件",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            help="可以上傳多個Excel文件"
        )
        
        if uploaded_files:
            process_uploaded_files(visualizer, uploaded_files)
            
    else:  # 目錄掃描模式
      #with sidebar:
      sidebar.warning("目錄掃描功能在Streamlit Cloud環境中可能受限")
      目錄 = sidebar.radio("輸入要掃描的目錄路徑:", ['SMPlug2PlugCable80mm'], horizontal=True, index=0)   #help="輸入相對路徑或絕對路徑"
      #if st.sidebar.button("開始掃描"):
      if 目錄 and os.path.exists(目錄):
          with st.spinner("正在掃描目錄..."):
              excel_files = visualizer.find_excel_files(目錄)
              
          if excel_files:
              st.success(f"找到 {len(excel_files)} 個Excel文件")
              xlsx=sidebar.radio('單一文件', excel_files, horizontal=True, index=0)
                #with st.expander("查看找到的文件"):
                #    for file_path in excel_files:
                #        st.write(f"- {file_path}")
              
              # 處理文件
              if xlsx:
                process_directory_files(visualizer, PureWindowsPath(xlsx))#.as_posix())
          else:
              st.warning("在指定目錄中未找到任何Excel文件")
      else:
          st.error("目錄不存在，請檢查路徑")

def process_uploaded_files(visualizer: ExcelVisualizer, uploaded_files: List):
    """處理上傳的文件"""
    st.header("📁 文件分析結果")
    
    for uploaded_file in uploaded_files:
        with st.spinner(f"正在分析 {uploaded_file.name}..."):
            # 讀取文件
            file_content = uploaded_file.getvalue()
            sheets_dict = visualizer.read_excel_sheets(file_content, uploaded_file.name)
            
            if sheets_dict:
                display_file_analysis(visualizer, uploaded_file.name, sheets_dict, file_content)
            else:
                st.error(f"無法讀取文件: {uploaded_file.name}")

def process_directory_files(visualizer: ExcelVisualizer, excel_files: List[Path]):
    """處理目錄中的文件"""
    #st.header("📁 目錄分析結果")
    #
    #progress_bar = st.progress(0)
    #total_files = len(excel_files)
    
    #for i, file_path in enumerate([excel_files]):
    #    #progress = (i + 1) / total_files
    #    progress_bar.progress(progress)
    #    
    #    with st.spinner(f"正在分析 {file_path.name} ({i+1}/{total_files})..."):
    #try:
        # 讀取文件
    #code(['file_path', file_path])
    with open(excel_files, 'rb') as f:
        file_content = f.read()
    
    sheets_dict = visualizer.read_excel_sheets(file_content, excel_files.name)
    
    if sheets_dict:
        display_file_analysis(visualizer, excel_files.name, sheets_dict, file_content)
    else:
        st.error(f"無法讀取文件: {file_path.name}")
            
    #except Exception as e:
    #    st.error(f"處理文件 {file_path.name} 時出錯: {e}")

def display_file_analysis(visualizer: ExcelVisualizer, file_name: str, sheets_dict: Dict, file_content: bytes):
    """顯示文件分析結果"""
    with st.container():
        st.markdown(f"### 📄 {file_name}")
        
        file_size = len(file_content) / 1024  # KB 文件信息
        st.write(f"**文件大小:** {file_size:.2f} KB | **工作表數量:** {len(sheets_dict)}")
        
        sheet_names = list(sheets_dict.keys()) # 工作表選擇
        selected_sheet = radio(f"選擇要分析的工作表 ({file_name}):", sheet_names, key=f"sheet_select_{file_name}", horizontal=True)
        
        if selected_sheet:
            df = sheets_dict[selected_sheet]
            structure = visualizer.analyze_sheet_structure(df)
            
            # 顯示數據表格
            with st.expander("📋 查看數據"):
                st.dataframe(df, use_container_width=True)
                
                # 顯示數據統計
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("行數", df.shape[0])
                with col2:
                    st.metric("列數", df.shape[1])
                with col3:
                    st.metric("數值列", len(structure['numeric_columns']))
                with col4:
                    st.metric("缺失值", structure['missing_values'])
            
            # 創建標簽頁用于不同的可視化
            tab1, tab2, tab3, tab4 = st.tabs(["📊 數據概覽", "🔢 數值分析", "📈 相關性分析", "📋 分類分析"])
            
            with tab1:
                st.plotly_chart(
                    visualizer.create_data_overview_plotly(file_name, selected_sheet, df, structure),
                    use_container_width=True
                )
            
            with tab2:
                if structure['has_numeric']:
                    st.plotly_chart(
                        visualizer.create_numeric_analysis_plotly(file_name, selected_sheet, df, structure),
                        use_container_width=True
                    )
                else:
                    st.info("該工作表沒有數值列可供分析")
            
            with tab3:
                if len(structure['numeric_columns']) >= 2:
                    st.plotly_chart(
                        visualizer.create_correlation_heatmap_plotly(file_name, selected_sheet, df, structure),
                        use_container_width=True
                    )
                else:
                    st.info("需要至少2個數值列才能進行相關性分析")
            
            with tab4:
                cat_fig = visualizer.create_categorical_analysis_plotly(file_name, selected_sheet, df, structure)
                if cat_fig:
                    st.plotly_chart(cat_fig, use_container_width=True)
                else:
                    st.info("沒有找到合適的分類列進行分析")
            
            # 數據下載
            with st.expander("💾 下載處理後的數據"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="下載CSV格式",
                    data=csv,
                    file_name=f"{Path(file_name).stem}_{selected_sheet}.csv",
                    mime="text/csv",
                    key=f"download_csv_{file_name}_{selected_sheet}"
                )
        
        st.markdown("---")

# 添加使用說明
with st.sidebar.expander("📖 使用說明"):
    st.markdown("""
    ### 功能說明:
    1. **上傳文件**: 直接上傳Excel文件進行分析
    2. **目錄掃描**: 遞歸掃描目錄中的所有Excel文件
    
    ### 支持的分析:
    - 📊 數據概覽和基本信息
    - 🔢 數值列分布分析
    - 📈 相關性熱力圖
    - 📋 分類數據分布
    
    ### 支持的格式:
    - .xlsx, .xls 文件
    - 多工作表支持
    - 自動識別數據類型
    """)

if __name__ == "__main__":
    main()
