import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.constants import h, k, epsilon_0, mu_0, c, pi, hbar
import pandas as pd
from dataclasses import dataclass

st.set_page_config(page_title="Kapton RF Cable Analyzer", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; color: #1f77b4; text-align: center; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.2rem; color: #666; text-align: center; margin-bottom: 2rem; }
    .scenario-box { background: #f0f2f6; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #1f77b4; }
    .warning-box { background: #fff3cd; padding: 1rem; border-radius: 5px; border-left: 5px solid #ffc107; }
    .danger-box { background: #f8d7da; padding: 1rem; border-radius: 5px; border-left: 5px solid #dc3545; }
    .success-box { background: #d4edda; padding: 1rem; border-radius: 5px; border-left: 5px solid #28a745; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Kapton Properties
# ============================================================
@dataclass
class KaptonProperties:
    epsilon_r_300K: float = 3.4
    tan_delta_300K: float = 0.002
    thermal_conductivity_300K: float = 0.12
    specific_heat_300K: float = 1090
    density: float = 1420

    def epsilon_r(self, T: float) -> float:
        if T < 1: return 2.8
        elif T < 77: return 2.9 + 0.5 * (T / 300)**0.5
        elif T < 400: return 3.4 - 0.3 * ((T - 300) / 100)
        else: return 3.1

    def tan_delta(self, T: float, f: float) -> float:
        f_GHz = f / 1e9
        if T < 0.1: return 5e-6 * (f_GHz)**0.3
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
        if T < 1: return 0.004 * T**1.5
        elif T < 10: return 0.004 + 0.001 * T**2
        elif T < 100: return 0.008 + 0.0001 * T**1.5
        else: return 0.12 * (T / 300)**0.8

    def specific_heat(self, T: float) -> float:
        theta_D = 500
        if T < theta_D / 10: return 0.5 * (T / theta_D)**3 * self.specific_heat_300K
        else: return self.specific_heat_300K * (T / 300)**0.9

    def dielectric_strength(self, T: float) -> float:
        base = 280
        if T < 77: return base * (1 + 0.5 * (77 - max(T, 4)) / 73)
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
        if T < 20: rrr = 100
        else: rrr = 1
        rho_0 = 1.7e-8 / rrr
        rho = rho_0 * (1 + 0.004 * (T - 4)) if T < 20 else 1.7e-8 * (1 + 0.004 * (T - 293))
        return np.sqrt(pi * f * mu_0 * rho)

    def propagation_constant(self, f, T):
        eps_r = self.kapton.epsilon_r(T)
        td = self.kapton.tan_delta(T, f)
        omega = 2 * pi * f
        alpha_d = (omega / 2) * np.sqrt(mu_0 * epsilon_0 * eps_r) * td
        Rs = self.surface_resistance(f, T)
        alpha_c = (Rs / (2 * pi)) * (1/self.a + 1/self.b) / np.sqrt(mu_0 / (epsilon_0 * eps_r))
        alpha = alpha_d + alpha_c
        beta = omega * np.sqrt(mu_0 * epsilon_0 * eps_r)
        return alpha + 1j * beta

# ============================================================
# Analysis Functions
# ============================================================
def analyze_hf(cable, f_range, T=300):
    results = {'frequency': f_range, 'IL': [], 'RL': [], 'XT': [], 'v_p': [], 'eps_eff': []}
    for f in f_range:
        gamma = cable.propagation_constant(f, T)
        alpha, beta = gamma.real, gamma.imag
        IL = 20 * np.log10(np.exp(alpha * cable.L))
        Z0 = (1/(2*pi)) * np.sqrt(mu_0/(epsilon_0*cable.kapton.epsilon_r(T))) * np.log(cable.b/cable.a)
        gamma_ref = (Z0 - 50) / (Z0 + 50)
        RL = -20 * np.log10(max(abs(gamma_ref), 1e-10))
        k_coupling = 0.01 * (cable.kapton.epsilon_r(T)/3.4) * (f/1e9)**0.5
        XT = 20 * np.log10(k_coupling * cable.L / (3*cable.c))
        v_p = 2*pi*f / beta
        eps_eff = (c/v_p)**2
        results['IL'].append(IL); results['RL'].append(RL); results['XT'].append(XT)
        results['v_p'].append(v_p); results['eps_eff'].append(eps_eff)
    return {k: np.array(v) for k, v in results.items()}

def analyze_ht(cable, T_range, f=10e9):
    results = {'temperature': T_range, 'IL': [], 'RL': [], 'XT': [], 'DS': [], 'PH': []}
    alpha_th = 20e-6
    for T in T_range:
        gamma = cable.propagation_constant(f, T)
        IL = 20 * np.log10(np.exp(gamma.real * cable.L))
        delta_T = T - 300
        b_new = cable.b * (1 + alpha_th * delta_T)
        a_new = cable.a * (1 + 17e-6 * delta_T)
        Z0_T = 50 * np.log(b_new/a_new) / np.log(cable.b/cable.a)
        gamma_ref = (Z0_T - 50) / (Z0_T + 50)
        RL = -20 * np.log10(max(abs(gamma_ref), 1e-10))
        k_coupling = 0.01 * (cable.kapton.epsilon_r(T)/3.4)
        XT = 20 * np.log10(k_coupling * cable.L / (3*cable.c))
        DS = cable.kapton.dielectric_strength(T)
        k_th = cable.kapton.thermal_conductivity(T)
        PH = k_th * 50 / (gamma.real * cable.L) * 1e-3
        results['IL'].append(IL); results['RL'].append(RL); results['XT'].append(XT)
        results['DS'].append(DS); results['PH'].append(PH)
    return {k: np.array(v) for k, v in results.items()}

def analyze_hv(cable, V_range, T=300, f=1e6):
    results = {'voltage': V_range, 'E_max': [], 'margin': [], 'I_leak': [], 'PD': [], 'R_ins': []}
    ds = cable.kapton.dielectric_strength(T) * 1e6
    for V in V_range:
        E_max = V / (cable.a * np.log(cable.b/cable.a))
        margin = ds / E_max
        sigma = cable.kapton.conductivity(T, f)
        R_ins = np.log(cable.b/cable.a) / (2 * pi * cable.L * sigma)
        I_leak = V / R_ins
        pd_risk = max(0, (E_max - 0.5*ds) / (0.5*ds)) if E_max > 0.5*ds else 0
        results['E_max'].append(E_max/1e6); results['margin'].append(margin)
        results['I_leak'].append(I_leak); results['PD'].append(pd_risk)
        results['R_ins'].append(R_ins/1e9)
    return {k: np.array(v) for k, v in results.items()}

def analyze_cryo(cable, T_range, f_qubit=5e9):
    results = {'temperature': T_range, 'T1': [], 'T2': [], 'n_th': [], 'td': [], 
               'Q_thermal': [], 'C': [], 'tau': [], 'TLS': []}
    for T in T_range:
        x = h * f_qubit / (k * T)
        n_th = np.exp(-x) if x > 50 else 1.0/(np.exp(x)-1.0) if np.exp(x) > 1.001 else 1.0/x
        td = cable.kapton.tan_delta(T, f_qubit)
        Q = 1.0/max(td, 1e-12)
        T1 = Q / (2 * pi * f_qubit)
        T_phi = 1e-3/max(T, 1e-6)
        T2 = 1.0/(1.0/(2*T1) + 1.0/T_phi)
        P_tls = 1e45 * max(T/0.01, 1e-6)**0.3
        k_th = cable.kapton.thermal_conductivity(T)
        delta_T = max(1.0 - T, 0.01) if T < 1 else 0.1
        area = pi * ((cable.a + cable.t_kapton)**2 - cable.a**2)
        Q_th = k_th * area * delta_T / cable.L
        C_v = cable.kapton.specific_heat(T)
        mass = cable.kapton.density * area * cable.L
        C_total = C_v * mass
        tau = C_total/max(k_th * area / cable.L, 1e-20) if k_th > 0 else 1e6
        results['T1'].append(T1); results['T2'].append(T2); results['n_th'].append(n_th)
        results['td'].append(td); results['Q_thermal'].append(Q_th); results['C'].append(C_total)
        results['tau'].append(tau); results['TLS'].append(P_tls)
    return {k: np.array(v) for k, v in results.items()}

# ============================================================
# UI
# ============================================================
st.markdown('<div class="main-header">🔬 Kapton RF Cable Extreme Environment Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Polyimide Dielectric Characterization for Aerospace & Quantum Applications</div>', unsafe_allow_html=True)

st.sidebar.header("⚙️ Cable Parameters")
core_r = st.sidebar.slider("Core Radius (mm)", 0.1, 2.0, 0.5, 0.1) * 1e-3
diel_r = st.sidebar.slider("Dielectric Radius (mm)", 0.5, 5.0, 1.5, 0.1) * 1e-3
shield_r = st.sidebar.slider("Shield Radius (mm)", 1.0, 6.0, 1.8, 0.1) * 1e-3
kapton_t = st.sidebar.slider("Kapton Thickness (μm)", 10, 200, 50, 5) * 1e-6
cable_len = st.sidebar.slider("Cable Length (m)", 0.1, 10.0, 1.0, 0.1)

cable = CoaxialCable(core_r, diel_r, shield_r, kapton_t, cable_len)

tab1, tab2, tab3, tab4 = st.tabs(["📡 High Frequency", "🔥 High Temperature", "⚡ High Voltage", "❄️ Cryogenic Quantum"])

# ===== Tab 1: High Frequency =====
with tab1:
    st.markdown('<div class="scenario-box">', unsafe_allow_html=True)
    st.header("High Frequency RF Performance")
    col1, col2 = st.columns(2)
    with col1:
        f_min = st.number_input("Min Freq (GHz)", 0.1, 100.0, 0.1, 0.1)
        f_max = st.number_input("Max Freq (GHz)", 1.0, 500.0, 50.0, 1.0)
    with col2:
        T_hf = st.slider("Temp (K)", 4, 400, 300, 1)
        n_points = st.slider("Points", 50, 500, 200, 50)

    f_range = np.linspace(f_min*1e9, f_max*1e9, n_points)
    res_hf = analyze_hf(cable, f_range, T_hf)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes[0,0].semilogx(res_hf['frequency']/1e9, res_hf['IL'], 'b-', lw=2)
    axes[0,0].set_xlabel('Frequency (GHz)'); axes[0,0].set_ylabel('IL (dB)'); axes[0,0].set_title('Insertion Loss'); axes[0,0].grid(True, alpha=0.3)
    axes[0,1].semilogx(res_hf['frequency']/1e9, res_hf['RL'], 'r-', lw=2)
    axes[0,1].set_xlabel('Frequency (GHz)'); axes[0,1].set_ylabel('RL (dB)'); axes[0,1].set_title('Return Loss'); axes[0,1].grid(True, alpha=0.3)
    axes[1,0].semilogx(res_hf['frequency']/1e9, res_hf['XT'], 'g-', lw=2)
    axes[1,0].axhline(y=-50, color='orange', ls='--', label='Spec'); axes[1,0].set_xlabel('Frequency (GHz)'); axes[1,0].set_ylabel('XT (dB)'); axes[1,0].set_title('Crosstalk'); axes[1,0].legend(); axes[1,0].grid(True, alpha=0.3)
    axes[1,1].semilogx(res_hf['frequency']/1e9, res_hf['v_p']/1e8, 'm-', lw=2)
    axes[1,1].axhline(y=c/1e8, color='gray', ls='--', label='c'); axes[1,1].set_xlabel('Frequency (GHz)'); axes[1,1].set_ylabel('v_p (×10⁸ m/s)'); axes[1,1].set_title('Phase Velocity'); axes[1,1].legend(); axes[1,1].grid(True, alpha=0.3)
    plt.tight_layout(); st.pyplot(fig)

    idx_10 = np.argmin(np.abs(res_hf['frequency']-10e9))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("IL@10GHz", f"{res_hf['IL'][idx_10]:.2f} dB")
    c2.metric("RL@10GHz", f"{res_hf['RL'][idx_10]:.1f} dB")
    c3.metric("XT@10GHz", f"{res_hf['XT'][idx_10]:.1f} dB")
    c4.metric("ε_eff", f"{res_hf['eps_eff'][0]:.3f}")
    st.markdown('</div>', unsafe_allow_html=True)

# ===== Tab 2: High Temperature =====
with tab2:
    st.markdown('<div class="scenario-box">', unsafe_allow_html=True)
    st.header("High Temperature Effects")
    col1, col2 = st.columns(2)
    with col1:
        T_min = st.number_input("Min T (K)", 77, 500, 77, 1)
        T_max = st.number_input("Max T (K)", 100, 800, 500, 10)
    with col2:
        f_ht = st.slider("Freq (GHz)", 0.1, 100.0, 10.0, 0.1) * 1e9
        n_t = st.slider("T Points", 50, 300, 100, 10)

    T_range = np.linspace(T_min, T_max, n_t)
    res_ht = analyze_ht(cable, T_range, f_ht)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes[0,0].plot(res_ht['temperature'], res_ht['IL'], 'b-', lw=2); axes[0,0].set_xlabel('T (K)'); axes[0,0].set_ylabel('IL (dB)'); axes[0,0].set_title('Insertion Loss'); axes[0,0].grid(True, alpha=0.3)
    axes[0,1].plot(res_ht['temperature'], res_ht['RL'], 'r-', lw=2); axes[0,1].set_xlabel('T (K)'); axes[0,1].set_ylabel('RL (dB)'); axes[0,1].set_title('Return Loss'); axes[0,1].grid(True, alpha=0.3)
    axes[1,0].plot(res_ht['temperature'], res_ht['DS'], 'g-', lw=2); axes[1,0].set_xlabel('T (K)'); axes[1,0].set_ylabel('DS (V/μm)'); axes[1,0].set_title('Dielectric Strength'); axes[1,0].grid(True, alpha=0.3)
    axes[1,1].semilogy(res_ht['temperature'], res_ht['PH'], 'm-', lw=2); axes[1,1].set_xlabel('T (K)'); axes[1,1].set_ylabel('PH (mW)'); axes[1,1].set_title('Power Handling'); axes[1,1].grid(True, alpha=0.3)
    plt.tight_layout(); st.pyplot(fig)

    if np.max(res_ht['IL']) > 3:
        st.markdown('<div class="warning-box">⚠️ IL exceeds 3 dB at high T. Consider thermal management.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ===== Tab 3: High Voltage =====
with tab3:
    st.markdown('<div class="scenario-box">', unsafe_allow_html=True)
    st.header("High Voltage Breakdown")
    col1, col2 = st.columns(2)
    with col1:
        V_min = st.number_input("Min V (V)", 100, 10000, 100, 100)
        V_max = st.number_input("Max V (V)", 1000, 100000, 10000, 500)
    with col2:
        T_hv = st.slider("T (K)", 4, 400, 300, 1)
        n_v = st.slider("V Points", 50, 300, 100, 10)

    V_range = np.linspace(V_min, V_max, n_v)
    res_hv = analyze_hv(cable, V_range, T_hv)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    ds_line = cable.kapton.dielectric_strength(T_hv)
    axes[0,0].plot(res_hv['voltage']/1000, res_hv['E_max'], 'b-', lw=2); axes[0,0].axhline(y=ds_line, color='r', ls='--', label=f'BD: {ds_line:.0f} V/μm'); axes[0,0].set_xlabel('V (kV)'); axes[0,0].set_ylabel('E (MV/m)'); axes[0,0].set_title('E-Field'); axes[0,0].legend(); axes[0,0].grid(True, alpha=0.3)
    axes[0,1].semilogy(res_hv['voltage']/1000, res_hv['margin'], 'g-', lw=2); axes[0,1].axhline(y=2, color='orange', ls='--', label='SF=2'); axes[0,1].set_xlabel('V (kV)'); axes[0,1].set_ylabel('Margin'); axes[0,1].set_title('Safety Margin'); axes[0,1].legend(); axes[0,1].grid(True, alpha=0.3)
    axes[1,0].semilogy(res_hv['voltage']/1000, np.abs(res_hv['I_leak']), 'r-', lw=2); axes[1,0].set_xlabel('V (kV)'); axes[1,0].set_ylabel('I_leak (A)'); axes[1,0].set_title('Leakage Current'); axes[1,0].grid(True, alpha=0.3)
    axes[1,1].plot(res_hv['voltage']/1000, res_hv['PD'], 'm-', lw=2); axes[1,1].fill_between(res_hv['voltage']/1000, res_hv['PD'], alpha=0.3, color='red'); axes[1,1].set_xlabel('V (kV)'); axes[1,1].set_ylabel('PD Risk'); axes[1,1].set_title('Partial Discharge'); axes[1,1].grid(True, alpha=0.3)
    plt.tight_layout(); st.pyplot(fig)

    critical_V = V_range[np.argmin(np.abs(res_hv['margin'] - 2))]
    st.markdown(f'<div class="warning-box">📊 Max operating voltage (2× SF): <b>{critical_V/1000:.2f} kV</b></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ===== Tab 4: Cryogenic Quantum =====
with tab4:
    st.markdown('<div class="scenario-box">', unsafe_allow_html=True)
    st.header("Cryogenic Quantum Computing")
    col1, col2 = st.columns(2)
    with col1:
        T_min_c = st.number_input("Min T (mK)", 1, 300, 15, 1)
        T_max_c = st.number_input("Max T (mK)", 10, 500, 300, 10)
    with col2:
        f_qubit = st.slider("Qubit Freq (GHz)", 1.0, 20.0, 5.0, 0.5) * 1e9
        n_c = st.slider("Cryo Points", 50, 300, 100, 10)

    T_range_c = np.linspace(T_min_c/1000, T_max_c/1000, n_c)
    res_cryo = analyze_cryo(cable, T_range_c, f_qubit)

    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    axes[0,0].semilogy(T_range_c*1000, res_cryo['T1']*1e6, 'b-', lw=2); axes[0,0].set_xlabel('T (mK)'); axes[0,0].set_ylabel('T₁ (μs)'); axes[0,0].set_title('T₁ Relaxation'); axes[0,0].grid(True, alpha=0.3)
    axes[0,1].semilogy(T_range_c*1000, res_cryo['T2']*1e6, 'r-', lw=2); axes[0,1].set_xlabel('T (mK)'); axes[0,1].set_ylabel('T₂ (μs)'); axes[0,1].set_title('T₂ Dephasing'); axes[0,1].grid(True, alpha=0.3)
    axes[0,2].semilogy(T_range_c*1000, res_cryo['n_th'], 'g-', lw=2); axes[0,2].set_xlabel('T (mK)'); axes[0,2].set_ylabel('⟨n_th⟩'); axes[0,2].set_title('Thermal Photons'); axes[0,2].grid(True, alpha=0.3)
    axes[1,0].semilogy(T_range_c*1000, res_cryo['td'], 'm-', lw=2); axes[1,0].set_xlabel('T (mK)'); axes[1,0].set_ylabel('tan δ'); axes[1,0].set_title('Loss Tangent (TLS)'); axes[1,0].grid(True, alpha=0.3)
    axes[1,1].loglog(T_range_c*1000, res_cryo['Q_thermal']*1e6, 'c-', lw=2); axes[1,1].set_xlabel('T (mK)'); axes[1,1].set_ylabel('Load (μW/m)'); axes[1,1].set_title('Heat Leak'); axes[1,1].grid(True, alpha=0.3)
    axes[1,2].loglog(T_range_c*1000, res_cryo['C']*1e6, 'orange', lw=2); axes[1,2].set_xlabel('T (mK)'); axes[1,2].set_ylabel('C (μJ/K)'); axes[1,2].set_title('Heat Capacity'); axes[1,2].grid(True, alpha=0.3)
    plt.tight_layout(); st.pyplot(fig)

    idx_20 = np.argmin(np.abs(T_range_c - 0.02))
    c1, c2, c3 = st.columns(3)
    c1.metric("T₁ @ 20mK", f"{res_cryo['T1'][idx_20]*1e6:.1f} μs")
    c2.metric("T₂ @ 20mK", f"{res_cryo['T2'][idx_20]*1e6:.1f} μs")
    c3.metric("tanδ @ 20mK", f"{res_cryo['td'][idx_20]:.2e}")

    if res_cryo['td'][idx_20] > 1e-5:
        st.markdown('<div class="danger-box">🚨 High TLS loss! Consider sapphire or SiN for quantum apps.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="success-box">✅ TLS loss acceptable for superconducting qubits.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Summary Table
st.markdown("---")
st.header("📋 Kapton Material Summary")
summary = {
    "Parameter": ["εᵣ (300K)", "tanδ (300K, 1GHz)", "Dielectric Strength", "k_th (300K)", "k_th (20mK)", "C_p (300K)", "Density"],
    "Value": ["3.4", "2×10⁻³", "280 V/μm", "0.12 W/(m·K)", f"{cable.kapton.thermal_conductivity(0.02):.2e} W/(m·K)", "1090 J/(kg·K)", "1420 kg/m³"],
    "Relevance": ["Impedance", "Attenuation", "Voltage Rating", "Heat Dissipation", "Quantum Thermalization", "Thermal Mass", "Mechanical"]
}
st.table(pd.DataFrame(summary))
st.caption("🔬 Kapton Analyzer v1.0 | Polyimide RF/Quantum Characterization Tool")
