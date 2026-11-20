# 溫區擬合物理模型整合、視覺化與文獻驗證 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將 CF3 對標推導中的物理溫區/熱負載計算整合為 heatload-distill 論文的「溫區擬合」物理模型（證據有界），開發對應之 topic-viz 視覺化/演示工具，並以 arxiv-search 蒐集相關推論以驗證該物理模型之正確性與適用邊界。

**Architecture:** 以現有同源/溯源鏈為骨幹：在 `docs/heatload-distill_paper.md`（EN）與 `docs/heatload-distill_paper.zh.md`（ZH，高度對齊）之模型章節新增「溫區擬合」物理溫區計算子節（Fourier 積分導熱、分溫階熱負載、溫區積分/長度回推正規化關係），來源錨定 `~/量傳線/三視圖/柔性/驗證/對標CF3規格電性熱負載物理推導.md` 與 `~/量傳線/溫區擬合/{02,03,04}` 既有推導/公式文件並與 SSOT κ(T) 積分用法一致；必要時同步 `.tex` 與編譯/展示鏈（`scripts/distill_paper_compile_viz.py`、`docs/distill_paper_compile_data.json`、consolidated/showcase）但不破壞既有 D4=A/不重擬合/不編造邊界。另依 topic-viz Format F 建立獨立之溫區擬合物理模型展示產物（spec + `*_viz_data.json` + offline HTML/Excel，可選 Streamlit showcase）與計算/產生腳本。文獻驗證以 `~/.agents/skills/arxiv-search/arxiv_search.py`（`arxiv` 4.1.0 可用）查詢並產出證據有界驗證紀錄文件，連結已知驗證文獻（Smith 2024、Raicu 2025 等）。

**Tech Stack:** Markdown/LaTeX（論文稿）、Python 3（`numpy`/stdlib；`arxiv` 4.1.0；既有 SSOT `~/.opencode/skills/heatload-coff-nist/scripts/{coeff_data,thermal_load}.py` 與/或專案 `src/量傳線設計/核心/熱負載NIST9.py` 作 κ(T)/∫κdT 參考）、topic-viz 產物（JSON/自包含 HTML/Excel by stdlib `zipfile+xml`）、現有 `scripts/distill_paper_compile_viz.py` 與 `scripts/distill_paper_showcase/*` 慣例。

**Spec:** 使用者需求（本對話）：(1) 以 `~/量傳線/三視圖/柔性/驗證/對標CF3規格電性熱負載物理推導.md` 加入物理溫區計算，成為 heatload-distill 論文之「溫區擬合」物理模型；(2) `@topic-viz` 開發視覺化、演示工具；(3) `@arxiv-search` 查詢相關推論並驗證此物理模型正確性。既有邊界與同源規格見 `docs/heatload-distill_paper.md`、`docs/NIST9熱負載整合說明.md`、`docs/9coeff_4step_視覺化規格.md`、`~/.opencode/skills/topic-viz/SKILL.md`。

## Global Constraints

- **證據有界 / 不擴權：** 不重擬合、不編造 κ(T) 係數或材料物性、不宣稱新量測；新增內容須可追溯至指定來源文件、既有專案產物、SSOT 定義或可驗證文獻。CF3/廠商數值僅作來源所述對標/推導脈絡，須標註來源與假設，不冒充本稿實測。
- **SSOT 與既有決策：** NIST 9 係數與 κ(T)/∫κdT 以 `~/.opencode/skills/heatload-coff-nist/scripts/{coeff_data,thermal_load}.py`（D4=A）為單一真相來源；`NbTi (Cri/oFlex 3)` 為 `runtime_polyfit` 且 `coeffs=null`，排除固定係數數值關係；沿用 D1–D6 非破壞性原則。
- **EN/ZH 對齊：** `docs/heatload-distill_paper.md` 與 `docs/heatload-distill_paper.zh.md` 章節結構/論證邏輯/關鍵公式與邊界聲明須保持高度一致（僅語言/排版差異）；若更新 `.tex`/consolidated/compile 產物，須維持同序與一致性並避免靜默漂移。
- **不破壞既有產物：** 保留 legacy/既有檔案與編譯鏈行為；新增檔案採明確命名（如 `溫區擬合_*` / `temperature_zone_*`）並記錄驗證；不修改/提交與本任務無關之髒工作區檔案。
- **環境相依誠實揭露：** `streamlit`/部分繪圖與科學套件可能缺失（目前已知 `arxiv` 4.1.0 可用；`rg/emacs-nox/bun` 已裝但 TS ljg-paper validator 有 SIGBUS 歷史限制）；互動/編譯驗證不可得時以 `py_compile`/可執行產生器/離線產物與錯誤記錄替代，不偽造執行結果。
- **單位與範圍：** 溫區/熱負載公式須明示單位、溫度區間與假設（穩態一維、線性近似或 κ(T) 積分、材料/幾何/薄膜效應與外推之適用限制），避免將示意外推當可靠預測。

