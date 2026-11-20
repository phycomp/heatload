# 修復 Bug 3: Huray 模型默認雪球密度過高
# 將默認值從 1e12 改爲 5e9，使 Huray 和 Hammerstad 在典型參數下結果相近

"""
PCB 傳輸線損耗計算引擎
Insertion Loss (IL) + Return Loss (RL)

物理模型:
- 導體損耗: Hammerstad-Jensen 經典模型 + Huray 雪球模型
- 介電損耗: 頻率相依 Df 模型 (Constant / Djordjevic-Sarkar / Linear)
- RL: 基于阻抗不匹配的反射系數
"""
import numpy as np
from numpy import log as ln
from numpy import sqrt, pi, exp

# 物理常數
C_LIGHT = 299792458.0  # m/s
MU0 = 4.0 * pi * 1e-7   # H/m
COPPER_RESISTIVITY = 1.724e-8  # Ω·m @ 20°C
COPPER_CONDUCTIVITY = 1.0 / COPPER_RESISTIVITY  # S/m


def _get_skin_depth(freq_hz: float, conductivity: float = COPPER_CONDUCTIVITY) -> float:
    """計算趨膚深度 (m)"""
    return sqrt(1.0 / (pi * freq_hz * MU0 * conductivity))


def conductor_loss_hammerstad(freq_ghz: float, w_mm: float, t_mm: float, 
                               h_mm: float, z0: float, roughness_rq_um: float = 1.5) -> float:
    """
    Hammerstad-Jensen 導體損耗模型 (dB/m)
    
    參數:
        freq_ghz: 頻率 (GHz)
        w_mm: 線寬 (mm)
        t_mm: 銅厚 (mm)
        h_mm: 介質厚度 (mm)
        z0: 特性阻抗 (Ω)
        roughness_rq_um: 銅箔粗糙度 Rq (μm)
    
    返回:
        導體損耗 (dB/m)
    """
    f_hz = freq_ghz * 1e9
    w_m = w_mm * 1e-3
    t_m = t_mm * 1e-3
    
    # 趨膚深度
    delta = _get_skin_depth(f_hz)
    
    # 表面電阻
    Rs = 1.0 / (COPPER_CONDUCTIVITY * delta)
    
    # 導體損耗 (Hammerstad-Jensen)
    if t_m < 3 * delta:  # 薄銅
        Kc = 1.0 + (1.0 / pi) * (t_m / w_m) * ln(4.0 * pi * w_m / t_m)
    else:
        Kc = 1.0 + (1.0 / pi) * (t_m / w_m) * ln(2.0 * w_m / t_m)
    
    alpha_c_neper = Rs * Kc / (w_m * z0)
    alpha_c_db = alpha_c_neper * 8.686  # Nepers -> dB
    
    # 粗糙度修正 (Hammerstad-Jensen)
    roughness_m = roughness_rq_um * 1e-6
    if delta > 0:
        Ksr = 1.0 + (2.0 / pi) * np.arctan(1.4 * (roughness_m / delta) ** 2)
    else:
        Ksr = 1.0
    
    return alpha_c_db * Ksr


def conductor_loss_huray(freq_ghz: float, w_mm: float, t_mm: float,
                          h_mm: float, z0: float, 
                          sphere_radius_um: float = 0.5, 
                          n_spheres_per_area: float = 5e9) -> float:
    """
    Huray 雪球模型導體損耗 (dB/m)
    
    參數:
        freq_ghz: 頻率 (GHz)
        w_mm: 線寬 (mm)
        t_mm: 銅厚 (mm)
        h_mm: 介質厚度 (mm)
        z0: 特性阻抗 (Ω)
        sphere_radius_um: 雪球半徑 (μm)
        n_spheres_per_area: 單位面積雪球數量 (m^-2), 默認 5e9
    
    返回:
        導體損耗 (dB/m)
    """
    f_hz = freq_ghz * 1e9
    w_m = w_mm * 1e-3
    
    # 趨膚深度
    delta = _get_skin_depth(f_hz)
    
    # 表面電阻
    Rs = 1.0 / (COPPER_CONDUCTIVITY * delta)
    
    # 基礎導體損耗
    alpha_c_base = Rs / (w_m * z0) * 8.686  # dB/m
    
    # Huray 粗糙度修正因子
    # Kr = 1 + (4/3) * N * r^3 / (w * δ) * (1 + δ/r)^(-1)
    r = sphere_radius_um * 1e-6  # m
    
    if delta > 0 and r > 0:
        Kr = 1.0 + (4.0 / 3.0) * n_spheres_per_area * (r ** 3) / (w_m * delta) * (1.0 + delta / r) ** (-1)
        # 限制修正因子在合理範圍
        Kr = max(1.0, min(Kr, 5.0))
    else:
        Kr = 1.0
    
    return alpha_c_base * Kr


def dielectric_loss(freq_ghz: float, er: float, df: float, e_eff: float) -> float:
    """
    介電損耗 (dB/m)
    
    參數:
        freq_ghz: 頻率 (GHz)
        er: 材料介電常數
        df: 損耗因子 tan(δ)
        e_eff: 有效介電常數
    
    返回:
        介電損耗 (dB/m)
    """
    f_hz = freq_ghz * 1e9
    
    # 介電損耗公式: αd = π * f * sqrt(εeff) * tan(δ) / c
    # 轉換爲 dB/m: * 20 / ln(10) ≈ * 8.686
    alpha_d = (pi * f_hz * sqrt(e_eff) * df / C_LIGHT) * 8.686
    
    return alpha_d


