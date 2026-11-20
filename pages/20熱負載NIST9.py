import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from 量傳線設計.核心.熱負載NIST9 import (
    list_materials, get_material, k_curve, integral_curve, compare_materials,
    calculate_thermal_load, sweep_parameter, sweep_materials_heatload,
)

st.set_page_config(page_title="熱負載 NIST9 模擬", layout="wide")
st.title("熱負載 NIST 9 係數模擬 (新平台整合)")
st.caption("共用核心: src/量傳線設計/核心/熱負載NIST9.py；資料/引擎: ~/.opencode/skills/heatload-coff-nist/scripts (coeff_data.py, thermal_load.py)。polyfit 可靠度: docs/polyfit_可靠度驗證.md")

mats_all = list_materials()
k_mats = [m["name"] for m in mats_all if m.get("category") == "k(T)" and m.get("coeffs") is not None]
if not k_mats:
    k_mats = [m["name"] for m in mats_all if m.get("category") == "k(T)"]
all_k = [m["name"] for m in mats_all if m.get("category") == "k(T)"]

with st.sidebar:
    st.subheader("材料與範圍")
    mat = st.selectbox("材料 κ(T)", all_k, index=all_k.index("Polyimide (Kapton)") if "Polyimide (Kapton)" in all_k else 0)
    info = get_material(mat)
    st.write({"equation_type": info.get("equation_type"), "T_low": info.get("t_low"), "T_high": info.get("t_high")})
    st.caption(info.get("source", ""))
    if info.get("coeffs") is None:
        st.warning("無固定 9 係數 (runtime 擬合/未提供)，不可直接用於 NIST9 計算。")
    extrap = st.checkbox("低溫外推 k~T^alpha (T<T_low)", value=False)
    st.subheader("幾何/溫區/激勵")
    stages_s = st.text_input("溫區 stages (K, 高→低)", "300,50,4,1,0.1,0.01")
    width = st.number_input("width", value=0.15, format="%.6f")
    thickness = st.number_input("thickness", value=1.0, format="%.6f")
    area_units = st.selectbox("面積單位", ["mil", "m"], index=0)
    length_s = st.text_input("length (m, 逗號/單值)", "0.3")
    pin = st.number_input("P_in (W)", value=1e-6, format="%.3e")
    atten_s = st.text_input("attenuation dB (逗號/單值)", "0,3,6,6,6")


def pf(s):
    return [float(x.strip()) for x in s.split(",") if x.strip()]


stages = pf(stages_s)
lengths = pf(length_s)
attens = pf(atten_s)

tabs = st.tabs(["κ(T) 曲線", "∫κdT 曲線", "材料比較", "多溫區穩態熱負載", "參數掃描模擬"])

with tabs[0]:
    if info.get("coeffs") is None:
        st.error("此材料無固定係數。請選擇具 9 係數的材料。")
    else:
        tmin = st.number_input("T_min (K)", value=float(info.get("t_low") or 1.0), key="tmin")
        tmax = st.number_input("T_max (K)", value=float(info.get("t_high") or 300.0), key="tmax")
        cur = k_curve(material=mat, t_min=tmin, t_max=tmax, n=400, extrapolate=extrap)
        fig, ax = plt.subplots()
        ax.loglog(cur["T"], cur["k"])
        ax.set_xlabel("T (K)"); ax.set_ylabel("κ(T) [W/m/K]"); ax.grid(True, which="both", alpha=0.3)
        ax.set_title(mat)
        st.pyplot(fig)

with tabs[1]:
    if info.get("coeffs") is None:
        st.error("此材料無固定係數。")
    else:
        tc = st.number_input("T_cold (K)", value=min(stages) if stages else 4.0, key="itc")
        th = st.number_input("T_hot (K)", value=max(stages) if stages else 300.0, key="ith")
        ic = integral_curve(material=mat, t_cold=tc, t_hot=th, n=300, extrapolate=extrap)
        st.metric(f"∫ κ dT ({tc}→{th} K)", f"{ic['integral'][-1]:.6e} W/m")
        fig, ax = plt.subplots()
        ax.semilogx(ic["T"], ic["integral"])
        ax.set_xlabel("T (K)"); ax.set_ylabel("∫ κ(T)dT (W/m)"); ax.grid(True, which="both", alpha=0.3)
        st.pyplot(fig)

with tabs[2]:
    defaults = [x for x in ["Copper (OFHC) RRR=100", "Stainless Steel 304 (UNS S30400)", "Polyimide (Kapton)", "Teflon (PTFE)"] if x in k_mats]
    if not defaults:
        defaults = k_mats[:4]
    sel = st.multiselect("比較材料", k_mats, default=defaults)
    cmin = st.number_input("比較 T_min", value=4.0, key="cmin")
    cmax = st.number_input("比較 T_max", value=300.0, key="cmax")
    if sel:
        comp = compare_materials(sel, t_min=cmin, t_max=cmax, n=300, extrapolate=extrap)
        fig, ax = plt.subplots()
        errs = []
        for c in comp:
            if "error" in c:
                errs.append(c)
                continue
            ax.loglog(c["T"], c["k"], label=c["material"])
        ax.legend(fontsize=8); ax.grid(True, which="both", alpha=0.3)
        ax.set_xlabel("T (K)"); ax.set_ylabel("κ(T)")
        st.pyplot(fig)
        if errs:
            st.dataframe(pd.DataFrame(errs))

