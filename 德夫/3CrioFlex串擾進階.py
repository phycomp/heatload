from streamlit import caption, columns, dataframe, download_button, error, expander, info, markdown, number_input, plotly_chart, set_page_config, sidebar, slider, subheader, success, tabs, title, empty, radio
from numpy import array, ceil, exp, linspace, log, log10, logspace, random, sqrt, zeros, zeros_like
from numpy.random import normal, uniform
from pandas import DataFrame
from plotly.graph_objects import Figure, Scatter
from 撓性Util import calc_flexible_crosstalk_modification, calc_flexible_bending_effects
# app_advanced.py - Cri/oFlex 進階量子串擾模擬器
#import streamlit as st
#import numpy as np
#import plotly.graph_objects as go
from plotly.express import imshow, bar
from scipy.constants import k, c, mu_0, epsilon_0, h, pi
from scipy.special import erf
#import pandas as pd

狀態=empty()
set_page_config(page_title="Cri/oFlex 量子進階模擬", layout="wide", page_icon="❄️") # ========== 頁面設定 ==========
title("❄️ Cri/oFlex 量子低溫傳輸線進階模擬器")
markdown("""
> **三大核心模組**：🔹 多通道時序分析 | 🔹 近場/遠場串擾 | 🔹 QEC資源估算  
> 工作溫度：20 mK | 頻率範圍：DC ~ 26 GHz | 傳輸線：Stripline (Ag/Polyimide)
""")

with sidebar:
  subheader("🌡️ 低溫環境設定") # ========== 側邊欄：全局參數 ==========
  temp_mK = slider("工作溫度 (mK)", 10, 100, 20, 5)
  info(f"熱噪聲電壓密度: {sqrt(4*k*temp_mK*1e-3*50):.2e} V/√Hz")

  subheader("🔧 傳輸線幾何參數")
  n_channels = slider("通道數量", 2, 64, 8, 2)
  line_length_mm = slider("傳輸線長度 L (mm)", 50, 600, 200, 10)
  trace_width_um = slider("線寬 w (μm)", 50, 200, 100, 10)
  trace_spacing_um = slider("線間距 s (μm)", 50, 300, 150, 10)
  dielectric_thick_um = slider("介電層厚度 h (μm)", 50, 150, 75, 5)

  subheader("📡 訊號與材料")
  freq_GHz = slider("操作頻率 (GHz)", 0.1, 26.0, 5.0, 0.1)
  rise_time_ps = slider("上升時間 (ps)", 10, 500, 50, 10)
  v_amplitude_V = slider("訊號振幅 (V)", 0.1, 2.0, 0.5, 0.1)
  epsilon_r = slider("εᵣ (Polyimide)", 2.0, 4.5, 3.5, 0.1)
  loss_tangent = number_input("tanδ @20mK", value=2.2e-5, format="%.1e")


def calc_stripline_params(w_um, s_um, h_um, eps_r, freq_ghz): # ========== 核心計算函數 ==========
    """計算 stripline 單位長度參數 (Hammerstad + 耦合修正)"""
    w, s, h = w_um*1e-6, s_um*1e-6, h_um*1e-6
    f = freq_ghz * 1e9
    
    # 特性阻抗與傳播常數
    Z0 = 60/sqrt(eps_r) * log(4*h/(0.67*pi*w*(0.8 + s/h)))
    eps_eff = eps_r
    v_p = c / sqrt(eps_eff)
    
    # 單位長度電容/電感
    C = eps_eff * epsilon_0 * (w/h) * 1.15  # 邊緣場修正
    L = mu_0 * (h/w) * 1.15
    
    # 耦合係數 (指數衰減模型) [[98]][[100]]
    k_coupling = exp(-pi * s / (2*h)) * 0.85  # 經驗修正
    C_m = k_coupling * C * 0.35
    L_m = k_coupling * L * 0.35
    
    # 低溫導體損耗 [[1]]
    rho_20mK = 1e-12  # Ag @20mK (殘餘電阻比 ~10⁴)
    R_s = sqrt(pi * f * mu_0 * rho_20mK)
    alpha_cond = (R_s/(2*Z0)) * (1/w + 1/(h*2))  # Np/m, R_s=√(πfμ₀ρ)
    
    # 介電損耗
    alpha_diel = pi * f * sqrt(eps_eff)/c * loss_tangent
    
    return {
        'Z0': Z0, 'C': C, 'L': L, 'C_m': C_m, 'L_m': L_m,
        'v_p': v_p, 'k_coupling': k_coupling,
        'alpha_cond': alpha_cond, 'alpha_diel': alpha_diel,
        'R_s': R_s
    }

