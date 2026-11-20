from streamlit import button, checkbox, columns, dataframe, download_button, error, info, markdown, metric, multiselect, number_input, pyplot, radio, set_page_config, sidebar, slider, spinner, subheader, success, table, tabs, write, text_input, session_state
from matplotlib.pyplot import Circle, Polygon, Rectangle, colorbar, figure, subplots, tight_layout
from numpy import arctan, array, exp, linspace, log, log10, mean, pi, sqrt
from json import dumps
from pandas import DataFrame

from pandas import DataFrame
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Dict, List, Tuple
import json
import pandas as pd
from scipy.optimize import minimize, differential_evolution, NonlinearConstraint
from scipy.interpolate import interp1d
import warnings

from scipy.special import ellipk, ellipe
from enum import Enum
warnings.filterwarnings('ignore')

# ============================================================
# 物理常數與材料參數
# ============================================================

# 真空磁導率
MU_0 = 4 * pi * 1e-7  # H/m

# 真空介電常數
EPS_0 = 8.854e-12  # F/m

# 玻爾茲曼常數
K_B = 1.381e-23  # J/K

# 材料熱導率參數 (W/m·K)
# 基於文獻數據擬合
MATERIAL_THERMAL = {
    "Ag": {
        "type": "power_law",
        "A": 420,      # 300K 參考值
        "alpha": 1.0,  # 高溫區
        "low_temp": {
            "A": 2000,
            "alpha": 2.5  # T < 20K
        }
    },
    "NbTi": {
        "type": "superconducting",
        "Tc": 9.2,     # K
        "normal_k": 10, # 正常態熱導率
        "sc_k": 0.001   # 超導態 (極低)
    },
    "Polyimide_Kapton": {
        "type": "power_law",
        "A": 0.155,
        "alpha": 1.0
    },
    "Cu": {
        "type": "power_law",
        "A": 400,
        "alpha": 1.0,
        "low_temp": {
            "A": 1500,
            "alpha": 2.3
        }
    }
}

# 介電常數與損耗
DIELECTRIC = {
    "Polyimide_Kapton": {
        "εr": 3.4,
        "tan_delta_rt": 0.003,
        "tan_delta_4K": 3e-5,   # 文獻值 ~2.2e-5 @ 20mK
        "tan_delta_20mK": 2.2e-5
    }
}

# ============================================================
# 數據類別定義
# ============================================================


# ============================================================
# 功能 1: 介電質多層膜 Stripline 物理尺寸動態示意圖
# ============================================================


# ============================================================
# 智能化設計優化器核心模組
# ============================================================


# ============================================================
# 材料庫定義 (補充)
# ============================================================

class MaterialType(Enum):
    CONDUCTOR = "conductor"
    DIELECTRIC = "dielectric"
    SUPERCONDUCTOR = "superconductor"
    NORMAL_METAL = "normal_metal"

@dataclass
class MaterialProperties:
    """材料物理性質"""
    name: str
    material_type: MaterialType
    conductivity_300K: float
    thermal_conductivity_300K: float
    conductivity_4K: float = None
    superconducting_Tc: float = None
    superconducting_gap: float = None
    er_300K: float = 1.0
    er_4K: float = None
    tan_delta_300K: float = 0.01
    tan_delta_4K: float = None
    tan_delta_20mK: float = None
    thermal_conductivity_4K: float = None
    thermal_expansion: float = 0.0
    specific_heat: float = 0.0
    youngs_modulus: float = 0.0
    poisson_ratio: float = 0.0
    density: float = 0.0
    min_thickness_um: float = 0.1
    max_thickness_um: float = 100.0
    roughness_um: float = 0.5

MATERIAL_LIBRARY = {
    "NbTi": MaterialProperties(
        name="NbTi", material_type=MaterialType.SUPERCONDUCTOR,
        conductivity_300K=1e6, conductivity_4K=1e6,
        superconducting_Tc=9.2, superconducting_gap=1.5e-3,
        thermal_conductivity_300K=10, thermal_conductivity_4K=0.001,
        density=6500, min_thickness_um=1.0, max_thickness_um=20.0, roughness_um=0.3
    ),
    "Ag": MaterialProperties(
        name="Ag", material_type=MaterialType.NORMAL_METAL,
        conductivity_300K=6.3e7, conductivity_4K=5.0e7,
        thermal_conductivity_300K=420, thermal_conductivity_4K=2000,
        density=10500, min_thickness_um=0.5, max_thickness_um=50.0, roughness_um=0.5
    ),
    "Cu": MaterialProperties(
        name="Cu", material_type=MaterialType.NORMAL_METAL,
        conductivity_300K=5.8e7, conductivity_4K=4.5e7,
        thermal_conductivity_300K=400, thermal_conductivity_4K=1500,
        density=8960, min_thickness_um=0.5, max_thickness_um=50.0, roughness_um=0.8
    ),
    "Al": MaterialProperties(
        name="Al", material_type=MaterialType.NORMAL_METAL,
        conductivity_300K=3.5e7, conductivity_4K=2.8e7,
        thermal_conductivity_300K=237, thermal_conductivity_4K=800,
        density=2700, min_thickness_um=1.0, max_thickness_um=50.0, roughness_um=0.6
    ),
    "Polyimide_Kapton": MaterialProperties(
        name="Polyimide_Kapton", material_type=MaterialType.DIELECTRIC,
        er_300K=3.4, er_4K=3.2,
        conductivity_300K=3.5e7, conductivity_4K=2.8e7,
        tan_delta_300K=0.003, tan_delta_4K=3e-5, tan_delta_20mK=2.2e-5,
        thermal_conductivity_300K=0.155, thermal_conductivity_4K=0.02,
        thermal_expansion=20, density=1420, youngs_modulus=2.5, poisson_ratio=0.34,
        min_thickness_um=12.5, max_thickness_um=250.0, roughness_um=0.1
    ),
    "Polyimide_UPILEX": MaterialProperties(
        name="Polyimide_UPILEX", material_type=MaterialType.DIELECTRIC,
        er_300K=3.5, er_4K=3.3,
        conductivity_300K=3.5e7, conductivity_4K=2.8e7,
        tan_delta_300K=0.002, tan_delta_4K=2e-5, tan_delta_20mK=1.5e-5,
        thermal_conductivity_300K=0.29, thermal_conductivity_4K=0.03,
        density=1450, youngs_modulus=8.8, poisson_ratio=0.35,
        min_thickness_um=12.5, max_thickness_um=125.0, roughness_um=0.05
    ),
    "Al2O3": MaterialProperties(
        name="Al2O3", material_type=MaterialType.DIELECTRIC,
        er_300K=9.8, er_4K=9.6,
        conductivity_300K=3.5e7, conductivity_4K=2.8e7,
        tan_delta_300K=1e-4, tan_delta_4K=5e-6,
        thermal_conductivity_300K=30, thermal_conductivity_4K=200,
        density=3970, youngs_modulus=300, poisson_ratio=0.22,
        min_thickness_um=100.0, max_thickness_um=500.0, roughness_um=0.2
    ),
}

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


def evaluate_design(params, constraints):
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
    return {"Z0": Z0, "Z0_error": Z0_error, "NEXT_dB": ct["NEXT_dB"], "FEXT_dB": ct["FEXT_dB"],
            "thermal_per_channel_uW": thermal["per_channel_uW"], "IL_dB": loss,
            "total_thickness_mm": total_thickness, "params": {"w_mm": w, "h_mm": h, "s_mm": s, "t_um": t}}


def objective_function(params, constraints):
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


def optimize_stripline_design(constraints, method="differential_evolution"):
    """執行 Stripline 尺寸優化"""
    bounds = [
        (constraints.min_trace_width_um / 1000, constraints.max_trace_width_um / 1000),
        (constraints.min_dielectric_um / 1000, constraints.max_dielectric_um / 1000),
        (constraints.min_pitch_mm, constraints.max_pitch_mm),
        (1.0, 20.0)
    ]
    if method == "differential_evolution":
        result = differential_evolution(lambda p: objective_function(p, constraints), bounds=bounds,
                                        maxiter=500, tol=1e-6, seed=42, polish=True)
    else:
        x0 = [0.15, 0.15, 2.0, 5.0]
        result = minimize(lambda p: objective_function(p, constraints), x0, method="SLSQP",
                        bounds=bounds, options={"maxiter": 500, "ftol": 1e-6})
    optimal_eval = evaluate_design(result.x, constraints)
    return {"success": result.success, "optimal_params": {"w_mm": result.x[0], "h_mm": result.x[1], "s_mm": result.x[2], "t_um": result.x[3]},
            "performance": optimal_eval, "final_penalty": result.fun, "n_iterations": result.nit if hasattr(result, 'nit') else None}


def scan_design_space(constraints, n_points=20):
    """掃描設計空間"""
    w_range = linspace(constraints.min_trace_width_um/1000, constraints.max_trace_width_um/1000, n_points)
    s_range = linspace(constraints.min_pitch_mm, constraints.max_pitch_mm, n_points)
    h_fixed = 0.15
    t_fixed = 5.0
    results = []
    for w in w_range:
        for s in s_range:
            if s <= w:
                continue
            params = array([w, h_fixed, s, t_fixed])
            eval_r = evaluate_design(params, constraints)
            eval_r["w_mm"] = w
            eval_r["s_mm"] = s
            results.append(eval_r)
    return DataFrame(results)


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


def calc_return_loss(Z0_design, Z0_actual):
    """計算反射損耗 RL = -20*log10(|Γ|)"""
    gamma = (Z0_actual - Z0_design) / (Z0_actual + Z0_design)
    return -20 * log10(abs(gamma))


def calc_via_impedance_discontinuity(specs, Z0_line):
    """計算 Via 引入的阻抗不連續性與損耗"""
    d_via = specs.via_diameter_um / 1e6
    h_total = specs.n_dielectric_layers * specs.dielectric_thickness_um / 1e6
    L_via = (MU_0 / (2 * pi)) * h_total * log(4 * h_total / d_via)
    d_pad = d_via * 1.5
    C_via = EPS_0 * specs.er * pi * (d_pad**2 - d_via**2) / (4 * h_total)
    Z_via = sqrt(L_via / C_via) if C_via > 0 else 1e6
    gamma_via = (Z_via - Z0_line) / (Z_via + Z0_line)
    RL_via = -20 * log10(abs(gamma_via))
    f = specs.frequency_GHz * 1e9
    omega = 2 * pi * f
    IL_inductive = 20 * log10(sqrt(1 + (omega * L_via / Z0_line)**2))
    IL_capacitive = 20 * log10(sqrt(1 + (omega * C_via * Z0_line)**2))
    IL_via_total = IL_inductive + IL_capacitive
    return {"L_via_H": L_via, "C_via_F": C_via, "Z_via_ohm": Z_via, "RL_via_dB": RL_via,
            "IL_via_inductive_dB": IL_inductive, "IL_via_capacitive_dB": IL_capacitive,
            "IL_via_total_dB": IL_via_total,
            "discontinuity_severity": "minor" if RL_via > 20 else "moderate" if RL_via > 10 else "severe"}


def calc_multilayer_loss(specs):
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
    We = w + (t / pi) * (1 + log(2 * b / t)) if w / b > 0.35 else w
    Z0 = (30 * pi / sqrt(specs.er)) * (b / We)
    sigma = {"Ag": 6.3e7, "NbTi": 1e6, "Cu": 5.8e7}.get(specs.conductor_material, 6.3e7)
    delta_s = sqrt(2 / (MU_0 * sigma * 2 * pi * f))
    kr = 1 + (2 / pi) * arctan(1.4 * (specs.conductor_roughness_um / 1e6 / delta_s)**2)
    Rs = kr / (sigma * delta_s)
    alpha_c = Rs / (Z0 * w)
    alpha_c_db = alpha_c * 8.686
    c = 3e8
    alpha_d = (pi * f * sqrt(specs.er) * tan_d) / c
    alpha_d_db = alpha_d * 8.686
    alpha_r_db = 0.01 * specs.frequency_GHz
    IL_total = (alpha_c_db + alpha_d_db + alpha_r_db) * L
    RL = calc_return_loss(50.0, Z0)
    via_impact = calc_via_impedance_discontinuity(specs, Z0)
    IL_with_via = IL_total + via_impact["IL_via_total_dB"] * (specs.length_mm / 10) * specs.via_density_per_mm
    return {"Z0_ohm": Z0, "IL_conductor_dB": alpha_c_db * L, "IL_dielectric_dB": alpha_d_db * L,
            "IL_radiation_dB": alpha_r_db * L, "IL_total_dB": IL_total, "IL_with_via_dB": IL_with_via,
            "RL_dB": RL, "RL_with_via_dB": min(RL, via_impact["RL_via_dB"]),
            "tan_delta_effective": tan_d, "skin_depth_um": delta_s * 1e6,
            "surface_roughness_factor": kr, "via_impact": via_impact,
            "loss_breakdown": {"conductor_pct": (alpha_c_db * L) / IL_total * 100 if IL_total > 0 else 0,
                               "dielectric_pct": (alpha_d_db * L) / IL_total * 100 if IL_total > 0 else 0,
                               "radiation_pct": (alpha_r_db * L) / IL_total * 100 if IL_total > 0 else 0}}


def optimize_material_via(specs, target_IL_dB=2.0, target_RL_dB=20.0):
    """優化材料與 Via 參數以達成目標 IL/RL"""
    def objective(x):
        s = MaterialViaSpecs(er=x[0], dielectric_thickness_um=x[1], via_density_per_mm=x[2],
                             conductor_thickness_um=x[3], trace_width_um=specs.trace_width_um,
                             pitch_mm=specs.pitch_mm, length_mm=specs.length_mm,
                             frequency_GHz=specs.frequency_GHz, temperature_K=specs.temperature_K,
                             conductor_material=specs.conductor_material)
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
    optimal_specs = MaterialViaSpecs(er=result.x[0], dielectric_thickness_um=result.x[1],
                                     via_density_per_mm=result.x[2], conductor_thickness_um=result.x[3],
                                     trace_width_um=specs.trace_width_um, pitch_mm=specs.pitch_mm,
                                     length_mm=specs.length_mm, frequency_GHz=specs.frequency_GHz,
                                     temperature_K=specs.temperature_K, conductor_material=specs.conductor_material)
    return {"optimal_specs": optimal_specs, "performance": calc_multilayer_loss(optimal_specs), "final_penalty": result.fun}


