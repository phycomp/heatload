# tools/polyfit_model.py
"""
用 DOE 資料擬合多項式，輸出係數給 Excel 匯出用。
輸入 CSV 欄位：H1,Er1,W1,W2,S1,T1,Zdiff
"""
import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression

FEATURES = ["H1", "Er1", "W1", "W2", "S1", "T1"]

def fit_poly(csv_path, degree=2, out_json="data/poly_coeffs.json"):
    df = pd.read_csv(csv_path)
    X = df[FEATURES].values
    y = df["Zdiff"].values

    poly = PolynomialFeatures(degree=degree, include_bias=True)
    Xp = poly.fit_transform(X)

    model = LinearRegression().fit(Xp, y)
    r2 = model.score(Xp, y)

    coeffs = {
        "degree": degree,
        "features": FEATURES,
        "powers": poly.powers_.tolist(),
        "coef": model.coef_.tolist(),
        "intercept": float(model.intercept_),
        "r2": float(r2),
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(coeffs, f, indent=2)
    print(f"R2 = {r2:.6f}, 係數已寫入 {out_json}")
    return coeffs

if __name__ == "__main__":
    fit_poly("polar_doe.csv", degree=2)
