"""Shared data loading for paper compare showcase (same-source, graceful degradation)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

_THIS = Path(__file__).resolve()


def find_project_root() -> Path:
    for p in [*_THIS.parents]:
        if (p / "docs").is_dir() and (p / "scripts").is_dir():
            return p
    return Path.cwd()


ROOT = find_project_root()
DOCS = ROOT / "docs"
VIZ_JSON = DOCS / "paper_compare_viz_data.json"
XLSX = DOCS / "paper_compare_viz_demo.xlsx"
NATURE_MD = DOCS / "heatload_distill_nature_manuscript.md"
COMPILED_MD = DOCS / "heatload-distill_paper_consolidated_final.md"


@st.cache_data(show_spinner=False)
def load_bundle() -> dict[str, Any]:
    bundle: dict[str, Any] = {
        "data": None,
        "paths": {
            "viz_data.json": VIZ_JSON,
            "compare.xlsx": XLSX,
            "nature.md": NATURE_MD,
            "compiled.md": COMPILED_MD,
        },
        "load_errors": {},
    }
    try:
        bundle["data"] = json.loads(VIZ_JSON.read_text(encoding="utf-8"))
    except Exception as e:
        bundle["load_errors"]["viz_data.json"] = str(e)
    return bundle


def show_degradation(bundle: dict[str, Any]) -> None:
    errs = bundle.get("load_errors", {})
    if not errs:
        return
    with st.expander("降級/錯誤紀錄 (Degradation)", expanded=False):
        for k, v in errs.items():
            st.write(f"- `{k}`: {v}")
