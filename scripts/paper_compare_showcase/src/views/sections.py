"""Sections view (same-source, radio to switch version)."""

from __future__ import annotations
import streamlit as st


def render(bundle: dict) -> None:
    data = bundle.get("data") or {}
    st.header("章節 Sections")
    st.caption("以 radio 切換版本，顯示各版章節標題與字元數（同源）。")
    sections = data.get("sections", {})
    version = st.radio(
        "版本 Version",
        ["Nature-style", "Compiled"],
        index=0,
        horizontal=True,
        key="sections_version",
    )
    key = "nature" if version == "Nature-style" else "compiled"
    rows = sections.get(key, [])
    if not rows:
        st.warning("無章節資料。")
        return
    st.write(f"**{version}** — 共 {len(rows)} 章")
    for s in rows:
        st.write(f"- {s.get('title', '?')} ({s.get('chars', 0)} chars)")