def calc_crosstalk_near_far(params, length_m, freq_ghz, rise_time_ps, v_amp):
    """計算 NEXT/FEXT 串擾 (含低溫修正) [[79]][[81]]"""
    C, L, C_m, L_m = params['C'], params['L'], params['C_m'], params['L_m']
    v_p = params['v_p']
    alpha_total = params['alpha_cond'] + params['alpha_diel']
    
    # 耦合係數
    K_b = 0.25 * (C_m/C + L_m/L)  # NEXT (反向)
    K_f = 0.5 * (C_m/C - L_m/L) * v_p  # FEXT (正向)
    
    T_D = length_m / v_p  # 傳輸延遲
    
    # NEXT: 階躍響應積分 [[104]]
    V_next = K_b * v_amp * min(1, T_D / (rise_time_ps*1e-12)) * exp(-alpha_total * length_m)
    
    # FEXT: 微分響應 + 衰減 [[98]]
    dVdt = v_amp / (rise_time_ps * 1e-12)
    V_fext = abs(K_f) * length_m * dVdt * exp(-alpha_total * length_m)
    
    return {
        'K_b': K_b, 'K_f': K_f, 'T_D_ns': T_D*1e9,
        'V_next_V': V_next, 'V_fext_V': V_fext,
        'NEXT_dB': 20*log10(max(V_next/v_amp, 1e-12)),
        'FEXT_dB': 20*log10(max(V_fext/v_amp, 1e-12)),
        'alpha_total': alpha_total
    }

def calc_near_far_field_coupling(params, channel_idx, distance_um, freq_ghz):
    """量子近場/遠場串擾分離計算 [[70]][[71]][[74]]"""
    w, s = params['L'], params['C']  # 簡化表示
    f = freq_ghz * 1e9
    wavelength = c / (f * sqrt(3.5))  # 有效波長
    
    # 近場邊界: r < λ/2π
    near_field_boundary = wavelength / (2*pi)
    
    # 近場耦合 (感應耦合為主) [[71]][[72]]
    if distance_um*1e-6 < near_field_boundary:
        # 電容耦合主導 (E-field)
        C_near = params['C_m'] * exp(-distance_um/100)
        # 電感耦合主導 (H-field)  
        L_near = params['L_m'] * exp(-distance_um/100)
        coupling_near = 0.5 * (C_near/params['C'] + L_near/params['L'])
        coupling_far = 0
        region = "近場 (感應耦合)"
    else:
        # 遠場耦合 (輻射耦合) [[74]][[75]]
        # 輻射效率近似 (小天線模型)
        radiation_eff = (pi * distance_um*1e-6 / wavelength)**2
        coupling_far = params['k_coupling'] * radiation_eff * sqrt(freq_ghz)
        coupling_near = 0
        region = "遠場 (輻射耦合)"
    
    return {
        'region': region,
        'near_field_boundary_mm': near_field_boundary*1e3,
        'coupling_near': coupling_near,
        'coupling_far': coupling_far,
        'total_coupling_dB': 20*log10(max(coupling_near + coupling_far, 1e-10))
    }

def calc_timing_skew_jitter(params, length_m, n_ch, rise_time_ps):
    """多通道時序偏差與抖動預算 [[21]][[30]][[128]]"""
    v_p = params['v_p']
    T_D = length_m / v_p
    
    # 製造公差引起的延遲差 (±2% 介電常數變化)
    skew_process = T_D * 0.02 * sqrt(n_ch)  # 統計疊加
    
    # 溫度梯度引起的延遲差 (20mK ±5mK)
    d_eps_dT = 1e-4  # Polyimide @20mK
    skew_thermal = T_D * 0.5 * d_eps_dT * 5 / 3.5
    
    # 總時序偏差 (RSS)
    total_skew = sqrt(skew_process**2 + skew_thermal**2)
    
    # 抖動預算分配 [[21]]
    jitter_random = sqrt(4*k*(20e-3)*50*1e9) * rise_time_ps*1e-12 / v_amplitude_V  # 熱噪聲
    jitter_deterministic = total_skew * 0.3  # 經驗比例
    
    # 眼圖開口餘裕
    eye_width_margin = rise_time_ps - 2*(total_skew*1e12 + jitter_deterministic*1e12)
    
    return {
        'T_D_ns': T_D*1e9,
        'skew_process_ps': skew_process*1e12,
        'skew_thermal_ps': skew_thermal*1e12,
        'total_skew_ps': total_skew*1e12,
        'jitter_random_ps': jitter_random*1e12,
        'jitter_deterministic_ps': jitter_deterministic*1e12,
        'eye_width_margin_ps': eye_width_margin,
        'timing_budget_used_pct': (total_skew + jitter_deterministic) / (rise_time_ps*1e-12) * 100
    }

