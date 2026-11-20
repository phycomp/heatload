import streamlit as st
from streamlit import code, radio, sidebar
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
from pathlib import Path

# 設置頁面
st.set_page_config(page_title="VNA多文件分析平台", page_icon="📊", layout="wide")

# 標題
st.title("📊 VNA多文件數據分析平台")
st.markdown("---")

# 設置數據目錄路徑
DATA_DIR = 'TDRReportRawData'   #"./vna_data"  # 修改為您的CSV文件目錄路徑

def load_vna_data(file_path):
    """加載單個VNA CSV文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
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
        df = pd.DataFrame([line.split(',') for line in data_lines], columns=headers)
        
        # 轉換數據類型
        numeric_columns = ['FREQ1.GHZ', 'LOGMAG1', 'FREQ2.GHZ', 'LOGMAG2', 
                         'FREQ3.GHZ', 'LOGMAG3', 'FREQ4.GHZ', 'LOGMAG4',
                         'FREQ5.GHZ', 'LOGMAG5', 'FREQ6.GHZ', 'LOGMAG6',
                         'TIME7.SEC', 'RESISTANCE7']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df, metadata, os.path.basename(file_path)
    
    except Exception as e:
        st.error(f"讀取文件 {file_path} 時發生錯誤: {str(e)}")
        return None, None, None

def get_csv_files(directory):
    """獲取目錄中的所有CSV文件"""
    目錄=Path(directory)
    csv_files = 目錄.glob('*/*.csv')    #glob.glob(os.path.join(directory, "*.csv"))
    return csv_files

# 主應用程式
def main():
    # 檢查目錄是否存在
    if not os.path.exists('TDRReportRawData'):
        st.error(f"數據目錄 '{DATA_DIR}' 不存在，請創建該目錄並放入CSV文件")
        st.info("或者修改代碼中的 DATA_DIR 變量指向您的CSV文件目錄")
        return
    
    # 獲取所有CSV文件
    csv_files = get_csv_files(DATA_DIR)
    
    code(['csv_files', csv_files])
    if not csv_files:
        st.error(f"在目錄 '{DATA_DIR}' 中未找到CSV文件")
        st.info("請確保CSV文件存在於該目錄中")
        return
    
    st.sidebar.header("📁 文件選擇")
    
    # 文件選擇器
    with sidebar:
      文件 = radio("選擇要分析的CSV文件:", csv_files, horizontal=True, index=0)   #[f.name for f in csv_files]
        #default=[os.path.basename(f) for f in csv_files[:2]]  # 預設選擇前2個文件
    
    #if not selected_files:
    #    st.info("請在左側選擇要分析的CSV文件")
    #    return
    
    # 加載選中的文件
      all_data = {}
      #for filename in selected_files:
      #    file_path = os.path.join(DATA_DIR, filename)
      #    code(['file_path', file_path])
      df, metadata, _ = load_vna_data(文件)
      if df is not None:
          all_data[文件] = {'df': df, 'metadata': metadata}
    
    if not all_data:
        st.error("未能成功加載任何文件數據")
        return
    
    # 文件信息摘要
    st.header("📋 文件信息摘要")
    col2, col3, col4 = st.columns(3)
    
    with col2:
        total_points = sum(len(data['df']) for data in all_data.values())
        st.metric("總數據點", f"{total_points} 點")
    
    with col3:
        avg_points = total_points // len(all_data)
        st.metric("平均數據點/文件", f"{avg_points} 點")
    
    with col4:
        freq_ranges = []
        for data in all_data.values():
            df = data['df']
            freq_range = f"{df['FREQ1.GHZ'].min():.1f}-{df['FREQ1.GHZ'].max():.1f}GHz"
            freq_ranges.append(freq_range)
        unique_ranges = len(set(freq_ranges))
        st.metric("頻率範圍數", f"{unique_ranges} 種")
    
    # 文件詳細信息
    with st.expander("📄 文件詳細信息"):
        for filename, data in all_data.items():
            df = data['df']
            metadata = data['metadata']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**{filename}**")
                st.write(f"數據點: {len(df)}")
                st.write(f"頻率: {df['FREQ1.GHZ'].min():.3f}-{df['FREQ1.GHZ'].max():.3f} GHz")
            
            with col2:
                if metadata:
                    st.write("設備信息:")
                    if 'MS46524B' in metadata:
                        st.write(f"型號: {metadata.get('MS46524B', 'N/A')}")
                    st.write(f"通道: {metadata.get('CHANNEL', 'N/A')}")
            
            with col3:
                st.write("S11性能:")
                s11_min = df['LOGMAG1'].min()
                s11_max = df['LOGMAG1'].max()
                st.write(f"範圍: {s11_min:.1f} to {s11_max:.1f} dB")
    
    st.markdown("---")
    
    # 頻域分析
    st.header("📡 頻域分析")
    
    # 頻率範圍比較
    st.subheader("頻率範圍比較")
    fig, ax = plt.subplots(figsize=(12, 6))
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(all_data)))
    
    for i, (filename, data) in enumerate(all_data.items()):
        df = data['df']
        freq = df['FREQ1.GHZ']
        s11 = df['LOGMAG1']
        
        ax.plot(freq, s11, label=filename, color=colors[i], linewidth=2)
    
    ax.set_xlabel('頻率 (GHz)')
    ax.set_ylabel('S11 (dB)')
    ax.set_title('多文件 S11 頻率響應比較')
    ax.grid(True, alpha=0.3)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    st.pyplot(fig)
    
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
                for filename, data in all_data.items():
                    df = data['df']
                    col_name = s_param_mapping[s_param]
                    
                    if col_name in df.columns:
                        min_val = df[col_name].min()
                        max_val = df[col_name].max()
                        avg_val = df[col_name].mean()
                        
                        stats_data.append({
                            '文件': filename,
                            '最小值': f"{min_val:.2f} dB",
                            '最大值': f"{max_val:.2f} dB", 
                            '平均值': f"{avg_val:.2f} dB"
                        })
                
                if stats_data:
                    stats_df = pd.DataFrame(stats_data)
                    st.dataframe(stats_df, use_container_width=True, height=200)
    
    st.markdown("---")
    
    # 阻抗分析
    st.header("⚡ 阻抗分析")
    
    # 檢查所有文件是否都有阻抗數據
    has_impedance = all('RESISTANCE7' in data['df'].columns for data in all_data.values())
    
    if has_impedance:
        # 阻抗比較圖
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("阻抗頻率響應比較")
            fig, ax = plt.subplots(figsize=(12, 6))
            
            for i, (filename, data) in enumerate(all_data.items()):
                df = data['df']
                freq = df['FREQ1.GHZ']
                impedance = df['RESISTANCE7']
                
                ax.plot(freq, impedance, label=filename, color=colors[i], linewidth=2)
            
            ax.set_xlabel('頻率 (GHz)')
            ax.set_ylabel('阻抗 (Ω)')
            ax.set_title('多文件阻抗頻率響應比較')
            ax.grid(True, alpha=0.3)
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            st.pyplot(fig)
        
        with col2:
            st.subheader("阻抗統計")
            impedance_stats = []
            
            for filename, data in all_data.items():
                df = data['df']
                impedance = df['RESISTANCE7']
                
                impedance_stats.append({
                    '文件': filename,
                    '最小值': f"{impedance.min():.2f} Ω",
                    '最大值': f"{impedance.max():.2f} Ω",
                    '平均值': f"{impedance.mean():.2f} Ω",
                    '標準差': f"{impedance.std():.2f} Ω"
                })
            
            stats_df = pd.DataFrame(impedance_stats)
            st.dataframe(stats_df, use_container_width=True, height=300)
    
    else:
        st.warning("部分或所有文件缺少阻抗數據")
    
    st.markdown("---")
    
    # 詳細數據視圖
    st.header("🔍 詳細數據視圖")
    
    # 選擇特定文件進行詳細分析
    selected_detail_file = st.selectbox(
        "選擇文件進行詳細分析:",
        list(all_data.keys())
    )
    
    if selected_detail_file:
        detail_data = all_data[selected_detail_file]
        df = detail_data['df']
        metadata = detail_data['metadata']
        
        st.subheader(f"詳細分析: {selected_detail_file}")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.write("**文件信息**")
            st.write(f"數據點數: {len(df)}")
            st.write(f"頻率範圍: {df['FREQ1.GHZ'].min():.3f}-{df['FREQ1.GHZ'].max():.3f} GHz")
            st.write(f"頻寬: {df['FREQ1.GHZ'].max() - df['FREQ1.GHZ'].min():.3f} GHz")
            
            if metadata:
                st.write("**元數據**")
                for key, value in list(metadata.items())[:5]:  # 顯示前5個元數據
                    st.write(f"{key}: {value}")
        
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
                fig, ax1 = plt.subplots(figsize=(10, 6))
                
                param_mapping = {
                    'S11': 'LOGMAG1', 'S21': 'LOGMAG2', 'S31': 'LOGMAG3',
                    'S41': 'LOGMAG4', 'S12': 'LOGMAG5', 'S22': 'LOGMAG6',
                    '阻抗': 'RESISTANCE7'
                }
                
                colors_detailed = ['blue', 'red', 'green', 'purple', 'orange', 'brown', 'black']
                
                # 繪製S參數（左軸）
                s_params = [p for p in plot_params if p != '阻抗']
                for i, param in enumerate(s_params):
                    col_name = param_mapping[param]
                    if col_name in df.columns:
                        ax1.plot(df['FREQ1.GHZ'], df[col_name], 
                                label=param, color=colors_detailed[i], linewidth=2)
                
                ax1.set_xlabel('頻率 (GHz)')
                ax1.set_ylabel('S參數 (dB)')
                ax1.grid(True, alpha=0.3)
                ax1.legend(loc='upper left')
                
                # 如果有選擇阻抗，添加右軸
                if '阻抗' in plot_params and 'RESISTANCE7' in df.columns:
                    ax2 = ax1.twinx()
                    ax2.plot(df['FREQ1.GHZ'], df['RESISTANCE7'], 
                            label='阻抗 (Ω)', color='black', linewidth=2, linestyle='--')
                    ax2.set_ylabel('阻抗 (Ω)')
                    ax2.legend(loc='upper right')
                
                plt.title(f'{selected_detail_file} - 詳細頻率響應')
                plt.tight_layout()
                st.pyplot(fig)
    
    st.markdown("---")
    
    # 數據導出
    st.header("💾 數據導出")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 導出合併統計報告
        st.subheader("導出統計報告")
        
        report_lines = ["VNA多文件分析報告", "="*50, ""]
        report_lines.append(f"生成時間: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"分析文件數: {len(all_data)}")
        report_lines.append("")
        
        for filename, data in all_data.items():
            df = data['df']
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
            use_container_width=True
        )
    
    with col2:
        st.subheader("導出處理後數據")
        st.info("選擇文件導出處理後的CSV數據")
        
        export_file = st.selectbox(
            "選擇要導出的文件:",
            list(all_data.keys())
        )
        
        if export_file:
            csv_data = all_data[export_file]['df'].to_csv(index=False)
            st.download_button(
                label=f"📥 下載 {export_file}",
                data=csv_data,
                file_name=f"processed_{export_file}",
                mime="text/csv",
                use_container_width=True
            )

# 運行主程序
if __name__ == "__main__":
    main()

# 頁腳
st.markdown("---")
st.caption("VNA多文件數據分析平台 | 批量射頻測量分析工具")
