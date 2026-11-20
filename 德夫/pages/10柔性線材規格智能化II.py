from numpy import arctan, array, exp, linspace, log, log10, mean, ndarray, pi, sqrt
from streamlit import sidebar, text_input, radio
from pandas import DataFrame
import numpy as np
import pandas as pd
from scipy.optimize import minimize, differential_evolution
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

# 物理常數
MU_0 = 4 * np.pi * 1e-7  # H/m
EPS_0 = 8.854e-12  # F/m

# ============================================================
# 數據類別
# ============================================================

@dataclass
class StriplineGeometry:
    """Stripline 幾何參數"""
    w: float        # 信號線寬度 (mm)
    t: float        # 信號線厚度 (μm)
    h: float        # 介電層厚度 (mm) 上下各一層
    s: float        # 通道間距 pitch (mm)
    L: float        # 傳輸線長度 (mm)
    n_channels: int # 通道數

@dataclass
class ThermalBoundary:
    """熱邊界條件"""
    T_hot: float
    T_cold: float
    stage: str

@dataclass
class MaterialStack:
    """多層膜結構"""
    layers: List[Dict]

@dataclass
class DesignConstraints:
    """設計規格約束"""
    target_Z0: float = 50.0
    Z0_tolerance: float = 5.0
    max_NEXT_dB: float = -40.0
    max_FEXT_dB: float = -40.0
    max_IL_dB: float = 3.0
    max_thermal_per_channel_uW: float = 200.0
    max_total_thickness_mm: float = 0.5
    min_bend_radius_mm: float = 5.0
    min_trace_width_um: float = 50.0
    max_trace_width_um: float = 500.0
    min_dielectric_um: float = 25.0
    max_dielectric_um: float = 500.0
    min_pitch_mm: float = 0.5
    max_pitch_mm: float = 5.0
    n_channels: int = 8
    frequency_GHz: float = 6.0
    length_mm: float = 400.0
    temperature_stage: str = "40K → 4K"
    conductor: str = "NbTi"
    dielectric: str = "Polyimide_Kapton"
    er: float = 3.4
    tan_delta: float = 3e-5

@dataclass
class MaterialViaSpecs:
    """材料與 Via 規格"""
    er: float = 3.4
    tan_delta_rt: float = 0.003
    tan_delta_4K: float = 3e-5
    tan_delta_20mK: float = 2.2e-5
    n_dielectric_layers: int = 2
    dielectric_thickness_um: float = 150.0
    via_enabled: bool = True
    via_diameter_um: float = 150.0
    via_density_per_mm: float = 2.0
    via_material: str = "Ag"
    conductor_material: str = "NbTi"
    conductor_thickness_um: float = 5.0
    conductor_roughness_um: float = 0.5
    trace_width_um: float = 150.0
    pitch_mm: float = 2.0
    length_mm: float = 400.0
    frequency_GHz: float = 6.0
    temperature_K: float = 4.0

# ============================================================
# 基礎計算函數
# ============================================================

def calc_stripline_impedance(geo: StriplineGeometry, er: float) -> float:
    """計算 Stripline 特性阻抗"""
    b = 2 * geo.h
    w = geo.w
    t = geo.t / 1000
    if w / b > 0.35:
        We = w + (t / np.pi) * (1 + np.log(2 * b / t))
    else:
        We = w - (b / (2 * np.pi)) * (1 - 0.5 * np.exp(-4 * np.pi * w / b)) * np.log(1 + 2 * t / b)
    Z0 = (30 * np.pi / np.sqrt(er)) * (b / We)
    return Z0

