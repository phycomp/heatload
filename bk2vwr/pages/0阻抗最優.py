from streamlit import columns, download_button, error, exception, expander, file_uploader, info, markdown, metric, plotly_chart, session_state, set_page_config, sidebar, spinner, success, warning, slider, number_input
from numpy import abs, angle, argmax, argmin, array, clip, imag, log10, max, maximum, mean, min, ndarray, real, sqrt, std, sum, zeros, linspace
from pandas import DataFrame
from skrf import Network
from plotly.graph_objects import Figure, Scatter, Scatterpolar
from streamlit import empty, sidebar, radio, text_input
from pathlib import Path
# app.py
#import streamlit as st
#import numpy as np
#import skrf as rf
#import pandas as pd
#import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from pathlib import Path
import io
# 頁面配置
set_page_config(
    page_title="S4P DUT 分析儀",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 樣式
markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .optimal-band {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .warning-band {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .critical-band {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

@dataclass
class DUTAnalysisResult:
    """DUT 分析結果"""
    frequency: ndarray
    s_params: ndarray  # (n_freq, 4, 4)

    # 差分模式參數
    sdd11: ndarray
    sdd21: ndarray
    scc11: ndarray
    scc21: ndarray
    scd21: ndarray  # 模式轉換

    # 阻抗
    z_diff: ndarray
    z_common: ndarray

    # 損耗
    il_db: ndarray  # 插入損耗
    rl_db: ndarray  # 回波損耗

    # 最優頻段
    optimal_bands: List[Dict]

    # 品質指標
    quality_score: ndarray

class S4PAnalyzer:
    """S4P 文件分析器"""

    def __init__(self, z0: float = 50.0, target_z_diff: float = 100.0):
        self.z0 = z0
        self.target_z_diff = target_z_diff  # 差分阻抗目標值

    def load_s4p(self, 檔):#file_content: bytes) -> Network:
        """載入 S4P 文件"""
        # 使用 BytesIO 處理上傳的文件
        #byte_stream = io.BytesIO(file_content)
        network = Network(檔)#byte_stream)
        return network

    def convert_to_mixed_mode(self, network: Network) -> Dict[str, ndarray]:
        """
        將單端 S 參數轉換為混合模式 S 參數

        4端口：1,2為差分對（正/負），3,4為差分對（正/負）
        """
        s = network.s  # (n_freq, 4, 4)
        n_freq = len(network.frequency)

        # 混合模式轉換矩陣
        # 對於差分對 (1,2) 和 (3,4)
        M = 1/sqrt(2) * array([
            [1, -1, 0, 0],   # 差分輸入
            [0, 0, 1, -1],   # 差分輸出
            [1, 1, 0, 0],    # 共模輸入
            [0, 0, 1, 1]     # 共模輸出
        ])

        # 對每個頻率點進行轉換
        s_mixed = zeros((n_freq, 4, 4), dtype=complex)

        for i in range(n_freq):
            s_single = s[i]
            # 混合模式 S = M · S_single · M^T
            s_mixed[i] = M @ s_single @ M.T

        # 提取子矩陣
        # S_dd: 差分-差分 (左上 2x2)
        # S_cc: 共模-共模 (右下 2x2)
        # S_dc: 差分-共模 (右上 2x2)
        # S_cd: 共模-差分 (左下 2x2)

        return {
            'sdd': s_mixed[:, :2, :2],
            'scc': s_mixed[:, 2:, 2:],
            'sdc': s_mixed[:, :2, 2:],
            'scd': s_mixed[:, 2:, :2],
            's_mixed_full': s_mixed
        }

    def calculate_impedance(self, sdd11: ndarray, scc11: ndarray) -> Dict[str, ndarray]:
        """
        計算差分和共模阻抗

        Z_diff = 2 * Z0 * (1 + Sdd11) / (1 - Sdd11)
        Z_common = Z0/2 * (1 + Scc11) / (1 - Scc11)
        """
        z_diff = 2 * self.z0 * (1 + sdd11) / (1 - sdd11 + 1e-12)
        z_common = self.z0 / 2 * (1 + scc11) / (1 - scc11 + 1e-12)

        return {
            'z_diff_real': real(z_diff),
            'z_diff_imag': imag(z_diff),
            'z_common_real': real(z_common),
            'z_common_imag': imag(z_common),
            'z_diff_mag': abs(z_diff),
            'z_common_mag': abs(z_common)
        }

    def calculate_losses(self, sdd21: ndarray, sdd11: ndarray) -> Dict[str, ndarray]:
        """
        計算插入損耗和回波損耗（dB）
        """
        il_db = -20 * log10(abs(sdd21) + 1e-12)  # 插入損耗（越小越好）
        rl_db = -20 * log10(abs(sdd11) + 1e-12)   # 回波損耗（越大越好）

        return {
            'il_db': il_db,
            'rl_db': rl_db,
            'il_linear': abs(sdd21),
            'rl_linear': abs(sdd11)
        }

    def calculate_mode_conversion(self, scd21: ndarray) -> ndarray:
        """
        計算模式轉換損耗（dB）
        衡量差分信號轉換為共模信號的程度
        """
        return -20 * log10(abs(scd21) + 1e-12)

    def find_optimal_bands(self,
                          frequency: ndarray,
                          il_db: ndarray,
                          rl_db: ndarray,
                          z_diff_real: ndarray,
                          scd21_db: ndarray,
                          il_threshold: float = 3.0,      # IL < 3dB
                          rl_threshold: float = 15.0,     # RL > 15dB
                          z_tolerance: float = 10.0,      # |Z - 100| < 10Ω
                          mode_conv_threshold: float = 20.0  # 模式轉換 > 20dB
                          ) -> List[Dict]:
        """
        找出最優頻率波段

        判斷標準：
        1. 插入損耗 IL < threshold
        2. 回波損耗 RL > threshold
        3. 差分阻抗 |Z_diff - 100Ω| < tolerance
        4. 模式轉換損耗 > threshold
        """
        # 計算綜合品質指標
        il_score = maximum(0, (il_threshold - il_db) / il_threshold)  # 越高越好
        rl_score = maximum(0, (rl_db - rl_threshold) / rl_threshold)  # 越高越好
        z_score = maximum(0, 1 - abs(z_diff_real - self.target_z_diff) / z_tolerance)
        mode_score = maximum(0, (scd21_db - mode_conv_threshold) / mode_conv_threshold)

        # 綜合品質分數（加權平均）
        quality_score = (0.3 * il_score +
                        0.3 * rl_score +
                        0.2 * z_score +
                        0.2 * mode_score)

        # 找出連續的高品質頻段
        optimal_mask = (il_db < il_threshold) & \
                      (rl_db > rl_threshold) & \
                      (abs(z_diff_real - self.target_z_diff) < z_tolerance) & \
                      (scd21_db > mode_conv_threshold)

        bands = []
        in_band = False
        band_start = 0

        for i in range(len(frequency)):
            if optimal_mask[i] and not in_band:
                band_start = i
                in_band = True
            elif not optimal_mask[i] and in_band:
                # 結束一個頻段
                band_end = i - 1
                if band_end > band_start:
                    band = self._create_band_dict(frequency, band_start, band_end,
                                                  il_db, rl_db, z_diff_real,
                                                  scd21_db, quality_score)
                    bands.append(band)
                in_band = False

        # 處理最後一個頻段
        if in_band:
            band = self._create_band_dict(frequency, band_start, len(frequency)-1,
                                          il_db, rl_db, z_diff_real,
                                          scd21_db, quality_score)
            bands.append(band)

        # 按品質分數排序
        bands.sort(key=lambda x: x['quality_score'], reverse=True)

        return bands

    def _create_band_dict(self, frequency, start, end, il_db, rl_db,
                          z_diff, scd21_db, quality_score) -> Dict:
        """創建頻段字典"""
        return {
            'start_freq': frequency[start] / 1e9,  # GHz
            'end_freq': frequency[end] / 1e9,
            'center_freq': (frequency[start] + frequency[end]) / 2 / 1e9,
            'bandwidth': (frequency[end] - frequency[start]) / 1e9,
            'avg_il': mean(il_db[start:end+1]),
            'min_il': min(il_db[start:end+1]),
            'avg_rl': mean(rl_db[start:end+1]),
            'max_rl': max(rl_db[start:end+1]),
            'avg_z_diff': mean(z_diff[start:end+1]),
            'z_deviation': max(abs(z_diff[start:end+1] - self.target_z_diff)),
            'avg_mode_conv': mean(scd21_db[start:end+1]),
            'quality_score': mean(quality_score[start:end+1]),
            'start_idx': start,
            'end_idx': end
        }

    def analyze(self, network: Network) -> DUTAnalysisResult:
        """完整分析"""
        # 混合模式轉換
        mixed = self.convert_to_mixed_mode(network)

        # 提取關鍵參數
        sdd11 = mixed['sdd'][:, 0, 0]
        sdd21 = mixed['sdd'][:, 1, 0]
        scc11 = mixed['scc'][:, 0, 0]
        scc21 = mixed['scc'][:, 1, 0]
        scd21 = mixed['scd'][:, 1, 0]

        # 計算阻抗
        z_result = self.calculate_impedance(sdd11, scc11)

        # 計算損耗
        loss_result = self.calculate_losses(sdd21, sdd11)

        # 模式轉換
        mode_conv = self.calculate_mode_conversion(scd21)

        # 找出最優頻段
        optimal_bands = self.find_optimal_bands(
            network.frequency.f,
            loss_result['il_db'],
            loss_result['rl_db'],
            z_result['z_diff_real'],
            mode_conv
        )

        # 計算品質分數
        quality_score = self._compute_overall_quality(
            loss_result['il_db'],
            loss_result['rl_db'],
            z_result['z_diff_real'],
            mode_conv
        )

        return DUTAnalysisResult(
            frequency=network.frequency.f,
            s_params=network.s,
            sdd11=sdd11,
            sdd21=sdd21,
            scc11=scc11,
            scc21=scc21,
            scd21=scd21,
            z_diff=z_result['z_diff_real'] + 1j * z_result['z_diff_imag'],
            z_common=z_result['z_common_real'] + 1j * z_result['z_common_imag'],
            il_db=loss_result['il_db'],
            rl_db=loss_result['rl_db'],
            optimal_bands=optimal_bands,
            quality_score=quality_score
        )

    def _compute_overall_quality(self, il_db, rl_db, z_diff_real, mode_conv_db) -> ndarray:
        """計算整體品質分數"""
        il_norm = clip((3.0 - il_db) / 3.0, 0, 1)
        rl_norm = clip((rl_db - 10.0) / 20.0, 0, 1)
        z_norm = clip(1.0 - abs(z_diff_real - 100.0) / 20.0, 0, 1)
        mode_norm = clip((mode_conv_db - 15.0) / 25.0, 0, 1)

        return 0.3 * il_norm + 0.3 * rl_norm + 0.2 * z_norm + 0.2 * mode_norm

# Streamlit UI 組件
def render_sidebar():
    """渲染側邊欄"""
    markdown("## ⚙️ 分析配置")

    # 閾值設定
    markdown("### 判斷閾值")

    il_threshold = slider(
        "插入損耗閾值 (dB)",
        min_value=0.5, max_value=10.0, value=3.0, step=0.5,
        help="IL 低於此值視為合格"
    )

    rl_threshold = slider(
        "回波損耗閾值 (dB)",
        min_value=5.0, max_value=30.0, value=15.0, step=1.0,
        help="RL 高於此值視為合格"
    )

    z_target = number_input(
        "目標差分阻抗 (Ω)",
        min_value=50.0, max_value=200.0, value=100.0, step=5.0
    )

    z_tolerance = slider(
        "阻抗容差 (Ω)",
        min_value=1.0, max_value=30.0, value=10.0, step=1.0,
        help="與目標阻抗的允許偏差"
    )

    mode_conv_threshold = slider(
        "模式轉換閾值 (dB)",
        min_value=10.0, max_value=40.0, value=20.0, step=1.0
    )

    return {
        'il_threshold': il_threshold,
        'rl_threshold': rl_threshold,
        'z_target': z_target,
        'z_tolerance': z_tolerance,
        'mode_conv_threshold': mode_conv_threshold
    }

def render_upload_section():
    """渲染文件上傳區"""
    markdown('<div class="main-header">📡 S4P DUT 分析儀</div>', unsafe_allow_html=True)

    col1, col2 = columns([2, 1])

    with col1:
        uploaded_file = file_uploader(
            "上傳 S4P 文件",
            type=['s4p', 's3p', 's2p'],
            help="支援 Touchstone 格式（.s2p, .s3p, .s4p）"
        )

    with col2:
        markdown("""
        ### 📋 支援格式
        - **.s4p**: 4端口差分對
        - **.s3p**: 3端口（簡化）
        - **.s2p**: 2端口（單端）

        ### 🔧 分析項目
        - 混合模式 S 參數
        - 差分/共模阻抗
        - 插入損耗 (IL)
        - 回波損耗 (RL)
        - 模式轉換
        - 最優頻段識別
        """)

    return uploaded_file

def render_summary_cards(result: DUTAnalysisResult):
    """渲染摘要卡片"""
    markdown("## 📊 分析摘要")

    col1, col2, col3, col4 = columns(4)

    with col1:
        metric(
            label="頻率範圍",
            value=f"{result.frequency[0]/1e9:.2f} - {result.frequency[-1]/1e9:.2f} GHz"
        )

    with col2:
        min_il_idx = argmin(result.il_db)
        metric(
            label="最佳插入損耗",
            value=f"{result.il_db[min_il_idx]:.2f} dB",
            delta=f"@ {result.frequency[min_il_idx]/1e9:.2f} GHz"
        )

    with col3:
        max_rl_idx = argmax(result.rl_db)
        metric(
            label="最佳回波損耗",
            value=f"{result.rl_db[max_rl_idx]:.2f} dB",
            delta=f"@ {result.frequency[max_rl_idx]/1e9:.2f} GHz"
        )

    with col4:
        avg_z = mean(real(result.z_diff))
        metric(
            label="平均差分阻抗",
            value=f"{avg_z:.1f} Ω",
            delta=f"偏差 {avg_z - 100:.1f} Ω"
        )

def render_optimal_bands(result: DUTAnalysisResult, thresholds: Dict):
    """渲染最優頻段"""
    markdown("## 🎯 最優頻段分析")

    if not result.optimal_bands:
        warning("⚠️ 未找到滿足所有條件的最優頻段，請放寬閾值設定")
        return

    # 顯示最優頻段數量
    success(f"✅ 找到 {len(result.optimal_bands)} 個最優頻段")

    # 顯示每個頻段
    for i, band in enumerate(result.optimal_bands[:5]):  # 顯示前5個
        with expander(f"頻段 {i+1}: {band['start_freq']:.2f} - {band['end_freq']:.2f} GHz "
                        f"(品質分數: {band['quality_score']:.3f})",
                        expanded=(i == 0)):

            cols = columns(4)

            with cols[0]:
                markdown(f"""
                **頻段資訊**
                - 中心頻率: {band['center_freq']:.2f} GHz
                - 帶寬: {band['bandwidth']:.2f} GHz
                - 頻點數: {band['end_idx'] - band['start_idx'] + 1}
                """)

            with cols[1]:
                markdown(f"""
                **損耗性能**
                - 平均 IL: {band['avg_il']:.2f} dB
                - 最小 IL: {band['min_il']:.2f} dB
                - 平均 RL: {band['avg_rl']:.2f} dB
                - 最大 RL: {band['max_rl']:.2f} dB
                """)

            with cols[2]:
                markdown(f"""
                **阻抗性能**
                - 平均 Z_diff: {band['avg_z_diff']:.1f} Ω
                - 最大偏差: {band['z_deviation']:.1f} Ω
                - 模式轉換: {band['avg_mode_conv']:.1f} dB
                """)

            with cols[3]:
                # 品質評級
                if band['quality_score'] > 0.8:
                    rating = "🟢 優秀"
                elif band['quality_score'] > 0.6:
                    rating = "🟡 良好"
                elif band['quality_score'] > 0.4:
                    rating = "🟠 一般"
                else:
                    rating = "🔴 較差"

                markdown(f"""
                **綜合評級**
                - 品質分數: {band['quality_score']:.3f}
                - 評級: {rating}
                """)

            # 在圖表上標記此頻段
            session_state[f'highlight_band_{i}'] = (band['start_idx'], band['end_idx'])

def render_sparam_plots(result: DUTAnalysisResult):
    """渲染 S 參數圖表"""
    markdown("## 📈 S 參數分析")

    freq_ghz = result.frequency / 1e9

    # 創建子圖
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            '差分回波損耗 (Sdd11)',
            '差分插入損耗 (Sdd21)',
            '共模回波損耗 (Scc11)',
            '共模插入損耗 (Scc21)',
            '模式轉換 (Scd21)',
            '差分阻抗'
        ),
        vertical_spacing=0.1,
        horizontal_spacing=0.08
    )

    # Sdd11
    fig.add_trace(
        Scatter(x=freq_ghz, y=result.rl_db, mode='lines',
                   name='Sdd11 (RL)', line=dict(color='blue', width=2)),
        row=1, col=1
    )
    fig.add_hline(y=15, line_dash="dash", line_color="green",
                  annotation_text="RL > 15dB", row=1, col=1)

    # Sdd21
    fig.add_trace(
        Scatter(x=freq_ghz, y=result.il_db, mode='lines',
                   name='Sdd21 (IL)', line=dict(color='red', width=2)),
        row=1, col=2
    )
    fig.add_hline(y=3, line_dash="dash", line_color="green",
                  annotation_text="IL < 3dB", row=1, col=2)

    # Scc11
    scc11_db = -20 * log10(abs(result.scc11) + 1e-12)
    fig.add_trace(
        Scatter(x=freq_ghz, y=scc11_db, mode='lines',
                   name='Scc11', line=dict(color='purple', width=2)),
        row=2, col=1
    )

    # Scc21
    scc21_db = -20 * log10(abs(result.scc21) + 1e-12)
    fig.add_trace(
        Scatter(x=freq_ghz, y=scc21_db, mode='lines',
                   name='Scc21', line=dict(color='orange', width=2)),
        row=2, col=2
    )

    # Scd21 (模式轉換)
    scd21_db = -20 * log10(abs(result.scd21) + 1e-12)
    fig.add_trace(
        Scatter(x=freq_ghz, y=scd21_db, mode='lines',
                   name='Scd21', line=dict(color='brown', width=2)),
        row=3, col=1
    )
    fig.add_hline(y=20, line_dash="dash", line_color="green",
                  annotation_text="> 20dB", row=3, col=1)

    # 差分阻抗
    fig.add_trace(
        Scatter(x=freq_ghz, y=real(result.z_diff), mode='lines',
                   name='Z_diff Real', line=dict(color='green', width=2)),
        row=3, col=2
    )
    fig.add_trace(
        Scatter(x=freq_ghz, y=imag(result.z_diff), mode='lines',
                   name='Z_diff Imag', line=dict(color='cyan', width=2, dash='dash')),
        row=3, col=2
    )
    fig.add_hline(y=100, line_dash="dash", line_color="black",
                  annotation_text="100Ω", row=3, col=2)
    fig.add_hline(y=90, line_dash="dot", line_color="gray", row=3, col=2)
    fig.add_hline(y=110, line_dash="dot", line_color="gray", row=3, col=2)

    # 標記最優頻段
    for i, band in enumerate(result.optimal_bands[:3]):
        color = ['rgba(0,255,0,0.2)', 'rgba(255,255,0,0.2)', 'rgba(255,165,0,0.2)'][i]
        for row in range(1, 4):
            for col in range(1, 3):
                fig.add_vrect(
                    x0=band['start_freq'], x1=band['end_freq'],
                    fillcolor=color, opacity=0.3,
                    layer="below", line_width=0,
                    row=row, col=col
                )

    # 更新布局
    fig.update_layout(
        height=900,
        showlegend=True,
        title_text="混合模式 S 參數分析",
        hovermode='x unified'
    )

    fig.update_xaxes(title_text="頻率 (GHz)")
    fig.update_yaxes(title_text="幅度 (dB)", row=1, col=1)
    fig.update_yaxes(title_text="幅度 (dB)", row=1, col=2)
    fig.update_yaxes(title_text="幅度 (dB)", row=2, col=1)
    fig.update_yaxes(title_text="幅度 (dB)", row=2, col=2)
    fig.update_yaxes(title_text="幅度 (dB)", row=3, col=1)
    fig.update_yaxes(title_text="阻抗 (Ω)", row=3, col=2)

    plotly_chart(fig, use_container_width=True)

def render_impedance_analysis(result: DUTAnalysisResult):
    """渲染阻抗分析"""
    markdown("## 🔍 阻抗匹配分析")

    freq_ghz = result.frequency / 1e9

    # Smith 圖近似（極坐標）
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'polar'}, {'type': 'xy'}]],
        subplot_titles=('差分阻抗 Smith 圖', '阻抗軌跡')
    )

    # 極坐標圖
    z_norm = result.z_diff / 100  # 歸一化到100Ω
    gamma = (z_norm - 1) / (z_norm + 1)

    fig.add_trace(
        Scatterpolar(
            r=abs(gamma),
            theta=angle(gamma, deg=True),
            mode='lines+markers',
            marker=dict(size=3, color=freq_ghz, colorscale='Viridis'),
            name='Z_diff'
        ),
        row=1, col=1
    )

    # 阻抗軌跡
    fig.add_trace(
        Scatter(
            x=freq_ghz, y=real(result.z_diff),
            mode='lines', name='Real(Z_diff)',
            line=dict(color='blue', width=2)
        ),
        row=1, col=2
    )
    fig.add_trace(
        Scatter(
            x=freq_ghz, y=imag(result.z_diff),
            mode='lines', name='Imag(Z_diff)',
            line=dict(color='red', width=2)
        ),
        row=1, col=2
    )

    fig.add_shape(type="circle", xref="x2 domain", yref="y2 domain", x0=0, y0=0, x1=1, y1=1, line_color="green", line_dash="dash", row=1, col=2)   # Adjust reference to your subplot
    #fig.add_trace(Scatterpolar(r=[100]*100, theta=list(range(0, 361, 4)), mode="lines", line=dict(color="green", dash="dash"), showlegend=False), row=1, col=2)

    #fig.add_hline(y=100, line_dash="dash", line_color="green", row=1, col=2)
    #fig.add_hrect(y0=90, y1=110, line_width=0, fillcolor="green", opacity=0.1, row=1, col=2)

    theta = linspace(0, 360, 100) # 建立 0 到 360 度的角度陣列

    # 透過順時針畫外圈、逆時針畫內圈的方式形成封閉圓環
    r_outer = [110] * len(theta)
    r_inner = [90] * len(theta)

    theta = linspace(0, 360, 100) # 建立 0 到 360 度的角度陣列

    # 透過順時針畫外圈、逆時針畫內圈的方式形成封閉圓環
    r_outer = [110] * len(theta)
    r_inner = [90] * len(theta)

    #fig.add_trace(Scatterpolar(r=r_outer+r_inner[::-1], theta=list(theta) + list(theta)[::-1], fill='toself', fillcolor='rgba(0, 128, 0, 0.1)', line=dict(width=0), mode='lines', showlegend=False, subplot="polar2"), row=1, col=2)  # 請確保對應到您 row=1, col=2 的 polar 編號               # 線寬為 0 # 綠色且不透明度 0.1
    fig.add_shape(type="circle", xref="x2 domain", yref="y2 domain", x0=.1, y0=.1, x1=.9, y1=.9, fillcolor="green", opacity=.1, line_width=0, row=1, col=2)  # 對應第 2 個子圖的軸      # 需要手動微調縮放比例以符合半徑 110

    fig.update_layout(height=500, showlegend=True)
    fig.update_xaxes(title_text="頻率 (GHz)", row=1, col=2)
    fig.update_yaxes(title_text="阻抗 (Ω)", row=1, col=2)

    plotly_chart(fig, use_container_width=True)

    # 阻抗匹配統計
    col1, col2, col3 = columns(3)

    z_real = real(result.z_diff)
    in_range = sum((z_real >= 90) & (z_real <= 110)) / len(z_real) * 100

    with col1:
        metric("阻抗在 100±10Ω 範圍內", f"{in_range:.1f}%")

    with col2:
        metric("最大阻抗偏差", f"{max(abs(z_real - 100)):.1f} Ω")

    with col3:
        metric("阻抗標準差", f"{std(z_real):.1f} Ω")