def crosstalk_to_error_rate(V_crosstalk_V, v_signal_V, qubit_coupling_MHz):
    """串擾電壓→量子閘錯誤率映射 [[4]][[88]][[115]]"""
    # 串擾引起的頻率偏移 (交流史塔克位移)
    delta_f = qubit_coupling_MHz * 1e6 * (V_crosstalk_V / v_signal_V)
    
    # 錯誤率近似 (擾動理論) [[4]]
    # P_error ≈ (Ω_crosstalk / Δ)^2，Ω為拉比頻率，Δ為失諧
    omega_rabi_MHz = 10  # 典型單量子位閘
    error_rate = (delta_f / (omega_rabi_MHz*1e6))**2 * 0.1  # 經驗係數
    
    return min(error_rate, 0.1)  # 上限 10%

def surface_code_resource_estimation(physical_error_rate, target_logical_error=1e-15):
    """表面碼資源估算 [[13]][[56]][[78]][[114]]"""
    # 表面碼閾值 ~0.57-1% [[56]]
    p_threshold = 0.0075
    
    if physical_error_rate >= p_threshold:
        return {'feasible': False, 'reason': '錯誤率高於表面碼閾值'}
    
    # 邏輯錯誤率近似: p_L ≈ 0.1*(p/p_th)^(d/2) [[56]]
    # 求解所需碼距離 d
    d = 2 * log(target_logical_error/0.1) / log(physical_error_rate/p_threshold)
    d = int(ceil(d / 2) * 2 + 1)  # 取奇數
    
    # 物理量子位元數量 (旋轉表面碼) [[108]][[114]]
    n_data = d**2
    n_ancilla = d**2 - 1
    n_physical = n_data + n_ancilla
    
    # T門開銷: 魔法態蒸餾 [[134]][[139]]
    # 每個T門需 ~10-100 物理量子位元 (取決於蒸餾層數)
    t_gate_overhead = 30  # 保守估計
    magic_state_qubits = n_physical * 0.3  # 30% 用於蒸餾
    
    # 總開銷估算 [[79]][[82]]
    total_physical_qubits = n_physical + magic_state_qubits
    
    return {
        'feasible': True,
        'code_distance': d,
        'n_data_qubits': n_data,
        'n_ancilla_qubits': n_ancilla,
        'n_physical_total': int(n_physical),
        't_gate_overhead_per_gate': t_gate_overhead,
        'magic_state_qubits': int(magic_state_qubits),
        'total_qubits_estimate': int(total_physical_qubits),
        'logical_error_rate_est': 0.1 * (physical_error_rate/p_threshold)**(d/2)
    }

# ========== 主應用程式 ==========

with sidebar: # ========== 新增: 側邊欄撓性參數設定 ==========
    subheader("🔧 撓性/彎曲設定")
#bend_enabled = checkbox("啟用彎曲模擬", value=False)
#if bend_enabled:
    bend_radius = slider("彎曲半徑 R (mm)", 1, 50, 10, 1)
    bend_angle = slider("彎曲角度 (°)", 0, 180, 90, 15)
    bend_location = radio( "彎曲位置", ["起始端", "中間", "末端", "多點彎曲"], horizontal=True)

    flex_cycles = number_input( "預期彎曲循環次數", value=1000, min_value=1, max_value=1000000) # 撓性循環測試
#else:
    #bend_radius = 1000  # 直線近似
    #bend_angle = 0
tab1, tab2, tab3, tab4, tab5 = tabs(["📊 儀表板", "⏱️ 時序分析", "🔗 串擾計算", "🧮 QEC資源", "🔸 撓性模擬"])

