# Heatload-Distill 整合論文（編譯稿，中文版）

> **編譯工具：** `scripts/distill_paper_compile_viz.py` (topic-viz Format F)。  
> **編譯時間：** 2026-11-20T07:42:03.739912+00:00  
> **編譯順序：** abstract（摘要）→ citation（引文與溯源）→ chapter（章節）→ rawdata（附錄 A 原始係數參照資料）→ reference（參考文獻）。  
> **附錄 A：** SSOT 原始係數參照資料（54 筆，48 `log_polynomial` / 5 `rational_copper` / 1 `runtime_polyfit`）以同源方式嵌入，僅供溯源；`NbTi (Cri/oFlex 3)` 為 `runtime_polyfit` 且 `coeffs=null`，不賦予係數。  
> **政策/邊界：** 證據有界、同源可追溯；D4=A SSOT；不重擬合、不編造係數/結論。`NbTi (Cri/oFlex 3)` 為 `runtime_polyfit` 且 `coeffs=null`（排除於固定係數數值關係）。投稿前須查核 *Cryogenics* 當期 scope/guidelines/APC/article type。  
> **一致性說明：** 本編譯稿由 `docs/heatload-distill_paper.zh.md`（與 EN 稿在章節/邏輯/內文/圖表(表格)/數值/公式/引用與邊界聲明高度一致）依同序編譯；引文/溯源彙編與 availability 沿用同源事實內容。

## 摘要

低溫工程中的熱預算評估——包括稀釋冷凍機系統中支撐件與互連線的傳導熱——通常仰賴材料熱導率 κ(T) 的擬合表示式，尤其是 9 係數 log-log 多項式（c0..c8 / a..i）以及針對特定材料之來源特定有理式/RRR 形式[^nist][^marquardt][^bradley][^simon1992][^flynn][^raicu2025]。近期高密度超導佈線研究凸顯了其實務影響：Smith *et al.* 結合文獻熱導率值與電纜截面，估算 1 英呎長柔性 Nb–47 wt% Ti 同軸帶狀電纜由 1 K 至 100 mK 每條跡線之傳導熱負載為 5 nW，並與商用同軸與 NbTi-on-polyimide 撓性線選項進行比較[^smith2024]。此類 nW 等級估算直接取決於所使用的 κ(T) 資料與擬合、其有效溫度範圍，以及外推處理方式。

本文提出 **Heatload-Distill**：一套用於低溫熱負載估算中 9 係數 κ(T) 擬合之、以溯源為基礎且具可靠度感知的回顧與工作流程。該流程將實務組織為四個可追溯步驟：(1) 文獻與材料資料庫溯源、(2) 9 參數與熱負載方程式之物理/模型詮釋、(3) 矩陣/最小平方法求解與數值條件性、(4) polyfit 可靠度驗證。其以單一真實來源（SSOT，決策 D4=A）與同源產物（`topic-viz` Format F：規格 + 快照 + 離線 HTML/Excel，具降級與錯誤揭露）為依據。

依據 `docs/9coeff_4step_flow.json` 與相關產物，我們回顧 54 筆資料庫條目（48 `log_polynomial`、5 `rational_copper`、1 `runtime_polyfit`）以及 53 筆固定係數材料用於數值係數–材料關係；`NbTi (Cri/oFlex 3)` 為 `runtime_polyfit` 且 `coeffs=null`，排除於固定係數數值關係之外。既有驗證證據（合成 log-log 三次樣條產生器、8 階 `np.polyfit`、T=2–300 K、N=50 對數間距點、擾動研究）顯示，擬合區間內積分熱導率（∫₂³⁰⁰ κ dT）在測試擾動下相對穩定，而深低溫外推（例如 κ 在 20 mK）對擾動及擬合/流程選擇高度敏感，僅應視為量級指標。證據亦顯示原始冪次基底之強病態、全域 8 階擬合下 NbTi Tc 附近之材料特定結構殘差，以及儲存係數與驗證擬合 Kapton 係數間之巨大差異（max |Δc|≈79.48）。本文不重擬合或發明係數，亦不宣稱新的材料物性量測。我們結論：可信的低溫熱負載估算應建立於可追溯溯源、明確有效範圍、具條件性感知之詮釋與不確定性揭露，而非孤立之外推值或未記錄係數。

**關鍵詞：** 低溫工程、低溫熱導率、9 係數擬合、熱負載估算、稀釋冷凍機、溯源、數值條件性、polyfit 可靠度、回顧

## Citations and Provenance (compiled)

> Compiled from sedimented distill sources (same-source, evidence-bounded). No unverified bibliographic details added. Submission policies/scope/APC/article type for *Cryogenics* must be checked against the latest journal guidelines before submission.

### Target and submission context
- Requested target (from `docs/heatload-distill_期刊候選.md`): **Cryogenics (Elsevier)**; review + reliability-aware workflow, not new measurements/re-fitting.
- **投稿門檻（誠實揭露）**：不得宣稱新量測物性或重擬合係數；須明示 SSOT（D4=A）、54 筆/53 固定係數、`NbTi (Cri/oFlex 3)` 為 `runtime_polyfit` 且 `coeffs=null`、條件數依實作/定義/來源/範圍/縮放而異、深低溫外推（如 k@20 mK）僅量級示意、擬合區間 ∫κdT 在測試擾動下相對穩定（條件性）、Kapton 係數流程敏感性、Tc 區結構殘差、環境相依缺失（streamlit/matplotlib/altair/plotly/scipy/openpyxl 等）導致互動/視覺降級或未驗證項目。Smith et al. 僅作已驗證動機/脈絡引用，本稿不重算或獨立驗證其數值。

### Provenance and SSOT boundary (same-source)
- SSOT (D4=A): `~/.opencode/skills/heatload-coff-nist/scripts/coeff_data.py`, `~/.opencode/skills/heatload-coff-nist/scripts/thermal_load.py`
- Database: **54** entries total (raw rows: 54); equation types: `log_polynomial`=48, `rational_copper`=5, `runtime_polyfit`=1.
- Fixed-coefficient numeric relations set: **53**; `NbTi (Cri/oFlex 3)` is `runtime_polyfit` with `coeffs=null` (excluded from fixed-coefficient numeric relations, no invented coeffs).
- Same-source snapshot: `docs/9coeff_4step_flow.json` (generated_at: `2026-11-19T10:48:13`, errors: 0).

