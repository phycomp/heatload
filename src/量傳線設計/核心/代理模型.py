"""代理模型（Surrogate Model）— 用 sklearn 加速評估。"""
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from 量傳線設計.核心.優化 import 評估設計

def 訓練代理模型(samples):
    """samples: list of (params_dict, (f1, f2))"""
    X = np.array([[p["w"], p["s"], p["h"], p["t"], p["pitch"]] for p, _ in samples])
    y1 = np.array([r[0] for _, r in samples])
    y2 = np.array([r[1] for _, r in samples])
    m1 = GradientBoostingRegressor(n_estimators=50, random_state=42)
    m2 = GradientBoostingRegressor(n_estimators=50, random_state=42)
    m1.fit(X, y1)
    m2.fit(X, y2)
    return m1, m2

def 預測(模型, params):
    m1, m2 = 模型
    X = np.array([[params["w"], params["s"], params["h"], params["t"], params["pitch"]]])
    return float(m1.predict(X)[0]), float(m2.predict(X)[0])

def 生成訓練資料(spec_name, n=20):
    import random
    samples = []
    for _ in range(n):
        params = {
            "w": random.uniform(10, 100),
            "s": random.uniform(50, 500),
            "h": random.uniform(0.05, 0.3),
            "t": random.uniform(1, 20),
            "pitch": random.uniform(0.5, 3.0),
        }
        f1, f2 = 評估設計(params, spec_name)
        if f1 != float("inf"):
            samples.append((params, (f1, f2)))
    return samples
