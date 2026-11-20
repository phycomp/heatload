"""Overview view (same-source)."""

from __future__ import annotations
import streamlit as st


def render(bundle: dict) -> None:
    data = bundle.get("data") or {}
    st.header("總覽 Overview")
    st.caption("兩版論文同源比較；資料取自 viz_data.json，不判定優劣。")
    stats = data.get("stats", {})
    nat = stats.get("nature", {})
    comp = stats.get("compiled", {})
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Nature-style")
        st.write(f"- 字元: {nat.get('chars', 'N/A')}")
        st.write(f"- 字數: {nat.get('words', 'N/A')}")
        st.write(f"- 章節: {len(data.get('sections', {}).get('nature', []))}")
    with c2:
        st.subheader("Compiled final")
        st.write(f"- 字元: {comp.get('chars', 'N/A')}")
        st.write(f"- 字數: {comp.get('words', 'N/A')}")
        st.write(f"- 章節: {len(data.get('sections', {}).get('compiled', []))}")
    with st.expander("同源說明 (same-source note)", expanded=False):
        st.caption(data.get("evidence_note", "_(no note)_"))
    src = data.get("sources", {})
    with st.expander("來源路徑 (sources)", expanded=False):
        st.write(f"- nature: `{src.get('nature', 'N/A')}`")
        st.write(f"- compiled: `{src.get('compiled', 'N/A')}`")
