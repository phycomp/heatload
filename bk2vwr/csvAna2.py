import streamlit as st
from streamlit import code, radio, sidebar
from pandas import read_csv, DataFrame, to_numeric, Timestamp
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
import glob
from pathlib import Path

# 設置頁面
st.set_page_config(page_title="VNA多文件分析平台", page_icon="📊", layout="wide")

# 標題
st.title("📊 VNA多文件數據分析平台")
st.markdown("---")

# 設置數據目錄路徑
#DATA_DIR = 'TDRReportRawData'
with sidebar:
  DATA_DIR = radio("CSV文件目錄路徑:", ["./TDRReportRawData/PASS__20251114_153309", "./TDRReportRawData/FAIL__20251113_163346", "./TDRReportRawData/PASS__20251113_163441"], horizontal=True, index=0)

def load_vna_data(file_path):
    """加載單個VNA CSV文件"""
    try:
        with open(file_path, encoding='utf-8') as file:
            content = file.read()

        lines = content.split('\n')
        metadata = {}
        data_lines = []

        for line in lines:
            if line.startswith('!'):
                if ':' in line:
                    key, value = line[1:].split(':', 1)
                    metadata[key.strip()] = value.strip()
                else:
                    metadata_line = line[1:].strip()
                    if metadata_line:
                        if ' ' in metadata_line:
                            key, value = metadata_line.split(' ', 1)
                            metadata[key] = value
            elif line.startswith('PNT'):
                headers = line.strip().split(',')
            elif line and line[0].isdigit():
                data_lines.append(line.strip())

        # 創建DataFrame
        df = DataFrame([line.split(',') for line in data_lines], columns=headers)

        # 轉換數據類型
        numeric_columns = ['FREQ1.GHZ', 'LOGMAG1', 'FREQ2.GHZ', 'LOGMAG2', 'FREQ3.GHZ', 'LOGMAG3', 'FREQ4.GHZ', 'LOGMAG4', 'FREQ5.GHZ', 'LOGMAG5', 'FREQ6.GHZ', 'LOGMAG6', 'TIME7.SEC', 'RESISTANCE7']

        for col in numeric_columns:
            if col in df.columns:
                df[col] = to_numeric(df[col], errors='coerce')

        return df, metadata, os.path.basename(file_path)

    except Exception as e:
        st.error(f"讀取文件 {file_path} 時發生錯誤: {str(e)}")
        return None, None, None

def get_csv_files(directory):
    """獲取目錄中的所有CSV文件"""
    目錄=Path(directory)
    csv_files = 目錄.glob('*.csv')
    return csv_files

def create_comparison_plot_with_overlapped_names(all_data, plot_type='S11'):
    """創建帶有重疊檔名的比較圖表"""

    # 顏色配置
    colors = px.colors.qualitative.Set1 + px.colors.qualitative.Set2 + px.colors.qualitative.Set3

    fig = go.Figure()

    param_mapping = {
        'S11': 'LOGMAG1', 'S21': 'LOGMAG2', 'S31': 'LOGMAG3',
        'S41': 'LOGMAG4', 'S12': 'LOGMAG5', 'S22': 'LOGMAG6',
        '阻抗': 'RESISTANCE7'
    }

    col_name = param_mapping.get(plot_type, 'LOGMAG1')
    yaxis_label = 'S參數 (dB)' if plot_type != '阻抗' else '阻抗 (Ω)'

    # 添加數據軌跡
    for i, (filename, df) in enumerate(all_data.items()):
        #df = data['df']
        #df['source_file']

        if col_name not in df.columns:
            continue

        freq = df['FREQ1.GHZ']
        values = df[col_name]
        color = colors[i % len(colors)]

        # 簡化檔名顯示（去除副檔名）
        filename=Path(filename)
        display_name = filename.stem#replace('.csv', '')

        # 添加數據線
        fig.add_trace(go.Scatter(
            x=freq,
            y=values,
            mode='lines',
            #name=display_name,
            line=dict(color=color, width=2),
            hovertemplate=f'<b>{display_name}</b><br>頻率: %{{x:.3f}} GHz<br>{plot_type}: %{{y:.2f}} {"dB" if plot_type != "阻抗" else "Ω"}<extra></extra>'
        ))

        # 在曲線末端添加檔名標籤（重疊顯示）
        if len(freq) > 0:
            # 選擇曲線上的幾個點來放置標籤（避免全部擠在一起）
            label_positions = [
                int(len(freq) * 0.1),  # 10%位置
                int(len(freq) * 0.5),  # 50%位置
                int(len(freq) * 0.9)   # 90%位置
            ]

            for pos in label_positions:
                if pos < len(freq):
                    fig.add_trace(go.Scatter(
                        x=[freq.iloc[pos]],
                        y=[values.iloc[pos]],
                        mode='text',
                        text=[display_name],
                        textposition="middle right",
                        textfont=dict(
                            color=color,
                            size=10,
                            family="Arial"
                        ),
                        showlegend=False,
                        hoverinfo='skip'
                    ))

    # 更新佈局
    fig.update_layout(
        title=dict(
            text=f'多文件 {plot_type} 頻率響應比較',
            x=0.5,
            xanchor='center',
            font=dict(size=16)
        ),
        xaxis=dict(
            title='頻率 (GHz)',
            gridcolor='lightgray',
            gridwidth=1
        ),
        yaxis=dict(
            title=yaxis_label,
            gridcolor='lightgray',
            gridwidth=1
        ),
        plot_bgcolor='white',
        height=600,
        margin=dict(l=80, r=80, t=80, b=80),
        hovermode='closest'
    )

    return fig