def render_quality_map(result: DUTAnalysisResult):
    """渲染品質熱力圖"""
    markdown("## 🗺️ 品質分數地圖")

    freq_ghz = result.frequency / 1e9

    fig = Figure()

    # 品質分數
    fig.add_trace(Scatter(
        x=freq_ghz, y=result.quality_score,
        mode='lines', fill='tozeroy',
        name='綜合品質分數',
        line=dict(color='green', width=2),
        fillcolor='rgba(0,255,0,0.2)'
    ))

    # 各項指標
    il_norm = clip((3.0 - result.il_db) / 3.0, 0, 1)
    rl_norm = clip((result.rl_db - 10.0) / 20.0, 0, 1)
    z_norm = clip(1.0 - abs(real(result.z_diff) - 100.0) / 20.0, 0, 1)

    fig.add_trace(Scatter(x=freq_ghz, y=il_norm, mode='lines',
                            name='IL 品質', line=dict(width=1, dash='dash')))
    fig.add_trace(Scatter(x=freq_ghz, y=rl_norm, mode='lines',
                            name='RL 品質', line=dict(width=1, dash='dash')))
    fig.add_trace(Scatter(x=freq_ghz, y=z_norm, mode='lines',
                            name='Z 品質', line=dict(width=1, dash='dash')))

    # 標記最優區域
    for band in result.optimal_bands[:3]:
        fig.add_vrect(
            x0=band['start_freq'], x1=band['end_freq'],
            fillcolor='rgba(0,255,0,0.2)', opacity=0.3,
            layer="below", line_width=0
        )

    fig.update_layout(
        title="品質分數 vs 頻率",
        xaxis_title="頻率 (GHz)",
        yaxis_title="品質分數 (0-1)",
        height=400,
        yaxis=dict(range=[0, 1])
    )

    plotly_chart(fig, use_container_width=True)

