import streamlit as st
import numpy as np
import pandas as pd

# ============================================================
# FLAX 電纜熱負載計算 Streamlit 展示
# 基於論文: IEEE TASC 2021, Smith et al.
# ============================================================

st.set_page_config(page_title="FLAX 熱負載計算", layout="wide")

st.title("🔬 Flexible Coaxial Ribbon Cable (FLAX) 熱負載推導計算")
st.markdown(
    "基於論文: *Flexible Coaxial Ribbon Cable for High-Density Superconducting Microwave Device Arrays*  "
    "(IEEE Trans. Appl. Supercond., Vol. 31, No. 1, 2021)"
)

# ============================================================
# 側邊欄 - 參數輸入
# ============================================================
st.sidebar.header("⚙️ 計算參數設定")

st.sidebar.subheader("幾何結構")
d_inner = st.sidebar.number_input("中心導體直徑 (mm)", value=0.076, min_value=0.01, max_value=1.0, step=0.001, format="%.3f")
d_pfa = st.sidebar.number_input("PFA 絕緣層直徑 (mm)", value=0.280, min_value=0.05, max_value=2.0, step=0.001, format="%.3f")
t_outer = st.sidebar.number_input("外屏蔽箔厚度 (mm)", value=0.025, min_value=0.001, max_value=0.5, step=0.001, format="%.3f")
pitch = st.sidebar.number_input("線芯間距 (mm)", value=3.56, min_value=1.0, max_value=10.0, step=0.01, format="%.2f")
n_traces = st.sidebar.number_input("線芯數量", value=10, min_value=1, max_value=50, step=1)

st.sidebar.subheader("溫度配置")
T_hot = st.sidebar.number_input("熱端溫度 T_hot (K)", value=3.4, min_value=0.1, max_value=10.0, step=0.1)
T_cold = st.sidebar.number_input("冷端溫度 T_cold (K)", value=0.09, min_value=0.01, max_value=1.0, step=0.01, format="%.2f")
T_sink = st.sidebar.number_input("中間熱沉溫度 T_sink (K)", value=0.80, min_value=0.05, max_value=2.0, step=0.05, format="%.2f")
L_total = st.sidebar.number_input("電纜總長度 (cm)", value=33.0, min_value=1.0, max_value=100.0, step=0.5)

st.sidebar.subheader("材料熱導率模型")
k_pfa_ref = st.sidebar.number_input("PFA k_ref @ 1K (W/m/K)", value=0.30, min_value=0.01, max_value=10.0, step=0.01)
pfa_exp = st.sidebar.number_input("PFA 溫度指數", value=1.5, min_value=0.5, max_value=3.0, step=0.1)
k_nbti_ref = st.sidebar.number_input("NbTi k_ref @ 1K (W/m/K)", value=0.01, min_value=0.001, max_value=1.0, step=0.001, format="%.3f")
nbti_exp = st.sidebar.number_input("NbTi 溫度指數", value=2.0, min_value=0.5, max_value=4.0, step=0.1)

st.sidebar.markdown("---")
with st.sidebar.expander("📖 說明"):
    st.markdown("""
    **公式**: 穩態一維熱傳導
    
    $$Q = \\frac{1}{L} \\int_{T_{cold}}^{T_{hot}} \\sum_i k_i(T) \\cdot A_i \\, dT$$
    
    - **PFA**: 非晶聚合物, $k(T) = k_{ref} \\cdot T^{exp}$ (聲子散射)
    - **NbTi**: 超導態, $k(T) = k_{ref} \\cdot T^{exp}$ (僅聲子貢獻)
    """)

# ============================================================
# 計算函數
# ============================================================

def k_PFA(T, k_ref, exp):
    return k_ref * (T ** exp)

def k_NbTi(T, k_ref, exp):
    return k_ref * (T ** exp)

