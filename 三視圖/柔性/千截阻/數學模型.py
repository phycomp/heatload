from numpy import arctan, inf, log, pi, sqrt, tan, tanh
### 📂 檔案 2：math_models.py (核心數學模型)
# 此檔案包含所有底層物理計算：Djordjevic-Sarkar 色散模型、Hammerstad-Jensen 阻抗模型（含蝕刻因子修正）、Hammerstad 粗糙度損耗模型，以及帶有邊界約束的 Scipy 逆工程優化器。
"""
核心傳輸線數學模型
包含：色散效應、梯形截面阻抗、粗糙度損耗、逆工程優化。
"""
import numpy as np
from scipy.optimize import minimize

# 物理常數
MU_0 = 4 * pi * 1e-7
EPS_0 = 8.854187817e-12
C_0 = 299792458

# ==========================================
# 1. Djordjevic-Sarkar 色散模型 (Q11)
# ==========================================
def calc_djordjevic_sarkar(f, mat_params):
    """
    計算特定頻率下的複數介電常數，分離出 Dk(f) 和 Df(f)。
    """
    Dk0 = mat_params["Dk0"]
    Dk_inf = mat_params["Dk_inf"]
    fm = mat_params["fm"]
    m = mat_params["m"]
    
    # 頻率比
    f_ratio = f / fm
    
    # 實部 (Dk)
    Dk_f = Dk_inf + (Dk0 - Dk_inf) / (1 + f_ratio**(2*m))
    
    # 虛部 (計算損耗因子 Df)
    # 這裡使用簡化的因果關係推導 Df
    Df_f = (Dk0 - Dk_inf) * m * f_ratio**m * tan(pi * m / 2) / ((1 + f_ratio**(2*m)) * Dk_f)
    
    # 疊加基礎損耗 (假設基礎損耗隨頻率線性或微幅增加，此處簡化為常數疊加)
    Df_total = Df_f + mat_params["Df_base"] * (f / 10e9)**0.1 
    
    return Dk_f, Df_total

# ==========================================
# 2. Hammerstad-Jensen 阻抗模型 (含 Etch Factor) (Q1, Q12)
# ==========================================
def calc_hammerstad_microstrip(W, H, t, Dk, EF):
    """
    計算 Surface Microstrip 阻抗。
    W: 頂部線寬 (m)
    H: 介質厚度 (m)
    t: 銅厚 (m)
    Dk: 介電常數
    EF: 蝕刻因子 (Etch Factor)，通常 2~5。EF=無限大代表完美矩形。
    """
    # 梯形截面修正：底部線寬縮減
    # 側壁蝕刻量 = t / EF (簡化模型)
    W_bot = W - 2 * (t / EF)
    if W_bot < 0.1 * W: W_bot = 0.1 * W # 防止極端值
    
    # 等效線寬 (梯形截面的平均寬度)
    W_eq = (W + W_bot) / 2.0
    
    u = W_eq / H
    t_H = t / H
    
    # 有效介電常數 (Hammerstad 公式)
    eps_eff = (Dk + 1)/2 + (Dk - 1)/2 * (1 + 10/u)**(-0.555)
    
    # 特性阻抗 (分 w/h < 1 和 w/h > 1 兩種情況)
    if u <= 1:
        Z0 = (60 / sqrt(eps_eff)) * log(8/u + 0.25*u)
    else:
        Z0 = (60 / sqrt(eps_eff)) / (u + 1.393 + 0.667*log(u + 1.444))
        
    # 銅厚修正 (Hammerstad & Jensen 修正項)
    delta_u = (t_H / pi) * log(1 + 4 / (t_H * (1/tanh(sqrt(6.5*u)) + 1)))
    u_eff = u + delta_u
    
    # 重新計算修正後的阻抗
    if u_eff <= 1:
        Z0_corr = (60 / sqrt(eps_eff)) * log(8/u_eff + 0.25*u_eff)
    else:
        Z0_corr = (60 / sqrt(eps_eff)) / (u_eff + 1.393 + 0.667*log(u_eff + 1.444))
        
    return Z0_corr, eps_eff

