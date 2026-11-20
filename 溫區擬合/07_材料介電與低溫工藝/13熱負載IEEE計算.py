from streamlit import caption, columns, subheader, info, markdown, multiselect, number_input, plotly_chart, radio, set_page_config, sidebar, subheader, table, tabs, code
from numpy import array, atleast_1d, interp, linspace, log10, logspace, pi, zeros_like
from plotly.graph_objects import Figure, Scatter
#"""
#Cryogenic Flex Cable Heat Load Calculator
#Streamlit app replicating https://mazinlab.github.io/FlaxHeatLoadCalc/
#
#Physics based on Smith et al. (2024) IEEE TASC paper
#"""
from streamlit import empty, pyplot
狀態=empty()
#import streamlit as st
#import numpy as np
from scipy import integrate
from scipy.interpolate import interp1d
#import plotly.graph_objects as go
from plotly.subplots import make_subplots

set_page_config(page_title="Cryogenic Cable Heat Load Calculator", layout="wide")

# ============================================================
# Custom CSS
# ============================================================
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
    .result-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin: 1rem 0;
    }
    .result-value {
        font-size: 3rem;
        font-weight: bold;
    }
    .result-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    .metric-card {
        background: black;
        border-radius: 10px;
        padding: 1rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Material Data
# ============================================================

# Nb47Ti thermal conductivity (Daal et al. 2019 + NIST)
def k_nbti(T):
    T = atleast_1d(T)
    result = zeros_like(T, dtype=float)
    mask_sub = T < 1.0
    result[mask_sub] = 0.0012 * T[mask_sub]**2.1
    mask_main = T >= 1.0
    t = T[mask_main]
    logt = log10(t)
    coeffs = [0.5, -0.3, 0.1, -0.02, 0.003, -0.0003, 0.00002, -0.000001, 0.00000005]
    logk = sum(c * logt**i for i, c in enumerate(coeffs))
    result[mask_main] = 10**logk
    return result

# PTFE thermal conductivity (Kushino et al. 2005 + NIST)
def k_ptfe(T):
    T = atleast_1d(T)
    result = zeros_like(T, dtype=float)
    mask_sub = T < 1.0
    result[mask_sub] = 0.0048 * T[mask_sub]**2.7
    mask_main = T >= 1.0
    t = T[mask_main]
    logt = log10(t)
    coeffs = [-1.2, 0.8, -0.15, 0.02, -0.002, 0.0001]
    logk = sum(c * logt**i for i, c in enumerate(coeffs))
    result[mask_main] = 10**logk
    return result

# FEP (approximated as PTFE)
def k_fep(T):
    return k_ptfe(T)

# Kapton thermal conductivity
def k_kapton(T):
    T = atleast_1d(T)
    result = zeros_like(T, dtype=float)
    mask_sub = T < 1.0
    result[mask_sub] = 0.005 * T[mask_sub]**1.5
    mask_main = T >= 1.0
    t = T[mask_main]
    logt = log10(t)
    coeffs = [-0.8, 0.5, -0.08, 0.01, -0.001]
    logk = sum(c * logt**i for i, c in enumerate(coeffs))
    result[mask_main] = 10**logk
    return result

# Copper thermal conductivity (NIST, RRR-dependent)
def k_copper(T, rrr=50):
    T = atleast_1d(T)
    logt = log10(T)
    coeffs = [2.0, -0.5, 0.1, -0.01, 0.001]
    logk = sum(c * logt**i for i, c in enumerate(coeffs))
    k = 10**logk * (rrr / 50)**0.8
    return k

# CuNi thermal conductivity
def k_cuni(T):
    T = atleast_1d(T)
    logt = log10(T)
    coeffs = [-0.5, 0.3, -0.05, 0.008, -0.001]
    logk = sum(c * logt**i for i, c in enumerate(coeffs))
    return 10**logk

# SS304 thermal conductivity
def k_ss304(T):
    T = atleast_1d(T)
    logt = log10(T)
    coeffs = [-0.3, 0.2, -0.03, 0.005, -0.0005]
    logk = sum(c * logt**i for i, c in enumerate(coeffs))
    return 10**logk

# Silver thermal conductivity
def k_silver(T):
    T = atleast_1d(T)
    logt = log10(T)
    coeffs = [2.5, -0.3, 0.05, -0.008, 0.001]
    logk = sum(c * logt**i for i, c in enumerate(coeffs))
    return 10**logk

# Material database
MATERIALS_DB = {
    'Conductors': {
        'NbTi': {'k_func': k_nbti, 'color': '#1f77b4'},
        'Nb (RRR~40)': {'k_func': k_nbti, 'color': '#ff7f0e'},
        'Cu (RRR=50)': {'k_func': lambda T: k_copper(T, 50), 'color': '#2ca02c'},
        'Cu (RRR=100)': {'k_func': lambda T: k_copper(T, 100), 'color': '#d62728'},
        'Cu (RRR=300)': {'k_func': lambda T: k_copper(T, 300), 'color': '#9467bd'},
        'CuNi (C7150)': {'k_func': k_cuni, 'color': '#8c564b'},
        'CuNi (Maybell)': {'k_func': k_cuni, 'color': '#e377c2'},
        'SS304': {'k_func': k_ss304, 'color': '#7f7f7f'},
        'Silver (Ag)': {'k_func': k_silver, 'color': '#bcbd22'},
    },
    'Dielectrics': {
        'PTFE (Teflon)': {'k_func': k_ptfe, 'eps_r': 2.1, 'tan_delta': 2e-4, 'color': '#17becf'},
        'FEP': {'k_func': k_fep, 'eps_r': 2.1, 'tan_delta': 2e-4, 'color': '#1f77b4'},
        'Kapton': {'k_func': k_kapton, 'eps_r': 3.4, 'tan_delta': 2e-3, 'color': '#ff7f0e'},
        'G-10': {'k_func': k_ptfe, 'eps_r': 4.5, 'tan_delta': 1e-2, 'color': '#2ca02c'},
    }
}

# ============================================================
# Cable Presets
# ============================================================

CABLE_PRESETS = {
    'FLAX v2 (Smith et al. 2024)': {
        'cable_type': 'Ribbon',
        'num_traces': 8,
        'inner_diameter_um': 127.0,
        'dielectric_thickness_um': 63.5,
        'trace_pitch_um': 3556.0,
        'foil_thickness_um': 25.4,
        'foil_sheets': 2,
        'inner_material': 'NbTi',
        'dielectric_material': 'FEP',
        'outer_material': 'NbTi',
    },
    'FLAX v1 (prior design)': {
        'cable_type': 'Ribbon',
        'num_traces': 8,
        'inner_diameter_um': 76.2,
        'dielectric_thickness_um': 63.5,
        'trace_pitch_um': 3556.0,
        'foil_thickness_um': 25.4,
        'foil_sheets': 2,
        'inner_material': 'NbTi',
        'dielectric_material': 'FEP',
        'outer_material': 'NbTi',
    },
    'Maybell CuNi/CuNi': {
        'cable_type': 'Ribbon',
        'num_traces': 8,
        'inner_diameter_um': 127.0,
        'dielectric_thickness_um': 63.5,
        'trace_pitch_um': 3556.0,
        'foil_thickness_um': 25.4,
        'foil_sheets': 2,
        'inner_material': 'CuNi (C7150)',
        'dielectric_material': 'PTFE (Teflon)',
        'outer_material': 'CuNi (C7150)',
    },
    'CryoCoax BCB012 (Semi-Rigid)': {
        'cable_type': 'Coaxial',
        'num_traces': 1,
        'inner_diameter_um': 200.0,
        'dielectric_thickness_um': 660.0,
        'outer_diameter_um': 1520.0,
        'outer_thickness_um': 150.0,
        'inner_material': 'NbTi',
        'dielectric_material': 'PTFE (Teflon)',
        'outer_material': 'NbTi',
    },
    'SC-086/50-CN-CN (CuNi Coax)': {
        'cable_type': 'Coaxial',
        'num_traces': 1,
        'inner_diameter_um': 200.0,
        'dielectric_thickness_um': 660.0,
        'outer_diameter_um': 1520.0,
        'outer_thickness_um': 150.0,
        'inner_material': 'CuNi (C7150)',
        'dielectric_material': 'PTFE (Teflon)',
        'outer_material': 'CuNi (C7150)',
    },
    'Copper Semi-Rigid': {
        'cable_type': 'Coaxial',
        'num_traces': 1,
        'inner_diameter_um': 200.0,
        'dielectric_thickness_um': 660.0,
        'outer_diameter_um': 1520.0,
        'outer_thickness_um': 150.0,
        'inner_material': 'Cu (RRR=50)',
        'dielectric_material': 'PTFE (Teflon)',
        'outer_material': 'Cu (RRR=50)',
    },
}

# ============================================================
# Core Calculation Functions
# ============================================================

def compute_heat_load(geometry, materials, T_cold, T_hot, L_m):
    """Compute steady-state heat load through cable"""

    d_inner = geometry['inner_diameter_um'] * 1e-6
    t_dielectric = geometry.get('dielectric_thickness_um', d_inner * 0.5) * 1e-6

    # Get k functions
    k_inner = MATERIALS_DB['Conductors'][materials['inner']]['k_func']
    k_diel = MATERIALS_DB['Dielectrics'][materials['dielectric']]['k_func']
    k_outer = MATERIALS_DB['Conductors'][materials['outer']]['k_func']

    # Compute cross-sectional areas
    if geometry['cable_type'] == 'Ribbon':
        pitch = geometry['trace_pitch_um'] * 1e-6
        foil_t = geometry['foil_thickness_um'] * 1e-6
        n_foil = geometry['foil_sheets']

        A_inner = pi * (d_inner / 2)**2
        d_outer_dielectric = d_inner + 2 * t_dielectric
        A_dielectric = pi * ((d_outer_dielectric / 2)**2 - (d_inner / 2)**2)
        A_outer = pitch * foil_t * n_foil
    else:
        d_outer = geometry.get('outer_diameter_um', 1520.0) * 1e-6
        t_outer = geometry.get('outer_thickness_um', 150.0) * 1e-6

        A_inner = pi * (d_inner / 2)**2
        d_outer_dielectric = d_inner + 2 * t_dielectric
        A_dielectric = pi * ((d_outer_dielectric / 2)**2 - (d_inner / 2)**2)
        r_outer_inner = d_outer_dielectric / 2
        r_outer_outer = r_outer_inner + t_outer
        A_outer = pi * (r_outer_outer**2 - r_outer_inner**2)

    # Thermal integrals
    def thermal_integral(k_func, T1, T2):
        #result, _ = integrate.quad(k_func, T1, T2, limit=100)
        T_array = linspace(T1, T2, 1000)
        k_array = k_func(T_array)  # 這會得到一個陣列
        result = integrate.simpson(k_array, x=T_array)
        return result

    #狀態.code([T_cold, T_hot])
    #k_inner=vectorize(k_inner)
    Q_inner = (A_inner / L_m) * thermal_integral(k_inner, T_cold, T_hot)
    Q_dielectric = (A_dielectric / L_m) * thermal_integral(k_diel, T_cold, T_hot)
    Q_outer = (A_outer / L_m) * thermal_integral(k_outer, T_cold, T_hot)

    Q_total = Q_inner + Q_dielectric + Q_outer

    # Avoid division by zero
    if Q_total < 1e-20:
        Q_total = 1e-20

    Q_per_trace = Q_total / geometry['num_traces']

    return {
        'total_heat_load_W': Q_total,
        'per_trace_W': Q_per_trace,
        'per_trace_nW': Q_per_trace * 1e9,
        'per_trace_pW': Q_per_trace * 1e12,
        'components': {
            'Inner Conductor': {
                'area_mm2': A_inner * 1e6,
                'heat_load_nW': Q_inner * 1e9,
                'fraction': Q_inner / Q_total
            },
            'Dielectric': {
                'area_mm2': A_dielectric * 1e6,
                'heat_load_nW': Q_dielectric * 1e9,
                'fraction': Q_dielectric / Q_total
            },
            'Outer Conductor': {
                'area_mm2': A_outer * 1e6,
                'heat_load_nW': Q_outer * 1e9,
                'fraction': Q_outer / Q_total
            },
        },
        'geometry_areas': {
            'A_inner_mm2': A_inner * 1e6,
            'A_dielectric_mm2': A_dielectric * 1e6,
            'A_outer_mm2': A_outer * 1e6,
        }
    }


def compute_temperature_profile(geometry, materials, T_cold, T_hot, L_m, n_points=200):
    """Compute temperature profile T(x) along cable"""

    d_inner = geometry['inner_diameter_um'] * 1e-6
    t_dielectric = geometry.get('dielectric_thickness_um', d_inner * 0.5) * 1e-6

    k_inner = MATERIALS_DB['Conductors'][materials['inner']]['k_func']
    k_diel = MATERIALS_DB['Dielectrics'][materials['dielectric']]['k_func']
    k_outer = MATERIALS_DB['Conductors'][materials['outer']]['k_func']

    if geometry['cable_type'] == 'Ribbon':
        pitch = geometry['trace_pitch_um'] * 1e-6
        foil_t = geometry['foil_thickness_um'] * 1e-6
        n_foil = geometry['foil_sheets']
        A_inner = pi * (d_inner / 2)**2
        d_outer_dielectric = d_inner + 2 * t_dielectric
        A_dielectric = pi * ((d_outer_dielectric / 2)**2 - (d_inner / 2)**2)
        A_outer = pitch * foil_t * n_foil
    else:
        d_outer = geometry.get('outer_diameter_um', 1520.0) * 1e-6
        t_outer = geometry.get('outer_thickness_um', 150.0) * 1e-6
        A_inner = pi * (d_inner / 2)**2
        d_outer_dielectric = d_inner + 2 * t_dielectric
        A_dielectric = pi * ((d_outer_dielectric / 2)**2 - (d_inner / 2)**2)
        r_outer_inner = d_outer_dielectric / 2
        r_outer_outer = r_outer_inner + t_outer
        A_outer = pi * (r_outer_outer**2 - r_outer_inner**2)

    def G(T):
        return (A_inner * k_inner(T) +
                A_dielectric * k_diel(T) +
                A_outer * k_outer(T))

    # Get heat load
    heat_result = compute_heat_load(geometry, materials, T_cold, T_hot, L_m)
    Q = heat_result['total_heat_load_W']

    if Q < 1e-20:
        # Isothermal case
        return [(s, T_cold) for s in linspace(0, 1, n_points)]

    # Build T-to-s lookup
    T_grid = logspace(log10(max(T_cold, 0.05)), log10(T_hot), 500)
    G_vals = G(T_grid)

    ds_dT = G_vals / (Q * L_m)

    s_grid = zeros_like(T_grid)
    for i in range(1, len(T_grid)):
        s_grid[i] = s_grid[i-1] + 0.5 * (ds_dT[i] + ds_dT[i-1]) * (T_grid[i] - T_grid[i-1])

    if s_grid[-1] > 0:
        s_grid = s_grid / s_grid[-1]

    s_uniform = linspace(0, 1, n_points)
    T_profile = interp(s_uniform, s_grid, T_grid)

    return list(zip(s_uniform, T_profile))


def compute_G_function(geometry, materials, T_range):
    """Compute cable thermal conductance function G(T)"""

    d_inner = geometry['inner_diameter_um'] * 1e-6
    t_dielectric = geometry.get('dielectric_thickness_um', d_inner * 0.5) * 1e-6

    k_inner = MATERIALS_DB['Conductors'][materials['inner']]['k_func']
    k_diel = MATERIALS_DB['Dielectrics'][materials['dielectric']]['k_func']
    k_outer = MATERIALS_DB['Conductors'][materials['outer']]['k_func']

    if geometry['cable_type'] == 'Ribbon':
        pitch = geometry['trace_pitch_um'] * 1e-6
        foil_t = geometry['foil_thickness_um'] * 1e-6
        n_foil = geometry['foil_sheets']
        A_inner = pi * (d_inner / 2)**2
        d_outer_dielectric = d_inner + 2 * t_dielectric
        A_dielectric = pi * ((d_outer_dielectric / 2)**2 - (d_inner / 2)**2)
        A_outer = pitch * foil_t * n_foil
    else:
        d_outer = geometry.get('outer_diameter_um', 1520.0) * 1e-6
        t_outer = geometry.get('outer_thickness_um', 150.0) * 1e-6
        A_inner = pi * (d_inner / 2)**2
        d_outer_dielectric = d_inner + 2 * t_dielectric
        A_dielectric = pi * ((d_outer_dielectric / 2)**2 - (d_inner / 2)**2)
        r_outer_inner = d_outer_dielectric / 2
        r_outer_outer = r_outer_inner + t_outer
        A_outer = pi * (r_outer_outer**2 - r_outer_inner**2)

    G_vals = []
    for T in T_range:
        G = (A_inner * k_inner(T) +
             A_dielectric * k_diel(T) +
             A_outer * k_outer(T))
        G_vals.append(G * 1e6)  # Convert to microW/(cm*K)

    return array(G_vals)


# ============================================================
# Streamlit UI
# ============================================================

#def main():
    # Sidebar
with sidebar:
    subheader("Cable Preset")
    preset_name = radio("Select Preset", list(CABLE_PRESETS.keys()), index=0 , horizontal=True)

    preset = CABLE_PRESETS[preset_name]
    code(['preset=', preset])
    #['preset=', {'cable_type': 'Ribbon', 'num_traces': 8, 'inner_diameter_um': 76.2, 'dielectric_thickness_um': 63.5, 'trace_pitch_um': 3556.0, 'foil_thickness_um': 25.4, 'foil_sheets': 2, 'inner_material': 'NbTi', 'dielectric_material': 'FEP', 'outer_material': 'NbTi'}]

    #markdown("---")
    subheader("Geometry")

    cable_type = radio("Cable Type", ['Ribbon', 'Coaxial'], index=0 if preset['cable_type'] == 'Ribbon' else 1 , horizontal=True)

    num_traces = number_input("Number of Traces", 1, 100, preset['num_traces'])

    col1, col2 = columns(2)
    with col1:
        inner_diameter = number_input(
            "Inner Diameter (um)", 10.0, 1000.0, preset['inner_diameter_um'], 0.1,
            help="Center conductor diameter"
        )
    with col2:
        dielectric_thickness = number_input(
            "Dielectric Thickness (um)", 10.0, 2000.0, 
            preset.get('dielectric_thickness_um', 63.5), 0.1
        )

    if cable_type == 'Ribbon':
        col1, col2 = columns(2)
        with col1:
            trace_pitch = number_input(
                "Trace Pitch (um)", 100.0, 10000.0, 
                preset.get('trace_pitch_um', 3556.0), 0.1
            )
        with col2:
            foil_thickness = number_input(
                "Foil Thickness (um)", 1.0, 200.0, 
                preset.get('foil_thickness_um', 25.4), 0.1
            )
        foil_sheets = number_input(
            "Foil Sheets", 1, 10, preset.get('foil_sheets', 2)
        )
        outer_diameter = 1520.0
        outer_thickness = 150.0
    else:
        col1, col2 = columns(2)
        with col1:
            outer_diameter = number_input(
                "Outer Diameter (um)", 100.0, 5000.0, 
                preset.get('outer_diameter_um', 1520.0), 0.1
            )
        with col2:
            outer_thickness = number_input(
                "Outer Thickness (um)", 10.0, 500.0, 
                preset.get('outer_thickness_um', 150.0), 0.1
            )
        trace_pitch = 3556.0
        foil_thickness = 25.4
        foil_sheets = 2

    #markdown("---")
    subheader("Materials")

    inner_material = radio("Inner Conductor", list(MATERIALS_DB['Conductors'].keys()), index=list(MATERIALS_DB['Conductors'].keys()).index(preset['inner_material']) , horizontal=True)

    dielectric_material = radio("Dielectric", list(MATERIALS_DB['Dielectrics'].keys()), index=list(MATERIALS_DB['Dielectrics'].keys()).index(preset['dielectric_material']) , horizontal=True)

    outer_material = radio("Outer Conductor", list(MATERIALS_DB['Conductors'].keys()), index=list(MATERIALS_DB['Conductors'].keys()).index(preset['outer_material']) , horizontal=True)

    #markdown("---")
    subheader("Temperature")

    col1, col2 = columns(2)
    with col1:
        T_cold = number_input("Cold End (K)", 0.05, 100.0, 0.1, 0.01)
    with col2:
        T_hot = number_input("Hot End (K)", 0.1, 300.0, 1.0, 0.1)

    cable_length = number_input("Cable Length (m)", 0.01, 10.0, 0.3048, 0.001,
                                   help="Default: 1 foot = 0.3048 m")

        #markdown("---")
    # Build geometry and materials dicts
    geometry = {
        'cable_type': cable_type,
        'num_traces': num_traces,
        'inner_diameter_um': inner_diameter,
        'dielectric_thickness_um': dielectric_thickness,
        'trace_pitch_um': trace_pitch,
        'foil_thickness_um': foil_thickness,
        'foil_sheets': foil_sheets,
        'outer_diameter_um': outer_diameter,
        'outer_thickness_um': outer_thickness,
    }

    materials = {
        'inner': inner_material,
        'dielectric': dielectric_material,
        'outer': outer_material,
    }

# Compute results
result = compute_heat_load(geometry, materials, T_cold, T_hot, cable_length)
T_profile = compute_temperature_profile(geometry, materials, T_cold, T_hot, cable_length)


# Tabs for plots
結果, tab1, tab2, tab3 = tabs(['結果', "溫度趨勢", "G(T) Function", "Material k(T)"]) #Temperature Profile

with tab1:
    subheader("Temperature Profile Along Cable")

    positions = [p[0] * 100 for p in T_profile]
    temperatures = [p[1] for p in T_profile]

    fig = Figure()
    fig.add_trace(Scatter(
        x=positions, y=temperatures,
        mode='lines',
        line=dict(color='#1f77b4', width=3),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.2)',
        name='T(x)'
    ))
    fig.update_layout(
        xaxis_title="Position along cable (%)",
        yaxis_title="Temperature (K)",
        yaxis_type="log" if T_cold < 1.0 else "linear",
        height=500,
        template="plotly_white"
    )
    plotly_chart(fig, use_container_width=True)

    # Data table
    subheader("Sample Points")
    sample_data = []
    for s, T in T_profile[::20]:
        sample_data.append({"Position (%)": "{:.1f}".format(s*100), "Temperature (K)": "{:.4f}".format(T)})
    table(sample_data)