def render_export_section(result: DUTAnalysisResult):
    """渲染匯出區"""
    markdown("## 💾 數據匯出")

    col1, col2 = columns(2)

    with col1:
        # 匯出最優頻段 CSV
        if result.optimal_bands:
            df_bands = DataFrame(result.optimal_bands)
            csv = df_bands.to_csv(index=False)
            download_button(
                label="下載最優頻段 CSV",
                data=csv,
                file_name="optimal_bands.csv",
                mime="text/csv"
            )

    with col2:
        # 匯出完整數據
        df_full = DataFrame({
            'Frequency_GHz': result.frequency / 1e9,
            'Sdd11_dB': -20 * log10(abs(result.sdd11) + 1e-12),
            'Sdd21_dB': -20 * log10(abs(result.sdd21) + 1e-12),
            'Z_diff_Real': real(result.z_diff),
            'Z_diff_Imag': imag(result.z_diff),
            'Quality_Score': result.quality_score
        })
        csv_full = df_full.to_csv(index=False)
        download_button(
            label="下載完整分析數據 CSV",
            data=csv_full,
            file_name="full_analysis.csv",
            mime="text/csv"
        )

def render_comparison_section():
    """渲染多文件比較區"""
    markdown("## 📊 多文件比較")
    info("上傳多個 S4P 文件進行比較分析")

    comparison_files = file_uploader(
        "上傳多個文件進行比較",
        type=['s4p', 's3p', 's2p'],
        accept_multiple_files=True,
        key='comparison'
    )

    if len(comparison_files) > 1:
        # 比較分析
        analyzer = S4PAnalyzer()
        results = []

        for file in comparison_files:
            network = analyzer.load_s4p(file.getvalue())
            result = analyzer.analyze(network)
            results.append({
                'name': file.name,
                'result': result
            })

        # 繪製比較圖
        fig = Figure()

        for item in results:
            freq_ghz = item['result'].frequency / 1e9
            fig.add_trace(Scatter(
                x=freq_ghz, y=item['result'].il_db,
                mode='lines', name=f"{item['name']} IL"
            ))

        fig.update_layout(
            title="插入損耗比較",
            xaxis_title="頻率 (GHz)",
            yaxis_title="IL (dB)",
            height=500
        )

        plotly_chart(fig, use_container_width=True)

