from streamlit import caption, columns, subheader, markdown, metric, number_input, pyplot, set_page_config, sidebar, slider, table, tabs, write
from matplotlib.pyplot import subplots, tight_layout
from numpy import abs, argmin, array, exp, linspace, log, log10, max as npMax, ndarray, sqrt
from pandas import DataFrame

#import streamlit as st
#import numpy as np
#import matplotlib.pyplot as plt
from scipy.special import jv, kv
from scipy.constants import h, k, epsilon_0, mu_0, c, pi, hbar
#import pandas as pd
from dataclasses import dataclass
from typing import Tuple, List
#import warnings
#warnings.filterwarnings('ignore')

# ============================================================
# Kapton Material Properties
# ============================================================
@dataclass
class KaptonProperties:
    """Kapton (Polyimide) material properties across temperature ranges"""
    
    # Base properties at 300K
    epsilon_r_300K: float = 3.4  # Relative permittivity
    tan_delta_300K: float = 0.002  # Loss tangent at 1kHz
    conductivity_300K: float = 1e-15  # S/m (essentially insulating)
    thermal_conductivity_300K: float = 0.12  # W/(m·K)
    specific_heat_300K: float = 1090  # J/(kg·K)
    density: float = 1420  # kg/m³
    
    # Temperature-dependent permittivity (empirical fit)
    def epsilon_r(self, T: float) -> float:
        """Relative permittivity as function of temperature (K)"""
        if T < 1:  # mK range
            return 2.8  # Reduced at very low T due to frozen dipoles
        elif T < 77:  # Cryogenic
            return 2.9 + 0.5 * (T / 300)**0.5
        elif T < 400:
            return 3.4 - 0.3 * ((T - 300) / 100)  # Slight decrease with T
        else:
            return 3.1  # High temp asymptote
    
    # Loss tangent (strongly frequency and temperature dependent)
    def tan_delta(self, T: float, f: float) -> float:
        """Loss tangent: increases with frequency, decreases with cooling"""
        f_GHz = f / 1e9
        
        if T < 0.1:  # mK range - dominated by two-level systems (TLS)
            # TLS loss: tan δ ∝ 1/√(1 + (2πfτ)²), saturates at low T
            tls_loss = 5e-6 * (f_GHz)**0.3
            return tls_loss
        elif T < 10:  # Cryogenic
            # Transition between TLS and phonon-dominated
            base = 1e-4 * (300 / T)**1.5
            freq_dep = 1 + 0.1 * f_GHz**0.5
            return base * freq_dep
        else:
            # Room temp: dipolar + conduction losses
            dipolar = self.tan_delta_300K * (300 / T)**0.3
            conduction = 1e-6 * f_GHz  # Increases with f
            return dipolar + conduction
    
    # Dielectric conductivity
    def conductivity(self, T: float, f: float) -> float:
        """AC conductivity: σ = ωε₀εᵣtanδ"""
        eps = self.epsilon_r(T)
        td = self.tan_delta(T, f)
        return 2 * pi * f * epsilon_0 * eps * td
    
    # Thermal conductivity (strong T dependence)
    def thermal_conductivity(self, T: float) -> float:
        """W/(m·K) - phonon dominated at low T"""
        if T < 1:
            return 0.004 * T**1.5  # Phonon glass behavior
        elif T < 10:
            return 0.004 + 0.001 * T**2
        elif T < 100:
            return 0.008 + 0.0001 * T**1.5
        else:
            return 0.12 * (T / 300)**0.8
    
    # Specific heat (Debye model approximation)
    def specific_heat(self, T: float) -> float:
        """J/(kg·K)"""
        theta_D = 500  # Debye temperature approximation for Kapton
        if T < theta_D / 10:
            x = theta_D / T
            # Low-T limit: C ∝ T³
            return 0.5 * (T / theta_D)**3 * self.specific_heat_300K
        else:
            return self.specific_heat_300K * (T / 300)**0.9
    
    # Dielectric strength
    def dielectric_strength(self, T: float) -> float:
        """V/μm - increases at low T"""
        base = 280  # V/μm at 300K
        if T < 77:
            return base * (1 + 0.5 * (77 - npMax(T, 4)) / 73)
        return base

