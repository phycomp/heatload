# 建立智能化設計優化器模組
# 在原 v2 基礎上新增兩大優化功能：
# 1. 逆向設計：給定規格約束 → 找出最優 stripline 尺寸
# 2. 材料/Via 優化：給定材料參數 → 計算 IL, RL

# ============================================================
# 智能化設計優化器模組 (新增)
# ============================================================

from dataclasses import dataclass
from scipy.optimize import minimize, differential_evolution, NonlinearConstraint
from scipy.interpolate import interp1d
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 功能 1: 逆向設計優化器 - 給定規格約束找出最優尺寸
# ============================================================

@dataclass
class DesignConstraints:
    """設計規格約束"""
    # 電氣規格
    target_Z0: float = 50.0           # 目標阻抗 (Ω)
    Z0_tolerance: float = 5.0         # 阻抗容差 (±Ω)
    max_NEXT_dB: float = -40.0        # 最大允許近端串擾 (dB)
    max_FEXT_dB: float = -40.0        # 最大允許遠端串擾 (dB)
    max_IL_dB: float = 3.0            # 最大允許插入損耗 (dB)
    
    # 熱規格
    max_thermal_per_channel_uW: float = 200.0  # 最大熱負載/通道 (μW)
    
    # 機械規格
    max_total_thickness_mm: float = 0.5        # 最大總厚度 (mm)
    min_bend_radius_mm: float = 5.0            # 最小彎曲半徑 (mm)
    
    # 製程限制
    min_trace_width_um: float = 50.0           # 最小線寬 (μm)
    max_trace_width_um: float = 500.0          # 最大線寬 (μm)
    min_dielectric_um: float = 25.0            # 最小介電厚 (μm)
    max_dielectric_um: float = 500.0           # 最大介電厚 (μm)
    min_pitch_mm: float = 0.5                  # 最小 pitch (mm)
    max_pitch_mm: float = 5.0                  # 最大 pitch (mm)
    
    # 固定參數
    n_channels: int = 8
    frequency_GHz: float = 6.0
    length_mm: float = 400.0
    temperature_stage: str = "40K → 4K"
    
    # 材料
    conductor: str = "NbTi"
    dielectric: str = "Polyimide_Kapton"
    er: float = 3.4
    tan_delta: float = 3e-5


def evaluate_design(params: np.ndarray, constraints: DesignConstraints) -> Dict:
    """
    評估一組設計參數的性能
    
    params = [w_mm, h_mm, s_mm, t_um]
    """
    w, h, s, t = params
    
    geo = StriplineGeometry(
        w=w, h=h, s=s, t=t,
        L=constraints.length_mm,
        n_channels=constraints.n_channels
    )
    
    # 1. 阻抗
    Z0 = calc_stripline_impedance(geo, constraints.er)
    Z0_error = abs(Z0 - constraints.target_Z0)
    
    # 2. 串擾
    f = constraints.frequency_GHz * 1e9
    ct = calc_crosstalk_stripline(geo, constraints.er, f)
    
    # 3. 熱負載
    temp_map = {"300K → 40K": (300, 40), "40K → 4K": (40, 4), 
                "4K → 1K": (4, 1), "1K → 100mK": (1, 0.1)}
    Th, Tc = temp_map.get(constraints.temperature_stage, (40, 4))
    boundary = ThermalBoundary(Th, Tc, constraints.temperature_stage)
    
    mat_name = constraints.conductor.split(" ")[0] if " " in constraints.conductor else constraints.conductor
    materials = MaterialStack(layers=[
        {"material": mat_name, "thickness": t, "width": w * 1000},
        {"material": "Polyimide_Kapton", "thickness": h * 1000 * 2, "width": s * 0.8 * 1000},
        {"material": mat_name, "thickness": t, "width": s * 0.8 * 1000}
    ])
    thermal = calc_thermal_load(geo, boundary, materials)
    
    # 4. 插入損耗
    loss = calc_insertion_loss(geo, constraints.er, constraints.tan_delta, f, mat_name)
    
    # 5. 總厚度
    total_thickness = 2 * h + 3 * (t / 1000)  # mm
    
    return {
        "Z0": Z0,
        "Z0_error": Z0_error,
        "NEXT_dB": ct["NEXT_dB"],
        "FEXT_dB": ct["FEXT_dB"],
        "thermal_per_channel_uW": thermal["per_channel_uW"],
        "IL_dB": loss,
        "total_thickness_mm": total_thickness,
        "params": {"w_mm": w, "h_mm": h, "s_mm": s, "t_um": t}
    }