def calc_crosstalk_stripline(geo: StriplineGeometry, er: float, f: float) -> Dict:
    """計算 Stripline 串擾"""
    w = geo.w
    s = geo.s
    h = geo.h
    L = geo.L / 1000
    eps = er * EPS_0
    C_self = eps * (w / (2 * h))
    Cm = eps * (w / 1000) / (s / 1000) * np.exp(-np.pi * s / (2 * h))
    L_self = MU_0 * (2 * h / w) * 1e-3
    Lm = MU_0 * (h / (2 * np.pi * s)) * 1e-3
    kc = Cm / (C_self + Cm) if (C_self + Cm) > 0 else 0
    kL = Lm / (L_self + Lm) if (L_self + Lm) > 0 else 0
    k = 0.5 * (kc + kL)
    c = 3e8
    beta = 2 * np.pi * f * np.sqrt(er) / c
    theta = beta * L
    if theta < 1:
        NEXT_linear = k * theta / 2
    else:
        NEXT_linear = k / 2
    FEXT_linear = k * theta
    return {
        "NEXT_dB": 20 * np.log10(max(abs(NEXT_linear), 1e-12)),
        "FEXT_dB": 20 * np.log10(max(abs(FEXT_linear), 1e-12)),
        "coupling_k": k, "Cm_per_m": Cm, "Lm_per_m": Lm, "beta": beta
    }

# 材料熱導率
MATERIAL_THERMAL = {
    "Ag": {"type": "power_law", "A": 420, "alpha": 1.0, "low_temp": {"A": 2000, "alpha": 2.5}},
    "NbTi": {"type": "superconducting", "Tc": 9.2, "normal_k": 10, "sc_k": 0.001},
    "Polyimide_Kapton": {"type": "power_law", "A": 0.155, "alpha": 1.0},
    "Cu": {"type": "power_law", "A": 400, "alpha": 1.0, "low_temp": {"A": 1500, "alpha": 2.3}}
}

def calc_thermal_conductivity(material: str, T: float) -> float:
    """計算材料熱導率"""
    props = MATERIAL_THERMAL.get(material, None)
    if props is None:
        return 1.0
    if props["type"] == "superconducting":
        Tc = props["Tc"]
        if T < Tc * 0.5:
            return props["sc_k"]
        elif T < Tc:
            return props["sc_k"] + (props["normal_k"] - props["sc_k"]) * ((T - 0.5*Tc) / (0.5*Tc))
        else:
            return props["normal_k"]
    elif props["type"] == "power_law":
        if "low_temp" in props and T < 20:
            A = props["low_temp"]["A"]
            alpha = props["low_temp"]["alpha"]
        else:
            A = props["A"]
            alpha = props["alpha"]
        return A * (T / 300) ** alpha
    return 1.0

def calc_thermal_load(geo: StriplineGeometry, boundary: ThermalBoundary, materials: MaterialStack) -> Dict:
    """計算熱負載"""
    T_hot = boundary.T_hot
    T_cold = boundary.T_cold
    L_m = geo.L / 1000
    n_points = 100
    T_range = np.linspace(T_cold, T_hot, n_points)
    total_kA = 0
    for layer in materials.layers:
        mat = layer["material"]
        thickness = layer["thickness"] / 1e6
        width = layer["width"] / 1000
        area = thickness * width
        k_avg = np.mean([calc_thermal_conductivity(mat, T) for T in T_range])
        total_kA += k_avg * area
    delta_T = T_hot - T_cold
    P = total_kA * delta_T / L_m
    P_per_channel = P / geo.n_channels
    return {
        "total_power_W": P, "per_channel_W": P_per_channel,
        "per_channel_uW": P_per_channel * 1e6, "per_channel_nW": P_per_channel * 1e9,
        "kA_total": total_kA, "delta_T": delta_T
    }

def calc_insertion_loss(geo: StriplineGeometry, er: float, tan_delta: float, f: float, material: str = "Ag") -> float:
    """計算插入損耗"""
    w = geo.w / 1000
    t = geo.t / 1e6
    L = geo.L / 1000
    h = geo.h / 1000
    sigma = {"Ag": 6.3e7, "NbTi": 1e6, "Cu": 5.8e7}.get(material, 6.3e7)
    delta_s = np.sqrt(2 / (MU_0 * sigma * 2 * np.pi * f))
    Rs = 1 / (sigma * delta_s)
    Z0 = 50
    alpha_c = Rs / (Z0 * w)
    alpha_c_db = alpha_c * 8.686
    c = 3e8
    alpha_d = (np.pi * f * np.sqrt(er) * tan_delta) / c
    alpha_d_db = alpha_d * 8.686
    return (alpha_c_db + alpha_d_db) * L

