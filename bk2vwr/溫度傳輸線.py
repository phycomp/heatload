import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 使用非交互式後端

# 設置頁面
st.set_page_config(page_title="傳輸線阻抗與材料特性模藕", layout="wide")
st.title("傳輸線阻抗與材料物理特性相關性模藕")
st.markdown("""
本應用模藕傳輸線特性阻抗與材料物理特性（特別是介電常數與溫度的關系）在不同溫度條件下的變化。
""")

# 側邊欄 - 輸入參數
st.sidebar.header("傳輸線參數")

# 材料選擇
material = st.sidebar.selectbox(
    "基板材料",
    ("FR-4", "Rogers RO4350B", "Teflon", "Alumina", "自定義")
)

# 基本傳輸線參數
frequency = st.sidebar.slider("頻率 (GHz)", 1.0, 100.0, 10.0, 0.1)
width = st.sidebar.slider("線寬 (mm)", 0.1, 5.0, 1.0, 0.1)
height = st.sidebar.slider("基板厚度 (mm)", 0.1, 5.0, 1.6, 0.1)
thickness = st.sidebar.slider("導體厚度 (μm)", 1.0, 100.0, 35.0, 1.0)

# 溫度範圍
temp_min = st.sidebar.slider("最低溫度 (°C)", -100, 0, -40, 5)
temp_max = st.sidebar.slider("最高溫度 (°C)", 0, 200, 125, 5)

# 材料特性與溫度的關系函數
def dielectric_constant_vs_temp(material, temp):
    """根據材料和溫度返回介電常數"""
    # 常溫參考值 (25°C)
    if material == "FR-4":
        er_ref = 4.5
        temp_coef = -150e-6  # 溫度系數 (1/°C)
    elif material == "Rogers RO4350B":
        er_ref = 3.48
        temp_coef = -50e-6
    elif material == "Teflon":
        er_ref = 2.1
        temp_coef = -200e-6
    elif material == "Alumina":
        er_ref = 9.8
        temp_coef = 100e-6
    else:  # 自定義
        er_ref = st.sidebar.slider("常溫介電常數", 1.0, 20.0, 4.0, 0.1)
        temp_coef = st.sidebar.slider("溫度系數 (ppm/°C)", -500, 500, -150, 10) * 1e-6
    
    # 計算當前溫度下的介電常數
    er = er_ref * (1 + temp_coef * (temp - 25))
    return er

def loss_tangent_vs_temp(material, temp):
    """根據材料和溫度返回損耗角正切"""
    # 常溫參考值 (25°C)
    if material == "FR-4":
        tan_d_ref = 0.02
        temp_coef = 0.0005  # 溫度系數
    elif material == "Rogers RO4350B":
        tan_d_ref = 0.0037
        temp_coef = 0.0001
    elif material == "Teflon":
        tan_d_ref = 0.0002
        temp_coef = 0.00005
    elif material == "Alumina":
        tan_d_ref = 0.0001
        temp_coef = 0.00002
    else:  # 自定義
        tan_d_ref = st.sidebar.slider("常溫損耗角正切", 0.0001, 0.05, 0.02, 0.001)
        temp_coef = st.sidebar.slider("損耗角溫度系數", 0.00001, 0.001, 0.0005, 0.00001)
    
    # 計算當前溫度下的損耗角正切
    tan_d = tan_d_ref + temp_coef * (temp - 25)
    return max(tan_d, 1e-6)  # 確保不爲負

# 微帶線特性阻抗計算
def microstrip_impedance(w, h, er, t=0.035):
    """
    計算微帶線特性阻抗
    w: 線寬 (mm)
    h: 基板厚度 (mm)
    er: 相對介電常數
    t: 導體厚度 (mm)
    """
    # 轉換爲米
    w_m = w * 1e-3
    h_m = h * 1e-3
    t_m = t * 1e-3
    
    # 有效介電常數
    if w_m/h_m > 1:
        ereff = (er + 1)/2 + (er - 1)/(2*np.sqrt(1 + 12*h_m/w_m))
    else:
        ereff = (er + 1)/2 + (er - 1)/2 * (1/np.sqrt(1 + 12*h_m/w_m) + 0.04*(1 - w_m/h_m)**2)
    
    # 特性阻抗
    if w_m/h_m > 1:
        Z0 = 120*np.pi / (w_m/h_m + 1.393 + 2/3*np.log(w_m/h_m + 1.444)) / np.sqrt(ereff)
    else:
        Z0 = 60/np.sqrt(ereff) * np.log(8*h_m/w_m + w_m/(4*h_m))
    
    return Z0, ereff

# 計算不同溫度下的特性
def calculate_temperature_effects(temp_range, material, width, height, thickness):
    impedances = []
    dielectric_constants = []
    loss_tangents = []
    effective_er = []
    
    for temp in temp_range:
        er = dielectric_constant_vs_temp(material, temp)
        tan_d = loss_tangent_vs_temp(material, temp)
        Z0, ereff = microstrip_impedance(width, height, er, thickness/1000)  # 轉換爲mm
        
        impedances.append(Z0)
        dielectric_constants.append(er)
        loss_tangents.append(tan_d)
        effective_er.append(ereff)
    
    return impedances, dielectric_constants, loss_tangents, effective_er

