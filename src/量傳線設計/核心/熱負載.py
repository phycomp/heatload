"""熱負載計算（簡化模型）。"""
from numpy import array, exp, linspace

h = 6.626e-34
k_B = 1.381e-23

def thermal_population(E, T):
    if T == 0:
        return 0.0
    return float(exp(-E / (k_B * T)))

def thermal_photon_number(f, T):
    if T == 0:
        return 0.0
    x = h * f / (k_B * T)
    if x > 50:
        return 0.0
    return 1.0 / (exp(x) - 1)

def 熱負載曲線(f01=5.5e9, alpha=-250e6, T_min=0.01, T_max=0.35, n=1000):
    E01 = h * f01
    E_alpha = h * abs(alpha)
    T_range = linspace(T_min, T_max, n)
    pop_1 = array([thermal_population(E01, T) for T in T_range])
    pop_2 = array([thermal_population(E01 + E_alpha, T) for T in T_range])
    n_th = array([thermal_photon_number(f01, T) for T in T_range])
    return {"T": T_range, "pop_1": pop_1, "pop_2": pop_2, "n_th": n_th}

def 回推溫區長度(熱導率=0.1, 截面積=1e-6, 溫差=50.0, 熱負載_W=1e-6):
    """傅立葉導熱：Q = k*A*dT/L -> L = k*A*dT/Q"""
    if 熱負載_W == 0:
        return float("inf")
    return 熱導率 * 截面積 * 溫差 / 熱負載_W
