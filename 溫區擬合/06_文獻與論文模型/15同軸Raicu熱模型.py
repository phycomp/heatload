from streamlit import caption, columns, dataframe, divider, expander, info, markdown, metric, pyplot, set_page_config, sidebar, subheader, tabs, title, number_input, code, table, caption
from matplotlib.pyplot import subplots
from numpy import arange, array, ceil, linspace, log10, logspace, trapezoid
from pandas import DataFrame
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# Cryogenic Thermal Modeling of Microwave High-Density Signaling
# Raicu et al., EPJ Quantum Technology (2025) 12:124
# ============================================================

set_page_config(page_title="Raicu et al. 2025 熱負載解析", layout="wide")


# ============================================================
# 側邊欄 — 論文核心參數
# ============================================================
with sidebar:
  subheader("⚙️ 論文核心參數")

  subheader("SC-086/50-SCN-CN 电缆截面")
  A_outer_mm2 = number_input("外导体截面 (mm²)", value=0.2389, format="%.4f")
  A_dielectric_mm2 = number_input("PTFE 介电层截面 (mm²)", value=0.3098, format="%.4f")
  A_inner_mm2 = number_input("内导体截面 (mm²)", value=0.0324, format="%.4f")

  subheader("Bluefors XLD1000-SL 温度级")
  T_50K = number_input("50K 级温度 (K)", value=50.0)
  T_4K = number_input("4K 级温度 (K)", value=3.5)
  T_still = number_input("Still 级温度 (K)", value=1.4)
  T_CP = number_input("CP 级温度 (K)", value=0.20)
  T_MXC = number_input("MXC 基温 (K)", value=0.02)

  P_50K = number_input("50K 制冷功率 (W)", value=40.0)
  P_4K = number_input("4K 制冷功率 (W)", value=0.70)
  P_still = number_input("Still 制冷功率 (W)", value=7e-3, format="%.3e")
  P_CP = number_input("CP 制冷功率 (W)", value=1e-3, format="%.3e")
  P_MXC = number_input("MXC 制冷功率 (W)", value=30e-6, format="%.3e")

  L_50K = number_input("50K 段长度 (m)", value=0.3053, format="%.4f")
  L_4K = number_input("4K 段长度 (m)", value=0.3155, format="%.4f")
  L_still = number_input("Still 段长度 (m)", value=0.2775, format="%.4f")
  L_CP = number_input("CP 段长度 (m)", value=0.1965, format="%.4f")
  L_MXC = number_input("MXC 段长度 (m)", value=0.1965, format="%.4f")

  N_max = number_input("最大电缆数 N", value=1008, min_value=1)

  subheader("主动负载参数")
  I_flux = number_input("通量偏置电流 (mA)", value=0.4, format="%.2f")
  att_dB = number_input("衰减器 (dB)", value=20)

# ============================================================
# 分頁
# ============================================================
論文摘要,物理推導, 熱導率測量, 靜態熱負載計算,主動熱負載計算, 量子處理器規模限制 = tabs([
    "📋 論文摘要",
    "🔬 物理推導",
    "📐 熱導率測量",
    "🌡️ 靜態熱負載計算",
    "⚡ 主動熱負載計算",
    "📊 量子處理器規模限制",
])
    