def compute_heat_load(d_inner_mm, d_pfa_mm, t_outer_mm, pitch_mm, n_traces, 
                        T_hot, T_cold, T_sink, L_total_cm,
                        k_pfa_ref, pfa_exp, k_nbti_ref, nbti_exp):
    
    # 轉換為 SI
    d_inner = d_inner_mm * 1e-3
    d_pfa = d_pfa_mm * 1e-3
    t_outer = t_outer_mm * 1e-3
    pitch = pitch_mm * 1e-3
    L_total = L_total_cm * 1e-2
    
    # 截面積計算
    r_inner = d_inner / 2
    A_inner = np.pi * r_inner**2
    
    r_pfa = d_pfa / 2
    A_pfa = np.pi * (r_pfa**2 - r_inner**2)
    
    w_outer_total = n_traces * pitch
    A_outer_total = w_outer_total * t_outer
    A_outer_per_trace = A_outer_total / n_traces
    
    A_total_per_trace = A_inner + A_pfa + A_outer_per_trace
    
    # 溫度網格
    T = np.linspace(0.01, max(T_hot, 4.0) + 0.5, 10000)
    
    # 各材料熱導貢獻
    G_inner = k_NbTi(T, k_nbti_ref, nbti_exp) * A_inner
    G_pfa = k_PFA(T, k_pfa_ref, pfa_exp) * A_pfa
    G_outer = k_NbTi(T, k_nbti_ref, nbti_exp) * A_outer_per_trace
    G_trace = G_inner + G_pfa + G_outer
    G_total = n_traces * G_trace
    
    # 有效熱導率 (μW/cm/K)
    k_eff_trace = (G_trace / A_total_per_trace) * 1e6 * 1e-2
    k_eff_total = (G_total / (A_total_per_trace * n_traces)) * 1e6 * 1e-2
    
    # ---- 場景計算 ----
    
    # 場景 A: 單線芯, 1K -> 90mK, 30cm
    L_A = 0.30
    T_hot_A = 1.0
    mask_A = (T >= T_cold) & (T <= T_hot_A)
    Q_single_1K = np.trapezoid(G_trace[mask_A], T[mask_A]) / L_A
    Q_inner_A = np.trapezoid(G_inner[mask_A], T[mask_A]) / L_A
    Q_pfa_A = np.trapezoid(G_pfa[mask_A], T[mask_A]) / L_A
    Q_outer_A = np.trapezoid(G_outer[mask_A], T[mask_A]) / L_A
    
    # 場景 B: 單線芯, T_hot -> T_cold, 30cm
    L_B = 0.30
    mask_B = (T >= T_cold) & (T <= T_hot)
    Q_single_full = np.trapezoid(G_trace[mask_B], T[mask_B]) / L_B
    
    # 場景 C: 10線芯, T_hot -> T_cold, L_total (無熱沉)
    mask_C = (T >= T_cold) & (T <= T_hot)
    Q_total_nosink = np.trapezoid(G_total[mask_C], T[mask_C]) / L_total
    
    # 場景 D: MEC 實際 (有熱沉)
    L_half = L_total / 2
    # 上段: T_hot -> T_sink
    mask_upper = (T >= T_sink) & (T <= T_hot)
    Q_upper = np.trapezoid(G_total[mask_upper], T[mask_upper]) / L_half
    # 下段: T_sink -> T_cold
    mask_lower = (T >= T_cold) & (T <= T_sink)
    Q_lower = np.trapezoid(G_total[mask_lower], T[mask_lower]) / L_half
    
    # 場景 E: 10線芯, 1K -> 90mK, L_half (模擬)
    mask_E = (T >= T_cold) & (T <= 1.0)
    Q_10trace_1K_half = np.trapezoid(G_total[mask_E], T[mask_E]) / L_half
    
    # 商業電纜估算 (固定比例)
    ratio_cryocoax = 2.0
    ratio_keycom = 2.2
    Q_cryocoax = Q_lower * ratio_cryocoax
    Q_keycom = Q_lower * ratio_keycom
    
    return {
        'geometry': {
            'A_inner_mm2': A_inner * 1e6,
            'A_pfa_mm2': A_pfa * 1e6,
            'A_outer_per_trace_mm2': A_outer_per_trace * 1e6,
            'A_total_per_trace_mm2': A_total_per_trace * 1e6,
            'A_total_all_mm2': A_total_per_trace * n_traces * 1e6,
        },
        'T': T,
        'G_trace': G_trace,
        'G_total': G_total,
        'G_inner': G_inner,
        'G_pfa': G_pfa,
        'G_outer': G_outer,
        'k_eff_trace': k_eff_trace,
        'k_eff_total': k_eff_total,
        'results': {
            'A': {
                'desc': f'單線芯, 1K → {T_cold*1000:.0f}mK, 30cm',
                'Q_total_nW': Q_single_1K * 1e9,
                'Q_inner_nW': Q_inner_A * 1e9,
                'Q_pfa_nW': Q_pfa_A * 1e9,
                'Q_outer_nW': Q_outer_A * 1e9,
            },
            'B': {
                'desc': f'單線芯, {T_hot}K → {T_cold*1000:.0f}mK, 30cm',
                'Q_total_nW': Q_single_full * 1e9,
            },
            'C': {
                'desc': f'{n_traces}線芯, {T_hot}K → {T_cold*1000:.0f}mK, {L_total*100:.1f}cm (無熱沉)',
                'Q_total_nW': Q_total_nosink * 1e9,
                'Q_total_uW': Q_total_nosink * 1e6,
            },
            'D': {
                'desc': f'MEC 實際: {n_traces}線芯, {T_hot}K → {T_cold*1000:.0f}mK, {L_total*100:.1f}cm, {T_sink*1000:.0f}mK熱沉',
                'Q_upper_nW': Q_upper * 1e9,
                'Q_upper_uW': Q_upper * 1e6,
                'Q_lower_nW': Q_lower * 1e9,
                'Q_lower_uW': Q_lower * 1e6,
                'improvement': Q_total_nosink / Q_lower if Q_lower > 0 else 0,
            },
            'E': {
                'desc': f'{n_traces}線芯, 1K → {T_cold*1000:.0f}mK, {L_half*100:.1f}cm (下半段)',
                'Q_total_nW': Q_10trace_1K_half * 1e9,
            },
            'compare': {
                'FLAX_nW': Q_lower * 1e9,
                'CryoCoax_nW': Q_cryocoax * 1e9,
                'KEYCOM_nW': Q_keycom * 1e9,
                'ratio_cryocoax': ratio_cryocoax,
                'ratio_keycom': ratio_keycom,
            }
        }
    }

