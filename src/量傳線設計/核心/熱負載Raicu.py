import numpy as np

COEFFS = {
    "outer": [-3.198399, 20.49947, -66.11415, 117.6898, -121.4773, 76.21467, -28.74949, 5.984756, -0.5266892],
    "dielectric": [2.7380, -30.677, 89.430, -136.99, 124.69, -69.556, 23.320, -4.3135, 0.33829],
    "inner": [-2.750003, 25.84512, -74.18405, 113.5856, -96.84387, 46.38328, -11.82451, 1.321682, -0.02456645],
}

VALID_RANGE = {
    "outer": {"min": 2.0, "max": 297.6},
    "dielectric": {"min": 4.0, "max": 300.0},
    "inner": {"min": 2.3, "max": 292.6},
}

# 電阻率擬合係數 (Table 6)
COEFFS_RHO = [-8.327474, 10.01214, -52.83315, 122.5470, -152.7599, 109.0327, -44.41614, 9.598158, -0.8539285]
RHO_MIN_TEMP = 3.8
RHO_LOW_T = 9.928e-9  # Ω·m

# 電纜截面積 (m²) - Table 2
A_OUTER = 0.2389e-6
A_DIELECTRIC = 0.3098e-6
A_INNER = 0.0324e-6

# 製冷機溫度級預設參數 (Table 1)
DEFAULT_STAGES = {
    "50K":   {"T": 40.0, "cooling_power": 30.0, "length": 0.3053, "T_above": 297.0},
    "4K":    {"T": 3.5,  "cooling_power": 0.7,  "length": 0.3155, "T_above": 40.0},
    "Still": {"T": 1.4,  "cooling_power": 7e-3, "length": 0.2775, "T_above": 3.5},
    "CP":    {"T": 0.2,  "cooling_power": 1e-3, "length": 0.1965, "T_above": 1.4},
    "MXC":   {"T": 0.02, "cooling_power": 30e-6,"length": 0.1965, "T_above": 0.2},
}

# 論文提供的單條磁通偏置線動態熱負載 (Table 9) - 用於驗證
PAPER_ACTIVE_SINGLE = {
    "50K":   {"coax": 4.157e-6,  "attenuator": 0.0},
    "4K":    {"coax": 6.903e-7,  "attenuator": 2.018e-4},
    "Still": {"coax": 1.515e-8,  "attenuator": 0.0},
    "CP":    {"coax": 1.120e-8,  "attenuator": 0.0},
    "MXC":   {"coax": 1.084e-8,  "attenuator": 0.0},
}

# ======================================
# 熱導率計算函數
# ======================================


def k_poly(T, coeffs):
    """多項式計算熱導率"""
    if T <= 0:
        return 0.0
    logT = np.log10(T)
    val = coeffs[0]
    for i in range(1, 9):
        val += coeffs[i] * (logT ** i)
    return 10.0 ** val


def thermal_conductivity(T, mat_name):
    """熱導率 k(T)，含線性外插至低溫區"""
    r = VALID_RANGE[mat_name]
    if T >= r["min"] and T <= r["max"]:
        return k_poly(T, COEFFS[mat_name])
    elif T < r["min"]:
        k_min = k_poly(r["min"], COEFFS[mat_name])
        return k_min * (T / r["min"])
    else:
        return k_poly(r["max"], COEFFS[mat_name])


# ======================================
# 電阻率計算函數
# ======================================

def resistivity(T):
    """電阻率 ρ(T)"""
    if T < RHO_MIN_TEMP:
        return RHO_LOW_T
    elif T > 300:
        return k_poly(300, COEFFS_RHO)
    else:
        return k_poly(T, COEFFS_RHO)


# ======================================
# 靜態熱負載計算
# ======================================

def integrate_k(T_low, T_high, mat_name, n=2000):
    """數值積分 ∫ k(T) dT"""
    if T_high <= T_low:
        return 0.0
    Ts = np.linspace(T_low, T_high, n)
    ks = np.array([thermal_conductivity(t, mat_name) for t in Ts])
    return float(np.trapezoid(ks, Ts))


def calc_static_heat_single(stage_params, stage_name):
    """計算單條電纜在某溫度級的靜態熱負載"""
    T_L = stage_params["T"]
    T_H = stage_params["T_above"]
    L = stage_params["length"]
    
    q_outer = (A_OUTER / L) * integrate_k(T_L, T_H, "outer")
    q_dielectric = (A_DIELECTRIC / L) * integrate_k(T_L, T_H, "dielectric")
    q_inner = (A_INNER / L) * integrate_k(T_L, T_H, "inner")
    q_total = q_outer + q_dielectric + q_inner
    
    return {
        "outer": q_outer,
        "dielectric": q_dielectric,
        "inner": q_inner,
        "total": q_total
    }


# ======================================
# 動態熱負載計算
# ======================================

