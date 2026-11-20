from streamlit import code, columns, dataframe, download_button, error, expander, header, info, markdown, metric, plotly_chart, set_page_config, sidebar, subheader, tabs, text_area, title, warning, write, radio
from numpy import nan
from pandas import DataFrame, ExcelFile, read_excel, to_numeric
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
import glob
from io import BytesIO
import json
import re

# 設置頁面
set_page_config(
    page_title="通用Excel數據分析儀表板",
    page_icon="📊",
    layout="wide"
)

title("📊 通用Excel數據分析儀表板")
markdown("---")

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
            numeric_count = to_numeric(clean_series, errors='coerce').notna().sum()
            
            # 如果超過50%的數據可以轉換爲數值，則認爲這是數值列
            if numeric_count / len(df) > 0.5:
                numeric_columns.append(col)
        except:
            continue
    return numeric_columns

def get_excel_files(directory="."):
    """獲取目錄下所有的Excel文件"""
    excel_files = glob.glob(os.path.join(directory, "*.xlsx")) + glob.glob(os.path.join(directory, "*.xls"))
    return [os.path.basename(f) for f in excel_files]

def extract_summary_info(df, sheet_name):
    """從Summary sheet中提取廠商信息和測試結果信息"""
    summary_info = {
        "sheet_name": sheet_name,
        "vendor_info": {},
        "test_results": {
            "summary": {},
            "details": []
        }
    }
    
    # 清理數據
    df_clean = clean_column_names(df)
    
    # 轉換爲字符串以便處理
    df_str = df_clean.astype(str)
    
    # 提取廠商信息（通常在表格的前半部分）
    vendor_keywords = {
        'project': ['project', '項目'],
        'serial_number': ['serial number', 'serial no', '序列號'],
        'equipment': ['equipment', '設備'],
        'version': ['version', '版本'],
        'test_script': ['test script', '測試腳本'],
        'start_time': ['start time', '開始時間'],
        'end_time': ['end time', '結束時間'],
        'test_result': ['test result', '測試結果'],
        'time_span': ['time span', '時間跨度', 'time span (sec.)']
    }
    
    # 搜索廠商信息
    for idx, row in df_str.iterrows():
        for i, cell in enumerate(row):
            cell_clean = cell.strip()
            if not cell_clean or cell_clean == 'nan':
                continue
                
            # 檢查是否是鍵值對格式
            for key, keywords in vendor_keywords.items():
                for keyword in keywords:
                    if keyword in cell_clean.lower():
                        # 嘗試獲取對應的值（可能在右側單元格）
                        if i + 1 < len(row):
                            value = row[i + 1].strip()
                            if value and value != 'nan':
                                summary_info["vendor_info"][key] = value
                                break
    
    # 提取測試結果詳細信息（通常在表格的後半部分）
    test_results_found = False
    judgement_header_found = False
    headers = []
    
    for idx, row in df_str.iterrows():
        row_clean = [cell.strip() for cell in row if cell.strip() and cell.strip() != 'nan']
        
        #code(['row_clean', row_clean])
        if not row_clean:
            continue
            
        # 尋找Judgement標題行
        if 'judgement' in ' '.join(row_clean).lower():
            headers = row_clean
            judgement_header_found = True
            continue
            
        # 如果找到了標題行，接下來的行就是測試結果數據
        #code(['judgement_header_found=', judgement_header_found,  'row_clean=', row_clean])
        #if judgement_header_found and row_clean:
            #code(['anyResult=', any(result in row_clean[0].upper() for result in ['PASS', 'FAIL', '通過', '失敗'])])
            #if any(result in row_clean[0].upper() for result in ['PASS', 'FAIL', '通過', '失敗']):
        if judgement_header_found and row_clean:
          first_cell = row_clean[0].upper() if row_clean else ""
          if any(result in first_cell for result in ['PASS', 'FAIL', '通过', '失败']):
                test_results_found = True
                #code(['row_clean>=header', len(row_clean) >= len(headers)])
                #if len(row_clean) >= len(headers):
                test_result = {
                    headers[j]: row_clean[j] if j < len(row_clean) else '' 
                    for j in range(min(len(headers), len(row_clean)))
                }
                summary_info["test_results"]["details"].append(test_result)
    
            # 統計測試結果

    #code(['details', summary_info["test_results"]["details"]])
    if summary_info["test_results"]["details"]:
        pass_count = sum(1 for item in summary_info["test_results"]["details"] 
                        if 'PASS' in item.get('Judgement', '').upper() or '通過' in item.get('Judgement', ''))
        fail_count = sum(1 for item in summary_info["test_results"]["details"] 
                        if 'FAIL' in item.get('Judgement', '').upper() or '失敗' in item.get('Judgement', ''))
        
        summary_info["test_results"]["summary"] = {
            "total_tests": len(summary_info["test_results"]["details"]),
            "pass_count": pass_count,
            "fail_count": fail_count,
            "pass_rate": f"{(pass_count/len(summary_info["test_results"]["details"])*100):.1f}%" if summary_info["test_results"]["details"] else "0%"
        }
    
    code(['summary_info', summary_info])
    return summary_info

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
            y_data = to_numeric(df_clean[y_col].astype(str).str.strip().replace('', np.nan), errors='coerce')
            
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
        fig_hist = make_subplots(rows=1, cols=min(3, len(analysis['numeric_columns'])), 
                               subplot_titles=analysis['numeric_columns'][:3])
        
        for i, col in enumerate(analysis['numeric_columns'][:3]):
            data = to_numeric(df_clean[col].astype(str).str.strip().replace('', np.nan), errors='coerce')
            fig_hiadd_trace(go.Histogram(x=data, name=col), row=1, col=i+1)
        
        fig_hiupdate_layout(height=400, title_text=f"{sheet_name} - 數值分布")
        visualizations.append(("數值分布", fig_hist))
        
        # 箱線圖
        if len(analysis['numeric_columns']) > 1:
            fig_box = go.Figure()
            for col in analysis['numeric_columns'][:5]:  # 限制顯示5個箱線圖
                data = to_numeric(df_clean[col].astype(str).str.strip().replace('', np.nan), errors='coerce')
                fig_box.add_trace(go.Box(y=data, name=col))
            
            fig_box.update_layout(height=400, title=f"{sheet_name} - 箱線圖")
            visualizations.append(("箱線圖", fig_box))
    
    # 3. 相關性熱力圖
    if len(analysis['numeric_columns']) > 2:
        try:
            # 創建數值數據的子集
            numeric_data = df_clean[analysis['numeric_columns']].apply(
                lambda x: to_numeric(x.astype(str).str.strip().replace('', np.nan), errors='coerce')
            )
            corr_matrix = numeric_data.corr()
            
            fig_corr = px.imshow(
                corr_matrix,
                title=f"{sheet_name} - 相關性熱力圖",
                color_continuous_scale='RdBu_r',
                aspect="auto"
            )
            visualizations.append(("相關性分析", fig_corr))
        except:
            pass
    
    return visualizations

