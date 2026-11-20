### 📂 檔案 1：materials_db.py (材料資料庫) 此檔案定義了高頻板材的 Djordjevic-Sarkar 色散模型參數、基礎損耗因子 (Df) 以及銅表面粗糙度 ($R_z$)。
"""
高頻板材材料資料庫
採用 Djordjevic-Sarkar 因果模型參數結構，支援 4-12 GHz 色散效應計算。
"""

MATERIALS_DB = {
    "Rogers 4003C (High Freq)": {
        "Dk0": 3.55,       # 低頻/靜態介電常數
        "Dk_inf": 3.30,    # 高頻/光頻介電常數
        "fm": 10e9,        # 共振頻率 (Hz)
        "m": 0.90,         # 色散斜率因子
        "Df_base": 0.0027, # 基礎損耗因子 (參考 10GHz)
        "Rz_um": 2.0,      # 銅表面粗糙度 Rz (um)，典型壓延銅
        "rho": 1.72e-8     # 銅電阻率 (Ohm*m)
    },
    "Isola 370HR (Mid Freq)": {
        "Dk0": 4.00,
        "Dk_inf": 3.70,
        "fm": 5e9,
        "m": 0.85,
        "Df_base": 0.0150, # FR4 等級損耗
        "Rz_um": 3.5,      # 典型反轉銅 (VLP)
        "rho": 1.72e-8
    },
    "Shengyi S1000-2 (Standard FR4)": {
        "Dk0": 4.50,
        "Dk_inf": 4.00,
        "fm": 2e9,
        "m": 0.90,
        "Df_base": 0.0180, # 標準 FR4 損耗
        "Rz_um": 4.5,      # 典型標準銅 (STD)
        "rho": 1.72e-8
    }
}

def get_material_params(mat_name):
    """獲取材料參數的輔助函數"""
    return MATERIALS_DB.get(mat_name, MATERIALS_DB["Isola 370HR (Mid Freq)"])
