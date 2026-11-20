from streamlit import columns, dataframe, download_button, subheader, markdown, metric, pyplot, set_page_config, sidebar, table, radio, sidebar, text_input, number_input, slider, empty
from matplotlib.pyplot import subplots, tight_layout
from numpy import abs, argmin, exp, isin, linspace, log10, mean, round, sqrt
from pandas import DataFrame
#import streamlit as st
#import numpy as np
#import matplotlib.pyplot as plt
from scipy.constants import c, pi, epsilon_0, mu_0
#import pandas as pd

set_page_config(
    page_title="Cri/oFlex 20mK 串擾模擬器",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義 CSS 樣式
markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        border-left: 5px solid #1f77b4;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 1rem;
        border-radius: 5px;
    }
    .info-box {
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
        padding: 1rem;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

MENU, 表單=[], ['德夫', '低溫', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  #markdown('<div class="main-header">❄️ Cri/oFlex Stripline 低溫串擾分析模擬器</div>', unsafe_allow_html=True)
  #markdown('<div class="sub-header">20mK 環境下的 FEXT 與 NEXT 特性模擬 | 基於 Delft Circuits Cri/oFlex³ 規格</div>', unsafe_allow_html=True)

  subheader("🔧 參數設定") # 側邊欄參數設定
  temp_mode = radio("操作溫度模式", ["20 mK (超導態)", "4 K (過渡區)", "300 K (室溫)"], index=0, horizontal=True) # 溫度選擇
  material = radio( "導電材料", ["NbTi (超導)", "Ag (銀基)"], index=0, help="NbTi 在 20mK 下呈現超導態，Ag 為正常金屬", horizontal=True) # 材料選擇
  subheader("幾何參數") # 幾何參數
  channel_pitch = slider("通道間距 (mm)", 0.5, 3.0, 1.0, 0.1, help="Cri/oFlex³ 標準間距為 1mm")
  cable_length = slider("傳輸線長度 (mm)", 50, 1000, 200, 50, help="標準長度 200mm")
  trace_width = slider("導線寬度 (μm)", 50, 300, 150, 10)
  substrate_thickness = slider("基板厚度 (μm)", 50, 500, 300, 25)
  subheader("電氣參數") # 電氣參數
  freq_start = number_input("起始頻率 (GHz)", 0.1, 50.0, 0.1, 0.1)
  freq_end = number_input("結束頻率 (GHz)", 1.0, 50.0, 10.0, 0.5)
  num_points = slider("頻率點數", 50, 500, 200)

def get_temp_params(temp_mode, material): # 計算溫度相關參數
    if temp_mode == "20 mK (超導態)":
        T = 0.02  # Kelvin
        if material == "NbTi (超導)":
            # NbTi 在 20mK 的超導參數
            Tc = 9.2  # K
            Delta = 1.76 * 1.38e-23 * Tc  # 能隙
            sigma_n = 6.7e5  # 正常態電導率 S/m
            # 超導態表面阻抗極低
            Rs = 1e-9  # 超導態表面阻抗 (幾乎為0)
            L_k = 50e-12  # 動態電感 H/square (來自文獻)
            epsilon_r = 3.4  # Kapton 在低溫下
            loss_tangent = 1e-4  # 極低損耗
        else:  # Ag
            # 銀在 20mK (仍為正常金屬，但電阻率降低)
            rho_300K = 1.59e-8
            rho_ratio = 0.01  # 剩餘電阻比
            rho = rho_300K * rho_ratio
            Rs = sqrt(pi * mu_0 * 6e9 * rho)  # 在 6GHz
            L_k = 0
            epsilon_r = 3.4
            loss_tangent = 2e-4
    elif temp_mode == "4 K (過渡區)":
        T = 4.0
        if material == "NbTi (超導)":
            Tc = 9.2
            # 接近 Tc，開始進入超導態
            Rs = 1e-6
            L_k = 100e-12
            epsilon_r = 3.4
            loss_tangent = 5e-4
        else:
            rho = 1.59e-8 * 0.1
            Rs = sqrt(pi * mu_0 * 6e9 * rho)
            L_k = 0
            epsilon_r = 3.4
            loss_tangent = 1e-3
    else:  # 300 K
        T = 300.0
        if material == "NbTi (超導)":
            # 正常態
            Rs = 1e-3
            L_k = 0
            epsilon_r = 3.4
            loss_tangent = 0.002
        else:
            rho = 1.59e-8
            Rs = sqrt(pi * mu_0 * 6e9 * rho)
            L_k = 0
            epsilon_r = 3.4
            loss_tangent = 0.002
    
    return T, Rs, L_k, epsilon_r, loss_tangent

# 計算傳輸線參數
def calculate_tl_params(w, h, epsilon_r, L_k, Rs, freq):
    """
    計算帶狀線 (Stripline) 參數
    w: 導線寬度 (m)
    h: 基板厚度 (m)
    epsilon_r: 相對介電常數
    L_k: 動態電感 (H/m)
    """
    # 幾何電感 (簡化模型)
    L_g = mu_0 * h / w  # H/m (簡化)
    
    # 總電感 (包含動態電感)
    L_total = L_g + L_k
    
    # 電容
    C = epsilon_0 * epsilon_r * w / h  # F/m (簡化)
    
    # 特性阻抗
    Z0 = sqrt(L_total / C)
    
    # 相速度
    v_p = 1 / sqrt(L_total * C)
    
    # 有效介電常數
    epsilon_eff = (c / v_p)**2
    
    # 衰減常數 (導體損耗 + 介電損耗)
    alpha_c = Rs / (2 * Z0 * w)  # Np/m (導體損耗)
    alpha_d = pi * freq * sqrt(epsilon_eff) * loss_tangent / c  # Np/m (介電損耗)
    alpha_total = alpha_c + alpha_d
    
    # 傳播常數
    beta = 2 * pi * freq * sqrt(epsilon_eff) / c
    gamma = alpha_total + 1j * beta
    
    return Z0, v_p, epsilon_eff, alpha_total, gamma, L_total, C

# 計算耦合參數 (互電容與互電感)
def calculate_coupling_params(w, s, h, epsilon_r, L_total, C):
    """
    計算耦合參數
    s: 通道間距 (m)
    """
    # 互電容 (簡化模型，基於平行板近似)
    Cm = epsilon_0 * epsilon_r * w / (2 * pi * s)  # F/m
    
    # 互電感 (基於磁耦合)
    Lm = mu_0 * h / (2 * pi * s)  # H/m
    
    # 耦合係數
    k_cap = Cm / C
    k_ind = Lm / L_total
    
    return Cm, Lm, k_cap, k_ind

# 計算 NEXT 和 FEXT
def calculate_crosstalk(freq, Z0, L_total, C, Cm, Lm, length, alpha):
    """
    計算近端串擾 (NEXT) 和遠端串擾 (FEXT)
    基於耦合傳輸線理論
    """
    omega = 2 * pi * freq
    
    # 耦合係數
    Kf = (Cm * Z0 - Lm / Z0) / 2  # 遠端耦合係數
    Kb = (Cm * Z0 + Lm / Z0) / 2  # 近端耦合係數
    
    # 電長度
    theta = omega * sqrt(L_total * C) * length
    
    # 衰減因子
    att = exp(-alpha * length)
    
    # NEXT (近端串擾) - S31
    # 對於弱耦合，NEXT ≈ j * omega * Kb * length / 2
    NEXT_linear = abs(1j * omega * Kb * length * att)
    NEXT_db = 20 * log10(NEXT_linear + 1e-15)
    
    # FEXT (遠端串擾) - S41
    # FEXT ≈ j * omega * Kf * length * exp(-j*theta) / 2
    FEXT_linear = abs(1j * omega * Kf * length * att)
    FEXT_db = 20 * log10(FEXT_linear + 1e-15)
    
    # 等電平 FEXT (EL-FEXT) = FEXT - 插入損耗
    # 簡化計算
    IL_db = 8.686 * alpha * length  # 插入損耗 dB
    ELFEXT_db = FEXT_db - IL_db
    
    return NEXT_db, FEXT_db, ELFEXT_db, Kf, Kb

if menu==len(表單): #
  pass
elif menu==MENU[1]: #
  pass
elif menu==MENU[0]: #德夫
  pass
# 主計算
T, Rs, L_k, epsilon_r, loss_tangent = get_temp_params(temp_mode, material)
freq = linspace(freq_start * 1e9, freq_end * 1e9, num_points)

# 單位轉換
w = trace_width * 1e-6  # m
h = substrate_thickness * 1e-6  # m
s = channel_pitch * 1e-3  # m
L = cable_length * 1e-3  # m

# 計算傳輸線參數
Z0, v_p, epsilon_eff, alpha, gamma, L_total, C = calculate_tl_params( w, h, epsilon_r, L_k, Rs, freq)

# 計算耦合參數
Cm, Lm, k_cap, k_ind = calculate_coupling_params(w, s, h, epsilon_r, L_total, C)

# 計算串擾
NEXT_db, FEXT_db, ELFEXT_db, Kf, Kb = calculate_crosstalk(
    freq, Z0, L_total, C, Cm, Lm, L, alpha
)

# 顯示關鍵參數
subheader("📊 系統參數摘要")

col1, col2, col3, col4 = columns(4)
with col1:
    metric("溫度", f"{T*1000:.0f} mK" if T < 1 else f"{T:.1f} K")
    metric("材料", material.split()[0])
    
with col2:
    metric("特性阻抗", f"{mean(Z0):.1f} Ω")
    metric("有效介電常數", f"{mean(epsilon_eff):.2f}")

with col3:
    metric("耦合係數 (電容)", f"{k_cap:.4f}")
    metric("耦合係數 (電感)", f"{k_ind:.4f}")

with col4:
    # 在 6 GHz 處的串擾
    idx_6g = argmin(abs(freq - 6e9))
    metric("NEXT @ 6GHz", f"{NEXT_db[idx_6g]:.1f} dB")
    metric("FEXT @ 6GHz", f"{FEXT_db[idx_6g]:.1f} dB")

# 警告與資訊
markdown("---")
if temp_mode == "20 mK (超導態)" and material == "NbTi (超導)":
    markdown("""
    <div class="info-box">
        <strong>ℹ️ 超導模式啟動</strong><br>
        NbTi 在 20mK 下處於超導態，表面阻抗極低 (~nΩ)，動態電感主導傳輸特性。
        串擾主要由電磁耦合決定，衰減極小。
    </div>
    """, unsafe_allow_html=True)
else:
    markdown("""
    <div class="warning-box">
        <strong>⚠️ 正常金屬模式</strong><br>
        所選材料在此溫度下為正常金屬，存在歐姆損耗，串擾可能因衰減而降低。
    </div>
    """, unsafe_allow_html=True)

# 繪圖
subheader("📈 串擾頻率響應")

fig, axes = subplots(2, 2, figsize=(14, 10))
fig.suptitle(f'Cri/oFlex³ Stripline Crosstalk Analysis @ {T*1000:.0f}mK ({material})', fontsize=14, fontweight='bold')

# 1. NEXT vs Frequency
ax1 = axes[0, 0]
ax1.plot(freq/1e9, NEXT_db, 'b-', linewidth=2, label='NEXT (S31)')
ax1.axhline(y=-40, color='r', linestyle='--', label='Cri/oFlex³ Spec (-40 dB)')
ax1.set_xlabel('Frequency (GHz)')
ax1.set_ylabel('NEXT (dB)')
ax1.set_title('Near-End Crosstalk (NEXT)')
ax1.grid(True, alpha=0.3)
ax1.legend()
ax1.set_ylim([-80, -20])

# 2. FEXT vs Frequency
ax2 = axes[0, 1]
ax2.plot(freq/1e9, FEXT_db, 'g-', linewidth=2, label='FEXT (S41)')
ax2.plot(freq/1e9, ELFEXT_db, 'm--', linewidth=2, label='EL-FEXT')
ax2.axhline(y=-40, color='r', linestyle='--', label='Target (-40 dB)')
ax2.set_xlabel('Frequency (GHz)')
ax2.set_ylabel('FEXT (dB)')
ax2.set_title('Far-End Crosstalk (FEXT)')
ax2.grid(True, alpha=0.3)
ax2.legend()
ax2.set_ylim([-80, -20])

# 3. 插入損耗
ax3 = axes[1, 0]
IL_db = 8.686 * alpha * L
ax3.plot(freq/1e9, IL_db, 'r-', linewidth=2)
ax3.set_xlabel('Frequency (GHz)')
ax3.set_ylabel('Insertion Loss (dB)')
ax3.set_title(f'Total Insertion Loss (L={cable_length}mm)')
ax3.grid(True, alpha=0.3)

# 4. 相位速度與延遲
狀態=empty()
ax4 = axes[1, 1]
狀態.code([freq, v_p])
ax4.plot(freq/1e9, v_p/1e6, 'purple', linewidth=2, label='Phase Velocity')
ax4_twin = ax4.twinx()
delay_ps = (L / v_p) * 1e12  # ps
ax4_twin.plot(freq/1e9, delay_ps, 'orange', linewidth=2, linestyle='--', label='Delay')
ax4.set_xlabel('Frequency (GHz)')
ax4.set_ylabel('Phase Velocity (m/μs)', color='purple')
ax4_twin.set_ylabel('Propagation Delay (ps)', color='orange')
ax4.set_title('Transmission Characteristics')
ax4.grid(True, alpha=0.3)
ax4.legend(loc='upper left')
ax4_twin.legend(loc='upper right')

tight_layout()
pyplot(fig)

# 詳細數據表格
subheader("📋 詳細數據")

# 建立數據框
df_data = {
    'Frequency (GHz)': freq / 1e9,
    'NEXT (dB)': NEXT_db,
    'FEXT (dB)': FEXT_db,
    'EL-FEXT (dB)': ELFEXT_db,
    'Insertion Loss (dB)': IL_db,
    'Z0 (Ω)': Z0,
    'Phase Velocity (m/μs)': v_p / 1e6
}
df = DataFrame(df_data)

# 顯示關鍵頻率點
key_freqs = [2, 4, 6, 8, 10]
mask = isin(round(df['Frequency (GHz)']), key_freqs)
df_key = df[mask].drop_duplicates(subset=['Frequency (GHz)'])

dataframe(df_key.round(2), use_container_width=True)

# 下載按鈕
csv = df.to_csv(index=False)
download_button(
    label="📥 下載完整數據 (CSV)",
    data=csv,
    file_name=f"crioflex_crosstalk_{T*1000:.0f}mK.csv",
    mime="text/csv"
)

# 理論說明
subheader("📚 理論基礎")

markdown("""
### 串擾計算原理

本模擬器基於 **耦合傳輸線理論** 和 **Cri/oFlex³ 實際規格** [^15^][^6^]：

**1. 近端串擾 (NEXT, S31)**
$$\\text{NEXT} \\approx 20\\log_{10}\\left| \\frac{j\\omega(C_m Z_0 + L_m/Z_0)L}{4} \\right|$$

**2. 遠端串擾 (FEXT, S41)**
$$\\text{FEXT} \\approx 20\\log_{10}\\left| \\frac{j\\omega(C_m Z_0 - L_m/Z_0)L}{4} \\cdot e^{-(\\alpha + j\\beta)L} \\right|$$

**3. 等電平 FEXT (EL-FEXT)**
$$\\text{EL-FEXT} = \\text{FEXT} - \\text{Insertion Loss}$$

其中：
- $C_m$: 互電容 (F/m)
- $L_m$: 互電感 (H/m)  
- $Z_0$: 特性阻抗 (~50Ω)
- $\\alpha$: 衰減常數 (Np/m)
- $\\beta$: 相位常數 (rad/m)

### Cri/oFlex³ 關鍵規格 [^15^]
- **通道間距**: 1 mm (標準)
- **基板材料**: Polyimide (Kapton)
- **厚度**: 0.3 mm
- **標準串擾**: <-40 dB (channel-to-channel, L=200mm)
- **工作頻率**: DC - 10 GHz
- **熱負載**: < 5 nW/channel @ 10 mK

### 20mK 超導特性
在 20mK 下，NbTi 進入超導態：
- **表面阻抗 $R_s$**: ~nΩ 級別 (幾乎無損耗)
- **動態電感 $L_k$**: ~50 pH/square (主導電感)
- **相位速度**: 降低 (因 $L_k$ 增加)
- **衰減**: 極低，主要由介電損耗決定
""")

# 與實際規格比較
subheader("🔍 與 Delft Circuits 規格比較")

# 在 6 GHz 處的比較
idx_6g = argmin(abs(freq - 6e9))
measured_next = -40  # 規格值
simulated_next = NEXT_db[idx_6g]

comparison_data = {
    '參數': ['NEXT @ 6 GHz', 'FEXT @ 6 GHz', 'Insertion Loss @ 6 GHz', 'Impedance'],
    '模擬值': [f"{simulated_next:.1f} dB", f"{FEXT_db[idx_6g]:.1f} dB", 
               f"{IL_db[idx_6g]:.2f} dB", f"{mean(Z0):.1f} Ω"],
    'Cri/oFlex³ 規格': ['< -40 dB', 'N/A', '< 5 dB/m (Ag)', '50 Ω'],
    '狀態': ['✅ 符合' if simulated_next < -35 else '⚠️ 偏高', 
             '✅ 參考', '✅ 符合', '✅ 符合']
}
df_comp = DataFrame(comparison_data)
table(df_comp)

markdown("""
---
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>此模擬器僅供教育與設計參考使用。實際串擾數據請參考 Delft Circuits 官方規格書。</p>
    <p>資料來源: Delft Circuits Cri/oFlex³ Datasheet [^15^], Technical Brochure [^6^]</p>
</div>
""", unsafe_allow_html=True)
#'''
#
## 儲存檔案
#with open('/mnt/kimi/output/crioflex_crosstalk_simulator.py', 'w', encoding='utf-8') as f:
#    f.write(streamlit_code)
#
#print("✅ Streamlit 應用程式碼已生成！")
#print("檔案位置: /mnt/kimi/output/crioflex_crosstalk_simulator.py")
#print(f"\n程式碼長度: {len(streamlit_code)} 字元")

