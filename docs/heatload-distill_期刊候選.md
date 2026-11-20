# Heatload-Distill 可投稿期刊候選與投稿目標（投稿前須再查核）

> 對象：涵蓋「熱負載研究流程」之流程/案例稿——**citation/溯源、材料資料庫（SSOT 54 筆）、模擬計算（κ(T)/∫κdT 與多溫區熱負載）、9 個參數（c0..c8 推導與物理意義/矩陣與病態）、distill 與可靠度驗證**（見 `docs/heatload-distill_paper.{md,tex}`、`docs/9coeff_4step_flow.json`、`docs/polyfit_可靠度驗證.md` 與 ljg-paper Org note）。  
> 篩選/精煉日期：2026-11-19（依公開 aims & scope/網頁資訊之初步判讀與本次 web 檢索摘要）。2026-11-19 更新：**Cryogenics (Elsevier)** 為本稿請求投稿目標；已納入 Smith et al. (2024, *IEEE Trans. Appl. Supercond.* 34(2), doi:10.1109/TASC.2024.3350516, arXiv:2306.13574) 作為已驗證之低溫互連文獻 κ(T)+幾何熱負載估算動機脈絡（僅引用已驗證內容，不重算第三方數據）。  
> **重要**：投稿前必須逐項查核 *Cryogenics* **當期** aims & scope、author guidelines、article type、字數/圖表/格式模板、審查政策、APC/open access 選項與版面政策、資料/程式碼可得性、匿名審查與倫理要求。本清單不保證錄取，且不構成對 scope、錄取或政策之最終判定。

## 0. 本稿框架與目標期刊
| 項目 | 說明 |
|---|---|
| **請求目標** | **Cryogenics (Elsevier)** — 低溫工程/熱建模方法與可追溯性主軸（見 §1） |
| **稿件框架** | 低溫熱建模/熱管理方法稿（review + reliability-aware workflow），非新量測物性、非重擬合係數 |
| **主張重心（需有證據支撐）** | SSOT 溯源降低 κ(T) 係數誤用風險；擬合區間積分在已驗證擾動下相對穩定、深低溫外推/係數敏感；病態與條件數解讀需脈絡；NbTi Tc 結構殘差與 runtime_polyfit 不可視為固定係數；連結稀釋冷凍機/量子互連熱預算估算之可追溯性（含 Smith et al. 2024 之文獻式熱負載估算脈絡） |
| **投稿前必查** | 最新 scope/guidelines、article type、字數/圖表/模板、APC/OA、資料與倫理要求、同儕審查與匿名政策 |

**投稿門檻（誠實揭露）**：不得宣稱新量測物性或重擬合係數；須明示 SSOT（D4=A）、54 筆/53 固定係數、`NbTi (Cri/oFlex 3)` 為 `runtime_polyfit` 且 `coeffs=null`、條件數依實作/定義/來源/範圍/縮放而異、深低溫外推（如 k@20 mK）僅量級示意、擬合區間 ∫κdT 在測試擾動下相對穩定（條件性）、Kapton 係數流程敏感性、Tc 區結構殘差、環境相依缺失（streamlit/matplotlib/altair/plotly/scipy/openpyxl 等）導致互動/視覺降級或未驗證項目。Smith et al. 僅作已驗證動機/脈絡引用，本稿不重算或獨立驗證其數值。

## 1. 低溫工程 / 熱建模主軸（目標與備選）
| 候選期刊 | 出版/型態 | 適配理由（與本流程對應） | 投稿前注意事項與不確定性 |
|---|---|---|---|
| **Cryogenics** (Elsevier) — **請求目標** | 國際低溫工程期刊；訂閱+Open Access 選項 | 公開 aims/scope 涵蓋低溫工程、熱流體/熱傳、低溫材料與熱/電等性質、量測技術，以及與超導/低溫電子、量子計算相關之低溫技術等。與「κ(T) 擬合係數之可追溯使用、熱導積分/多溫區熱負載估算、材料性質資料可靠度與外推風險」直接相關；Smith et al. (2024) 顯示低溫互連之文獻 κ(T)+幾何權重熱負載估算為實務需求，與本稿可追溯/可靠度邊界主張相呼應。可將本工作定位為**可追溯熱負載建模與可靠度揭露之方法/工程實務稿**（而非新材料數據）。 | **投稿前必查**當期 scope/guidelines、article type、novelty/impact 期待、字數/圖表/模板、資料可得性與倫理要求、APC/OA 與版面政策。宜強化對實際熱預算決策的量化影響與可重用性（避免超出既有證據），並依期刊格式同步 `paper.tex`。 |
| **EPJ Quantum Technology** (Springer Nature, Open Access) | 量子技術 OA 期刊；Research/Comment/Review 等型態（依官網） | 聚焦量子科學與技術；領域內已有低溫/微波高密度訊號熱建模等與稀釋冷凍機熱負載相關工作（如 Raicu et al. 2025, EPJ QT 12:124，亦為本案溯源之一）。若稿件明確連結**量子處理器低溫佈線/互連與熱預算建模的溯源與可靠度驗證流程**，情境契合。 | 必須扣緊量子技術/低溫系統應用語境，否則可能被視為一般資料整理或內部流程。OA APC、版權與資料可得性要求以投稿時官網為準。 |
| **Journal of Low Temperature Physics** (Springer Nature) | 低溫物理期刊 | 傳統涵蓋低溫物性與熱現象；近期亦見低溫微波元件熱行為等應用相關研究。適合強調 κ(T) 擬合/係數詮釋、矩陣/病態與外推 vs 擬合區間積分之物理-數值討論（若以學術分析角度重寫）。 | 需確認當期 aims & scope 對「流程蒸餾/工程可追溯性」稿件之接受度與所需學術增量；純流程文件化恐不足。版面費/APC/格式依當期指南。**適配度待定稿主軸後再核**。 |
| **IOP Conference Series: Materials Science and Engineering** 或相關低溫工程會議論文集 | 會議論文（依會議/審查） | 若短期目標為交流「可追溯熱負載計算流程/教學與工程實務」而非期刊新穎性，會議管道可能較務實。 | 非等同期刊論文之影響/索引保證；需符合會議主題與投稿時程。列為**備選發表管道**，非首選期刊。 |

