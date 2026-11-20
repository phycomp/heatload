# -*- coding: utf-8 -*-
"""
tl_synthesis.py
===============
PCB 傳輸線「合成」（逆工程）程式庫 —— 專案 Phase B 交付物。

公式來源分兩族：
  [IPC]  IPC-2141A / Mantaro 公開閉式（Mantaro 已給部分反函數，本庫重新推導並驗證）
  [DOC2] DOC-002 保角映射 / Hammerstad 模型（逆解採牛頓迭代，回報收斂資訊）

統一入口 solve(section, target, **params) -> dict（反解值、殘差、迭代數、適用域警告）。
所有幾何參數單位：mm；阻抗：Ω；傳播延遲：ns/m。
"""
import numpy as np

ETA0 = 120.0 * np.pi
MU0  = 4.0e-7 * np.pi
EPS0 = 8.854187817e-12

# =====================================================================
# 數值工具
# =====================================================================

def elliptic_ratio(k):
    """K(k')/K(k) 的 Hilberg 近似（精度 < 3e-6，DOC-002 §3.5）。"""
    k = float(k)
    if k >= 1.0:
        return 0.0
    kp = np.sqrt(1.0 - k * k)
    if k <= 1.0 / np.sqrt(2.0):
        skp = np.sqrt(kp)
        return (1.0 / np.pi) * np.log(2.0 * (1.0 + skp) / (1.0 - skp))
    sk = np.sqrt(k)
    return np.pi / np.log(2.0 * (1.0 + sk) / (1.0 - sk))


def newton(f, x0, tol=1e-10, max_iter=100, xmin=1e-12):
    """牛頓迭代（數值微分）。回傳 (x, iterations, residual)。"""
    x = float(x0)
    for it in range(1, max_iter + 1):
        fx = f(x)
        h = max(1e-10, abs(x) * 1e-6)
        dfx = (f(x + h) - fx) / h
        if abs(dfx) < 1e-30:
            break
        x_new = x - fx / dfx
        if x_new < xmin:
            x_new = xmin
        if abs(x_new - x) < tol * max(1.0, abs(x_new)):
            return x_new, it, abs(f(x_new))
        x = x_new
    return x, max_iter, abs(f(x))


# =====================================================================
# [IPC] Microstrip 族
# =====================================================================

def microstrip_z0(w, h, t=0.0, er=4.2):
    """[IPC] Z0 = 87/√(er+1.41) · ln(5.98h/(0.8w+t))，適用 0.1 ≤ w/h ≤ 3.0"""
    return 87.0 / np.sqrt(er + 1.41) * np.log(5.98 * h / (0.8 * w + t))


def microstrip_w(z0, h, t=0.0, er=4.2):
    """[IPC] 解析反函數（DOC-003 §II.1 推導）：
    w = ( 5.98h / exp(z0·√(er+1.41)/87) − t ) / 0.8"""
    return (5.98 * h / np.exp(z0 * np.sqrt(er + 1.41) / 87.0) - t) / 0.8


def microstrip_tpd(er):
    """[IPC] Tpd = 3.333√(0.475·er + 0.67) ns/m"""
    return 3.333 * np.sqrt(0.475 * er + 0.67)


def embedded_microstrip_eeff(h, h1, er):
    """[IPC] 嵌入式微帶有效介電常數 ε_eff = εr·(1 − e^{−1.55·h1/h})，適用 h1/h ≥ 1.2"""
    return er * (1.0 - np.exp(-1.55 * h1 / h))


def embedded_microstrip_z0(w, h, h1, t=0.0, er=4.2):
    """[IPC] Z0 = 60/√ε_eff · ln(5.98h/(0.8w+t))"""
    eeff = embedded_microstrip_eeff(h, h1, er)
    return 60.0 / np.sqrt(eeff) * np.log(5.98 * h / (0.8 * w + t))


def embedded_microstrip_w(z0, h, h1, t=0.0, er=4.2):
    """[IPC] 解析反函數：w = ( 5.98h / exp(z0·√ε_eff/60) − t ) / 0.8"""
    eeff = embedded_microstrip_eeff(h, h1, er)
    return (5.98 * h / np.exp(z0 * np.sqrt(eeff) / 60.0) - t) / 0.8


# =====================================================================
# [IPC] Stripline 族（h = 走線到任一接地平面的距離；平面間距 = 2h）
# =====================================================================