with tabs[3]:
    st.markdown(r"$Q_{solid}=\sum (A/L)\int_{T_c}^{T_h}\kappa(T)dT$, $Q_{rf}=\sum P_{in}(1-10^{-\alpha/10})$")
    geom = {"width": width, "thickness": thickness, "length": lengths[0] if len(lengths) == 1 else lengths, "area_units": area_units}
    use_mat = mat if info.get("coeffs") is not None else (k_mats[0] if k_mats else mat)
    if use_mat != mat:
        st.info(f"計算材料改用: {use_mat}")
    try:
        res = calculate_thermal_load(material=use_mat, stages=stages, geometry=geom,
                                     attenuation=attens[0] if len(attens) == 1 else attens,
                                     pin=pin, extrapolate_low_t=extrap)
        c1, c2, c3 = st.columns(3)
        c1.metric("total_load (W)", f"{res['total_load_w']:.4e}")
        c2.metric("solid_conduction (W)", f"{res['solid_conduction_w']:.4e}")
        c3.metric("attenuator_dissipation (W)", f"{res['attenuator_dissipation_w']:.4e}")
        df = pd.DataFrame(res["stages"])
        st.dataframe(df, use_container_width=True)
        fig, ax = plt.subplots()
        labels = [f"{d['T_hot_K']}→{d['T_cold_K']}K" for d in res["stages"]]
        ax.bar(labels, df["solid_conduction_w"], label="Q_solid")
        ax.bar(labels, df["attenuator_dissipation_w"], bottom=df["solid_conduction_w"], label="Q_rf")
        ax.set_ylabel("W"); ax.set_yscale("log"); ax.legend(); ax.grid(True, alpha=0.3, axis="y")
        st.pyplot(fig)
        with st.expander("完整結果 JSON"):
            st.json({k: v for k, v in res.items() if k != "stages"})
    except Exception as e:
        st.error(str(e))

with tabs[4]:
    base_geom = {"width": width, "thickness": thickness, "length": lengths[0] if lengths else 0.3, "area_units": area_units}
    base_mat = mat if info.get("coeffs") is not None else (k_mats[0] if k_mats else mat)
    base = {"material": base_mat, "stages": stages, "geometry": base_geom,
            "attenuation": attens[0] if len(attens) == 1 else attens, "pin": pin, "extrapolate_low_t": extrap}
    mode = st.radio("掃描類型", ["參數掃描", "材料掃描"], horizontal=True)
    if mode == "參數掃描":
        param = st.selectbox("參數", ["length", "width", "thickness", "pin", "attenuation"])
        vs = st.text_input("值列表 (逗號)", "0.1,0.2,0.3,0.5,1.0")
        if st.button("執行參數掃描"):
            vals = pf(vs)
            res = sweep_parameter(base, param, vals)
            rows = [{param: r.get("_sweep_value"), "total_load_w": r.get("total_load_w"),
                     "solid_conduction_w": r.get("solid_conduction_w"),
                     "attenuator_dissipation_w": r.get("attenuator_dissipation_w"), "error": r.get("error")} for r in res]
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
            if "total_load_w" in df and df["total_load_w"].notna().any():
                fig, ax = plt.subplots()
                ax.plot(df[param], df["total_load_w"], "o-", label="total")
                if "solid_conduction_w" in df:
                    ax.plot(df[param], df["solid_conduction_w"], "s--", label="solid")
                ax.set_xlabel(param); ax.set_ylabel("W"); ax.grid(True, alpha=0.3); ax.legend()
                st.pyplot(fig)
    else:
        selm = st.multiselect("掃描材料", k_mats, default=defaults, key="swm")
        if st.button("執行材料掃描"):
            res = sweep_materials_heatload(selm, stages=stages, geometry=base_geom,
                                           attenuation=attens[0] if len(attens) == 1 else attens,
                                           pin=pin, extrapolate_low_t=extrap)
            rows = [{"material": r.get("_sweep_material", r.get("material")),
                     "total_load_w": r.get("total_load_w"), "solid_conduction_w": r.get("solid_conduction_w"),
                     "attenuator_dissipation_w": r.get("attenuator_dissipation_w"), "error": r.get("error")} for r in res]
            df = pd.DataFrame(rows).sort_values("total_load_w", na_position="last")
            st.dataframe(df, use_container_width=True)
            if df["total_load_w"].notna().any():
                fig, ax = plt.subplots()
                ax.barh(df["material"].astype(str), df["total_load_w"])
                ax.set_xscale("log"); ax.set_xlabel("total_load_w (W)"); ax.grid(True, alpha=0.3, axis="x")
                st.pyplot(fig)

with st.expander("說明與限制"):
    st.markdown(r'''
- **NIST 9 係數**: log-polynomial $\log_{10}\kappa=\sum_{n=0}^{8}c_n(\log_{10}T)^n$ 或 OFHC Cu rational；係數/來源/範圍來自 `coeff_data.py` (54 材料)，不重擬合、不編造。
- **熱負載**: $Q_{solid}=\sum_i (A/L_i)\int_{T_{c,i}}^{T_{h,i}}\kappa(T)dT$ (log-spaced 梯形)；$Q_{rf}=\sum_i P_{in}(1-10^{-\alpha_i/10})$。
- **範圍外**: 預設回傳 0；可選低溫 $k(T)\sim T^\alpha$ 外推 (可能高估，須保守解讀)。
- **NbTi (Cri/oFlex 3)**: 來源無固定 9 係數 (runtime polyfit, 受 noise/seed 影響)，`coeff_data` 不提供固定值；不可當固定 NIST 係數。
- **polyfit 可靠度**: 見 `docs/polyfit_可靠度驗證.md` 與頁面 `31nist9_polyfit_可靠度` / `scripts/validate_polyfit_reliability.py`。
''')