### 條件性/較不建議（低溫主軸）
| 候選 | 理由 | 建議 |
|---|---|---|
| **IEEE Transactions on Applied Superconductivity (TAS)** | 應用超導範圍廣，但稿件若缺乏直接超導器件/材料/系統之新實驗或設計貢獻，且偏量子低溫封裝流程，可能與 scope 邊界緊張。 | 僅在改寫為明確的**應用超導/超導互連熱管理**且具對應證據時考慮；投稿前務必對照最新 scope 或詢編輯。 |
| **Scientific Data (Nature Portfolio)** 等 data descriptor 期刊 | 本案核心為既有來源係數之整合/驗證與流程蒸餾，非新產生可獨立重用之一手量測資料集。 | 一般不建議，除非另行產出並釋出具明確貢獻的新資料集。 |

## 2. 可重現工作流 / 研究軟體主軸（需先開源封裝與歸檔）
| 候選期刊 | 出版/型態 | 適配理由（與本流程對應） | 投稿前注意事項與不確定性 |
|---|---|---|---|
| **Journal of Open Research Software (JORS)** (Ubiquity Press, Open Access) | Software Metapaper / Issues in Research Software 等 | 適合具重用潛力之研究軟體/可重現工作流描述。若將 SSOT 驅動之 4-step 同源產生器、快照/HTML/Excel/Streamlit 展示、可靠度驗證腳本與文件規格封裝為**公開可得、可保存、可引用**之軟體/工作流，可投稿 metapaper 類型。 | **先決條件**：公開儲存庫、OSI 相容授權、可執行文件、版本歸檔（建議 DOI，如 Zenodo/機構庫）、軟體引用資訊；目前產物多為本機/專案內路徑，未達投稿門檻。APC/費率與文章型態以投稿時官網與期刊頁為準（本次未取得可確證之固定金額，勿自行填寫）。 |
| **SoftwareX** (Elsevier, Open Access) | Original Software Publication | 鼓勵具科學影響之研究軟體簡短發表。適合將 distill/viz/驗證工具鏈整理為可重用套件並強調對低溫熱負載建模工作之支撐。 | 同樣需公開程式碼、文件、可執行性與存檔；審查重點在軟體品質與重用價值而非領域新物性結論。APC/模板依當期指南查核。 |

## 3. 推薦順序（依當前請求與證據成熟度）
- **使用者請求目標 / 首選**：**Cryogenics**（低溫工程/熱性質與熱負載可追溯性主軸；投稿前依當期 scope/guidelines/APC/article type 格式化與查核）。
- **備選（需調整主軸/語境）**：**EPJ Quantum Technology**（若明確嵌入量子低溫互連/稀釋冷凍機熱預算情境並扣緊期刊受眾）；**Journal of Low Temperature Physics**（強化物理-數值分析與結論邊界；適配待核）。
- **需先完成開源封裝與歸檔**：**JORS** 或 **SoftwareX**（工作流/軟體主軸，非目前稿件主形態）。
- **條件性/備選**：TAS（範圍匹配時）、低溫工程相關會議（交流取向）。

## 4. 投稿前查核清單（務必逐項完成）
1. 以投稿當日官網確認：aims & scope、article type、字數/格式模板、同儕審查政策、APC/版面費與減免。
2. 準備可公開產物策略：版本標記、儲存庫/存檔 DOI、授權、環境與相依、降級行為說明、重現步驟。
3. 對齊主張與證據：僅使用 SSOT/同源快照/既有驗證支持之陳述；保留所有限制與不確定性（不重擬合/不編造、NbTi runtime_polyfit+coeffs=null、條件數脈絡、外推不可靠、Tc 結構殘差、係數流程敏感性、執行期未驗證項）。
4. 語言與版式：以 `heatload-distill_paper.md`/`.tex` 為基礎依 **Cryogenics** 當期模板與指南改寫（article type、結構、參考文獻格式、圖表、資料可得性聲明等）；必要時補圖表與資料可得性聲明，並保留已驗證引用（含 Smith et al. 2024）與所有限制揭露。
5. 利益衝突/致謝/資料來源聲明依期刊要求完整填寫。
