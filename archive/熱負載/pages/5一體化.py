from streamlit import caption, columns, error, header, markdown, metric, set_page_config, sidebar, subheader, success, table, title, warning, write, radio, number_input, slider
import streamlit as st
import numpy as np


set_page_config(page_title="Cri/oFlex 3 一體化熱負載模擬器", layout="wide") # --- 網頁配置與標題 ---
with sidebar:
  總長度=radio("選擇 Cri/oFlex® 3 產品總長度", options=[300, 500, 700, 1000, 1200], index=3, format_func=lambda x: f"{x} mm" , horizontal=True) # 依照規格書底部的標準選項 # 預設 1000 mm

  通道總數 = number_input("排線通道總數 (Channels)", min_value=1, value=96, step=1)

  markdown("---")
  header("📏 稀釋冷凍機溫層物理垂直間距分佈")
  markdown("請依您冷凍機內部的實體銅盤盤面間距，分配排線的縱向直鋪長度（單位：mm）：")

# 動態分配滑桿（以 1000mm 為例，各層合理垂直跨度）
  L_300_50 = slider("300K → 50K 垂直間距 (mm)", 50, 400, 250, 10)
  L_50_4 = slider("50K → 4K 垂直間距 (mm)", 50, 300, 200, 10)
  L_4_06 = slider("4K → 0.6K (Still) 垂直間距 (mm)", 50, 250, 150, 10)
  L_06_100m = slider("0.6K → 100mK 垂直間距 (mm)", 50, 250, 150, 10)
  L_100m_10m = slider("100mK → 10mK (MXC) 垂直間距 (mm)", 50, 250, 150, 10)

# 計算分配後的直鋪長度總和
  直鋪長度 = L_300_50 + L_50_4 + L_4_06 + L_06_100m + L_100m_10m
  應力緩衝 = 總長度 - 直鋪長度

  markdown("---")
  header("🔬 柔性線截面積結構參數")
  pitch = slider("通道間距 Pitch (mm)", 0.5, 2.0, 1.0, 0.1) / 1000.0
  thickness = slider("基板厚度 Thickness (mm)", 0.1, 0.5, 0.3, 0.05) / 1000.0
  A_poly = pitch * thickness

# --- 核心物理模型：低溫熱導率積分與線性縮放機制 ---
# 規格書標準基準點：總長為 1000mm 鋪設時的每通道被動熱負載
base_data = {
    "300K → 50K":   {"銀": 2.7e-3,  "鈮鈦": None,      "預設長度": 250},
    "50K → 4K":     {"銀": 0.8e-3,  "鈮鈦": None,      "預設長度": 200},
    "4K → 0.6K":    {"銀": 5.4e-6,  "鈮鈦": 540.0e-9,  "預設長度": 150},
    "0.6K → 100mK": {"銀": 290.0e-9,"鈮鈦": 29.0e-9,   "預設長度": 150},
    "100mK → 10mK": {"銀": 5.9e-9,  "鈮鈦": 590.0e-12, "預設長度": 150}
}

# 當前用戶分配的實際段長度
長度配置 = {
    "300K → 50K": L_300_50,
    "50K → 4K": L_50_4,
    "4K → 0.6K": L_4_06,
    "0.6K → 100mK": L_06_100m,
    "100mK → 10mK": L_100m_10m
}

# --- 主畫面佈局 ---
col1, col2 = columns([3, 2])

