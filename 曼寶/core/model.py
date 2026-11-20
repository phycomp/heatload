# core/model.py
import math

def _z0_microstrip(W, H, T, Er):
    """
    單端 microstrip 特性阻抗近似 (Hammerstad-Jensen 簡化)
    W, H, T 單位一致；Er 無因次
    """
    if W <= 0 or H <= 0:
        return float("nan")
    u = W / H
    # 有效介電常數
    a = 1 + (1/49)*math.log((u**4 + (u/52)**2)/(u**4 + 0.432)) + (1/18.7)*math.log(1 + (u/18.1)**3)
    b = 0.564 * ((Er - 0.9)/(Er + 3))**0.053
    eeff = (Er + 1)/2 + (Er - 1)/2 * (1 + 10/u)**(-a*b)
    # 阻抗
    F = 6 + (2*math.pi - 6)*math.exp(-(30.666/u)**0.7528)
    z01 = (376.73/(2*math.pi)) * math.log(F/u + math.sqrt(1 + (2/u)**2))
    z0 = z01 / math.sqrt(eeff)
    # 厚度修正 (簡化)
    if T > 0:
        dW = (T/math.pi) * math.log(1 + 4*math.e/((T/H)**2 * (1/math.tanh(math.sqrt(6.517*u)))**2))
        z0 = z0 * (1 - dW/W) if W > dW else z0
    return z0

def edge_coupled_surface_microstrip_zdd(
    H1: float, Er1: float, W1: float, W2: float, S1: float, T1: float
) -> float:
    """
    Edge-Coupled Surface Microstrip 差動阻抗初版。
    回傳 Zdiff (Ohm)。
    注意：此為近似，需以 Polar DOE 修正。
    """
    Wavg = (W1 + W2) / 2.0
    z0 = _z0_microstrip(Wavg, H1, T1, Er1)
    # 差動耦合修正 (經驗式)
    k = S1 / (S1 + 2 * Wavg) if (S1 + 2 * Wavg) > 0 else 0
    coupling = math.exp(-1.6 * k)
    z_diff = 2 * z0 * (1 - 0.35 * coupling)
    return z_diff