### Key verified references (from provenance snapshot)
- **Raicu et al. (2025) Cryogenic thermal modeling of microwave high density signaling** — `10.1140/epjqt/s40507-025-00427-1`: Table 4: k(T) 9-coeff fits (outer/dielectric/PTFE/inner). Table 6: rho(T) inner. PTFE coeffs sourced from NIST Cryogenics Index [9,10] per Table 4 note.
- **NIST Cryogenics Index of Material Properties** — `https://trc.nist.gov/cryogenics/materials/materialproperties.htm`: Cryogenic material property fits (a..i 9 coefficients) and valid ranges; primary database source for many entries.
- **NIST Cryogenics Material Properties: Equations** — `https://trc.nist.gov/cryogenics/materials/materialproperties.htm (equations)`: log-log polynomial form log10(y)=a+b(log10 T)+...+i(log10 T)^8 and related equation types.
- **Marquardt, Le & Radebaugh (2000) Cryogenic Material Properties Database** — `https://cryocooler.org/resources/Documents/C11/247.pdf`: Defines 9-parameter (a..i) cryogenic material property fits.
- **Bradley et al. (2006) Cryogenic Material Properties Database, Update 2006**: Database update (referenced by sources).
- **Simon, Drexler & Reed (1992) Properties of Copper and Copper Alloys at Cryogenic Temperatures**: OFHC Cu rational-form conductivity data/fits (RRR variants).
- **Flynn, Cryogenic Engineering**: Textbook basis for cryogenic heat load / multi-stage modeling (cited in skill overview).
- **Kapton (Cri/oFlex 3) 9-coeff (project-derived, documented source)** — `熱負載/推導柔性多項式耦合系數.md L138-166 / 16柔性八階擬合.py context`: Stored 7-sig-fig coeffs in coeff_data with stated provenance; used as fixed-coeff material entry (distinct from runtime_polyfit NbTi).
- **NbTi (Cri/oFlex 3) — no fixed coefficients** — `熱負載/pages/16柔性八階擬合.py`: NBTI_COEFFS not a numeric constant (runtime np.polyfit on simulated PPMS-like data, seed/noise dependent); coeff_data marks N/A runtime_polyfit (no invention).
- **Smith et al. (2024)** Improved Flexible Coaxial Ribbon Cable for High-Density Superconducting Arrays — `doi:10.1109/TASC.2024.3350516`, arXiv:2306.13574: verified motivating/comparison context only (literature κ(T)+cross-section heat-load estimation; reported 5 nW/trace 1 K→100 mK for 1-ft in cited work). Not re-computed or extended here.

### Source roles (as recorded in manuscript)
| Source | Role in this review | Notes |
|---|---|---|
| Raicu et al. (2025), *EPJ Quantum Technology* 12:124[^raicu2025] | Cryogenic thermal modeling context for microwave high-density signaling; upstream linkage recorded in project citations | Application context; not a source for new coefficients here |
| NIST Cryogenics Index of Material Properties[^nist] | Primary cryogenic material-property database reference | Upstream database/properties context |
| Marquardt et al. (2000)[^marquardt] | Cryogenic material properties database (11th International Cryocooler Conference), as recorded | Bibliographic details limited to project record |
| Bradley et al. (2006)[^bradley] | Cryogenic material properties database update (ICEC 21), as recorded | Bibliographic details limited to project record |
| Simon et al. (1992), NIST Monograph 177[^simon1992] | Properties of copper/copper alloys at cryogenic temperatures; supports OFHC copper source context (incl. `rational_copper` usage) | Source context for rational/RRR-related forms |
| Flynn, *Cryogenic Engineering*[^flynn] | Foundational cryogenic engineering/thermal-load modeling context, as recorded | Edition/publisher details not fully specified in project record |
| Smith et al. (2024), *IEEE Trans. Appl. Supercond.* / arXiv:2306.13574[^smith2024] | Verified application example of literature-based cryogenic cable heat-load estimation and material/cross-section comparison | Motivating context only; no re-computation performed here |
**Citation policy.** References are limited to sources already present in project provenance files plus the user-specified, programmatically verified Smith *et al.* paper (DOI/arXiv metadata/BibTeX retrieved). No unverified bibliographic details or external claims are added.

## 章節（編譯）

## 1. 緒論
### 1.1 低溫熱負載估算與 κ(T) 擬合的角色
超導電子與量子技術所用低溫系統對各溫階熱預算有嚴格限制。常見工程任務為估算電纜、支撐件與互連線之傳導熱流 $Q=\frac{A}{L}\int_{T_c}^{T_h}\kappa(T)\,dT$，有時結合耗散項。對多數材料而言，κ(T) 以緊湊擬合形式表示——最常見為 9 係數 log-log 多項式，以及針對 OFHC 銅等特定案例之來源特定有理式/RRR 關係——並透過低溫材料資料庫與既有建模研究提供[^nist][^marquardt][^bradley][^simon1992][^flynn][^raicu2025]。

此類表示式的影響具體可見。在高密度超導陣列脈絡中，Smith *et al.* 報導改良之 53 wt% Nb–47 wt% Ti 柔性同軸帶狀電纜（FLAX），並以組成材料之文獻 κ(T) 值依截面加權求和計算每條跡線熱負載；對 1 英呎電纜，其估算由 1 K 至 100 mK 每條跡線為 5 nW（約為其比較中最小商用超導同軸線之一半），同時亦指出此類計算中的材料相依權衡與假設（例如以 PTFE 資料估算 PFA、幾何/材料加權、以及 κ(T) 資料外推）[^smith2024]。此例說明：nW 至 µW 等級之設計決策可能取決於係數選擇、有效溫度範圍與外推行為。

### 1.2 問題：缺乏可追溯性的精確度
重用時的核心困難往往不在於係數是否可得，而在於脈絡流失：係數來源為何、在哪個溫度範圍有效、如何取得或以數值求解，以及外推值何時變得不可靠。熱負載數值可能看似精確，卻建立在未記錄之溯源、超出範圍評估、病態擬合或流程相依係數之上。對低溫工程實務而言，這會在比較、預算與溝通中產生可避免的風險。

### 1.3 目的與範圍
**目的。** 以既有 SSOT 紀錄與驗證產物為基礎，回顧並整合一套用於低溫熱負載估算中 9 係數 κ(T) 擬合之、以溯源為基礎且具可靠度感知的工作流程——**Heatload-Distill**。

**範圍內。** 溯源/資料庫紀錄（SSOT）、模型形式與參數詮釋、矩陣/最小平方法條件性考量、可靠度驗證結果，以及其對熱負載估算實務之意涵，並組織為同源可稽核鏈。

**範圍外。** 新的實驗量測、SSOT 固定係數之重擬合、缺漏係數之發明、將 runtime 擬合結果提升為固定材料性質，以及超出已引用/已驗證證據之主張（包括對第三方電纜設計之任何重算）。

### 1.4 貢獻
- **面向低溫實務之溯源回顧。** 我們將可信的 9 係數熱負載估算框定為跨越來源/資料庫、模型、數值求解與驗證邊界之可追溯鏈，並以實際低溫互連熱負載估算需求為動機[^smith2024][^raicu2025]。
- **同源整合工作流程。** 我們整合四步驟流程與產物（規格、快照、離線 HTML/Excel、快照驅動互動檢視），並與 SSOT 決策（D1–D6, D4=A）及可追溯輸出對齊。
- **基於證據之可靠度詮釋。** 我們綜整關於條件性、擾動敏感度、擬合區間積分穩定性、深低溫外推不確定性、係數/流程敏感性，以及材料特定模型結構殘差（NbTi 近 Tc）之既有證據，並轉化為保守使用指引。
- **目標期刊關聯性。** 我們將本工作定位為低溫工程方法/回顧貢獻：關注 κ(T) 擬合資料於熱負載估算之可追溯且具可靠度感知的使用，而非新的材料物性資料集。

