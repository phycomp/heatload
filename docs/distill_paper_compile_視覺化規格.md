# Distill Paper Compile — 視覺化與演示規格（topic-viz Format F）

> 主題：將已沉澱之 heatload-distill 論文文件依序編譯並合併為整合稿（abstract, citation, chapter, reference），同時提供同源快照與離線可視化/演示。  
> 產物類型：**F 混合型**（規格 MD + 同源資料快照 JSON + 離線 HTML + Excel + 合併輸出）— 規格先行、資料同源、離線可開、可降級。  
> 原則：**證據有界、同源可追溯、不重擬合、不編造係數/結論**；SSOT 決策 **D4=A**（`~/.opencode/skills/heatload-coff-nist/scripts/{coeff_data,thermal_load}.py`）。缺資料/不可用來源以 `errors` 降級呈現，不以猜測補齊。

## 1. 目標與範圍
- **目標**：把分散於已沉澱 distill 文件中的論文要素，依指定順序 `abstract → citation → chapter → reference` 編譯、彙整並合併為一份 consolidated paper，同時以視覺化/演示工具（同源快照、HTML、Excel、Streamlit）呈現編譯來源、順序、各區塊內容、圖表與合併結果。
- **範圍（編譯來源，same-source/evidence-bounded）**：
  - 主要論文來源（編譯本文）：EN 由 `docs/heatload-distill_paper.md`（主）/`docs/heatload-distill_paper.tex`（對齊）編譯；ZH 由 `docs/heatload-distill_paper.zh.md`（主）/`docs/heatload-distill_paper.zh.tex`（對齊）編譯。
  - EN/ZH pairing（同源追蹤與一致性）：`docs/heatload-distill_paper.zh.md`、`docs/heatload-distill_paper.zh.tex` 與英文稿在章節/邏輯/內文/圖表(表格)/數值/公式/引用與邊界聲明上保持高度一致（語言/排版差異除外），已納入 snapshot `inputs` 追蹤與 availability 揭露。EN/ZH 之 abstract/chapter/reference 由各自對齊稿依同序編譯；citation/provenance 與 availability 為同源事實彙編（內容共享，標題/一致性說明依語言呈現）。
  - 引文與投稿脈絡：`docs/heatload-distill_期刊候選.md`（目標 *Cryogenics*、動機/限制/查核項）、`~/.opencode/skills/heatload-coff-nist/references/citations.md`
  - 同源流程/可靠度證據：`docs/9coeff_4step_flow.json`、`docs/polyfit_可靠度驗證.md`、`docs/polyfit_可靠度驗證.json`
  - 規格與整合脈絡：`docs/9coeff_4step_視覺化規格.md`、`docs/NIST9熱負載整合說明.md`
  - ljg-paper 筆記/地圖：`~/Context/20261119T120029--paper-heatload-distill__paper.org`、`~/Context/20261119T120029--paper-heatload-distill__paper-map.md`
- **非目標**：不重擬合/不新增或發明係數；不宣稱新量測；不重算或獨立驗證第三方（Smith et al. 2024）數值；不替代期刊投稿模板/政策查核；不修改 SSOT 或既有來源文件。

## 2. 編譯順序與區塊定義（契約）

| 順序 | 區塊 | 定義（從沉澱文件編譯） | 主要來源 | 邊界/備註 |
|---:|---|---|---|---|
| 1 | `abstract` | 摘要全文 | `heatload-distill_paper.md` `## Abstract` | 保留原證據措辭與限制 |
| 2 | `citation` | 引文與溯源彙編（Citations and Provenance, compiled）：目標期刊/投稿門檻、SSOT(D4=A)與計數邊界、同源快照識別、關鍵已驗證參考文獻（含 Smith et al. 2024 動機脈絡、Raicu/NIST/Marquardt/Bradley/Simon/Flynn 等來源角色） | `期刊候選.md` §0/§1/§4 要點、`9coeff_4step_flow.json` provenance+db、`paper.md` §2.2、`citations.md` | 僅彙編已存在/已驗證資訊；不新增未驗證書目細節；Smith 僅動機/比較脈絡 |
| 3 | `chapter` | 正文章節（1–8）：Introduction、Provenance/SSOT、Models & Numerical、Workflow & Artifacts、Reliability Evidence、Discussion、Limitations、Conclusion | `heatload-distill_paper.md` `## 1.`–`## 8.` | 依來源原文編譯（保持章節結構與內容）；Availability/References 依序單列 |
| 4 | `reference` | 參考文獻彙編 | `heatload-distill_paper.md` `## References`（footnote refs） | 以來源手稿既有合併參考為準；不臆造條目 |