def stripline_z0(w, h, t=0.0, er=4.2):
    """[IPC] Z0 = 60/√er · ln(1.9(2h+t)/(0.8w+t))，適用 0.1 ≤ w/h ≤ 2.0 且 t/h < 0.25"""
    return 60.0 / np.sqrt(er) * np.log(1.9 * (2.0 * h + t) / (0.8 * w + t))


def stripline_w(z0, h, t=0.0, er=4.2):
    """[IPC] 解析反函數：w = ( 1.9(2h+t) / exp(z0·√er/60) − t ) / 0.8"""
    return (1.9 * (2.0 * h + t) / np.exp(z0 * np.sqrt(er) / 60.0) - t) / 0.8


def stripline_tpd(er):
    """[IPC] Tpd = 3.333√er ns/m"""
    return 3.333 * np.sqrt(er)


def asymmetric_stripline_z0(w, h, h1, t=0.0, er=4.2):
    """[IPC] 非對稱帶狀線（h = 較薄側, h1 = 較厚側）：
    Z0 = 80/√er · ln(1.9(2h+t)/(0.8w+t)) · (1 − h/(4h1))"""
    base = 80.0 / np.sqrt(er) * np.log(1.9 * (2.0 * h + t) / (0.8 * w + t))
    return base * (1.0 - h / (4.0 * h1))


def asymmetric_stripline_w(z0, h, h1, t=0.0, er=4.2):
    """[IPC] 解析反函數：把修正因子併入指數（DOC-003 §II.5 推導）"""
    corr = 1.0 - h / (4.0 * h1)
    return (1.9 * (2.0 * h + t) / np.exp(z0 * np.sqrt(er) / (80.0 * corr)) - t) / 0.8


def broadside_stripline_z0(w, h, h1, t=0.0, er=4.2):
    """[IPC] 寬邊耦合帶狀線（h = 外側介質, h1 = 中心介質）：
    Z0 = 80/√er · ln(1.9(2h+t)/(0.8w+t)) · (1 − h/(4(h+h1+t)))"""
    base = 80.0 / np.sqrt(er) * np.log(1.9 * (2.0 * h + t) / (0.8 * w + t))
    return base * (1.0 - h / (4.0 * (h + h1 + t)))


def broadside_stripline_w(z0, h, h1, t=0.0, er=4.2):
    corr = 1.0 - h / (4.0 * (h + h1 + t))
    return (1.9 * (2.0 * h + t) / np.exp(z0 * np.sqrt(er) / (80.0 * corr)) - t) / 0.8


# =====================================================================
# [IPC] 差分對
# =====================================================================

def diff_microstrip_zd(w, d, h, t=0.0, er=4.2):
    """[IPC] Zd = 174/√(er+1.41) · ln(5.98h/(0.8w+t)) · (1 − 0.48·e^{−0.96·d/h})
    d = 兩線間距（edge-to-edge 依 Mantaro 圖示）"""
    return (174.0 / np.sqrt(er + 1.41) * np.log(5.98 * h / (0.8 * w + t))
            * (1.0 - 0.48 * np.exp(-0.96 * d / h)))


def diff_microstrip_w(zd, d, h, t=0.0, er=4.2):
    """[IPC] 解析反函數（把耦合因子併入指數）"""
    cf = 1.0 - 0.48 * np.exp(-0.96 * d / h)
    return (5.98 * h / np.exp(zd * np.sqrt(er + 1.41) / (174.0 * cf)) - t) / 0.8


def diff_microstrip_d(z0, zd, h):
    """[IPC] From-Zo 版：Zd = 2Z0(1 − 0.48e^{−0.96d/h}) → d 的解析反函數"""
    return -h / 0.96 * np.log(1.0 - zd / (2.0 * z0))


def diff_stripline_zd(w, d, h, t=0.0, er=4.2):
    """[IPC] Zd = 120/√er · ln(1.9(2h+t)/(0.8w+t)) · (1 − 0.347·e^{−2.9d/(2h+t)})"""
    return (120.0 / np.sqrt(er) * np.log(1.9 * (2.0 * h + t) / (0.8 * w + t))
            * (1.0 - 0.347 * np.exp(-2.9 * d / (2.0 * h + t))))


def diff_stripline_w(zd, d, h, t=0.0, er=4.2):
    cf = 1.0 - 0.347 * np.exp(-2.9 * d / (2.0 * h + t))
    return (1.9 * (2.0 * h + t) / np.exp(zd * np.sqrt(er) / (120.0 * cf)) - t) / 0.8


# =====================================================================
# 元件級
# =====================================================================

def coax_z0(di, do, er, mur=1.0):
    """Z0 = 60/√(er·mur) · ln(do/di)"""
    return 60.0 / np.sqrt(er * mur) * np.log(do / di)