## 2. 溯源與 SSOT：熱負載估算的基礎
### 2.1 溯源在低溫互連比較中的重要性
跨電纜或互連技術之熱負載比較可能對材料物性假設敏感。Smith *et al.* 明確地以文獻 κ(T) 值結合截面積計算熱導率/熱負載貢獻，使用 PTFE 值估算 PFA，並在比較中報告外推區域，同時討論依材料系統而異的導體主導與介電主導區間[^smith2024]。這並非否定此類估算；相反地，它突顯了可辯護比較需要透明的來源、範圍與外推處理——正是以溯源為基礎之工作流程必須保留的資訊。

### 2.2 來源角色（依專案溯源紀錄）
| 來源 | 在本回顧中的角色 | 備註 |
|---|---|---|
| Raicu et al. (2025), *EPJ Quantum Technology* 12:124[^raicu2025] | 微波高密度訊號之低溫熱建模脈絡；專案引用中記錄之上游連結 | 應用脈絡；此處非新係數來源 |
| NIST Cryogenics Index of Material Properties[^nist] | 主要低溫材料物性資料庫參考 | 上游資料庫/物性脈絡 |
| Marquardt et al. (2000)[^marquardt] | 低溫材料物性資料庫（第 11 屆 International Cryocooler Conference），依紀錄 | 書目細節限於專案紀錄 |
| Bradley et al. (2006)[^bradley] | 低溫材料物性資料庫更新（ICEC 21），依紀錄 | 書目細節限於專案紀錄 |
| Simon et al. (1992), NIST Monograph 177[^simon1992] | 低溫下銅與銅合金性質；支援 OFHC 銅來源脈絡（含 `rational_copper` 用途） | 有理式/RRR 相關形式之來源脈絡 |
| Flynn, *Cryogenic Engineering*[^flynn] | 基礎低溫工程/熱負載建模脈絡，依紀錄 | 版本/出版社細節於專案紀錄中未完全指定 |
| Smith et al. (2024), *IEEE Trans. Appl. Supercond.* / arXiv:2306.13574[^smith2024] | 基於文獻之低溫電纜熱負載估算與材料/截面比較之已驗證應用範例 | 僅動機脈絡；本文未重算 |

**引用政策。** 參考文獻僅限於已存在於專案溯源檔案中的來源，加上使用者指定且可程式化驗證之 Smith *et al.* 論文（DOI/arXiv metadata/BibTeX 已擷取）。不新增未驗證書目細節或外部主張。

### 2.3 SSOT 資料庫、涵蓋範圍與邊界
- **SSOT (D4=A)：** `~/.opencode/skills/heatload-coff-nist/scripts/coeff_data.py` 與 `thermal_load.py`（路徑與摘要記錄於 `docs/9coeff_4step_flow.json`）。
- **資料庫組成：** 共 54 筆材料條目 — 48 `log_polynomial`、5 `rational_copper`、1 `runtime_polyfit`。
- **固定係數分析集合：** 53 筆材料用於數值係數–材料關係。
- **Runtime 擬合例外：** `NbTi (Cri/oFlex 3)` 為 `runtime_polyfit` 且 `coeffs=null`（快照中來源/備註：runtime `np.polyfit` 於 seed=42 模擬資料，受 `noise_pct` 影響；無儲存數值常數）。因此其**排除於固定係數數值關係**之外，且不賦予發明之係數。
- **原始可追溯性：** Step 1 產物保留全部 54 筆原始列（材料、方程類型、有效範圍、c0..c8/coeffs、來源、備註）供逐列檢視。
- **專案決策（D1–D6）：** 非破壞性整合（B,D,D,A,A,C），在保留既有資產同時新增共用核心/頁面/同源產物（見 `docs/NIST9熱負載整合說明.md`、`docs/NIST9_視覺化規格.md`）。

## 3. 模型與數值公式化
### 3.1 熱導率與熱負載模型
對多數材料，κ(T) 以 log-log 多項式形式表示：
$$
\log_{10}\kappa(T)=\sum_{n=0}^{8} c_n \left(\log_{10}T\right)^n
$$
部分材料（例如 SSOT 中之 OFHC 銅條目）使用來源特定有理式/RRR 形式（`rational_copper`）[^simon1992][^nist][^marquardt][^bradley]。

專案產物中常用之分溫階傳導熱負載模型為：
$$
Q_{solid}=\sum_i \frac{A}{L_i}\int_{T_{c,i}}^{T_{h,i}}\kappa(T)\,dT
$$
並在適用時以選用耗散項 $Q_{rf}=\sum_i P_{in}\left(1-10^{-\alpha_i/10}\right)$ 表示。超出範圍處理與選用之低溫外推（例如驗證實作脈絡中擬合範圍以下 $k(T)\sim T^\alpha$）必須保守詮釋；外推值不等同於已驗證材料性質[^flynn][^raicu2025]。

### 3.2 「溫區擬合」之物理溫區計算（分溫階導熱與長度回推）
為將第 3.1 節之通用分溫階積分 $Q_{solid}$ 與實際低溫互連尺寸設計及溫區評估（「`溫區擬合`」，temperature-zone fitting 與分溫階物理計算）銜接，專案推導筆記（`docs/溫區擬合_物理模型_來源萃取.md`）將物理計算拆解為四個具條件邊界之層次：

1. **一維穩態傅立葉導熱與分溫階積分脈絡。** 在沿長度為 $L_i$ $[\text{m}]$、有效導熱截面積為 $A$ $[\text{m}^2]$ 之線段 $i$ 呈一維穩態軸向熱傳導，且區間內無中間熱錨分流、無側向輻射熱交換、亦無分散式內部熱源的假設下，跨越溫度邊界 $(T_{c,i}, T_{h,i})$ $[\text{K}]$ 之傳導熱負載 $Q_i$（或 $P_i$）$[\text{W}]$ 由非線性傅立葉定積分決定：
   $$
   Q_i = \frac{A}{L_i}\int_{T_{c,i}}^{T_{h,i}}\kappa(T)\,dT = \frac{A}{L_i}I_i, \qquad I_i = \int_{T_{c,i}}^{T_{h,i}}\kappa(T)\,dT \ \left[\text{W}\cdot\text{m}^{-1}\right]
   $$
   在專案對標推導（`~/量傳線/三視圖/柔性/驗證/對標CF3規格電性熱負載物理推導.md` 與 `~/量傳線/溫區擬合/03_熱傳導與熱導率模型/傅立葉導熱定律回推長度.md`）中，此分溫階公式係對照來源文獻所載之廠商參考溫階進行評估——例如 $4\text{–}40\text{ K}$ 溫階（$\Delta T=36\text{ K}$，$L=0.4\text{ m}$，對標基準 $<125\ \mu\text{W}/\text{ch}$）與 $10\text{–}350\text{ mK}$ 溫階（$\Delta T=340\text{ mK}$，$L=0.2\text{ m}$，對標基準 $\sim 20\text{ nW}/\text{ch}$）——嚴格作為具來源依據之規格/推導脈絡，而非新的實驗量測結果。

