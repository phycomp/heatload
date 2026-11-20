# ui/results_table.py
import streamlit as st
import pandas as pd

def render_results(results, summary):
    st.subheader("掃描結果")
    for name, rows in results.items():
        st.markdown(f"**{name}**")
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    st.subheader("Summary")
    st.dataframe(pd.DataFrame(summary), use_container_width=True)
