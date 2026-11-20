"""Overview view for compiled distill paper (EN/ZH bilingual)."""

from __future__ import annotations

import streamlit as st

from src.data import (
    consistency_note,
    get_sections_pair,
    show_degradation,
    split_chapters,
)


def render(bundle: dict) -> None:
    compile_data = bundle.get("compile_data") or {}
    meta = compile_data.get("meta", {})
    inputs = compile_data.get("inputs", {})
    errors = compile_data.get("errors", [])
    ssot_counts = meta.get("ssot_counts", {})
    en_sec, zh_sec = get_sections_pair(bundle)

    st.header("總覽 / Overview")
    st.caption(
        "Compiled distill paper showcase（EN/ZH 雙語，同源、證據有界、D4=A；no refit, no invented coefficients/claims）。"
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Compile blocks", "4")
    c2.metric("Source docs tracked", len(inputs))
    c3.metric("Errors/degradations", len(errors))
    c4.metric("Raw DB entries", ssot_counts.get("raw_entries", 54))

    st.subheader("編譯順序與產物")
    st.code(
        "abstract → citation → chapter → reference  (+ availability disclosure)\n"
        "EN consolidated: docs/heatload-distill_paper_consolidated.md\n"
        "ZH consolidated: docs/heatload-distill_paper_consolidated.zh.md\n"
        "Same-source snapshot: docs/distill_paper_compile_data.json (sections + sections_zh)",
        language="text",
    )

    st.subheader("EN/ZH 一致性（同源檢查）")
    en_ch = len(split_chapters(en_sec.get("chapter", "")))
    zh_ch = len(split_chapters(zh_sec.get("chapter", "")))
    has_zh = bool(zh_sec)
    m1, m2, m3 = st.columns(3)
    m1.metric("EN chapters", en_ch)
    m2.metric("ZH chapters", zh_ch if has_zh else "N/A")
    m3.metric("ZH compiled", "Yes" if has_zh else "No")
    st.info(consistency_note(bundle))
    st.markdown(
        "- **摘要/章節/參考文獻/合併稿**：EN 與 ZH 由各自對齊稿（`heatload-distill_paper.md` / `.zh.md`）依同序編譯，章節/邏輯/內文/圖表(表格)/數值/公式/引用與邊界高度一致；差異為語言與必要排版。\n"
        "- **Citation & Availability**：同源事實彙編區塊，EN/ZH 共享內容。\n"
        "- **圖表/證據**：共用同源快照與可靠度/流程證據（SSOT D4=A），語言切換不改變數值與結論邊界。"
    )

    st.subheader("證據邊界 / Boundaries")
    st.markdown(
        "- **SSOT D4=A:** heatload-coff-nist `coeff_data.py` / `thermal_load.py` only; **no refit, no invented coefficients/claims**.\n"
        "- **DB:** 54 raw entries (48 `log_polynomial`, 5 `rational_copper`, 1 `runtime_polyfit`), **53 fixed-coeff** for numeric relations; "
        "`NbTi (Cri/oFlex 3)` = `runtime_polyfit`, `coeffs=null` (excluded from fixed-coefficient numeric relations).\n"
        "- **Smith et al. 2024** (doi:10.1109/TASC.2024.3350516, arXiv:2306.13574): verified motivating/comparison context only (not re-computed/extended).\n"
        "- **Reliability (conditional):** in-range integrals comparatively stable under tested perturbations; deep-low-T extrapolation (e.g. `k(20 mK)`) "
        "highly sensitive / order-of-magnitude indicator only; conditioning context-dependent; NbTi Tc-region structural residual; "
        "Kapton stored-vs-fit `max |Δc|≈79.48` (existing evidence).\n"
        "- **Target:** *Cryogenics* (Elsevier) — check latest scope/guidelines/APC/article type/format before submission."
    )

    if inputs:
        st.subheader("Inputs (tracked, EN/ZH pairing)")
        rows = []
        for k, v in inputs.items():
            if isinstance(v, dict):
                rows.append(
                    {
                        "key": k,
                        "exists": v.get("exists"),
                        "bytes": v.get("bytes"),
                        "path": v.get("path", ""),
                    }
                )
        if rows:
            st.dataframe(rows, width="stretch")

    show_degradation(bundle, errors)