def display_summary_info(summary_info):
    """顯示Summary分頁的完整信息"""
    subheader("📋 Summary信息總覽")
    
    # 顯示廠商信息
    if summary_info["vendor_info"]:
        write("### 廠商信息")
        vendor_df = DataFrame(list(summary_info["vendor_info"].items()), 
                               columns=['項目', '值'])
        dataframe(vendor_df, use_container_width=True)
    
    # 顯示測試結果統計
    if summary_info["test_results"]["summary"]:
        write("### 測試結果統計")
        stats = summary_info["test_results"]["summary"]
        
        col1, col2, col3, col4 = columns(4)
        with col1:
            metric("總測試數", stats["total_tests"])
        with col2:
            metric("通過數", stats["pass_count"], delta=f"{stats['pass_count']}")
        with col3:
            metric("失敗數", stats["fail_count"], delta=f"{stats['fail_count']}", delta_color="inverse")
        with col4:
            metric("通過率", stats["pass_rate"])
    
    # 顯示詳細測試結果
    if summary_info["test_results"]["details"]:
        write("### 詳細測試結果")
        test_results_df = DataFrame(summary_info["test_results"]["details"])
        
        # 爲PASS/FAIL添加顏色
        def color_judgement(val):
            if 'PASS' in str(val).upper() or '通過' in str(val):
                return 'color: green; font-weight: bold'
            elif 'FAIL' in str(val).upper() or '失敗' in str(val):
                return 'color: red; font-weight: bold'
            return ''
        
        styled_df = test_results_df.style.applymap(color_judgement, subset=['Judgement'])
        dataframe(styled_df, use_container_width=True)
    
    # JSON格式顯示
    with expander("JSON格式數據"):
        json_tabs = tabs(["格式化JSON", "原始JSON"])
        
        with json_tabs[0]:
            json_str = json.dumps(summary_info, ensure_ascii=False, indent=2)
            code(json_str, language='json')
        
        with json_tabs[1]:
            compact_json = json.dumps(summary_info, ensure_ascii=False, separators=(',', ':'))
            text_area("原始JSON", compact_json, height=200)
        
            # JSON下載
            download_button(label="📥 下載Summary信息爲JSON", data=json.dumps(summary_info, ensure_ascii=False, indent=2), file_name=f"{summary_info['sheet_name']}_summary.json", mime="application/json")

