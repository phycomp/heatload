import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.title("🛰️ Delft Cri/oFlex 物理性能模擬器")

# =========================================================================
# 1. 定義 w (μm) 與 t (nm) 的輸入邊界與預設值 (依據 Cri/oFlex 3 官方數據)
# =========================================================================
st.sidebar.header("📐 幾何尺寸設定")
w = st.sidebar.slider("訊號線寬度 W (μm)", min_value=10, max_value=300, value=150)
t = st.sidebar.slider("NbTi 超導膜厚 t (nm)", min_value=10, max_value=500, value=100)

# =========================================================================
# 2. 核心物理常數與計算邏輯
# =========================================================================
φ0 = 2.07e-15      # 磁通量子 (Wb)
mu0 = 4 * np.pi * 1e-7 # 真空磁導率
lambda_L = 200e-9    # NbTi 倫敦穿透深度 (200 nm)
xi = 5e-9            # NbTi 超導相干長度 (5 nm)

w_m = w * 1e-6       # 微米轉公尺
t_m = t * 1e-9       # 奈米轉公尺

# 2.1 計算本質解對合電流密度 Jd (A/m^2) 與其 A/cm^2 單位
jd = φ0 / (3 * np.sqrt(3) * np.pi * mu0 * (lambda_L**2) * xi)
jd_a_cm2 = jd / 1e4 

# 2.2 計算邊緣電流擠壓修正因子 (Current Crowding Factor)
crowding_factor = np.sqrt((2.4 * lambda_L / w_m) * np.tanh(w_m / (2 * lambda_L)))

# 2.3 計算實際總臨界電流 Ic (A) 與平均 Jc (A/cm^2)
ic_real = jd * (t_m * w_m) * crowding_factor
jc_avg_a_cm2 = (ic_real / (t_m * w_m)) / 1e4

# =========================================================================
# 3. 數據指標面板顯示
# =========================================================================
st.subheader("🧬 傳輸線超導極限數據")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("本質解對合極限 (Jd)", f"{jd_a_cm2 / 1e6:.1f} MA/cm²")
with col2:
    st.metric("平均臨界電流密度 (Jc_avg)", f"{jc_avg_a_cm2 / 1e6:.2f} MA/cm²")
with col3:
    st.metric("通道最大直流電流 (Ic)", f"{ic_real * 1e3:.1f} mA")

# =========================================================================
# 4. 訊號線內部電流密度分佈動態視覺化 (Matplotlib)
# =========================================================================
st.write("---")
st.subheader("📊 訊號線內部電流密度分佈動態視覺化")

# 建立橫向坐標軸 (避開邊緣奇異點，x 範圍從 -W/2 到 +W/2)
x = np.linspace(-w_m/2 * 0.999, w_m/2 * 0.999, 500)

# 根據倫敦麥克米倫公式計算局部電流密度 J(x)
jx = ic_real / (np.pi * t_m * np.sqrt((w_m/2)**2 - x**2))
jx_a_cm2 = jx / 1e4 # 轉為 A/cm^2

# 繪製圖表
fig, ax = plt.subplots(figsize=(7, 3.5))
ax.plot(x * 1e6, jx_a_cm2 / 1e6, color='#FF4B4B', linewidth=2.5, label="Local Current Density $J(x)$")
ax.axhline(jd_a_cm2 / 1e6, color='black', linestyle='--', alpha=0.7, label="Depairing Limit $J_d$")

# 圖表美化設定
ax.set_title(f"Current Crowding Effect (W={w}μm, t={t}nm)", fontsize=10, fontweight='bold')
ax.set_xlabel("Position across trace width $x$ ($\mu$m)", fontsize=9)
ax.set_ylabel("Current Density ($MA/cm^2$)", fontsize=9)
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend(fontsize=8, loc='upper center')
ax.set_ylim(0, jd_a_cm2 / 1e6 * 1.2)

# 在 Streamlit 中渲染圖表
st.pyplot(fig)

st.caption("💡 觀察：當您在側邊欄放大『線寬 W』時，雖然通道能承載的總電流 $I_c$ 變大，但中央凹陷會更深，代表邊緣擠壓效應越明顯。")
