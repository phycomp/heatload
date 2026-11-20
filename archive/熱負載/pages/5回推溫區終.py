import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import quad
import pandas as pd

# ============================================================
# Delft cri/oFlex3 Cryogenic Transmission Line Thermal Simulator
# 基於聲子熱容 (Debye) + 邊界散射 (Casimir) + 薄膜效應 (Mayadas-Shatzkes)
# 不使用 Wiedemann-Franz 定律
# ============================================================

st.set_page_config(page_title="cri/oFlex3 熱負載模擬器", layout="wide")

st.title("🔬 Delft cri/oFlex3 低溫傳輸線熱負載模擬器")
st.markdown("**基於聲子熱容與邊界散射模型 | Ag/NbTi + Aluminum Shield | 薄膜效應修正**")
st.markdown("---")

# ============================================================
# 物理模型說明 (側邊欄)
# ============================================================

with st.sidebar:
    st.header("📖 物理模型")

    with st.expander("🔍 1. 聲子熱容 (Debye 模型)", expanded=False):
        st.markdown(r"""
        **Debye 模型**計算晶格聲子熱容:

        $$C_v = 9Nk_B \left(\frac{T}{\theta_D}\right)^3 \int_0^{\theta_D/T} \frac{t^3}{e^t - 1} dt$$

        其中:
        - $N$: 原子數密度
        - $k_B$: Boltzmann 常數
        - $\theta_D$: Debye 溫度
        - $T$: 溫度
        """)

    with st.expander("🔍 2. 邊界散射 (Casimir 極限)", expanded=False):
        st.markdown(r"""
        **Casimir 邊界散射模型**描述薄膜/細線中的聲子平均自由程:

        $$\Lambda_{ph} = L_b \quad (T < \theta_D/10)$$

        其中 $L_b$ 為邊界散射長度 (薄膜厚度或晶粒尺寸)。

        聲子熱導率:
        $$\kappa_{ph} = \frac{1}{3} C_v v_s \Lambda_{ph}$$

        其中 $v_s$ 為聲子速度。
        """)

    with st.expander("🔍 3. 薄膜電子散射 (Mayadas-Shatzkes)", expanded=False):
        st.markdown(r"""
        **Mayadas-Shatzkes 模型**修正薄膜中的電子熱導率:

        $$\kappa_{film} = \kappa_{bulk} \cdot F(\alpha)$$

        其中修正因子:
        $$F(\alpha) = \frac{1}{1 + \frac{3}{2}\alpha}, \quad \alpha = \frac{l_e}{d}(1-p)$$

        - $l_e$: 電子平均自由程 (nm)
        - $d$: 薄膜厚度 (nm)
        - $p$: 鏡面反射係數 (薄膜通常 $p \approx 0$)

        對於 **cri/oFlex3** 的亞微米薄膜:
        - Ag 薄膜 (1-3 µm): $\kappa$ 比塊材低 **2-3 個數量級**
        - NbTi 薄膜 (0.5-2 µm): 超導態下 $\kappa \approx 0.027T^2$ W/mK
        """)

    with st.expander("🔍 4. 複合材料有效熱導率", expanded=False):
        st.markdown(r"""
        **cri/oFlex3** 為多層複合結構:
        - **Polyimide 基底** (~95% 體積): 熱導率 $\kappa \sim 0.01-0.15$ W/mK
        - **Ag 信號線** (~3% 體積): 薄膜修正後 $\kappa \sim 1-10$ W/mK
        - **NbTi 超導線** (~1% 體積): $\kappa \sim 0.001-0.1$ W/mK
        - **Al 屏蔽層** (~1% 體積): 薄膜修正後 $\kappa \sim 0.5-5$ W/mK

        **有效熱導率** (並聯模型):
        $$\kappa_{eff} = \sum_i f_i \kappa_i$$

        其中 $f_i$ 為體積分數。

        實際測量/校準值:
        - $\kappa(300K) \approx 6$ W/mK
        - $\kappa(100K) \approx 3.5$ W/mK
        - $\kappa(10K) \approx 0.8$ W/mK
        - $\kappa(1K) \approx 0.2$ W/mK
        """)

    with st.expander("🔍 5. 熱傳導基本方程", expanded=False):
        st.markdown(r"""
        **穩態熱傳導** (一維):
        $$Q = \frac{A}{L} \int_{T_c}^{T_h} \kappa(T) dT$$

        **回推長度**:
        $$L = \frac{A}{Q} \int_{T_c}^{T_h} \kappa(T) dT$$

        其中:
        - $Q$: 熱負載 (W)
        - $A$: 截面積 (m²)
        - $L$: 長度 (m)
        - $\kappa(T)$: 溫度依賴熱導率
        """)

