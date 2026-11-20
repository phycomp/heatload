# ============================================================
# COMSOL Thermal Contact Resistance Calibration Tool (Final)
# 最終修正版：考慮多層結構等效熱導率 + 合理實驗參數
# ============================================================

import numpy as np
from scipy.optimize import minimize
import json
import csv

# ==================== 多層結構等效熱導率 ====================

def effective_thermal_conductivity_crioflex(T, 
                                              w_signal_um=200, 
                                              t_ag_um=2.0,
                                              t_nb_nm=300,
                                              h_kapton_um=25,
                                              w_total_um=830):
    """
    計算 Cri/oFlex 多層帶狀線的等效軸向熱導率
    
    結構（由上至下）:
    - 上接地 Ag: t_ag_um, w_total_um
    - 上 Kapton: h_kapton_um/2
    - 信號 Nb: t_nb_nm, w_signal_um
    - 下 Kapton: h_kapton_um/2
    - 下接地 Ag: t_ag_um, w_total_um
    
    假設各層並聯傳熱
    """
    # 材料熱導率
    k_kapton = np.interp(T, [4, 10, 20, 50, 100, 300], 
                          [0.012, 0.018, 0.025, 0.045, 0.075, 0.12])
    
    # Ag 薄膜熱導率 (RRR ~ 10 的薄膜，低溫下受邊界散射限制)
    # 塊材 Ag: k ~ 2000 W/mK @ 10K, 薄膜約 100-500 W/mK
    k_ag = 200.0 * (T / 10.0)**0.5 if T < 50 else 300.0
    
    # Nb 超導態熱導率 (極低，電子被凍結)
    k_nb = 0.3 * (T / 10.0)**2.5
    
    # 截面積 (m²)
    A_ag = 2 * (t_ag_um * 1e-6) * (w_total_um * 1e-6)  # 上下兩層
    A_nb = (t_nb_nm * 1e-9) * (w_signal_um * 1e-6)
    A_kapton = (h_kapton_um * 1e-6) * (w_total_um * 1e-6)
    A_total = A_ag + A_nb + A_kapton
    
    # 並聯等效熱導率
    k_eff = (k_ag * A_ag + k_nb * A_nb + k_kapton * A_kapton) / A_total
    
    return k_eff, A_total, {'Ag': A_ag, 'Nb': A_nb, 'Kapton': A_kapton}

def steady_state_1d_multilayer(T_stage, Q_input, L, T, 
                                w_signal_um=200, t_ag_um=2.0, 
                                t_nb_nm=300, h_kapton_um=25, 
                                w_total_um=830, Rt_contact=1e-4):
    """
    多層帶狀線穩態熱傳導模型
    
    假設：
    - 一端 (x=0) 通過接觸電阻連接到熱錨
    - 另一端 (x=L) 絕熱
    - 均勻體積熱源
    """
    k_eff, A_total, areas = effective_thermal_conductivity_crioflex(
        T, w_signal_um, t_ag_um, t_nb_nm, h_kapton_um, w_total_um
    )
    
    n_segments = 100
    x = np.linspace(0, L, n_segments)
    
    # 接觸面溫度
    T_interface = T_stage + Q_input * Rt_contact / A_total
    
    # 溫度分佈 (均勻熱源，一端絕熱)
    # T(x) = T_interface + (Q/(2*k_eff*A_total*L)) * (2*L*x - x²)
    T_profile = T_interface + (Q_input / (2 * k_eff * A_total * L)) * (2 * L * x - x**2)
    T_max = T_profile[-1]
    
    # 溫升分解
    dT_contact = Q_input * Rt_contact / A_total
    dT_conduction = Q_input * L / (2 * k_eff * A_total)
    
    return {
        'T_profile': T_profile,
        'x': x,
        'T_interface': T_interface,
        'T_max': T_max,
        'k_eff': k_eff,
        'A_total': A_total,
        'areas': areas,
        'dT_contact': dT_contact,
        'dT_conduction': dT_conduction,
        'T_stage': T_stage,
        'Q_input': Q_input
    }