def create_detailed_plot_with_names(df, filename, selected_params):
    """創建單文件詳細圖表，帶有重疊參數名稱"""

    param_mapping = {
        'S11': ('LOGMAG1', 'S參數 (dB)', '#1f77b4'),
        'S21': ('LOGMAG2', 'S參數 (dB)', '#ff7f0e'),
        'S31': ('LOGMAG3', 'S參數 (dB)', '#2ca02c'),
        'S41': ('LOGMAG4', 'S參數 (dB)', '#d62728'),
        'S12': ('LOGMAG5', 'S參數 (dB)', '#9467bd'),
        'S22': ('LOGMAG6', 'S參數 (dB)', '#8c564b'),
        '阻抗': ('RESISTANCE7', '阻抗 (Ω)', '#000000')
    }

    # 創建子圖（如果需要雙Y軸）
    has_impedance = '阻抗' in selected_params and 'RESISTANCE7' in df.columns
    has_s_params = any(p in selected_params for p in ['S11', 'S21', 'S31', 'S41', 'S12', 'S22'])

    if has_impedance and has_s_params:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        secondary_y = True
    else:
        fig = go.Figure()
        secondary_y = False

    # 添加數據軌跡
    for param in selected_params:
        if param in param_mapping:
            col_name, y_label, color = param_mapping[param]

            if col_name in df.columns:
                use_secondary_y = secondary_y and param == '阻抗'

                # 添加數據線
                fig.add_trace(go.Scatter(
                    x=df['FREQ1.GHZ'],
                    y=df[col_name],
                    mode='lines',
                    name=param,
                    line=dict(color=color, width=2, dash='dash' if param == '阻抗' else 'solid'),
                    hovertemplate=f'<b>{param}</b><br>頻率: %{{x:.3f}} GHz<br>數值: %{{y:.2f}} {"dB" if param != "阻抗" else "Ω"}<extra></extra>',
                    yaxis='y2' if use_secondary_y else 'y'
                ))

                # 在曲線上添加參數名稱標籤
                if len(df) > 0:
                    # 選擇幾個位置放置標籤
                    positions = [int(len(df) * 0.2), int(len(df) * 0.8)]

                    for pos in positions:
                        if pos < len(df):
                            fig.add_trace(go.Scatter(
                                x=[df['FREQ1.GHZ'].iloc[pos]],
                                y=[df[col_name].iloc[pos]],
                                mode='text',
                                text=[param],
                                textposition="middle right",
                                textfont=dict(
                                    color=color,
                                    size=12,
                                    family="Arial"
                                ),
                                showlegend=False,
                                hoverinfo='skip',
                                yaxis='y2' if use_secondary_y else 'y'
                            ))

    # 更新佈局
    layout_config = dict(
        title=dict(
            text=f'{filename} - 詳細頻率響應',
            x=0.5,
            xanchor='center',
            font=dict(size=16)
        ),
        xaxis=dict(
            title='頻率 (GHz)',
            gridcolor='lightgray',
            gridwidth=1
        ),
        yaxis=dict(
            title='S參數 (dB)' if has_s_params else '阻抗 (Ω)',
            gridcolor='lightgray',
            gridwidth=1
        ),
        plot_bgcolor='white',
        height=500,
        margin=dict(l=80, r=80, t=80, b=80),
        hovermode='closest'
    )

    if has_impedance and has_s_params:
        layout_config['yaxis2'] = dict(
            title='阻抗 (Ω)',
            gridcolor='lightgray',
            gridwidth=1,
            overlaying='y',
            side='right'
        )

    fig.update_layout(**layout_config)

    return fig

