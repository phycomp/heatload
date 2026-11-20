# core/validators.py
LIMITS = {
    "H1": (1.0, None),
    "Er1": (1.0, None),
    "W1": (0.1, None),
    "W2": (0.1, None),
    "S1": (0.1, None),
    "T1": (0.1, None),
}

MIN_TAPER_UM = 0.1  # 最小 taper，避免 W2 >= W1

def clamp_params(params: dict, taper_mode: str = "A") -> tuple[dict, list[str]]:
    """
    taper_mode:
      A: W2 = W1 - MIN_TAPER (預設)
      B: W2 = W1
    """
    warnings = []
    p = dict(params)
    for k, (lo, hi) in LIMITS.items():
        if lo is not None and p[k] < lo:
            warnings.append(f"{k} 低於下限 {lo}，已 clamp")
            p[k] = lo
        if hi is not None and p[k] > hi:
            warnings.append(f"{k} 高於上限 {hi}，已 clamp")
            p[k] = hi
    if p["W2"] > p["W1"]:
        if taper_mode == "A":
            p["W2"] = max(MIN_TAPER_UM, p["W1"] - MIN_TAPER_UM)
            warnings.append("W2 > W1，taper 變負，已套用模式 A：W2 = W1 - MIN_TAPER")
        elif taper_mode == "B":
            p["W2"] = p["W1"]
            warnings.append("W2 > W1，taper 變負，已套用模式 B：W2 = W1")
        else:
            warnings.append("W2 > W1，taper 變負（未處理）")
    return p, warnings
