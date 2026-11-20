# tools/compare_polar.py
"""
比較 Polar 與 Python 模型，輸出誤差統計與圖。
"""
import numpy as np
import pandas as pd
import plotly.express as px
from core.model import edge_coupled_surface_microstrip_zdd

FEATURES = ["H1", "Er1", "W1", "W2", "S1", "T1"]

def compare(csv_path, out_html="polar_vs_python.html"):
    df = pd.read_csv(csv_path).dropna(subset=["Zdiff"])
    df["Zpy"] = df.apply(
        lambda r: edge_coupled_surface_microstrip_zdd(
            r.H1, r.Er1, r.W1, r.W2, r.S1, r.T1
        ), axis=1
    )
    df["error"] = df["Zpy"] - df["Zdiff"]
    df["rel_error_%"] = df["error"] / df["Zdiff"] * 100

    print("=== 誤差統計 ===")
    print(df["error"].describe())
    print("最大絕對誤差：", df["error"].abs().max())
    print("最大相對誤差 %：", df["rel_error_%"].abs().max())

    fig = px.scatter(df, x="Zdiff", y="Zpy",
                     title="Polar vs Python Zdiff",
                     labels={"Zdiff": "Polar", "Zpy": "Python"})
    fig.add_shape(type="line", x0=df.Zdiff.min(), y0=df.Zdiff.min(),
                  x1=df.Zdiff.max(), y1=df.Zdiff.max(),
                  line=dict(dash="dash"))
    fig.write_html(out_html)
    print(f"圖已寫入 {out_html}")
    return df

if __name__ == "__main__":
    compare("polar_doe.csv")
