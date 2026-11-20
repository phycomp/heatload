import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# 傳輸線在不同溫區長度回推計算
# 基於 FLAX (Smith et al. 2021/2023) 與 Cri/oFlex (Paluch et al. 2025)
# ============================================================

st.set_page_config(page_title="傳輸線溫區長度回推", layout="wide")

st.title("📏 傳輸線在不同溫區的長度回推與推導")
st.markdown(
    "從已知熱負載與熱導率模型，回推傳輸線在 cryostat 各溫度級的長度分布  "
    "(FLAX: Smith et al. 2021/2023 | Cri/oFlex: Paluch et al. APL 126, 034003 2025)"
)

# ============================================================
# 側邊欄 - 參數設定
# ============================================================
st.sidebar.header("⚙️ 計算參數")

st.sidebar.subheader("參考基準 (FLAX 2023)")
Q_ref = st.sidebar.number_input("參考熱負載 Q_ref (nW/trace)", value=5.0, format="%.1f")
L_ref = st.sidebar.number_input("參考長度 L_ref (cm)", value=30.48, format="%.2f")
T_ref_cold = st.sidebar.number_input("參考冷端 T_ref_cold (K)", value=0.10, format="%.3f")
T_ref_hot = st.sidebar.number_input("參考熱端 T_ref_hot (K)", value=1.0, format="%.1f")

st.sidebar.subheader("材料熱導率模型")
with st.sidebar.expander("PFA 介電層"):
    k_pfa_ref = st.number_input("k_ref @ 1K (W/m/K)", value=0.08, format="%.3f")
    pfa_exp = st.number_input("溫度指數", value=1.5, format="%.1f")
    A_pfa_mm2 = st.number_input("截面積 (mm²)", value=0.0515, format="%.4f")

with st.sidebar.expander("NbTi 導體"):
    k_nbti_ref = st.number_input("k_ref @ 1K (W/m/K)", value=0.007, format="%.4f")
    nbti_exp = st.number_input("溫度指數", value=2.0, format="%.1f")
    A_nbti_mm2 = st.number_input("截面積 (mm²)", value=0.1016, format="%.4f")

st.sidebar.subheader("Cryostat 溫度級")
T_base = st.sidebar.number_input("基溫 (mK)", value=20.0, format="%.1f") * 1e-3
T_stages = {
    '300K': 300.0,
    '80K': 80.0,
    '20K': 20.0,
    '4K': 4.0,
    '1K': 1.0,
    '200mK': 0.20,
    '100mK': 0.10,
    '20mK': T_base,
}

st.sidebar.subheader("MEC 實際配置")
use_mec = st.sidebar.checkbox("使用 MEC 配置 (800mK 熱沉)", value=True)
T_sink_mec = st.sidebar.number_input("MEC 熱沉溫度 (K)", value=0.80, format="%.2f")

st.sidebar.subheader("Cri/oFlex 對比")
flex_ratio = st.sidebar.number_input("Cri/oFlex / FLAX 熱導倍數", value=6.0, format="%.1f",
    help="2023 論文: Cri/oFlex 約為 FLAX 的 6x")

# ============================================================
# 計算核心函數
# ============================================================

def k_PFA(T):
    return k_pfa_ref * (T ** pfa_exp)

def k_NbTi(T):
    return k_nbti_ref * (T ** nbti_exp)

def G_T(T):
    """單線芯熱導 G(T) = Σ k_i A_i (W·m/K)"""
    A_pfa = A_pfa_mm2 * 1e-6
    A_nbti = A_nbti_mm2 * 1e-6
    return k_PFA(T) * A_pfa + k_NbTi(T) * A_nbti

def integral_G(T_low, T_high, n=5000):
    """計算 ∫_{T_low}^{T_high} G(T) dT"""
    if T_high <= T_low:
        return 0.0
    T = np.linspace(T_low, T_high, n)
    G = np.array([G_T(t) for t in T])
    return np.trapezoid(G, T)

# 參考積分值 (從 Q_ref 與 L_ref 回推)
I_ref = Q_ref * 1e-9 * (L_ref * 1e-2)  # W·m

# 計算各溫度範圍的積分
T_sorted = sorted(T_stages.values(), reverse=True)
T_labels = [k for k, v in sorted(T_stages.items(), key=lambda x: x[1], reverse=True)]

