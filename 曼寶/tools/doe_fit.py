# tools/doe_fit.py
"""
1. 用 Excel 跑 DOE，輸出 CSV：
   H1,Er1,W1,W2,S1,T1,Zdiff_polar
2. 用 Python 模型算 Zdiff_py
3. 擬合修正：Zdiff_corrected = a*Zdiff_py + b 或 多項式
4. 把係數寫回 model.py
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from core.model import edge_coupled_surface_microstrip_zdd

def fit(csv_path):
    df = pd.read_csv(csv_path)
    df["Zpy"] = df.apply(lambda r: edge_coupled_surface_microstrip_zdd(
        r.H1, r.Er1, r.W1, r.W2, r.S1, r.T1), axis=1)
    X = df[["Zpy"]].values
    y = df["Zdiff_polar"].values
    m = LinearRegression().fit(X, y)
    print("slope =", m.coef_[0], "intercept =", m.intercept_)
    print("R2 =", m.score(X, y))
    return m

if __name__ == "__main__":
    fit("polar_doe.csv")