# ============================================================
# RF Coaxial Cable Model
# ============================================================
class CoaxialCable:
    """Model of coaxial cable with Kapton insulation layer"""
    
    def __init__(self, 
                 core_radius: float = 0.5e-3,      # Inner conductor radius (m)
                 dielectric_radius: float = 1.5e-3, # Dielectric outer radius (m)
                 shield_radius: float = 1.8e-3,     # Shield inner radius (m)
                 kapton_thickness: float = 50e-6,   # Kapton wrap thickness (m)
                 cable_length: float = 1.0,         # Cable length (m)
                 kapton: KaptonProperties = None):
        
        self.a = core_radius           # Inner conductor
        self.b = dielectric_radius     # Dielectric outer
        self.c = shield_radius         # Shield inner
        self.t_kapton = kapton_thickness
        self.L = cable_length
        self.kapton = kapton or KaptonProperties()
        
        # Conductor properties (copper)
        self.sigma_cu = 5.8e7  # S/m
        self.mu_cu = mu_0
        
    def surface_resistance(self, f: float, T: float) -> float:
        """Surface resistance of copper at temperature T and frequency f"""
        # RRR (Residual Resistivity Ratio) effect
        if T < 20:
            rrr = 100  # Typical for annealed copper at cryo
        else:
            rrr = 1
        
        rho_0 = 1.7e-8 / rrr  # Residual resistivity
        rho = rho_0 * (1 + 0.004 * (T - 4)) if T < 20 else 1.7e-8 * (1 + 0.004 * (T - 293))
        
        skin_depth = sqrt(rho / (pi * f * mu_0))
        return sqrt(pi * f * mu_0 * rho)  # Rs = √(πfμ₀ρ)
    
    def characteristic_impedance(self, f: float, T: float) -> complex:
        """Complex characteristic impedance"""
        eps_r = self.kapton.epsilon_r(T)
        td = self.kapton.tan_delta(T, f)
        
        # Complex permittivity
        eps_c = eps_r * (1 - 1j * td)
        
        # For coax: Z₀ = (1/2π)√(μ/ε) * ln(b/a)
        Z0 = (1 / (2 * pi)) * sqrt(mu_0 / (epsilon_0 * eps_c)) * log(self.b / self.a)
        return Z0
    
    def propagation_constant(self, f: float, T: float) -> complex:
        """γ = α + jβ"""
        eps_r = self.kapton.epsilon_r(T)
        td = self.kapton.tan_delta(T, f)
        
        omega = 2 * pi * f
        eps_c = eps_r * (1 - 1j * td)
        
        # Phase constant
        beta = omega * sqrt(mu_0 * epsilon_0 * eps_c.real)
        
        # Attenuation: dielectric loss + conductor loss
        alpha_d = (omega / 2) * sqrt(mu_0 * epsilon_0 * eps_r) * td
        
        Rs = self.surface_resistance(f, T)
        alpha_c = (Rs / (2 * pi)) * (1/self.a + 1/self.b) / sqrt(mu_0 / (epsilon_0 * eps_r))
        
        alpha = alpha_d + alpha_c
        return alpha + 1j * beta.real

# ============================================================
# Scenario 1: High Frequency Analysis
# ============================================================
def analyze_high_frequency(cable: CoaxialCable, f_range: ndarray, T: float = 300):
    """Analyze RF performance at high frequencies"""
    
    results = {
        'frequency': f_range,
        'insertion_loss': [],
        'return_loss': [],
        'crosstalk': [],
        'phase_velocity': [],
        'effective_eps': []
    }
    
    for f in f_range:
        gamma = cable.propagation_constant(f, T)
        alpha = gamma.real  # Np/m
        beta = gamma.imag
        
        # Insertion Loss (dB)
        IL = 20 * log10(exp(alpha * cable.L))  # α in Np/m
        results['insertion_loss'].append(IL)
        
        # Return Loss (assume slight mismatch, |Γ| = 0.05)
        Z0 = cable.characteristic_impedance(f, T)
        Z0_nominal = 50  # Ohm
        gamma_ref = (Z0 - Z0_nominal) / (Z0 + Z0_nominal)
        RL = -20 * log10(abs(gamma_ref))
        results['return_loss'].append(RL)
        
        # Crosstalk (near-end, NEXT) - simplified model
        # NEXT ∝ coupling coefficient × frequency × length
        # Kapton's high εᵣ increases coupling vs air
        k_coupling = 0.01 * (cable.kapton.epsilon_r(T) / 3.4) * (f / 1e9)**0.5
        separation = 3 * cable.c  # 3x cable diameter separation
        NEXT = 20 * log10(k_coupling * cable.L / separation)
        results['crosstalk'].append(NEXT)
        
        # Phase velocity
        v_p = 2 * pi * f / beta
        results['phase_velocity'].append(v_p)
        
        # Effective permittivity
        eps_eff = (c / v_p)**2
        results['effective_eps'].append(eps_eff)
    
    return {k: array(v) for k, v in results.items()}

# ============================================================
# Scenario 2: High Temperature Analysis
# ============================================================
def analyze_high_temperature(cable: CoaxialCable, T_range: ndarray, f: float = 10e9):
    """Analyze thermal effects on RF performance"""
    
    results = {
        'temperature': T_range,
        'insertion_loss': [],
        'return_loss': [],
        'crosstalk': [],
        'dielectric_strength': [],
        'thermal_expansion_effect': [],
        'power_handling': []
    }
    
    # Thermal expansion coefficient for Kapton (approx)
    alpha_th = 20e-6  # /K (in-plane)
    
    for T in T_range:
        gamma = cable.propagation_constant(f, T)
        alpha_att = gamma.real
        
        # IL increases with T due to higher loss tangent
        IL = 20 * log10(exp(alpha_att * cable.L))
        results['insertion_loss'].append(IL)
        
        # Z0 changes with T (thermal expansion)
        # b/a ratio changes
        delta_T = T - 300
        b_new = cable.b * (1 + alpha_th * delta_T)
        a_new = cable.a * (1 + 17e-6 * delta_T)  # Cu expansion
        Z0_T = 50 * log(b_new / a_new) / log(cable.b / cable.a)
        
        gamma_ref = (Z0_T - 50) / (Z0_T + 50)
        RL = -20 * log10(npMax(abs(gamma_ref), 1e-10))
        results['return_loss'].append(RL)
        
        # Crosstalk: thermal noise + increased dielectric loss
        k_coupling = 0.01 * (cable.kapton.epsilon_r(T) / 3.4)
        NEXT = 20 * log10(k_coupling * cable.L / (3 * cable.c))
        results['crosstalk'].append(NEXT)
        
        # Dielectric strength decreases with T
        ds = cable.kapton.dielectric_strength(T)
        results['dielectric_strength'].append(ds)
        
        # Thermal expansion effect on impedance
        results['thermal_expansion_effect'].append((Z0_T - 50) / 50 * 100)  # % deviation
        
        # Power handling limited by thermal conductivity
        # P_max ∝ k * ΔT / (α * L)
        k_th = cable.kapton.thermal_conductivity(T)
        delta_T_max = 50  # Max allowed temp rise
        P_max = k_th * delta_T_max / (alpha_att * cable.L) * 1e-3  # mW
        results['power_handling'].append(P_max)
    
    return {k: array(v) for k, v in results.items()}