with tab1: # --- Tab 1: 儀表板 ---
    subheader("🎯 快速評估摘要")
    
    # 執行基礎計算
    params = calc_stripline_params(trace_width_um, trace_spacing_um, dielectric_thick_um, epsilon_r, freq_GHz)
    ct = calc_crosstalk_near_far(params, line_length_mm/1000, freq_GHz, rise_time_ps, v_amplitude_V)
    timing = calc_timing_skew_jitter(params, line_length_mm/1000, n_channels, rise_time_ps)
    
    col1, col2, col3, col4 = columns(4)
    col1.metric("特性阻抗", f"{params['Z0']:.1f} Ω")
    col2.metric("耦合係數 k", f"{params['k_coupling']:.3f}")
    col3.metric("總串擾 (worst)", f"{max(ct['NEXT_dB'], ct['FEXT_dB']):.1f} dB")
    col4.metric("時序偏差", f"{timing['total_skew_ps']:.2f} ps")
    
    狀態.code(params)
    # 規格符合性檢查
    markdown("### ✅ 規格符合性檢查")
    spec_checks = [
        ("串擾隔離度 ≤ -60 dB", max(ct['NEXT_dB'], ct['FEXT_dB']) <= -60),
        ("時序偏差 < 10% 上升時間", timing['total_skew_ps'] < rise_time_ps*0.1),
        ("眼圖餘裕 > 20 ps", timing['eye_width_margin_ps'] > 20),
        ("熱負載 < 20 nW @20mK", (params['alpha_cond']*line_length_mm/1000)*v_amplitude_V**2/50*1e9 < 20)
    ]
    
    for check, passed in spec_checks:
        markdown(f"{'✅' if passed else '❌'} {check}")
    
    # 頻譜圖
    subheader("📈 頻域串擾響應")
    freqs = logspace(8, 10.5, 150)
    data = []
    for f_ghz in freqs/1e9:
        p = calc_stripline_params(trace_width_um, trace_spacing_um, dielectric_thick_um, epsilon_r, f_ghz)
        ct_f = calc_crosstalk_near_far(p, line_length_mm/1000, f_ghz, rise_time_ps, v_amplitude_V)
        data.append({'freq_GHz': f_ghz, 'NEXT_dB': ct_f['NEXT_dB'], 'FEXT_dB': ct_f['FEXT_dB']})
    
    df_freq = DataFrame(data)
    fig_spec = Figure()
    fig_spec.add_trace(Scatter(x=df_freq['freq_GHz'], y=df_freq['NEXT_dB'], name='NEXT', line_color='red'))
    fig_spec.add_trace(Scatter(x=df_freq['freq_GHz'], y=df_freq['FEXT_dB'], name='FEXT', line_color='blue'))
    fig_spec.add_hline(y=-60, line_dash="dash", line_color="green", annotation_text="Cri/oFlex 規格")
    fig_spec.update_layout(xaxis_title="頻率 (GHz)", yaxis_title="串擾 (dB)", 
                          xaxis_type="log", height=350, template="plotly_white")
    plotly_chart(fig_spec, use_container_width=True)