2. **簡化特例：常數/平均 $\kappa$ 與 Wiedemann–Franz（$\rho=\text{const}$）解析極限。** 在窄溫度區間或作數量級尺度估算時，以區間平均值 $\kappa_{avg}=\frac{1}{\Delta T}\int_{T_c}^{T_h}\kappa(T)\,dT$ 取代 $\kappa(T)$ 可得線性近似 $Q \approx \frac{\kappa_{avg}A}{L}\Delta T$（$\Delta T = T_h - T_c$）。對於處於低溫彈性雜質散射主導區、電阻率近似常數（$\rho(T)\approx \rho_0=\text{const}$，電阻 $R=\rho L/A$）之正常態金屬，將傅立葉導熱結合 Wiedemann–Franz 定律 $\kappa_e(T) = L_0 T/\rho$（$L_0 \approx 2.44\times 10^{-8}\ \text{W}\cdot\Omega\cdot\text{K}^{-2}$），可積分得出封閉形式之溫度平方差關係（`~/量傳線/溫區擬合/03_熱傳導與熱導率模型/基礎推導熱負載.md`）：
   $$
   Q = \frac{L_0 A}{2\rho L}\left(T_h^2 - T_c^2\right) = \frac{L_0 T_{avg}\Delta T}{R}, \qquad \kappa_{avg} = \frac{L_0 T_{avg}}{\rho}, \quad T_{avg}=\frac{T_h+T_c}{2}
   $$
   （當存在偏置電流 $I$ 時可疊加直流焦耳熱 $I^2 R$，而微波衰減耗散則銜接第 3.1 節之 $Q_{rf}$）。此平方差公式具嚴格條件限制：其**不適用**於非晶介電質基材（如 polyimide/Kapton，由聲子邊界散射與雙能階系統散射主導），**不適用**於臨界溫度以下之超導體（例如 NbTi 在 $T_c \approx 9.2\text{–}9.8\text{ K}$ 以下，庫柏對凝聚使電子熱導呈指數衰減並使 Wiedemann–Franz 關係失效），亦**不適用**於 $\rho(T)$ 隨溫度劇烈變化之較高溫非彈性散射區間（`~/量傳線/溫區擬合/04_溫區長度回推與約束/推導溫區公式.md`；該筆記中之分段冪次式僅作為定性物理機制示意，所有正式計算仍受第 2.3 節 SSOT D4=A 資料庫約束）。

3. **溫區熱導積分比與面積正規化之長度回推。** 由於多層柔性排線包含複合導體/介電質截面，其有效導熱截面積 $A$ 難以僅由外部規格書精確拆解，`~/量傳線/溫區擬合/03_熱傳導與熱導率模型/傅立葉導熱定律回推長度.md` 中之推導在**橫截面幾何與材料層疊結構完全相同**（$A_{image}=A_{ref}$）的前提下，將目標溫區（"$\text{image}$"）對基準溫區（"$\text{ref}$"）進行正規化相除：
   $$
   I_{ref}=\int_{T_{c,ref}}^{T_{h,ref}}\kappa(T)\,dT, \qquad I_{image}=\int_{T_{c,image}}^{T_{h,image}}\kappa(T)\,dT
   $$
   $$
   \frac{P_{image}}{P_{ref}} = \frac{L_{ref}}{L}\left(\frac{I_{image}}{I_{ref}}\right) \implies L = L_{ref}\left(\frac{P_{ref}}{P_{image}}\right)\left(\frac{I_{image}}{I_{ref}}\right)
   $$
   其中 $I_{image}/I_{ref}$ 為溫區熱導積分比（來源筆記中以基準溫階 $40\text{ K}\to 4\text{ K}$、$L_{ref}=40\text{ cm}, P_{ref}=125\ \mu\text{W}$ 擴展至目標溫階 $50\text{ K}\to 4\text{ K}$、示例積分比 $I_{image}/I_{ref}=1.48$ 作說明）。一旦比較異構層疊（例如 7 層 $300\ \mu\text{m}$ GSG 柔性線對比含導通孔之 11 層 $144.1\ \mu\text{m}$ FPC），此截面積 $A$ 之消去即不再成立，必須顯式保留分層面積比 $\sum_k A_k\int\kappa_k(T)\,dT$。

4. **極低溫溫度分布假設、量子比特退相干閾值與安全長度限制。** 在毫克耳文溫階（$10\text{–}350\text{ mK}$），探索性推導筆記（`~/量傳線/溫區擬合/02_極低溫溫區與熱負載/crioFlex3回推量子比特溫區長度.md` 與 `~/量傳線/溫區擬合/04_溫區長度回推與約束/最大安全長度.md`）將排線溫度分布與 transmon 熱激發閾值耦合。對於 $f_{01}=5.5\text{ GHz}$（$\alpha=-250\text{ MHz}$）之 transmon，要求激發態熱佔據率 $P_{|1\rangle}=\exp(-hf_{01}/k_B T)<1\%$（或 $n_{th}=[\exp(hf_{01}/k_B T)-1]^{-1}<0.01$）可得出臨界溫度 $T_{crit}\approx 57.6\text{ mK}$。在**簡化之常數 $\kappa$、無中途熱錨線性溫度分布** $T(x)=T_c+(T_h-T_c)(x/L)$（由 $T_c=10\text{ mK}$ 至 $T_h=350\text{ mK}$）假設下，對 $L=20\text{ cm}$ 而言，冷端低於 $T_{crit}$ 之區域長度為 $x_{safe}=L(T_{crit}-T_c)/(T_h-T_c)\approx 2.8\text{ cm}$；若要求 $x_{req}=5\text{ cm}$ 之安全區，則回推總長為 $L_{new}=x_{req}(T_h-T_c)/(T_{crit}-T_c)\approx 35.7\text{ cm}$（而另一含分散式自發熱 $\Delta T\propto L^2$ 之探索假設則給出 $L_{\max}\approx 7.5\text{ cm}$）。此類回推長度對邊界假設高度敏感：因 $\kappa(T)$ 在 mK 區間隨溫度強烈變化，穩態熱通量守恆 $\kappa(T)\frac{dT}{dx}=\text{const}$ 會產生非線性溫度分布；實際稀釋冷凍機配置亦仰賴分級熱錨與微波濾波/衰減器，而非單靠未錨定之懸空線段；且 SSOT 多項式擬合（通常有效範圍為 $\ge 1\text{–}4\text{ K}$，而 `NbTi (Cri/oFlex 3)` 為 `runtime_polyfit` 且 `coeffs=null`）不可外推至 $10\text{–}350\text{ mK}$ 並當作已驗證之材料性質。

### 3.3 9 參數擬合之最小平方法/矩陣觀點
令 $x_i=\log_{10}T_i$ 且 $y_i=\log_{10}\kappa(T_i)$，多項式模型可寫為
$$
y_i \approx \sum_{j=0}^{8} c_j x_i^j,\quad X_{i,j}=x_i^j,\quad y \approx Xc
$$
並以最小平方法求解（例如正規方程 $X^T X c = X^T y$ 或數值上更穩定之等價方法）。係數具實務詮釋（$c_0$ 尺度、$c_1$ 主趨勢、高階項曲率/細節），但在高階單項式基底中彼此相關，且可能對雜訊、縮放、範圍與實作細節敏感；不應視為獨立微觀常數。

