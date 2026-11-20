"""Consolidated paper view for compiled distill paper (EN/ZH bilingual)."""

from __future__ import annotations

import streamlit as st

from src.data import (
    LANG_BILINGUAL,
    LANG_EN,
    LANG_ZH,
    current_lang,
    get_sections_pair,
    show_degradation,
)


def _dl_button(text: str, label: str, fname: str, key: str) -> None:
    st.download_button(label, data=text, file_name=fname, mime="text/markdown", key=key)


def render(bundle: dict) -> None:
    compile_data = bundle.get("compile_data") or {}
    errors = compile_data.get("errors", [])
    lang = current_lang(bundle)
    en_sec, zh_sec = get_sections_pair(bundle)

    st.header("合併稿 / Consolidated Paper")
    st.caption(
        "Compiled order: abstract → citation → chapter → reference (+ availability). "
        "Evidence-bounded merge; not a journal-formatted/peer-reviewed final. "
        "EN/ZH 由對齊稿同序編譯。"
    )

    en_text = en_sec.get("consolidated") or bundle.get("consolidated_text") or ""
    zh_text = zh_sec.get("consolidated") or bundle.get("consolidated_text_zh") or ""

    if lang == LANG_EN:
        if en_text:
            st.markdown(en_text)
            _dl_button(
                en_text,
                "下載 EN consolidated markdown",
                "heatload-distill_paper_consolidated.md",
                "dl_en",
            )
        else:
            st.warning("EN 合併稿不可用。")
    elif lang == LANG_ZH:
        if zh_text:
            st.markdown(zh_text)
            _dl_button(
                zh_text,
                "下載 ZH consolidated markdown",
                "heatload-distill_paper_consolidated.zh.md",
                "dl_zh",
            )
        else:
            st.warning("ZH 合併稿不可用（缺 `sections_zh`/檔案），顯示 EN。")
            if en_text:
                st.markdown(en_text)
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("English")
            if en_text:
                st.markdown(en_text)
                _dl_button(
                    en_text,
                    "下載 EN",
                    "heatload-distill_paper_consolidated.md",
                    "dl_en_bi",
                )
            else:
                st.warning("EN 合併稿不可用。")
        with c2:
            st.subheader("中文")
            if zh_text:
                st.markdown(zh_text)
                _dl_button(
                    zh_text,
                    "下載 ZH",
                    "heatload-distill_paper_consolidated.zh.md",
                    "dl_zh_bi",
                )
            else:
                st.warning("ZH 合併稿不可用（缺 `sections_zh`/檔案）。")

    if lang == LANG_BILINGUAL and en_text and zh_text:
        st.success(
            "EN/ZH 合併稿同序編譯（abstract→citation→chapter→reference+availability）；"
            "章節/邏輯/數值/公式/引用與邊界高度一致，差異為語言與必要排版/標題文字。"
        )

    show_degradation(bundle, errors)
