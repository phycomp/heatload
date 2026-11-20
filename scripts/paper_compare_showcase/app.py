#!/usr/bin/env python3
"""Streamlit showcase: Nature-style vs compiled paper comparison.

Follows topic-viz distill-showcase norms:
- Single app.py entry point; st.set_page_config called once (here).
- src/views/ function modules; subtopics in sidebar via st.radio(horizontal=True).
- Same-source: docs/paper_compare_viz_data.json; graceful degradation on missing data.
- Four mandatory norms: selectbox->radio, expander+with, use_container_width->width,
  set_page_config once.

Run: cd ~/量傳線 && streamlit run scripts/paper_compare_showcase/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = APP_DIR.parent
for p in (str(APP_DIR), str(SCRIPTS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

# st.set_page_config MUST be called once, before any other Streamlit call.
st.set_page_config(
    page_title="Paper Compare — Nature-style vs compiled",
    layout="wide",
)

from src.data import load_bundle, show_degradation  # noqa: E402
from src.views import axis_compare, overview, sections, stats  # noqa: E402

SUBTOPICS = [
    "總覽 Overview",
    "軸對照 Axis comparison",
    "章節 Sections",
    "指標 Statistics",
]


def main() -> None:
    st.title("論文版本比較 — Nature-style vs compiled")
    st.caption(
        "同源比較（唯讀兩份論文 → viz_data.json）；只比較結構/主張/邊界，不判定優劣。"
        " topic-viz Format F；離線 HTML 規則已移除，展示採 Streamlit + Excel。"
    )

    bundle = load_bundle()
    data = bundle.get("data")

    # Sidebar: subtopics (radio, horizontal=True)
    st.sidebar.header("子主題 Subtopics")
    selected = st.sidebar.radio(
        "選擇檢視", SUBTOPICS, index=0, horizontal=True, key="subtopic_radio"
    )

    with st.sidebar.expander("來源狀態 (same-source)", expanded=False):
        paths = bundle.get("paths", {})
        for label, p in paths.items():
            st.caption(f"{label}: `{'OK' if p and p.exists() else 'missing'}`")
        errs = bundle.get("load_errors", {})
        if errs:
            st.error(f"讀取錯誤: {errs}")

    if not data:
        st.error("找不到或無法讀取 `docs/paper_compare_viz_data.json`。")
        st.info("請先執行：`cd ~/量傳線 && python3 /tmp/opencode/build_compare_viz.py`")
        show_degradation(bundle)
        return

    if selected == "總覽 Overview":
        overview.render(bundle)
    elif selected == "軸對照 Axis comparison":
        axis_compare.render(bundle)
    elif selected == "章節 Sections":
        sections.render(bundle)
    elif selected == "指標 Statistics":
        stats.render(bundle)
    else:
        overview.render(bundle)

    show_degradation(bundle)


if __name__ == "__main__":
    main()
