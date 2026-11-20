from streamlit import caption, columns, info, markdown, metric, set_page_config, sidebar, subheader, table, title, write, slider, number_input
import streamlit as st
import numpy as np

from streamlit import empty, pyplot
with sidebar: # --- 側邊欄：幾何與工程參數設定 ---
  set_page_config(page_title="Cri/oFlex 3 熱負載長度反推模擬器", layout="wide") # --- 網頁標題與設定 ---
  subheader("📏 柔性排線幾何結構參數")
  channels_total = number_input("通道總數 (Channels)", min_value=1, value=96, step=1)
  pitch = slider("通道間距 Pitch (mm)", 0.5, 3.0, 1.0, 0.1) / 1000.0  # 轉公尺
  thickness = slider("基板厚度 Thickness (mm)", 0.1, 1.0, 0.3, 0.05) / 1000.0  # 轉公尺
  狀態=empty()
  subheader("⚡ 導體微米級截面積")
  t_cond = slider("導體層厚度 (µm)", 0.5, 5.0, 1.5, 0.5) / 1e6  # 轉公尺
  w_cond = slider("導體線寬 (mm)", 0.05, 0.5, 0.1, 0.05) / 1000.0  # 轉公尺
  A_cond = t_cond * w_cond
  A_poly = pitch * thickness # 單通道分攤的 Polyimide 截面積
  info(f"**單通道幾何修正資訊：**\n"
                  f"- Polyimide 截面積: {A_poly*1e6:.3f} mm²\n"
                  f"- 內層金屬截面積: {A_cond*1e6:.6f} mm²\n"
                  f"- 面積比 (Poly/Metal): ~{int(A_poly/A_cond)} 倍") #顯示計算出的截面積資訊

# --- 核心物理模型：材料低溫熱導率積分 ($\int \kappa dT$) ---
# 依據 NIST 數據庫簡化之各溫區導熱積分估算函數 (單位: W/m)
def 熱導率積分(material, t_low, t_high):
    if material == "Polyimide":
        def poly_integ(t): # Polyimide 在極低溫下遵循 T^2 ~ T3 趨勢，中高溫趨於線性
            return .002 * (t**2.2) if t < 4 else .012 * (t**1.5) + .03
        return poly_integ(t_high) - poly_integ(t_low)
    
    elif material == "Ag":
        # 純銀 (RRR=100) 低溫下具有極高熱導率
        def ag_integ(t):
            return 0.5 * (t**2) if t < 4 else 400 * t - 1200
        return ag_integ(t_high) - ag_integ(t_low)
    
    elif material == "NbTi":
        # 鈮鈦超導體在 4K 以下進入超導態，熱導率劇烈下降
        def nbti_integ(t):
            return 0.005 * (t**3) if t < 4 else 0.15 * (t**1.2)
        return nbti_integ(t_high) - nbti_integ(t_low)
    return 0.0

溫度段 = {
    "300K → 50K":   {"T_hi": 300.0, "T_lo": 50.0,  "P_Ag": 2.7e-3,  "P_NbTi": None},
    "50K → 4K":     {"T_hi": 50.0,  "T_lo": 4.0,   "P_Ag": 0.8e-3,  "P_NbTi": None},
    "4K → 0.6K":    {"T_hi": 4.0,   "T_lo": 0.6,   "P_Ag": 5.4e-6,  "P_NbTi": 540e-9},
    "0.6K → 100mK": {"T_hi": 0.6,   "T_lo": 0.1,   "P_Ag": 290e-9,  "P_NbTi": 29e-9},
    "100mK → 10mK": {"T_hi": 0.1,   "T_lo": 0.01,  "P_Ag": 5.9e-9,  "P_NbTi": 590e-12}
} # --- 溫區資料定義 (圖中數據) ---

# --- 主畫面布局 ---
col1, col2 = columns([2, 1])