def coax_di(z0, do, er, mur=1.0):
    return do * np.exp(-z0 * np.sqrt(er * mur) / 60.0)


def coax_do(z0, di, er, mur=1.0):
    return di * np.exp(z0 * np.sqrt(er * mur) / 60.0)


def parallel_wire_z0(s, d, er):
    """Z0 = 120/√er · acosh(s/d)；Tpd = 3.333√er ns/m"""
    return 120.0 / np.sqrt(er) * np.arccosh(s / d)


def parallel_wire_s(z0, d, er):
    return d * np.cosh(z0 * np.sqrt(er) / 120.0)


def parallel_wire_tpd(er):
    return 3.333 * np.sqrt(er)


def plane_lc(w, h, er, mur=1.0):
    """平行板（w >> h）：L = μ0·mur·h/w (H/m)，C = ε0·er·w/h (F/m)。
    回傳 dict(L_nH_m, C_pF_m, Z_plate, Tpd_ns_m)"""
    L = MU0 * mur * h / w
    C = EPS0 * er * w / h
    return dict(L_nH_m=L * 1e9, C_pF_m=C * 1e12,
                Z_plate=np.sqrt(L / C), Tpd_ns_m=np.sqrt(L * C) * 1e9)


def pad_capacitance(w, l, h, t=0.0, er=4.2):
    """[IPC] 矩形焊盤電容（Mantaro 公式，幾何單位 mm，結果 pF）：
    C = 8.854·er·(w−h)(l−h)/h + 26.40·(er+1.41)·(w+l)/ln(5.98h/(0.8h+t))
    適用 w>h 且 l>h，含邊緣電容。"""
    c1 = 8.854 * er * (w - h) * (l - h) / h
    c2 = 26.40 * (er + 1.41) * (w + l) / np.log(5.98 * h / (0.8 * h + t))
    return c1 + c2


# =====================================================================
# [DOC2] CPW（保角映射族，逆解 🔴 牛頓迭代）
# =====================================================================

def cpw_z0(s, w, h=np.inf, er=4.2, t=0.0):
    """[DOC2] CPW 特性阻抗（Wen 1969 + 有限厚度修正）"""
    if t > 0:
        s = s + t / np.pi * (1.0 + np.log(4.0 * np.pi * s / t))
    d = s + 2.0 * w
    k = s / d
    if np.isinf(h) or h > 10.0 * d:
        q = 0.5
    else:
        k1 = np.clip(np.sinh(np.pi * s / (4.0 * h)) / np.sinh(np.pi * d / (4.0 * h)), 0.0, 1.0)
        rk = elliptic_ratio(k)
        rk1 = elliptic_ratio(k1) if k1 > 0 else 0.0
        q = rk1 / rk if (rk1 > 0 and rk > 0) else 0.5
    eeff = 1.0 + (er - 1.0) / 2.0 * q
    return 30.0 * np.pi / np.sqrt(eeff) * elliptic_ratio(k), eeff


def cpw_solve_s(z0_target, w, h=np.inf, er=4.2, t=0.0):
    """給定槽寬 w，牛頓反解中心導體寬 s。回傳 (s, iterations, residual)。"""
    f = lambda s: cpw_z0(s, w, h, er, t)[0] - z0_target
    s0 = w  # 初始值：k=1/3 附近
    s, it, res = newton(f, s0)
    return s, it, res


# =====================================================================
# [DOC2] 差分 Stripline 保角映射精確解（逆解 🔴 牛頓迭代）
# =====================================================================

def diff_stripline_conformal(w, s, b, er=4.2):
    """[DOC2] 偶模/奇模阻抗（Cohn 1954）：
    ke = tanh(πw/2b)·tanh(π(w+s)/2b)，ko = tanh(πw/2b)/tanh(π(w+s)/2b)"""
    tw = np.tanh(np.pi * w / (2.0 * b))
    tws = max(np.tanh(np.pi * (w + s) / (2.0 * b)), 1e-10)
    ke = np.clip(tw * tws, 0.0, 1.0)
    ko = np.clip(tw / tws, 0.0, 1.0)
    z0e = 60.0 / np.sqrt(er) * elliptic_ratio(ke)
    z0o = 60.0 / np.sqrt(er) * elliptic_ratio(ko)
    return dict(Z0_even=z0e, Z0_odd=z0o, Z_diff=2.0 * z0o)


