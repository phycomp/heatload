# core/sensitivity.py
import numpy as np
from core.model import edge_coupled_surface_microstrip_zdd
from core.validators import clamp_params

def offsets(n: int):
    if n == 3:
        return [-1, 0, 1]
    if n == 5:
        return [-2, -1, 0, 1, 2]
    if n == 7:
        return [-3, -2, -1, 0, 1, 2, 3]
    raise ValueError("n_points 只支援 3/5/7")

def _z(p):
    return edge_coupled_surface_microstrip_zdd(
        p["H1"], p["Er1"], p["W1"], p["W2"], p["S1"], p["T1"]
    )

def sweep_height(nom, delta, n, taper_mode):
    return _generic_sweep(nom, delta, n, taper_mode, "H1",
                          lambda p, k, d: p.update({"H1": p["H1"] + k*d}))

def sweep_width(nom, delta, n, taper_mode):
    def mut(p, k, d):
        p["W1"] += k*d
        p["W2"] += k*d
    return _generic_sweep(nom, delta, n, taper_mode, "W1", mut)

def sweep_taper(nom, delta, n, taper_mode):
    return _generic_sweep(nom, delta, n, taper_mode, "W2",
                          lambda p, k, d: p.update({"W2": p["W2"] + k*d}))

def sweep_separation(nom, delta, n, taper_mode):
    # 維持中心到中心距離：S 變，W 不變，等效中心距離 = S + W
    # 原 Excel 用 F26+D26-D25 維持 center 距離，這裡簡化為只改 S
    return _generic_sweep(nom, delta, n, taper_mode, "S1",
                          lambda p, k, d: p.update({"S1": p["S1"] + k*d}))

def sweep_trace_height(nom, delta, n, taper_mode):
    return _generic_sweep(nom, delta, n, taper_mode, "T1",
                          lambda p, k, d: p.update({"T1": p["T1"] + k*d}))

def sweep_er(nom, delta, n, taper_mode):
    return _generic_sweep(nom, delta, n, taper_mode, "Er1",
                          lambda p, k, d: p.update({"Er1": p["Er1"] + k*d}))

def _generic_sweep(nom, delta, n, taper_mode, label, mutator):
    z0 = _z(nom)
    rows = []
    for k in offsets(n):
        p = dict(nom)
        mutator(p, k, delta)
        p, warns = clamp_params(p, taper_mode)
        z = _z(p)
        rows.append({
            "offset": k,
            label: p[label],
            "Zdiff": z,
            "rel_%": (z - z0) / z0 * 100 if z0 else 0.0,
            "warnings": "; ".join(warns),
        })
    return rows

def all_sweeps(nom, cfg, taper_mode):
    return {
        "Height":       sweep_height(nom, cfg["height_delta"], cfg["n_points"], taper_mode),
        "Trace Width":  sweep_width(nom, cfg["width_delta"], cfg["n_points"], taper_mode),
        "Taper":        sweep_taper(nom, cfg["taper_delta"], cfg["n_points"], taper_mode),
        "Separation":   sweep_separation(nom, cfg["sep_delta"], cfg["n_points"], taper_mode),
        "Trace Height": sweep_trace_height(nom, cfg["trace_h_delta"], cfg["n_points"], taper_mode),
        "Dielectric":   sweep_er(nom, cfg["er_delta"], cfg["n_points"], taper_mode),
    }

def summarize(results, nominal_z):
    rows = []
    for name, data in results.items():
        vals = [r["Zdiff"] for r in data]
        rels = [r["rel_%"] for r in data]
        rows.append({
            "parameter": name,
            "min": min(vals),
            "max": max(vals),
            "range": max(vals) - min(vals),
            "min_rel_%": min(rels),
            "max_rel_%": max(rels),
            "nominal": nominal_z,
        })
    return rows
