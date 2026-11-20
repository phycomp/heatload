"""Charts view for compiled distill paper (same-source, evidence-bounded)."""

from __future__ import annotations

import streamlit as st

from src.data import bar_chart_fallback, fmt_num, log10_safe, show_degradation


def render(bundle: dict) -> None:
    compile_data = bundle.get("compile_data") or {}
    errors = compile_data.get("errors", [])
    reliab = bundle.get("reliab")
    flow = bundle.get("flow")

    st.header("圖表 / Charts")
    st.caption(
        "同源已驗證/彙編證據（compile snapshot / reliability JSON / 4-step flow）。"
        "不重擬合、不編造；外推與條件性結論依來源限制標註。"
        " 圖表與數值證據為語言無關之同源事實，EN/ZH 檢視共用一致資料與邊界。"
    )

    # --- DB composition ---
    st.subheader("1) 係數資料庫組成 (SSOT, same-source)")
    eq = {}
    if flow:
        s1 = next((s for s in flow.get("steps", []) if s.get("id") == 1), {})
        eq = (s1.get("database", {}) or {}).get("equation_types") or {}
    if not eq:
        eq = {"log_polynomial": 48, "rational_copper": 5, "runtime_polyfit": 1}
    bar_chart_fallback(eq, "equation_type counts (54 raw entries)")
    st.markdown(
        "- **53** fixed-coeff materials for numeric relations; **1** `runtime_polyfit` (`NbTi (Cri/oFlex 3)`, `coeffs=null`, excluded).  \n"
        "- Source: `docs/9coeff_4step_flow.json` / SSOT `coeff_data.py` (D4=A)."
    )

    if not reliab:
        st.warning(
            "可靠度圖表來源不可用：`docs/polyfit_可靠度驗證.json` 無法讀取，以下圖表降級。"
        )
        show_degradation(bundle, errors)
        return

    cond = reliab.get("condition", {})
    baseline = reliab.get("baseline_noise1_seed42", {})
    sens = reliab.get("sensitivity_noise_seed", {})

    # --- Conditioning ---
    st.subheader("2) 數值條件數 / Conditioning (ill-conditioning, context-dependent)")
    if cond:
        cond_rows = [
            {
                "metric": "cond(V)_raw",
                "value": cond.get("cond_V_raw"),
                "log10(value)": log10_safe(cond.get("cond_V_raw")),
            },
            {
                "metric": "cond(V^T V)_raw",
                "value": cond.get("cond_VTV_raw"),
                "log10(value)": log10_safe(cond.get("cond_VTV_raw")),
            },
            {
                "metric": "cond(V_centered_scaled)",
                "value": cond.get("cond_V_centered_scaled"),
                "log10(value)": log10_safe(cond.get("cond_V_centered_scaled")),
            },
        ]
        st.table(
            [
                {
                    k: fmt_num(v)
                    if k != "log10(value)"
                    else (f"{v:.4f}" if isinstance(v, (int, float)) else "N/A")
                    for k, v in r.items()
                }
                for r in cond_rows
            ]
        )
        log_data = {
            r["metric"]: r["log10(value)"]
            for r in cond_rows
            if isinstance(r.get("log10(value)"), (int, float))
        }
        if log_data:
            bar_chart_fallback(
                log_data, "log10(condition number) — for scale visualization only"
            )
        st.caption(
            "Raw monomial basis ill-conditioned; centering/scaling improves conditioning in reported setup. "
            "Condition numbers depend on implementation/definition/source/range/scaling (not directly comparable across setups). "
            f"Generator: {reliab.get('generator', '')}, HAVE_SCIPY={reliab.get('have_scipy')}."
        )
    else:
        st.info("Conditioning data unavailable.")

    # --- Baseline metrics ---
    st.subheader("3) 基準擬合指標 (noise=1%, seed=42, conditional evidence)")
    b_kap = baseline.get("kapton", {})
    b_nbt = baseline.get("nbti", {})
    if b_kap and b_nbt:
        mcols = st.columns(4)
        metrics_def = [
            ("R²", "r2"),
            ("RMSE (log10)", "rmse_log10"),
            ("∫₂³⁰⁰ κ dT (W/m)", "integral_2_300K"),
            ("k(20 mK) (W/m/K)", "k_at_20mK"),
        ]
        for col, (label, key) in zip(mcols, metrics_def):
            with col:
                st.markdown(f"**{label}**")
                st.write(f"Kapton: `{fmt_num(b_kap.get(key))}`")
                st.write(f"NbTi: `{fmt_num(b_nbt.get(key))}`")

        r2 = {"Kapton": b_kap.get("r2", 0), "NbTi": b_nbt.get("r2", 0)}
        rmse = {
            "Kapton": b_kap.get("rmse_log10", 0),
            "NbTi": b_nbt.get("rmse_log10", 0),
        }
        integ = {
            "Kapton": b_kap.get("integral_2_300K", 0),
            "NbTi": b_nbt.get("integral_2_300K", 0),
        }
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**R² (in-range fit)**")
            bar_chart_fallback(r2)
        with c2:
            st.markdown("**RMSE (log10)**")
            bar_chart_fallback(rmse)
        with c3:
            st.markdown("**∫₂³⁰⁰ κ dT (W/m, comparatively stable in-range)**")
            bar_chart_fallback(integ)

        st.markdown("**k(20 mK) — deep extrapolation (indicator only, NOT reliable)**")
        k20_log = {
            "Kapton log10": log10_safe(b_kap.get("k_at_20mK")),
            "NbTi log10": log10_safe(b_nbt.get("k_at_20mK")),
        }
        k20_log = {k: v for k, v in k20_log.items() if isinstance(v, (int, float))}
        if k20_log:
            bar_chart_fallback(k20_log, "log10(k at 20 mK)) — far outside fit range")
        st.warning(
            "k(20 mK) values are deep-low-temperature extrapolations and highly sensitive to perturbations/fitting/process; "
            "treat only as conservative order-of-magnitude indicators, not predictions."
        )
        tc = b_nbt.get("tc_region") or {}
        if tc.get("max_abs_resid_log10") is not None:
            st.info(
                f"NbTi Tc-region structural residual (global 8th-order): max |resid_log10| = {fmt_num(tc.get('max_abs_resid_log10'))} "
                f"(reported points in ~7.5–12.5 K region) — model-form limitation, not a refit."
            )
    else:
        st.info("Baseline metrics unavailable.")

    # --- Sensitivity ---
    st.subheader("4) 擾動敏感度 (noise ∈ {0,1,2,5}%, 6 seeds, 24 runs/material)")
    s_kap = sens.get("kapton", {})
    s_nbt = sens.get("nbti", {})
    if s_kap and s_nbt:
        st.markdown("**∫₂³⁰⁰ κ dT 範圍 (比較穩定, in-range, conditional)**")
        st.table(
            [
                {
                    "material": "Kapton",
                    "min": fmt_num(s_kap.get("integral_min")),
                    "max": fmt_num(s_kap.get("integral_max")),
                },
                {
                    "material": "NbTi",
                    "min": fmt_num(s_nbt.get("integral_min")),
                    "max": fmt_num(s_nbt.get("integral_max")),
                },
            ]
        )
        integ_range = {
            "Kapton min": s_kap.get("integral_min", 0),
            "Kapton max": s_kap.get("integral_max", 0),
            "NbTi min": s_nbt.get("integral_min", 0),
            "NbTi max": s_nbt.get("integral_max", 0),
        }
        bar_chart_fallback(integ_range)

        st.markdown("**k(20 mK) 範圍 (深低溫外推，高敏感，僅量級示意)**")
        st.table(
            [
                {
                    "material": "Kapton",
                    "min": fmt_num(s_kap.get("k20mK_min")),
                    "max": fmt_num(s_kap.get("k20mK_max")),
                    "note": "extrapolation indicator only",
                },
                {
                    "material": "NbTi",
                    "min": fmt_num(s_nbt.get("k20mK_min")),
                    "max": fmt_num(s_nbt.get("k20mK_max")),
                    "note": "extrapolation indicator only",
                },
            ]
        )
        klog = {
            "Kapton min log10": log10_safe(s_kap.get("k20mK_min")),
            "Kapton max log10": log10_safe(s_kap.get("k20mK_max")),
            "NbTi min log10": log10_safe(s_nbt.get("k20mK_min")),
            "NbTi max log10": log10_safe(s_nbt.get("k20mK_max")),
        }
        klog = {k: v for k, v in klog.items() if isinstance(v, (int, float))}
        if klog:
            bar_chart_fallback(
                klog, "log10(k20mK) ranges — extrapolation, not reliable prediction"
            )
        st.caption(
            "Within reported protocol, in-range integrals comparatively stable; k(20 mK) varied (~factor ~2 in runs) but remains "
            "far outside fit range and process-sensitive. Results do not generalize without further validation."
        )
    else:
        st.info("Sensitivity data unavailable.")

    # --- provenance checks ---
    st.subheader("5) 係數/狀態溯源檢查 (provenance checks)")
    kap_cmp = reliab.get("kapton_coeffdata_compare", {})
    nbti_status = reliab.get("nbti_coeffdata_status", {})
    if kap_cmp:
        st.markdown(
            f"- **Kapton stored vs validation-fit:** max |Δc| ≈ `{fmt_num(kap_cmp.get('max_abs_diff'))}` "
            f"(process/generator dependence; reinforces provenance requirements)."
        )
    if nbti_status:
        st.markdown(
            f"- **NbTi (Cri/oFlex 3):** equation_type=`{nbti_status.get('equation_type')}`, "
            f"coeffs=`{nbti_status.get('coeffs')}` (runtime_polyfit, not fixed; excluded from fixed-coeff numeric relations)."
        )
        src = nbti_status.get("source")
        if src:
            st.caption(f"SSOT note: {src}")

    st.divider()
    st.caption(
        "Chart sources: `docs/polyfit_可靠度驗證.json`, `docs/9coeff_4step_flow.json`, `docs/distill_paper_compile_data.json` "
        "(same-origin). Limitations: conditional protocol, no-refit/no-invention, extrapolation not predictive."
    )
    show_degradation(bundle, errors)