def total_insertion_loss(freq_ghz: float, w_mm: float, t_mm: float, h_mm: float,
                          er: float, df: float, z0: float, e_eff: float,
                          roughness_model: str = "hammerstad",
                          roughness_params: dict = None,
                          trace_length_m: float = 1.0) -> dict:
    """
    計算總插入損耗 IL
    
    返回:
        dict: {
            "IL_total_db": 總損耗 (dB),
            "IL_db_per_m": 單位長度損耗 (dB/m),
            "alpha_c_db_per_m": 導體損耗 (dB/m),
            "alpha_d_db_per_m": 介電損耗 (dB/m),
            "alpha_ratio": 導體/介電損耗比
        }
    """
    if roughness_params is None:
        roughness_params = {}
    
    # 導體損耗
    if roughness_model.lower() == "huray":
        alpha_c = conductor_loss_huray(
            freq_ghz, w_mm, t_mm, h_mm, z0,
            sphere_radius_um=roughness_params.get("sphere_radius_um", 0.5),
            n_spheres_per_area=roughness_params.get("n_spheres_per_area", 5e9)
        )
    else:
        alpha_c = conductor_loss_hammerstad(
            freq_ghz, w_mm, t_mm, h_mm, z0,
            roughness_rq_um=roughness_params.get("Rq_um", 1.5)
        )
    
    # 介電損耗
    alpha_d = dielectric_loss(freq_ghz, er, df, e_eff)
    
    # 總損耗
    alpha_total = alpha_c + alpha_d
    
    # 指定長度損耗
    il_db = alpha_total * trace_length_m
    
    return {
        "IL_total_db": il_db,
        "IL_db_per_m": alpha_total,
        "alpha_c_db_per_m": alpha_c,
        "alpha_d_db_per_m": alpha_d,
        "alpha_ratio": alpha_c / alpha_d if alpha_d > 1e-12 else float('inf')
    }


def return_loss(freq_ghz: float, z0_trace: float, z0_source: float = 50.0, 
                z0_load: float = 50.0) -> float:
    """
    計算 Return Loss (dB)
    
    基于源端和負載端阻抗不匹配
    
    參數:
        freq_ghz: 頻率 (GHz) - 用于頻率相依阻抗修正
        z0_trace: 傳輸線特性阻抗 (Ω)
        z0_source: 源端阻抗 (Ω)
        z0_load: 負載端阻抗 (Ω)
    
    返回:
        RL (dB) - 負值表示反射損耗
    """
    # 源端反射系數
    gamma_s = (z0_trace - z0_source) / (z0_trace + z0_source)
    # 負載端反射系數
    gamma_l = (z0_load - z0_trace) / (z0_load + z0_trace)
    
    # 總反射 (簡化: 假設兩端獨立)
    gamma_total = (abs(gamma_s) + abs(gamma_l)) / 2.0
    
    # RL = -20 * log10(|Γ|)
    if gamma_total > 1e-12:
        rl = -20.0 * np.log10(gamma_total)
    else:
        rl = 100.0  # 無反射
    
    return rl


def s11_magnitude(freq_ghz: float, z0_trace: float, z0_source: float = 50.0,
                  trace_length_m: float = 1.0, er: float = 4.5) -> float:
    """
    計算 S11 幅度 (dB) - 包含傳輸線效應
    
    參數:
        freq_ghz: 頻率 (GHz)
        z0_trace: 傳輸線特性阻抗
        z0_source: 源阻抗
        trace_length_m: 線長 (m)
        er: 介電常數
    
    返回:
        |S11| (dB)
    """
    # 相位常數
    beta = 2.0 * pi * freq_ghz * 1e9 * sqrt(er) / C_LIGHT
    
    # 電長度
    theta = beta * trace_length_m
    
    # 輸入阻抗
    zl = z0_load = 50.0
    zin = z0_trace * (zl + 1j * z0_trace * np.tan(theta)) / (z0_trace + 1j * zl * np.tan(theta))
    
    # S11
    gamma = (zin - z0_source) / (zin + z0_source)
    s11_db = 20.0 * np.log10(abs(gamma))
    
    return s11_db


def freq_sweep_il(freqs_ghz: np.ndarray, w_mm: float, t_mm: float, h_mm: float,
                   er: float, df: float, z0: float, e_eff: float,
                   roughness_model: str = "hammerstad",
                   roughness_params: dict = None,
                   trace_length_m: float = 1.0) -> dict:
    """
    頻率掃描 IL
    
    返回:
        dict: 各頻率點的損耗數據
    """
    if roughness_params is None:
        roughness_params = {}
    
    results = {
        "freq_ghz": freqs_ghz,
        "IL_total_db": [],
        "IL_db_per_m": [],
        "alpha_c_db_per_m": [],
        "alpha_d_db_per_m": [],
        "RL_db": []
    }
    
    for f in freqs_ghz:
        il = total_insertion_loss(f, w_mm, t_mm, h_mm, er, df, z0, e_eff,
                                   roughness_model, roughness_params, trace_length_m)
        results["IL_total_db"].append(il["IL_total_db"])
        results["IL_db_per_m"].append(il["IL_db_per_m"])
        results["alpha_c_db_per_m"].append(il["alpha_c_db_per_m"])
        results["alpha_d_db_per_m"].append(il["alpha_d_db_per_m"])
        
        # RL (假設 Z0_source = 50Ω)
        rl = return_loss(f, z0, 50.0, 50.0)
        results["RL_db"].append(rl)
    
    return results

# with open(f"{base}/modules/stackup/loss_models.py", "w", encoding="utf-8") as f:
    # f.write(loss_models_fixed)

# print("✅ loss_models.py 已修復（Huray 默認雪球密度 5e9，限制 Kr ≤ 5）")