## Review Focus

- **範圍外推被當定論：** 使用者依示例參數/外推（如 mK 級 κ 外推、線性溫度分布或 ΔT∝L/L² 簡化）得到結論時，模型與文件應明確區分「區間積分/來源支持」與「假設敏感之外推/示意」，避免將 20 mK 等深低溫點值或幾何反推當精確預測。
- **EN/ZH 與編譯鏈不同步：** 僅改 EN md 未同步 ZH/tex/consolidated/snapshot 會導致 `distill_paper_compile_viz.py` 產物與展示不一致；變更需檢查抽取段落（Abstract/1–8/Availability/References）與 `sections/sections_zh` 影響並再生對應產物。
- **引用不可驗證或錯植：** 將 CF3/內部推導文件寫成同儕文獻、或新增未查核書目/DOI；文獻驗證輸出須區分「已驗證 arXiv/期刊 metadata」與「專案內部來源/待查核」。
- **SSOT 邊界與 runtime 擬合誤用：** 在示例計算中把 `NbTi (Cri/oFlex 3)` runtime 擬合或非 SSOT 係數當固定權威值而未標註狀態/來源。
- **視覺化數值與來源不一致：** HTML/Excel/Streamlit 展示之數值未由同一 `*_viz_data.json`/明確公式驅動，或未標註 `errors`/降級/假設，造成看似精確但不可追溯。

---

## Subsystem A — 論文整合：溫區擬合物理模型（paper-distill）

### Task 1: 萃取來源並定義「溫區擬合 物理模型」內容邊界

**Files:**
- Read: `~/量傳線/三視圖/柔性/驗證/對標CF3規格電性熱負載物理推導.md`
- Read: `~/量傳線/溫區擬合/02_極低溫溫區與熱負載/crioFlex3回推量子比特溫區長度.md`
- Read: `~/量傳線/溫區擬合/03_熱傳導與熱導率模型/傅立葉導熱定律回推長度.md`, `~/量傳線/溫區擬合/03_熱傳導與熱導率模型/基礎推導熱負載.md`
- Read: `~/量傳線/溫區擬合/04_溫區長度回推與約束/推導溫區公式.md`, `~/量傳線/溫區擬合/04_溫區長度回推與約束/最大安全長度.md`
- Read: `docs/heatload-distill_paper.md:60-110`, `docs/heatload-distill_paper.zh.md` 對應段落
- Create: `docs/溫區擬合_物理模型_來源萃取.md`（短文，列出可納入之公式/假設/來源路徑與不可越界項）

**Interfaces:**
- Produces: 一份可追溯萃取清單（公式：$Q=\frac{A}{L}\int_{T_c}^{T_h}\kappa(T)dT$、$Q=\kappa A \Delta T/L$ 近似、W-F $\kappa=L_0T/\rho$ 與 $\rho=const$ 積分形式、溫區積分比 $L=L_{ref}(P_{ref}/P)(I_{image}/I_{ref})$、溫度分布/安全長度之條件性；來源標註；明確排除：新量測、新擬合係數、未驗證廠商斷言作定論）。

- [ ] **Step 1: 彙整公式與假設並寫入萃取文件**
  - 在 `docs/溫區擬合_物理模型_來源萃取.md` 建立章節：`## 來源`、`## 可納入之物理模型與公式`、`## 假設與適用邊界`、`## 不納入/不主張`、`## 與既有論文章節 3 的銜接點`。
