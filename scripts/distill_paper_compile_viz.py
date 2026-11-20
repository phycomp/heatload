#!/usr/bin/env python3
"""Compile sedimented distill paper documents (topic-viz, Format F).

Compile order (requested): abstract, citation, chapter, reference -> consolidated paper.
Evidence-bounded, same-source: no refit, no invented coefficients/claims, SSOT D4=A.

Outputs:
  - docs/distill_paper_compile_data.json (same-source snapshot)
  - docs/distill_paper_compile_demo.html  (offline, self-contained)
  - docs/distill_paper_compile_demo.xlsx  (stdlib zipfile+xml, no extra deps)
  - docs/heatload-distill_paper_consolidated.md (merged consolidated paper)
"""

from __future__ import annotations

import html
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT_JSON = DOCS / "distill_paper_compile_data.json"
OUT_HTML = DOCS / "distill_paper_compile_demo.html"
OUT_XLSX = DOCS / "distill_paper_compile_demo.xlsx"
OUT_CONSOLIDATED_MD = DOCS / "heatload-distill_paper_consolidated.md"
OUT_CONSOLIDATED_MD_ZH = DOCS / "heatload-distill_paper_consolidated.zh.md"

PAPER_MD = DOCS / "heatload-distill_paper.md"
PAPER_TEX = DOCS / "heatload-distill_paper.tex"
PAPER_ZH_MD = DOCS / "heatload-distill_paper.zh.md"
PAPER_ZH_TEX = DOCS / "heatload-distill_paper.zh.tex"
JOURNAL_MD = DOCS / "heatload-distill_期刊候選.md"
FLOW_JSON = DOCS / "9coeff_4step_flow.json"
RELIAB_JSON = DOCS / "polyfit_可靠度驗證.json"
RELIAB_MD = DOCS / "polyfit_可靠度驗證.md"
SPEC_4STEP = DOCS / "9coeff_4step_視覺化規格.md"
NIST9_INT = DOCS / "NIST9熱負載整合說明.md"

ORG_NOTE = Path("/home/sam/Context/20261119T120029--paper-heatload-distill__paper.org")
ORG_MAP = Path(
    "/home/sam/Context/20261119T120029--paper-heatload-distill__paper-map.md"
)
CITATIONS_REF = Path(
    "/home/sam/.opencode/skills/heatload-coff-nist/references/citations.md"
)

# Demo (topic-viz integration): 9coeff 4-step + 溫區擬合 fitting
WENQU_SEDIMENT = DOCS / "溫區擬合_科學成果沉澱.md"
WENQU_EXTRACT = DOCS / "溫區擬合_物理模型_來源萃取.md"
WENQU_ARXIV = DOCS / "溫區擬合_物理模型_arxiv驗證.md"
WENQU_VIZ_SPEC = DOCS / "溫區擬合_物理模型_viz_spec.md"
WENQU_FITTING_SVG = DOCS / "溫區擬合_物理模型_fitting示意圖.svg"
NINECOEFF_DEMO_HTML = DOCS / "9coeff_4step_demo.html"
NINECOEFF_DEMO_XLSX = DOCS / "9coeff_4step_demo.xlsx"


def read_text(path: Path) -> tuple[str | None, str | None]:
    try:
        return path.read_text(encoding="utf-8"), None
    except Exception as e:
        return None, str(e)


