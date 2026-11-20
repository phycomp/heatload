from streamlit import caption, columns, dataframe, download_button, expander, subheader, markdown, pyplot, set_page_config, sidebar, success, warning, radio, text_input, empty, slider, number_input
from matplotlib.pyplot import subplots, tight_layout
from numpy import abs, argmin, exp, isin, linspace, log10, mean, round, sinc, sqrt
from pandas import DataFrame
#"""
#Cri/oFlex 20mK 串擾模擬器 (精簡版)
#Streamlit 應用程式 - 分析超導傳輸線在極低溫下的 NEXT/FEXT 特性
#"""

#import streamlit as st
#import numpy as np
#import matplotlib.pyplot as plt
from scipy.constants import c, pi, epsilon_0, mu_0, k as k_B
#import pandas as pd

# 頁面設定
set_page_config(page_title="Cri/oFlex 20mK 串擾模擬器", page_icon="❄️", layout="wide")

markdown("""
<style>
.main-header { font-size: 2.2rem; font-weight: bold; color: #1f77b4; text-align: center; }
.metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; 
               border-radius: 10px; padding: 1rem; text-align: center; }
</style>
""", unsafe_allow_html=True)

#markdown('<div class="main-header">❄️ Cri/oFlex Stripline 低溫串擾分析模擬器</div>', unsafe_allow_html=True)
#markdown("<p style='text-align: center; color: 666;'>20mK 環境下的 FEXT 與 NEXT 特性模擬</p>", unsafe_allow_html=True)

# ==================== 物理計算函數 ====================

def get_material_params(T, material):
    """取得材料在溫度 T 下的參數"""
    if material == "NbTi":
        Tc = 9.2
        if T < Tc:
            # 超導態: 動態電感主導
            L_k = 50e-12 * (1 + (T/Tc)**2)  # H/m, 溫度修正
            Rs = 1e-9 * (T/0.02)  # Ω, 極低表面阻抗
            loss_tan = 1e-4
        else:
            L_k = 0
            Rs = 1e-3  # 正常態
            loss_tan = 0.002
    else:  # Ag
        L_k = 0
        rho = 1.59e-8 * (0.01 if T < 10 else 1)  # 低溫剩餘電阻
        Rs = sqrt(pi * mu_0 * 6e9 * rho)
        loss_tan = 2e-4 if T < 10 else 0.002
    return Rs, L_k, loss_tan

def calculate_tl_params(w, h, s, eps_r, L_k, Rs, freq):
    """計算傳輸線參數"""
    # 電感與電容
    L_g = mu_0 * h / w  # 幾何電感
    總電感 = L_g + L_k  # 總電感(含動態電感)
    C = epsilon_0 * eps_r * w / h  # 電容
    #ε0
    # 特性阻抗與相速度
    Z0 = sqrt(總電感 / C)
    v_p = 1 / sqrt(總電感 * C)
    eps_eff = (c / v_p)**2

    # 衰減 (導體 + 介電)
    alpha_c = Rs / (2 * Z0 * w)
    alpha_d = pi * freq * sqrt(eps_eff) * 1e-4 / c
    alpha = alpha_c + alpha_d

    # 耦合參數 (互電容/電感)
    Cm = epsilon_0 * eps_r * w / (2 * pi * s) * exp(-s/h)
    Lm = mu_0 * h / (2 * pi * s) * exp(-s/h)

    beta = 2 * pi * freq / v_p

    return Z0, v_p, eps_eff, alpha, beta, Cm, Lm, 總電感, C

def calculate_crosstalk(freq, Z0, Cm, Lm, 總電感, C, alpha, beta, length):
    """計算 NEXT 與 FEXT"""
    omega = 2 * pi * freq

    # 耦合係數
    Kf = (Cm * Z0 - Lm/Z0) / 2  # 前向
    Kb = (Cm * Z0 + Lm/Z0) / 2  # 後向

    theta = beta * length
    att = exp(-alpha * length)

    # NEXT: 近端串擾 (S31) - 累積耦合，與長度無關(飽和)
    NEXT_lin = abs(1j * omega * Kb * length * att * sinc(theta/pi))
    近場串擾 = 20 * log10(NEXT_lin + 1e-15)

    # FEXT: 遠端串擾 (S41) - 隨長度增加
    FEXT_lin = abs(1j * omega * Kf * length * att)
    FEXT_db = 20 * log10(FEXT_lin + 1e-15)

    # 插入損耗
    IL_db = -8.686 * alpha * length

    return 近場串擾, FEXT_db, IL_db, Kf, Kb

