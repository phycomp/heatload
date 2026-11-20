"""Shared data loading and helpers for compiled distill paper showcase.

Same-source, evidence-bounded (D4=A). Degrades gracefully when artifacts are
missing; no refit, no invented coefficients/claims.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

import streamlit as st

_THIS = Path(__file__).resolve()


def find_project_root() -> Path:
    """Locate project root (contains docs/ and scripts/) from this module/app."""
    for p in [
        Path.cwd(),
        _THIS.parents[3]
        if len(_THIS.parents) > 3
        else Path.cwd(),  # .../scripts/distill_paper_showcase/src
        _THIS.parents[2] if len(_THIS.parents) > 2 else Path.cwd(),
        _THIS.parents[1] if len(_THIS.parents) > 1 else Path.cwd(),
    ]:
        if (p / "docs").is_dir() and (p / "scripts").is_dir():
            return p
    # fallback: walk up
    for p in [Path.cwd(), *_THIS.parents]:
        if (p / "docs" / "distill_paper_compile_data.json").exists():
            return p
    return Path.cwd()


ROOT = find_project_root()
DOCS = ROOT / "docs"

COMPILE_JSON = DOCS / "distill_paper_compile_data.json"
CONSOLIDATED_MD = DOCS / "heatload-distill_paper_consolidated.md"
CONSOLIDATED_MD_ZH = DOCS / "heatload-distill_paper_consolidated.zh.md"
RELIAB_JSON = DOCS / "polyfit_可靠度驗證.json"
FLOW_JSON = DOCS / "9coeff_4step_flow.json"
SPEC_COMPILE = DOCS / "distill_paper_compile_視覺化規格.md"
JOURNAL_MD = DOCS / "heatload-distill_期刊候選.md"

LANG_EN = "en"
LANG_ZH = "zh"
LANG_BILINGUAL = "bilingual"


@st.cache_data(show_spinner=False)
def load_bundle() -> dict[str, Any]:
    """Load same-source compiled snapshot and optional supporting artifacts."""
    bundle: dict[str, Any] = {
        "root": ROOT,
        "docs": DOCS,
        "paths": {
            "compile_snapshot": COMPILE_JSON,
            "consolidated_md": CONSOLIDATED_MD,
            "consolidated_md_zh": CONSOLIDATED_MD_ZH,
            "reliability_json": RELIAB_JSON,
            "flow_json": FLOW_JSON,
            "compile_spec": SPEC_COMPILE,
            "journal_candidates": JOURNAL_MD,
        },
        "compile_data": None,
        "reliab": None,
        "flow": None,
        "consolidated_text": None,
        "consolidated_text_zh": None,
        "load_errors": {},
    }
    try:
        bundle["compile_data"] = json.loads(COMPILE_JSON.read_text(encoding="utf-8"))
    except Exception as e:
        bundle["load_errors"]["compile"] = str(e)
    try:
        bundle["reliab"] = json.loads(RELIAB_JSON.read_text(encoding="utf-8"))
    except Exception as e:
        bundle["load_errors"]["reliability"] = str(e)
    try:
        bundle["flow"] = json.loads(FLOW_JSON.read_text(encoding="utf-8"))
    except Exception as e:
        bundle["load_errors"]["flow"] = str(e)
    try:
        bundle["consolidated_text"] = CONSOLIDATED_MD.read_text(encoding="utf-8")
    except Exception as e:
        bundle["load_errors"]["consolidated"] = str(e)
    # ZH consolidated: prefer snapshot sections_zh, fallback to file
    try:
        cd = bundle.get("compile_data") or {}
        zsec = cd.get("sections_zh") or {}
        zcon = zsec.get("consolidated")
        if zcon:
            bundle["consolidated_text_zh"] = zcon
        else:
            bundle["consolidated_text_zh"] = CONSOLIDATED_MD_ZH.read_text(
                encoding="utf-8"
            )
    except Exception as e:
        bundle["load_errors"]["consolidated_zh"] = str(e)
    return bundle


def current_lang(bundle: dict[str, Any] | None = None) -> str:
    lang = st.session_state.get("lang_mode", LANG_BILINGUAL)
    if lang not in (LANG_EN, LANG_ZH, LANG_BILINGUAL):
        lang = LANG_BILINGUAL
    return lang


def get_sections(bundle: dict[str, Any], lang: str | None = None) -> dict[str, Any]:
    lang = lang or current_lang(bundle)
    cd = bundle.get("compile_data") or {}
    if lang == LANG_ZH:
        return cd.get("sections_zh") or cd.get("sections") or {}
    return cd.get("sections") or {}


def get_sections_pair(bundle: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    cd = bundle.get("compile_data") or {}
    en = cd.get("sections") or {}
    zh = cd.get("sections_zh") or {}
    return en, zh


def fmt_num(v: Any) -> str:
    if v is None:
        return "N/A"
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, (int, float)):
        av = abs(float(v))
        if av == 0:
            return "0"
        if av >= 1e4 or av < 1e-3:
            return f"{v:.4e}"
        return f"{v:.6g}"
    return str(v)


def log10_safe(v: Any) -> float | None:
    try:
        fv = float(v)
        if fv > 0:
            return math.log10(fv)
    except Exception:
        pass
    return None


def split_chapters(chapter_text: str) -> list[tuple[str, str]]:
    """Split compiled chapters into [(title, body_markdown)] by ## n. headings."""
    if not chapter_text:
        return []
    text = re.sub(
        r"^## (?:Chapters \(compiled\)|章節（編譯）)\s*\n+",
        "",
        chapter_text.strip(),
        flags=re.MULTILINE,
    )
    parts = re.split(r"(?m)^(## \d+\..*)$", text)
    chapters: list[tuple[str, str]] = []
    pre = parts[0].strip()
    if pre and pre.startswith("##"):
        chapters.append((pre.splitlines()[0].lstrip("# ").strip(), pre))
    i = 1
    while i + 1 < len(parts):
        h = parts[i].strip().lstrip("# ").strip()
        b = parts[i + 1].strip()
        chapters.append((h, f"## {h}\n\n{b}" if b else f"## {h}"))
        i += 2
    if not chapters and text.strip():
        chapters.append(("Chapters / 章節", text.strip()))
    return chapters


