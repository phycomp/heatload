#!/usr/bin/env python3
"""Streamlit viz/demo for compiled distill paper (topic-viz, Format F).

Compatibility entry point aligned with distill-showcase structure.
Primary implementation lives in:
  - scripts/distill_paper_showcase/app.py
  - scripts/distill_paper_showcase/src/{data,views/*}

Displays compiled paper 摘要 (abstract) / 章節 (chapters) / 圖表 (charts),
plus citations/sources, consolidated, and overview — driven by same-source
compiled artifacts with graceful degradation. Supports EN/ZH/bilingual views.

Policy: D4=A (heatload-coff-nist SSOT), no refit, no invented coefficients/claims.

Run:
  cd ~/量傳線 && streamlit run scripts/distill_paper_compile_streamlit.py
  # preferred showcase entry:
  # streamlit run scripts/distill_paper_showcase/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_THIS = Path(__file__).resolve()
SCRIPTS_DIR = _THIS.parent
SHOWCASE_DIR = SCRIPTS_DIR / "distill_paper_showcase"
for p in (str(SHOWCASE_DIR), str(SCRIPTS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

# st.set_page_config must be called once (compat entry).
st.set_page_config(
    page_title="Compiled Distill Paper | topic-viz (compat, EN/ZH)", layout="wide"
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
    st.title("編譯後 Distill 論文 — Streamlit 展示 (compat, EN/ZH)")
    st.caption(
        "相容入口（對齊 distill-showcase 結構）。同源快照驅動、證據有界；SSOT D4=A，no refit，no invented coefficients/claims。"
    )

    bundle = load_bundle()
    compile_data = bundle.get("compile_data")

    st.sidebar.header("子主題 Subtopics")
    selected = st.sidebar.radio(
        "選擇檢視",
        SUBTOPICS,
        index=0,
        horizontal=True,
        key="compat_subtopic_radio",
    )

    st.sidebar.subheader("語言 Language")
    lang_label = st.sidebar.radio(
        "顯示語言",
        list(LANG_OPTIONS.keys()),
        index=0,
        horizontal=True,
        key="compat_lang_mode_label",
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

    meta = (compile_data or {}).get("meta", {})
    st.sidebar.divider()
    if compile_data:
        with st.sidebar.expander("EN/ZH 一致性檢查", expanded=False):
            st.caption(consistency_note(bundle))
    st.sidebar.caption(f"Compiled at: {meta.get('compiled_at', 'N/A')}")
    st.sidebar.caption("Preferred: streamlit run scripts/distill_paper_showcase/app.py")

    if not compile_data:
        st.error(
            "找不到或無法讀取 `docs/distill_paper_compile_data.json`。\n\n"
            "請先執行：`cd ~/量傳線 && python3 scripts/distill_paper_compile_viz.py`"
        )
        return

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


if __name__ == "__main__":
    main()