# --- Tab 2: 多通道時序分析 ---
with tab2:
    subheader("⏱️ 多通道同步時序分析")
    
    markdown("""
    #### 🔍 時序偏差來源
    - **製程偏差**: 介電常數 ±2%, 線寬 ±5μm → 延遲變化
    - **溫度梯度**: 20mK ±5mK → εᵣ 微調 [[1]]
    - **負載不均**: 通道間熱負載差異 → 傳播速度漂移
    """)
    
    # 時序偏差掃描
    lengths = array([100, 200, 300, 400, 500, 600])
    skews = []
    for L in lengths:
        p = calc_stripline_params(trace_width_um, trace_spacing_um, dielectric_thick_um, epsilon_r, freq_GHz)
        t = calc_timing_skew_jitter(p, L/1000, n_channels, rise_time_ps)
        skews.append(t['total_skew_ps'])
    
    fig_skew = Figure()
    fig_skew.add_trace(Scatter(x=lengths, y=skews, mode='lines+markers', name='總時序偏差'))
    fig_skew.add_hline(y=rise_time_ps*0.1, line_dash="dot", line_color="orange", 
                      annotation_text="10% 上升時間預算")
    fig_skew.update_layout(xaxis_title="傳輸線長度 (mm)", yaxis_title="時序偏差 (ps)",
                          height=300, template="plotly_white")
    plotly_chart(fig_skew, use_container_width=True)
    
    # 眼圖模擬
    markdown("#### 👁️ 眼圖預覽 (單通道)")
    # 簡化眼圖: 疊加多個上升/下降邊沿
    t_eye = linspace(-200, 200, 1000)  # ps
    ui = zeros_like(t_eye)
    
    # 加入抖動與串擾擾動
    for i in range(50):
        jitter = normal(0, timing['jitter_random_ps'])
        skew = uniform(-timing['total_skew_ps'], timing['total_skew_ps'])
        # 簡化上升沿模型
        edge = 0.5 * (1 + erf((t_eye - jitter - skew) / (rise_time_ps/2.35)))
        ui += edge * (1 if i%2==0 else -1)
    ui /= 50
    
    fig_eye = Figure()
    fig_eye.add_trace(Scatter(x=t_eye, y=ui, line_color='cyan', name='疊加波形'))
    fig_eye.add_vrect(x0=-rise_time_ps/2, x1=rise_time_ps/2, fillcolor="green", opacity=0.1,
                     annotation_text="採樣視窗", annotation_position="top")
    fig_eye.update_layout(xaxis_title="時間 (ps)", yaxis_title="歸一化電壓",
                         height=300, template="plotly_white", showlegend=False)
    plotly_chart(fig_eye, use_container_width=True)
    
    # 抖動預算表
    markdown("#### 📋 抖動預算分配")
    jitter_df = DataFrame({
        '來源': ['製程偏差', '溫度梯度', '熱噪聲', '串擾誘發', '總預算'],
        '貢獻 (ps)': [timing['skew_process_ps'], timing['skew_thermal_ps'], 
                     timing['jitter_random_ps'], timing['jitter_deterministic_ps'],
                     rise_time_ps*0.3],  # 30% 上升時間作為總抖動預算
        '佔比 (%)': [timing['skew_process_ps']/rise_time_ps*100,
                    timing['skew_thermal_ps']/rise_time_ps*100,
                    timing['jitter_random_ps']/rise_time_ps*100,
                    timing['jitter_deterministic_ps']/rise_time_ps*100,
                    30]
    })
    dataframe(jitter_df.style.format({'貢獻 (ps)': '{:.2f}', '佔比 (%)': '{:.1f}'}), use_container_width=True)

# --- Tab 3: 近場/遠場串擾計算 ---
with tab3:
    subheader("🔗 量子近場/遠場串擾分離計算")
    
    markdown("""
    #### 📐 耦合區域判別 [[70]][[74]]
    - **近場 (r < λ/2π)**: 感應耦合 (電容/電感) 主導 → 與距離指數衰減
    - **遠場 (r > λ/2π)**: 輻射耦合 主導 → 與距離平方反比 + 頻率依賴
    
    > 20mK 低溫效應: 導體損耗極低 → 串擾傳播距離增加，需更嚴格隔離 [[1]][[11]]
    """)
    
    # 距離掃描
    distances = logspace(1, 3, 100)  # 10μm ~ 1mm
    couplings = []
    regions = []
    
    for d in distances:
        cf = calc_near_far_field_coupling(params, 0, d, freq_GHz)
        couplings.append(cf['total_coupling_dB'])
        regions.append(cf['region'])
    
    fig_coupling = Figure()
    fig_coupling.add_trace(Scatter(x=distances, y=couplings, mode='lines', 
                                     name='總耦合', line_color='purple'))
    # 標記近場/遠場邊界
    boundary = calc_near_far_field_coupling(params, 0, 100, freq_GHz)['near_field_boundary_mm']*1e3
    fig_coupling.add_vline(x=boundary, line_dash="dash", line_color="gray",
                          annotation_text=f"近場邊界 λ/2π = {boundary:.1f} μm")
    fig_coupling.add_hline(y=-60, line_dash="dot", line_color="green", annotation_text="規格 -60 dB")
    
    fig_coupling.update_layout(xaxis_title="通道間距 (μm)", yaxis_title="耦合強度 (dB)",
                              xaxis_type="log", height=400, template="plotly_white")
    plotly_chart(fig_coupling, use_container_width=True)
    
    # 量子位元串擾錯誤率估算
    markdown("#### ⚛️ 串擾→量子閘錯誤率映射")
    qubit_coupling = slider("量子位元-傳輸線耦合強度 (MHz)", 1, 100, 10, 1)
    
    error_next = crosstalk_to_error_rate(ct['V_next_V'], v_amplitude_V, qubit_coupling)
    error_fext = crosstalk_to_error_rate(ct['V_fext_V'], v_amplitude_V, qubit_coupling)
    
    col1, col2 = columns(2)
    col1.metric("NEXT 誘發錯誤率", f"{error_next:.2e}", 
               delta="✅ <1e-4" if error_next < 1e-4 else "⚠️ 需校準")
    col2.metric("FEXT 誘發錯誤率", f"{error_fext:.2e}",
               delta="✅ <1e-4" if error_fext < 1e-4 else "⚠️ 需校準")
    
    # 多通道串擾熱圖
    markdown("#### 🔥 多通道串擾熱圖 (相鄰通道)")
    channel_matrix = zeros((n_channels, n_channels))
    for i in range(n_channels):
        for j in range(n_channels):
            if i != j:
                dist = abs(i-j) * trace_spacing_um
                cf = calc_near_far_field_coupling(params, i, dist, freq_GHz)
                channel_matrix[i,j] = 20*log10(max(cf['coupling_near']+cf['coupling_far'], 1e-12))
    
    fig_heat = imshow(channel_matrix, color_continuous_scale='RdBu_r', labels={'x':'受害通道', 'y':'干擾通道', 'color':'耦合 (dB)'}, title=f"{n_channels}×{n_channels} 通道串擾矩陣")
    fig_heat.update_layout(height=400)
    plotly_chart(fig_heat, use_container_width=True)