**合併稿（consolidated paper）**：依上述順序輸出 `abstract → citation → chapter → reference`，並附 `Availability and Source Artifacts (compiled)` 作為來源/限制揭露（不改變四區塊編譯順序）。合併稿為同源編譯產物，非新投稿定稿。

## 3. SSOT / 證據邊界（必須保留）
- D4=A：僅用 heatload-coff-nist SSOT；**不重擬合、不編造係數/結論**。
- 資料庫邊界：54 筆原始條目（48 `log_polynomial`, 5 `rational_copper`, 1 `runtime_polyfit`），53 筆固定係數用於數值關係；`NbTi (Cri/oFlex 3)` 為 `runtime_polyfit` 且 `coeffs=null`，排除於固定係數數值關係。
- 可靠度邊界（條件性）：擬合區間積分（如 ∫₂³⁰⁰ κ dT）在測試擾動下相對穩定；深低溫外推與 `k(20 mK)` 高度敏感/僅量級示意；條件數依實作/定義/來源/範圍/縮放而異；NbTi 於 Tc 附近具結構殘差；Kapton 儲存 vs 驗證擬合係數差異大（`max |Δc|≈79.48`，依既有報告）。
- Smith et al. 2024 (doi:10.1109/TASC.2024.3350516, arXiv:2306.13574)：**已驗證動機/比較脈絡**，不重算/不延伸。
- 投稿：請求目標 *Cryogenics* (Elsevier)，**投稿前須查核最新 scope/guidelines/APC/article type/模板/政策**；`paper.tex` / `paper.zh.tex` 尚未套用當期期刊 class，中文稿 LaTeX（`xeCJK`/`Noto Sans CJK TC`）編譯未於本環境驗證。

## 4. 資料快照契約（`docs/distill_paper_compile_data.json`）
同源驅動 HTML/Excel、Streamlit 與合併輸出（單一快照）：

- `meta`: `compiled_at`, `generator`, `topic_viz_format`, `compile_order`, `policy`, `ssot_counts`
- `inputs`: 各來源檔案 `{path, exists, bytes, mtime|error}`（含 EN/ZH manuscript pairing）
- `sections`: `{abstract, citation, chapter, reference, consolidated, availability}`（EN 編譯文本）
- `sections_zh`: `{abstract, citation, chapter, reference, consolidated, availability}`（ZH 編譯文本；ZH abstract/chapter/reference 取自對齊之 ZH 稿，同序編譯）
- `outputs`: 產物路徑（json/html/xlsx/consolidated_md/consolidated_md_zh）
- `errors`: 編譯/讀取/降級紀錄（無則空陣列）

## 5. 視覺化與演示工具（結構與入口）

### 5.1 產生器（編譯/同源快照/離線產物）
- **腳本**：`scripts/distill_paper_compile_viz.py`
- **角色**：讀取沉澱來源 → 依序編譯四區塊 → 產生同源快照與離線產物（JSON/HTML/Excel/consolidated Markdown）。
- **不變邊界**：D4=A、no refit、no invented coefficients/claims、證據有界、降級入 `errors`。

