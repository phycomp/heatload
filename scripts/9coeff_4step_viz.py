#!/usr/bin/env python3
"""Generate visualization & demo for 9-coeff heatload 4-step flow.

Steps:
  1. 研究論文暨材料資料庫
  2. 物理推導9個參數
  3. 矩陣運算 得出9個參數
  4. polyfit去驗證

Outputs (same-source snapshot driven):
  - docs/9coeff_4step_flow.json
  - docs/9coeff_4step_demo.html
  - docs/9coeff_4step_demo.xlsx

Policy: D4=A (heatload-coff-nist SSOT), no refit/invented coeffs.
Degrade gracefully with errors recorded when sources unavailable.
"""

from __future__ import annotations

import csv
import datetime as _dt
import importlib.util
import json
import math
import os
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SCRIPTS = ROOT / "scripts"
OUT_JSON = DOCS / "9coeff_4step_flow.json"
OUT_HTML = DOCS / "9coeff_4step_demo.html"
OUT_XLSX = DOCS / "9coeff_4step_demo.xlsx"
SKILL = Path("/home/sam/.opencode/skills/heatload-coff-nist")
COEFF_DATA_PY = SKILL / "scripts" / "coeff_data.py"
COEFF_TABLE_CSV = SKILL / "references" / "coefficient_table.csv"
CITATIONS_MD = SKILL / "references" / "citations.md"
RELIAB_JSON = DOCS / "polyfit_可靠度驗證.json"
RELIAB_MD = DOCS / "polyfit_可靠度驗證.md"


def read_text(p: Path):
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return None


def load_json(p: Path, errors, label):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"{label}: {e}")
        return None


def load_coeff_module(errors):
    try:
        spec = importlib.util.spec_from_file_location("coeff_data_4step", COEFF_DATA_PY)
        mod = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(mod)  # type: ignore
        return mod
    except Exception as e:
        errors.append(f"coeff_data import: {e}")
        return None


def summarize_coeff_db(mod, errors):
    info = {
        "path": str(COEFF_DATA_PY),
        "count": None,
        "equation_types": {},
        "categories": {},
        "samples": [],
        "nbti_status": None,
        "kapton": None,
        "raw_materials": [],
    }
    if not mod:
        return info
    try:
        mats = getattr(mod, "MATERIALS", {})
        info["count"] = len(mats)
        for name, d in mats.items():
            et = d.get("equation_type")
            cat = d.get("category") or d.get("quantity") or "?"
            info["equation_types"][et] = info["equation_types"].get(et, 0) + 1
            info["categories"][cat] = info["categories"].get(cat, 0) + 1
            coeffs = d.get("coeffs")
            row = {
                "material": name,
                "coeffs_c0_c8": coeffs,
                "equation_type": et,
                "valid_range_K": d.get("valid_range_K"),
                "category": cat,
                "source": d.get("source"),
                "note": d.get("note"),
                "quantity": d.get("quantity"),
            }
            # also provide individual c0-c8 fields for tables/charts
            for i in range(9):
                row[f"c{i}"] = coeffs[i] if coeffs and len(coeffs) == 9 else None
            info["raw_materials"].append(row)
        for key in [
            "Raicu outer (C7150)",
            "Raicu dielectric (PTFE)",
            "Raicu inner (Ag-coated C7150)",
            "Raicu rho inner (Table 6)",
            "Kapton (Cri/oFlex 3)",
            "NbTi (Cri/oFlex 3)",
            "Copper (OFHC) RRR=100",
        ]:
            d = mats.get(key)
            if d:
                item = {
                    "material": key,
                    "coeffs": d.get("coeffs"),
                    "equation_type": d.get("equation_type"),
                    "valid_range_K": d.get("valid_range_K"),
                    "source": d.get("source"),
                    "note": d.get("note"),
                    "quantity": d.get("quantity"),
                }
                info["samples"].append(item)
                if key == "Kapton (Cri/oFlex 3)":
                    info["kapton"] = item
                if key == "NbTi (Cri/oFlex 3)":
                    info["nbti_status"] = item
    except Exception as e:
        errors.append(f"coeff_data summarize: {e}")
    return info


def parse_citations_summary(text, errors):
    out = {"path": str(CITATIONS_MD), "key_refs": [], "notes": []}
    if text is None:
        errors.append(f"citations read: missing {CITATIONS_MD}")
        return out
    # curated key refs (source-of-truth in file)
    out["key_refs"] = [
        {
            "id": "raicu2025",
            "title": "Raicu et al. (2025) Cryogenic thermal modeling of microwave high density signaling",
            "venue": "EPJ Quantum Technology 12:124",
            "doi": "10.1140/epjqt/s40507-025-00427-1",
            "url": "https://doi.org/10.1140/epjqt/s40507-025-00427-1",
            "dataset": "https://doi.org/10.5281/zenodo.15238913",
            "content": "Table 4: k(T) 9-coeff fits (outer/dielectric/PTFE/inner). Table 6: rho(T) inner. PTFE coeffs sourced from NIST Cryogenics Index [9,10] per Table 4 note.",
        },
        {
            "id": "nist_db",
            "title": "NIST Cryogenics Index of Material Properties",
            "url": "https://trc.nist.gov/cryogenics/materials/materialproperties.htm",
            "content": "Cryogenic material property fits (a..i 9 coefficients) and valid ranges; primary database source for many entries.",
        },
        {
            "id": "nist_eqn",
            "title": "NIST Cryogenics Material Properties: Equations",
            "url": "https://trc.nist.gov/cryogenics/materials/materialproperties.htm (equations)",
            "content": "log-log polynomial form log10(y)=a+b(log10 T)+...+i(log10 T)^8 and related equation types.",
        },
        {
            "id": "marquardt2000",
            "title": "Marquardt, Le & Radebaugh (2000) Cryogenic Material Properties Database",
            "venue": "11th International Cryocooler Conference, Keystone CO (2000), pp.681-687",
            "url": "https://cryocooler.org/resources/Documents/C11/247.pdf",
            "content": "Defines 9-parameter (a..i) cryogenic material property fits.",
        },
        {
            "id": "bradley2006",
            "title": "Bradley et al. (2006) Cryogenic Material Properties Database, Update 2006",
            "venue": "ICEC 21, Prague (2006)",
            "content": "Database update (referenced by sources).",
        },
        {
            "id": "simon1992",
            "title": "Simon, Drexler & Reed (1992) Properties of Copper and Copper Alloys at Cryogenic Temperatures",
            "venue": "NIST Monograph 177",
            "content": "OFHC Cu rational-form conductivity data/fits (RRR variants).",
        },
        {
            "id": "flynn",
            "title": "Flynn, Cryogenic Engineering",
            "content": "Textbook basis for cryogenic heat load / multi-stage modeling (cited in skill overview).",
        },
        {
            "id": "kapton_crioflex",
            "title": "Kapton (Cri/oFlex 3) 9-coeff (project-derived, documented source)",
            "source_file": "熱負載/推導柔性多項式耦合系數.md L138-166 / 16柔性八階擬合.py context",
            "content": "Stored 7-sig-fig coeffs in coeff_data with stated provenance; used as fixed-coeff material entry (distinct from runtime_polyfit NbTi).",
        },
        {
            "id": "nbti_note",
            "title": "NbTi (Cri/oFlex 3) — no fixed coefficients",
            "source_file": "熱負載/pages/16柔性八階擬合.py",
            "content": "NBTI_COEFFS not a numeric constant (runtime np.polyfit on simulated PPMS-like data, seed/noise dependent); coeff_data marks N/A runtime_polyfit (no invention).",
        },
    ]
    out["notes"].append(
        "Parsed as curated summary anchored to citations.md sections; see citations.md for full verbatim references."
    )
    return out


