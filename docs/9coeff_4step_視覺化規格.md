# 9 係數熱負載 4 步驟流程 — 視覺化與演示規格

> 主題：依 `heatload-coff-nist`（SSOT, D4=A）與 `topic-viz`（F 混合型：規格+同源快照+離線 HTML+Excel）將 9 係數 κ(T) 模型之建立與驗證流程，以易懂規格與可追溯證據呈現。  
> 流程：**1. 研究論文暨材料資料庫 → 2. 物理推導 9 個參數 → 3. 矩陣運算得出 9 個參數 → 4. polyfit 去驗證**。  
> 原則：**不重擬合、不編造係數/結論**；來源、單位、範圍、外推限制與不確定性必須明示。

## 1. 目標與範圍
- **目標**：把 9 係數（c0..c8 / a..i）熱負載模型從「文獻/資料庫來源」到「物理模型與擬合形式」到「最小二乘矩陣求解」再到「可靠度驗證」的完整鏈路可視化、可演示、可查核。
- **範圍**：上級論文/資料庫出處、係數資料庫**原始資料**與範例、κ(T)/Q_solid/Q_rf 模型與推導要點、log-log 8 階多項式最小二乘之 **c0..c8 推導與 9 參數物理意義**、**病態條件(ill-conditioning)與中心化/縮放之物理-數值推導說明（先於圖表）**、**9 參數與材料關係**、polyfit 可靠度與限制。
- **非目標**：不產生新擬合係數、不取代 SSOT（`~/.opencode/skills/heatload-coff-nist/scripts/{coeff_data,thermal_load}.py`）、不宣稱超出來源/驗證證據的物理精度。

## 2. 4 步驟規格（流程契約）

| 步驟 | 問題 | 輸入/來源 | 方法/產物 | 輸出/證據 |
|---|---|---|---|---|
| 1. 研究論文暨材料資料庫 | 9 係數從哪來、涵蓋哪些材料與範圍？原始資料長什麼樣？ | Raicu 2025 (EPJQT 12:124, Table 4/6)、Zenodo 10.5281/zenodo.15238913、NIST Cryogenics Index、Marquardt 2000、Simon 1992/NIST Monograph 177、Bradley 2006、Flynn；`citations.md`/`coefficient_table.*`/`coeff_data.py` | 蒐集與建庫並分四區塊呈現：a.上級論文/資料庫出處 b.係數資料庫摘要(SSOT) c.資料庫原始資料(raw data) d.重點材料/係數樣本(索引) | 54 筆原始資料（含 c0..c8/範圍/來源/註記；`NbTi (Cri/oFlex 3)` 為 `runtime_polyfit`, `coeffs=null`）、可追溯 DOI/URL/本機路徑、摘要與樣本索引 |
| 2. 物理推導 9 個參數 | 為何用 9 參數、代表什麼物理量？ | Fourier 熱傳導、Wiedemann–Franz（ρ 交叉驗證）、NIST/Raicu log-log 擬合形式；`SKILL.md`、`熱負載/MDs/基礎推導熱負載.md`、`熱負載/推導*多項式*.md` | 建立 κ(T) 與熱負載模型：`log10 κ(T)=Σ_{n=0}^{8} c_n (log10 T)^n`（a..i=c0..c8），`Q_solid=Σ(A/L)∫κdT`，`Q_rf=Σ P_in(1-10^{-α/10})`；`rational_copper` 為 Cu 例外 | 9 參數定義、單位、模型適用/範圍外政策（預設 0；可選低溫外推且可能高估） |
| 3. 矩陣運算得出 9 個參數 | 如何由資料求得 c0..c8？各參數物理意義？數值穩定性如何？係數與材料關係為何？ | log-log 資料點 `(x_i,y_i)=(log10 T_i, log10 k_i)`（PPMS TTO/既有擬合資料流程）；`推導柔性多項式耦合係數.md`、`推導柔性八階係數.md`；SSOT 係數表 | (a) 最小二乘 8 階多項式推導 c0..c8：Vandermonde `X_{i,j}=x_i^j`、`S(c)=||y-Xc||^2`、正規方程 `X^T X c = X^T y`、求解 `c`；並給出 c0..c8 物理意義。(b) **先**以物理-數值推導說明病態條件與中心化/縮放（再給示例圖表），並註明條件數數值依實作/定義/來源而異。(c) 呈現固定 9 係數材料之 c0..c8 與材料關係圖表/表 | c0..c8 推導步驟與結果形式、9 參數物理意義表、病態/縮放說明+示例圖表（含條件數依賴 caveat）、材料×c0..c8 關係表與分佈/輪廓圖（排除 `NbTi (Cri/oFlex 3)` `runtime_polyfit/null`） |
| 4. polyfit 去驗證 | 擬合/係數可靠嗎、限制在哪？ | `docs/polyfit_可靠度驗證.{json,md}`、`scripts/validate_polyfit_reliability.py`、`coeff_data` 對照 | 噪聲/seed 敏感度、條件數、殘差（含 NbTi Tc 區）、外推行為(α/斜率/k20mK)、積分穩定度、與存檔係數比較 | 可信區間/不穩定區、`NbTi=runtime_polyfit` 無固定係數、外推不確定性明示 |

