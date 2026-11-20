# NIST 9 係數熱負載整合 — 易懂規格與視覺化演示

> 來源：本輪重構交付（D1=B, D2=D, D3=D, D4=A, D5=A, D6=C）。單一真相來源：`~/.opencode/skills/heatload-coff-nist/scripts/{coeff_data,thermal_load}.py`。本規格將重構文件轉為可視覺化、可演示的規格描述。

## 1. 目標與範圍
- **目標**：以 NIST 9 參數模型統一熱負載計算與模擬，並以可視覺化方式呈現 κ(T)、∫κdT、材料比較、多溫區穩態熱負載與 polyfit 可靠度。
- **範圍**：`~/量傳線/熱負載/pages` 舊目錄整合 + 新平台 `src/量傳線設計/核心/`、`pages/`；保留原始檔（D5=A）。
- **非目標**：不重擬合/不編造係數；不取代具 runtime 擬合性質之頁面邏輯的物理真值宣稱。

## 2. 決策規格（固定）
| 決策 | 值 | 規格意義 |
|---|---|---|
| D1 | B | 整合至新平台核心+頁面，同時處理 `熱負載/pages` |
| D2 | D | 交付：共用核心模組 + 重構/新增頁面 + 新模擬頁 |
| D3 | D | 功能：κ(T)/∫κdT 曲線、材料比較、多溫區穩態熱負載、參數掃描/模擬 |
| D4 | A | 9 係數資料/引擎僅來自 heatload-coff-nist 技能腳本 |
| D5 | A | 保留原檔，新增共用層/新頁面與 `_legacy` 備份 |
| D6 | C | 本輪完成實作與驗證 |

## 3. 架構規格（資料流）
```mermaid
flowchart LR
  subgraph SSOT[單一真相來源 D4=A]
    CD[coeff_data.py\n54 材料, c0..c8, 範圍/來源]
    TL[thermal_load.py\nk(T), ∫k dT, Q_solid+Q_rf]
  end
  subgraph Core[共用核心 D2]
    C1[src/量傳線設計/核心/熱負載NIST9.py\n薄封裝+曲線/比較/掃描]
    C2[熱負載/pages/_nist9_共用.py\n檔案載入核心/fallback]
  end
  subgraph Pages[頁面 D1/B D3/D D5/A]
    P1[pages/4熱負載.py + pages/20熱負載NIST9.py]
    P2[熱負載/pages/10nist低溫庫.py (重構)\n30nist9_熱負載模擬.py\n31nist9_polyfit_可靠度.py]
    P3[原檔保留: 16柔性八階擬合.py\nlegacy 備份]
  end
  subgraph Verify[驗證與演示]
    V1[scripts/validate_polyfit_reliability.py]
    V2[docs/polyfit_可靠度驗證.md/json]
    V3[scripts/nist9_viz_demo.py -> docs/nist9_viz_demo.html]
  end
  CD --> TL --> C1
  CD --> TL --> C2
  C1 --> P1
  C2 --> P2
  V1 --> V2 --> P2
  V2 --> V3
  C1 -.可選取樣.-> V3
```

## 4. 計算模型規格
| 項目 | 規格 |
|---|---|
| κ(T) | `log_polynomial`: `log10 κ = Σ_{n=0..8} c_n (log10 T)^n`；或 OFHC Cu `rational_copper`（依來源） |
| 固體導熱 | `Q_solid = Σ_i (A/L_i) ∫_{T_c,i}^{T_h,i} κ(T) dT`（log-spaced 梯形積分） |
| 衰減器/RF 耗散 | `Q_rf = Σ_i P_in (1 - 10^{-α_i/10})` |
| 範圍處理 | 預設範圍外 κ=0；可選低溫外推 `k(T)~T^alpha`（可能高估，須保守解讀） |
| 係數政策 | 僅使用具來源/範圍之固定 c0..c8；`NbTi (Cri/oFlex 3)` 無固定係數（`runtime_polyfit`）→ 不編造、不納入固定係數計算 |

