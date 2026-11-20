from streamlit import caption, dataframe, expander, info, markdown, plotly_chart, set_page_config, sidebar, subheader, title, write, radio, number_input
from numpy import pi as π
from pandas import DataFrame
#import streamlit as st
#import numpy as np
#import pandas as pd
from plotly.express import bar

# ------------------------------
# 常數與輔助函數
# ------------------------------
L0 = 2.44e-8  # W·Ω/K^2

def AWG轉直徑(awg):   #awg_to_diameter
    """AWG 轉直徑 (m)"""
    if awg <= 0:
        return 0.01168  # 4/0 約 11.68 mm
    return 0.127e-3 * (92 ** ((36 - awg) / 39))

def AWG轉面積(awg):  #awg_to_area
    d = AWG轉直徑(awg)  #awg_to_diameter
    return π * (d/2)**2

# 預定義 AWG 選項
AWG_OPTIONS = [24, 30, 32, 34, 36, 38, 40]

# 溫度段定義
segments = [
    ("300 K → 50 K", 300, 50),
    ("50 K → 4 K", 50, 4),
    ("4 K → 0.6 K", 4, 0.6),
    ("0.6 K → 100 mK", 0.6, 0.1),
    ("100 mK → 10 mK", 0.1, 0.01),
]

# 原始方案材料與電阻率 (Ω·m)
# 根據典型值設定
rho_original = {
    "300 K → 50 K": 1.6e-8,      # Ag 室溫附近
    "50 K → 4 K": 70e-8,          # NbTi 正常態
    "4 K → 0.6 K": 1e-10,         # 高純 Ag 殘餘電阻 (RRR=1000)
    "0.6 K → 100 mK": 1e-10,
    "100 mK → 10 mK": 1e-10,
}

# CuNi44 近似電阻率 (全溫度段常數)
rho_cuni = 50e-8   # Ω·m

# 預設長度 (m) – 可讓用戶調整
default_lengths = {
    "300 K → 50 K": 0.2,
    "50 K → 4 K": 0.2,
    "4 K → 0.6 K": 0.5,
    "0.6 K → 100 mK": 0.3,
    "100 mK → 10 mK": 0.4,
}

# ------------------------------
# 熱負載計算函數 (WF 定律)
# ------------------------------
def heat_load_wf(area, rho, th, tc, length):
    """
    使用 Wiedemann-Franz 定律計算熱流 Q (W)
    Q = (A * L0 * (Th^2 - Tc^2)) / (2 * rho * L)
    """
    if length <= 0 or area <= 0 or rho <= 0:
        return 0.0
    delta_T2 = th**2 - tc**2
    numerator = area * L0 * delta_T2
    denominator = 2 * rho * length
    return numerator / denominator

# ------------------------------
# Streamlit UI
# ------------------------------
set_page_config(page_title="低溫傳輸線熱負載模擬", layout="wide")

lengths = {}
with sidebar: # 側邊欄 – 全局參數
    subheader("⚙️ 全局設定")
    selected_awg = radio("選擇 AWG 線徑", AWG_OPTIONS, index=AWG_OPTIONS.index(36), horizontal=True)
    wire_diameter_mm = AWG轉直徑(selected_awg) * 1000    #awg_to_diameter
    wire_area_m2 = AWG轉面積(selected_awg)  #awg_to_area
    info(f"**線徑**: {selected_awg} AWG → {wire_diameter_mm:.3f} mm\n**截面積**: {wire_area_m2:.3e} m²")
    subheader("📏 各溫度段長度 (m)") # 各段長度獨立調整
    for name, _, _ in segments:
        default = default_lengths[name]
        lengths[name] = number_input(f"{name} 長度 (m)", value=default, step=0.05, format="%.3f")

# 進階：材料電阻率調整（選項）
subheader("🧪 材料電阻率微調 (原始方案)")
rho_ag_high = number_input("Ag 高溫段 (300→50K) ρ (Ω·m)", value=1.6e-8, format="%.1e")
rho_nbti = number_input("NbTi (50→4K) ρ (Ω·m)", value=70e-8, format="%.1e")
rho_ag_low = number_input("Ag 低溫段 (4K 以下) ρ (Ω·m)", value=1e-10, format="%.1e")
# 更新原始電阻率字典
rho_original_custom = {
    "300 K → 50 K": rho_ag_high,
    "50 K → 4 K": rho_nbti,
    "4 K → 0.6 K": rho_ag_low,
    "0.6 K → 100 mK": rho_ag_low,
    "100 mK → 10 mK": rho_ag_low,
}

# 計算按鈕
#compute = button("🚀 計算熱負載", type="primary")


