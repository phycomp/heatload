import streamlit as st
from 阻抗模型 import ImpedanceModel
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import re

# 設置頁面
st.set_page_config(
    page_title="TDR與阻抗匹配分析",
    page_icon="📡",
    layout="wide"
)

# 標題和說明
st.title("📡 TDR與阻抗匹配分析系統")
st.markdown("""
這個應用使用PyTorch分析TDR（時域反射計）測量數據，并提供阻抗匹配建議。
上傳您的TDR數據文件或使用示例數據進行測試。
""")


# 模藕TDR數據生成
def generate_sample_tdr_data():
    """生成示例TDR數據"""
    time = np.linspace(0, 10, 1000)
    
    # 模藕TDR響應 - 包含幾個阻抗不連續點
    impedance = np.ones_like(time) * 50  # 基準阻抗50歐姆
    
    # 添加阻抗變化
    impedance[200:300] = 75  # 高阻抗區域
    impedance[500:600] = 30  # 低阻抗區域
    impedance[700:800] = 60  # 另一個高阻抗區域
    
    # 添加噪聲
    noise = np.random.normal(0, 2, size=impedance.shape)
    impedance += noise
    
    # 創建DataFrame
    df = pd.DataFrame({
        'Time (ns)': time,
        'Impedance (Ohms)': impedance,
        'Reflection Coefficient': (impedance - 50) / (impedance + 50)
    })
    
    return df

# 分析TDR數據
def analyze_tdr_data(df):
    """分析TDR數據并識別阻抗不連續點"""
    impedance = df['Impedance (Ohms)'].values
    time = df['Time (ns)'].values
    
    # 尋找阻抗變化點
    diff = np.diff(impedance)
    threshold = np.std(diff) * 2
    
    # 識別顯著變化點
    change_points = np.where(np.abs(diff) > threshold)[0]
    
    # 分析每個變化點
    analysis = []
    for i, point in enumerate(change_points):
        if i == 0:
            prev_imp = impedance[0]
        else:
            prev_imp = impedance[change_points[i-1]]
        
        current_imp = impedance[point]
        delta_z = current_imp - prev_imp
        gamma = (current_imp - 50) / (current_imp + 50)
        
        analysis.append({
            '位置點': point,
            '時間(ns)': time[point],
            '阻抗變化(Ω)': delta_z,
            '反射系數': gamma,
            '類型': '高阻抗' if delta_z > 0 else '低阻抗'
        })
    
    return pd.DataFrame(analysis)

# 阻抗匹配建議
def get_matching_recommendations(analysis_df):
    """根據分析結果提供阻抗匹配建議"""
    recommendations = []
    
    for _, row in analysis_df.iterrows():
        imp_change = row['阻抗變化(Ω)']
        gamma = row['反射系數']
        
        if abs(gamma) < 0.1:
            rec = f"在 {row['時間(ns)']:.2f} ns 處的阻抗變化較小，無需特殊匹配。"
        elif imp_change > 0:
            rec = f"在 {row['時間(ns)']:.2f} ns 處檢測到高阻抗({imp_change:.1f}Ω)。建議使用串聯電感或并聯電容進行匹配。"
        else:
            rec = f"在 {row['時間(ns)']:.2f} ns 處檢測到低阻抗({imp_change:.1f}Ω)。建議使用串聯電容或并聯電感進行匹配。"
        
        recommendations.append(rec)
    
    return recommendations

# 側邊欄
st.sidebar.header("數據輸入選項")

data_source = st.sidebar.radio(
    "選擇數據源:",
    ["使用示例數據", "上傳CSV文件"]
)

df = None

if data_source == "上傳CSV文件":
    uploaded_file = st.sidebar.file_uploader("上傳TDR數據CSV文件", type=["csv"])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.sidebar.success("文件上傳成功!")
        except Exception as e:
            st.sidebar.error(f"文件讀取錯誤: {e}")
else:
    df = generate_sample_tdr_data()
    st.sidebar.info("使用示例TDR數據")