def objective_function(params: np.ndarray, constraints: DesignConstraints) -> float:
    """
    多目標優化目標函數 (加權懲罰法)
    
    目標：最小化綜合懲罰值
    """
    eval_result = evaluate_design(params, constraints)
    
    penalty = 0.0
    
    # 阻抗懲罰 (高權重)
    if eval_result["Z0_error"] > constraints.Z0_tolerance:
        penalty += 1000 * (eval_result["Z0_error"] - constraints.Z0_tolerance) ** 2
    else:
        penalty += 0.1 * eval_result["Z0_error"]  # 小懲罰鼓勵更接近 50Ω
    
    # 串擾懲罰
    if eval_result["NEXT_dB"] > constraints.max_NEXT_dB:
        penalty += 500 * (eval_result["NEXT_dB"] - constraints.max_NEXT_dB) ** 2
    if eval_result["FEXT_dB"] > constraints.max_FEXT_dB:
        penalty += 500 * (eval_result["FEXT_dB"] - constraints.max_FEXT_dB) ** 2
    
    # 熱負載懲罰
    if eval_result["thermal_per_channel_uW"] > constraints.max_thermal_per_channel_uW:
        penalty += 100 * (eval_result["thermal_per_channel_uW"] - constraints.max_thermal_per_channel_uW) ** 2
    
    # 插入損耗懲罰
    if eval_result["IL_dB"] > constraints.max_IL_dB:
        penalty += 200 * (eval_result["IL_dB"] - constraints.max_IL_dB) ** 2
    
    # 厚度懲罰
    if eval_result["total_thickness_mm"] > constraints.max_total_thickness_mm:
        penalty += 500 * (eval_result["total_thickness_mm"] - constraints.max_total_thickness_mm) ** 2
    
    # 次要目標：最小化 pitch (高密度)
    penalty += 0.5 * params[2]  # s_mm
    
    # 次要目標：最小化厚度
    penalty += 1.0 * eval_result["total_thickness_mm"]
    
    return penalty


def optimize_stripline_design(constraints: DesignConstraints, 
                               method: str = "differential_evolution") -> Dict:
    """
    執行 Stripline 尺寸優化
    
    返回最優設計參數與性能預測
    """
    # 定義搜索邊界
    bounds = [
        (constraints.min_trace_width_um / 1000, constraints.max_trace_width_um / 1000),  # w (mm)
        (constraints.min_dielectric_um / 1000, constraints.max_dielectric_um / 1000),    # h (mm)
        (constraints.min_pitch_mm, constraints.max_pitch_mm),                            # s (mm)
        (1.0, 20.0)                                                                      # t (μm)
    ]
    
    if method == "differential_evolution":
        result = differential_evolution(
            lambda p: objective_function(p, constraints),
            bounds=bounds,
            maxiter=500,
            tol=1e-6,
            seed=42,
            workers=-1,
            polish=True
        )
    else:
        # 使用 SLSQP (需要初始猜測)
        x0 = [0.15, 0.15, 2.0, 5.0]  # 初始值
        result = minimize(
            lambda p: objective_function(p, constraints),
            x0,
            method="SLSQP",
            bounds=bounds,
            options={"maxiter": 500, "ftol": 1e-6}
        )
    
    # 評估最優解
    optimal_eval = evaluate_design(result.x, constraints)
    
    return {
        "success": result.success,
        "optimal_params": {
            "w_mm": result.x[0],
            "h_mm": result.x[1], 
            "s_mm": result.x[2],
            "t_um": result.x[3]
        },
        "performance": optimal_eval,
        "final_penalty": result.fun,
        "n_iterations": result.nit if hasattr(result, 'nit') else None
    }


def scan_design_space(constraints: DesignConstraints, 
                      n_points: int = 20) -> pd.DataFrame:
    """
    掃描設計空間，生成 Pareto 前沿分析
    """
    import pandas as pd
    
    # 固定某些參數，掃描 w 和 s
    w_range = np.linspace(constraints.min_trace_width_um/1000, 
                          constraints.max_trace_width_um/1000, n_points)
    s_range = np.linspace(constraints.min_pitch_mm, 
                          constraints.max_pitch_mm, n_points)
    
    h_fixed = 0.15  # mm
    t_fixed = 5.0   # μm
    
    results = []
    for w in w_range:
        for s in s_range:
            if s <= w:  # pitch 必須大於線寬
                continue
            params = np.array([w, h_fixed, s, t_fixed])
            eval_r = evaluate_design(params, constraints)
            eval_r["w_mm"] = w
            eval_r["s_mm"] = s
            results.append(eval_r)
    
    return pd.DataFrame(results)


# ============================================================
# 功能 2: 材料/Via 優化器 - 計算 IL, RL
# ============================================================

