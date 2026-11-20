"""Axis comparison view (same-source)."""

from __future__ import annotations
import streamlit as st


def render(bundle: dict) -> None:
    data = bundle.get("data") or {}
    st.header("軸對照 Axis comparison")
    st.caption("七個比較軸，逐列並排；全部取自 viz_data.json。")
    rows = data.get("axis_comparison", [])
    if not rows:
        st.warning("無軸對照資料。")
        return
    c1, c2, c3 = st.columns([2, 4, 4])
    with c1:
        st.subheader("軸")
        for r in rows:
            st.write(f"**{r.get('axis', '?')}**")
    with c2:
        st.subheader("Nature-style")
        for r in rows:
            st.write(r.get("nature", "—"))
    with c3:
        st.subheader("Compiled")
        for r in rows:
            st.write(r.get("compiled", "—"))
    with st.expander("比較邊界 (boundary)", expanded=False):
        st.caption(
            "僅描述結構、主張與邊界差異，不比較内容品質；兩版同源（Nature-style 由 compiled material 寫成）。"
        )