# ===================== 分頁 1: 論文摘要 =====================
with 論文摘要:
    subheader("論文摘要與結構")

    col1, col2 = columns(2)

    with col1:
        subheader("研究背景")
        markdown("""
        **超導量子計算機規模化挑戰**：

        超導量子計算機需要微波控制線從室溫連接到稀釋制冷機混合室（MXC）。
        增加線數而不進行熱建模預測，會導致各溫度級制冷功率被壓垮。

        **本文研究對象**：
        - 電纜: SC-086/50-SCN-CN 半刚性同轴电缆
        - 制造商: Coax Co., Ltd. (日本)
        - 應用: Bluefors XLD1000-SL HDW（高密度布線）
        - 材料: C7150 白銅外導體 + PTFE 介電層 + 鍍銀 C7150 内導體

        **核心貢獻**：
        1. 測量并擬合 SC-086/50-SCN-CN 各組件熱導率（2K-300K）
        2. 測量内導體直流電阻率（室溫-3.8K）
        3. 建立靜態和主動熱負載模型
        4. 應用于 Bluefors XLD1000-SL，評估 100-225 量子比特規模
        """)

    with col2:
        subheader("關鍵結論")
        markdown("""
        **Bluefors XLD1000-SL + HDW 1008 線容量**：

        | 配置 | 量子比特上限 | 限制因素 |
        |:-----|:------------|:---------|
        | 理論極限（全部制冷功率） | ~200 qubits | 熱負載 |
        | 實際限制（工程裕度） | **~140 qubits** | 制冷功率 + MXC 空間 |

        **意外發現**：
        - 最大比例熱負載出現在 **CP 級**（69.3%），而非 MXC！
        - 原因: CP 段長度短 + 溫差大 (1.4K→0.2K) + 上方累積熱流

        **改進方向**：
        1. 4K 以下改用超導電纜（消除主動負載 + 大幅降低靜態負載）
        2. 使用柔性微波帶線（截面更小，熱負載更低）
        3. 光纖 + 轉換器（消除熱傳導）
        4. cryo-CMOS 或 RSFQ 數字電路（減少線數）
        """)

    subheader("SC-086/50-SCN-CN 電纜結構")
    markdown("""
    ```
    【截面結構】

    外導體: C7150 白銅 (Cu:Ni ≈ 62.5:37.5)
    ┌─────────────────────────────┐  ← 外徑  .86 mm
    │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │    截面  .2389 mm²
    │  ○━━━━━━━━━━━━━━━━━━━━━━━○  │  ← PTFE 介電層
    │  ○  鍍銀 C7150 内導體    ○  │     外徑 .66  mm, 截面: .3098 mm²
    │  ○  銀鍍層 ~3-4 μm       ○  │     内徑 .203 mm, 截面: .0324 mm²
    │  ○━━━━━━━━━━━━━━━━━━━━━━━○  │
    │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
    └─────────────────────────────┘

    【Bluefors HDW 配置】

    室溫 (300K) → 50K 級 → 4K 級 → Still 級 → CP 級 → MXC (20mK)
    ┌────┴────┐   ┌──┴──┐   ┌──┴──┐    ┌──┴──┐  ┌──┴──┐  ┌──┴───┐
    │   HDW   │   │ 熱沉│   │ 熱沉│    │ 熱沉│  │ 熱沉│  │ 量子 │
    │   法蘭  │   │ 50K │   │  4K │    │Still│  │ CP  │  │處理器│
    └────┬────┘   └──┬──┘   └──┬──┘    └──┬──┘  └──┬──┘  └──┬───┘
    電纜長度:   0.3053m   0.3155m   0.2775m   0.1965m  0.1965m
    (Below MXC: 0.1965m, 等溫 @ MXC, 不計入靜態負載)

    各級熱沉截斷熱流，每段獨立計算。
    ```
    """)

    subheader("Bluefors XLD1000-SL 溫度級配置")

    df_stages = DataFrame({
        '溫度級': ['50K', '4K', 'Still', 'CP', 'MXC', 'Below MXC'],
        '溫度 (K)': [T_50K, T_4K, T_still, T_CP, T_MXC, T_MXC],
        '制冷功率 (W)': [P_50K, P_4K, f"{P_still:.3e}", f"{P_CP:.3e}", f"{P_MXC:.3e}", '-'],
        '段長度 (m)': [L_50K, L_4K, L_still, L_CP, L_MXC, L_MXC],
        '電纜熱沉': ['有', '有', '有', '有', '有', '等溫'],
    })
    dataframe(df_stages, use_container_width=True, hide_index=True)

    info("""
    **注**：Bluefors 僅官方指定 MXC 的制冷功率和基溫。其他溫度級的制冷功率是作者
    通過在裸機各級加熱器測量溫度響應（"熱圖"）估計的，標有星號*。
    """)