# 主界面
if df is not None:
    # 顯示數據
    st.subheader("TDR數據預覽")
    st.dataframe(df.head(10))
    
    # 繪制TDR曲線
    st.subheader("TDR阻抗曲線")
    
    fig = make_subplots(rows=2, cols=1, 
                        subplot_titles=('阻抗 vs 時間', '反射系數 vs 時間'),
                        vertical_spacing=0.1)
    
    fig.add_trace(
        go.Scatter(x=df['Time (ns)'], y=df['Impedance (Ohms)'], 
                  mode='lines', name='阻抗', line=dict(color='blue')),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=df['Time (ns)'], y=df['Reflection Coefficient'], 
                  mode='lines', name='反射系數', line=dict(color='red')),
        row=2, col=1
    )
    
    fig.update_xaxes(title_text="時間 (ns)", row=2, col=1)
    fig.update_yaxes(title_text="阻抗 (Ω)", row=1, col=1)
    fig.update_yaxes(title_text="反射系數", row=2, col=1)
    fig.update_layout(height=600)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 分析數據
    st.subheader("阻抗不連續點分析")
    
    if st.button("分析TDR數據"):
        with st.spinner("分析中..."):
            analysis_df = analyze_tdr_data(df)
            
            if not analysis_df.empty:
                st.dataframe(analysis_df)
                
                # 顯示匹配建議
                st.subheader("阻抗匹配建議")
                recommendations = get_matching_recommendations(analysis_df)
                
                for i, rec in enumerate(recommendations):
                    st.info(f"{i+1}. {rec}")
            else:
                st.success("未檢測到顯著的阻抗不連續點。傳輸線匹配良好。")
    
    # 模型訓練部分
    st.subheader("PyTorch模型訓練")
    
    st.markdown("""
    下面演示如何使用PyTorch創建一個簡單的語言模型來處理阻抗相關的文本數據。
    這個模型可以學習阻抗匹配規則和模式。
    """)
    
    # 模藕訓練數據
    vocab = {
        '<PAD>': 0, '<UNK>': 1, '阻抗': 2, '匹配': 3, '電容': 4, '電感': 5,
        '串聯': 6, '并聯': 7, '高': 8, '低': 9, '反射': 10, '系數': 11,
        '傳輸線': 12, '50': 13, '75': 14, 'Ω': 15, '建議': 16
    }
    
    # 示例訓練句子
    training_sentences = [
        "高 阻抗 建議 串聯 電感",
        "低 阻抗 建議 并聯 電感",
        "阻抗 匹配 使用 電容 和 電感",
        "反射 系數 高 需要 匹配",
        "傳輸線 阻抗 50 Ω 匹配"
    ]
    
    # 轉換爲索引序列
    def text_to_sequence(text, vocab):
        tokens = text.split()
        return [vocab.get(token, vocab['<UNK>']) for token in tokens]
    
    # 準備訓練數據
    sequences = [text_to_sequence(sent, vocab) for sent in training_sentences]
    
    # 填充序列到相同長度
    max_len = max(len(seq) for seq in sequences)
    padded_sequences = []
    for seq in sequences:
        padded_seq = seq + [vocab['<PAD>']] * (max_len - len(seq))
        padded_sequences.append(padded_seq)
    
    # 轉換爲PyTorch張量
    input_data = torch.tensor(padded_sequences, dtype=torch.long)
    
    # 初始化模型
    vocab_size = len(vocab)
    embedding_dim = 16
    hidden_dim = 32
    output_dim = 10  # 假設的輸出維度
    
    model = ImpedanceModel(vocab_size, embedding_dim, hidden_dim, output_dim)
    
    # 模藕訓練過程
    if st.button("訓練模型"):
        with st.spinner("訓練模型中..."):
            # 模藕訓練過程
            criterion = nn.MSELoss()
            optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
            
            # 模藕訓練循環
            progress_bar = st.progress(0)
            loss_values = []
            
            for epoch in range(100):
                optimizer.zero_grad()
                outputs = model(input_data)
                loss = criterion(outputs, torch.randn(len(training_sentences), output_dim))
                loss.backward()
                optimizer.step()
                
                loss_values.append(loss.item())
                
                if epoch % 20 == 0:
                    progress_bar.progress((epoch + 1) / 100)
            
            progress_bar.progress(100)
            
            # 顯示訓練損失
            fig_loss = go.Figure()
            fig_loss.add_trace(go.Scatter(
                x=list(range(len(loss_values))),
                y=loss_values,
                mode='lines',
                name='訓練損失'
            ))
            fig_loss.update_layout(
                title="訓練損失曲線",
                xaxis_title="迭代次數",
                yaxis_title="損失值"
            )
            
            st.plotly_chart(fig_loss, use_container_width=True)
            
            st.success("模型訓練完成!")
    
    # 阻抗計算工具
    st.subheader("阻抗計算工具")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**反射系數計算**")
        z_l = st.number_input("負載阻抗 Z_L (Ω)", value=75.0, min_value=1.0, max_value=1000.0)
        z_0 = st.number_input("特性阻抗 Z_0 (Ω)", value=50.0, min_value=1.0, max_value=1000.0)
        
        gamma = (z_l - z_0) / (z_l + z_0)
        swr = (1 + abs(gamma)) / (1 - abs(gamma)) if abs(gamma) != 1 else float('inf')
        
        st.write(f"反射系數 Γ: {gamma:.4f}")
        st.write(f"駐波比 SWR: {swr:.4f}")
    
    with col2:
        st.markdown("**阻抗匹配網絡**")
        matching_type = st.selectbox(
            "匹配網絡類型",
            ["L型網絡", "π型網絡", "T型網絡"]
        )
        
        freq = st.number_input("工作頻率 (MHz)", value=100.0, min_value=0.1, max_value=10000.0)
        
        if st.button("計算匹配元件值"):
            # 簡化的匹配計算
            omega = 2 * np.pi * freq * 1e6
            
            if matching_type == "L型網絡":
                # 簡化計算
                l_value = 1 / (omega * 0.01)  # 簡化計算
                c_value = 1 / (omega * 100)   # 簡化計算
                
                st.write(f"建議電感值: {l_value*1e9:.2f} nH")
                st.write(f"建議電容值: {c_value*1e12:.2f} pF")
            else:
                st.info("該匹配網絡計算需要更復雜的參數。")

else:
    st.info("請上傳TDR數據文件或使用示例數據開始分析。")

# 底部信息
st.markdown("---")
st.markdown("""
### 關于此應用
- **TDR分析**: 識別傳輸線中的阻抗不連續點
- **阻抗匹配**: 提供基于分析結果的匹配建議
- **PyTorch模型**: 演示如何使用深度學習處理阻抗相關數據
- **計算工具**: 提供基本的阻抗和反射系數計算

使用此應用可以快速分析TDR測量數據，識別問題區域，并獲得阻抗匹配建議。
""")