# ============================================================
# 功能 1: 逆向設計優化器
# ============================================================

def evaluate_design(params: np.ndarray, constraints: DesignConstraints) -> Dict:
    """評估一組設計參數的性能"""
    w, h, s, t = params
    geo = StriplineGeometry(w=w, h=h, s=s, t=t, L=constraints.length_mm, n_channels=constraints.n_channels)
    Z0 = calc_stripline_impedance(geo, constraints.er)
    Z0_error = abs(Z0 - constraints.target_Z0)
    f = constraints.frequency_GHz * 1e9
    ct = calc_crosstalk_stripline(geo, constraints.er, f)
    temp_map = {"300K → 40K": (300, 40), "40K → 4K": (40, 4), "4K → 1K": (4, 1), "1K → 100mK": (1, 0.1)}
    Th, Tc = temp_map.get(constraints.temperature_stage, (40, 4))
    boundary = ThermalBoundary(Th, Tc, constraints.temperature_stage)
    mat_name = constraints.conductor.split(" ")[0] if " " in constraints.conductor else constraints.conductor
    materials = MaterialStack(layers=[
        {"material": mat_name, "thickness": t, "width": w * 1000},
        {"material": "Polyimide_Kapton", "thickness": h * 1000 * 2, "width": s * 0.8 * 1000},
        {"material": mat_name, "thickness": t, "width": s * 0.8 * 1000}
    ])
    thermal = calc_thermal_load(geo, boundary, materials)
    loss = calc_insertion_loss(geo, constraints.er, constraints.tan_delta, f, mat_name)
    total_thickness = 2 * h + 3 * (t / 1000)
    return {
        "Z0": Z0, "Z0_error": Z0_error, "NEXT_dB": ct["NEXT_dB"], "FEXT_dB": ct["FEXT_dB"],
        "thermal_per_channel_uW": thermal["per_channel_uW"], "IL_dB": loss,
        "total_thickness_mm": total_thickness,
        "params": {"w_mm": w, "h_mm": h, "s_mm": s, "t_um": t}
    }

def objective_function(params: np.ndarray, constraints: DesignConstraints) -> float:
    """多目標優化目標函數 (加權懲罰法)"""
    eval_result = evaluate_design(params, constraints)
    penalty = 0.0
    if eval_result["Z0_error"] > constraints.Z0_tolerance:
        penalty += 1000 * (eval_result["Z0_error"] - constraints.Z0_tolerance) ** 2
    else:
        penalty += 0.1 * eval_result["Z0_error"]
    if eval_result["NEXT_dB"] > constraints.max_NEXT_dB:
        penalty += 500 * (eval_result["NEXT_dB"] - constraints.max_NEXT_dB) ** 2
    if eval_result["FEXT_dB"] > constraints.max_FEXT_dB:
        penalty += 500 * (eval_result["FEXT_dB"] - constraints.max_FEXT_dB) ** 2
    if eval_result["thermal_per_channel_uW"] > constraints.max_thermal_per_channel_uW:
        penalty += 100 * (eval_result["thermal_per_channel_uW"] - constraints.max_thermal_per_channel_uW) ** 2
    if eval_result["IL_dB"] > constraints.max_IL_dB:
        penalty += 200 * (eval_result["IL_dB"] - constraints.max_IL_dB) ** 2
    if eval_result["total_thickness_mm"] > constraints.max_total_thickness_mm:
        penalty += 500 * (eval_result["total_thickness_mm"] - constraints.max_total_thickness_mm) ** 2
    penalty += 0.5 * params[2]
    penalty += 1.0 * eval_result["total_thickness_mm"]
    return penalty