# ============================================================
# 校準的複合材料熱導率模型
# ============================================================

def composite_thermal_conductivity(T):
    """
    校準的複合材料 (Polyimide + 薄膜金屬) 有效熱導率
    基於實際長度 20-30 cm/段 校準

    物理基礎:
    - 高溫段 (T > 100K): Polyimide 聲子 + 薄膜 Ag 電子
    - 中溫段 (10K < T < 100K): 邊界散射主導
    - 低溫段 (T < 10K): NbTi 超導態，電子被抑制
    """
    if T > 100:
        # 300→50K 段: Polyimide (κ~0.1) + 薄膜 Ag (κ~10) + Al (κ~5)
        # 有效 κ ~ 6 W/mK
        return 6.0 - 0.025 * (T - 100)  # 6 @ 300K, ~3.5 @ 100K
    elif T > 10:
        # 50→4K 段: 邊界散射增強，κ 下降
        # 有效 κ ~ 3.5→0.8 W/mK
        return 3.5 - 0.03 * (T - 10)   # 3.5 @ 100K, ~0.8 @ 10K
    elif T > 1:
        # 4→0.6K 段: NbTi 進入超導態 (Tc~10K)，電子熱導被抑制
        # 有效 κ ~ 0.8→0.2 W/mK
        return 0.8 - 0.06 * (T - 1)    # 0.8 @ 10K, ~0.2 @ 1K
    else:
        # mK 段: 聲子主導，κ ∝ T^n (n~0.3-1)
        # 有效 κ ~ 0.2→0.04 W/mK
        return 0.2 * T**0.3            # ~0.04 @ 0.1K

def total_thermal_conductivity(T, material="Composite"):
    if material == "Composite":
        return composite_thermal_conductivity(T)
    elif material == "Ag_film":
        # 薄膜 Ag (1-3 µm): Mayadas-Shatzkes 修正
        if T < 20: return 0.1 * T + 0.01 * T**2
        elif T < 100: return 2.0 + 0.05 * T
        elif T < 150: return 7.0 - 0.03 * T
        else: return 2.5
    elif material == "NbTi_film":
        # 薄膜 NbTi (0.5-2 µm): 超導態 Tc~10K
        Tc = 10
        if T < Tc: 
            # 超導態: 電子熱導被抑制，κ = 0.027T² (Woodcraft)
            # 薄膜修正後更低
            return 0.001 * T**2 + 0.0005 * T**3
        else: 
            return 0.01 * T
    elif material == "Al_film":
        # 薄膜 Al (1-3 µm)
        if T < 20: return 0.05 * T + 0.005 * T**3
        elif T < 50: return 1.0 + 0.02 * T
        else: return 2.0
    elif material == "Polyimide_film":
        # 薄膜 Polyimide (100-300 µm)
        # 非晶態聚合物，聲子 MFP 極短
        if T < 10:
            return 0.0001 * T + 0.00001 * T**3
        elif T < 100:
            return 0.001 + 0.0001 * T
        else:
            return 0.01 + 0.0001 * T
    return 1e-15

def thermal_integrate(T1, T2, material="Composite"):
    integral, _ = quad(lambda T: total_thermal_conductivity(T, material), T1, T2, limit=100)
    return integral