def read_json(path: Path) -> tuple[dict | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as e:
        return None, str(e)


def file_meta(path: Path) -> dict:
    try:
        st = path.stat()
        return {
            "path": str(path),
            "exists": True,
            "bytes": st.st_size,
            "mtime": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"path": str(path), "exists": False, "error": str(e)}


def extract_between(text: str, start_pat: str, end_pat: str | None) -> str:
    m = re.search(start_pat, text, re.MULTILINE)
    if not m:
        return ""
    s = m.end()
    if end_pat:
        e = re.search(end_pat, text[s:], re.MULTILINE)
        if e:
            return text[s : s + e.start()].strip()
    return text[s:].strip()


def extract_section(text: str, heading: str, next_heading: str | None = None) -> str:
    # heading like r"^## Abstract\s*$"
    m = re.search(heading, text, re.MULTILINE)
    if not m:
        return ""
    # content starts after this heading line
    line_end = text.find("\n", m.start())
    s = (line_end + 1) if line_end != -1 else m.end()
    if next_heading:
        e = re.search(next_heading, text[s:], re.MULTILINE)
        if e:
            return text[s : s + e.start()].strip()
    return text[s:].strip()


def collect_inputs(errors: list[str]) -> dict:
    inputs = {}
    specs = [
        ("paper_md", PAPER_MD),
        ("paper_tex", PAPER_TEX),
        ("paper_zh_md", PAPER_ZH_MD),
        ("paper_zh_tex", PAPER_ZH_TEX),
        ("journal_candidates", JOURNAL_MD),
        ("flow_snapshot", FLOW_JSON),
        ("reliability_json", RELIAB_JSON),
        ("reliability_md", RELIAB_MD),
        ("spec_4step", SPEC_4STEP),
        ("nist9_integration", NIST9_INT),
        ("ljg_org", ORG_NOTE),
        ("ljg_map", ORG_MAP),
        ("citations_ref", CITATIONS_REF),
        ("ninecoeff_flow", FLOW_JSON),
        ("ninecoeff_spec", SPEC_4STEP),
        ("ninecoeff_demo_html", NINECOEFF_DEMO_HTML),
        ("ninecoeff_demo_xlsx", NINECOEFF_DEMO_XLSX),
        ("wenqu_sediment", WENQU_SEDIMENT),
        ("wenqu_extract", WENQU_EXTRACT),
        ("wenqu_arxiv", WENQU_ARXIV),
        ("wenqu_viz_spec", WENQU_VIZ_SPEC),
        ("wenqu_fitting_svg", WENQU_FITTING_SVG),
    ]
    for key, path in specs:
        inputs[key] = file_meta(path)
        if not path.exists():
            # some are optional in strictness but we record
            pass
    return inputs


def build_citation_section(
    flow: dict | None,
    journal_text: str | None,
    paper_text: str | None,
    errors: list[str],
) -> str:
    lines: list[str] = []
    lines.append("## Citations and Provenance (compiled)")
    lines.append("")
    lines.append(
        "> Compiled from sedimented distill sources (same-source, evidence-bounded). "
        "No unverified bibliographic details added. Submission policies/scope/APC/article type "
        "for *Cryogenics* must be checked against the latest journal guidelines before submission."
    )
    lines.append("")

    # Target journal / framework from journal doc
    lines.append("### Target and submission context")
    if journal_text:
        # extract section 0 table-ish info
        sec0 = extract_section(
            journal_text, r"^## 0\. 本稿框架與目標期刊\s*$", r"^## 1\."
        )
        if sec0:
            # keep compact: first ~40 lines
            sl = [l for l in sec0.splitlines() if l.strip()]
            lines.append(
                "- Requested target (from `docs/heatload-distill_期刊候選.md`): **Cryogenics (Elsevier)**; "
                "review + reliability-aware workflow, not new measurements/re-fitting."
            )
            # include key gate note line if present
            for l in sl:
                if "投稿門檻" in l or "不得宣稱" in l:
                    lines.append(f"- {l.lstrip('>').strip()}")
                    break
        else:
            lines.append(
                "- Requested target: **Cryogenics (Elsevier)** (see `docs/heatload-distill_期刊候選.md`)."
            )
    else:
        errors.append("journal_candidates unreadable; target-journal context degraded")
        lines.append(
            "- Requested target: *Cryogenics* (journal notes unavailable in this run)."
        )
    lines.append("")

    # Provenance/SSOT stats from snapshot
    lines.append("### Provenance and SSOT boundary (same-source)")
    if flow:
        s1 = next((s for s in flow.get("steps", []) if s.get("id") == 1), {})
        prov = s1.get("provenance", {}) or {}
        db = s1.get("database", {}) or {}
        n = db.get("material_count_coeff_data")
        raw = db.get("raw_materials") or []
        eq = db.get("equation_types") or {}
        lines.append(
            f"- SSOT (D4=A): `{(prov.get('ssot_paths') or {}).get('coeff_data', '~/.opencode/skills/heatload-coff-nist/scripts/coeff_data.py')}`, `{(prov.get('ssot_paths') or {}).get('thermal_load', '~/.opencode/skills/heatload-coff-nist/scripts/thermal_load.py')}`"
        )
        if n is not None:
            lines.append(
                f"- Database: **{n}** entries total (raw rows: {len(raw)}); equation types: "
                + ", ".join(f"`{k}`={v}" for k, v in eq.items())
                + "."
            )
        lines.append(
            "- Fixed-coefficient numeric relations set: **53**; `NbTi (Cri/oFlex 3)` is `runtime_polyfit` with `coeffs=null` (excluded from fixed-coefficient numeric relations, no invented coeffs)."
        )
        lines.append(
            f"- Same-source snapshot: `docs/9coeff_4step_flow.json` (generated_at: `{flow.get('meta', {}).get('generated_at')}`, errors: {len(flow.get('errors') or [])})."
        )
        lines.append("")
        lines.append("### Key verified references (from provenance snapshot)")
        krefs = prov.get("key_refs") or []
        if krefs:
            for r in krefs:
                title = r.get("title") or r.get("id") or ""
                ident = (
                    r.get("doi")
                    or r.get("dataset")
                    or r.get("url")
                    or r.get("source_file")
                    or ""
                )
                content = r.get("content") or ""
                bullet = f"- **{title}**"
                if ident:
                    bullet += f" — `{ident}`"
                if content:
                    bullet += f": {content}"
                lines.append(bullet)
        else:
            errors.append("provenance key_refs missing in snapshot")
            lines.append("- (key_refs unavailable; see paper references)")
        # also include Smith explicitly as motivating verified ref (in paper/journal, may not be in flow key_refs)
        lines.append(
            "- **Smith et al. (2024)** Improved Flexible Coaxial Ribbon Cable for High-Density Superconducting Arrays — `doi:10.1109/TASC.2024.3350516`, arXiv:2306.13574: verified motivating/comparison context only (literature κ(T)+cross-section heat-load estimation; reported 5 nW/trace 1 K→100 mK for 1-ft in cited work). Not re-computed or extended here."
        )
    else:
        errors.append("flow snapshot unreadable; provenance stats degraded")
        lines.append(
            "- (Snapshot unavailable; see consolidated chapters/references for stated boundaries.)"
        )
    lines.append("")

    # Source roles table from paper if present
    if paper_text:
        m = re.search(r"^### 2\.2 Source roles.*?$", paper_text, re.MULTILINE)
        if m:
            # capture table block until 2.3
            block = extract_section(
                paper_text,
                r"^### 2\.2 Source roles \(as recorded in project provenance\)\s*$",
                r"^### 2\.3 ",
            )
            if block:
                lines.append("### Source roles (as recorded in manuscript)")
                # include table lines
                for l in block.splitlines():
                    if l.strip().startswith("|") or l.strip().startswith(
                        "**Citation policy"
                    ):
                        lines.append(l)
                lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_chapters_section(paper_text: str, errors: list[str], lang: str = "en") -> str:
    if not paper_text:
        errors.append(f"paper markdown unreadable; chapters degraded ({lang})")
        heading = "## 章節（編譯）" if lang == "zh" else "## Chapters (compiled)"
        return f"{heading}\n\n*(Unavailable: source paper markdown not readable.)*\n"
    if lang == "zh":
        m = re.search(r"^## 1\. 緒論\s*$", paper_text, re.MULTILINE)
        if not m:
            errors.append("could not locate chapters start (## 1. 緒論, zh)")
            return "## 章節（編譯）\n\n*(來源未找到章節。)*\n"
        start = m.start()
        e = re.search(r"^## 可得性\s*$", paper_text[m.start() :], re.MULTILINE)
        if e:
            body = paper_text[start : m.start() + e.start()].strip()
        else:
            e2 = re.search(r"^## 參考文獻\s*$", paper_text[m.start() :], re.MULTILINE)
            body = (
                paper_text[start : m.start() + e2.start()].strip()
                if e2
                else paper_text[start:].strip()
            )
        return "## 章節（編譯）\n\n" + body + "\n"
    # from ## 1. Introduction up to before ## Availability
    m = re.search(r"^## 1\. Introduction\s*$", paper_text, re.MULTILINE)
    if not m:
        errors.append("could not locate chapters start (## 1. Introduction)")
        return (
            "## Chapters (compiled)\n\n*(Unavailable: chapters not found in source.)*\n"
        )
    start = m.start()
    e = re.search(r"^## Availability\s*$", paper_text[m.start() :], re.MULTILINE)
    if e:
        body = paper_text[start : m.start() + e.start()].strip()
    else:
        e2 = re.search(r"^## References\s*$", paper_text[m.start() :], re.MULTILINE)
        body = (
            paper_text[start : m.start() + e2.start()].strip()
            if e2
            else paper_text[start:].strip()
        )
    return "## Chapters (compiled)\n\n" + body + "\n"


def build_abstract_section(paper_text: str, errors: list[str], lang: str = "en") -> str:
    if not paper_text:
        errors.append(f"paper markdown unreadable; abstract degraded ({lang})")
        heading = "## 摘要" if lang == "zh" else "## Abstract"
        return f"{heading}\n\n*(Unavailable: source paper markdown not readable.)*\n"
    if lang == "zh":
        abs_text = extract_section(paper_text, r"^## 摘要\s*$", r"^## 1\. 緒論\s*$")
        if not abs_text:
            errors.append("abstract (摘要) not found in zh paper markdown")
            abs_text = "*(摘要未在來源中找到。)*"
        return "## 摘要\n\n" + abs_text.strip() + "\n"
    abs_text = extract_section(
        paper_text, r"^## Abstract\s*$", r"^## 1\. Introduction\s*$"
    )
    if not abs_text:
        errors.append("abstract not found in paper markdown")
        abs_text = "*(Abstract not found in source.)*"
    return "## Abstract\n\n" + abs_text.strip() + "\n"


def build_reference_section(
    paper_text: str, errors: list[str], lang: str = "en"
) -> str:
    if not paper_text:
        errors.append(f"paper markdown unreadable; references degraded ({lang})")
        heading = "## 參考文獻（編譯）" if lang == "zh" else "## References (compiled)"
        return f"{heading}\n\n*(Unavailable: source paper markdown not readable.)*\n"
    if lang == "zh":
        m = re.search(r"^## 參考文獻\s*$", paper_text, re.MULTILINE)
        if not m:
            errors.append("references (參考文獻) not found in zh paper markdown")
            return "## 參考文獻（編譯）\n\n*(來源未找到參考文獻。)*\n"
        refs = paper_text[m.start() :].strip()
        refs = re.sub(
            r"^## 參考文獻\s*$",
            "## 參考文獻（編譯）",
            refs,
            count=1,
            flags=re.MULTILINE,
        )
        return refs + "\n"
    m = re.search(r"^## References\s*$", paper_text, re.MULTILINE)
    if not m:
        errors.append("references section not found in paper markdown")
        return "## References (compiled)\n\n*(Unavailable: references not found in source.)*\n"
    refs = paper_text[m.start() :].strip()
    refs = re.sub(
        r"^## References\s*$",
        "## References (compiled)",
        refs,
        count=1,
        flags=re.MULTILINE,
    )
    return refs + "\n"


def collect_raw_materials(flow: dict | None) -> tuple[list[dict], str | None]:
    """Read SSOT raw materials (54 rows) from flow step id==1.

    Evidence boundary: rows are reproduced verbatim for provenance only.
    """
    if not flow:
        return [], "flow snapshot unavailable"
    steps = flow.get("steps") or []
    step1 = next((s for s in steps if s.get("id") == 1), None)
    if step1 is None:
        return [], "steps[id==1] not found"
    db = step1.get("database") or {}
    rows = db.get("raw_materials") or []
    if not isinstance(rows, list) or not rows:
        return [], "database.raw_materials missing/empty"
    return rows, None


def _md_cell(value) -> str:
    """Escape a Markdown table cell: pipes escaped, newlines flattened."""
    if value is None:
        return "null"
    s = str(value).replace("\r", " ").replace("\n", " ")
    s = s.replace("|", "\\|")
    return s.strip()


def _md_trunc(value, limit: int) -> str:
    s = _md_cell(value)
    if len(s) <= limit:
        return s
    return s[: max(limit - 1, 0)].rstrip() + "…"


def _fmt_coeff(value, equation_type: str) -> str:
    """Safe coefficient rendering. None never becomes an invented number."""
    if value is None:
        if equation_type == "runtime_polyfit":
            return "null (runtime_polyfit)"
        return "null"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return f"{float(value):.10g}"
    return _md_cell(value)


def build_rawdata_section(
    flow: dict | None, errors: list[str], lang: str = "en"
) -> str:
    """Appendix A: SSOT raw coefficient reference data (54 rows, same-source)."""
    rows, err = collect_raw_materials(flow)
    zh = lang == "zh"
    heading = (
        "## 附錄 A. SSOT 原始係數參照資料（54 筆）"
        if zh
        else "## Appendix A. SSOT Raw Coefficient Reference Data (54 entries)"
    )
    if err:
        errors.append(f"rawdata appendix degraded ({lang}): {err}")
        degraded_heading = (
            "## 附錄 A. SSOT 原始係數參照資料（降級）"
            if zh
            else "## Appendix A. SSOT Raw Coefficient Reference Data (degraded)"
        )
        note = (
            "*(raw data unavailable (degraded): 無法自 `docs/9coeff_4step_flow.json` "
            "讀取 `steps[id=1].database.raw_materials`。)*"
            if zh
            else "*(raw data unavailable (degraded): could not read "
            "`steps[id=1].database.raw_materials` from `docs/9coeff_4step_flow.json`.)*"
        )
        return f"{degraded_heading}\n\n{note}\n"

    n = len(rows)
    counts: dict[str, int] = {}
    for r in rows:
        k = r.get("equation_type") or "unknown"
        counts[k] = counts.get(k, 0) + 1
    eq_desc = ", ".join(f"`{k}`={v}" for k, v in sorted(counts.items()))
    runtime_n = counts.get("runtime_polyfit", 0)
    fixed_n = n - runtime_n
    null_range_n = sum(1 for r in rows if r.get("valid_range_K") is None)
    if n != 54:
        errors.append(f"rawdata appendix: expected 54 rows, got {n} ({lang})")

    lines: list[str] = [heading, ""]
    intro: list[str] = []

    if zh:
        intro.append(
            "> **定位：** 僅為**參照資料／附錄**（provenance 溯源脈絡），"
            "**非新量測、非重擬合、非新增係數**；正文結論不以此附錄改寫。"
        )
        intro.append(
            f"> **來源（同源）：** SSOT D4=A 快照 `docs/9coeff_4step_flow.json` → "
            f"`steps[id=1].database.raw_materials`，共 **{n}** 列（依快照原始順序）。"
        )
        intro.append(
            f"> **組成：** {n} = {eq_desc}；其中固定係數可數值引用者 **{fixed_n}** 筆。"
        )
        intro.append(
            "> **排除項：** `NbTi (Cri/oFlex 3)` 為 `runtime_polyfit` 且 `coeffs=null`"
            "（執行期以 `np.polyfit` 產生，受 `noise_pct` 滑桿影響）；"
            "本附錄**不為其賦予任何係數**，並將其排除於固定係數數值關係之外。"
        )
        intro.append(
            f"> **讀法：** `c0..c8` 逐列原樣轉錄，**僅供溯源**；"
            f"`valid_range_K` 於快照中有 {null_range_n}/{n} 列為 `null`（SSOT 未記錄區間，"
            "不代填）。任何單列皆不得視為新資料、重擬合結果或外推授權。"
        )
        intro.append(
            "> **呈現：** 表格單元格中的 `|` 已轉義、換行已攤平；過長 `source`/`note` 已截斷（`…`）。"
        )
    else:
        intro.append(
            "> **Role:** reference/appendix only — provenance context, "
            "**not new measurements and not a re-fit**; conclusions in the body are not rewritten by this appendix."
        )
        intro.append(
            f"> **Source (same-source):** SSOT D4=A snapshot `docs/9coeff_4step_flow.json` → "
            f"`steps[id=1].database.raw_materials`, **{n}** rows in snapshot order."
        )
        intro.append(
            f"> **Breakdown:** {n} = {eq_desc}; **{fixed_n}** entries support fixed-coefficient numeric relations."
        )
        intro.append(
            "> **Exclusion:** `NbTi (Cri/oFlex 3)` is `runtime_polyfit` with `coeffs=null` "
            "(produced at runtime by `np.polyfit`, sensitive to `noise_pct`); "
            "**no coefficients are assigned to it here**, and it stays excluded from fixed-coefficient numeric relations."
        )
        intro.append(
            f"> **Reading note:** `c0..c8` are transcribed verbatim per row for traceability only; "
            f"`valid_range_K` is `null` in {null_range_n}/{n} rows (no range recorded in the SSOT, not back-filled). "
            "No row is new data, a re-fit, or an extrapolation licence."
        )
        intro.append(
            "> **Rendering:** `|` inside cells is escaped, newlines flattened, and long `source`/`note` values truncated (`…`)."
        )
    # trailing two spaces keep the blockquote lines separate when rendered as Markdown
    lines.extend(
        line + ("  " if i < len(intro) - 1 else "") for i, line in enumerate(intro)
    )
    lines.append("")

    head = (
        ["#", "material", "category", "equation_type", "valid_range_K"]
        + [f"c{i}" for i in range(9)]
        + ["source", "note"]
    )
    lines.append("| " + " | ".join(head) + " |")
    lines.append(
        "|" + "|".join(["---:"] + ["---"] * 4 + ["---:"] * 9 + ["---", "---"]) + "|"
    )
    for i, r in enumerate(rows, 1):
        eq = r.get("equation_type") or ""
        vr = r.get("valid_range_K")
        cells = [
            str(i),
            _md_cell(r.get("material")),
            _md_cell(r.get("category")),
            _md_cell(eq),
            "null" if vr is None else _md_cell(vr),
        ]
        cells += [_fmt_coeff(r.get(f"c{k}"), eq) for k in range(9)]
        cells += [_md_trunc(r.get("source"), 110), _md_trunc(r.get("note"), 40)]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    if zh:
        lines.append(
            f"*附錄列數：{n} 列（{eq_desc}）；固定係數 {fixed_n} 筆；"
            f"`runtime_polyfit` 排除 {runtime_n} 筆。*"
        )
    else:
        lines.append(
            f"*Appendix row count: {n} ({eq_desc}); {fixed_n} fixed-coefficient entries; "
            f"{runtime_n} `runtime_polyfit` excluded.*"
        )
    return "\n".join(lines).strip() + "\n"


def build_consolidated(
    meta: dict,
    abstract: str,
    citation: str,
    chapters: str,
    rawdata: str,
    references: str,
    availability_note: str,
    lang: str = "en",
) -> str:
    parts = []
    if lang == "zh":
        parts.append("# Heatload-Distill 整合論文（編譯稿，中文版）")
        parts.append("")
        parts.append(
            "> **編譯工具：** `scripts/distill_paper_compile_viz.py` (topic-viz Format F)。  "
        )
        parts.append(f"> **編譯時間：** {meta.get('compiled_at')}  ")
        parts.append(
            "> **編譯順序：** abstract（摘要）→ citation（引文與溯源）→ chapter（章節）→ rawdata（附錄 A 原始係數參照資料）→ reference（參考文獻）。  "
        )
        parts.append(
            "> **附錄 A：** SSOT 原始係數參照資料（54 筆，48 `log_polynomial` / 5 `rational_copper` / 1 `runtime_polyfit`）"
            "以同源方式嵌入，僅供溯源；`NbTi (Cri/oFlex 3)` 為 `runtime_polyfit` 且 `coeffs=null`，不賦予係數。  "
        )
        parts.append(
            "> **政策/邊界：** 證據有界、同源可追溯；D4=A SSOT；不重擬合、不編造係數/結論。"
            "`NbTi (Cri/oFlex 3)` 為 `runtime_polyfit` 且 `coeffs=null`（排除於固定係數數值關係）。"
            "投稿前須查核 *Cryogenics* 當期 scope/guidelines/APC/article type。  "
        )
        parts.append(
            "> **一致性說明：** 本編譯稿由 `docs/heatload-distill_paper.zh.md`（與 EN 稿在章節/邏輯/內文/圖表(表格)/數值/公式/引用與邊界聲明高度一致）依同序編譯；引文/溯源彙編與 availability 沿用同源事實內容。"
        )
    else:
        parts.append("# Heatload-Distill Consolidated Paper (compiled)")
        parts.append("")
        parts.append(
            "> **Compiled by:** `scripts/distill_paper_compile_viz.py` (topic-viz Format F).  "
        )
        parts.append(f"> **Compiled at:** {meta.get('compiled_at')}  ")
        parts.append(
            "> **Compile order:** abstract, citation, chapter, rawdata (Appendix A), reference.  "
        )
        parts.append(
            "> **Appendix A:** SSOT raw coefficient reference data (54 entries: 48 `log_polynomial`, "
            "5 `rational_copper`, 1 `runtime_polyfit`) embedded same-source for traceability only; "
            "`NbTi (Cri/oFlex 3)` is `runtime_polyfit` with `coeffs=null` and receives no coefficients.  "
        )
        parts.append(
            "> **Policy:** Evidence-bounded, same-source; D4=A SSOT; no refit, no invented coefficients/claims. "
            "`NbTi (Cri/oFlex 3)` is `runtime_polyfit` with `coeffs=null` (excluded from fixed-coefficient numeric relations). "
            "Check latest *Cryogenics* scope/guidelines/APC/article type before submission."
        )
    parts.append("")
    parts.append(abstract.strip())
    parts.append("")
    parts.append(citation.strip())
    parts.append("")
    parts.append(chapters.strip())
    parts.append("")
    parts.append(rawdata.strip())
    parts.append("")
    parts.append(references.strip())
    parts.append("")
    parts.append(availability_note.strip())
    parts.append("")
    return "\n".join(parts)


def build_availability(flow: dict | None, inputs: dict) -> str:
    lines = ["## Availability and Source Artifacts (compiled)", ""]
    lines.append(
        "Primary sedimented distill paper documents and same-source artifacts used for compilation:"
    )
    for key, meta in inputs.items():
        mark = "ok" if meta.get("exists") else "missing"
        lines.append(f"- `{meta.get('path')}` ({mark})")
    lines.append("")
    lines.append(
        "Key artifacts: `docs/heatload-distill_paper.md/.tex` (EN), `docs/heatload-distill_paper.zh.md/.tex` (ZH, aligned in sections/logic/content/tables/values/formulas/citations/boundaries), "
        "`docs/heatload-distill_期刊候選.md`, `docs/9coeff_4step_flow.json`, `docs/polyfit_可靠度驗證.md/.json`, "
        "ljg-paper org/map, `docs/9coeff_4step_視覺化規格.md`, `docs/NIST9熱負載整合說明.md`, "
        "SSOT/provenance under `~/.opencode/skills/heatload-coff-nist/`."
    )
    lines.append("")
    lines.append(
        "**Limitations/gaps (not resolved by this compilation):** consolidated/sections currently compiled from EN sedimented source (ZH pairing tracked as same-source input but not merged into compiled text); "
        "raw SSOT data is embedded only as **Appendix A / `rawdata` reference** (same-source, 54 rows: 48 `log_polynomial` + 5 `rational_copper` + 1 `runtime_polyfit`; `NbTi (Cri/oFlex 3)` `runtime_polyfit` with `coeffs=null` excluded and given no coefficients) — it is provenance context, not new measurement or re-fit, and its `valid_range_K` fields are `null` wherever the SSOT records no range; "
        "`提昇論文品質.md` stale/unverified; TS ljg-paper validator unavailable in this environment; "
        "missing `streamlit/matplotlib/altair/plotly/scipy/openpyxl` for some interactive/runtime visuals; "
        "actual *Cryogenics* submission formatting/APC/scope must be checked externally; `.tex`/`.zh.tex` not templated to current journal class; "
        "ZH LaTeX (xeCJK/CJK fonts) compilation unverified; 溫區擬合同源 viz snapshot/demo (Task 5: viz_data/json/html/xlsx generator) not yet produced—compiled platform demonstrates fitting via sediment doc + inline SVG + doc-listed examples (degraded, evidence-bounded)."
    )
    return "\n".join(lines) + "\n"


def build_demo_section(flow: dict | None, errors: list[str]) -> dict:
    """Build demo payload combining 9coeff 4-step and 溫區擬合 fitting for compiled platform."""
    demo: dict = {"ninecoeff_4step": {}, "wenqu_fitting": {}}

    # ---- 9coeff 4-step (same-source) ----
    n9: dict = {
        "title": "9 參數 κ(T) 擬合 4 步驟流程（same-source demo）",
        "policy": {
            "D4": "A (SSOT: heatload-coff-nist coeff_data.py, thermal_load.py)",
            "boundary": "不重擬合、不編造係數/結論；NbTi (Cri/oFlex 3) runtime_polyfit, coeffs=null（排除固定係數數值關係）",
        },
        "artifacts": {
            "flow_snapshot": "docs/9coeff_4step_flow.json",
            "spec": "docs/9coeff_4step_視覺化規格.md",
            "demo_html": "docs/9coeff_4step_demo.html",
            "demo_xlsx": "docs/9coeff_4step_demo.xlsx",
            "reliability": "docs/polyfit_可靠度驗證.md/.json",
        },
        "steps": [],
        "counts": {},
        "errors": [],
    }
    if flow:
        meta_f = flow.get("meta", {}) or {}
        n9["generated_at"] = meta_f.get("generated_at")
        n9["flow_order"] = meta_f.get("flow") or []
        for s in flow.get("steps") or []:
            step = {
                "id": s.get("id"),
                "title": s.get("title"),
                "goal": s.get("goal"),
            }
            if s.get("id") == 1:
                db = s.get("database", {}) or {}
                prov = s.get("provenance", {}) or {}
                eq = db.get("equation_types") or {}
                n9["counts"] = {
                    "material_count_coeff_data": db.get("material_count_coeff_data"),
                    "raw_materials": len(db.get("raw_materials") or []),
                    "equation_types": eq,
                    "fixed_coeff_entries": 53,
                    "runtime_polyfit_excluded": "NbTi (Cri/oFlex 3), coeffs=null",
                }
                step["key_refs"] = [
                    {
                        "title": r.get("title"),
                        "id": r.get("doi")
                        or r.get("dataset")
                        or r.get("url")
                        or r.get("source_file"),
                    }
                    for r in (prov.get("key_refs") or [])
                ]
            if s.get("id") == 4:
                ev = s.get("evidence", {}) or {}
                step["evidence_summary"] = ev
            n9["steps"].append(step)
    else:
        n9["errors"].append("9coeff_4step_flow.json unavailable; 4-step demo degraded")
        errors.append("demo: 9coeff flow snapshot unreadable")
    demo["ninecoeff_4step"] = n9

    # ---- 溫區擬合 fitting (evidence-bounded, doc-listed + analytical schematic) ----
    svg_text, svg_err = read_text(WENQU_FITTING_SVG)
    if svg_err:
        errors.append(f"demo: 溫區擬合 fitting SVG unreadable: {svg_err}")
    sediment_text, sed_err = read_text(WENQU_SEDIMENT)
    if sed_err:
        errors.append(f"demo: 溫區擬合 sediment doc unreadable: {sed_err}")

    # extract short assumption/conclusion bullets from sediment if available (lightweight)
    assumptions = [
        "M1 一維穩態傅立葉積分：Q=(A/L)∫κ(T)dT（分溫階）；κ 依 SSOT valid_range_K（D4=A, 54材/53固定係數；NbTi runtime_polyfit null 排除）。",
        "M2 線性/平均 κ 近似：窄溫區或已知 κ_avg；跨數量級溫區以單點 κ 代替會偏差顯著。",
        "M3 Wiedemann–Franz（ρ=const）：僅正常態金屬低溫彈性散射；介電質/超導態(<Tc)/非彈性散射失效。",
        "M4 積分比回推：L=L_ref(P_ref/P_image)(I_image/I_ref) 僅同構 A_image=A_ref；異構層疊須 Σ_k A_k∫κ_k dT。",
        "M5 mK 條件式安全長度：T_crit≈57.6 mK（f01=5.5 GHz, P|1><1%）；線性/ΔT∝L² 回推為假設敏感示例，非設計定論。",
    ]
    process = [
        "本機蒐證萃取：來源萃取/viz_spec/論文 §3.2（EN/ZH 對齊）。",
        "文獻交叉：arXiv Q1–Q6 + metadata 核對（Raicu 2025, Smith 2020/2024, Krinner 2019, Paluch 2024；W-F 邊界文獻）；有查詢限制揭露。",
        "計算/擬合驗證：解析代入（積分比 1.48→59.2 cm/185 μW；mK 2.8/35.71/7.48 cm）＋ κ∝T^β 剖面敏感度示意；引用 polyfit 可靠度（區間內積分穩定、外推敏感、未重擬合）。",
        "同源 viz 產物（viz_data/html/xlsx generator, Task 5）未產出—以 SVG/表格降級展示。",
    ]
    conclusions = [
        "M1 分溫階傅立葉積分與熱預算：已支持（與主流一致；Raicu/Smith/Krinner 實務對齊）。",
        "κ(T) 9參數擬合與區間內積分：已支持（區間內；SSOT D4=A）；外推/係數詮釋受限。",
        "M3 Wiedemann–Franz：條件支持（僅適用材料/溫區）。",
        "M4 積分比回推：假設相依（代數正確但同構受限，非通用經驗公式）。",
        "M5 mK 線性剖面與安全長度：假設敏感/示例性（不同假設矛盾尺度），不可作設計定論。",
    ]
    calc_rows = [
        ["案例", "條件/輸入", "公式", "結果", "性質"],
        [
            "積分比回推（等功率）",
            "L_ref=0.4 m, P_ref=P_image=125 μW, I_im/I_ref=1.48, 同構A",
            "L=L_ref(P_ref/P_image)(I_im/I_ref)",
            "59.2 cm",
            "doc_listed_example, 假設相依",
        ],
        [
            "積分比回推（等長）",
            "同上, L=L_ref",
            "P_image=P_ref(L_ref/L)(I_im/I_ref)",
            "185.0 μW/ch",
            "doc_listed_example",
        ],
        [
            "mK 安全區（線性）",
            "10→350 mK, T_crit=57.6 mK, L=20 cm, κ=const",
            "x_safe=L(T_crit-T_c)/(T_h-T_c)",
            "2.80 cm",
            "假設敏感示例",
        ],
        [
            "mK 延長（線性）",
            "x_req=5 cm",
            "L_new=x_req(T_h-T_c)/(T_h-T_c)? use (T_h-T_c)/(T_crit-T_c)",
            "35.71 cm",
            "假設敏感示例",
        ],
        [
            "mK 上限（探索式）",
            "ΔT∝L²",
            "L_max=L√((T_crit-T_c)/(T_h-T_c))",
            "7.48 cm",
            "探索式假設",
        ],
        [
            "異構層疊",
            "CF3 7層 300µm vs FPC 11層 144.1µm",
            "消去 A",
            "N/A",
            "須 Σ_k A_k∫κ_k dT",
        ],
    ]
    # fix formula text in row 4 display
    calc_rows[4][2] = "L_new=x_req(T_h-T_c)/(T_crit-T_c)"

    demo["wenqu_fitting"] = {
        "title": "溫區擬合（分溫階導熱）— 計算/擬合 fitting 成果展示",
        "boundary": "證據有界：非新量測；不重擬合 κ(T) 係數；CF3/vendor 僅脈絡；SSOT D4=A；mK/線性回推為假設敏感示例；NbTi runtime_polyfit null 排除。",
        "artifacts": {
            "sediment": "docs/溫區擬合_科學成果沉澱.md",
            "extract": "docs/溫區擬合_物理模型_來源萃取.md",
            "arxiv": "docs/溫區擬合_物理模型_arxiv驗證.md",
            "viz_spec": "docs/溫區擬合_物理模型_viz_spec.md",
            "fitting_svg": "docs/溫區擬合_物理模型_fitting示意圖.svg",
            "viz_snapshot_pending": "docs/溫區擬合_物理模型_viz_data.json/.html/.xlsx（Task 5 未產出）",
        },
        "assumptions": assumptions,
        "process": process,
        "conclusions": conclusions,
        "calculation_table": calc_rows,
        "fitting_svg_inline": svg_text or "",
        "fitting_svg_error": svg_err,
        "sediment_excerpt": (sediment_text or "")[:12000],
    }
    return demo


# ---------- HTML ----------
def render_html(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    # simple self-contained HTML with tabs and pre/code rendering
    title = "Distill Paper Compile — topic-viz (abstract, citation, chapter, reference)"
    css = """
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:0;background:#0b1020;color:#e8ecf7}
    header{padding:16px 20px;border-bottom:1px solid #25304d;background:#0f1630;position:sticky;top:0;z-index:5}
    h1{margin:0;font-size:20px} .sub{color:#9fb0d0;font-size:12px;margin-top:4px}
    .wrap{padding:16px 20px} .tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
    .tab{padding:8px 12px;border:1px solid #2a3657;border-radius:8px;cursor:pointer;background:#121a36;color:#cfe0ff}
    .tab.active{background:#1d2a52;border-color:#4b6cb7}
    .panel{display:none} .panel.active{display:block}
    .card{background:#121a36;border:1px solid #26345a;border-radius:10px;padding:14px;margin-bottom:12px}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}
    .k{color:#9fb0d0;font-size:12px} .v{font-size:18px;font-weight:600}
    pre, .md{white-space:pre-wrap;word-break:break-word;background:#0c1328;border:1px solid #223055;border-radius:8px;padding:12px;overflow:auto;max-height:70vh}
    table{border-collapse:collapse;width:100%;font-size:13px} th,td{border:1px solid #2a3657;padding:6px 8px;vertical-align:top}
    th{background:#182244;text-align:left} .ok{color:#7ee787} .bad{color:#ff9b9b} .warn{color:#ffd37a}
    .pill{display:inline-block;padding:2px 8px;border-radius:999px;border:1px solid #355;font-size:12px;margin-right:6px}
    a{color:#8ab4ff}
    """
    return f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{html.escape(title)}</title>
<style>{css}</style></head>
<body>
<header><h1>{html.escape(title)}</h1>
<div class="sub">Same-source, evidence-bounded compile demo (offline). Order: abstract → citation → chapter → rawdata (Appendix A) → reference → consolidated.</div></header>
<div class="wrap">
  <div class="tabs" id="tabs"></div>
  <div id="panels"></div>
</div>
<script id="data" type="application/json">{payload}</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const   TABS = [
  ['overview','Overview'],
  ['abstract','Abstract'],
  ['citation','Citation & Provenance'],
  ['chapter','Chapters'],
  ['reference','References'],
  ['consolidated','Consolidated Paper'],
  ['rawdata','Raw Data 參照'],
  ['ninecoeff','9參數 4-Step Demo'],
  ['wenqu','溫區擬合 Fitting'],
  ['sources','Sources & Errors']
];
const tabsEl = document.getElementById('tabs');
const panelsEl = document.getElementById('panels');
let active = 'overview';
function esc(s){{return String(s??'').replace(/[&<>]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c]))}}
function render(){{
  tabsEl.innerHTML = TABS.map(([id,lab])=>`<div class="tab ${{id===active?'active':''}}" data-id="${{id}}">${{lab}}</div>`).join('');
  tabsEl.querySelectorAll('.tab').forEach(el=>el.onclick=()=>{{active=el.dataset.id;render();}});
  const S = D.sections||{{}};
  const M = D.meta||{{}};
  const I = D.inputs||{{}};
  const E = D.errors||[];
  const DEMO = D.demo||{{}};
  const N9 = DEMO.ninecoeff_4step||{{}};
  const WQ = DEMO.wenqu_fitting||{{}};
  const ov = `
    <div class="card"><div class="grid">
      <div><div class="k">Compiled at</div><div class="v">${{esc(M.compiled_at||'')}}</div></div>
      <div><div class="k">Compile order</div><div class="v">abstract→citation→chapter→rawdata→reference</div></div>
      <div><div class="k">Source docs</div><div class="v">${{Object.keys(I).length}}</div></div>
      <div><div class="k">Errors/degradations</div><div class="v ${{E.length?'warn':'ok'}}">${{E.length}}</div></div>
      <div><div class="k">Demo</div><div class="v">9coeff 4-Step + 溫區擬合 Fitting</div></div>
    </div></div>
    <div class="card"><b>Policy / boundaries</b><ul>
      <li>Evidence-bounded, same-source; SSOT D4=A (no refit, no invented coefficients/claims).</li>
      <li>54 raw entries (48 log_polynomial, 5 rational_copper, 1 runtime_polyfit), 53 fixed-coeff; <code>NbTi (Cri/oFlex 3)</code> runtime_polyfit, <code>coeffs=null</code>.</li>
      <li>Smith et al. 2024 (doi:10.1109/TASC.2024.3350516, arXiv:2306.13574) verified motivating/comparison context only.</li>
      <li>Target <i>Cryogenics</i> (Elsevier): check latest scope/guidelines/APC/article type before submission; .tex not templated.</li>
      <li><b>Demo integration:</b> 9參數 4-step（same-source snapshot/flow）+ 溫區擬合 fitting（sci-sediment 四區塊＋計算/擬合示意圖）於本平台同源展示（evidence-bounded, 可降級）。</li>
    </ul></div>
    <div class="card"><b>Consolidated output</b><div class="md">${{esc(D.outputs?.consolidated_md||'')}}</div></div>`;
  function srcPanel(){{
    const rows = Object.entries(I).map(([k,v])=>`<tr><td>${{esc(k)}}</td><td>${{esc(v.path)}}</td><td class="${{v.exists?'ok':'bad'}}">${{v.exists?'exists':'missing'}}</td><td>${{esc(v.bytes??'')}}</td></tr>`).join('');
    const errs = E.length? `<ul>${{E.map(e=>`<li class="warn">${{esc(e)}}</li>`).join('')}}</ul>`:'<div class="ok">No compile errors recorded.</div>';
    return `<div class="card"><b>Input sources</b><table><tr><th>key</th><th>path</th><th>status</th><th>bytes</th></tr>${{rows}}</table></div><div class="card"><b>Errors / degradations</b>${{errs}}</div>`;
  }}
  function n9Panel(){{
    const steps = (N9.steps||[]).map(s=>{{
      const refs = (s.key_refs||[]).map(r=>`<li>${{esc(r.title||'')}}${{r.id?` <span class="k">(${{esc(r.id)}})</span>`:''}}</li>`).join('');
      let extra='';
      if(s.id===1 && refs) extra = `<div><b>Key refs</b><ul>${{refs}}</ul></div>`;
      if(s.id===4 && s.evidence_summary){{
        const ev=s.evidence_summary; const rows=Object.entries(ev).map(([k,v])=>`<tr><th>${{esc(k)}}</th><td>${{esc(typeof v==='object'?JSON.stringify(v,null,2):String(v))}}</td></tr>`).join('');
        extra += `<div><b>Evidence summary (Step 4)</b><table>${{rows}}</table></div>`;
      }}
      return `<div class="card"><b>Step ${{esc(s.id)}}. ${{esc(s.title||'')}}</b><div>${{esc(s.goal||'')}}</div>${{extra}}</div>`;
    }}).join('');
    const counts = N9.counts||{{}};
    const cntRows = Object.entries(counts).map(([k,v])=>`<tr><th>${{esc(k)}}</th><td>${{esc(typeof v==='object'?JSON.stringify(v):String(v))}}</td></tr>`).join('');
    const arts = Object.entries(N9.artifacts||{{}}).map(([k,v])=>`<li><b>${{esc(k)}}</b>: <code>${{esc(v)}}</code></li>`).join('');
    const flow = (N9.flow_order||[]).map(x=>`<li>${{esc(x)}}</li>`).join('');
    return `<div class="card"><b>${{esc(N9.title||'9參數 4-Step')}}</b>
      <div class="k">Policy</div><ul><li>D4: ${{esc((N9.policy||{{}}).D4||'')}}</li><li>${{esc((N9.policy||{{}}).boundary||'')}}</li></ul>
      <div class="k">Generated (snapshot)</div><div>${{esc(N9.generated_at||'n/a')}}</div>
      <div class="k" style="margin-top:8px">Flow</div><ol>${{flow||'<li>(n/a)</li>'}}</ol>
    </div>
    <div class="card"><b>Counts / boundary</b><table>${{cntRows||'<tr><td>(n/a)</td></tr>'}}</table></div>
    ${{steps||'<div class="card warn">4-step data unavailable (degraded).</div>'}}
    <div class="card"><b>Artifacts (same-source)</b><ul>${{arts}}</ul></div>`;
  }}
  function wqPanel(){{
    const asm = (WQ.assumptions||[]).map(x=>`<li>${{esc(x)}}</li>`).join('');
    const proc = (WQ.process||[]).map(x=>`<li>${{esc(x)}}</li>`).join('');
    const conc = (WQ.conclusions||[]).map(x=>`<li>${{esc(x)}}</li>`).join('');
    const rows = (WQ.calculation_table||[]);
    let tbl='';
    if(rows.length){{
      const head = rows[0].map(h=>`<th>${{esc(h)}}</th>`).join('');
      const body = rows.slice(1).map(r=>`<tr>${{r.map(c=>`<td>${{esc(c)}}</td>`).join('')}}</tr>`).join('');
      tbl = `<table><tr>${{head}}</tr>${{body}}</table>`;
    }}
    const arts = Object.entries(WQ.artifacts||{{}}).map(([k,v])=>`<li><b>${{esc(k)}}</b>: <code>${{esc(v)}}</code></li>`).join('');
    const svg = WQ.fitting_svg_inline ? `<div style="overflow:auto;border:1px solid #223055;border-radius:8px;background:#fff;padding:8px">${{WQ.fitting_svg_inline}}</div>` : `<div class="warn">Fitting SVG unavailable${{WQ.fitting_svg_error?': '+esc(WQ.fitting_svg_error):''}} (degraded).</div>`;
    return `<div class="card"><b>${{esc(WQ.title||'溫區擬合 fitting')}}</b>
      <div class="pill warn">evidence-bounded</div><div class="pill">same-source demo</div>
      <p>${{esc(WQ.boundary||'')}}</p></div>
    <div class="card"><b>1. 模型假設 (Model Assumptions)</b><ul>${{asm}}</ul></div>
    <div class="card"><b>2. 驗證過程 (Verification Process)</b><ul>${{proc}}</ul></div>
    <div class="card"><b>3. 驗證結論 (Verification Conclusion)</b><ul>${{conc}}</ul></div>
    <div class="card"><b>4. 計算/擬合 fitting 圖表 (Calculation & Fitting)</b>
      <p class="k">Panel A–C：溫度剖面假設敏感度、mK 安全長度回推對照、積分比長度/熱負載回推（doc-listed + analytical schematic；非新量測、非 SSOT mK 外推、未重擬合）。</p>
      ${{svg}}
      <h4 style="margin:12px 0 6px">計算表（doc-listed）</h4>
      ${{tbl}}
    </div>
    <div class="card"><b>Artifacts</b><ul>${{arts}}</ul>
      <details><summary>科學成果沉澱節錄（source）</summary><div class="md">${{esc((WQ.sediment_excerpt||'').slice(0,8000))}}</div></details>
    </div>`;
  }}

  const panels = {{
    overview: ov,
    abstract: `<div class="card"><b>Abstract</b><div class="md">${{esc(S.abstract||'')}}</div></div>`,
    citation: `<div class="card"><b>Citation & Provenance (compiled)</b><div class="md">${{esc(S.citation||'')}}</div></div>`,
    chapter: `<div class="card"><b>Chapters (compiled, 1–8)</b><div class="md">${{esc(S.chapter||'')}}</div></div>`,
    reference: `<div class="card"><b>References (compiled)</b><div class="md">${{esc(S.reference||'')}}</div></div>`,
    consolidated: `<div class="card"><b>Consolidated merged paper</b><div class="md">${{esc(S.consolidated||'')}}</div></div>`,
    rawdata: `<div class="card"><b>附錄 A. SSOT 原始係數參照資料（54 筆）</b>
      <div class="pill">same-source</div><div class="pill warn">reference only, no refit</div>
      <p class="k">來源 `docs/9coeff_4step_flow.json` → `steps[id=1].database.raw_materials`；48 `log_polynomial` / 5 `rational_copper` / 1 `runtime_polyfit`；`NbTi (Cri/oFlex 3)` 為 `runtime_polyfit`、`coeffs=null`（不賦予係數、排除於固定係數數值關係）。</p>
      <div class="md">${{esc(S.rawdata||'raw data unavailable (degraded)')}}</div></div>`,
    ninecoeff: n9Panel(),
    wenqu: wqPanel(),
    sources: srcPanel()
  }};
  panelsEl.innerHTML = TABS.map(([id])=>`<div class="panel ${{id===active?'active':''}}">${{panels[id]||''}}</div>`).join('');
}}
render();
</script>
</body></html>
"""


# ---------- minimal XLSX (stdlib) ----------
def xlsx_col(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def sheet_xml(rows: list[list]):
    # rows: list of list of (value, type) where type in {'s','n','inline'}
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
        "<sheetData>",
    ]
    for r_idx, row in enumerate(rows, 1):
        out.append(f'<row r="{r_idx}">')
        for c_idx, cell in enumerate(row, 1):
            ref = f"{xlsx_col(c_idx)}{r_idx}"
            if cell is None:
                continue
            if isinstance(cell, (int, float)) and not isinstance(cell, bool):
                out.append(f'<c r="{ref}"><v>{cell}</v></c>')
            else:
                txt = xml_escape(str(cell))
                out.append(
                    f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{txt}</t></is></c>'
                )
        out.append("</row>")
    out.append("</sheetData></worksheet>")
    return "".join(out)


def build_xlsx(path: Path, sheets: dict[str, list[list]]):
    sheet_names = list(sheets.keys())
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            + "".join(
                f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                for i in range(len(sheet_names))
            )
            + '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            "</Types>",
        )
        z.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>",
        )
        wb_sheets = "".join(
            f'<sheet name="{xml_escape(name)}" sheetId="{i + 1}" r:id="rId{i + 1}"/>'
            for i, name in enumerate(sheet_names)
        )
        z.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f"<sheets>{wb_sheets}</sheets></workbook>",
        )
        rels = (
            "".join(
                f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i + 1}.xml"/>'
                for i in range(len(sheet_names))
            )
            + f'<Relationship Id="rId{len(sheet_names) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        )
        z.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{rels}</Relationships>',
        )
        z.writestr(
            "xl/styles.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
            '<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>'
            '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
            "</styleSheet>",
        )
        for i, name in enumerate(sheet_names, 1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", sheet_xml(sheets[name]))


def make_xlsx_rows(data: dict) -> dict[str, list[list]]:
    I = data.get("inputs", {})
    S = data.get("sections", {})
    E = data.get("errors", [])
    DEMO = data.get("demo", {}) or {}
    overview = [
        ["Field", "Value"],
        ["compiled_at", data.get("meta", {}).get("compiled_at")],
        ["compile_order", "abstract, citation, chapter, rawdata, reference"],
        [
            "rawdata_reference",
            "Appendix A / sections.rawdata — 54 SSOT raw rows embedded same-source (reference only, no refit)",
        ],
        ["policy", "SSOT D4=A; no refit; no invented coefficients/claims"],
        [
            "counts",
            "54 raw (48 log_polynomial,5 rational_copper,1 runtime_polyfit), 53 fixed-coeff; NbTi runtime_polyfit coeffs=null",
        ],
        [
            "target",
            "Cryogenics (Elsevier), check latest scope/guidelines/APC/article type before submission",
        ],
        [
            "demo_integration",
            "9參數 4-step (same-source) + 溫區擬合 fitting (sci-sediment, evidence-bounded)",
        ],
        ["consolidated_output", data.get("outputs", {}).get("consolidated_md")],
        ["errors_count", len(E)],
    ]
    sources = [["key", "path", "exists", "bytes", "mtime_or_error"]]
    for k, v in I.items():
        sources.append(
            [
                k,
                v.get("path"),
                str(v.get("exists")),
                v.get("bytes", ""),
                v.get("mtime") or v.get("error") or "",
            ]
        )
    errs = [["error_or_degradation"]] + ([[e] for e in E] or [["(none)"]])

    def text_sheet(title: str, text: str):
        rows = [[title]]
        for line in (text or "").splitlines():
            rows.append([line])
        return rows

    # 9coeff 4-step demo sheet
    n9 = DEMO.get("ninecoeff_4step", {}) or {}
    n9_rows = [
        ["9參數 4-Step Demo (same-source)"],
        ["title", n9.get("title", "")],
        ["generated_at", n9.get("generated_at", "")],
        ["D4", (n9.get("policy") or {}).get("D4", "")],
        ["boundary", (n9.get("policy") or {}).get("boundary", "")],
        [],
    ]
    n9_rows.append(["Counts/Boundary", "Value"])
    for k, v in (n9.get("counts") or {}).items():
        n9_rows.append(
            [
                k,
                json.dumps(v, ensure_ascii=False)
                if isinstance(v, (dict, list))
                else str(v),
            ]
        )
    n9_rows.append([])
    n9_rows.append(["Step", "Title", "Goal"])
    for s in n9.get("steps") or []:
        n9_rows.append([s.get("id", ""), s.get("title", ""), s.get("goal", "")])
    n9_rows.append([])
    n9_rows.append(["Artifacts", "Path"])
    for k, v in (n9.get("artifacts") or {}).items():
        n9_rows.append([k, v])

    # 溫區擬合 fitting sheet
    wq = DEMO.get("wenqu_fitting", {}) or {}
    wq_rows = [
        ["溫區擬合 fitting — 科學成果展示 (evidence-bounded)"],
        ["title", wq.get("title", "")],
        ["boundary", wq.get("boundary", "")],
        [],
    ]
    wq_rows.append(["1. 模型假設", ""])
    for a in wq.get("assumptions") or []:
        wq_rows.append(["", a])
    wq_rows.append([])
    wq_rows.append(["2. 驗證過程", ""])
    for p in wq.get("process") or []:
        wq_rows.append(["", p])
    wq_rows.append([])
    wq_rows.append(["3. 驗證結論", ""])
    for c in wq.get("conclusions") or []:
        wq_rows.append(["", c])
    wq_rows.append([])
    wq_rows.append(["4. 計算/擬合 fitting 圖表/表", ""])
    wq_rows.append(["fitting_svg", (wq.get("artifacts") or {}).get("fitting_svg", "")])
    wq_rows.append(["note", "Panel A-C 互動圖見 HTML; 本表提供 doc-listed 計算值"])
    for row in wq.get("calculation_table") or []:
        wq_rows.append(row)
    wq_rows.append([])
    wq_rows.append(["Artifacts", "Path"])
    for k, v in (wq.get("artifacts") or {}).items():
        wq_rows.append([k, v])

    # RawData_SSOT sheet (54 rows, same-source reference; no refit)
    raw_payload = DEMO.get("rawdata_ssot", {}) or {}
    raw_cols = raw_payload.get("columns") or (
        ["material", "equation_type", "valid_range_K"]
        + [f"c{i}" for i in range(9)]
        + ["source", "note"]
    )
    rawdata_rows: list[list] = [
        ["RawData_SSOT — SSOT 原始係數參照資料（same-source, reference only）"],
        ["source", raw_payload.get("source", "")],
        ["count", raw_payload.get("count", "")],
        ["boundary", raw_payload.get("boundary", "")],
        [],
        list(raw_cols),
    ]
    for r in raw_payload.get("rows") or []:
        rawdata_rows.append([r.get(c) for c in raw_cols])
    if not raw_payload.get("rows"):
        rawdata_rows.append(["raw data unavailable (degraded)"])

    return {
        "Overview": overview,
        "Sources": sources,
        "Errors": errs,
        "Abstract": text_sheet("Abstract (compiled)", S.get("abstract", "")),
        "Citation": text_sheet(
            "Citation & Provenance (compiled)", S.get("citation", "")
        ),
        "Chapters": text_sheet("Chapters 1-8 (compiled)", S.get("chapter", "")),
        "References": text_sheet("References (compiled)", S.get("reference", "")),
        "RawData_SSOT": rawdata_rows,
        "9coeff_4Step": n9_rows,
        "溫區擬合_Fitting": wq_rows,
        "Consolidated": text_sheet(
            "Consolidated merged paper", S.get("consolidated", "")
        ),
    }


def main() -> int:
    errors: list[str] = []
    inputs = collect_inputs(errors)
    flow, e = read_json(FLOW_JSON)
    (errors.append(f"flow_snapshot: {e}") if e else None)
    reliab, e = read_json(RELIAB_JSON)
    (errors.append(f"reliability_json: {e}") if e else None)
    paper_text, e = read_text(PAPER_MD)
    (errors.append(f"paper_md: {e}") if e else None)
    paper_zh_text, e = read_text(PAPER_ZH_MD)
    (errors.append(f"paper_zh_md: {e}") if e else None)
    journal_text, e = read_text(JOURNAL_MD)
    (errors.append(f"journal_candidates: {e}") if e else None)

    abstract = build_abstract_section(paper_text or "", errors, lang="en")
    citation = build_citation_section(flow, journal_text, paper_text, errors)
    chapters = build_chapters_section(paper_text or "", errors, lang="en")
    rawdata = build_rawdata_section(flow, errors, lang="en")
    references = build_reference_section(paper_text or "", errors, lang="en")
    availability = build_availability(flow, inputs)

    abstract_zh = build_abstract_section(paper_zh_text or "", errors, lang="zh")
    chapters_zh = build_chapters_section(paper_zh_text or "", errors, lang="zh")
    rawdata_zh = build_rawdata_section(flow, errors, lang="zh")
    references_zh = build_reference_section(paper_zh_text or "", errors, lang="zh")

    demo = build_demo_section(flow, errors)

    # Raw SSOT rows (same-source) for the XLSX sheet + machine-readable snapshot
    raw_rows, raw_err = collect_raw_materials(flow)
    if raw_err:
        (errors.append(f"rawdata xlsx degraded: {raw_err}") if raw_err else None)
    raw_columns = (
        ["material", "equation_type", "valid_range_K"]
        + [f"c{i}" for i in range(9)]
        + ["source", "note"]
    )
    demo["rawdata_ssot"] = {
        "source": "docs/9coeff_4step_flow.json → steps[id==1].database.raw_materials",
        "count": len(raw_rows),
        "boundary": (
            "參照資料：非新量測、非重擬合、不編造係數；"
            "`NbTi (Cri/oFlex 3)` 為 `runtime_polyfit` 且 `coeffs=null`（不賦予係數、排除於固定係數數值關係）；"
            "`valid_range_K` 於快照為 null 者原樣保留、不代填。"
            if not raw_err
            else f"raw data unavailable (degraded): {raw_err}"
        ),
        "columns": raw_columns,
        "rows": [
            {
                "material": r.get("material"),
                "equation_type": r.get("equation_type"),
                "valid_range_K": r.get("valid_range_K"),
                **{
                    f"c{i}": (
                        r.get(f"c{i}")
                        if r.get(f"c{i}") is not None
                        else (
                            "null (runtime_polyfit)"
                            if r.get("equation_type") == "runtime_polyfit"
                            else None
                        )
                    )
                    for i in range(9)
                },
                "source": r.get("source"),
                "note": r.get("note"),
            }
            for r in raw_rows
        ],
    }

    meta = {
        "compiled_at": datetime.now(timezone.utc).isoformat(),
        "generator": "scripts/distill_paper_compile_viz.py",
        "topic_viz_format": "F (mixed: spec + same-source snapshot + offline HTML + Excel + consolidated merge + demo integration)",
        "compile_order": ["abstract", "citation", "chapter", "rawdata", "reference"],
        "rawdata_reference": True,
        "rawdata_entries": len(raw_rows),
        "rawdata_boundary": (
            "Appendix A reference data only: same-source SSOT rows (no new measurement, no refit, "
            "no invented coefficients); NbTi (Cri/oFlex 3) runtime_polyfit coeffs=null excluded from fixed-coefficient relations"
        ),
        "demo_integration": [
            "9coeff_4step (same-source)",
            "溫區擬合_fitting (sci-sediment, evidence-bounded)",
        ],
        "policy": {
            "D4": "A (heatload-coff-nist SSOT only)",
            "no_refit": True,
            "no_invented_coeffs": True,
            "evidence_bounded": True,
        },
        "ssot_counts": {
            "raw_entries": 54,
            "fixed_coeff_entries": 53,
            "runtime_polyfit": 1,
            "nbti": "runtime_polyfit, coeffs=null, excluded from fixed-coefficient numeric relations",
        },
    }

    consolidated = build_consolidated(
        meta, abstract, citation, chapters, rawdata, references, availability, lang="en"
    )
    consolidated_zh = build_consolidated(
        meta,
        abstract_zh,
        citation,
        chapters_zh,
        rawdata_zh,
        references_zh,
        availability,
        lang="zh",
    )
    sections = {
        "abstract": abstract,
        "citation": citation,
        "chapter": chapters,
        "rawdata": rawdata,
        "reference": references,
        "consolidated": consolidated,
        "availability": availability,
    }
    sections_zh = {
        "abstract": abstract_zh,
        "citation": citation,
        "chapter": chapters_zh,
        "rawdata": rawdata_zh,
        "reference": references_zh,
        "consolidated": consolidated_zh,
        "availability": availability,
    }

    data = {
        "meta": meta,
        "inputs": inputs,
        "sections": sections,
        "sections_zh": sections_zh,
        "demo": demo,
        "outputs": {
            "snapshot_json": str(OUT_JSON),
            "demo_html": str(OUT_HTML),
            "demo_xlsx": str(OUT_XLSX),
            "consolidated_md": str(OUT_CONSOLIDATED_MD),
            "consolidated_md_zh": str(OUT_CONSOLIDATED_MD_ZH),
        },
        "errors": errors,
    }

    OUT_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    OUT_HTML.write_text(render_html(data), encoding="utf-8")
    build_xlsx(OUT_XLSX, make_xlsx_rows(data))
    OUT_CONSOLIDATED_MD.write_text(consolidated, encoding="utf-8")
    OUT_CONSOLIDATED_MD_ZH.write_text(consolidated_zh, encoding="utf-8")

    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_HTML}")
    print(f"Wrote {OUT_XLSX}")
    print(f"Wrote {OUT_CONSOLIDATED_MD}")
    print(f"Wrote {OUT_CONSOLIDATED_MD_ZH}")
    if errors:
        print("Errors/degradations:")
        for e in errors:
            print(f" - {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
