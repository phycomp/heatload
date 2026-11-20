from streamlit import columns, error, info, metric, pyplot, set_page_config, sidebar, subheader, success, title, radio, number_input, slider
from matplotlib.pyplot import subplots
from numpy import log, pi, real, sqrt
import streamlit as st
# import skrf as skrf
from skrf import Frequency
from skrf.media import MLine, DefinedGammaZ0
import matplotlib.pyplot as plt
import numpy as np
from fontUtil2 import 配置中文
配置中文()

# 網頁基本設定
set_page_config(page_title="PCB 傳輸線物理結構模擬器", layout="wide")
傳輸線類型=["Microstrip (微帶線)", "Stripline (帶狀線)"]
with sidebar:
  # 側邊欄：結構與材料參數輸入
  subheader("🛠️ 材料與幾何結構設定")

  # 選擇傳輸線類型
  類型 = radio("選擇傳輸線結構 (Type)", 傳輸線類型, horizontal=True)

  # 材料基本參數
  subheader("💎 材料特性")
  er = number_input("相對介電常數 (Dk / er)", min_value=1.0, max_value=20.0, value=4.2, step=0.1, help="例如 FR4 約 4.2, Rogers 約 3.5")
  tand = number_input("介質損耗角正切 (Df / tanδ)", min_value=0.000, max_value=0.100, value=0.020, step=0.001, format="%.3f", help="例如 FR4 約 0.02, 低損耗板材約 0.004")
  rho = number_input("導體電阻率 (Copper Rho, Ω·m)", min_value=1e-8, max_value=1e-6, value=1.72e-8, format="%.2e", help="標準純銅約 1.72e-8")

  # 幾何尺寸參數 (單位均轉換為標註單位)
  subheader("📐 幾何尺寸設定")
  w_mm = slider("線寬 w (mm)", min_value=0.05, max_value=3.00, value=0.35, step=0.01)
  h_mm = slider("介質總厚度 h (mm)", min_value=0.10, max_value=3.00, value=0.20, step=0.01, help="對 Microstrip 為線到地層厚度；對 Stripline 為兩地層間的總距離 H")
  t_um = slider("導體/銅厚 t (um)", min_value=10, max_value=100, value=35, step=5, help="1 oz 銅厚約為 35 um")
  length_cm = slider("走線總長度 (cm)", min_value=1.0, max_value=50.0, value=10.0, step=0.5)

  # 頻率範圍設定
  subheader("📶 頻率設定")
  f_start = number_input("起始頻率 (GHz)", min_value=0.1, max_value=100.0, value=1.0, step=0.5)
  f_stop = number_input("終止頻率 (GHz)", min_value=0.1, max_value=100.0, value=20.0, step=0.5)
  f_pts = slider("頻率掃描點數", min_value=50, max_value=1000, value=401, step=50)

# 核心模擬與計算邏輯
def 核心():
    # 建立 scikit-rf 頻率物件
    freq = Frequency(f_start, f_stop, f_pts, unit='GHz')

    # 單位轉換
    w_m = w_mm * 1e-3
    h_m = h_mm * 1e-3
    t_m = t_um * 1e-6
    光速 = 3e8  # 光速

    if 類型==傳輸線類型[0]:   #"Microstrip" in 類型
        # 使用 scikit-rf 內建的 MLine 物理模型
        media = MLine(frequency=freq, w=w_m, h=h_m, t=t_m, ep_r=er, rho=rho, tand=tand)
        # 取得隨頻率變化的特徵阻抗 Z0 (取實部展示)
        z0_calc = real(media.z0[0])

    else:  # Stripline 帶狀線 (採用經典解析與損耗擴展公式)
        # 1. 計算對稱帶狀線特徵阻抗 (IPC-2141 解析式)
        # Z0 = (60 / sqrt(er)) * ln( 4*H / (0.67 * pi * (0.8*W + T)) )
        effective_w = 0.8 * w_m + t_m
        z0_calc = (60.0 / sqrt(er)) * log((4.0 * h_m) / (0.67 * pi * effective_w))

        # 2. 計算衰減常數 (包含介質損耗與隨頻率變化的趨膚效應導體損耗)
        f_arr = freq.f
        # 介質損耗 α_d (Np/m)
        alpha_d = (pi * f_arr * sqrt(er) * tand) / 光速

        # 導體趨膚效應損耗 α_c (Np/m) -> 隨根號頻率增長
        # 趨膚深度 skin_depth = sqrt(rho / (pi * f * mu))
        mu_0 = 4 * pi * 1e-7
        skin_depth = sqrt(rho / (pi * f_arr * mu_0))
        # 經典帶狀線導體損耗估算 (基於電流繞走線四周分布之電阻抗效應)
        r_ac = rho / (2 * (w_m + t_m) * skin_depth)
        alpha_c = r_ac / (2 * z0_calc)

        # 總傳播常數 gamma = alpha + j * beta
        alpha_total = alpha_d + alpha_c
        beta = (2 * pi * f_arr * sqrt(er)) / 光速
        gamma = alpha_total + 1j * beta

        # 使用通用 DefinedGammaZ0 將計算結果橋接至 scikit-rf 網絡
        media = DefinedGammaZ0(frequency=freq, z0=z0_calc, gamma=gamma)

    # 建立指定長度的傳輸線網絡元件 (1 cm = 0.01 m)
    line_network = media.line(length_cm / 100.0, unit='m')

    # 提取正值的 IL 與 RL (dB)
    #il = -line_network.s21_db #.flatten()
    #rl = -line_network.s11_db #.flatten()
    il = -line_network.s21.s_db.flatten()
    rl = -line_network.s11.s_db.flatten()

    # 網頁前端排版展示
    success(f"⚡ 計算完成！當前結構估算特徵阻抗 $Z_0$ ≈ **{z0_calc:.2f} Ω**")

    col1, col2 = columns([1, 3])

    with col1:
        subheader("📊 指標摘要")
        metric(label="估算特徵阻抗 Z0", value=f"{z0_calc:.1f} Ω")
        metric(label="走線總長度", value=f"{length_cm} cm")
        metric(label="最高頻處插入損失 (IL)", value=f"{il[-1]:.2f} dB")
        metric(label="最高頻處回流損失 (RL)", value=f"{rl[-1]:.2f} dB")

        info("""
        💡 **提示：**
        * **IL (插入損失)**：越接近 0dB 損耗越小。
        * **RL (回流損失)**：數值越大（例如 > 20dB）代表反射越小、阻抗匹配越完美。
        """)

    with col2:
        subheader("📈 S 參數響應曲線 (IL / RL)")
        fig, ax = subplots(figsize=(10, 5.5))
        ax.plot(freq.f_scaled, il, label='Insertion Loss (IL)', color='crimson', lw=2.5)
        ax.plot(freq.f_scaled, rl, label='Return Loss (RL)', color='dodgerblue', lw=2.5)

        ax.set_xlabel('Frequency (GHz)', fontsize=11)
        ax.set_ylabel('Loss (dB)', fontsize=11)
        ax.set_title(f'{類型} 模擬結果 ({length_cm}cm)', fontsize=13, fontweight='bold')
        ax.legend(loc='best', frameon=True, shadow=True)
        ax.grid(True, linestyle='--', alpha=0.6)

        # 限制 Y 軸顯示範圍讓圖表更易讀
        ax.set_ylim(bottom=0)

        pyplot(fig)
核心()

#except Exception as e:
#    error(f"模擬計算過程中發生錯誤，請檢查參數設定。錯誤訊息: {e}")
with sidebar:
  subheader("📟 PCB 傳輸線物理結構模擬器 (Microstrip / Stripline)")
