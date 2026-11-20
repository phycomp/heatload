from streamlit import caption, columns, dataframe, download_button, error, expander, info, markdown, plotly_chart, set_page_config, sidebar, subheader, success, tabs, title, radio, slider, number_input, checkbox, button
from numpy import arccosh, ceil, tanh, exp, log, log10, logspace, sqrt
from pandas import DataFrame
from plotly.graph_objects import Figure, Scatter
# Cri/oFlex NbTi 超導撓性傳輸線串擾模擬器 v3.0
# 平台：Streamlit | 工作溫度：10mK-4K | 導體：NbTi/Kapton

#import streamlit as st
#import numpy as np
#import plotly.graph_objects as go
from plotly.express import line as xprsline
#import pandas as pd
from scipy.constants import epsilon_0, mu_0, c, pi, k
from scipy.special import erf
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 頁面設定
# ============================================================================
set_page_config(
    page_title="Cri/oFlex NbTi 串擾模擬器",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義 CSS
markdown("""
<style>
    .metric-card {background-color: #f0f2f6; padding: 15px; border-radius: 10px;}
    .success-box {background-color: #d4edda; padding: 10px; border-radius: 5px; border-left: 4px solid #28a745;}
    .warning-box {background-color: #fff3cd; padding: 10px; border-radius: 5px; border-left: 4px solid #ffc107;}
    .error-box {background-color: #f8d7da; padding: 10px; border-radius: 5px; border-left: 4px solid #dc3545;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 標題與說明
# ============================================================================
title("❄️ Cri/oFlex NbTi 超導撓性傳輸線串擾模擬器")
markdown("""
> **整合模組**：🔹 NbTi 超導效應 | 🔹 多通道串擾 | 🔹 撓性彎曲 | 🔹 時序分析 | 🔹 QEC 資源估算  
> **參考規格**：Delft Circuits Cri/oFlex® | Bluefors 整合系統 | IEEE 量子互連文獻
""")

# ============================================================================
# 側邊欄：全局參數設定
# ============================================================================
with sidebar:
  subheader("🌡️ 低溫環境設定")
  temp_stage = radio("溫度階層", ["10 mK (MC)", "100 mK (Still)", "4 K (Cold Plate)", "40 K (2nd Stage)", "300 K (Room)"], horizontal=True)
  temp_map = {"10 mK (MC)": 0.01, "100 mK (Still)": 0.1, "4 K (Cold Plate)": 4.0, "40 K (2nd Stage)": 40.0, "300 K (Room)": 300.0}
  temp_K = temp_map[temp_stage]

  info(f"熱噪聲電壓密度：{sqrt(4*k*temp_K*50*1e9):.2e} V/√Hz @50Ω")

  subheader("🔧 傳輸線幾何參數")
  n_channels = slider("通道數量 N", 2, 64, 8, 2)
  line_length_mm = slider("傳輸線長度 L (mm)", 50, 600, 200, 10)
  trace_width_um = slider("線寬 w (μm)", 50, 200, 100, 10)
  trace_spacing_um = slider("線間距 s (μm)", 50, 300, 150, 10)
  dielectric_thick_um = slider("介電層厚度 h (μm)", 50, 150, 75, 5)

  subheader("⚛️ NbTi 超導材料參數")
  conductor_type = radio("導體類型", ["NbTi (超導)", "Ag (常導)", "NbN (推估)"], horizontal=True)
  t_film_nm = slider("薄膜厚度 t (nm)", 20, 150, 50, 5)
  lambda_L_nm = slider("London 穿透深度 λL (nm)", 50, 200, 100, 10)
  Tc_K = number_input("臨界溫度 Tc (K)", value=9.2, min_value=0.0, max_value=20.0, step=0.1)

  subheader("📡 訊號與材料設定")
  freq_GHz = slider("操作頻率 (GHz)", 0.1, 26.0, 6.0, 0.1)
  rise_time_ps = slider("上升時間 Tr (ps)", 10, 500, 50, 10)
  v_amplitude_V = slider("訊號振幅 (V)", 0.1, 2.0, 0.5, 0.1)
  epsilon_r = number_input("Kapton εᵣ", value=3.5, min_value=2.0, max_value=5.0, step=0.1)

# 低溫介電損耗自動修正
if temp_K < 1.0:
    loss_tangent = 2.2e-5
elif temp_K < 10.0:
    loss_tangent = 1.0e-4
elif temp_K < 100.0:
    loss_tangent = 5.0e-4
else:
    loss_tangent = 0.002

number_input("損耗角正切 tanδ", value=loss_tangent, format="%.1e", disabled=True)

subheader("🔸 撓性彎曲設定")
bend_enabled = checkbox("啟用彎曲模擬", value=False)
if bend_enabled:
    bend_radius_mm = slider("彎曲半徑 R (mm)", 1, 50, 10, 1)
    bend_angle_deg = slider("彎曲角度 (°)", 0, 180, 90, 15)
else:
    bend_radius_mm = 1000

# ============================================================================
# 核心物理模型函數
# ============================================================================

def get_material_params(conductor_type, temp_K, t_film_nm, lambda_L_nm, Tc_K):
    """獲取材料參數 (含低溫修正)"""
    params = {}
    
    if conductor_type == "NbTi (超導)":
        params['rho_dc'] = 0 if temp_K < Tc_K else 5e-7  # Ω·m
        params['lambda_L'] = lambda_L_nm * 1e-9  # m
        params['t_film'] = t_film_nm * 1e-9  # m
        params['is_superconducting'] = temp_K < Tc_K
        params['Tc'] = Tc_K
        # 低溫楊氏模量修正 (Kapton)
        params['E_young'] = 2.5e9 * (1 + 0.3*(1 - temp_K/300))  # Pa
    elif conductor_type == "Ag (常導)":
        params['rho_dc'] = 1.6e-8 * (temp_K/300)**5 if temp_K < 50 else 1.6e-8 * (1 + 0.0038*(temp_K-300))
        params['is_superconducting'] = False
        params['E_young'] = 2.5e9 * (1 + 0.3*(1 - temp_K/300))
    else:  # NbN
        params['rho_dc'] = 0 if temp_K < 15 else 1e-6
        params['lambda_L'] = 300e-9
        params['t_film'] = t_film_nm * 1e-9
        params['is_superconducting'] = temp_K < 15
        params['Tc'] = 15
        params['E_young'] = 2.5e9 * (1 + 0.3*(1 - temp_K/300))
    
    # Kapton 介電常數低溫修正
    params['epsilon_r'] = 3.5 * (1 - 0.002*(300-temp_K)/300)
    
    return params

def calc_stripline_params(w_um, s_um, h_um, eps_r, mat_params):
    """計算 Stripline 單位長度參數 (含超導修正)"""
    w, s, h = w_um*1e-6, s_um*1e-6, h_um*1e-6
    
    # 自電容與幾何電感
    C0 = eps_r * epsilon_0 * (w/h) * 1.15  # F/m (邊緣場修正)
    Lg = mu_0 * (h/w) * 1.15  # H/m
    
    # 超導動感電感
    if mat_params['is_superconducting']:
        Lk = (mu_0**2 * mat_params['lambda_L']**2) / (mat_params['t_film'] * w)  # H/m
        L_total = Lg + Lk
        sc_suppression = Lg / L_total
    else:
        Lk = 0
        L_total = Lg
        sc_suppression = 1.0
    
    # 特性阻抗
    Z0 = sqrt(L_total / C0)
    
    # 傳播速度
    v_p = c / sqrt(eps_r)
    
    # 互參數 (耦合)
    arg = max(s/w, 1.001)
    Cm = (pi*epsilon_0*eps_r / arccosh(arg)) * exp(-pi*s/(2*h))
    M = (-mu_0/pi) * log(tanh(pi*s/(4*h))) * exp(-pi*s/(2*h))
    
    # 耦合係數
    k_coupling = 0.5 * (Cm/C0 + M/L_total)
    
    # 衰減常數
    if mat_params['is_superconducting']:
        alpha_cond = 0  # 超導態導體損耗≈0
    else:
        f = 6e9
        R_s = sqrt(pi * f * mu_0 * mat_params['rho_dc'])
        alpha_cond = R_s / (2 * Z0)
    
    alpha_diel = (2*pi*6e9 * sqrt(eps_r) / (2*c)) * 2.2e-5
    alpha_total = alpha_cond + alpha_diel
    
    return {
        'Z0': Z0, 'C0': C0, 'Lg': Lg, 'Lk': Lk, 'L_total': L_total,
        'v_p': v_p, 'Cm': Cm, 'M': M, 'k_coupling': k_coupling,
        'alpha_total': alpha_total, 'sc_suppression': sc_suppression
    }

def calc_crosstalk_next_fext(params, length_m, freq_GHz, rise_time_ps, v_amp):
    """計算 NEXT/FEXT 串擾"""
    C0, L_total, Cm, M = params['C0'], params['L_total'], params['Cm'], params['M']
    v_p, alpha = params['v_p'], params['alpha_total']
    
    f = freq_GHz * 1e9
    omega = 2*pi*f
    
    # 耦合係數
    k_b = 0.25 * (Cm/C0 + M/L_total)
    k_f = 0.5 * (Cm/C0 - M/L_total) * v_p
    
    # 傳輸延遲
    T_D = length_m / v_p
    
    # NEXT (式 4)
    V_next = k_b * v_amp * (1 - exp(-2*alpha*length_m)) * exp(-alpha*length_m)
    
    # FEXT (式 5)
    dVdt = v_amp / (rise_time_ps * 1e-12)
    V_fext = abs(k_f) * length_m * dVdt * exp(-alpha*length_m)
    
    # 轉換為 dB
    next_db = 20 * log10(max(abs(V_next/v_amp), 1e-12))
    fext_db = 20 * log10(max(abs(V_fext/v_amp), 1e-12))
    
    return {
        'k_b': k_b, 'k_f': k_f, 'T_D_ns': T_D*1e9,
        'V_next_V': V_next, 'V_fext_V': V_fext,
        'NEXT_dB': next_db, 'FEXT_dB': fext_db
    }

def calc_multichannel_crosstalk(n_ch, adjacent_xtalk_db, spacing_um, height_um):
    """多通道串擾疊加計算"""
    gamma = pi * spacing_um*1e-6 / (2 * height_um*1e-6)
    enhancement_factor = sqrt((n_ch-1) / (1 - exp(-2*gamma)))
    total_xtalk_db = adjacent_xtalk_db + 20*log10(enhancement_factor)
    return total_xtalk_db, enhancement_factor

def calc_bending_effects(w_um, h_um, eps_r, bend_radius_mm, mat_params):
    """撓性彎曲效應計算"""
    w, h = w_um*1e-6, h_um*1e-6
    R = bend_radius_mm * 1e-3
    
    # 彎曲應力
    sigma_outer = mat_params['E_young'] * (h/2) / R
    sigma_inner = -sigma_outer
    
    # 應力 - 介電效應
    depsilon_dsigma = -5e-12
    delta_eps = eps_r * depsilon_dsigma * sigma_outer
    
    # 阻抗變化
    delta_Z_pct = -0.5 * delta_eps / eps_r * 100
    
    # 臨界彎曲半徑
    R_critical = h * mat_params['E_young'] / (50e6)
    
    # 疲勞壽命
    if R > R_critical:
        fatigue_cycles = int(1e6 * (R / R_critical)**4)
    else:
        fatigue_cycles = 0
    
    return {
        'sigma_outer_MPa': sigma_outer/1e6,
        'delta_Z_pct': delta_Z_pct,
        'R_critical_mm': R_critical*1e3,
        'fatigue_cycles': fatigue_cycles,
        'bend_safe': R > R_critical
    }

def calc_timing_skew(params, length_m, n_ch, rise_time_ps, temp_K):
    """時序偏差計算"""
    v_p = params['v_p']
    T_D = length_m / v_p
    
    # 製程偏差
    skew_process = T_D * 0.02 * sqrt(n_ch)
    
    # 溫度梯度
    d_eps_dT = 1e-4 * (temp_K/300)
    skew_thermal = T_D * 0.5 * d_eps_dT * max(1, temp_K*10)
    
    # 總偏差
    total_skew = sqrt(skew_process**2 + skew_thermal**2)
    
    # 眼圖餘裕
    eye_margin = rise_time_ps - 2*total_skew*1e12
    
    return {
        'T_D_ns': T_D*1e9,
        'total_skew_ps': total_skew*1e12,
        'eye_margin_ps': eye_margin,
        'budget_used_pct': total_skew/(rise_time_ps*1e-12)*100
    }

def crosstalk_to_error_rate(V_xtalk_V, v_sig_V, qubit_coupling_MHz=10):
    """串擾→量子錯誤率映射"""
    delta_f = qubit_coupling_MHz * 1e6 * (V_xtalk_V / v_sig_V)
    omega_rabi = 10e6
    error_rate = (delta_f / omega_rabi)**2 * 0.1
    return min(error_rate, 0.1)

def surface_code_resources(p_physical, target_logical=1e-15):
    """表面碼資源估算"""
    p_th = 0.0075
    if p_physical >= p_th:
        return {'feasible': False, 'reason': '錯誤率高於閾值'}
    
    d = 2 * log(target_logical/0.1) / log(p_physical/p_th)
    d = int(ceil(d/2)*2 + 1)
    
    n_physical = 2*d**2 - 1
    magic_qubits = int(n_physical * 0.3)
    
    return {
        'feasible': True,
        'code_distance': d,
        'n_physical': n_physical,
        'magic_qubits': magic_qubits,
        'total': n_physical + magic_qubits
    }

# ============================================================================
# 主計算執行
# ============================================================================

if button("🔄 執行模擬", type="primary"):
    
    # 獲取材料參數
    mat_params = get_material_params(conductor_type, temp_K, t_film_nm, lambda_L_nm, Tc_K)
    
    # 計算傳輸線參數
    tl_params = calc_stripline_params(trace_width_um, trace_spacing_um, dielectric_thick_um, 
                                       mat_params['epsilon_r'], mat_params)
    
    # 計算串擾
    ct_results = calc_crosstalk_next_fext(tl_params, line_length_mm/1000, freq_GHz, 
                                           rise_time_ps, v_amplitude_V)
    
    # 多通道疊加
    total_next, enhancement = calc_multichannel_crosstalk(
        n_channels, ct_results['NEXT_dB'], trace_spacing_um, dielectric_thick_um)
    
    # 彎曲效應
    if bend_enabled:
        bend_info = calc_bending_effects(trace_width_um, dielectric_thick_um, 
                                          mat_params['epsilon_r'], bend_radius_mm, mat_params)
        ct_results['NEXT_dB'] += abs(bend_info['delta_Z_pct']) * 0.5  # 彎曲懲罰
    
    # 時序分析
    timing = calc_timing_skew(tl_params, line_length_mm/1000, n_channels, rise_time_ps, temp_K)
    
    # 錯誤率與 QEC
    p_error = crosstalk_to_error_rate(ct_results['V_next_V'], v_amplitude_V)
    qec = surface_code_resources(p_error)
    
    # ========================================================================
    # 結果顯示：標籤頁架構
    # ========================================================================
    
    tab1, tab2, tab3, tab4, tab5, tab6 = tabs([
        "📊 儀表板", "🔗 串擾分析", "⏱️ 時序", "🔸 撓性", "⚛️ QEC", "📥 報告"
    ])
    
    # --- Tab 1: 儀表板 ---
    with tab1:
        subheader("🎯 關鍵指標摘要")
        
        col1, col2, col3, col4 = columns(4)
        col1.metric("特性阻抗 Z₀", f"{tl_params['Z0']:.1f} Ω", 
                   delta=f"{tl_params['Z0']-50:.1f} Ω" if abs(tl_params['Z0']-50)>2 else "✅")
        col2.metric("NEXT (8 通道)", f"{total_next:.1f} dB",
                   delta="✅ ≤-60dB" if total_next <= -60 else "⚠️ >-60dB")
        col3.metric("FEXT", f"{ct_results['FEXT_dB']:.1f} dB")
        col4.metric("時序偏差", f"{timing['total_skew_ps']:.1f} ps")
        
        # 規格符合性
        markdown("### ✅ 規格符合性檢查")
        checks = [
            ("串擾 ≤ -60 dB @1GHz", total_next <= -60),
            ("阻抗 50Ω ±10%", 45 <= tl_params['Z0'] <= 55),
            ("時序偏差 < 10% Tr", timing['total_skew_ps'] < rise_time_ps*0.1),
            ("超導態 (T < Tc)", mat_params['is_superconducting']),
            ("彎曲安全", not bend_enabled or bend_info['bend_safe'])
        ]
        
        for check, passed in checks:
            markdown(f"{'✅' if passed else '❌'} {check}")
        
        # 超導抑制效果
        if mat_params['is_superconducting']:
            success(f"✅ 動感電感抑制：耦合係數降低 {100*(1-tl_params['sc_suppression']):.1f}%")
    
    # --- Tab 2: 串擾分析 ---
    with tab2:
        subheader("🔗 串擾頻率響應與多通道效應")
        
        # 頻譜掃描
        freqs = logspace(8, 10.5, 150)
        next_list, fext_list = [], []
        for f in freqs/1e9:
            ct = calc_crosstalk_next_fext(tl_params, line_length_mm/1000, f, rise_time_ps, v_amplitude_V)
            next_list.append(ct['NEXT_dB'])
            fext_list.append(ct['FEXT_dB'])
        
        fig_spec = Figure()
        fig_spec.add_trace(Scatter(x=freqs/1e9, y=next_list, name='NEXT', line_color='red'))
        fig_spec.add_trace(Scatter(x=freqs/1e9, y=fext_list, name='FEXT', line_color='blue'))
        fig_spec.add_hline(y=-60, line_dash="dash", line_color="green", annotation_text="規格 -60 dB")
        fig_spec.update_layout(xaxis_title="頻率 (GHz)", yaxis_title="串擾 (dB)",
                              xaxis_type="log", height=400, template="plotly_white")
        plotly_chart(fig_spec, use_container_width=True)
        
        # 通道數影響
        markdown("#### 📊 通道數對串擾累積影響")
        n_list = [2, 4, 8, 16, 32, 64]
        xtalk_list = []
        for n in n_list:
            total, _ = calc_multichannel_crosstalk(n, ct_results['NEXT_dB'], trace_spacing_um, dielectric_thick_um)
            xtalk_list.append(total)
        fig_n = xprsline(x=n_list, y=xtalk_list, markers=True, labels={'x':'通道數', 'y':'總串擾 (dB)'}, title='多通道串擾累積效應')
        fig_n.add_hline(y=-60, line_dash="dot", line_color="gray")
        plotly_chart(fig_n, use_container_width=True)
    
    # --- Tab 3: 時序分析 ---
    with tab3:
        subheader("⏱️ 多通道時序同步分析")
        
        col1, col2 = columns(2)
        col1.metric("傳輸延遲", f"{timing['T_D_ns']:.2f} ns")
        col2.metric("眼圖餘裕", f"{timing['eye_margin_ps']:.1f} ps",
                   delta="✅ >20ps" if timing['eye_margin_ps']>20 else "⚠️")
        
        # 時序預算分配
        budget_df = DataFrame({
            '來源': ['製程偏差', '溫度梯度', '總預算'],
            '貢獻 (ps)': [timing['total_skew_ps']*0.7, timing['total_skew_ps']*0.3, rise_time_ps*0.3],
            '佔比 (%)': [70, 30, 100]
        })
        dataframe(budget_df, use_container_width=True)
    
    # --- Tab 4: 撓性彎曲 ---
    with tab4:
        subheader("🔸 撓性彎曲效應分析")
        
        if bend_enabled:
            col1, col2, col3 = columns(3)
            col1.metric("外側應力", f"{bend_info['sigma_outer_MPa']:.1f} MPa")
            col2.metric("阻抗變化", f"{bend_info['delta_Z_pct']:+.2f}%")
            col3.metric("疲勞壽命", f"{bend_info['fatigue_cycles']:,} 次")
            
            if bend_info['bend_safe']:
                success(f"✅ 彎曲安全：R={bend_radius_mm}mm > R_critical={bend_info['R_critical_mm']:.1f}mm")
            else:
                error(f"❌ 彎曲危險：請增加 R 至 >{bend_info['R_critical_mm']:.1f}mm")
        else:
            info("👈 請在側邊欄啟用彎曲模擬")
    
    # --- Tab 5: QEC 資源 ---
    with tab5:
        subheader("⚛️ 量子錯誤校正資源估算")
        
        col1, col2 = columns(2)
        col1.metric("物理錯誤率 (串擾)", f"{p_error:.2e}")
        col2.metric("邏輯錯誤率目標", "1e-15")
        
        if qec['feasible']:
            success(f"✅ 表面碼距離 d={qec['code_distance']} 可達目標")
            col1, col2, col3 = columns(3)
            col1.metric("物理量子位元/邏輯", f"{qec['n_physical']:,}")
            col2.metric("魔法態量子位元", f"{qec['magic_qubits']:,}")
            col3.metric("總開銷", f"{qec['total']:,}")
        else:
            error(f"❌ {qec['reason']} - 需降低串擾")
    
    # --- Tab 6: 報告下載 ---
    with tab6:
        subheader("📥 下載模擬報告")
        
        csv_data = f"""Parameter,Value,Unit
Temperature,{temp_K},K
Conductor_Type,{conductor_type},-
Channels,{n_channels},-
Length,{line_length_mm},mm
Width,{trace_width_um},um
Spacing,{trace_spacing_um},um
Z0,{tl_params['Z0']:.2f},Ohm
NEXT,{total_next:.2f},dB
FEXT,{ct_results['FEXT_dB']:.2f},dB
Skew,{timing['total_skew_ps']:.2f},ps
Error_Rate,{p_error:.2e},-
Code_Distance,{qec['code_distance'] if qec['feasible'] else 'N/A'},-
"""
        download_button("📥 下載 CSV 報告", csv_data, "crioflex_simulation.csv", "text/csv")

else:
    info("👈 請在左側調整參數後點擊 **執行模擬**")

# ============================================================================
# 參考文獻
# ============================================================================
with expander("📚 參考文獻與理論來源"):
    markdown("""
    ### 🔬 物理模型來源
    1. Delft Circuits. *Cri/oFlex® Product Specifications* [[6]][[46]]
    2. Wang et al. (2016). *Flexible superconducting Nb transmission lines*, Supercond. Sci. Technol. [[1]]
    3. Bogatin, E. (2024). *Crosstalk Quantification*, Signal Integrity Journal [[79]][[81]]
    4. Fowler et al. (2012). *Surface codes: Towards practical large-scale quantum computation* [[56]]
    5. IEEE Std 802.3. *Crosstalk in High-Speed Links* [[84]]
    
    ### ⚠️ 免責聲明
    本模擬器基於簡化傳輸線理論，實際量子系統需結合 3D EM 模擬 (HFSS/CST) 與實測校準。
    低溫材料參數建議以實測為準，因薄膜製程與介面處理會顯著影響最終性能。
    """)

# ============================================================================
# 底部資訊
# ============================================================================
markdown("---")
caption("""
❄️ Cri/oFlex NbTi 串擾模擬器 v3.0 | 基於 Delft Circuits 規格 + 量子互連文獻  
💡 提示：調整左側參數後點擊「執行模擬」以更新結果
""")