def optimize_stripline_design(constraints: DesignConstraints, method: str = "differential_evolution") -> Dict:
    """執行 Stripline 尺寸優化"""
    bounds = [
        (constraints.min_trace_width_um / 1000, constraints.max_trace_width_um / 1000),
        (constraints.min_dielectric_um / 1000, constraints.max_dielectric_um / 1000),
        (constraints.min_pitch_mm, constraints.max_pitch_mm),
        (1.0, 20.0)
    ]
    if method == "differential_evolution":
        result = differential_evolution(
            lambda p: objective_function(p, constraints),
            bounds=bounds, maxiter=500, tol=1e-6, seed=42, polish=True
        )
    else:
        x0 = [0.15, 0.15, 2.0, 5.0]
        result = minimize(
            lambda p: objective_function(p, constraints), x0,
            method="SLSQP", bounds=bounds, options={"maxiter": 500, "ftol": 1e-6}
        )
    optimal_eval = evaluate_design(result.x, constraints)
    return {
        "success": result.success,
        "optimal_params": {"w_mm": result.x[0], "h_mm": result.x[1], "s_mm": result.x[2], "t_um": result.x[3]},
        "performance": optimal_eval,
        "final_penalty": result.fun,
        "n_iterations": result.nit if hasattr(result, 'nit') else None
    }

def scan_design_space(constraints: DesignConstraints, n_points: int = 20):
    """掃描設計空間，生成 Pareto 前沿分析"""
    w_range = np.linspace(constraints.min_trace_width_um/1000, constraints.max_trace_width_um/1000, n_points)
    s_range = np.linspace(constraints.min_pitch_mm, constraints.max_pitch_mm, n_points)
    h_fixed = 0.15
    t_fixed = 5.0
    results = []
    for w in w_range:
        for s in s_range:
            if s <= w:
                continue
            params = np.array([w, h_fixed, s, t_fixed])
            eval_r = evaluate_design(params, constraints)
            eval_r["w_mm"] = w
            eval_r["s_mm"] = s
            results.append(eval_r)
    return pd.DataFrame(results)

# ============================================================
# 功能 2: 材料/Via 優化器
# ============================================================

def calc_return_loss(Z0_design: float, Z0_actual: float) -> float:
    """計算反射損耗 RL = -20*log10(|Γ|)"""
    gamma = (Z0_actual - Z0_design) / (Z0_actual + Z0_design)
    return -20 * np.log10(abs(gamma))

def calc_via_impedance_discontinuity(specs: MaterialViaSpecs, Z0_line: float) -> Dict:
    """計算 Via 引入的阻抗不連續性與損耗"""
    d_via = specs.via_diameter_um / 1e6
    h_total = specs.n_dielectric_layers * specs.dielectric_thickness_um / 1e6
    L_via = (MU_0 / (2 * np.pi)) * h_total * np.log(4 * h_total / d_via)
    d_pad = d_via * 1.5
    C_via = EPS_0 * specs.er * np.pi * (d_pad**2 - d_via**2) / (4 * h_total)
    Z_via = np.sqrt(L_via / C_via) if C_via > 0 else 1e6
    gamma_via = (Z_via - Z0_line) / (Z_via + Z0_line)
    RL_via = -20 * np.log10(abs(gamma_via))
    f = specs.frequency_GHz * 1e9
    omega = 2 * np.pi * f
    IL_inductive = 20 * np.log10(np.sqrt(1 + (omega * L_via / Z0_line)**2))
    IL_capacitive = 20 * np.log10(np.sqrt(1 + (omega * C_via * Z0_line)**2))
    IL_via_total = IL_inductive + IL_capacitive
    return {
        "L_via_H": L_via, "C_via_F": C_via, "Z_via_ohm": Z_via, "RL_via_dB": RL_via,
        "IL_via_inductive_dB": IL_inductive, "IL_via_capacitive_dB": IL_capacitive,
        "IL_via_total_dB": IL_via_total,
        "discontinuity_severity": "minor" if RL_via > 20 else "moderate" if RL_via > 10 else "severe"
    }

