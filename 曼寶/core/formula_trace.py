# core/formula_trace.py
def trace_row(param, offset, value, z, rel, z0):
    return (
        f"Zdiff({param}={value:.4f}, offset={offset}) = "
        f"f(...) = {z:.4f} Ω | "
        f"相對 nominal({z0:.4f}) = {rel:+.3f}%"
    )

def trace_model():
    return (
        "模型：Edge-Coupled Surface Microstrip（Python 近似）\n"
        "Zdiff = 2 * Z0(Wavg, H1, T1, Er1) * (1 - 0.35 * exp(-1.6 * S1/(S1+2*Wavg)))\n"
        "Wavg = (W1 + W2)/2\n"
        "Z0 使用 Hammerstad-Jensen 近似。\n"
        "注意：此為 baseline，需以 Polar DOE 修正。"
    )
