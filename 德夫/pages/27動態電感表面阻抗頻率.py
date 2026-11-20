from numpy import array, cosh, exp, inf, linspace, pi as π, polyfit, sinh, sqrt, tanh
from json import dump
# ============================================================
# BCS Kinetic Inductance Calculator for HFSS Surface Impedance
# 用途：計算超導薄膜的動態電感與表面阻抗，輸出 HFSS 可用的頻率-阻抗表
# 支援材料：Nb, NbTi, NbTiN, Al, WSi
# ============================================================

import numpy as np
from scipy import integrate
from scipy.interpolate import interp1d
import json

# ==================== 物理常數 ====================
hbar = 1.054571817e-34      # J·s
kB = 1.380649e-23           # J/K
e = 1.602176634e-19         # C
mu0 = 4 * π * 1e-7      # H/m

# ==================== 材料參數庫 ====================
MATERIALS = {
    'Nb': {
        'Tc': 9.2,          # K
        'lambda_L_0': 90e-9, # m (London penetration depth at 0K)
        'Delta_0_over_kBTc': 1.76,  # BCS weak coupling
        'sigma_n': 6.9e6,   # S/m (normal state conductivity)
        'd': 300e-9,        # m (film thickness)
    },
    'NbTi': {
        'Tc': 9.0,
        'lambda_L_0': 250e-9,
        'Delta_0_over_kBTc': 1.76,
        'sigma_n': 5.0e6,
        'd': 200e-9,
    },
    'NbTiN': {
        'Tc': 14.0,
        'lambda_L_0': 200e-9,
        'Delta_0_over_kBTc': 1.85,
        'sigma_n': 8.0e6,
        'd': 100e-9,
    },
    'Al': {
        'Tc': 1.2,
        'lambda_L_0': 50e-9,
        'Delta_0_over_kBTc': 1.76,
        'sigma_n': 3.5e7,
        'd': 200e-9,
    },
    'WSi': {
        'Tc': 4.75,
        'lambda_L_0': 450e-9,
        'Delta_0_over_kBTc': 1.9,
        'sigma_n': 1.0e5,
        'd': 40e-9,
    }
}

def delta_T(T, Tc, Delta_0_over_kBTc):
    """溫度相關的超導能隙 (BCS approximation)"""
    Delta_0 = Delta_0_over_kBTc * kB * Tc
    if T >= Tc:
        return 0.0
    # 簡化 BCS 溫度依賴 (Padé approximant)
    t = T / Tc
    return Delta_0 * tanh(1.74 * sqrt(1.0 / t - 1.0))

def lambda_L_T(T, lambda_L_0, Tc):
    """溫度相關的 London penetration depth"""
    if T >= Tc:
        return inf
    t = T / Tc
    # 低溫近似: lambda_L(T) = lambda_L(0) / sqrt(1 - (T/Tc)^4)
    return lambda_L_0 / sqrt(1.0 - t**4)

def 厚度修正(d, lambda_L):
    """有限厚度修正因子 xi (Swihart / Sheen et al.)"""
    if d / lambda_L > 5:
        return 1.
    # 近似: xi = coth(d/lambda_L) / (d/lambda_L)
    x = d / lambda_L
    return cosh(x) / (x * sinh(x)) if x > .01 else 1. + x**2/3

def 動態電感(lambda_L, d, xi=1.0):
    """計算動態電感 sheet inductance Lk [H/sq]"""
    return mu0 * lambda_L * xi

def surface_impedance_superconductor(f, T, material='Nb'):
    """
    計算超導體的表面阻抗 Zs = Rs + j*Xs
    使用 Mattis-Bardeen 理論的簡化模型 (local limit)
    
    參數:
        f: 頻率 [Hz]
        T: 溫度 [K]
        material: 材料名稱
    回傳:
        Rs: 表面電阻 [Ohm]
        Xs: 表面電抗 [Ohm]
        Lk: 動態電感 [H/sq]
    """
    params = MATERIALS[material]
    Tc = params['Tc']
    lambda_L_0 = params['lambda_L_0']
    Delta_0_over_kBTc = params['Delta_0_over_kBTc']
    sigma_n = params['sigma_n']
    d = params['d']
    
    if T >= Tc:
        # 正常態
        omega = 2 * π * f
        skin_depth = sqrt(2 / (mu0 * sigma_n * omega))
        Rs = 1 / (sigma_n * skin_depth)
        Xs = Rs  # 正常態 Rs = Xs
        Lk = 0
        return Rs, Xs, Lk
    
    Delta = delta_T(T, Tc, Delta_0_over_kBTc)
    lambda_L = lambda_L_T(T, lambda_L_0, Tc)
    xi = 厚度修正(d, lambda_L)
    Lk = 動態電感(lambda_L, d, xi)
    
    omega = 2 * π * f
    
    # Mattis-Bardeen 簡化 (sigma2 >> sigma1 limit)
    # Xs ≈ omega * mu0 * lambda_L * xi
    Xs = omega * Lk
    
    # Rs from quasiparticle conductivity (simplified)
    # Rs ≈ (sigma1/sigma2) * Xs / 2
    # 使用 BCS 近似: sigma1/sigma2 ~ exp(-Delta/kBT) at low T
    if T > 0:
        ratio = exp(-Delta / (kB * T))
    else:
        ratio = 0
    Rs = ratio * Xs / 2.0
    
    return Rs, Xs, Lk