# --- Tab 4: QEC資源估算 ---
with tab4:
    subheader("🧮 量子錯誤校正資源估算")
    
    markdown("""
    #### 🔄 串擾→錯誤率→QEC開銷 流程
    1. 物理串擾電壓 → 量子閘錯誤率 `p` [[4]][[88]]
    2. 錯誤率 `p` → 表面碼距離 `d` (目標邏輯錯誤率 10⁻¹⁵) [[56]][[114]]
    3. 碼距離 `d` → 物理量子位元數量 + T門開銷 [[79]][[139]]
    """)
    
    # 錯誤率輸入
    markdown("#### 📥 錯誤率設定")
    col1, col2 = columns(2)
    with col1:
        p_gate = number_input("單量子位閘錯誤率 (含串擾)", value=1e-3, format="%.1e", min_value=1e-6, max_value=1e-1)
    with col2:
        p_2q = number_input("雙量子位閘錯誤率 (含串擾)", value=5e-3, format="%.1e", min_value=1e-5, max_value=1e-1)
    
    # 使用較差的錯誤率進行估算
    p_physical = max(p_gate, p_2q)
    
    # 執行資源估算
    qec_result = surface_code_resource_estimation(p_physical)
    
    if qec_result['feasible']:
        success(f"✅ 可行: 表面碼距離 d = {qec_result['code_distance']} 可達邏輯錯誤率 {qec_result['logical_error_rate_est']:.2e}")
        
        # 資源摘要
        col1, col2, col3 = columns(3)
        col1.metric("物理量子位元/邏輯量子位元", f"{qec_result['n_physical_total']:,}")
        col2.metric("魔法態蒸餾開銷", f"{qec_result['magic_state_qubits']:,} qubits")
        col3.metric("T門等效開銷", f"{qec_result['t_gate_overhead_per_gate']}×/gate")
        
        # 碼距離掃描
        markdown("#### 📈 邏輯錯誤率 vs 碼距離")
        distances = array([3, 5, 7, 9, 11, 13, 15])
        p_logical = []
        p_th = 0.0075
        for d in distances:
            pL = 0.1 * (p_physical/p_th)**(d/2)
            p_logical.append(pL)
        
        fig_qec = Figure()
        fig_qec.add_trace(Scatter(x=distances, y=p_logical, mode='lines+markers', name=f'p_phys = {p_physical:.1e}', line_color='blue'))
        fig_qec.add_hline(y=1e-15, line_dash="dash", line_color="green", annotation_text="目標: 10⁻¹⁵")
        fig_qec.add_vline(x=qec_result['code_distance'], line_dash="dot", line_color="red", annotation_text=f"建議 d={qec_result['code_distance']}")
        
        fig_qec.update_layout(xaxis_title="表面碼距離 d", yaxis_title="邏輯錯誤率", yaxis_type="log", height=350, template="plotly_white")
        plotly_chart(fig_qec, use_container_width=True)
        
        # T門數量估算 [[31]][[139]]
        markdown("#### ⚡ T門/魔法態開銷估算")
        n_t_gates = number_input("演算法所需邏輯T門數量", value=10000, min_value=100, max_value=10000000, step=1000)
        
        # 魔法態蒸餾開銷: 每層蒸餾 ~3-5× 量子位元，2-3層達 10⁻¹⁵ [[136]][[137]]
        distillation_layers = 2 if p_physical < 1e-3 else 3
        magic_states_needed = n_t_gates * (3 ** distillation_layers)
        total_t_overhead = qec_result['n_physical_total'] * magic_states_needed * 0.1  # 時序並行係數
        
        info(f"""
        - 蒸餾層數: {distillation_layers} (基於 p={p_physical:.1e})
        - 所需魔法態總數: {magic_states_needed:,}
        - 等效物理量子位元-週期開銷: ~{total_t_overhead:,.0f}
        
        > 💡 **優化建議**: 減少 T-depth [[139]]、使用替代閘分解 [[134]] 可顯著降低開銷
        """)
        
    else:
        error(f"❌ {qec_result['reason']}")
        markdown("#### 🔧 改善建議")
        markdown("""
        1. **降低串擾**: 增加線間距 ≥ 3×線寬 [[88]]、加入接地屏蔽層
        2. **校準補償**: 實時串擾校準 [[92]][[93]]、動態頻率調諧
        3. **編碼選擇**: 考慮低密度奇偶檢查碼 (LDPC) 降低開銷 [[109]]
        """)
    
    # 資源估算匯出
    if qec_result['feasible']:
        download_button(
            "📥 下載資源估算報告 (CSV)",
            data=f"Parameter,Value\nPhysical_error_rate,{p_physical}\nCode_distance,{qec_result['code_distance']}\nPhysical_qubits_per_logical,{qec_result['n_physical_total']}\nMagic_state_qubits,{qec_result['magic_state_qubits']}\nT_gate_overhead,{qec_result['t_gate_overhead_per_gate']}",
            file_name="qec_resource_estimate.csv",
            mime="text/csv"
        )

