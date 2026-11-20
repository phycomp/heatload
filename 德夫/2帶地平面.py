from streamlit import pyplot, empty
import numpy as np
from scipy.special import ellipk

def 帶地平面(w, s, g, h, er):
    """
    計算帶地平面共面波導 (GCPW) 的奇偶模阻抗
    w: 訊號線寬
    s: 訊號線與側面接地的間隙 (Gap)
    g: 兩條訊號線中間的接地線寬度 (Middle Ground)
    h: 介電層厚度
    er: 介電常數
    """
    
    def get_k_and_k_prime(w_eff, s_eff, h_eff):
        # 建立共形映射的模數 k
        k = w_eff / (w_eff + 2 * s_eff)
        # 考慮底部接地影響的修正項 (簡化模型)
        k_h = np.tanh((np.pi * w_eff) / (4 * h_eff)) / np.tanh((np.pi * (w_eff + 2 * s_eff)) / (4 * h_eff))
        
        # 計算橢圓積分比值 K(k)/K(k')
        def k_ratio(k_val):
            kp = np.sqrt(1 - k_val**2)
            return ellipk(k_val) / ellipk(kp)
            
        return k_ratio(k), k_ratio(k_h)

    # 1. 計算單線特性阻抗 (用於參考)
    ratio_air, ratio_d = get_k_and_k_prime(w, s, h)
    eeff = (1 + er * ratio_d / ratio_air) / (1 + ratio_d / ratio_air)
    z0 = 60 * np.pi / (np.sqrt(eeff) * (ratio_air + ratio_d))

    # 2. 偶模與奇模計算 (基於耦合係數簡化模型)
    # 這裡使用耦合係數 k_c 近似，實際精確解需解 4x4 矩陣，這裡採工程常用近似
    # 增加中間接地 g 會顯著降低耦合
    coupling_factor = np.exp(-np.pi * g / (2 * s + w))
    
    z0e = z0 * (1 + 0.5 * coupling_factor)
    z0o = z0 * (1 - 0.5 * coupling_factor)
    
    # 3. 耦合強度 (dB)
    k_coeff = (z0e - z0o) / (z0e + z0o)
    crosstalk_db = 20 * np.log10(k_coeff / 2) if k_coeff > 0 else -100

    return {
        "Single_Z0": round(z0, 2),
        "Even_Mode_Z0e": round(z0e, 2),
        "Odd_Mode_Z0o": round(z0o, 2),
        "Crosstalk_dB": round(crosstalk_db, 2)
    }

params = {
    "w": 10,   # 線寬
    "s": 5,    # 間隙
    "g": 15,   # 中間接地寬度 (加大此值可降低串擾)
    "h": 20,   # 基板厚度
    "er": 4.4  # FR-4 介電常數
}
# 範例參數 (單位: mil 或 mm 皆可，比例正確即可)

狀態=empty()
result = 帶地平面(**params)
狀態.code(result)