### 3.4 數值條件性
此擬合之原始單項式/類 Vandermonde 基底具強病態。中心化/縮放可改善條件性，但所報告之條件數取決於實作、定義、來源資料、溫度範圍與縮放慣例。因此，在由係數值或衍生外推得出結論前，必須在脈絡中報告並詮釋條件性。

## 4. Heatload-Distill 工作流程與同源產物
### 4.1 產物契約
- **規格：** `docs/9coeff_4step_視覺化規格.md`
- **同源快照：** `docs/9coeff_4step_flow.json`（`errors: 0`，generated 2026-11-19T10:48:13）
- **離線產物：** `docs/9coeff_4step_demo.html`、`docs/9coeff_4step_demo.xlsx`
- **互動檢視：** `scripts/9coeff_4step_streamlit_demo.py`（快照驅動、可降級）與 wrapper `熱負載/pages/32_9coeff_4step_demo.py`
- **產生器：** `scripts/9coeff_4step_viz.py`

### 4.2 四步驟可追溯鏈
| 步驟 | 目標 | 主要證據/產物 | 邊界 |
|---|---|---|---|
| 1. 文獻與材料資料庫 | 固定溯源與可檢視輸入 | 54 筆原始列、溯源錨點、SSOT 路徑 | `NbTi (Cri/oFlex 3)` 明確標示為 `runtime_polyfit`、`coeffs=null` |
| 2. 9 參數之物理/模型詮釋 | 解釋參數如何進入 κ(T) 與熱負載模型 | 模型形式、$Q_{solid}$/$Q_{rf}$、範圍/外推規則 | 超出範圍/外推需保守詮釋 |
| 3. 9 參數之矩陣求解 | 解釋最小平方法求解、條件性、係數關係 | 設計矩陣/正規方程觀點、條件性/縮放注意事項、53 筆材料固定係數關係 | 條件數具脈絡相依性；NbTi 排除於固定係數數值關係 |
| 4. Polyfit 可靠度驗證 | 區分相對穩定輸出與敏感邊界 | `docs/polyfit_可靠度驗證.md/json`、快照 Step 4 摘要 | 驗證界定可信度；不確立新材料性質 |

### 4.3 非破壞性整合脈絡
依決策 D1–D5，在保留既有資產並使計算/顯示與 SSOT 對齊的同時，新增/重構共用核心模組與頁面（例如 `src/量傳線設計/核心/熱負載NIST9.py`、新增/更新頁面與 legacy 備份）。離線產物可檢視；當相依套件（`streamlit`、繪圖/科學/Excel 函式庫）不可用時，互動/視覺輸出可能降級或於執行期未驗證。

## 5. 可靠度證據回顧（Kapton 與 NbTi 案例）
> **證據基礎：** `docs/polyfit_可靠度驗證.md`、`docs/polyfit_可靠度驗證.json` 與 `docs/9coeff_4step_flow.json`（Step 4）。本節僅回顧既有驗證輸出。

### 5.1 驗證設定（依報告）
- 資料產生：`scipy.CubicSpline(log-log)`（報告為 `HAVE_SCIPY=True`）
- 擬合：$\log_{10}(k)=\sum_{n=0}^{8} c_n (\log_{10}T)^n$，n=0..8，使用 `np.polyfit(x,y,8)`
- 取樣：T = 2–300 K，N = 50，對數間距
- 實作中低溫外推：當 $T < T_{min}$，$k(T)=T^\alpha$（α 由端點行為定義）
- 擾動研究：noise ∈ {0,1,2,5}%、seeds = 6（每材料 24 次執行）

### 5.2 條件性與基準結果
| 量 | 報告值 / 觀察 | 詮釋 |
|---|---:|---|
| cond(V)_raw | 1.309×10^7 | 原始單項式基底嚴重病態 |
| cond(V^T V)_raw | 1.713×10^14 | 正規方程形式下條件性放大 |
| cond(V_centered_scaled) | 5.256×10^4 | 此設定下經中心化/縮放改善；高階敏感性仍存 |

| 指標 | Kapton（基準，noise=1%，seed=42） | NbTi（基準） | 詮釋 |
|---|---:|---:|---|
| R² | 0.999976 | 0.990847 | 擬合區間內擬合良好；NbTi 較低 |
| RMSE (log10) | 0.003461 | 0.121327 | NbTi 殘差較大 |
| α_extrap | -10.2796 | -9.2815 | 實作定義之外推指數 |
| k(20 mK) [W/m/K] | 2.916×10^17 | 5.875×10^15 | 深度外推，高度不確定（僅指標） |
| ∫₂³⁰⁰ κ dT [W/m] | 28.907 | 2226.46 | 本驗證中擬合區間積分相對穩定 |
| Tc 區域 max \|resid_log10\| | — | 0.492（~7.5–12.5 K 樣本） | 全域 8 階多項式下 NbTi 相變附近結構殘差 |

### 5.3 擾動敏感度與溯源檢查
- **Kapton（24 次執行）：** k(20 mK) 範圍 1.904×10^17–3.968×10^17 W/m/K；∫₂³⁰⁰ κ dT 範圍 28.737–29.497 W/m。
- **NbTi（24 次執行）：** k(20 mK) 範圍 3.837×10^15–7.995×10^15 W/m/K；∫₂³⁰⁰ κ dT 範圍 2209.92–2271.26 W/m；Tc 區域結構殘差持續存在。
- **詮釋：** 在測試擾動協議內，擬合區間積分保持相對穩定，而深低溫外推之 k(20 mK) 在報告執行中約變動 ~2 倍，但其遠在擬合範圍之外且對擬合/流程選擇敏感。這些外推值僅應視為保守量級指標，而非可靠預測。結果**不能**推廣至任意材料、幾何、溫度範圍或擬合管線。
- **Kapton 係數溯源檢查：** 儲存/來源係數與驗證擬合係數差異顯著（快照摘要中 `max_abs_diff ≈ 79.48`），與流程/產生器相依性一致，並強化溯源要求。
- **NbTi 狀態：** SSOT 記錄為 `runtime_polyfit` 且 `coeffs=null`；無固定係數集可用或可發明。

## 6. 討論與低溫熱負載估算實務指引
1. **從溯源與範圍出發，而非係數可得性。** 如基於文獻 κ(T) 與幾何加權之低溫電纜熱負載計算所示[^smith2024]，可辯護估算需要明確來源、材料對應與有效溫度區間；`runtime_polyfit`/缺漏固定係數必須保持可見。
2. **在有支持時使用擬合區間積分，保守看待外推。** 在報告驗證中，∫₂³⁰⁰ κ dT 在擾動下相對穩定，而 k(20 mK) 高度敏感且遠在擬合範圍外——僅適合作為量級指標，非可靠點預測。
3. **隨係數報告數值/擬合脈絡。** 高階單項式擬合具病態（此設定下 raw cond(V)=1.309×10^7、cond(V^T V)=1.713×10^14、centered/scaled 5.256×10^4）；條件數與係數值取決於實作/定義/來源/範圍/縮放。
4. **承認材料/模型限制。** NbTi 在 Tc 附近於全域 8 階多項式下呈現結構殘差，顯示單一函數形式在相變區可能不足；本稿記錄此限制，但不提出或擬合替代模型。
5. **保留可稽核產物。** 同源規格/快照/離線輸出與揭露之錯誤/降級（快照 `errors: 0`）支持可追溯性；環境相依之互動驗證應被報告而非假設。