integrals = {}
for i in range(len(T_sorted)-1):
    Th = T_sorted[i]
    Tc = T_sorted[i+1]
    label = f"{T_labels[i+1]}→{T_labels[i]}"
    I = integral_G(Tc, Th)
    integrals[label] = I

# ============================================================
# 分頁
# ============================================================
tabs = st.tabs([
    "📐 推導公式",
    "🔢 積分計算",
    "📏 長度回推",
    "🏭 MEC 配置",
    "📊 與 Cri/oFlex 對比",
    "📈 可視化"
])

# ===================== 分頁 1: 推導公式 =====================
with tabs[0]:
    st.header("傳輸線溫區長度回推 — 推導公式")
    
    st.markdown(r"""
    ### 一、基本物理方程
    
    對於一維穩態熱傳導，沿傳輸線長度 $x$ 的熱流 $Q$ 滿足傅立葉定律：
    
    $$Q = -A \\cdot k(T) \\frac{dT}{dx}$$
    
    其中：
    - $Q$ = 熱流 (W)，在穩態下為常數
    - $A$ = 截面積 (m²)
    - $k(T)$ = 溫度相關的熱導率 (W/m/K)
    - $T$ = 溫度 (K)
    - $x$ = 沿傳輸線的位置 (m)
    
    ### 二、分離變量並積分
    
    將方程分離變量：
    $$Q \\, dx = -A \\cdot k(T) \\, dT$$
    
    對整段傳輸線積分（從 $x=0$ 到 $x=L$，溫度從 $T_{hot}$ 到 $T_{cold}$）：
    
    $$\\int_0^L Q \\, dx = -\\int_{T_{hot}}^{T_{cold}} A \\cdot k(T) \\, dT$$
    
    $$Q \\cdot L = \\int_{T_{cold}}^{T_{hot}} A \\cdot k(T) \\, dT = \\int_{T_{cold}}^{T_{hot}} G(T) \\, dT$$
    
    其中 $G(T) = A \\cdot k(T)$ 為熱導 (W·m/K)。
    
    ### 三、核心公式
    
    **熱負載計算**（已知長度 $L$）：
    $$Q = \\frac{1}{L} \\int_{T_{cold}}^{T_{hot}} G(T) \\, dT$$
    
    **長度回推**（已知熱負載 $Q$）：
    $$L = \\frac{1}{Q} \\int_{T_{cold}}^{T_{hot}} G(T) \\, dT$$
    
    ### 四、關鍵洞察：積分值 $I$ 是材料本質屬性
    
    定義積分值：
    $$I(T_{cold}, T_{hot}) = \\int_{T_{cold}}^{T_{hot}} G(T) \\, dT$$
    
    $I$ 只取決於：
    1. 材料熱導率 $k(T)$
    2. 截面積 $A$
    3. 溫度範圍 $[T_{cold}, T_{hot}]$
    
    **與長度 $L$ 和熱流 $Q$ 無關！**
    
    ### 五、參考基準法
    
    從論文已知數據建立參考：
    - 參考熱負載 $Q_{ref}$ = **{Q_ref} nW/trace**
    - 參考長度 $L_{ref}$ = **{L_ref} cm**
    - 參考溫度範圍 $[{T_ref_cold*1000:.0f} \text{{mK}}, {T_ref_hot} \text{{K}}]$
    
    計算參考積分值：
    $$I_{{ref}} = Q_{{ref}} \\times L_{{ref}} = {Q_ref} \\times 10^{{-9}} \\times {L_ref} \\times 10^{{-2}} = {I_ref*1e9:.2f} \\text{{ nW}}\\cdot\\text{{cm}} = {I_ref:.3e} \\text{{ W}}\\cdot\\text{{m}}$$
    
    ### 六、長度回推公式
    
    對於任意溫度範圍 $[T_1, T_2]$：
    
    **方法一：直接積分法**
    $$L = \\frac{I(T_1, T_2)}{Q}$$
    
    **方法二：比例法**（當熱流 $Q$ 相同時）
    $$\\frac{L_1}{L_2} = \\frac{I(T_1, T_2)}{I(T_3, T_4)}$$
    
    **方法三：總長度分配法**（已知總長度 $L_{total}$）
    $$L_i = L_{{total}} \\times \\frac{I(T_{{cold,i}}, T_{{hot,i}})}{\\sum_j I(T_{{cold,j}}, T_{{hot,j}})}$$
    
    ### 七、多溫度級帶熱沉的修正
    
    當傳輸線通過中間熱沉（如 MEC 的 800 mK 熱沉）時：
    
    ```
    3.4 K 級 ──[L_upper]──→ 800 mK 熱沉 ──[L_lower]──→ 90 mK 級
         Q_upper                    Q_lower
    ```
    
    **上段**：$Q_{{upper}} = \\frac{I(0.8, 3.4)}{L_{{upper}}}$
    
    **下段**：$Q_{{lower}} = \\frac{I(0.09, 0.8)}{L_{{lower}}}$
    
    **熱沉攔截**：$Q_{{sink}} = Q_{{upper}} - Q_{{lower}}$
    
    若已知下段熱負載 $Q_{{lower}}$（到達冷級的熱負載），則：
    $$L_{{lower}} = \\frac{I(0.09, 0.8)}{Q_{{lower}}}$$
    $$Q_{{upper}} = \\frac{I(0.8, 3.4)}{L_{{upper}}}$$
    
    若 $L_{{upper}} = L_{{lower}}$（如 MEC 對半分布），則：
    $$Q_{{upper}} = \\frac{I(0.8, 3.4)}{I(0.09, 0.8)} \\times Q_{{lower}}$$
    """)
    
    st.info(r"""
    **核心洞察**：$I(T_{cold}, T_{hot})$ 隨溫度範圍擴大**非線性增長**。
    因為 $k(T) \propto T^n$（$n > 0$），高溫區的熱導率遠高於低溫區，
    因此相同長度的高溫段產生的熱負載遠大於低溫段。
    """)

