import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from fontUtil2 import 配置中文
配置中文()

# ============================================================
# 柔性微波带线热负载与热化计算 — 基于 Paluch et al. APL 126, 034003 (2025)
# 结合 FLAX (Smith et al. 2021/2023) 与 Delft Cri/oFlex 参数
# ============================================================

st.set_page_config(page_title="柔性微波带线 多温区热负载计算", layout="wide")

st.title("🌡️ 柔性微波带线 (Flexline) 多温区热负载计算")
st.markdown(
    "基于论文: *Thermalization of a flexible microwave stripline measured by a superconducting qubit*  "
    "(Paluch et al., **Appl. Phys. Lett. 126, 034003 (2025)**)  "
    "& *FLAX* (Smith et al., IEEE TASC 2021 / arXiv:2306.13574)"
)
from streamlit import empty, pyplot
狀態=empty()
# ============================================================
# 側邊欄 - 全局參數
# ============================================================
st.sidebar.header("⚙️ 全局配置")

st.sidebar.subheader("温度级配置")
T_stages = {
    '300K': 300.0,   # 室温
    '80K': 80.0,     # 液氮/预冷级
    '20K': 20.0,     # 低温级
    '4K': 4.0,       # 液氦级
    '200mK': 0.20,   # 中间级
    '20mK': 0.020,   # 稀释制冷机基温
}

st.sidebar.markdown("**温度级 (K)**")
for name, default in T_stages.items():
    T_stages[name] = st.sidebar.number_input(f"{name}", value=default, format="%.3f", key=f"T_{name}")

st.sidebar.subheader("材料热导率模型")
with st.sidebar.expander("NbTi 超導態"):
    k_nbti_ref = st.number_input("k_ref @ 1K (W/m/K)", value=0.007, format="%.4f")
    nbti_exp = st.number_input("溫度指數", value=2.0, format="%.1f")

with st.sidebar.expander("Kapton (Polyimide)"):
    k_kapton_ref = st.number_input("k_ref @ 1K (W/m/K)", value=0.15, format="%.4f")
    kapton_exp = st.number_input("溫度指數", value=1.0, format="%.1f")

with st.sidebar.expander("PFA/PTFE"):
    k_pfa_ref = st.number_input("k_ref @ 1K (W/m/K)", value=0.08, format="%.4f")
    pfa_exp = st.number_input("溫度指數", value=1.5, format="%.1f")

with st.sidebar.expander("銅 (Cu, 熱沉/熱化用)"):
    k_cu_ref = st.number_input("k_ref @ 1K (W/m/K)", value=500.0, format="%.1f")
    cu_exp = st.number_input("溫度指數", value=1.0, format="%.1f", key='溫度指數')

st.sidebar.subheader("量子比特參數")
fr = st.sidebar.number_input("諧振器頻率 fr (GHz)", value=7.458, format="%.3f")
chi = st.sidebar.number_input("色散頻移 χ/2π (MHz)", value=2.70, format="%.2f")
kappa = st.sidebar.number_input("諧振器線寬 κ/2π (MHz)", value=4.10, format="%.2f")

st.sidebar.subheader("主動加熱參數")
P_pulse_input = st.sidebar.number_input("加熱脈衝輸入功率 (dBm)", value=4.0, format="%.1f")
P_pulse_atten = st.sidebar.number_input("稀釋級衰減器吸收功率 (μW)", value=0.25, format="%.2f")

# ============================================================
# 計算核心
# ============================================================

def k_material(T, k_ref, exp):
    return k_ref * (T ** exp)

def n_BE(f_hz, T):
    """Bose-Einstein 分布"""
    if T <= 0:
        return 0
    h = 6.626e-34
    kB = 1.381e-23
    x = h * f_hz / (kB * T)
    return 1.0 / (np.exp(x) - 1.0)

def compute_passive_heat_load(T_hot, T_cold, L_m, A_m2, k_ref, exp, n_points=5000):
    """計算穩態被動熱負載 Q = (1/L) ∫ k(T) A dT"""
    if T_hot <= T_cold:
        return 0.0
    T = np.linspace(T_cold, T_hot, n_points)
    k = k_material(T, k_ref, exp)
    G = k * A_m2
    integral = np.trapezoid(G, T)
    return integral / L_m