def generate_hfss_surface_impedance_table(material='Nb', T=0.02, 
                                           f_start=1e9, f_stop=20e9, n_points=100,
                                           output_file='hfss_surface_impedance.csv'):
    """
    生成 HFSS 可用的表面阻抗頻率表
    HFSS 中可透過 Polynomial Curve Fitting Function 匯入
    """
    freqs = linspace(f_start, f_stop, n_points)
    data = []
    
    for f in freqs:
        Rs, Xs, Lk = surface_impedance_superconductor(f, T, material)
        data.append({
            'Frequency_Hz': f,
            'Frequency_GHz': f / 1e9,
            'Rs_Ohm': Rs,
            'Xs_Ohm': Xs,
            'Lk_pH_per_sq': Lk * 1e12,
            'Zs_Ohm': sqrt(Rs**2 + Xs**2)
        })
    
    # 儲存 CSV
    import csv
    #with open(output_file, 'w', newline='') as f:
    #    writer = csv.DictWriter(f, fieldnames=data[0].keys())
    #    writer.writeheader()
    #    writer.writerows(data)
    
    # 同時輸出 HFSS 多項式擬合格式 (Surface Impedance 邊界條件用)
    Xs_vals = array([d['Xs_Ohm'] for d in data])
    freqs_GHz = array([d['Frequency_GHz'] for d in data])
    
    # 多項式擬合: Xs = a0 + a1*f + a2*f^2 + ...
    degree = 5
    coeffs = polyfit(freqs_GHz, Xs_vals, degree)
    poly_str = ' + '.join([f'{c:.6e}*f^{degree-i}' for i, c in enumerate(coeffs)])
    
    result = {
        'material': material,
        'temperature_K': T,
        'film_thickness_nm': MATERIALS[material]['d'] * 1e9,
        'lambda_L_0_nm': MATERIALS[material]['lambda_L_0'] * 1e9,
        'Tc_K': MATERIALS[material]['Tc'],
        'polynomial_coefficients': coeffs.tolist(),
        'polynomial_string': poly_str,
        'csv_file': output_file,
        'sample_data': data[:5]
    }
    
    #with open(output_file.replace('.csv', '_hfss_config.json'), 'w') as f:
    #    json.dump(result, f, indent=2)
    
    return result

# ==================== 執行範例 ====================
from streamlit import sidebar, radio, text_input, empty
MENU, 表單=[], ['阻抗', 'HFSS', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
狀態=empty()
if menu==len(表單):
  pass
elif menu==MENU[0]: #阻抗
    # 計算 Nb @ 20 mK, 1-20 GHz
    result_nb = generate_hfss_surface_impedance_table(
        material='Nb', T=0.02, 
        f_start=1e9, f_stop=20e9, n_points=100,
        output_file='/mnt/agents/output/hfss_surface_impedance_Nb_20mK.csv'
    )
    
    # 計算 NbTi @ 20 mK
    result_nbti = generate_hfss_surface_impedance_table(
        material='NbTi', T=0.02,
        f_start=1e9, f_stop=20e9, n_points=100,
        output_file='/mnt/agents/output/hfss_surface_impedance_NbTi_20mK.csv'
    )
    
    #print("=" * 60)
    輸入="HFSS Surface Impedance Generation Complete\n"
    #print("=" * 60)
    輸入+=f"\n[Nb @ 20 mK]"
    輸入+=f"  λL(0) = {result_nb['lambda_L_0_nm']:.1f} nm\n"
    輸入+=f"  Film thickness = {result_nb['film_thickness_nm']:.1f} nm\n"
    輸入+=f"  Polynomial (Xs vs f[GHz]): {result_nb['polynomial_string']}\n"
    輸入+=f"  CSV: {result_nb['csv_file']}"
    
    輸入+=f"\n[NbTi @ 20 mK]"
    輸入+=f"  λL(0) = {result_nbti['lambda_L_0_nm']:.1f} nm\n"
    輸入+=f"  Film thickness = {result_nbti['film_thickness_nm']:.1f} nm\n"
    輸入+=f"  Polynomial (Xs vs f[GHz]): {result_nbti['polynomial_string']}\n"
    輸入+=f"  CSV: {result_nbti['csv_file']}\n"
    
    # 列印前 5 筆數據供參考
    輸入+=f"\n[Nb @ 20 mK — 樣本數據]\n"
    輸入+=f"{'Freq(GHz)':>10} {'Rs(μΩ)':>12} {'Xs(mΩ)':>12} {'Lk(pH/sq)':>12}\n"
    for d in result_nb['sample_data']:
        輸入+=f"{d['Frequency_GHz']:>10.2f} {d['Rs_Ohm']*1e6:>12.3f} {d['Xs_Ohm']*1e3:>12.3f} {d['Lk_pH_per_sq']:>12.3f}\n"
    狀態.code(輸入)
elif menu==MENU[1]: #
  pass
elif menu==MENU[2]: #
  pass