def calc_multilayer_loss(specs: MaterialViaSpecs) -> Dict:
    """計算多層膜結構的總損耗 (IL) 與反射 (RL)"""
    if specs.temperature_K < 1:
        tan_d = specs.tan_delta_20mK
    elif specs.temperature_K < 10:
        tan_d = specs.tan_delta_4K
    else:
        tan_d = specs.tan_delta_rt
    w = specs.trace_width_um / 1e6
    t = specs.conductor_thickness_um / 1e6
    h = specs.dielectric_thickness_um / 1e6
    L = specs.length_mm / 1000
    f = specs.frequency_GHz * 1e9
    b = 2 * h
    We = w + (t / np.pi) * (1 + np.log(2 * b / t)) if w / b > 0.35 else w
    Z0 = (30 * np.pi / np.sqrt(specs.er)) * (b / We)
    sigma = {"Ag": 6.3e7, "NbTi": 1e6, "Cu": 5.8e7}.get(specs.conductor_material, 6.3e7)
    delta_s = np.sqrt(2 / (MU_0 * sigma * 2 * np.pi * f))
    kr = 1 + (2 / np.pi) * np.arctan(1.4 * (specs.conductor_roughness_um / 1e6 / delta_s)**2)
    Rs = kr / (sigma * delta_s)
    alpha_c = Rs / (Z0 * w)
    alpha_c_db = alpha_c * 8.686
    c = 3e8
    alpha_d = (np.pi * f * np.sqrt(specs.er) * tan_d) / c
    alpha_d_db = alpha_d * 8.686
    alpha_r_db = 0.01 * specs.frequency_GHz
    IL_total = (alpha_c_db + alpha_d_db + alpha_r_db) * L
    RL = calc_return_loss(50.0, Z0)
    via_impact = calc_via_impedance_discontinuity(specs, Z0)
    IL_with_via = IL_total + via_impact["IL_via_total_dB"] * (specs.length_mm / 10) * specs.via_density_per_mm
    return {
        "Z0_ohm": Z0, "IL_conductor_dB": alpha_c_db * L, "IL_dielectric_dB": alpha_d_db * L,
        "IL_radiation_dB": alpha_r_db * L, "IL_total_dB": IL_total, "IL_with_via_dB": IL_with_via,
        "RL_dB": RL, "RL_with_via_dB": min(RL, via_impact["RL_via_dB"]),
        "tan_delta_effective": tan_d, "skin_depth_um": delta_s * 1e6,
        "surface_roughness_factor": kr, "via_impact": via_impact,
        "loss_breakdown": {
            "conductor_pct": (alpha_c_db * L) / IL_total * 100 if IL_total > 0 else 0,
            "dielectric_pct": (alpha_d_db * L) / IL_total * 100 if IL_total > 0 else 0,
            "radiation_pct": (alpha_r_db * L) / IL_total * 100 if IL_total > 0 else 0
        }
    }

def optimize_material_via(specs: MaterialViaSpecs, target_IL_dB: float = 2.0, target_RL_dB: float = 20.0) -> Dict:
    """優化材料與 Via 參數以達成目標 IL/RL"""
    def objective(x):
        s = MaterialViaSpecs(
            er=x[0], dielectric_thickness_um=x[1], via_density_per_mm=x[2],
            conductor_thickness_um=x[3], trace_width_um=specs.trace_width_um,
            pitch_mm=specs.pitch_mm, length_mm=specs.length_mm,
            frequency_GHz=specs.frequency_GHz, temperature_K=specs.temperature_K,
            conductor_material=specs.conductor_material
        )
        result = calc_multilayer_loss(s)
        penalty = 0
        if result["IL_total_dB"] > target_IL_dB:
            penalty += 100 * (result["IL_total_dB"] - target_IL_dB)**2
        if result["RL_dB"] < target_RL_dB:
            penalty += 50 * (target_RL_dB - result["RL_dB"])**2
        penalty += 0.01 * (x[1] * specs.n_dielectric_layers)
        return penalty
    bounds = [(2.0, 5.0), (50.0, 300.0), (0.5, 5.0), (1.0, 20.0)]
    result = differential_evolution(objective, bounds, maxiter=300, seed=42)
    optimal_specs = MaterialViaSpecs(
        er=result.x[0], dielectric_thickness_um=result.x[1],
        via_density_per_mm=result.x[2], conductor_thickness_um=result.x[3],
        trace_width_um=specs.trace_width_um, pitch_mm=specs.pitch_mm,
        length_mm=specs.length_mm, frequency_GHz=specs.frequency_GHz,
        temperature_K=specs.temperature_K, conductor_material=specs.conductor_material
    )
    return {
        "optimal_specs": optimal_specs,
        "performance": calc_multilayer_loss(optimal_specs),
        "final_penalty": result.fun
    }

