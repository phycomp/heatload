"""Statistics view (same-source)."""

from __future__ import annotations
import streamlit as st


def render(bundle: dict) -> None:
    data = bundle.get("data") or {}
    st.header("指標 Statistics")
    st.caption("兩版量化指標並排；單選以 radio 選擇指標。")
    stats = data.get("stats", {})
    nat = stats.get("nature", {})
    comp = stats.get("compiled", {})
    metrics = ["chars", "words", "figure_mentions", "table_rows", "math_tokens"]
    metric = st.radio(
        "指標 Metric", metrics, index=0, horizontal=True, key="stats_metric"
    )
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Nature-style")
        st.write(nat.get(metric, "N/A"))
    with c2:
        st.subheader("Compiled")
        st.write(comp.get(metric, "N/A"))
    with st.expander("全部指標 (all metrics)", expanded=False):
        st.table(
            {
                "metric": metrics,
                "nature": [nat.get(m, "N/A") for m in metrics],
                "compiled": [comp.get(m, "N/A") for m in metrics],
            }
        )
