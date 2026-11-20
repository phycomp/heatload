import streamlit as st
import numpy as np
import skrf as skrf
import matplotlib.pyplot as plt
import time
import random

st.set_page_config(page_title="量子帶狀線補償模擬器", layout="wide")
st.title("📐 量子傳輸線 - 閉環優化與高頻補償牆")
st.caption("整合 Nb/NbN/Ta 超導製程、低溫熱收縮、表面阻抗(SIBC)與梯形墊補償")

MATERIAL_RECIPES = {
    "Nb (鈮)":  {"contraction": -0.0014, "lambda_0": 85e-9,  "tc": 9.2},
    "NbN (氮化鈮)": {"contraction": -0.0009, "lambda_0": 200e-9, "tc": 16.0},
    "Ta (鉭)":  {"contraction": -0.0020, "lambda_0": 50e-9,  "tc": 4.4}
}

st.sidebar.header("🎯 設計目標")
TARGET_Z0 = st.sidebar.slider("目標特徵阻抗 (Ω)", 40.0, 60.0, 50.0, 0.5)
TARGET_QI = st.sidebar.number_input("目標品質因子 (Qi)", value=100000, step=10000)

st.sidebar.header("🏭 超導製程材料切換")
mat_choice = st.sidebar.selectbox("選擇超導材料", list(MATERIAL_RECIPES.keys()))
recipe = MATERIAL_RECIPES[mat_choice]

st.sidebar.header("🌡️ 環境與封裝")
TEMPERATURE = st.sidebar.slider("工作溫度 (K)", 0.01, 9.0, 0.1, 0.1)
L_BONDWIRE = st.sidebar.slider("端點打線電感 Bondwire (nH)", 0.0, 2.0, 0.8, 0.1) * 1e-9
PAD_LENGTH_UM = st.sidebar.slider("梯形墊總長度 (μm)", 100, 1000, 300, 50)

EPS_R_KAPTON, TAN_D_KAPTON, FILM_THICKNESS = 3.4, 1e-3, 200e-9
VACUUM_MU, VACUUM_EPS = 4 * np.pi * 1e-7, 8.854187817e-12

def evaluate_stripline(w_um, trench_factor, freq_hz):
    w, h, t = w_um * 1e-6, 25.0 * 1e-6, FILM_THICKNESS
    h = h * (1.0 - 0.012) 
    w = w * (1.0 + recipe["contraction"])
    b = 2 * h
    
    eff_eps_r = EPS_R_KAPTON * (1 - trench_factor) + 1.0 * trench_factor
    eff_tan_d = TAN_D_KAPTON * (1 - trench_factor)
    
    cf = (2 * np.log((b - t + 2*t)/(b - t))) / np.pi if (w / (b - t)) >= 0.35 else 0.0
    w_eff = w + cf * (b - t)
    
    c_m = 4 * VACUUM_EPS * eff_eps_r * (w_eff / (b - t))
    l_m = (VACUUM_MU * (b - t)) / (4 * w_eff)
    
    lambda_T = recipe["lambda_0"] / np.sqrt(1.0 - (TEMPERATURE / recipe["tc"])**4) if TEMPERATURE < recipe["tc"] else recipe["lambda_0"]
    l_k = (VACUUM_MU * lambda_T * (1.0 / np.tanh(t / lambda_T))) / w
    l_total = l_m + l_k
    
    z0 = np.sqrt(l_total / c_m)
    beta = (2 * np.pi * freq_hz) * np.sqrt(l_total * c_m)
    alpha = (beta * eff_tan_d) / 2
    return z0, beta / (2 * alpha) if alpha > 0 else float('inf'), alpha, beta

def simulate_compensated_network(w_um, trench_factor, pad_w_max):
    freq = skrf.Frequency(start=4.0, stop=10.0, npoints=201, unit='ghz')
    z0_list, gamma_list = [], []
    for f in freq.f:
        z0, _, alpha, beta = evaluate_stripline(w_um, trench_factor, f)
        z0_list.append(z0)
        gamma_list.append(complex(alpha, beta))
    
    media = skrf.media.DefinedGammaZ0(frequency=freq, z0=np.array(z0_list), gamma=np.array(gamma_list))
    stripline_core = media.line(d=10, unit='mm')
    z0_core = np.array(z0_list)
    z_pad = z0_core * (w_um / pad_w_max)
    taper_segment = media.line(d=PAD_LENGTH_UM, unit='um', z0=(z0_core + z_pad)/2)
    
    ref_media = skrf.media.DefinedGammaZ0(frequency=freq, z0=50.0)
    bond_l = ref_media.inductor(L=L_BONDWIRE)
    bond_r = ref_media.inductor(L=L_BONDWIRE)
    return bond_l ** stripline_core ** bond_r, bond_l ** taper_segment ** stripline_core ** taper_segment ** bond_r

