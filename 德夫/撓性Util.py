from numpy import exp, log10, pi, sqrt
# ========== 新增: 撓性材料力學-電氣耦合模型 ==========

def calc_flexible_bending_effects(w_um, h_um, eps_r, bend_radius_mm, length_mm):
    """
    計算撓性傳輸線彎曲效應對電氣參數的影響
    
    參數:
        w_um: 線寬 (μm)
        h_um: 介電層厚度 (μm)
        eps_r: 相對介電常數
        bend_radius_mm: 彎曲半徑 (mm)
        length_mm: 傳輸線長度 (mm)
    
    返回:
        dict: 彎曲引起的參數變化
    """
    w, h = w_um*1e-6, h_um*1e-6
    R = bend_radius_mm * 1e-3  # 轉為公尺
    
    # Polyimide 材料參數 @20mK [[1]][[10]]
    E_young = 2.5e9  # 楊氏模量 (Pa)
    nu_poisson = 0.34  # 泊松比
    CTE = 20e-6  # 熱膨脹係數 (/K)
    
    # 彎曲應力計算 (梁理論)
    # 外側最大拉伸應力
    sigma_outer = E_young * (h/2) / R  # Pa
    
    # 內側最大壓縮應力
    sigma_inner = -sigma_outer
    
    # 應力引起的介電常數變化 (電致伸縮效應)
    # Δε/ε ≈ -0.5% @ 100 MPa (Polyimide 經驗值)
    depsilon_dsigma = -5e-12  # /Pa
    delta_eps_outer = eps_r * depsilon_dsigma * sigma_outer
    delta_eps_inner = eps_r * depsilon_dsigma * sigma_inner
    
    eps_r_bent = eps_r + (delta_eps_outer + delta_eps_inner) / 2 # 有效介電常數變化 (平均)
    
    # 阻抗變化估算
    # Z ∝ 1/√ε_eff, ΔZ/Z ≈ -0.5·Δε/ε
    delta_Z_pct = -0.5 * (eps_r_bent - eps_r) / eps_r * 100
    
    # 彎曲損耗增加 [[10]]
    # α_bend ∝ (h/R)² · f^(3/2)
    alpha_bend = 0.1 * (h/R)**2 * sqrt(5e9)  # dB/m @5GHz 參考
    
    # 臨界彎曲半徑 (避免永久變形)
    R_critical = h * E_young / (50e6)  # 50 MPa 屈服強度
    
    # 疲勞壽命估算 (彎曲循環次數)
    # N_f ≈ (R/R_critical)^m, m≈3-5 for Polyimide
    if R > R_critical:
        fatigue_cycles = int(1e6 * (R / R_critical)**4)
    else:
        fatigue_cycles = 0  # 超過臨界值，可能永久損壞
    
    return {
        'sigma_outer_MPa': sigma_outer / 1e6,
        'sigma_inner_MPa': sigma_inner / 1e6,
        'eps_r_bent': eps_r_bent,
        'delta_eps_pct': (eps_r_bent - eps_r) / eps_r * 100,
        'delta_Z_pct': delta_Z_pct,
        'alpha_bend_dBm': alpha_bend,
        'R_critical_mm': R_critical * 1e3,
        'fatigue_cycles': fatigue_cycles,
        'bend_safe': R > R_critical
    }


def calc_flexible_crosstalk_modification(params, bend_info, bend_radius_mm):
    """
    計算彎曲對串擾耦合係數的修正
    
    彎曲會改變:
    1. 線間有效距離 (外側增加, 內側減少)
    2. 耦合電容/電感分佈
    3. 模式轉換 (差模→共模)
    """
    R = bend_radius_mm * 1e-3
    s_eff = params.get('trace_spacing', 150e-6)  # 預設線間距
    
    # 彎曲引起的線間距變化
    # 外側通道: s_eff increases
    # 內側通道: s_eff decreases
    delta_s = s_eff * (s_eff / (2*R))  # 一階近似
    
    # 修正耦合係數
    k_original = params['k_coupling']
    
    # 外側通道耦合減弱
    k_outer = k_original * exp(-pi * delta_s / (2 * 75e-6))
    
    # 內側通道耦合增強
    k_inner = k_original * exp(pi * delta_s / (2 * 75e-6))
    
    # 平均耦合係數 (保守估計取較大值)
    k_bent = max(k_outer, k_inner)
    
    # 模式轉換損耗 (差模→共模)
    # 彎曲不對稱性引起
    mode_conversion_dB = 10 * log10(1 + (s_eff/R)**2)
    
    return {
        'k_original': k_original,
        'k_outer': k_outer,
        'k_inner': k_inner,
        'k_bent': k_bent,
        'mode_conversion_dB': mode_conversion_dB,
        'crosstalk_penalty_dB': 20*log10(k_bent/k_original)
    }
