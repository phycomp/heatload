from streamlit import button, cache_data, cache_resource, columns, dataframe, error, expander, image, info, markdown, metric as 量測, multiselect, plotly_chart, radio, set_page_config, sidebar, slider, success, tabs, text_area, warning, write, secrets, empty
from psycopg import connect as pgCnnct
from numpy import argmax, argmin, clip, interp, linspace, log10, mean, zeros
from pandas import DataFrame, read_sql
from plotly.graph_objects import Bar, Figure, Heatmap, Scatter, Scatterpolar
# quantum_transmission_simulator.py
#import streamlit as st
#import psycopg
#import pandas as pd
#import numpy as np
#import plotly.graph_objects as go
#plotly.express import barmode
from plotly.subplots import make_subplots
import scipy.signal as signal
from datetime import datetime

# 頁面配置
set_page_config(
    page_title="量子傳輸線模擬器",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義CSS
markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .warning-text {
        color: #e74c3c;
        font-weight: bold;
    }
    .success-text {
        color: #27ae60;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# 數據庫連接
# ============================================

scrt=secrets['uleam']
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "quantum_db",
    "user": "postgres",
    "password": "your_password"
}

#@cache_resource
def get_db_connection():
    """獲取數據庫連接"""
    try:
        conn = pgCnnct(**scrt)
        return conn
    except Exception as e:
        error(f"數據庫連接失敗: {e}")
        return None

@cache_data(ttl=3600)
def load_vendors():
    """加載供應商列表"""
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, technology, country FROM vendors ORDER BY name")
            vendors = cur.fetchall()
            conn.close()
            return vendors
    return []

@cache_data(ttl=3600)
def load_transmission_lines(vendor_id=None):
    """加載傳輸線產品"""
    conn = get_db_connection()
    if conn:
        query = """
            SELECT 
                t.id, t.product_name, t.product_series,
                t.impedance, t.frequency_max, t.insertion_loss,
                t.crosstalk_typical, t.pitch, t.height,
                t.material_conductor, t.is_superconducting,
                t.shielding_effectiveness, v.name as vendor_name
            FROM transmission_lines t
            JOIN vendors v ON t.vendor_id = v.id
        """
        if vendor_id:
            query += f" WHERE v.id = {vendor_id}"
        query += " ORDER BY v.name, t.product_name"
        
        df = read_sql(query, conn)
        conn.close()
        return df
    return DataFrame()

@cache_data(ttl=3600)
def load_frequency_response(product_id):
    """加載特定產品的頻率響應"""
    conn = get_db_connection()
    if conn:
        query = """
            SELECT frequency_ghz, s11_db, s21_db, s31_db, s41_db, 
                   phase_deg, group_delay_ps, measurement_temp
            FROM frequency_characteristics
            WHERE transmission_line_id = %s
            ORDER BY frequency_ghz
        """
        df = read_sql(query, conn, params=(product_id,))
        conn.close()
        return df
    return DataFrame()

# ============================================
# 物理計算引擎
# ============================================

class TransmissionLineSimulator:
    """傳輸線模擬器"""
    
    def __init__(self, product_data, freq_response):
        self.product = product_data
        self.freq_response = freq_response
        self.c = 299792458  # 光速 (m/s)
        
    def calculate_insertion_loss(self, frequency_ghz, length_m):
        """計算插入損耗"""
        if not self.freq_response.empty and 's21_db' in self.freq_response.columns:
            # 使用實測數據插值
            s21_interp = interp(frequency_ghz, self.freq_response['frequency_ghz'], self.freq_response['s21_db'])
            loss_db = s21_interp * length_m # 按長度縮放 (dB 與長度成正比)
        else:
            loss_db = self.product['insertion_loss'] * length_m * (frequency_ghz / 1e9) ** 0.5 # 使用近似模型
        return loss_db
    
    def calculate_crosstalk(self, frequency_ghz, length_m):
        """計算串擾 (遠端串擾 FEXT)"""
        if not self.freq_response.empty and 's31_db' in self.freq_response.columns:
            # 使用實測串擾數據
            xtalk_interp = interp(frequency_ghz, self.freq_response['frequency_ghz'], self.freq_response['s31_db'])
            xtalk_db = xtalk_interp + 10 * log10(length_m) # 串擾隨長度增加而增加 (按對數比例)
        else:
            # 基于物理參數的近似模型
            pitch_m = self.product['pitch'] / 1000
            freq_hz = frequency_ghz * 1e9
            
            # 耦合系數計算
            if self.product['is_superconducting']:
                coupling_factor = 0.05 * (1 / (pitch_m ** 1.5))
            else:
                coupling_factor = 0.15 * (1 / (pitch_m ** 2))
            
            freq_dep = (freq_hz / 1e9) ** 0.8 # 頻率依賴性
            
            shielding = self.product.get('shielding_effectiveness', 60) / 60 # 屏蔽效能
            
            # 串擾計算 (dB)
            xtalk_linear = coupling_factor * freq_dep * length_m / shielding
            xtalk_db = -20 * log10(max(xtalk_linear, 0.001))
            
        return clip(xtalk_db, -70, -10)
    
    def calculate_return_loss(self, frequency_ghz):
        """計算回波損耗"""
        if not self.freq_response.empty and 's11_db' in self.freq_response.columns:
            return interp(frequency_ghz,
                           self.freq_response['frequency_ghz'],
                           self.freq_response['s11_db'])
        else:
            # 基于阻抗匹配的近似
            vswr = 1.2 + 0.1 * (frequency_ghz / self.product['frequency_max'])
            rl_db = -20 * log10((vswr - 1) / (vswr + 1))
            return rl_db
    
    def calculate_group_delay(self, frequency_ghz):
        """計算群延遲"""
        if not self.freq_response.empty and 'group_delay_ps' in self.freq_response.columns:
            return interp(frequency_ghz,
                           self.freq_response['frequency_ghz'],
                           self.freq_response['group_delay_ps'])
        else:
            # 近似群延遲 (ps/m)
            velocity_factor = 0.7 if not self.product['is_superconducting'] else 0.95
            delay_ps_m = 1000 * 1000 / (self.c * velocity_factor) * 1e12
            return delay_ps_m
    
    def calculate_snr(self, frequency_ghz, length_m, input_power_dbm=-20):
        """計算信噪比"""
        loss_db = self.calculate_insertion_loss(frequency_ghz, length_m)
        xtalk_db = self.calculate_crosstalk(frequency_ghz, length_m)
        
        # 噪聲基底 (熱噪聲)
        noise_floor = -174 + 10 * log10(1e6)  # -114 dBm @ 1MHz BW
        noise_floor = -114
        
        # 考慮串擾作爲干擾
        interference = xtalk_db + input_power_dbm
        
        # 輸出信號功率
        output_power = input_power_dbm - loss_db
        
        # SNR
        snr = output_power - max(noise_floor, interference)
        return snr

# ============================================
# 可視化函數
# ============================================

def plot_frequency_response(freqs, insertion_loss, crosstalk, return_loss):
    """繪制頻率響應圖"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('插入損耗 (S21)', '串擾 (S31/FEXT)',
                       '回波損耗 (S11)', '群延遲'),
        vertical_spacing=0.12
    )
    
    # 插入損耗
    fig.add_trace(
        Scatter(x=freqs, y=insertion_loss, mode='lines+markers',
                  name='插入損耗', line=dict(color='red', width=2),
                  marker=dict(size=6)),
        row=1, col=1
    )
    fig.update_yaxes(title_text="損耗 (dB)", row=1, col=1)
    
    # 串擾
    fig.add_trace(
        Scatter(x=freqs, y=crosstalk, mode='lines+markers',
                  name='串擾', line=dict(color='blue', width=2),
                  marker=dict(size=6)),
        row=1, col=2
    )
    fig.update_yaxes(title_text="串擾 (dB)", row=1, col=2)
    
    # 回波損耗
    fig.add_trace(
        Scatter(x=freqs, y=return_loss, mode='lines+markers',
                  name='回波損耗', line=dict(color='green', width=2),
                  marker=dict(size=6)),
        row=2, col=1
    )
    fig.update_yaxes(title_text="回波損耗 (dB)", row=2, col=1)
    fig.update_xaxes(title_text="頻率 (GHz)", row=2, col=1)
    
    fig.update_yaxes(title_text="群延遲 (ps)", row=2, col=2) # 群延遲 (如果有數據)
    fig.update_xaxes(title_text="頻率 (GHz)", row=2, col=2)
    
    fig.update_layout(height=800, showlegend=True,
                     title_text="傳輸線頻率響應特性")
    
    return fig

def plot_crosstalk_heatmap(freqs, lengths, crosstalk_matrix):
    """繪制串擾熱力圖"""
    fig = Figure(data=Heatmap(
        z=crosstalk_matrix,
        x=freqs,
        y=lengths,
        colorscale='RdYlBu_r',
        zmin=-60, zmax=-15,
        colorbar=dict(title="串擾 (dB)")
    ))
    
    fig.update_layout(
        title="串擾 vs 頻率 & 長度",
        xaxis_title="頻率 (GHz)",
        yaxis_title="長度 (m)",
        height=500
    )
    
    return fig

def plot_vendor_comparison(vendor_data, metric='insertion_loss'):
    """繪制供應商對比圖"""
    metrics_map = {
        'insertion_loss': '插入損耗 (dB/m @ 6GHz)',
        'crosstalk': '串擾 (dB @ 6GHz)',
        'frequency_max': '最高頻率 (GHz)',
        'pitch': '間距 (mm)'
    }
    
    fig = Figure()
    
    for vendor in vendor_data['vendor_name'].unique():
        vendor_df = vendor_data[vendor_data['vendor_name'] == vendor]
        
        if metric == 'insertion_loss':
            values = vendor_df['insertion_loss']
            text = [f"{v:.2f} dB/m" for v in values]
        elif metric == 'crosstalk':
            values = vendor_df['crosstalk_typical']
            text = [f"{v:.0f} dB" for v in values]
        elif metric == 'frequency_max':
            values = vendor_df['frequency_max']
            text = [f"{v:.1f} GHz" for v in values]
        else:
            values = vendor_df['pitch']
            text = [f"{v:.2f} mm" for v in values]
        
        fig.add_trace(Bar(
            name=vendor,
            x=vendor_df['product_name'],
            y=values,
            text=text,
            textposition='auto',
            marker_color=['#1f77b4' if not sc else '#ff7f0e' 
                         for sc in vendor_df['is_superconducting']]
        ))
    
    fig.update_layout(
        title=f"供應商性能對比 - {metrics_map[metric]}",
        xaxis_title="產品型號",
        yaxis_title=metrics_map[metric],
        barmode='group',
        height=500,
        showlegend=True
    )
    
    return fig

# ============================================
# 主應用
# ============================================

def main():
    markdown('<div class="main-header">🔬 量子傳輸線模擬器</div>', 
                unsafe_allow_html=True)
    markdown('### 六家供應商 · 頻率響應 · 串擾計算')
    
    # 側邊欄
    with sidebar:
        image("https://img.icons8.com/fluency/96/quantum-computing.png", width=80)
        markdown("## 參數配置")
        
        # 供應商選擇
        vendors = load_vendors()
        if not vendors:
            error("無法加載供應商數據，請檢查數據庫連接")
            return
        
        vendor_names = [f"{v[1]} ({v[2]})" for v in vendors]
        selected_vendor_idx = radio("選擇供應商", range(len(vendor_names)), format_func=lambda x: vendor_names[x], horizontal=True)
        selected_vendor = vendors[selected_vendor_idx]
        
        # 產品選擇
        products_df = load_transmission_lines(selected_vendor[0])
        if products_df.empty:
            warning(f"沒有找到 {selected_vendor[1]} 的產品數據")
            return
        
        product_names = products_df['product_name'].tolist()
        selected_product = radio("選擇產品型號", product_names, horizontal=True)
        product_data = products_df[products_df['product_name'] == selected_product].iloc[0]
        
        markdown("---")
        markdown("### 模擬參數")
        
        # 模擬參數
        length = slider("傳輸線長度 (m)", 0.1, 2.0, 0.5, 0.05,
                          help="信號傳輸距離，影響損耗和串擾")
        
        freq_range = slider("頻率範圍 (GHz)", 0.1, 50.0, (0.1, 12.0),
                              help="掃描頻率範圍")
        
        input_power = slider("輸入功率 (dBm)", -30, 10, -20,
                               help="輸入信號功率")
        
        temperature = slider("工作溫度 (K)", 0.01, 300.0, 4.0, help="低溫環境溫度")
        
        markdown("---")
        markdown("### 產品信息")
        info(f"""
        **{product_data['product_name']}**
        - 供應商: {product_data['vendor_name']}
        - 技術: {"🔬 超導" if product_data['is_superconducting'] else "🔌 常溫"}
        - 阻抗: {product_data['impedance']} Ω
        - 最高頻率: {product_data['frequency_max']} GHz
        - 間距: {product_data['pitch']} mm
        - 材料: {product_data['material_conductor']}
        """)
    
    # 主內容區域
    tab1, tab2, tab3, tab4 = tabs(["📊 頻率響應模擬", "🔀 串擾分析", 
                                      "📈 供應商對比", "📋 技術規格"])
    
    freq_response = load_frequency_response(product_data['id']) # 加載頻率響應數據
    
    simulator = TransmissionLineSimulator(product_data, freq_response) # 創建模擬器
    
    freqs = linspace(freq_range[0], freq_range[1], 100) # 頻率點
    
    insertion_loss = [simulator.calculate_insertion_loss(f, length) for f in freqs] # 計算各項參數
    crosstalk = [simulator.calculate_crosstalk(f, length) for f in freqs]
    return_loss = [simulator.calculate_return_loss(f) for f in freqs]
    snr = [simulator.calculate_snr(f, length, input_power) for f in freqs]
    
    狀態=empty()
    狀態.code([freqs])
    with tab1:
        markdown('<div class="sub-header">📡 頻率響應特性</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = columns(4)
        
        with col1:
            量測("最低插入損耗", f"{insertion_loss[0]:.2f} dB", delta=f"@{freqs[0]:.1f}GHz")
        with col2:
            量測("最高插入損耗", f"{insertion_loss[-1]:.2f} dB", delta=f"@{freqs[-1]:.1f}GHz", delta_color="inverse")
        with col3:
            量測("最佳串擾", f"{crosstalk[argmax(crosstalk)]:.1f} dB")
        with col4:
          量測("最差串擾", f"{crosstalk[argmin(crosstalk)]:.1f} dB", delta_color="inverse")
        
        # 頻率響應圖
        fig = plot_frequency_response(freqs, insertion_loss, crosstalk, return_loss)
        plotly_chart(fig, use_container_width=True)
        
        # SNR分析
        markdown("### 📶 信噪比分析")
        fig_snr = Figure()
        fig_snr.add_trace(Scatter(x=freqs, y=snr, mode='lines+markers',
                                     name='SNR', line=dict(color='purple', width=2)))
        fig_snr.add_hline(y=20, line_dash="dash", line_color="green",
                         annotation_text="良好 SNR 阈值")
        fig_snr.add_hline(y=10, line_dash="dash", line_color="orange",
                         annotation_text="最小 SNR 阈值")
        fig_snr.update_layout(xaxis_title="頻率 (GHz)", yaxis_title="SNR (dB)",
                             height=400)
        plotly_chart(fig_snr, use_container_width=True)
    
    with tab2:
        markdown('<div class="sub-header">🔀 串擾深度分析</div>', 
                    unsafe_allow_html=True)
        
        col1, col2 = columns([1, 1])
        
        with col1:
            # 串擾 vs 頻率 (不同長度)
            markdown("#### 不同長度的串擾特性")
            fig_xtalk_len = Figure()
            for test_len in [0.2, 0.5, 1.0, 1.5]:
                xtalk_len = [simulator.calculate_crosstalk(f, test_len) for f in freqs]
                fig_xtalk_len.add_trace(Scatter(x=freqs, y=xtalk_len,
                                                   name=f'{test_len}m'))
            fig_xtalk_len.update_layout(xaxis_title="頻率 (GHz)", 
                                        yaxis_title="串擾 (dB)",
                                        height=400)
            plotly_chart(fig_xtalk_len, use_container_width=True)
        
        with col2:
            # 串擾熱力圖
            markdown("#### 串擾熱力圖")
            test_lengths = linspace(0.1, 2.0, 20)
            test_freqs = linspace(freq_range[0], freq_range[1], 30)
            xtalk_matrix = zeros((len(test_lengths), len(test_freqs)))
            
            for i, l in enumerate(test_lengths):
                for j, f in enumerate(test_freqs):
                    xtalk_matrix[i, j] = simulator.calculate_crosstalk(f, l)
            
            fig_heat = plot_crosstalk_heatmap(test_freqs, test_lengths, xtalk_matrix)
            plotly_chart(fig_heat, use_container_width=True)
        
        # 串擾阈值分析
        markdown("#### 串擾性能評估")
        
        # 計算關鍵頻率點的串擾
        critical_freqs = [1, 2, 4, 6, 8, 10]
        critical_freqs = [f for f in critical_freqs if freq_range[0] <= f <= freq_range[1]]
        
        xtalk_at_freqs = [simulator.calculate_crosstalk(f, length) for f in critical_freqs]
        
        xtalk_df = DataFrame({
            '頻率 (GHz)': critical_freqs,
            '串擾 (dB)': [f"{x:.1f}" for x in xtalk_at_freqs],
            '性能評級': ['優秀' if x < -35 else '良好' if x < -25 else '需改進' 
                       for x in xtalk_at_freqs]
        })
        
        dataframe(xtalk_df, use_container_width=True)
        
        # 串擾改善建議
        avg_xtalk = mean(crosstalk)
        if avg_xtalk < -35:
            success("✅ 串擾性能優秀，適合高密度量子比特布線")
        elif avg_xtalk < -25:
            info("ℹ️ 串擾性能良好，建議配合濾波電路使用")
        else:
            warning("⚠️ 串擾較高，建議增加間距或使用屏蔽更好的產品")
    
    with tab3:
        markdown('<div class="sub-header">📊 六家供應商性能對比</div>', 
                    unsafe_allow_html=True)
        
        all_products = load_transmission_lines()
        
        metric = radio("選擇對比指標", ['insertion_loss', 'crosstalk', 'frequency_max', 'pitch'], format_func=lambda x: {'insertion_loss':'插入損耗', 'crosstalk':'串擾', 'frequency_max':'最高頻率', 'pitch':'間距'}[x], horizontal=True) # 對比指標選擇
        
        fig_compare = plot_vendor_comparison(all_products, metric)
        plotly_chart(fig_compare, use_container_width=True)
        
        # 雷達圖對比
        markdown("#### 綜合性能雷達圖")
        
        # 選擇要對比的產品
        compare_products = multiselect("選擇要對比的產品", 
                                         all_products['product_name'].tolist(),
                                         default=all_products['product_name'].tolist()[:3])
        
        if compare_products:
            # 歸一化指標
            categories = ['插入損耗', '串擾', '最高頻率', '間距', '屏蔽效能']
            
            fig_radar = Figure()
            
            for prod_name in compare_products:
                prod = all_products[all_products['product_name'] == prod_name].iloc[0]
                
                # 歸一化處理 (損耗和串擾越小越好，取倒數)
                values = [
                    min(20 / max(prod['insertion_loss'], 0.1), 10),  # 插入損耗
                    min(50 / max(-prod['crosstalk_typical'], 5), 10),  # 串擾 (取負值)
                    prod['frequency_max'] / 10,  # 最高頻率
                    max(5 / max(prod['pitch'], 0.1), 0.5),  # 間距 (越小越好)
                    prod['shielding_effectiveness'] / 10  # 屏蔽效能
                ]
                
                fig_radar.add_trace(Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name=prod_name
                ))
            
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
                showlegend=True,
                height=500
            )
            plotly_chart(fig_radar, use_container_width=True)
    
    with tab4:
        markdown('<div class="sub-header">📋 技術規格書</div>', 
                    unsafe_allow_html=True)
        
        col1, col2 = columns(2)
        
        with col1:
            markdown("#### 電氣參數")
            electrical_params = DataFrame({
                '參數': ['阻抗', '最高頻率', '插入損耗', '回波損耗', '串擾', 'VSWR'],
                '數值': [
                    f"{product_data['impedance']} Ω",
                    f"{product_data['frequency_max']} GHz",
                    f"{product_data['insertion_loss']} dB/m",
                    f"{product_data.get('return_loss', 'N/A')} dB",
                    f"{product_data['crosstalk_typical']} dB",
                    f"{product_data.get('vswr', '1.2')}"
                ]
            })
            dataframe(electrical_params, use_container_width=True)
            
            markdown("#### 機械參數")
            mechanical_params = DataFrame({
                '參數': ['間距', '高度/直徑', '最小彎曲半徑', '重量'],
                '數值': [
                    f"{product_data['pitch']} mm",
                    f"{product_data['height']} mm",
                    f"{product_data.get('bend_radius_min', 'N/A')} mm",
                    f"{product_data.get('weight_per_meter', 'N/A')} g/m"
                ]
            })
            dataframe(mechanical_params, use_container_width=True)
        
        with col2:
            markdown("#### 材料參數")
            material_params = DataFrame({
                '參數': ['導體材料', '介質材料', '屏蔽材料', '超導特性'],
                '數值': [
                    product_data['material_conductor'],
                    product_data.get('material_dielectric', 'N/A'),
                    product_data.get('material_shield', 'N/A'),
                    '是' if product_data['is_superconducting'] else '否'
                ]
            })
            dataframe(material_params, use_container_width=True)
            
            markdown("#### 環境參數")
            狀態.code([product_data])
            env_params = DataFrame({
                '參數': ['屏蔽效能', '應用領域'],   #'工作溫度', '功率處理', 
                '數值': [
                    #f"{product_data['operating_temp_min']} - {product_data['operating_temp_max']} K",
                    #f"{product_data['power_handling']} W",
                    f"{product_data['shielding_effectiveness']} dB",
                    product_data.get('application', '通用')
                ]
            })
            env_params
            dataframe(env_params, width='stretch')
        
        # 頻率響應數據表
        markdown("#### 頻率響應數據")
        if not freq_response.empty:
            dataframe(freq_response.round(2), use_container_width=True)
        else:
            info("該產品暫無詳細頻率響應數據")
    
    # 保存模擬結果
    with expander("💾 保存模擬結果"):
        col1, col2 = columns([3, 1])
        with col1:
            notes = text_area("實驗備注", "量子傳輸線性能評估")
        with col2:
            write("")
            write("")
            if button("保存到數據庫", type="primary"):
                try:
                    conn = get_db_connection()
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO simulation_logs 
                            (transmission_line_id, frequency_start_ghz, frequency_end_ghz,
                             length_m, temperature_k, calculated_crosstalk_db,
                             calculated_loss_db, simulation_notes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (product_data['id'], freq_range[0], freq_range[1],
                              length, temperature, mean(crosstalk),
                              mean(insertion_loss), notes))
                        conn.commit()
                    success("模擬結果已保存到數據庫！")
                except Exception as e:
                    error(f"保存失敗: {e}")

if __name__ == "__main__":
    main()