def diff_stripline_conformal_w(zdiff_target, s, b, er=4.2):
    """給定間距 s，牛頓反解線寬 w，使 Z_diff = target。回傳 (w, iterations, residual)。"""
    f = lambda w: diff_stripline_conformal(w, s, b, er)["Z_diff"] - zdiff_target
    w0 = b / 4.0
    w, it, res = newton(f, w0)
    return w, it, res


# =====================================================================
# [DOC2] Hammerstad 微帶（跨族對照用）
# =====================================================================

def microstrip_hj_z0(w, h, er=4.2):
    """[DOC2] Hammerstad-Jensen 正向模型（供 IPC 族交叉比對）"""
    wh = w / h
    a, bb = (er + 1) / 2.0, (er - 1) / 2.0
    F = (1 + 12 / wh) ** (-0.5) + (0.04 * (1 - wh) ** 2 if wh <= 1 else 0.0)
    eeff = a + bb * F
    if wh <= 1:
        z0 = ETA0 / (2 * np.pi * np.sqrt(eeff)) * np.log(8 / wh + wh / 4)
    else:
        z0 = ETA0 / (np.sqrt(eeff) * (wh + 1.393 + 0.667 * np.log(wh + 1.444)))
    return z0, eeff


# =====================================================================
# 疊構層（Polar 模板映射）
# =====================================================================

PREPREG_UM = {"106": 57.0, "1080": 70.0, "1651": 131.0}   # 壓合後厚度（標稱）
CORE_UM = 400.0                                            # FR4 core（標稱）
ER_FR4 = 4.2

TEMPLATES = {
    "6L_foil_build": dict(
        desc="Polar 6L foil build（L1/L6 外層 foil；機械鑽孔 L1–L6）",
        total_um=1557.34, n=6,
        copper_um={1: 18, 2: 35, 3: 35, 4: 35, 5: 35, 6: 18},
        signal_layers=[1, 3, 4, 6], plane_layers=[2, 5],
        # 各訊號層到最近參考平面的介質厚度（µm）
        # L1/L6: 1651×2 = 262；L3/L4: core(400)+pp(1080+106+1080=233) → 對稱帶狀線半間距
        h_microstrip_um={1: 262.0, 6: 262.0},
        h_stripline_um={3: 316.5, 4: 316.5},
    ),
    "8L_foil_build": dict(
        desc="Polar 8L foil build（含 L1–L2 / L8–L7 laser drill 微盲孔）",
        total_um=1526.90, n=8,
        copper_um={1: 18, 2: 18, 3: 35, 4: 35, 5: 35, 6: 35, 7: 18, 8: 18},
        signal_layers=[1, 2, 4, 5, 7, 8], plane_layers=[3, 6],
        h_microstrip_um={1: 57.0, 8: 57.0, 2: 70.0, 7: 70.0},
        h_stripline_um={4: 300.0, 5: 300.0},
    ),
}

class Stackup:
    """Polar 風格疊構：template 載入 → assign(layer, target) 自動選公式並反解線寬。"""

    def __init__(self, template="6L_foil_build", er=ER_FR4):
        if template not in TEMPLATES:
            raise KeyError(f"未知模板 {template}；可用：{list(TEMPLATES)}")
        self.tpl = TEMPLATES[template]
        self.name = template
        self.er = er

    @classmethod
    def from_polar_template(cls, name):
        return cls(name)

    @property
    def layers(self):
        return list(range(1, self.tpl["n"] + 1))

    def h_for(self, layer, section):
        key = "h_microstrip_um" if "microstrip" in section else "h_stripline_um"
        return self.tpl[key][layer] / 1000.0  # mm

    def assign(self, layer, target_z0=None, target_zd=None, section=None, d=None):
        """給定目標阻抗，反解線寬。外層→microstrip，內層→stripline（可覆寫 section）。"""
        t = self.tpl["copper_um"][layer] / 1000.0
        if section is None:
            section = "microstrip" if layer in (1, self.tpl["n"]) else "stripline"
        h = self.h_for(layer, section)
        if target_zd is not None:                       # 差分
            if d is None:
                raise ValueError("差分指派需提供間距 d (mm)")
            if section == "microstrip":
                w = diff_microstrip_w(target_zd, d, h, t, self.er)
                chk = diff_microstrip_zd(w, d, h, t, self.er)
                tpd = microstrip_tpd(self.er)
            else:
                w = diff_stripline_w(target_zd, d, h, t, self.er)
                chk = diff_stripline_zd(w, d, h, t, self.er)
                tpd = stripline_tpd(self.er)
            return dict(layer=layer, section=section + "_diff", w_mm=w, d_mm=d,
                        target=target_zd, forward_check=chk,
                        residual_pct=abs(chk - target_zd) / target_zd * 100,
                        tpd_ns_m=tpd)
        if section == "microstrip":
            w = microstrip_w(target_z0, h, t, self.er)
            chk = microstrip_z0(w, h, t, self.er)
            tpd = microstrip_tpd(self.er)
        else:
            w = stripline_w(target_z0, h, t, self.er)
            chk = stripline_z0(w, h, t, self.er)
            tpd = stripline_tpd(self.er)
        return dict(layer=layer, section=section, w_mm=w,
                    target=target_z0, forward_check=chk,
                    residual_pct=abs(chk - target_z0) / target_z0 * 100,
                    tpd_ns_m=tpd)


