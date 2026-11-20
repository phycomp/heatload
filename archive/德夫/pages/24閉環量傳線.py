from streamlit import button, caption, columns, empty, info, progress, pyplot, set_page_config, sidebar, slider, subheader, success, title, warning, number_input
from matplotlib.pyplot import subplots
from numpy import array, log, pi, sqrt, tanh
import streamlit as st
import numpy as np
import skrf as skrf
import matplotlib.pyplot as plt

# 設定網頁標題與排版
set_page_config(page_title="量子帶狀線閉環優化模擬器", layout="wide")
title("🎛️ Stripline 量子傳輸線 - 迴圈工程 (Loop Engineering) 模擬實作")
caption("基於 scikit-rf 物理核心、超導動態電感(Lk)與打線(Bondwire)寄生修正")

with sidebar:
# ==========================================
# 1. 側邊欄：使用者定義與環境約束
# ==========================================
  subheader("🎯 設計目標與環境約束")
  TARGET_Z0 = slider("目標特徵阻抗 (Ω)", 40.0, 60.0, 50.0, 0.5)
  目標品質 = number_input("目標品質因子 (Qi)", value=100000, step=10000)

  subheader("🌡️ 物理與封裝參數設定")
  TEMPERATURE = slider("工作溫度 Temperature (K)", 0.01, 9.0, 0.1, 0.1)
  L_BONDWIRE = slider("端點打線電感 Bondwire (nH)", 0.0, 2.0, 0.8, 0.1) * 1e-9

  # 固定物理常數
  T_CRITICAL = 9.2        # 鈮 (Nb) 的 Tc
  LAMBDA_0 = 85e-9        # 鈮的 lambda_0
  EPS_R_KAPTON = 3.4      # Kapton 介電常數
  TAN_D_KAPTON = 1e-3     # Kapton 損耗
  FILM_THICKNESS = 200e-9 # 鈮厚度
  VACUUM_MU = 4 * pi * 1e-7
  VACUUM_EPS = 8.854187817e-12

# ==========================================
# 2. 核心物理與 scikit-rf 計算函數
# ==========================================
def get_kinetic_inductance_per_m(w, t, T):
    if T >= T_CRITICAL: return 0.0
    lambda_T = LAMBDA_0 / sqrt(1.0 - (T / T_CRITICAL)**4)
    lk_square = VACUUM_MU * lambda_T * (1.0 / tanh(t / lambda_T))
    return lk_square / w

def evaluate_stripline(w_um, trench_factor, freq_hz, T):
    w, h, t = w_um * 1e-6, 25.0 * 1e-6, FILM_THICKNESS
    b = 2 * h
    eff_eps_r = EPS_R_KAPTON * (1 - trench_factor) + 1.0 * trench_factor
    eff_tan_d = TAN_D_KAPTON * (1 - trench_factor)
    
    cf = (2 * log((b - t + 2*t)/(b - t))) / pi if (w / (b - t)) >= 0.35 else 0.0
    w_eff = w + cf * (b - t)
    
    c_m = 4 * VACUUM_EPS * eff_eps_r * (w_eff / (b - t))
    l_m = (VACUUM_MU * (b - t)) / (4 * w_eff)
    l_k_per_m = get_kinetic_inductance_per_m(w, t, T)
    l_total = l_m + l_k_per_m
    
    z0 = sqrt(l_total / c_m)
    beta = (2 * pi * freq_hz) * sqrt(l_total * c_m)
    alpha = (beta * eff_tan_d) / 2
    return z0, beta / (2 * alpha) if alpha > 0 else float('inf'), alpha, beta

def simulate_network(w_um, trench_factor):
    freq = skrf.Frequency(start=4.0, stop=10.0, npoints=201, unit='ghz')
    z0_list, gamma_list = [], []
    for f in freq.f:
        z0, _, alpha, beta = evaluate_stripline(w_um, trench_factor, f, TEMPERATURE)
        z0_list.append(z0)
        gamma_list.append(complex(alpha, beta))
    
    media = skrf.media.DefinedGammaZ0(frequency=freq, z0=array(z0_list), gamma=array(gamma_list))
    stripline_core = media.line(d=10, unit='mm')
    
    ref_media = skrf.media.DefinedGammaZ0(frequency=freq, z0=50.0)
    bond_l = ref_media.inductor(L=L_BONDWIRE)
    bond_r = ref_media.inductor(L=L_BONDWIRE)
    return bond_l ** stripline_core ** bond_r

# ==========================================
# 3. 畫面佈局與閉環控制
# ==========================================
控制, 繪製 = columns([1, 2])

with 控制:
    subheader("🔄 閉環控制中心 (Loop Engine)")
    init_w = slider("初始中心線寬 Width (um)", 5.0, 40.0, 15.0, 0.5)
    init_trench = slider("初始 Kapton 挖空率 (Trench)", 0.0, 0.95, 0.0, 0.05)
    max_steps = slider("最大迭代輪次", 5, 30, 15, 1)
    
    start_btn = button("🚀 開始自動化閉環優化", type="primary")