- [ ] **Step 2: 自檢邊界**
  - Run: `sed -n '1,220p' docs/溫區擬合_物理模型_來源萃取.md`
  - Expected: 含 SSOT/D4=A 與「不重擬合/不新量測」邊界、列出各公式對應來源檔路徑。
- [ ] **Step 3: Commit（若使用者要求提交且範圍許可）**
  - `git add docs/溫區擬合_物理模型_來源萃取.md && git commit -m "docs: 萃取溫區擬合物理模型來源與邊界"`

### Task 2: 在 EN 論文新增「溫區擬合 物理模型」子節

**Files:**
- Modify: `docs/heatload-distill_paper.md`（建議於 `### 3.1` 後新增 `### 3.2 Physical temperature-zone calculation for 溫區擬合 (stage-wise conduction and length back-calculation)`，並將原 `3.2/3.3` 依序後移為 `3.3/3.4`，同步修正文內引用若有）
- Read: `docs/溫區擬合_物理模型_來源萃取.md`

**Interfaces:**
- Consumes: Task 1 萃取清單與來源路徑
- Produces: EN 稿含明確命名之「溫區擬合」物理模型子節，涵蓋：(a) 穩態 Fourier 導熱與分溫階積分 $Q_i=(A/L_i)\int_{T_{c,i}}^{T_{h,i}}\kappa(T)dT$（與 3.1 一致並延伸為溫區計算）、(b) 簡化/特例（$\kappa\approx const$、W-F 與 $\rho=const \Rightarrow Q=\frac{L_0A}{2\rho L}(T_h^2-T_c^2)$ 之條件性）、(c) 溫區積分比/正規化長度回推 $L=L_{ref}(P_{ref}/P_{image})(I_{image}/I_{ref})$、(d) 溫度分布與安全長度之假設相依性與限制；標註來源（CF3 對標推導文件、溫區擬合公式文件、標準定律）與不確定性。

- [ ] **Step 1: 編輯 EN 章節並調整編號**
  - 插入新子節並重編後續 3.x 標題；保持公式可讀（Markdown/LaTeX 數學）。
- [ ] **Step 2: 驗證結構與關鍵標記**
  - Run: `rg -n "^### 3\\.|溫區擬合|temperature-zone|Fourier|I_\{image\}|P_\{ref\}" docs/heatload-distill_paper.md`
  - Expected: 出現新子節標題與核心公式符號；`3.2/3.3/3.4` 連續且唯一。
- [ ] **Step 3: Commit**
  - `git add docs/heatload-distill_paper.md && git commit -m "docs(paper): add temperature-zone (溫區擬合) physical model section (EN)"`

### Task 3: 同步 ZH 論文與必要之 tex/編譯產物

**Files:**
- Modify: `docs/heatload-distill_paper.zh.md`（對應 EN 新增/重編子節，保持章節邏輯、公式、邊界聲明高度一致）
- Modify (if maintained): `docs/heatload-distill_paper.tex`, `docs/heatload-distill_paper.zh.tex`
- Modify/Regenerate (as applicable): `scripts/distill_paper_compile_viz.py` 僅在抽取邏輯受新結構影響時最小修正；`docs/heatload-distill_paper_consolidated.md`, `docs/heatload-distill_paper_consolidated.zh.md`, `docs/distill_paper_compile_data.json`（由編譯腳本重生）
- Read: `scripts/distill_paper_compile_viz.py`（確認章節抽取 regex：EN 自 `## 1. Introduction` 至 `## Availability`，ZH 自 `## 1. 緒論` 至 `## 可得性`；子節新增通常不需改 regex，但需驗證）

**Interfaces:**
- Consumes: Task 2 EN 定稿內容
- Produces: ZH 與 EN 對齊；編譯/同源快照反映更新內容與 `errors` 狀態（若可執行）。

- [ ] **Step 1: 更新 ZH md 對齊 EN**
  - 翻譯/對齊新增子節（建議標題含「溫區擬合物理模型」），保留公式與符號一致。
