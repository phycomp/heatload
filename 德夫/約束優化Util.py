from dataclasses import dataclass
from scipy.optimize import minimize, differential_evolution, NonlinearConstraint
from numpy import arctan, array, exp, linspace, log, log10, mean, pi, sqrt
from pandas import DataFrame

MU_0 = 4 * pi * 1e-7  # H/m 真空磁導率
EPS_0 = 8.854e-12  # F/m 真空介電常數
K_B = 1.381e-23  # J/K 玻爾茲曼常數
# 材料熱導率參數 (W/m·K) 基於文獻數據擬合
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
    | $arepsilon_r$ | 相對介電常數 (Polyimide = 3.4) | — |
    | $arepsilon_0$ | 真空介電常數 = $8.854 \times 10^{-12}$ | F/m |
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

    #### 5.1 相位常數 $eta$

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
