#!/usr/bin/env python3
"""Generate Excel workbook version of NIST9 viz demo from nist9_viz_data.json.
Dependency-free (stdlib zipfile+xml). Mirrors demo presentation flow/views.
"""

from __future__ import annotations
import json, math, zipfile
from pathlib import Path
from datetime import datetime, timezone
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "docs" / "nist9_viz_data.json"
OUT_XLSX = ROOT / "docs" / "nist9_viz_demo.xlsx"


def col_letter(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def cell_ref(r: int, c: int) -> str:
    return f"{col_letter(c)}{r}"


def sheet_xml(rows):
    # rows: list[list[value]]; value can be None/str/number/bool
    out = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" ',
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">',
        "<sheetData>",
    ]
    for ri, row in enumerate(rows, start=1):
        if not row:
            continue
        out.append(f'<row r="{ri}">')
        for ci, val in enumerate(row, start=1):
            if val is None or val == "":
                continue
            r = cell_ref(ri, ci)
            if isinstance(val, bool):
                out.append(f'<c r="{r}" t="b"><v>{1 if val else 0}</v></c>')
            elif isinstance(val, int) and not isinstance(val, bool):
                out.append(f'<c r="{r}"><v>{val}</v></c>')
            elif isinstance(val, float):
                if math.isnan(val) or math.isinf(val):
                    out.append(
                        f'<c r="{r}" t="inlineStr"><is><t>{escape(str(val))}</t></is></c>'
                    )
                else:
                    out.append(f'<c r="{r}"><v>{repr(val)}</v></c>')
            else:
                s = str(val)
                out.append(
                    f'<c r="{r}" t="inlineStr"><is><t xml:space="preserve">{escape(s)}</t></is></c>'
                )
        out.append("</row>")
    out.append("</sheetData></worksheet>")
    return "".join(out)


def write_xlsx(path: Path, sheets):
    # sheets: list[(name, rows)]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    content_types = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    for i in range(len(sheets)):
        content_types.append(
            f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
    content_types.append("</Types>")

    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        "</Relationships>"
    )

    wb_rels = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
    ]
    for i in range(len(sheets)):
        wb_rels.append(
            f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i + 1}.xml"/>'
        )
    wb_rels.append(
        f'<Relationship Id="rId{len(sheets) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    )
    wb_rels.append("</Relationships>")

    wb = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" ',
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>',
    ]
    for i, (name, _) in enumerate(sheets, start=1):
        safe = escape(name)[:31]
        wb.append(f'<sheet name="{safe}" sheetId="{i}" r:id="rId{i}"/>')
    wb.append("</sheets></workbook>")

    styles = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
        "</styleSheet>"
    )

    core = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<dc:creator>topic-viz</dc:creator><cp:lastModifiedBy>topic-viz</cp:lastModifiedBy>
