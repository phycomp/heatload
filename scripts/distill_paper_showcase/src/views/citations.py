"""Citations and sources view for compiled distill paper (EN/ZH bilingual)."""

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


def render(bundle: dict) -> None:
    compile_data = bundle.get("compile_data") or {}
    inputs = compile_data.get("inputs", {})
    errors = compile_data.get("errors", [])
    lang = current_lang(bundle)
    en_sec, zh_sec = get_sections_pair(bundle)

    st.header("引文與來源 / Citations & Sources")
    st.caption(
        "同源引文/溯源、參考文獻與可得性。Citation/Availability 為同源事實彙編（共享）；"
        "References 由 EN/ZH 對齊稿各自編譯（引用鍵與條目一致）。"
    )

    tabs = st.tabs(["Citation & Provenance", "References", "Availability & Inputs"])
    with tabs[0]:
        ctext = en_sec.get("citation", "") or zh_sec.get("citation", "")
        if ctext:
            st.info("此區塊為同源事實彙編，EN/ZH 共享同一內容。")
            st.markdown(ctext)
        else:
            st.warning("Citation 區塊不可用。")

    with tabs[1]:
        en_ref = en_sec.get("reference", "")
        zh_ref = zh_sec.get("reference", "")
        if lang == LANG_EN:
            st.markdown(en_ref or "_(EN references unavailable)_")
        elif lang == LANG_ZH:
            if zh_ref:
                st.markdown(zh_ref)
            else:
                st.warning("ZH 參考文獻不可用，顯示 EN。")
                st.markdown(en_ref or "_(unavailable)_")
        else:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("English")
                st.markdown(en_ref or "_(EN references unavailable)_")
            with c2:
                st.subheader("中文")
                if zh_ref:
                    st.markdown(zh_ref)
                else:
                    st.warning("ZH 參考文獻不可用（缺 `sections_zh`）。")
        if lang == LANG_BILINGUAL and en_ref and zh_ref:
            st.success(
                "EN/ZH 參考文獻由對齊稿同序編譯，引用鍵與條目內容高度一致（語言/標題文字差異除外）。"
            )

    with tabs[2]:
        atext = en_sec.get("availability", "") or zh_sec.get("availability", "")
        if atext:
            st.info("Availability 為同源事實揭露，EN/ZH 共享同一內容。")
            st.markdown(atext)
        else:
            st.warning("Availability 區塊不可用。")

        if inputs:
            st.subheader("Inputs (same-source tracked, EN/ZH pairing)")
            rows = []
            for k, v in inputs.items():
                if isinstance(v, dict):
                    rows.append(
                        {
                            "key": k,
                            "exists": v.get("exists"),
                            "bytes": v.get("bytes"),
                            "mtime": v.get("mtime", ""),
                            "path": v.get("path", ""),
                            "error": v.get("error", ""),
                        }
                    )
            if rows:
                st.dataframe(rows, width="stretch")

    show_degradation(bundle, errors)
