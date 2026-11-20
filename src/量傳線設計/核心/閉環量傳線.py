"""閉環量傳線（stripline 量子傳輸線）計算。"""
from numpy import array, log, pi, sqrt, tanh
import skrf as skrf

T_CRITICAL = 9.2
LAMBDA_0 = 85e-9
EPS_R_KAPTON = 3.4
TAN_D_KAPTON = 1e-3
FILM_THICKNESS = 200e-9
VACUUM_MU = 4 * pi * 1e-7
VACUUM_EPS = 8.854187817e-12

def get_kinetic_inductance_per_m(w, t, T):
    if T >= T_CRITICAL:
        return 0.0
    lam = LAMBDA_0 / sqrt(1.0 - (T / T_CRITICAL) ** 4)
    lk_square = VACUUM_MU * lam * (1.0 / tanh(t / lam))
    return lk_square / w

def evaluate_stripline(w_um, trench_factor, freq_hz, T, film_thickness=FILM_THICKNESS):
    w, h, t = w_um * 1e-6, 25.0 * 1e-6, film_thickness
    b = 2 * h
    eff_eps_r = EPS_R_KAPTON * (1 - trench_factor) + 1.0 * trench_factor
    eff_tan_d = TAN_D_KAPTON * (1 - trench_factor)
    if (w / (b - t)) >= 0.35:
        cf = (2 * log((b - t + 2 * t) / (b - t))) / pi
    else:
        cf = 0.0
    w_eff = w + cf * (b - t)
    c_m = 4 * VACUUM_EPS * eff_eps_r * (w_eff / (b - t))
    l_m = (VACUUM_MU * (b - t)) / (4 * w_eff)
    l_k_per_m = get_kinetic_inductance_per_m(w, t, T)
    l_total = l_m + l_k_per_m
    z0 = sqrt(l_total / c_m)
    beta = (2 * pi * freq_hz) * sqrt(l_total * c_m)
    alpha = (beta * eff_tan_d) / 2
    qi = beta / (2 * alpha) if alpha > 0 else float("inf")
    return z0, qi, alpha, beta

def simulate_network(w_um, trench_factor, T, L_BONDWIRE=0.8e-9):
    freq = skrf.Frequency(start=4.0, stop=10.0, npoints=201, unit='ghz')
    z0_list, gamma_list = [], []
    for f in freq.f:
        z0, _, alpha, beta = evaluate_stripline(w_um, trench_factor, f, T)
        z0_list.append(z0)
        gamma_list.append(complex(alpha, beta))
    media = skrf.media.DefinedGammaZ0(frequency=freq, z0=array(z0_list), gamma=array(gamma_list))
    stripline_core = media.line(d=10, unit='mm')
    ref_media = skrf.media.DefinedGammaZ0(frequency=freq, z0=50.0)
    bond_l = ref_media.inductor(L=L_BONDWIRE)
    bond_r = ref_media.inductor(L=L_BONDWIRE)
    return bond_l ** stripline_core ** bond_r