# ============================================================
# 執行計算
# ============================================================
results = compute_heat_load(
    d_inner, d_pfa, t_outer, pitch, n_traces,
    T_hot, T_cold, T_sink, L_total,
    k_pfa_ref, pfa_exp, k_nbti_ref, nbti_exp
)

geo = results['geometry']
res = results['results']
T = results['T']

# ============================================================
# 分頁導航
# ============================================================
tabs = st.tabs([
    "📐 幾何結構", 
    "📊 材料熱導率", 
    "🔥 熱負載計算", 
    "🏭 MEC 實際配置", 
    "⚖️ 商業比較",
    "📈 圖表總覽"
])

# ===================== 分頁 1: 幾何結構 =====================
with tabs[0]:
    st.header("電纜幾何結構")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("截面尺寸")
        df_geo = pd.DataFrame({
            '結構': ['中心導體 (NbTi)', '絕緣層 (PFA)', '外屏蔽 (Nb47Ti)', '單線芯合計', f'{n_traces}線芯總計'],
            '材料': ['NbTi', 'PFA', 'Nb47Ti', '-', '-'],
            '截面積 (mm²)': [
                f"{geo['A_inner_mm2']:.4f}",
                f"{geo['A_pfa_mm2']:.4f}",
                f"{geo['A_outer_per_trace_mm2']:.4f}",
                f"{geo['A_total_per_trace_mm2']:.4f}",
                f"{geo['A_total_all_mm2']:.4f}",
            ],
            '佔單線芯比例': [
                f"{geo['A_inner_mm2']/geo['A_total_per_trace_mm2']*100:.1f}%",
                f"{geo['A_pfa_mm2']/geo['A_total_per_trace_mm2']*100:.1f}%",
                f"{geo['A_outer_per_trace_mm2']/geo['A_total_per_trace_mm2']*100:.1f}%",
                "100%",
                "-",
            ]
        })
        st.dataframe(df_geo, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("示意圖")
        st.markdown(f"""
        ```
        外屏蔽 Nb47Ti 箔 (厚 {t_outer} mm)
        ┌─────────────────────────────────────┐
        │  ○━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━○  │  ← PFA 絕緣層 Ø {d_pfa} mm
        │  ○       NbTi 中心導體 Ø {d_inner} mm      ○  │
        │  ○━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━○  │
        └─────────────────────────────────────┘
             ↑ 微點焊 (間距 < λ/16 ≈ 2 mm @ 8 GHz)
        
        10 線芯排佈 (間距 {pitch} mm):
        
        ○──{pitch}──○──{pitch}──○──{pitch}──○──{pitch}──○──{pitch}──○──{pitch}──○──{pitch}──○──{pitch}──○──{pitch}──○
        
        ═════════════════════════════════════════════════════════════
        共享外導體 Nb47Ti 箔 (寬 ~{pitch * n_traces:.1f} mm)
        ```
        """)
    
    st.subheader("關鍵設計參數")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("線芯數量", f"{n_traces}")
    c2.metric("線芯間距", f"{pitch} mm")
    c3.metric("電纜總長度", f"{L_total} cm")
    c4.metric("單線芯總截面", f"{geo['A_total_per_trace_mm2']:.3f} mm²")

# ===================== 分頁 2: 材料熱導率 =====================
with tabs[1]:
    st.header("材料熱導率模型")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("PFA (絕緣層)")
        st.markdown(f"""
        **公式**: $k(T) = {k_pfa_ref} \\times T^{{{pfa_exp}}}$ (W/m/K)
        
        | 溫度 | 熱導率 (W/m/K) | 熱導率 (mW/m/K) |
        |:----:|:-------------:|:---------------:|
        | 0.1 K | {k_PFA(0.1, k_pfa_ref, pfa_exp):.4f} | {k_PFA(0.1, k_pfa_ref, pfa_exp)*1000:.2f} |
        | 0.5 K | {k_PFA(0.5, k_pfa_ref, pfa_exp):.4f} | {k_PFA(0.5, k_pfa_ref, pfa_exp)*1000:.2f} |
        | 1.0 K | {k_PFA(1.0, k_pfa_ref, pfa_exp):.4f} | {k_PFA(1.0, k_pfa_ref, pfa_exp)*1000:.2f} |
        | 2.0 K | {k_PFA(2.0, k_pfa_ref, pfa_exp):.4f} | {k_PFA(2.0, k_pfa_ref, pfa_exp)*1000:.2f} |
        | 3.0 K | {k_PFA(3.0, k_pfa_ref, pfa_exp):.4f} | {k_PFA(3.0, k_pfa_ref, pfa_exp)*1000:.2f} |
        | 4.0 K | {k_PFA(4.0, k_pfa_ref, pfa_exp):.4f} | {k_PFA(4.0, k_pfa_ref, pfa_exp)*1000:.2f} |
        """)
        st.info("非晶聚合物，聲子散射主導，低溫下熱導率隨溫度升高而增大。佔單線芯截面 ~38%，是主要熱傳導路徑。")
    
    with col2:
        st.subheader("Nb47Ti (超導態)")
        st.markdown(f"""
        **公式**: $k(T) = {k_nbti_ref} \\times T^{{{nbti_exp}}}$ (W/m/K)
        
        | 溫度 | 熱導率 (W/m/K) | 熱導率 (mW/m/K) |
        |:----:|:-------------:|:---------------:|
        | 0.1 K | {k_NbTi(0.1, k_nbti_ref, nbti_exp):.5f} | {k_NbTi(0.1, k_nbti_ref, nbti_exp)*1000:.3f} |
        | 0.5 K | {k_NbTi(0.5, k_nbti_ref, nbti_exp):.5f} | {k_NbTi(0.5, k_nbti_ref, nbti_exp)*1000:.3f} |
        | 1.0 K | {k_NbTi(1.0, k_nbti_ref, nbti_exp):.5f} | {k_NbTi(1.0, k_nbti_ref, nbti_exp)*1000:.3f} |
        | 2.0 K | {k_NbTi(2.0, k_nbti_ref, nbti_exp):.5f} | {k_NbTi(2.0, k_nbti_ref, nbti_exp)*1000:.3f} |
        | 3.0 K | {k_NbTi(3.0, k_nbti_ref, nbti_exp):.5f} | {k_NbTi(3.0, k_nbti_ref, nbti_exp)*1000:.3f} |
        | 4.0 K | {k_NbTi(4.0, k_nbti_ref, nbti_exp):.5f} | {k_NbTi(4.0, k_nbti_ref, nbti_exp)*1000:.3f} |
        """)
        st.info("超導態下電子熱導被能隙抑制，僅餘聲子貢獻。熱導率極低 (~3個數量級低於正常態金屬如銅)。")
    
    st.subheader("有效熱導率 $G(T) = \\sum k_i(T) \\cdot A_i$ (單線芯)")
    
    # 計算特定溫度點的 G(T)
    temps = [0.1, 0.2, 0.5, 0.8, 1.0, 2.0, 3.0, 4.0]
    g_data = []
    for t in temps:
        g_inner = k_NbTi(t, k_nbti_ref, nbti_exp) * geo['A_inner_mm2'] * 1e-6
        g_pfa = k_PFA(t, k_pfa_ref, pfa_exp) * geo['A_pfa_mm2'] * 1e-6
        g_outer = k_NbTi(t, k_nbti_ref, nbti_exp) * geo['A_outer_per_trace_mm2'] * 1e-6
        g_total = g_inner + g_pfa + g_outer
        g_data.append({
            '溫度 (K)': t,
            'NbTi 內導體 (W·m/K)': g_inner,
            'PFA 絕緣層 (W·m/K)': g_pfa,
            'NbTi 外屏蔽 (W·m/K)': g_outer,
            '單線芯合計 (W·m/K)': g_total,
            '10線芯合計 (W·m/K)': g_total * n_traces,
        })
    
    df_g = pd.DataFrame(g_data)
    st.dataframe(df_g, use_container_width=True, hide_index=True)

# ===================== 分頁 3: 熱負載計算 =====================
with tabs[2]:
    st.header("熱負載計算結果")
    
    st.markdown("""
    **計算公式**:
    
    $$Q = \\frac{1}{L} \\int_{T_{cold}}^{T_{hot}} G(T) \\, dT = \\frac{1}{L} \\int_{T_{cold}}^{T_{hot}} \\sum_i k_i(T) \\cdot A_i \\, dT$$
    """)
    
    st.subheader("各場景計算結果")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 場景 A: 單線芯基準")
        st.markdown(f"""
        ```
        熱端: 1 K                    冷端: {T_cold*1000:.0f} mK
        ←──────── L = 30 cm ─────────→
        
        總熱負載: {res['A']['Q_total_nW']:.2f} nW
        (論文報告: 20 nW)
        ```
        """)
        
        df_A = pd.DataFrame({
            '材料': ['NbTi 中心導體', 'PFA 絕緣層', 'Nb47Ti 外屏蔽', '合計'],
            '熱負載 (nW)': [
                f"{res['A']['Q_inner_nW']:.3f}",
                f"{res['A']['Q_pfa_nW']:.3f}",
                f"{res['A']['Q_outer_nW']:.3f}",
                f"{res['A']['Q_total_nW']:.2f}",
            ],
            '佔比': [
                f"{res['A']['Q_inner_nW']/res['A']['Q_total_nW']*100:.1f}%",
                f"{res['A']['Q_pfa_nW']/res['A']['Q_total_nW']*100:.1f}%",
                f"{res['A']['Q_outer_nW']/res['A']['Q_total_nW']*100:.1f}%",
                "100%",
            ]
        })
        st.dataframe(df_A, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("#### 場景 B: 單線芯全溫度範圍")
        st.markdown(f"""
        ```
        熱端: {T_hot} K               冷端: {T_cold*1000:.0f} mK
        ←──────── L = 30 cm ─────────→
        
        總熱負載: {res['B']['Q_total_nW']:.2f} nW
        ```
        """)
        st.metric("相對於場景 A 的倍數", f"{res['B']['Q_total_nW'] / res['A']['Q_total_nW']:.1f}x", 
                  f"溫度範圍擴大 {T_hot/1.0:.1f}K/1K")
    
    st.divider()
    
    col3, col4 = st.columns(2)
    with col3:
        st.markdown(f"#### 場景 C: {n_traces}線芯 (無熱沉)")
        st.markdown(f"""
        ```
        熱端: {T_hot} K               冷端: {T_cold*1000:.0f} mK
        ←──────── L = {L_total} cm ─────────→
        
        總熱負載: {res['C']['Q_total_nW']:.2f} nW = {res['C']['Q_total_uW']:.3f} μW
        ```
        """)
        st.warning(f"無熱沉時，{n_traces}線芯熱負載高達 {res['C']['Q_total_uW']:.2f} μW，對 90mK 級製冷機負擔極大！")
    
    with col4:
        st.markdown(f"#### 場景 E: {n_traces}線芯, 1K → {T_cold*1000:.0f}mK, 半長")
        st.markdown(f"""
        ```
        熱端: 1 K                    冷端: {T_cold*1000:.0f} mK
        ←──────── L = {L_total/2:.1f} cm ─────────→
        
        總熱負載: {res['E']['Q_total_nW']:.2f} nW
        ```
        """)

# ===================== 分頁 4: MEC 實際配置 =====================
with tabs[3]:
    st.header("MEC 實際配置 (含 800mK 中間熱沉)")
    
    st.markdown(f"""
    ```
    3.4 K 級                      800 mK 熱沉                    90 mK 冷級
    ─────┬──────────────────────────┬──────────────────────────┬─────
         │                          │                          │
         │  ←─── {L_total/2:.1f} cm ───→   │  ←─── {L_total/2:.1f} cm ───→   │
         │        (上段)           │        (下段)           │
         │                          │                          │
         ▼                          ▼                          ▼
    產生熱流:                    攔截熱流:                   到達熱流:
    {res['D']['Q_upper_nW']:.2f} nW              {res['D']['Q_upper_nW']-res['D']['Q_lower_nW']:.2f} nW (被吸收)            {res['D']['Q_lower_nW']:.2f} nW
    ({res['D']['Q_upper_uW']:.3f} μW)              幾乎全部被 800mK 熱沉吸收          到達 90mK 冷級
    3.4K → 800mK                (上段熱流 - 下段熱流)          800mK → 90mK
    ```
    """)
    
    st.subheader("熱沉效果分析")
    col1, col2, col3 = st.columns(3)
    col1.metric("無熱沉總熱負載", f"{res['C']['Q_total_nW']:.1f} nW", f"{res['C']['Q_total_uW']:.3f} μW")
    col2.metric("有熱沉 90mK 負載", f"{res['D']['Q_lower_nW']:.1f} nW", f"{res['D']['Q_lower_uW']:.3f} μW")
    col3.metric("熱沉降低倍數", f"{res['D']['improvement']:.1f}x", "大幅下降！")
    
    st.markdown("""
    **關鍵結論**:
    - 800 mK 中間熱沉是降低 90 mK 冷級熱負載的**關鍵設計**
    - 上段產生的熱流 (3.4K → 800mK) 幾乎全部被 800mK 級的製冷機吸收
    - 僅有下段 (800mK → 90mK) 的熱負載到達 90mK 冷級
    - 這使得 90mK 級實際負擔從 ~4.8 μW 降至 ~0.25 μW，降幅達 **19 倍**
    """)
    
    st.subheader("論文報告值對照")
    st.markdown("""
    | 參數 | 計算值 | 論文報告值 | 誤差 |
    |:-----|:------:|:----------:|:----:|
    | 單線芯 1K → 90mK, 30cm | ~24 nW | 20 nW | ~20% |
    | 10線芯 90mK 級總負載 | ~246 nW | ~200 nW | ~23% |
    """)
    st.info("計算誤差來自熱導率文獻值的近似擬合，以及製造批次間的材料差異。")

# ===================== 分頁 5: 商業比較 =====================
with tabs[4]:
    st.header("與商業電纜熱負載比較")
    
    cmp = res['compare']
    
    st.markdown(f"""
    ### 90 mK 冷級熱負載比較 ({n_traces}線芯, {T_hot}K → {T_cold*1000:.0f}mK, 含熱沉)
    
    ```
    FLAX (本論文)              {cmp['FLAX_nW']:>8.1f} nW  ████████████████
    ────────────────────────────────────────────────────────────
    CryoCoax (5139-P1NN-611-100P)  {cmp['CryoCoax_nW']:>8.1f} nW  ████████████████████████████████████████  ({cmp['ratio_cryocoax']:.1f}x)
    ────────────────────────────────────────────────────────────
    KEYCOM (NbTiNbTi034)       {cmp['KEYCOM_nW']:>8.1f} nW  ██████████████████████████████████████████████  ({cmp['ratio_keycom']:.1f}x)
    ────────────────────────────────────────────────────────────
    NikaFlex (微帶線, 同實驗室)  ~{cmp['FLAX_nW']:>7.1f} nW  ████████████████  (約 1x)
    ```
    """)
    
    st.subheader("FLAX 低熱負載的設計原因")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**1. 小截面積**")
        st.markdown(f"""
        - 單線芯總截面: {geo['A_total_per_trace_mm2']:.3f} mm²
        - PFA 介質截面: {geo['A_pfa_mm2']:.4f} mm²
        - 商業同軸電纜介質截面通常為此 2-3 倍
        """)
    
    with col2:
        st.markdown("**2. 超導態金屬**")
        st.markdown(f"""
        - NbTi 在超導態熱導率極低
        - 1K 時: {k_nbti_ref} W/m/K (聲子主導)
        - 正常態金屬 (如銅): >1000 W/m/K
        - 金屬部分幾乎不傳熱
        """)
    
    with col3:
        st.markdown("**3. 材料選擇**")
        st.markdown(f"""
        - PFA 熱導率 < PTFE (商用電纜常用)
        - 非晶聚合物結構降低聲子平均自由程
        - 0.1K 時: {k_PFA(0.1, k_pfa_ref, pfa_exp):.4f} W/m/K
        """)
    
    st.subheader("取捨分析")
    st.markdown("""
    | 特性 | FLAX | 商用同軸 (CryoCoax/KEYCOM) |
    |:-----|:----:|:--------------------------:|
    | 90mK 熱負載 | ~246 nW | ~500-540 nW |
    | 8 GHz 傳輸損耗 | ~1 dB | ~0.5 dB |
    | 串擾 | -60 dB | -30 dB (估計) |
    | 最小彎曲半徑 | ~2 mm | 較大 (半剛性) |
    | 線芯密度 | 10線/35.6mm | 單線 |
    | 柔性 | ✅ 高 | ⚠️ 半剛性 |
    
    **FLAX 的優勢**: 熱負載減半 + 串擾低 30 dB + 高密度柔性互連
    **代價**: 傳輸損耗略高 (1 dB vs 0.5 dB)，主要因製造缺陷導致的阻抗不匹配
    """)

# ===================== 分頁 6: 圖表總覽 =====================
with tabs[5]:
    st.header("圖表總覽")
    
    import matplotlib.pyplot as plt
    
    T_plot = T[(T >= 0.05) & (T <= 4.5)]
    
    # 圖 1: 材料熱導率
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    ax1.loglog(T_plot, k_PFA(T_plot, k_pfa_ref, pfa_exp), 'b-', linewidth=2, label=f'PFA: $k = {k_pfa_ref} T^{{{pfa_exp}}}$')
    ax1.loglog(T_plot, k_NbTi(T_plot, k_nbti_ref, nbti_exp), 'r-', linewidth=2, label=f'NbTi: $k = {k_nbti_ref} T^{{{nbti_exp}}}$')
    ax1.axvline(x=1.0, color='gray', linestyle='--', alpha=0.5, label='1K 參考')
    ax1.axvline(x=T_cold, color='green', linestyle='--', alpha=0.5, label=f'{T_cold*1000:.0f}mK 冷端')
    ax1.set_xlabel('Temperature T (K)', fontsize=12)
    ax1.set_ylabel('Thermal Conductivity k (W/m/K)', fontsize=12)
    ax1.set_title('Material Thermal Conductivity vs Temperature', fontsize=14)
    ax1.legend()
    ax1.grid(True, which='both', alpha=0.3)
    st.pyplot(fig1)
    
    # 圖 2: 熱導 G(T) - 各材料貢獻
    mask_plot = (T >= 0.05) & (T <= 4.5)
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    ax2.semilogy(T[mask_plot], results['G_inner'][mask_plot], 'r-', linewidth=2, label='NbTi Inner Conductor')
    ax2.semilogy(T[mask_plot], results['G_pfa'][mask_plot], 'b-', linewidth=2, label='PFA Dielectric')
    ax2.semilogy(T[mask_plot], results['G_outer'][mask_plot], 'g-', linewidth=2, label='NbTi Outer Shield')
    ax2.semilogy(T[mask_plot], results['G_trace'][mask_plot], 'k--', linewidth=2, label='Single Trace Total')
    ax2.axvline(x=1.0, color='gray', linestyle='--', alpha=0.5)
    ax2.axvline(x=T_cold, color='green', linestyle='--', alpha=0.5)
    ax2.set_xlabel('Temperature T (K)', fontsize=12)
    ax2.set_ylabel('Thermal Conductance G(T) (W·m/K)', fontsize=12)
    ax2.set_title('Thermal Conductance per Trace vs Temperature', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    st.pyplot(fig2)
    
    # 圖 3: 10線芯總熱導 vs 溫度
    fig3, ax3 = plt.subplots(figsize=(10, 5))
    ax3.semilogy(T[mask_plot], results['G_total'][mask_plot], 'purple', linewidth=2.5, label=f'{n_traces} Traces Total')
    ax3.axvline(x=1.0, color='gray', linestyle='--', alpha=0.5, label='1K')
    ax3.axvline(x=T_sink, color='orange', linestyle='--', alpha=0.7, label=f'{T_sink*1000:.0f}mK Sink')
    ax3.axvline(x=T_cold, color='green', linestyle='--', alpha=0.5, label=f'{T_cold*1000:.0f}mK Cold')
    ax3.axvline(x=T_hot, color='red', linestyle='--', alpha=0.5, label=f'{T_hot}K Hot')
    ax3.fill_between(T[mask_plot], 1e-20, results['G_total'][mask_plot], 
                      where=(T[mask_plot] >= T_cold) & (T[mask_plot] <= T_hot), 
                      alpha=0.2, color='purple', label='Integration Range')
    ax3.set_xlabel('Temperature T (K)', fontsize=12)
    ax3.set_ylabel('Total Thermal Conductance G(T) (W·m/K)', fontsize=12)
    ax3.set_title(f'Total Thermal Conductance ({n_traces} Traces) vs Temperature', fontsize=14)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    st.pyplot(fig3)
    
    # 圖 4: 累積熱負載 (積分曲線)
    fig4, ax4 = plt.subplots(figsize=(10, 5))
    T_int = T[mask_plot]
    G_cum = np.cumsum(results['G_total'][mask_plot]) * (T_int[1] - T_int[0])
    ax4.plot(T_int, G_cum * 1e9 / (L_total * 1e-2), 'purple', linewidth=2.5)
    ax4.axvline(x=T_sink, color='orange', linestyle='--', alpha=0.7, label=f'{T_sink*1000:.0f}mK Sink (split point)')
    ax4.axvline(x=T_cold, color='green', linestyle='--', alpha=0.5, label=f'{T_cold*1000:.0f}mK Cold')
    ax4.axvline(x=T_hot, color='red', linestyle='--', alpha=0.5, label=f'{T_hot}K Hot')
    ax4.set_xlabel('Temperature T (K)', fontsize=12)
    ax4.set_ylabel('Cumulative Heat Load at 90mK (nW)', fontsize=12)
    ax4.set_title('Cumulative Heat Load (from T_cold to T)', fontsize=14)
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    st.pyplot(fig4)
    
    # 圖 5: 比較柱狀圖
    fig5, ax5 = plt.subplots(figsize=(10, 5))
    labels = ['FLAX\n(with sink)', 'FLAX\n(no sink)', 'CryoCoax\n(estimated)', 'KEYCOM\n(estimated)']
    values = [cmp['FLAX_nW'], res['C']['Q_total_nW'], cmp['CryoCoax_nW'], cmp['KEYCOM_nW']]
    colors = ['green', 'orange', 'red', 'darkred']
    bars = ax5.bar(labels, values, color=colors, alpha=0.7, edgecolor='black')
    ax5.set_ylabel('Heat Load at 90mK Stage (nW)', fontsize=12)
    ax5.set_title('Heat Load Comparison (10 traces, 3.4K→90mK, 33cm)', fontsize=14)
    ax5.set_yscale('log')
    for bar, val in zip(bars, values):
        ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height()*1.15, 
                f'{val:.1f} nW', ha='center', va='bottom', fontsize=11, fontweight='bold')
    ax5.grid(True, alpha=0.3, axis='y')
    st.pyplot(fig5)

# ============================================================
# 底部: 計算過程說明
# ============================================================
st.divider()
with st.expander("📐 詳細計算過程展開"):
    st.markdown("""
    ### 計算步驟
    
    **Step 1: 幾何截面積計算**
    ```
    中心導體: A_inner = π × (d_inner/2)² = π × ({d_inner/2:.4f} mm)² = {geo['A_inner_mm2']:.4f} mm²
    絕緣層:   A_pfa = π × [(d_pfa/2)² - (d_inner/2)²] = {geo['A_pfa_mm2']:.4f} mm²
    外屏蔽:   A_outer = pitch × t_outer = {pitch} × {t_outer} = {geo['A_outer_per_trace_mm2']:.4f} mm² (每線芯)
    ```
    
    **Step 2: 材料熱導率模型**
    ```
    PFA:   k(T) = {k_pfa_ref} × T^{pfa_exp}  (W/m/K)
    NbTi:  k(T) = {k_nbti_ref} × T^{nbti_exp}  (W/m/K)
    ```
    
    **Step 3: 單線芯熱導 G(T)**
    ```
    G_trace(T) = k_NbTi(T) × A_inner + k_PFA(T) × A_pfa + k_NbTi(T) × A_outer
    G_total(T) = n_traces × G_trace(T) = {n_traces} × G_trace(T)
    ```
    
    **Step 4: 熱負載積分**
    ```
    Q = (1/L) × ∫_{T_cold}^{T_hot} G_total(T) dT
    
    使用數值梯形積分 (np.trapezoid) 在 10000 點網格上計算
    ```
    
    **Step 5: 熱沉分段**
    ```
    上段 (3.4K → 800mK, L = {L_total/2:.1f} cm): Q_upper = (1/L_half) × ∫_{0.8}^{3.4} G_total(T) dT
    下段 (800mK → 90mK, L = {L_total/2:.1f} cm): Q_lower = (1/L_half) × ∫_{0.09}^{0.8} G_total(T) dT
    
    90mK 級實際負載 = Q_lower
    ```
    """)
    
    st.markdown("### 積分驗證 (手動檢查點)")
    # 驗證 1K 附近的 G(T)
    t_check = 1.0
    g_check = k_NbTi(t_check, k_nbti_ref, nbti_exp) * geo['A_inner_mm2']*1e-6 + \
              k_PFA(t_check, k_pfa_ref, pfa_exp) * geo['A_pfa_mm2']*1e-6 + \
              k_NbTi(t_check, k_nbti_ref, nbti_exp) * geo['A_outer_per_trace_mm2']*1e-6
    g_total_check = g_check * n_traces
    
    st.markdown(f"""
    | 檢查項 | 數值 |
    |:-------|-----:|
    | T = 1.0 K 時單線芯 G(T) | {g_check:.3e} W·m/K |
    | T = 1.0 K 時 {n_traces}線芯 G(T) | {g_total_check:.3e} W·m/K |
    | PFA 在 1K 的 k | {k_PFA(1.0, k_pfa_ref, pfa_exp):.3f} W/m/K |
    | NbTi 在 1K 的 k | {k_NbTi(1.0, k_nbti_ref, nbti_exp):.3f} W/m/K |
    """)

st.divider()
st.caption("FLAX Heat Load Calculator | Based on Smith et al. IEEE TASC 2021 | Streamlit Edition")