with col1:
    header("📊 一體化排線各溫層靜態熱負載計算結果 (單通道)")
    write("根據傅立葉導熱線性反比關係 $P_{\\text{actual}} = P_{\\text{base}} \\times \\frac{L_{\\text{base}}}{L_{\\text{actual}}}$ 進行動態外推：")
    
    # 檢查長度是否超標
    if 應力緩衝 < 0:
        error(f"🚨 **工程錯誤**：您分配的垂直間距總和 ({直鋪長度} mm) 已超過所選的 Cri/oFlex 總長度規格 ({總長度} mm)！請調大產品長度或縮短溫層間距。")
    else:
        # 建立展示表格
        table_data = []
        p_mxc_ag_final = 0.0
        p_mxc_nbti_final = 0.0
        p_50k_final = 0.0
        p_4k_final = 0.0
        
        for 溫度段, 熱負載 in base_data.items():
            L_b = 熱負載["預設長度"]
            L_a = 長度配置[溫度段]
            
            # 依長度反比縮放熱負載
            銀負載 = 熱負載["銀"] * (L_b / L_a)
            鈮鈦負載 = 熱負載["鈮鈦"] * (L_b / L_a) if 熱負載["鈮鈦"] else None
            
            # 記錄特定溫層用於右側摘要
            if 溫度段 == "300K → 50K": p_50k_final = 銀負載
            if 溫度段 == "50K → 4K": p_4k_final = 銀負載
            if 溫度段 == "100mK → 10mK":
                p_mxc_ag_final = 銀負載
                p_mxc_nbti_final = 鈮鈦負載
                
            table_data.append({
                "溫度區段": 溫度段,
                "分配直鋪長度": f"{L_a} mm",
                "實際單通道負荷 (Ag 銀線)": f"{銀負載*1e6:.2f} µW" if 銀負載 >= 1e-6 else f"{銀負載*1e9:.1f} nW",
                "實際單通道負荷 (NbTi 超導)": f"{鈮鈦負載*1e9:.1f} nW" if 鈮鈦負載 and 鈮鈦負載 >= 1e-9 else (f"{鈮鈦負載*1e12:.1f} pW" if 鈮鈦負載 else "高溫段不適用")
            })
            
        table(table_data)

with col2:
    header("📐 產品製造與佈線工藝摘要")
    
    # 顯示總長度規格狀態
    metric("Cri/oFlex® 3 產品總長度", f"{總長度} mm")
    metric("內部直鋪垂直總跨度", f"{直鋪長度} mm")
    
    # 應力緩衝安全裕度評估
    if 應力緩衝 >= 0:
        if 應力緩衝 < 總長度 * 0.05:
            warning(f"⚠️ **低溫緩衝裕度 (Slack)**: {應力緩衝} mm\n\n剩餘長度過短 (＜5%)，可能無法有效抵禦 Polyimide 基材低溫收縮產生的拉扯應力！")
        else:
            success(f"✅ **低溫緩衝裕度 (Slack)**: {應力緩衝} mm\n\n剩餘長度充足 (約 {應力緩衝/總長度*100:.1f}%)，可於各溫層熱錨定夾具旁鋪設為 S 型應力釋放弧線。")
            
    #markdown("---")
    subheader("🧊 96 通道全開 - 冷凍機總體靜態熱衝擊")
    
    if 應力緩衝 >= 0:
        metric("50K Stage 總負荷", f"{p_50k_final * 通道總數 * 1000:.1f} mW")
        metric("4K Stage 總負荷", f"{p_4k_final * 通道總數 * 1000:.1f} mW")
        markdown("**MXC 混合室 (10mK) 總負荷抉擇：**")
        error(f"🔴 全線採用【純銀 Ag 版本】: {p_mxc_ag_final * 通道總數 * 1e9:.1f} nW")
        success(f"🟢 全線採用【鈮鈦 NbTi 超導版】: {p_mxc_nbti_final * 通道總數 * 1e9:.2f} nW")

with sidebar:
  markdown("---")
  subheader("💡 Monolithic 一體化設計之工程觀察")
  markdown(f"""
  *   **一體化製程本質**：Cri/oFlex® 3 的產品長度（例如您選擇的 **{總長度} mm**）在出廠時即固定。上層的熱錨定夾具只是「壓接」在排線的特定位置上，並非將排線切斷。
  *   **滑桿聯動的物理意義**：當您在左側嘗試把某一溫層的間距拉長（例如將 100mK $\rightarrow$ 10mK 拉長），您會發現該溫層的熱阻變大，**熱負載立刻下降**。這完美模擬了如何透過調配冷凍機內部的佈線走向，去最佳化特定溫層的熱預算。
  """)
  subheader("📦 原廠出廠成品規格 (Monolithic)") # --- 側邊欄設定：原廠成品規格選型 ---
  title("🎛️ Cri/oFlex® 3 一體化 (Monolithic) 柔性線熱負載模擬器")
  caption("基於 Delft Circuits 原廠出廠規格：一條直通到底（RT to mK）之總長度分配與靜態熱流預算分析")
