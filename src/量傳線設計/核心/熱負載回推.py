"""熱負載回推模型比較。"""
from numpy import array, linspace

def 回推模型比較(L0=20.0, T_cold=10.0, T_hot=350.0, T_crit=57.6):
    """回傳不同回推策略的長度 (cm)。"""
    # cri/oFlex3 原始 20 cm
    # Safe zone 2.8 cm (經驗)
    L_new = L0 * 5 / 47.6
    L_anchor = 10.0
    L_back = L0 * (T_hot - T_crit) / (T_hot - T_cold)
    models = ['cri/oFlex3 (Original)', 'Safe zone (2.8 cm)', f'Extended ({L_new:.1f} cm)', 'With thermal anchor (10 cm)', f'Back-calc ({L_back:.1f} cm)']
    lengths = [L0, 2.8, L_new, L_anchor, L_back]
    return models, lengths

def 溫度分布(L, T_cold, T_hot):
    x = linspace(0, L, 100)
    T = T_cold + (T_hot - T_cold) * (x / L)
    return x, T