def draw_stripline_cross_section(geo: StriplineGeometry, pitch: float, 
                                  via_enabled: bool, via_diameter: float, 
                                  via_density: float, n_channels: int):
    """
    繪製 Stripline 橫截面動態示意圖

    結構示意 (G-S-G 多層膜):

    ┌─────────────────────────────────────────┐  ← 上接地層 (Top GND)
    │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │
    ├─────────────────────────────────────────┤  ← 上介電層 (Polyimide)
    │     ═══════     ═══════     ═══════   │  ← 信號層 (Signal)
    │     S1    GND   S2    GND   S3        │
    ├─────────────────────────────────────────┤  ← 下介電層 (Polyimide)
    │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │
    └─────────────────────────────────────────┘  ← 下接地層 (Bottom GND)
         ↑_________↑
            pitch
    """
    fig, ax = subplots(figsize=(14, 6))

    # 尺寸轉換 (mm)
    w = geo.w  # 信號線寬
    h = geo.h  # 單層介電厚
    t = geo.t / 1000  # μm -> mm (導體厚)
    s = pitch  # 通道間距
    total_h = 2 * h + 3 * t  # 總厚度

    # 繪圖區域設定
    n_draw = min(n_channels, 6)  # 最多畫 6 個通道
    total_width = s * (n_draw + 0.5)
    margin = s * 0.3

    ax.set_xlim(-margin, total_width + margin)
    ax.set_ylim(-margin, total_h + margin)
    ax.set_aspect('equal')
    ax.axis('off')

    # 顏色定義
    colors = {
        'polyimide': '#E8DCC8',      # 淡棕色 (Polyimide)
        'ag_nbti': '#B8860B',        # 暗金色 (Ag/NbTi 導體)
        'via': '#8B4513',            # 深棕色 (Via)
        'text': '#2C3E50',           # 深藍灰 (文字)
        'dimension': '#E74C3C',      # 紅色 (尺寸線)
        'arrow': '#3498DB'           # 藍色 (箭頭)
    }

    # 繪製多層膜結構
    # 上接地層
    gnd_top = Rectangle((-margin/2, 2*h + 2*t), total_width + margin, t, 
                             facecolor=colors['ag_nbti'], edgecolor='black', linewidth=1.5)
    ax.add_patch(gnd_top)
    ax.text(total_width/2, 2*h + 2*t + t/2, 'Top GND (Ag/NbTi)', 
            ha='center', va='center', fontsize=9, color='white', fontweight='bold')

    # 上介電層
    dielectric_top = Rectangle((-margin/2, h + t), total_width + margin, h, 
                                    facecolor=colors['polyimide'], edgecolor='black', linewidth=1.5, alpha=0.7)
    ax.add_patch(dielectric_top)
    ax.text(-margin/2 + 0.1, h + t + h/2, 'Polyimide\nεr=3.4', 
            ha='left', va='center', fontsize=8, color=colors['text'])

    # 信號層 (多通道)
    for i in range(n_draw):
        x_center = s * (i + 0.5)
        sig = Rectangle((x_center - w/2, h + t - t/2), w, t, 
                            facecolor=colors['ag_nbti'], edgecolor='black', linewidth=1.5)
        ax.add_patch(sig)
        ax.text(x_center, h + t, f'S{i+1}', ha='center', va='center', 
                fontsize=8, color='white', fontweight='bold')

        # 接地分隔 (G-S-G)
        if i < n_draw - 1:
            gnd_sep_x = x_center + s/2
            gnd_sep = Rectangle((gnd_sep_x - w*0.3/2, h + t - t/2), w*0.3, t,
                                    facecolor='#D4AF37', edgecolor='black', linewidth=1)
            ax.add_patch(gnd_sep)
            ax.text(gnd_sep_x, h + t, 'G', ha='center', va='center',
                    fontsize=7, color='white')

    # 下介電層
    dielectric_bottom = Rectangle((-margin/2, 0), total_width + margin, h, 
                                       facecolor=colors['polyimide'], edgecolor='black', linewidth=1.5, alpha=0.7)
    ax.add_patch(dielectric_bottom)
    ax.text(-margin/2 + 0.1, h/2, 'Polyimide\nεr=3.4', 
            ha='left', va='center', fontsize=8, color=colors['text'])

    # 下接地層
    gnd_bottom = Rectangle((-margin/2, -t), total_width + margin, t, 
                                facecolor=colors['ag_nbti'], edgecolor='black', linewidth=1.5)
    ax.add_patch(gnd_bottom)
    ax.text(total_width/2, -t/2, 'Bottom GND (Ag/NbTi)', 
            ha='center', va='center', fontsize=9, color='white', fontweight='bold')

    # Via Stitching (如果啟用)
    if via_enabled:
        via_spacing = 1.0 / via_density  # mm
        n_vias_x = int(total_width / via_spacing) + 1
        via_r = via_diameter / 2000  # μm -> mm (半徑)

        for i in range(n_vias_x):
            x_via = i * via_spacing
            if x_via > total_width:
                break
            # 上層 Via
            via_top = Circle((x_via, 2*h + 2*t - via_r), via_r, 
                                  facecolor=colors['via'], edgecolor='black', linewidth=1)
            ax.add_patch(via_top)
            # 下層 Via
            via_bottom = Circle((x_via, -t + via_r), via_r,
                                    facecolor=colors['via'], edgecolor='black', linewidth=1)
            ax.add_patch(via_bottom)
            # 連接線
            ax.plot([x_via, x_via], [2*h + 2*t - 2*via_r, -t + 2*via_r], 
                    color=colors['via'], linewidth=2, alpha=0.6)

        ax.text(total_width + margin*0.5, h + t, f'Via\nØ{via_diameter}μm\n{via_density}/mm', 
                ha='left', va='center', fontsize=8, color=colors['via'],
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # 尺寸標註 - 信號線寬度 w
    arrow_y = -margin * 0.6
    ax.annotate('', xy=(s*0.5 - w/2, arrow_y), xytext=(s*0.5 + w/2, arrow_y),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text(s*0.5, arrow_y - 0.15, f'w = {w*1000:.0f} μm', ha='center', va='top',
            fontsize=9, color=colors['dimension'], fontweight='bold')

    # 尺寸標註 - Pitch s
    arrow_y2 = -margin * 1.0
    ax.annotate('', xy=(s*0.5, arrow_y2), xytext=(s*1.5, arrow_y2),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text(s, arrow_y2 - 0.15, f'pitch = {s:.1f} mm', ha='center', va='top',
            fontsize=9, color=colors['dimension'], fontweight='bold')

    # 尺寸標註 - 介電厚度 h
    ax.annotate('', xy=(total_width + margin*0.4, h + t), xytext=(total_width + margin*0.4, 2*h + 2*t),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text(total_width + margin*0.6, 1.5*h + t, f'h = {h*1000:.0f} μm', ha='left', va='center',
            fontsize=9, color=colors['dimension'], fontweight='bold', rotation=90)

    # 尺寸標註 - 總厚度
    ax.annotate('', xy=(-margin*0.4, -t), xytext=(-margin*0.4, 2*h + 3*t),
                arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=1.5))
    ax.text(-margin*0.6, h + t, f'total = {total_h*1000:.0f} μm', ha='right', va='center',
            fontsize=9, color=colors['arrow'], fontweight='bold', rotation=90)

    # 標題
    ax.set_title(f'Cri/oFlex3 Stripline Cross-Section\n({n_channels} channels, G-S-G configuration)', 
                 fontsize=13, fontweight='bold', pad=20)

    # 圖例
    legend_elements = [
        Rectangle((0,0),1,1, facecolor=colors['ag_nbti'], edgecolor='black', label='Ag/NbTi Conductor'),
        Rectangle((0,0),1,1, facecolor=colors['polyimide'], edgecolor='black', alpha=0.7, label='Polyimide (εr=3.4)'),
        Circle((0,0), 0.1, facecolor=colors['via'], label='GND Via')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=8, framealpha=0.9)

    tight_layout()
    return fig


def draw_stripline_3d_schematic(geo: StriplineGeometry, pitch: float, length: float, n_channels: int):
    """
    繪製 Stripline 3D 立體示意圖 (簡化透視)
    """
    fig, ax = subplots(figsize=(14, 5))

    w = geo.w
    h = geo.h
    t = geo.t / 1000
    L = length / 10  # 縮放顯示
    s = pitch
    n_draw = min(n_channels, 4)

    # 透視參數
    skew = 0.3
    depth = L

    # 繪製上接地層 (3D 透視)
    for i in range(n_draw):
        x0 = s * i + 0.2
        # 上表面
        poly_top = Polygon([
            [x0, 2*h + 3*t],
            [x0 + w, 2*h + 3*t],
            [x0 + w + skew*depth, 2*h + 3*t + 0.1],
            [x0 + skew*depth, 2*h + 3*t + 0.1]
        ], facecolor='#B8860B', edgecolor='black', alpha=0.9)
        ax.add_patch(poly_top)

        # 信號線
        poly_sig = Polygon([
            [x0, h + t],
            [x0 + w, h + t],
            [x0 + w + skew*depth, h + t + 0.1],
            [x0 + skew*depth, h + t + 0.1]
        ], facecolor='#DAA520', edgecolor='black', alpha=0.9)
        ax.add_patch(poly_sig)

        # 下接地層
        poly_bot = Polygon([
            [x0, 0],
            [x0 + w, 0],
            [x0 + w + skew*depth, 0.1],
            [x0 + skew*depth, 0.1]
        ], facecolor='#B8860B', edgecolor='black', alpha=0.9)
        ax.add_patch(poly_bot)

        # 側面介電層線條
        ax.plot([x0, x0 + skew*depth], [2*h + 3*t, 2*h + 3*t + 0.1], 'k-', linewidth=0.5, alpha=0.3)
        ax.plot([x0, x0 + skew*depth], [0, 0.1], 'k-', linewidth=0.5, alpha=0.3)

    # 長度標註
    ax.annotate('', xy=(s*n_draw + 0.5, -0.3), xytext=(0.2, -0.3),
                arrowprops=dict(arrowstyle='<->', color='red', lw=2))
    ax.text(s*n_draw/2, -0.6, f'L = {length} mm', ha='center', va='top',
            fontsize=11, color='red', fontweight='bold')

    ax.set_xlim(-0.5, s*n_draw + 2)
    ax.set_ylim(-1, 2*h + 4*t + 0.5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Cri/oFlex3 Stripline 3D Perspective View\n(Multilayer Polyimide + Ag/NbTi)', 
                 fontsize=13, fontweight='bold')

    tight_layout()
    return fig



# ============================================================
# 功能 2: 串擾推導公式展示
# ============================================================

def show_crosstalk_derivation(geo: StriplineGeometry, er: float, f: float):
    """
    展示完整的串擾推導公式與計算過程
    """
    w = geo.w / 1000  # mm -> m
    s = geo.s / 1000   # mm -> m  
    h = geo.h / 1000   # mm -> m
    t = geo.t / 1e6    # μm -> m
    L = geo.L / 1000   # mm -> m

    eps = er * EPS_0

    # 計算實際數值
    # 1. 單位長度自電容 Cs
    # 平行板近似 (對稱 stripline, 上下各一接地層)
    Cs = eps * w / h  # F/m

    # 2. 單位長度互電容 Cm
    # 基於平行線耦合模型 (經驗公式)
    Cm = eps * w / s * exp(-pi * s / (2 * h))

    # 3. 單位長度自電感 Ls
    Ls = MU_0 * h / w

    # 4. 單位長度互電感 Lm
    Lm = MU_0 * h / (2 * pi) * log(1 + 2*h/s)

    # 5. 電容耦合係數
    kc = Cm / (Cs + Cm)

    # 6. 電感耦合係數
    kL = Lm / (Ls + Lm)

    # 7. 綜合耦合係數
    k = 0.5 * (kc + kL)

    # 8. 相位常數
    c = 3e8
    beta = 2 * pi * f * sqrt(er) / c

    # 9. 近端串擾 (NEXT)
    theta = beta * L
    if theta < 1:
        NEXT_linear = k * theta / 2
    else:
        NEXT_linear = k / 2
    NEXT_dB = 20 * log10(max(abs(NEXT_linear), 1e-12))

    # 10. 遠端串擾 (FEXT)
    FEXT_linear = k * theta
    FEXT_dB = 20 * log10(max(abs(FEXT_linear), 1e-12))

    return {
        "Cs": Cs,
        "Cm": Cm,
        "Ls": Ls,
        "Lm": Lm,
        "kc": kc,
        "kL": kL,
        "k": k,
        "beta": beta,
        "theta": theta,
        "NEXT_linear": NEXT_linear,
        "NEXT_dB": NEXT_dB,
        "FEXT_linear": FEXT_linear,
        "FEXT_dB": FEXT_dB,
        "w_m": w,
        "s_m": s,
        "h_m": h,
        "L_m": L
    }


def render_formula_section():
    """
    渲染完整的公式推導區塊 (Streamlit markdown)
    """
    formula_md = r"""
    ---

    ## 📐 串擾推導公式詳解

    ### 一、幾何與材料參數

    | 符號 | 定義 | 單位 |
    |------|------|------|
    | $w$ | 信號線寬度 | m |
    | $t$ | 導體厚度 | m |
    | $h$ | 單層介電厚度 (上下對稱) | m |
    | $s$ | 通道間距 (Pitch) | m |
    | $L$ | 傳輸線長度 | m |
    | $arepsilon_r$ | 相對介電常數 (Polyimide = 3.4) | — |
    | $arepsilon_0$ | 真空介電常數 = $8.854 \times 10^{-12}$ | F/m |
    | $\mu_0$ | 真空磁導率 = $4\pi \times 10^{-7}$ | H/m |
    | $f$ | 工作頻率 | Hz |

    ---

    ### 二、單位長度電容

    #### 2.1 自電容 $C_s$ (Self-Capacitance)

    對於對稱 Stripline (Ground-Signal-Ground)，信號線與上下兩接地層形成平行板電容：

    $$
    C_s = \varepsilon_0 \varepsilon_r \cdot \frac{w}{h}
    $$

    **物理意義**：單位長度信號線對單一接地層的電容。由於上下兩層並聯，總自電容為 $2C_s$。

    ---

    #### 2.2 互電容 $C_m$ (Mutual Capacitance)

    相鄰信號線間的電容耦合，採用經驗衰減模型：

    $$
    C_m = \varepsilon_0 \varepsilon_r \cdot \frac{w}{s} \cdot \exp\left(-\frac{\pi s}{2h}\right)
    $$

    **物理意義**：
    - $\frac{w}{s}$：幾何比例因子
    - $\exp\left(-\frac{\pi s}{2h}\right)$：介電屏蔽衰減項，$s \\gg h$ 時快速衰減

    ---

    ### 三、單位長度電感

    #### 3.1 自電感 $L_s$ (Self-Inductance)

    $$
    L_s = \mu_0 \cdot \frac{h}{w}
    $$

    **物理意義**：信號線電流迴路 (Signal → GND) 的單位長度電感。

    ---

    #### 3.2 互電感 $L_m$ (Mutual Inductance)

    基於平行導線互感公式：

    $$
    L_m = \frac{\mu_0}{2\pi} \cdot h \cdot \ln\left(1 + \frac{2h}{s}\right)
    $$

    **物理意義**：相鄰通道電流產生的磁通耦合。

    ---

    ### 四、耦合係數

    #### 4.1 電容耦合係數 $k_c$

    $$
    k_c = \frac{C_m}{C_s + C_m}
    $$

    **物理意義**：互電容佔總電容的比例。$k_c \ll 1$ 為弱耦合條件。

    ---

    #### 4.2 電感耦合係數 $k_L$

    $$
    k_L = \frac{L_m}{L_s + L_m}
    $$

    **物理意義**：互電感佔總電感的比例。

    ---

    #### 4.3 綜合耦合係數 $k$

    對於對稱 Stripline，綜合耦合係數為電容與電感耦合的算術平均：

    $$
    k = \frac{1}{2}(k_c + k_L)
    $$

    ---

    ### 五、傳播參數

    #### 5.1 相位常數 $eta$

    $$
    \beta = \frac{2\pi f \sqrt{\varepsilon_r}}{c} = \omega \sqrt{\varepsilon_r} / c
    $$

    其中 $c = 3 \times 10^8$ m/s 為光速。

    ---

    #### 5.2 電長度 $	heta$

    $$
    \theta = \beta \cdot L = \frac{2\pi f L \sqrt{\varepsilon_r}}{c}
    $$

    **判斷條件**：
    - $\theta \ll 1$：電短線，串擾與長度成正比
    - $\theta \approx 1$：需考慮分佈效應
    - $\theta \\gg 1$：飽和區，串擾趨近耦合係數

    ---

    ### 六、串擾公式

    #### 6.1 近端串擾 (NEXT - Near-End Crosstalk)

    在弱耦合條件下 ($k \ll 1$)：

    $$
    \text{NEXT}_{linear} = \begin{cases}
    \displaystyle\frac{k \cdot \theta}{2}, & \theta < 1 \\
    \displaystyle\frac{k}{2}, & \theta \\geq 1
    \end{cases}
    $$

    轉換為 dB：

    $$
    \text{NEXT}_{dB} = 20 \log_{10}(\text{NEXT}_{linear})
    $$

    **物理意義**：
    - 近端串擾為後向傳播的干擾波
    - 在電短線區 ($\theta < 1$)，與電長度 $\theta$ 成正比
    - 在電長線區飽和於 $k/2$

    ---

    #### 6.2 遠端串擾 (FEXT - Far-End Crosstalk)

    $$
    \text{FEXT}_{linear} = k \cdot \theta = k \cdot \frac{2\pi f L \sqrt{\varepsilon_r}}{c}
    $$

    轉換為 dB：

    $$
    \text{FEXT}_{dB} = 20 \log_{10}(\text{FEXT}_{linear})
    $$

    **物理意義**：
    - 遠端串擾為前向傳播的干擾波
    - 與電長度 $\theta$ 始終成正比
    - 高頻長線時 FEXT 通常大於 NEXT

    ---

    ### 七、Via Stitching 屏蔽改善

    接地 Via 提供額外的橫向接地路徑，改善屏蔽效能：

    $$
    \Delta S_{via} = 20 \log_{10}\left(1 + 0.5 \cdot \rho_{via} \cdot s\right)
    $$

    其中 $\rho_{via}$ 為 Via 密度 (個/mm)。

    改善後串擾：

    $$
    \text{NEXT}'_{dB} = \text{NEXT}_{dB} - \Delta S_{via}
    $$

    ---

    ### 八、設計準則

    | 指標 | 目標值 | 改善方法 |
    |------|--------|----------|
    | NEXT | < -40 dB | 增大 pitch、增加 via 密度、減小 $h$ |
    | FEXT | < -40 dB | 縮短線長、降低頻率、使用低 $\varepsilon_r$ 材料 |
    | $k$ | < 0.01 | $s > 3h$ 為經驗法則 |
    | $Z_0$ | 50 ± 5 Ω | 調整 $w/h$ 比例 |

    ---
    """
    return formula_md


def show_formula_calculation(geo: StriplineGeometry, er: float, f: float):
    """
    顯示當前參數下的逐步計算過程
    """
    calc = show_crosstalk_derivation(geo, er, f)

    calc_md = rf"""
    ### 📊 當前參數逐步計算

    **輸入參數：**
    - $w$ = {calc['w_m']*1e6:.1f} μm = {calc['w_m']:.4e} m
    - $s$ = {calc['s_m']*1e3:.2f} mm = {calc['s_m']:.4e} m
    - $h$ = {calc['h_m']*1e6:.1f} μm = {calc['h_m']:.4e} m
    - $L$ = {calc['L_m']*1e3:.1f} mm = {calc['L_m']:.4e} m
    - $\varepsilon_r$ = {er}
    - $f$ = {f/1e9:.2f} GHz

    ---

    **Step 1: 單位長度自電容 $C_s$**

    $$
    C_s = \varepsilon_0 \varepsilon_r \frac{{w}}{{h}} = (8.854 \times 10^{{-12}}) \times {er} \times \frac{{{calc['w_m']:.4e}}}{{{calc['h_m']:.4e}}} = {calc['Cs']:.4e} \text{{ F/m}}
    $$

    **Step 2: 單位長度互電容 $C_m$**

    $$
    C_m = \varepsilon_0 \varepsilon_r \frac{{w}}{{s}} \exp\left(-\frac{{\pi s}}{{2h}}\right) = {calc['Cm']:.4e} \text{{ F/m}}
    $$

    **Step 3: 單位長度自電感 $L_s$**

    $$
    L_s = \mu_0 \frac{{h}}{{w}} = (4\pi \times 10^{{-7}}) \times \frac{{{calc['h_m']:.4e}}}{{{calc['w_m']:.4e}}} = {calc['Ls']:.4e} \text{{ H/m}}
    $$

    **Step 4: 單位長度互電感 $L_m$**

    $$
    L_m = \frac{{\mu_0}}{{2\pi}} h \ln\left(1 + \frac{{2h}}{{s}}\right) = {calc['Lm']:.4e} \text{{ H/m}}
    $$

    **Step 5: 耦合係數**

    $$
    k_c = \frac{{C_m}}{{C_s + C_m}} = \frac{{{calc['Cm']:.4e}}}{{{calc['Cs']:.4e} + {calc['Cm']:.4e}}} = {calc['kc']:.6f}
    $$

    $$
    k_L = \frac{{L_m}}{{L_s + L_m}} = \frac{{{calc['Lm']:.4e}}}{{{calc['Ls']:.4e} + {calc['Lm']:.4e}}} = {calc['kL']:.6f}
    $$

    $$
    k = \frac{{1}}{{2}}(k_c + k_L) = {calc['k']:.6f}
    $$

    **Step 6: 相位常數與電長度**

    $$
    \beta = \frac{{2\pi f \sqrt{{\varepsilon_r}}}}{{c}} = \frac{{2\pi \times {f:.3e} \times \sqrt{{{er}}}}}{{3 \times 10^8}} = {calc['beta']:.4e} \text{{ rad/m}}
    $$

    $$
    \theta = \beta L = {calc['beta']:.4e} \times {calc['L_m']:.4e} = {calc['theta']:.4f}
    $$

    **Step 7: 串擾計算**

    {"$\theta < 1$ (電短線區)，使用線性公式：" if calc['theta'] < 1 else "$\theta \\geq 1$ (電長線區)，使用飽和公式："}

    $$
    \text{{NEXT}}_{{linear}} = {calc['NEXT_linear']:.6e} \quad \Rightarrow \quad \text{{NEXT}}_{{dB}} = 20\log_{{10}}({calc['NEXT_linear']:.6e}) = \mathbf{{{calc['NEXT_dB']:.2f} \text{{ dB}}}}
    $$

    $$
    \text{{FEXT}}_{{linear}} = {calc['FEXT_linear']:.6e} \quad \Rightarrow \quad \text{{FEXT}}_{{dB}} = 20\log_{{10}}({calc['FEXT_linear']:.6e}) = \mathbf{{{calc['FEXT_dB']:.2f} \text{{ dB}}}}
    $$

    ---

    **驗證：**
    - $k \ll 1$？ {'✅ 是' if calc['k'] < 0.1 else '⚠️ 否，耦合過強'}
    - NEXT < -40 dB？ {'✅ 達標' if calc['NEXT_dB'] < -40 else '⚠️ 未達標'}
    - FEXT < -40 dB？ {'✅ 達標' if calc['FEXT_dB'] < -40 else '⚠️ 未達標'}
    """

    return calc_md, calc


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
    T_hot: float    # 熱端溫度 (K)
    T_cold: float   # 冷端溫度 (K)
    stage: str      # 溫度階段標識

@dataclass
class MaterialStack:
    """多層膜結構"""
    layers: List[Dict]  # [{"material": str, "thickness": float, "width": float}]

# ============================================================
# 計算核心函數
# ============================================================

def calc_stripline_impedance(geo: StriplineGeometry, er: float) -> float:
    """
    計算 Stripline 特性阻抗 (Wadell 公式)
    Z0 = (30π / sqrt(er)) * (b / We)
    其中 b = 2h (總介電厚度), We = 有效寬度
    """
    b = 2 * geo.h  # 總介電厚度 mm
    w = geo.w
    t = geo.t / 1000  # μm -> mm

    # 有效寬度修正 (考慮厚度效應)
    if w / b > 0.35:
        We = w + (t / pi) * (1 + log(2 * b / t))
    else:
        We = w - (b / (2 * pi)) * (1 - 0.5 * exp(-4 * pi * w / b)) * log(1 + 2 * t / b)

    Z0 = (30 * pi / sqrt(er)) * (b / We)
    return Z0

def calc_crosstalk_stripline(geo: StriplineGeometry, er: float, f: float) -> Dict[str, float]:
    """
    計算 Stripline 串擾 (近端 NEXT 與遠端 FEXT)

    基於耦合係數模型:
    - 電容耦合係數: kc = Cm / (Cs + Cm)
    - 電感耦合係數: kL = Lm / (Ls + Lm)

    對於對稱 stripline (G-S-G), 串擾主要由互容與互感決定
    """
    w = geo.w  # mm
    s = geo.s  # mm
    h = geo.h  # mm
    L = geo.L / 1000  # mm -> m

    # 介電常數
    eps = er * EPS_0

    # 單位長度電容 (F/m) - 簡化模型
    # 對於寬度 w, 間距 s 的平行線
    C_self = eps * (w / (2 * h))  # 簡化自電容

    # 互容 (基於平行板近似修正)
    # Cm ~ eps * w / s * exp(-π*s/(2h))  (經驗公式)
    Cm = eps * (w / 1000) / (s / 1000) * exp(-pi * s / (2 * h))

    # 單位長度電感 (H/m)
    L_self = MU_0 * (2 * h / w) * 1e-3  # 簡化

    # 互感
    Lm = MU_0 * (h / (2 * pi * s)) * 1e-3

    # 耦合係數
    kc = Cm / (C_self + Cm) if (C_self + Cm) > 0 else 0
    kL = Lm / (L_self + Lm) if (L_self + Lm) > 0 else 0

    # 綜合耦合係數
    k = 0.5 * (kc + kL)

    # 相位常數
    c = 3e8  # m/s
    beta = 2 * pi * f * sqrt(er) / c

    # 近端串擾 (NEXT) - dB
    # NEXT ≈ 20*log10(k * beta * L / 2) for weak coupling
    if beta * L < 1:
        next_linear = k * beta * L / 2
        NEXT_db = 20 * log10(max(next_linear, 1e-12))
    else:
        NEXT_db = 20 * log10(k / 2)

    # 遠端串擾 (FEXT) - dB
    # FEXT ∝ k * beta * L (與長度成正比)
    fext_linear = k * beta * L
    FEXT_db = 20 * log10(max(fext_linear, 1e-12))

    return {
        "NEXT_dB": NEXT_db,
        "FEXT_dB": FEXT_db,
        "coupling_k": k,
        "Cm_per_m": Cm,
        "Lm_per_m": Lm,
        "beta": beta
    }

def calc_thermal_conductivity(material: str, T: float) -> float:
    """
    計算材料在溫度 T 下的熱導率 (W/m·K)
    """
    props = MATERIAL_THERMAL.get(material, None)
    if props is None:
        return 1.0

    if props["type"] == "superconducting":
        Tc = props["Tc"]
        if T < Tc * 0.5:  # 超導態 (簡化)
            return props["sc_k"]
        elif T < Tc:
            # 過渡區
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

def calc_thermal_load(geo: StriplineGeometry, boundary: ThermalBoundary, 
                      materials: MaterialStack) -> Dict[str, float]:
    """
    計算通過傳輸線的熱負載 (W)

    使用積分形式:
    P = (A/L) * ∫ k(T) dT

    對於多層結構，等效熱導為各層並聯
    """
    T_hot = boundary.T_hot
    T_cold = boundary.T_cold
    L_m = geo.L / 1000  # mm -> m

    # 數值積分計算熱導
    n_points = 100
    T_range = linspace(T_cold, T_hot, n_points)

    total_kA = 0  # 總熱導截面積積

    for layer in materials.layers:
        mat = layer["material"]
        thickness = layer["thickness"] / 1e6  # μm -> m
        width = layer["width"] / 1000  # mm -> m
        area = thickness * width

        # 計算該層的平均熱導率
        k_avg = mean([calc_thermal_conductivity(mat, T) for T in T_range])
        total_kA += k_avg * area

    # 熱流計算 (簡化線性梯度)
    # P = kA * ΔT / L
    delta_T = T_hot - T_cold
    P = total_kA * delta_T / L_m

    # 每通道熱負載
    P_per_channel = P / geo.n_channels

    return {
        "total_power_W": P,
        "per_channel_W": P_per_channel,
        "per_channel_uW": P_per_channel * 1e6,
        "per_channel_nW": P_per_channel * 1e9,
        "kA_total": total_kA,
        "delta_T": delta_T
    }

def calc_insertion_loss(geo: StriplineGeometry, er: float, tan_delta: float, 
                        f: float, material: str = "Ag") -> float:
    """
    計算插入損耗 (dB)

    包含:
    1. 導體損耗 (skin effect)
    2. 介電損耗
    """
    w = geo.w / 1000  # mm -> m
    t = geo.t / 1e6   # μm -> m
    L = geo.L / 1000  # mm -> m
    h = geo.h / 1000  # mm -> m

    # 導體電導率
    sigma = {"Ag": 6.3e7, "NbTi": 1e6, "Cu": 5.8e7}.get(material, 6.3e7)

    # 趨膚深度
    delta_s = sqrt(2 / (MU_0 * sigma * 2 * pi * f))

    # 導體損耗 (dB/m) - 簡化公式
    # αc = Rs / (Z0 * w) 
    Rs = 1 / (sigma * delta_s)  # 表面電阻
    Z0 = 50  # 假設匹配
    alpha_c = Rs / (Z0 * w)  # Np/m
    alpha_c_db = alpha_c * 8.686  # dB/m

    # 介電損耗 (dB/m)
    # αd = (π * f * sqrt(er) * tanδ) / c
    c = 3e8
    alpha_d = (pi * f * sqrt(er) * tan_delta) / c  # Np/m
    alpha_d_db = alpha_d * 8.686  # dB/m

    total_loss_db = (alpha_c_db + alpha_d_db) * L

    return total_loss_db

def calc_via_impact(pitch: float, via_diameter: float, via_density: float) -> Dict:
    """
    計算 Via stitching 對串擾的改善

    via_density: vias per mm
    """
    # Via 間距
    via_spacing = 1.0 / via_density  # mm

    # 屏蔽效能改善 (經驗公式)
    # 更密集的 via 提供更好的接地連續性
    shielding_improvement = 20 * log10(1 + 0.5 * via_density * pitch)

    return {
        "via_spacing_mm": via_spacing,
        "shielding_improvement_dB": shielding_improvement,
        "recommended_density": min(2.0, 1.0 / (pitch / 4))  # 推薦密度
    }

# ============================================================
# Streamlit UI
# ============================================================



# ============================================================
# 智能化設計優化器 UI 函數
# ============================================================



# ============================================================
# 擴展智能化設計 UI - 完整物理參數分析
# ============================================================

def render_extended_optimizer_section():
    """渲染擴展優化器 UI"""
    markdown("---")
    header("🔬 完整物理參數分析與動態優化")

    ext_tab1, ext_tab2, ext_tab3 = tabs([
        "📊 完整參數分析",
        "🔗 相依條件動態優化", 
        "🎯 多目標 Pareto 前沿"
    ])

    # ========== Tab 1: 完整參數分析 ==========
    with ext_tab1:
        subheader("📊 傳輸線完整物理參數分析")
        markdown("分析所有電氣、熱學、機械、Via 參數")

        col_input, col_output = columns([1, 2])

        with col_input:
            markdown("**🔧 幾何參數**")
            w_full = number_input("信號線寬 (mm)", 0.05, 1.0, 0.15, 0.01, key="full_w")
            h_full = number_input("介電層厚 (mm)", 0.025, 0.5, 0.15, 0.005, key="full_h")
            s_full = number_input("Pitch (mm)", 0.5, 5.0, 2.0, 0.1, key="full_s")
            t_sig_full = number_input("信號層厚 (μm)", 1.0, 50.0, 5.0, 0.5, key="full_tsig")
            t_gnd_full = number_input("接地層厚 (μm)", 1.0, 50.0, 5.0, 0.5, key="full_tgnd")
            n_layer_full = slider("介電層數", 1, 6, 2, 1, key="full_nlayer")
            len_full = number_input("線長 (mm)", 100, 1500, 400, 50, key="full_len")
            n_ch_full = radio("通道數", [4, 8, 16, 32], index=1, key="full_nch", horizontal=True)
            bend_full = number_input("彎曲半徑 (mm)", 1.0, 50.0, 5.0, 0.5, key="full_bend")

            markdown("**🧪 材料選擇**")
            mat_sig_full = radio("信號導體", ["NbTi", "Ag", "Cu", "Al"], index=0, key="full_matsig", horizontal=True)
            mat_gnd_full = radio("接地導體", ["NbTi", "Ag", "Cu", "Al"], index=0, key="full_matgnd", horizontal=True)
            mat_die_full = radio("介電材料", ["Polyimide_Kapton", "Polyimide_UPILEX", "Al2O3"], index=0, key="full_matdie", horizontal=True)

            markdown("**⚡ 環境條件**")
            T_hot_full = number_input("熱端溫度 (K)", 1.0, 300.0, 40.0, 1.0, key="full_thot")
            T_cold_full = number_input("冷端溫度 (K)", 0.01, 10.0, 4.0, 0.1, key="full_tcold")
            f_full = number_input("頻率 (GHz)", 0.1, 20.0, 6.0, 0.1, key="full_f")

            markdown("**🔩 Via 參數**")
            via_en_full = checkbox("啟用 Via", value=True, key="full_viaen")
            via_d_full = number_input("Via 直徑 (μm)", 50.0, 500.0, 150.0, 10.0, key="full_viad")
            via_den_full = slider("Via 密度", 0.5, 5.0, 2.0, 0.1, key="full_viaden")

            analyze_full = button("🔬 執行完整分析", type="primary", use_container_width=True, key="btn_analyze_full")

        with col_output:
            if analyze_full:
                with spinner("正在執行完整物理分析..."):
                    # 建立參數
                    geo = StriplineGeometry(
                        w_signal_mm=w_full, h_dielectric_mm=h_full, pitch_mm=s_full,
                        t_signal_um=t_sig_full, t_gnd_um=t_gnd_full, n_dielectric_layers=n_layer_full,
                        length_mm=len_full, n_channels=n_ch_full, bend_radius_mm=bend_full
                    )
                    via = ViaParameters(
                        enabled=via_en_full, diameter_um=via_d_full, density_per_mm=via_den_full
                    )
                    env = EnvironmentalConditions(
                        temperature_range_K=(T_hot_full, T_cold_full),
                        operating_frequency_GHz=f_full
                    )

                    analyzer = TransmissionLineAnalyzer(geo, via, env, mat_sig_full, mat_gnd_full, mat_die_full)
                    result = analyzer.full_analysis()

                success("✅ 分析完成！")

                # 摘要卡片
                markdown("### 📋 性能摘要")
                cols_summary = columns(5)
                with cols_summary[0]:
                    metric("Z₀", f"{result['summary']['Z0_ohm']:.2f} Ω")
                with cols_summary[1]:
                    metric("IL", f"{result['summary']['IL_dB']:.3f} dB")
                with cols_summary[2]:
                    metric("NEXT", f"{result['crosstalk']['NEXT_dB']:.1f} dB")
                with cols_summary[3]:
                    metric("熱負載", f"{result['summary']['thermal_per_channel_uW']:.1f} μW")
                with cols_summary[4]:
                    metric("厚度", f"{result['summary']['total_thickness_mm']:.3f} mm")

                # 詳細參數分頁
                detail_tabs = tabs(["⚡ 電氣", "📉 損耗", "📡 串擾", "🌡️ 熱學", "🔧 機械", "🔩 Via"])

                with detail_tabs[0]:
                    elec = result['electrical']
                    cols_e = columns(3)
                    with cols_e[0]:
                        metric("特性阻抗", f"{elec['Z0_ohm']:.2f} Ω")
                        metric("有效介電常數", f"{elec['ereff']:.3f}")
                    with cols_e[1]:
                        metric("相位速度", f"{elec['vp_m_s']:.3e} m/s")
                        metric("波長", f"{elec['wavelength_m']*1000:.2f} mm")
                    with cols_e[2]:
                        metric("延遲", f"{elec['delay_ns_m']:.2f} ns/m")
                        metric("電長度", f"{elec['theta_rad']:.3f} rad")

                with detail_tabs[1]:
                    loss = result['loss']
                    fig_loss, ax_loss = subplots(figsize=(8, 4))
                    categories = ['Conductor', 'Dielectric', 'Radiation', 'Leakage']
                    values = [loss['IL_conductor_dB'], loss['IL_dielectric_dB'], 
                             loss['IL_radiation_dB'], loss['IL_leakage_dB']]
                    colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
                    bars = ax_loss.bar(categories, values, color=colors, edgecolor='black')
                    ax_loss.set_ylabel("Loss (dB)")
                    ax_loss.set_title(f"Loss Breakdown @ {f_full} GHz")
                    for bar, val in zip(bars, values):
                        height = bar.get_height()
                        ax_loss.text(bar.get_x() + bar.get_width()/2., height,
                                    f'{val:.3f}', ha='center', va='bottom')
                    pyplot(fig_loss)

                    cols_l = columns(3)
                    with cols_l[0]:
                        metric("趨膚深度", f"{loss['skin_depth_um']:.2f} μm")
                    with cols_l[1]:
                        metric("粗糙度因子", f"{loss['surface_roughness_factor']:.3f}")
                    with cols_l[2]:
                        metric("表面電阻", f"{loss['Rs_ohm_sq']:.4f} Ω/sq")

                with detail_tabs[2]:
                    xt = result['crosstalk']
                    cols_x = columns(3)
                    with cols_x[0]:
                        metric("NEXT", f"{xt['NEXT_dB']:.1f} dB")
                        metric("FEXT", f"{xt['FEXT_dB']:.1f} dB")
                    with cols_x[1]:
                        metric("耦合係數 k", f"{xt['coupling_coefficient_k']:.4f}")
                        metric("電容耦合 kc", f"{xt['capacitive_coupling_kc']:.4f}")
                    with cols_x[2]:
                        metric("電感耦合 kL", f"{xt['inductive_coupling_kL']:.4f}")
                        metric("Via 改善", f"{xt['via_shielding_improvement_dB']:.1f} dB")

                    markdown("**單位長度參數:**")
                    write(f"- 自電容 Cs = {xt['Cs_per_m']:.3e} F/m")
                    write(f"- 互電容 Cm = {xt['Cm_per_m']:.3e} F/m")
                    write(f"- 自電感 Ls = {xt['Ls_per_m']:.3e} H/m")
                    write(f"- 互電感 Lm = {xt['Lm_per_m']:.3e} H/m")

                with detail_tabs[3]:
                    th = result['thermal']
                    cols_t = columns(3)
                    with cols_t[0]:
                        metric("總熱負載", f"{th['total_thermal_load_W']:.3e} W")
                        metric("每通道", f"{th['per_channel_uW']:.2f} μW")
                    with cols_t[1]:
                        metric("熱阻", f"{th['thermal_resistance_K_W']:.2f} K/W")
                        metric("溫度梯度", f"{th['temperature_gradient_K_m']:.2f} K/m")
                    with cols_t[2]:
                        metric("k_signal", f"{th['k_signal_W_m_K']:.2f} W/m·K")
                        metric("k_dielectric", f"{th['k_dielectric_W_m_K']:.4f} W/m·K")

                with detail_tabs[4]:
                    mech = result['mechanical']
                    cols_m = columns(3)
                    with cols_m[0]:
                        metric("總厚度", f"{mech['total_thickness_mm']:.3f} mm")
                        metric("總寬度", f"{mech['total_width_mm']:.1f} mm")
                    with cols_m[1]:
                        metric("質量", f"{mech['mass_g']:.3f} g")
                        metric("有效楊氏模量", f"{mech['effective_youngs_modulus_GPa']:.2f} GPa")
                    with cols_m[2]:
                        metric("柔性指數", f"{mech['flexibility_index']:.1f}")
                        metric("可彎曲", "✅" if mech['is_flexible'] else "❌")

                with detail_tabs[5]:
                    if result['via']['enabled']:
                        v = result['via']
                        cols_v = columns(3)
                        with cols_v[0]:
                            metric("Via 電感", f"{v['L_via_nH']:.3f} nH")
                            metric("Via 電容", f"{v['C_via_fF']:.3f} fF")
                        with cols_v[1]:
                            metric("Via 阻抗", f"{v['Z_via_ohm']:.1f} Ω")
                            metric("Via 反射", f"{v['RL_via_dB']:.1f} dB")
                        with cols_v[2]:
                            metric("總數量", f"{v['total_via_count']:.0f}")
                            metric("深徑比", f"{v['aspect_ratio']:.2f}")
                        markdown(f"**不連續性嚴重度:** {v['discontinuity_severity']}")
                    else:
                        info("Via 未啟用")

                # 匯出 JSON
                markdown("### 📥 匯出完整分析")
                download_button("下載完整分析 JSON",
                    data=json.dumps(result, indent=2, default=str),
                    file_name="full_analysis.json", mime="application/json")

    # ========== Tab 2: 相依條件動態優化 ==========
    with ext_tab2:
        subheader("🔗 相依條件動態優化")
        markdown("考慮材料-幾何-電氣-熱學-製程的相依關係，自動找出最優解")

        col_dyn, col_dyn_result = columns([1, 2])

        with col_dyn:
            markdown("**📋 性能約束**")
            dyn_z0 = number_input("目標 Z₀ (Ω)", 40.0, 60.0, 50.0, 1.0, key="dyn_z0")
            dyn_z0tol = number_input("Z₀ 容差 (Ω)", 1.0, 10.0, 3.0, 0.5, key="dyn_z0tol")
            dyn_max_il = number_input("最大 IL (dB)", 0.5, 10.0, 2.5, 0.1, key="dyn_il")
            dyn_min_rl = number_input("最小 RL (dB)", 5.0, 40.0, 20.0, 1.0, key="dyn_rl")
            dyn_max_next = number_input("最大 NEXT (dB)", -80.0, -20.0, -45.0, 1.0, key="dyn_next")
            dyn_max_fext = number_input("最大 FEXT (dB)", -80.0, -20.0, -45.0, 1.0, key="dyn_fext")
            dyn_max_thermal = number_input("最大熱負載 (μW)", 10.0, 500.0, 150.0, 10.0, key="dyn_thermal")
            dyn_max_thick = number_input("最大厚度 (mm)", 0.1, 2.0, 0.4, 0.05, key="dyn_thick")

            markdown("**🏭 製程約束**")
            dyn_min_w = number_input("最小線寬 (μm)", 25.0, 200.0, 50.0, 5.0, key="dyn_minw")
            dyn_max_w = number_input("最大線寬 (μm)", 100.0, 500.0, 300.0, 10.0, key="dyn_maxw")
            dyn_max_layer = slider("最大層數", 2, 10, 6, 1, key="dyn_maxlayer")

            markdown("**🧪 可用材料**")
            dyn_mats = multiselect("材料選擇", 
                ["NbTi", "Ag", "Cu", "Al", "Polyimide_Kapton", "Polyimide_UPILEX", "Al2O3"],
                default=["NbTi", "Ag", "Cu", "Polyimide_Kapton", "Polyimide_UPILEX"],
                key="dyn_mats")

            markdown("**🌡️ 環境**")
            dyn_thot = number_input("熱端 (K)", 10.0, 300.0, 40.0, 1.0, key="dyn_thot")
            dyn_tcold = number_input("冷端 (K)", 0.01, 10.0, 4.0, 0.1, key="dyn_tcold")
            dyn_freq = number_input("頻率 (GHz)", 0.1, 20.0, 6.0, 0.1, key="dyn_freq")
            dyn_len = number_input("線長 (mm)", 100, 1500, 400, 50, key="dyn_len")

            run_dyn = button("🚀 執行動態優化", type="primary", use_container_width=True, key="btn_dyn")

        with col_dyn_result:
            if run_dyn:
                with spinner("正在執行動態約束優化 (可能需要數分鐘)..."):
                    constraints = PerformanceConstraints(
                        target_Z0_ohm=dyn_z0, Z0_tolerance_ohm=dyn_z0tol,
                        max_insertion_loss_dB=dyn_max_il, min_return_loss_dB=dyn_min_rl,
                        max_crosstalk_NEXT_dB=dyn_max_next, max_crosstalk_FEXT_dB=dyn_max_fext,
                        max_thermal_load_per_channel_uW=dyn_max_thermal,
                        max_total_thickness_mm=dyn_max_thick
                    )
                    manufacturing = ManufacturingConstraints(
                        min_trace_width_um=dyn_min_w, max_trace_width_um=dyn_max_w,
                        max_layer_count=dyn_max_layer, available_materials=dyn_mats
                    )
                    env = EnvironmentalConditions(
                        temperature_range_K=(dyn_thot, dyn_tcold),
                        operating_frequency_GHz=dyn_freq
                    )

                    optimizer = DynamicConstraintOptimizer()
                    best = optimizer.optimize_with_dependencies(constraints, manufacturing, env, dyn_mats)

                if best:
                    success("✅ 動態優化完成！")

                    markdown("### 🏆 最優設計")
                    cols_best = columns(3)
                    with cols_best[0]:
                        markdown("**材料組合**")
                        write(f"信號: {best['materials']['signal']}")
                        write(f"接地: {best['materials']['ground']}")
                        write(f"介電: {best['materials']['dielectric']}")
                    with cols_best[1]:
                        markdown("**幾何參數**")
                        g = best['geometry']
                        write(f"w = {g['w_signal_mm']*1000:.1f} μm")
                        write(f"h = {g['h_dielectric_mm']*1000:.1f} μm")
                        write(f"s = {g['pitch_mm']:.2f} mm")
                        write(f"t_sig = {g['t_signal_um']:.1f} μm")
                        write(f"t_gnd = {g['t_gnd_um']:.1f} μm")
                        write(f"n_layer = {g['n_dielectric_layers']}")
                    with cols_best[2]:
                        markdown("**優化得分**")
                        write(f"得分: {best['score']:.2f}")
                        write(f"迭代: 多材料組合評估")

                    # 詳細分析最優設計
                    geo_opt = StriplineGeometry(
                        w_signal_mm=best['geometry']['w_signal_mm'],
                        h_dielectric_mm=best['geometry']['h_dielectric_mm'],
                        pitch_mm=best['geometry']['pitch_mm'],
                        t_signal_um=best['geometry']['t_signal_um'],
                        t_gnd_um=best['geometry']['t_gnd_um'],
                        n_dielectric_layers=best['geometry']['n_dielectric_layers'],
                        length_mm=dyn_len, n_channels=8
                    )
                    via_opt = ViaParameters(enabled=True)
                    analyzer_opt = TransmissionLineAnalyzer(geo_opt, via_opt, env,
                        best['materials']['signal'], best['materials']['ground'], best['materials']['dielectric'])
                    result_opt = analyzer_opt.full_analysis()

                    markdown("### 📊 最優設計性能驗證")
                    cols_verify = columns(5)
                    with cols_verify[0]:
                        z0_err = abs(result_opt['summary']['Z0_ohm'] - dyn_z0)
                        metric("Z₀", f"{result_opt['summary']['Z0_ohm']:.2f} Ω",
                                 delta=f"±{z0_err:.2f}Ω", 
                                 delta_color="normal" if z0_err < dyn_z0tol else "inverse")
                    with cols_verify[1]:
                        metric("IL", f"{result_opt['summary']['IL_dB']:.3f} dB",
                                 delta="OK" if result_opt['summary']['IL_dB'] < dyn_max_il else "FAIL",
                                 delta_color="normal" if result_opt['summary']['IL_dB'] < dyn_max_il else "inverse")
                    with cols_verify[2]:
                        metric("NEXT", f"{result_opt['crosstalk']['NEXT_dB']:.1f} dB",
                                 delta="OK" if result_opt['crosstalk']['NEXT_dB'] < dyn_max_next else "FAIL",
                                 delta_color="normal" if result_opt['crosstalk']['NEXT_dB'] < dyn_max_next else "inverse")
                    with cols_verify[3]:
                        metric("熱負載", f"{result_opt['summary']['thermal_per_channel_uW']:.1f} μW",
                                 delta="OK" if result_opt['summary']['thermal_per_channel_uW'] < dyn_max_thermal else "FAIL",
                                 delta_color="normal" if result_opt['summary']['thermal_per_channel_uW'] < dyn_max_thermal else "inverse")
                    with cols_verify[4]:
                        metric("厚度", f"{result_opt['summary']['total_thickness_mm']:.3f} mm",
                                 delta="OK" if result_opt['summary']['total_thickness_mm'] < dyn_max_thick else "FAIL",
                                 delta_color="normal" if result_opt['summary']['total_thickness_mm'] < dyn_max_thick else "inverse")

                    # 約束歷史
                    if optimizer.constraint_history:
                        markdown("### 📈 優化歷史")
                        hist_df = DataFrame([
                            {"材料組合": f"{h['materials'][0]}/{h['materials'][1]}/{h['materials'][2]}",
                             "得分": h['score'], "有效": h['valid']}
                            for h in optimizer.constraint_history[:10]
                        ])
                        dataframe(hist_df)

                    # 匯出
                    download_button("下載最優設計 JSON",
                        data=json.dumps(best, indent=2, default=str),
                        file_name="dynamic_optimal_design.json", mime="application/json")
                else:
                    error("❌ 未找到滿足所有約束的有效設計，請放寬約束條件")
            else:
                info("👈 請輸入約束條件，然後點擊「執行動態優化」")

    # ========== Tab 3: 多目標 Pareto 前沿 ==========
    with ext_tab3:
        subheader("🎯 多目標 Pareto 前沿優化")
        markdown("同時優化多個目標，生成非支配解集")

        col_pareto, col_pareto_result = columns([1, 2])

        with col_pareto:
            markdown("**🎯 目標函數**")
            obj1 = radio("目標 1", ["最小化 IL", "最小化 NEXT", "最小化熱負載", "最小化厚度", "最小化質量"], index=0, key="p_obj1", horizontal=True)
            obj2 = radio("目標 2", ["最小化 IL", "最小化 NEXT", "最小化熱負載", "最小化厚度", "最小化質量"], index=1, key="p_obj2", horizontal=True)
            obj3 = radio("目標 3", ["最小化 IL", "最小化 NEXT", "最小化熱負載", "最小化厚度", "最小化質量"], index=2, key="p_obj3", horizontal=True)

            markdown("**🔧 搜索空間**")
            p_w_min = number_input("w 最小 (mm)", 0.05, 0.5, 0.05, 0.01, key="p_wmin")
            p_w_max = number_input("w 最大 (mm)", 0.1, 1.0, 0.3, 0.01, key="p_wmax")
            p_h_min = number_input("h 最小 (mm)", 0.025, 0.5, 0.05, 0.005, key="p_hmin")
            p_h_max = number_input("h 最大 (mm)", 0.05, 0.5, 0.3, 0.005, key="p_hmax")
            p_s_min = number_input("s 最小 (mm)", 0.5, 3.0, 0.5, 0.1, key="p_smin")
            p_s_max = number_input("s 最大 (mm)", 1.0, 5.0, 3.0, 0.1, key="p_smax")

            markdown("**⚙️ 演算法參數**")
            p_pop = slider("種群大小", 10, 100, 30, 5, key="p_pop")
            p_gen = slider("世代數", 10, 200, 50, 10, key="p_gen")

            p_mat_sig = radio("信號材料", ["NbTi", "Ag", "Cu"], index=0, key="p_matsig", horizontal=True)
            p_mat_die = radio("介電材料", ["Polyimide_Kapton", "Polyimide_UPILEX"], index=0, key="p_matdie", horizontal=True)
            p_f = number_input("頻率 (GHz)", 0.1, 20.0, 6.0, 0.1, key="p_f")
            p_len = number_input("線長 (mm)", 100, 1500, 400, 50, key="p_len")

            run_pareto = button("🚀 執行 Pareto 優化", type="primary", use_container_width=True, key="btn_pareto")

        with col_pareto_result:
            if run_pareto:
                with spinner("正在執行 NSGA-II 風格多目標優化..."):
                    # 建立目標函數映射
                    def make_obj(obj_name, mat_sig, mat_die, f, len_mm):
                        def obj(x):
                            w, h, s = x
                            geo = StriplineGeometry(w_signal_mm=w, h_dielectric_mm=h, pitch_mm=s,
                                                   t_signal_um=5, t_gnd_um=5, n_dielectric_layers=2,
                                                   length_mm=len_mm, n_channels=8)
                            env = EnvironmentalConditions(operating_frequency_GHz=f)
                            analyzer = TransmissionLineAnalyzer(geo, ViaParameters(), env, mat_sig, mat_sig, mat_die)
                            try:
                                r = analyzer.full_analysis()
                            except:
                                return 1e10

                            if obj_name == "最小化 IL":
                                return r['loss']['IL_total_dB']
                            elif obj_name == "最小化 NEXT":
                                return -r['crosstalk']['NEXT_dB']  # 轉為正數
                            elif obj_name == "最小化熱負載":
                                return r['thermal']['per_channel_uW']
                            elif obj_name == "最小化厚度":
                                return r['mechanical']['total_thickness_mm']
                            elif obj_name == "最小化質量":
                                return r['mechanical']['mass_g']
                            return 1e10
                        return obj

                    objectives = [
                        make_obj(obj1, p_mat_sig, p_mat_die, p_f, p_len),
                        make_obj(obj2, p_mat_sig, p_mat_die, p_f, p_len),
                        make_obj(obj3, p_mat_sig, p_mat_die, p_f, p_len)
                    ]

                    pareto_opt = MultiObjectiveParetoOptimizer()
                    pareto_front = pareto_opt.optimize(
                        objectives=objectives,
                        bounds=[(p_w_min, p_w_max), (p_h_min, p_h_max), (p_s_min, p_s_max)],
                        population_size=p_pop, generations=p_gen
                    )

                success(f"✅ Pareto 優化完成！找到 {len(pareto_front)} 個非支配解")

                if pareto_front:
                    # 3D Pareto 圖
                    markdown("### 📊 Pareto 前沿 3D 視圖")

                    obj_names = [obj1.replace("最小化 ", ""), obj2.replace("最小化 ", ""), obj3.replace("最小化 ", "")]

                    fig_pareto_3d = figure(figsize=(10, 8))
                    ax_3d = fig_pareto_3d.add_subplot(111, projection='3d')

                    xs = [sol['objectives'][0] for sol in pareto_front]
                    ys = [sol['objectives'][1] for sol in pareto_front]
                    zs = [sol['objectives'][2] for sol in pareto_front]

                    scatter = ax_3d.scatter(xs, ys, zs, c=range(len(pareto_front)), 
                                           cmap='viridis', s=100, edgecolors='black')
                    ax_3d.set_xlabel(obj_names[0])
                    ax_3d.set_ylabel(obj_names[1])
                    ax_3d.set_zlabel(obj_names[2])
                    ax_3d.set_title("Pareto Front (3D)")
                    colorbar(scatter, ax=ax_3d, label="Solution Index")
                    pyplot(fig_pareto_3d)

                    # 解列表
                    markdown("### 📋 Pareto 解集")
                    pareto_data = []
                    for i, sol in enumerate(pareto_front[:20]):  # 最多顯示20個
                        pareto_data.append({
                            "解": i+1,
                            obj_names[0]: f"{sol['objectives'][0]:.3f}",
                            obj_names[1]: f"{sol['objectives'][1]:.3f}",
                            obj_names[2]: f"{sol['objectives'][2]:.3f}",
                            "w (mm)": f"{sol['parameters'][0]:.3f}",
                            "h (mm)": f"{sol['parameters'][1]:.3f}",
                            "s (mm)": f"{sol['parameters'][2]:.3f}"
                        })

                    dataframe(DataFrame(pareto_data))

                    # 匯出 Pareto 解集
                    download_button("下載 Pareto 解集 JSON",
                        data=json.dumps([{"objectives": s['objectives'], "parameters": s['parameters'].tolist()} 
                                        for s in pareto_front], indent=2),
                        file_name="pareto_front.json", mime="application/json")
            else:
                info("👈 請選擇目標函數與搜索空間，然後點擊「執行 Pareto 優化」")


def render_optimizer_section():
    """渲染智能化設計優化器 UI 區塊"""
    #markdown("---")
    subheader("🧠 智能化設計優化器")

    opt_tab1, opt_tab2 = tabs([
        "🔧 逆向設計：規格 → 尺寸", 
        "🧪 材料/Via 優化：參數 → IL/RL"
    ])

    # ========== Tab 1: 逆向設計 ==========
    with opt_tab1:
        subheader("🔧 逆向設計優化器")
        markdown("給定電氣/熱/機械規格約束，自動找出最優 Stripline 尺寸")

        col_spec, col_result = columns([1, 2])

        with col_spec:
            markdown("**📋 規格約束輸入**")

            markdown("<div style='color:#1f77b4;font-weight:bold;'>電氣規格</div>", unsafe_allow_html=True)
            target_Z0 = number_input("目標阻抗 Z₀ (Ω)", 40.0, 60.0, 50.0, 1.0, key="opt_z0")
            Z0_tol = number_input("阻抗容差 (±Ω)", 1.0, 10.0, 5.0, 0.5, key="opt_z0tol")
            max_NEXT = number_input("最大 NEXT (dB)", -80.0, -20.0, -40.0, 1.0, key="opt_next")
            max_FEXT = number_input("最大 FEXT (dB)", -80.0, -20.0, -40.0, 1.0, key="opt_fext")
            max_IL = number_input("最大插入損耗 (dB)", 0.5, 10.0, 3.0, 0.1, key="opt_il")

            markdown("<div style='color:#d62728;font-weight:bold;'>熱規格</div>", unsafe_allow_html=True)
            max_thermal = number_input("最大熱負載/通道 (μW)", 10.0, 1000.0, 200.0, 10.0, key="opt_thermal")
            temp_stage_opt = radio("溫度階段", ["300K → 40K", "40K → 4K", "4K → 1K", "1K → 100mK"], index=1, key="opt_temp", horizontal=True)

            markdown("<div style='color:#2ca02c;font-weight:bold;'>機械/製程規格</div>", unsafe_allow_html=True)
            max_thickness = number_input("最大總厚度 (mm)", 0.1, 2.0, 0.5, 0.05, key="opt_thick")
            n_ch_opt = radio("通道數", [4, 8, 16, 32], index=1, key="opt_ch", horizontal=True)
            freq_opt = number_input("工作頻率 (GHz)", 0.1, 20.0, 6.0, 0.1, key="opt_freq")
            length_opt = number_input("線長 (mm)", 100, 1500, 400, 50, key="opt_len")

            mat_opt = radio("導體材料", ["NbTi", "Ag", "Cu"], index=0, key="opt_mat", horizontal=True)

            run_optimize = button("🚀 執行優化", type="primary", use_container_width=True, key="btn_opt")

        with col_result:
            if run_optimize:
                with spinner("正在執行多目標優化 (Differential Evolution)..."):
                    constraints = DesignConstraints(
                        target_Z0=target_Z0, Z0_tolerance=Z0_tol,
                        max_NEXT_dB=max_NEXT, max_FEXT_dB=max_FEXT,
                        max_IL_dB=max_IL, max_thermal_per_channel_uW=max_thermal,
                        max_total_thickness_mm=max_thickness, n_channels=n_ch_opt,
                        frequency_GHz=freq_opt, length_mm=length_opt,
                        temperature_stage=temp_stage_opt, conductor=mat_opt
                    )
                    result = optimize_stripline_design(constraints)

                if result["success"]:
                    success("✅ 優化成功！")

                    markdown("### 📐 最優設計參數")
                    params = result["optimal_params"]
                    perf = result["performance"]

                    cols = columns(4)
                    with cols[0]:
                        metric("線寬 w", f"{params['w_mm']*1000:.1f} μm")
                    with cols[1]:
                        metric("介電厚 h", f"{params['h_mm']*1000:.1f} μm")
                    with cols[2]:
                        metric("Pitch s", f"{params['s_mm']:.2f} mm")
                    with cols[3]:
                        metric("導體厚 t", f"{params['t_um']:.1f} μm")

                    markdown("### 📊 性能預測")
                    cols2 = columns(4)
                    with cols2[0]:
                        delta_Z0 = abs(perf["Z0"] - target_Z0)
                        metric("特性阻抗", f"{perf['Z0']:.2f} Ω",
                                 delta=f"±{delta_Z0:.2f}Ω",
                                 delta_color="normal" if delta_Z0 < Z0_tol else "inverse")
                    with cols2[1]:
                        metric("NEXT", f"{perf['NEXT_dB']:.1f} dB",
                                 delta="OK" if perf['NEXT_dB'] < max_NEXT else "FAIL",
                                 delta_color="normal" if perf['NEXT_dB'] < max_NEXT else "inverse")
                    with cols2[2]:
                        metric("FEXT", f"{perf['FEXT_dB']:.1f} dB",
                                 delta="OK" if perf['FEXT_dB'] < max_FEXT else "FAIL",
                                 delta_color="normal" if perf['FEXT_dB'] < max_FEXT else "inverse")
                    with cols2[3]:
                        metric("熱負載", f"{perf['thermal_per_channel_uW']:.1f} μW",
                                 delta="OK" if perf['thermal_per_channel_uW'] < max_thermal else "FAIL",
                                 delta_color="normal" if perf['thermal_per_channel_uW'] < max_thermal else "inverse")

                    cols3 = columns(3)
                    with cols3[0]:
                        metric("插入損耗", f"{perf['IL_dB']:.2f} dB")
                    with cols3[1]:
                        metric("總厚度", f"{perf['total_thickness_mm']:.3f} mm")
                    with cols3[2]:
                        metric("迭代次數", f"{result['n_iterations']}")

                    # 設計空間掃描
                    markdown("### 🔍 設計空間 Pareto 分析")
                    with spinner("掃描設計空間..."):
                        df_scan = scan_design_space(constraints, n_points=12)

                    if not df_scan.empty:
                        fig_pareto, axes = subplots(1, 3, figsize=(15, 4))

                        sc1 = axes[0].scatter(df_scan['w_mm']*1000, df_scan['s_mm'], 
                                              c=df_scan['Z0'], cmap='RdYlGn_r', 
                                              s=50, edgecolors='black', linewidth=0.5)
                        axes[0].scatter(params['w_mm']*1000, params['s_mm'], 
                                       c='red', s=200, marker='*', edgecolors='black', linewidth=2,
                                       label='Optimal', zorder=5)
                        axes[0].set_xlabel("Trace Width (μm)")
                        axes[0].set_ylabel("Pitch (mm)")
                        axes[0].set_title("Characteristic Impedance Z₀")
                        colorbar(sc1, ax=axes[0], label="Z₀ (Ω)")
                        axes[0].legend()

                        sc2 = axes[1].scatter(df_scan['w_mm']*1000, df_scan['s_mm'],
                                              c=df_scan['NEXT_dB'], cmap='RdYlGn',
                                              s=50, edgecolors='black', linewidth=0.5)
                        axes[1].scatter(params['w_mm']*1000, params['s_mm'],
                                       c='red', s=200, marker='*', edgecolors='black', linewidth=2,
                                       label='Optimal', zorder=5)
                        axes[1].axhline(y=max_NEXT, color='red', linestyle='--', alpha=0.5)
                        axes[1].set_xlabel("Trace Width (μm)")
                        axes[1].set_ylabel("Pitch (mm)")
                        axes[1].set_title("Near-End Crosstalk (NEXT)")
                        colorbar(sc2, ax=axes[1], label="NEXT (dB)")
                        axes[1].legend()

                        sc3 = axes[2].scatter(df_scan['w_mm']*1000, df_scan['s_mm'],
                                              c=df_scan['thermal_per_channel_uW'], cmap='YlOrRd',
                                              s=50, edgecolors='black', linewidth=0.5)
                        axes[2].scatter(params['w_mm']*1000, params['s_mm'],
                                       c='red', s=200, marker='*', edgecolors='black', linewidth=2,
                                       label='Optimal', zorder=5)
                        axes[2].set_xlabel("Trace Width (μm)")
                        axes[2].set_ylabel("Pitch (mm)")
                        axes[2].set_title("Thermal Load per Channel")
                        colorbar(sc3, ax=axes[2], label="μW")
                        axes[2].legend()

                        tight_layout()
                        pyplot(fig_pareto)

                    # 匯出
                    markdown("### 📥 匯出最優設計")
                    optimal_design = {
                        "optimization_method": "Differential Evolution",
                        "constraints": {"target_Z0": target_Z0, "max_NEXT_dB": max_NEXT,
                                       "max_FEXT_dB": max_FEXT, "max_IL_dB": max_IL,
                                       "max_thermal_uW": max_thermal, "max_thickness_mm": max_thickness},
                        "optimal_dimensions": params,
                        "predicted_performance": {k: v for k, v in perf.items() if k != "params"}
                    }
                    download_button("下載最優設計 JSON",
                        data=json.dumps(optimal_design, indent=2, default=str),
                        file_name="optimal_stripline_design.json", mime="application/json")
                else:
                    error("❌ 優化失敗，請放寬約束條件後重試")
            else:
                info("👈 請在左側輸入規格約束，然後點擊「執行優化」")

    # ========== Tab 2: 材料/Via 優化 ==========
    with opt_tab2:
        subheader("🧪 材料與 Via 參數優化")
        markdown("給定材料介電係數、多層膜間距、Via 參數，計算 IL/RL 並優化")

        col_mat, col_ilrl = columns([1, 2])

        with col_mat:
            markdown("**🔬 材料參數輸入**")

            markdown("<div style='color:#1f77b4;font-weight:bold;'>介電材料</div>", unsafe_allow_html=True)
            er_input = number_input("相對介電常數 εr", 1.5, 10.0, 3.4, 0.1, key="mv_er")
            tan_rt = number_input("室溫損耗角 tanδ", 0.0001, 0.1, 0.003, 0.0001, format="%.4f", key="mv_tanrt")
            tan_4k = number_input("4K 損耗角 tanδ", 1e-6, 0.01, 3e-5, 1e-6, format="%.6f", key="mv_tan4k")
            tan_20mk = number_input("20mK 損耗角 tanδ", 1e-7, 0.001, 2.2e-5, 1e-7, format="%.7f", key="mv_tan20mk")
            n_dielectric = slider("介電層數", 1, 6, 2, 1, key="mv_nlayer")
            dielectric_thick = number_input("單層介電厚度 (μm)", 25.0, 500.0, 150.0, 5.0, key="mv_dthick")

            markdown("<div style='color:#ff7f0e;font-weight:bold;'>Via 設計</div>", unsafe_allow_html=True)
            via_en = checkbox("啟用 Via", value=True, key="mv_viaen")
            via_d = number_input("Via 直徑 (μm)", 50.0, 500.0, 150.0, 10.0, key="mv_viad")
            via_den = slider("Via 密度 (個/mm)", 0.5, 5.0, 2.0, 0.1, key="mv_viaden")

            markdown("<div style='color:#2ca02c;font-weight:bold;'>導體</div>", unsafe_allow_html=True)
            mat_ilrl = radio("導體", ["NbTi", "Ag", "Cu"], index=0, key="mv_mat", horizontal=True)
            cond_thick = number_input("導體厚度 (μm)", 1.0, 50.0, 5.0, 0.5, key="mv_cthick")
            roughness = number_input("表面粗糙度 (μm)", 0.1, 5.0, 0.5, 0.1, key="mv_rough")

            markdown("<div style='color:#d62728;font-weight:bold;'>幾何與操作</div>", unsafe_allow_html=True)
            w_ilrl = number_input("線寬 (μm)", 50.0, 500.0, 150.0, 10.0, key="mv_w")
            p_ilrl = number_input("Pitch (mm)", 0.5, 5.0, 2.0, 0.1, key="mv_p")
            l_ilrl = number_input("線長 (mm)", 100.0, 1500.0, 400.0, 50.0, key="mv_l")
            f_ilrl = number_input("頻率 (GHz)", 0.1, 20.0, 6.0, 0.1, key="mv_f")
            T_ilrl = number_input("溫度 (K)", 0.01, 300.0, 4.0, 1.0, key="mv_t")

            calc_ilrl = button("🔬 計算 IL/RL", type="primary", use_container_width=True, key="btn_calc_ilrl")

            markdown("---")
            markdown("**🎯 自動優化**")
            target_il = number_input("目標 IL (dB)", 0.1, 5.0, 2.0, 0.1, key="mv_til")
            target_rl = number_input("目標 RL (dB)", 10.0, 40.0, 20.0, 1.0, key="mv_trl")
            auto_opt = button("🚀 自動優化材料/Via", type="secondary", use_container_width=True, key="btn_autopt")

        with col_ilrl:
            if calc_ilrl:
                specs = MaterialViaSpecs(
                    er=er_input, tan_delta_rt=tan_rt, tan_delta_4K=tan_4k, tan_delta_20mK=tan_20mk,
                    n_dielectric_layers=n_dielectric, dielectric_thickness_um=dielectric_thick,
                    via_enabled=via_en, via_diameter_um=via_d, via_density_per_mm=via_den,
                    conductor_material=mat_ilrl, conductor_thickness_um=cond_thick,
                    conductor_roughness_um=roughness, trace_width_um=w_ilrl,
                    pitch_mm=p_ilrl, length_mm=l_ilrl, frequency_GHz=f_ilrl, temperature_K=T_ilrl
                )
                result_ilrl = calc_multilayer_loss(specs)

                success("✅ 計算完成！")

                markdown("### 📊 S 參數預測")
                cols_ilrl = columns(4)
                with cols_ilrl[0]:
                    metric("插入損耗 IL", f"{result_ilrl['IL_total_dB']:.3f} dB",
                             delta=f"含Via: {result_ilrl['IL_with_via_dB']:.3f} dB", delta_color="off")
                with cols_ilrl[1]:
                    metric("反射損耗 RL", f"{result_ilrl['RL_dB']:.1f} dB",
                             delta=f"含Via: {result_ilrl['RL_with_via_dB']:.1f} dB", delta_color="off")
                with cols_ilrl[2]:
                    metric("特性阻抗", f"{result_ilrl['Z0_ohm']:.2f} Ω")
                with cols_ilrl[3]:
                    metric("有效損耗角", f"{result_ilrl['tan_delta_effective']:.2e}")

                # 損耗分解
                markdown("### 📉 損耗分解")
                breakdown = result_ilrl['loss_breakdown']
                fig_breakdown, ax_break = subplots(figsize=(8, 4))
                labels = ['Conductor Loss', 'Dielectric Loss', 'Radiation Loss']
                sizes = [breakdown['conductor_pct'], breakdown['dielectric_pct'], breakdown['radiation_pct']]
                colors = ['#ff9999', '#66b3ff', '#99ff99']
                bars = ax_break.bar(labels, sizes, color=colors, edgecolor='black', linewidth=1.5)
                ax_break.set_ylabel("Percentage (%)")
                ax_break.set_title(f"Loss Breakdown @ {f_ilrl} GHz, {T_ilrl}K")
                ax_break.set_ylim(0, max(sizes) * 1.2)
                for bar, size in zip(bars, sizes):
                    height = bar.get_height()
                    ax_break.text(bar.get_x() + bar.get_width()/2., height,
                                 f'{size:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
                pyplot(fig_breakdown)

                # 頻率響應
                markdown("### 📈 IL/RL 頻率響應")
                freqs_scan = linspace(0.1, 20, 100)
                il_scan = []
                rl_scan = []
                for f_s in freqs_scan:
                    s_temp = MaterialViaSpecs(
                        er=er_input, tan_delta_rt=tan_rt, tan_delta_4K=tan_4k, tan_delta_20mK=tan_20mk,
                        n_dielectric_layers=n_dielectric, dielectric_thickness_um=dielectric_thick,
                        via_enabled=via_en, via_diameter_um=via_d, via_density_per_mm=via_den,
                        conductor_material=mat_ilrl, conductor_thickness_um=cond_thick,
                        conductor_roughness_um=roughness, trace_width_um=w_ilrl,
                        pitch_mm=p_ilrl, length_mm=l_ilrl, frequency_GHz=f_s, temperature_K=T_ilrl
                    )
                    r_s = calc_multilayer_loss(s_temp)
                    il_scan.append(r_s['IL_total_dB'])
                    rl_scan.append(r_s['RL_dB'])

                fig_freq, ax_freq = subplots(figsize=(10, 5))
                ax_freq.plot(freqs_scan, il_scan, 'b-', linewidth=2, label='Insertion Loss (S21)')
                ax_freq.plot(freqs_scan, rl_scan, 'r--', linewidth=2, label='Return Loss (S11)')
                ax_freq.axvline(x=f_ilrl, color='green', linestyle=':', alpha=0.7, label=f'Design Freq {f_ilrl} GHz')
                ax_freq.set_xlabel("Frequency (GHz)", fontsize=12)
                ax_freq.set_ylabel("Magnitude (dB)", fontsize=12)
                ax_freq.set_title(f"S-Parameters vs Frequency ({mat_ilrl}, {T_ilrl}K, L={l_ilrl}mm)", fontsize=13)
                ax_freq.legend(fontsize=11)
                ax_freq.grid(True, alpha=0.3)
                ax_freq.set_ylim(-30, 5)
                pyplot(fig_freq)

            elif auto_opt:
                with spinner("正在執行材料/Via 自動優化..."):
                    base_specs = MaterialViaSpecs(
                        er=er_input, tan_delta_rt=tan_rt, tan_delta_4K=tan_4k, tan_delta_20mK=tan_20mk,
                        n_dielectric_layers=n_dielectric, dielectric_thickness_um=dielectric_thick,
                        via_enabled=via_en, via_diameter_um=via_d, via_density_per_mm=via_den,
                        conductor_material=mat_ilrl, conductor_thickness_um=cond_thick,
                        conductor_roughness_um=roughness, trace_width_um=w_ilrl,
                        pitch_mm=p_ilrl, length_mm=l_ilrl, frequency_GHz=f_ilrl, temperature_K=T_ilrl
                    )
                    opt_result = optimize_material_via(base_specs, target_IL_dB=target_il, target_RL_dB=target_rl)

                success("✅ 材料/Via 優化完成！")
                opt_s = opt_result["optimal_specs"]
                opt_p = opt_result["performance"]

                markdown("### 🎯 最優材料/Via 參數")
                opt_cols = columns(4)
                with opt_cols[0]:
                    metric("最優 εr", f"{opt_s.er:.2f}")
                with opt_cols[1]:
                    metric("最優介電厚", f"{opt_s.dielectric_thickness_um:.1f} μm")
                with opt_cols[2]:
                    metric("最優 Via 密度", f"{opt_s.via_density_per_mm:.2f}/mm")
                with opt_cols[3]:
                    metric("最優導體厚", f"{opt_s.conductor_thickness_um:.1f} μm")

                markdown("### 📊 優化後性能")
                perf_cols = columns(3)
                with perf_cols[0]:
                    metric("IL", f"{opt_p['IL_total_dB']:.3f} dB", delta=f"目標: {target_il} dB")
                with perf_cols[1]:
                    metric("RL", f"{opt_p['RL_dB']:.1f} dB", delta=f"目標: {target_rl} dB")
                with perf_cols[2]:
                    metric("Z₀", f"{opt_p['Z0_ohm']:.2f} Ω")

            else:
                info("👈 請輸入材料與 Via 參數，然後點擊「計算 IL/RL」或「自動優化」")

set_page_config(
    page_title="Cri/oFlex3 柔性傳輸線規格計算器",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義 CSS
markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4;
    margin-bottom: 0.5rem;
}
.sub-header {
    font-size: 1.2rem;
    color: #666;
    margin-bottom: 2rem;
}
.metric-card {
    background-color: #f0f2f6;
    border-radius: 10px;
    padding: 20px;
    margin: 10px 0;
}
.highlight {
    background-color: black;
    border-left: 4px solid #1f77b4;
    padding: 15px;
    margin: 15px 0;
}
</style>
""", unsafe_allow_html=True)

from streamlit import empty
MENU, 表單=[], ['計算結果', '傳輸線特性', '串擾', '熱負載', '損耗', '物理結構', '推導公式', '規格摘要', '最優解']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
狀態=empty()
  #狀態.code([])

with sidebar:
    # 側邊欄 - 參數輸入
        subheader("⚙️ 設計參數")
        subheader("幾何結構")
        n_channels = radio("通道數", [4, 8, 16, 32], index=1, horizontal=True)
        pitch = slider("通道間距 Pitch (mm)", 0.5, 5.0, 2.0, 0.1)
        length = slider("傳輸線長度 (mm)", 100, 1500, 400, 50)
        sig_width = slider("信號線寬度 (μm)", 50, 500, 150, 10)
        sig_thickness = slider("導體厚度 (μm)", 1, 20, 5, 1)
        dielectric_thickness = slider("單層介電厚度 (μm)", 50, 300, 150, 10)

        subheader("材料選擇")
        conductor_material = radio( "導體材料", ["Ag (銀)", "NbTi (超導)", "Cu (銅)"], index=1, horizontal=True)
        dielectric_material = radio( "介電材料", ["Polyimide Kapton"], index=0, horizontal=True)

        subheader("Via 設計")
        via_enabled = checkbox("啟用 Via Stitching", value=True)
        via_density = slider("Via 密度 (個/mm)", 0.5, 5.0, 2.0, 0.1)
        via_diameter = slider("Via 直徑 (μm)", 50, 300, 150, 10)

        subheader("操作條件")
        frequency = slider("工作頻率 (GHz)", 0.1, 20.0, 6.0, 0.1)
        temp_stage = radio( "溫度階段", ["300K → 40K", "40K → 4K", "4K → 1K", "1K → 100mK", "RT → mK (全段)"], index=1, horizontal=True)

        subheader("計算選項")
        calc_crosstalk = checkbox("計算串擾", value=True)
        calc_thermal = checkbox("計算熱負載", value=True)
        calc_loss = checkbox("計算插入損耗", value=True)

if menu==len(表單): #
  pass
elif menu==MENU[0]: # 主內容區
    col1, col2 = columns([2, 1])

    with col1:
        subheader("📊 計算結果")
        if 'geo' not in session_state: # 建立幾何結構
          geo = StriplineGeometry(
            w=sig_width / 1000,  # μm -> mm
            t=sig_thickness,
            h=dielectric_thickness / 1000,  # μm -> mm
            s=pitch,
            L=length,
            n_channels=n_channels
        )
        else: geo=session_state['geo']

        # 介電參數
        dielectric = DIELECTRIC["Polyimide_Kapton"]
        #er = dielectric["er"]
        εr=session_state['εr']=dielectric["εr"]

        # 溫度邊界
        temp_map = {
            "300K → 40K": (300, 40),
            "40K → 4K": (40, 4),
            "4K → 1K": (4, 1),
            "1K → 100mK": (1, 0.1),
            "RT → mK (全段)": (300, 0.01)
        }
        T_hot, T_cold = temp_map[temp_stage]
        session_state['T_cold']=T_cold
        session_state['T_hot']=T_hot
        boundary = ThermalBoundary(T_hot=T_hot, T_cold=T_cold, stage=temp_stage)

        # 材料堆疊 (Cri/oFlex3 典型結構)
        mat_name = session_state['mat_name']=conductor_material.split(" ")[0]
        materials = session_state['materials']=MaterialStack(layers=[
            {"material": mat_name, "thickness": sig_thickness, "width": sig_width},
            {"material": "Polyimide_Kapton", "thickness": dielectric_thickness * 2, "width": pitch * 0.8},
            {"material": mat_name, "thickness": sig_thickness, "width": pitch * 0.8}  # 接地層
        ])

        # 計算結果容器
        results = {}

        # 1. 特性阻抗
        Z0 = session_state['Z0']=calc_stripline_impedance(geo, εr)

        # 2. 串擾計算
        if calc_crosstalk:
            crosstalk = calc_crosstalk_stripline(geo, εr, frequency * 1e9)
            results["crosstalk"] = crosstalk

            # Via 影響
            if via_enabled:
                via_info = calc_via_impact(pitch, via_diameter, via_density)
                results["via"] = via_info
                crosstalk["NEXT_dB"] -= via_info["shielding_improvement_dB"]
                crosstalk["FEXT_dB"] -= via_info["shielding_improvement_dB"]

        # 3. 熱負載計算
        if calc_thermal:
            thermal = calc_thermal_load(geo, boundary, materials)
            results["thermal"] = thermal

        # 4. 插入損耗
        if calc_loss:
            # 根據溫度選擇損耗角
            if T_cold < 1:
                tan_d = dielectric["tan_delta_20mK"]
            elif T_cold < 10:
                tan_d = dielectric["tan_delta_4K"]
            else:
                tan_d = dielectric["tan_delta_rt"]

            loss = calc_insertion_loss(geo, εr, tan_d, frequency * 1e9, mat_name)
            results["loss"] = loss
        session_state['results']=results
        session_state['geo']=geo
        session_state['εr']=εr
        session_state['tan_d']=tan_d

elif menu==MENU[1]: # 顯示結果 阻抗卡片
        subheader("📐 傳輸線特性")
        Z0=session_state['Z0']
        εr=session_state['εr']
        cols=columns(3)
        with cols[0]:
            metric("特性阻抗", f"{Z0:.1f} Ω", 
                     delta=f"{'✓ 匹配' if 45 < Z0 < 55 else '✗ 不匹配'}",
                     delta_color="normal" if 45 < Z0 < 55 else "inverse")
        with cols[1]:
            metric("通道密度", f"{n_channels} ch", 
                     delta=f"{n_channels/pitch:.1f} ch/mm")
        with cols[2]:
            effective_er = εr
            v_phase = 3e8 / sqrt(effective_er)
            delay = (length / 1000) / v_phase * 1e9
            metric("傳輸延遲", f"{delay:.2f} ns")

elif menu==MENU[2]: # 串擾卡片
        results=session_state['results']
        geo=session_state['geo']
        εr=session_state['εr']
        if calc_crosstalk and "crosstalk" in results:
            subheader("📡 串擾分析")
            ct = results["crosstalk"]
            cols = columns(4)
            with cols[0]:
                metric("近端串擾 (NEXT)", f"{ct['NEXT_dB']:.1f} dB",
                         delta="優良" if ct['NEXT_dB'] < -40 else "需改善",
                         delta_color="normal" if ct['NEXT_dB'] < -40 else "inverse")
            with cols[1]:
                metric("遠端串擾 (FEXT)", f"{ct['FEXT_dB']:.1f} dB")
            with cols[2]:
                metric("耦合係數 k", f"{ct['coupling_k']:.4f}")
            with cols[3]:
                if via_enabled and "via" in results:
                    metric("Via 屏蔽改善", f"{results['via']['shielding_improvement_dB']:.1f} dB")

            # 串擾頻率響應圖
            markdown("<div class='highlight'>串擾頻率響應 (1-18 GHz)</div>", unsafe_allow_html=True)
            freqs = linspace(1, 18, 100) * 1e9
            next_vals = []
            fext_vals = []
            for f in freqs:
                ct_f = calc_crosstalk_stripline(geo, εr, f)
                if via_enabled and "via" in results:
                    ct_f["NEXT_dB"] -= results["via"]["shielding_improvement_dB"]
                    ct_f["FEXT_dB"] -= results["via"]["shielding_improvement_dB"]
                next_vals.append(ct_f["NEXT_dB"])
                fext_vals.append(ct_f["FEXT_dB"])

            fig, ax = subplots(figsize=(10, 4))
            ax.plot(freqs/1e9, next_vals, 'b-', linewidth=2, label='NEXT (近端)')
            ax.plot(freqs/1e9, fext_vals, 'r--', linewidth=2, label='FEXT (遠端)')
            ax.axhline(y=-40, color='g', linestyle=':', alpha=0.7, label='-40 dB 目標')
            ax.axhline(y=-60, color='orange', linestyle=':', alpha=0.7, label='-60 dB 目標')
            ax.set_xlabel("Frequency (GHz)", fontsize=12)
            ax.set_ylabel("Crosstalk (dB)", fontsize=12)
            ax.set_title("Cri/oFlex3 Stripline Crosstalk vs Frequency", fontsize=14)
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_ylim(-100, -20)
            pyplot(fig)

elif menu==MENU[3]: # 熱負載卡片
        results=session_state['results']
        geo=session_state['geo']
        εr=session_state['εr']
        mat_name = session_state['mat_name']
        materials = session_state['materials']
        if calc_thermal and "thermal" in results:
            subheader("🌡️ 熱負載分析")
            th = results["thermal"]
            cols = columns(4)
            with cols[0]:
                metric("總熱負載", f"{th['total_power_W']*1e6:.2f} μW")
            with cols[1]:
                metric("每通道熱負載", f"{th['per_channel_uW']:.2f} μW",
                         delta=f"{th['per_channel_nW']:.1f} nW",
                         delta_color="off")
            with cols[2]:
                metric("溫差 ΔT", f"{th['delta_T']:.1f} K")
            with cols[3]:
                metric("等效 kA", f"{th['kA_total']*1e6:.3f} μW·m/K")

            # 熱負載溫度依賴圖
            markdown("<div class='highlight'>各溫度階段熱負載分佈</div>", unsafe_allow_html=True)
            stages = [(300, 40), (40, 4), (4, 1), (1, 0.1)]
            stage_names = ["300K→40K", "40K→4K", "4K→1K", "1K→100mK"]
            powers = []
            for Th, Tc in stages:
                b = ThermalBoundary(Th, Tc, "")
                p = calc_thermal_load(geo, b, materials)
                powers.append(p["per_channel_uW"])

            fig2, ax2 = subplots(figsize=(10, 4))
            colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
            bars = ax2.bar(stage_names, powers, color=colors, edgecolor='black', linewidth=1.2)
            ax2.set_ylabel("Heat Load per Channel (μW)", fontsize=12)
            ax2.set_title("Thermal Load Distribution Across Cryogenic Stages", fontsize=14)
            ax2.set_yscale('log')
            ax2.grid(True, alpha=0.3, axis='y')

            # 在柱狀圖上標註數值
            for bar, power in zip(bars, powers):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{power:.2f}',
                        ha='center', va='bottom', fontsize=10)

            pyplot(fig2)

            # 與 Cri/oFlex3 官方數據比較
            markdown("""
            <div class="highlight">
            <b>📋 與 Cri/oFlex3 官方規格比較:</b><br>
            • 官方標稱: 4K-40K, L=0.4m: < 125 μW/通道<br>
            • 官方標稱: 10mK-350mK, L=0.2m: ~ 20 nW/通道<br>
            • 本計算 NbTi 超導態: 大幅降低熱負載 (10× 改善)
            </div>
            """, unsafe_allow_html=True)

elif menu==MENU[4]: # 插入損耗
        results=session_state['results']
        geo=session_state['geo']
        εr=session_state['εr']
        mat_name = session_state['mat_name']
        materials = session_state['materials']
        tan_d = session_state['tan_d']
        if calc_loss and "loss" in results:
            subheader("📉 插入損耗")
            cols = columns(2)
            with cols[0]:
                metric(f"@{frequency} GHz 插入損耗", f"{results['loss']:.2f} dB",
                         delta="優良" if results['loss'] < 3 else "偏高",
                         delta_color="normal" if results['loss'] < 3 else "inverse")
            with cols[1]:
                # 計算衰減常數
                alpha_total = results['loss'] / (length / 1000)
                metric("衰減常數", f"{alpha_total:.2f} dB/m")

            # 損耗頻率響應
            markdown("<div class='highlight'>插入損耗頻率響應</div>", unsafe_allow_html=True)
            freqs_loss = linspace(0.1, 20, 200) * 1e9
            losses = []
            for f in freqs_loss:
                l = calc_insertion_loss(geo, εr, tan_d, f, mat_name)
                losses.append(l)

            fig3, ax3 = subplots(figsize=(10, 4))
            ax3.plot(freqs_loss/1e9, losses, 'purple', linewidth=2)
            ax3.axvline(x=frequency, color='red', linestyle='--', alpha=0.7, label=f'設計頻率 {frequency} GHz')
            ax3.set_xlabel("Frequency (GHz)", fontsize=12)
            ax3.set_ylabel("Insertion Loss (dB)", fontsize=12)
            ax3.set_title(f"Insertion Loss vs Frequency ({mat_name}, L={length}mm)", fontsize=14)
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            pyplot(fig3)

elif menu==MENU[5]: # 新增功能 1: 動態示意圖
        subheader("🔍 物理結構動態示意圖")
        geo=session_state['geo']
        tab1, tab2 = tabs(["📐 橫截面 (Cross-Section)", "📦 立體透視 (3D View)"])

        with tab1:
            fig_cross = draw_stripline_cross_section(geo, pitch, via_enabled, via_diameter, via_density, n_channels)
            pyplot(fig_cross)

            markdown("""
            <div style="background-color:black; padding:15px; border-radius:8px; margin-top:10px;">
            <b>結構說明：</b><br>
            • <b>G-S-G 配置</b>：Ground-Signal-Ground 對稱 Stripline，上下接地層提供完整屏蔽<br>
            • <b>Polyimide 介電層</b>：上下各一層，總介電厚度 = 2h，提供機械柔性與電氣隔離<br>
            • <b>Ag/NbTi 導體</b>：信號層與接地層採用多層膜結構，NbTi 提供超導低熱導特性<br>
            • <b>Via Stitching</b>：縱向接地 Via 提供橫向屏蔽，降低通道間耦合
            </div>
            """, unsafe_allow_html=True)

        with tab2:
            fig_3d = draw_stripline_3d_schematic(geo, pitch, length, n_channels)
            pyplot(fig_3d)

elif menu==MENU[6]: # 新增功能 2: 推導公式展示
        geo=session_state['geo']
        εr=session_state['εr']
        subheader("📐 串擾推導公式與計算過程")
        formula_tab1, formula_tab2, 計算摘要 = tabs(["📖 完整推導", "🔢 當前參數逐步計算", '計算摘要'])

        with formula_tab1:
            markdown(render_formula_section())

        with formula_tab2:
            calc_md, calc_vals = show_formula_calculation(geo, εr, frequency * 1e9)
            markdown(calc_md)

        with 計算摘要:
            # 顯示計算結果摘要表
            subheader("計算結果摘要")
            result_df = {
                "參數": [
                    "單位長度自電容 Cs",
                    "單位長度互電容 Cm", 
                    "單位長度自電感 Ls",
                    "單位長度互電感 Lm",
                    "電容耦合係數 kc",
                    "電感耦合係數 kL",
                    "綜合耦合係數 k",
                    "相位常數 β",
                    "電長度 θ",
                    "近端串擾 NEXT",
                    "遠端串擾 FEXT"
                ],
                "數值": [
                    f"{calc_vals['Cs']:.4e} F/m",
                    f"{calc_vals['Cm']:.4e} F/m",
                    f"{calc_vals['Ls']:.4e} H/m",
                    f"{calc_vals['Lm']:.4e} H/m",
                    f"{calc_vals['kc']:.6f}",
                    f"{calc_vals['kL']:.6f}",
                    f"{calc_vals['k']:.6f}",
                    f"{calc_vals['beta']:.4e} rad/m",
                    f"{calc_vals['theta']:.4f}",
                    f"{calc_vals['NEXT_dB']:.2f} dB",
                    f"{calc_vals['FEXT_dB']:.2f} dB"
                ]
            }
            table(result_df)


elif menu==MENU[7]:
        subheader("📋 規格摘要")
        mat_name = session_state['mat_name']
        # 設計規格表
        subheader("設計參數")
        spec_data = {
            "參數": ["通道數", "Pitch", "長度", "線寬", "導體厚", "介電厚", "導體材料", "介電材料"],
            "數值": [
                f"{n_channels} ch",
                f"{pitch} mm",
                f"{length} mm",
                f"{sig_width} μm",
                f"{sig_thickness} μm",
                f"{dielectric_thickness} μm",
                conductor_material,
                dielectric_material
            ]
        }
        table(spec_data)

        # 性能指標
        subheader("性能指標")
        perf_data = {}
        results=session_state['results']
        Z0=session_state['Z0']
        if calc_crosstalk and "crosstalk" in results:
            perf_data["串擾 (NEXT)"] = f"{results['crosstalk']['NEXT_dB']:.1f} dB"
        if calc_thermal and "thermal" in results:
            perf_data["熱負載/通道"] = f"{results['thermal']['per_channel_uW']:.2f} μW"
        if calc_loss and "loss" in results:
            perf_data["插入損耗"] = f"{results['loss']:.2f} dB"
        perf_data["特性阻抗"] = f"{Z0:.1f} Ω"

        perf_df = {"指標": list(perf_data.keys()), "數值": list(perf_data.values())}
        table(perf_df)

        # 設計建議
        subheader("💡 設計建議")
        suggestions = []

        if Z0 < 45 or Z0 > 55:
            suggestions.append(f"⚠️ 阻抗 {Z0:.1f}Ω 偏離 50Ω 目標，建議調整線寬至 {150 * 50/Z0:.0f}μm")
        else:
            suggestions.append("✅ 阻抗匹配良好")

        if calc_crosstalk and "crosstalk" in results:
            if results['crosstalk']['NEXT_dB'] > -40:
                suggestions.append(f"⚠️ 串擾偏高，建議增加 pitch 至 {pitch * 1.5:.1f}mm 或增加 via 密度")
            else:
                suggestions.append("✅ 串擾性能優良")

        T_cold=session_state['T_cold']
        T_hot=session_state['T_hot']
        if calc_thermal and "thermal" in results:
            if mat_name == "NbTi" and T_cold < 9.2:
                suggestions.append("✅ NbTi 超導態運行，熱負載極低")
            elif results['thermal']['per_channel_uW'] > 200:
                suggestions.append("⚠️ 熱負載偏高，建議使用 NbTi 或縮短長度")
            else:
                suggestions.append("✅ 熱負載在合理範圍")

        if via_enabled:
            suggestions.append(f"✅ Via stitching 密度 {via_density}/mm 提供良好屏蔽")

        for s in suggestions:
            markdown(f"<div style='margin: 5px 0;'>{s}</div>", unsafe_allow_html=True)

        # 匯出按鈕
        subheader("📥 匯出結果")
        export_data = {
            "geometry": {
                "n_channels": n_channels,
                "pitch_mm": pitch,
                "length_mm": length,
                "signal_width_um": sig_width,
                "conductor_thickness_um": sig_thickness,
                "dielectric_thickness_um": dielectric_thickness
            },
            "materials": {
                "conductor": conductor_material,
                "dielectric": dielectric_material
            },
            "results": results,
            "impedance_ohm": Z0
        }

        json_str = json.dumps(export_data, indent=2, default=str)
        download_button(
            label="下載 JSON 規格檔",
            data=json_str,
            file_name=f"crioflex3_spec_{length}mm_{n_channels}ch.json",
            mime="application/json"
        )

elif menu==MENU[8]: #智能化設計優化器
  render_optimizer_section()

with sidebar:
    from 材料物理參數 import materials_data
    資框=DataFrame(materials_data)
    資框.T
    # 標題區
    markdown('<div class="sub-header">🔬 Cri/oFlex3 柔性傳輸線規格計算器</div>', unsafe_allow_html=True)
    markdown('<div class="sub-header">NbTi/Ag + Polyimide 多層膜 Stripline 串擾與熱負載分析</div>', unsafe_allow_html=True)
    """Cri/oFlex3 柔性傳輸線規格計算器
=====================================
針對 NbTi/Ag + Polyimide 多層膜柔性 stripline 的串擾與熱負載計算工具

技術參數基準 (Delft Circuits Cri/oFlex3):
- 通道數: 8 channels/flex
- 厚度: 0.3 mm
- Pitch: 2 mm
- 材料: Polyimide + Ag/NbTi
- 線型: Stripline (G-S-G)
- 阻抗: 50 Ω
- 頻率: DC ~ 18 GHz
- 彎曲半徑: 5 mm
- 長度: 200 ~ 1000 mm
"""