## 7. 限制
- 本文為既有專案證據之回顧/整合，非新的實驗或重擬合研究。
- 資料庫涵蓋與方程類型受 SSOT 與上游來源限制；未量化完整材料/流程不確定性。
- 可靠度結論以報告之合成資料與擾動協議為條件，未經進一步驗證不得推廣。
- 所有互動/視覺元件之執行期驗證具環境相依性；在受限環境中，離線同源產物為主要可稽核紀錄。
- 動機電纜範例（Smith *et al.*）僅作已驗證脈絡使用；本稿不重算或獨立驗證第三方熱負載數值。
- 期刊適配性、文章型態與投稿要求必須依 *Cryogenics* 當期指南確認（見 `docs/heatload-distill_期刊候選.md`）。

## 8. 結論
Heatload-Distill 將 9 係數低溫 κ(T) 熱負載估算之溯源、建模、數值求解脈絡與可靠度證據整合為四步驟、同源、可稽核工作流程。來自 SSOT 紀錄與驗證產物的證據支持低溫工程使用上的明確邊界：在測試條件下，擬合區間積分量可相對穩定，而深低溫外推與高階係數對擾動、流程選擇與數值條件性敏感，且在特定區間（如 NbTi 近 Tc）存在材料特定結構殘差。因此，可信的熱負載估算應建立於可追溯溯源、明確有效範圍與不確定性揭露，而非未記錄或孤立之外推值。

## 附錄 A. SSOT 原始係數參照資料（54 筆）

> **定位：** 僅為**參照資料／附錄**（provenance 溯源脈絡），**非新量測、非重擬合、非新增係數**；正文結論不以此附錄改寫。  
> **來源（同源）：** SSOT D4=A 快照 `docs/9coeff_4step_flow.json` → `steps[id=1].database.raw_materials`，共 **54** 列（依快照原始順序）。  
> **組成：** 54 = `log_polynomial`=48, `rational_copper`=5, `runtime_polyfit`=1；其中固定係數可數值引用者 **53** 筆。  
> **排除項：** `NbTi (Cri/oFlex 3)` 為 `runtime_polyfit` 且 `coeffs=null`（執行期以 `np.polyfit` 產生，受 `noise_pct` 滑桿影響）；本附錄**不為其賦予任何係數**，並將其排除於固定係數數值關係之外。  
> **讀法：** `c0..c8` 逐列原樣轉錄，**僅供溯源**；`valid_range_K` 於快照中有 54/54 列為 `null`（SSOT 未記錄區間，不代填）。任何單列皆不得視為新資料、重擬合結果或外推授權。  
> **呈現：** 表格單元格中的 `|` 已轉義、換行已攤平；過長 `source`/`note` 已截斷（`…`）。

