# core/model.py（加入修正）
import json, os, math
import numpy as np

CORR_JSON = "data/correction_coeffs.json"
_CORR = None

def _load_corr():
    global _CORR
    if _CORR is None and os.path.exists(CORR_JSON):
        with open(CORR_JSON, "r", encoding="utf-8") as f:
            _CORR = json.load(f)
    return _CORR

def _apply_correction(zpy, H1, Er1, W1, W2, S1, T1):
    corr = _load_corr()
    if corr is None:
        return zpy
    feats = [zpy, H1, Er1, W1, W2, S1, T1]
    val = corr["intercept"]
    for power, coef in zip(corr["powers"], corr["coef"]):
        term = coef
        for p, v in zip(power, feats):
            if p == 0:
                continue
            term *= v ** p
        val += term
    return val

def edge_coupled_surface_microstrip_zdd(H1, Er1, W1, W2, S1, T1):
    zpy = _baseline(H1, Er1, W1, W2, S1, T1)
    return _apply_correction(zpy, H1, Er1, W1, W2, S1, T1)