@dataclass
class MaterialViaSpecs:
    """材料與 Via 規格"""
    # 介電材料參數
    er: float = 3.4
    tan_delta_rt: float = 0.003
    tan_delta_4K: float = 3e-5
    tan_delta_20mK: float = 2.2e-5
    
    # 多層膜結構
    n_dielectric_layers: int = 2
    dielectric_thickness_um: float = 150.0
    
    # Via 參數
    via_enabled: bool = True
    via_diameter_um: float = 150.0
    via_density_per_mm: float = 2.0
    via_material: str = "Ag"
    
    # 導體參數
    conductor_material: str = "NbTi"
    conductor_thickness_um: float = 5.0
    conductor_roughness_um: float = 0.5
    
    # 幾何
    trace_width_um: float = 150.0
    pitch_mm: float = 2.0
    length_mm: float = 400.0
    frequency_GHz: float = 6.0
    temperature_K: float = 4.0


def calc_return_loss(Z0_design: float, Z0_actual: float) -> float:
    """
    計算反射損耗 (Return Loss)
    
    RL = -20*log10(|Γ|)
    Γ = (Z0_actual - Z0_design) / (Z0_actual + Z0_design)
    """
    gamma = (Z0_actual - Z0_design) / (Z0_actual + Z0_design)
    RL = -20 * np.log10(abs(gamma))
    return RL


def calc_via_impedance_discontinuity(specs: MaterialViaSpecs, 
                                      Z0_line: float) -> Dict:
    """
    計算 Via 引入的阻抗不連續性與損耗
    
    Via 模型：串聯電感 + 並聯電容
    """
    # Via 幾何
    d_via = specs.via_diameter_um / 1e6  # m
    h_total = specs.n_dielectric_layers * specs.dielectric_thickness_um / 1e6  # m
    
    # Via 電感 (近似公式)
    # L_via ≈ (μ0/2π) * h * ln(4h/d)
    L_via = (MU_0 / (2 * np.pi)) * h_total * np.log(4 * h_total / d_via)
    
    # Via 電容 (pad 電容近似)
    # C_via ≈ ε0*εr*π*(d_pad² - d_via²)/(4*h)
    d_pad = d_via * 1.5  # pad 直徑
    C_via = EPS_0 * specs.er * np.pi * (d_pad**2 - d_via**2) / (4 * h_total)
    
    # Via 阻抗
    Z_via = np.sqrt(L_via / C_via) if C_via > 0 else 1e6
    
    # 反射係數
    gamma_via = (Z_via - Z0_line) / (Z_via + Z0_line)
    RL_via = -20 * np.log10(abs(gamma_via))
    
    # Via 引起的插入損耗增量 (簡化模型)
    f = specs.frequency_GHz * 1e9
    omega = 2 * np.pi * f
    
    # 串聯電感損耗
    IL_inductive = 20 * np.log10(np.sqrt(1 + (omega * L_via / Z0_line)**2))
    
    # 並聯電容損耗
    IL_capacitive = 20 * np.log10(np.sqrt(1 + (omega * C_via * Z0_line)**2))
    
    IL_via_total = IL_inductive + IL_capacitive
    
    return {
        "L_via_H": L_via,
        "C_via_F": C_via,
        "Z_via_ohm": Z_via,
        "RL_via_dB": RL_via,
        "IL_via_inductive_dB": IL_inductive,
        "IL_via_capacitive_dB": IL_capacitive,
        "IL_via_total_dB": IL_via_total,
        "discontinuity_severity": "minor" if RL_via > 20 else "moderate" if RL_via > 10 else "severe"
    }


