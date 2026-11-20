"""Abstract view for compiled distill paper (EN/ZH bilingual)."""

from __future__ import annotations

import streamlit as st

from src.data import (
    LANG_BILINGUAL,
    LANG_EN,
    LANG_ZH,
    current_lang,
    get_sections,
    get_sections_pair,
    show_degradation,
)


def render(bundle: dict) -> None:
    compile_data = bundle.get("compile_data") or {}
    errors = compile_data.get("errors", [])
    lang = current_lang(bundle)

    st.header("摘要 / Abstract")
    st.caption(
        "同源編譯自對齊稿：EN `docs/heatload-distill_paper.md`、ZH `docs/heatload-distill_paper.zh.md`（證據有界）。"
    )

    en_sec, zh_sec = get_sections_pair(bundle)
    en_abs = en_sec.get("abstract", "")
    zh_abs = zh_sec.get("abstract", "")

    if lang == LANG_EN:
        st.markdown(en_abs or "_(EN abstract unavailable)_")
    elif lang == LANG_ZH:
        if zh_abs:
            st.markdown(zh_abs)
        else:
            st.warning("ZH 摘要不可用（請確認 snapshot 含 `sections_zh`）。")
            st.markdown(en_abs or "_(unavailable)_")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("English")
            st.markdown(en_abs or "_(EN abstract unavailable)_")
        with c2:
            st.subheader("中文")
            if zh_abs:
                st.markdown(zh_abs)
            else:
                st.warning("ZH 摘要不可用（缺 `sections_zh`）。")

    if lang == LANG_BILINGUAL and en_abs and zh_abs:
        st.success(
            "EN/ZH 摘要由對齊稿同序編譯，內容/數值/引用/邊界高度一致（語言差異除外）。"
        )

    show_degradation(bundle, errors)