# 主應用邏輯
sidebar.title("📁 文件選擇")

# 文件上傳或目錄選擇
with sidebar:
  analysis_mode = radio("選擇分析模式:", ["上傳單個文件", "分析目錄下所有文件"], horizontal=True, index=1)

if analysis_mode == "上傳單個文件":
    uploaded_file = sidebar.file_uploader("選擇Excel文件", type=["xlsx", "xls"])
    files_to_process = [uploaded_file] if uploaded_file else []
else:
    #directory_path = sidebar.text_input("目錄路徑(留空使用當前目錄):", ".")
    #if sidebar.button("掃描Excel文件"):
        #excel_files = get_excel_files(directory_path)
        #selected_files = sidebar.multiselect("選擇要分析的文件:", excel_files)
        #files_to_process = [os.path.join(directory_path, f) for f in selected_files]
    with sidebar:
      目錄 = radio("目錄路徑(留空使用當前目錄):", ["TDRReportRawData", 'TDR_Fail'], horizontal=True, key=0)  #sidebar.text_input
      XLSX = get_excel_files(目錄)
      #code(['excel_files', excel_files])
      selected_files = radio("選擇要分析的文件:", XLSX, horizontal=True, key=1)  #sidebar.multiselect

if XLSX:
    # 創建標簽頁用于不同文件
    分頁 = tabs(XLSX)
    #file_tabs = tabs([os.path.basename(f.name) if hasattr(f, 'name') else os.path.basename(f) for f in files_to_process])
    
    for file_idx, file_path in enumerate(XLSX):
        fullPath=f'{目錄}/{file_path}'
        with 分頁[file_idx]:
            try:
                # 讀取Excel文件
                if hasattr(file_path, 'getvalue'):  # 上傳的文件
                    excel_file = ExcelFile(fullPath)
                    file_name = file_path.name
                else:  # 本地文件
                    excel_file = ExcelFile(fullPath)
                    file_name = os.path.basename(fullPath)
                
                sheet_names = excel_file.sheet_names
                
                header(f"文件: {file_name}")
                write(f"包含 {len(sheet_names)} 個工作表: {', '.join(sheet_names)}")
                
                # 爲每個sheet創建子標簽頁
                sheet_tabs = tabs([f"📊 {sheet}" for sheet in sheet_names])
                
                for sheet_idx, sheet_name in enumerate(sheet_names):
                    with sheet_tabs[sheet_idx]:
                        try:
                            # 讀取sheet數據
                            df = read_excel(excel_file, sheet_name=sheet_name)
                            
                            if df.empty:
                                warning(f"工作表 '{sheet_name}' 爲空")
                                continue
                            
                            # 如果是Summary sheet，使用專門的提取函數
                            if 'summary' in sheet_name.lower():
                                summary_info = extract_summary_info(df, sheet_name)
                                display_summary_info(summary_info)
                            else:
                                # 對于其他sheet，使用原來的分析流程
                                info(f"正在分析工作表: {sheet_name}")
                                
                                # 分析數據結構
                                analysis, df_clean = analyze_sheet_structure(df, sheet_name)
                                
                                # 顯示基本信息
                                col1, col2, col3, col4 = columns(4)
                                with col1:
                                    metric("行數", analysis['shape'][0])
                                with col2:
                                    metric("列數", analysis['shape'][1])
                                with col3:
                                    metric("數值列", len(analysis['numeric_columns']))
                                with col4:
                                    metric("文本列", len(analysis['text_columns']))
                                
                                # 顯示數據結構信息
                                with expander("數據結構詳情"):
                                    write("**數值列:**", analysis['numeric_columns'])
                                    write("**文本列:**", analysis['text_columns'])
                                    if analysis['potential_x_column']:
                                        write("**建議X軸:**", analysis['potential_x_column'])
                                    if analysis['potential_y_columns']:
                                        write("**建議Y軸:**", analysis['potential_y_columns'])
                                
                                # 創建可視化
                                visualizations = create_visualizations(df_clean, analysis, sheet_name)
                                
                                if visualizations:
                                    # 爲每個可視化創建子標簽頁
                                    viz_tabs = tabs([viz[0] for viz in visualizations])
                                    
                                    for viz_idx, (viz_name, viz_fig) in enumerate(visualizations):
                                        with viz_tabs[viz_idx]:
                                            plotly_chart(viz_fig, use_container_width=True)
                                else:
                                    info("未找到足夠的數據創建可視化圖表")
                                
                                # 顯示數據預覽
                                with expander("數據預覽"):
                                    dataframe(df_clean.head(20), use_container_width=True)
                                    
                                    # 數據統計
                                    subheader("數據統計")
                                    if analysis['numeric_columns']:
                                        numeric_stats = df_clean[analysis['numeric_columns']].apply(
                                            lambda x: to_numeric(x.astype(str).str.strip().replace('', np.nan), errors='coerce')
                                        ).describe()
                                        dataframe(numeric_stats, use_container_width=True)
                                
                                # 數據下載
                                subheader("數據導出")
                                csv_data = df_clean.to_csv(index=False).encode('utf-8')
                                
                                download_button( label=f"📥 下載 {sheet_name} 數據爲CSV", data=csv_data, file_name=f"{file_name}_{sheet_name}.csv", mime="text/csv")
                            
                        except Exception as e:
                            error(f"處理工作表 '{sheet_name}' 時出錯: {str(e)}")
                
            except Exception as e:
                error(f"讀取文件時出錯: {str(e)}")

else:
    # 顯示使用說明
    info("👆 請選擇要分析的Excel文件")
    
    with expander("📖 使用說明"):
        markdown("""
        ### 🎯 功能特性：
        
        **Summary分頁專門處理**:
        - 自動提取廠商信息（Project, Equipment, Version等）
        - 識別測試結果統計（PASS/FAIL計數）
        - 顯示詳細測試項目列表
        - 數據框格式展示
        
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
        
        ### 📊 Summary分頁支持的信息：
        - 廠商和設備信息
        - 測試配置和版本信息
        - 測試時間信息
        - 測試結果統計
        - 詳細測試項目列表
        """)
