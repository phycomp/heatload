#!/usr/bin/env python3
"""Streamlit demo for 9-coeff heatload 4-step flow (topic-viz, distill docs).

Default: Streamlit visualization driven by same-source snapshot.
Opens distilled documents (spec, validation, derivations, provenance sources).
Policy: D4=A (heatload-coff-nist SSOT), no refit/invented coeffs.
Graceful degradation when files/data unavailable.

Run:
  cd ~/量傳線 && streamlit run scripts/9coeff_4step_streamlit_demo.py
"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

# Resolve project root (~/量傳線) whether run from scripts/ or 熱負載/pages/
_THIS = Path(__file__).resolve()


def _find_root() -> Path:
    for p in [
        _THIS.parent,
        _THIS.parent.parent,
        _THIS.parent.parent.parent,
        Path.cwd(),
    ]:
        if (
            (p / "docs" / "9coeff_4step_flow.json").exists()
            or (p / "docs").is_dir()
            and (p / "scripts").is_dir()
        ):
            return p
    return Path.cwd()


ROOT = _find_root()
DOCS = ROOT / "docs"
SNAP_PATH = DOCS / "9coeff_4step_flow.json"
SPEC_PATH = DOCS / "9coeff_4step_視覺化規格.md"
RELIAB_MD = DOCS / "polyfit_可靠度驗證.md"
RELIAB_JSON = DOCS / "polyfit_可靠度驗證.json"
HTML_PATH = DOCS / "9coeff_4step_demo.html"
XLSX_PATH = DOCS / "9coeff_4step_demo.xlsx"
SKILL_ROOT = Path("/home/sam/.opencode/skills/heatload-coff-nist")

st.set_page_config(page_title="9coeff 4-step flow | topic-viz", layout="wide")
st.title("9 係數熱負載 4 步驟流程 — 視覺化與演示 (Streamlit)")
st.caption(
    "topic-viz: 同源快照驅動、規格先行、離線可追溯、可降級 | D4=A SSOT，不重擬合/不編造係數"
)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as e:
        return None, str(e)


def read_text(path: Path):
    try:
        return path.read_text(encoding="utf-8"), None
    except Exception as e:
        return None, str(e)


snap, snap_err = load_json(SNAP_PATH)

with st.sidebar:
    st.header("導航")
    page = st.radio(
        "預設展示",
        [
            "總覽 (4-step)",
            "Step 1 論文暨材料資料庫",
            "Step 2 物理推導9個參數",
            "Step 3 矩陣運算得出9參數",
            "Step 4 polyfit去驗證",
            "開啟 distill 文件",
        ],
        index=0,
    )
    st.divider()
    st.subheader("產物")
    for label, p in [
        ("規格", SPEC_PATH),
        ("快照", SNAP_PATH),
        ("HTML", HTML_PATH),
        ("XLSX", XLSX_PATH),
        ("polyfit驗證.md", RELIAB_MD),
        ("polyfit驗證.json", RELIAB_JSON),
    ]:
        st.write(("✅ " if p.exists() else "⚠️ ") + f"{label}: `{p}`")
    if snap_err:
        st.error(f"快照讀取失敗: {snap_err}")


def show_errors(errors):
    if errors:
        st.warning("降級/錯誤紀錄 (errors)")
        for e in errors:
            st.write("- ", e)


def fmt(v):
    if v is None:
        return ""
    if isinstance(v, float):
        av = abs(v)
        if av == 0:
            return "0"
        if av >= 1e4 or (av != 0 and av < 1e-3):
            return f"{v:.4e}"
        return f"{v:.6g}"
    return v


if not snap:
    st.error(
        "找不到或無法讀取同源快照 docs/9coeff_4step_flow.json。請先執行: `python3 scripts/9coeff_4step_viz.py`"
    )
    st.stop()

meta = snap.get("meta", {})
steps = {s.get("id"): s for s in snap.get("steps", [])}
errors = snap.get("errors", [])

if page == "總覽 (4-step)":
    st.subheader("流程")
    cols = st.columns(4)
    flow = meta.get("flow", [])
    titles = [
        "1.研究論文暨材料資料庫",
        "2.物理推導9個參數",
        "3.矩陣運算 得出9個參數",
        "4.polyfit去驗證",
    ]
    for i, c in enumerate(cols):
        c.markdown(f"**Step {i + 1}**  \n{titles[i]}")
        if i < 3:
            c.caption("→")
    st.info(
        "政策: "
        + str(meta.get("policy", {}).get("D4", ""))
        + "；"
        + str(meta.get("policy", {}).get("no_invention", ""))
    )
    show_errors(errors)
    st.subheader("架構/資料流 (同源)")
    st.code(
        "1.研究論文暨材料資料庫 (citations + coefficient_table + coeff_data)\n"
        "  -> 2.物理推導9參數 (log10 κ=Σ c_n(log10 T)^n, Q_solid/Q_rf)\n"
        "  -> 3.矩陣運算得9參數 (Vandermonde, X^T X c=X^T y, 條件數/縮放)\n"
        "  -> 4.polyfit驗證 (R²/RMSE/敏感度/Tc殘差/外推限制)\n"
        "  => docs/9coeff_4step_flow.json (同源快照) => demo.html + demo.xlsx + Streamlit",
        language="text",
    )
    st.subheader("各步驟目標")
    for sid in [1, 2, 3, 4]:
        s = steps.get(sid, {})
        with st.expander(f"Step {sid}: {s.get('title', '')}"):
            st.write(s.get("goal", ""))
    st.subheader("開啟 distill 文件 (快速入口)")
    spec_text, _ = read_text(SPEC_PATH)
    if spec_text:
        with st.expander("9coeff_4step_視覺化規格.md (distill spec)", expanded=True):
            st.markdown(spec_text)
    else:
        st.warning(f"缺少規格檔: {SPEC_PATH}")

elif page == "Step 1 論文暨材料資料庫":
    s1 = steps.get(1, {})
    st.header("Step 1：研究論文暨材料資料庫")
    st.write(s1.get("goal", ""))
    prov = s1.get("provenance", {})
    refs = prov.get("key_refs", [])
    db = s1.get("database", {})

    tab_prov, tab_summary, tab_raw, tab_samples = st.tabs(
        [
            "a.上級論文/資料庫出處",
            "b.係數資料庫摘要 (SSOT)",
            "c.資料庫原始資料 (raw data)",
            "d.重點材料/係數樣本 (索引)",
        ]
    )

    with tab_prov:
        st.subheader("上級論文/資料庫出處")
        if refs:
            st.table(
                [
                    {
                        "出處": r.get("title", ""),
                        "識別/連結": r.get("doi")
                        or r.get("url")
                        or r.get("dataset")
                        or r.get("source_file", ""),
                        "內容": r.get("content", ""),
                    }
                    for r in refs
                ]
            )
        else:
            st.info("無出處摘要 (降級)")

    with tab_summary:
        st.subheader("係數資料庫摘要 (SSOT)")
        c1, c2, c3 = st.columns(3)
        c1.metric("coeff_data 筆數", db.get("material_count_coeff_data", "?"))
        c2.metric("CSV 筆數", db.get("material_count_csv", "?"))
        c3.metric("equation_types", len(db.get("equation_types", {}) or {}))
        st.json(
            {
                "equation_types": db.get("equation_types"),
                "categories": db.get("categories"),
            }
        )
        st.caption("SSOT: " + ", ".join(db.get("ssot_paths", [])))

    with tab_raw:
        st.subheader("資料庫原始資料 (raw data)")
        raw_materials = db.get("raw_materials", [])
        if raw_materials:
            # present full raw rows; keep coeffs_c0_c8 visible as list too
            display_rows = []
            for r in raw_materials:
                row = {
                    "material": r.get("material"),
                    "equation_type": r.get("equation_type"),
                    "valid_range_K": r.get("valid_range_K"),
                    "category/quantity": r.get("category") or r.get("quantity"),
                    "c0": r.get("c0"),
                    "c1": r.get("c1"),
                    "c2": r.get("c2"),
                    "c3": r.get("c3"),
                    "c4": r.get("c4"),
                    "c5": r.get("c5"),
                    "c6": r.get("c6"),
                    "c7": r.get("c7"),
                    "c8": r.get("c8"),
                    "coeffs_c0_c8": r.get("coeffs_c0_c8"),
                    "source": r.get("source"),
                    "note": r.get("note"),
                }
                display_rows.append(row)
            st.dataframe(display_rows, width="stretch", height=500)
            st.caption(
                f"共 {len(raw_materials)} 筆原始資料列（含 c0..c8），來源 SSOT；NbTi 為 runtime_polyfit 時 coeffs=null。"
            )
        else:
            st.info("無原始資料列 (降級：請確認快照含 database.raw_materials 並重產生)")

    with tab_samples:
        st.subheader("重點材料/係數樣本 (索引)")
        samples = db.get("key_samples", [])
        if samples:
            st.dataframe(samples, width="stretch")
        else:
            st.info("無樣本")

    show_errors(errors)

elif page == "Step 2 物理推導9個參數":
    s2 = steps.get(2, {})
    st.header("Step 2：物理推導 9 個參數")
    st.write(s2.get("goal", ""))
    model = s2.get("model", {})
    lp = model.get("log_polynomial", {})
    st.subheader("log-log polynomial (9 係數)")
    st.latex(
        r"\log_{10}\kappa(T)=c_0+c_1\log_{10}T+c_2(\log_{10}T)^2+\cdots+c_8(\log_{10}T)^8"
    )
    st.latex(r"\kappa(T)=10^{\sum_{n=0}^{8} c_n (\log_{10}T)^n}\quad (\mathrm{W/m/K})")
    st.write(
        {
            "參數": lp.get("params"),
            "單位": lp.get("units"),
            "範圍/政策": lp.get("validity"),
        }
    )
    rc = model.get("rational_copper", {})
    st.subheader("rational_copper (OFHC Cu 例外)")
    st.latex(
        r"\log_{10}\kappa=\frac{a+cT^{1/2}+eT+gT^{3/2}+iT^2}{1+bT^{1/2}+dT+fT^{3/2}+hT^2},\ (a..i)=(c_0..c_8)"
    )
    hl = model.get("heatload", {})
    st.subheader("熱負載積分模型")
    st.latex(
        r"Q_{solid}=\sum_j \frac{A}{L_j}\int_{T_{cold,j}}^{T_{hot,j}}\kappa(T)\,dT"
    )
    st.latex(
        r"Q_{rf}=\sum_j P_{in}\left(1-10^{-\alpha_j/10}\right),\quad Q_{total}=Q_{solid}+Q_{rf}"
    )
    st.code(
        f"Q_solid: {hl.get('solid_conduction')}\nQ_rf: {hl.get('attenuator_dissipation')}\nQ_total: {hl.get('total')}",
        language="text",
    )
    st.subheader("推導要點 (依來源)")
    for p in s2.get("derivation_points", []):
        st.markdown(f"- {p}")
    st.caption("來源: " + " | ".join(s2.get("source_refs", [])))

elif page == "Step 3 矩陣運算得出9參數":
    s3 = steps.get(3, {})
    st.header("Step 3：矩陣運算 得出 9 個參數")
    st.write(s3.get("goal", ""))

    tab_deriv, tab_mean, tab_cond, tab_rel, tab_ex = st.tabs(
        [
            "c0..c8 推導",
            "9 參數物理意義",
            "病態條件與中心化/縮放",
            "9 參數與材料關係",
            "Kapton 係數示例",
        ]
    )

    with tab_deriv:
        st.subheader("c0..c8 推導過程 (最小二乘/正規方程)")
        st.latex(
            r"y_i=\log_{10}\kappa_i,\quad x_i=\log_{10}T_i,\quad y_i\approx\sum_{j=0}^{8}c_j x_i^j"
        )
        st.latex(r"X_{i,j}=x_i^j\ (N\times 9),\quad \min_c S(c)=\|y-Xc\|^2")
        st.latex(r"X^T X\,c = X^T y \;\Rightarrow\; c=(X^T X)^{-1}X^T y")
        deriv = s3.get("derivation_c0_c8", {})
        for step in deriv.get("steps", []):
            st.markdown(f"- {step}")
        if deriv.get("result_form"):
            st.code(deriv.get("result_form"), language="text")
        st.info(s3.get("normal_equation", {}).get("note", ""))

    with tab_mean:
        st.subheader("9 個參數 c0..c8 的物理意義")
        st.caption(s3.get("parameter_meaning_note", ""))
        meanings = s3.get("parameter_meanings_c0_c8", [])
        if meanings:
            st.table(meanings)
        else:
            st.info("無參數物理意義資料 (降級)")

    with tab_cond:
        st.subheader(
            "病態條件 (ill-conditioning) 與中心化/縮放：物理-數值推導與說明（先於圖表）"
        )
        cond_exp = s3.get("conditioning_explanation", {})
        if cond_exp:
            for src in cond_exp.get("source_basis", []):
                st.caption(f"依據: {src}")
            for step in cond_exp.get("derivation_steps", []):
                st.markdown(f"- {step}")
            st.warning(cond_exp.get("condition_number_dependency_note", ""))
        else:
            st.markdown(
                "- 高次冪基底在有限區間上高度相關，使 Vandermonde/Gram 矩陣病態；中心化/縮放可降低條件數。"
            )
            st.warning("條件數數值依實作/定義/來源而異，須依各自來源解讀。")

        st.subheader("條件數示例與圖表 (來源示例)")
        ce = s3.get("conditioning_example", {})
        st.table(
            [
                {
                    "指標": "cond(X)",
                    "值": fmt(ce.get("cond_X")),
                    "來源": ce.get("source", ""),
                },
                {
                    "指標": "cond(X^T X)",
                    "值": fmt(ce.get("cond_XTX")),
                    "來源": ce.get("source", ""),
                },
                {
                    "指標": "縮放",
                    "值": ce.get("scaling", ""),
                    "來源": ce.get("source", ""),
                },
                {
                    "指標": "cond(X_scaled)",
                    "值": fmt(ce.get("cond_X_scaled")),
                    "來源": ce.get("source", ""),
                },
                {
                    "指標": "改善倍數(約)",
                    "值": fmt(ce.get("improvement_factor_approx")),
                    "來源": ce.get("source", ""),
                },
            ]
        )
        st.caption(ce.get("interpretation", ""))
        chart_data = {
            "cond(X)": float(ce.get("cond_X") or 0),
            "cond(X^T X)": float(ce.get("cond_XTX") or 0),
            "cond(X_scaled)": float(ce.get("cond_X_scaled") or 0),
        }
        try:
            import pandas as _pd

            st.bar_chart(_pd.DataFrame({"value": chart_data}))
        except Exception:
            st.bar_chart(chart_data)

    with tab_rel:
        st.subheader("9 參數與材料之關係")
        rel = s3.get("material_coeff_relation", {})
        st.write(rel.get("description", ""))
        rel_rows = rel.get("rows", [])
        if rel_rows:
            st.caption(
                f"納入固定 9 係數材料數: {rel.get('materials_with_fixed_coeffs_count', len(rel_rows))}；"
                f"未納入(無固定係數): {', '.join(rel.get('materials_without_fixed_coeffs', [])) or '無'}"
            )
            coeff_cols = [f"c{i}" for i in range(9)]
            tab_profile, tab_dist, tab_table = st.tabs(
                [
                    "9 參數與材料關係圖表",
                    "各係數 c0..c8 跨材料數值分佈",
                    "資料表：材料 × c0..c8（係數-材料關係原始資料）",
                ]
            )

            with tab_profile:
                left, right = st.columns([3, 7])
                mat_names = [r.get("material") for r in rel_rows]
                sel_row = None
                with left:
                    sel = st.radio(
                        "選擇材料檢視其 c0..c8 係數輪廓",
                        options=mat_names,
                        key="mat_coeff_profile",
                        horizontal=True,
                    )
                    sel_row = next(
                        (r for r in rel_rows if r.get("material") == sel), None
                    )
                    if sel_row:
                        st.caption(
                            f"材料: {sel}  \n"
                            f"equation_type: {sel_row.get('equation_type')}  \n"
                            f"valid_range_K: {sel_row.get('valid_range_K')}  \n"
                            f"source: {sel_row.get('source')}"
                        )

                with right:
                    st.markdown(
                        "**圖表：各材料之 c0..c8 係數分佈（長表，依係數分面檢視）**"
                    )
                    if sel_row:
                        profile = {f"c{i}": sel_row.get(f"c{i}") for i in range(9)}
                        try:
                            import pandas as _pd

                            st.bar_chart(_pd.DataFrame({"value": profile}))
                        except Exception:
                            st.bar_chart(profile)

            with tab_dist:
                st.markdown(
                    "**圖表：各係數 c0..c8 在全部固定係數材料間的數值分佈（箱型替代：依係數索引彙整表/統計）**"
                )
                stats = []
                for c in coeff_cols:
                    vals = [
                        r.get(c) for r in rel_rows if isinstance(r.get(c), (int, float))
                    ]
                    if vals:
                        stats.append(
                            {
                                "coeff": c,
                                "count": len(vals),
                                "min": min(vals),
                                "max": max(vals),
                                "mean": sum(vals) / len(vals),
                            }
                        )
                if stats:
                    st.dataframe(stats, width="stretch")
                    try:
                        import pandas as _pd

                        st.line_chart(
                            _pd.DataFrame(stats).set_index("coeff")[
                                ["min", "mean", "max"]
                            ]
                        )
                    except Exception:
                        pass
                else:
                    st.info("無可用係數統計資料")

            with tab_table:
                st.markdown("**資料表：材料 × c0..c8（係數-材料關係原始資料）**")
                try:
                    import pandas as _pd

                    st.dataframe(_pd.DataFrame(rel_rows), width="stretch", height=400)
                except Exception:
                    st.dataframe(rel_rows, width="stretch", height=400)

            st.caption(rel.get("note", ""))
        else:
            st.info(
                "無材料係數關係資料 (降級：請確認快照含 material_coeff_relation.rows 並重產生)"
            )

    with tab_ex:
        st.subheader("Kapton 係數示例 c0..c8=a..i (來源 md)")
        rexp = s3.get("result_example", {})
        coeffs = rexp.get("coeffs_c0_c8", [])
        if coeffs:
            st.table(
                [
                    {"係數": f"c{i} ({chr(97 + i)})", "值": coeffs[i]}
                    for i in range(len(coeffs))
                ]
            )
        q = rexp.get("quality_reported_in_source", {})
        st.write(
            {
                "R² (來源示例)": q.get("R2"),
                "RMSE_log10": q.get("RMSE_log10"),
                "max|resid|_log10": q.get("max_abs_residual_log10"),
            }
        )
        st.warning(rexp.get("note", ""))

elif page == "Step 4 polyfit去驗證":
    s4 = steps.get(4, {})
    st.header("Step 4：polyfit 去驗證")
    st.write(s4.get("goal", ""))
    st.subheader("條件數 (可靠度驗證)")
    st.json(s4.get("condition", {}))
    base = s4.get("baseline_noise1_seed42", {})
    sens = s4.get("sensitivity_noise_seed", {})
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Kapton baseline (noise=1%, seed=42)**")
        st.json(base.get("kapton", {}))
        st.markdown("**Kapton 敏感度範圍**")
        st.json(sens.get("kapton", {}))
    with c2:
        st.markdown("**NbTi baseline (noise=1%, seed=42)**")
        st.json(base.get("nbti", {}))
        st.markdown("**NbTi 敏感度範圍**")
        st.json(sens.get("nbti", {}))
    st.subheader("Kapton 係數對照 (stored vs fitted)")
    comp = s4.get("kapton_coeffdata_compare", {})
    sc = comp.get("stored_coeffs") or []
    fc = comp.get("fitted_coeffs_noise1_seed42") or []
    ad = comp.get("abs_diff") or []
    rd = comp.get("rel_diff_pct") or []
    rows = []
    for i in range(max(len(sc), len(fc))):
        rows.append(
            {
                "coeff": f"c{i}",
                "stored": sc[i] if i < len(sc) else None,
                "fitted_noise1_seed42": fc[i] if i < len(fc) else None,
                "abs_diff": ad[i] if i < len(ad) else None,
                "rel_diff_%": rd[i] if i < len(rd) else None,
            }
        )
    if rows:
        st.dataframe(rows, width="stretch")
    st.caption(comp.get("stored_source", ""))
    st.subheader("NbTi 狀態")
    st.json(s4.get("nbti_coeffdata_status", {}))
    st.subheader("NbTi Tc 區殘差點 (基準)")
    tc_pts = (base.get("nbti", {}) or {}).get("tc_points", [])
    if tc_pts:
        st.dataframe(tc_pts, width="stretch")
    st.subheader("解讀 / 限制")
    for it in s4.get("interpretation", []):
        st.markdown(f"- {it}")

elif page == "開啟 distill 文件":
    st.header("開啟 distill 文件 (蒸餾/規格/來源)")
    st.caption(
        "預設以 Streamlit 展示；讀取失敗時降級提示。依 distill-showcase：radio 選擇 + 左3右7 佈局。"
    )

    candidates = [
        ("[distill] 9 係數 4 步驟視覺化規格", SPEC_PATH),
        ("[distill] polyfit 可靠度驗證報告", RELIAB_MD),
        ("[data] 9 係數 4 步驟快照 JSON", SNAP_PATH),
        ("[data] polyfit 可靠度驗證 JSON", RELIAB_JSON),
        ("[source] 基礎推導熱負載", ROOT / "熱負載/MDs/基礎推導熱負載.md"),
        ("[source] 推導溫區公式", ROOT / "熱負載/MDs/推導溫區公式.md"),
        ("[source] 推導多項式耦合系數", ROOT / "熱負載/推導多項式耦合系數.md"),
        ("[source] 推導柔性多項式耦合系數", ROOT / "熱負載/推導柔性多項式耦合系數.md"),
        ("[source] 推導柔性八階係數", ROOT / "熱負載/推導柔性八階係數.md"),
        ("[source] NIST9 視覺化規格 (既有)", DOCS / "NIST9_視覺化規格.md"),
        (
            "[provenance] heatload-coff-nist citations",
            SKILL_ROOT / "references/citations.md",
        ),
        (
            "[provenance] heatload-coff-nist coefficient_table",
            SKILL_ROOT / "references/coefficient_table.md",
        ),
        (
            "[provenance] heatload-coff-nist 00_熱負載總覽",
            SKILL_ROOT / "references/00_熱負載總覽.md",
        ),
    ]
    existing = [(label, p) for label, p in candidates if p.exists()]
    missing = [(label, p) for label, p in candidates if not p.exists()]
    labels = [f"{'✅' if p.exists() else '⚠️'} {label}" for label, p in candidates]

    left, right = st.columns([3, 7])
    with left:
        st.subheader("文件列表")
        choice = st.radio(
            "選擇要開啟的文件",
            options=list(range(len(candidates))),
            format_func=lambda i: labels[i],
        )
        st.caption(f"可開啟: {len(existing)} / {len(candidates)}")
        if missing:
            with st.expander("缺少檔案", expanded=False):
                for l, p in missing:
                    st.write(f"- {l}: `{p}`")
        st.divider()
        st.subheader("離線演示產物")
        for name, p in [("HTML demo", HTML_PATH), ("Excel demo", XLSX_PATH)]:
            if p.exists():
                st.success(f"{name}")
                st.caption(str(p))
                try:
                    st.download_button(
                        f"下載 {p.name}",
                        data=p.read_bytes(),
                        file_name=p.name,
                        key=f"dl_{p.name}",
                    )
                except Exception:
                    pass
            else:
                st.warning(f"{name} 不存在")
                st.caption(str(p))

    with right:
        label, path = candidates[choice]
        st.subheader(label)
        st.write(f"路徑: `{path}`")
        if not path.exists():
            st.error("檔案不存在或無法存取 (降級)")
        else:
            text, err = read_text(path)
            if err:
                st.error(f"讀取失敗: {err}")
            else:
                if path.suffix.lower() == ".json":
                    try:
                        st.json(json.loads(text))
                    except Exception:
                        st.code(text, language="json")
                else:
                    st.markdown(text)
        if path == HTML_PATH and path.exists():
            html_text, e = read_text(path)
            if html_text and not e:
                with st.expander("預覽 HTML demo (內嵌)", expanded=False):
                    st.components.v1.html(html_text, height=800, scrolling=True)

st.divider()
st.caption(f"root={ROOT} | snapshot={SNAP_PATH} | errors={len(errors)}")