### 2.1 A/B/C 實作要求（本次精修）
- **A. Step 1 — 分成四分頁/四區塊呈現**：快照 `steps[0]` 以四部分展示：(a) 上級論文/資料庫出處 (`provenance.key_refs`)、(b) 係數資料庫摘要 SSOT (`database.material_count_*`/`equation_types`/`categories`/`ssot_paths`)、(c) 資料庫原始資料 raw data (`database.raw_materials`，54 筆，含 c0..c8/coeffs_c0_c8/equation_type/valid_range_K/category/quantity/source/note)、(d) 重點材料/係數樣本索引 (`database.key_samples`)。HTML/Excel/Streamlit 需對應呈現（Streamlit Step 1 採四分頁 tabs）。
- **B. Step 3**：
  - **(a)** `derivation_c0_c8` 推導 c0..c8 求解過程；`parameter_meanings_c0_c8` 給出 c0..c8 各自物理意義（log-log 多項式在 x=log10(T) 基底上的層級貢獻/尺度與形狀調制；有效係數）。
  - **(b)** `conditioning_explanation` 先於圖表，從 Vandermonde/Gram 矩陣、x 冪次放大與基底相關性推導病態條件，並說明中心化/縮放對降低條件數之機制；`condition_number_dependency_note` 明確註記「條件數數值依實作/定義/來源而異（如 cond 範數、對象 X 或 XᵀX、縮放/平移、資料點/取樣與執行環境）」，示例圖表需標示來源/示例性質。
  - **(c)** `material_coeff_relation` 呈現**固定 9 係數材料（53 筆）**之 c0..c8 與材料關係（材料×係數表、單材料輪廓/跨材料統計圖）；**排除** `NbTi (Cri/oFlex 3)`（`runtime_polyfit`，`coeffs=null`），並於說明中標註。
- **C. 開啟 distill 文件（Streamlit）**：`scripts/9coeff_4step_streamlit_demo.py`「開啟 distill 文件」頁採 `st.radio`（取代 `selectbox`）與 `st.columns([3, 7])` 左3右7佈局（對齊 `@distill-showcase` 習慣）。

## 3. 架構與資料流（同源）
```mermaid
flowchart LR
  S1[1.論文暨材料資料庫\ncitations+coeff table+coeff_data\nraw_materials 54筆] --> S2[2.物理推導9參數\nlog10 κ=Σ c_n(log10 T)^n\nFourier ∫κdT, Q_solid/Q_rf]
  S2 --> S3[3.矩陣運算得9參數\nc0..c8推導+物理意義\n病態/縮放說明→示例圖表\n係數-材料關係(53筆固定)]
  S3 --> S4[4.polyfit驗證\nR²/RMSE/敏感度/Tc殘差\n外推與積分穩定度]
  S4 --> SNAP[docs/9coeff_4step_flow.json\n同源快照]
  SNAP --> HTML[docs/9coeff_4step_demo.html\n離線互動]
  SNAP --> XLSX[docs/9coeff_4step_demo.xlsx\n分頁表格]
  SNAP --> ST[Streamlit demo\n預設展示+開啟distill文件]
```
- **SSOT**：係數/引擎 `~/.opencode/skills/heatload-coff-nist/scripts/{coeff_data,thermal_load}.py`；驗證 `docs/polyfit_可靠度驗證.json`；出處 `references/citations.md`。
- **降級**：若某來源檔不可讀，快照記錄 `errors` 並以可得證據呈現，不補造。