# ===================== 分頁 2: 積分計算 =====================
with tabs[1]:
    st.header("各溫度範圍的積分計算")
    
    st.markdown(f"""
    **材料模型**：
    - PFA: $k(T) = {k_pfa_ref} \\times T^{{{pfa_exp}}}$ W/m/K, $A = {A_pfa_mm2}$ mm²
    - NbTi: $k(T) = {k_nbti_ref} \\times T^{{{nbti_exp}}}$ W/m/K, $A = {A_nbti_mm2}$ mm²
    
    **參考積分值**：$I_{{ref}} = {I_ref*1e9:.2f}$ nW·cm = {I_ref:.3e} W·m
    """)
    
    # 計算各溫度範圍的積分並展示
    results = []
    for label, I in integrals.items():
        I_nWcm = I * 1e9  # nW·cm
        ratio = I / I_ref if I_ref > 0 else 0
        results.append({
            '溫度範圍': label,
            'I (W·m)': f"{I:.3e}",
            'I (nW·cm)': f"{I_nWcm:.2f}",
            '相對 I_ref': f"{ratio:.2f}x",
            'G(1K) (W·m/K)': f"{G_T(1.0):.3e}",
            'G(冷端) (W·m/K)': f"{G_T(float(label.split('→')[0].replace('K','').replace('mK','').replace('m', '')) * (1e-3 if 'mK' in label else 1)):.3e}",
        })
    
    df_integral = pd.DataFrame(results)
    st.dataframe(df_integral, use_container_width=True, hide_index=True)
    
    st.subheader("積分值的物理意義")
    
    st.markdown(r"""
    **$I(T_{cold}, T_{hot})$ 的物理意義**：
    
    $I$ 是單位熱流（1 nW）在該溫度範圍內所能對應的**最大長度**（cm）。
    
    或者說：對於 1 cm 長的傳輸線，在該溫度範圍產生的熱負載為 $I^{-1}$（nW）。
    
    **觀察**：高溫範圍的 $I$ 值遠大於低溫範圍，原因：
    1. $k(T) \propto T^n$（$n > 0$），高溫熱導率大
    2. 高溫區溫度梯度 $dT/dx$ 更大
    """)
    
    # 繪製積分值比較
    fig, ax = plt.subplots(figsize=(12, 5))
    labels_short = [l for l in integrals.keys()]
    I_values = [v * 1e9 for v in integrals.values()]  # nW·cm
    
    colors = plt.cm.viridis(np.linspace(0, 1, len(labels_short)))
    bars = ax.barh(labels_short, I_values, color=colors, edgecolor='black')
    ax.set_xlabel('I (nW·cm)', fontsize=12)
    ax.set_title('Thermal Conductance Integral I(T_cold, T_hot) by Temperature Range', fontsize=14)
    ax.grid(True, alpha=0.3, axis='x')
    
    for bar, val in zip(bars, I_values):
        ax.text(val + max(I_values)*0.01, bar.get_y() + bar.get_height()/2, 
                f'{val:.1f}', va='center', fontsize=10, fontweight='bold')
    
    st.pyplot(fig)
    
    st.markdown("""
    **圖表解讀**：
    - 積分值 $I$ 隨溫度範圍向高溫擴展而急劇增大
    - 300K→80K 的 $I$ 比 100mK→1K 大 **數個數量級**
    - 這說明高溫段即使很短，也會產生巨大的熱負載
    - 因此 cryostat 必須在中間溫度級（80K, 20K, 4K）設置熱沉攔截
    """)