# ==========================================
# 3. Hammerstad 粗糙度損耗模型 (Q4, Q10)
# ==========================================
def calc_roughness_factor(f, rho, Rz_um):
    """
    計算粗糙度修正因子 K_sr。
    輸入 Rz (um)，轉換為 Rq (um) 進行 Hammerstad 計算。
    """
    # 趨膚深度 delta
    delta = sqrt(rho / (pi * f * MU_0))
    
    # Rz 轉換為 Rq (均方根粗糙度)，經驗公式 Rq ≈ Rz / 4
    Rq = Rz_um * 1e-6 / 4.0 
    
    # Hammerstad 粗糙度修正因子
    # K_sr = 1 + (2/pi) * arctan( 1.4 * (Delta/delta)^2 )
    K_sr = 1 + (2 / pi) * arctan(1.4 * (Rq / delta)**2)
    
    return K_sr

# ==========================================
# 4. 總損耗計算 (IL)
# ==========================================
def calc_total_insertion_loss(f, W, H, t, Dk, Df, EF, Rz_um, rho):
    """
    計算總插入損耗 (dB/m)。
    IL_total = IL_conductor + IL_dielectric
    """
    Z0, eps_eff = calc_hammerstad_microstrip(W, H, t, Dk, EF)
    
    # 1. 導體損耗 (包含粗糙度)
    R_s = sqrt(pi * f * MU_0 * rho) # 表面電阻
    K_sr = calc_roughness_factor(f, rho, Rz_um)
    
    # 導體損耗公式 (簡化版)
    alpha_c = (R_s / (Z0 * H)) * K_sr * 1.0 # 1.0 為幾何因子 A 的簡化
    alpha_c_Np = alpha_c 
    
    # 2. 介質損耗
    alpha_d = (pi * f / C_0) * (Df * sqrt(eps_eff))
    
    # 轉換為 dB/m (1 Np = 8.686 dB)
    IL_total_dB_m = (alpha_c_Np + alpha_d) * 8.686
    
    return IL_total_dB_m, Z0

# ==========================================
# 5. 逆工程優化器 (Q6, Q13)
# ==========================================
def inverse_engineering(target_Z, H, t, Dk, EF, W_min, W_max):
    """
    給定目標阻抗，反推線寬 W。
    使用 Scipy minimize 並設定製造工藝邊界。
    """
    def objective(w_val):
        W = w_val[0]
        Z0, _ = calc_hammerstad_microstrip(W, H, t, Dk, EF)
        return (Z0 - target_Z)**2

    # 初始猜測值：線寬約等於介質厚度 (50 ohm 附近極穩定的啟發式起點)
    w0 = [H] 
    
    # 製造工藝邊界約束 (Q13)
    bounds = [(W_min, W_max)]
    
    result = minimize(objective, w0, method='L-BFGS-B', bounds=bounds)
    
    if result.success:
        return result.x[0], result.fun
    else:
        return None, inf
# math_models_v4.py (新增部分)
import numpy as np