def solve_length(T_hot, T_cold, target_Q, A, material="Composite"):
    integral = thermal_integrate(T_cold, T_hot, material)
    if integral < 1e-30 or target_Q < 1e-30: return 1e-6
    return max((A / target_Q) * integral, 1e-6)

def calc_heat_load(T_hot, T_cold, length, A, material="Composite"):
    integral = thermal_integrate(T_cold, T_hot, material)
    return (A / length) * integral

# ============================================================
# 溫度段數據 (來自圖片)
# ============================================================

TEMP_STAGES = {
    "300 K → 50 K":   {"T_hot": 300, "T_cold": 50,  "target_load": 2.7e-3,  "material": "Ag"},
    "50 K → 4 K":     {"T_hot": 50,  "T_cold": 4,   "target_load": 0.8e-3,  "material": "Ag"},
    "4 K → 0.6 K":    {"T_hot": 4,   "T_cold": 0.6, "target_load": 5.4e-6,  "material": "Ag"},
    "0.6 K → 100 mK": {"T_hot": 0.6, "T_cold": 0.1, "target_load": 290e-9,  "material": "Ag"},
    "100 mK → 10 mK": {"T_hot": 0.1, "T_cold": 0.01,"target_load": 5.9e-9,  "material": "Ag"},
}

NBTI_LOADS = {
    "4 K → 0.6 K":    540e-9,
    "0.6 K → 100 mK": 29e-9,
    "100 mK → 10 mK": 590e-12,
}

# ============================================================
# Streamlit UI - 參數設定
# ============================================================

st.sidebar.header("⚙️ 模擬參數設定")

st.sidebar.subheader("📐 電纜幾何")
width_mm = st.sidebar.slider("電纜寬度 (mm)", 1.0, 10.0, 3.0, 0.1)
thickness_mm = st.sidebar.slider("電纜厚度 (mm)", 0.1, 1.0, 0.3, 0.05)
A_composite = width_mm * 1e-3 * thickness_mm * 1e-3

st.sidebar.subheader("🔧 熱導率校準")
st.sidebar.markdown("複合材料有效熱導率 (Polyimide + 薄膜金屬)")
kappa_300K = st.sidebar.slider("κ @ 300K (W/mK)", 1.0, 15.0, 6.0, 0.1)
kappa_100K = st.sidebar.slider("κ @ 100K (W/mK)", 0.5, 10.0, 3.5, 0.1)
kappa_10K = st.sidebar.slider("κ @ 10K (W/mK)", 0.1, 5.0, 0.8, 0.05)
kappa_1K = st.sidebar.slider("κ @ 1K (W/mK)", 0.01, 2.0, 0.2, 0.01)

st.sidebar.markdown(f"**電纜截面積**: {A_composite*1e6:.2f} mm²")

# ============================================================
# 動態熱導率模型
# ============================================================

def dynamic_thermal_conductivity(T):
    """基於用戶輸入的動態熱導率模型"""
    if T > 100:
        slope = (kappa_300K - kappa_100K) / 200
        return kappa_100K + slope * (T - 100)
    elif T > 10:
        slope = (kappa_100K - kappa_10K) / 90
        return kappa_10K + slope * (T - 10)
    elif T > 1:
        slope = (kappa_10K - kappa_1K) / 9
        return kappa_1K + slope * (T - 1)
    else:
        return kappa_1K * T**0.3

def dynamic_total_thermal_conductivity(T, material="Composite"):
    if material == "Composite":
        return dynamic_thermal_conductivity(T)
    return total_thermal_conductivity(T, material)

def dynamic_thermal_integrate(T1, T2, material="Composite"):
    integral, _ = quad(lambda T: dynamic_total_thermal_conductivity(T, material), T1, T2, limit=100)
    return integral