def coeff_table_count(csv_path: Path, errors):
    try:
        with csv_path.open(newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            return sum(1 for _ in r)
    except Exception as e:
        errors.append(f"coefficient_table.csv read: {e}")
        return None


def build_step2():
    return {
        "id": 2,
        "title": "物理推導 9 個參數",
        "goal": "建立 κ(T) 的 9 參數表示與熱負載積分模型，說明參數意義與適用邊界。",
        "model": {
            "log_polynomial": {
                "name": "NIST/Raicu log-log polynomial (9 coefficients)",
                "params": "c0..c8 對應 a..i",
                "formula_kappa": "log10(kappa(T)) = c0 + c1*log10(T) + c2*(log10(T))^2 + ... + c8*(log10(T))^8",
                "formula_eval": "kappa(T) = 10^(log10(kappa(T)))",
                "units": "kappa: W/(m*K), T: K (Table 6 之 rho 同形但單位 Ω*m)",
                "validity": "各材料 valid_range_K；範圍外預設 0；可選低溫外推 k(T)=T^alpha（可能高估）",
            },
            "rational_copper": {
                "name": "OFHC Cu rational form (RRR variants)",
                "formula": "log10(kappa)= (a + c*T^0.5 + e*T + g*T^1.5 + i*T^2) / (1 + b*T^0.5 + d*T + f*T^1.5 + h*T^2)",
                "mapping": "(a,b,c,d,e,f,g,h,i) = (c0..c8)",
            },
            "heatload": {
                "solid_conduction": "Q_solid = Σ_j (A/L_j) * ∫_{T_cold,j}^{T_hot,j} kappa(T) dT",
                "attenuator_dissipation": "Q_rf = Σ_j P_in * (1 - 10^(-alpha_j/10))",
                "total": "Q_total = Q_solid + Q_rf",
            },
        },
        "derivation_points": [
            "Fourier 定律 q = -kappa*A*dT/dx；一維穩態下 Q=(A/L)∫kappa(T)dT（需 κ(T) 模型與溫區積分）。",
            "Wiedemann–Franz kappa/(sigma*T)=L0 提供金屬電子熱導與電導關聯；Table 6 提供 rho(T) 係數可供交叉驗證（非 κ）。",
            "為跨多數量級溫區與材料行為，採 log-log 空間擬合：x=log10(T), y=log10(kappa)，以 8 階多項式表示 y(x)=Σ c_n x^n。",
            "9 參數(c0..c8)即多項式 0–8 次係數；高階項捕捉多溫區轉折，係數需足夠有效位數避免高溫端 x^8 放大截斷誤差。",
        ],
        "source_refs": [
            "~/.opencode/skills/heatload-coff-nist/SKILL.md",
            "~/.opencode/skills/heatload-coff-nist/references/citations.md",
            "~/量傳線/熱負載/MDs/基礎推導熱負載.md",
            "~/量傳線/熱負載/MDs/推導溫區公式.md",
            "~/量傳線/熱負載/推導多項式耦合系數.md",
        ],
    }


def build_step3(coeff_db=None):
    # values taken from derivation md (Cri/oFlex 3 Kapton illustrative example)
    raw_materials = (coeff_db or {}).get("raw_materials", [])
    materials_with_coeffs = [
        r
        for r in raw_materials
        if r.get("coeffs_c0_c8") and len(r.get("coeffs_c0_c8")) == 9
    ]
    materials_without_fixed = [
        r.get("material")
        for r in raw_materials
        if not (r.get("coeffs_c0_c8") and len(r.get("coeffs_c0_c8")) == 9)
    ]
    param_meanings = [
        {
            "param": "c0 (a)",
            "term": "(log10 T)^0 = 1",
            "meaning": "常數項/截距：對應多項式在 log10(T)=0（T=1 K，若在模型/範圍語境下）之 log10(κ) 基準尺度，決定整體量級的平移。",
        },
        {
            "param": "c1 (b)",
            "term": "(log10 T)^1",
            "meaning": "一次項/線性斜率：在 log-log 座標中主導局部一階趨勢（等效冪次/斜率貢獻），反映 κ 隨溫度變化的主要升降趨勢。",
        },
        {
            "param": "c2 (c)",
            "term": "(log10 T)^2",
            "meaning": "二次項/曲率：提供 log-log 曲線的二階彎曲修正，描述偏離單一冪律的曲率。",
        },
        {
            "param": "c3 (d)",
            "term": "(log10 T)^3",
            "meaning": "三次項：提供更高階的彎曲與非對稱變化能力，協助表達中間溫區轉折。",
        },
        {
            "param": "c4 (e)",
            "term": "(log10 T)^4",
            "meaning": "四次項：進一步修正寬溫域內的形狀，使多溫區行為可被平滑連接。",
        },
        {
            "param": "c5 (f)",
            "term": "(log10 T)^5",
            "meaning": "五次項：高階形狀修正，捕捉更細緻的溫度相依變化。",
        },
        {
            "param": "c6 (g)",
            "term": "(log10 T)^6",
            "meaning": "六次項：高階微調，對跨多數量級且具多轉折特徵之 κ(T) 提供額外彈性。",
        },
        {
            "param": "c7 (h)",
            "term": "(log10 T)^7",
            "meaning": "七次項：更高階修正；因 x=log10(T) 之冪次放大，在較高溫/較大 x 區域對數值與有效位數更敏感。",
        },
        {
            "param": "c8 (i)",
            "term": "(log10 T)^8",
            "meaning": "八次項（最高階）：控制最高階曲率與端點行為；當 x 較大時 x^8 放大顯著，係數截斷誤差會影響 κ(T) 評估。",
        },
    ]
    conditioning_explanation = {
        "title": "病態條件 (ill-conditioning) 與中心化/縮放：物理-數值推導與說明（先於圖表）",
        "source_basis": [
            "熱負載/推導柔性多項式耦合系數.md（Vandermonde、X^T X、cond 範例）",
            "熱負載/推導柔性八階係數.md（最小二乘/正規方程與數值穩定策略）",
            "docs/polyfit_可靠度驗證.json（條件數與擾動敏感度實證）",
        ],
        "derivation_steps": [
            "1) 模型與變數：在 log-log 空間令 x=log10(T)、y=log10(κ(T))，以 8 階多項式 y(x)=Σ_{n=0}^{8} c_n x^n 近似材料熱導率之溫度相依（NIST/Raicu 9 係數形式）。對常見 T∈[2,300] K，x 約落在 [0.301, 2.477]。",
            "2) Vandermonde 設計矩陣：X_{i,n}=x_i^n，n=0..8。各欄為同一變數 x 的不同冪次基底；在有限區間上，高次冪 {x^p, x^q} 彼此形狀相近、相關性高，使欄向量近似線性相依，X 趨於病態。",
            "3) 最小二乘與正規方程：目標 min||y-Xc||^2 導出 X^T X c = X^T y。Gram 矩陣 X^T X 的條件數約為 cond(X)^2（依範數定義），故 X 的病態會在正規方程中被平方放大，求解 c 對資料擾動與浮點誤差高度敏感。",
            "4) 物理/數值後果：κ=10^y 且 y 含 c_n x^n；當 x 較大時（如 x^8≈1417@300K）高階項被放大，係數微小誤差可造成 y 之可觀偏差並進一步影響 κ 與積分熱負載 Q=∫κ dT，因此需要足夠有效位數與穩定求解策略。",
            "5) 中心化/縮放：令 x'=(x-x̄)/s（x̄、s 取資料均值/尺度等）將自變數映射至尺度均衡區間，可降低冪次基底共線性並平衡欄尺度，使 cond(X')/cond(X'^T X') 顯著下降。",
            "6) 等價求解：可在縮放座標求解後還原係數，或使用 QR/SVD、numpy.polyfit 等具內部縮放/穩定策略之方法；模型等價，但數值穩定性改善。",
        ],
        "condition_number_dependency_note": "條件數數值依實作/定義/來源而異：包括範數（2-norm/∞-norm 等）、計算對象（cond(X)、cond(X^T X)、cond(X'_scaled)）、資料點範圍與取樣、是否中心化/縮放及參數、以及演算法/浮點環境。因此推導文件示例與獨立驗證腳本可報告不同數值，須各自標註來源與定義，不可直接混比為同一量。",
    }
    material_rows = []
    for r in materials_with_coeffs:
        coeffs = r.get("coeffs_c0_c8") or []
        entry = {
            "material": r.get("material"),
            "category": r.get("category"),
            "equation_type": r.get("equation_type"),
            "valid_range_K": r.get("valid_range_K"),
            "source": r.get("source"),
        }
        for i in range(9):
            entry[f"c{i}"] = coeffs[i] if i < len(coeffs) else None
        material_rows.append(entry)
    return {
        "id": 3,
        "title": "矩陣運算 得出 9 個參數",
        "goal": "由 log-log 資料點以最小二乘求解 8 階多項式係數 c0..c8，推導係數求解、說明 9 參數物理意義、先解釋病態條件與中心化/縮放，再呈現係數-材料關係。",
        "problem_setup": {
            "data": "N 筆量測/擬合資料點；x_i=log10(T_i), y_i=log10(k_i)",
            "model": "y = c0 + c1*x + c2*x^2 + ... + c8*x^8 (N>=9)",
            "objective": "min S(c)=||y - Xc||^2",
        },
        "derivation_c0_c8": {
            "steps": [
                "令 x_i=log10(T_i), y_i=log10(k_i)，模型 y_i ≈ Σ_{j=0}^{8} c_j x_i^j（c0..c8 對應 a..i）。",
                "建構 N×9 Vandermonde 矩陣 X，元素 X_{i,j}=x_i^j；令 c=[c0..c8]^T、y=[y1..yN]^T。",
                "定義殘差平方和 S(c)=||y-Xc||^2=(y-Xc)^T(y-Xc)=y^T y - 2 c^T X^T y + c^T X^T X c。",
                "令梯度為零：∂S/∂c = -2 X^T y + 2 X^T X c = 0，得正規方程 X^T X c = X^T y。",
                "當 X 滿秩時 c=(X^T X)^{-1} X^T y；實務可用 QR/SVD 或帶縮放平移之穩定實作求得同一最小二乘解 c0..c8。",
            ],
            "result_form": "c0..c8 = argmin_c Σ_i (y_i - Σ_{j=0}^{8} c_j x_i^j)^2（升冪係數）",
            "source_refs": [
                "~/量傳線/熱負載/推導柔性多項式耦合系數.md",
                "~/量傳線/熱負載/推導柔性八階係數.md",
            ],
        },
        "parameter_meanings_c0_c8": param_meanings,
        "parameter_meaning_note": "c0..c8 為 log10(κ)-log10(T) 經驗擬合模型中的多項式係數（a..i），用以參數化材料 κ(T) 曲線之尺度與各階形狀；其意義應結合模型形式、有效溫區與來源解讀，非各自獨立之單一微觀物理常數。對 rational_copper 條目，同一組 (c0..c8)=(a..i) 代入不同公式形式，角色依該方程定義（見 Step 2/SSOT）。",
        "vandermonde": {
            "definition": "X_{i,j} = x_i^j, i=0..N-1, j=0..8 (N x 9)",
            "example_context": "推導柔性多項式耦合系數.md（Cri/oFlex3/Kapton 示意，N=50, T∈[2,300]K）",
            "x_preview": [0.3010, 0.3454, 0.3899, 0.4343, 0.4787],
            "row_preview_note": "前 5 行之 [1, x, x^2, ..., x^8] 量級跨越大，顯示冪次基底相關性/病態來源（詳見來源 md）。",
        },
        "normal_equation": {
            "expand": "S(c)=y^T y - 2*c^T*(X^T y) + c^T*(X^T X)*c",
            "gradient_zero": "∂S/∂c = -2*X^T*y + 2*X^T*X*c = 0",
            "equation": "X^T X c = X^T y",
            "solution": "c = (X^T X)^(-1) X^T y",
            "note": "實務常以 QR/SVD 或 numpy.polyfit 之縮放平移求解以提升數值穩定性；數學等價於最小二乘解。",
        },
        "conditioning_explanation": conditioning_explanation,
        "conditioning_example": {
            "source": "熱負載/推導柔性多項式耦合系數.md（示例；定義/取樣依該文件）",
            "cond_X": 1.31e7,
            "cond_XTX": 1.71e14,
            "scaling": "x'=(x-x̄)/x_scale, x̄=1.3891, x_scale=1.0880 (示例)",
            "cond_X_scaled": 5.17e2,
            "improvement_factor_approx": 2.5e4,
            "interpretation": "高次冪基底高度相關導致病態；中心化/縮放顯著改善條件數。此為來源示例，條件數數值依實作/定義/來源而異（見上方說明與 Step 4 驗證）。",
        },
        "result_example": {
            "source": "熱負載/推導柔性多項式耦合系數.md（Cri/oFlex 3 Kapton, 7 significant figures）",
            "order": "ascending c0..c8 = a..i",
            "coeffs_c0_c8": [
                -4.769084,
                10.92915,
                -26.55324,
                36.1195,
                -27.08454,
                11.58217,
                -2.777787,
                0.3432157,
                -0.01715343,
            ],
            "quality_reported_in_source": {
                "R2": 0.999907,
                "RMSE_log10": 0.0067,
                "max_abs_residual_log10": 0.0163,
            },
            "note": "此為來源文件所載擬合結果/存檔係數示例；與 coeff_data 中 Kapton (Cri/oFlex 3) 一致。與獨立重現擬合之差異屬可靠度驗證議題（見步驟4）。",
        },
        "material_coeff_relation": {
            "description": "9 個參數 (c0..c8) 與材料之關係：同一參數化框架下，各材料由其 κ(T)（或對映量）資料/來源擬合得到不同係數向量；係數差異反映材料與溫區行為差異，並受 equation_type 與有效範圍影響。",
            "materials_with_fixed_coeffs_count": len(materials_with_coeffs),
            "materials_without_fixed_coeffs": materials_without_fixed,
            "chart_fields": ["material", "category", "equation_type", "valid_range_K"]
            + [f"c{i}" for i in range(9)],
            "rows": material_rows,
            "note": "僅納入具固定 9 係數之材料（53 筆）以呈現係數-材料關係；NbTi (Cri/oFlex 3) 為 runtime_polyfit、coeffs=null，不納入數值關係圖表（SSOT，不編造）。rational_copper 之 (c0..c8) 映射同名但方程形式不同，解讀需區分 equation_type。",
        },
        "precision_note": "x=log10(300)≈2.4771 時 x^8≈1417.7，高階項截斷誤差會被放大；來源示例指出 7 位有效數字可將全溫區誤差控制在較小範圍（依該擬合情境）。",
        "source_refs": [
            "~/量傳線/熱負載/推導柔性多項式耦合系數.md",
            "~/量傳線/熱負載/推導柔性八階係數.md",
            "~/量傳線/docs/polyfit_可靠度驗證.json",
        ],
    }


def build_step1(citations, coeff_db, csv_count):
    samples = coeff_db.get("samples", [])
    sample_rows = []
    for s in samples:
        sample_rows.append(
            {
                "material": s.get("material"),
                "equation_type": s.get("equation_type"),
                "valid_range_K": s.get("valid_range_K"),
                "source": s.get("source"),
                "coeffs": s.get("coeffs"),
                "note": s.get("note"),
            }
        )
    raw_materials = coeff_db.get("raw_materials", [])
    return {
        "id": 1,
        "title": "研究論文暨材料資料庫",
        "goal": "確認 9 係數之上級文獻/資料庫出處，直接呈現資料庫原始資料（材料、係數、範圍、來源等），建立可追溯性。",
        "provenance": citations,
        "database": {
            "ssot_paths": [
                str(COEFF_DATA_PY),
                str(SKILL / "references" / "coefficient_table.md"),
                str(COEFF_TABLE_CSV),
                str(CITATIONS_MD),
            ],
            "material_count_coeff_data": coeff_db.get("count"),
            "material_count_csv": csv_count,
            "equation_types": coeff_db.get("equation_types"),
            "categories": coeff_db.get("categories"),
            "raw_materials": raw_materials,
            "key_samples": sample_rows,
            "notes": [
                "多數材料為 log_polynomial 9 係數；OFHC Cu 採 rational_copper；Table 6 為 rho(T) 同形係數。",
                "部分 NIST 條目尾端係數為 0 係原始低階擬合，如實保留。",
                "NbTi (Cri/oFlex 3) 無固定數值係數（runtime_polyfit），coeffs=null 且不納入固定材料計算。",
                "本步驟直接展示資料庫原始資料列（含 c0..c8、equation_type、valid_range_K、category/quantity、source、note），來源為 heatload-coff-nist SSOT。",
            ],
        },
        "source_refs": [
            "~/.opencode/skills/heatload-coff-nist/references/citations.md",
            "~/.opencode/skills/heatload-coff-nist/references/coefficient_table.md",
            "~/.opencode/skills/heatload-coff-nist/references/00_熱負載總覽.md",
            "~/.opencode/skills/heatload-coff-nist/scripts/coeff_data.py",
            "~/.opencode/skills/heatload-coff-nist/references/coefficient_table.csv",
        ],
    }


def build_step4(reliab):
    if not reliab:
        return {
            "id": 4,
            "title": "polyfit 去驗證",
            "goal": "驗證擬合可靠度與限制。",
            "status": "missing",
            "source_refs": [str(RELIAB_JSON)],
        }
    baseline = reliab.get("baseline_noise1_seed42", {})
    sens = reliab.get("sensitivity_noise_seed", {})
    cond = reliab.get("condition", {})
    comp = reliab.get("kapton_coeffdata_compare", {})
    nbti_status = reliab.get("nbti_coeffdata_status", {})

    # compact residual points
    def compact_baseline(name):
        b = baseline.get(name, {})
        out = {
            k: b.get(k)
            for k in [
                "r2",
                "rmse_log10",
                "alpha_extrap",
                "poly_slope_at_Tmin",
                "alpha_minus_slope",
                "k_at_20mK",
                "integral_2_300K",
            ]
        }
        out["coeffs_c0_c8"] = b.get("coeffs_asc_c0_c8")
        tc = b.get("tc_region") or {}
        out["tc_max_abs_resid_log10"] = tc.get("max_abs_resid_log10")
        out["tc_points"] = tc.get("points") or []
        return out

    return {
        "id": 4,
        "title": "polyfit 去驗證",
        "goal": "以獨立驗證檢視擬合品質、數值條件、擾動敏感度與外推/積分行為，界定可用性。",
        "source": {
            "json": str(RELIAB_JSON),
            "md": str(RELIAB_MD),
            "script": str(ROOT / "scripts" / "validate_polyfit_reliability.py"),
        },
        "condition": cond,
        "baseline_noise1_seed42": {
            "kapton": compact_baseline("kapton"),
            "nbti": compact_baseline("nbti"),
        },
        "sensitivity_noise_seed": {
            "kapton": sens.get("kapton"),
            "nbti": sens.get("nbti"),
        },
        "kapton_coeffdata_compare": comp,
        "nbti_coeffdata_status": nbti_status,
        "interpretation": [
            "條件數顯示原始冪次基底病態，縮放可改善但高階擬合仍對資料/擾動敏感。",
            "Kapton：擬合 R² 高、∫(2-300K) 較穩，但 k(20mK) 外推跨大範圍且與多項式斜率差異大，深低溫外推不可靠。",
            "NbTi：存在 Tc 轉變區殘差結構，全域 8 階多項式難精確描述；且無固定係數(runtime_polyfit)，可靠度較低。",
            "存檔 Kapton 係數與本驗證擬合係數可有顯著差異（來源/資料生成/流程不同）→ 驗證強調流程敏感性與來源可追溯的重要性。",
        ],
        "source_refs": [
            str(RELIAB_JSON),
            str(RELIAB_MD),
            str(ROOT / "scripts" / "validate_polyfit_reliability.py"),
        ],
    }


def build_snapshot():
    errors = []
    mod = load_coeff_module(errors)
    coeff_db = summarize_coeff_db(mod, errors)
    csv_count = coeff_table_count(COEFF_TABLE_CSV, errors)
    citations_text = read_text(CITATIONS_MD)
    citations = parse_citations_summary(citations_text, errors)
    reliab = load_json(RELIAB_JSON, errors, "polyfit reliability json")
    steps = [
        build_step1(citations, coeff_db, csv_count),
        build_step2(),
        build_step3(coeff_db),
        build_step4(reliab),
    ]
    snapshot = {
        "meta": {
            "title": "9 係數熱負載 4 步驟流程 — 視覺化與演示",
            "generated_at": _dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "flow": [
                "1.研究論文暨材料資料庫",
                "2.物理推導9個參數",
                "3.矩陣運算 得出9個參數",
                "4.polyfit去驗證",
            ],
            "policy": {
                "D4": "A (heatload-coff-nist SSOT: coeff_data.py, thermal_load.py)",
                "no_invention": "不重擬合、不編造係數/結論；缺資料記 errors 並降級",
            },
            "source": {
                "coeff_data": str(COEFF_DATA_PY),
                "coefficient_table_csv": str(COEFF_TABLE_CSV),
                "citations": str(CITATIONS_MD),
                "reliability_json": str(RELIAB_JSON),
                "reliability_md": str(RELIAB_MD),
            },
        },
        "steps": steps,
        "errors": errors,
    }
    return snapshot


# ---------- Excel (stdlib minimal xlsx) ----------


def col_name(n):
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def cell_ref(r, c):
    return f"{col_name(c)}{r}"


def xml_escape(s):
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def make_sheet_xml(rows):
    # rows: list of list of (type,value) where type in {s,n,inline}
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
        "<sheetData>",
    ]
    for i, row in enumerate(rows, 1):
        out.append(f'<row r="{i}">')
        for j, val in enumerate(row, 1):
            ref = cell_ref(i, j)
            if val is None:
                continue
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                    out.append(
                        f'<c r="{ref}" t="inlineStr"><is><t>{xml_escape(val)}</t></is></c>'
                    )
                else:
                    out.append(f'<c r="{ref}"><v>{val}</v></c>')
            else:
                out.append(
                    f'<c r="{ref}" t="inlineStr"><is><t>{xml_escape(val)}</t></is></c>'
                )
        out.append("</row>")
    out.append("</sheetData></worksheet>")
    return "".join(out)


