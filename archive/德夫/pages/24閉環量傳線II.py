from streamlit import subheader, sidebar, slider, number_input
from numpy import array, log, pi, sqrt, tanh
import streamlit as st
import numpy as np
import skrf as skrf
import matplotlib.pyplot as plt
import time

#from 量傳線Util import simulate_network, evaluate_stripline
# (前面 evaluate_stripline 與 simulate_network 的函數定義保持不變...)

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

def simulate_network(w_um, trench_factor):  #, TEMPERAvURE
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
# 介面佈局與動態閉環引擎
# ==========================================
st.subheader("🔄 Agent 閉環自適應收斂中心")

col_input, col_view = st.columns([1, 2])

with col_input:
    init_w = st.slider("初始中心線寬 Width (um)", 5.0, 40.0, 15.0, 0.5)
    init_trench = st.slider("初始 Kapton 挖空率 (Trench)", 0.0, 0.95, 0.0, 0.05)
    max_steps = st.slider("最大安全迭代限制 (輪)", 5, 50, 20, 1)
    start_btn = st.button("🚀 驅動自動收斂迴圈", type="primary")

with col_view:
    # 建立動態更新的看板容器
    status_msg = st.empty()
    metric_dashboard = st.empty()
    plot_container = st.empty()

if start_btn:
    # 初始化控制狀態
    current_w = init_w
    current_trench = init_trench
    history_z0 = []
    history_qi = []
    steps = []
    
    iteration = 0
    converged = False
    z0, qi, _, _ = evaluate_stripline(current_w, current_trench, 7.0e9, TEMPERATURE)
    
    # 啟動自動化收斂 While 迴圈
    #while iteration < max_steps:
    while abs(z0 - TARGET_Z0) >= .2: # and qi >= 目標品質:
        iteration += 1
        steps.append(iteration)
        
        # 🔔 核心修正：動態調用模擬與物理評估 (行動與觀察)
        net = simulate_network(current_w, current_trench)
        z0, qi, _, _ = evaluate_stripline(current_w, current_trench, 7.0e9, TEMPERATURE)
        
        # 紀錄當前輪次的物理量
        history_z0.append(z0)
        history_qi.append(qi)
        
        # 1. 畫面更新：即時更新數據看板
        with metric_dashboard.container():
            c1, c2, c3 = st.columns(3)
            c1.metric(f"Step {iteration} 線寬 (W)", f"{current_w:.2f} μm")
            c2.metric(f"Step {iteration} 阻抗 (Z0)", f"{z0:.2f} Ω", f"{z0 - TARGET_Z0:.2f} Ω", delta_color="inverse")
            c3.metric(f"Step {iteration} 品質因子 (Qi)", f"{qi:.2e}")
            
        status_msg.info(f"🔄 偵測中... 目前誤差：{abs(z0 - TARGET_Z0):.2f} Ω，正在尋找平衡點。")
        
        # 2. 畫面更新：即時繪製史密斯圖與收斂曲線
        fig, ax = plt.subplots(1, 2, figsize=(10, 4.5))
        net.plot_s_smith(m=0, n=0, ax=ax[0], color='blue', lw=2, label=f'Step {iteration}')
        ax[0].set_title("Real-time Smith Chart")
        
        ax2 = ax[1].twinx()
        ax[1].plot(steps, history_z0, 'g-o', label='Z0')
        ax2.plot(steps, history_qi, 'b-s', label='Qi')
        ax[1].axhline(TARGET_Z0, color='g', linestyle=':', alpha=0.5)
        ax[1].set_title("Optimization Trajectory")
        ax[1].set_xlabel("Steps")
        fig.tight_layout()
        
        # 將最新的圖表渲染進容器中覆蓋舊圖
        plot_container.pyplot(fig)
        plt.close(fig) # 釋放記憶體
        
        # 3. 驗證自動收斂條件 (Verify)
        if abs(z0 - TARGET_Z0) <= 0.2 and qi >= 目標品質:
            converged = True
            status_msg.success(f"🎉 【自動收斂成功】系統於第 {iteration} 輪完全達標！")
            break
            
        # 4. 感知與推理：動態互補修正參數 (Preceive & Reason)
        # 阻抗高於目標 -> 加寬線寬以拉高電容壓低阻抗；反之縮窄
        if z0 > TARGET_Z0:
            current_w += min(2.0, abs(z0 - TARGET_Z0) * 0.4)  # 比例控制加速收斂
        else:
            current_w -= min(2.0, abs(z0 - TARGET_Z0) * 0.4)
            
        # 品質因子不足 -> 微幅拉高挖空率，降低 Kapton 損耗體積
        if qi < 目標品質:
            current_trench = min(0.95, current_trench + 0.05)
            
        # 防止幾何參數越界
        current_w = max(5.0, min(50.0, current_w))
        
        # 稍作停頓，讓人類肉眼能看見介面上的動畫步進
        time.sleep(0.4)
        
    if not converged:
        status_msg.warning("⚠️ 達到最大安全輪次限制，系統已強制熔斷。")