col_ctrl, col_plot = st.columns(2)
with col_ctrl:
    st.subheader("🔄 補償閉環引擎 (Loop Engine)")
    init_w = st.slider("初始中心線寬 Width (um)", 5.0, 80.0, 25.0, 0.5)
    init_trench = st.slider("初始 Kapton 挖空率 (Trench)", 0.0, 0.95, 0.2, 0.05)
    init_pad_w = st.slider("初始梯形墊寬度 W_pad (um)", 25.0, 150.0, 40.0, 0.5)
    max_steps = st.slider("最大安全迭代限制 (輪)", 10, 100, 40, 5)
    start_btn = st.button("🚀 啟動自適應閉環優化", type="primary")

with col_ctrl:
    status_msg = st.empty()
    metric_dashboard = st.empty()
    plot_container = st.empty()

if start_btn:
    current_w, current_trench, current_pad_w = init_w, init_trench, init_pad_w
    history_loss, steps = [], []
    best_loss = float('inf')
    best_config = {}
    iteration, saturation_counter, stagnation_limit, rollback_limit = 0, 0, 5, 12
    converged = False
    
    while iteration < max_steps:
        iteration += 1
        steps.append(iteration)
        uncomp_net, comp_net = simulate_compensated_network(current_w, current_trench, current_pad_w)
        z0, qi, _, _ = evaluate_stripline(current_w, current_trench, 7.0e9)
        
        s11_mean_mag = np.mean(comp_net.s_mag[:, 0, 0] ** 2)
        z0_error = (z0 - TARGET_Z0) ** 2
        qi_penalty = ((TARGET_QI - qi) / TARGET_QI) ** 2 * 150 if qi < TARGET_QI else 0
        current_loss = z0_error + qi_penalty + (s11_mean_mag * 1000)
        
        history_loss.append(current_loss)
        temperature = np.exp(-iteration / (max_steps * 0.4))
        adaptive_lr = 0.8 * (0.2 + 0.8 * temperature)
        
        if current_loss < best_loss:
            best_loss = current_loss
            best_config = {"w": current_w, "trench": current_trench, "pad_w": current_pad_w, "uncomp": uncomp_net, "comp": comp_net, "z0": z0, "qi": qi, "step": iteration}
            saturation_counter = 0
        else:
            saturation_counter += 1
            
        with metric_dashboard.container():
            c1, c2, c3 = st.columns(3)
            c1.metric(f"Step {iteration} 線寬 (W)", f"{current_w:.2f} μm")
            c2.metric("梯形墊寬度 (W_pad)", f"{current_pad_w:.2f} μm")
            c3.metric(f"Step {iteration} 阻抗 (Z0)", f"{z0:.2f} Ω")
            
        if abs(z0 - TARGET_Z0) <= 0.15 and qi >= TARGET_QI:
            converged = True
            status_msg.success(f"🎉【優化成功】於第 {iteration} 輪達到最優解！")
            break
            
        if saturation_counter >= rollback_limit:
            current_w, current_trench, current_pad_w = best_config["w"], best_config["trench"], best_config["pad_w"]
            saturation_counter = 0
            status_msg.error("💥 [演算法回溯]: 重置回歷史最佳點！")
        elif saturation_counter >= stagnation_limit:
            current_w += random.gauss(0, 3.0 * temperature)
            current_pad_w += random.gauss(0, 5.0 * temperature)
            current_trench = max(0.0, min(0.95, current_trench + random.gauss(0, 0.05 * temperature)))
            status_msg.warning("⚡ [退火微擾]: 注入微擾突破 Local Minimum...")
        else:
            status_msg.info("🔄 自適應優化中...")
            current_w += (1 if z0 > TARGET_Z0 else -1) * min(2.0, abs(z0 - TARGET_Z0) * adaptive_lr)
            current_pad_w += (0.5 if comp_net.s_db[-1, 0, 0] > -20 else -0.5) * adaptive_lr
            if qi < TARGET_QI: current_trench = min(0.95, current_trench + 0.02 * adaptive_lr)
            
        current_w = max(5.0, min(80.0, current_w))
        current_pad_w = max(current_w, min(180.0, current_pad_w))
        
        fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
        comp_net.plot_s_smith(m=0, n=0, ax=ax[0], color='green', lw=2, label='Compensated')
        uncomp_net.plot_s_smith(m=0, n=0, ax=ax[0], color='red', linestyle='--', alpha=0.5, label='Uncompensated')
        ax[0].set_title(f"Real-time Smith Chart (Step {iteration})")
        ax[0].legend(loc="upper left")
        
        ax[1].plot(steps, history_loss, 'r-x', lw=2, label='Total Loss')
        ax[1].set_yscale('log')
        ax[1].set_title("Loss Saturation Analysis")
        ax[1].set_xlabel("Steps")
        ax[1].grid(True, which="both", alpha=0.3)
        fig.tight_layout()
        
        plot_container.pyplot(fig)
        plt.close(fig)
        time.sleep(0.1)
