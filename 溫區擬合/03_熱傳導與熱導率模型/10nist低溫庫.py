"""NIST 9 係數低溫材料庫 (heatload-coff-nist 引擎)
- 單一真相來源: ~/.opencode/skills/heatload-coff-nist/scripts/{coeff_data,thermal_load}.py (D4=A)
- 54 材料、9 係數 c0..c8、來源/有效範圍/方程型式
- κ(T)、∫κdT 曲線、材料比較、簡易多溫區熱負載估算
(原始版本備份: 10nist低溫庫_legacy.py, D5=A)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import _nist9_共用 as n9  # noqa: E402

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="NIST9 低溫材料庫", layout="wide")
st.title("NIST 9 係數低溫材料庫與熱導計算")
st.caption("引擎: heatload-coff-nist (coeff_data.py 54 材料, thermal_load.py). 原始頁面: 10nist低溫庫_legacy.py")

mats_all = n9.list_materials()
mat_names = [m["name"] for m in mats_all]
k_mats = [m["name"] for m in mats_all if m.get("category") == "k(T)"]
if not k_mats:
    k_mats = mat_names

with st.sidebar:
    st.subheader("材料")
    category = st.selectbox("類別", ["全部", "k(T)", "rho(T)", "Metal", "Nonmetal"], index=0)
    names = mat_names
    if category == "k(T)":
        names = [m["name"] for m in mats_all if m.get("category") == "k(T)"]
    elif category == "rho(T)":
        names = [m["name"] for m in mats_all if m.get("category") == "rho(T)"]
    elif category == "Metal":
        names = [m["name"] for m in mats_all if m.get("category") == "Metal"]
    elif category == "Nonmetal":
        names = [m["name"] for m in mats_all if m.get("category") == "Nonmetal"]
    if not names:
        names = mat_names
    mat = st.selectbox("材料", names, index=0)
    extrap = st.checkbox("低溫外推 (T < T_low, k~T^alpha)", value=False)

m = n9.get_material(mat)
tabs = st.tabs(["材料/9係數", "κ(T) 曲線", "積分 ∫κdT", "材料比較", "熱負載估算"])

with tabs[0]:
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("屬性")
        st.json({
            "name": m.get("name", mat),
            "category": m.get("category"),
            "equation_type": m.get("equation_type"),
            "t_low_K": m.get("t_low"),
            "t_high_K": m.get("t_high"),
        })
        st.caption(m.get("source", ""))
        if m.get("note"):
            st.info(m.get("note"))
    with c2:
        st.subheader("9 係數 c0..c8")
        coeffs = m.get("coeffs")
        if coeffs is None:
            st.warning("此材料無固定 9 係數（來源標示 runtime 擬合/不可編造）。請以明確擬合條件或實測資料另行提供 coeffs。")
        else:
            dfc = pd.DataFrame({"coeff": [f"c{i}" for i in range(9)], "value": coeffs})
            st.dataframe(dfc, use_container_width=True)
            st.code(", ".join(f"{v:.9g}" for v in coeffs))

with tabs[1]:
    if m.get("coeffs") is None:
        st.warning("無固定係數可計算。")
    else:
        lo = float(m.get("t_low") or 1.0)
        hi = float(m.get("t_high") or 300.0)
        tmin = st.number_input("T_min (K)", value=lo, key="k_tmin")
        tmax = st.number_input("T_max (K)", value=hi, key="k_tmax")
        logx = st.checkbox("log X", value=True, key="k_lx")
        logy = st.checkbox("log Y", value=True, key="k_ly")
        cur = n9.k_curve(material=mat, t_min=tmin, t_max=tmax, n=400, extrapolate=extrap)
        fig, ax = plt.subplots()
        if logx and logy:
            ax.loglog(cur["T"], cur["k"])
        elif logx:
            ax.semilogx(cur["T"], cur["k"])
        elif logy:
            ax.semilogy(cur["T"], cur["k"])
        else:
            ax.plot(cur["T"], cur["k"])
        ax.set_xlabel("T (K)"); ax.set_ylabel("κ(T) [W/m/K]")
        ax.grid(True, which="both", alpha=0.3); ax.set_title(mat)
        st.pyplot(fig)

with tabs[2]:
    if m.get("coeffs") is None:
        st.warning("無固定係數可計算。")
    else:
        tc = st.number_input("T_cold (K)", value=float(m.get("t_low") or 4.0), key="i_tc")
        th = st.number_input("T_hot (K)", value=float(m.get("t_high") or 300.0), key="i_th")
        if th > tc:
            ic = n9.integral_curve(material=mat, t_cold=tc, t_hot=th, n=300, extrapolate=extrap)
            st.metric(f"∫ κ dT ({tc}→{th} K) [W/m]", f"{ic['integral'][-1]:.6e}")
            fig, ax = plt.subplots()
            ax.semilogx(ic["T"], ic["integral"])
            ax.set_xlabel("T (K)"); ax.set_ylabel("累積 ∫ κ(T)dT (W/m)")
            ax.grid(True, which="both", alpha=0.3)
            st.pyplot(fig)
        else:
            st.error("T_hot 必須 > T_cold")

with tabs[3]:
    defaults = [x for x in ["Copper (OFHC) RRR=100", "Stainless Steel 304 (UNS S30400)", "Polyimide (Kapton)", "Teflon (PTFE)"] if x in k_mats]
    if not defaults:
        defaults = k_mats[:4]
    sel = st.multiselect("比較材料 (k(T))", k_mats, default=defaults)
    cmin = st.number_input("T_min (K)", value=4.0, key="cmin")
    cmax = st.number_input("T_max (K)", value=300.0, key="cmax")
    if sel:
        comp = n9.compare_materials(sel, t_min=cmin, t_max=cmax, n=300, extrapolate=extrap)
        fig, ax = plt.subplots()
        for c in comp:
            if "error" in c:
                st.warning(f"{c['material']}: {c['error']}")
                continue
            ax.loglog(c["T"], c["k"], label=c["material"])
        ax.legend(fontsize=8); ax.grid(True, which="both", alpha=0.3)
        ax.set_xlabel("T (K)"); ax.set_ylabel("κ(T)")
        st.pyplot(fig)

with tabs[4]:
    st.markdown("多溫區穩態: $Q_{solid}=\\sum (A/L)\\int\\kappa dT$ + $Q_{rf}=\\sum P_{in}(1-10^{-\\alpha/10})$")
    if m.get("coeffs") is None and m.get("category") == "k(T)":
        st.warning("此材料無固定係數，無法直接計算。")
    else:
        calc_mat = mat if m.get("category") == "k(T)" and m.get("coeffs") is not None else ("Polyimide (Kapton)" if "Polyimide (Kapton)" in k_mats else k_mats[0])
        if calc_mat != mat:
            st.info(f"熱負載計算改用 κ(T) 材料: {calc_mat}")
        stages_s = st.text_input("溫區 (K, 高->低)", "300,50,4,1,0.1,0.01")
        width = st.number_input("寬 width", value=0.15, format="%.6f")
        thickness = st.number_input("厚 thickness", value=1.0, format="%.6f")
        area_units = st.selectbox("面積單位", ["mil", "m"], index=0)
        length_s = st.text_input("各段長度 (m)", "0.3")
        pin = st.number_input("P_in (W)", value=1e-6, format="%.3e")
        atten_s = st.text_input("各段衰減 dB", "0,3,6,6,6")
        def pf(s):
            return [float(x.strip()) for x in s.split(",") if x.strip()]
        try:
            res = n9.calculate_thermal_load(material=calc_mat, stages=pf(stages_s),
                                            geometry={"width": width, "thickness": thickness,
                                                      "length": pf(length_s)[0] if len(pf(length_s))==1 else pf(length_s),
                                                      "area_units": area_units},
                                            attenuation=pf(atten_s)[0] if len(pf(atten_s))==1 else pf(atten_s),
                                            pin=pin, extrapolate_low_t=extrap)
            c1, c2, c3 = st.columns(3)
            c1.metric("total (W)", f"{res['total_load_w']:.4e}")
            c2.metric("solid (W)", f"{res['solid_conduction_w']:.4e}")
            c3.metric("rf/atten (W)", f"{res['attenuator_dissipation_w']:.4e}")
            st.dataframe(pd.DataFrame(res["stages"]))
        except Exception as e:
            st.error(str(e))