# ===================== 分頁 2: 物理推導 =====================
with 物理推導:
    subheader("物理推導")

    markdown(r"""
    ### 一、靜態熱負載（熱傳導）

    同軸電纜由三種材料組成：外導體（白銅）、介電層（PTFE）、内導體（鍍銀白銅）。
    將每種材料視為獨立的**並聯熱傳導路徑**，總熱導為各組件之和。

    **單組件熱負載**（傅立葉定律積分形式）：
    $$q_{component} = \frac{A}{L} \int_{T_L}^{T_H} k(T) dT$$

    其中：
    - $q_{component}$ = 組件熱負載 (W)
    - $A$ = 組件截面積 (m²)
    - $L$ = 電纜段長度 (m)
    - $T_H, T_L$ = 段兩端高/低溫度 (K)
    - $k(T)$ = 材料溫度相關熱導率 (W/m/K)

    **總靜態熱負載**（三組件並聯）：
    $$q_{cable} = q_{outer} + q_{dielectric} + q_{inner} = \sum_{component} q_{component}$$

    **N 根電纜在溫度級的總熱負載**：
    $$q_{stage} = N \times q_{cable}$$

    ### 二、熱導率擬合模型

    使用 **8 階泰勒級數**（NIST 低溫材料數據庫格式）擬合 $\log_{10} k$ 與 $\log_{10} T$：

    $$k(T) = 10^{\left[ a + b(\log_{10} T) + c(\log_{10} T)^2 + d(\log_{10} T)^3 + e(\log_{10} T)^4 + f(\log_{10} T)^5 + g(\log_{10} T)^6 + h(\log_{10} T)^7 + i(\log_{10} T)^8 \right]}$$

    **優勢**：此格式可處理跨越多個數量級的函數（如熱導率從 300K 到 2K 變化數百倍）。

    **低溫外推**：實驗數據最低到 ~2K，低于此溫度用直線外推到原點（$k(0)=0$）。
    此假設可能**高估**低溫熱導率（實際斜率更大）。

    ### 三、主動熱負載（歐姆加熱）

    電纜載流時產生的焦耳熱：
    $$q_{active} = \int_0^L I^2 \rho(T) \frac{1}{A} dx$$

    對于均勻電纜，簡化為：
    $$q_{active} = I^2 \times R = I^2 \times \rho(T) \frac{L}{A}$$

    其中：
    - $I$ = 線路電流（通量偏置線 $I = 0.4$ mA）
    - $\rho(T)$ = 電阻率（$\Omega$·m）
    - 電阻率同樣用 8 階多項式擬合 $\log_{10} \rho$ vs $log_{10} T$

    **關鍵發現**：内導體在 ~10K 以下電阻率趨于常數（雜質散射主導），
    $\rho_{const} = 9.928 \times 10^{-9} \Omega$-m。

    **注**：微波頻率下電阻率由趨膚效應主導（銀鍍層），與此處直流測量不同。

    ### 四、衰減器主動負載

    T-pad 衰減器（20 dB 範例）：
    ```
    輸入 ──R1──┬──R3──┬──R2── 輸出
              │      │
             GND    GND

    對于 50Ω 系統、20 dB 衰減：
    R1 = R2 = 40.91 Ω, R3 = 10.1 Ω
    ```

    衰減器功耗取決于輸入電流/功率。通量偏置線（DC 恆流）在衰減器上產生：
    $$P_{att} = I_{in}^2 \times (R1 + R2 + R3)$$

    但需考慮衰減后電流：$I_{out} = I_{in} \times 10^{-Att/20}$

    ### 五、制冷機級聯熱平衡

    每級的**淨熱負載** = 上方傳入的熱負載 + 本級主動負載 - 傳到下方的熱負載

    $$q_{net, i} = q_{from, i-1} + q_{active, i} - q_{to, i+1}$$

    熱流方向：總是從高溫流向低溫。每級熱沉截斷傳導熱流，
    只允許該段溫差產生的熱流繼續向下。

    ### 六、規模化模型

    模型量子處理器：$n \times n$ 通量可調 transmon 陣列，每對之間有可調耦合器。

    | 組件 | 數量 | 控制線/讀出線 | 說明 |
    |:-----|:-----|:-------------|:-----|
    | 量子比特 | $n^2$ | 每個: XY 驅動 + 通量偏置 + 讀出諧振器 | |
    | 可調耦合器 | $2n(n-1)$ | 每個: 通量偏置 | |
    | 讀出鏈 | $\lceil n^2/6 \rceil$ | 每條: Read-In + Read-Out + TWPA 泵浦 | 6 路復用 |

    總線數 = $2n^2$ (XY + 通量) + $2n(n-1)$ (耦合器通量) + $3\lceil n^2/6 \rceil$ (讀出)

    10×10 (100 qubits): 431 線
    15×15 (225 qubits): 984 線（接近 1008 上限）
    16×16 (256 qubits): 1121 線（**超過 1008！**）
    """)

