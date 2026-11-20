"""Impedance-matching network design: L-section, single/double stub, pi/T.

Conventions: all impedances in Ohm, frequency in Hz. Solutions return both
reactances and, when f is given, concrete L/C component values.
Sign convention: X > 0 -> inductor, X < 0 -> capacitor (shunt or series).
"""
import numpy as np

C0 = 299792458.0  # m/s


def _to_lc(x, f):
    """Reactance -> component value. Returns dict with kind and value."""
    if f is None:
        return {"kind": "L" if x > 0 else "C", "X_ohm": x}
    w = 2 * np.pi * f
    if x > 0:
        return {"kind": "L", "X_ohm": x, "value_H": x / w}
    return {"kind": "C", "X_ohm": x, "value_F": -1.0 / (w * x)}


def _absorb_xl(xs, XL, f):
    """Merge load reactance into the series arm, then convert to L/C."""
    return _to_lc(xs + XL, f)


def l_match(zl, z0=50.0, f=None):
    """L-section match of complex load zl to real z0.

    Returns up to 4 solutions (2 topologies x 2 passbands).
    Topology 'shunt_at_source': source -- shunt -- series -- load (needs RL < z0)
    Topology 'shunt_at_load':   source -- series -- shunt -- load (needs RL > z0)
    Load reactance XL is absorbed into the series arm.
    """
    zl = complex(zl)
    RL, XL = zl.real, zl.imag
    sols = []
    if RL <= 0:
        raise ValueError("load resistance must be positive")
    if RL < z0:
        xs_mag = np.sqrt(RL * (z0 - RL))
        for sgn in (+1, -1):
            xs = sgn * xs_mag
            xp = -z0 * RL / xs
            sols.append({
                "topology": "shunt_at_source",
                "series": _absorb_xl(xs, XL, f),
                "shunt": _to_lc(xp, f),
                "zin_check": _zin_lmatch(xs + XL, xp, RL),
            })
    if RL > z0:
        xp_mag = RL * np.sqrt(z0 / (RL - z0))
        for sgn in (+1, -1):
            xp = sgn * xp_mag
            xs = -RL ** 2 * xp / (RL ** 2 + xp ** 2)
            sols.append({
                "topology": "shunt_at_load",
                "series": _absorb_xl(xs, XL, f),
                "shunt": _to_lc(xp, f),
                "zin_check": _zin_lmatch(xs + XL, xp, RL),
            })
    return sols


def _zin_lmatch(xs, xp, RL):
    """Input impedance of: series j*xs feeding (RL || j*xp)."""
    return 1j * xs + RL * 1j * xp / (RL + 1j * xp)


def _yin_line(y, d_over_lambda):
    """Normalized admittance at d from load, yL normalized."""
    t = np.tan(2 * np.pi * d_over_lambda)
    return (y + 1j * t) / (1 + 1j * y * t)


def _stub_length(b, f, stub_type):
    """Length of shunt stub providing normalized susceptance b at frequency f."""
    beta_l = np.arctan(b) if stub_type == "open" else np.arctan(-1.0 / b)
    l_over_lambda = np.mod(beta_l / (2 * np.pi), 0.5)
    out = {"type": stub_type, "b_norm": b, "l_over_lambda": l_over_lambda}
    if f:
        lam = C0 / f
        out["length_m"] = l_over_lambda * lam
    return out


def single_stub(zl, z0=50.0, f=None, stub_types=("short", "open")):
    """Single shunt-stub match. Returns solutions with line length d and stub length."""
    zl = complex(zl)
    y = z0 / zl  # normalized load admittance
    roots = []
    grid = np.linspace(1e-6, 0.5, 4001)
    g_prev = np.real(_yin_line(y, grid[0])) - 1
    for i in range(1, len(grid)):
        g = np.real(_yin_line(y, grid[i])) - 1
        if g == 0 or g * g_prev < 0:
            lo, hi = grid[i - 1], grid[i]
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                gm = np.real(_yin_line(y, mid)) - 1
                if gm * g_prev <= 0:
                    hi = mid
                else:
                    lo, mid
                    lo = mid
                    g_prev = gm
            d = 0.5 * (lo + hi)
            roots.append(d)
        g_prev = g
    sols = []
    for d in roots:
        b = -np.imag(_yin_line(y, d))
        for st in stub_types:
            sols.append({
                "topology": "single_shunt_stub",
                "d_over_lambda": d,
                "stub": _stub_length(b, f, st),
            })
    return sols