# ============================================================
# 分頁
# ============================================================
tabs = st.tabs([
    "📋 論文摘要",
    "🌡️ 被動熱負載 (穩態)",
    "⚡ 主動熱負載 (脈衝加熱)",
    "🔬 熱化時間與光子數",
    "📊 多溫區熱流圖",
    "📈 比較分析"
])

# ===================== 分頁 1: 論文摘要 =====================
with tabs[0]:
    st.header("論文摘要與關鍵發現")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("實驗設置")
        st.markdown("""
        **論文**: Paluch et al., *Appl. Phys. Lett.* 126, 034003 (2025)
        
        **對比兩種輸入鏈**:
        
        1. **傳統同軸電纜** (Coaxial Cable)
           - SMA 接頭衰減器
           - 60 dB 總衰減，分布於各溫度級
           - 20 mK 衰減器額外用銅辮熱化
           - 熱化時間常數: **τ_cool = 0.55 ms**
        
        2. **柔性微波帶線** (Flexline / Cri/oFlex® 3)
           - Delft Circuits 集成衰減器
           - 60 dB 總衰減，分布於各溫度級
           - 80K, 20K, 4K, 200mK, 20mK 各級熱夾具
           - 熱化時間常數: **τ_cool = 0.28 ms** (快 2x)
        
        **量子比特**: Fluxonium qubit
        - 諧振器頻率 fᵣ = 7.458 GHz
        - 色散頻移 χ/2π = 2.70 MHz
        - 線寬 κ/2π = 4.10 MHz
        - 諧振器-Qubit 耦合: 電容耦合
        """
        )
    
    with col2:
        st.subheader("關鍵發現")
        st.markdown("""
        **熱化性能**:
        - 柔性帶線衰減器熱化時間: **0.28 ms**
        - 同軸電纜衰減器熱化時間: **0.55 ms**
        - 帶線比同軸**快近一倍**
        
        **光子數 (被動熱負載指標)**:
        - 柔性帶線殘餘光子數: **⟨n⟩ = (2.2 ± 0.9) × 10⁻³**
        - 對應等效黑體溫度 ~58 mK (平衡態)
        - 此值處於文獻報告的下限範圍 (10⁻⁴ ~ 10⁻¹)
        
        **量子比特溫度**:
        - 柔性帶線: **T_q = (26.4 ± 2.0) mK**
        - 同軸電纜: **T_q = (30.4 ± 1.4) mK**
        - 均接近稀釋制冷機基溫 ~20 mK
        - 兩者無顯著差異
        
        **Qubit 性能**:
        - 能量弛豫率 Γ₁/2π = 76.0 kHz
        - 回聲退相干率 Γ₂^echo/2π = 40.7 kHz
        - 兩種輸入鏈之間無顯著性能差異
        """)
    
    #st.divider()
    st.subheader("温度级与衰减分布")
    st.markdown("""
    ```
    室溫 (300 K)
         │
    ┌────┴────┐
    │  30 dB  │ ← 柔性帶線: 80 K 熱夾具
    │ 衰減器  │    同軸: 80 K 熱化
    └────┬────┘
         │
       80 K 級
         │
    ┌────┴────┐
    │  20 dB  │ ← 柔性帶線: 20 K 熱夾具
    │ 衰減器  │    同軸: 20 K 熱化
    └────┬────┘
         │
       20 K 級
         │
    ┌────┴────┐
    │  10 dB  │ ← 柔性帶線: 4 K 熱夾具
    │ 衰減器  │    同軸: 4 K 熱化
    └────┬────┘
         │
       4 K 級
         │
    ┌────┴────┐
    │  0 dB   │ ← 可選濾波器
    │ 或濾波  │    同軸: 12 GHz 低通 @ 20 mK
    └────┬────┘
         │
    200 mK 級
         │
    ┌────┴────┐
    │  0 dB   │ ← 柔性帶線: 200 mK 熱夾具
    │ (無衰減)│    同軸: 200 mK 熱化
    └────┬────┘
         │
    20 mK 級 (稀釋級)
         │
    ┌────┴────┐
    │  0 dB   │ ← 柔性帶線: 20 mK 熱夾具
    │ (輸出)  │    同軸: 20 mK 熱化 + 銅辮
    └────┬────┘
         │
    Fluxonium Qubit + 諧振器
    ```
    
    **注**: 論文補充材料說明柔性帶線在 80K, 20K, 4K, 200mK, 20mK 均有定制熱夾具。
    同軸電纜則通過 Ag-鍍銅線在 40 mK 中間級熱化，20 mK 衰減器額外用銅辮熱化。
    """)