with tab2:
    subheader("Cable Thermal Conductance G(T)")
    markdown("G(T) = $\sum_i A_i * k_i(T)$ [microW/(cm*K)]")

    T_range = logspace(log10(max(0.05, T_cold*0.5)), log10(T_hot*2), 200)
    G_vals = compute_G_function(geometry, materials, T_range)

    fig = Figure()
    fig.add_trace(Scatter(
        x=T_range, y=G_vals,
        mode='lines',
        line=dict(color='#ff7f0e', width=3),
        name='G(T)'
    ))
    fig.update_layout(
        xaxis_title="Temperature (K)",
        yaxis_title="G(T) [microW/(cm*K)]",
        xaxis_type="log",
        yaxis_type="log",
        height=500,
        template="plotly_white"
    )
    plotly_chart(fig, use_container_width=True)

    # Compare with other presets
    subheader("Compare with Other Cable Presets")

    compare_presets = multiselect(
        "Select cables to compare",
        list(CABLE_PRESETS.keys()),
        default=[preset_name, 'CryoCoax BCB012 (Semi-Rigid)']
    )

    if compare_presets:
        fig = Figure()
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

        for i, name in enumerate(compare_presets):
            p = CABLE_PRESETS[name]
            g = {
                'cable_type': p['cable_type'],
                'num_traces': p['num_traces'],
                'inner_diameter_um': p['inner_diameter_um'],
                'dielectric_thickness_um': p.get('dielectric_thickness_um', 63.5),
                'trace_pitch_um': p.get('trace_pitch_um', 3556.0),
                'foil_thickness_um': p.get('foil_thickness_um', 25.4),
                'foil_sheets': p.get('foil_sheets', 2),
                'outer_diameter_um': p.get('outer_diameter_um', 1520.0),
                'outer_thickness_um': p.get('outer_thickness_um', 150.0),
            }
            m = {
                'inner': p['inner_material'],
                'dielectric': p['dielectric_material'],
                'outer': p['outer_material'],
            }
            G_vals_comp = compute_G_function(g, m, T_range)

            fig.add_trace(Scatter(
                x=T_range, y=G_vals_comp,
                mode='lines',
                line=dict(color=colors[i % len(colors)], width=2),
                name=name
            ))

        fig.update_layout(
            xaxis_title="Temperature (K)",
            yaxis_title="G(T) [microW/(cm*K)]",
            xaxis_type="log",
            yaxis_type="log",
            height=500,
            template="plotly_white"
        )
        plotly_chart(fig, use_container_width=True)