# ========== 參考文獻與說明 ==========
#with expander("📚 理論來源與模型假設"):
    markdown("""
    ### 🔬 串擾模型
    - NEXT/FEXT 公式: Bogatin, Signal Integrity Journal (2024) [[79]][[81]]
    - 耦合係數: 指數衰減模型 + 低溫修正 [[98]][[100]]
    - 近場/遠場判別: λ/2π 邊界 + 感應/輻射耦合分離 [[70]][[71]][[74]]
    
    ### 🌡️ 低溫修正 (20mK)
    - 銀導體電阻率: ρ ≈ 1×10⁻¹² Ω·m (RRR ~10⁴) [[1]]
    - Polyimide 損耗: tanδ ≈ 2.2×10⁻⁵ @20mK [[1]]
    - 熱噪聲: √(4kTRB) → 20mK 時極低
    
    ### ⚛️ 量子錯誤映射
    - 串擾→頻率偏移: 交流史塔克位移模型 [[4]][[88]]
    - 錯誤率近似: 擾動理論 + 實驗校準係數 [[115]][[118]]
    
    ### 🧮 表面碼資源估算
    - 邏輯錯誤率: p_L ≈ 0.1×(p/p_th)^(d/2) [[56]][[114]]
    - 物理量子位元: n ≈ 2d²-1 (旋轉表面碼) [[108]]
    - T門開銷: 魔法態蒸餾 ~30×/gate (保守估計) [[134]][[139]]
    
    > ⚠️ **免責**: 本模擬器基於簡化模型，實際量子系統需結合 3D EM 模擬 (HFSS/CST) 
    > 與實測校準。串擾與錯誤率映射需針對特定量子位元架構校準 [[92]][[95]]。
    """)

