from dataclasses import dataclass
# ============================================================
# 智能化設計優化器核心模組
# ============================================================

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
    return -20 * np.log10(abs(gamma))


def calc_via_impedance_discontinuity(specs, Z0_line):
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