# 主程序
if st.sidebar.button("開始模擬"):
    # 生成溫度範圍
    temp_range = np.linspace(temp_min, temp_max, 100)
    
    # 計算不同溫度下的特性
    impedances, dielectric_constants, loss_tangents, effective_er = calculate_temperature_effects(
        temp_range, material, width, height, thickness
    )
    
    # 創建圖表
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    
    # 特性阻抗 vs 溫度
    ax1.plot(temp_range, impedances, 'b-', linewidth=2)
    ax1.set_xlabel('溫度 (°C)')
    ax1.set_ylabel('特性阻抗 (Ω)')
    ax1.set_title('特性阻抗 vs 溫度')
    ax1.grid(True, alpha=0.3)
    
    # 介電常數 vs 溫度
    ax2.plot(temp_range, dielectric_constants, 'r-', linewidth=2)
    ax2.set_xlabel('溫度 (°C)')
    ax2.set_ylabel('介電常數')
    ax2.set_title('介電常數 vs 溫度')
    ax2.grid(True, alpha=0.3)
    
    # 損耗角正切 vs 溫度
    ax3.plot(temp_range, loss_tangents, 'g-', linewidth=2)
    ax3.set_xlabel('溫度 (°C)')
    ax3.set_ylabel('損耗角正切')
    ax3.set_title('損耗角正切 vs 溫度')
    ax3.grid(True, alpha=0.3)
    ax3.set_yscale('log')  # 使用對數坐標
    
    # 有效介電常數 vs 溫度
    ax4.plot(temp_range, effective_er, 'm-', linewidth=2)
    ax4.set_xlabel('溫度 (°C)')
    ax4.set_ylabel('有效介電常數')
    ax4.set_title('有效介電常數 vs 溫度')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # 顯示特定溫度點的數值
    st.subheader("特定溫度點的參數值")
    
    # 選擇特定溫度點
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**低溫**")
        low_temp = temp_min
        idx_low = np.argmin(np.abs(temp_range - low_temp))
        st.write(f"溫度: {low_temp}°C")
        st.write(f"特性阻抗: {impedances[idx_low]:.2f} Ω")
        st.write(f"介電常數: {dielectric_constants[idx_low]:.3f}")
        st.write(f"損耗角正切: {loss_tangents[idx_low]:.6f}")
        st.write(f"有效介電常數: {effective_er[idx_low]:.3f}")
    
    with col2:
        st.markdown("**常溫**")
        room_temp = 25
        idx_room = np.argmin(np.abs(temp_range - room_temp))
        st.write(f"溫度: {room_temp}°C")
        st.write(f"特性阻抗: {impedances[idx_room]:.2f} Ω")
        st.write(f"介電常數: {dielectric_constants[idx_room]:.3f}")
        st.write(f"損耗角正切: {loss_tangents[idx_room]:.6f}")
        st.write(f"有效介電常數: {effective_er[idx_room]:.3f}")
    
    with col3:
        st.markdown("**高溫**")
        high_temp = temp_max
        idx_high = np.argmin(np.abs(temp_range - high_temp))
        st.write(f"溫度: {high_temp}°C")
        st.write(f"特性阻抗: {impedances[idx_high]:.2f} Ω")
        st.write(f"介電常數: {dielectric_constants[idx_high]:.3f}")
        st.write(f"損耗角正切: {loss_tangents[idx_high]:.6f}")
        st.write(f"有效介電常數: {effective_er[idx_high]:.3f}")
    
    # 顯示參數變化百分比
    st.subheader("溫度變化引起的參數變化")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        delta_Z0 = ((impedances[idx_high] - impedances[idx_low]) / impedances[idx_room]) * 100
        st.metric("特性阻抗變化", f"{delta_Z0:.2f}%")
    
    with col2:
        delta_er = ((dielectric_constants[idx_high] - dielectric_constants[idx_low]) / dielectric_constants[idx_room]) * 100
        st.metric("介電常數變化", f"{delta_er:.2f}%")
    
    with col3:
        delta_tan_d = ((loss_tangents[idx_high] - loss_tangents[idx_low]) / loss_tangents[idx_room]) * 100
        st.metric("損耗角正切變化", f"{delta_tan_d:.2f}%")

else:
    st.info("請在左側邊欄設置參數，然後點擊**開始模擬**按鈕。")

# 添加說明
st.sidebar.markdown("---")
st.sidebar.markdown("""
### 說明
- **特性阻抗**: 傳輸線的特征阻抗，受介電常數和幾何尺寸影響
- **介電常數**: 材料儲存電能的能力，通常隨溫度變化
- **損耗角正切**: 材料損耗的度量，通常隨溫度升高而增加
- **有效介電常數**: 考慮微帶線結構後的實際介電常數
""")