with tab5:
    subheader("🔸 撓性傳輸線彎曲效應模擬")

    #if bend_enabled:
    # 執行撓性計算
    bend_info = calc_flexible_bending_effects( trace_width_um, dielectric_thick_um, epsilon_r, bend_radius, line_length_mm)

    bend_ct = calc_flexible_crosstalk_modification(params, bend_info, bend_radius)

    # 安全性檢查
    if bend_info['bend_safe']:
        success(f"✅ 彎曲安全: R={bend_radius}mm > R_critical={bend_info['R_critical_mm']:.2f}mm")
    else:
        error(f"❌ 彎曲危險: R={bend_radius}mm < R_critical={bend_info['R_critical_mm']:.2f}mm")

    # 關鍵指標
    col1, col2, col3, col4 = columns(4)
    col1.metric("外側應力", f"{bend_info['sigma_outer_MPa']:.2f} MPa")
    col2.metric("阻抗變化", f"{bend_info['delta_Z_pct']:+.2f}%")
    col3.metric("耦合係數變化", f"{bend_ct['crosstalk_penalty_dB']:+.2f} dB")
    col4.metric("疲勞壽命", f"{bend_info['fatigue_cycles']:,} 次")

    # 彎曲半徑掃描圖
    markdown("#### 📈 彎曲半徑對電氣特性影響")

    radii = linspace(2, 50, 100)
    delta_Z_list = []
    k_penalty_list = []
    fatigue_list = []

    for R in radii:
        info = calc_flexible_bending_effects(
            trace_width_um, dielectric_thick_um, epsilon_r, R, line_length_mm
        )
        delta_Z_list.append(info['delta_Z_pct'])
        fatigue_list.append(info['fatigue_cycles'])

        p_temp = params.copy()
        p_temp['trace_spacing'] = trace_spacing_um * 1e-6
        ct_mod = calc_flexible_crosstalk_modification(p_temp, info, R)
        k_penalty_list.append(ct_mod['crosstalk_penalty_dB'])

    fig_bend = Figure()
    fig_bend.add_trace(Scatter(x=radii, y=delta_Z_list, name='阻抗變化 %', line_color='blue'))
    fig_bend.add_trace(Scatter(x=radii, y=k_penalty_list, name='串擾懲罰 dB', line_color='red'))
    fig_bend.add_vline(x=bend_info['R_critical_mm'], line_dash="dash", line_color="orange", annotation_text="臨界彎曲半徑")
    fig_bend.update_layout(xaxis_title="彎曲半徑 (mm)", yaxis_title="變化量", height=350, template="plotly_white")
    plotly_chart(fig_bend, use_container_width=True)

    # 疲勞壽命圖
    markdown("#### 🔁 疲勞壽命 vs 彎曲半徑")

    fig_fatigue = Figure()
    fig_fatigue.add_trace(Scatter(x=radii, y=fatigue_list, mode='lines', name='預估循環次數', line_color='green'))
    fig_fatigue.add_hline(y=flex_cycles, line_dash="dot", line_color="gray", annotation_text=f"需求: {flex_cycles:,} 次")
    fig_fatigue.update_layout(xaxis_title="彎曲半徑 (mm)", yaxis_title="循環次數", yaxis_type="log", height=300, template="plotly_white")
    plotly_chart(fig_fatigue, use_container_width=True)

    # 彎曲位置效應
    markdown("#### 📍 彎曲位置對串擾影響")

    bend_positions = ["起始端", "中間", "末端", "多點彎曲"]
    position_impact = []

    for pos in bend_positions:
        if pos == "起始端":
            impact = bend_ct['crosstalk_penalty_dB'] * 0.3  # 影響較小
        elif pos == "中間":
            impact = bend_ct['crosstalk_penalty_dB'] * 1.0  # 影響最大
        elif pos == "末端":
            impact = bend_ct['crosstalk_penalty_dB'] * 0.4
        else:  # 多點
            impact = bend_ct['crosstalk_penalty_dB'] * 1.5

        position_impact.append(impact)

    fig_pos = bar(x=bend_positions, y=position_impact, labels={'x': '彎曲位置', 'y': '串擾懲罰 (dB)'}, color=position_impact, color_continuous_scale='RdYlGn_r')
    plotly_chart(fig_pos, use_container_width=True)

    # 設計建議
    markdown("#### 💡 撓性設計建議")

    recommendations = []
    if bend_info['R_critical_mm'] > bend_radius:
        recommendations.append("⚠️ 增加彎曲半徑至 ≥{:.1f}mm".format(bend_info['R_critical_mm']))
    if abs(bend_info['delta_Z_pct']) > 5:
        recommendations.append("⚠️ 阻抗變化 >5%, 建議加入阻抗補償結構")
    if bend_ct['crosstalk_penalty_dB'] > 3:
        recommendations.append("⚠️ 串擾懲罰 >3dB, 建議增加線間距或加入屏蔽")
    if bend_info['fatigue_cycles'] < flex_cycles:
        recommendations.append("⚠️ 疲勞壽命不足, 建議選用更厚介電層或更大彎曲半徑")

    if recommendations:
        for rec in recommendations:
            warning(rec)
    else:
        success("✅ 當前設計滿足所有撓性要求")

    #else:
    #   info("👈 請在側邊欄勾選 **啟用彎曲模擬** 以查看撓性效應分析")

# ========== 底部資訊 ==========
markdown("---")
caption("""
❄️ Cri/oFlex 量子低溫傳輸線模擬器 | 基於 Delft Circuits 規格 [[40]][[46]] + 量子串擾文獻 [[1]][[11]][[16]]  
💡 提示: 調整左側參數後，各模組將自動更新計算結果
""")