# ===================== 分頁 3: 熱導率測量 =====================
with 熱導率測量:
    subheader("熱導率與電阻率測量")

    markdown("""
    **實驗方法**：Quantum Design PPMS TTO（Thermal Transport Option）

    脈沖加熱法：在樣品一端加電熱脈沖，兩個溫度計測量溫升，
    擬合溫升-時間曲線提取熱導率。軟件自動校正輻射損失。
    """)

    # 論文擬合系數
    subheader("論文 8 階擬合系數（$k(T)$ 單位: W/m/K）")

    coeffs = {
        '外導體 (C7150)': {'a': -3.198399, 'b': 20.49947, 'c': -66.11415, 'd': 117.6898, 'e': -121.4773, 'f': 76.21467, 'g': -28.74949, 'h': 5.984756, 'i': -0.5266892, 'valid': '2.0-297.6 K'},
        '介電層 (PTFE, NIST)': {'a': 2.7380, 'b': -30.677, 'c': 89.430, 'd': -136.99, 'e': 124.69, 'f': -69.556, 'g': 23.320, 'h': -4.3135, 'i': 0.33829, 'valid': '4-300 K'},
        '内導體 (鍍銀 C7150)': {'a': -2.750003, 'b': 25.84512, 'c': -74.18405, 'd': 113.5856, 'e': -96.84387, 'f': 46.38328, 'g': -11.82451, 'h': 1.321682, 'i': -0.02456645, 'valid': '2.3-292.6 K'},
    }


    for name, c in coeffs.items():
        #with expander(f"{name} — 有效範圍: {c['valid']}"):
      左, 右=columns(2)
      with 左:
        code(f"{name} — 有效範圍: {c['valid']}")
      with 右:
        df_coeff = DataFrame({
            '系數': ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'],
            '值': [c['a'], c['b'], c['c'], c['d'], c['e'], c['f'], c['g'], c['h'], c['i']],
        })
        df_coeff=df_coeff.style.set_caption(f"{name} — 有效範圍: {c['valid']}")
        #caption(f"{name} — 有效範圍: {c['valid']}")
        df_coeff
      #dataframe(df_coeff)

      #table(df_coeff, width='stretch', hide_index=True)

    # 熱導率計算函數
    def k_model(T, coeffs_dict):
        if T <= 0:
            return 0
        logT = log10(T)
        logk = (coeffs_dict['a'] + coeffs_dict['b']*logT + coeffs_dict['c']*logT**2 +
                coeffs_dict['d']*logT**3 + coeffs_dict['e']*logT**4 + coeffs_dict['f']*logT**5 +
                coeffs_dict['g']*logT**6 + coeffs_dict['h']*logT**7 + coeffs_dict['i']*logT**8)
        return 10**logk

    # 計算特定溫度點
    temps_check = [2, 4, 10, 20, 50, 100, 200, 300]
    k_data = []
    for T in temps_check:
        k_data.append({
            'T (K)': T,
            'k_outer (W/m/K)': k_model(T, coeffs['外導體 (C7150)']),
            'k_PTFE (W/m/K)': k_model(T, coeffs['介電層 (PTFE, NIST)']),
            'k_inner (W/m/K)': k_model(T, coeffs['内導體 (鍍銀 C7150)']),
        })

    df_k = DataFrame(k_data)
    subheader("擬合熱導率數值")
    dataframe(df_k, use_container_width=True, hide_index=True)

    # 繪圖
    fig, ax = subplots(figsize=(12, 5))
    T_range = logspace(0.3, 2.5, 500)  # 2K to 300K

    k_outer = [k_model(T, coeffs['外導體 (C7150)']) for T in T_range]
    k_ptfe = [k_model(T, coeffs['介電層 (PTFE, NIST)']) for T in T_range]
    k_inner = [k_model(T, coeffs['内導體 (鍍銀 C7150)']) for T in T_range]

    ax.loglog(T_range, k_outer, 'b-', linewidth=2, label='Outer Conductor (C7150)')
    ax.loglog(T_range, k_ptfe, 'g-', linewidth=2, label='Dielectric (PTFE)')
    ax.loglog(T_range, k_inner, 'r-', linewidth=2, label='Inner Conductor (Ag-plated C7150)')

    # 標記溫度級
    stage_temps = [T_50K, T_4K, T_still, T_CP, T_MXC]
    stage_names = ['50K', '4K', 'Still', 'CP', 'MXC']
    for T, name in zip(stage_temps, stage_names):
        ax.axvline(x=T, color='gray', linestyle='--', alpha=0.3)
        ax.text(T, max(k_outer)*0.5, name, rotation=90, fontsize=9, ha='right', va='top')

    ax.set_xlabel('Temperature T (K)', fontsize=12)
    ax.set_ylabel('Thermal Conductivity k(T) (W/m/K)', fontsize=12)
    ax.set_title('Fitted Thermal Conductivity vs Temperature (Raicu et al. Fig. 3)', fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    pyplot(fig)

    markdown("""
    **圖表解讀**：
    - 外導體（白銅）熱導率最高，低溫下仍顯著（合金中電子貢獻）
    - PTFE 介電層熱導率最低，是主要熱阻來源
    - 内導體（鍍銀）熱導率介于兩者之間，銀鍍層改善低溫導熱
    - 所有材料在 300K→2K 范圍內變化 2-3 個數量級
    """)

    subheader("直流電阻率測量")

    markdown("""
    **實驗配置**：10" (0.254 m) 電纜樣品裝在 4K 級，兩端接 SMA 穿牆接頭，
    四端法測量電阻。

    **關鍵發現**：
    - 電阻率在 ~10K 以下趨于常數（雜質散射主導，Matthiessen 定律）
    - 常數值: $\rho = 9.928 \times 10^{-9} \Omega$-m
    - 低于 3.8K 用此常數外推

    **注**：RF 電阻率由趨膚效應主導（銀鍍層），與直流值不同。
    """)

    # 電阻率簡化模型（低溫常數）
    rho_const = 9.928e-9  # Ohm-m
    metric("低溫電阻率 (T<10K)", f"{rho_const:.3e} Ω·m", "雜質散射主導")

# ===================== 分頁 4: 靜態熱負載 =====================
with 靜態熱負載計算:
    subheader("靜態熱負載計算")

    markdown(r"""
    **公式**（每段、每組件）：
    $$q_{component} = \frac{A}{L} \int_{T_L}^{T_H} k(T) \, dT$$

    使用數值積分（梯形法）計算各段積分。
    """)

    # 計算各段積分
    def compute_q_segment(T_low, T_high, L_m, A_mm2, coeff_dict, n_pts=5000):
        T = linspace(T_low, T_high, n_pts)
        k = array([k_model(t, coeff_dict) for t in T])
        I = trapezoid(k, T)  # W/m/K * K = W/m
        A = A_mm2 * 1e-6  # m²
        q = A * I / L_m  # W
        return q, I

    segments = [
        ('300K→50K', 300.0, T_50K, L_50K),
        ('50K→4K', T_50K, T_4K, L_4K),
        ('4K→Still', T_4K, T_still, L_still),
        ('Still→CP', T_still, T_CP, L_CP),
        ('CP→MXC', T_CP, T_MXC, L_MXC),
    ]

    results_static = []
    for name, Th, Tl, L in segments:
        q_o, I_o = compute_q_segment(Tl, Th, L, A_outer_mm2, coeffs['外導體 (C7150)'])
        q_d, I_d = compute_q_segment(Tl, Th, L, A_dielectric_mm2, coeffs['介電層 (PTFE, NIST)'])
        q_i, I_i = compute_q_segment(Tl, Th, L, A_inner_mm2, coeffs['内導體 (鍍銀 C7150)'])
        q_total = q_o + q_d + q_i

        results_static.append({
            '溫度段': name,
            'T_H (K)': Th,
            'T_L (K)': Tl,
            '長度 (m)': L,
            '外導體 (W)': q_o,
            'PTFE (W)': q_d,
            '内導體 (W)': q_i,
            '單電纜總計 (W)': q_total,
            '單電纜總計 (nW)': q_total * 1e9,
            'N=1008 總計 (W)': q_total * N_max,
            'N=1008 總計 (mW)': q_total * N_max * 1e3,
        })

    df_static = DataFrame(results_static)
    dataframe(df_static, use_container_width=True, hide_index=True)

    # 計算各級佔制冷功率比例
    cooling_powers = [P_50K, P_4K, P_still, P_CP, P_MXC]

    subheader("各級熱負載佔制冷功率比例")

    ratio_data = []
    for i, (r, cp) in enumerate(zip(results_static, cooling_powers)):
        q_N = r['N=1008 總計 (W)']
        ratio = q_N / cp * 100 if cp > 0 else 0
        ratio_data.append({
            '溫度段': r['溫度段'],
            '制冷功率 (W)': cp,
            'N=1008 熱負載 (W)': q_N,
            '佔比 (%)': ratio,
        })

    df_ratio = DataFrame(ratio_data)
    dataframe(df_ratio, use_container_width=True, hide_index=True)

    # 繪圖
    fig, ax = subplots(figsize=(12, 5))

    stages = [r['溫度段'] for r in results_static]
    q_single = [r['單電纜總計 (W)'] * 1e9 for r in results_static]  # nW
    q_N = [r['N=1008 總計 (W)'] * 1e3 for r in results_static]  # mW

    x = arange(len(stages))
    width = 0.35

    ax.bar(x - width/2, q_single, width, label='Single Cable (nW)', color='lightblue', edgecolor='black')
    ax2 = ax.twinx()
    ax2.bar(x + width/2, q_N, width, label='N=1008 (mW)', color='salmon', edgecolor='black')

    ax.set_ylabel('Single Cable Heat Load (nW)', fontsize=12)
    ax2.set_ylabel('N=1008 Heat Load (mW)', fontsize=12, color='salmon')
    ax.set_title('Static Heat Load by Refrigerator Stage', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(stages, rotation=15)
    ax.legend(loc='upper left')
    ax2.legend(loc='upper right')
    ax.grid(True, alpha=0.3, axis='y')
    pyplot(fig)

    # 制冷功率佔比圖
    fig2, ax2 = subplots(figsize=(12, 5))

    ratios = [r['佔比 (%)'] for r in ratio_data]
    colors = ['green' if r < 50 else 'orange' if r < 80 else 'red' for r in ratios]

    bars = ax2.bar([r['溫度段'] for r in ratio_data], ratios, color=colors, edgecolor='black')
    ax2.axhline(y=50, color='green', linestyle='--', alpha=0.5, label='50% margin')
    ax2.axhline(y=80, color='red', linestyle='--', alpha=0.5, label='80% warning')
    ax2.set_ylabel('Fraction of Cooling Power (%)', fontsize=12)
    ax2.set_title('Static Heat Load / Cooling Power Ratio (N=1008)', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')

    for bar, val in zip(bars, ratios):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(ratios)*0.01,
                f'{val:.1f}%', ha='center', fontsize=10, fontweight='bold')

    pyplot(fig2)

    markdown("""
    **關鍵發現**（論文 Fig. 4）：

    1. **CP 級佔比最高** (~69%)：段長短 (0.1965 m) + 溫差大 (1.4K→0.2K) + 上方累積熱流
    2. **MXC 佔比反而低**：雖然制冷功率最小 (30 μW)，但段長短且溫差小
    3. **50K 和 4K 佔比低**：制冷功率大（40 W 和 0.7 W），輕松承受
    4. **Still 級佔比中等**：7 mW 制冷功率，負擔可接受

    **結論**： unexpectedly，最大瓶頸不是 MXC，而是 **CP 級**！
    """)

    # 材料貢獻分解
    subheader("材料貢獻分解（N=1008, 各段）")

    for r in results_static:
        q_total = r['N=1008 總計 (W)']
        if q_total > 0:
            q_o = r['外導體 (W)'] * N_max
            q_d = r['PTFE (W)'] * N_max
            q_i = r['内導體 (W)'] * N_max
            col1, col2, col3, col4 = columns(4)
            col1.metric(f"{r['溫度段']}", f"{q_total*1e3:.2f} mW")
            col2.metric("外導體", f"{q_o/q_total*100:.1f}%")
            col3.metric("PTFE", f"{q_d/q_total*100:.1f}%")
            col4.metric("内導體", f"{q_i/q_total*100:.1f}%")

# ===================== 分頁 5: 主動熱負載 =====================
with 主動熱負載計算:
    subheader("主動熱負載計算")

    markdown("""
    **主動熱負載來源**：
    1. 通量偏置線（恆流 DC）— 主要來源
    2. XY 驅動線（脈沖，佔空比低）— 可忽略
    3. 讀出線（脈沖）— 可忽略
    4. 衰減器電阻功耗
    5. TWPA 泵浦線（50Ω 終端）
    6. LNA（4K 級半導體放大器，7.8 mW/個）

    **本模型只計算通量偏置線 + 衰減器 + TWPA + LNA**
    """)

    subheader("通量偏置線主動負載模型")

    markdown(r"""
    **假設**：
    - 每個量子比特和可調耦合器各有 1 條通量偏置線
    - 每條線載流 $I = 0.4$ mA（DC）
    - 20 dB 衰減器安裝在 4K 級（T-pad 結構）
    - 電纜電阻: $R = \rho L / A$

    **T-pad 衰減器（20 dB, 50Ω）**：
    - R1 = R2 = 40.91 Ω, R3 = 10.1 Ω
    - 輸入阻抗 = 輸出阻抗 = 50Ω
    - 電流衰減: $I_{out} = I_{in} / 10$ (20 dB = 10x 電壓衰減)

    **電流計算**（從 MXC 向上反推）：
    - MXC 需要 $I_{MXC} = 0.4$ mA
    - 4K 衰減器輸出 = 0.4 mA → 輸入 = 4.0 mA
    - 4K 級以上無衰減器，電流 = 4.0 mA
    """)

    # 主動負載計算
    I_mxc = I_flux * 1e-3  # A
    I_4K_above = I_mxc * 10**(att_dB/20)  # 衰減器上方電流

    col1, col2 = columns(2)
    col1.metric("MXC 電流", f"{I_mxc*1e3:.1f} mA")
    col2.metric("4K 以上電流", f"{I_4K_above*1e3:.1f} mA")

    # 簡化主動負載計算（使用低溫常數電阻率）
    rho_low = 9.928e-9  # Ohm-m

    active_results = []
    for name, Th, Tl, L in segments:
        # 簡化：使用低溫常數電阻率（保守估計，實際高溫電阻率更高）
        R = rho_low * L / (A_inner_mm2 * 1e-6)  # Ohm

        # 確定該段電流
        if 'CP→MXC' in name or 'Still→CP' in name:
            I = I_mxc  # 衰減器下方
        elif '4K→Still' in name:
            I = I_4K_above  # 衰減器上方
        elif '50K→4K' in name or '300K→50K' in name:
            I = I_4K_above  # 同上方
        else:
            I = I_mxc

        P = I**2 * R  # W

        active_results.append({
            '溫度段': name,
            '長度 (m)': L,
            '電流 (mA)': I * 1e3,
            '電阻 (μΩ)': R * 1e6,
            '單線功耗 (W)': P,
            '單線功耗 (nW)': P * 1e9,
        })

    df_active = DataFrame(active_results)
    dataframe(df_active, use_container_width=True, hide_index=True)

    # 衰減器功耗
    subheader("衰減器功耗（20 dB T-pad @ 4K 級）")

    R1 = 40.91  # Ohm
    R2 = 40.91
    R3 = 10.1
    I_in_att = I_4K_above  # A

    P_R1 = I_in_att**2 * R1
    P_R2 = I_mxc**2 * R2
    # R3 電流 = I_in + I_out（近似）
    P_R3 = (I_in_att + I_mxc)**2 * R3 / 4  # 簡化
    P_att_total = P_R1 + P_R2 + P_R3

    markdown(f"""
    ```
    T-pad 衰減器功率分布:
    R1 (40.91Ω): P = I_in² × R1 = ({I_in_att*1e3:.1f} mA)² × 40.91 = {P_R1*1e6:.1f} μW
    R2 (40.91Ω): P = I_out² × R2 = ({I_mxc*1e3:.1f} mA)² × 40.91 = {P_R2*1e6:.1f} μW
    R3 (10.1Ω):  P ≈ {(I_in_att+I_mxc)/2*1e3:.1f} mA × 10.1 = {P_R3*1e6:.1f} μW

    總衰減器功耗: ~{P_att_total*1e6:.1f} μW = {P_att_total*1e3:.3f} mW (每線)
    N=1008 總衰減器功耗: ~{P_att_total*1e3*N_max:.1f} mW
    ```
    """)

    # 其他主動負載
    subheader("其他主動負載")

    markdown("""
    **TWPA 泵浦線**（每條讀出鏈 1 條）：
    - TWPA 泵浦功率: -60 dBm @ TWPA
    - 定向耦合器: 20 dB → 輸入 -40 dBm = 0.1 μW
    - 終端 50Ω 負載消耗絕大部分功率
    - 每線 RMS 電流: ~0.044 mA
    - 讀出鏈數: $\lceil n^2/6 \rceil$

    **LNA（4K 級）**：
    - 每個 LNA 功耗: 7.8 mW
    - 讀出鏈數 = LNA 數量
    - 144 qubits (24 條讀出鏈): 24 × 7.8 = 187.2 mW @ 4K

    **注**：LNA 是 4K 級最大的主動負載之一！
    """)

    # TWPA 和 LNA 規模化
    n_list = [10, 11, 12, 13, 14, 15]
    qubits = [n**2 for n in n_list]
    readout_chains = [ceil(q/6) for q in qubits]
    lna_power = [rc * 7.8e-3 for rc in readout_chains]  # W

    fig, ax = subplots(figsize=(10, 5))
    ax.plot(qubits, [p*1e3 for p in lna_power], 'o-', linewidth=2, markersize=8, color='purple')
    ax.set_xlabel('Number of Qubits', fontsize=12)
    ax.set_ylabel('LNA Total Power @ 4K (mW)', fontsize=12)
    ax.set_title('LNA Active Load vs Processor Size', fontsize=14)
    ax.grid(True, alpha=0.3)
    pyplot(fig)

# ===================== 分頁 6: 規模限制 =====================
with 量子處理器規模限制:
    subheader("量子處理器規模限制")

    markdown("""
    **模型處理器**：$n \times n$ 通量可調 transmon 陣列，可調耦合器連接每對。

    **控制線需求**（每個處理器）：
    - 每個量子比特: 1 XY 驅動 + 1 通量偏置 + 1 讀出諧振器
    - 每個可調耦合器: 1 通量偏置
    - 讀出鏈: 6 路復用（Read-In + Read-Out + TWPA 泵浦）
    """)

    # 計算不同規模的總線數和熱負載
    scale_results = []
    for n in range(10, 17):
        n_qubits = n**2
        n_couplers = 2*n*(n-1)
        n_readout = int(ceil(n_qubits / 6))

        # 總線數
        n_xy = n_qubits  # XY 驅動線
        n_qubit_flux = n_qubits  # 量子比特通量偏置
        n_coupler_flux = n_couplers  # 耦合器通量偏置
        n_readin = n_readout
        n_readout_line = n_readout
        n_twap_pump = n_readout

        total_lines = n_xy + n_qubit_flux + n_coupler_flux + n_readin + n_readout_line + n_twap_pump

        # 靜態熱負載（使用 CP→MXC 段作為代表，這是最受限的段之一）
        q_per_line = results_static[4]['單電纜總計 (W)']  # CP→MXC
        q_total_static = q_per_line * total_lines

        # 主動負載（通量偏置線）
        n_flux_lines = n_qubit_flux + n_coupler_flux  # 有電流的線
        P_flux_per_line = rho_low * L_CP / (A_inner_mm2 * 1e-6) * (I_mxc)**2
        P_flux_total = P_flux_per_line * n_flux_lines

        # LNA 功率
        P_lna = n_readout * 7.8e-3

        scale_results.append({
            'n': n,
            '量子比特數': n_qubits,
            '耦合器數': n_couplers,
            '讀出鏈數': n_readout,
            '總線數': total_lines,
            '靜態熱負載 (W)': q_total_static,
            '靜態熱負載 (mW)': q_total_static * 1e3,
            '通量線主動 (W)': P_flux_total,
            '通量線主動 (mW)': P_flux_total * 1e3,
            'LNA 主動 (W)': P_lna,
            'LNA 主動 (mW)': P_lna * 1e3,
        })

    df_scale = DataFrame(scale_results)
    dataframe(df_scale, use_container_width=True, hide_index=True)

    # 可視化
    fig, ax = subplots(figsize=(12, 6))

    x = arange(len(scale_results))
    qubits_list = [r['量子比特數'] for r in scale_results]
    total_lines_list = [r['總線數'] for r in scale_results]

    # 雙軸圖
    ax.bar(x, total_lines_list, color='lightblue', edgecolor='black', label='Total Lines')
    ax.axhline(y=1008, color='red', linestyle='--', linewidth=2, label='HDW Max (1008)')

    ax2 = ax.twinx()
    ax2.plot(x, qubits_list, 'o-', color='purple', linewidth=2, markersize=8, label='Qubits')

    ax.set_xlabel('Processor Size (n × n)', fontsize=12)
    ax.set_ylabel('Total Control Lines', fontsize=12, color='blue')
    ax2.set_ylabel('Number of Qubits', fontsize=12, color='purple')
    ax.set_title('Processor Scaling: Lines vs Qubits', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r['n']}×{r['n']}" for r in scale_results])
    ax.legend(loc='upper left')
    ax2.legend(loc='upper right')
    ax.grid(True, alpha=0.3, axis='y')
    pyplot(fig)

    markdown("""
    **規模限制分析**：

    1. **HDW 線數上限**: 1008 條
       - 15×15 (225 qubits): 984 線 ✓ 可容納
       - 16×16 (256 qubits): 1121 線 ✗ **超過上限！**

    2. **理論熱負載上限**: ~200 qubits（使用全部制冷功率）
       - 更大規模會壓垮 CP 或 4K 級制冷

    3. **實際限制**: ~140 qubits
       - 工程裕度（避免滿負載運行）
       - MXC 空間限制（讀出組件體積）
       - 預計 24 條讀出鏈（144 qubits）已難以在 MXC 安裝

    **結論**：SC-086/50-SCN-CN + Bluefors XLD1000-SL HDW 的實際上限約 **140 量子比特**。
    """)

    subheader("改進方向")

    markdown("""
    | 改進方案 | 效果 | 狀態 |
    |:---------|:-----|:-----|
    | **超導電纜（4K 以下）** | 消除主動負載 + 靜態降低數量級 | 可用（NbTi 電纜） |
    | **柔性微波帶線** | 截面更小，熱負載更低 | 商業化（Delft Cri/oFlex） |
    | **光纖 + 光電轉換** | 消除熱傳導 | 演示中（Lecocq et al. 2021） |
    | **cryo-CMOS 開關** | 減少線數 | 開發中（imec, Intel） |
    | **RSFQ/AQFP 數字電路** | 片上控制，極低功耗 | 研究階段 |
    | **動力學電感參量放大器（KIPA）** | 4K 運行，替代 TWPA + LNA | 開發中（Malnou et al.） |

    **最優組合**：4K 以上用白銅同軸 + 4K 以下用超導柔性帶線 + cryo-CMOS 開關復用
    """)

    subheader("與其他文獻對比")

    markdown("""
    | 文獻 | 電纜類型 | 規模評估 | 關鍵差異 |
    |:-----|:---------|:---------|:---------|
    | **Raicu 2025** | SC-086/50-SCN-CN 白銅 | ~140 qubits | 實測熱導率，CP 級受限 |
    | **Krinner 2019** | UT-085 同軸 | ~100 qubits | 較早評估，較小制冷機 |
    | **Smith 2021 (FLAX)** | NbTi/PFA 柔性 | MKID 陣列 | 探測器陣列，非量子計算 |
    | **Paluch 2025** | Cri/oFlex 3 柔性 | 熱化驗證 | 用量子比特測量熱化時間 |
    | **Deshpande 2019** | 多種電纜比較 | 高密度布線 | 聚焦布線密度 |

    **Raicu 2025 的獨特貢獻**：
    1. 首次完整測量 SC-086/50-SCN-CN 熱導率和電阻率
    2. 使用實測數據（而非文獻值）建立模型
    3. 發現 CP 級是意外瓶頸（而非 MXC）
    4. 明確給出 Bluefors XLD1000-SL 的量化規模限制
    """)

#divider()
with sidebar:
  title("📐 Cryogenic Thermal Modeling of Microwave High-Density Signaling")
  markdown(
      "**Raicu et al., EPJ Quantum Technology 12:124 (2025)** — doi:10.1140/epjqt/s40507-025-00427-1  "
      "SC-086/50-SCN-CN 半刚性同轴电缆在 Bluefors XLD1000-SL 稀释制冷机中的热负载建模"
  )
  caption("Raicu et al. (2025) Thermal Modeling Analysis | SC-086/50-SCN-CN in Bluefors XLD1000-SL | Streamlit Edition")