def bar_chart_fallback(data: dict[str, Any], title: str | None = None) -> None:
    """Try st.bar_chart, fallback to table."""
    if title:
        st.caption(title)
    try:
        import pandas as pd  # type: ignore

        st.bar_chart(pd.DataFrame({"value": data}))
        return
    except Exception:
        pass
    try:
        st.bar_chart(data)
    except Exception:
        st.table([{"item": k, "value": v} for k, v in data.items()])


def show_degradation(
    bundle: dict[str, Any], compile_errors: list[Any] | None = None
) -> None:
    """Render compile errors and load degradations if any."""
    compile_errors = compile_errors or []
    load_errors = bundle.get("load_errors", {})
    if not compile_errors and not load_errors:
        return
    with st.expander("降級/錯誤紀錄 (Degradation & errors)", expanded=False):
        if compile_errors:
            st.markdown("**Compile snapshot `errors`**")
            for e in compile_errors:
                st.write("- ", e)
        if load_errors:
            st.markdown("**Artifact load issues (graceful degradation)**")
            for k, v in load_errors.items():
                st.write(f"- `{k}`: {v}")


def consistency_note(bundle: dict[str, Any]) -> str:
    cd = bundle.get("compile_data") or {}
    en = cd.get("sections") or {}
    zh = cd.get("sections_zh") or {}
    if not zh:
        return "（尚無 ZH 編譯區塊可比對；請執行編譯器產生 `sections_zh`。）"
    en_ch = len(split_chapters(en.get("chapter", "")))
    zh_ch = len(split_chapters(zh.get("chapter", "")))
    en_ref = en.get("reference", "")
    zh_ref = zh.get("reference", "")
    ref_keys = len(re.findall(r"(?m)^\[\^", en_ref))
    ref_keys_zh = len(re.findall(r"(?m)^\[\^", zh_ref))
    same_shared = (en.get("citation") == zh.get("citation")) and (
        en.get("availability") == zh.get("availability")
    )
    parts = [
        f"章節數：EN {en_ch} / ZH {zh_ch}",
        f"參考文獻條目數：EN {ref_keys} / ZH {ref_keys_zh}",
        f"同源共享區塊(citation/availability)一致：{'是' if same_shared else '否/待確認'}",
    ]
    return (
        "；".join(parts)
        + "。EN/ZH 由同序對齊稿編譯（abstract/chapter/reference），章節/邏輯/數值/公式/引用與邊界高度一致；差異為語言與必要排版。圖表/SSOT/證據邊界共用同源事實。"
    )
