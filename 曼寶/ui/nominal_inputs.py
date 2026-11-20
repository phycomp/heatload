from streamlit import columns, subheader
# ui/nominal_inputs.py
import streamlit as st

def render_nominal(preset, unit):
    subheader("Nominal 設計參數")
    c1, c2, c3 = columns(3)
    H1 = c1.number_input(f"H1 ({unit})", value=float(preset["H1"]))
    Er1 = c2.number_input("Er1", value=float(preset["Er1"]))
    W1 = c3.number_input(f"W1 ({unit})", value=float(preset["W1"]))
    W2 = c1.number_input(f"W2 ({unit})", value=float(preset["W2"]))
    S1 = c2.number_input(f"S1 ({unit})", value=float(preset["S1"]))
    T1 = c3.number_input(f"T1 ({unit})", value=float(preset["T1"]))
    return {"H1": H1, "Er1": Er1, "W1": W1, "W2": W2, "S1": S1, "T1": T1}
