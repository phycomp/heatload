from streamlit import columns, download_button, expander, info, markdown, metric, plotly_chart, set_page_config, sidebar, subheader, title, slider, number_input, button, radio, text_input
from numpy import arange, exp, log, log10, logspace, pi, sqrt
from plotly.graph_objects import Figure, Scatter
## 🐍 Streamlit 模擬器程式碼

# app.py - Cri/oFlex 低溫串擾模擬器
#import streamlit as st
#import numpy as np
#import plotly.graph_objects as go
from scipy.constants import k, c, mu_0, epsilon_0

# ========== 頁面設定 ==========
set_page_config(page_title="Cri/oFlex 低溫串擾模擬", layout="wide")

with sidebar: # ========== 側邊欄參數 ==========
  title("❄️ Cri/oFlex 撓性傳輸線串擾模擬器 (20mK)")
  #markdown("""
  #> 基於 stripline 耦合傳輸線理論，計算低溫環境下的 **NEXT** (近端) 與 **FEXT** (遠端) 串擾
  #""")
  subheader("🔧 傳輸線參數")
  line_length = slider("傳輸線長度 L (mm)", 50, 600, 200, 10) # 幾何參數
  trace_width = slider("線寬 w (μm)", 50, 200, 100, 10)
  trace_spacing = slider("線間距 s (μm)", 50, 300, 150, 10)
  dielectric_thick = slider("介電層厚度 h (μm)", 50, 150, 75, 5)

  subheader("材料特性") # 材料參數
  epsilon_r = slider("相對介電常數 εᵣ", 2.0, 4.5, 3.5, 0.1)  # Polyimide ~3.5
  loss_tangent = number_input("損耗角正切 tanδ @20mK", value=2.2e-5, format="%.1e")
  conductor_resistivity = number_input("銀導體電阻率 ρ (Ω·m) @20mK", value=1.0e-12, format="%.1e")

  subheader("📡 訊號設定") # 訊號參數
  freq = slider("頻率 (GHz)", 0.1, 26.0, 5.0, 0.1)
  rise_time = slider("訊號上升時間 (ps)", 10, 500, 50, 10)
  v_amplitude = slider("訊號振幅 (V)", 0.1, 2.0, 0.5, 0.1)

def calculate_stripline_params(w, s, h, eps_r, freq_ghz): # ========== 計算模組 ==========
    """計算 stripline 單位長度參數 (簡化 Hammerstad 模型)"""
    w, s, h = w*1e-6, s*1e-6, h*1e-6  # 轉為公尺
    f = freq_ghz * 1e9
    
    # 有效介電常數
    eps_eff = eps_r
    
    # 特性阻抗近似 (單端)
    Z0 = 60/sqrt(eps_r) * log(4*h/(0.67*pi*w*(0.8 + s/h)))
    
    # 單位長度電容與電感
    C = eps_eff * epsilon_0 * (w/h) * 1.1  # 簡化平行板模型修正
    L = mu_0 * (h/w) * 1.1
    
    # 互電容/互電感 (耦合係數近似)
    k_coupling = exp(-pi * s / (2*h))  # 經驗耦合係數
    C_m = k_coupling * C * 0.3
    L_m = k_coupling * L * 0.3
    
    # 傳播速度
    v_p = c / sqrt(eps_eff)
    
    return {
        'Z0': Z0, 'C': C, 'L': L, 'C_m': C_m, 'L_m': L_m,
        'v_p': v_p, 'k_coupling': k_coupling
    }

def calculate_crosstalk(params, length_m, freq_ghz, rise_time_ps, v_amp):
    """計算 NEXT/FEXT 串擾"""
    C, L, C_m, L_m = params['C'], params['L'], params['C_m'], params['L_m']
    v_p = params['v_p']
    
    # 耦合係數
    K_b = 0.25 * (C_m/C + L_m/L)  # NEXT 係數
    K_f = 0.5 * (C_m/C - L_m/L) * v_p  # FEXT 係數
    
    # 傳輸延遲
    T_D = length_m / v_p
    
    # 頻率相關參數
    f = freq_ghz * 1e9
    omega = 2 * pi * f
    
    # 上升時間對應頻寬
    bw = 0.35 / (rise_time_ps * 1e-12)
    
    # NEXT 峰值電壓 (階躍響應近似)
    V_next_peak = K_b * v_amp * min(1, T_D / (rise_time_ps*1e-12))
    
    # FEXT 峰值電壓 (微分響應)
    dVdt = v_amp / (rise_time_ps * 1e-12)
    V_fext_peak = abs(K_f) * length_m * dVdt * exp(-length_m * 0.1)  # 加入衰減
    
    # 轉換為 dB
    next_db = 20 * log10(max(V_next_peak/v_amp, 1e-10))
    fext_db = 20 * log10(max(V_fext_peak/v_amp, 1e-10))
    
    return {
        'K_b': K_b, 'K_f': K_f, 'T_D_ns': T_D*1e9,
        'V_next_V': V_next_peak, 'V_fext_V': V_fext_peak,
        'NEXT_dB': next_db, 'FEXT_dB': fext_db
    }