# ===================== 分頁 2: 被動熱負載 =====================
with tabs[1]:
    st.header("被動熱負載 (穩態傳導)")
    
    st.markdown("""
    被動熱負載通過低溫電纜材料從高溫級傳導至低溫級。
    對於柔性微波帶線 (Cri/oFlex® 3)，主要材料為 **NbTi 導體 + Kapton 介電層**。
    
    **公式**: $Q = \\frac{1}{L} \\int_{T_{cold}}^{T_{hot}} k(T) \\cdot A \\, dT$
    """)
    
    st.subheader("各溫度級間的被動熱負載")
    
    # 定義各段配置
    segments = [
        ('300K → 80K', 300.0, 80.0, 'flexline'),
        ('80K → 20K', 80.0, 20.0, 'flexline'),
        ('20K → 4K', 20.0, 4.0, 'flexline'),
        ('4K → 200mK', 4.0, 0.20, 'flexline'),
        ('200mK → 20mK', 0.20, 0.02, 'flexline'),
    ]
    
    # 材料參數 (典型值)
    # Flexline (Cri/oFlex 3): 假設截面
    # 參考 Delft 規格和 FLAX 對比
    A_flex_nbti = 1.0e-6  # m², NbTi 導體截面 (估計)
    A_flex_kapton = 5.0e-6  # m², Kapton 介電層截面 (估計)
    L_flex = 1.0  # m, 假設每段 1 m (總長約 2-3 m)
    
    # 同軸電纜 (CryoCoax 最小規格)
    A_coax_nbti = 2.0e-6  # m², 導體截面更大
    A_coax_ptfe = 15.0e-6  # m², PTFE 介電層截面更大
    L_coax = 1.0
    
    results = []
    for name, T_h, T_c, ctype in segments:
        # Flexline 熱負載
        Q_flex_nbti = compute_passive_heat_load(T_h, T_c, L_flex, A_flex_nbti, k_nbti_ref, nbti_exp)
        Q_flex_kapton = compute_passive_heat_load(T_h, T_c, L_flex, A_flex_kapton, k_kapton_ref, kapton_exp)
        Q_flex_total = Q_flex_nbti + Q_flex_kapton
        
        # Coax 熱負載 (參考對比)
        Q_coax_nbti = compute_passive_heat_load(T_h, T_c, L_coax, A_coax_nbti, k_nbti_ref, nbti_exp)
        Q_coax_ptfe = compute_passive_heat_load(T_h, T_c, L_coax, A_coax_ptfe, k_pfa_ref, pfa_exp)
        Q_coax_total = Q_coax_nbti + Q_coax_ptfe
        
        results.append({
            '溫度段': name,
            'T_hot (K)': T_h,
            'T_cold (K)': T_c,
            'Flexline NbTi (nW)': Q_flex_nbti * 1e9,
            'Flexline Kapton (nW)': Q_flex_kapton * 1e9,
            'Flexline 合計 (nW)': Q_flex_total * 1e9,
            'Flexline 合計 (μW)': Q_flex_total * 1e6,
            'Coax 合計 (nW)': Q_coax_total * 1e9,
            'Coax/Flex 比值': Q_coax_total / Q_flex_total if Q_flex_total > 0 else 0,
        })
    
    df_passive = pd.DataFrame(results)
    st.dataframe(df_passive, use_container_width=True, hide_index=True)
    
    # 繪圖
    fig, ax = plt.subplots(figsize=(12, 5))
    x = np.arange(len(segments))
    width = 0.35
    flex_vals = [r['Flexline 合計 (nW)'] for r in results]
    coax_vals = [r['Coax 合計 (nW)'] for r in results]
    
    ax.bar(x - width/2, flex_vals, width, label='Flexline (Cri/oFlex 3)', color='salmon')
    ax.bar(x + width/2, coax_vals, width, label='Coaxial (CryoCoax)', color='lightblue')
    ax.set_yscale('log')
    ax.set_ylabel('Heat Load (nW)', fontsize=12)
    ax.set_title('Passive Heat Load per Segment (1m length)', fontsize=14)
    ax.set_xticks(x)
    #狀態.code(segments)
    #[('300K → 80K', 300.0, 80.0, 'flexline'), ('80K → 20K', 80.0, 20.0, 'flexline'), ('20K → 4K', 20.0, 4.0, 'flexline'), ('4K → 200mK', 4.0, 0.2, 'flexline'), ('200mK → 20mK', 0.2, 0.02, 'flexline')]
    ax.set_xticklabels([r[0] for r in segments], rotation=15)  #'溫度段'
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    st.pyplot(fig)
    
    st.info("""
    **關鍵觀察**: 
    - 柔性帶線由於截面緊湊，被動熱負載通常比同軸電纜低 2-5 倍
    - 高溫段 (300K→80K, 80K→20K) 熱負載最大，但對稀釋級影響小
    - 低溫段 (4K→200mK, 200mK→20mK) 熱負載雖小，但對制冷機負擔最敏感
    - NbTi 超導態熱導率極低，熱流主要由 Kapton/PTFE 介電層主導
    """)