def calibrate_thermal_contact_resistance(
    measured_data,
    L=0.1,
    w_signal_um=200,
    t_ag_um=2.0,
    t_nb_nm=300,
    h_kapton_um=25,
    w_total_um=830,
    initial_guess=1e-4,
    method='Nelder-Mead'
):
    """
    從實驗數據校準熱接觸電阻
    
    measured_data: [{'T_stage': 4.0, 'T_measured': 4.15, 'Q_input': 1e-5}, ...]
    """
    def objective(Rt):
        error = 0
        for data in measured_data:
            T_stage = data['T_stage']
            T_meas = data['T_measured']
            Q = data['Q_input']
            
            # 使用測量溫度估算 k_eff
            T_est = (T_stage + T_meas) / 2
            
            result = steady_state_1d_multilayer(
                T_stage, Q, L, T_est,
                w_signal_um, t_ag_um, t_nb_nm, h_kapton_um, w_total_um,
                Rt[0]
            )
            error += (T_meas - result['T_max'])**2
        return error
    
    result = minimize(objective, [initial_guess], method=method,
                      bounds=[(1e-7, 1e-2)])
    
    Rt_calibrated = result.x[0]
    
    # 計算校準後的預測
    predictions = []
    for data in measured_data:
        T_stage = data['T_stage']
        T_meas = data['T_measured']
        Q = data['Q_input']
        T_est = (T_stage + T_meas) / 2
        
        res = steady_state_1d_multilayer(
            T_stage, Q, L, T_est,
            w_signal_um, t_ag_um, t_nb_nm, h_kapton_um, w_total_um,
            Rt_calibrated
        )
        predictions.append({
            'T_stage': T_stage,
            'T_measured': T_meas,
            'T_predicted': res['T_max'],
            'T_interface': res['T_interface'],
            'Q_input': Q,
            'k_eff': res['k_eff'],
            'A_total_m2': res['A_total'],
            'dT_contact_K': res['dT_contact'],
            'dT_conduction_K': res['dT_conduction']
        })
    
    return {
        'Rt_calibrated': Rt_calibrated,
        'Rt_calibrated_cm2K_W': Rt_calibrated * 1e4,
        'L_m': L,
        'geometry': {
            'w_signal_um': w_signal_um,
            't_ag_um': t_ag_um,
            't_nb_nm': t_nb_nm,
            'h_kapton_um': h_kapton_um,
            'w_total_um': w_total_um
        },
        'predictions': predictions,
        'optimization_success': result.success
    }