- [ ] **Step 2: 語法與一致性檢查（環境可得範圍）**
  - Run: `python3 -m py_compile scripts/distill_paper_compile_viz.py`
  - Run: `rg -n "^### 3\\.|溫區擬合" docs/heatload-distill_paper.md docs/heatload-distill_paper.zh.md`
  - Expected: 兩檔 3.x 結構對應；編譯腳本可解析。
- [ ] **Step 3: 重生編譯產物（若相依/路徑可用）**
  - Run: `cd ~/量傳線 && python3 scripts/distill_paper_compile_viz.py`
  - Expected: 更新 consolidated 與 `docs/distill_paper_compile_data.json`；`errors` 僅含環境已知/合理降級（記錄實際輸出）。若因路徑相依（如 `/home/sam/Context/...`）失敗，記錄錯誤並採最小可行修補或在驗證紀錄中說明。
- [ ] **Step 4: 檢查輸出**
  - Run: `python3 -m json.tool docs/distill_paper_compile_data.json >/dev/null && echo OK`
  - Run: `rg -n "溫區擬合|temperature-zone" docs/heatload-distill_paper_consolidated.md docs/heatload-distill_paper_consolidated.zh.md | head`
  - Expected: JSON 合法；consolidated 章節包含新增內容（若重生成功）。
- [ ] **Step 5: Commit**
  - `git add docs/heatload-distill_paper*.md docs/heatload-distill_paper*.tex docs/heatload-distill_paper_consolidated*.md docs/distill_paper_compile_data.json scripts/distill_paper_compile_viz.py`（僅限實際變更檔）並提交說明性訊息。

---

## Subsystem B — 視覺化與演示工具（topic-viz）

### Task 4: 定義溫區擬合物理模型視覺化規格與資料快照契約

**Files:**
- Read: `~/.opencode/skills/topic-viz/SKILL.md`, `~/.opencode/skills/topic-viz/references/format_playbook.md`
- Read: `docs/溫區擬合_物理模型_來源萃取.md`
- Create: `docs/溫區擬合_物理模型_viz_spec.md`
- Create: `docs/溫區擬合_物理模型_viz_data.json`（由 Task 5 腳本產生亦可；若先手寫範本須標註 generated_by）

**Interfaces:**
- Produces: spec 明確視圖/分頁（至少：溫區分段與邊界溫度、$Q=(A/L)\int\kappa dT$ 與簡化公式對照、溫區積分比/長度回推計算器式參數表、假設與限制/`errors` 欄位）；資料契約含 `meta`（source/provenance/assumptions/units）、`stages`、`models`、`backcalc`、`references`、`errors`。

- [ ] **Step 1: 撰寫 spec（Format F 混合：A 規格/公式 + C 曲線/分段示意可選 + E 參數表）**
  - 內容含輸入來源、輸出檔名、視圖、降級策略（無即時 κ(T) 計算時用文件列舉之示例點並標註）。
- [ ] **Step 2: 自檢**
  - Run: `sed -n '1,260p' docs/溫區擬合_物理模型_viz_spec.md`
  - Expected: 含 SSOT/來源路徑、視圖清單、資料欄位與限制聲明。
- [ ] **Step 3: Commit**
  - `git add docs/溫區擬合_物理模型_viz_spec.md && git commit -m "docs: add 溫區擬合 physical model viz spec"`

### Task 5: 實作資料快照與離線 demo 產生器（HTML/Excel）

**Files:**
- Create: `scripts/溫區擬合_physical_model_viz.py`（或等價 ASCII 安全檔名，如 `scripts/temperature_zone_physical_model_viz.py`；擇一並於 spec/文件一致引用）
- Create: `docs/溫區擬合_物理模型_viz_data.json`
- Create: `docs/溫區擬合_物理模型_viz_demo.html`
- Create: `docs/溫區擬合_物理模型_viz_demo.xlsx`
- Read: `scripts/distill_paper_compile_viz.py`、`scripts/9coeff_4step_viz.py`（若存在）作結構參考；`src/量傳線設計/核心/熱負載NIST9.py` 或 SSOT scripts 介面（可選，用於示例 ∫κdT）