# ============================================================
# Scenario 3: High Voltage Analysis
# ============================================================
def analyze_high_voltage(cable: CoaxialCable, V_range: ndarray, T: float = 300, f: float = 1e6):
    """Analyze high voltage breakdown and corona effects"""
    
    results = {
        'voltage': V_range,
        'electric_field_max': [],  # At inner conductor surface
        'breakdown_margin': [],
        'leakage_current': [],
        'partial_discharge_risk': [],
        'insulation_resistance': []
    }
    
    ds = cable.kapton.dielectric_strength(T) * 1e6  # Convert to V/m
    
    for V in V_range:
        # E-field in coaxial structure: E(r) = V / (r * ln(b/a))
        E_max = V / (cable.a * log(cable.b / cable.a))
        results['electric_field_max'].append(E_max / 1e6)  # MV/m
        
        # Breakdown margin
        margin = ds / E_max
        results['breakdown_margin'].append(margin)
        
        # Leakage current through Kapton
        sigma = cable.kapton.conductivity(T, f)
        R_ins = log(cable.b / cable.a) / (2 * pi * cable.L * sigma)
        I_leak = V / R_ins
        results['leakage_current'].append(I_leak)
        
        # Partial discharge risk (voids, imperfections)
        # PD inception when E > 0.7 * ds locally
        pd_risk = 1 if E_max > 0.7 * ds else 0
        # Add probabilistic factor for surface roughness
        if E_max > 0.5 * ds:
            pd_risk = (E_max - 0.5 * ds) / (0.5 * ds)
        results['partial_discharge_risk'].append(pd_risk)
        
        # Insulation resistance
        results['insulation_resistance'].append(R_ins / 1e9)  # GΩ
    
    return {k: array(v) for k, v in results.items()}

# ============================================================
# Scenario 4: Cryogenic / Quantum Computing (mK range)
# ============================================================
def analyze_cryogenic_quantum(cable: CoaxialCable, T_range: ndarray, f_qubit: float = 5e9):
    """Analyze quantum coherence and thermal loading at mK temperatures"""
    
    results = {
        'temperature': T_range,
        'qubit_coherence_time_T1': [],
        'qubit_coherence_time_T2': [],
        'thermal_photon_occupation': [],
        'dielectric_loss_tangent': [],
        'thermal_load_per_meter': [],
        'heat_capacity': [],
        'thermal_relaxation_time': [],
        'tls_density': []
    }
    
    # Qubit parameters (typical transmon)
    omega_q = 2 * pi * f_qubit
    E_j = 20 * 1e9 * h  # Josephson energy ~20 GHz
    E_c = 0.3 * 1e9 * h  # Charging energy
    
    for T in T_range:
        # Thermal photon occupation: n_th = 1 / (exp(ℏω/kT) - 1)
        if h * f_qubit / (k * T) > 50:
            n_th = exp(-h * f_qubit / (k * T))
        else:
            n_th = 1 / (exp(h * f_qubit / (k * T)) - 1)
        results['thermal_photon_occupation'].append(n_th)
        
        # Dielectric loss tangent at mK (TLS dominated)
        td = cable.kapton.tan_delta(T, f_qubit)
        results['dielectric_loss_tangent'].append(td)
        
        # T1 coherence time limited by dielectric loss
        # 1/T1 = (4πf/E_j) * (E_c/E_j) * ε_r * tanδ * ...
        # Simplified: T1 ∝ 1/(ω * tanδ)
        quality_factor = 1 / td
        T1 = quality_factor / (2 * pi * f_qubit)
        results['qubit_coherence_time_T1'].append(T1)
        
        # T2: dephasing (T2 ≈ 2*T1 at low T, plus additional noise)
        # Pure dephasing from low-frequency noise (1/f)
        T_phi = 1e-3 / (T + 1e-6)  # Empirical 1/f noise model
        T2 = 1 / (1/(2*T1) + 1/T_phi)
        results['qubit_coherence_time_T2'].append(T2)
        
        # TLS density (two-level systems per volume per energy)
        # P_TLS ∝ T^0.3 (roughly constant in mK range)
        P_tls = 1e45 * (T / 0.01)**0.3  # states/(J·m³)
        results['tls_density'].append(P_tls)
        
        # Thermal load (heat leak) through Kapton
        # Q = k * A * ΔT / L
        k_th = cable.kapton.thermal_conductivity(T)
        # Assume 1K bath to mK stage
        delta_T = 1.0 - T if T < 1 else 0.1
        area = pi * ((cable.a + cable.t_kapton)**2 - cable.a**2)
        Q = k_th * area * delta_T / cable.L
        results['thermal_load_per_meter'].append(Q)
        
        # Heat capacity of Kapton layer
        C_v = cable.kapton.specific_heat(T)
        mass = cable.kapton.density * pi * ((cable.a + cable.t_kapton)**2 - cable.a**2) * cable.L
        C_total = C_v * mass
        results['heat_capacity'].append(C_total)
        
        # Thermal relaxation time
        tau = C_total / (k_th * area / cable.L) if k_th > 0 else 1e6
        results['thermal_relaxation_time'].append(tau)
    
    return {k: array(v) for k, v in results.items()}

