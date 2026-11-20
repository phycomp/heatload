import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from 量傳線設計.核心.熱負載 import 熱負載曲線, 回推溫區長度
from 量傳線設計.核心.熱負載NIST9 import (
    list_materials,
    get_material,
    k_curve,
    integral_curve,
    compare_materials,
    calculate_thermal_load,
    sweep_parameter,
)

st.set_page_config(page_title="熱負載", layout="wide")
st.title("熱負載")

with st.sidebar:
    spec_name = st.selectbox("規格", ["CF3", "FPC", "Uleam1"], index=0)
    st.caption(f"規格: {spec_name}")
    st.markdown("---")
    st.caption("NIST 9 係數模擬: 來源 heatload-coff-nist (coeff_data/thermal_load)")

tab1, tab2, tab3 = st.tabs(["熱負載曲線(原)", "回推溫區長度(原)", "NIST 9 係數模擬"])
with tab1:
    f01 = st.number_input("f01 (GHz)", value=5.5) * 1e9
    res = 熱負載曲線(f01=f01)
    fig, ax = plt.subplots()
    ax.plot(res["T"], res["pop_1"], label="pop_1")
    ax.plot(res["T"], res["n_th"], label="n_th")
    ax.set_xlabel("T (K)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

with tab2:
    k = st.number_input("熱導率 k", value=0.1)
    A = st.number_input("截面積 A (m^2)", value=1e-6, format="%.2e")
    dT = st.number_input("溫差 (K)", value=50.0)
    Q = st.number_input("熱負載 Q (W)", value=1e-6, format="%.2e")
    L = 回推溫區長度(熱導率=k, 截面積=A, 溫差=dT, 熱負載_W=Q)
    st.metric("回推長度 L (m)", f"{L:.4f}")

with tab3:
    mats_all = list_materials()
    k_mats = [
        m["name"]
        for m in mats_all
        if m.get("category") == "k(T)" and m.get("coeffs") is not None
    ]
    c1, c2 = st.columns(2)
    with c1:
        mat = st.selectbox(
            "材料 κ(T)",
            k_mats,
            index=k_mats.index("Polyimide (Kapton)")
            if "Polyimide (Kapton)" in k_mats
            else 0,
        )
        stages_s = st.text_input(
            "溫區 stages (K, 高→低)", "300,50,4,1,0.1,0.01", key="p4_st"
        )
        length_s = st.text_input("length (m)", "0.3", key="p4_len")
        pin = st.number_input("P_in (W)", value=1e-6, format="%.3e", key="p4_pin")
        atten_s = st.text_input("attenuation dB", "0,3,6,6,6", key="p4_att")
    with c2:
        info = get_material(mat)
        st.write(
            {
                "equation_type": info.get("equation_type"),
                "T_low": info.get("t_low"),
                "T_high": info.get("t_high"),
            }
        )
        width = st.number_input("width", value=0.15, format="%.6f", key="p4_w")
        thickness = st.number_input("thickness", value=1.0, format="%.6f", key="p4_t")
        area_units = st.selectbox("面積單位", ["mil", "m"], index=0, key="p4_au")
        extrap = st.checkbox("低溫外推", value=False, key="p4_ex")

    def _pf(s):
        return [float(x.strip()) for x in s.split(",") if x.strip()]

    stages = _pf(stages_s)
    lengths = _pf(length_s)
    attens = _pf(atten_s)
    geom = {
        "width": width,
        "thickness": thickness,
        "length": lengths[0] if len(lengths) == 1 else lengths,
        "area_units": area_units,
    }
    try:
        res = calculate_thermal_load(
            material=mat,
            stages=stages,
            geometry=geom,
            attenuation=attens[0] if len(attens) == 1 else attens,
            pin=pin,
            extrapolate_low_t=extrap,
        )
        m1, m2, m3 = st.columns(3)
        m1.metric("total (W)", f"{res['total_load_w']:.4e}")
        m2.metric("solid (W)", f"{res['solid_conduction_w']:.4e}")
        m3.metric("atten/rf (W)", f"{res['attenuator_dissipation_w']:.4e}")
        df = pd.DataFrame(res["stages"])
        st.dataframe(df, use_container_width=True)
        cur = k_curve(
            material=mat,
            t_min=min(stages),
            t_max=max(stages),
            n=200,
            extrapolate=extrap,
        )
        fig, ax = plt.subplots()
        ax.loglog(cur["T"], cur["k"])
        ax.set_xlabel("T (K)")
        ax.set_ylabel("κ(T) [W/m/K]")
        ax.grid(True, which="both", alpha=0.3)
        st.pyplot(fig)
    except Exception as e:
        st.error(str(e))
    st.caption(
        "完整模擬/比較/掃描見: pages/20熱負載NIST9.py；polyfit 可靠度見 docs/polyfit_可靠度驗證.md"
    )