def double_stub(zl, z0=50.0, f=None, d0_over_lambda=0.125,
                stub_types=("short", "open")):
    """Double shunt stub, fixed spacing d0 (default lambda/8). Both stub lengths solved."""
    zl = complex(zl)
    y = z0 / zl
    t = np.tan(2 * np.pi * d0_over_lambda)

    def g2(b1):
        y1 = y + 1j * b1
        return np.real((y1 + 1j * t) / (1 + 1j * y1 * t))

    roots = []
    grid = np.linspace(-40, 40, 8001)
    g_prev = g2(grid[0]) - 1
    for i in range(1, len(grid)):
        g = g2(grid[i]) - 1
        if g == 0 or g * g_prev < 0:
            lo, hi = grid[i - 1], grid[i]
            glo = g_prev
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                gm = g2(mid) - 1
                if gm * glo <= 0:
                    hi = mid
                else:
                    lo = mid
                    glo = gm
            roots.append(0.5 * (lo + hi))
        g_prev = g
    sols = []
    for b1 in roots:
        y1 = y + 1j * b1
        y2 = (y1 + 1j * t) / (1 + 1j * y1 * t)
        b2 = -np.imag(y2)
        for st in stub_types:
            sols.append({
                "topology": "double_shunt_stub",
                "d0_over_lambda": d0_over_lambda,
                "stub1": _stub_length(b1, f, st),
                "stub2": _stub_length(b2, f, st),
            })
    return sols


def pi_match(rs, rl, f=None, q=None, rv=None, lowpass=True):
    """Pi network (shunt-series-shunt). Requires rv > max(rs, rl).

    Provide either virtual resistance rv, or input q (rv = rmin*(1+q^2),
    requires q >= sqrt(rmax/rmin - 1)).
    """
    rs, rl = float(rs), float(rl)
    if rv is None:
        if q is None:
            raise ValueError("provide q or rv")
        rmin = min(rs, rl)
        rv = rmin * (1 + q ** 2)
    if rv <= max(rs, rl):
        raise ValueError("pi network requires rv > max(rs, rl)")
    q1 = np.sqrt(rv / rs - 1)
    q2 = np.sqrt(rv / rl - 1)
    s = 1 if lowpass else -1
    xp1 = s * rv / q1 * -1     # shunt: lowpass -> C (negative reactance)
    xp2 = s * rv / q2 * -1
    xs = -s * rv * (q1 + q2)   # series: lowpass -> L
    out = {
        "topology": "pi",
        "rv": rv,
        "shunt_source": _to_lc(xp1, f),
        "series": _to_lc(xs, f),
        "shunt_load": _to_lc(xp2, f),
    }
    zin = 1j * xs + (rl * 1j * xp2) / (rl + 1j * xp2)
    zin = (rs * 1j * xp1) / (rs + 1j * xp1 + 0 * zin)  # placeholder, real check below
    # full check: source -- shunt xp1 -- series xs -- shunt xp2 -- load rl
    zr = 1j * xs + rl * 1j * xp2 / (rl + 1j * xp2)
    out["zin_check"] = rs * 1j * xp1 / (rs + 1j * xp1) * 0 + zr * (rs * 1j * xp1) / (rs * 1j * xp1 + 0)
    out["zin_check"] = (rs * 1j * xp1) / (rs + 1j * xp1) if False else (
        (zr * 1j * xp1) / (zr + 1j * xp1))
    return out


def t_match(rs, rl, f=None, x2=None):
    """T network (series-shunt-series), low-pass style.

    Parameterized by the load-side series reactance x2 (choose via desired Q,
    e.g. x2 = q*rl). Solves middle shunt and source-side series reactance.
    General solution of the T design equations; signs may mix (then the
    realization is not pure low-pass).
    """
    rs, rl = float(rs), float(rl)
    if x2 is None:
        x2 = np.sqrt(rl * max(rs, rl))  # sensible default ~ geometric mean
    a = rl - rs
    if abs(a) < 1e-12:
        raise ValueError("use L-match for rs == rl")
    disc = rs * rl * (x2 ** 2 + max(rl, rs) * abs(rl - rs))
    x = (rs * x2 + np.sqrt(disc)) / a if a > 0 else (rs * x2 - np.sqrt(disc)) / a
    den = rl ** 2 + (x2 + x) ** 2
    x1 = -(x2 ** 2 * x + x2 * x ** 2 + x * rl ** 2) / den
    out = {
        "topology": "t",
        "series_source": _to_lc(x1, f),
        "shunt": _to_lc(x, f),
        "series_load": _to_lc(x2, f),
    }
    zr = rl + 1j * x2
    zpar = zr * 1j * x / (zr + 1j * x)
    out["zin_check"] = 1j * x1 + zpar
    return out


def s11_of_network(zin_fn, freqs, z0=50.0):
    """S11 (linear) over a frequency sweep for an input-impedance function."""
    freqs = np.asarray(freqs, dtype=float)
    return np.array([(zin_fn(f) - z0) / (zin_fn(f) + z0) for f in freqs])


def gamma(zl, z0=50.0):
    zl = np.asarray(zl, dtype=complex)
    return (zl - z0) / (zl + z0)