# ==================== 執行範例（最終版）====================
if __name__ == '__main__':
    # 模擬實驗數據
    # 場景：Cri/oFlex 帶狀線 (0.3mm 厚, 0.83mm 寬, 100mm 長)
    # 通入微波功率 (10-50 μW)，測量遠端溫度
    # 真實系統中，單通道總熱負載約 125 μW (4K→40K)，局部實驗用較小功率
    
    simulated_experiment = [
        {'T_stage': 4.0, 'T_measured': 4.12, 'Q_input': 2e-5},   # 20 μW → ΔT = 0.12 K
        {'T_stage': 4.0, 'T_measured': 4.28, 'Q_input': 4e-5},   # 40 μW → ΔT = 0.28 K
        {'T_stage': 4.0, 'T_measured': 4.48, 'Q_input': 6e-5},   # 60 μW → ΔT = 0.48 K
        {'T_stage': 4.0, 'T_measured': 4.72, 'Q_input': 8e-5},   # 80 μW → ΔT = 0.72 K
    ]
    
    # 校準
    result = calibrate_thermal_contact_resistance(
        measured_data=simulated_experiment,
        L=0.1,
        w_signal_um=200,
        t_ag_um=2.0,
        t_nb_nm=300,
        h_kapton_um=25,
        w_total_um=830,
        initial_guess=1e-4
    )
    
    print("=" * 75)
    print("COMSOL Thermal Contact Resistance Calibration (Multilayer Model)")
    print("=" * 75)
    
    geo = result['geometry']
    print(f"\n帶狀線幾何:")
    print(f"  總寬度: {geo['w_total_um']} μm, 總厚度: {geo['t_ag_um']*2 + geo['h_kapton_um'] + geo['t_nb_nm']/1000:.1f} μm")
    print(f"  信號線: {geo['w_signal_um']} μm × {geo['t_nb_nm']} nm (Nb)")
    print(f"  接地層: {geo['w_total_um']} μm × {geo['t_ag_um']} μm × 2 (Ag)")
    print(f"  Kapton: {geo['w_total_um']} μm × {geo['h_kapton_um']} μm")
    
    print(f"\n校準結果:")
    print(f"  熱接觸電阻 Rt = {result['Rt_calibrated']:.3e} K·m²/W")
    print(f"                = {result['Rt_calibrated_cm2K_W']:.3f} cm²·K/W")
    print(f"  優化成功: {result['optimization_success']}")
    
    # 計算等效熱導率 @ 4K
    k_eff_4K, A_tot, areas = effective_thermal_conductivity_crioflex(4.0, **geo)
    print(f"\n等效熱導率 @ 4K: {k_eff_4K:.3f} W/(m·K)")
    print(f"  總截面積: {A_tot*1e6:.3f} mm²")
    print(f"  Ag 貢獻: {areas['Ag']*1e6:.4f} mm²")
    print(f"  Nb 貢獻: {areas['Nb']*1e6:.6f} mm²")
    print(f"  Kapton 貢獻: {areas['Kapton']*1e6:.3f} mm²")
    
    print(f"\n{'='*75}")
    print(f"校準數據對照:")
    print(f"{'T_stage(K)':>12} {'Q(μW)':>10} {'T_meas(K)':>12} {'T_pred(K)':>12} {'誤差(mK)':>10} {'傳導ΔT(mK)':>12} {'接觸ΔT(mK)':>12}")
    print(f"{'-'*75}")
    for p in result['predictions']:
        err = (p['T_measured'] - p['T_predicted']) * 1e3
        print(f"{p['T_stage']:>12.2f} {p['Q_input']*1e6:>10.1f} {p['T_measured']:>12.3f} {p['T_predicted']:>12.3f} {err:>10.2f} {p['dT_conduction_K']*1e3:>12.2f} {p['dT_contact_K']*1e3:>12.2f}")
    
    # 生成 COMSOL 配置
    config = {
        'physics_interface': 'Heat Transfer in Solids (ht)',
        'boundary_condition': 'Thermal Contact',
        'contact_model': 'Equivalent thin resistive layer',
        'layer_resistance': {
            'value': result['Rt_calibrated'],
            'unit': 'K·m²/W'
        },
        'multilayer_geometry': geo,
        'effective_thermal_conductivity_4K': k_eff_4K,
        'calibration_data': result['predictions'],
        'usage_in_comsol': {
            'step_1': 'Add "Thermal Contact" boundary condition',
            'step_2': 'Select "Equivalent thin resistive layer"',
            'step_3': f"Enter Layer resistance = {result['Rt_calibrated']:.3e} [K·m²/W]",
            'step_4': 'For temperature-dependent Rt: Rt0*(4[K]/ht.T)^n, n≈1',
            'step_5': 'Set material thermal conductivity to multilayer effective value'
        }
    }
    
    with open('/mnt/agents/output/comsol_thermal_contact_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n{'='*75}")
    print("COMSOL 配置檔已更新:")
    for step, desc in config['usage_in_comsol'].items():
        print(f"  {step}: {desc}")
    
    # 生成溫度相關等效熱導率表
    temps = np.linspace(4, 300, 50)
    with open('/mnt/agents/output/cryogenic_material_properties.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Temperature_K', 'k_eff_Cri_oFlex_W_mK', 
                         'k_Kapton_W_mK', 'k_Ag_film_W_mK', 'k_Nb_W_mK',
                         'A_total_mm2', 'A_Ag_mm2', 'A_Nb_mm2', 'A_Kapton_mm2'])
        for T in temps:
            k_eff, A_tot, areas = effective_thermal_conductivity_crioflex(T, **geo)
            k_kapton = np.interp(T, [4, 10, 20, 50, 100, 300], [0.012, 0.018, 0.025, 0.045, 0.075, 0.12])
            k_ag = 200.0 * (T / 10.0)**0.5 if T < 50 else 300.0
            k_nb = 0.3 * (T / 10.0)**2.5
            writer.writerow([
                T, k_eff, k_kapton, k_ag, k_nb,
                A_tot*1e6, areas['Ag']*1e6, areas['Nb']*1e6, areas['Kapton']*1e6
            ])
    
    print(f"\n所有檔案已儲存至 /mnt/agents/output/")
