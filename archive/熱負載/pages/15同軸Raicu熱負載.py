import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ======================================
# 頁面配置
# ======================================
st.set_page_config(
    page_title="低溫傳輸線熱負載模擬器",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================================
# 論文數據與模型
# ======================================

# 熱導率擬合係數 (Table 4)
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

def main():
    st.title("🧊 低溫傳輸線熱負載模擬器")
    st.markdown("""
    基於論文 **Raicu et al. (2025)** *Cryogenic thermal modeling of microwave high density signaling*  
    模擬 Bluefors XLD1000-SL 稀釋製冷機中 SC-086/50-SCN-CN 同軸電纜的熱負載。
    """)
    
    # ---- 側邊欄參數 ----
    st.sidebar.header("⚙️ 模擬參數設定")
    
    # 處理器規模
    st.sidebar.subheader("處理器規模")
    n_qubits = st.sidebar.slider("量子位元數量", 100, 225, 144, step=1)
    multiplex = st.sidebar.selectbox("讀出多工比", [4, 6, 8], index=1)
    
    # 電流參數
    st.sidebar.subheader("電流參數")
    I_flux = st.sidebar.slider("磁通偏置電流 (mA)", 0.1, 2.0, 0.4, step=0.1) * 1e-3
    att_dB = st.sidebar.selectbox("衰減器 (dB)", [0, 10, 20, 30], index=2)
    att_loc = st.sidebar.selectbox("衰減器位置", ["50K", "4K", "Still", "CP"], index=1)
    
    # LNA / TWPA
    st.sidebar.subheader("讀出鏈路")
    lna_power = st.sidebar.slider("LNA 功耗 (mW)", 0.0, 20.0, 7.8, step=0.1) * 1e-3
    
    # 溫度級參數
    st.sidebar.subheader("製冷機溫度級")
    with st.sidebar.expander("編輯溫度級參數"):
        stages = {}
        for name, defaults in DEFAULT_STAGES.items():
            col1, col2, col3 = st.columns(3)
            with col1:
                T = st.number_input(f"{name} T (K)", value=defaults["T"], format="%.3f", key=f"T_{name}")
            with col2:
                cp = st.number_input(f"{name} P (W)", value=defaults["cooling_power"], format="%.6e", key=f"CP_{name}")
            with col3:
                L = st.number_input(f"{name} L (m)", value=defaults["length"], format="%.4f", key=f"L_{name}")
            stages[name] = {"T": T, "cooling_power": cp, "length": L, "T_above": defaults["T_above"]}
    
    # 使用預設值按鈕
    if st.sidebar.button("恢復預設參數"):
        stages = {k: dict(v) for k, v in DEFAULT_STAGES.items()}
        st.rerun()
    
    # ---- 主頁面 ----
    
    # 1. 計算結果
    result = calc_total_heat(stages, n_qubits, multiplex, I_flux, att_dB, att_loc, lna_power)
    
    if result is None:
        st.error("無法計算該量子位元數量的處理器規模。請選擇 100-225 之間的完全平方數或接近值。")
        return
    
    pc = result["processor"]
    total = result["total"]
    
    # 頂部摘要卡片
    st.divider()
    st.subheader("📊 處理器配置摘要")
    
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("量子位元", pc["qubits"])
    c2.metric("耦合器", pc["couplers"])
    c3.metric("讀出電路", pc["readout_circuits"])
    c4.metric("總線數", pc["total_lines"])
    c5.metric("磁通偏置線", pc["flux_lines"])
    
    # 2. 總熱負載表格
    st.divider()
    st.subheader("🔥 各溫度級總熱負載")
    
    data = []
    for name in ["50K", "4K", "Still", "CP", "MXC"]:
        t = total[name]
        data.append({
            "溫度級": name,
            "溫度 (K)": f"{stages[name]['T']:.3f}",
            "靜態 (W)": f"{t['static']:.4e}",
            "動態 (W)": f"{t['active']:.4e}",
            "總計 (W)": f"{t['total']:.4e}",
            "冷卻功率 (W)": f"{t['cooling_power']:.4e}",
            "占比 (%)": f"{t['fraction']:.2f}",
            "安全餘量 (%)": f"{t['margin']:.2f}",
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # 3. 視覺化圖表
    st.divider()
    st.subheader("📈 熱負載視覺化")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        # 熱負載堆疊柱狀圖
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        
        stage_names = ["50K", "4K", "Still", "CP", "MXC"]
        x = np.arange(len(stage_names))
        width = 0.6
        
        static_vals = [total[s]["static"] for s in stage_names]
        active_vals = [total[s]["active"] for s in stage_names]
        cp_vals = [total[s]["cooling_power"] for s in stage_names]
        
        # 使用對數尺度顯示（因數值差異極大）
        ax1.bar(x - width/3, static_vals, width/2, label="靜態熱負載", color="steelblue", alpha=0.8)
        ax1.bar(x + width/3, active_vals, width/2, label="動態熱負載", color="coral", alpha=0.8)
        ax1.bar(x, cp_vals, width/2, label="冷卻功率", color="lightgray", alpha=0.5, edgecolor="black")
        
        ax1.set_yscale("log")
        ax1.set_ylabel("Power (W)", fontsize=12)
        ax1.set_title("各溫度級熱負載 vs 冷卻功率 (對數尺度)", fontsize=13)
        ax1.set_xticks(x)
        ax1.set_xticklabels(stage_names)
        ax1.legend()
        ax1.grid(axis="y", alpha=0.3)
        
        st.pyplot(fig1)
    
    with col_right:
        # 冷卻功率占比圖
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        
        fractions = [total[s]["fraction"] for s in stage_names]
        margins = [total[s]["margin"] for s in stage_names]
        colors_bar = ["green" if f < 100 else "red" for f in fractions]
        
        bars = ax2.bar(stage_names, fractions, color=colors_bar, alpha=0.8, edgecolor="black")
        ax2.axhline(y=100, color="red", linestyle="--", linewidth=2, label="100% 上限")
        ax2.set_ylabel("冷卻功率占比 (%)", fontsize=12)
        ax2.set_title(f"{n_qubits} 量子位元：各溫度級冷卻功率使用率", fontsize=13)
        ax2.legend()
        ax2.grid(axis="y", alpha=0.3)
        
        # 標註數值
        for bar, val in zip(bars, fractions):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 2,
                     f"{val:.1f}%", ha="center", va="bottom", fontsize=10, fontweight="bold")
        
        st.pyplot(fig2)
    
    # 4. 擴展規模分析
    st.divider()
    st.subheader("📉 擴展規模分析（100-225 量子位元）")
    
    qubit_range = [100, 121, 144, 169, 196, 225]
    scale_results = []
    for q in qubit_range:
        r = calc_total_heat(stages, q, multiplex, I_flux, att_dB, att_loc, lna_power)
        if r:
            scale_results.append({
                "qubits": q,
                "total_lines": r["processor"]["total_lines"],
                "50K": r["total"]["50K"]["fraction"],
                "4K": r["total"]["4K"]["fraction"],
                "Still": r["total"]["Still"]["fraction"],
                "CP": r["total"]["CP"]["fraction"],
                "MXC": r["total"]["MXC"]["fraction"],
            })
    
    if scale_results:
        df_scale = pd.DataFrame(scale_results)
        
        fig3, ax3 = plt.subplots(figsize=(12, 5))
        
        for stage in ["50K", "4K", "Still", "CP", "MXC"]:
            vals = [r[stage] for r in scale_results]
            ax3.plot(qubit_range[:len(vals)], vals, marker="o", linewidth=2, label=f"{stage}")
        
        ax3.axhline(y=100, color="red", linestyle="--", linewidth=2, label="冷卻功率上限")
        ax3.set_xlabel("量子位元數量", fontsize=12)
        ax3.set_ylabel("冷卻功率占比 (%)", fontsize=12)
        ax3.set_title("熱負載擴展趨勢", fontsize=13)
        ax3.legend()
        ax3.grid(alpha=0.3)
        ax3.set_ylim(0, 130)
        
        st.pyplot(fig3)
        
        st.dataframe(df_scale, use_container_width=True, hide_index=True)
    
    # 5. 單條電纜詳細分析
    st.divider()
    st.subheader("🔬 單條電纜熱負載分解")
    
    tab1, tab2 = st.tabs(["靜態熱負載", "動態熱負載"])
    
    with tab1:
        static_data = []
        for name in ["50K", "4K", "Still", "CP", "MXC"]:
            s = result["static_single"][name]
            static_data.append({
                "溫度級": name,
                "外導體 (W)": f"{s['outer']:.4e}",
                "介電層 (W)": f"{s['dielectric']:.4e}",
                "內導體 (W)": f"{s['inner']:.4e}",
                "總計 (W)": f"{s['total']:.4e}",
            })
        st.dataframe(pd.DataFrame(static_data), use_container_width=True, hide_index=True)
    
    with tab2:
        active_data = []
        for name in ["50K", "4K", "Still", "CP", "MXC"]:
            a = result["active_single"][name]
            active_data.append({
                "溫度級": name,
                "電纜耗散 (W)": f"{a['coax']:.4e}",
                "衰減器耗散 (W)": f"{a['attenuator']:.4e}",
                "總動態 (W)": f"{a['total']:.4e}",
            })
        st.dataframe(pd.DataFrame(active_data), use_container_width=True, hide_index=True)
    
    # 6. 結論與建議
    st.divider()
    st.subheader("💡 結論與建議")
    
    # 找出最限制性的溫度級
    max_fraction = max((total[s]["fraction"], s) for s in ["50K", "4K", "Still", "CP", "MXC"])
    bottleneck = max_fraction[1]
    bottleneck_val = max_fraction[0]
    
    if bottleneck_val > 100:
        st.error(f"⚠️ **{bottleneck} 級熱負載已超過冷卻功率 ({bottleneck_val:.1f}%)！** 系統無法維持標稱溫度。")
    elif bottleneck_val > 80:
        st.warning(f"⚠️ **{bottleneck} 級熱負載接近冷卻功率上限 ({bottleneck_val:.1f}%)**，安全餘量不足。")
    else:
        st.success(f"✅ 所有溫度級均有足夠安全餘量。最限制級為 **{bottleneck}** ({bottleneck_val:.1f}%)。")
    
    # 估算理論上限
    st.markdown("""
    #### 理論擴展上限估算
    根據論文結論，Bluefors XLD1000-SL 使用 HDW 佈線的理論上限約為 **200 量子位元**，
    考慮工程安全餘量與 MXC 讀出電路空間後，實際建議上限約為 **140 量子位元**。
    """)
    
    # 改進建議
    with st.expander("🔧 改進方向"):
        st.markdown("""
        - **4K 以下改用超導電纜**：可大幅降低靜態與動態熱負載
        - **使用低溫 CMOS 控制電路**：減少室溫至 MXC 的傳輸線數量
        - **光纖傳輸**：在 MXC 處進行光-微波轉換，消除同軸電纜熱負載
        - **將 TWPA 泵浦終端電阻移至 CP 級**：降低 MXC 熱負載
        - **使用動態電感參量放大器（KIPA）**：可於 4K 運作，取代 TWPA + LNA
        """)


if __name__ == "__main__":
    main()