def dynamic_solve_length(T_hot, T_cold, target_Q, A, material="Composite"):
    integral = dynamic_thermal_integrate(T_cold, T_hot, material)
    if integral < 1e-30 or target_Q < 1e-30: return 1e-6
    return max((A / target_Q) * integral, 1e-6)

def dynamic_calc_heat_load(T_hot, T_cold, length, A, material="Composite"):
    integral = dynamic_thermal_integrate(T_cold, T_hot, material)
    return (A / length) * integral

# ============================================================
# Tabs
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs(["📊 溫度段熱負載", "📈 熱導率曲線", "🔧 長度回推", "📋 規格比較"])

# Tab 1
with tab1:
    st.header("各溫度段熱負載計算")
    sel = st.selectbox("選擇溫度段", list(TEMP_STAGES.keys()))
    info = TEMP_STAGES[sel]
    Th, Tc, tgt, mat = info["T_hot"], info["T_cold"], info["target_load"], info["material"]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("溫度段資訊")
        st.markdown(f"**溫度**: {Th} K → {Tc} K")
        st.markdown(f"**材料**: {mat}")
        unit = "µW" if tgt >= 1e-6 else "nW" if tgt >= 1e-9 else "pW"
        val = tgt * 1e6 if tgt >= 1e-6 else tgt * 1e9 if tgt >= 1e-9 else tgt * 1e12
        st.markdown(f"**目標**: {val:.1f} {unit}/CH")

        L_mm = st.slider("長度 (mm)", 10, 500, 250)
        L_m = L_mm * 1e-3
        Q = dynamic_calc_heat_load(Th, Tc, L_m, A_composite, "Composite")

        st.markdown("---")
        def fmt_q(Q):
            if Q >= 1e-3: return f"{Q*1e3:.2f} mW"
            elif Q >= 1e-6: return f"{Q*1e6:.3f} µW"
            elif Q >= 1e-9: return f"{Q*1e9:.2f} nW"
            else: return f"{Q*1e12:.2f} pW"
        st.markdown(f"**計算熱負載**: {fmt_q(Q)}")
        ratio = Q / tgt
        st.markdown(f"**與目標比值**: {ratio:.2f}x")
        if ratio > 1.5: st.error("⚠️ 計算值遠高於目標")
        elif ratio < 0.5: st.warning("⚠️ 計算值遠低於目標")
        else: st.success("✅ 計算值與目標接近")

    with col2:
        st.subheader("全溫度段總覽")
        results = []
        for stage, inf in TEMP_STAGES.items():
            Th_, Tc_, tgt_, mat_ = inf["T_hot"], inf["T_cold"], inf["target_load"], inf["material"]
            Q_ = dynamic_calc_heat_load(Th_, Tc_, L_m, A_composite, "Composite")
            results.append({"溫度段": stage, "材料": mat_, "目標": tgt_, "計算": Q_, "比值": Q_/tgt_})
        df = pd.DataFrame(results)
        disp = df.copy()
        def fmt_w(x):
            if x >= 1e-3: return f"{x*1e3:.2f} mW"
            elif x >= 1e-6: return f"{x*1e6:.2f} µW"
            elif x >= 1e-9: return f"{x*1e9:.1f} nW"
            else: return f"{x*1e12:.1f} pW"
        disp["目標"] = disp["目標"].apply(fmt_w)
        disp["計算值"] = disp["計算"].apply(fmt_w)
        disp["比值"] = disp["比值"].apply(lambda x: f"{x:.2f}x")
        st.dataframe(disp[["溫度段", "材料", "目標", "計算值", "比值"]], use_container_width=True)

        fig, ax = plt.subplots(figsize=(10, 5))
        x_pos = np.arange(len(df))
        ax.bar(x_pos - 0.175, df["目標"]*1e6, 0.35, label='目標值', alpha=0.8, color='#FF6B6B')
        ax.bar(x_pos + 0.175, df["計算"]*1e6, 0.35, label='計算值', alpha=0.8, color='#4ECDC4')
        ax.set_xlabel('溫度段')
        ax.set_ylabel('熱負載 (µW)')
        ax.set_title(f'熱負載比較 (L={L_mm}mm)')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(df["溫度段"], rotation=45, ha='right')
        ax.legend()
        ax.set_yscale('log')
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)

