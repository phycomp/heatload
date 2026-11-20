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
  TARGET_QI = number_input("目標品質因子 (Qi)", value=100000, step=10000)

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
    w, h, t = w_um * 1e-6, 12.5 * 1e-6, FILM_THICKNESS
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
# 介面配置升級
# ==========================================
st.subheader("🚀 演算法優化：自適應步長與最佳記憶回溯收斂中心")

col_input, col_view = st.columns(2)

with col_input:
    init_w = st.slider("初始中心線寬 Width (um)", 5.0, 80.0, 15.0, 0.5)
    init_trench = st.slider("初始 Kapton 挖空率 (Trench)", 0.0, 0.95, 0.0, 0.05)
    max_steps = st.sidebar.slider("最大安全迭代限制 (輪)", 10, 150, 80, 5)
    st.caption("⚙️ 演算法高級微調參數")
    INITIAL_LR = st.slider("初始學習率 (Learning Rate)", 0.1, 2.0, 0.8, 0.1)
    start_btn = st.button("🚀 啟動自適應閉環優化", type="primary")

with col_view:
    status_msg = st.empty()
    metric_dashboard = st.empty()
    plot_container = st.empty()

if start_btn:
    # 狀態變數初始化
    current_w = init_w
    current_trench = init_trench
    history_loss = []
    steps = []
    
    # 💡 演算法修正元件 1：最佳紀錄暫存器
    best_loss = float('inf')
    best_config = {"w": current_w, "trench": current_trench, "net": None, "z0": 0, "qi": 0}
    
    # 飽和與回溯計數器
    saturation_counter = 0
    stagnation_limit = 5     # 連續 5 輪沒突破歷史最佳就啟動大微擾
    rollback_limit = 10     # 連續 10 輪沒突破就強制回溯到歷史最佳點
    
    iteration = 0
    converged = False
    
    while iteration < max_steps:
        iteration += 1
        steps.append(iteration)
        
        # 1. 執行模擬與評估 (Act & Observe)
        net = simulate_network(current_w, current_trench)
        z0, qi, _, _ = evaluate_stripline(current_w, current_trench, 7.0e9, TEMPERATURE)
        
        # 計算嚴格的損失函數 (納入阻抗誤差平方與品質因子懲罰)
        #z0_error = (z0 - TARGET_Z0) ** 2
        #qi_penalty = ((TARGET_QI - qi) / TARGET_QI) ** 2 * 200 if qi < TARGET_QI else 0
        #current_loss = z0_error + qi_penalty
        
        # 修正：給予阻抗誤差更高的懲罰權重（例如放大 5 倍），並平衡 Trench 的拉高速度
        z0_error = 5.0 * ((z0 - TARGET_Z0) ** 2)
        qi_penalty = ((TARGET_QI - qi) / TARGET_QI) ** 2 * 100 if qi < TARGET_QI else 0
        current_loss = z0_error + qi_penalty
        history_loss.append(current_loss)
        # 💡 演算法修正元件 2：自適應學習率與溫度衰減 (模擬退火)
        # 隨著迭代增加，基礎步長自發性衰減，確保後期精準收斂
        temperature = np.exp(-iteration / (max_steps * 0.4))
        adaptive_lr = INITIAL_LR * (0.2 + 0.8 * temperature)
        
        # 💡 演算法修正元件 3：更新歷史最佳記憶庫
        if current_loss < best_loss:
            best_loss = current_loss
            best_config = {
                "w": current_w, "trench": current_trench, "net": net, "z0": z0, "qi": qi, "step": iteration
            }
            saturation_counter = 0  # 重新計數
        else:
            saturation_counter += 1
            
        # 2. 畫面即時渲染看板
        with metric_dashboard.container():
            c1, c2, c3 = st.columns(3)
            c1.metric(f"Step {iteration} 線寬 (W)", f"{current_w:.2f} μm")
            c2.metric("當前最小 Loss (Best)", f"{best_loss:.2f}", delta=f"停滯 {saturation_counter} 輪" if saturation_counter > 0 else "新低點", delta_color="inverse")
            c3.metric(f"Step {iteration} 阻抗 (Z0)", f"{z0:.2f} Ω")
            
        # 3. 驗證終止條件 (Verify)
        if abs(z0 - TARGET_Z0) <= 0.15 and qi >= TARGET_QI:
            converged = True
            status_msg.success(f"🎉 【高級演算法收斂成功】成功繞過 Local Minimum！於第 {iteration} 輪達到全球最優解。")
            break
            
        # 4. 推理與多層級狀態控制決策 (Reasoning Core)
        if saturation_counter >= rollback_limit:
            # 🚨 狀態 C：嚴重停滯，執行強制回溯重置
            current_w = best_config["w"]
            current_trench = best_config["trench"]
            saturation_counter = 0
            status_msg.error(f"💥 [演算法回溯]: 連續未突破，強制將幾何重置回第 {best_config['step']} 輪的歷史最佳點！")
            
        #elif saturation_counter >= stagnation_limit:
        #    # ⚠️ 狀態 B：陷入局部陷阱，注入受溫度調變的隨機微擾
        #    w_perturb = random.gauss(0, 2.5 * temperature)
        #    trench_perturb = random.gauss(0, 0.1 * temperature)
        #    current_w += w_perturb
        #    current_trench = max(0.0, min(0.95, current_trench + trench_perturb))
        #    status_msg.warning(f"⚡ [退火微擾]: 偵測到局部飽和，注入微擾 ➔ ΔW: {w_perturb:.2f}, ΔTrench: {trench_perturb*100:.1f}% (溫度: {temperature:.2f})")
             
        elif saturation_counter >= stagnation_limit:
            w_perturb = random.gauss(0, 2.5 * temperature)
            trench_perturb = random.gauss(0, 0.1 * temperature)

            # 檢查是否撞牆，若撞牆則將微擾反向彈回
            if current_w + w_perturb > 80.0:
                current_w -= abs(w_perturb)  # 反向推回
                current_trench = min(0.95, current_trench + 0.05) # 補償：增加挖空率
            else:
                current_w += w_perturb
                current_trench = max(0.0, min(0.95, current_trench + trench_perturb))
        else:
            # ✅ 狀態 A：正常收斂路徑 (結合自適應步長)
            status_msg.info(f"🔄 正常自適應收斂中... 步長係數 (LR): {adaptive_lr:.2f}")
            error_sign = 1 if z0 > TARGET_Z0 else -1
            # 使用梯度方向配合自適應步長更新 W
            current_w += error_sign * min(2.5, abs(z0 - TARGET_Z0) * adaptive_lr)
            
            if qi < TARGET_QI:
                current_trench = min(0.95, current_trench + 0.03 * adaptive_lr)
                
        # 物理幾何邊界防禦
        current_w = max(5.0, min(80.0, current_w))
        
        # 5. 繪製圖表 (使用歷史最佳網路作展示)
        #fig, ax = plt.subplots(1, 2, figsize=(10, 4.5))
        #display_net = net if net is not None else best_config["net"]
        #if display_net:
        #    display_net.plot_s_smith(m=0, n=0, ax=ax, color='blue', lw=2)
        #ax.set_title(f"Smith Chart (Best Step: {best_config.get('step', iteration)})")
        #
        #ax.plot(steps, history_loss, 'r-x', lw=2)
        #ax.axhline(best_loss, color='grey', linestyle='--', alpha=0.5)
        #ax.set_yscale('log')
        #ax.set_title("Loss Trajectory (Adaptive + Annealing)")
        #ax.set_xlabel("Steps")
        #ax.grid(True, which="both", alpha=0.3)
        #fig.tight_layout()
        #
        #plot_container.pyplot(fig)
        #plt.close(fig)
        # 5. 繪製圖表 (修正 ax 陣列傳遞問題)
        fig, ax = plt.subplots(1, 2, figsize=(10, 4.5))
        display_net = net if net is not None else best_config["net"]
        
        if display_net:
            # 🔔 修正點：明確指定傳入第一個子圖 ax[0]
            display_net.plot_s_smith(m=0, n=0, ax=ax[0], color='blue', lw=2)
        ax[0].set_title(f"Smith Chart (Best Step: {best_config.get('step', iteration)})")
        
        # 🔔 修正點：將 Loss 曲線繪製在第二個子圖 ax[1] 上
        ax[1].plot(steps, history_loss, 'r-x', lw=2)
        ax[1].axhline(best_loss, color='grey', linestyle='--', alpha=0.5)
        ax[1].set_yscale('log')
        ax[1].set_title("Loss Trajectory (Adaptive + Annealing)")
        ax[1].set_xlabel("Steps")
        ax[1].grid(True, which="both", alpha=0.3)
        fig.tight_layout()
        
        plot_container.pyplot(fig)
        plt.close(fig)

        time.sleep(0.2)
        
    #if not converged:
    #    # 如果最終仍未達標準，但我們有最佳記憶庫，直接將系統強制拉回歷史最優解輸出
    #    st.error(f"⚠️ 達到最大迭代限制。演算法自動提取歷史最優解（第 {best_config['step']} 輪）：W = {best_config['w']:.2f} um, Z0 = {best_config['z0']:.2f} Ω")
    #    
    #    fig, ax = plt.subplots(1, 2, figsize=(10, 4.5))
    #    best_config["net"].plot_s_smith(m=0, n=0, ax=ax, color='green', lw=2)
    #    ax.plot(steps, history_loss, 'r-x')
    #    ax.set_yscale('log')
    #    fig.tight_layout()
    #    plot_container.pyplot(fig)
    #    plt.close(fig)
    if not converged:
        # 如果最終仍未達標準，但我們有最佳記憶庫，直接將系統強制拉回歷史最優解輸出
        st.error(f"⚠️ 達到最大迭代限制。演算法自動提取歷史最優解（第 {best_config['step']} 輪）：W = {best_config['w']:.2f} um, Z0 = {best_config['z0']:.2f} Ω")
        
        fig, ax = plt.subplots(1, 2, figsize=(10, 4.5))
        
        # 🔔 修正點：明確指定傳入第一個子圖 ax[0]
        best_config["net"].plot_s_smith(m=0, n=0, ax=ax[0], color='green', lw=2)
        ax[0].set_title(f"Best S11 Smith Chart (Step: {best_config['step']})")
        
        # 🔔 修正點：將 Loss 曲線繪製在第二個子圖 ax[1] 上
        ax[1].plot(steps, history_loss, 'r-x')
        ax[1].set_yscale('log')
        ax[1].set_title("Loss Trajectory (Final Status)")
        ax[1].set_xlabel("Steps")
        ax[1].grid(True, which="both", alpha=0.3)
        
        fig.tight_layout()
        plot_container.pyplot(fig)
        plt.close(fig)