**Interfaces:**
- Consumes: Task 4 spec/契約；CF3 推導之代表性溫區與數值（如 4–40 K、10–350 mK、0.4 m/0.2 m、125 μW/20 nW 等，須標註「來源示例/規格脈絡非本稿新量測」）
- Produces: 單一 JSON 快照驅動之自包含 HTML（內嵌 CSS/JS/SVG/JSON，無 CDN）與 Excel（多分頁：模型公式/參數、溫區案例、回推計算、限制與來源；優先 stdlib 產生 xlsx）。

- [ ] **Step 1: 實作快照組裝與輸出**
  - 腳本支援：讀取/內建示例參數 → 計算可由公式直接得到之量（如 $I$ 比值、線性/簡化 ΔT、示例 $Q=\kappa A\Delta T/L$）→ 寫入 JSON/HTML/XLSX；κ(T) 積分示例若無可用引擎則以文件化示例與 `errors` 降級。
- [ ] **Step 2: 產生與靜態驗證**
  - Run: `python3 -m py_compile scripts/temperature_zone_physical_model_viz.py`（或實際檔名）
  - Run: `cd ~/量傳線 && python3 scripts/temperature_zone_physical_model_viz.py`
  - Expected: 產生/更新 JSON、HTML、XLSX；終端無未處理例外（或僅記錄可追蹤 `errors`）。
- [ ] **Step 3: 內容一致性檢查**
  - Run: `python3 -m json.tool docs/溫區擬合_物理模型_viz_data.json >/dev/null && echo OK`
  - Run: `ls -lh docs/溫區擬合_物理模型_viz_demo.html docs/溫區擬合_物理模型_viz_demo.xlsx`
  - Expected: JSON 合法且含 `meta/errors`；兩個離線產物存在。
- [ ] **Step 4: Commit**
  - 加入 `scripts/*temperature_zone*viz*.py`、`docs/溫區擬合_物理模型_viz_*` 並提交。

### Task 6:（選用）Streamlit 互動展示骨架（環境相依）

**Files:**
- Create: `scripts/溫區擬合_physical_model_showcase/app.py`（或 `scripts/temperature_zone_physical_model_showcase/`）
- Create: `scripts/溫區擬合_physical_model_showcase/src/{data.py,views/__init__.py,views/overview.py,views/models.py,views/backcalc.py}`（依 spec 裁剪）
- Read: `~/.opencode/skills/topic-viz/references/streamlit_showcase.md`, `scripts/distill_paper_showcase/app.py`

**Interfaces:**
- Consumes: `docs/溫區擬合_物理模型_viz_data.json`
- Produces: 同源快照驅動展示；單次 `st.set_page_config`；單選一律 `st.radio`/`st.sidebar.radio`；可折疊區塊用 `with st.expander(...)`；寬度參數用 `width='stretch'/'content'`；缺相依時降級顯示 `errors`。

- [ ] **Step 1: 建立最小可載入結構與 `py_compile`**
  - Run: `python3 -m py_compile scripts/temperature_zone_physical_model_showcase/app.py scripts/temperature_zone_physical_model_showcase/src/data.py scripts/temperature_zone_physical_model_showcase/src/views/*.py`
  - Expected: 語法通過（即使未安裝 streamlit 亦可 py_compile）。
- [ ] **Step 2: 記錄互動驗證狀態**
  - Run (if available): `python3 -c "import streamlit"`；若可用再 `streamlit run ...` 煙囪測試；不可用則於 `docs/溫區擬合_物理模型_viz_spec.md` 或驗證紀錄註明「未執行（缺相依）」。
- [ ] **Step 3: Commit**

---

## Subsystem C — arXiv 文獻搜尋與物理模型正確性驗證

### Task 7: 執行 arxiv-search 並彙整相關推論

**Files:**
- Read/Execute: `~/.agents/skills/arxiv-search/arxiv_search.py`（使用 `python3`，`arxiv` 4.1.0 已確認可用）
- Create: `docs/溫區擬合_物理模型_arxiv驗證.md`

