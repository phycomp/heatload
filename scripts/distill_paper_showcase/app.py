#!/usr/bin/env python3
"""Distill-showcase-style Streamlit app for compiled heatload-distill paper.

Follows distill-showcase writing norms:
- Single app.py entry point
- st.set_page_config called once (here)
- src/views/ function modules
- Subtopics in sidebar (radio, horizontal=True)

Displays compiled paper: 摘要 (abstract), 章節 (chapters), 圖表 (charts),
plus citations/sources, consolidated, overview. Same-source, evidence-bounded
(D4=A; no refit, no invented coefficients/claims).

Bilingual presentation: EN / ZH / side-by-side, driven by same-source compiled
sections (EN: sections, ZH: sections_zh) with explicit consistency notes.

Run:
  cd ~/量傳線 && streamlit run scripts/distill_paper_showcase/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Ensure showcase package and project scripts are importable.
APP_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = APP_DIR.parent
for p in (str(APP_DIR), str(SCRIPTS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

# st.set_page_config must be called once, before other Streamlit calls.
st.set_page_config(
    page_title="Distill Showcase — Heatload Distill Paper (EN/ZH)",
    layout="wide",
)

from src.data import LANG_BILINGUAL, LANG_EN, LANG_ZH, consistency_note, load_bundle  # noqa: E402
from src.views import (  # noqa: E402
    abstract,
    chapters,
    charts,
    citations,
    consolidated,
    overview,
)

SUBTOPICS = [
    "摘要 Abstract",
    "章節 Chapters",
    "圖表 Charts",
    "引文與來源 Citations",
    "合併稿 Consolidated",
    "總覽 Overview",
]

LANG_OPTIONS = {
    "雙語對照 Bilingual": LANG_BILINGUAL,
    "中文 ZH": LANG_ZH,
    "English EN": LANG_EN,
}


def main() -> None:
    st.title("編譯後 Distill 論文 — Streamlit 展示 (EN/ZH, Distill Showcase)")
    st.caption(
        "同源、證據有界；SSOT D4=A（heatload-coff-nist），no refit，no invented coefficients/claims。"
        " 編譯順序：abstract → citation → chapter → reference。"
        " 中英文由對齊稿同序編譯，支援雙語檢視。"
    )

    bundle = load_bundle()
    compile_data = bundle.get("compile_data")

    # Sidebar: subtopics (distill-showcase norm: radio, horizontal=True)
    st.sidebar.header("子主題 Subtopics")
    selected = st.sidebar.radio(
        "選擇檢視",
        SUBTOPICS,
        index=0,
        horizontal=True,
        key="subtopic_radio",
    )

    st.sidebar.subheader("語言 Language")
    lang_label = st.sidebar.radio(
        "顯示語言",
        list(LANG_OPTIONS.keys()),
        index=0,
        horizontal=True,
        key="lang_mode_label",
    )
    st.session_state["lang_mode"] = LANG_OPTIONS[lang_label]

    st.sidebar.divider()
    st.sidebar.subheader("來源狀態")
    paths = bundle.get("paths", {})
    for label, p in [
        ("compile snapshot", paths.get("compile_snapshot")),
        ("consolidated EN", paths.get("consolidated_md")),
        ("consolidated ZH", paths.get("consolidated_md_zh")),
        ("reliability .json", paths.get("reliability_json")),
        ("flow .json", paths.get("flow_json")),
        ("compile spec", paths.get("compile_spec")),
        ("journal candidates", paths.get("journal_candidates")),
    ]:
        if p is not None:
            st.sidebar.write(("✅ " if p.exists() else "⚠️ ") + f"{label}: `{p.name}`")

    load_err = (bundle.get("load_errors") or {}).get("compile")
    if load_err:
        st.sidebar.error(f"compile snapshot 讀取失敗: {load_err}")

    if not compile_data:
        st.error(
            "找不到或無法讀取 `docs/distill_paper_compile_data.json`。\n\n"
            "請先執行：`cd ~/量傳線 && python3 scripts/distill_paper_compile_viz.py`"
        )
        st.info("本展示為同源檢視工具，不以猜測補齊內容（graceful degradation）。")
        return

    # consistency cue (same-source, evidence-bounded)
    with st.sidebar.expander("EN/ZH 一致性檢查 (same-source)", expanded=False):
        st.caption(consistency_note(bundle))

    if selected == "摘要 Abstract":
        abstract.render(bundle)
    elif selected == "章節 Chapters":
        chapters.render(bundle)
    elif selected == "圖表 Charts":
        charts.render(bundle)
    elif selected == "引文與來源 Citations":
        citations.render(bundle)
    elif selected == "合併稿 Consolidated":
        consolidated.render(bundle)
    elif selected == "總覽 Overview":
        overview.render(bundle)
    else:
        abstract.render(bundle)

    # Footer boundary note
    meta = compile_data.get("meta", {})
    st.sidebar.divider()
    st.sidebar.caption(f"Compiled at: {meta.get('compiled_at', 'N/A')}")
    st.sidebar.caption("Policy: D4=A SSOT, no-refit, no-invented coefficients/claims")


if __name__ == "__main__":
    main()