### 5.2 Streamlit 展示（distill-showcase 結構，主入口，EN/ZH 雙語）
- **主入口（建議）**：`scripts/distill_paper_showcase/app.py`
- **結構（`@distill-showcase` 慣例）**：
  - `scripts/distill_paper_showcase/app.py`：單一入口；`st.set_page_config(...)` 僅在此呼叫一次；sidebar 以 `st.radio(..., horizontal=True)` 選擇子主題，並提供語言切換（雙語對照/中文/English，`radio(..., horizontal=True)`）。
  - `scripts/distill_paper_showcase/src/data.py`：專案根路徑定位、同源快照/輔助證據載入（快取）、EN/ZH 區塊存取（`sections`/`sections_zh`）、章節切分、格式化、圖表降級渲染與錯誤/降級呈現、一致性提示。
  - `scripts/distill_paper_showcase/src/views/`：各檢視模組（`render(bundle)`）—
    - `abstract.py`：摘要（EN/ZH/雙語對照）
    - `chapters.py`：章節 1–8（EN/ZH/雙語對照，依章瀏覽/完整檢視）
    - `charts.py`：圖表（同源證據，語言無關）
    - `citations.py`：引文與來源（citation/availability 同源共享；references 與 inputs 呈現 EN/ZH/雙語）
    - `consolidated.py`：合併稿（EN/ZH/雙語，分別可下載）
    - `overview.py`：總覽/邊界/來源狀態/EN-ZH 一致性檢查
  - `scripts/distill_paper_showcase/src/views/__init__.py`：檢視匯出。
- **資料驅動來源**：`docs/distill_paper_compile_data.json`（主，同源快照：`sections` EN + `sections_zh` ZH）並輔以同源 `docs/polyfit_可靠度驗證.json`、`docs/9coeff_4step_flow.json`、`docs/heatload-distill_paper_consolidated.md`、`docs/heatload-distill_paper_consolidated.zh.md`（皆可降級）。
- **展示內容**：**摘要**、**章節**、**圖表**，並提供**引文與來源**、**合併稿**與**總覽/一致性/降級紀錄**；支援 **EN/ZH/雙語對照** 呈現（摘要/章節/參考文獻/合併稿依語言編譯區塊顯示，citation/availability 與圖表為同源共享證據）。
- **EN/ZH 一致性（同源）**：ZH `abstract/chapter/reference/consolidated` 由 `docs/heatload-distill_paper.zh.md` 依同序編譯，與 EN 對齊稿在章節/邏輯/內文/圖表(表格)/數值/公式/引用與邊界聲明高度一致（語言與必要排版差異除外）；`citation`/`availability` 為同源事實彙編共享區塊，圖表與數值證據共用同源資料。展示層提供結構性一致性提示，但不改寫/不臆造內容。
- **圖表（同源、證據有界，不重擬合/不編造）**：資料庫組成（54/53/1）、條件數（log10 尺度輔助）、基準指標（R²/RMSE/∫₂³⁰⁰ κ dT、`k(20 mK)` 僅外推示意）、擾動敏感度範圍、NbTi Tc 結構殘差與溯源檢查（Kapton `max |Δc|≈79.48`、NbTi `runtime_polyfit, coeffs=null`）。
- **降級行為**：snapshot/輔助證據/ZH 區塊缺失或讀取失敗時顯示 `errors`/提示並保留可用區塊，不以猜測補齊。

### 5.3 相容保留入口（baseline 單檔）
- **腳本**：`scripts/distill_paper_compile_streamlit.py`
- **角色**：先前單檔 compiled-paper viewer，邏輯已重構/對齊至 distill-showcase 結構；保留作相容執行入口（同樣由同源 snapshot/證據驅動、具 EN/ZH 語言切換與降級）。

### 5.4 離線產物
- **離線 HTML**：`docs/distill_paper_compile_demo.html`（單檔自包含，內嵌 CSS/JS/JSON，無 CDN）
  - 視圖：Overview（順序/政策/計數/來源狀態）、Abstract、Citation & Provenance、Chapters、References、Consolidated Paper、Sources & Errors
- **Excel**：`docs/distill_paper_compile_demo.xlsx`（stdlib `zipfile+xml`，無額外依賴）
  - 分頁：Overview、Sources、Errors、Abstract、Citation、Chapters、References、Consolidated（文字/表格化呈現）
- **合併稿（EN）**：`docs/heatload-distill_paper_consolidated.md`（依 `abstract,citation,chapter,reference` 順序合併 + availability/限制附錄）
- **合併稿（ZH）**：`docs/heatload-distill_paper_consolidated.zh.md`（同序由對齊之 `docs/heatload-distill_paper.zh.md` 編譯，內容與 EN 高度一致；引文/溯源與 availability 沿用同源事實）