| # | material | category | equation_type | valid_range_K | c0 | c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 | source | note |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | Aluminum 1100 (UNS A91100) | Metal | log_polynomial | null | 0.07918 | 1.0957 | -0.07277 | 0.08084 | 0.02803 | -0.09464 | 0.04179 | -0.00571 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 2 | Aluminum 3003-F (UNS A93003) | Metal | log_polynomial | null | 0.23733 | 0.48068 | -0.17101 | 0.06534 | -0.01659 | -0.00579 | 0.00444 | -0.00089 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 3 | Aluminum 5083-O (UNS A95083) | Metal | log_polynomial | null | -0.57148 | 1.5397 | -0.97109 | 0.44247 | -0.13926 | 0.02341 | -0.00101 | -0.0005 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 4 | Aluminum 6061-T6 (UNS A96061) | Metal | log_polynomial | null | 0.07918 | 1.0957 | -0.07277 | 0.08084 | 0.02803 | -0.09464 | 0.04179 | -0.00571 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 5 | Aluminum 6063-T5 (UNS A96063) | Metal | log_polynomial | null | 0.07918 | 1.0957 | -0.07277 | 0.08084 | 0.02803 | -0.09464 | 0.04179 | -0.00571 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 6 | Beryllium | Metal | log_polynomial | null | 1.442 | -0.159 | 0.193 | -0.073 | 0.011 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 7 | Beryllium Copper | Metal | log_polynomial | null | -0.50015 | 1.9319 | -1.6954 | 0.71218 | 1.2788 | -1.6145 | 0.68722 | -0.10501 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 8 | Brass (UNS C2600) | Metal | log_polynomial | null | -0.786 | 1.37 | -0.5 | 0.1 | -0.01 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 9 | Copper (OFHC) RRR=50 | Metal | rational_copper | null | 1.8743 | -0.41538 | -0.6018 | 0.13294 | 0.26426 | -0.0219 | -0.051276 | 0.0014871 | 0.003723 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 10 | Copper (OFHC) RRR=100 | Metal | rational_copper | null | 2.2154 | -0.47461 | -0.88068 | 0.13871 | 0.29505 | -0.02043 | -0.04831 | 0.001281 | 0.003207 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 11 | Copper (OFHC) RRR=150 | Metal | rational_copper | null | 2.3797 | -0.4918 | -0.98615 | 0.13942 | 0.30475 | -0.019713 | -0.046897 | 0.0011969 | 0.0029988 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 12 | Copper (OFHC) RRR=300 | Metal | rational_copper | null | 1.357 | 0.3981 | 2.669 | -0.1346 | -0.6683 | 0.01342 | 0.05773 | 0.0002147 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 13 | Copper (OFHC) RRR=500 | Metal | rational_copper | null | 2.8075 | -0.54074 | -1.2777 | 0.15362 | 0.36444 | -0.02105 | -0.051727 | 0.0012226 | 0.0030964 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 14 | Inconel 718 (UNS N107718) | Metal | log_polynomial | null | -8.28921 | 39.447 | -83.4353 | 98.169 | -67.2088 | 26.7082 | -5.7205 | 0.51115 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 15 | Indium | Metal | log_polynomial | null | 1.5 | -0.5 | 0.1 | -0.02 | 0.003 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 16 | Invar (Fe-36Ni) (UNS K93600) | Metal | log_polynomial | null | -0.5 | 0.8 | -0.3 | 0.05 | -0.005 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 17 | Lead | Metal | log_polynomial | null | 38.963479 | -221.40505 | 597.56622 | -900.93831 | 816.40461 | -455.08342 | 152.94025 | -28.451163 | 2.2516244 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 18 | Molybdenum | Metal | log_polynomial | null | 1.8 | -0.3 | 0.05 | -0.008 | 0.001 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 19 | Nickel Steel Fe 2.25 Ni | Metal | log_polynomial | null | -0.3 | 0.5 | -0.2 | 0.03 | -0.003 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 20 | Nickel Steel Fe 3.25 Ni (UNS S20103) | Metal | log_polynomial | null | -0.3 | 0.5 | -0.2 | 0.03 | -0.003 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 21 | Nickel Steel Fe 5.0 Ni (UNS S20153) | Metal | log_polynomial | null | -0.3 | 0.5 | -0.2 | 0.03 | -0.003 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 22 | Nickel Steel Fe 9.0 Ni (UNS S21800) | Metal | log_polynomial | null | -0.3 | 0.5 | -0.2 | 0.03 | -0.003 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 23 | Platinum | Metal | log_polynomial | null | 1.5 | -0.3 | 0.05 | -0.008 | 0.001 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 24 | Stainless Steel 304 (UNS S30400) | Metal | log_polynomial | null | -1.4087 | 1.3982 | 0.2543 | -0.626 | 0.2334 | 0.4256 | -0.4658 | 0.165 | -0.0199 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 25 | Stainless Steel 304L (UNS S30403) | Metal | log_polynomial | null | -1.4087 | 1.3982 | 0.2543 | -0.626 | 0.2334 | 0.4256 | -0.4658 | 0.165 | -0.0199 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 26 | Stainless Steel 310 (UNS S31000) | Metal | log_polynomial | null | -1.4087 | 1.3982 | 0.2543 | -0.626 | 0.2334 | 0.4256 | -0.4658 | 0.165 | -0.0199 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 27 | Stainless Steel 316 (UNS S31600) | Metal | log_polynomial | null | -1.4087 | 1.3982 | 0.2543 | -0.626 | 0.2334 | 0.4256 | -0.4658 | 0.165 | -0.0199 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 28 | Ti-6Al-4V (UNS R56400) | Metal | log_polynomial | null | -5107.8774 | 19240.422 | -30789.064 | 27134.756 | -14226.379 | 4438.2154 | -763.07767 | 55.796592 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 29 | Apiezon N | Nonmetal | log_polynomial | null | -1.5 | 0.8 | -0.2 | 0.03 | -0.003 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 30 | Balsa | Nonmetal | log_polynomial | null | -2 | 0.5 | -0.1 | 0.01 | 0 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c4–c8=0（如實補 0） |
| 31 | Beechwood/phenolic | Nonmetal | log_polynomial | null | -1.8 | 0.6 | -0.15 | 0.02 | 0 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c4–c8=0（如實補 0） |
| 32 | Fiberglass Epoxy G-10 (Normal) | Nonmetal | log_polynomial | null | -4.1236 | 13.788 | -26.068 | 26.272 | -14.663 | 4.4954 | -0.6905 | 0.0397 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 33 | Fiberglass Epoxy G-10 (Warp) | Nonmetal | log_polynomial | null | -2.64827 | 8.80228 | -24.8998 | 41.1625 | -39.8754 | 23.1778 | -7.95635 | 1.48806 | -0.11701 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 34 | Glass Fabric/polyester | Nonmetal | log_polynomial | null | -1.5 | 0.5 | -0.1 | 0.01 | 0 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c4–c8=0（如實補 0） |
| 35 | Glass mat/epoxy | Nonmetal | log_polynomial | null | -1.5 | 0.5 | -0.1 | 0.01 | 0 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c4–c8=0（如實補 0） |
| 36 | Kevlar-49 Fiber (Aramid) | Nonmetal | log_polynomial | null | -1 | 0.3 | -0.05 | 0.005 | 0 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c4–c8=0（如實補 0） |
| 37 | Kevlar-49 Composite (Aramid) | Nonmetal | log_polynomial | null | -1 | 0.3 | -0.05 | 0.005 | 0 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c4–c8=0（如實補 0） |
| 38 | Polyamide (Nylon) | Nonmetal | log_polynomial | null | 2.738 | -30.677 | 89.43 | -136.99 | 124.69 | -69.556 | 23.32 | -4.3135 | 0.33829 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 39 | Polyethylene Terephthalate (Mylar) | Nonmetal | log_polynomial | null | -2.6135 | 2.3239 | -4.7586 | 7.1602 | -4.9155 | 1.6324 | -0.2507 | 0.0131 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 40 | Polyimide (Kapton) | Nonmetal | log_polynomial | null | 5.73101 | -39.5199 | 79.9313 | -83.8572 | 50.9157 | -17.9835 | 3.42413 | -0.27133 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 41 | Polystyrene (density 2 lb/ft3) | Nonmetal | log_polynomial | null | -1145.45 | 4086.02 | -6234.293 | 5260.106 | -2649.914 | 797.0372 | -132.5244 | 9.3968 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 42 | Polystyrene (density 3.12 lb/ft3) | Nonmetal | log_polynomial | null | -1.5194 | -4.6449 | 11.643 | -15.969 | 12.722 | -5.821 | 1.4174 | -0.14128 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 43 | Polystyrene (density 6.24 lb/ft3) | Nonmetal | log_polynomial | null | 7.39582 | -59.6737 | 160.58 | -240.33 | 218.817 | -124.155 | 42.9088 | -8.26683 | 0.68082 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 44 | Polyurethane | Nonmetal | log_polynomial | null | -1.5 | 0.5 | -0.1 | 0.01 | 0 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c4–c8=0（如實補 0） |
| 45 | Polyvinyl Chloride (PVC) | Nonmetal | log_polynomial | null | -1.5 | 0.5 | -0.1 | 0.01 | 0 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c4–c8=0（如實補 0） |
| 46 | Sapphire | Nonmetal | log_polynomial | null | 3 | -0.5 | 0.1 | -0.02 | 0.003 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 47 | Silicon | Nonmetal | log_polynomial | null | 3.5 | -0.6 | 0.12 | -0.02 | 0.003 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 48 | Teflon (PTFE) | Nonmetal | log_polynomial | null | -2 | 0.5 | -0.1 | 0.01 | 0 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c4–c8=0（如實補 0） |
| 49 | Raicu outer (C7150) | k(T) | log_polynomial | null | -3.198399 | 20.49947 | -66.11415 | 117.6898 | -121.4773 | 76.21467 | -28.74949 | 5.984756 | -0.5266892 | Raicu et al. 2025, EPJQT 12:124, Table 4 (k(T)) |  |
| 50 | Raicu dielectric (PTFE) | k(T) | log_polynomial | null | 2.738 | -30.677 | 89.43 | -136.99 | 124.69 | -69.556 | 23.32 | -4.3135 | 0.33829 | Raicu et al. 2025, EPJQT 12:124, Table 4 (k(T))；PTFE 源自 NIST DB [9,10] |  |
| 51 | Raicu inner (Ag-coated C7150) | k(T) | log_polynomial | null | -2.750003 | 25.84512 | -74.18405 | 113.5856 | -96.84387 | 46.38328 | -11.82451 | 1.321682 | -0.02456645 | Raicu et al. 2025, EPJQT 12:124, Table 4 (k(T)) |  |
| 52 | Raicu rho inner (Table 6) | rho(T) | log_polynomial | null | -8.327474 | 10.01214 | -52.83315 | 122.547 | -152.7599 | 109.0327 | -44.41614 | 9.598158 | -0.8539285 | Raicu et al. 2025, EPJQT 12:124, Table 6 (rho(T), ohm·m) |  |
| 53 | Kapton (Cri/oFlex 3) | k(T) | log_polynomial | null | -4.769084 | 10.92915 | -26.55324 | 36.1195 | -27.08454 | 11.58217 | -2.777787 | 0.3432157 | -0.01715343 | 推導柔性多項式耦合系數.md L138-166 / 16柔性八階擬合.py（Cri/oFlex 3，7 位有效數字） |  |
| 54 | NbTi (Cri/oFlex 3) | k(T) | runtime_polyfit | null | null (runtime_polyfit) | null (runtime_polyfit) | null (runtime_polyfit) | null (runtime_polyfit) | null (runtime_polyfit) | null (runtime_polyfit) | null (runtime_polyfit) | null (runtime_polyfit) | null (runtime_polyfit) | 讀不到固定數值：16柔性八階擬合.py 於執行期以 np.polyfit 對 seed=42 模擬 PPMS 資料擬合，且受 noise_pct 滑桿影響；原始檔未提供 NBTI_COEFFS 數字常數，故不填寫（不編… |  |

