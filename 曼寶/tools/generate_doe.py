# tools/generate_doe.py
"""
產生 DOE 組合（Latin Hypercube 或全因子），輸出 CSV。
"""
import numpy as np
import pandas as pd
from scipy.stats import qmc

def generate_lhs(n_samples=200, seed=42, out="polar_doe_input.csv"):
    ranges = {
        "H1": (4.0, 12.0),
        "Er1": (3.0, 5.0),
        "W1": (6.0, 16.0),
        "W2": (5.0, 15.0),
        "S1": (4.0, 14.0),
        "T1": (0.5, 2.5),
    }
    sampler = qmc.LatinHypercube(d=len(ranges), seed=seed)
    sample = sampler.random(n=n_samples)
    lower = np.array([v[0] for v in ranges.values()])
    upper = np.array([v[1] for v in ranges.values()])
    scaled = qmc.scale(sample, lower, upper)
    df = pd.DataFrame(scaled, columns=list(ranges.keys()))
    df["Zdiff"] = ""
    df.to_csv(out, index=False)
    print(f"已產生 {out}，共 {n_samples} 組，請用 Polar 填入 Zdiff")
    return df

if __name__ == "__main__":
    generate_lhs()
