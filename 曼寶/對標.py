# 把印出的 slope、intercept 寫回 model.py：
Z_CORRECT_SLOPE = 1.0
Z_CORRECT_INTERCEPT = 0.0

def edge_coupled_surface_microstrip_zdd(...):
    z = ...  # 原模型
    return Z_CORRECT_SLOPE * z + Z_CORRECT_INTERCEPT
