# ui/formula_view.py
import streamlit as st
from core.formula_trace import trace_model, trace_row

def render_formula(results, nominal_z):
    st.subheader("公式追溯")
    st.code(trace_model())
    for name, rows in results.items():
        with st.expander(f"{name} 公式"):
            for r in rows:
                st.text(trace_row(name, r["offset"], r.get(name, 0), r["Zdiff"], r["rel_%"], nominal_z))