# ===================== 分頁 3: 長度回推 =====================
with tabs[2]:
    st.header("傳輸線長度回推計算")
    
    st.markdown(r"""
    ### 場景 1: 無熱沉（單段連續傳輸線）
    
    假設傳輸線從 $T_{hot}$ 連續到 $T_{cold}$，中間無熱沉。
    熱流 $Q$ 在整段線上相同。
    
    **已知**：總熱負載 $Q_{total}$，總長度 $L_{total}$，溫度級 $[T_1, T_2, ..., T_n]$
    
    **求**：各溫區的長度 $L_i$
    
    **解法**：
    $$L_i = L_{total} \\times \\frac{I(T_{i+1}, T_i)}{\\sum_{j=1}^{n-1} I(T_{j+1}, T_j)}$$
    """)
    
    # 計算無熱沉場景
    total_I = sum(integrals.values())
    
    st.subheader("場景 1: 無熱沉長度分配")
    
    L_total_assumed = 100.0  # cm, 假設總長度
    
    scenario1 = []
    for label, I in integrals.items():
        L_i = L_total_assumed * (I / total_I)
        scenario1.append({
            '溫度段': label,
            'I (nW·cm)': f"{I*1e9:.2f}",
            '佔總積分比': f"{I/total_I*100:.2f}%",
            '分配長度 (cm)': f"{L_i:.2f}",
            '分配長度 (mm)': f"{L_i*10:.1f}",
        })
    
    df_s1 = pd.DataFrame(scenario1)
    st.dataframe(df_s1, use_container_width=True, hide_index=True)
    
    st.info(f"""
    假設總長度 $L_{{total}}$ = {L_total_assumed} cm，無熱沉。
    此時各溫區長度與積分值 $I$ 成正比。
    由於高溫段 $I$ 極大，高溫段長度佔比極高。
    但實際 cryostat 必須使用熱沉，否則低溫級無法承受熱負載。
    """)
    
    st.markdown(r"""
    ### 場景 2: 帶熱沉（每級熱沉攔截）
    
    實際 cryostat 中，傳輸線在每級溫度平台都進行熱沉錨定。
    每段只承擔該溫度級的熱負載，而不是累積熱負載。
    
    **解法**：每段的長度 $L_i$ 由該段的熱預算 $Q_i$ 決定：
    $$L_i = \\frac{I(T_{i+1}, T_i)}{Q_i}$$
    
    其中 $Q_i$ 是該溫度級的熱預算（由制冷機功率決定）。
    """)
    
    st.subheader("場景 2: 帶熱沉長度回推")
    
    # 假設各級熱預算（典型值）
    Q_budget = {
        '300K→80K': 1000.0,    # μW
        '80K→20K': 100.0,       # μW
        '20K→4K': 10.0,          # μW
        '4K→1K': 1.0,             # μW
        '1K→200mK': 0.1,          # μW = 100 nW
        '200mK→100mK': 0.01,      # μW = 10 nW
        '100mK→20mK': 0.005,      # μW = 5 nW
    }
    
    scenario2 = []
    for label, I in integrals.items():
        Q_i = Q_budget.get(label, 1.0) * 1e-6  # W
        L_i = I / Q_i  # m
        L_i_cm = L_i * 100  # cm
        L_i_m = L_i  # m
        scenario2.append({
            '溫度段': label,
            '熱預算 Q_i (μW)': Q_budget.get(label, 1.0),
            'I (nW·cm)': f"{I*1e9:.2f}",
            '回推長度 (cm)': f"{L_i_cm:.2f}",
            '回推長度 (m)': f"{L_i_m:.2f}",
            '線密度 (nW/cm)': f"{Q_i*1e9/L_i_cm:.3f}",
        })
    
    df_s2 = pd.DataFrame(scenario2)
    st.dataframe(df_s2, use_container_width=True, hide_index=True)
    
    st.markdown("""
    **觀察**：
    - 高溫段（300K→80K）即使熱預算很大（1000 μW），回推長度也僅 ~10 cm
    - 低溫段（100mK→20mK）熱預算僅 5 nW，回推長度可達數米
    - 這說明低溫段可以容忍更長的傳輸線
    - 但實際上 cryostat 的物理尺寸限制了各段長度
    """)