# ===================== 分頁 3: 主動熱負載 =====================
with tabs[2]:
    st.header("主動熱負載 (脈衝加熱)")
    
    st.markdown("""
    論文中使用 **DC 加熱脈衝** (4 dBm, 0.25 μW @ 稀釋級衰減器) 來主動加熱衰減器，
    測量其熱化時間常數。此外，日常的 Readout/Control 脈衝也會產生主動熱負載。
    
    **主動熱負載來源**:
    1. Readout 脈衝: 測量諧振器狀態
    2. Control 脈衝: 操控量子比特
    3. DC 加熱脈衝: 論文實驗用，功率 4 dBm → 稀釋級 0.25 μW
    
    **熱化動態模型** (論文 Eq. 3):
    $$T(t_{cool}) = T_{eq} + \\Delta T \\exp(-t_{cool}/\\tau_{cool})$$
    
    其中 $T_{eq}$ = 平衡溫度, $\\tau_{cool}$ = 熱化時間常數, $\\Delta T$ = 加熱溫升。
    """)
    
    st.subheader("脈衝加熱功率計算")
    
    # 輸入功率 dBm 轉換
    P_input_mW = 10 ** (P_pulse_input / 10.0)  # mW
    P_input_uW = P_input_mW * 1000
    
    col1, col2, col3 = st.columns(3)
    col1.metric("輸入功率", f"{P_pulse_input} dBm", f"{P_input_uW:.2f} μW")
    col2.metric("稀釋級衰減器吸收", f"{P_pulse_atten} μW", "論文給定")
    col3.metric("其他級功率", "> 0.25 μW", "更高溫度級吸收更多")
    
    st.subheader("各溫度級主動熱負載分布")
    
    # 假設衰減分布 (論文: 60 dB 總衰減，分布於各級)
    # 典型分布: 30 dB @ 80K, 20 dB @ 20K, 10 dB @ 4K (或其他組合)
    # 功率隨衰減下降: P_out = P_in × 10^(-Att/10)
    
    attenuation_distribution = {
        '300K': 0,
        '80K': 30,
        '20K': 20,
        '4K': 10,
        '200mK': 0,
        '20mK': 0,
    }
    
    # 計算各級吸收的功率 (假設輸入 4 dBm = 2.51 mW)
    P_in = P_input_mW  # mW
    P_at_each = {}
    P_cumulative = P_in
    
    for stage, att in attenuation_distribution.items():
        P_absorbed = P_cumulative * (1 - 10**(-att/10.0))  # mW
        P_at_each[stage] = P_absorbed * 1000  # μW
        P_cumulative = P_cumulative * 10**(-att/10.0)
    
    df_active = pd.DataFrame({
        '溫度級': list(attenuation_distribution.keys()),
        '衰減 (dB)': list(attenuation_distribution.values()),
        '吸收功率 (μW)': [P_at_each[s] for s in attenuation_distribution.keys()],
        '透射功率 (μW)': [P_cumulative * 1000] + [P_cumulative * 1000 * 10**(-sum(list(attenuation_distribution.values())[:i+1])/10) for i in range(len(attenuation_distribution)-1)],
    })
    st.dataframe(df_active, use_container_width=True, hide_index=True)
    
    st.subheader("熱化動態模擬")
    
    tau_flex = 0.28e-3  # s, 柔性帶線熱化時間
    tau_coax = 0.55e-3  # s, 同軸電纜熱化時間
    
    t_cool = np.linspace(0, 2.0e-3, 500)  # 0 to 2 ms
    
    # 論文給定的溫升 (不同加熱脈衝寬度)
    DT_values = [24e-3, 55e-3, 114e-3]  # K (mK 轉換)
    T_eq = 58e-3  # K, 平衡溫度 (論文擬合值)
    
    fig, ax = plt.subplots(figsize=(12, 5))
    for DT, label in zip(DT_values, ['0.5 μs', '5 μs', '50 μs']):
        T_flex = T_eq + DT * np.exp(-t_cool / tau_flex)
        T_coax = T_eq + DT * np.exp(-t_cool / tau_coax)
        ax.plot(t_cool * 1000, T_flex * 1000, label=f'Flexline, θ_heat={label}', linestyle='-', linewidth=2)
        ax.plot(t_cool * 1000, T_coax * 1000, label=f'Coax, θ_heat={label}', linestyle='--', linewidth=2, alpha=0.7)
    
    ax.axhline(y=T_eq * 1000, color='gray', linestyle=':', alpha=0.5, label=f'T_eq = {T_eq*1000:.0f} mK')
    ax.set_xlabel('Cooling Time t_cool (ms)', fontsize=12)
    ax.set_ylabel('Temperature T (mK)', fontsize=12)
    ax.set_title('Thermalization of Attenuators After Heat Pulse', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    
    st.markdown("""
    **圖表解讀**: 論文使用 DC 加熱脈衝 (4 dBm) 主動加熱衰減器，測量冷卻曲線。
    - 柔性帶線 (實線): 熱化時間常數 **0.28 ms** → 衰減器更快恢復到平衡溫度
    - 同軸電纜 (虛線): 熱化時間常數 **0.55 ms** → 衰減器在高溫停留更久
    - 三種脈衝寬度 (0.5, 5, 50 μs) 對應不同溫升 ΔT = 24, 55, 114 mK
    - 熱化更快意味著：連續脈衝操作時，衰減器平均溫度更低，光子數更少
    """)

# ===================== 分頁 4: 熱化時間與光子數 =====================
with tabs[3]:
    st.header("熱化時間與殘餘光子數")
    
    st.markdown("""
    **論文核心測量**: 使用量子比特退相干來推斷諧振器中的光子數，從而評估輸入鏈的熱化性能。
    
    **光子-量子比特退相干關係** (論文 Eq. 1-2):
    
    $$\\Gamma_{\\phi n} + 2i\\Delta f_{q;\\bar{n}} = \\frac{\\chi^2}{\\kappa^2 + \\chi^2} \\kappa \\bar{n} \\left( \\sqrt{1 + i\\frac{2\\chi}{\\kappa \\bar{n}}} - 1 \\right)$$
    
    在 $\\chi \\ll \\kappa$ 且 $\\bar{n} \\ll 0.1$ 的極限下：
    $$\\Gamma_{\\phi n} \\approx \\frac{\\chi^2}{\\kappa} \\bar{n}$$
    
    由此從測量的退相干率推導光子數 $\\bar{n}$。
    """)
    
    st.subheader("殘餘光子數與等效溫度")
    
    # 論文測量值
    n_bar_measured = 2.2e-3
    n_bar_err = 0.9e-3
    
    # 從光子數計算等效黑體溫度
    h = 6.626e-34
    kB = 1.381e-23
    f_r = fr * 1e9
    
    # T_eff 從 n_BE = n_bar
    # n = 1/(exp(hf/kT) - 1) => T = hf / (k ln(1 + 1/n))
    T_eff = h * f_r / (kB * np.log(1 + 1 / n_bar_measured))
    
    col1, col2, col3 = st.columns(3)
    col1.metric("測量光子數 ⟨n⟩", f"{n_bar_measured:.1e}", f"± {n_bar_err:.1e}")
    col2.metric("等效黑體溫度", f"{T_eff*1000:.1f} mK", f"諧振器 fᵣ = {fr} GHz")
    col3.metric("量子比特溫度", f"26.4 mK", "接近基溫 20 mK")
    
    st.subheader("不同溫度下的平衡光子數")
    
    T_range = np.linspace(10e-3, 100e-3, 200)  # 10 mK to 100 mK
    n_BE_range = [n_BE(f_r, T) for T in T_range]
    
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.semilogy(T_range * 1000, n_BE_range, 'b-', linewidth=2, label=f'Bose-Einstein, fᵣ={fr} GHz')
    ax.axhline(y=n_bar_measured, color='red', linestyle='--', label=f'Measured ⟨n⟩ = {n_bar_measured:.1e}')
    ax.axvline(x=T_eff * 1000, color='green', linestyle='--', label=f'T_eff = {T_eff*1000:.1f} mK')
    ax.axvline(x=20, color='gray', linestyle=':', alpha=0.5, label='Cryostat base T = 20 mK')
    ax.set_xlabel('Temperature (mK)', fontsize=12)
    ax.set_ylabel('Average Photon Number ⟨n⟩', fontsize=12)
    ax.set_title('Equilibrium Photon Number in Resonator vs Temperature', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    
    st.info("""
    **關鍵洞察**:
    - 在 20 mK 基溫下，7.458 GHz 諧振器的平衡光子數應為 ~10⁻⁸ 量級
    - 實測 ~2.2 × 10⁻³ 遠高於平衡值，說明輸入鏈存在**非平衡熱光子**
    - 這些熱光子來自高溫級通過微波線傳導的黑體輻射
    - 論文測量的 ⟨n⟩ ~ 2.2 × 10⁻³ 對應等效溫度 ~58 mK，處於文獻報告的下限 (10⁻⁴ ~ 10⁻¹)
    - 這意味著柔性帶線的熱化性能與傳統同軸相當甚至略優
    """)
    
    st.subheader("熱化時間常數對比")
    
    tau_data = {
        '柔性帶線 (Flexline)': 0.28,
        '同軸電纜 (Coaxial)': 0.55,
    }
    
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    colors = ['salmon', 'lightblue']
    for i, (name, tau) in enumerate(tau_data.items()):
        ax2.barh(i, tau, color=colors[i], edgecolor='black', height=0.5)
        ax2.text(tau + 0.02, i, f'{tau} ms', va='center', fontsize=12, fontweight='bold')
    ax2.set_yticks(range(len(tau_data)))
    ax2.set_yticklabels(tau_data.keys())
    ax2.set_xlabel('Thermalization Time Constant τ_cool (ms)', fontsize=12)
    ax2.set_title('Attenuator Thermalization Time Comparison', fontsize=14)
    ax2.grid(True, alpha=0.3, axis='x')
    st.pyplot(fig2)
    
    st.markdown("""
    **熱化時間的物理意義**:
    - 衰減器吸收微波功率後溫度瞬間升高
    - 熱化時間 τ_cool 決定了溫度恢復到平衡的速度
    - 更快的熱化 (τ 更小) → 連續操作時平均溫度更低 → 更少光子數
    - 柔性帶線 0.28 ms 比同軸 0.55 ms 快近一倍，主要歸因於更好的熱夾具設計
    """)

# ===================== 分頁 5: 多溫區熱流圖 =====================
with tabs[4]:
    st.header("多溫區熱流圖")
    
    st.markdown("""
    綜合被動熱負載 (穩態傳導) 與主動熱負載 (脈衝加熱) 的全鏈路熱流圖。
    """)
    
    # 建立熱流模型
    stages = ['300K', '80K', '20K', '4K', '200mK', '20mK']
    T_vals = [T_stages[s] for s in stages]
    
    # 被動熱流 (連續傳導)
    Q_passive = []
    for i in range(len(stages)-1):
        T_h, T_c = T_vals[i], T_vals[i+1]
        # Flexline 簡化計算
        Q = compute_passive_heat_load(T_h, T_c, 0.5, A_flex_kapton, k_kapton_ref, kapton_exp)
        Q_passive.append(Q * 1e9)  # nW
    
    # 主動熱流 (脈衝加熱，各級衰減器吸收)
    Q_active = [P_at_each[s] * 1000 for s in stages]  # nW (μW → nW)
    
    # 熱流圖
    fig, ax = plt.subplots(figsize=(14, 6))
    
    y_positions = np.arange(len(stages))
    
    # 繪製溫度級
    for i, (stage, T) in enumerate(zip(stages, T_vals)):
        color = plt.cm.coolwarm(1.0 - (T - 0.02) / (300 - 0.02))
        ax.barh(i, 1.0, height=0.6, color=color, edgecolor='black', alpha=0.8)
        ax.text(0.5, i, f'{stage}\nT = {T:.3f} K', ha='center', va='center', 
                fontsize=11, fontweight='bold', color='white' if T > 50 else 'black')
    
    # 繪製被動熱流箭頭
    for i in range(len(stages)-1):
        Q_val = Q_passive[i]
        arrow_width = min(max(np.log10(Q_val + 1) * 0.05, 0.01), 0.3)
        ax.annotate('', xy=(1.1, i+1), xytext=(1.1, i),
                   arrowprops=dict(arrowstyle='->', color='red', lw=arrow_width*10))
        ax.text(1.15, i + 0.5, f'Passive\n{Q_val:.1f} nW', fontsize=9, va='center', color='red')
    
    # 繪製主動熱流標記
    for i, stage in enumerate(stages):
        Q_act = Q_active[i]
        if Q_act > 0.1:
            ax.text(1.4, i, f'Active: {Q_act:.1f} nW', fontsize=9, va='center', color='blue')
    
    ax.set_xlim(-0.2, 1.8)
    ax.set_ylim(-0.5, len(stages) - 0.5)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_title('Cryogenic Input Chain Heat Flow Diagram', fontsize=14)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    st.pyplot(fig)
    
    st.markdown("""
    **熱流圖解讀**:
    - **紅色箭頭**: 被動熱負載 (穩態熱傳導)，從高溫級流向低溫級
    - **藍色文字**: 主動熱負載 (脈衝吸收)，各級衰減器吸收的功率
    - 被動熱流在高溫段 (300K→80K) 最大，但對稀釋級影響通過級聯衰減
    - 主動熱負載在稀釋級 (20 mK) 最敏感，因為制冷能力最低 (~μW 級)
    """)
    
    st.subheader("總熱負載匯總")
    
    # 計算到達 20mK 的總熱負載
    Q_passive_to_20mK = sum(Q_passive[-2:])  # 200mK→20mK + 4K→200mK (部分)
    Q_active_at_20mK = Q_active[-1]  # 20mK 級衰減器吸收
    
    # 實際上，高溫段被動熱負載被中間熱沉攔截，只有最後兩段到達 20mK
    Q_total_to_20mK = Q_passive[-1] + Q_active[-1]  # 200mK→20mK 傳導 + 20mK 主動
    
    col1, col2, col3 = st.columns(3)
    col1.metric("200mK→20mK 被動熱流", f"{Q_passive[-1]:.2f} nW")
    col2.metric("20mK 主動熱負載", f"{Q_active[-1]:.2f} nW")
    col3.metric("20mK 總熱負載", f"{Q_total_to_20mK:.2f} nW", "關鍵指標")
    
    st.info("""
    論文報告稀釋級衰減器吸收 0.25 μW = 250 nW 的加熱脈衝功率，
    但這是**主動實驗脈衝**，非常規操作功率。日常 Readout/Control 脈衝功率遠低於此。
    被動熱負載在 20mK 級通常為 nW 量級，是稀釋制冷機設計的關鍵約束。
    """)

# ===================== 分頁 6: 比較分析 =====================
with tabs[5]:
    st.header("柔性帶線 vs 同軸電纜 vs FLAX 比較")
    
    st.markdown("""
    **三種低溫微波互連技術熱性能對比**
    """)
    
    comparison_data = {
        '參數': [
            '材料結構',
            '介電材料',
            '導體材料',
            '熱化時間 (衰減器)',
            '殘餘光子數 ⟨n⟩',
            '量子比特溫度 T_q',
            '8 GHz 傳輸損耗',
            '8 GHz 串擾',
            '被動熱負載 (1K→100mK, 1ft)',
            '線芯密度',
            '最小彎曲半徑',
            '商業供應商',
        ],
        '柔性帶線 (Cri/oFlex 3)': [
            'NbTi/Kapton 微帶線',
            'Kapton (聚酰亞胺)',
            'NbTi',
            '0.28 ms',
            '~2.2 × 10⁻³',
            '~26.4 mK',
            '~7 dB (文獻)',
            '~-60 dB',
            '~TBD (估計低)',
            '高 (多通道)',
            '~0.3 mm',
            'Delft Circuits',
        ],
        '同軸電纜 (CryoCoax)': [
            'NbTi/PTFE 同軸',
            'PTFE',
            'NbTi',
            '0.55 ms',
            '~2.2 × 10⁻³ (類似)',
            '~30.4 mK',
            '~0.5 dB',
            '~-60 dB',
            '~10 nW/trace',
            '低 (單通道)',
            '較大 (半剛性)',
            'CryoCoax',
        ],
        'FLAX (改進版 2023)': [
            'NbTi/PFA 同軸帶線',
            'PFA',
            'NbTi',
            'N/A (無集成衰減)',
            'N/A (用於陣列)',
            'N/A (探測器陣列)',
            '~1.5 dB',
            '~-40 dB',
            '~5 nW/trace',
            '高 (10線芯)',
            '~2 mm',
            'Maybell Quantum',
        ],
    }
    
    df_compare = pd.DataFrame(comparison_data)
    st.dataframe(df_compare, use_container_width=True, hide_index=True)
    
    st.divider()
    
    st.subheader("多溫區熱負載計算對比")
    
    # 計算三種技術在各溫度段的熱負載
    temp_segments = [
        ('300K→80K', 300, 80),
        ('80K→20K', 80, 20),
        ('20K→4K', 20, 4),
        ('4K→200mK', 4, 0.2),
        ('200mK→20mK', 0.2, 0.02),
    ]
    
    # 簡化模型
    A_flex = 5.0e-6  # Kapton 主導
    A_coax = 15.0e-6  # PTFE 主導
    A_flax = 0.057e-6  # PFA 主導 (單線芯, 參考前作)
    
    L = 1.0  # m
    
    compare_results = []
    for name, Th, Tc in temp_segments:
        Q_flex = compute_passive_heat_load(Th, Tc, L, A_flex, k_kapton_ref, kapton_exp) * 1e9
        Q_coax = compute_passive_heat_load(Th, Tc, L, A_coax, k_pfa_ref, pfa_exp) * 1e9
        Q_flax = compute_passive_heat_load(Th, Tc, L, A_flax, k_pfa_ref, pfa_exp) * 1e9
        
        compare_results.append({
            '溫度段': name,
            'Flexline (nW)': Q_flex,
            'Coaxial (nW)': Q_coax,
            'FLAX 單線芯 (nW)': Q_flax,
            'Coax/Flex': Q_coax / Q_flex if Q_flex > 0 else 0,
        })
    
    df_compare2 = pd.DataFrame(compare_results)
    st.dataframe(df_compare2, use_container_width=True, hide_index=True)
    
    # 繪圖
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(temp_segments))
    width = 0.25
    
    flex_v = [r['Flexline (nW)'] for r in compare_results]
    coax_v = [r['Coaxial (nW)'] for r in compare_results]
    flax_v = [r['FLAX 單線芯 (nW)'] for r in compare_results]
    
    ax.bar(x - width, flex_v, width, label='Flexline (Cri/oFlex 3)', color='salmon')
    ax.bar(x, coax_v, width, label='Coaxial (CryoCoax)', color='lightblue')
    ax.bar(x + width, flax_v, width, label='FLAX (single trace)', color='gold')
    
    ax.set_yscale('log')
    ax.set_ylabel('Heat Load (nW)', fontsize=12)
    ax.set_title('Passive Heat Load Comparison Across Temperature Stages', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels([r['溫度段'] for r in compare_results], rotation=15)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    st.pyplot(fig)
    
    st.info("""
    **比較結論**:
    - **FLAX** 單線芯熱負載最低 (~5 nW @ 1K→100mK)，但為專用陣列設計
    - **柔性帶線** (Flexline) 熱負載介於同軸和 FLAX 之間，但集成度最高
    - **同軸電纜** 截面大，熱負載最高，但傳輸損耗最低
    - **柔性帶線** 的熱化性能 (0.28 ms) 優於同軸 (0.55 ms)，對連續操作更有利
    - 對於量子計算應用，三種技術均可達到 ~20-30 mK 的量子比特溫度，但柔性帶線在密度和熱化速度上有優勢
    """)

st.divider()
st.caption("Flexible Stripline Heat Load Calculator | Based on Paluch et al. APL 126, 034003 (2025) & FLAX (Smith et al. 2021/2023) | Streamlit Edition")
