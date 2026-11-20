from streamlit import columns, divider, expander, pyplot, set_page_config, sidebar, title, write, subheader, slider, number_input
from matplotlib.pyplot import subplots
from numpy import abs, exp, linspace, log10, pi, sqrt
#import streamlit as st
#import numpy as np
#import pandas as pd
#import matplotlib.pyplot as plt
# 頁面配置
set_page_config(page_title="Cri/oFlex NbTi 超導串擾模擬", layout="wide")
with sidebar:
  title("❄️ NbTi 超導傳輸線：動力學電感與串擾模擬 (20mK)")
  # --- 側邊欄參數設定
  subheader("1. 幾何結構參數")
  w = slider("線寬 w (um)", 10, 100, 50)
  d = slider("超導層厚度 d (nm)", 50, 500, 100)
  s = slider("線間距 s (um)", 20, 200, 100)
  length = slider("線路長度 (m)", 0.1, 1.0, 0.2)
  subheader("2. 超導物理參數 (NbTi)")
  lambda_L = slider("倫敦穿透深度 λL (nm)", 150, 300, 200)
  er = number_input("介電常數 (Polyimide)", value=3.4)
def simulate_cryo_xtalk(): # --- 物理計算引擎 ---
    f = linspace(0.1, 20, 200) # 0.1 to 20 GHz
    omega = 2 * pi * f * 1e9
    # A. 電感計算 (單位: H/m)
    mu0 = 4 * pi * 1e-7
    e0 = 8.854e-12
    # 幾何自感 (簡化模型)
    L_geo = mu0 * (0.5) # 假設值，實際需依結構調整
    # 動力學電感 Lk (NbTi 修正項)
    L_k = (mu0 * (lambda_L*1e-9)**2) / ((w*1e-6) * (d*1e-9))
    L_total = L_geo + L_k
    # 自容 C (單位: F/m)
    C = (e0 * er * (w*1e-6)) / (10e-6) # 假設介電層厚度 10um
    # B. 耦合項 (Lm, Cm)
    # 互感 Lm 與互容 Cm 隨距離 s 指數衰減
    coupling_factor = exp(-s / 50)
    L_m = L_geo * 0.1 * coupling_factor
    C_m = C * 0.1 * coupling_factor
    # C. 阻抗與速度
    Z0 = sqrt(L_total / C)
    v = 1 / sqrt(L_total * C)
    # D. 串擾公式 (頻域)
    # NEXT (近端): 1/4 * (Lm/L + Cm/C) * Sinusoidal factor (簡化為線性增加)
    next_mag = (omega * length / (2 * Z0)) * (L_m + C_m * Z0**2)
    next_db = 20 * log10(next_mag + 1e-12)
    # FEXT (遠端): 1/2v * (Cm/C - Lm/L) * omega * length
    # 非均勻介質導致 Cm/C != Lm/L
    fext_coef = (1 / (2 * v)) * (C_m / C - L_m / L_total)
    fext_mag = omega * length * fext_coef
    fext_db = 20 * log10(abs(fext_mag) + 1e-12)
    return f, next_db, fext_db, L_k, L_geo, Z0
f, next_db, fext_db, L_k, L_geo, Z0 = simulate_cryo_xtalk()
# --- 儀表板顯示 ---
col1, col2, col3 = columns(3)
col1.metric("動力學電感 Lk", f"{L_k*1e6:.2f} μH/m")
col2.metric("幾何電感 Lgeo", f"{L_geo*1e6:.2f} μH/m")
col3.metric("特性阻抗 Z0", f"{Z0:.2f} Ω")
divider()
# 圖表顯示
fig, ax = subplots(figsize=(10, 5))
ax.plot(f, next_db, label='NEXT (Near-End)', color='#FF4B4B', linewidth=2)
ax.plot(f, fext_db, label='FEXT (Far-End)', color='#1C83E1', linestyle='--', linewidth=2)
ax.set_title(f"Crosstalk Analysis for NbTi @ 20mK (Length={length}m)", fontsize=14)
ax.set_xlabel("Frequency (GHz)")
ax.set_ylabel("Crosstalk Magnitude (dB)")
ax.set_ylim([-100, -10])
ax.grid(True, alpha=0.3)
ax.legend()
pyplot(fig)
# 物理意義說明
with expander("🔍 物理參數解析"):
    write(f"""
    1. **動力學電感 ($L_k$) 的影響**：在當前設定下，$L_k$ 佔總電感的 **{ (L_k/(L_k+L_geo))*100 :.1f}%**。這會降低信號傳播速度並提高阻抗 $Z_0$。
    2. **超導特性**：模擬假設 $R=0$。在極低溫下，損耗極低導致串擾隨頻率上升的斜率非常陡峭。
    3. **FEXT 抵消**：如果介質完全均勻，FEXT 曲線會顯著下降。目前的數值反映了 Cri/oFlex 在 Polyimide 介質中的非對稱性。
    """)