## 5. 模組與頁面規格
| 類型 | 路徑 | 職責 | 狀態 |
|---|---|---|---|
| 核心 | `src/量傳線設計/核心/熱負載NIST9.py` | 材料查詢、κ/積分、曲線、比較、熱負載、掃描 | 新增 |
| 匯出 | `src/量傳線設計/核心/__init__.py` | 匯出 NIST9 API | 更新 |
| 共用層 | `熱負載/pages/_nist9_共用.py` | 舊頁面共用入口（核心優先/fallback） | 新增 |
| 新平台頁 | `pages/20熱負載NIST9.py` | κ(T)/∫κdT/比較/多溫區/掃描 | 新增 |
| 新平台頁 | `pages/4熱負載.py` | 原功能 + NIST 9 模擬分頁 | 擴充 |
| 舊目錄頁 | `熱負載/pages/10nist低溫庫.py` | NIST9 材料庫與估算（引擎化） | 重構 |
| 備份 | `熱負載/pages/10nist低溫庫_legacy.py` | 原 10 頁備份 | 新增 |
| 舊目錄頁 | `熱負載/pages/30nist9_熱負載模擬.py` | 完整 NIST9 模擬/掃描 | 新增 |
| 舊目錄頁 | `熱負載/pages/31nist9_polyfit_可靠度.py` | 可靠度報告呈現 | 新增 |
| 原檔保留 | `熱負載/pages/16柔性八階擬合.py` | runtime polyfit 原行為 | 未改 |
| 備份 | `熱負載/pages/16柔性八階擬合_legacy.py` | 原 16 頁備份 | 新增 |

## 6. API 規格（`熱負載NIST9.py` / 共用層）
| 函式 | 輸入（摘要） | 輸出（摘要） |
|---|---|---|
| `list_materials(kind?)` | `kind: 'k(T)'|'rho(T)'|None` | 材料清單+meta |
| `get_material(name)` / `resolve_material(...)` | 名稱或自訂 coeffs | 係數/方程/範圍/meta |
| `k_of_T(T, coeffs, ...)` | T/coeffs/範圍/外推 | κ(T) |
| `integrate_kappa(T_cold,T_hot,...)` | 區間與係數 | ∫κdT |
| `calculate_thermal_load(...)` | material/coeffs, stages, geometry, attenuation, pin | `total/solid/attenuator` + 各段明細 |
| `k_curve(...)` / `integral_curve(...)` | 材料與溫度範圍 | 曲線資料點 |
| `compare_materials(materials,...)` | 材料列表 | 各材料曲線/誤差 |
| `sweep_parameter(base,param,values)` | 基準設定+參數值 | 掃描結果序列 |
| `sweep_materials_heatload(materials,...)` | 材料列表+固定條件 | 熱負載比較序列 |

## 7. Polyfit 可靠度規格（16柔性八階擬合）
| 指標 | Kapton (baseline, noise=1%, seed=42) | NbTi (baseline) | 判讀 |
|---|---:|---:|---|
| R² | 0.999961 | 0.992615 | 擬合區間高，但 NbTi 較低 |
| RMSE(log10) | 0.004398 | 0.107797 | NbTi 結構性殘差較大 |
| α 範圍（擾動） | [-10.362, -10.175] | [-9.397, -9.210] | 外推斜率敏感 |
| k(20mK) 範圍 | [1.93e17, 4.03e17] | [4.44e15, 9.25e15] | 深低溫外推不可靠 |
| ∫₂³⁰⁰ κ dT 範圍 | [28.374, 29.124] | [2084.42, 2141.32] | 擬合區間積分相對穩定 |
| Tc 區殘差 | - | max |resid_log10|≈0.337 (7.6–11.4K) | NbTi Tc 轉變區不可由單一 8 階全域多項式精確描述 |
| `coeff_data` 狀態 | 固定係數有來源 | `coeffs=null`, `runtime_polyfit` | NbTi 不可編造固定係數 |

**驗收規則**：主熱負載計算須用固定來源 NIST 9 係數；runtime 擬合結果僅在明示條件下作區間/趨勢參考，深低溫外推須保守並標註不確定性。

## 8. 視覺化與演示工具規格
- **工具**：`scripts/nist9_viz_demo.py`
- **輸入**：`docs/polyfit_可靠度驗證.json`（必要）、NIST9 引擎（可選，用於取樣曲線/熱負載）
- **輸出**：`docs/nist9_viz_demo.html`（自包含，離線可開）、`docs/nist9_viz_data.json`（嵌入資料快照）
- **視圖**：總覽與決策、架構流、κ(T) 曲線、∫κdT 曲線、材料比較、多溫區熱負載分解、polyfit 可靠度儀表（R²/RMSE/α/k20mK/積分範圍/Tc 殘差）、檔案與 API 規格。
- **技術**：純 HTML/CSS/JS + SVG（無外部 CDN 依賴），資料內嵌。

## 9. 驗證規格
- `python3 -m py_compile <核心/頁面/腳本>` 通過。
- 核心 smoke：54 材料可列舉；`k_curve/integral_curve/calculate_thermal_load/compare_materials/sweep_parameter` 可執行。
- 可靠度重現：`python3 scripts/validate_polyfit_reliability.py` 產出 md/json。
- 演示生成：`python3 scripts/nist9_viz_demo.py` 產出 html/data。