with tab3:
    subheader("Material Thermal Conductivity k(T)")

    T_range = logspace(log10(0.05), log10(300), 300)

    fig = Figure()

    # Plot conductor materials
    for name, data in MATERIALS_DB['Conductors'].items():
        k_vals = data['k_func'](T_range)
        fig.add_trace(Scatter(
            x=T_range, y=k_vals,
            mode='lines',
            line=dict(color=data['color'], width=2),
            name="{} (conductor)".format(name)
        ))

    # Plot dielectric materials
    for name, data in MATERIALS_DB['Dielectrics'].items():
        k_vals = data['k_func'](T_range)
        fig.add_trace(Scatter(
            x=T_range, y=k_vals,
            mode='lines',
            line=dict(color=data['color'], width=2, dash='dash'),
            name="{} (dielectric)".format(name)
        ))

    fig.update_layout(
        xaxis_title="Temperature (K)",
        yaxis_title="k(T) [W/(m*K)]",
        xaxis_type="log",
        yaxis_type="log",
        height=600,
        template="plotly_white"
    )
    plotly_chart(fig, use_container_width=True)

    info("""
    **Data Sources**:
    - Sub-Kelvin: Daal et al. (2019), Kushino et al. (2005), Lakeshore
    - Above 1K: NIST Cryogenic Materials Database
    - NbTi superconducting: Electronic thermal conductivity suppressed below Tc~9.2K, phonon-dominated
    """)

