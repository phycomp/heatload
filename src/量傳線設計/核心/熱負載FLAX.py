"""FLAX 熱負載計算（2023 改進版核心函數）。"""
from numpy import linspace, pi, trapezoid

def k_PFA(T, k_ref, exp):
    return k_ref * (T ** exp)

def k_NbTi(T, k_ref, exp):
    return k_ref * (T ** exp)

def compute_geometry(d_inner_mm, d_pfa_mm, t_outer_mm, pitch_mm, n_traces):
    d_inner = d_inner_mm * 1e-3
    d_pfa = d_pfa_mm * 1e-3
    t_outer = t_outer_mm * 1e-3
    pitch = pitch_mm * 1e-3

    r_inner = d_inner / 2
    A_inner = pi * r_inner**2

    r_pfa = d_pfa / 2
    A_pfa = pi * (r_pfa**2 - r_inner**2)

    w_outer_total = n_traces * pitch
    A_outer_total = w_outer_total * t_outer
    A_outer_per_trace = A_outer_total / n_traces

    A_total_per_trace = A_inner + A_pfa + A_outer_per_trace

    return {
        'd_inner': d_inner, 'd_pfa': d_pfa, 't_outer': t_outer, 'pitch': pitch,
        'A_inner': A_inner, 'A_pfa': A_pfa, 'A_outer_per_trace': A_outer_per_trace,
        'A_total_per_trace': A_total_per_trace, 'n_traces': n_traces,
        'f_inner': A_inner / A_total_per_trace,
        'f_pfa': A_pfa / A_total_per_trace,
        'f_outer': A_outer_per_trace / A_total_per_trace,
    }

def compute_heat_load(geo, T_cold, T_hot, L_cm, k_pfa_ref, pfa_exp, k_nbti_ref, nbti_exp):
    L = L_cm * 1e-2
    T = linspace(max(0.01, T_cold * 0.5), T_hot * 1.2, 5000)

    A_i = geo['A_inner']
    A_p = geo['A_pfa']
    A_o = geo['A_outer_per_trace']

    G_inner = k_NbTi(T, k_nbti_ref, nbti_exp) * A_i
    G_pfa = k_PFA(T, k_pfa_ref, pfa_exp) * A_p
    G_outer = k_NbTi(T, k_nbti_ref, nbti_exp) * A_o
    G_trace = G_inner + G_pfa + G_outer
    G_total = geo['n_traces'] * G_trace

    mask = (T >= T_cold) & (T <= T_hot)

    Q_single = trapezoid(G_trace[mask], T[mask]) / L
    Q_inner = trapezoid(G_inner[mask], T[mask]) / L
    Q_pfa = trapezoid(G_pfa[mask], T[mask]) / L
    Q_outer = trapezoid(G_outer[mask], T[mask]) / L
    Q_total = trapezoid(G_total[mask], T[mask]) / L

    k_eff = (G_trace / geo['A_total_per_trace']) * 1e6 * 1e-2

    return {
        'T': T, 'G_trace': G_trace, 'G_total': G_total,
        'G_inner': G_inner, 'G_pfa': G_pfa, 'G_outer': G_outer,
        'k_eff': k_eff, 'mask': mask,
        'Q_single_nW': Q_single * 1e9,
        'Q_inner_nW': Q_inner * 1e9,
        'Q_pfa_nW': Q_pfa * 1e9,
        'Q_outer_nW': Q_outer * 1e9,
        'Q_total_nW': Q_total * 1e9,
    }
