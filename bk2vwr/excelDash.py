import streamlit as st
from streamlit import radio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import glob
from excel_visualizer import ExcelVisualizer
import base64
from datetime import datetime

# 設定頁面
st.set_page_config(
    page_title="Excel 數據視覺化儀表板",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class ExcelDashboard:
    def __init__(self):
        self.visualizer = ExcelVisualizer()
        self.init_session_state()
    
    def init_session_state(self):
        """初始化 session state"""
        if 'excel_data' not in st.session_state:
            st.session_state.excel_data = None
        if 'current_sheet' not in st.session_state:
            st.session_state.current_sheet = None
        if 'visualizations' not in st.session_state:
            st.session_state.visualizations = {}
    
    def sidebar_controls(self):
        """側邊欄控制"""
        st.sidebar.title("📁 檔案控制")
        
        # 檔案上傳
        uploaded_file = st.sidebar.file_uploader(
            "上傳 Excel 檔案",
            type=['xlsx', 'xls'],
            help="支援 .xlsx 和 .xls 格式"
        )
        
        # 或選擇目錄中的檔案
        data_dir = st.sidebar.text_input("資料目錄路徑", value="TDRReportRawData")
        
        excel_files = []
        if os.path.exists(data_dir):
            excel_files = glob.glob(os.path.join(data_dir, "*.xlsx")) + glob.glob(os.path.join(data_dir, "*.xls"))
        
        file_options = ["-- 選擇檔案 --"] + [os.path.basename(f) for f in excel_files]
        
        selected_file = st.sidebar.selectbox(
            "或選擇現有檔案",
            file_options
        )
        
        # 確定要載入的檔案
        file_to_load = None
        if uploaded_file is not None:
            file_to_load = uploaded_file
        elif selected_file != "-- 選擇檔案 --":
            file_path = os.path.join(data_dir, selected_file)
            if os.path.exists(file_path):
                file_to_load = file_path
        
        # 載入按鈕
        if file_to_load and st.sidebar.button("載入檔案"):
            self.load_excel_file(file_to_load)
        
        # 圖表設定
        st.sidebar.markdown("---")
        st.sidebar.title("🎨 圖表設定")
        
        self.chart_theme = st.sidebar.selectbox(
            "圖表主題",
            ["plotly", "plotly_white", "plotly_dark", "ggplot2", "seaborn", "simple_white"]
        )
        
        self.auto_detect = st.sidebar.checkbox("自動檢測圖表類型", value=True)
        
        return file_to_load
    
    def load_excel_file(self, file_source):
        """載入 Excel 檔案"""
        try:
            if hasattr(file_source, 'read'):
                # 上傳的檔案
                excel_data = self.visualizer.read_excel_file(file_source)
            else:
                # 檔案路徑
                excel_data = self.visualizer.read_excel_file(file_source)
            
            st.session_state.excel_data = excel_data
            st.session_state.current_sheet = excel_data['sheet_names'][0] if excel_data['sheet_names'] else None
            st.session_state.visualizations = {}
            
            st.success(f"成功載入檔案: {excel_data['filename']}")
            
        except Exception as e:
            st.error(f"載入檔案時發生錯誤: {e}")
    
    def display_file_overview(self):
        """顯示檔案概覽"""
        if not st.session_state.excel_data:
            return
        
        excel_data = st.session_state.excel_data
        
        st.header("📋 檔案概覽")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("檔案名稱", excel_data['filename'])
        with col2:
            st.metric("工作表數量", len(excel_data['sheets']))
        with col3:
            total_rows = sum(sheet['shape'][0] for sheet in excel_data['sheets'].values())
            st.metric("總數據行數", total_rows)
        
        # 工作表選擇
        sheet_names = excel_data['sheet_names']
        selected_sheet = radio( "選擇工作表", sheet_names, key="sheet_selector", horizontal=True)
        
        st.session_state.current_sheet = selected_sheet
        
        # 顯示工作表資訊
        self.display_sheet_info(selected_sheet)
    
    def display_sheet_info(self, sheet_name: str):
        """顯示工作表資訊"""
        sheet_data = st.session_state.excel_data['sheets'][sheet_name]
        df = sheet_data['dataframe']
        
        st.subheader(f"📊 工作表: {sheet_name}")
        
        # 基本資訊
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("行數", sheet_data['shape'][0])
        with col2:
            st.metric("欄位數", sheet_data['shape'][1])
        with col3:
            st.metric("數值欄位", len(sheet_data['numeric_columns']))
        with col4:
            st.metric("分類欄位", len(sheet_data['categorical_columns']))
        
        # 數據預覽
        st.subheader("數據預覽")
        st.dataframe(df.head(100), use_container_width=True)
        
        # 數據資訊
        with st.expander("數據詳細資訊"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**欄位資訊:**")
                column_info = pd.DataFrame({
                    '欄位名稱': df.columns,
                    '數據類型': df.dtypes.values,
                    '非空值數量': df.count().values,
                    '空值數量': df.isnull().sum().values
                })
                st.dataframe(column_info, use_container_width=True)
            
            with col2:
                st.write("**基本統計:**")
                if sheet_data['numeric_columns']:
                    st.dataframe(df[sheet_data['numeric_columns']].describe(), use_container_width=True)
                else:
                    st.info("沒有數值數據可顯示統計資訊")
    
    def display_visualizations(self):
        """顯示視覺化圖表"""
        if not st.session_state.current_sheet:
            return
        
        sheet_name = st.session_state.current_sheet
        sheet_data = st.session_state.excel_data['sheets'][sheet_name]
        df = sheet_data['dataframe']
        
        st.header("📈 數據視覺化")
        
        # 生成或獲取視覺化
        if sheet_name not in st.session_state.visualizations:
            with st.spinner("生成視覺化圖表中..."):
                st.session_state.visualizations[sheet_name] = (
                    self.visualizer.generate_comprehensive_visualizations(df, sheet_name)
                )
        
        visualizations = st.session_state.visualizations[sheet_name]
        
        # 自定義圖表選項
        st.subheader("自定義圖表")
        self.custom_chart_interface(df, sheet_name)
        
        # 自動生成的圖表
        st.subheader("自動生成圖表")
        
        if 'plotly_charts' in visualizations and visualizations['plotly_charts']:
            # 顯示圖表網格
            charts = visualizations['plotly_charts']
            num_charts = len(charts)
            
            # 根據圖表數量決定列數
            if num_charts <= 2:
                cols = st.columns(2)
            elif num_charts <= 4:
                cols = st.columns(2)
            else:
                cols = st.columns(3)
            
            for i, chart_data in enumerate(charts):
                col_idx = i % len(cols)
                with cols[col_idx]:
                    config = chart_data['config']
                    fig = chart_data['figure']
                    
                    # 更新主題
                    fig.update_layout(template=self.chart_theme)
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 圖表資訊
                    with st.expander("圖表資訊", expanded=False):
                        st.write(f"**類型:** {config['type']}")
                        st.write(f"**標題:** {config.get('title', 'N/A')}")
                        if 'x_column' in config:
                            st.write(f"**X軸:** {config['x_column']}")
                        if 'y_column' in config:
                            st.write(f"**Y軸:** {config['y_column']}")
        else:
            st.info("沒有足夠的數據生成自動圖表")
        
        # 相關性熱力圖
        if 'correlation_heatmap' in visualizations:
            st.subheader("相關性分析")
            fig_corr = visualizations['correlation_heatmap']
            fig_corr.update_layout(template=self.chart_theme)
            st.plotly_chart(fig_corr, use_container_width=True)
        
        # 統計資訊
        if 'statistics' in visualizations:
            st.subheader("統計摘要")
            st.dataframe(visualizations['statistics'], use_container_width=True)
    
    def custom_chart_interface(self, df: pd.DataFrame, sheet_name: str):
        """自定義圖表介面"""
        col1, col2 = st.columns(2)
        
        with col1:
            chart_type = radio("圖表類型", self.visualizer.supported_chart_types, key="custom_chart_type", horizontal=True)
        
        with col2:
            # 根據圖表類型顯示不同的選項
            if chart_type in ['line', 'bar', 'scatter']:
                x_column = st.selectbox("X軸", df.columns, key="custom_x")
                y_column = st.selectbox("Y軸", df.columns, key="custom_y")
                
                if st.button("生成自定義圖表"):
                    chart_config = {
                        'type': chart_type,
                        'x_column': x_column,
                        'y_column': y_column,
                        'title': f"{sheet_name} - {x_column} vs {y_column}"
                    }
                    
                    fig = self.visualizer.create_plotly_chart(df, chart_config)
                    fig.update_layout(template=self.chart_theme)
                    st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type in ['histogram', 'box']:
                column = st.selectbox("選擇欄位", df.columns, key="custom_single")
                
                if st.button("生成自定義圖表"):
                    chart_config = {
                        'type': chart_type,
                        'x_column' if chart_type == 'histogram' else 'y_column': column,
                        'title': f"{sheet_name} - {column} {chart_type}"
                    }
                    
                    fig = self.visualizer.create_plotly_chart(df, chart_config)
                    fig.update_layout(template=self.chart_theme)
                    st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == 'pie':
                column = st.selectbox("選擇欄位", df.select_dtypes(include=['object']).columns, 
                                    key="custom_pie")
                
                if st.button("生成自定義圖表"):
                    chart_config = {
                        'type': 'pie',
                        'names_column': column,
                        'title': f"{sheet_name} - {column} 分布"
                    }
                    
                    fig = self.visualizer.create_plotly_chart(df, chart_config)
                    fig.update_layout(template=self.chart_theme)
                    st.plotly_chart(fig, use_container_width=True)
    
    def export_options(self):
        """匯出選項"""
        st.sidebar.markdown("---")
        st.sidebar.title("💾 匯出選項")
        
        if st.session_state.excel_data and st.session_state.current_sheet:
            if st.sidebar.button("匯出當前圖表"):
                self.export_current_charts()
    
    def export_current_charts(self):
        """匯出當前圖表"""
        sheet_name = st.session_state.current_sheet
        if sheet_name in st.session_state.visualizations:
            visualizations = st.session_state.visualizations[sheet_name]
            
            # 建立匯出資料夾
            export_dir = f"exports/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(export_dir, exist_ok=True)
            
            # 匯出圖表
            if 'plotly_charts' in visualizations:
                for i, chart_data in enumerate(visualizations['plotly_charts']):
                    html_content = self.visualizer.export_chart_as_html(
                        chart_data['figure'],
                        f"{export_dir}/chart_{i+1}.html"
                    )
            
            st.sidebar.success(f"圖表已匯出至 {export_dir}")
    
    def run(self):
        """執行儀表板"""
        st.title("📊 Excel 數據視覺化儀表板")
        st.markdown("上傳 Excel 檔案並自動生成數據視覺化圖表")
        
        # 側邊欄控制
        file_to_load = self.sidebar_controls()
        
        # 主內容區域
        if st.session_state.excel_data:
            self.display_file_overview()
            self.display_visualizations()
        else:
            # 顯示歡迎訊息和示例
            self.display_welcome_message()
        
        # 匯出選項
        self.export_options()
    
    def display_welcome_message(self):
        """顯示歡迎訊息"""
        st.markdown("""
        ## 🚀 歡迎使用 Excel 數據視覺化儀表板
        
        這個工具可以幫助您：
        
        - 📁 **上傳 Excel 檔案**並自動分析所有工作表
        - 📊 **自動檢測數據模式**並生成合適的圖表
        - 🎨 **多種圖表類型**：折線圖、柱狀圖、散點圖、直方圖等
        - 🔍 **互動式探索**：點擊、縮放、篩選數據
        - 💾 **匯出圖表**為 HTML 格式
        
        ### 使用方法：
        1. 在左側邊欄上傳 Excel 檔案或選擇現有檔案
        2. 點擊「載入檔案」按鈕
        3. 選擇要分析的工作表
        4. 探索自動生成的視覺化圖表
        5. 使用自定義選項創建特定圖表
        
        ### 支援的檔案格式：
        - Microsoft Excel (.xlsx, .xls)
        - 多工作表支援
        - 自動數據類型檢測
        """)
        
        # 顯示示例數據
        with st.expander("📋 查看示例數據結構"):
            sample_data = pd.DataFrame({
                '日期': pd.date_range('2023-01-01', periods=100),
                '銷售額': np.random.normal(1000, 200, 100),
                '產品類別': np.random.choice(['A', 'B', 'C'], 100),
                '數量': np.random.randint(1, 100, 100),
                '利潤': np.random.normal(200, 50, 100)
            })
            st.dataframe(sample_data.head(10))

# 執行應用程式
if __name__ == "__main__":
    dashboard = ExcelDashboard()
    dashboard.run()
