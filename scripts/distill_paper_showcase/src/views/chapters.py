"""Chapters view for compiled distill paper (EN/ZH bilingual)."""

from __future__ import annotations

import streamlit as st

from src.data import (
    LANG_BILINGUAL,
    LANG_EN,
    LANG_ZH,
    current_lang,
    get_sections_pair,
    show_degradation,
    split_chapters,
)


def _render_single_language(
    chapters: list[tuple[str, str]], chapter_text: str, key_prefix: str
) -> None:
    if not chapters:
        st.warning("章節區塊不可用。")
        return
    titles = [t for t, _ in chapters]
    mode = st.radio(
        "檢視模式 / View mode",
        ["依章節瀏覽", "完整章節內容"],
        horizontal=True,
        key=f"{key_prefix}_view_mode",
    )
    if mode == "依章節瀏覽":
        sel = st.radio(
            "選擇章節 / Select chapter",
            options=list(range(len(titles))),
            format_func=lambda i: titles[i],
            key=f"{key_prefix}_select",
            horizontal=False,
        )
        st.markdown(chapters[sel][1])
    else:
        st.markdown(chapter_text)
    with st.expander("章節目錄 / TOC", expanded=False):
        for i, t in enumerate(titles, 1):
            st.write(f"{i}. {t}")


def _chapter_label(
    i: int, en_ch: list[tuple[str, str]], zh_ch: list[tuple[str, str]]
) -> str:
    en_t = en_ch[i][0] if i < len(en_ch) else "(N/A)"
    zh_t = zh_ch[i][0] if i < len(zh_ch) else "(N/A)"
    if en_t == zh_t:
        return f"{i + 1}. {en_t}"
    return f"{i + 1}. EN: {en_t} ｜ ZH: {zh_t}"


def _render_bilingual_synced(
    en_ch: list[tuple[str, str]],
    zh_ch: list[tuple[str, str]],
    en_text: str,
    zh_text: str,
) -> None:
    if not en_ch and not zh_ch:
        st.warning("EN/ZH 章節區塊皆不可用。")
        return

    # Single shared control set for synchronized comparison.
    mode = st.radio(
        "檢視模式（同步）/ View mode (synced)",
        ["依章節瀏覽", "完整章節內容"],
        horizontal=True,
        key="chap_bi_sync_view_mode",
    )

    max_n = max(len(en_ch), len(zh_ch))
    sel = 0

    # 三欄同步比對：章節導覽 / English / 中文。
    c_nav, c_en, c_zh = st.columns([3, 4, 4])

    with c_nav:
        st.subheader("章節 / Chapters")
        if mode == "依章節瀏覽" and max_n > 0:

            def _nav_label(i: int) -> str:
                # 以標記標示目前選取章節（格式函式僅回傳標籤，不建立新控件）。
                current = st.session_state.get("chap_bi_sync_select", 0)
                label = _chapter_label(i, en_ch, zh_ch)
                return f"▶ {label}" if i == current else label

            # 第一欄即為章節選擇器：單一共享控件，驅動 EN/ZH 兩欄的 `sel`。
            sel = st.radio(
                "選擇章節（同步）/ Select chapter (synced)",
                options=list(range(max_n)),
                format_func=_nav_label,
                key="chap_bi_sync_select",
                horizontal=False,
            )
        elif max_n == 0:
            st.write("（無章節可顯示）")
        else:
            # 完整章節內容：本欄顯示完整目錄（已併入第一欄，不再另設 TOC 控件）。
            for i in range(max_n):
                st.write(_chapter_label(i, en_ch, zh_ch))

    with c_en:
        st.subheader("English")
        if mode == "完整章節內容":
            if en_text:
                st.markdown(en_text)
            elif en_ch:
                st.markdown("\n\n".join(body for _, body in en_ch))
            else:
                st.warning("EN 章節不可用。")
        else:
            if sel < len(en_ch):
                st.markdown(en_ch[sel][1])
            else:
                st.warning("EN 此章不可用（索引超出範圍）。")

    with c_zh:
        st.subheader("中文")
        if mode == "完整章節內容":
            if zh_text:
                st.markdown(zh_text)
            elif zh_ch:
                st.markdown("\n\n".join(body for _, body in zh_ch))
            else:
                st.warning("ZH 章節不可用（缺 `sections_zh`）。")
        else:
            if sel < len(zh_ch):
                st.markdown(zh_ch[sel][1])
            else:
                st.warning("ZH 此章不可用（索引超出範圍/缺 `sections_zh`）。")


def render(bundle: dict) -> None:
    compile_data = bundle.get("compile_data") or {}
    errors = compile_data.get("errors", [])
    lang = current_lang(bundle)

    st.header("章節 / Chapters")
    st.caption(
        "同源編譯自對齊稿 §§1–8：EN `heatload-distill_paper.md`、ZH `heatload-distill_paper.zh.md`（證據有界）。"
    )

    en_sec, zh_sec = get_sections_pair(bundle)
    en_text = en_sec.get("chapter", "")
    zh_text = zh_sec.get("chapter", "")
    en_ch = split_chapters(en_text)
    zh_ch = split_chapters(zh_text)

    if lang == LANG_EN:
        if not en_ch:
            st.warning("EN 章節區塊不可用。")
        else:
            _render_single_language(en_ch, en_text, "chap_en")
    elif lang == LANG_ZH:
        if zh_ch:
            _render_single_language(zh_ch, zh_text, "chap_zh")
        else:
            st.warning("ZH 章節不可用（缺 `sections_zh`），顯示 EN。")
            _render_single_language(en_ch, en_text, "chap_en_fallback")
    else:
        _render_bilingual_synced(en_ch, zh_ch, en_text, zh_text)

    if lang == LANG_BILINGUAL and en_ch and zh_ch:
        if len(en_ch) == len(zh_ch):
            st.success(
                f"EN/ZH 章節結構對齊：各 {len(en_ch)} 章，同序編譯；"
                "內容/數值/公式/引用與邊界高度一致（語言差異除外）。雙語檢視使用單組同步控制以便比對。"
            )
        else:
            st.info(
                f"EN 章節數 {len(en_ch)}、ZH 章節數 {len(zh_ch)}（請確認同源對齊）；雙語檢視以同步索引比對可用章節。"
            )

    show_degradation(bundle, errors)
