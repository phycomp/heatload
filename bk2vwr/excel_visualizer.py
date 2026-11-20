import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
from typing import List, Dict, Any, Optional
import numpy as np
import io
import base64

class ExcelVisualizer:
    def __init__(self):
        self.supported_chart_types = ['line', 'bar', 'scatter', 'histogram', 'box', 'heatmap', 'pie']
    
    def read_excel_file(self, file_path: str) -> Dict[str, Any]:
        """讀取 Excel 檔案並返回所有工作表的數據"""
        try:
            excel_file = pd.ExcelFile(file_path)
            sheets_data = {}
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                sheets_data[sheet_name] = {
                    'dataframe': df,
                    'shape': df.shape,
                    'columns': df.columns.tolist(),
                    'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
                    'categorical_columns': df.select_dtypes(include=['object']).columns.tolist(),
                    'data_types': df.dtypes.to_dict()
                }
            
            return {
                'filename': file_path.split('/')[-1],
                'sheets': sheets_data,
                'sheet_names': excel_file.sheet_names
            }
        except Exception as e:
            raise Exception(f"讀取 Excel 檔案時發生錯誤: {e}")
    
    def detect_chart_types(self, df: pd.DataFrame, sheet_name: str) -> List[Dict[str, Any]]:
        """自動檢測適合的圖表類型"""
        suggestions = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        # 如果有數值數據
        if len(numeric_cols) > 0:
            # 單一數值變數 - 直方圖、箱形圖
            if len(numeric_cols) == 1:
                suggestions.extend([
                    {'type': 'histogram', 'x_column': numeric_cols[0], 'title': f'{sheet_name} - {numeric_cols[0]} 分布'},
                    {'type': 'box', 'y_column': numeric_cols[0], 'title': f'{sheet_name} - {numeric_cols[0]} 箱形圖'}
                ])
            
            # 多個數值變數 - 散點圖、相關熱力圖
            if len(numeric_cols) >= 2:
                suggestions.extend([
                    {'type': 'scatter', 'x_column': numeric_cols[0], 'y_column': numeric_cols[1], 
                     'title': f'{sheet_name} - {numeric_cols[0]} vs {numeric_cols[1]}'},
                    {'type': 'heatmap', 'columns': numeric_cols[:5], 'title': f'{sheet_name} - 相關性熱力圖'}
                ])
            
            # 時間序列數據檢測
            date_columns = df.select_dtypes(include=['datetime64']).columns.tolist()
            if date_columns and numeric_cols:
                suggestions.append({
                    'type': 'line', 
                    'x_column': date_columns[0], 
                    'y_column': numeric_cols[0],
                    'title': f'{sheet_name} - 時間序列'
                })
        
        # 如果有分類數據和數值數據
        if categorical_cols and numeric_cols:
            suggestions.extend([
                {'type': 'bar', 'x_column': categorical_cols[0], 'y_column': numeric_cols[0],
                 'title': f'{sheet_name} - {categorical_cols[0]} 比較'},
                {'type': 'box', 'x_column': categorical_cols[0], 'y_column': numeric_cols[0],
                 'title': f'{sheet_name} - {categorical_cols[0]} 分布'}
            ])
        
        # 如果有分類數據
        if categorical_cols:
            value_counts = df[categorical_cols[0]].value_counts()
            if len(value_counts) <= 10:  # 避免太多類別的圓餅圖
                suggestions.append({
                    'type': 'pie', 
                    'names_column': categorical_cols[0],
                    'title': f'{sheet_name} - {categorical_cols[0]} 比例'
                })
        
        return suggestions
    
    def create_plotly_chart(self, df: pd.DataFrame, chart_config: Dict[str, Any]) -> go.Figure:
        """根據配置創建 Plotly 圖表"""
        chart_type = chart_config['type']
        
        try:
            if chart_type == 'line':
                fig = px.line(df, x=chart_config['x_column'], y=chart_config['y_column'],
                            title=chart_config.get('title', 'Line Chart'))
            
            elif chart_type == 'bar':
                fig = px.bar(df, x=chart_config['x_column'], y=chart_config['y_column'],
                           title=chart_config.get('title', 'Bar Chart'))
            
            elif chart_type == 'scatter':
                fig = px.scatter(df, x=chart_config['x_column'], y=chart_config['y_column'],
                               title=chart_config.get('title', 'Scatter Plot'))
            
            elif chart_type == 'histogram':
                fig = px.histogram(df, x=chart_config['x_column'],
                                 title=chart_config.get('title', 'Histogram'))
            
            elif chart_type == 'box':
                if 'x_column' in chart_config:
                    fig = px.box(df, x=chart_config['x_column'], y=chart_config['y_column'],
                               title=chart_config.get('title', 'Box Plot'))
                else:
                    fig = px.box(df, y=chart_config['y_column'],
                               title=chart_config.get('title', 'Box Plot'))
            
            elif chart_type == 'heatmap':
                # 計算相關性矩陣
                corr_matrix = df[chart_config['columns']].corr()
                fig = px.imshow(corr_matrix,
                              title=chart_config.get('title', 'Correlation Heatmap'),
                              color_continuous_scale='RdBu_r',
                              aspect="auto")
            
            elif chart_type == 'pie':
                value_counts = df[chart_config['names_column']].value_counts()
                fig = px.pie(values=value_counts.values, names=value_counts.index,
                           title=chart_config.get('title', 'Pie Chart'))
            
            else:
                # 預設圖表
                fig = px.scatter(df, title="Default Chart")
            
            # 更新佈局
            fig.update_layout(
                height=400,
                showlegend=True,
                template="plotly_white"
            )
            
            return fig
            
        except Exception as e:
            # 創建錯誤圖表
            fig = go.Figure()
            fig.add_annotation(text=f"創建圖表時發生錯誤: {str(e)}",
                            xref="paper", yref="paper",
                            x=0.5, y=0.5, xanchor="center", yanchor="middle",
                            showarrow=False)
            fig.update_layout(title="圖表生成錯誤")
            return fig
    
    def create_matplotlib_chart(self, df: pd.DataFrame, chart_config: Dict[str, Any]) -> str:
        """創建 Matplotlib 圖表並返回 base64 編碼的圖片"""
        try:
            plt.figure(figsize=(10, 6))
            chart_type = chart_config['type']
            
            if chart_type == 'line':
                plt.plot(df[chart_config['x_column']], df[chart_config['y_column']])
                plt.xlabel(chart_config['x_column'])
                plt.ylabel(chart_config['y_column'])
            
            elif chart_type == 'bar':
                plt.bar(df[chart_config['x_column']], df[chart_config['y_column']])
                plt.xlabel(chart_config['x_column'])
                plt.ylabel(chart_config['y_column'])
            
            elif chart_type == 'histogram':
                plt.hist(df[chart_config['x_column']].dropna(), bins=20, alpha=0.7)
                plt.xlabel(chart_config['x_column'])
                plt.ylabel('頻率')
            
            elif chart_type == 'scatter':
                plt.scatter(df[chart_config['x_column']], df[chart_config['y_column']])
                plt.xlabel(chart_config['x_column'])
                plt.ylabel(chart_config['y_column'])
            
            plt.title(chart_config.get('title', 'Chart'))
            plt.tight_layout()
            
            # 轉換為 base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            plt.close()
            return f"創建圖表時發生錯誤: {e}"
    
    def create_altair_chart(self, df: pd.DataFrame, chart_config: Dict[str, Any]) -> alt.Chart:
        """創建 Altair 圖表"""
        try:
            chart_type = chart_config['type']
            
            if chart_type == 'line':
                chart = alt.Chart(df).mark_line().encode(
                    x=alt.X(chart_config['x_column']),
                    y=alt.Y(chart_config['y_column'])
                )
            
            elif chart_type == 'bar':
                chart = alt.Chart(df).mark_bar().encode(
                    x=alt.X(chart_config['x_column']),
                    y=alt.Y(chart_config['y_column'])
                )
            
            elif chart_type == 'scatter':
                chart = alt.Chart(df).mark_circle().encode(
                    x=alt.X(chart_config['x_column']),
                    y=alt.Y(chart_config['y_column'])
                )
            
            elif chart_type == 'histogram':
                chart = alt.Chart(df).mark_bar().encode(
                    x=alt.X(chart_config['x_column'], bin=True),
                    y='count()'
                )
            
            else:
                # 預設圖表
                if len(df.columns) >= 2:
                    chart = alt.Chart(df).mark_circle().encode(
                        x=alt.X(df.columns[0]),
                        y=alt.Y(df.columns[1])
                    )
                else:
                    chart = alt.Chart(df).mark_bar().encode(
                        x=alt.X(df.columns[0]),
                        y='count()'
                    )
            
            return chart.properties(
                title=chart_config.get('title', 'Chart'),
                width=600,
                height=400
            )
            
        except Exception as e:
            # 返回錯誤訊息圖表
            error_df = pd.DataFrame({'error': [f'錯誤: {str(e)}']})
            chart = alt.Chart(error_df).mark_text().encode(
                text='error:N'
            ).properties(
                title='圖表生成錯誤',
                width=600,
                height=400
            )
            return chart
    
    def generate_comprehensive_visualizations(self, df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
        """為工作表生成全面的視覺化"""
        visualizations = {}
        
        # 基本統計資訊
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            visualizations['statistics'] = df[numeric_cols].describe()
        
        # 自動檢測並生成圖表
        chart_suggestions = self.detect_chart_types(df, sheet_name)
        
        plotly_charts = []
        for suggestion in chart_suggestions[:6]:  # 限制圖表數量
            try:
                fig = self.create_plotly_chart(df, suggestion)
                plotly_charts.append({
                    'config': suggestion,
                    'figure': fig
                })
            except Exception as e:
                print(f"生成圖表時發生錯誤: {e}")
        
        visualizations['plotly_charts'] = plotly_charts
        
        # 相關性矩陣
        if len(numeric_cols) > 1:
            try:
                corr_matrix = df[numeric_cols].corr()
                fig_corr = px.imshow(corr_matrix, 
                                   title=f"{sheet_name} - 相關性熱力圖",
                                   color_continuous_scale='RdBu_r',
                                   aspect="auto")
                visualizations['correlation_heatmap'] = fig_corr
            except Exception as e:
                print(f"生成相關性熱力圖時發生錯誤: {e}")
        
        return visualizations
    
    def export_chart_as_html(self, fig: go.Figure, filename: str) -> str:
        """將圖表導出為 HTML 檔案"""
        return fig.to_html(include_plotlyjs='cdn', full_html=False)