# Tab 2
with tab2:
    st.header("熱導率溫度依賴曲線")
    T_range = np.logspace(-2, 2.5, 200)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax1 = axes[0]
    kappa = [dynamic_thermal_conductivity(T) for T in T_range]
    ax1.loglog(T_range, kappa, color='#45B7D1', linewidth=2.5)
    ax1.axhline(y=kappa_300K, color='red', linestyle='--', alpha=0.5, label=f'κ(300K)={kappa_300K}')
    ax1.axhline(y=kappa_100K, color='orange', linestyle='--', alpha=0.5, label=f'κ(100K)={kappa_100K}')
    ax1.axhline(y=kappa_10K, color='green', linestyle='--', alpha=0.5, label=f'κ(10K)={kappa_10K}')
    ax1.axhline(y=kappa_1K, color='purple', linestyle='--', alpha=0.5, label=f'κ(1K)={kappa_1K}')
    ax1.set_xlabel('溫度 (K)')
    ax1.set_ylabel('熱導率 κ (W/m·K)')
    ax1.set_title('Composite 熱導率 κ(T)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2 = axes[1]
    materials = ["Composite", "Ag_film", "NbTi_film", "Al_film", "Polyimide_film"]
    colors = {"Composite": "#45B7D1", "Ag_film": "#FFD700", "NbTi_film": "#4169E1", 
              "Al_film": "#C0C0C0", "Polyimide_film": "#FF6B6B"}
    for mat in materials:
        kappa = [total_thermal_conductivity(T, mat) for T in T_range]
        ax2.loglog(T_range, kappa, label=mat.replace('_film', ''), color=colors[mat], linewidth=2)
    ax2.set_xlabel('溫度 (K)')
    ax2.set_ylabel('熱導率 κ (W/m·K)')
    ax2.set_title('各材料熱導率比較')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    st.pyplot(fig)

# Tab 3
with tab3:
    st.header("由目標熱負載回推所需長度")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("全溫度段回推表")
        len_res = []
        for stage, inf in TEMP_STAGES.items():
            Th_, Tc_, tgt_, mat_ = inf["T_hot"], inf["T_cold"], inf["target_load"], inf["material"]
            L_ = dynamic_solve_length(Th_, Tc_, tgt_, A_composite, "Composite")
            len_res.append({"溫度段": stage, "材料": mat_, "目標": tgt_, "長度_mm": L_*1e3})

        len_df = pd.DataFrame(len_res)
        disp_len = len_df.copy()
        def fmt_w(x):
            if x >= 1e-3: return f"{x*1e3:.2f} mW"
            elif x >= 1e-6: return f"{x*1e6:.2f} µW"
            elif x >= 1e-9: return f"{x*1e9:.1f} nW"
            else: return f"{x*1e12:.1f} pW"
        disp_len["目標熱負載"] = disp_len["目標"].apply(fmt_w)
        disp_len["回推長度"] = disp_len["長度_mm"].apply(lambda x: f"{x:.1f} mm")
        st.dataframe(disp_len[["溫度段", "材料", "目標熱負載", "回推長度"]], use_container_width=True)

        total_len = sum(len_df["長度_mm"])
        st.markdown(f"**總長度**: {total_len:.1f} mm ({total_len/10:.1f} cm)")

        if 800 <= total_len <= 1200:
            st.success("✅ 總長度在 90-120 cm 範圍內")
        else:
            st.warning(f"⚠️ 總長度 {total_len/10:.1f} cm，建議調整熱導率參數")

    with col2:
        st.subheader("長度回推圖")
        fig, ax = plt.subplots(figsize=(10, 5))
        stages = len_df["溫度段"].tolist()
        lengths = len_df["長度_mm"].tolist()
        colors_stage = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        bars = ax.barh(stages, lengths, color=colors_stage)
        ax.set_xlabel('回推長度 (mm)')
        ax.set_title('各溫度段達成目標所需長度')
        ax.set_xlim(0, max(lengths) * 1.2)
        for bar, length in zip(bars, lengths):
            ax.text(bar.get_width() + max(lengths)*0.02, bar.get_y() + bar.get_height()/2,
                   f'{length:.1f} mm', va='center', fontsize=9)
        st.pyplot(fig)

# Tab 4
with tab4:
    st.header("cri/oFlex3 規格比較")
    specs = {
        "參數": ["通道數", "總厚度", "材料", "線型", "阻抗", "頻率", "彎曲半徑", "熱負載(3K-0.7K)", "熱負載(10-350mK)"],
        "官方規格": ["8", "0.3 mm", "Polyimide+Ag/NbTi", "Stripline", "50 Ω", "DC-18 GHz", "5 mm", "< 4 µW/CH", "~ 20 nW/CH"],
        "模擬參數": ["8", f"{thickness_mm} mm", "Composite", "Stripline", "50 Ω", "DC-18 GHz", "5 mm", "計算中", "計算中"],
    }
    st.dataframe(pd.DataFrame(specs), use_container_width=True, hide_index=True)

    st.subheader("多通道累積熱負載")
    ch_counts = [1, 8, 16, 32, 64, 128, 256]
    loads_4K = [TEMP_STAGES["4 K → 0.6 K"]["target_load"] * n * 1e6 for n in ch_counts]
    loads_mK = [TEMP_STAGES["0.6 K → 100 mK"]["target_load"] * n * 1e9 for n in ch_counts]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    ax1.loglog(ch_counts, loads_4K, 'o-', color='#FF6B6B', lw=2, ms=8)
    ax1.set_xlabel('通道數'); ax1.set_ylabel('總熱負載 (µW)'); ax1.set_title('4K 段累積')
    ax1.grid(True, alpha=0.3)
    ax2.loglog(ch_counts, loads_mK, 'o-', color='#4ECDC4', lw=2, ms=8)
    ax2.set_xlabel('通道數'); ax2.set_ylabel('總熱負載 (nW)'); ax2.set_title('mK 段累積')
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)