with col1:
    subheader("📊 各溫層長度反推結果")
    write(r"系統採用傅立葉導熱公式反推： $L = \frac{1}{P} \cdot [A_{\text{metal}}\int\kappa_{\text{metal}}dT + A_{\text{poly}}\int\kappa_{\text{poly}}dT]$")
    
    total_len_ag = 0.0
    total_len_nbti = 0.0
    
    # 建立表格呈現數據
    table_data = []
    
    for name, 負載 in 溫度段.items():
        t_hi, t_lo = 負載["T_hi"], 負載["T_lo"]
        
        # 計算此溫區的熱導率積分值
        int_poly = 熱導率積分("Polyimide", t_lo, t_hi)
        int_ag = 熱導率積分("Ag", t_lo, t_hi)
        int_nbti = 熱導率積分("NbTi", t_lo, t_hi)
        
        # --- 銀線 (Ag) 長度計算 ---
        p_ag = 負載["P_Ag"]
        # 傅立葉分子：金屬貢獻 + Polyimide 修正項
        numerator_ag = (A_cond * int_ag) + (A_poly * int_poly)
        L_ag = (numerator_ag / p_ag) * 100.0 if p_ag else 0.0  # 轉公分
        if p_ag: total_len_ag += L_ag
            
        # --- 鈮鈦線 (NbTi) 長度計算 ---
        p_nbti = 負載["P_NbTi"]
        if p_nbti:
            numerator_nbti = (A_cond * int_nbti) + (A_poly * int_poly)
            L_nbti = (numerator_nbti / p_nbti) * 100.0  # 轉公分
            total_len_nbti += L_nbti
        else:
            # 高溫段不適用超導，預設與 Ag 段共用長度結構
            L_nbti = L_ag
            total_len_nbti += L_ag
            
        table_data.append({
            "溫度區段": name,
            "圖中負載 (Ag)": f"{p_ag*1e6:.2f} µW" if p_ag >= 1e-6 else f"{p_ag*1e9:.1f} nW",
            "反推長度 (Ag)": f"{L_ag:.2f} cm",
            "圖中負載 (NbTi)": f"{p_nbti*1e9:.1f} nW" if p_nbti and p_nbti >= 1e-9 else (f"{p_nbti*1e12:.1f} pW" if p_nbti else "N/A"),
            "反推長度 (NbTi)": f"{L_nbti:.2f} cm"
        })
        
    table(table_data)

with col2:
    subheader("總體規格摘要")
    metric("96 CH 整體總物理長度 (銀線版)", f"{total_len_ag/100:.3f} m")
    metric("96 CH 整體總物理長度 (鈮鈦超導版)", f"{total_len_nbti/100:.3f} m")
    
    # 計算全開時對稀釋冷凍機帶來的總靜態熱耗散
    markdown("---")
    subheader("🧊 96 通道全開總被動熱負荷")
    write("這是整條排線對冷凍機各階層抽氣功率的總考量：")
    #[{'300K → 50K': {'T_hi': 300.0, 'T_lo': 50.0, 'P_Ag': 0.0027, 'P_NbTi': None}, '50K → 4K': {'T_hi': 50.0, 'T_lo': 4.0, 'P_Ag': 0.0008, 'P_NbTi': None}, '4K → 0.6K': {'T_hi': 4.0, 'T_lo': 0.6, 'P_Ag': 5.4e-06, 'P_NbTi': 5.4e-07}, '0.6K → 100mK': {'T_hi': 0.6, 'T_lo': 0.1, 'P_Ag': 2.9e-07, 'P_NbTi': 2.9e-08}, '100mK → 10mK': {'T_hi': 0.1, 'T_lo': 0.01, 'P_Ag': 5.9e-09, 'P_NbTi': 5.9e-10}}]
    狀態.code(f"**50K 溫層總負載:** {溫度段['300K → 50K']['P_Ag'] * channels_total * 1000:.1f} mW\n\n"
            f"**MXC (10mK) 總負載 (Ag):** {溫度段['100mK → 10mK']['P_Ag'] * channels_total * 1e9:.1f} nW\n\n"
            f"**4K 溫層總負載:** {溫度段['50K → 4K']['P_Ag'] * channels_total * 1000:.2f} mW\n\n"
            f"**MXC (10mK) 總負載 (NbTi):** {溫度段['100mK → 10mK']['P_NbTi'] * channels_total * 1e9:.2f} nW"
    )

with sidebar: # --- 進階工程修正與說明提示 ---
    title("🎛️ Cri/oFlex® 3 柔性線熱負載與長度反推模擬器")
    caption("整合大面積 Polyimide 基材截面積修正與低溫材料熱導率積分模型 (96 CH 高密度排線適用)")
    subheader("💡 物理修正與工程邊界效應說明")
    markdown("""
    * **接觸熱阻修正 (Contact Thermal Resistance)**：本模擬基於理想熱導率積分。在實務組裝中，96 通道的黃金熱錨定夾具會引入機械接觸熱阻。因此實際加工長度通常會比模擬反推的純物理長度**放寬 15% 至 20%** 以預留裕度。
    * **Polyimide 的主導效應**：您可以嘗試在左側調整 '基板厚度'。您會發現，在 4K 以下的極低溫區段，微調基板厚度對 NbTi 線材反推長度的影響極為顯著，這證實了低溫下**大面積基材熱傳導**是決定低溫熱預算的主要物理瓶頸。
    """)