MENU, 表單=[], ['串擾', '', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
if menu==len(表單): #
  pass
elif menu==MENU[1]: #
  pass
elif menu==MENU[0]: #串擾
  #pass
#if button("🔄 執行模擬"): # ========== 主計算 ==========
    L_m = line_length / 1000  ## 參數轉換 mm → m
    
    params = calculate_stripline_params(trace_width, trace_spacing, dielectric_thick, epsilon_r, freq) # 計算傳輸線參數
    
    results = calculate_crosstalk(params, L_m, freq, rise_time, v_amplitude) # 計算串擾
    
    # ========== 結果顯示 ==========
    col1, col2, col3 = columns(3)
    
    with col1:
        metric("特性阻抗 Z₀", f"{params['Z0']:.1f} Ω")
        metric("耦合係數 k", f"{params['k_coupling']:.3f}")
    
    with col2:
        metric("NEXT (近端串擾)", f"{results['NEXT_dB']:.2f} dB", 
                 delta=f"{results['V_next_V']*1e3:.3f} mV" if results['V_next_V'] > 0 else None)
    
    with col3:
        metric("FEXT (遠端串擾)", f"{results['FEXT_dB']:.2f} dB",
                 delta=f"{results['V_fext_V']*1e3:.3f} mV" if results['V_fext_V'] > 0 else None)
    
    # ========== 頻譜圖 ==========
    subheader("📊 串擾頻率響應")
    
    freqs = logspace(8, 10.5, 200)  # 100 MHz ~ 30 GHz
    next_db_freq = []
    fext_db_freq = []
    
    for f_ghz in freqs / 1e9:
        p = calculate_stripline_params(trace_width, trace_spacing, dielectric_thick, epsilon_r, f_ghz)
        r = calculate_crosstalk(p, L_m, f_ghz, rise_time, v_amplitude)
        next_db_freq.append(r['NEXT_dB'])
        fext_db_freq.append(r['FEXT_dB'])
    
    fig = Figure()
    fig.add_trace(Scatter(x=freqs/1e9, y=next_db_freq, name='NEXT', line=dict(color='red')))
    fig.add_trace(Scatter(x=freqs/1e9, y=fext_db_freq, name='FEXT', line=dict(color='blue')))
    fig.add_hline(y=-60, line_dash="dash", annotation_text="Cri/oFlex 規格 -60 dB", annotation_position="top right", line_color="green")
    
    fig.update_layout(
        xaxis_title="頻率 (GHz)", yaxis_title="串擾 (dB)",
        xaxis_type="log", hovermode="x unified",
        height=400, template="plotly_white"
    )
    plotly_chart(fig, use_container_width=True)
    
    # ========== 低溫效應分析 ==========
    #with expander("🌡️ 低溫 (20mK) 效應分析"):
    markdown(f"""
    ### 20mK 環境下的關鍵修正
    
    | 效應 | 室溫 (300K) | 20mK | 對串擾影響 |
    |------|-----------|------|-----------|
    | 導體損耗 | ~1.6×10⁻⁸ Ω·m | ~1×10⁻¹² Ω·m | ✅ 降低插入損耗，串擾耦合更明顯 |
    | 介電損耗 | ~0.002 | {loss_tangent:.1e} | ✅ 降低介質吸收，信號完整性提升 |
    | 熱噪聲電壓 | ~0.25 nV/√Hz | ~0.002 nV/√Hz | ✅ 信噪比顯著提升 |
    | 傳輸延遲變化 | 基準 | -0.3% | ⚠️ εᵣ 微調需校準 |
    
    > 📌 **設計建議**：在 20mK 下，雖然串擾耦合係數理論不變，但由於損耗極低，
    > 長距離傳輸時串擾累積效應需特別注意。建議保持線間距 ≥ 3×線寬 [[88]]。
    """)
    
    # ========== 參數掃描 ==========
    subheader("🔍 參數掃描：線間距對串擾影響")
    
    spacings = arange(50, 301, 25)
    scan_next = []
    scan_fext = []
    
    for s in spacings:
        p = calculate_stripline_params(trace_width, s, dielectric_thick, epsilon_r, freq)
        r = calculate_crosstalk(p, L_m, freq, rise_time, v_amplitude)
        scan_next.append(r['NEXT_dB'])
        scan_fext.append(r['FEXT_dB'])
    
    fig2 = Figure()
    fig2.add_trace(Scatter(x=spacings, y=scan_next, name='NEXT', mode='lines+markers'))
    fig2.add_trace(Scatter(x=spacings, y=scan_fext, name='FEXT', mode='lines+markers'))
    fig2.add_hline(y=-60, line_dash="dot", line_color="gray")
    
    fig2.update_layout(
        xaxis_title="線間距 s (μm)", yaxis_title="串擾 (dB)",
        height=350, template="plotly_white"
    )
    plotly_chart(fig2, use_container_width=True)
    
    # ========== 匯出結果 ==========
    download_button(
        "📥 下載模擬結果 (CSV)",
        data=f"Parameter,Value\nLength_mm,{line_length}\nSpacing_um,{trace_spacing}\nNEXT_dB,{results['NEXT_dB']:.3f}\nFEXT_dB,{results['FEXT_dB']:.3f}",
        file_name="crioflex_crosstalk_results.csv",
        mime="text/csv"
    )

else:
    info("👈 請在左側調整參數後點擊 **執行模擬**")

with expander("📚 參考文獻與理論來源"): # ========== 參考文獻 ==========
    markdown("""
    1. Delft Circuits. *Cri/oFlex® Datasheet* - 低溫撓性傳輸線規格 [[3]][[10]]
    2. Wang et al. (2016). *Flexible superconducting Nb transmission lines on thin film*, 
       Supercond. Sci. Technol. - 20mK 損耗測量 [[1]]
    3. Bogatin, E. *Signal Integrity Journal* (2024). "How Interconnects Work: Crosstalk Quantification" [[81]]
    4. Cadence Design Systems. "Deep Dive Into Near End Crosstalk (NEXT)" - 耦合係數公式 [[79]]
    5. IEEE 802.3. *Crosstalk in High-Speed Links* - FEXT/NEXT 測量標準 [[84]]
    
    > ⚠️ **免責聲明**：本模擬器基於簡化傳輸線理論，實際量子系統佈線請結合 3D EM 模擬 
    > (如 HFSS, CST) 與實測校準。
    """)