# ==========================================
# 7. Offset Coplanar Waveguide 1B1A 模型
# ==========================================
def 共平面1b1a(H1_um, Er1, H2_um, Er2, W1_mil, W2_mil, D1_mil, T1_mil):
    """
    計算 Offset Coplanar Waveguide (1B1A) 的特性阻抗。
    
    參數:
    H1_um, H2_um: 上下基板厚度 (um)
    Er1, Er2: 上下基板介電常數
    W1_mil: 底部線寬 (mil) - 梯形截面下寬
    W2_mil: 頂部線寬 (mil) - 梯形截面上寬
    D1_mil: 接地帶總間距 (mil) - 兩個接地帶內緣之間的距離
    T1_mil: 銅厚 (mil)
    
    返回:
    Z0: 特性阻抗 (Ohm)
    eps_eff: 有效介電常數
    """
    # 1. 單位轉換 (mil -> meter)
    W1 = W1_mil * 25.4e-6
    W2 = W2_mil * 25.4e-6
    D1 = D1_mil * 25.4e-6
    T1 = T1_mil * 25.4e-6
    
    # 2. 等效線寬 (梯形截面平均)
    W_eq = (W1 + W2) / 2.0
    
    # 防止 D1 小於 W_eq 的錯誤輸入
    if D1 <= W_eq:
        D1 = W_eq * 1.1 
        
    # 3. 計算幾何因子 k (Modulus)
    # k = W_eq / D1 (因為 D1 = W_eq + 2*Gap)
    k = W_eq / D1
    if k >= 1.0: k = 0.999
    k_prime = sqrt(1 - k**2) # Complementary modulus
    
    # 4. 計算橢圓積分比 K(k')/K(k)
    # 使用高精度近似公式 (誤差 < 0.1%)
    if k <= 0.70710678: # k^2 <= 0.5
        # K(k')/K(k) = pi / ln(2 * (1+sqrt(k'))/(1-sqrt(k')))
        # 注意：這裡是 K(k')/K(k)，因為 Z0 公式需要這個比值
        # 修正：標準近似是 K(k)/K(k') = (1/pi)*ln(...)
        # 所以 K(k')/K(k) = pi / ln(...)
        K_ratio = pi / log(2 * (1 + sqrt(k_prime)) / (1 - sqrt(k_prime)))
    else:
        # K(k')/K(k) = (1/pi) * ln(2 * (1+sqrt(k))/(1-sqrt(k)))
        K_ratio = (1 / pi) * log(2 * (1 + sqrt(k)) / (1 - sqrt(k)))
        
    # 5. 計算有效介電常數 (Eff)
    # 對於 Offset 結構，電場分佈在上下基板。
    # 採用加權平均模型，權重與基板厚度成反比 (電場集中在薄層)
    # 簡化工程公式：當 H1, H2 >> D1 時，eff = (Er1+Er2)/2
    # 這裡使用厚度加權：
    weight1 = H2_um / (H1_um + H2_um) # 上基板越厚，下基板影響越大？不，電場線長度
    # 正確物理模型：電容並聯 C_total = C_up + C_down
    # C_up proportional to Er2, C_down proportional to Er1
    # 如果 H1=H2, eff = (Er1+Er2)/2
    eps_eff = (Er1 + Er2) / 2.0
    
    # 6. 計算空氣中阻抗 Z0_air
    Z0_air = 30 * pi * K_ratio
    
    # 7. 計算實際阻抗
    Z0 = Z0_air / sqrt(eps_eff)
    
    # 8. 銅厚修正 (簡化版)
    # 銅厚會增加等效線寬，降低阻抗
    # Delta_W 近似
    if T1 > 0:
        # 使用 CPW 的銅厚修正因子 (近似)
        # Z0_corr = Z0 * (1 - 0.5 * (T1 / (W_eq + 2*((D1-W_eq)/2)))) 
        # 更準確：將 W_eq 增加
        gap = (D1 - W_eq) / 2.0
        if gap > 0:
            delta_w = (T1 / pi) * log(1 + 4 / (T1 * 0.1 + 1e-9)) # 簡化對數項
            W_eff = W_eq + delta_w
            k_eff = W_eff / D1
            if k_eff >= 1.0: k_eff = 0.999
            k_prime_eff = sqrt(1 - k_eff**2)
            
            if k_eff <= 0.70710678:
                K_ratio_eff = pi / log(2 * (1 + sqrt(k_prime_eff)) / (1 - sqrt(k_prime_eff)))
            else:
                K_ratio_eff = (1 / pi) * log(2 * (1 + sqrt(k_eff)) / (1 - sqrt(k_eff)))
                
            Z0_air_eff = 30 * pi * K_ratio_eff
            Z0 = Z0_air_eff / sqrt(eps_eff)

    return Z0, eps_eff