# ==================== UI 介面 ====================
MENU, 表單=[], ['德夫', '參數', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  subheader("⚙️ 參數設定")

  temp_mode = radio("溫度", ["20 mK", "4 K", "300 K"], index=0, horizontal=True) # 溫度與材料
  material = radio("材料", ["NbTi (超導)", "Ag (銀基)"], index=0, horizontal=True)

  T = 0.02 if temp_mode == "20 mK" else (4.0 if temp_mode == "4 K" else 300.0)
  mat_name = "NbTi" if "NbTi" in material else "Ag"

  subheader("幾何參數") # 幾何參數
  pitch = slider("通道間距 (mm)", 0.5, 5.0, 1.0, 0.1)
  length = slider("長度 (mm)", 50, 1000, 200, 50)
  width = slider("線寬 (μm)", 50, 500, 150, 10)
  thickness = slider("基板厚 (μm)", 50, 500, 300, 25)

  # 頻率
  subheader("頻率範圍")
  f_start = number_input("起始 (GHz)", 0.1, 50.0, 0.1)
  f_end = number_input("結束 (GHz)", 1.0, 50.0, 10.0)
  n_points = slider("點數", 50, 500, 200)

  # ==================== 執行計算 ====================

  # 單位轉換
  w, h, s, L = width*1e-6, thickness*1e-6, pitch*1e-3, length*1e-3
  freq = linspace(f_start*1e9, f_end*1e9, n_points)

  # 取得材料參數
  Rs, L_k, loss_tan = get_material_params(T, mat_name)

  # 計算傳輸線參數
  Z0, v_p, eps_eff, alpha, beta, Cm, Lm, 總電感, C = calculate_tl_params(w, h, s, 3.4, L_k, Rs, freq)
if menu==len(表單): #
  pass
elif menu==MENU[1]: #
  pass
elif menu==MENU[0]: #德夫
  pass

  # 計算串擾
  近場串擾, FEXT_db, IL_db, Kf, Kb = calculate_crosstalk(freq, Z0, Cm, Lm, 總電感, C, alpha, beta, L)

  # 找出 6GHz 索引
  idx_6g = argmin(abs(freq - 6e9))

  # ==================== 結果顯示 ====================

  subheader("📊 關鍵指標")

  cols = columns(5)
  metrics = [
      ("NEXT @ 6G", f"{近場串擾[idx_6g]:.1f} dB"),
      ("FEXT @ 6G", f"{FEXT_db[idx_6g]:.1f} dB"),
      ("阻抗 Z0", f"{mean(Z0):.1f} Ω"),
      ("相速度", f"{mean(v_p)/1e6:.1f} m/μs"),
      ("插入損耗", f"{IL_db[idx_6g]:.3f} dB")
  ]

  for col, (label, value) in zip(cols, metrics):
      col.markdown(f"""
      <div class="metric-card">
          <div style="font-size: 1.6rem; font-weight: bold;">{value}</div>
          <div style="font-size: 0.9rem; opacity: 0.9;">{label}</div>
      </div>
      """, unsafe_allow_html=True)

  # 狀態提示
  if T == 0.02 and mat_name == "NbTi":
      success(f"✅ 超導模式: Lk = {L_k*1e12:.1f} pH/m, Rs ≈ {Rs*1e9:.1f} nΩ")
  else:
      warning(f"⚠️ 正常金屬: Rs = {Rs*1e6:.3f} μΩ")

  # ==================== 圖表 ====================

  狀態=empty()
  subheader("📈 頻率響應")

  fig, axes = subplots(2, 2, figsize=(14, 10))

  # NEXT/FEXT
  ax = axes[0, 0]
  ax.plot(freq/1e9, 近場串擾, 'b-', lw=2.5, label='NEXT (S31)', marker='o', markevery=20)
  ax.plot(freq/1e9, FEXT_db, 'r-', lw=2.5, label='FEXT (S41)', marker='s', markevery=20)
  ax.axhline(-40, color='g', ls='--', lw=2, label='Spec (-40 dB)')
  ax.fill_between(freq/1e9, -100, -40, alpha=0.1, color='green')
  ax.set_xlabel('Frequency (GHz)')
  ax.set_ylabel('Crosstalk (dB)')
  ax.set_title('NEXT vs FEXT')
  ax.legend()
  ax.grid(True, alpha=0.3)
  ax.set_ylim([-80, -20])

  # 插入損耗
  ax = axes[0, 1]
  ax.plot(freq/1e9, IL_db, 'g-', lw=2.5)
  ax.set_xlabel('Frequency (GHz)')
  ax.set_ylabel('Insertion Loss (dB)')
  ax.set_title('Insertion Loss (S21)')
  ax.grid(True, alpha=0.3)

  # 阻抗與相速度
  ax = axes[1, 0]
  狀態.code([freq, Z0])
  ax.plot(freq/1e9, [Z0]*len(freq), 'purple', lw=2.5)
  ax.axhline(50, color='r', ls='--', label='Target 50Ω')
  ax.set_xlabel('Frequency (GHz)')
  ax.set_ylabel('Impedance (Ω)')
  ax.set_title('Characteristic Impedance')
  ax.legend()
  ax.grid(True, alpha=0.3)

  # 耦合係數
  狀態.code([freq, Kb])
  ax = axes[1, 1]
  ax.plot(freq/1e9, [abs(Kb)*1e12]*len(freq), 'b-', lw=2, label='Kb (backward)')
  ax.plot(freq/1e9, [abs(Kf)*1e12]*len(freq), 'r-', lw=2, label='Kf (forward)')
  ax.set_xlabel('Frequency (GHz)')
  ax.set_ylabel('Coupling (ps)')
  ax.set_title('Coupling Coefficients')
  ax.legend()
  ax.grid(True, alpha=0.3)

  tight_layout()
  pyplot(fig)

  # ==================== 數據表 ====================

  subheader("📋 數據表格")

  df = DataFrame({
      'Freq (GHz)': round(freq/1e9, 2),
      'NEXT (dB)': round(近場串擾, 2),
      'FEXT (dB)': round(FEXT_db, 2),
      'IL (dB)': round(IL_db, 3),
      'Z0 (Ω)': round(Z0, 1)
  })

  # 顯示關鍵頻率
  key_freqs = [1, 2, 4, 6, 8, 10]
  df_display = df[isin(df['Freq (GHz)'], key_freqs)].drop_duplicates('Freq (GHz)')
  dataframe(df_display, use_container_width=True)

  # 下載 CSV
  csv = df.to_csv(index=False)
  download_button("📥 下載 CSV", csv, f"crioflex_{T*1000:.0f}mK.csv", "text/csv")

  # ==================== 理論說明 ====================

  with expander("📚 理論公式與說明"):
      markdown("""
      ### 串擾計算公式

      **近端串擾 (NEXT):**

      $$S_{31} \approx 20\log_{10}\left| \frac{j\omega L}{4} \left( \frac{L_m}{Z_0} + C_m Z_0 \right) \text{sinc}\left(\frac{\theta}{\pi}\right) e^{-\alpha L} \right|$$

      **遠端串擾 (FEXT):**

      $$S_{41} \approx 20\log_{10}\left| \frac{j\omega L}{4} \left( C_m Z_0 - \frac{L_m}{Z_0} \right) e^{-j\theta} e^{-\alpha L} \right|$$

      **超導動態電感:**

      $$L_k = \frac{\mu_0 \lambda_L^2}{w \cdot t} \cdot \frac{1}{1-(T/T_c)^4}$$

      ### Cri/oFlex³ 規格

      - 通道間距: 1 mm (標準)
      - NEXT 規格: < -40 dB @ 6GHz, L=200mm
      - 阻抗: 50 Ω
      - 熱負載: < 5 nW/channel @ 10mK
      """, unsafe_allow_html=True)

  markdown("---")
  caption("基於耦合傳輸線理論與超導電路模型 | 僅供參考")
