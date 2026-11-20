from json import dumps as jsnDumps
from streamlit import subheader, tabs, sidebar, success, markdown, columns, number_input, radio, metric, download_button, slider, checkbox, button, info, json as stJSON
from 約束優化Util import DesignConstraints, optimize_stripline_design, scan_design_space
from matplotlib.pyplot import rcParams, savefig, show, subplots, tight_layout
from streamlit import pyplot
from matplotlib.pyplot import Circle, Polygon, Rectangle, colorbar, figure, subplots, tight_layout
from dataclasses import dataclass
from scipy.optimize import minimize, differential_evolution, NonlinearConstraint
from numpy import arctan, array, exp, linspace, log, log10, mean, pi, sqrt
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


#fig, ax4= subplots(figsize=(10, 6))
#pyplot(fig)
with sidebar:
    """渲染智能化設計優化器 UI 區塊"""
    #markdown("---")
    subheader("🧠 智能化設計優化器")
    # ========== Tab 1: 逆向設計 ==========
    #with opt_tab1:
    subheader("🔧 逆向設計優化器")
    markdown("給定電氣/熱/機械規格約束，自動找出最優 Stripline 尺寸")
    #col_spec, col_result = columns([1, 2])

    #with col_spec:
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

        #run_optimize = button("🚀 執行優化", type="primary", use_container_width=True, key="btn_opt")

        #with col_result:
        #    if run_optimize:
        #        with spinner("正在執行多目標優化 (Differential Evolution)..."):
opt_tab1, opt_tab2 = tabs([
    "🔧 逆向設計：規格 → 尺寸", 
    "🧪 材料/Via 優化：參數 → IL/RL"
])
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
    #with spinner("掃描設計空間..."):
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
    stJSON(optimal_design)
    download_button("下載最優設計 JSON", data=jsnDumps(optimal_design, indent=2, default=str), file_name="optimal_stripline_design.json", mime="application/json")
#else:
#    error("❌ 優化失敗，請放寬約束條件後重試")
#else:
#info("👈 請在左側輸入規格約束，然後點擊「執行優化」")

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
                #with spinner("正在執行材料/Via 自動優化..."):
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

