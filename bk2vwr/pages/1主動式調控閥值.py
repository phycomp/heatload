from streamlit import columns, dataframe, download_button, error, exception, expander, file_uploader, info, markdown, metric, plotly_chart, set_page_config, sidebar, spinner, slider, number_input, checkbox, radio, text_input
from pathlib import Path
from streamlit import empty
from numpy import abs, argmax, argmin, array, clip, imag, log10, max, mean, min, ndarray, real, sqrt, zeros
from pandas import DataFrame
from skrf import Network
from plotly.graph_objects import Figure, Scatter
# app.py
#import streamlit as st
#import numpy as np
#import skrf as rf
#import pandas as pd
#import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from io import BytesIO
from scipy.ndimage import uniform_filter1d
from scipy.signal import find_peaks

# 頁面配置
set_page_config(
    page_title="S4P DUT 分析儀 - Adaptive 波段",
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
    .optimal-band {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .adaptive-band {
        background-color: #e7f3ff;
        border-left: 4px solid #0066cc;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .compromise-band {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .metric-highlight {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

@dataclass
class AdaptiveBandResult:
    """Adaptive 波段分析結果"""
    # 原始閾值
    original_il: float
    original_rl: float
    original_z_tol: float

    # 自適應閾值
    adaptive_il: float
    adaptive_rl: float
    adaptive_z_tol: float

    # 找到的頻段
    bands: List[Dict]

    # 妥協方案
    compromise_bands: List[Dict]

    # 閾值調整歷程
    threshold_history: List[Dict]

    # 最佳單一指標頻段
    best_il_band: Optional[Dict]
    best_rl_band: Optional[Dict]
    best_z_band: Optional[Dict]

class AdaptiveBandFinder:
    """
    Adaptive 移動波段分析器
    自動調整閾值找出最適頻段
    """

    def __init__(self,
                 frequency: ndarray,
                 il_db: ndarray,
                 rl_db: ndarray,
                 z_diff_real: ndarray,
                 scd21_db: ndarray,
                 target_z: float = 100.0):

        self.frequency = frequency
        self.il_db = il_db
        self.rl_db = rl_db
        self.z_diff = z_diff_real
        self.scd21_db = scd21_db
        self.target_z = target_z

        # 數據平滑
        self.il_smooth = self._smooth_data(il_db, window=5)
        self.rl_smooth = self._smooth_data(rl_db, window=5)
        self.z_smooth = self._smooth_data(z_diff_real, window=5)

    def _smooth_data(self, data: ndarray, window: int = 5) -> ndarray:
        """平滑數據減少噪聲影響"""
        return uniform_filter1d(data, size=window)

    def find_adaptive_bands(self,
                           initial_il: float = 3.0,
                           initial_rl: float = 15.0,
                           initial_z_tol: float = 10.0,
                           initial_mode: float = 20.0,
                           max_iterations: int = 20,
                           min_band_width_ghz: float = 1.0) -> AdaptiveBandResult:
        """
        自適應尋找最適頻段

        策略：
        1. 先嘗試原始閾值
        2. 若無結果，逐步放寬閾值
        3. 同時尋找單一指標最優的「局部最佳」頻段
        4. 提供妥協方案（放寬次要指標，保持主要指標嚴格）
        """

        threshold_history = []

        # 步驟1：嘗試原始閾值
        bands = self._find_bands(initial_il, initial_rl, initial_z_tol, initial_mode)

        if bands:
            # 找到符合原始閾值的頻段
            return AdaptiveBandResult(
                original_il=initial_il,
                original_rl=initial_rl,
                original_z_tol=initial_z_tol,
                adaptive_il=initial_il,
                adaptive_rl=initial_rl,
                adaptive_z_tol=initial_z_tol,
                bands=bands,
                compromise_bands=[],
                threshold_history=[{
                    'iteration': 0,
                    'il': initial_il, 'rl': initial_rl,
                    'z_tol': initial_z_tol, 'mode': initial_mode,
                    'bands_found': len(bands)
                }],
                best_il_band=None,
                best_rl_band=None,
                best_z_band=None
            )

        # 步驟2：逐步放寬閾值尋找頻段
        current_il = initial_il
        current_rl = initial_rl
        current_z_tol = initial_z_tol
        current_mode = initial_mode

        il_step = 0.5      # IL 每次放寬 0.5dB
        rl_step = 2.0      # RL 每次降低 2dB
        z_step = 2.0       # Z 容差每次增加 2Ω
        mode_step = 2.0    # 模式轉換每次降低 2dB

        for iteration in range(max_iterations):
            # 輪流放寬不同指標
            phase = iteration % 4

            if phase == 0:
                current_il += il_step  # 放寬 IL
            elif phase == 1:
                current_rl -= rl_step  # 降低 RL
            elif phase == 2:
                current_z_tol += z_step  # 放寬 Z
            else:
                current_mode -= mode_step  # 降低模式轉換

            # 確保閾值合理
            current_il = min(current_il, 10.0)
            current_rl = max(current_rl, 5.0)
            current_z_tol = min(current_z_tol, 30.0)
            current_mode = max(current_mode, 10.0)

            # 嘗試尋找頻段
            bands = self._find_bands(current_il, current_rl, current_z_tol, current_mode,
                                    min_width_ghz=min_band_width_ghz)

            threshold_history.append({
                'iteration': iteration + 1,
                'il': current_il, 'rl': current_rl,
                'z_tol': current_z_tol, 'mode': current_mode,
                'bands_found': len(bands)
            })

            if bands:
                # 找到頻段，記錄自適應閾值
                adaptive_il = current_il
                adaptive_rl = current_rl
                adaptive_z_tol = current_z_tol
                break
        else:
            # 即使放寬到最大仍未找到，使用最寬鬆閾值
            adaptive_il = current_il
            adaptive_rl = current_rl
            adaptive_z_tol = current_z_tol
            bands = self._find_bands(current_il, current_rl, current_z_tol, current_mode,
                                     min_width_ghz=0.1)  # 允許極窄頻段

        # 步驟3：尋找單一指標最優的「局部最佳」頻段
        best_il = self._find_best_single_metric_band('il')
        best_rl = self._find_best_single_metric_band('rl')
        best_z = self._find_best_single_metric_band('z')

        # 步驟4：生成妥協方案
        compromise_bands = self._generate_compromise_bands(
            initial_il, initial_rl, initial_z_tol, initial_mode
        )

        return AdaptiveBandResult(
            original_il=initial_il,
            original_rl=initial_rl,
            original_z_tol=initial_z_tol,
            adaptive_il=adaptive_il,
            adaptive_rl=adaptive_rl,
            adaptive_z_tol=adaptive_z_tol,
            bands=bands,
            compromise_bands=compromise_bands,
            threshold_history=threshold_history,
            best_il_band=best_il,
            best_rl_band=best_rl,
            best_z_band=best_z
        )

    def _find_bands(self,
                    il_thresh: float,
                    rl_thresh: float,
                    z_tol: float,
                    mode_thresh: float,
                    min_width_ghz: float = 1.0) -> List[Dict]:
        """根據閾值尋找頻段"""

        # 計算綜合掩碼
        mask = (self.il_smooth < il_thresh) & \
               (self.rl_smooth > rl_thresh) & \
               (abs(self.z_smooth - self.target_z) < z_tol) & \
               (self.scd21_db > mode_thresh)

        bands = []
        in_band = False
        start_idx = 0

        for i in range(len(self.frequency)):
            if mask[i] and not in_band:
                start_idx = i
                in_band = True
            elif not mask[i] and in_band:
                end_idx = i - 1
                bandwidth = (self.frequency[end_idx] - self.frequency[start_idx]) / 1e9

                if bandwidth >= min_width_ghz:
                    band = self._create_band_dict(start_idx, end_idx)
                    bands.append(band)

                in_band = False

        # 處理最後一個頻段
        if in_band:
            end_idx = len(self.frequency) - 1
            bandwidth = (self.frequency[end_idx] - self.frequency[start_idx]) / 1e9

            if bandwidth >= min_width_ghz:
                band = self._create_band_dict(start_idx, end_idx)
                bands.append(band)

        # 按品質排序
        bands.sort(key=lambda x: x['quality_score'], reverse=True)

        return bands

    def _create_band_dict(self, start: int, end: int) -> Dict:
        """創建頻段字典"""
        freq_start = self.frequency[start] / 1e9
        freq_end = self.frequency[end] / 1e9

        return {
            'start_freq': freq_start,
            'end_freq': freq_end,
            'center_freq': (freq_start + freq_end) / 2,
            'bandwidth': freq_end - freq_start,
            'start_idx': start,
            'end_idx': end,
            'avg_il': mean(self.il_db[start:end+1]),
            'min_il': min(self.il_db[start:end+1]),
            'avg_rl': mean(self.rl_db[start:end+1]),
            'max_rl': max(self.rl_db[start:end+1]),
            'avg_z': mean(self.z_diff[start:end+1]),
            'z_deviation': max(abs(self.z_diff[start:end+1] - self.target_z)),
            'avg_mode_conv': mean(self.scd21_db[start:end+1]),
            'quality_score': self._calculate_band_quality(start, end)
        }

    def _calculate_band_quality(self, start: int, end: int) -> float:
        """計算頻段品質分數"""
        il_score = mean(clip((3.0 - self.il_db[start:end+1]) / 3.0, 0, 1))
        rl_score = mean(clip((self.rl_db[start:end+1] - 10.0) / 20.0, 0, 1))
        z_score = mean(clip(1.0 - abs(self.z_diff[start:end+1] - self.target_z) / 20.0, 0, 1))
        mode_score = mean(clip((self.scd21_db[start:end+1] - 15.0) / 25.0, 0, 1))

        return 0.3 * il_score + 0.3 * rl_score + 0.2 * z_score + 0.2 * mode_score

    def _find_best_single_metric_band(self, metric: str) -> Optional[Dict]:
        """
        尋找單一指標最優的頻段

        metric: 'il', 'rl', 'z'
        """
        window_size = max(10, len(self.frequency) // 50)  # 動態窗口

        if metric == 'il':
            # 找 IL 最低的連續區域
            smoothed = uniform_filter1d(self.il_db, size=window_size)
            # 找局部最小值
            peaks, _ = find_peaks(-smoothed, distance=window_size, prominence=0.5)

            if len(peaks) == 0:
                return None

            best_peak = peaks[argmin(smoothed[peaks])]

            # 擴展頻段直到 IL 增加 1dB
            threshold = smoothed[best_peak] + 1.0
            left = best_peak
            right = best_peak

            while left > 0 and smoothed[left] < threshold:
                left -= 1
            while right < len(smoothed) - 1 and smoothed[right] < threshold:
                right += 1

            return self._create_band_dict(left, right)

        elif metric == 'rl':
            # 找 RL 最高的連續區域
            smoothed = uniform_filter1d(self.rl_db, size=window_size)
            peaks, _ = find_peaks(smoothed, distance=window_size, prominence=2.0)

            if len(peaks) == 0:
                return None

            best_peak = peaks[argmax(smoothed[peaks])]

            threshold = smoothed[best_peak] - 3.0
            left = best_peak
            right = best_peak

            while left > 0 and smoothed[left] > threshold:
                left -= 1
            while right < len(smoothed) - 1 and smoothed[right] > threshold:
                right += 1

            return self._create_band_dict(left, right)

        elif metric == 'z':
            # 找 Z 最接近目標的連續區域
            z_error = abs(self.z_diff - self.target_z)
            smoothed = uniform_filter1d(z_error, size=window_size)
            peaks, _ = find_peaks(-smoothed, distance=window_size, prominence=1.0)

            if len(peaks) == 0:
                return None

            best_peak = peaks[argmin(smoothed[peaks])]

            threshold = smoothed[best_peak] + 5.0  # 允許 5Ω 偏差
            left = best_peak
            right = best_peak

            while left > 0 and smoothed[left] < threshold:
                left -= 1
            while right < len(smoothed) - 1 and smoothed[right] < threshold:
                right += 1

            return self._create_band_dict(left, right)

        return None

    def _generate_compromise_bands(self,
                                    il_strict: float,
                                    rl_strict: float,
                                    z_strict: float,
                                    mode_strict: float) -> List[Dict]:
        """
        生成妥協方案：放寬次要指標，保持主要指標嚴格
        """
        compromises = []

        # 方案1：保持 IL 嚴格，放寬 RL 和 Z
        bands = self._find_bands(il_strict, rl_strict - 5, z_strict + 5, mode_strict - 5)
        if bands:
            compromises.append({
                'name': '低損耗優先',
                'description': f'保持 IL < {il_strict}dB，放寬 RL 和 Z',
                'bands': bands[:3],
                'priority': 'insertion_loss'
            })

        # 方案2：保持 RL 嚴格，放寬 IL
        bands = self._find_bands(il_strict + 2, rl_strict, z_strict + 5, mode_strict - 5)
        if bands:
            compromises.append({
                'name': '高匹配優先',
                'description': f'保持 RL > {rl_strict}dB，放寬 IL',
                'bands': bands[:3],
                'priority': 'return_loss'
            })

        # 方案3：保持 Z 嚴格，放寬其他
        bands = self._find_bands(il_strict + 2, rl_strict - 3, z_strict, mode_strict - 5)
        if bands:
            compromises.append({
                'name': '阻抗匹配優先',
                'description': f'保持 Z = {self.target_z}±{z_strict}Ω，放寬損耗',
                'bands': bands[:3],
                'priority': 'impedance'
            })

        # 方案4：極寬鬆（所有指標都放寬）
        bands = self._find_bands(il_strict + 3, rl_strict - 5, z_strict + 10, mode_strict - 10,
                                  min_width_ghz=0.5)
        if bands:
            compromises.append({
                'name': '最大可用頻段',
                'description': '放寬所有指標，找出最大可用範圍',
                'bands': bands[:3],
                'priority': 'bandwidth'
            })

        return compromises

# S4P 分析器（保留原有功能）
class S4PAnalyzer:
    """S4P 文件分析器"""

    def __init__(self, z0: float = 50.0, target_z_diff: float = 100.0):
        self.z0 = z0
        self.target_z_diff = target_z_diff

    def load_s4p(self, 檔):   #file_content: bytes) -> Network:
        #byte_stream = BytesIO(file_content)
        network = Network(檔)#byte_stream)
        return network

    def convert_to_mixed_mode(self, network: Network) -> Dict:
        s = network.s
        n_freq = len(network.frequency)

        M = 1/sqrt(2) * array([
            [1, -1, 0, 0],
            [0, 0, 1, -1],
            [1, 1, 0, 0],
            [0, 0, 1, 1]
        ])

        s_mixed = zeros((n_freq, 4, 4), dtype=complex)
        for i in range(n_freq):
            s_mixed[i] = M @ s[i] @ M.T

        return {
            'sdd': s_mixed[:, :2, :2],
            'scc': s_mixed[:, 2:, 2:],
            'sdc': s_mixed[:, :2, 2:],
            'scd': s_mixed[:, 2:, :2]
        }

    def calculate_impedance(self, sdd11: ndarray, scc11: ndarray) -> Dict:
        z_diff = 2 * self.z0 * (1 + sdd11) / (1 - sdd11 + 1e-12)
        z_common = self.z0 / 2 * (1 + scc11) / (1 - scc11 + 1e-12)

        return {
            'z_diff_real': real(z_diff),
            'z_diff_imag': imag(z_diff),
            'z_common_real': real(z_common)
        }

    def calculate_losses(self, sdd21: ndarray, sdd11: ndarray) -> Dict:
        return {
            'il_db': -20 * log10(abs(sdd21) + 1e-12),
            'rl_db': -20 * log10(abs(sdd11) + 1e-12)
        }

# Streamlit UI 組件
def render_sidebar():
    """渲染側邊欄"""
    markdown("## ⚙️ 分析配置")

    markdown("### 初始閾值設定")

    il_threshold = slider(
        "插入損耗閾值 IL (dB)",
        min_value=0.5, max_value=15.0, value=3.0, step=0.5,
        help="初始 IL 閾值，若無結果將自動放寬"
    )

    rl_threshold = slider(
        "回波損耗閾值 RL (dB)",
        min_value=5.0, max_value=30.0, value=15.0, step=1.0,
        help="初始 RL 閾值，若無結果將自動降低"
    )

    z_target = number_input(
        "目標差分阻抗 (Ω)",
        min_value=50.0, max_value=200.0, value=100.0, step=5.0
    )

    z_tolerance = slider(
        "阻抗容差 (Ω)",
        min_value=1.0, max_value=30.0, value=10.0, step=1.0,
        help="初始 Z 容差，若無結果將自動增加"
    )

    mode_conv_threshold = slider(
        "模式轉換閾值 (dB)",
        min_value=10.0, max_value=40.0, value=20.0, step=1.0
    )

    markdown("### Adaptive 設定")

    min_band_width = slider(
        "最小頻段寬度 (GHz)",
        min_value=0.1, max_value=5.0, value=1.0, step=0.1,
        help="最窄可接受的頻段寬度"
    )

    enable_adaptive = checkbox(
        "啟用 Adaptive 分析",
        value=True,
        help="自動調整閾值尋找最適頻段"
    )

    show_single_metric = checkbox(
        "顯示單一指標最優頻段",
        value=True,
        help="顯示 IL/RL/Z 各自最優的局部頻段"
    )

    return {
        'il_threshold': il_threshold,
        'rl_threshold': rl_threshold,
        'z_target': z_target,
        'z_tolerance': z_tolerance,
        'mode_conv_threshold': mode_conv_threshold,
        'min_band_width': min_band_width,
        'enable_adaptive': enable_adaptive,
        'show_single_metric': show_single_metric
    }

def render_upload_section():
    markdown('<div class="main-header">📡 S4P DUT 分析儀 - Adaptive 波段</div>',
                unsafe_allow_html=True)

    col1, col2 = columns([2, 1])

    with col1:
        uploaded_file = file_uploader(
            "上傳 S4P 文件",
            type=['s4p', 's3p', 's2p'],
            help="支援 Touchstone 格式"
        )

    with col2:
        markdown("""
        ### 🔧 新功能：Adaptive 移動波段
        - **自動閾值調整**：找不到頻段時自動放寬條件
        - **單一指標最優**：找出 IL/RL/Z 各自最佳頻段
        - **妥協方案**：提供多種優先級策略
        - **閾值歷程**：可視化調整過程
        """)

    return uploaded_file

def render_adaptive_results(adaptive_result: AdaptiveBandResult, thresholds: Dict, freq_ghz: ndarray):
    """渲染 Adaptive 分析結果"""

    markdown("## 🎯 Adaptive 波段分析結果")

    # 顯示閾值調整歷程
    if len(adaptive_result.threshold_history) > 1:
        with expander("📊 閾值調整歷程", expanded=True):
            markdown("### 自適應閾值調整過程")

            # 繪製閾值調整圖
            fig = Figure()

            history = adaptive_result.threshold_history
            iterations = [h['iteration'] for h in history]

            fig.add_trace(Scatter(
                x=iterations, y=[h['il'] for h in history],
                mode='lines+markers', name='IL 閾值',
                line=dict(color='red')
            ))
            fig.add_trace(Scatter(
                x=iterations, y=[h['rl'] for h in history],
                mode='lines+markers', name='RL 閾值',
                line=dict(color='blue')
            ))
            fig.add_trace(Scatter(
                x=iterations, y=[h['z_tol'] for h in history],
                mode='lines+markers', name='Z 容差',
                line=dict(color='green')
            ))

            # 標記找到頻段的點
            found_indices = [i for i, h in enumerate(history) if h['bands_found'] > 0]
            if found_indices:
                fig.add_vline(
                    x=history[found_indices[0]]['iteration'],
                    line_dash="dash", line_color="green",
                    annotation_text="找到頻段!"
                )

            fig.update_layout(
                title="閾值調整歷程",
                xaxis_title="迭代次數",
                yaxis_title="閾值",
                height=400
            )

            plotly_chart(fig, use_container_width=True)

            # 顯示閾值變化表格
            df_history = DataFrame(history)
            dataframe(df_history, use_container_width=True)

    # 顯示最終閾值
    col1, col2, col3, col4 = columns(4)

    with col1:
        delta_il = adaptive_result.adaptive_il - adaptive_result.original_il
        metric(
            "自適應 IL 閾值",
            f"{adaptive_result.adaptive_il:.1f} dB",
            delta=f"{delta_il:+.1f} dB" if delta_il != 0 else "未變動",
            delta_color="inverse" if delta_il > 0 else "off"
        )

    with col2:
        delta_rl = adaptive_result.adaptive_rl - adaptive_result.original_rl
        metric(
            "自適應 RL 閾值",
            f"{adaptive_result.adaptive_rl:.1f} dB",
            delta=f"{delta_rl:+.1f} dB" if delta_rl != 0 else "未變動",
            delta_color="inverse" if delta_rl < 0 else "off"
        )

    with col3:
        delta_z = adaptive_result.adaptive_z_tol - adaptive_result.original_z_tol
        metric(
            "自適應 Z 容差",
            f"±{adaptive_result.adaptive_z_tol:.1f} Ω",
            delta=f"{delta_z:+.1f} Ω" if delta_z != 0 else "未變動",
            delta_color="inverse" if delta_z > 0 else "off"
        )

    with col4:
        metric(
            "找到頻段數",
            f"{len(adaptive_result.bands)} 個"
        )

    # 顯示找到的頻段
    if adaptive_result.bands:
        markdown("### ✅ 自適應最優頻段")

        for i, band in enumerate(adaptive_result.bands[:5]):
            with expander(
                f"頻段 {i+1}: {band['start_freq']:.2f} - {band['end_freq']:.2f} GHz "
                f"(BW: {band['bandwidth']:.2f} GHz)",
                expanded=(i == 0)
            ):
                render_band_details(band)
    else:
        error("⚠️ 即使放寬閾值仍未找到頻段，請檢查數據品質")

    # 顯示單一指標最優頻段
    if thresholds['show_single_metric']:
        markdown("### 🎖️ 單一指標最優頻段")

        cols = columns(3)

        metrics = [
            ('IL 最優', adaptive_result.best_il_band, 'red', 'min_il'),
            ('RL 最優', adaptive_result.best_rl_band, 'blue', 'max_rl'),
            ('Z 匹配最優', adaptive_result.best_z_band, 'green', 'z_deviation')
        ]

        for col, (name, band, color, key_metric) in zip(cols, metrics):
            with col:
                if band:
                    markdown(f"""
                    <div style="border-left: 4px solid {color}; padding: 10px;
                                background-color: #f8f9fa; border-radius: 5px;">
                        <h4>{name}</h4>
                        <p><b>{band['start_freq']:.2f} - {band['end_freq']:.2f} GHz</b></p>
                        <p>帶寬: {band['bandwidth']:.2f} GHz</p>
                        <p>IL: {band['avg_il']:.2f} dB</p>
                        <p>RL: {band['avg_rl']:.2f} dB</p>
                        <p>Z: {band['avg_z']:.1f} Ω</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    info(f"未找到 {name} 頻段")

    # 顯示妥協方案
    if adaptive_result.compromise_bands:
        markdown("### 🔄 妥協方案")

        for compromise in adaptive_result.compromise_bands:
            with expander(f"{compromise['name']}: {compromise['description']}"):
                for i, band in enumerate(compromise['bands'][:3]):
                    markdown(f"""
                    <div class="compromise-band">
                        <b>選項 {i+1}:</b> {band['start_freq']:.2f} - {band['end_freq']:.2f} GHz
                        (BW: {band['bandwidth']:.2f} GHz, 品質: {band['quality_score']:.3f})
                    </div>
                    """, unsafe_allow_html=True)

def render_band_details(band: Dict):
    """渲染頻段詳細資訊"""
    cols = columns(4)

    with cols[0]:
        markdown(f"""
        **頻段資訊**
        - 起始: {band['start_freq']:.3f} GHz
        - 結束: {band['end_freq']:.3f} GHz
        - 中心: {band['center_freq']:.3f} GHz
        - 帶寬: {band['bandwidth']:.3f} GHz
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
        - 平均 Z_diff: {band['avg_z']:.1f} Ω
        - 最大偏差: {band['z_deviation']:.1f} Ω
        - 模式轉換: {band['avg_mode_conv']:.1f} dB
        """)

    with cols[3]:
        # 品質評級
        score = band['quality_score']
        if score > 0.8:
            rating = "🟢 優秀"
            color = "green"
        elif score > 0.6:
            rating = "🟡 良好"
            color = "orange"
        elif score > 0.4:
            rating = "🟠 一般"
            color = "darkorange"
        else:
            rating = "🔴 較差"
            color = "red"

        markdown(f"""
        **綜合評級**
        - 品質分數: {score:.3f}
        - 評級: <span style="color: {color}; font-weight: bold;">{rating}</span>
        """, unsafe_allow_html=True)

def render_sparam_plots_with_adaptive(result, adaptive_result, freq_ghz):
    """渲染帶有 Adaptive 標記的 S 參數圖"""

    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            '差分回波損耗 (Sdd11)',
            '差分插入損耗 (Sdd21)',
            '共模回波損耗 (Scc11)',
            '模式轉換 (Scd21)',
            '品質分數地圖',
            '差分阻抗'
        ),
        vertical_spacing=0.1
    )

    # Sdd11
    fig.add_trace(
        Scatter(x=freq_ghz, y=result['rl_db'], mode='lines',
                   name='RL', line=dict(color='blue', width=2)),
        row=1, col=1
    )

    # Sdd21
    fig.add_trace(
        Scatter(x=freq_ghz, y=result['il_db'], mode='lines',
                   name='IL', line=dict(color='red', width=2)),
        row=1, col=2
    )

    # Scc11
    scc11_db = -20 * log10(abs(result['scc11']) + 1e-12)
    fig.add_trace(
        Scatter(x=freq_ghz, y=scc11_db, mode='lines',
                   name='Scc11', line=dict(color='purple', width=1)),
        row=2, col=1
    )

    # Scd21
    scd21_db = -20 * log10(abs(result['scd21']) + 1e-12)
    fig.add_trace(
        Scatter(x=freq_ghz, y=scd21_db, mode='lines',
                   name='Mode Conv', line=dict(color='brown', width=2)),
        row=2, col=2
    )

    # 品質分數
    # 重新計算品質分數
    il_norm = clip((3.0 - result['il_db']) / 3.0, 0, 1)
    rl_norm = clip((result['rl_db'] - 10.0) / 20.0, 0, 1)
    z_norm = clip(1.0 - abs(result['z_diff_real'] - 100.0) / 20.0, 0, 1)
    mode_norm = clip((scd21_db - 15.0) / 25.0, 0, 1)
    quality = 0.3 * il_norm + 0.3 * rl_norm + 0.2 * z_norm + 0.2 * mode_norm

    fig.add_trace(
        Scatter(x=freq_ghz, y=quality, mode='lines', fill='tozeroy',
                   name='Quality', line=dict(color='green'),
                   fillcolor='rgba(0,255,0,0.2)'),
        row=3, col=1
    )

    # 差分阻抗
    fig.add_trace(
        Scatter(x=freq_ghz, y=result['z_diff_real'], mode='lines',
                   name='Z_diff', line=dict(color='green', width=2)),
        row=3, col=2
    )
    fig.add_hline(y=100, line_dash="dash", line_color="black", row=3, col=2)

    # 標記所有類型的頻段
    colors = {
        'adaptive': 'rgba(0,255,0,0.2)',
        'il_best': 'rgba(255,0,0,0.15)',
        'rl_best': 'rgba(0,0,255,0.15)',
        'z_best': 'rgba(0,255,0,0.15)',
        'compromise': 'rgba(255,165,0,0.15)'
    }

    # Adaptive 頻段
    for band in adaptive_result.bands[:3]:
        for row in range(1, 4):
            for col in range(1, 3):
                fig.add_vrect(
                    x0=band['start_freq'], x1=band['end_freq'],
                    fillcolor=colors['adaptive'], opacity=0.5,
                    layer="below", line_width=0,
                    row=row, col=col
                )

    # 單一指標頻段
    single_bands = [
        (adaptive_result.best_il_band, colors['il_best']),
        (adaptive_result.best_rl_band, colors['rl_best']),
        (adaptive_result.best_z_band, colors['z_best'])
    ]

    for band, color in single_bands:
        if band:
            for row in range(1, 4):
                for col in range(1, 3):
                    fig.add_vrect(
                        x0=band['start_freq'], x1=band['end_freq'],
                        fillcolor=color, opacity=0.3,
                        layer="below", line_width=0,
                        row=row, col=col
                    )

    fig.update_layout(
        height=900,
        showlegend=True,
        title_text="S 參數分析（綠色=Adaptive頻段, 紅/藍/淺綠=單一指標最優）"
    )

    fig.update_xaxes(title_text="頻率 (GHz)")

    plotly_chart(fig, use_container_width=True)

MENU, 表單=[], ['主動式', '', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  狀態=empty()
  thresholds = render_sidebar()
  狀態.code([thresholds])
if menu==len(表單): #
  pass
elif menu==MENU[1]: #
  pass
elif menu==MENU[0]: #主動式
  pass
#def main():
    #uploaded_file = render_upload_section()

    #if uploaded_file is not None:
        #try:
            #with spinner("正在分析 S4P 文件..."):
                # 載入和分析
  根=Path('.')
  資檔=根.glob('*.s4p')
  檔=radio('s4p', 資檔, horizontal=True)
  analyzer = S4PAnalyzer(z0=50.0, target_z_diff=thresholds['z_target'])

  network = analyzer.load_s4p(檔) #uploaded_file.getvalue()

  # 混合模式轉換
  mixed = analyzer.convert_to_mixed_mode(network)
  sdd11 = mixed['sdd'][:, 0, 0]
  sdd21 = mixed['sdd'][:, 1, 0]
  scc11 = mixed['scc'][:, 0, 0]
  scd21 = mixed['scd'][:, 1, 0]

  # 計算參數
  z_result = analyzer.calculate_impedance(sdd11, scc11)
  loss_result = analyzer.calculate_losses(sdd21, sdd11)

  freq_ghz = network.frequency.f / 1e9

  result = {
      'frequency': network.frequency.f,
      'sdd11': sdd11,
      'sdd21': sdd21,
      'scc11': scc11,
      'scd21': scd21,
      'z_diff_real': z_result['z_diff_real'],
      'z_diff_imag': z_result['z_diff_imag'],
      'il_db': loss_result['il_db'],
      'rl_db': loss_result['rl_db']
  }

  # Adaptive 分析
  if thresholds['enable_adaptive']:
      adaptive_finder = AdaptiveBandFinder(network.frequency.f, loss_result['il_db'], loss_result['rl_db'], z_result['z_diff_real'], -20 * log10(abs(scd21) + 1e-12), target_z=thresholds['z_target'])

      adaptive_result = adaptive_finder.find_adaptive_bands(initial_il=thresholds['il_threshold'], initial_rl=thresholds['rl_threshold'], initial_z_tol=thresholds['z_tolerance'], initial_mode=thresholds['mode_conv_threshold'], min_band_width_ghz=thresholds['min_band_width'])
  else:
      # 非 adaptive 模式，使用原始閾值
      adaptive_result = AdaptiveBandFinder(
          network.frequency.f,
          loss_result['il_db'],
          loss_result['rl_db'],
          z_result['z_diff_real'],
          -20 * log10(abs(scd21) + 1e-12),
          target_z=thresholds['z_target']
      ).find_adaptive_bands(
          initial_il=thresholds['il_threshold'],
          initial_rl=thresholds['rl_threshold'],
          initial_z_tol=thresholds['z_tolerance'],
          initial_mode=thresholds['mode_conv_threshold'],
          max_iterations=0  # 不進行自適應調整
      )

  # 顯示結果
  markdown("## 📊 分析摘要")

  col1, col2, col3, col4 = columns(4)

  with col1:
      metric("頻率範圍",
               f"{freq_ghz[0]:.2f} - {freq_ghz[-1]:.2f} GHz")

  with col2:
      min_il_idx = argmin(loss_result['il_db'])
      metric("最佳 IL",
               f"{loss_result['il_db'][min_il_idx]:.2f} dB",
               f"@ {freq_ghz[min_il_idx]:.2f} GHz")

  with col3:
      max_rl_idx = argmax(loss_result['rl_db'])
      metric("最佳 RL",
               f"{loss_result['rl_db'][max_rl_idx]:.2f} dB",
               f"@ {freq_ghz[max_rl_idx]:.2f} GHz")

  with col4:
      avg_z = mean(z_result['z_diff_real'])
      metric("平均 Z_diff",
               f"{avg_z:.1f} Ω",
               f"偏差 {avg_z - thresholds['z_target']:.1f} Ω")

  # Adaptive 結果
  if thresholds['enable_adaptive']:
      render_adaptive_results(adaptive_result, thresholds, freq_ghz)

  # S 參數圖表
  render_sparam_plots_with_adaptive(result, adaptive_result, freq_ghz)

  # 數據匯出
  markdown("## 💾 數據匯出")

  col1, col2 = columns(2)

  with col1:
      # 匯出所有頻段
      all_bands = []
      all_bands.extend([{**b, 'type': 'adaptive'} for b in adaptive_result.bands])

      if adaptive_result.best_il_band:
          all_bands.append({**adaptive_result.best_il_band, 'type': 'IL_best'})
      if adaptive_result.best_rl_band:
          all_bands.append({**adaptive_result.best_rl_band, 'type': 'RL_best'})
      if adaptive_result.best_z_band:
          all_bands.append({**adaptive_result.best_z_band, 'type': 'Z_best'})

      for comp in adaptive_result.compromise_bands:
          for b in comp['bands']:
              all_bands.append({**b, 'type': f"compromise_{comp['priority']}"})

      if all_bands:
          df_bands = DataFrame(all_bands)
          download_button(
              "下載所有頻段 CSV",
              df_bands.to_csv(index=False),
              "all_bands.csv",
              "text/csv"
          )

  with col2:
      # 閾值歷程
      if len(adaptive_result.threshold_history) > 1:
          df_history = DataFrame(adaptive_result.threshold_history)
          download_button(
              "下載閾值調整歷程 CSV",
              df_history.to_csv(index=False),
              "threshold_history.csv",
              "text/csv"
          )

        #except Exception as e:
        #    error(f"分析錯誤: {str(e)}")
        #    exception(e)
with sidebar:
        info("👆 請上傳 S4P 文件開始分析")

        # 顯示功能說明
        with expander("🔍 Adaptive 移動波段功能說明", expanded=True):
            markdown("""
            ### 功能特色

            **1. 自動閾值調整**
            - 當原始閾值找不到頻段時，系統自動逐步放寬條件
            - 輪流放寬 IL、RL、Z 容差、模式轉換等指標
            - 記錄完整調整歷程供參考

            **2. 單一指標最優頻段**
            - **IL 最優**: 找出插入損耗最低的連續頻段
            - **RL 最優**: 找出回波損耗最高的連續頻段
            - **Z 匹配最優**: 找出阻抗最接近目標的連續頻段

            **3. 妥協方案**
            - **低損耗優先**: 保持 IL 嚴格，放寬其他指標
            - **高匹配優先**: 保持 RL 嚴格，放寬其他指標
            - **阻抗匹配優先**: 保持 Z 嚴格，放寬其他指標
            - **最大可用頻段**: 放寬所有指標，找出最大範圍

            **4. 品質評分機制**
            - 綜合考慮 IL、RL、Z、模式轉換四項指標
            - 加權計算品質分數（0-1）
            - 便於比較不同頻段的優劣
            """)

if __name__ == "__main__": main()
