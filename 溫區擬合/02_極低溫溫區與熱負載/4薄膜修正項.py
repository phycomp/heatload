import streamlit as st
import numpy as np

# --- 網頁標題與設定 ---
st.set_page_config(page_title="Cri/oFlex 3 等長修正模擬器", layout="wide")
st.title("🎛️ Cri/oFlex® 3 柔性線【等長約束】熱負載模擬器")
st.caption("修正版：強制導體等長邊界條件，並引入薄膜尺寸效應與接觸熱阻修正")

# --- 側邊欄：幾何與工程參數設定 ---
st.sidebar.header("📏 柔性排線幾何結構參數")
channels_total = st.sidebar.number_input("通道總數 (Channels)", min_value=1, value=96, step=1)
pitch = st.sidebar.slider("通道間距 Pitch (mm)", 0.5, 3.0, 1.0, 0.1) / 1000.0  # 轉公尺
thickness = st.sidebar.slider("基板厚度 Thickness (mm)", 0.1, 1.0, 0.3, 0.05) / 1000.0  # 轉公尺

# 單通道分攤的 Polyimide 截面積
A_poly = pitch * thickness 

st.sidebar.markdown("---")
st.sidebar.header("⚡ 導體微米級截面積")
t_cond = st.sidebar.slider("導體層厚度 (µm)", 0.5, 5.0, 1.5, 0.5) / 1e6  # 轉公尺
w_cond = st.sidebar.slider("導體線寬 (mm)", 0.05, 0.5, 0.1, 0.05) / 1000.0  # 轉公尺
A_cond = t_cond * w_cond

st.sidebar.markdown("---")
st.sidebar.header("🛠️ 工程實務修正項")
# 引入微米級薄膜因晶格散射導致的熱導率衰減（通常比塊材低一個數量級）
film_correction = st.sidebar.slider("薄膜導熱衰減因子 (Film Scatter)", 0.05, 1.0, 0.15, 0.05, 
                                    help="微米級金屬薄膜的低溫熱導率遠低於NIST塊材數據，此因子用於修正尺寸效應。")
contact_resistance = st.sidebar.slider("接觸熱阻增益因子", 1.0, 2.0, 1.2, 0.1,
                                       help="考慮黃金熱錨定夾具的接觸熱阻，實際物理長度需乘以此放寬係數。")

# --- 物理模型：引入薄膜修正的導熱積分 ---
def get_corrected_integral(material, t_low, t_high):
    if material == "Polyimide":
        def poly_integ(t):
            return 0.002 * (t**2.2) if t < 4 else 0.012 * (t**1.5) + 0.03
        return poly_integ(t_high) - poly_integ(t_low)
    
    elif material == "Ag":
        # 塊材積分乘上薄膜幾何修正
        def ag_integ(t):
            return 0.5 * (t**2) if t < 4 else 400 * t - 1200
        return (ag_integ(t_high) - ag_integ(t_low)) * film_correction
    
    elif material == "NbTi":
        def nbti_integ(t):
            return 0.005 * (t**3) if t < 4 else 0.15 * (t**1.2)
        return (nbti_integ(t_high) - nbti_integ(t_low)) * film_correction
    return 0.0

# --- 溫區資料定義 ---
stages = {
    "300K → 50K":   {"T_hi": 300.0, "T_lo": 50.0,  "P_Ag": 2.7e-3,  "P_NbTi": None},
    "50K → 4K":     {"T_hi": 50.0,  "T_lo": 4.0,   "P_Ag": 0.8e-3,  "P_NbTi": None},
    "4K → 0.6K":    {"T_hi": 4.0,   "T_lo": 0.6,   "P_Ag": 5.4e-6,  "P_NbTi": 540e-9},
    "0.6K → 100mK": {"T_hi": 0.6,   "T_lo": 0.1,   "P_Ag": 290e-9,  "P_NbTi": 29e-9},
    "100mK → 10mK": {"T_hi": 0.1,   "T_lo": 0.01,  "P_Ag": 5.9e-9,  "P_NbTi": 590e-12}
}

# --- 主畫面布局 ---
col1, col2 = st.columns(2)

with col1:
    st.header("📐 溫層約束等長計算結果")
    st.write("依據排線一體化製程，Ag 與 NbTi 在同溫層內**共用唯一物理長度**。系統採用加權權重聯立求解。")
    
    total_len = 0.0
    table_data = []
    
    for name, info in stages.items():
        t_hi, t_lo = info["T_hi"], info["T_lo"]
        
        int_poly = get_corrected_integral("Polyimide", t_lo, t_hi)
        int_ag = get_corrected_integral("Ag", t_lo, t_hi)
        int_nbti = get_corrected_integral("NbTi", t_lo, t_hi)
        
        p_ag = info["P_Ag"]
        p_nbti = info["P_NbTi"]
        
        # 聯立求解核心邏輯：
        # 如果該溫區同時有 Ag 與 NbTi 的數據，由兩者聯合推導出最具物理合理性的單一長度
        if p_nbti is not None and p_ag is not None:
            L_from_ag = ((A_cond * int_ag) + (A_poly * int_poly)) / p_ag
            L_from_nbti = ((A_cond * int_nbti) + (A_poly * int_poly)) / p_nbti
            # 取兩者幾何平均值，並套用接觸熱阻增益，確保等長且合理
            L_final = (np.sqrt(L_from_ag * L_from_nbti)) * contact_resistance * 100.0 # 轉公分
        else:
            # 高溫段僅有 Ag 數據
            L_final = (((A_cond * int_ag) + (A_poly * int_poly)) / p_ag) * contact_resistance * 100.0
            
        total_len += L_final
        
        table_data.append({
            "溫度區段": name,
            "圖中負載 (Ag)": f"{p_ag*1e6:.1f} µW" if p_ag >= 1e-6 else f"{p_ag*1e9:.1f} nW",
            "圖中負載 (NbTi)": f"{p_nbti*1e9:.1f} nW" if p_nbti and p_nbti >= 1e-9 else (f"{p_nbti*1e12:.1f} pW" if p_nbti else "高溫段未裝配"),
            "修正後統一長度 (L)": f"**{L_final:.2f} cm**"
        })
        
    st.table(table_data)

with col2:
    st.header("📦 96 CH 排線整體規格")
    st.metric("單條排線總物理長度 (Total Length)", f"{total_len/100:.2f} m ({total_len:.1f} cm)")
    
    st.markdown("---")
    st.subheader("❄️ 稀釋冷凍機各層靜態熱功耗")
    st.info(f"**50K 溫層總功耗:** {stages['300K → 50K']['P_Ag'] * channels_total * 1000:.1f} mW\n\n"
            f"**4K 溫層總功耗:** {stages['50K → 4K']['P_Ag'] * channels_total * 1000:.1f} mW\n\n"
            f"**MXC (10mK) 總功耗 (Ag):** {stages['100mK → 10mK']['P_Ag'] * channels_total * 1e9:.1f} nW\n\n"
            f"**MXC (10mK) 總功耗 (NbTi):** {stages['100mK → 10mK']['P_NbTi'] * channels_total * 1e9:.1f} nW")
