import streamlit as st
from glob import glob
from streamlit import cache_data, dataframe, code, sidebar, radio
from pandas import DataFrame, read_excel
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import io

# 設置頁面
st.set_page_config(
    page_title="VNA測試數據分析",
    page_icon="📊",
    layout="wide"
)

st.title("📊 VNA測試數據分析儀表板")
st.markdown("---")

with sidebar:
  XLSX=glob('TDRReportRawData/*.xlsx')
  xlsx=radio('xlsx文件', XLSX, horizontal=True, key=0)
# 文件上傳
#uploaded_file = st.file_uploader("上傳PASS__20251113_163441.xlsx文件", type="xlsx")
#uploaded_file='TDRReportRawData/PASS__20251113_163441.xlsx'

if xlsx:    # is not None
    #try:
        # 讀取所有sheet
        summary_df = read_excel(xlsx, sheet_name='Summary', header=None)
        report_df = read_excel(xlsx, sheet_name='Report')
        data_df = read_excel(xlsx, sheet_name='Data')
        dataframe(data_df)
        code(['欄位', data_df.columns])
        #['欄位', Index(['Frequency (GHz)', '[2] CH(1) TR(1) Diff IL THRU',
        #'[3] CH(1) TR(2) Diff RL ', '[4] CH(1) TR(3) Diff RL ',
        #'[38] CH(5) TR(1) Diff IL THRU', '[39] CH(5) TR(2) Diff RL ',
        #'[40] CH(5) TR(3) Diff RL '],
        #dtype='object')]
        st.success("✅ 文件讀取成功！")
        
        # 顯示基本信息
        st.subheader("📋 測試概覽")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("測試結果", "PASS", delta="通過", delta_color="normal")
        with col2:
            st.metric("測試時長", "11.034秒")
        with col3:
            st.metric("頻率範圍", "0.03-26.4 GHz")
        with col4:
            st.metric("測試項目數", "10個")
        
        st.markdown("---")
        
        # 標簽頁布局
        tab1, tab2, tab3, tab4 = st.tabs(["📈 數據可視化", "🔍 頻率點分析", "📊 數據分布分析", "📋 原始數據"])
        
        with tab1:
            st.subheader("頻率響應曲線")
            
            # 選擇要顯示的通道
            channels = st.multiselect(
                "選擇要顯示的測試通道",
                options=['CH1_Diff_IL', 'CH1_Diff_RL_1', 'CH1_Diff_RL_2', 'CH5_Diff_IL', 'CH5_Diff_RL_1', 'CH5_Diff_RL_2'],
                default=['CH1_Diff_IL', 'CH5_Diff_IL']
            )
            
            # 創建圖表
            fig = go.Figure()
            
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
            channel_mapping = {
                'CH1_Diff_IL': ('[2] CH(1) TR(1) Diff IL THRU', 'CH1 Diff IL'),
                'CH1_Diff_RL_1': ('[3] CH(1) TR(2) Diff RL', 'CH1 Diff RL (Port1)'),
                'CH1_Diff_RL_2': ('[4] CH(1) TR(3) Diff RL', 'CH1 Diff RL (Port2)'),
                'CH5_Diff_IL': ('[38] CH(5) TR(1) Diff IL THRU', 'CH5 Diff IL'),
                'CH5_Diff_RL_1': ('[39] CH(5) TR(2) Diff RL', 'CH5 Diff RL (Port1)'),
                'CH5_Diff_RL_2': ('[40] CH(5) TR(3) Diff RL', 'CH5 Diff RL (Port2)')
            }
            
            for i, channel in enumerate(channels):
                if channel in channel_mapping:
                    col_name, display_name = channel_mapping[channel]
                    if col_name in data_df.columns:
                        fig.add_trace(go.Scatter(
                            x=data_df['Frequency (GHz)'],
                            y=data_df[col_name],
                            name=display_name,
                            line=dict(color=colors[i % len(colors)], width=2),
                            opacity=0.8
                        ))
            
            fig.update_layout(
                title="頻率響應曲線",
                xaxis_title="頻率 (GHz)",
                yaxis_title="幅度 (dB)",
                height=500,
                template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 插入損耗和回波損耗對比
            st.subheader("通道對比分析")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # CH1 vs CH5 插入損耗對比
                fig_il = go.Figure()
                fig_il.add_trace(go.Scatter(
                    x=data_df['Frequency (GHz)'],
                    y=data_df['[2] CH(1) TR(1) Diff IL THRU'],   #[2] CH(1) TR(1) Diff IL THRU'
                    name='CH1 Diff IL',
                    line=dict(color='blue', width=2)
                ))
                fig_il.add_trace(go.Scatter(
                    x=data_df['Frequency (GHz)'],
                    y=data_df['[38] CH(5) TR(1) Diff IL THRU'],
                    name='CH5 Diff IL',
                    line=dict(color='red', width=2)
                ))
                fig_il.update_layout(
                    title="插入損耗對比 (CH1 vs CH5)",
                    xaxis_title="頻率 (GHz)",
                    yaxis_title="插入損耗 (dB)",
                    height=400
                )
                st.plotly_chart(fig_il, use_container_width=True)
            
            with col2:
                # CH1 回波損耗對比
                data_df
                fig_rl = go.Figure()
                fig_rl.add_trace(go.Scatter(
                    x=data_df['Frequency (GHz)'],
                    y=data_df['[3] CH(1) TR(2) Diff RL '], #['[3] CH(1) TR(2) Diff RL'],
                    name='CH1 Diff RL Port1',
                    line=dict(color='green', width=2)
                ))
                fig_rl.add_trace(go.Scatter(
                    x=data_df['Frequency (GHz)'],
                    y=data_df['[4] CH(1) TR(3) Diff RL '],
                    name='CH1 Diff RL Port2',
                    line=dict(color='orange', width=2)
                ))
                fig_rl.update_layout(
                    title="CH1 回波損耗對比",
                    xaxis_title="頻率 (GHz)",
                    yaxis_title="回波損耗 (dB)",
                    height=400
                )
                st.plotly_chart(fig_rl, use_container_width=True)
        
        with tab2:
            st.subheader("特定頻率點分析")
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                # 頻率選擇
                frequency_options = data_df['Frequency (GHz)'].unique()
                selected_freq = st.selectbox(
                    "選擇頻率點 (GHz)",
                    options=frequency_options,
                    index=len(frequency_options)//2
                )
                
                # 獲取選定頻率的數據
                freq_data = data_df[data_df['Frequency (GHz)'] == selected_freq].iloc[0]
                
                st.metric("選定頻率", f"{selected_freq} GHz")
                
                # 顯示該頻率點的關鍵數據
                st.write("**該頻率點測試值:**")
                st.write(f"- CH1 Diff IL: {freq_data['[2] CH(1) TR(1) Diff IL THRU']:.3f} dB")
                st.write(f"- CH1 Diff RL Port1: {freq_data['[3] CH(1) TR(2) Diff RL ']:.3f} dB")
                st.write(f"- CH1 Diff RL Port2: {freq_data['[4] CH(1) TR(3) Diff RL ']:.3f} dB")
                st.write(f"- CH5 Diff IL: {freq_data['[38] CH(5) TR(1) Diff IL THRU']:.3f} dB")
                st.write(f"- CH5 Diff RL Port1: {freq_data['[39] CH(5) TR(2) Diff RL ']:.3f} dB")
                st.write(f"- CH5 Diff RL Port2: {freq_data['[40] CH(5) TR(3) Diff RL ']:.3f} dB")
            
            with col2:
                # 在圖表中高亮顯示選定的頻率點
                fig_highlight = go.Figure()
                
                # 添加CH1 Diff IL曲線
                fig_highlight.add_trace(go.Scatter(
                    x=data_df['Frequency (GHz)'],
                    y=data_df['[2] CH(1) TR(1) Diff IL THRU'],
                    name='CH1 Diff IL',
                    line=dict(color='lightblue', width=1),
                    opacity=0.7
                ))
                
                # 高亮點
                fig_highlight.add_trace(go.Scatter(
                    x=[selected_freq],
                    y=[freq_data['[2] CH(1) TR(1) Diff IL THRU']],
                    mode='markers',
                    name=f'{selected_freq} GHz',
                    marker=dict(color='red', size=12, line=dict(width=2, color='darkred')),
                    showlegend=True
                ))
                
                fig_highlight.update_layout(
                    title=f"頻率點 {selected_freq} GHz 在CH1 Diff IL曲線上的位置",
                    xaxis_title="頻率 (GHz)",
                    yaxis_title="插入損耗 (dB)",
                    height=400
                )
                
                st.plotly_chart(fig_highlight, use_container_width=True)
            
            # 頻率範圍統計
            st.subheader("頻率範圍統計")
            freq_ranges = [
                (0, 5, "低頻段 (0-5 GHz)"),
                (5, 10, "中頻段 (5-10 GHz)"),
                (10, 15, "中高頻段 (10-15 GHz)"),
                (15, 20, "高頻段 (15-20 GHz)"),
                (20, 26.4, "超高頻段 (20-26.4 GHz)")
            ]
            
            stats_data = []
            for low, high, name in freq_ranges:
                mask = (data_df['Frequency (GHz)'] >= low) & (data_df['Frequency (GHz)'] <= high)
                if mask.any():
                    subset = data_df[mask]
                    stats_data.append({
                        '頻段': name,
                        'CH1_IL_均值': subset['[2] CH(1) TR(1) Diff IL THRU'].mean(),
                        'CH1_IL_標準差': subset['[2] CH(1) TR(1) Diff IL THRU'].std(),
                        'CH5_IL_均值': subset['[38] CH(5) TR(1) Diff IL THRU'].mean(),
                        'CH5_IL_標準差': subset['[38] CH(5) TR(1) Diff IL THRU'].std()
                    })
            
            stats_df = DataFrame(stats_data)
            st.dataframe(stats_df, use_container_width=True, width='stretch') #.to_string()
            #"{:.3f}" style.format("{:.3f}")
        
        with tab3:
            st.subheader("數據分布分析")
            
            # 選擇分析的數據列
            analysis_col = st.selectbox(
                "選擇要分析的數據列",
                options=['[2] CH(1) TR(1) Diff IL THRU', '[38] CH(5) TR(1) Diff IL THRU', 
                        '[3] CH(1) TR(2) Diff RL', '[4] CH(1) TR(3) Diff RL']
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                # 直方圖
                fig_hist = px.histogram(
                    data_df, 
                    x=analysis_col,
                    nbins=50,
                    title=f"{analysis_col} 分布直方圖",
                    color_discrete_sequence=['#3366CC']
                )
                fig_hist.update_layout(height=400)
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col2:
                # 箱線圖
                fig_box = px.box(
                    data_df,
                    y=analysis_col,
                    title=f"{analysis_col} 箱線圖",
                    color_discrete_sequence=['#3366CC']
                )
                fig_box.update_layout(height=400)
                st.plotly_chart(fig_box, use_container_width=True)
            
            # 統計摘要
            st.subheader("統計摘要")
            selected_data = data_df[analysis_col]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("均值", f"{selected_data.mean():.3f}")
            with col2:
                st.metric("標準差", f"{selected_data.std():.3f}")
            with col3:
                st.metric("最小值", f"{selected_data.min():.3f}")
            with col4:
                st.metric("最大值", f"{selected_data.max():.3f}")
            
            # 相關性分析
            st.subheader("通道間相關性分析")
            correlation_data = data_df[['[2] CH(1) TR(1) Diff IL THRU',
            '[38] CH(5) TR(1) Diff IL THRU',
            '[3] CH(1) TR(2) Diff RL ', #'[3] CH(1) TR(2) Diff RL',
            '[4] CH(1) TR(3) Diff RL ']]    #[4] CH(1) TR(3) Diff RL
            
            # 重命名列以便顯示
            correlation_data.columns = ['CH1_IL', 'CH5_IL', 'CH1_RL1', 'CH1_RL2']
            
            fig_corr = px.imshow(
                correlation_data.corr(),
                title="通道間相關性矩陣",
                color_continuous_scale='RdBu_r',
                aspect="auto"
            )
            st.plotly_chart(fig_corr, use_container_width=True)
        
        with tab4:
            st.subheader("原始數據浏覽")
            
            # 選擇要顯示的數據集
            dataset = st.selectbox(
                "選擇數據集",
                ["測試數據 (Data)", "報告 (Report)", "摘要 (Summary)"]
            )
            
            if dataset == "測試數據 (Data)":
                st.dataframe(data_df, use_container_width=True)
            elif dataset == "報告 (Report)":
                st.dataframe(report_df, use_container_width=True)
            else:
                st.dataframe(summary_df, use_container_width=True)
            
            # 數據下載
            st.subheader("數據導出")
            
            @cache_data
            def convert_df_to_csv(df):
                return df.to_csv(index=False).encode('utf-8')
            
            csv_data = convert_df_to_csv(data_df)
            
            st.download_button(
                label="📥 下載測試數據爲CSV",
                data=csv_data,
                file_name="vna_test_data.csv",
                mime="text/csv"
            )
    
    #except Exception as e:
    #    st.error(f"讀取文件時出錯: {str(e)}")
    #    st.info("請確保上傳的文件格式正確，包含Summary、Report和Data三個工作表")

else:
    st.info("👆 請上傳PASS__20251113_163441.xlsx文件開始分析")
    
    # 顯示使用說明
    with st.expander("使用說明"):
        st.markdown("""
        ### 功能說明：
        
        1. **數據可視化** 📈
           - 查看各通道的頻率響應曲線
           - 對比不同通道的性能
           - 交互式圖表，支持縮放和懸停查看數值
        
        2. **頻率點分析** 🔍
           - 分析特定頻率點的測試值
           - 查看不同頻段的統計信息
           - 定位關鍵頻率性能
        
        3. **數據分布分析** 📊
           - 查看數據分布直方圖和箱線圖
           - 統計分析（均值、標準差等）
           - 通道間相關性分析
        
        4. **原始數據** 📋
           - 浏覽原始測試數據
           - 導出數據爲CSV格式
        
        ### 支持的數據類型：
        - 差分插入損耗 (Diff IL)
        - 差分回波損耗 (Diff RL)
        - 多通道測試數據
        - 頻率範圍：0.03-26.4 GHz
        """)
