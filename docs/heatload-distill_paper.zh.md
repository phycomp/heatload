# 基於溯源之 9 係數低溫熱導率擬合於熱負載估算的應用：回顧與可靠度感知工作流

> **文件類型：** 以既有來源、SSOT 資料庫紀錄、同源產物與可靠度驗證輸出為基礎，針對 *Cryogenics* (Elsevier) 準備之回顧/方法稿（草稿）。  
> **格式：** Markdown（本檔）。LaTeX 對應稿維護於 `docs/heatload-distill_paper.zh.tex`（與英文版章節、邏輯、內文、圖表/表格保持高度一致）；投稿前應與英文稿同步並依期刊當期要求模板化。期刊與投稿說明：`docs/heatload-distill_期刊候選.md`。  
> **日期：** 2026-11-19（同源快照 `docs/9coeff_4step_flow.json`，`generated_at`: `2026-11-19T10:48:13`，`errors: 0`）。  
> **範圍聲明：** 本稿**不**重擬合或發明係數，**不**宣稱新的材料物性量測，亦**不**引入超出已引用/已驗證專案證據之結論。所有量化陳述均對應既有 SSOT/溯源紀錄與驗證產物，並明確說明限制與不確定性。投稿適配性、文章型態、格式、APC/開放取用、資料/倫理政策等必須於投稿前依期刊當期指南查核。

## 摘要
低溫工程中的熱預算評估——包括稀釋冷凍機系統中支撐件與互連線的傳導熱——通常仰賴材料熱導率 κ(T) 的擬合表示式，尤其是 9 係數 log-log 多項式（c0..c8 / a..i）以及針對特定材料之來源特定有理式/RRR 形式[^nist][^marquardt][^bradley][^simon1992][^flynn][^raicu2025]。近期高密度超導佈線研究凸顯了其實務影響：Smith *et al.* 結合文獻熱導率值與電纜截面，估算 1 英呎長柔性 Nb–47 wt% Ti 同軸帶狀電纜由 1 K 至 100 mK 每條跡線之傳導熱負載為 5 nW，並與商用同軸與 NbTi-on-polyimide 撓性線選項進行比較[^smith2024]。此類 nW 等級估算直接取決於所使用的 κ(T) 資料與擬合、其有效溫度範圍，以及外推處理方式。

本文提出 **Heatload-Distill**：一套用於低溫熱負載估算中 9 係數 κ(T) 擬合之、以溯源為基礎且具可靠度感知的回顧與工作流程。該流程將實務組織為四個可追溯步驟：(1) 文獻與材料資料庫溯源、(2) 9 參數與熱負載方程式之物理/模型詮釋、(3) 矩陣/最小平方法求解與數值條件性、(4) polyfit 可靠度驗證。其以單一真實來源（SSOT，決策 D4=A）與同源產物（`topic-viz` Format F：規格 + 快照 + 離線 HTML/Excel，具降級與錯誤揭露）為依據。

依據 `docs/9coeff_4step_flow.json` 與相關產物，我們回顧 54 筆資料庫條目（48 `log_polynomial`、5 `rational_copper`、1 `runtime_polyfit`）以及 53 筆固定係數材料用於數值係數–材料關係；`NbTi (Cri/oFlex 3)` 為 `runtime_polyfit` 且 `coeffs=null`，排除於固定係數數值關係之外。既有驗證證據（合成 log-log 三次樣條產生器、8 階 `np.polyfit`、T=2–300 K、N=50 對數間距點、擾動研究）顯示，擬合區間內積分熱導率（∫₂³⁰⁰ κ dT）在測試擾動下相對穩定，而深低溫外推（例如 κ 在 20 mK）對擾動及擬合/流程選擇高度敏感，僅應視為量級指標。證據亦顯示原始冪次基底之強病態、全域 8 階擬合下 NbTi Tc 附近之材料特定結構殘差，以及儲存係數與驗證擬合 Kapton 係數間之巨大差異（max |Δc|≈79.48）。本文不重擬合或發明係數，亦不宣稱新的材料物性量測。我們結論：可信的低溫熱負載估算應建立於可追溯溯源、明確有效範圍、具條件性感知之詮釋與不確定性揭露，而非孤立之外推值或未記錄係數。

**關鍵詞：** 低溫工程、低溫熱導率、9 係數擬合、熱負載估算、稀釋冷凍機、溯源、數值條件性、polyfit 可靠度、回顧

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

## 可得性
- **規格與同源產物：** `docs/9coeff_4step_視覺化規格.md`、`docs/9coeff_4step_flow.json`、`docs/9coeff_4step_demo.html`、`docs/9coeff_4step_demo.xlsx`
- **可靠度驗證：** `docs/polyfit_可靠度驗證.md`、`docs/polyfit_可靠度驗證.json`
- **整合文件：** `docs/NIST9熱負載整合說明.md`、`docs/NIST9_視覺化規格.md`
- **SSOT 與溯源：** `~/.opencode/skills/heatload-coff-nist/scripts/{coeff_data,thermal_load}.py`、`~/.opencode/skills/heatload-coff-nist/references/citations.md`
- **產生/顯示腳本：** `scripts/9coeff_4step_viz.py`、`scripts/9coeff_4step_streamlit_demo.py`、`scripts/validate_polyfit_reliability.py`
- **期刊候選與投稿說明：** `docs/heatload-distill_期刊候選.md`

## 參考文獻
[^raicu2025]: Raicu, N., Hogan, T., Wu, X., Vahidpour, M., Snow, D., Hollister, M., & Field, M. (2025). *Cryogenic thermal modeling of microwave high density signaling*. EPJ Quantum Technology, 12:124. https://doi.org/10.1140/epjqt/s40507-025-00427-1 (Dataset: https://doi.org/10.5281/zenodo.15238913)
[^nist]: NIST Cryogenics Index of Material Properties. https://trc.nist.gov/cryogenics/materials/materialproperties.htm
[^marquardt]: Marquardt, E. D., Le, J. P., & Radebaugh, R. (2000). *Cryogenic Material Properties Database*. 11th International Cryocooler Conference.（書目細節依專案引用紀錄。）
[^bradley]: Bradley, P. E., et al. (2006). *Cryogenic Material Properties Database, Update 2006*. ICEC 21.（書目細節依專案引用紀錄。）
[^simon1992]: Simon, N. J., Drexler, E. S., & Reed, R. P. (1992). *Properties of Copper and Copper Alloys at Cryogenic Temperatures*. NIST Monograph 177. NIST.
[^flynn]: Flynn, T. M. *Cryogenic Engineering*.（版本/出版社細節於專案引用中未完全指定。）
[^smith2024]: Smith, J. P., Mazin, B. A., Boaventura, A., Thompson, K. J., & Daal, M. (2024). *Improved Flexible Coaxial Ribbon Cable for High-Density Superconducting Arrays*. IEEE Transactions on Applied Superconductivity, 34(2), 1–6. https://doi.org/10.1109/TASC.2024.3350516 (arXiv:2306.13574, https://arxiv.org/abs/2306.13574)
