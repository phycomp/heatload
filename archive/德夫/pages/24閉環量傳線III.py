from streamlit import button, caption, columns, empty, info, progress, pyplot, set_page_config, sidebar, slider, subheader, success, title, warning, number_input
from numpy import array, log, pi, sqrt, tanh

import streamlit as st
import numpy as np
import skrf as skrf
import matplotlib.pyplot as plt
import time
import random

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
# 介面佈局與動態閉環引擎
# ==========================================
st.subheader("🔄 具備微擾機制(Anti-Saturation)的閉環自適應收斂中心")

col_input, col_view = st.columns(2)

with col_input:
    init_w = st.slider("初始中心線寬 Width (um)", 5.0, 40.0, 15.0, 0.5)
    init_trench = st.slider("初始 Kapton 挖空率 (Trench)", 0.0, 0.95, 0.0, 0.05)
    max_steps = st.slider("最大安全迭代限制 (輪)", 5, 100, 50, 5) # 增加迭代次數上限
    PERTURB_STRENGTH = st.slider("微擾強度 (Perturbation Scale)", 0.1, 3.0, 1.0, 0.1)
    start_btn = st.button("🚀 驅動自動收斂迴圈", type="primary")

with col_view:
    status_msg = st.empty()
    metric_dashboard = st.empty()
    plot_container = st.empty()

if start_btn:
    current_w = init_w
    current_trench = init_trench
    history_z0 = []
    history_qi = []
    history_loss = [] # 追蹤損失函數
    steps = []
    
    iteration = 0
    converged = False
    
    # 飽和偵測計數器
    saturation_counter = 0
    SATURATION_THRESHOLD = 4  # 連續 4 輪 Loss 變化極小即判定為飽和
    LOSS_CHANGE_LIMIT = 0.05  # Loss 變化量小於此值視為停滯
    
    while iteration < max_steps:
        iteration += 1
        steps.append(iteration)
        
        # 1. 執行模擬與評估 (Act & Observe)
        net = simulate_network(current_w, current_trench)
        z0, qi, _, _ = evaluate_stripline(current_w, current_trench, 7.0e9, TEMPERATURE)
        
        # 計算當前輪次的目標損失函數 (Loss Function)
        z0_error = (z0 - TARGET_Z0) ** 2
        qi_penalty = ((目標品質 - qi) / 目標品質) ** 2 * 100 if qi < 目標品質 else 0
        current_loss = z0_error + qi_penalty
        
        history_z0.append(z0)
        history_qi.append(qi)
        history_loss.append(current_loss)
        
        # 2. 飽和度診斷 (Perceive Saturation)
        is_saturated = False
        if len(history_loss) > 1:
            loss_delta = abs(history_loss[-1] - history_loss[-2])
            if loss_delta < LOSS_CHANGE_LIMIT:
                saturation_counter += 1
            else:
                saturation_counter = 0 # 重新計算
                
            if saturation_counter >= SATURATION_THRESHOLD:
                is_saturated = True
                saturation_counter = 0 # 觸發微擾後重設
        
        # 3. 畫面即時更新
        with metric_dashboard.container():
            c1, c2, c3 = st.columns(3)
            c1.metric(f"Step {iteration} 線寬 (W)", f"{current_w:.2f} μm")
            c2.metric(f"Step {iteration} 損失 (Loss)", f"{current_loss:.2f}", f"-{loss_delta:.3f}" if len(history_loss)>1 else None)
            c3.metric(f"Step {iteration} 阻抗 (Z0)", f"{z0:.2f} Ω")
            
        # 4. 驗證終止條件 (Verify)
        if abs(z0 - TARGET_Z0) <= 0.1 and qi >= 目標品質:
            converged = True
            status_msg.success(f"🎉 【自動收斂成功】系統成功突破飽和，於第 {iteration} 輪達到最優解！")
            break
            
        # 5. 推理與參數修正機制 (Reason & Action Adjustment)
        if is_saturated:
            # 💡 【核心升級：微擾機制】
            # 當系統陷入 Local Minimum 飽和時，主動注入隨機擾動 (Gaussian Noise)
            w_perturb = random.gauss(0, PERTURB_STRENGTH)
            trench_perturb = random.gauss(0, PERTURB_STRENGTH * 0.05)
            
            current_w += w_perturb
            current_trench = max(0.0, min(0.95, current_trench + trench_perturb))
            status_msg.warning(f"⚡ [飽和警報]: 系統陷入局部陷阱！主動注入微擾 ➔ ΔW: {w_perturb:.2f}, ΔTrench: {trench_perturb*100:.1f}%")
        else:
            # 正常的一階比例控制收斂路徑
            status_msg.info(f"🔄 正常收斂中... 目前誤差：{abs(z0 - TARGET_Z0):.2f} Ω")
            if z0 > TARGET_Z0:
                current_w += min(1.5, abs(z0 - TARGET_Z0) * 0.3)
            else:
                current_w -= min(1.5, abs(z0 - TARGET_Z0) * 0.3)
                
            if qi < 目標品質:
                current_trench = min(0.95, current_trench + 0.02)
                
        # 邊界約束防禦
        current_w = max(5.0, min(50.0, current_w))
        
        # 6. 渲染物理圖表 (Smith Chart & Loss Trajectory)
        fig, ax = plt.subplots(1, 2, figsize=(10, 4.5))
        net.plot_s_smith(m=0, n=0, ax=ax[0], color='blue', lw=2)
        ax[0].set_title(f"Real-time Smith Chart (Step {iteration})")
        
        # 改為繪製 Loss 函數的收斂/微擾軌跡
        ax[1].plot(steps, history_loss, 'r-x', label='Loss Function', lw=2)
        ax[1].set_yscale('log') # 使用對數座標，更清晰觀察飽和與驟降
        ax[1].set_title("Loss Function Saturation & Drop")
        ax[1].set_xlabel("Steps")
        ax[1].grid(True, which="both", alpha=0.3)
        fig.tight_layout()
        
        plot_container.pyplot(fig)
        plt.close(fig)
        
        time.sleep(0.3)
        
    if not converged:
        status_msg.error("⚠️ 達到最大迭代限制，系統未在容許誤差內收斂。")