def write_xlsx(path: Path, sheets):
    # sheets: [(name, rows)]
    now = _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    content_types = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
    ]
    for idx in range(1, len(sheets) + 1):
        content_types.append(
            f'<Override PartName="/xl/worksheets/sheet{idx}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
    content_types += [
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
        "</Types>",
    ]
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        "</Relationships>"
    )
    wb_sheets = []
    wb_rels = []
    for i, (name, _) in enumerate(sheets, 1):
        wb_sheets.append(
            f'<sheet name="{xml_escape(name[:31])}" sheetId="{i}" r:id="rId{i}"/>'
        )
        wb_rels.append(
            f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>'
        )
    wb_rels.append(
        '<Relationship Id="rIdS" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
        + "".join(wb_sheets)
        + "</sheets></workbook>"
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(wb_rels)
        + "</Relationships>"
    )
    styles = '<?xml version="1.0" encoding="UTF-8"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf/></cellStyleXfs><cellXfs count="1"><xf xfId="0"/></cellXfs></styleSheet>'
    core = f'<?xml version="1.0" encoding="UTF-8"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>9coeff 4-step flow</dc:title><dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>'
    app = '<?xml version="1.0" encoding="UTF-8"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>topic-viz</Application></Properties>'
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "".join(content_types))
        z.writestr("_rels/.rels", rels)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        z.writestr("xl/styles.xml", styles)
        z.writestr("docProps/core.xml", core)
        z.writestr("docProps/app.xml", app)
        for i, (_, rows) in enumerate(sheets, 1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", make_sheet_xml(rows))


def fmt(v):
    if v is None:
        return ""
    if isinstance(v, float):
        if v == 0:
            return 0
        av = abs(v)
        if av >= 1e4 or av < 1e-3:
            return float(f"{v:.6g}")
        return float(f"{v:.8g}")
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return v


def build_excel_sheets(snap):
    steps = {s["id"]: s for s in snap["steps"]}
    s1, s2, s3, s4 = steps[1], steps[2], steps[3], steps[4]
    meta = snap["meta"]
    sheets = []

    # 流程總覽
    rows = [
        ["9 係數熱負載 4 步驟流程 — 視覺化/演示（同源快照）"],
        [""],
        ["生成時間", meta.get("generated_at")],
        ["政策 D4", meta.get("policy", {}).get("D4")],
        ["不編造", meta.get("policy", {}).get("no_invention")],
        [""],
        ["步驟", "目標", "主要輸出/證據"],
    ]
    for s in snap["steps"]:
        rows.append([f"{s['id']}. {s['title']}", s.get("goal", ""), s.get("id")])
    rows += [
        ["", ""],
        ["主要輸出檔", "路徑"],
        ["規格", str(DOCS / "9coeff_4step_視覺化規格.md")],
        ["快照", str(OUT_JSON)],
        ["HTML", str(OUT_HTML)],
        ["Excel", str(OUT_XLSX)],
        ["", ""],
        ["errors", len(snap.get("errors", []))],
    ]
    for e in snap.get("errors", []):
        rows.append(["error", e])
    sheets.append(("流程總覽", rows))

    # 1. 論文與資料庫
    rows = [
        ["Step 1 研究論文暨材料資料庫"],
        ["目標", s1.get("goal")],
        [""],
        ["主要出處", "DOI/URL", "內容"],
    ]
    for r in s1.get("provenance", {}).get("key_refs", []):
        link = (
            r.get("doi") or r.get("url") or r.get("dataset") or r.get("source_file", "")
        )
        rows.append([r.get("title", ""), link, r.get("content", "")])
    rows += [
        ["", ""],
        ["資料庫摘要", "值"],
        ["coeff_data 筆數", s1.get("database", {}).get("material_count_coeff_data")],
        [
            "coefficient_table.csv 筆數",
            s1.get("database", {}).get("material_count_csv"),
        ],
        [
            "equation_types",
            json.dumps(
                s1.get("database", {}).get("equation_types", {}), ensure_ascii=False
            ),
        ],
        ["", ""],
        [
            "重點樣本材料",
            "equation_type",
            "valid_range_K",
            "coeffs(c0..c8)",
            "source/note",
        ],
    ]
    for sm in s1.get("database", {}).get("key_samples", []):
        rows.append(
            [
                sm.get("material"),
                sm.get("equation_type"),
                fmt(sm.get("valid_range_K")),
                fmt(sm.get("coeffs")),
                (sm.get("source") or "")
                + (" | " + sm.get("note") if sm.get("note") else ""),
            ]
        )
    sheets.append(("1-論文與資料庫", rows))

    # 2. 物理推導
    m = s2.get("model", {})
    lp = m.get("log_polynomial", {})
    rc = m.get("rational_copper", {})
    hl = m.get("heatload", {})
    rows = [
        ["Step 2 物理推導 9 個參數"],
        ["目標", s2.get("goal")],
        [""],
        ["log_polynomial", "內容"],
        ["參數", lp.get("params")],
        ["kappa 公式", lp.get("formula_kappa")],
        ["計算", lp.get("formula_eval")],
        ["單位", lp.get("units")],
        ["範圍/政策", lp.get("validity")],
        ["", ""],
        ["rational_copper", rc.get("formula")],
        ["mapping", rc.get("mapping")],
        ["", ""],
        ["熱負載", "公式"],
        ["Q_solid", hl.get("solid_conduction")],
        ["Q_rf", hl.get("attenuator_dissipation")],
        ["Q_total", hl.get("total")],
        ["", ""],
        ["推導要點", "說明"],
    ]
    for p in s2.get("derivation_points", []):
        rows.append(["-", p])
    sheets.append(("2-物理推導", rows))

    # 3. 矩陣運算
    ce = s3.get("conditioning_example", {})
    rexp = s3.get("result_example", {})
    deriv = s3.get("derivation_c0_c8", {})
    cond_exp = s3.get("conditioning_explanation", {})
    meanings = s3.get("parameter_meanings_c0_c8", [])
    rel = s3.get("material_coeff_relation", {})
    rows = [
        ["Step 3 矩陣運算 得出 9 個參數"],
        ["目標", s3.get("goal")],
        [""],
        ["問題設定", "內容"],
        ["資料", s3.get("problem_setup", {}).get("data")],
        ["模型", s3.get("problem_setup", {}).get("model")],
        ["目標函數", s3.get("problem_setup", {}).get("objective")],
        ["", ""],
        ["c0..c8 推導過程 (最小二乘/正規方程)", "內容"],
    ]
    for stp in deriv.get("steps", []):
        rows.append(["-", stp])
    rows.append(["結果形式", deriv.get("result_form")])
    rows.append(["推導來源", fmt(deriv.get("source_refs"))])
    rows += [
        ["", ""],
        ["Vandermonde/正規方程", "內容"],
        ["X_{i,j}", s3.get("vandermonde", {}).get("definition")],
        ["X^T X c", s3.get("normal_equation", {}).get("equation")],
        ["解", s3.get("normal_equation", {}).get("solution")],
        ["數值實務", s3.get("normal_equation", {}).get("note")],
        ["", ""],
        ["9 參數 c0..c8 物理意義", "項/對應", "意義"],
    ]
    for m in meanings:
        rows.append([m.get("param"), m.get("term"), m.get("meaning")])
    if not meanings:
        rows.append(["(無 parameter_meanings_c0_c8，請重產生快照)", "", ""])
    rows += [
        ["", ""],
        [
            "病態條件與中心化/縮放（先於圖表，物理-數值推導）",
            "內容",
            "",
        ],
        ["標題", cond_exp.get("title"), ""],
        ["依據來源", fmt(cond_exp.get("source_basis")), ""],
    ]
    for stp in cond_exp.get("derivation_steps", []):
        rows.append(["推導步驟", stp, ""])
    rows.append(
        [
            "條件數數值依賴說明(重要)",
            cond_exp.get("condition_number_dependency_note"),
            "",
        ]
    )
    rows += [
        ["", ""],
        ["條件數示例(來源md，圖表用值)", "值", "來源/備註"],
        ["cond(X)", ce.get("cond_X"), ce.get("source")],
        ["cond(X^T X)", ce.get("cond_XTX"), ""],
        ["縮放策略", ce.get("scaling"), ""],
        ["cond(X_scaled)", ce.get("cond_X_scaled"), ""],
        ["改善倍數(約)", ce.get("improvement_factor_approx"), ""],
        ["解讀", ce.get("interpretation"), ""],
        ["", ""],
        ["Kapton 係數示例(c0..c8=a..i, 來源md)", "值", ""],
    ]
    for i, c in enumerate(rexp.get("coeffs_c0_c8", [])):
        rows.append([f"c{i}", c, ""])
    rows += [
        ["R²(來源示例)", rexp.get("quality_reported_in_source", {}).get("R2"), ""],
        [
            "RMSE_log10(來源示例)",
            rexp.get("quality_reported_in_source", {}).get("RMSE_log10"),
            "",
        ],
        [
            "max|resid|(來源示例)",
            rexp.get("quality_reported_in_source", {}).get("max_abs_residual_log10"),
            "",
        ],
        ["note", rexp.get("note"), ""],
        ["", ""],
        [
            "9 參數與材料關係 (material_coeff_relation)",
            "說明",
            "",
        ],
        ["描述", rel.get("description"), ""],
        [
            "納入固定9係數材料數",
            rel.get("materials_with_fixed_coeffs_count"),
            fmt(rel.get("materials_with_fixed_coeffs_sources")),
        ],
        [
            "未納入(無固定數值係數)",
            fmt(rel.get("materials_without_fixed_coeffs")),
            rel.get("note"),
        ],
        [
            "材料",
            "equation_type",
            "valid_range_K",
            "category/quantity",
            "c0",
            "c1",
            "c2",
            "c3",
            "c4",
            "c5",
            "c6",
            "c7",
            "c8",
            "coeffs_c0_c8",
            "source",
        ],
    ]
    rel_rows = rel.get("rows", [])
    for rr in rel_rows:
        rows.append(
            [
                rr.get("material"),
                rr.get("equation_type"),
                fmt(rr.get("valid_range_K")),
                rr.get("category") or rr.get("quantity"),
                fmt(rr.get("c0")),
                fmt(rr.get("c1")),
                fmt(rr.get("c2")),
                fmt(rr.get("c3")),
                fmt(rr.get("c4")),
                fmt(rr.get("c5")),
                fmt(rr.get("c6")),
                fmt(rr.get("c7")),
                fmt(rr.get("c8")),
                fmt(rr.get("coeffs_c0_c8")),
                rr.get("source"),
            ]
        )
    if not rel_rows:
        rows.append(
            [
                "(無 material_coeff_relation.rows，請重產生快照)",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        )
    sheets.append(("3-矩陣運算", rows))

    # 4. polyfit驗證
    rows = [
        ["Step 4 polyfit 去驗證"],
        ["目標", s4.get("goal")],
        [""],
        ["條件數(可靠度json)", "值"],
    ]
    for k, v in (s4.get("condition") or {}).items():
        rows.append([k, v])
    rows += [["", ""], ["基準(noise=1%,seed=42)", "kapton", "nbti"]]
    bk = s4.get("baseline_noise1_seed42", {}).get("kapton", {})
    bn = s4.get("baseline_noise1_seed42", {}).get("nbti", {})
    for key in [
        "r2",
        "rmse_log10",
        "alpha_extrap",
        "poly_slope_at_Tmin",
        "alpha_minus_slope",
        "k_at_20mK",
        "integral_2_300K",
        "tc_max_abs_resid_log10",
    ]:
        rows.append([key, fmt(bk.get(key)), fmt(bn.get(key))])
    rows += [["", ""], ["敏感度摘要", "kapton", "nbti"]]
    sk = s4.get("sensitivity_noise_seed", {}).get("kapton", {})
    sn = s4.get("sensitivity_noise_seed", {}).get("nbti", {})
    for key in [
        "n_runs",
        "r2_min",
        "rmse_max",
        "alpha_min",
        "alpha_max",
        "k20mK_min",
        "k20mK_max",
        "integral_min",
        "integral_max",
    ]:
        rows.append([key, fmt(sk.get(key)), fmt(sn.get(key))])
    rows += [
        ["", ""],
        [
            "Kapton 係數對照",
            "stored(c0..c8)",
            "fitted(c0..c8)",
            "abs_diff",
            "rel_diff_%",
        ],
    ]
    comp = s4.get("kapton_coeffdata_compare", {})
    sc = comp.get("stored_coeffs") or []
    fc = comp.get("fitted_coeffs_noise1_seed42") or []
    ad = comp.get("abs_diff") or []
    rd = comp.get("rel_diff_pct") or []
    for i in range(max(len(sc), len(fc), len(ad), len(rd))):
        rows.append(
            [
                f"c{i}",
                fmt(sc[i] if i < len(sc) else None),
                fmt(fc[i] if i < len(fc) else None),
                fmt(ad[i] if i < len(ad) else None),
                fmt(rd[i] if i < len(rd) else None),
            ]
        )
    rows += [
        ["", ""],
        ["NbTi 狀態", fmt(s4.get("nbti_coeffdata_status"))],
        ["", ""],
        ["解讀", "內容"],
    ]
    for it in s4.get("interpretation", []):
        rows.append(["-", it])
    # Tc residual points
    rows += [["", ""], ["NbTi Tc 區殘差點(基準)", "T", "resid_log10", "ratio_k/kfit"]]
    for p in bn.get("tc_points", []):
        rows.append(["", p.get("T"), p.get("resid_log10"), p.get("ratio_k/kfit")])
    sheets.append(("4-polyfit驗證", rows))

    # 係數與來源摘要
    rows = [
        ["係數/來源摘要(同源)"],
        [
            "材料",
            "equation_type",
            "valid_range_K",
            "coeffs c0..c8 or status",
            "source",
            "note",
        ],
    ]
    for sm in s1.get("database", {}).get("key_samples", []):
        rows.append(
            [
                sm.get("material"),
                sm.get("equation_type"),
                fmt(sm.get("valid_range_K")),
                fmt(sm.get("coeffs")),
                sm.get("source"),
                sm.get("note"),
            ]
        )
    sheets.append(("係數與來源摘要", rows))

    # 限制與錯誤
    rows = [
        ["限制與錯誤/降級紀錄"],
        ["類型", "內容"],
        ["政策", "不重擬合、不編造係數/結論；SSOT=heatload-coff-nist scripts"],
        ["範圍", "範圍外預設 0；低溫外推 k(T)=T^alpha 可能高估"],
        ["NbTi", "runtime_polyfit, coeffs=null（無固定數值）"],
        [
            "驗證",
            "深低溫 k(20mK) 外推不確定；積分(2-300K)較穩定；Tc 區殘差提示模型侷限",
        ],
        ["", ""],
        ["errors_count", len(snap.get("errors", []))],
    ]
    for e in snap.get("errors", []):
        rows.append(["error", e])
    sheets.append(("限制與錯誤", rows))

    return sheets


# ---------- HTML ----------


def js_json(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def build_html(snap):
    data = js_json(snap)
    html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>9 係數熱負載 4 步驟流程 — 視覺化與演示</title>
<style>
:root{{--bg:#0b1020;--panel:#121a33;--muted:#93a4c7;--text:#e8eefc;--accent:#6ea8fe;--ok:#7ee787;--warn:#ffcc66;--bad:#ff7b72;--line:#243055}}
*{{box-sizing:border-box}} body{{margin:0;font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,"Noto Sans TC",sans-serif;background:linear-gradient(180deg,#0b1020,#0e1530);color:var(--text)}}
header{{padding:18px 22px;border-bottom:1px solid var(--line);position:sticky;top:0;background:rgba(11,16,32,.92);backdrop-filter:blur(6px);z-index:5}}
h1{{margin:0 0 6px;font-size:20px}} .sub{{color:var(--muted);font-size:13px}}
.wrap{{max-width:1200px;margin:0 auto;padding:16px 18px 40px}}
.grid{{display:grid;grid-template-columns:repeat(12,1fr);gap:12px}}
.card{{grid-column:span 12;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 14px 12px}}
.card h2{{margin:0 0 8px;font-size:16px}} .h3{{margin:10px 0 6px;font-size:14px;color:#d7e3ff}}
.span6{{grid-column:span 6}} .span4{{grid-column:span 4}} .span8{{grid-column:span 8}}
.pill{{display:inline-block;padding:3px 8px;border-radius:999px;font-size:12px;margin:2px 6px 2px 0;border:1px solid var(--line);color:var(--muted)}}
.ok{{color:var(--ok);border-color:#2f5}} .warn{{color:var(--warn)}} .bad{{color:var(--bad)}}
.flow{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:8px 0}}
.step{{padding:8px 10px;border-radius:10px;border:1px solid #355; background:#0f1730;min-width:180px}}
.arrow{{color:var(--muted);font-size:18px}}
table{{width:100%;border-collapse:collapse;font-size:12.5px}} th,td{{border-bottom:1px solid var(--line);padding:6px 6px;vertical-align:top;text-align:left}}
th{{color:#cfe0ff;font-weight:600}} code, pre{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
pre{{white-space:pre-wrap;background:#0c142b;border:1px solid var(--line);padding:8px;border-radius:8px;font-size:12px;color:#dbe7ff}}
.muted{{color:var(--muted)}} .kpi{{font-size:22px;font-weight:700}} .small{{font-size:12px}}
svg{{max-width:100%;height:auto;background:#0c142b;border:1px solid var(--line);border-radius:8px}}
.tabs{{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 10px}} .tab{{cursor:pointer;padding:6px 10px;border:1px solid var(--line);border-radius:8px;color:var(--muted);background:#0f1730}} .tab.active{{color:var(--text);border-color:#4b6ab0}}
.section{{display:none}} .section.active{{display:block}}
.note{{border-left:3px solid var(--warn);padding:6px 10px;background:#1a1730;border-radius:6px;color:#f6e7bf;font-size:13px}}
.scroll{{max-height:420px;overflow:auto;border:1px solid var(--line);border-radius:8px}}
@media (max-width:900px){{.span6,.span4,.span8{{grid-column:span 12}}}}
</style>
</head>
<body>
<header>
  <h1>9 係數熱負載 4 步驟流程 — 視覺化與演示</h1>
  <div class="sub" id="meta"></div>
</header>
<div class="wrap">
  <div class="tabs" id="tabs"></div>

  <div id="sec-overview" class="section active">
    <div class="grid">
      <div class="card span8">
        <h2>流程總覽（同源快照驅動）</h2>
        <div class="flow">
          <div class="step"><b>1. 研究論文暨材料資料庫</b><div class="muted small">出處/原始係數庫/範圍</div></div><div class="arrow">→</div>
          <div class="step"><b>2. 物理推導 9 個參數</b><div class="muted small">log-log κ(T) 與 Q 積分</div></div><div class="arrow">→</div>
          <div class="step"><b>3. 矩陣運算得 9 參數</b><div class="muted small">推導c0..c8/物理意義/病態說明/材料關係</div></div><div class="arrow">→</div>
          <div class="step"><b>4. polyfit 去驗證</b><div class="muted small">R²/敏感度/殘差/限制</div></div>
        </div>
        <div id="policy"></div>
        <div class="note" style="margin-top:10px">原則：D4=A（僅用 heatload-coff-nist SSOT），不重擬合、不編造係數/結論；缺資料以 errors 降級呈現。</div>
      </div>
      <div class="card span4">
        <h2>產物與狀態</h2>
        <div id="artifacts"></div>
        <div id="errors"></div>
      </div>
      <div class="card span12">
        <h2>資料流（規格）</h2>
        <pre id="arch"></pre>
      </div>
    </div>
  </div>

  <div id="sec-s1" class="section"><div class="grid">
    <div class="card span12"><h2>Step 1：研究論文暨材料資料庫</h2><div id="s1-goal" class="muted"></div></div>
    <div class="card span7"><h2>上級論文/資料庫出處</h2><div id="s1refs"></div></div>
    <div class="card span5"><h2>係數資料庫摘要 (SSOT)</h2><div id="s1db"></div></div>
    <div class="card span12"><h2>資料庫原始資料 (raw_materials, 含 c0..c8)</h2><div id="s1raw" class="scroll"></div>
      <div class="note" style="margin-top:8px">來源 SSOT（coeff_data.py / coefficient_table.csv）；NbTi (Cri/oFlex 3) 為 runtime_polyfit，coeffs=null，不納入固定係數數值關係計算。</div></div>
    <div class="card span12"><h2>重點材料/係數樣本（索引）</h2><div id="s1samples"></div></div>
  </div></div>

  <div id="sec-s2" class="section"><div class="grid">
    <div class="card span12"><h2>Step 2：物理推導 9 個參數</h2><div id="s2-goal" class="muted"></div></div>
    <div class="card span6"><h2>κ(T) 9 參數模型</h2><pre id="s2kappa"></pre></div>
    <div class="card span6"><h2>熱負載積分模型</h2><pre id="s2heat"></pre></div>
    <div class="card span12"><h2>推導要點（依來源）</h2><div id="s2points"></div></div>
  </div></div>

  <div id="sec-s3" class="section"><div class="grid">
    <div class="card span12"><h2>Step 3：矩陣運算 得出 9 個參數</h2><div id="s3-goal" class="muted"></div></div>
    <div class="card span6"><h2>c0..c8 推導過程與 Vandermonde/正規方程</h2><pre id="s3matrix"></pre></div>
    <div class="card span6"><h2>9 參數 c0..c8 物理意義</h2><div id="s3meanings"></div></div>
    <div class="card span12"><h2>病態條件 (ill-conditioning) 與中心化/縮放：物理-數值推導與說明（先於圖表）</h2>
      <div id="s3condexp"></div>
      <div class="h3">條件數示例與圖表（來源示例）</div>
      <div id="s3cond"></div><div id="s3condchart" style="margin-top:8px"></div></div>
    <div class="card span12"><h2>9 參數與材料之關係（同源，固定 9 係數材料）</h2>
      <div id="s3relmeta" class="muted small"></div>
      <div class="h3">單一材料 c0..c8 輪廓圖</div>
      <div id="s3relprofile"></div>
      <div class="h3">各係數跨材料分佈統計圖（min/mean/max）</div>
      <div id="s3relstats"></div>
      <div class="h3">材料 × c0..c8 關係表</div>
      <div id="s3reltable" class="scroll"></div></div>
    <div class="card span12"><h2>Kapton 係數示例（c0..c8 = a..i，來源 md）</h2><div id="s3coeffs"></div>
      <div class="note">示例係數與品質指標引自推導文件；跨來源/重現差異屬步驟 4 驗證重點。</div></div>
  </div></div>

  <div id="sec-s4" class="section"><div class="grid">
    <div class="card span12"><h2>Step 4：polyfit 去驗證</h2><div id="s4-goal" class="muted"></div></div>
    <div class="card span6"><h2>基準與敏感度（可靠度 json）</h2><div id="s4base"></div></div>
    <div class="card span6"><h2>Kapton 係數對照 / NbTi 狀態</h2><div id="s4cmp"></div></div>
    <div class="card span12"><h2>Tc 區殘差與解讀</h2><div id="s4tc"></div><div id="s4interp" style="margin-top:8px"></div></div>
  </div></div>
</div>
<script>
const SNAP = {data};
const byId = id => document.getElementById(id);
const esc = s => String(s==null?'':s).replace(/[&<>]/g, c=>({{"&":"&amp;","<":"&lt;",">":"&gt;"}}[c]));
function fmt(v) {{
  if (v===null||v===undefined) return '';
  if (typeof v==='number') {{
    if (!isFinite(v)) return String(v);
    const av=Math.abs(v); if (av===0) return '0';
    if (av>=1e4 || (av>0 && av<1e-3)) return v.toExponential(4);
    return Number(v.toPrecision(6)).toString();
  }}
  if (typeof v==='object') return esc(JSON.stringify(v));
  return esc(v);
}}
function table(headers, rows) {{
  let h='<table><thead><tr>'+headers.map(x=>'<th>'+esc(x)+'</th>').join('')+'</tr></thead><tbody>';
  for(const r of (rows||[])) h+='<tr>'+r.map(x=>'<td>'+ (typeof x==='string'&&x.startsWith('<')?x:fmt(x)) +'</td>').join('')+'</tr>';
  return h+'</tbody></table>';
}}
function svgBars(items, opts) {{
  opts = opts||{{}}; const w=opts.w||560,h=opts.h||200,pad=44; const vals=items.map(i=>Number(i.v)||0);
  const maxAbs=Math.max(...vals.map(v=>Math.abs(v)),1e-12);
  const zeroY = h-28; const scale=(h-60)/(2*maxAbs);
  let s=`<svg viewBox="0 0 ${{w}} ${{h}}" xmlns="http://www.w3.org/2000/svg">`;
  s+=`<text x="10" y="16" fill="#93a4c7" font-size="11">${{esc(opts.title||'')}}</text>`;
  s+=`<line x1="${{pad}}" y1="${{zeroY}}" x2="${{w-10}}" y2="${{zeroY}}" stroke="#445" stroke-width="1"/>`;
  const bw=(w-pad-20)/Math.max(items.length,1)-6;
  items.forEach((it,i)=>{{const x=pad+i*((w-pad-20)/Math.max(items.length,1)); const v=Number(it.v)||0; const bh=v*scale; const y = bh>=0? zeroY-bh : zeroY; const hh=Math.abs(bh);
    s+=`<rect x="${{x}}" y="${{y}}" width="${{Math.max(bw,4)}}" height="${{Math.max(hh,0)}}" fill="${{opts.color||'#6ea8fe'}}"/>`;
    s+=`<text x="${{x}}" y="${{h-8}}" fill="#cfe0ff" font-size="10">${{esc(it.k)}}</text>`;
  }});
  return s+'</svg>';
}}
const tabs=[['overview','總覽'],['s1','1.論文/資料庫'],['s2','2.物理推導'],['s3','3.矩陣運算'],['s4','4.polyfit驗證']];
byId('tabs').innerHTML=tabs.map((t,i)=>`<div class="tab ${{i==0?'active':''}}" data-sec="sec-${{t[0]}}">${{t[1]}}</div>`).join('');
document.querySelectorAll('.tab').forEach(el=>el.onclick=()=>{{
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active')); el.classList.add('active');
  document.querySelectorAll('.section').forEach(x=>x.classList.remove('active')); byId(el.dataset.sec).classList.add('active');
}});
byId('meta').textContent = `生成時間: ${{SNAP.meta.generated_at}} | 同源: 9coeff_4step_flow.json → demo.html + demo.xlsx`;
byId('policy').innerHTML = `<span class="pill ok">D4=A SSOT</span><span class="pill warn">不重擬合/不編造</span><span class="pill">log-log 9 係數 c0..c8=a..i</span><span class="pill">範圍外預設0 / 低溫外推可能高估</span>`;
byId('arch').textContent = `1.研究論文暨材料資料庫 (citations + coefficient_table + coeff_data/raw_materials)\n  -> 2.物理推導9參數 (log10 κ=Σ c_n(log10 T)^n, Q_solid/Q_rf)\n  -> 3.矩陣運算得9參數 (c0..c8推導, 物理意義, 病態/中心化縮放說明, 係數-材料關係)\n  -> 4.polyfit驗證 (R²/RMSE/敏感度/Tc殘差/外推限制)\n  => docs/9coeff_4step_flow.json (同源快照) => demo.html + demo.xlsx`;
byId('artifacts').innerHTML = table(['產物','檔名'],[['規格','docs/9coeff_4step_視覺化規格.md'],['快照','docs/9coeff_4step_flow.json'],['HTML','docs/9coeff_4step_demo.html'],['Excel','docs/9coeff_4step_demo.xlsx']]);
const errs=SNAP.errors||[]; byId('errors').innerHTML = errs.length? `<div class="h3 bad">Errors / 降級紀錄 (${{errs.length}})</div><pre>${{esc(errs.join('\\n'))}}</pre>` : `<div class="h3 ok">errors: 無（或已完整載入）</div>`;

function getStep(id){{return SNAP.steps.find(s=>s.id===id)||{{}}}}
// Step1
const s1=getStep(1); byId('s1-goal').textContent=s1.goal||'';
byId('s1refs').innerHTML = table(['出處','識別/連結','內容'], (s1.provenance?.key_refs||[]).map(r=>[r.title, r.doi||r.url||r.dataset||r.source_file||'', r.content]));
const db=s1.database||{{}}; byId('s1db').innerHTML = `<div class="kpi">${{fmt(db.material_count_coeff_data)}}</div><div class="muted">coeff_data 材料筆數 (CSV: ${{fmt(db.material_count_csv)}})</div>`
  + table(['項目','值'], [['equation_types', JSON.stringify(db.equation_types||{{}})], ['SSOT', (db.ssot_paths||[]).join('<br>')]]);
const raw=db.raw_materials||[];
if(raw.length){{
  byId('s1raw').innerHTML = table(['材料','equation_type','valid_range_K','category/qty','c0','c1','c2','c3','c4','c5','c6','c7','c8','source','note'], raw.map(r=>[r.material,r.equation_type,r.valid_range_K,r.category||r.quantity,r.c0,r.c1,r.c2,r.c3,r.c4,r.c5,r.c6,r.c7,r.c8,r.source,r.note]));
}} else {{
  byId('s1raw').innerHTML = '<div class="muted">無 raw_materials（降級：請重產生快照）</div>';
}}
byId('s1samples').innerHTML = table(['材料','equation_type','valid_range_K','coeffs(c0..c8)','source / note'], (db.key_samples||[]).map(x=>[x.material,x.equation_type,x.valid_range_K,x.coeffs,(x.source||'') + (x.note?('\\n'+x.note):'')]));

// Step2
const s2=getStep(2); byId('s2-goal').textContent=s2.goal||'';
const lp=s2.model?.log_polynomial||{{}}; byId('s2kappa').textContent = `參數: ${{lp.params}}\n${{lp.formula_kappa}}\n${{lp.formula_eval}}\n單位: ${{lp.units}}\n範圍: ${{lp.validity}}\n\nrational_copper: ${{s2.model?.rational_copper?.formula}}\n${{s2.model?.rational_copper?.mapping}}`;
const hl=s2.model?.heatload||{{}}; byId('s2heat').textContent = `${{hl.solid_conduction}}\n${{hl.attenuator_dissipation}}\n${{hl.total}}`;
byId('s2points').innerHTML = '<ul>'+ (s2.derivation_points||[]).map(p=>'<li>'+esc(p)+'</li>').join('') + '</ul>' + `<div class="muted small">來源: ${{esc((s2.source_refs||[]).join(' | '))}}</div>`;

// Step3
const s3=getStep(3); byId('s3-goal').textContent=s3.goal||'';
const deriv=s3.derivation_c0_c8||{{}}; const steps=deriv.steps||[];
let mtxt = `目標: c0..c8 = argmin_c ||y - Xc||^2\n模型: ${{s3.problem_setup?.model}}\n資料: ${{s3.problem_setup?.data}}\n\n推導步驟:\n` + steps.map((s,i)=>`${{i+1}}. ${{s}}`).join('\n');
mtxt += `\n\nVandermonde: ${{s3.vandermonde?.definition}}\n正規方程:\n  ${{s3.normal_equation?.expand}}\n  ${{s3.normal_equation?.gradient_zero}}\n  ${{s3.normal_equation?.equation}}\n  ${{s3.normal_equation?.solution}}\n\n${{s3.normal_equation?.note||''}}\n\n結果形式: ${{deriv.result_form||''}}`;
byId('s3matrix').textContent = mtxt;
const meanings=s3.parameter_meanings_c0_c8||[];
byId('s3meanings').innerHTML = meanings.length? table(['參數','項/對應','物理意義'], meanings.map(m=>[m.param,m.term,m.meaning])) + `<div class="muted small">${{esc(s3.parameter_meaning_note||'')}}</div>` : '<div class="muted">無 parameter_meanings_c0_c8（降級：請重產生快照）</div>';
const condExp=s3.conditioning_explanation||{{}}; const dsteps=condExp.derivation_steps||[];
let cexpHtml = '';
if(dsteps.length){{
  cexpHtml += '<ul>' + dsteps.map(s=>'<li>'+esc(s)+'</li>').join('') + '</ul>';
  cexpHtml += `<div class="note" style="margin-top:8px"><b>條件數數值依賴說明：</b>${{esc(condExp.condition_number_dependency_note||'條件數數值依實作/定義/來源而異，須依各自來源解讀。')}}</div>`;
  cexpHtml += `<div class="muted small">依據: ${{esc((condExp.source_basis||[]).join(' | '))}}</div>`;
}} else {{
  cexpHtml = '<div class="muted">無 conditioning_explanation（降級：請重產生快照）</div>';
}}
byId('s3condexp').innerHTML = cexpHtml;
const ce=s3.conditioning_example||{{}}; byId('s3cond').innerHTML = table(['條件數指標(示例, 來源md)','值','來源/備註'],[['cond(X)',ce.cond_X,ce.source||''],['cond(X^T X)',ce.cond_XTX,''],['縮放',ce.scaling,''],['cond(X_scaled)',ce.cond_X_scaled,''],['改善倍數(約)',ce.improvement_factor_approx,'']]) + `<div class="muted small">${{esc(ce.interpretation||'')}}</div>`;
function logBarChart(items) {{
  const w=520,h=180,pad=40,vals=items.map(i=>Math.log10(Math.max(i.v,1))); const max=Math.max(...vals,1);
  const bw=(w-pad*2)/Math.max(items.length,1)-12; let s=`<svg viewBox="0 0 ${{w}} ${{h}}" xmlns="http://www.w3.org/2000/svg">`;
  s+=`<text x="10" y="16" fill="#93a4c7" font-size="11">log10(cond) 對比（示例，數值依實作/定義/來源）</text>`;
  items.forEach((it,i)=>{{const x=pad+i*((w-pad*2)/Math.max(items.length,1)); const val=Math.log10(Math.max(it.v,1)); const bh=(val/max)*(h-pad-30); const y=h-20-bh; s+=`<rect x="${{x}}" y="${{y}}" width="${{Math.max(bw,6)}}" height="${{Math.max(bh,0)}}" fill="#6ea8fe"/>`; s+=`<text x="${{x}}" y="${{h-6}}" fill="#cfe0ff" font-size="10">${{esc(it.k)}}</text>`; s+=`<text x="${{x}}" y="${{Math.max(y-4,12)}}" fill="#e8eefc" font-size="10">${{fmt(it.v)}}</text>`;}});
  return s+'</svg>';
}}
byId('s3condchart').innerHTML = logBarChart([['cond(X)',ce.cond_X],['cond(X^T X)',ce.cond_XTX],['cond(X_scaled)',ce.cond_X_scaled]].filter(x=>x[1]).map(x=>({{k:x[0],v:x[1]}})));
const rel=s3.material_coeff_relation||{{}}; const relRows=rel.rows||[];
byId('s3relmeta').textContent = (rel.description||'') + ` | 固定9係數材料數: ${{rel.materials_with_fixed_coeffs_count ?? relRows.length}} | 未納入(無固定係數): ${{(rel.materials_without_fixed_coeffs||[]).join(', ') || '無'}}`;
if(relRows.length){{
  const first=relRows[0];
  const profItems = Array.from({{length:9}},(_,i)=>({{k:'c'+i, v:first['c'+i]}}));
  byId('s3relprofile').innerHTML = `<div class="muted small">示例材料: ${{esc(first.material||'')}} (equation_type=${{esc(first.equation_type||'')}})</div>` + svgBars(profItems, {{title:'c0..c8 輪廓（示例材料）', color:'#7ee787'}});
  const coeffKeys=['c0','c1','c2','c3','c4','c5','c6','c7','c8'];
  const stats=coeffKeys.map(k=>{{const vals=relRows.map(r=>Number(r[k])).filter(v=>isFinite(v)); const min=Math.min(...vals), max=Math.max(...vals), mean=vals.reduce((a,b)=>a+b,0)/vals.length; return {{k, min, mean, max, count:vals.length}};}});
  const statItems = stats.map(s=>({{k:s.k, v:s.mean}}));
  byId('s3relstats').innerHTML = svgBars(statItems, {{title:'各係數跨材料平均值(mean) 概覽', color:'#6ea8fe'}}) + table(['coeff','count','min','mean','max'], stats.map(s=>[s.k,s.count,s.min,s.mean,s.max])) + `<div class="muted small">${{esc(rel.note||'')}}</div>`;
  byId('s3reltable').innerHTML = table(['材料','equation_type','valid_range_K','category/qty','c0','c1','c2','c3','c4','c5','c6','c7','c8','source'], relRows.map(r=>[r.material,r.equation_type,r.valid_range_K,r.category||r.quantity,r.c0,r.c1,r.c2,r.c3,r.c4,r.c5,r.c6,r.c7,r.c8,r.source]));
}} else {{
  byId('s3relprofile').innerHTML = '<div class="muted">無 material_coeff_relation.rows（降級：請重產生快照）</div>';
  byId('s3relstats').innerHTML = '';
  byId('s3reltable').innerHTML = '';
}}
const rexp=s3.result_example||{{}}; const coeffs=rexp.coeffs_c0_c8||[];
byId('s3coeffs').innerHTML = table(['係數','值(c0..c8=a..i)'], coeffs.map((c,i)=>['c'+i+' ( '+String.fromCharCode(97+i)+' )', c])) + table(['品質(來源示例)','值'], [['R²',rexp.quality_reported_in_source?.R2],['RMSE_log10',rexp.quality_reported_in_source?.RMSE_log10],['max|resid|',rexp.quality_reported_in_source?.max_abs_residual_log10]]);

// Step4
const s4=getStep(4); byId('s4-goal').textContent=s4.goal||'';
const b=s4.baseline_noise1_seed42||{{}}; const sens=s4.sensitivity_noise_seed||{{}};
function bRows(name){{const o=b[name]||{{}}; return [['R²',o.r2],['RMSE_log10',o.rmse_log10],['alpha_extrap',o.alpha_extrap],['poly_slope@Tmin',o.poly_slope_at_Tmin],['alpha-slope',o.alpha_minus_slope],['k(20mK)',o.k_at_20mK],['∫κdT 2-300K',o.integral_2_300K],['Tc max|resid|',o.tc_max_abs_resid_log10]];}}
byId('s4base').innerHTML = `<div class="h3">條件數</div>`+table(['指標','值'], Object.entries(s4.condition||{{}}))
 + `<div class="h3">基準 (noise=1%, seed=42)</div><div class="grid"><div class="card span6" style="padding:8px"><b>Kapton</b>`+table(['指標','值'],bRows('kapton'))+`</div><div class="card span6" style="padding:8px"><b>NbTi</b>`+table(['指標','值'],bRows('nbti'))+`</div></div>`
 + `<div class="h3">敏感度範圍</div>`+table(['材料','n','R²_min','RMSE_max','alpha範圍','k20mK範圍','∫κdT範圍'], [['kapton',sens.kapton?.n_runs,sens.kapton?.r2_min,sens.kapton?.rmse_max, fmt(sens.kapton?.alpha_min)+' ~ '+fmt(sens.kapton?.alpha_max), fmt(sens.kapton?.k20mK_min)+' ~ '+fmt(sens.kapton?.k20mK_max), fmt(sens.kapton?.integral_min)+' ~ '+fmt(sens.kapton?.integral_max)], ['nbti',sens.nbti?.n_runs,sens.nbti?.r2_min,sens.nbti?.rmse_max, fmt(sens.nbti?.alpha_min)+' ~ '+fmt(sens.nbti?.alpha_max), fmt(sens.nbti?.k20mK_min)+' ~ '+fmt(sens.nbti?.k20mK_max), fmt(sens.nbti?.integral_min)+' ~ '+fmt(sens.nbti?.integral_max)]]);
const comp=s4.kapton_coeffdata_compare||{{}}; const sc=comp.stored_coeffs||[], fc=comp.fitted_coeffs_noise1_seed42||[], ad=comp.abs_diff||[];
let cmpRows=[]; for(let i=0;i<Math.max(sc.length,fc.length);i++) cmpRows.push(['c'+i,sc[i],fc[i],ad[i],(comp.rel_diff_pct||[])[i]]);
byId('s4cmp').innerHTML = `<div class="h3">Kapton 係數對照（存檔 vs 驗證擬合）</div>`+table(['係數','stored','fitted(noise1,seed42)','abs diff','rel diff %'],cmpRows)+`<div class="muted small">${{esc(comp.stored_source||'')}}</div>`
 + `<div class="h3">NbTi 係數狀態</div><pre>${{esc(JSON.stringify(s4.nbti_coeffdata_status||{{}},null,2))}}</pre>`;
const tc=(b.nbti?.tc_points)||[]; byId('s4tc').innerHTML = tc.length? table(['T(K)','resid_log10','ratio k/kfit'], tc.map(p=>[p.T,p.resid_log10,p.ratio_k/kfit])) : '<div class="muted">無 Tc 殘差點資料</div>';
byId('s4interp').innerHTML = '<ul>'+ (s4.interpretation||[]).map(p=>'<li>'+esc(p)+'</li>').join('') + '</ul>';
</script>
</body></html>"""
    return html


def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    snap = build_snapshot()
    OUT_JSON.write_text(
        json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    OUT_HTML.write_text(build_html(snap), encoding="utf-8")
    sheets = build_excel_sheets(snap)
    write_xlsx(OUT_XLSX, sheets)
    print(f"WROTE {OUT_JSON}")
    print(f"WROTE {OUT_HTML}")
    print(f"WROTE {OUT_XLSX}")
    print(f"errors={len(snap.get('errors', []))}")
    for e in snap.get("errors", []):
        print(" -", e)


if __name__ == "__main__":
    main()