MENU, 表單=[], ['側邊欄', '', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  thresholds = render_sidebar()
  狀態=empty()
  #狀態.code([])
if menu==len(表單): #
  pass
elif menu==MENU[1]: #
  pass
elif menu==MENU[0]: #側邊欄
# 主程序
  #with sidebar:
    # 側邊欄

    # 文件上傳
    #uploaded_file = render_upload_section()

    #if uploaded_file is not None:
        #try:
            # 分析
            #with spinner("正在分析 S4P 文件..."):
  根=Path('.')
  資檔=根.glob('*.s4p')
  檔=radio('s4p', 資檔, horizontal=True)
  analyzer = S4PAnalyzer(z0=50., target_z_diff=thresholds['z_target'])

  if 檔:
    #內容 = 檔.read_bytes()

    #with 檔.open(encoding="utf-8") as fin:
    #with file_path.open(mode="r", encoding="utf-8") as file:
      #content = file.read()
      #內容=fin.read()
    #狀態.code(內容)
    network = analyzer.load_s4p(檔) #內容uploaded_file.getvalue()
    result = analyzer.analyze(network)

    # 使用用戶設定的閾值重新計算最優頻段
    result.optimal_bands = analyzer.find_optimal_bands(
        result.frequency,
        result.il_db,
        result.rl_db,
        real(result.z_diff),
        -20 * log10(abs(result.scd21) + 1e-12),
        il_threshold=thresholds['il_threshold'],
        rl_threshold=thresholds['rl_threshold'],
        z_tolerance=thresholds['z_tolerance'],
        mode_conv_threshold=thresholds['mode_conv_threshold']
    )

    # 顯示結果
    render_summary_cards(result)
    render_optimal_bands(result, thresholds)
    render_sparam_plots(result)
    render_impedance_analysis(result)
    render_quality_map(result)
    render_export_section(result)
    render_comparison_section()

        #except Exception as e:
        #    error(f"分析過程中發生錯誤: {str(e)}")
        #    exception(e)
    #else:
        # 顯示示例

        #with expander("查看示例分析"):
with sidebar:
  info("👆 請上傳 S4P 文件開始分析")
  markdown("""
  ### 示例：理想差分傳輸線

  **預期結果：**
  - 在設計頻率範圍內，IL < 1dB
  - RL > 20dB
  - Z_diff ≈ 100Ω ± 5Ω
  - 模式轉換 > 25dB

  **最優頻段判斷：**
  1. 找出 IL 最低且平坦的區域
  2. 確認 RL 在此區域 > 15dB
  3. 檢查 Z_diff 是否在 90-110Ω 範圍內
  4. 確認模式轉換足夠低（> 20dB）
  """)

#if __name__ == "__main__": main()