# =====================================================================
# 統一求解器
# =====================================================================

def solve(section, target, h=None, h1=None, t=0.0, er=4.2, d=None,
          w=None, b=None, method="auto"):
    """統一合成入口。
    section: microstrip | embedded_microstrip | stripline | asymmetric_stripline
             | broadside_stripline | diff_microstrip | diff_stripline
             | coax | parallel_wire | cpw | diff_stripline_conformal
    回傳 dict(geometry, forward_check, residual_pct [, iterations] [, warning])
    """
    res = dict(section=section, target=target, method=method)
    if section == "microstrip":
        wv = microstrip_w(target, h, t, er); res.update(w_mm=wv, tpd_ns_m=microstrip_tpd(er))
    elif section == "embedded_microstrip":
        wv = embedded_microstrip_w(target, h, h1, t, er); res.update(w_mm=wv)
    elif section == "stripline":
        wv = stripline_w(target, h, t, er); res.update(w_mm=wv, tpd_ns_m=stripline_tpd(er))
    elif section == "asymmetric_stripline":
        wv = asymmetric_stristrip_w = asymmetric_stripline_w(target, h, h1, t, er)
        res.update(w_mm=wv)
    elif section == "broadside_stripline":
        wv = broadside_stripline_w(target, h, h1, t, er); res.update(w_mm=wv)
    elif section == "diff_microstrip":
        wv = diff_microstrip_w(target, d, h, t, er); res.update(w_mm=wv, d_mm=d)
    elif section == "diff_stripline":
        wv = diff_stripline_w(target, d, h, t, er); res.update(w_mm=wv, d_mm=d)
    elif section == "coax":
        res.update(di_mm=coax_di(target, w, er))   # w 在此當 do
    elif section == "parallel_wire":
        res.update(s_mm=parallel_wire_s(target, d, er))   # d = 線徑
    elif section == "cpw":
        sv, it, rr = cpw_solve_s(target, w, h if h else np.inf, er, t)
        res.update(s_mm=sv, iterations=it); res["residual_abs"] = rr
    elif section == "diff_stripline_conformal":
        wv, it, rr = diff_stripline_conformal_w(target, d, b, er)
        res.update(w_mm=wv, s_mm=d, iterations=it); res["residual_abs"] = rr
    else:
        raise KeyError(f"未知 section：{section}")

    # 正向代回驗證（三步驗證之第二步）
    if section == "microstrip":
        chk = microstrip_z0(res["w_mm"], h, t, er)
    elif section == "embedded_microstrip":
        chk = embedded_microstrip_z0(res["w_mm"], h, h1, t, er)
    elif section == "stripline":
        chk = stripline_z0(res["w_mm"], h, t, er)
    elif section == "asymmetric_stripline":
        chk = asymmetric_stripline_z0(res["w_mm"], h, h1, t, er)
    elif section == "broadside_stripline":
        chk = broadside_stripline_z0(res["w_mm"], h, h1, t, er)
    elif section == "diff_microstrip":
        chk = diff_microstrip_zd(res["w_mm"], d, h, t, er)
    elif section == "diff_stripline":
        chk = diff_stripline_zd(res["w_mm"], d, h, t, er)
    elif section == "coax":
        chk = coax_z0(res["di_mm"], w, er)
    elif section == "parallel_wire":
        chk = parallel_wire_z0(res["s_mm"], d, er)
    elif section == "cpw":
        chk = cpw_z0(res["s_mm"], w, h if h else np.inf, er, t)[0]
    elif section == "diff_stripline_conformal":
        chk = diff_stripline_conformal(res["w_mm"], d, b, er)["Z_diff"]
    res["forward_check"] = chk
    res["residual_pct"] = abs(chk - target) / target * 100
    return res