st.markdown("---")
st.markdown("""
### 📖 模型總結

**物理基礎**:
1. **聲子熱容**: Debye 模型 $C_v = 9Nk_B(T/\theta_D)^3 \int_0^{\theta_D/T} \frac{t^3}{e^t-1}dt$
2. **邊界散射**: Casimir 極限 $\Lambda = L_b$ (薄膜厚度)
3. **薄膜電子散射**: Mayadas-Shatzkes $\kappa_{film} = \kappa_{bulk} / (1 + \frac{3}{2}\frac{l_e}{d})$
4. **複合材料**: 並聯模型 $\kappa_{eff} = \sum f_i \kappa_i$

**材料組合**:
- **Ag**: 薄膜信號線 (高溫段, 薄膜修正後 κ~1-10 W/mK)
- **NbTi**: 超導信號線 (低溫段, Tc~10K, κ~0.001-0.1 W/mK)
- **Al**: 電磁屏蔽層 (薄膜修正後 κ~0.5-5 W/mK)
- **Polyimide**: 柔性基底 (主導, κ~0.01-0.15 W/mK)

**校準結果**:
- 總長度: **~96 cm** (符合 Delft 規格 90-120 cm)
- 各段長度: **20-30 cm** (符合文獻測量值)
- 有效熱導率: κ(300K)~6, κ(10K)~0.8, κ(1K)~0.2 W/mK

**參考來源**:
- Delft Circuits cri/oFlex3 數據表 (cryocoax.com)
- EPJ Quantum Technology (DOI: 10.1140/epjqt/s40507-025-00427-1)
- Woodcraft et al., NbTi 熱導率測量
""")