## 6. 降級與錯誤處理
- 來源缺失或不可讀：對應區塊標註 unavailable，記錄於 `errors`，其餘區塊/產物仍盡可能產出。
- 可選/環境相依來源（如 ljg org/map 路徑存在性）納入 inputs 狀態；不因單一輔助來源缺失而中止全體編譯。
- 互動視覺/圖表相依（如 `streamlit`、`pandas`/繪圖路徑）缺失時，Streamlit 無法執行或圖表退回表格/提示；離線同源產物仍可檢視。
- 不以推測補齊書目、數值或結論。

## 7. 驗證
- `python3 -m py_compile scripts/distill_paper_compile_viz.py scripts/distill_paper_compile_streamlit.py scripts/distill_paper_showcase/app.py scripts/distill_paper_showcase/src/data.py scripts/distill_paper_showcase/src/views/*.py`
- 執行產生器並確認產物存在且可讀：json/html/xlsx/consolidated_md/consolidated_md_zh
- `python3 -m json.tool docs/distill_paper_compile_data.json`；檢查 `errors`、`compile_order`、EN/ZH 區塊非空、`sections_zh` 與來源一致性
- 抽查 EN 合併稿順序為 Abstract → Citations and Provenance → Chapters (1–8) → References → Availability；ZH 合併稿同序且與 EN 章節/數值/引用/邊界高度一致
- 一致性檢查：SSOT 計數/邊界（54/53/runtime_polyfit/`coeffs=null`）、Smith 2024 引用、*Cryogenics* 查核聲明、no-refit/no-invention
- Streamlit（環境相依）：`streamlit run scripts/distill_paper_showcase/app.py`（主入口）或相容 `streamlit run scripts/distill_paper_compile_streamlit.py` 可載入 compiled snapshot 並顯示 EN/ZH/雙語之摘要/章節/圖表/引文/合併稿；若缺 `streamlit` 或圖表來源則依降級提示處理（本次未在無相依環境中執行互動驗證）

## 8. 重現
```bash
cd ~/量傳線
# 1) 編譯沉澱文件 → snapshot/HTML/Excel/consolidated
python3 scripts/distill_paper_compile_viz.py
# outputs: docs/distill_paper_compile_data.json, docs/distill_paper_compile_demo.html,
#          docs/distill_paper_compile_demo.xlsx, docs/heatload-distill_paper_consolidated.md

# 2) Streamlit 展示 compiled 論文（摘要/章節/圖表，需 streamlit）
# 主入口（distill-showcase 結構：單一 app.py、src/views/、sidebar radio horizontal）
streamlit run scripts/distill_paper_showcase/app.py
# 相容入口（單檔 baseline）
# streamlit run scripts/distill_paper_compile_streamlit.py
```

## 9. 已知限制/缺口（本次不宣稱完成）
- `~/量傳線/提昇論文品質.md` 為既有過時報告，未依當前改寫重生/驗證。
- TS ljg-paper validator（bun）於本環境不可用；無 emacs/Denote/org-lint；本環境目前缺 `streamlit/matplotlib/altair/plotly/scipy/openpyxl` 等互動視覺相依（Streamlit 展示腳本/模組已提供並通過語法檢查，但互動執行未在此環境驗證）。
- *Cryogenics* 當期投稿格式/APC/政策/範疇需外部查核；`docs/heatload-distill_paper.tex` / `.zh.tex` 未套模板；中文 LaTeX 編譯（字型/CJK）未於本環境驗證。
- Streamlit distill-showcase/相容入口已支援 EN/ZH/雙語對照（依同源 `sections`/`sections_zh`）；離線 HTML/Excel 目前仍以 EN `sections` 為主要展示內容（ZH consolidated/`sections_zh` 已在 snapshot/檔案中可得，但離線 UI 未提供語言切換）。
- 合併稿為編譯彙整稿，保留來源內容邊界，不代表已完成同儕審查潤飾或投稿格式定稿。