# 主應用程式
def main():
    # 檢查目錄是否存在
    if not os.path.exists(DATA_DIR):
        st.error(f"數據目錄 '{DATA_DIR}' 不存在，請創建該目錄並放入CSV文件")
        st.info("或者修改代碼中的 DATA_DIR 變量指向您的CSV文件目錄")
        return

    # 獲取所有CSV文件
    csv_files = get_csv_files(DATA_DIR)

    if not csv_files:
        st.error(f"在目錄 '{DATA_DIR}' 中未找到CSV文件")
        st.info("請確保CSV文件存在於該目錄中")
        return

    st.sidebar.header("📁 文件選擇")

    #with sidebar:
    #  文件 = radio("選擇要分析的CSV文件:", csv_files, horizontal=True, index=0)   #[f.name for f in csv_files]

    # 加載選中的文件
    all_data={}
    #df, metadata, _ = load_vna_data(文件)
    #if df is not None:
    #    all_data[文件] = {'df': df, 'metadata': metadata}
    for file_path in list(csv_files):
        #code(['file_path', file_path])
        df = read_csv(file_path, skiprows=16)
        
        file_name = Path(file_path).stem # 獲取文件名（不含擴展名）
        
        # 添加文件名作爲標識列
        #df['source_file'] = file_name
        
        all_data[file_name]=df

    if not all_data:
        st.error("未能成功加載任何文件數據")
        return
    # 文件信息摘要
    st.header("📋 文件信息摘要")
    col2, col3, col4 = st.columns(3)

    with col2:
        total_points = sum(len(資框) for 資框 in all_data)
        st.metric("總數據點", f"{total_points} 點")

    with col3:
        avg_points = total_points // len(all_data)
        st.metric("平均數據點/文件", f"{avg_points} 點")

    with col4:
        freq_ranges = []
        for file_name, df in all_data.items():
            freq_range = f"{df['FREQ1.GHZ'].min():.1f}-{df['FREQ1.GHZ'].max():.1f}GHz"
            freq_ranges.append(freq_range)
        unique_ranges = len(set(freq_ranges))
        st.metric("頻率範圍數", f"{unique_ranges} 種")

    # 文件詳細信息
    with st.expander("📄 文件詳細信息"):
        for file_name, df in all_data.items():
            #df = data['df']
            #metadata = data['metadata']

            col1, col2, col3 = st.columns(3)

            with col1:
                #st.write(f"**{filename}**")
                #st.write(f"數據點: {len(df)}")
                st.write(f"頻率: {df['FREQ1.GHZ'].min():.3f}-{df['FREQ1.GHZ'].max():.3f} GHz")

            with col2:
                pass
                #if metadata:
                #    st.write("設備信息:")
                #    if 'MS46524B' in metadata:
                #        st.write(f"型號: {metadata.get('MS46524B', 'N/A')}")
                #    st.write(f"通道: {metadata.get('CHANNEL', 'N/A')}")

            with col3:
                st.write("S11性能:")
                s11_min = df['LOGMAG1'].min()
                s11_max = df['LOGMAG1'].max()
                st.write(f"範圍: {s11_min:.1f} to {s11_max:.1f} dB")

    st.markdown("---")

    # 頻域分析
    st.header("📡 頻域分析")

    # 頻率範圍比較 - 使用Plotly
    st.subheader("頻率範圍比較")

    # 選擇比較類型
    comparison_type = st.selectbox(
        "選擇比較參數:",
        ['S11', 'S21', 'S31', 'S41', 'S12', 'S22', '阻抗'],
        key="comparison_type"
    )

    fig_comparison = create_comparison_plot_with_overlapped_names(all_data, comparison_type)
    st.plotly_chart(fig_comparison, width='stretch')

    # S參數統計
    st.subheader("S參數統計比較")

    # 選擇要比較的S參數
    s_param_options = ['S11', 'S21', 'S31', 'S41', 'S12', 'S22']
    selected_s_params = st.multiselect(
        "選擇要比較的S參數:",
        s_param_options,
        default=['S11', 'S21']
    )

    if selected_s_params:
        col_count = len(selected_s_params)
        cols = st.columns(col_count)

        s_param_mapping = {
            'S11': 'LOGMAG1', 'S21': 'LOGMAG2', 'S31': 'LOGMAG3',
            'S41': 'LOGMAG4', 'S12': 'LOGMAG5', 'S22': 'LOGMAG6'
        }

        for idx, s_param in enumerate(selected_s_params):
            with cols[idx]:
                st.write(f"**{s_param} 統計**")

                stats_data = []
                for filename, df in all_data.items():
                    filename=Path(filename)
                    col_name = s_param_mapping[s_param]

                    if col_name in df.columns:
                        min_val = df[col_name].min()
                        max_val = df[col_name].max()
                        avg_val = df[col_name].mean()

                        stats_data.append({
                            '文件': filename.stem,  #replace('.csv', ''),
                            '最小值': f"{min_val:.2f} dB",
                            '最大值': f"{max_val:.2f} dB",
                            '平均值': f"{avg_val:.2f} dB"
                        })

                if stats_data:
                    stats_df = DataFrame(stats_data)
                    st.dataframe(stats_df, width='stretch', height=200)

    st.markdown("---")

    # 阻抗分析
    st.header("⚡ 阻抗分析")

    # 檢查所有文件是否都有阻抗數據
    has_impedance = all('RESISTANCE7' in df.columns for data in all_data.values())

    if has_impedance:
        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader("阻抗頻率響應比較")
            fig_impedance = create_comparison_plot_with_overlapped_names(all_data, '阻抗')
            st.plotly_chart(fig_impedance, width='stretch')

        with col2:
            st.subheader("阻抗統計")
            impedance_stats = []

            for filename, df in all_data.items():
                filename=Path(filename)
                impedance = df['RESISTANCE7']

                impedance_stats.append({
                    '文件': filename.stem, #replace('.csv', ''),
                    '最小值': f"{impedance.min():.2f} Ω",
                    '最大值': f"{impedance.max():.2f} Ω",
                    '平均值': f"{impedance.mean():.2f} Ω",
                    '標準差': f"{impedance.std():.2f} Ω"
                })

            stats_df = DataFrame(impedance_stats)
            st.dataframe(stats_df, width='stretch', height=300)

    else:
        st.warning("部分或所有文件缺少阻抗數據")

    st.markdown("---")

    # 詳細數據視圖
    st.header("🔍 詳細數據視圖")

    # 選擇特定文件進行詳細分析
    selected_detail_file = radio( "選擇文件進行詳細分析:", list(all_data.keys()), horizontal=True, index=0)

    if selected_detail_file:
        df = all_data[selected_detail_file]
        df
        #metadata = df['metadata']

        st.subheader(f"詳細分析: {selected_detail_file}")

        col1, col2 = st.columns([1, 2])

        with col1:
            st.write("**文件信息**")
            st.write(f"數據點數: {len(df)}")
            st.write(f"頻率範圍: {df['FREQ1.GHZ'].min():.3f}-{df['FREQ1.GHZ'].max():.3f} GHz")
            st.write(f"頻寬: {df['FREQ1.GHZ'].max() - df['FREQ1.GHZ'].min():.3f} GHz")

            #if metadata:
            #    st.write("**元數據**")
            #    for key, value in list(metadata.items())[:5]:  # 顯示前5個元數據
            #        st.write(f"{key}: {value}")

        with col2:
            st.write("**S參數詳細視圖**")

            # 交互式參數選擇
            plot_params = st.multiselect(
                "選擇要繪製的參數:",
                ['S11', 'S21', 'S31', 'S41', 'S12', 'S22', '阻抗'],
                default=['S11', '阻抗'],
                key="detail_plot"
            )

            if plot_params:
                fig_detailed = create_detailed_plot_with_names(df, selected_detail_file, plot_params)
                st.plotly_chart(fig_detailed, width='stretch')

    st.markdown("---")

    # 數據導出
    st.header("💾 數據導出")

    col1, col2 = st.columns(2)

    with col1:
        # 導出合併統計報告
        st.subheader("導出統計報告")

        report_lines = ["VNA多文件分析報告", "="*50, ""]
        report_lines.append(f"生成時間: {Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"分析文件數: {len(all_data)}")
        report_lines.append("")

        for filename, df in all_data.items():
            report_lines.append(f"文件: {filename}")
            report_lines.append(f"  數據點: {len(df)}")
            report_lines.append(f"  頻率範圍: {df['FREQ1.GHZ'].min():.3f}-{df['FREQ1.GHZ'].max():.3f} GHz")
            report_lines.append(f"  S11範圍: {df['LOGMAG1'].min():.2f} to {df['LOGMAG1'].max():.2f} dB")
            if 'RESISTANCE7' in df.columns:
                report_lines.append(f"  阻抗範圍: {df['RESISTANCE7'].min():.2f} to {df['RESISTANCE7'].max():.2f} Ω")
            report_lines.append("")

        report_text = "\n".join(report_lines)

        st.download_button(
            label="📄 下載統計報告",
            data=report_text,
            file_name="vna_multi_file_analysis_report.txt",
            mime="text/plain",
            width='stretch'
        )

    with col2:
        st.subheader("導出處理後數據")
        st.info("選擇文件導出處理後的CSV數據")

        export_file = st.selectbox(
            "選擇要導出的文件:",
            list(all_data.keys())
        )

        if export_file:
            csv_data = all_data[export_file].to_csv(index=False)
            st.download_button(
                label=f"📥 下載 {export_file}",
                data=csv_data,
                file_name=f"processed_{export_file}",
                mime="text/csv",
                width='stretch'
            )

# 運行主程序
if __name__ == "__main__":
    main()

# 頁腳
st.markdown("---")
st.caption("VNA多文件數據分析平台 | 批量射頻測量分析工具")