*附錄列數：54 列（`log_polynomial`=48, `rational_copper`=5, `runtime_polyfit`=1）；固定係數 53 筆；`runtime_polyfit` 排除 1 筆。*

## 參考文獻（編譯）
[^raicu2025]: Raicu, N., Hogan, T., Wu, X., Vahidpour, M., Snow, D., Hollister, M., & Field, M. (2025). *Cryogenic thermal modeling of microwave high density signaling*. EPJ Quantum Technology, 12:124. https://doi.org/10.1140/epjqt/s40507-025-00427-1 (Dataset: https://doi.org/10.5281/zenodo.15238913)
[^nist]: NIST Cryogenics Index of Material Properties. https://trc.nist.gov/cryogenics/materials/materialproperties.htm
[^marquardt]: Marquardt, E. D., Le, J. P., & Radebaugh, R. (2000). *Cryogenic Material Properties Database*. 11th International Cryocooler Conference.（書目細節依專案引用紀錄。）
[^bradley]: Bradley, P. E., et al. (2006). *Cryogenic Material Properties Database, Update 2006*. ICEC 21.（書目細節依專案引用紀錄。）
[^simon1992]: Simon, N. J., Drexler, E. S., & Reed, R. P. (1992). *Properties of Copper and Copper Alloys at Cryogenic Temperatures*. NIST Monograph 177. NIST.
[^flynn]: Flynn, T. M. *Cryogenic Engineering*.（版本/出版社細節於專案引用中未完全指定。）
[^smith2024]: Smith, J. P., Mazin, B. A., Boaventura, A., Thompson, K. J., & Daal, M. (2024). *Improved Flexible Coaxial Ribbon Cable for High-Density Superconducting Arrays*. IEEE Transactions on Applied Superconductivity, 34(2), 1–6. https://doi.org/10.1109/TASC.2024.3350516 (arXiv:2306.13574, https://arxiv.org/abs/2306.13574)

## Availability and Source Artifacts (compiled)

Primary sedimented distill paper documents and same-source artifacts used for compilation:
- `/home/sam/量傳線/docs/heatload-distill_paper.md` (ok)
- `/home/sam/量傳線/docs/heatload-distill_paper.tex` (ok)
- `/home/sam/量傳線/docs/heatload-distill_paper.zh.md` (ok)
- `/home/sam/量傳線/docs/heatload-distill_paper.zh.tex` (ok)
- `/home/sam/量傳線/docs/heatload-distill_期刊候選.md` (ok)
- `/home/sam/量傳線/docs/9coeff_4step_flow.json` (ok)
- `/home/sam/量傳線/docs/polyfit_可靠度驗證.json` (ok)
- `/home/sam/量傳線/docs/polyfit_可靠度驗證.md` (ok)
- `/home/sam/量傳線/docs/9coeff_4step_視覺化規格.md` (ok)
- `/home/sam/量傳線/docs/NIST9熱負載整合說明.md` (ok)
- `/home/sam/Context/20261119T120029--paper-heatload-distill__paper.org` (ok)
- `/home/sam/Context/20261119T120029--paper-heatload-distill__paper-map.md` (ok)
- `/home/sam/.opencode/skills/heatload-coff-nist/references/citations.md` (ok)
- `/home/sam/量傳線/docs/9coeff_4step_flow.json` (ok)
- `/home/sam/量傳線/docs/9coeff_4step_視覺化規格.md` (ok)
- `/home/sam/量傳線/docs/9coeff_4step_demo.html` (ok)
- `/home/sam/量傳線/docs/9coeff_4step_demo.xlsx` (ok)
- `/home/sam/量傳線/docs/溫區擬合_科學成果沉澱.md` (ok)
- `/home/sam/量傳線/docs/溫區擬合_物理模型_來源萃取.md` (ok)
- `/home/sam/量傳線/docs/溫區擬合_物理模型_arxiv驗證.md` (ok)
- `/home/sam/量傳線/docs/溫區擬合_物理模型_viz_spec.md` (ok)
- `/home/sam/量傳線/docs/溫區擬合_物理模型_fitting示意圖.svg` (ok)

Key artifacts: `docs/heatload-distill_paper.md/.tex` (EN), `docs/heatload-distill_paper.zh.md/.tex` (ZH, aligned in sections/logic/content/tables/values/formulas/citations/boundaries), `docs/heatload-distill_期刊候選.md`, `docs/9coeff_4step_flow.json`, `docs/polyfit_可靠度驗證.md/.json`, ljg-paper org/map, `docs/9coeff_4step_視覺化規格.md`, `docs/NIST9熱負載整合說明.md`, SSOT/provenance under `~/.opencode/skills/heatload-coff-nist/`.

**Limitations/gaps (not resolved by this compilation):** consolidated/sections currently compiled from EN sedimented source (ZH pairing tracked as same-source input but not merged into compiled text); raw SSOT data is embedded only as **Appendix A / `rawdata` reference** (same-source, 54 rows: 48 `log_polynomial` + 5 `rational_copper` + 1 `runtime_polyfit`; `NbTi (Cri/oFlex 3)` `runtime_polyfit` with `coeffs=null` excluded and given no coefficients) — it is provenance context, not new measurement or re-fit, and its `valid_range_K` fields are `null` wherever the SSOT records no range; `提昇論文品質.md` stale/unverified; TS ljg-paper validator unavailable in this environment; missing `streamlit/matplotlib/altair/plotly/scipy/openpyxl` for some interactive/runtime visuals; actual *Cryogenics* submission formatting/APC/scope must be checked externally; `.tex`/`.zh.tex` not templated to current journal class; ZH LaTeX (xeCJK/CJK fonts) compilation unverified; 溫區擬合同源 viz snapshot/demo (Task 5: viz_data/json/html/xlsx generator) not yet produced—compiled platform demonstrates fitting via sediment doc + inline SVG + doc-listed examples (degraded, evidence-bounded).
