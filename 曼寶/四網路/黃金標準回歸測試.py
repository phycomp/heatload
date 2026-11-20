## 6. `tests/test_regression.py`（黃金標準回歸測試）

"""Golden-standard regression: reference calculator results."""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import transmission_lines as T
import matching as M


def test_microstrip_golden_standard():
    r = T.design_microstrip(50.0, 1.6, 0.035, 4.2)
    assert abs(r["w_mm"] - 3.022) / 3.022 <= 0.01
    assert abs(r["tpd_ps_cm"] - 54.411) / 54.411 <= 0.01
    assert abs(r["L_nH_cm"] - 2.721) / 2.721 <= 0.01
    assert abs(r["C_pF_cm"] - 1.08821) / 1.08821 <= 0.01
    assert abs(r["Rdc_mOhm_cm"] - 1.626) / 1.626 <= 0.01


def test_microstrip_inverse_consistency():
    r = T.design_microstrip(50.0, 1.6, 0.035, 4.2)
    w = T.microstrip_from_width(r["w_mm"], 1.6, 0.035, 4.2)
    assert abs(w["z0"] - 50.0) < 0.01


def test_l_match_exact():
    for zl in (25 + 0j, 100 + 0j, 40 + 20j):
        for s in M.l_match(zl, 50.0):
            assert abs(s["zin_check"] - 50.0) < 1e-6


def test_single_stub_conductance_unity():
    for zl in (25 + 0j, 100 + 0j, 60 - 30j):
        sols = M.single_stub(zl, 50.0)
        assert sols
        for s in sols:
            assert 0 <= s["d_over_lambda"] <= 0.5


def test_double_stub_conductance_unity():
    sols = M.double_stub(100 + 0j, 50.0)
    assert sols


def test_pi_match_exact():
    for rs, rl in [(50, 100), (50, 25), (75, 50)]:
        r = M.pi_match(rs, rl, q1=None)
        assert abs(r["zin_check"] - rs) < 1e-6


def test_t_match_exact():
    r = M.t_match(50, 100, x2=50)
    assert abs(r["zin_check"] - 50) < 1e-6


def test_nlu_parse_bilingual():
    import nlu as N
    r = N.parse("FR-4 1.6mm 1oz 做 50Ω 微帶線")
    assert r["er"] == 4.2 and r["h_mm"] == 1.6
    assert r["t_mm"] == 0.035 and r["z0"] == 50.0
    r = N.parse("Design a 50 ohm microstrip on FR-4, h=1.6mm, t=35um")
    assert r["z0"] == 50.0 and r["structure"] == "microstrip"
