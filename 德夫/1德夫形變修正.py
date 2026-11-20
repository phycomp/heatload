from streamlit import columns, divider, pyplot, set_page_config, sidebar, title, warning, subheader, slider, empty, number_input
from matplotlib.pyplot import subplots
from numpy import abs, exp, linspace, log10, pi, sqrt
#import streamlit as st
#import numpy as np
#import pandas as pd
import matplotlib.pyplot as plt

# 頁面配置
set_page_config(page_title="Cri/oFlex 熱夾具形變模擬", layout="wide")
title("❄️ Cri/oFlex: 熱夾具壓力對 NbTi 串擾之影響")

with sidebar:
  subheader("1. 熱夾具機械壓力") # --- 側邊欄：物理參數 ---
  pressure_mpa = slider("夾具壓力 (MPa)", 0.0, 50.0, 10.0)
  e_modulus = number_input("Polyimide 楊氏模數 (GPa) @ 4K", value=5.0) # 低溫下會變硬

  subheader("2. 原始幾何參數")
  s_init = slider("原始線間距 s (um)", 20, 200, 80)
  h_init = slider("原始介電層厚度 h (um)", 10, 100, 25)
  w = slider("線寬 w (um)", 20, 100, 50)

  subheader("3. 超導修正 (NbTi)")
  lambda_l = 200 # nm
  d_layer = 100  # nm

# --- 計算形變與電磁參數 ---
def calculate_deformed_xtalk():
    # A. 機械形變計算
    strain = (pressure_mpa * 1e6) / (e_modulus * 1e9)
    poisson_ratio = 0.34
    
    h_eff = h_init * (1 - strain)      # 壓縮後的厚度
    s_eff = s_init * (1 - poisson_ratio * strain) # 橫向擴張導致間距縮小
    
    # B. 電磁參數
    mu0 = 4 * pi * 1e-7
    e0 = 8.854e-12
    er = 3.4 * (1 + 0.05 * strain) # 密度增加導致 er 微升
    
    # 電感計算 (包含動力學電感 Lk)
    L_geo = mu0 * (h_eff / w) # 簡化平行板模型
    L_k = (mu0 * (lambda_l*1e-9)**2) / ((w*1e-6) * (d_layer*1e-9))
    L_total = L_geo + L_k
    
    # 電容計算
    C = (e0 * er * w) / h_eff
    
    # 耦合係數：隨 s_eff 減少而增加
    # 互容 Cm 隨厚度減小與間距縮小而增強
    Cm = (e0 * er) / (s_eff / h_eff) 
    Lm = L_geo * exp(-s_eff / h_eff)
    
    # C. 頻域模擬
    f = linspace(0.1, 20, 200)
    omega = 2 * pi * f * 1e9
    Z0 = sqrt(L_total / C)
    v = 1 / sqrt(L_total * C)
    
    # NEXT/FEXT 公式 (dB)
    next_mag = (omega * 0.2 / (2 * Z0)) * (Lm + Cm * Z0**2)
    next_db = 20 * log10(next_mag + 1e-12)
    
    fext_coef = (1 / (2 * v)) * (Cm / C - Lm / L_total)
    fext_db = 20 * log10(abs(omega * 0.2 * fext_coef) + 1e-12)
    
    return f, next_db, fext_db, s_eff, h_eff, Z0

f, next_db, fext_db, s_eff, h_eff, Z0 = calculate_deformed_xtalk()

# --- 顯示結果 ---
col1, col2, col3 = columns(3)
col1.metric("壓縮後間距 s'", f"{s_eff:.2f} μm", f"{s_eff - s_init:.2f} μm")
col2.metric("壓縮後厚度 h'", f"{h_eff:.2f} μm", f"{h_eff - h_init:.2f} μm")
col3.metric("受壓後阻抗 Z0", f"{Z0:.2f} Ω")

divider()

fig, ax = subplots(figsize=(10, 5))
ax.plot(f, next_db, label='NEXT (Deformed)', color='red', linewidth=2)
ax.plot(f, fext_db, label='FEXT (Deformed)', color='blue', linestyle='--', linewidth=2)
ax.set_ylim([-100, -10])
ax.set_ylabel("Crosstalk (dB)")
ax.set_xlabel("Frequency (GHz)")
ax.grid(True, alpha=0.2)
ax.legend()
pyplot(fig)

warning(f"💡 物理警示：當壓力達到 {pressure_mpa} MPa 時，線間距縮小了 {abs(s_eff-s_init)/s_init*100:.1f}%，這導致高頻串擾增加了約 {abs(next_db[-1] - next_db[0])/10:.1f} dB。")
