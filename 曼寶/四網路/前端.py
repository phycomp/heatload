## 5. `frontend/streamlit_app.py`

import numpy as np
import requests
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="智能阻抗平台", layout="wide")
API = st.sidebar.text_input("Backend URL", "http://localhost:8000")

plt.rcParams["font.sans-serif"] = ["Noto Sans CJK TC", "Microsoft JhengHei",
                                   "PingFang TC", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False


def smith_chart(gammas, zl=None, z0=50.0):
    """Blank Smith chart + plotted reflection-coefficient trajectory."""
    fig, ax = plt.subplots(figsize=(6, 6))
    th = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(th), np.sin(th), color="gray", lw=0.8)
    for r in [0.2, 0.5, 1, 2, 5]:
        c = r / (1 + r)
        rad = 1 / (1 + r)
        ax.add_patch(plt.Circle((c, 0), rad, fill=False, color="lightgray", lw=0.5))
    ax.add_patch(plt.Circle((-0.5, 0), 0.5, fill=False, color="lightgray", lw=0.5))
    ax.add_patch(plt.Circle((-2, 0), 2, fill=False, color="lightgray", lw=0.5))
    if zl is not None:
        g = (zl - z0) / (zl + z0)
        ax.plot([g.real], [g.imag], "rx", ms=12, mew=2, label="load")
    if gammas is not None:
        ax.plot(gammas.real, gammas.imag, "b.-", ms=3, lw=1, label="S11(f)")
    ax.set_aspect("equal"); ax.legend()
    ax.set_title("Smith Chart"); ax.axis("off")
    return fig


def s11_plot(freqs_ghz, s11):
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(freqs_ghz, 20 * np.log10(np.abs(s11) + 1e-12))
    ax.set_xlabel("Frequency (GHz)"); ax.set_ylabel("|S11| (dB)")
    ax.grid(True, alpha=0.3)
    return fig


st.title("智能阻抗平台")

text = st.text_input("自然語言輸入（中英皆可）",
                     "FR-4 1.6mm 1oz 做 50Ω 微帶線 要多寬")
if st.button("解析"):
    r = requests.post(f"{API}/api/parse", json={"text": text}).json()
    st.session_state["p"] = r
p = st.session_state.get("p", {})

c1, c2, c3 = st.columns(3)
structure = c1.selectbox("結構", ["microstrip", "stripline", "cpwg", "diffpair"],
                         index=["microstrip", "stripline", "cpwg", "diffpair"]
                         .index(p.get("structure", "microstrip")))
er = c2.number_input("εr", value=float(p.get("er", 4.2)))
h = c3.number_input("h (mm)", value=float(p.get("h_mm", 1.6)))
c4, c5, c6 = st.columns(3)
t = c4.number_input("t (mm)", value=float(p.get("t_mm", 0.035)))
z0 = c5.number_input("Z0 (Ω)", value=float(p.get("z0", 50.0)))
s = c6.number_input("gap s (mm)", value=float(p.get("s_mm", 0.2)))

if st.button("計算阻抗"):
    ep = {"microstrip": "design/microstrip", "stripline": "design/stripline",
          "cpwg": "design/cpwg", "diffpair": "design/diffpair"}[structure]
    r = requests.post(f"{API}/api/{ep}",
                      json={"z0": z0, "h": h, "t": t, "er": er, "s": s}).json()
    st.table(r)

st.divider()
st.subheader("阻抗匹配")
m1, m2, m3, m4 = st.columns(4)
mkind = m1.selectbox("網路", ["l", "stub", "pi", "t"])
zl_re = m2.number_input("ZL 實部", value=float(p.get("zl_re", 25.0)))
zl_im = m3.number_input("ZL 虛部", value=float(p.get("zl_im", 0.0)))
fghz = m4.number_input("頻率 (GHz)", value=float(p.get("f_ghz", 2.4)))

if st.button("設計匹配網路"):
    if mkind == "l":
        r = requests.post(f"{API}/api/match/l",
                          json={"zl_re": zl_re, "zl_im": zl_im,
                                "z0": z0, "f_ghz": fghz}).json()
        st.json(r)
        # 以第一組解畫 S11 掃頻（低通解：串 L 並 C）
        f = np.linspace(0.5 * fghz, 2 * fghz, 200) * 1e9
        w = 2 * np.pi * f
        best = r[0]
        xs = best["series"]["X_ohm"]
        xp = best["shunt"]["X_ohm"]
        zin = 1j * xs * (w / (2 * np.pi * fghz * 1e9)) + \
            zl_re * 1j * xp / (zl_re + 1j * xp) * (fghz * 1e9 / f)
        s11 = (zin - z0) / (zin + z0)
        st.pyplot(smith_chart(s11, zl=complex(zl_re, zl_im), z0=z0))
        st.pyplot(s11_plot(f / 1e9, s11))
    else:
        r = requests.post(f"{API}/api/match/{mkind}",
                          json={"zl_re": zl_re, "zl_im": zl_im, "z0": z0,
                                "f_ghz": fghz}).json()
        st.json(r)