# ------------------------------
# 主界面：兩種方案對比
# ------------------------------
#if compute:
def 計算熱負載():
    # 計算原始方案各段熱負載
    q_original = {}
    for (name, th, tc) in segments:
        rho = rho_original_custom[name]
        length = lengths[name]
        q = heat_load_wf(wire_area_m2, rho, th, tc, length)
        q_original[name] = q
    
    # 計算全 CuNi 方案
    q_cuni = {}
    for (name, th, tc) in segments:
        length = lengths[name]
        q = heat_load_wf(wire_area_m2, rho_cuni, th, tc, length)
        q_cuni[name] = q
    
    # 製作 DataFrame
    df = DataFrame({
        "溫度段": [name for name, _, _ in segments],
        "原始 Ag/NbTi 熱負載 (W)": [q_original[name] for name, _, _ in segments],
        "全 CuNi 熱負載 (W)": [q_cuni[name] for name, _, _ in segments],
    })
    
    # 轉換為更友善的單位 (W, μW, nW, pW)
    def format_power(val):
        if val >= 1e-3:
            return f"{val*1e3:.2f} mW"
        elif val >= 1e-6:
            return f"{val*1e6:.2f} μW"
        elif val >= 1e-9:
            return f"{val*1e9:.2f} nW"
        elif val >= 1e-12:
            return f"{val*1e12:.2f} pW"
        else:
            return f"{val:.2e} W"
    
    df["原始 (格式化)"] = df["原始 Ag/NbTi 熱負載 (W)"].apply(format_power)
    df["CuNi (格式化)"] = df["全 CuNi 熱負載 (W)"].apply(format_power)
    
    # 顯示表格
    subheader(f"📊 模擬結果 (線徑 {selected_awg} AWG)")
    dataframe(df[["溫度段", "原始 (格式化)", "CuNi (格式化)"]], use_container_width=True)
    
    # 顯示數值對比圖 (柱狀圖, 對數刻度)
    fig = bar(
        df.melt(id_vars="溫度段", value_vars=["原始 Ag/NbTi 熱負載 (W)", "全 CuNi 熱負載 (W)"],
                var_name="方案", value_name="熱負載 (W)"),
        x="溫度段", y="熱負載 (W)", color="方案", barmode="group",
        log_y=True, title=f"各溫度段熱負載對比 (AWG {selected_awg})",
        labels={"熱負載 (W)": "熱負載 (W, 對數刻度)"}
    )
    plotly_chart(fig, use_container_width=True)
    
    # 詳細數值表 (科學記號)
    subheader("📈 詳細數值 (W, 科學記號)")
    dataframe(df[["溫度段", "原始 Ag/NbTi 熱負載 (W)", "全 CuNi 熱負載 (W)"]], use_container_width=True)
    
    # 討論
    markdown("### 💡 觀察")
    improvement = {}
    for name in q_original:
        orig = q_original[name]
        cuni = q_cuni[name]
        if orig > 0:
            ratio = cuni / orig
            if ratio < 1:
                improvement[name] = f"降低至 {ratio:.2f} 倍"
            else:
                improvement[name] = f"增加至 {ratio:.2f} 倍"
        else:
            improvement[name] = "N/A"
    
    write("相較於原始方案，全 CuNi 方案的熱負載變化：")
    for name, msg in improvement.items():
        write(f"- **{name}**：{msg}")
    
    caption("注意：CuNi 電阻率高，雖降低固體傳導熱，但若承載電流，焦耳熱會顯著上升。此模擬僅考慮被動傳導。")
#else:
    #info("👈 請在左側設定參數後點擊「計算熱負載」")

計算熱負載()
with sidebar:
#with expander("📖 物理模型說明"):
    #markdown("---")
    caption("公式：Q = (A·L₀·(Tₕ²−T꜀²)) / (2·ρ·L)")
    markdown(r"""
    - **Wiedemann-Franz 定律**：$ k = L_0 T / \rho $，其中 $L_0 = 2.44 \times 10^{-8} \, \text{W·Ω/K}^2$。
    - 熱流 $ Q = \frac{A}{L} \int_{T_c}^{T_h} k(T) dT = \frac{A L_0 (T_h^2 - T_c^2)}{2 \rho L}$，假設 $\rho$ 在區間內為常數。
    - 原始方案：
        - 高溫段 (300→50K) : Ag ($\rho \approx 1.6\times10^{-8} \Omega\cdot m$)
        - 中溫段 (50→4K) : NbTi ($\rho \approx 70\times10^{-8} \Omega\cdot m$)
        - 低溫段 (4K 以下) : 高純 Ag ($\rho \approx 1\times10^{-10} \Omega\cdot m$，對應 RRR≈1000)
    - 替代方案：全段使用 CuNi44 ($\rho \approx 50\times10^{-8} \Omega\cdot m$)。
    - 注意：極低溫下材料的殘餘電阻率可能偏離常數近似，此工具僅提供合理估算。
    """)
    title("🔧 低溫傳輸線熱負載模擬 (Wiedemann-Franz 定律)")
    markdown("比較 **Ag/NbTi** 原始方案 與 **全 CuNi** 替代方案，在不同 AWG 線徑下的各溫度段熱負載。")