<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>"""

    app = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        "<Application>topic-viz</Application></Properties>"
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "".join(content_types))
        z.writestr("_rels/.rels", rels)
        z.writestr("docProps/core.xml", core)
        z.writestr("docProps/app.xml", app)
        z.writestr("xl/workbook.xml", "".join(wb))
        z.writestr("xl/_rels/workbook.xml.rels", "".join(wb_rels))
        z.writestr("xl/styles.xml", styles)
        for i, (_, rows) in enumerate(sheets, start=1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", sheet_xml(rows))


def fmt(v):
    if isinstance(v, float):
        if abs(v) >= 1e4 or (0 < abs(v) < 1e-3):
            return f"{v:.6e}"
        return round(v, 12)
    return v


def build_sheets(data):
    sheets = []
    meta = data["meta"]
    # 1 總覽決策
    rows = [
        ["NIST 9 係數熱負載整合 — 視覺化與演示 (Excel)"],
        ["generated_at", meta.get("generated_at")],
        ["source.reliability", meta.get("source", {}).get("reliability")],
        ["source.engine", meta.get("source", {}).get("engine")],
        [],
        ["決策", "值", "規格意義"],
    ]
    for d in data.get("decisions", []):
        rows.append([d.get("id"), d.get("v"), d.get("desc")])
    sheets.append(("總覽決策", rows))

    # 2 計算模型
    m = data.get("model", {})
    rows = [
        ["計算模型規格"],
        ["項目", "規格"],
        ["κ(T)", m.get("kappa")],
        ["Q_solid", m.get("q_solid")],
        ["Q_rf", m.get("q_rf")],
        ["政策", m.get("policy")],
        [],
        [
            "說明",
            "Excel 版為資料快照呈現（表格/數值），對應 docs/nist9_viz_demo.html 視圖；曲線以取樣點資料表呈現。",
        ],
    ]
    sheets.append(("計算模型", rows))

    # 3 交付清單
    rows = [["交付清單"], ["類別", "項目"]]
    for cat, items in data.get("deliverables", {}).items():
        for it in items:
            rows.append([cat, it])
    sheets.append(("交付清單", rows))

    # 4,5 曲線樣本
    def curve_sheet(key, title, yname):
        rows = [[title]]
        for c in data.get("samples", {}).get(key, []):
            rows.append([])
            rows.append(["material", c.get("material")])
            rows.append(["T (K)", yname])
            for t, y in zip(c.get("T", []), c.get(yname, [])):
                rows.append([fmt(t), fmt(y)])
        if len(rows) == 1:
            rows.append(
                ["(無取樣資料)", str(data.get("samples", {}).get("errors", []))]
            )
        return (title[:31], rows)

    sheets.append(curve_sheet("k_curves", "κT曲線樣本", "k"))
    sheets.append(curve_sheet("integral_curves", "積分曲線樣本", "integral"))

    # 6 熱負載分解
    hl = data.get("samples", {}).get("heatload")
    rows = [["多溫區熱負載演示 (樣本)"]]
    if hl:
        rows += [
            ["材料", hl.get("material")],
            ["P_in (W)", fmt(hl.get("pin_w"))],
            ["面積 A (m^2)", fmt(hl.get("area_m2"))],
            ["Total (W)", fmt(hl.get("total_load_w"))],
            ["Solid (W)", fmt(hl.get("solid_conduction_w"))],
            ["Atten/RF (W)", fmt(hl.get("attenuator_dissipation_w"))],
            [],
            [
                "stage",
                "T_hot_K",
                "T_cold_K",
                "length_m",
                "atten_db",
                "integral_k_dT",
                "solid_conduction_w",
                "attenuator_dissipation_w",
            ],
        ]
        # find total per stage key
        for s in hl.get("stages", []):
            total = (s.get("solid_conduction_w", 0) or 0) + (
                s.get("attenuator_dissipation_w", 0) or 0
            )
            rows.append(
                [
                    s.get("stage"),
                    fmt(s.get("T_hot_K")),
                    fmt(s.get("T_cold_K")),
                    fmt(s.get("length_m")),
                    fmt(
                        s.get("attenuation_db")
                        if "attenuation_db" in s
                        else s.get("atten_db")
                    ),
                    fmt(s.get("integral_k_dT")),
                    fmt(s.get("solid_conduction_w")),
                    fmt(s.get("attenuator_dissipation_w")),
                    fmt(total),
                ]
            )
        # header adjust: last col is stage total
        rows[8].append("total_stage_w")
    else:
        rows.append(
            ["(無樣本熱負載資料)", str(data.get("samples", {}).get("errors", []))]
        )
    sheets.append(("熱負載分解", rows))

    # 7 可靠度基準
    rel = data.get("reliability", {})
    base = rel.get("baseline_noise1_seed42", {})
    rows = [
        ["polyfit 可靠度 - baseline (noise=1%, seed=42)"],
        ["generator", rel.get("generator")],
        ["have_scipy", rel.get("have_scipy")],
        [],
        [
            "材料",
            "R²",
            "RMSE(log10)",
            "α_extrap",
            "poly_slope_at_Tmin",
            "α-slope",
            "k_at_20mK",
            "∫₂³⁰⁰κdT",
            "max|resid_log10| Tc區",
        ],
    ]
    for name, key in [("Kapton", "kapton"), ("NbTi", "nbti")]:
        b = base.get(key, {})
        tc = b.get("tc_region", {}) or {}
        rows.append(
            [
                name,
                fmt(b.get("r2")),
                fmt(b.get("rmse_log10")),
                fmt(b.get("alpha_extrap")),
                fmt(b.get("poly_slope_at_Tmin")),
                fmt(b.get("alpha_minus_slope")),
                fmt(b.get("k_at_20mK")),
                fmt(b.get("integral_2_300K")),
                fmt(tc.get("max_abs_resid_log10")),
            ]
        )
    # coeffs
    rows += [
        [],
        [
            "Kapton coeffs_asc_c0_c8 (baseline fit)",
            *(fmt(x) for x in base.get("kapton", {}).get("coeffs_asc_c0_c8", [])),
        ],
        [
            "NbTi coeffs_asc_c0_c8 (baseline fit)",
            *(fmt(x) for x in base.get("nbti", {}).get("coeffs_asc_c0_c8", [])),
        ],
    ]
    # Tc points
    tcpts = (base.get("nbti", {}).get("tc_region") or {}).get("points") or []
    if tcpts:
        rows += [[], ["NbTi Tc 區殘差點"], ["T (K)", "resid_log10", "ratio_k/kfit"]]
        for p in tcpts:
            rows.append(
                [fmt(p.get("T")), fmt(p.get("resid_log10")), fmt(p.get("ratio_k/kfit"))]
            )
    sheets.append(("可靠度基準", rows))

    # 8 可靠度敏感度
    sens = rel.get("sensitivity_noise_seed", {})
    rows = [
        ["擾動敏感度範圍 (noise/seed)"],
        [
            "材料",
            "n_runs",
            "r2_min",
            "rmse_max",
            "alpha_min",
            "alpha_max",
            "k20mK_min",
            "k20mK_max",
            "integral_min",
            "integral_max",
        ],
    ]
    for name, key in [("Kapton", "kapton"), ("NbTi", "nbti")]:
        s = sens.get(key, {})
        rows.append(
            [
                name,
                s.get("n_runs"),
                fmt(s.get("r2_min")),
                fmt(s.get("rmse_max")),
                fmt(s.get("alpha_min")),
                fmt(s.get("alpha_max")),
                fmt(s.get("k20mK_min")),
                fmt(s.get("k20mK_max")),
                fmt(s.get("integral_min")),
                fmt(s.get("integral_max")),
            ]
        )
    rows += [
        [],
        [
            "Kapton coeff_rel_std_pct_c0_c8",
            *(
                fmt(x)
                for x in sens.get("kapton", {}).get("coeff_rel_std_pct_c0_c8", [])
            ),
        ],
        [
            "NbTi coeff_rel_std_pct_c0_c8",
            *(fmt(x) for x in sens.get("nbti", {}).get("coeff_rel_std_pct_c0_c8", [])),
        ],
    ]
    sheets.append(("可靠度敏感度", rows))

    # 9 coeffdata compare / status
    rows = [["Kapton: coeff_data 對照 (stored vs fitted)"]]
    kc = rel.get("kapton_coeffdata_compare", {})
    rows += [
        ["stored_source", kc.get("stored_source")],
        ["stored_note", kc.get("stored_note")],
        [],
        ["i", "stored_c", "fitted_c_noise1_seed42", "abs_diff", "rel_diff_pct"],
    ]
    for i, (a, b, c, d) in enumerate(
        zip(
            kc.get("stored_coeffs", []),
            kc.get("fitted_coeffs_noise1_seed42", []),
            kc.get("abs_diff", []),
            kc.get("rel_diff_pct", []),
        )
    ):
        rows.append([i, fmt(a), fmt(b), fmt(c), fmt(d)])
    rows += [
        ["max_abs_diff", fmt(kc.get("max_abs_diff"))],
        [],
        ["NbTi coeff_data 狀態"],
        ["coeffs", kc2 := rel.get("nbti_coeffdata_status", {}).get("coeffs")],
        ["equation_type", rel.get("nbti_coeffdata_status", {}).get("equation_type")],
        ["source", rel.get("nbti_coeffdata_status", {}).get("source")],
    ]
    sheets.append(("係數對照", rows))

    # 10 檔案API規格
    rows = [["檔案與 API 規格"], [], ["核心檔案"]]
    for x in data.get("deliverables", {}).get("core", []):
        rows.append([x])
    rows.append([])
    rows.append(["新平台頁面"])
    for x in data.get("deliverables", {}).get("platform_pages", []):
        rows.append([x])
    rows.append([])
    rows.append(["舊目錄整合"])
    for x in data.get("deliverables", {}).get("legacy_pages", []):
        rows.append([x])
    rows.append([])
    rows.append(["文件/腳本"])
    for x in data.get("deliverables", {}).get("docs_scripts", []):
        rows.append([x])
    rows += [
        [],
        ["API (熱負載NIST9)", "用途"],
        ["list_materials/get_material/resolve_material", "查詢材料與 9 係數/來源/範圍"],
        ["k_of_T / integrate_kappa", "κ(T) 與溫區積分"],
        ["k_curve / integral_curve", "κ(T)、∫κdT 曲線資料"],
        ["compare_materials", "多材料比較"],
        ["calculate_thermal_load", "多溫區 Q_solid + Q_rf 熱負載"],
        ["sweep_parameter / sweep_materials_heatload", "參數/材料掃描模擬"],
        [],
        ["樣本錯誤", str(data.get("samples", {}).get("errors", []))],
    ]
    sheets.append(("檔案API規格", rows))

    return sheets


def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    sheets = build_sheets(data)
    write_xlsx(OUT_XLSX, sheets)
    print(f"WROTE {OUT_XLSX}")
    print(f"sheets: {[s[0] for s in sheets]}")
    print(f"rows: {[len(s[1]) for s in sheets]}")


if __name__ == "__main__":
    main()
