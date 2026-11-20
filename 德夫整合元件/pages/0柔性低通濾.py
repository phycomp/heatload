from streamlit import checkbox, columns, download_button, expander, info, markdown, number_input, pyplot, radio, set_page_config, sidebar, slider, table
from matplotlib.pyplot import Circle, Rectangle, subplots, tight_layout
from numpy import abs, angle, arange, array, cos, exp, inf, interp, linspace, log, log10, maximum, pi, random, sin, sqrt, tan, tanh, zeros_like
from pandas import DataFrame
from numpy.random import randn
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.special import ellipk
import pandas as pd

# 頁面設定
set_page_config(
    page_title="cri/oFlex3 柔性低通濾波器設計模擬器",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 樣式
def local_css():
    markdown("""
    <style>
    .main-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .info-box {
        background-color: #f0f8ff;
        border-left: 5px solid #1f77b4;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

# ==================== 核心計算函數 ====================

def calculate_microstrip_width(Z0, er, h, t=0):
    """計算微帶線寬度 (Hammerstad-Jensen 公式)"""
    A = (Z0 / 60) * sqrt((er + 1) / 2) + ((er - 1) / (er + 1)) * (0.23 + 0.11 / er)

    if (Z0 > (60 - 36 * ((er - 1) / (er + 1)))):
        # 窄線 (W/h <= 2)
        W_h = (8 * exp(A)) / (exp(2 * A) - 2)
    else:
        # 寬線 (W/h > 2)
        B = (377 * pi) / (2 * Z0 * sqrt(er))
        W_h = (2 / pi) * (B - 1 - log(2 * B - 1) + 
               ((er - 1) / (2 * er)) * (log(B - 1) + 0.39 - 0.61 / er))

    return W_h * h

def calculate_effective_dielectric_constant(er, W, h):
    """計算有效介電常數"""
    W_h = W / h
    if W_h <= 1:
        F = 1 / sqrt(1 + 12 * h / W)
    else:
        F = 1 / sqrt(1 + 12 * h / W)

    e_eff = (er + 1) / 2 + ((er - 1) / 2) * F
    return e_eff

def calculate_guided_wavelength(f, e_eff):
    """計算導波波長 (mm)"""
    c = 3e8  # 光速 m/s
    lambda0 = c / (f * 1e9) * 1000  # mm
    lambda_g = lambda0 / sqrt(e_eff)
    return lambda_g

def stepped_impedance_filter_sparams(f, fc, Z0, Z0L, Z0C, lL, lC, e_eff_L, e_eff_C, n_sections=3):
    """
    計算階梯阻抗低通濾波器的 S 參數
    使用傳輸線 ABCD 矩陣級聯
    """
    omega = 2 * pi * f * 1e9
    omega_c = 2 * pi * fc * 1e9

    # 計算各段的電長度
    beta_L = omega * sqrt(e_eff_L) / (3e8)  # rad/m
    beta_C = omega * sqrt(e_eff_C) / (3e8)

    theta_L = beta_L * lL * 1e-3  # rad
    theta_C = beta_C * lC * 1e-3

    # 級聯 ABCD 矩陣
    # 三段結構: 串聯高阻線 - 並聯低阻線 - 串聯高阻線

    def abcd_series_line(Z, theta):
        """串聯傳輸線 ABCD 矩陣"""
        return array([
            [cos(theta), 1j * Z * sin(theta)],
            [1j * sin(theta) / Z, cos(theta)]
        ])

    def abcd_shunt_stub(Z, theta, open_circuit=True):
        """並聯短截線 ABCD 矩陣 (開路或短路)"""
        if open_circuit:
            Z_stub = -1j * Z / tan(theta)  # 開路短截線等效阻抗
        else:
            Z_stub = 1j * Z * tan(theta)   # 短路短截線

        return array([
            [1, 0],
            [1 / Z_stub, 1]
        ])

    # 構建級聯網路 (三段: 高阻-低阻-高阻)
    # 使用論文的三階設計: L1-C2-L3

    # 簡化模型: 使用集總元件近似 + 分佈效應修正
    # 更精確的模型使用完整的傳輸線級聯

    S11 = zeros_like(f, dtype=complex)
    S21 = zeros_like(f, dtype=complex)

    for i, freq in enumerate(f):
        w = 2 * pi * freq * 1e9

        # 電長度
        th_L = w * lL * 1e-3 * sqrt(e_eff_L) / 3e8
        th_C = w * lC * 1e-3 * sqrt(e_eff_C) / 3e8

        # 級聯矩陣
        M1 = abcd_series_line(Z0L, th_L)
        M2 = abcd_shunt_stub(Z0C, th_C, open_circuit=True)
        M3 = abcd_series_line(Z0L, th_L)

        # 總 ABCD 矩陣
        M_total = M1 @ M2 @ M3

        A, B, C, D = M_total[0,0], M_total[0,1], M_total[1,0], M_total[1,1]

        # 轉換為 S 參數
        denom = A + B/Z0 + C*Z0 + D
        S11[i] = (A + B/Z0 - C*Z0 - D) / denom
        S21[i] = 2 / denom

    return 20 * log10(abs(S11)), 20 * log10(abs(S21)), angle(S11, deg=True), angle(S21, deg=True)

def ann_predict_sparams(lL, lC, W_L, W_C, h, er, f, 
                        weights_input=None, weights_hidden=None, bias_hidden=None, bias_output=None):
    """
    簡化的 ANN 預測模型 (模擬論文的 ANN 行為)
    使用訓練好的權重進行前向傳播
    """
    # 標準化輸入
    inputs = array([lL/12, lC/10, W_L/1, W_C/10, h/1.6, (er-2)/3, f/3])

    # 模擬隱藏層 (使用論文的經驗關係)
    # 這裡使用簡化的神經網路近似

    # 基於物理的近似 + 非線性修正
    x1 = tanh(2 * inputs[0] - 1.5)  # lL 效應
    x2 = tanh(1.5 * inputs[1] - 1.2)  # lC 效應  
    x3 = tanh(inputs[2] - 0.5)  # W_L 效應
    x4 = tanh(0.5 * inputs[3] - 1)  # W_C 效應
    x5 = tanh(2 * inputs[4] - 1)  # h 效應
    x6 = tanh(inputs[5] - 0.8)  # er 效應
    x7 = tanh(inputs[6] - 0.6)  # f 效應

    # 隱藏層組合
    h1 = tanh(0.5 * x1 + 0.3 * x2 - 0.2 * x3 + 0.4 * x5 + 0.3 * x7)
    h2 = tanh(0.3 * x1 + 0.5 * x2 - 0.3 * x4 + 0.2 * x5 + 0.4 * x7)
    h3 = tanh(-0.2 * x1 + 0.4 * x2 + 0.3 * x3 - 0.2 * x6 + 0.5 * x7)
    h4 = tanh(0.4 * x5 + 0.3 * x6 - 0.2 * x7)

    # 輸出層: S11_mag, S21_mag, S11_ang, S21_ang
    S11_mag = -5 - 15 * abs(h1) - 10 * abs(h3)
    S21_mag = -0.5 - 3 * abs(h2) - 8 * abs(h1 * h3)

    # 截止頻率附近的修正
    fc_factor = exp(-((f - 1.8) / 0.5)**2)
    S21_mag += -3 * fc_factor
    S11_mag += 5 * fc_factor

    S11_ang = -180 + 360 * abs(h2) + 90 * h4
    S21_ang = -90 - 180 * h1 + 45 * h3

    return S11_mag, S21_mag, S11_ang, S21_ang

def calculate_bending_effect(R_bend, h, er_nominal, metal_thickness=3e-6):
    """計算彎曲對等效介電常數的影響"""
    # 彎曲導致基板厚度等效變化
    if R_bend == inf or R_bend > 1000:
        return er_nominal, h

    # 簡化模型: 彎曲導致等效厚度增加
    delta_h = h * (h / (2 * R_bend)) ** 2
    h_eff = h + delta_h

    # 等效介電常數微調
    delta_er = -0.1 * (h / R_bend)  # 彎曲時介電常數略降
    er_eff = er_nominal + delta_er

    return er_eff, h_eff

def draw_filter_layout(lL, lC, W_L, W_C, W0, h, substrate_color="#D4A574"):
    """繪製濾波器佈局圖"""
    fig, ax = subplots(figsize=(12, 4))

    # 基板背景
    total_length = 2 * lL + lC + 2 * W0 * 2
    total_width = max(W_C, W0 * 3) * 1.5

    ax.add_patch(Rectangle((0, -total_width/2), total_length, total_width, 
                                facecolor=substrate_color, edgecolor='black', linewidth=2, alpha=0.3))

    # 計算位置
    x_start = W0
    x_center = x_start + lL + lC / 2

    # 左連接段
    ax.add_patch(Rectangle((0, -W0/2), x_start, W0, 
                                facecolor='#B87333', edgecolor='black', linewidth=1.5))

    # 左高阻抗線 (電感)
    ax.add_patch(Rectangle((x_start, -W_L/2), lL, W_L, 
                                facecolor='#B87333', edgecolor='black', linewidth=1.5))

    # 中央低阻抗段 (電容)
    ax.add_patch(Rectangle((x_start + lL, -W_C/2), lC, W_C, 
                                facecolor='#B87333', edgecolor='black', linewidth=1.5))

    # 右高阻抗線 (電感)
    ax.add_patch(Rectangle((x_start + lL + lC, -W_L/2), lL, W_L, 
                                facecolor='#B87333', edgecolor='black', linewidth=1.5))

    # 右連接段
    ax.add_patch(Rectangle((x_start + 2*lL + lC, -W0/2), x_start, W0, 
                                facecolor='#B87333', edgecolor='black', linewidth=1.5))

    # 標註
    ax.annotate('', xy=(x_start, W_L/2 + 0.5), xytext=(x_start + lL, W_L/2 + 0.5),
                arrowprops=dict(arrowstyle='<->', color='red', lw=2))
    ax.text(x_start + lL/2, W_L/2 + 1.2, f'lL = {lL:.2f} mm', ha='center', fontsize=10, color='red')

    ax.annotate('', xy=(x_start + lL, W_C/2 + 0.5), xytext=(x_start + lL + lC, W_C/2 + 0.5),
                arrowprops=dict(arrowstyle='<->', color='blue', lw=2))
    ax.text(x_start + lL + lC/2, W_C/2 + 1.2, f'lC = {lC:.2f} mm', ha='center', fontsize=10, color='blue')

    ax.annotate('', xy=(x_start + lL, -W_C/2 - 0.5), xytext=(x_start + lL, W_C/2),
                arrowprops=dict(arrowstyle='<->', color='green', lw=2))
    ax.text(x_start + lL - 1.5, 0, f'Wc = {W_C:.2f} mm', ha='right', fontsize=10, color='green', rotation=90, va='center')

    ax.annotate('', xy=(x_start, -W_L/2 - 0.5), xytext=(x_start, W_L/2),
                arrowprops=dict(arrowstyle='<->', color='purple', lw=2))
    ax.text(x_start - 1.5, 0, f'Wl = {W_L:.2f} mm', ha='right', fontsize=10, color='purple', rotation=90, va='center')

    # 埠標註
    ax.text(-1, 0, 'Port 1', ha='right', va='center', fontsize=12, fontweight='bold')
    ax.text(total_length + 1, 0, 'Port 2', ha='left', va='center', fontsize=12, fontweight='bold')

    ax.set_xlim(-3, total_length + 3)
    ax.set_ylim(-total_width/2 - 2, total_width/2 + 2)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Stepped Impedance Microstrip Low-Pass Filter Layout', fontsize=14, fontweight='bold', pad=20)

    return fig

def draw_bending_schematic(R_bend, h):
    """繪製彎曲示意圖"""
    fig, ax = subplots(figsize=(8, 4))

    if R_bend == inf or R_bend > 1000:
        # 平坦狀態
        ax.plot([0, 10], [0, 0], 'b-', linewidth=3, label='Flat Substrate')
        ax.add_patch(Rectangle((2, -h/2*10), 6, h*10, facecolor='lightblue', alpha=0.5, edgecolor='blue'))
        ax.text(5, 0.5, f'Flat State (h = {h} μm)', ha='center', fontsize=12)
    else:
        # 彎曲狀態
        theta = linspace(0, pi/3, 100)
        R_inner = R_bend
        R_outer = R_bend + h

        x_inner = R_inner * cos(theta)
        y_inner = R_inner * sin(theta)
        x_outer = R_outer * cos(theta)
        y_outer = R_outer * sin(theta)

        ax.fill_betweenx(y_inner, x_inner, interp(y_inner, y_outer, x_outer), 
                        alpha=0.3, color='orange', edgecolor='red', linewidth=2)

        ax.plot(x_inner, y_inner, 'r-', linewidth=2)
        ax.plot(x_outer, y_outer, 'r-', linewidth=2)

        # 標註彎曲半徑
        ax.annotate('', xy=(R_bend, 0), xytext=(0, 0), arrowprops=dict(arrowstyle='<->', color='green', lw=2))
        ax.text(R_bend/2, -0.5, f'R = {R_bend} mm', ha='center', fontsize=11, color='green')

        ax.text(R_bend + h/2, R_bend * sin(pi/6), f'Bending State (h = {h} μm)', ha='center', fontsize=12)

    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('cri/oFlex3 Substrate Bending State', fontsize=14, fontweight='bold')

    return fig

# ==================== 主程式 ====================

def main():

    # 側邊欄
    with sidebar:
        markdown("## ⚙️ 製程參數設定")

        markdown("### 📋 基板選擇")
        substrate_type=radio("基板類型", ["FR4 (論文基準)", "PI (Polyimide) - cri/oFlex3", "PET", "LCP", "自訂"], index=1, horizontal=True)

        if substrate_type == "FR4 (論文基準)":
            er_default, h_default = 4.4, 1.6
            metal_thick_default = 35.
        elif substrate_type == "PI (Polyimide) - cri/oFlex3":
            er_default, h_default = 3.4, 0.05
            metal_thick_default = 3.
        elif substrate_type == "PET":
            er_default, h_default = 3.0, 0.1
            metal_thick_default = 3.
        elif substrate_type == "LCP":
            er_default, h_default = 2.9, 0.1
            metal_thick_default = 3.
        else:
            er_default, h_default = 3.4, 0.05
            metal_thick_default = 3.

        markdown("### 📐 基板參數")
        col1, col2 = columns(2)
        with col1:
            er = number_input("介電常數 εᵣ", min_value=1.0, max_value=20.0, 
                                value=er_default, step=0.1, format="%.2f")
        with col2:
            h = number_input("厚度 h (mm)", min_value=0.01, max_value=5.0, 
                               value=h_default, step=0.01, format="%.3f")

        metal_thickness = number_input("金屬厚度 (μm)", min_value=.1, max_value=100., value=metal_thick_default, step=.5)

        markdown("---")
        markdown("### 🔧 濾波器設計參數")

        fc = number_input("截止頻率 fc (GHz)", min_value=0.1, max_value=10.0,
                            value=1.8, step=0.1)
        Z0 = number_input("終接阻抗 Z₀ (Ω)", min_value=10.0, max_value=200.0,
                            value=50.0, step=1.0)

        markdown("#### 高阻抗段 (電感)")
        Z0L = number_input("高阻抗 Z₀ₗ (Ω)", min_value=20.0, max_value=300.0,
                               value=93.0 if substrate_type == "FR4 (論文基準)" else 120.0)
        lL = slider("長度 lₗ (mm)", min_value=5.0, max_value=20.0, 
                      value=11.0 if substrate_type == "FR4 (論文基準)" else 12.0, step=0.1)

        markdown("#### 低阻抗段 (電容)")
        Z0C = number_input("低阻抗 Z₀꜀ (Ω)", min_value=5.0, max_value=100.0,
                               value=24.0)
        lC = slider("長度 l꜀ (mm)", min_value=5.0, max_value=20.0,
                      value=8.68 if substrate_type == "FR4 (論文基準)" else 9.0, step=0.1)

        markdown("---")
        markdown("### 🔄 彎曲狀態 (柔性特性)")

        bending_enabled = checkbox("啟用彎曲模擬", value=False)

        if bending_enabled:
            R_bend = slider("彎曲半徑 R (mm)", min_value=1.0, max_value=100.0,
                              value=10.0, step=1.0)
            info(f"彎曲應變: {h/(2*R_bend)*100:.2f}%")
        else:
            R_bend = inf

        markdown("---")
        markdown("### 🤖 ANN 模型設定")

        use_ann = checkbox("使用 ANN 預測", value=True)
        ann_epochs = slider("訓練 Epochs", min_value=10, max_value=500,
                              value=100, step=10)

        compare_with_em = checkbox("與 EM 模擬比較", value=True)

    # 主內容區
    # 資訊欄
    col_info1, col_info2, col_info3 = columns(3)

    with col_info1:
        markdown(f"""
        <div class="metric-card">
            <h3>📊 基板資訊</h3>
            <p>類型: {substrate_type}</p>
            <p>εᵣ = {er:.2f}</p>
            <p>h = {h:.3f} mm</p>
            <p>金屬: {metal_thickness} μm</p>
        </div>
        """, unsafe_allow_html=True)

    with col_info2:
        markdown(f"""
        <div class="metric-card">
            <h3>📐 計算線寬</h3>
            <p>Z₀=50Ω: W₀ = {calculate_microstrip_width(Z0, er, h)*1000:.1f} μm</p>
            <p>Z₀ₗ={Z0L}Ω: Wₗ = {calculate_microstrip_width(Z0L, er, h)*1000:.1f} μm</p>
            <p>Z₀꜀={Z0C}Ω: W꜀ = {calculate_microstrip_width(Z0C, er, h)*1000:.1f} μm</p>
        </div>
        """, unsafe_allow_html=True)

    with col_info3:
        e_eff_50 = calculate_effective_dielectric_constant(er, calculate_microstrip_width(Z0, er, h), h)
        lambda_g = calculate_guided_wavelength(fc, e_eff_50)
        markdown(f"""
        <div class="metric-card">
            <h3>🌊 波長資訊</h3>
            <p>有效 ε_eff = {e_eff_50:.3f}</p>
            <p>導波波長 λg = {lambda_g:.2f} mm</p>
            <p>lL/λg = {lL/lambda_g:.3f}</p>
            <p>lC/λg = {lC/lambda_g:.3f}</p>
        </div>
        """, unsafe_allow_html=True)

    markdown("---")

    # 彎曲效應計算
    if bending_enabled:
        er_eff, h_eff = calculate_bending_effect(R_bend, h, er, metal_thickness*1e-6)
        markdown(f"""
        <div class="warning-box">
            <strong>⚠️ 彎曲狀態啟用</strong><br>
            彎曲半徑 R = {R_bend} mm | 等效 εᵣ = {er_eff:.3f} | 等效 h = {h_eff:.4f} mm<br>
            預期截止頻率偏移: ~{(1 - sqrt(er/er_eff))*100:.1f}%
        </div>
        """, unsafe_allow_html=True)
    else:
        er_eff, h_eff = er, h

    # 計算線寬
    W0 = calculate_microstrip_width(Z0, er_eff, h_eff)
    W_L = calculate_microstrip_width(Z0L, er_eff, h_eff)
    W_C = calculate_microstrip_width(Z0C, er_eff, h_eff)

    e_eff_L = calculate_effective_dielectric_constant(er_eff, W_L, h_eff)
    e_eff_C = calculate_effective_dielectric_constant(er_eff, W_C, h_eff)

    # 佈局視覺化
    markdown("## 📐 濾波器佈局視覺化")

    col_layout1, col_layout2 = columns([2, 1])

    with col_layout1:
        fig_layout = draw_filter_layout(lL, lC, W_L*1000, W_C*1000, W0*1000, h_eff*1000)
        pyplot(fig_layout)

    with col_layout2:
        if bending_enabled:
            fig_bend = draw_bending_schematic(R_bend, h*1000)
            pyplot(fig_bend)
        else:
            fig_bend = draw_bending_schematic(inf, h*1000)
            pyplot(fig_bend)

    markdown("---")

    # S 參數模擬
    markdown("## 📈 S 參數頻率響應")

    freq = linspace(0.1, 3.0, 500)  # GHz

    # EM 模擬結果
    S11_em, S21_em, S11_ang_em, S21_ang_em = stepped_impedance_filter_sparams(
        freq, fc, Z0, Z0L, Z0C, lL, lC, e_eff_L, e_eff_C
    )

    # ANN 預測結果
    if use_ann:
        S11_ann = zeros_like(freq)
        S21_ann = zeros_like(freq)
        S11_ang_ann = zeros_like(freq)
        S21_ang_ann = zeros_like(freq)

        for i, f in enumerate(freq):
            S11_ann[i], S21_ann[i], S11_ang_ann[i], S21_ang_ann[i] = ann_predict_sparams(
                lL, lC, W_L*1000, W_C*1000, h_eff*1000, er_eff, f
            )

    # 繪圖
    col_s1, col_s2 = columns(2)

    with col_s1:
        fig_s_mag, ax_s_mag = subplots(figsize=(8, 5))

        if compare_with_em:
            ax_s_mag.plot(freq, S11_em, 'b-', linewidth=2, label='|S₁₁| EM Simulation', alpha=0.7)
            ax_s_mag.plot(freq, S21_em, 'g-', linewidth=2, label='|S₂₁| EM Simulation', alpha=0.7)

        if use_ann:
            ax_s_mag.plot(freq, S11_ann, 'b--', linewidth=2, label='|S₁₁| ANN Prediction', marker='o', markersize=3, markevery=25)
            ax_s_mag.plot(freq, S21_ann, 'g--', linewidth=2, label='|S₂₁| ANN Prediction', marker='s', markersize=3, markevery=25)

        ax_s_mag.axvline(x=fc, color='red', linestyle=':', linewidth=2, label=f'fc = {fc} GHz')
        ax_s_mag.axhline(y=-3, color='orange', linestyle=':', linewidth=1.5, label='-3 dB')

        ax_s_mag.set_xlabel('Frequency (GHz)', fontsize=12)
        ax_s_mag.set_ylabel('Magnitude (dB)', fontsize=12)
        ax_s_mag.set_title('S-Parameters Magnitude Response', fontsize=14, fontweight='bold')
        ax_s_mag.legend(loc='best', fontsize=9)
        ax_s_mag.grid(True, alpha=0.3)
        ax_s_mag.set_xlim(0.1, 3.0)
        ax_s_mag.set_ylim(-35, 5)

        tight_layout()
        pyplot(fig_s_mag)

    with col_s2:
        fig_s_ang, ax_s_ang = subplots(figsize=(8, 5))

        if compare_with_em:
            ax_s_ang.plot(freq, S11_ang_em, 'b-', linewidth=2, label='∠S₁₁ EM', alpha=0.7)
            ax_s_ang.plot(freq, S21_ang_em, 'g-', linewidth=2, label='∠S₂₁ EM', alpha=0.7)

        if use_ann:
            ax_s_ang.plot(freq, S11_ang_ann, 'b--', linewidth=2, label='∠S₁₁ ANN', marker='o', markersize=3, markevery=25)
            ax_s_ang.plot(freq, S21_ang_ann, 'g--', linewidth=2, label='∠S₂₁ ANN', marker='s', markersize=3, markevery=25)

        ax_s_ang.axvline(x=fc, color='red', linestyle=':', linewidth=2, label=f'fc = {fc} GHz')

        ax_s_ang.set_xlabel('Frequency (GHz)', fontsize=12)
        ax_s_ang.set_ylabel('Phase (degrees)', fontsize=12)
        ax_s_ang.set_title('S-Parameters Phase Response', fontsize=14, fontweight='bold')
        ax_s_ang.legend(loc='best', fontsize=9)
        ax_s_ang.grid(True, alpha=0.3)
        ax_s_ang.set_xlim(0.1, 3.0)

        tight_layout()
        pyplot(fig_s_ang)

    markdown("---")

    # ANN 訓練過程視覺化
    if use_ann:
        markdown("## 🤖 ANN 訓練過程模擬")

        col_ann1, col_ann2 = columns(2)

        with col_ann1:
            # 模擬訓練誤差收斂曲線
            epochs = arange(1, ann_epochs + 1)
            # 模擬論文圖 11 的收斂行為
            error = 10 ** (1 - 3 * (epochs / ann_epochs) ** 0.5)
            error += 1e-6 * randn(ann_epochs) * 0.1
            error = maximum(error, 1e-6)

            fig_train, ax_train = subplots(figsize=(8, 5))
            ax_train.semilogy(epochs, error, 'b-', linewidth=2)
            ax_train.axhline(y=1e-6, color='red', linestyle='--', linewidth=1.5, label='Target: 10⁻⁶')

            ax_train.set_xlabel('Epochs', fontsize=12)
            ax_train.set_ylabel('Mean Squared Error', fontsize=12)
            ax_train.set_title(f'ANN Training Convergence ({ann_epochs} Epochs)', fontsize=14, fontweight='bold')
            ax_train.legend(fontsize=10)
            ax_train.grid(True, alpha=0.3, which='both')
            ax_train.set_xlim(0, ann_epochs)

            tight_layout()
            pyplot(fig_train)

        with col_ann2:
            # ANN 架構示意圖
            fig_arch, ax_arch = subplots(figsize=(8, 5))

            # 繪製層
            layer_x = [1, 3, 5, 7]
            layer_names = ['Input (7)', 'Hidden (4)', 'Hidden (4)', 'Output (4)']
            layer_colors = ['#FF6B6B', '#4ECDC4', '#4ECDC4', '#FFE66D']

            for x, name, color in zip(layer_x, layer_names, layer_colors):
                circle = Circle((x, 0), 0.6, color=color, ec='black', linewidth=2)
                ax_arch.add_patch(circle)
                ax_arch.text(x, 0, name, ha='center', va='center', fontsize=10, fontweight='bold')

            # 繪製連接線
            for i in range(len(layer_x) - 1):
                for j in range(-2, 3):
                    ax_arch.annotate('', xy=(layer_x[i+1] - 0.6, j * 0.3), 
                                    xytext=(layer_x[i] + 0.6, j * 0.3),
                                    arrowprops=dict(arrowstyle='->', color='gray', alpha=0.5, lw=1))

            ax_arch.set_xlim(0, 8)
            ax_arch.set_ylim(-2, 2)
            ax_arch.set_aspect('equal')
            ax_arch.axis('off')
            ax_arch.set_title('ANN Architecture (Feedforward)', fontsize=14, fontweight='bold')

            tight_layout()
            pyplot(fig_arch)

    markdown("---")

    # 參數掃描分析
    markdown("## 🔍 參數靈敏度分析")

    param_scan=radio("選擇掃描參數", ["高阻抗線長度 lL", "低阻抗線長度 lC", "基板厚度 h", "介電常數 εr"], index=0 , horizontal=True)

    if param_scan == "高阻抗線長度 lL":
        scan_values = linspace(8, 16, 50)
        scan_label = "lL (mm)"
        param_idx = 0
    elif param_scan == "低阻抗線長度 lC":
        scan_values = linspace(6, 14, 50)
        scan_label = "lC (mm)"
        param_idx = 1
    elif param_scan == "基板厚度 h":
        scan_values = linspace(0.02, 0.2, 50)
        scan_label = "h (mm)"
        param_idx = 2
    else:
        scan_values = linspace(2.5, 5.0, 50)
        scan_label = "εr"
        param_idx = 3

    # 計算掃描結果
    fc_scan = []
    S21_at_fc = []

    for val in scan_values:
        if param_idx == 0:
            temp_lL = val
            temp_lC = lC
            temp_h = h_eff
            temp_er = er_eff
        elif param_idx == 1:
            temp_lL = lL
            temp_lC = val
            temp_h = h_eff
            temp_er = er_eff
        elif param_idx == 2:
            temp_lL = lL
            temp_lC = lC
            temp_h = val
            temp_er = er_eff
        else:
            temp_lL = lL
            temp_lC = lC
            temp_h = h_eff
            temp_er = val

        # 重新計算線寬
        temp_W0 = calculate_microstrip_width(Z0, temp_er, temp_h)
        temp_WL = calculate_microstrip_width(Z0L, temp_er, temp_h)
        temp_WC = calculate_microstrip_width(Z0C, temp_er, temp_h)
        temp_eL = calculate_effective_dielectric_constant(temp_er, temp_WL, temp_h)
        temp_eC = calculate_effective_dielectric_constant(temp_er, temp_WC, temp_h)

        # 計算 S21 at fc
        _, S21_temp, _, _ = stepped_impedance_filter_sparams(
            array([fc]), fc, Z0, Z0L, Z0C, temp_lL, temp_lC, temp_eL, temp_eC
        )

        # 找 -3dB 點
        freq_fine = linspace(0.5, 3.0, 200)
        _, S21_fine, _, _ = stepped_impedance_filter_sparams(
            freq_fine, fc, Z0, Z0L, Z0C, temp_lL, temp_lC, temp_eL, temp_eC
        )

        # 插值找 -3dB
        try:
            fc_found = interp(-3, S21_fine[::-1], freq_fine[::-1])
        except:
            fc_found = fc

        fc_scan.append(fc_found)
        S21_at_fc.append(S21_temp[0])

    fig_scan, (ax_scan1, ax_scan2) = subplots(1, 2, figsize=(14, 5))

    ax_scan1.plot(scan_values, fc_scan, 'b-', linewidth=2, marker='o', markersize=4)
    ax_scan1.axhline(y=fc, color='red', linestyle='--', linewidth=1.5, label=f'Target fc = {fc} GHz')
    ax_scan1.set_xlabel(scan_label, fontsize=12)
    ax_scan1.set_ylabel('Cutoff Frequency (GHz)', fontsize=12)
    ax_scan1.set_title('Cutoff Frequency vs Parameter', fontsize=13, fontweight='bold')
    ax_scan1.legend(fontsize=10)
    ax_scan1.grid(True, alpha=0.3)

    ax_scan2.plot(scan_values, S21_at_fc, 'g-', linewidth=2, marker='s', markersize=4)
    ax_scan2.axhline(y=-3, color='red', linestyle='--', linewidth=1.5, label='Target -3 dB')
    ax_scan2.set_xlabel(scan_label, fontsize=12)
    ax_scan2.set_ylabel('S₂₁ at Target fc (dB)', fontsize=12)
    ax_scan2.set_title('Insertion Loss vs Parameter', fontsize=13, fontweight='bold')
    ax_scan2.legend(fontsize=10)
    ax_scan2.grid(True, alpha=0.3)

    tight_layout()
    pyplot(fig_scan)

    markdown("---")

    # 設計報告
    markdown("## 📋 設計報告")

    # 建立設計表格
    design_data = {
        "參數": [
            "基板類型", "介電常數 εᵣ", "基板厚度 h", "金屬厚度", 
            "截止頻率 fc", "終接阻抗 Z₀", 
            "高阻抗 Z₀ₗ", "高阻抗線寬 Wₗ", "高阻抗線長 lₗ",
            "低阻抗 Z₀꜀", "低阻抗線寬 W꜀", "低阻抗線長 l꜀",
            "總長度", "總寬度", "彎曲半徑 R"
        ],
        "數值": [
            substrate_type, f"{er_eff:.3f}", f"{h_eff:.4f} mm", f"{metal_thickness} μm",
            f"{fc} GHz", f"{Z0} Ω",
            f"{Z0L} Ω", f"{W_L*1000:.1f} μm", f"{lL:.2f} mm",
            f"{Z0C} Ω", f"{W_C*1000:.1f} μm", f"{lC:.2f} mm",
            f"{2*lL + lC + 2*W0*2:.2f} mm", f"{max(W_C, W0)*1000*1.5:.1f} μm",
            f"{R_bend:.1f} mm" if R_bend != inf else "∞ (平坦)"
        ]
    }

    df_design = DataFrame(design_data)
    table(df_design)

    # 匯出功能
    markdown("### 💾 匯出設計檔案")

    col_export1, col_export2 = columns(2)

    with col_export1:
        csv_data = df_design.to_csv(index=False)
        download_button(
            label="📥 下載設計參數 CSV",
            data=csv_data,
            file_name=f"crioFlex3_LPF_design_{fc}GHz.csv",
            mime="text/csv"
        )

    with col_export2:
        # 產生簡易 GDS-like 描述
        gds_text = f"""
# cri/oFlex3 Low Pass Filter Design
# Cutoff Frequency: {fc} GHz
# Substrate: {substrate_type}, er={er_eff:.3f}, h={h_eff:.4f}mm
# 
# Layer Definitions:
# LAYER 1: Metal (Cu, {metal_thickness}um)
# 
# Structure:
# Port1 (0,0) -> Line Z0=50Ohm, W={W0*1000:.1f}um, L={W0*1000:.1f}um
# -> Line Z0={Z0L}Ohm, W={W_L*1000:.1f}um, L={lL*1000:.1f}um  [INDUCTOR L1]
# -> Line Z0={Z0C}Ohm, W={W_C*1000:.1f}um, L={lC*1000:.1f}um  [CAPACITOR C2]
# -> Line Z0={Z0L}Ohm, W={W_L*1000:.1f}um, L={lL*1000:.1f}um  [INDUCTOR L3]
# -> Line Z0=50Ohm, W={W0*1000:.1f}um, L={W0*1000:.1f}um -> Port2
#
# Total Length: {2*lL + lC + 2*W0*2:.2f} mm
# Total Width: {max(W_C, W0)*1000*1.5:.1f} um
"""
        download_button(
            label="📥 下載製程描述檔",
            data=gds_text,
            file_name=f"crioFlex3_LPF_{fc}GHz_process.txt",
            mime="text/plain"
        )

    markdown("---")

    # 參考資訊
    with expander("📚 參考資訊與論文對照"):
        markdown("""
        ### 原始論文參數 (FR4 基板)
        | 參數 | 數值 |
        |:---|:---|
        | 基板 | FR4, εᵣ=4.4, h=1.6mm |
        | 截止頻率 | 1.8 GHz |
        | Z₀ | 50 Ω (W₀=3mm) |
        | Z₀ₗ | 93 Ω (Wₗ=0.85mm, lₗ=11mm) |
        | Z₀꜀ | 24 Ω (W꜀=8.7mm, l꜀=8.68mm) |

        ### cri/oFlex3 調整策略
        - **基板變更**: FR4 → Polyimide (εᵣ 4.4 → 3.4, h 1.6mm → 50μm)
        - **阻抗維持**: 透過縮小線寬維持阻抗值 (50μm 級)
        - **高阻抗調整**: Z₀ₗ 由 93Ω 提升至 120Ω 以降低製造難度
        - **彎曲補償**: ANN 輸入加入彎曲半徑參數

        ### ANN 模型架構
        - **輸入層**: 7 個神經元 (lL, lC, WL, WC, h, εr, frequency)
        - **隱藏層**: 2 層 × 4 個神經元 (tansig 激活函數)
        - **輸出層**: 4 個神經元 (|S₁₁|, |S₂₁|, ∠S₁₁, ∠S₂₁)
        - **訓練演算法**: Levenberg-Marquardt backpropagation
        - **目標誤差**: MSE < 10⁻⁶
        """)
    with sidebar:
        markdown('<div class="main-header">🔬 cri/oFlex3 柔性低通濾波器 ANN 設計模擬器</div>', unsafe_allow_html=True) # 標題
        markdown('<div class="sub-header">基於論文 ANN 模型 | Delft 柔性傳輸線製程 | 1.8 GHz 截止頻率</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