#import streamlit as st
#import numpy as np
#import matplotlib.pyplot as plt
from scipy.constants import h, k, epsilon_0, mu_0, c, pi, hbar
#import pandas as pd
from dataclasses import dataclass

set_page_config(page_title="Kapton RF Cable Analyzer", layout="wide")

# Custom CSS
markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    .scenario-box {
        background: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .warning-box {
        background: black;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #ffc107;
    }
    .danger-box {
        background: #f8d7da;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)
from streamlit import empty, radio, text_input, sidebar
MENU, 表單=[], ['PI分析', '', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
狀態=empty()
if menu==len(表單): #
  pass
elif menu==MENU[1]: #
  pass
elif menu==MENU[0]: #PI分析
  pass
# ============================================================
# Kapton Properties Class
# ============================================================
@dataclass
class KaptonProperties:
    epsilon_r_300K: float = 3.4
    tan_delta_300K: float = 0.002
    conductivity_300K: float = 1e-15
    thermal_conductivity_300K: float = 0.12
    specific_heat_300K: float = 1090
    density: float = 1420
    
    def epsilon_r(self, T: float) -> float:
        if T < 1:
            return 2.8
        elif T < 77:
            return 2.9 + 0.5 * (T / 300)**0.5
        elif T < 400:
            return 3.4 - 0.3 * ((T - 300) / 100)
        else:
            return 3.1
    
    def tan_delta(self, T: float, f: float) -> float:
        f_GHz = f / 1e9
        if T < 0.1:
            return 5e-6 * (f_GHz)**0.3
        elif T < 10:
            base = 1e-4 * (300 / T)**1.5
            freq_dep = 1 + 0.1 * f_GHz**0.5
            return base * freq_dep
        else:
            dipolar = self.tan_delta_300K * (300 / T)**0.3
            conduction = 1e-6 * f_GHz
            return dipolar + conduction
    
    def conductivity(self, T: float, f: float) -> float:
        eps = self.epsilon_r(T)
        td = self.tan_delta(T, f)
        return 2 * pi * f * epsilon_0 * eps * td
    
    def thermal_conductivity(self, T: float) -> float:
        if T < 1:
            return 0.004 * T**1.5
        elif T < 10:
            return 0.004 + 0.001 * T**2
        elif T < 100:
            return 0.008 + 0.0001 * T**1.5
        else:
            return 0.12 * (T / 300)**0.8
    
    def specific_heat(self, T: float) -> float:
        theta_D = 500
        if T < theta_D / 10:
            return 0.5 * (T / theta_D)**3 * self.specific_heat_300K
        else:
            return self.specific_heat_300K * (T / 300)**0.9
    
    def dielectric_strength(self, T: float) -> float:
        base = 280
        if T < 77:
            return base * (1 + 0.5 * (77 - npMax(T, 4)) / 73)
        return base

# ============================================================
# Coaxial Cable Model
# ============================================================
class CoaxialCable:
    def __init__(self, core_radius=0.5e-3, dielectric_radius=1.5e-3, 
                 shield_radius=1.8e-3, kapton_thickness=50e-6, 
                 cable_length=1.0, kapton=None):
        self.a = core_radius
        self.b = dielectric_radius
        self.c = shield_radius
        self.t_kapton = kapton_thickness
        self.L = cable_length
        self.kapton = kapton or KaptonProperties()
        self.sigma_cu = 5.8e7
        
    def surface_resistance(self, f, T):
        if T < 20:
            rrr = 100
        else:
            rrr = 1
        rho_0 = 1.7e-8 / rrr
        rho = rho_0 * (1 + 0.004 * (T - 4)) if T < 20 else 1.7e-8 * (1 + 0.004 * (T - 293))
        return sqrt(pi * f * mu_0 * rho)
    
    def propagation_constant(self, f, T):
        eps_r = self.kapton.epsilon_r(T)
        td = self.kapton.tan_delta(T, f)
        omega = 2 * pi * f
        alpha_d = (omega / 2) * sqrt(mu_0 * epsilon_0 * eps_r) * td
        Rs = self.surface_resistance(f, T)
        alpha_c = (Rs / (2 * pi)) * (1/self.a + 1/self.b) / sqrt(mu_0 / (epsilon_0 * eps_r))
        alpha = alpha_d + alpha_c
        beta = omega * sqrt(mu_0 * epsilon_0 * eps_r)
        return alpha + 1j * beta

# ============================================================
# Analysis Functions
# ============================================================
def analyze_hf(cable, f_range, T=300):
    results = {'frequency': f_range, 'IL': [], 'RL': [], 'XT': [], 'v_p': [], 'eps_eff': []}
    for f in f_range:
        gamma = cable.propagation_constant(f, T)
        alpha, beta = gamma.real, gamma.imag
        IL = 20 * log10(exp(alpha * cable.L))
        Z0 = (1/(2*pi)) * sqrt(mu_0/(epsilon_0*cable.kapton.epsilon_r(T))) * log(cable.b/cable.a)
        gamma_ref = (Z0 - 50) / (Z0 + 50)
        RL = -20 * log10(max(abs(gamma_ref), 1e-10))
        k_coupling = 0.01 * (cable.kapton.epsilon_r(T)/3.4) * (f/1e9)**0.5
        XT = 20 * log10(k_coupling * cable.L / (3*cable.c))
        v_p = 2*pi*f / beta
        eps_eff = (c/v_p)**2
        results['IL'].append(IL)
        results['RL'].append(RL)
        results['XT'].append(XT)
        results['v_p'].append(v_p)
        results['eps_eff'].append(eps_eff)
    return {k: array(v) for k, v in results.items()}

def analyze_ht(cable, T_range, f=10e9):
    results = {'temperature': T_range, 'IL': [], 'RL': [], 'XT': [], 'DS': [], 'PH': []}
    alpha_th = 20e-6
    for T in T_range:
        gamma = cable.propagation_constant(f, T)
        IL = 20 * log10(exp(gamma.real * cable.L))
        delta_T = T - 300
        b_new = cable.b * (1 + alpha_th * delta_T)
        a_new = cable.a * (1 + 17e-6 * delta_T)
        Z0_T = 50 * log(b_new/a_new) / log(cable.b/cable.a)
        gamma_ref = (Z0_T - 50) / (Z0_T + 50)
        RL = -20 * log10(max(abs(gamma_ref), 1e-10))
        k_coupling = 0.01 * (cable.kapton.epsilon_r(T)/3.4)
        XT = 20 * log10(k_coupling * cable.L / (3*cable.c))
        DS = cable.kapton.dielectric_strength(T)
        k_th = cable.kapton.thermal_conductivity(T)
        PH = k_th * 50 / (gamma.real * cable.L) * 1e-3
        results['IL'].append(IL)
        results['RL'].append(RL)
        results['XT'].append(XT)
        results['DS'].append(DS)
        results['PH'].append(PH)
    return {k: array(v) for k, v in results.items()}

def analyze_hv(cable, V_range, T=300, f=1e6):
    results = {'voltage': V_range, 'E_max': [], 'margin': [], 'I_leak': [], 'PD': [], 'R_ins': []}
    ds = cable.kapton.dielectric_strength(T) * 1e6
    for V in V_range:
        E_max = V / (cable.a * log(cable.b/cable.a))
        margin = ds / E_max
        sigma = cable.kapton.conductivity(T, f)
        R_ins = log(cable.b/cable.a) / (2 * pi * cable.L * sigma)
        I_leak = V / R_ins
        pd_risk = max(0, (E_max - 0.5*ds) / (0.5*ds)) if E_max > 0.5*ds else 0
        results['E_max'].append(E_max/1e6)
        results['margin'].append(margin)
        results['I_leak'].append(I_leak)
        results['PD'].append(pd_risk)
        results['R_ins'].append(R_ins/1e9)
    return {k: array(v) for k, v in results.items()}

def analyze_cryo(cable, T_range, f_qubit=5e9):
    results = {'temperature': T_range, 'T1': [], 'T2': [], 'n_th': [], 'td': [], 
               'Q_thermal': [], 'C': [], 'tau': [], 'TLS': []}
    omega_q = 2 * pi * f_qubit
    for T in T_range:
        x = h * f_qubit / (k * T)
        n_th = exp(-x) if x > 50 else 1/(exp(x)-1)
        td = cable.kapton.tan_delta(T, f_qubit)
        Q = 1/td
        T1 = Q / (2 * pi * f_qubit)
        T_phi = 1e-3 / (T + 1e-6)
        T2 = 1 / (1/(2*T1) + 1/T_phi)
        P_tls = 1e45 * (T/0.01)**0.3
        k_th = cable.kapton.thermal_conductivity(T)
        delta_T = 1.0 - T if T < 1 else 0.1
        area = pi * ((cable.a + cable.t_kapton)**2 - cable.a**2)
        Q_th = k_th * area * delta_T / cable.L
        C_v = cable.kapton.specific_heat(T)
        mass = cable.kapton.density * area * cable.L
        C_total = C_v * mass
        tau = C_total / (k_th * area / cable.L) if k_th > 0 else 1e6
        results['T1'].append(T1)
        results['T2'].append(T2)
        results['n_th'].append(n_th)
        results['td'].append(td)
        results['Q_thermal'].append(Q_th)
        results['C'].append(C_total)
        results['tau'].append(tau)
        results['TLS'].append(P_tls)
    return {k: array(v) for k, v in results.items()}

with sidebar:
    # Sidebar parameters
    subheader("⚙️ Cable Parameters")
    core_r = slider("Core Radius (mm)", 0.1, 2.0, 0.5, 0.1) * 1e-3
    diel_r = slider("Dielectric Radius (mm)", 0.5, 5.0, 1.5, 0.1) * 1e-3
    shield_r = slider("Shield Radius (mm)", 1.0, 6.0, 1.8, 0.1) * 1e-3
    kapton_t = slider("Kapton Thickness (μm)", 10, 200, 50, 5) * 1e-6
    cable_len = slider("Cable Length (m)", 0.1, 10.0, 1.0, 0.1)

cable = CoaxialCable(core_r, diel_r, shield_r, kapton_t, cable_len)

# Scenario selection
tab1, tab2, tab3, tab4 = tabs([
    "📡 High Frequency (GHz)", 
    "🔥 High Temperature (K)", 
    "⚡ High Voltage (kV)", 
    "❄️ Cryogenic Quantum (mK)"
])

# ============================================================
# Tab 1: High Frequency
# ============================================================
with tab1:
    #markdown('<div class="scenario-box">', unsafe_allow_html=True)
    subheader("High Frequency RF Performance")
    write("Analyze Insertion Loss, Return Loss, Crosstalk, and Phase Velocity across microwave frequencies.")
    
    col1, col2 = columns(2)
    with col1:
        f_min = number_input("Min Frequency (GHz)", 0.1, 100.0, 0.1, 0.1)
        f_max = number_input("Max Frequency (GHz)", 1.0, 500.0, 50.0, 1.0)
    with col2:
        T_hf = slider("Temperature (K)", 4, 400, 300, 1)
        n_points = slider("Frequency Points", 50, 500, 200, 50)
    
    f_range = linspace(f_min*1e9, f_max*1e9, n_points)
    res_hf = analyze_hf(cable, f_range, T_hf)
    
    fig, axes = subplots(2, 2, figsize=(14, 10))
    
    axes[0,0].semilogx(res_hf['frequency']/1e9, res_hf['IL'], 'b-', linewidth=2)
    axes[0,0].set_xlabel('Frequency (GHz)')
    axes[0,0].set_ylabel('Insertion Loss (dB)')
    axes[0,0].set_title('Insertion Loss vs Frequency')
    axes[0,0].grid(True, alpha=0.3)
    
    axes[0,1].semilogx(res_hf['frequency']/1e9, res_hf['RL'], 'r-', linewidth=2)
    axes[0,1].set_xlabel('Frequency (GHz)')
    axes[0,1].set_ylabel('Return Loss (dB)')
    axes[0,1].set_title('Return Loss vs Frequency')
    axes[0,1].grid(True, alpha=0.3)
    
    axes[1,0].semilogx(res_hf['frequency']/1e9, res_hf['XT'], 'g-', linewidth=2)
    axes[1,0].axhline(y=-50, color='orange', linestyle='--', label='Typical Spec')
    axes[1,0].set_xlabel('Frequency (GHz)')
    axes[1,0].set_ylabel('Near-End Crosstalk (dB)')
    axes[1,0].set_title('Crosstalk vs Frequency')
    axes[1,0].legend()
    axes[1,0].grid(True, alpha=0.3)
    
    axes[1,1].semilogx(res_hf['frequency']/1e9, res_hf['v_p']/1e8, 'm-', linewidth=2)
    axes[1,1].axhline(y=c/1e8, color='gray', linestyle='--', label='Speed of Light')
    axes[1,1].set_xlabel('Frequency (GHz)')
    axes[1,1].set_ylabel('Phase Velocity (×10⁸ m/s)')
    axes[1,1].set_title('Phase Velocity vs Frequency')
    axes[1,1].legend()
    axes[1,1].grid(True, alpha=0.3)
    
    tight_layout()
    pyplot(fig)
    
    # Metrics
    col_m1, col_m2, col_m3, col_m4 = columns(4)
    with col_m1:
        metric("IL @ 10 GHz", f"{res_hf['IL'][argmin(abs(res_hf['frequency']-10e9))]:.2f} dB")
    with col_m2:
        metric("RL @ 10 GHz", f"{res_hf['RL'][argmin(abs(res_hf['frequency']-10e9))]:.1f} dB")
    with col_m3:
        metric("XT @ 10 GHz", f"{res_hf['XT'][argmin(abs(res_hf['frequency']-10e9))]:.1f} dB")
    with col_m4:
        metric("ε_eff", f"{res_hf['eps_eff'][0]:.3f}")
    
    markdown('</div>', unsafe_allow_html=True)

# ============================================================
# Tab 2: High Temperature
# ============================================================
with tab2:
    #markdown('<div class="scenario-box">', unsafe_allow_html=True)
    subheader("High Temperature Thermal Effects")
    write("Temperature-dependent RF degradation, dielectric strength, and power handling.")
    
    col1, col2 = columns(2)
    with col1:
        T_min = number_input("Min Temperature (K)", 77, 500, 77, 1)
        T_max = number_input("Max Temperature (K)", 100, 800, 500, 10)
    with col2:
        f_ht = slider("Analysis Frequency (GHz)", 0.1, 100.0, 10.0, 0.1) * 1e9
        n_t = slider("Temp Points", 50, 300, 100, 10)
    
    T_range = linspace(T_min, T_max, n_t)
    res_ht = analyze_ht(cable, T_range, f_ht)
    
    fig, axes = subplots(2, 2, figsize=(14, 10))
    
    axes[0,0].plot(res_ht['temperature'], res_ht['IL'], 'b-', linewidth=2)
    axes[0,0].set_xlabel('Temperature (K)')
    axes[0,0].set_ylabel('Insertion Loss (dB)')
    axes[0,0].set_title(f'Insertion Loss @ {f_ht/1e9:.1f} GHz')
    axes[0,0].grid(True, alpha=0.3)
    
    axes[0,1].plot(res_ht['temperature'], res_ht['RL'], 'r-', linewidth=2)
    axes[0,1].set_xlabel('Temperature (K)')
    axes[0,1].set_ylabel('Return Loss (dB)')
    axes[0,1].set_title('Return Loss vs Temperature')
    axes[0,1].grid(True, alpha=0.3)
    
    axes[1,0].plot(res_ht['temperature'], res_ht['DS'], 'g-', linewidth=2)
    axes[1,0].set_xlabel('Temperature (K)')
    axes[1,0].set_ylabel('Dielectric Strength (V/μm)')
    axes[1,0].set_title('Dielectric Strength vs Temperature')
    axes[1,0].grid(True, alpha=0.3)
    
    ax2 = axes[1,1]
    ax2.plot(res_ht['temperature'], res_ht['PH'], 'm-', linewidth=2)
    ax2.set_xlabel('Temperature (K)')
    ax2.set_ylabel('Max Power Handling (mW)')
    ax2.set_title('Power Handling vs Temperature')
    ax2.grid(True, alpha=0.3)
    
    tight_layout()
    pyplot(fig)
    
    # Warning for high temp
    max_il = max(res_ht['IL'])
    if max_il > 3:
        markdown(f'<div class="warning-box">⚠️ Warning: Insertion loss exceeds 3 dB at high temperatures. Consider thermal management.</div>', 
                    unsafe_allow_html=True)
    
    markdown('</div>', unsafe_allow_html=True)

# ============================================================
# Tab 3: High Voltage
# ============================================================
with tab3:
    #markdown('<div class="scenario-box">', unsafe_allow_html=True)
    subheader("High Voltage Breakdown Analysis")
    write("Electric field distribution, breakdown margin, leakage current, and partial discharge risk.")
    
    col1, col2 = columns(2)
    with col1:
        V_min = number_input("Min Voltage (V)", 100, 10000, 100, 100)
        V_max = number_input("Max Voltage (V)", 1000, 100000, 10000, 500)
    with col2:
        T_hv = slider("Temperature (K)", 4, 400, 300, 1, key='溫度')
        n_v = slider("Voltage Points", 50, 300, 100, 10, key='電壓')
    
    V_range = linspace(V_min, V_max, n_v)
    res_hv = analyze_hv(cable, V_range, T_hv)
    
    fig, axes = subplots(2, 2, figsize=(14, 10))
    
    axes[0,0].plot(res_hv['voltage']/1000, res_hv['E_max'], 'b-', linewidth=2)
    ds_line = cable.kapton.dielectric_strength(T_hv)
    axes[0,0].axhline(y=ds_line, color='r', linestyle='--', label=f'Breakdown: {ds_line:.0f} V/μm')
    axes[0,0].set_xlabel('Voltage (kV)')
    axes[0,0].set_ylabel('Max E-Field (MV/m)')
    axes[0,0].set_title('Electric Field vs Applied Voltage')
    axes[0,0].legend()
    axes[0,0].grid(True, alpha=0.3)
    
    axes[0,1].semilogy(res_hv['voltage']/1000, res_hv['margin'], 'g-', linewidth=2)
    axes[0,1].axhline(y=2, color='orange', linestyle='--', label='Safety Factor = 2')
    axes[0,1].set_xlabel('Voltage (kV)')
    axes[0,1].set_ylabel('Breakdown Margin')
    axes[0,1].set_title('Safety Margin vs Voltage')
    axes[0,1].legend()
    axes[0,1].grid(True, alpha=0.3)
    
    axes[1,0].semilogy(res_hv['voltage']/1000, abs(res_hv['I_leak']), 'r-', linewidth=2)
    axes[1,0].set_xlabel('Voltage (kV)')
    axes[1,0].set_ylabel('Leakage Current (A)')
    axes[1,0].set_title('Leakage Current vs Voltage')
    axes[1,0].grid(True, alpha=0.3)
    
    axes[1,1].plot(res_hv['voltage']/1000, res_hv['PD'], 'm-', linewidth=2)
    axes[1,1].fill_between(res_hv['voltage']/1000, res_hv['PD'], alpha=0.3, color='red')
    axes[1,1].set_xlabel('Voltage (kV)')
    axes[1,1].set_ylabel('PD Risk (0-1)')
    axes[1,1].set_title('Partial Discharge Risk')
    axes[1,1].grid(True, alpha=0.3)
    
    tight_layout()
    pyplot(fig)
    
    # Critical voltage alert
    critical_V = V_range[argmin(abs(res_hv['margin'] - 2))]
    markdown(f'<div class="warning-box">📊 Recommended max operating voltage (2× safety factor): <b>{critical_V/1000:.2f} kV</b></div>', 
                unsafe_allow_html=True)
    
    markdown('</div>', unsafe_allow_html=True)

# ============================================================
# Tab 4: Cryogenic Quantum
# ============================================================
with tab4:
    #markdown('<div class="scenario-box">', unsafe_allow_html=True)
    subheader("Cryogenic Quantum Computing Environment")
    write("Qubit coherence times, TLS losses, thermal loading, and heat capacity at millikelvin temperatures.")
    
    col1, col2 = columns(2)
    with col1:
        T_min_c = number_input("Min Temperature (mK)", 1, 300, 15, 1)
        T_max_c = number_input("Max Temperature (mK)", 10, 500, 300, 10)
    with col2:
        f_qubit = slider("Qubit Frequency (GHz)", 1.0, 20.0, 5.0, 0.5) * 1e9
        n_c = slider("Temp Points", 50, 300, 100, 10, key='暫時溫度')
    
    T_range_c = linspace(T_min_c/1000, T_max_c/1000, n_c)
    res_cryo = analyze_cryo(cable, T_range_c, f_qubit)
    
    fig, axes = subplots(2, 3, figsize=(16, 10))
    
    axes[0,0].semilogy(res_cryo['temperature']*1000, res_cryo['T1']*1e6, 'b-', linewidth=2)
    axes[0,0].set_xlabel('Temperature (mK)')
    axes[0,0].set_ylabel('T₁ (μs)')
    axes[0,0].set_title('Energy Relaxation Time T₁')
    axes[0,0].grid(True, alpha=0.3)
    
    axes[0,1].semilogy(res_cryo['temperature']*1000, res_cryo['T2']*1e6, 'r-', linewidth=2)
    axes[0,1].set_xlabel('Temperature (mK)')
    axes[0,1].set_ylabel('T₂ (μs)')
    axes[0,1].set_title('Dephasing Time T₂')
    axes[0,1].grid(True, alpha=0.3)
    
    axes[0,2].semilogy(res_cryo['temperature']*1000, res_cryo['n_th'], 'g-', linewidth=2)
    axes[0,2].set_xlabel('Temperature (mK)')
    axes[0,2].set_ylabel('⟨n_th⟩')
    axes[0,2].set_title('Thermal Photon Occupation')
    axes[0,2].grid(True, alpha=0.3)
    
    axes[1,0].loglog(res_cryo['temperature']*1000, res_cryo['td'], 'm-', linewidth=2)
    axes[1,0].set_xlabel('Temperature (mK)')
    axes[1,0].set_ylabel('tan δ')
    axes[1,0].set_title('Dielectric Loss Tangent')
    axes[1,0].grid(True, alpha=0.3)
    
    axes[1,1].loglog(res_cryo['temperature']*1000, res_cryo['Q_thermal']*1e6, 'c-', linewidth=2)
    axes[1,1].set_xlabel('Temperature (mK)')
    axes[1,1].set_ylabel('Thermal Load (μW/m)')
    axes[1,1].set_title('Heat Leak Through Kapton')
    axes[1,1].grid(True, alpha=0.3)
    
    axes[1,2].loglog(res_cryo['temperature']*1000, res_cryo['C']*1e6, 'orange', linewidth=2)
    axes[1,2].set_xlabel('Temperature (mK)')
    axes[1,2].set_ylabel('Heat Capacity (μJ/K)')
    axes[1,2].set_title('Kapton Heat Capacity')
    axes[1,2].grid(True, alpha=0.3)
    
    tight_layout()
    pyplot(fig)
    
    # Quantum metrics
    col_q1, col_q2, col_q3 = columns(3)
    idx_20mK = argmin(abs(res_cryo['temperature'] - 0.02))
    with col_q1:
        metric("T₁ @ 20mK", f"{res_cryo['T1'][idx_20mK]*1e6:.1f} μs")
    with col_q2:
        metric("T₂ @ 20mK", f"{res_cryo['T2'][idx_20mK]*1e6:.1f} μs")
    with col_q3:
        metric("tanδ @ 20mK", f"{res_cryo['td'][idx_20mK]:.2e}")
    
    # TLS warning
    if res_cryo['td'][idx_20mK] > 1e-5:
        markdown('<div class="danger-box">🚨 High TLS loss detected! Consider using sapphire substrate or amorphous silicon nitride for quantum applications.</div>', 
                    unsafe_allow_html=True)
    else:
        markdown('<div class="warning-box">✅ TLS loss within acceptable range for superconducting qubits.</div>', 
                    unsafe_allow_html=True)
    
    markdown('</div>', unsafe_allow_html=True)

# ============================================================
# Summary Table
# ============================================================
with sidebar:
    # ============================================================
    # UI Layout
    # ============================================================
#markdown("---")
    subheader("📋 Parameter Summary")
    summary_data = {
    "Parameter": ["Relative Permittivity (300K)", "Loss Tangent (300K, 1GHz)", 
                  "Dielectric Strength", "Thermal Conductivity (300K)",
                  "Thermal Conductivity (20mK)", "Specific Heat (300K)", "Density"],
    "Value": ["3.4", "2×10⁻³", "280 V/μm", "0.12 W/(m·K)", 
              f"{cable.kapton.thermal_conductivity(0.02):.2e} W/(m·K)", 
              "1090 J/(kg·K)", "1420 kg/m³"],
    "Relevance": ["Impedance matching", "Signal attenuation", "Voltage rating", 
                  "Heat dissipation", "Quantum thermalization", "Thermal mass", "Mechanical stability"]
}
    table(DataFrame(summary_data))
#markdown("---")
    caption("🔬 Kapton Analyzer v1.0 | Based on polyimide material models and coaxial transmission line theory")
    markdown('<div class="sub-header">🔬 Kapton RF Cable Extreme Environment Analyzer</div>', unsafe_allow_html=True)
    markdown('<div class="sub-header">Polyimide Dielectric Characterization for Aerospace & Quantum Applications</div>', unsafe_allow_html=True)