## 4. 模型與資料契約（節錄，依來源）
- `log_polynomial`：$\log_{10}\kappa(T)=c_0+c_1\log_{10}T+\cdots+c_8(\log_{10}T)^8$，$\kappa=10^{(\cdot)}$（W/m/K）；Table 6 同形用於 ρ(T) [Ω·m]，不得當 κ。
- `rational_copper`（OFHC Cu）：$\log_{10}\kappa=\frac{a+cT^{1/2}+eT+gT^{3/2}+iT^2}{1+bT^{1/2}+dT+fT^{3/2}+hT^2}$，`(a..i)=(c0..c8)`。
- 熱負載：$Q_{solid}=\sum_j (A/L_j)\int_{T_{c,j}}^{T_{h,j}}\kappa(T)dT$；$Q_{rf}=\sum_j P_{in}(1-10^{-\alpha_j/10})$。
- 矩陣求解：$x_i=\log_{10}T_i,\;y_i=\log_{10}\kappa_i,\;X_{ij}=x_i^j,\;c=\arg\min\|y-Xc\|^2 \Rightarrow X^T X c=X^T y$。
- 範圍：各材料 `valid_range_K`；範圍外預設 κ=0；低溫 `extrapolate_low_t` 依 `k(T)=T^α`（可能高估）。NbTi(Cri/oFlex3) 為 `runtime_polyfit`、`coeffs=null`。

## 5. 視覺化與演示規格
- **規格文件**：本檔。
- **資料快照**：`docs/9coeff_4step_flow.json`（steps、sources、coeff_db 摘要、`database.raw_materials`、Step 3 `derivation_c0_c8`/`parameter_meanings_c0_c8`/`conditioning_explanation`/`material_coeff_relation`、verification 指標、errors、meta/provenance）。
- **離線 HTML**：`docs/9coeff_4step_demo.html`（單檔內嵌 CSS/JS/JSON/SVG；分步導覽 1→4；Step 1 原始資料表；Step 3 推導+物理意義+病態/縮放說明（先）與示例圖表+係數-材料關係圖表/表；Step 4 驗證與限制）。
- **Excel**：`docs/9coeff_4step_demo.xlsx`（同源快照；分頁：流程總覽、1-論文與資料庫(含原始資料)、2-物理推導、3-矩陣運算(含推導/物理意義/病態說明/材料關係)、4-polyfit驗證、係數與來源摘要、限制與錯誤）。stdlib `zipfile+xml` 可攜產生。
- **Streamlit（預設展示）**：`scripts/9coeff_4step_streamlit_demo.py` + `熱負載/pages/32_9coeff_4step_demo.py`；同源快照驅動；Step 1 原始資料、Step 3 A/B/C 圖文；「開啟 distill 文件」採 `radio` + 左3右7佈局。

## 6. 驗證與限制
- 驗證：`python3 -m py_compile scripts/9coeff_4step_viz.py scripts/9coeff_4step_streamlit_demo.py 熱負載/pages/32_9coeff_4step_demo.py`；執行產生 json/html/xlsx；抽查快照欄位與來源檔一致、HTML/Excel 同源、離線可開；確認 `errors` 與 A/B/C 覆蓋（53 固定係數納入關係、`NbTi (Cri/oFlex 3)` 排除/null）。
- 可靠度結論（依 `polyfit_可靠度驗證`）：擬合在擾動下有範圍變動；深低溫外推（k@20mK）高度不確定；積分(2–300K)相對穩定；NbTi 因 Tc 轉變與 runtime 擬合更不可靠且無固定係數。
- 不確定性：不同來源文件之示例條件數/係數可能因資料生成、縮放定義、範數/對象選擇或執行環境差異而不同，須各自標註來源，不互相冒充；病態/縮放之條件數數值須視為依實作/定義/來源之示例。

## 7. 重現與展示
```bash
cd ~/量傳線
# 產生同源快照與離線 HTML/Excel
python3 scripts/9coeff_4step_viz.py
# 輸出: docs/9coeff_4step_flow.json, docs/9coeff_4step_demo.html, docs/9coeff_4step_demo.xlsx

# Streamlit 演示工具（預設展示，並可開啟 distill/來源文件）
streamlit run scripts/9coeff_4step_streamlit_demo.py
# 或於 Streamlit pages 執行: 熱負載/pages/32_9coeff_4step_demo.py
```

## 8. 主要來源（可追溯）
- `~/.opencode/skills/heatload-coff-nist/{SKILL.md,references/citations.md,references/coefficient_table.md,references/00_熱負載總覽.md,scripts/coeff_data.py,scripts/thermal_load.py}`
- `~/量傳線/docs/polyfit_可靠度驗證.{json,md}`、`~/量傳線/scripts/validate_polyfit_reliability.py`
- `~/量傳線/熱負載/MDs/基礎推導熱負載.md`、`~/量傳線/熱負載/推導多項式耦合係數.md`、`~/量傳線/熱負載/推導柔性多項式耦合係數.md`、`~/量傳線/熱負載/推導柔性八階係數.md`
- `~/.opencode/skills/distill-showcase/{SKILL.md,app.py}` (Streamlit radio + columns[3,7] 習慣)