def calc_multilayer_loss(specs: MaterialViaSpecs) -> Dict:
    """
    計算多層膜結構的總損耗 (IL) 與反射 (RL)
    """
    # 根據溫度選擇損耗角
    if specs.temperature_K < 1:
        tan_d = specs.tan_delta_20mK
    elif specs.temperature_K < 10:
        tan_d = specs.tan_delta_4K
    else:
        tan_d = specs.tan_delta_rt
    
    # 幾何參數
    w = specs.trace_width_um / 1e6  # m
    t = specs.conductor_thickness_um / 1e6  # m
    h = specs.dielectric_thickness_um / 1e6  # m
    L = specs.length_mm / 1000  # m
    f = specs.frequency_GHz * 1e9
    
    # 1. 特性阻抗計算
    b = 2 * h
    We = w + (t / np.pi) * (1 + np.log(2 * b / t)) if w / b > 0.35 else w
    Z0 = (30 * np.pi / np.sqrt(specs.er)) * (b / We)
    
    # 2. 導體損耗 (含表面粗糙度修正)
    sigma = {"Ag": 6.3e7, "NbTi": 1e6, "Cu": 5.8e7}.get(specs.conductor_material, 6.3e7)
    delta_s = np.sqrt(2 / (MU_0 * sigma * 2 * np.pi * f))
    
    # 表面粗糙度修正 (Hammerstad-Jensen 模型)
    kr = 1 + (2 / np.pi) * np.arctan(1.4 * (specs.conductor_roughness_um / 1e6 / delta_s)**2)
    Rs = kr / (sigma * delta_s)
    
    alpha_c = Rs / (Z0 * w)  # Np/m
    alpha_c_db = alpha_c * 8.686
    
    # 3. 介電損耗
    c = 3e8
    alpha_d = (np.pi * f * np.sqrt(specs.er) * tan_d) / c
    alpha_d_db = alpha_d * 8.686
    
    # 4. 輻射損耗 (簡化)
    alpha_r_db = 0.01 * specs.frequency_GHz  # 簡化經驗值
    
    # 5. 總插入損耗
    IL_total = (alpha_c_db + alpha_d_db + alpha_r_db) * L
    
    # 6. 反射損耗 (假設設計目標 50Ω)
    RL = calc_return_loss(50.0, Z0)
    
    # 7. Via 影響
    via_impact = calc_via_impedance_discontinuity(specs, Z0)
    IL_with_via = IL_total + via_impact["IL_via_total_dB"] * (specs.length_mm / 10) * specs.via_density_per_mm
    
    return {
        "Z0_ohm": Z0,
        "IL_conductor_dB": alpha_c_db * L,
        "IL_dielectric_dB": alpha_d_db * L,
        "IL_radiation_dB": alpha_r_db * L,
        "IL_total_dB": IL_total,
        "IL_with_via_dB": IL_with_via,
        "RL_dB": RL,
        "RL_with_via_dB": min(RL, via_impact["RL_via_dB"]),
        "tan_delta_effective": tan_d,
        "skin_depth_um": delta_s * 1e6,
        "surface_roughness_factor": kr,
        "via_impact": via_impact,
        "loss_breakdown": {
            "conductor_pct": (alpha_c_db * L) / IL_total * 100 if IL_total > 0 else 0,
            "dielectric_pct": (alpha_d_db * L) / IL_total * 100 if IL_total > 0 else 0,
            "radiation_pct": (alpha_r_db * L) / IL_total * 100 if IL_total > 0 else 0
        }
    }


def optimize_material_via(specs: MaterialViaSpecs, 
                          target_IL_dB: float = 2.0,
                          target_RL_dB: float = 20.0) -> Dict:
    """
    優化材料與 Via 參數以達成目標 IL/RL
    
    優化變數: er, dielectric_thickness, via_density, conductor_thickness
    """
    def objective(x):
        s = MaterialViaSpecs(
            er=x[0],
            dielectric_thickness_um=x[1],
            via_density_per_mm=x[2],
            conductor_thickness_um=x[3],
            trace_width_um=specs.trace_width_um,
            pitch_mm=specs.pitch_mm,
            length_mm=specs.length_mm,
            frequency_GHz=specs.frequency_GHz,
            temperature_K=specs.temperature_K,
            conductor_material=specs.conductor_material
        )
        result = calc_multilayer_loss(s)
        
        penalty = 0
        if result["IL_total_dB"] > target_IL_dB:
            penalty += 100 * (result["IL_total_dB"] - target_IL_dB)**2
        if result["RL_dB"] < target_RL_dB:
            penalty += 50 * (target_RL_dB - result["RL_dB"])**2
        
        # 次要目標：最小化厚度
        penalty += 0.01 * (x[1] * specs.n_dielectric_layers)
        
        return penalty
    
    bounds = [
        (2.0, 5.0),      # er
        (50.0, 300.0),   # dielectric_thickness_um
        (0.5, 5.0),      # via_density_per_mm
        (1.0, 20.0)      # conductor_thickness_um
    ]
    
    result = differential_evolution(objective, bounds, maxiter=300, seed=42)
    
    optimal_specs = MaterialViaSpecs(
        er=result.x[0],
        dielectric_thickness_um=result.x[1],
        via_density_per_mm=result.x[2],
        conductor_thickness_um=result.x[3],
        trace_width_um=specs.trace_width_um,
        pitch_mm=specs.pitch_mm,
        length_mm=specs.length_mm,
        frequency_GHz=specs.frequency_GHz,
        temperature_K=specs.temperature_K,
        conductor_material=specs.conductor_material
    )
    
    return {
        "optimal_specs": optimal_specs,
        "performance": calc_multilayer_loss(optimal_specs),
        "final_penalty": result.fun
    }