# ============================================================
# 使用範例
# ============================================================
from streamlit import empty
MENU, 表單=[], ['最優尺寸', '材料/打洞Via', '']		#智能化, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
狀態=empty()
if menu==len(表單): #
  pass
elif menu==MENU[0]: #智能化
    輸出="=" * 60
    輸出+="Cri/oFlex3 智能化設計優化器 - 使用範例\n"
    輸出+="=" * 60

    # 範例 1: 逆向設計
    輸出+="\n[範例 1] 逆向設計優化"
    輸出+="-" * 40
    constraints = DesignConstraints(
        target_Z0=50.0, Z0_tolerance=3.0,
        max_NEXT_dB=-45.0, max_FEXT_dB=-45.0,
        max_IL_dB=2.5, max_thermal_per_channel_uW=150.0,
        n_channels=8, frequency_GHz=6.0, length_mm=400,
        temperature_stage="40K → 4K", conductor="NbTi"
    )
    result = optimize_stripline_design(constraints)
    if result["success"]:
        輸出+=f"✅ 優化成功！\n"
        p = result["optimal_params"]
        perf = result["performance"]
        輸出+=f"   最優尺寸: w={p['w_mm']*1000:.1f}μm, h={p['h_mm']*1000:.1f}μm, s={p['s_mm']:.2f}mm, t={p['t_um']:.1f}μm\n"
        輸出+=f"   性能預測: Z₀={perf['Z0']:.2f}Ω, NEXT={perf['NEXT_dB']:.1f}dB, 熱負載={perf['thermal_per_channel_uW']:.1f}μW"
    狀態.code(輸出)

elif menu==MENU[1]: #
    # 範例 2: 材料/Via 優化
    輸出="\n[範例 2] 材料/Via 優化\n"
    輸出+="-" * 40
    specs = MaterialViaSpecs(
        er=3.4, conductor_material="NbTi", temperature_K=4.0,
        frequency_GHz=6.0, length_mm=400, trace_width_um=150
    )
    result2 = optimize_material_via(specs, target_IL_dB=2.0, target_RL_dB=20.0)
    opt_s = result2["optimal_specs"]
    opt_p = result2["performance"]
    輸出+=f"✅ 優化完成！\n"
    輸出+=f"   最優參數: εr={opt_s.er:.2f}, 介電厚={opt_s.dielectric_thickness_um:.1f}μm, Via密度={opt_s.via_density_per_mm:.2f}/mm\n"
    輸出+=f"   性能: IL={opt_p['IL_total_dB']:.3f}dB, RL={opt_p['RL_dB']:.1f}dB, Z₀={opt_p['Z0_ohm']:.2f}Ω"
    狀態.code(輸出)

with sidebar:
  """Cri/oFlex3 智能化設計優化器模組
=================================
針對 NbTi/Ag + Polyimide 多層膜柔性 Stripline 的逆向設計與材料優化工具

功能:
1. 逆向設計：給定規格約束 → 自動找出最優 Stripline 尺寸
2. 材料/Via 優化：給定材料參數 → 計算並優化 IL/RL

依賴: numpy, scipy, pandas, matplotlib
"""