# 初始化繪圖與狀態紀錄
history = []
current_w, current_trench = init_w, init_trench

#if start_btn:
#    progress_bar = progress(0)
status_text = empty()
狀態=empty()
z0, qi, _, _ = evaluate_stripline(current_w, current_trench, 7.0e9, TEMPERATURE)
狀態.code([z0, qi])
# 執行自動化閉環迭代
#for step in range(1, max_steps + 1):
step=0
while abs(z0 - TARGET_Z0) >= .3 or qi >= 目標品質:
    # 1. 執行模擬 (行動 Act)
    net = simulate_network(current_w, current_trench)
    #狀態.code(net)
    
    # 2. 讀取中心頻率 7 GHz 的指標 (觀察 Observe)
    z0, qi, _, _ = evaluate_stripline(current_w, current_trench, 7.0e9, TEMPERATURE)
    step+=1
    
    # 紀錄歷史軌跡
    history.append({
        "step": step, "w": current_w, "trench": current_trench, "z0": z0, "qi": qi, "net": net
    })
    
    status_text.text(f"🔄 迭代第 {step}/{max_steps} 輪：Z0 = {z0:.2f} Ω, Qi = {qi:.2e}")
    #progress_bar.progress(step / max_steps)
    
    # 3. 驗證終止條件 (驗證 Verify)
    #if abs(z0 - TARGET_Z0) <= 0.3 and qi >= 目標品質:
    #    success(f"🎉 系統收斂成功！於第 {step} 輪達到最優化指標。")
    #    break
        
    # 4. 決策更新參數 (感知與推理 Perceive & Reason)
    # 阻抗控制迴圈：阻抗高於目標則加寬線，反之縮窄
    Δ = 1.2 if z0 > TARGET_Z0 else -1.2
    current_w = max(5.0, min(50.0, current_w + Δ))
    
    # 品質因子控制迴圈：Qi 不足時加大挖空率以阻絕 Kapton 損耗
    if qi < 目標品質:
        current_trench = min(0.95, current_trench + 0.05)
        
    if z0 > TARGET_Z0:
        current_w += min(2.0, abs(z0 - TARGET_Z0) * 0.4)  # 比例控制加速收斂
    else:
        current_w -= min(2.0, abs(z0 - TARGET_Z0) * 0.4)
        
    # 品質因子不足 -> 微幅拉高挖空率，降低 Kapton 損耗體積
    #if qi < TARGET_QI:
    #    current_trench = min(0.95, current_trench + 0.05)
        
    # 防止幾何參數越界
    current_w = max(5.0, min(50.0, current_w))

#else:
#    warning("⚠️ 達到最大迭代輪次，系統未完美收斂，輸出最佳近似解。")

# ==========================================
# 4. 數據視覺化與圖表渲染
# ==========================================
with 繪製:
    subheader("📊 物理指標動態觀測牆")
    
    if len(history) > 0:
        # 建立展示圖表
        fig, ax = subplots(1, 2, figsize=(12, 5.5))
        
        # 繪製最後收斂的史密斯圖
        final_data = history[-1]
        final_data["net"].plot_s_smith(m=0, n=0, ax=ax[0], color='blue', lw=2, label=f'Final Step {final_data["step"]}')
        
        # 如果有初始軌跡，繪製出來做對比
        if len(history) > 1:
            history[0]["net"].plot_s_smith(m=0, n=0, ax=ax[0], color='grey', linestyle='--', alpha=0.6, label='Initial Guess')
            
        ax[0].set_title(f"S11 Smith Chart (4-10 GHz)\nFinal Z0: {final_data['z0']:.1f} Ω")
        ax[0].legend()
        
        # 繪製迭代收斂曲線
        steps = [h["step"] for h in history]
        z0_vals = [h["z0"] for h in history]
        qi_vals = [h["qi"] for h in history]
        
        ax2 = ax[1].twinx()
        p1, = ax[1].plot(steps, z0_vals, 'g-o', label='Impedance Z0', lw=2)
        p2, = ax2.plot(steps, qi_vals, 'b-s', label='Quality Factor Qi', lw=2)
        ax[1].axhline(TARGET_Z0, color='g', linestyle=':', alpha=0.5)
        
        ax[1].set_xlabel('Iteration Steps')
        ax[1].set_ylabel('Impedance Z0 (Ω)', color='g')
        ax2.set_ylabel('Internal Qi', color='b')
        ax[1].set_title("Loop Optimization Trajectory")
        ax[1].grid(True, alpha=0.3)
        
        pyplot(fig)
        
        # 數據看板
        c1, c2, c3 = columns(3)
        c1.metric("💡 最終線寬 (Width)", f"{final_data['w']:.2f} μm")
        c2.metric("🌌 基板挖空率 (Trench)", f"{final_data['trench']*100:.1f} %")
        c3.metric("📈 最終品質因子 (Qi)", f"{final_data['qi']:.2e}")
    else:
        info("💡 請點擊左側的「開始自動化閉環優化」按鈕，驅動 AI 迴圈引擎進行即時物理推算與繪圖。")