# Summary table
#markdown("---")
subheader("Summary Table")

summary_data = []
for name, preset_data in CABLE_PRESETS.items():
    g = {
        'cable_type': preset_data['cable_type'],
        'num_traces': preset_data['num_traces'],
        'inner_diameter_um': preset_data['inner_diameter_um'],
        'dielectric_thickness_um': preset_data.get('dielectric_thickness_um', 63.5),
        'trace_pitch_um': preset_data.get('trace_pitch_um', 3556.0),
        'foil_thickness_um': preset_data.get('foil_thickness_um', 25.4),
        'foil_sheets': preset_data.get('foil_sheets', 2),
        'outer_diameter_um': preset_data.get('outer_diameter_um', 1520.0),
        'outer_thickness_um': preset_data.get('outer_thickness_um', 150.0),
    }
    m = {
        'inner': preset_data['inner_material'],
        'dielectric': preset_data['dielectric_material'],
        'outer': preset_data['outer_material'],
    }
    r = compute_heat_load(g, m, 0.1, 1.0, 0.3048)
    summary_data.append({
        "Cable": name,
        "Type": preset_data['cable_type'],
        "Heat Load (nW/trace)": "{:.2f}".format(r['per_trace_nW']),
        "Inner": preset_data['inner_material'],
        "Dielectric": preset_data['dielectric_material'],
        "Outer": preset_data['outer_material'],
    })

table(summary_data)

# Footer
#markdown("---")

#if __name__ == "__main__": main()
with sidebar:
    #markdown('<div class="sub-header">Cryogenic Cable Heat Load Calculator</div>', unsafe_allow_html=True)
    #markdown('<div class="sub-header">Steady-state thermal conduction for cryogenic coaxial cables (0.1-300 K)</div>', unsafe_allow_html=True)
    info("""
    **Physics**: Based on Fourier's law with temperature-dependent 
    thermal conductivity k(T). Integrals evaluated via adaptive 
    Simpson quadratu

    **Reference**: Smith et al. (2024), IEEE Trans. Appl. Supercond.
    """)
    caption("""**Cryogenic Cable Heat Load Calculator** | Based on Smith et al. (2024) IEEE TASC 
| Physics: Fourier's law with adaptive Simpson quadrature
| GitHub: MazinLab/FlaxHeatLoadCalc
""")