**Interfaces:**
- Produces: 查詢紀錄（query、日期、參數、命中摘要）與與本模型相關之推論對照：Fourier 積分/分溫階熱傳導（支持）、κ(T) 來源與積分估算實務（Smith 2024, Raicu 2025 等）、W-F 與低溫金屬/超導電子熱導適用條件、薄膜/邊界散射與簡化模型限制；區分「arXiv/已驗證 metadata 支持」與「教科書/專案內部推導」。

- [ ] **Step 1: 執行多組查詢並保存輸出**
  - Run: `python3 ~/.agents/skills/arxiv-search/arxiv_search.py "cryogenic cable thermal load conduction integral kappa(T) dilution refrigerator stages" --max-papers 8 --sort relevance`
  - Run: `python3 ~/.agents/skills/arxiv-search/arxiv_search.py "Wiedemann-Franz law low temperature thermal conductivity cryogenic interconnect" --max-papers 8 --sort relevance`
  - Run: `python3 ~/.agents/skills/arxiv-search/arxiv_search.py "Raicu cryogenic thermal modeling microwave high density signaling coaxial cable" --max-papers 5 --sort relevance`
  - Expected: 取得可引用之標題/摘要（含與 Smith/Raicu 相關線索者優先）；網路受限時記錄失敗與替代（既有引用）。
- [ ] **Step 2: 撰寫驗證報告**
  - 在 `docs/溫區擬合_物理模型_arxiv驗證.md` 建立：`## 查詢`、`## 相關文獻與推論`、`## 對本物理模型之支持點`、`## 限制與不確定性`、`## 結論（證據有界）`。明確結論：核心模型 $Q=(A/L)\int\kappa dT$ 與分溫階熱預算、W-F 作為金屬電子熱導關係（低溫/材料條件下）為標準物理且與低溫佈線熱建模文獻實務一致；長度回推/溫度分布之線性化屬假設相依簡化，須以 κ(T) 積分與實際邊界條件校核。
- [ ] **Step 3: 連結回論文/viz 來源說明**
  - 於萃取文件或 viz spec `references` 補充已驗證文獻（不杜撰未查核細節）。
- [ ] **Step 4: Commit**
  - `git add docs/溫區擬合_物理模型_arxiv驗證.md docs/溫區擬合_物理模型_來源萃取.md docs/溫區擬合_物理模型_viz_spec.md`（視實際修改）並提交。

### Task 8: 整體驗收與交付紀錄

**Files:**
- Modify: `docs/提昇論文品質.md` 或新建 `docs/溫區擬合_物理模型_實作與驗證紀錄.md`（擇一，避免覆寫歷史脈絡時須保留原資訊）

**Interfaces:**
- Produces: 一份交付/驗證清單：變更檔案、產生產物路徑、執行命令與結果（py_compile/json.tool/產生器/arXiv）、未完成項（tex 完整同步、Streamlit 實跑、外部期刊查核等）與已知限制。

- [ ] **Step 1: 彙總驗證結果**
  - 收集 Tasks 1–7 的命令與輸出摘要、`errors`/降級。
- [ ] **Step 2: 撰寫紀錄並最終自檢**
  - Run: `git status --short -- docs scripts`（僅檢視本任務相關路徑）
  - Expected: 僅本任務相關變更列出；無誤刪既有關鍵產物。
- [ ] **Step 3: Commit（若要求）**

## Notes for Implementers
- `scripts/distill_paper_compile_viz.py` 目前以 regex 擷取 EN `## Abstract`/`## 1. Introduction`→`## Availability`/`## References` 與 ZH 對應段；新增子節（`### 3.x`）應可被包含於 chapters，但務必重跑並檢查 consolidated 與 JSON。若調整章節編號，需同時檢查目錄式引用與人工連結。
- 論文主體強調 κ(T) 擬合溯源與可靠度；「溫區擬合 物理模型」應定位為**將 κ(T) 積分/熱傳導物理應用於溫區與長度/熱負載計算的模型化表述**，與 Step 2 物理詮釋一致，避免喧賓奪主或引入未支持之新結論。
- arXiv 結果具時效與查詢敏感性；報告須附查詢字串與日期，並保留與本主題最直接相關之條目（Smith 2024, Raicu 2025 等為高相關既知文獻）。

