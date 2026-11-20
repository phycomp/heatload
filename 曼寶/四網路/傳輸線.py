"""Transmission-line impedance models.

Primary method follows IPC-2221 closed forms, which reproduce the reference
calculator (Mantaro Microstrip Impedance From Zo) used as the regression
golden standard:
    FR-4 er=4.2, h=1.6 mm, t=35 um, Zo=50  ->  w = 3.022 mm,
    Tpd = 54.4 ps/cm, L = 2.72 nH/cm, C = 1.09 pF/cm, Rdc = 1.63 mOhm/cm
Hammerstad/Jensen is provided as an alternative (method="hammerstad").
"""
import numpy as np

RHO_CU = 1.72e-8      # Ohm*m, annealed copper @ 20 C (matches reference calculator)
PS_PER_CM_VACUUM = 33.33  # reference-calculator convention for propagation delay


def eeff_ipc(er):
    """Effective permittivity approximation used by the reference calculator."""
    return 0.475 * er + 0.67


# ---------------- microstrip ----------------
def microstrip_z0_ipc(w, h, t, er):
    return 87.0 / np.sqrt(er + 1.41) * np.log(5.98 * h / (0.8 * w + t))


def microstrip_w_from_z0_ipc(z0, h, t, er):
    return (5.98 * h / np.exp(z0 * np.sqrt(er + 1.41) / 87.0) - t) / 0.8


def microstrip_z0_hammerstad(w, h, t, er):
    dw = t / np.pi * np.log(
        1 + 4 * np.e / ((t / h) * (1.0 / np.tanh(np.sqrt(6.517 * w / h))) ** 2))
    u = (w + dw) / h
    ee = (er + 1) / 2 + (er - 1) / 2 / np.sqrt(1 + 12 / u)
    if u <= 1:
        return 60 / np.sqrt(ee) * np.log(8 / u + u / 4), ee
    return 377.0 / (np.sqrt(ee) * (u + 1.393 + 0.667 * np.log(u + 1.444))), ee


def microstrip_w_from_z0_hammerstad(z0, h, t, er, iters=90):
    lo, hi = 1e-4 * h, 1e3 * h
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        z, _ = microstrip_z0_hammerstad(mid, h, t, er)
        if z > z0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _line_metrics(z0, ee, w, t):
    tpd = PS_PER_CM_VACUUM * np.sqrt(ee)          # ps/cm
    return dict(
        w_mm=w,
        z0=z0,                                        # Ohm
        eeff=ee,
        tpd_ps_cm=tpd,
        L_nH_cm=z0 * tpd * 1e-3,                      # Z0 * Tpd
        C_pF_cm=tpd / z0,                             # Tpd / Z0
        Rdc_mOhm_cm=RHO_CU / (w * 1e-3 * t * 1e-3) * 10.0,  # Ohm/m -> mOhm/cm
    )


def design_microstrip(z0, h, t, er, method="ipc"):
    """Given target Zo, return required width and per-length metrics."""
    h, t = float(h), float(t)
    if method == "ipc":
        w = microstrip_w_from_z0_ipc(z0, h, t, er)
        z0_check = microstrip_z0_ipc(w, h, t, er)
        ee = eeff_ipc(er)
    elif method == "hammerstad":
        w = microstrip_w_from_z0_hammerstad(z0, h, t, er)
        z0_check, ee = microstrip_z0_hammerstad(w, h, t, er)
    else:
        raise ValueError("method must be 'ipc' or 'hammerstad'")
    out = _line_metrics(z0_check, ee, w, t)
    out["method"] = method
    return out


def microstrip_from_width(w, h, t, er, method="ipc"):
    """Given width, return Zo and per-length metrics."""
    h, t = float(h), float(t)
    if method == "ipc":
        z0 = microstrip_z0_ipc(w, h, t, er)
        ee = eeff_ipc(er)
    else:
        z0, ee = microstrip_z0_hammerstad(w, h, t, er)
    out = _line_metrics(z0, ee, w, t)
    out["method"] = method
    return out


# ---------------- stripline (IPC-2221 / Cohn) ----------------
def stripline_z0(w, h, t, er):
    """h = distance from trace centre plane to one ground plane; b = 2h."""
    b = 2.0 * h
    return 60.0 / np.sqrt(er) * np.log(4 * b / (0.67 * np.pi * (0.8 * w + t)))


def stripline_w_from_z0(z0, h, t, er):
    b = 2.0 * h
    return (4 * b / np.exp(z0 * np.sqrt(er) / 60.0) / (0.67 * np.pi) - t) / 0.8


def design_stripline(z0, h, t, er):
    w = stripline_w_from_z0(z0, h, t, er)
    z0_check = stripline_z0(w, h, t, er)
    out = _line_metrics(z0_check, er, w, t)
    out["method"] = "ipc-stripline"
    return out


# ---------------- grounded coplanar waveguide (CPWG) ----------------
def _ellip_k_ratio(k):
    from scipy.special import ellipk
    k = np.clip(k, 1e-12, 1 - 1e-12)
    kp = np.sqrt(1 - k ** 2)
    return ellipk(k ** 2) / ellipk(kp ** 2)


def cpwg_z0(w, s, h, er):
    """Conductor-backed CPW. w = trace, s = gap to side grounds, h to back plane."""
    k1 = w / (w + 2 * s)
    k2 = (np.sinh(np.pi * w / (4 * h)) / np.sinh(np.pi * (w + 2 * s) / (4 * h)))
    r1 = _ellip_k_ratio(k1)
    r2 = _ellip_k_ratio(k2)
    ee = 1 + (er - 1) / 2 * (1 / r2) * r1 * 0 + (er - 1) / 2 * (_ellip_k_ratio(np.sqrt(1 - k2 ** 2)) * 0)
    # standard closed form (Wadell): ee = 1 + (er-1)/2 * K(k2')/K(k2) * K(k1)/K(k1')
    ee = 1 + (er - 1) / 2 * _ellip_k_ratio(np.sqrt(1 - k2 ** 2)) * r1
    z0 = 60 * np.pi / (np.sqrt(ee) * (r1 + r2))
    return z0, ee


def cpwg_w_from_z0(z0, s, h, er, iters=80):
    lo, hi = 1e-4 * h, 1e3 * h
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        z, _ = cpwg_z0(mid, s, h, er)
        if z > z0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo, hi)


def design_cpwg(z0, s, h, er):
    w = cpwg_w_from_z0(z0, s, h, er)
    z0_check, ee = cpwg_z0(w, s, h, er)
    out = _line_metrics(z0_check, ee, w, 0.035)
    out["s_mm"] = s
    out["method"] = "cpwg-conformal"
    return out


# ---------------- edge-coupled differential pair ----------------
def diffpair_zdiff(w, s, h, t, er, method="ipc"):
    """IPC-2141 style: Zdiff = 2*Z0*(1 - 0.48*exp(-0.96*s/h))."""
    if method == "ipc":
        z0 = microstrip_z0_ipc(w, h, t, er)
    else:
        z0, _ = microstrip_z0_hammerstad(w, h, t, er)
    return 2 * z0 * (1 - 0.48 * np.exp(-0.96 * s / h))


def diffpair_s_from_zdiff(zdiff, w, h, t, er, method="ipc", iters=80):
    lo, hi = 1e-4 * h, 1e3 * h
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        z = diffpair_zdiff(w, mid, h, t, er, method)
        if z > zdiff:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)
