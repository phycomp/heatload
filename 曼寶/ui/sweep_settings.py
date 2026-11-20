from streamlit import columns, selectbox, subheader
# ui/sweep_settings.py
# import streamlit as st

def render_sweep():
    subheader("擾動量與掃描點數")
    c1, c2, c3 = columns(3)
    height_delta = c1.number_input("Height Δ", value=0.3)
    width_delta = c2.number_input("Width Δ", value=0.2)
    taper_delta = c3.number_input("Taper Δ", value=0.1)
    sep_delta = c1.number_input("Separation Δ", value=0.02)
    trace_h_delta = c2.number_input("traceHeightΔ", value=.05)
    er_delta = c3.number_input("Er Δ", value=0.15)
    n_points = selectbox("掃描點數", [3, 5, 7], index=1)
    return {
        "height_delta": height_delta,
        "width_delta": width_delta,
        "taper_delta": taper_delta,
        "sep_delta": sep_delta,
        "trace_h_delta": trace_h_delta,
        "er_delta": er_delta,
        "n_points": n_points,
    }
