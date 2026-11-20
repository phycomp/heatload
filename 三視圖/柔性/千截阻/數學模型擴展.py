### 📂 檔案 1：`math_models_v2.py` (核心數學模型擴展) 此檔案在 Phase 1 的基礎上，新增了 **Symmetric Stripline (對稱帶狀線)**、**Differential Microstrip (差分微帶線)**，以及 **實測數據反推 (逆向工程場景 2)** 的優化器。

# math_models_v2.py
"""
Phase 2 核心數學模型擴展
包含：對稱帶狀線、差分微帶線、實測逆向工程優化器。
"""
import numpy as np
from scipy.optimize import minimize

# 繼承 Phase 1 的常數與基礎函數 (實際專案中應從 math_models.py import)
MU_0 = 4 * np.pi * 1e-7
EPS_0 = 8.854187817e-12
C_0 = 299792458

# ==========================================
# 1. Symmetric Stripline (對稱帶狀線) - IPC-2141 標準
# ==========================================
def calc_symmetric_stripline(W, b, t, Dk, EF):
    """
    計算 Symmetric Stripline 阻抗。
    W: 線寬 (m)
    b: 兩個參考平面之間的總介質厚度 (m)
    t: 銅厚 (m)
    Dk: 介電常數 (帶狀線完全被介質包圍，Dk_eff = Dk)
    EF: 蝕刻因子
    """
    # 梯形截面修正 (上下皆蝕刻)
    W_bot = W - 2 * (t / EF)
    if W_bot < 0.1 * W: W_bot = 0.1 * W
    W_eq = (W + W_bot) / 2.0
    
    # 歸一化參數
    w_b = W_eq / b
    t_b = t / b
    
    # IPC-2141 帶狀線公式 (分界點 w/b = 0.35)
    if w_b < 0.35:
        Z0 = (60 / np.sqrt(Dk)) * np.log(4 * b / (0.67 * np.pi * (0.8 * W_eq + t)))
    else:
        # 修正項 C
        C = (2.0 / np.pi) * np.log(2.0) + (1.0 / np.pi) * np.log((1.0 + np.sqrt(1.0 + (1.0 / 0.092 * (t_b)**2))) / (1.0 + (1.0 / 0.092 * (t_b)**2)))
        # 這裡使用更穩定的 Wadell 近似公式替代複雜的 IPC C 項計算
        Z0 = (94.13 / np.sqrt(Dk)) / (w_b / (1 - 0.44 * t_b) + 0.118 + 0.067 * np.log(w_b / (1 - 0.44 * t_b)))
        
    return Z0, Dk # 帶狀線的 eps_eff 等於 Dk

# ==========================================
# 2. Differential Microstrip (差分微帶線)
# ==========================================
def calc_diff_microstrip(W, S, H, t, Dk, EF):
    """
    計算 Differential Microstrip 差分阻抗 Zd。
    W: 單根線寬 (m)
    S: 線距 (m) (邊緣到邊緣)
    H: 介質厚度 (m)
    """
    # 先計算單端微帶線阻抗與有效介電常數 (复用 Phase 1 邏輯，此處簡化寫法)
    # 實際應用中應 import calc_hammerstad_microstrip
    W_bot = W - 2 * (t / EF)
    if W_bot < 0.1 * W: W_bot = 0.1 * W
    W_eq = (W + W_bot) / 2.0
    u = W_eq / H
    eps_eff = (Dk + 1)/2 + (Dk - 1)/2 * (1 + 10/u)**(-0.555)
    
    if u <= 1:
        Z0_se = (60 / np.sqrt(eps_eff)) * np.log(8/u + 0.25*u)
    else:
        Z0_se = (60 / np.sqrt(eps_eff)) / (u + 1.393 + 0.667*np.log(u + 1.444))

    # 差分阻抗近似公式 (考慮耦合係數)
    # 使用 Polar SI9000 常用的經驗修正公式
    s_h = S / H
    coupling_factor = np.exp(-0.8 * s_h) # 耦合隨間距指數衰減
    
    # 奇模阻抗 Zodd 近似
    Z_odd = Z0_se * (1 - 0.48 * np.exp(-0.96 * s_h)) 
    Z_diff = 2 * Z_odd
    
    return Z_diff, Z0_se, eps_eff

# ==========================================
# 3. 逆向工程場景 2：實測數據反推 (Q6)
# ==========================================
def inverse_engineering_meas_Dk(target_Z_meas, W, H, t, EF):
    """
    場景 2A: 給定實測阻抗與物理尺寸，反推實際的有效介電常數 (Dk_eff)。
    這在 TDR 量測後，用來驗證板材 Dk 是否符合規格。
    """
    def objective(dk_val):
        # 簡化：假設 Dk_eff 隨 Dk 線性變化，此處直接用 Dk 作為變數
        Dk = dk_val[0]
        u = W / H
        eps_eff = (Dk + 1)/2 + (Dk - 1)/2 * (1 + 10/u)**(-0.555)
        if u <= 1:
            Z0 = (60 / np.sqrt(eps_eff)) * np.log(8/u + 0.25*u)
        else:
            Z0 = (60 / np.sqrt(eps_eff)) / (u + 1.393 + 0.667*np.log(u + 1.444))
        return (Z0 - target_Z_meas)**2

    # 初始猜測：FR4 典型值 4.2
    d0 = [4.2]
    bounds = [(2.0, 10.0)] # 物理邊界
    
    result = minimize(objective, d0, method='L-BFGS-B', bounds=bounds)
    return result.x[0] if result.success else None

def inverse_engineering_meas_W(target_Z_meas, H, t, Dk, EF, W_min, W_max):
    """
    場景 2B: 給定實測阻抗，反推「實際蝕刻後」的線寬。
    這可以用來評估 PCB 廠的蝕刻補償是否準確。
    """
    def objective(w_val):
        W = w_val[0]
        W_bot = W - 2 * (t / EF)
        if W_bot < 0.1 * W: W_bot = 0.1 * W
        W_eq = (W + W_bot) / 2.0
        u = W_eq / H
        eps_eff = (Dk + 1)/2 + (Dk - 1)/2 * (1 + 10/u)**(-0.555)
        if u <= 1:
            Z0 = (60 / np.sqrt(eps_eff)) * np.log(8/u + 0.25*u)
        else:
            Z0 = (60 / np.sqrt(eps_eff)) / (u + 1.393 + 0.667*np.log(u + 1.444))
        return (Z0 - target_Z_meas)**2

    w0 = [H]
    bounds = [(W_min, W_max)]
    result = minimize(objective, w0, method='L-BFGS-B', bounds=bounds)
    return result.x[0] if result.success else None

# math_models_v3.py (增量部分)
# ==========================================
# 6. Return Loss (RL) 計算
# ==========================================
def calc_return_loss(Z_calc, Z_target=50.0):
    """
    計算相對於目標系統阻抗的 Return Loss (dB)。
    Z_calc: 計算出的傳輸線阻抗
    Z_target: 系統目標阻抗 (通常為 50 或 100 ohm)
    """
    # 反射係數 Gamma
    gamma = abs((Z_calc - Z_target) / (Z_calc + Z_target))
    
    # 防止 log(0) 錯誤
    if gamma == 0:
        return 100.0 # 理想匹配，RL 趨近無限大，此處設為 100dB
        
    # RL = -20 * log10(|Gamma|)
    RL_dB = -20 * np.log10(gamma)
    return RL_dB