def calc_active_heat_flux_line(stages, I_mxc, att_dB=20, att_loc="4K"):
    """
    計算磁通偏置線的動態熱負載
    使用論文方法：從 MXC 電流反推各級電流，再積分電阻耗散
    """
    # 20 dB T-pad 衰減器參數 (R1=R2=40.91Ω, R3=10.1Ω)
    R1, R2, R3 = 40.91, 40.91, 10.1
    Z0 = 50.0
    
    # 衰減因子（電壓/電流比）
    att_ratio = 10 ** (att_dB / 20.0)
    
    # 從 MXC 電流反推輸入電流
    I_in = I_mxc * att_ratio
    
    active = {}
    for name in stages:
        T = stages[name]["T"]
        L = stages[name]["length"]
        
        # 決定此級的電流（在衰減器之上還是之下）
        if name == att_loc:
            I_local = I_in
        elif name in ["50K"] and att_loc == "4K":
            I_local = I_in
        elif name in ["Still", "CP", "MXC"] and att_loc == "4K":
            I_local = I_mxc
        else:
            I_local = I_in if name == att_loc else (I_mxc if stages[name]["T"] < stages[att_loc]["T"] else I_in)
        
        # 電纜電阻（簡化：使用平均溫度電阻率）
        R_cable = resistivity(T) * L / A_INNER
        P_cable = R_cable * I_local ** 2
        
        # 衰減器耗散（僅在衰減器所在級）
        P_att = 0.0
        if name == att_loc and att_dB > 0:
            # T-pad 衰減器功率耗散
            # 輸入功率 = I_in² * Z0 (近似)
            P_in = (I_in ** 2) * Z0
            # 衰減器耗散 = P_in - P_out = P_in * (1 - 10^(-att_dB/10))
            P_att = P_in * (1 - 10 ** (-att_dB / 10.0))
        
        active[name] = {
            "coax": P_cable,
            "attenuator": P_att,
            "total": P_cable + P_att
        }
    
    return active


def calc_active_heat_flux_line_simple(stages, I_mxc, att_dB=20, att_loc="4K"):
    """使用論文 Table 9 的驗證值（比例縮放）"""
    # 以論文值為基準，按電流平方比例縮放
    scale = (I_mxc / 0.4e-3) ** 2
    active = {}
    for name in stages:
        paper = PAPER_ACTIVE_SINGLE[name]
        active[name] = {
            "coax": paper["coax"] * scale,
            "attenuator": paper["attenuator"] * scale,
            "total": (paper["coax"] + paper["attenuator"]) * scale
        }
    return active


# ======================================
# 處理器規模計算
# ======================================

def calc_processor_lines(n_qubits_array, multiplex=6):
    """計算不同規模處理器所需的線數"""
    results = []
    for n in range(10, 16):
        n_qubits = n * n
        if n_qubits not in n_qubits_array and len(n_qubits_array) > 0:
            continue
        n_couplers = 2 * n * (n - 1)
        n_readout = int(np.ceil(n_qubits / multiplex))
        
        qubit_lines = 2 * n_qubits       # XY + flux bias
        coupler_lines = n_couplers         # flux bias
        readout_lines = 3 * n_readout    # read-in + read-out + TWPA pump
        total_lines = qubit_lines + coupler_lines + readout_lines
        
        results.append({
            "n": n,
            "qubits": n_qubits,
            "couplers": n_couplers,
            "readout_circuits": n_readout,
            "qubit_lines": qubit_lines,
            "coupler_lines": coupler_lines,
            "readout_lines": readout_lines,
            "total_lines": total_lines,
            "flux_lines": (qubit_lines // 2) + coupler_lines,  # 有電流的線
        })
    return results


# ======================================
# 總熱負載計算
# ======================================

def calc_total_heat(stages, n_qubits, multiplex=6, I_flux=0.4e-3, att_dB=20, att_loc="4K",
                    lna_power=7.8e-3, twpa_current=0.044e-3, use_paper_validation=True):
    """計算完整處理器的總熱負載"""
    
    # 取得處理器線數
    procs = calc_processor_lines([n_qubits], multiplex)
    if not procs:
        return None
    pc = procs[0]
    
    n_flux_lines = pc["flux_lines"]
    n_readout = pc["readout_circuits"]
    n_total_lines = pc["total_lines"]
    
    # 計算單條靜態熱負載
    static_single = {}
    for name, params in stages.items():
        static_single[name] = calc_static_heat_single(params, name)
    
    # 計算單條動態熱負載
    if use_paper_validation:
        active_single = calc_active_heat_flux_line_simple(stages, I_flux, att_dB, att_loc)
    else:
        active_single = calc_active_heat_flux_line(stages, I_flux, att_dB, att_loc)
    
    # 總熱負載
    total = {}
    for name in stages:
        # 靜態：所有線都貢獻
        q_static = static_single[name]["total"] * n_total_lines
        
        # 動態：只有 flux bias 線有電流
        q_active_flux = active_single[name]["total"] * n_flux_lines
        
        # TWPA 泵浦線動態負載（小量，簡化為每條 readout 一個小值）
        # 論文提到 TWPA 泵浦線在 4K/Still/CP 有 10dB 衰減器，負載很小
        q_active_twpa = 0.0  # 簡化忽略（論文圖8說很小）
        
        # LNA 功耗（4K 級）
        q_lna = 0.0
        if name == "4K":
            q_lna = lna_power * n_readout
        
        q_active = q_active_flux + q_active_twpa + q_lna
        q_total = q_static + q_active
        
        cp = stages[name]["cooling_power"]
        fraction = (q_total / cp * 100) if cp > 0 else 0
        
        total[name] = {
            "static": q_static,
            "active": q_active,
            "active_flux": q_active_flux,
            "active_lna": q_lna,
            "total": q_total,
            "cooling_power": cp,
            "fraction": fraction,
            "margin": 100 - fraction
        }
    
    return {
        "processor": pc,
        "static_single": static_single,
        "active_single": active_single,
        "total": total
    }


# ======================================
# Streamlit UI
# ======================================