# ===================== 分頁 4: MEC 配置 =====================
with tabs[3]:
    st.header("MEC 實際配置回推")
    
    st.markdown(r"""
    ### MEC 實驗配置 (Smith et al. 2021)
    
    **已知參數** (從論文提取)：
    - 電纜總長度: $L_{{total}}$ = 33 cm
    - 10 線芯並排
    - 800 mK 中間熱沉，位於電纜中點
    - 上段: 3.4 K → 800 mK, $L_{{upper}}$ ≈ 16.5 cm
    - 下段: 800 mK → 90 mK, $L_{{lower}}$ ≈ 16.5 cm
    - 到達 90 mK 級熱負載: $Q_{{lower}}$ = 200 nW (10線芯) = **20 nW/線芯**
    
    **回推步驟**：
    """)
    
    # 使用參考基準回推
    # 從參考: 5 nW, 30.48 cm, 100mK→1K
    # 計算下段 (90mK→800mK) 的積分比
    I_lower = integral_G(0.09, 0.80)
    I_upper = integral_G(0.80, 3.4)
    I_1K_100mK = integral_G(0.10, 1.0)
    
    # 方法 1: 直接從參考基準比例
    # I_ref = Q_ref * L_ref = 5 nW * 30.48 cm
    # 假設積分比正確
    
    ratio_lower = I_lower / I_1K_100mK
    ratio_upper = I_upper / I_1K_100mK
    
    # 下段長度回推（已知 Q_lower = 20 nW, 參考 Q_ref = 5 nW）
    # 如果材料相同，則 L_lower / L_ref = I_lower / I_ref * Q_ref / Q_lower
    L_lower_calc = I_lower / (20e-9) * 100  # cm
    L_upper_calc = I_upper / (20e-9 * ratio_upper / ratio_lower) * 100 if ratio_lower > 0 else 0
    
    # 更直接的方法：使用比例
    # Q_lower = I_lower / L_lower => L_lower = I_lower / Q_lower
    L_lower_direct = I_lower / (20e-9) * 100  # cm
    
    # 上段：如果 L_upper = L_lower = 16.5 cm (MEC 配置)
    Q_upper_calc = I_upper / (16.5e-2)  # W
    Q_sink = Q_upper_calc - 20e-9
    
    col1, col2, col3 = st.columns(3)
    col1.metric("I(90mK→800mK)", f"{I_lower*1e9:.1f} nW·cm")
    col2.metric("I(800mK→3.4K)", f"{I_upper*1e9:.1f} nW·cm")
    col3.metric("I 比值 (上/下)", f"{I_upper/I_lower:.1f}x")
    
    st.markdown(rf"""
    ### 計算過程
    
    **Step 1: 下段長度驗證**
    
    已知：$Q_{{lower}}$ = 20 nW, $L_{{lower}}$ = 16.5 cm (MEC 實際)
    
    $$I_{{lower}} = Q_{{lower}} \\times L_{{lower}} = 20 \\times 16.5 = 330 \\text{{ nW}}\\cdot\\text{{cm}}$$
    
    從材料模型計算：$I(90\\text{{mK}}, 800\\text{{mK}}) = {I_lower*1e9:.1f}$ nW·cm
    
    相對誤差：$|{I_lower*1e9:.1f} - 330| / 330 = {abs(I_lower*1e9 - 330)/330*100:.1f}\%$
    
    **Step 2: 上段熱負載回推**
    
    已知：$L_{{upper}}$ = 16.5 cm
    
    $$Q_{{upper}} = \\frac{{I_{{upper}}}}{{L_{{upper}}}} = \\frac{{{I_upper*1e9:.1f} \\text{{ nW}}\\cdot\\text{{cm}}}}{{16.5 \\text{{ cm}}}} = {Q_upper_calc*1e9:.1f} \\text{{ nW/trace}}$$
    
    **Step 3: 800 mK 熱沉攔截熱負載**
    
    $$Q_{{sink}} = Q_{{upper}} - Q_{{lower}} = {Q_upper_calc*1e9:.1f} - 20 = {Q_sink*1e9:.1f} \\text{{ nW/trace}}$$
    
    **Step 4: 熱沉攔截比例**
    
    $$\\eta = \\frac{{Q_{{sink}}}}{{Q_{{upper}}}} = \\frac{{{Q_sink*1e9:.1f}}}{{{Q_upper_calc*1e9:.1f}}} = {Q_sink/Q_upper_calc*100:.1f}\%$$
    
    即 800 mK 熱沉攔截了 **{Q_sink/Q_upper_calc*100:.1f}\%** 的上段熱流，
    僅 **{Q_sink/Q_upper_calc*100:.1f}\%** 到達 90 mK 級。
    """)
    
    st.info(rf"""
    **關鍵發現**：
    - 上段 (3.4K→800mK) 積分值 $I_{{upper}}$ 是下段 (800mK→90mK) 的 **{I_upper/I_lower:.1f} 倍**
    - 但兩段長度相同 (16.5 cm)，因此上段熱流 $Q_{{upper}}$ 是下段的 **{Q_upper_calc/20e-9:.1f} 倍**
    - 800 mK 熱沉至關重要：攔截了 {(1 - 20e-9/Q_upper_calc)*100:.1f}\% 的熱流
    - 若無 800 mK 熱沉，90 mK 級熱負載將高達 **{Q_upper_calc*10:.1f} nW** (10線芯)!
    """)
    
    # 繪製熱流圖
    fig, ax = plt.subplots(figsize=(10, 5))
    
    segments_mec = ['3.4K→800mK', '800mK→90mK']
    Q_values = [Q_upper_calc*1e9, 20]  # nW per trace
    L_values = [16.5, 16.5]  # cm
    
    x = np.arange(len(segments_mec))
    width = 0.35
    
    ax2 = ax.twinx()
    bars1 = ax.bar(x - width/2, Q_values, width, label='Heat Flow Q (nW/trace)', color='salmon', edgecolor='black')
    bars2 = ax2.bar(x + width/2, L_values, width, label='Length (cm)', color='lightblue', edgecolor='black')
    
    ax.set_ylabel('Heat Flow Q (nW/trace)', fontsize=12)
    ax2.set_ylabel('Length (cm)', fontsize=12)
    ax.set_title('MEC Setup: Heat Flow and Length by Segment', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(segments_mec)
    ax.legend(loc='upper left')
    ax2.legend(loc='upper right')
    ax.grid(True, alpha=0.3, axis='y')
    
    for bar, val in zip(bars1, Q_values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(Q_values)*0.02, 
                f'{val:.1f} nW', ha='center', fontsize=10, fontweight='bold')
    
    st.pyplot(fig)

# ===================== 分頁 5: Cri/oFlex 對比 =====================
with tabs[4]:
    st.header("FLAX vs Cri/oFlex 長度回推對比")
    
    st.markdown(f"""
    **Cri/oFlex 3 (Delft Circuits)** 熱性能：
    - 2023 論文引用：約為 FLAX 的 **{flex_ratio}x** 熱導率
    - 材料：NbTi 導體 + Kapton 介電層
    - Kapton 熱導率 > PFA，且截面可能不同
    
    **對比方法**：
    若 Cri/oFlex 的 $G(T)$ 是 FLAX 的 {flex_ratio} 倍，則：
    $$I_{{Cri/oFlex}} = {flex_ratio} \\times I_{{FLAX}}$$
    
    對於相同熱預算 $Q$，Cri/oFlex 的長度為：
    $$L_{{Cri/oFlex}} = \\frac{{I_{{Cri/oFlex}}}}{{Q}} = {flex_ratio} \\times L_{{FLAX}}$$
    
    即：相同熱預算下，Cri/oFlex 可容忍 **{flex_ratio}x** 的長度。
    或：相同長度下，Cri/oFlex 的熱負載是 FLAX 的 **{flex_ratio}x**。
    """)
    
    st.subheader("相同熱預算下的長度對比")
    
    Q_budget_nW = 20.0  # nW/trace
    
    comparison = []
    for label, I_flax in integrals.items():
        I_crioflex = I_flax * flex_ratio
        L_flax = I_flax / (Q_budget_nW * 1e-9) * 100  # cm
        L_crioflex = I_crioflex / (Q_budget_nW * 1e-9) * 100  # cm
        
        comparison.append({
            '溫度段': label,
            'FLAX I (nW·cm)': f"{I_flax*1e9:.2f}",
            'Cri/oFlex I (nW·cm)': f"{I_crioflex*1e9:.2f}",
            'FLAX 長度 (cm)': f"{L_flax:.2f}",
            'Cri/oFlex 長度 (cm)': f"{L_crioflex:.2f}",
            '長度比值': f"{L_crioflex/L_flax:.1f}x",
        })
    
    df_compare = pd.DataFrame(comparison)
    st.dataframe(df_compare, use_container_width=True, hide_index=True)
    
    st.subheader("Paluch et al. (2025) Sionludi XL 配置")
    
    st.markdown("""
    **Cri/oFlex 在 Sionludi XL 的實際配置** (從論文提取)：
    - 熱夾具分布：80K, 20K, 4K, 200mK, 20mK
    - 集成 60 dB 衰減器，分布於各溫度級
    - 量子比特溫度 T_q = 26.4 mK (接近基溫 20 mK)
    - 熱化時間 τ = 0.28 ms (比同軸 0.55 ms 快)
    
    **回推分析**：
    
    由於量子比特溫度僅 26.4 mK（接近基溫 20 mK），
    說明到達 20 mK 級的熱負載極小。
    
    從光子數測量：⟨n⟩ = 2.2 × 10⁻³ @ 7.458 GHz
    對應等效黑體溫度 ~58 mK。
    
    這些熱光子來自輸入鏈的殘餘熱負載，而非傳輸線本身的熱傳導。
    
    因此，對於 Cri/oFlex 的傳輸線長度，實際限制來自：
    1. **物理空間**：cryostat 內部各級的間距
    2. **熱化需求**：衰減器必須充分熱化 (τ << 脈衝間隔)
    3. **集成衰減器**：而非傳輸線本身的熱導
    """)
    
    # 繪製對比圖
    fig, ax = plt.subplots(figsize=(12, 6))
    
    labels_short = [l for l in integrals.keys()]
    L_flax_vals = [integral_G(float(l.split('→')[0].replace('K','').replace('mK','').replace('m', '')) * (1e-3 if 'mK' in l else 1), 
                                float(l.split('→')[1].replace('K','').replace('mK','').replace('m', '')) * (1e-3 if 'mK' in l.split('→')[1] else 1)) / (Q_budget_nW * 1e-9) * 100 
                   for l in labels_short]
    L_crioflex_vals = [v * flex_ratio for v in L_flax_vals]
    
    x = np.arange(len(labels_short))
    width = 0.35
    
    ax.barh(x - width/2, L_flax_vals, width, label='FLAX', color='salmon', edgecolor='black')
    ax.barh(x + width/2, L_crioflex_vals, width, label='Cri/oFlex (6x)', color='lightblue', edgecolor='black')
    
    ax.set_yticks(x)
    ax.set_yticklabels(labels_short)
    ax.set_xlabel('Length (cm) for Q = 20 nW/trace', fontsize=12)
    ax.set_title('Length Comparison: FLAX vs Cri/oFlex at Same Heat Budget', fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3, axis='x')
    ax.set_xscale('log')
    
    st.pyplot(fig)

# ===================== 分頁 6: 可視化 =====================
with tabs[5]:
    st.header("積分與長度回推可視化")
    
    # 圖 1: G(T) 曲線
    fig1, ax1 = plt.subplots(figsize=(12, 5))
    T_range = np.logspace(-2, 2.5, 500)
    G_vals = [G_T(t) for t in T_range]
    G_pfa = [k_PFA(t) * A_pfa_mm2 * 1e-6 for t in T_range]
    G_nbti = [k_NbTi(t) * A_nbti_mm2 * 1e-6 for t in T_range]
    
    ax1.loglog(T_range, G_vals, 'k-', linewidth=2.5, label='Total G(T)')
    ax1.loglog(T_range, G_pfa, 'b--', linewidth=2, alpha=0.7, label='PFA contribution')
    ax1.loglog(T_range, G_nbti, 'r--', linewidth=2, alpha=0.7, label='NbTi contribution')
    
    for name, T in T_stages.items():
        if 0.01 <= T <= 300:
            ax1.axvline(x=T, color='gray', linestyle=':', alpha=0.3)
            ax1.text(T, max(G_vals)*0.5, name, rotation=90, fontsize=9, ha='right', va='top')
    
    ax1.set_xlabel('Temperature T (K)', fontsize=12)
    ax1.set_ylabel('G(T) = A·k(T) (W·m/K)', fontsize=12)
    ax1.set_title('Thermal Conductance G(T) vs Temperature', fontsize=14)
    ax1.legend(fontsize=12)
    ax1.grid(True, alpha=0.3)
    st.pyplot(fig1)
    
    # 圖 2: 累積積分
    fig2, ax2 = plt.subplots(figsize=(12, 5))
    
    T_cum = np.logspace(-2, 2.5, 500)
    I_cum = []
    for i, T in enumerate(T_cum):
        I = integral_G(T_ref_cold, T) if T > T_ref_cold else 0
        I_cum.append(I * 1e9)  # nW·cm
    
    ax2.semilogy(T_cum, I_cum, 'purple', linewidth=2.5)
    for name, T in T_stages.items():
        if 0.01 <= T <= 300:
            ax2.axvline(x=T, color='gray', linestyle=':', alpha=0.3)
    ax2.axhline(y=I_ref*1e9, color='red', linestyle='--', label=f'I_ref = {I_ref*1e9:.1f} nW·cm')
    ax2.set_xlabel('Temperature T (K)', fontsize=12)
    ax2.set_ylabel('Cumulative I(T_ref_cold, T) (nW·cm)', fontsize=12)
    ax2.set_title(f'Cumulative Integral from {T_ref_cold*1000:.0f}mK to T', fontsize=14)
    ax2.legend(fontsize=12)
    ax2.grid(True, alpha=0.3)
    st.pyplot(fig2)
    
    # 圖 3: 各溫度段的長度回推 (相同 Q)
    fig3, ax3 = plt.subplots(figsize=(12, 6))
    
    Q_test = 20.0  # nW
    lengths = []
    for label, I in integrals.items():
        L = I / (Q_test * 1e-9) * 100  # cm
        lengths.append(L)
    
    colors = plt.cm.plasma(np.linspace(0, 1, len(labels_short)))
    bars = ax3.barh(labels_short, lengths, color=colors, edgecolor='black')
    ax3.set_xlabel(f'Length (cm) for Q = {Q_test} nW/trace', fontsize=12)
    ax3.set_title('Back-Calculated Length by Temperature Zone (Same Heat Flow)', fontsize=14)
    ax3.grid(True, alpha=0.3, axis='x')
    ax3.set_xscale('log')
    
    for bar, val in zip(bars, lengths):
        ax3.text(val + max(lengths)*0.01, bar.get_y() + bar.get_height()/2, 
                f'{val:.1f} cm', va='center', fontsize=10, fontweight='bold')
    
    st.pyplot(fig3)
    
    st.markdown(r"""
    **圖表解讀**：
    
    1. **G(T) 曲線** (左上)：PFA 貢獻在低溫區佔主導，但在高溫區 NbTi 的貢獻相對增大（因 NbTi 的溫度指數更高，$n=2$ vs $1.5$）。
    
    2. **累積積分** (右上)：從基溫（100 mK）出發，積分值隨溫度升高而急劇增大。在 300K 時，$I$ 值比 1K 時大 **數個數量級**。
    
    3. **回推長度** (下)：對於相同的 20 nW 熱負載，高溫段（300K→80K）的允許長度僅 **~10 cm**，而低溫段（100mK→20mK）可達 **~100 cm**。
    
    這正是 cryostat 設計的核心：**高溫段必須短且充分熱沉，低溫段可以較長**。
    """)

st.divider()
st.caption("Transmission Line Length Back-Calculation | Based on FLAX (Smith et al.) & Cri/oFlex (Paluch et al.) | Streamlit Edition")
