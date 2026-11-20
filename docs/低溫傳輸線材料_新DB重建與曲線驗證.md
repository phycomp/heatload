# 低溫傳輸線材料資料庫重建與曲線驗證（NIST 官網）— 科學成果沉澱

> **技能：** `sci-sediment`（四區塊骨架）＋ `sci-concept-valid`（可驗證性判準）＋ `web-search`（NIST 官網查證）＋ `arxiv-search`（材料組成文獻）
> **日期：** 2026-11-20
> **範圍：** 低溫傳輸線材料（SC 同軸 / FLAX / Cri-oFlex 3 / NbTi-polyimide / 不鏽鋼-NbTi 同軸）
> **邊界：** 另建新 DB、不碰 SSOT（heatload-coff-nist D4=A）；不重擬合、不編造、不宣稱新量測；NIST 官網僅供 a-i 係數、無原始量測點；超範圍不外推。

---

## 1. 模型假設（Model Assumptions）

### 1.1 系統與範圍
- **對象**：低溫傳輸線的組成材料導熱模型 — 導體/屏蔽（OFHC Cu、不鏽鋼、BeCu、Brass、Invar）、介電質（PTFE、Polyimide/Kapton）。
- **資料源**：NIST TRC 低溫材料性質官網 `https://trc.nist.gov/cryogenics/materials/materialproperties.htm`（2026-11-20 抓取），逐材料頁面 a–i 係數與 data/equation range、fit error。
- **不納入**：C7150 / Ag-coated C7150 / PFA / NbTi 無 NIST 官網條目（屬文獻來源：Raicu Table 4/6、Delft Cri-oFlex 3），仍引用 SSOT 既有條目，不重建。

### 1.2 控制方程（與 SSOT 同一物理模型）
- **log-log 9 參數（大部分材料）**：$\log_{10}\kappa(T)=\sum_{n=0}^{8} c_n(\log_{10}T)^n$，$\kappa$ in W/(m·K)，$T$ in K。
- **rational 形式（OFHC Cu RRR 變體）**：$\log_{10}\kappa=\frac{a+c\sqrt T+eT+gT^{1.5}+iT^2}{1+b\sqrt T+dT+fT^{1.5}+hT^2}$。
- **Wiedemann–Franz 交叉**（僅正常態金屬低溫彈性散射；介電/超導態不適用，見 §4）。

### 1.3 假設與邊界
- **有效範圍**：係數僅在頁面標示 `data range`／`equation range` 內有效；8 階 log-log 多項式超範圍外推會發散（本次已排除 293 K 對 Brass 5–116 K 的外推）。
- **製程敏感**：聚合物（PTFE/PFA/Kapton）κ 對結晶度/密度/取向敏感（Zhou 2019, arXiv:1909.07607v1），單一 a-i 曲線為「該批次擬合」，非普世常數。
- **不重擬合**：NIST 官網僅提供 a-i 擬合係數（無 raw 量測點），故本次做「曲線比對/對帳」，非重新 least-squares 擬合。

---

## 2. 驗證過程（Verification Process）

### 2.1 抓取（web-search / requests + UA）
- 索引頁 43 連結 → 成功抓 42 材料頁；7 筆解析失敗（Apiezon N/Be/In/Sapphire/Si/Glass-mat/Regenerator：無熱導表或 404）如實記 `errors`。
- 抓取器 `/tmp/opencode/nist_scrape.py`：解析 Thermal Conductivity 表（過濾 Specific Heat/Expansion），存 `docs/nist_material_db_scraped.json`（含 source URL、抓取時間、原始 a-i、range、fit error）。

### 2.2 範圍縮小（傳輸線材料映射）
- 材料組成依已查證文獻：SC-086 coax = C7150/Ag-C7150/PTFE（Raicu 2025 `arXiv:2502.01945v3`）；FLAX = Nb47Ti+PFA（Smith 2020/2024）；Cri-oFlex 3 = NbTi+Kapton；不鏽鋼/NbTi coax（Krinner 2019 `arXiv:1806.07862v1`）。
- 選出 9 筆 NIST 材料並映射元件角色 → `docs/nist_transmission_line_materials.json`。

### 2.3 曲線比對（同模型、共同有效範圍內）
- 比對器 `/tmp/opencode/curve_compare.py`：對 8 筆非-Cu 材料，取新 DB 與 SSOT **共同有效範圍**內的對數間距溫度點，用同一 $\kappa(T)$ 公式評估，逐值對帳 + 係數簽章比對揪出錯位。
- 產出 `docs/nist_transmission_line_curve_compare.json`（comparisons + 13 misassignment_flags + errors）。

### 2.4 過程限制（誠實揭露）
- 7 材料抓取失敗（頁面無熱導表/404）→ 未納入，不猜值。
- Brass/BeCu 等 range 較窄 → 已排除超範圍取樣（如 Brass 293 K）。
- OFHC Cu 為 rational 形式 → 單獨處理，不納入 log-log 對帳。
- 無 raw 量測點 → 不能重新擬合，只做係數/曲線對帳。

---

## 3. 驗證結論（Verification Conclusion）

### 3.1 逐命題分級
| 命題 | 分級 | 證據 |
|---|---|---|
| 新 DB 抓取忠實再現 NIST 官網 a-i（42 材料） | **已支持（本機+官網）** | 抓取 JSON 含 URL/日期/原始係數；Brass 等抽驗與官網逐值一致 |
| 4 筆 SSOT 與官網 exact match（Kapton、SS304/304L/316） | **已支持** | 係數逐值 1e-6 內相同，κ 曲線差 0% |
| **Teflon 錯位鏈**：Nylon←Teflon、Mylar←Nylon、Raicu-PTFE←Teflon | **已支持（本機硬證據）** | 三筆 SSOT 係數簽章分别等於 NIST Teflon/Nylon/Teflon；官網 Nylon a0=-2.6135、Teflon a0=2.738 |
| SSOT `Teflon (PTFE)` 偏離官網 +357.6%（293 K）、Brass +986%（77 K）、Invar +742% | **已支持（範圍內）** | 均為低階/理想化擬合（c5–c8=0 等）vs 官網完整 9 階，且在共同有效範圍內 |
| 聚合物 κ 製程敏感，單一值非普世常數 | **文獻支持（已驗證）** | Zhou 2019 `arXiv:1909.07607v1`、Drobizhev 2016 `arXiv:1612.02514v2` |
| 低溫聲子 κ 冪次對缺陷/邊界敏感 | **文獻支持（已驗證）** | van Ostaay 2018 `arXiv:1805.02019v1` |

### 3.2 整體結論（證據有界）
- **SSOT 的 NIST 54 筆在攝取時使用「低階/通用擬合」**（多筆 c5–c8=0），與 NIST 官網現在的完整 9 階係數**不一致**；對傳輸線工程做量級估算尚可，做材料特定精確比較不可靠。
- **確認三筆係數錯位**（Nylon/Mylar/Raicu-PTFE）——這是比上一輪「疑誤植」更強的硬判定。
- **4 筆 exact match**（Kapton/SS304 系）顯示 SSOT 並非全錯，錯在「低階擬合＋錯位」兩類。
- **不主張**：不宣稱任何 NIST 材料「正確值」優於 SSOT 的適用性結論（取決於具體電纜批次/製程）、不重擬合、不宣稱新量測、不捏造書目。

### 3.3 適用與失效邊界
- **可用**：新 DB 做 κ(T) 量級估算、材料間相對比較、錯位稽核；SSOT 做既有 heatload 計算（D4=A 邊界不變）。
- **需謹慎**：具體電纜的導體/介電必須用該電纜文獻值（Raicu C7150/PTFE、FLAX Nb47Ti/PFA、Cri-oFlex NbTi/Kapton），不能用通用 NIST 值替代。
- **失效**：超範圍外推、把低階理想化係數當高精度常數、把錯位後的 Nylon/Mylar 值當材料物性。

---

## 4. 計算/擬合/模擬圖表（Charts & Tables）

### 4.1 產物清單與角色
| 產物 | 角色 | `value_origin` | 狀態 |
|---|---|---|---|
| `docs/nist_material_db_scraped.json` | 全量抓取（42 材料 + errors） | `nist_official_coeffs_scraped` | 已產出 |
| `docs/nist_transmission_line_materials.json` | 9 筆傳輸線材料子集 + 元件映射 | `nist_official_coeffs_scraped` | 已產出 |
| `docs/nist_transmission_line_curve_compare.json` | 曲線對帳 + 13 錯位旗標 | `ssot_vs_nist_in_range` | 已產出 |
| `docs/低溫傳輸線_新DB曲線對照.svg` | 4 面板 κ(T) 對照（實線 NIST/虛線 SSOT，僅範圍內） | `ssot_vs_nist_in_range`，標 EXACT/MISMATCH | 已產出 |

### 4.2 曲線對照（共同有效範圍內，雙對數）
- **Panel A Teflon**：SSOT 低階擬合 κ(293K)=0.0596 vs NIST 官網 0.2726（+357.6%）→ MISMATCH。
- **Panel B SS304**：兩者逐值一致 → EXACT MATCH。
- **Panel C Kapton**：兩者一致 → EXACT MATCH。
- **Panel D Brass**：SSOT c5–c8=0 低階擬合 κ(77K)=3.66 vs NIST 完整 9 階 39.8（+986%，77K 在 5–116 K 範圍內，非外推）→ MISMATCH。
- 圖例/軸/單位/範圍見 SVG 內標註；未偽造外推曲線。

### 4.3 對照表（範圍內代表點）
| 材料 | 共同範圍 | κ(T) new vs SSOT | exact | 註記 |
|---|---|---|---|---|
| Polyimide (Kapton) | 4–300 K | 0.1907 vs 0.1907 (293K) | 是 | — |
| Stainless Steel 304/304L/316 | 4–300 K | 15.12 vs 15.12 (293K) | 是 | 三筆共用 |
| Teflon | 4–300 K | 0.2726 vs 0.0596 (293K) | 否 | +357.6% |
| Brass | 5–116 K | 39.8 vs 3.66 (77K) | 否 | +986%，SSOT 低階擬合 |
| Invar | 4–300 K | 13.76 vs 1.63 (293K) | 否 | +742% |

### 4.4 降級與標註
- 抓取失敗 7 材料：記 `errors`，未納入、未猜值。
- 超範圍取樣（Brass 293K、BeCu 150/293K）：已排除，不畫外推。
- OFHC Cu rational 5 RRR 變體：單獨存，不納入 log-log 對帳。
- 文獻來源材料（C7150/PFA/NbTi）：無 NIST 頁，引用 SSOT，不重建。

---

## 5. 產物索引與同源追蹤
- 抓取器：`/tmp/opencode/nist_scrape.py`（暫存，未進 repo）
- 子集生成器：`/tmp/opencode/build_transmission_line_db.py`
- 比對器：`/tmp/opencode/curve_compare.py`；繪圖：`/tmp/opencode/make_curve_svg.py`
- 資料：`docs/nist_material_db_scraped.json`、`docs/nist_transmission_line_materials.json`、`docs/nist_transmission_line_curve_compare.json`
- 圖表：`docs/低溫傳輸線_新DB曲線對照.svg`
- 前序：`docs/係數資料庫_自洽卻不可信_概念驗證.md`、`docs/核實_原始資料與係數驗證.md`、`docs/polyfit_可靠度驗證.json`
- 文獻：`arXiv:1612.02514v2`、`arXiv:1909.07607v1`、`arXiv:1805.02019v1`、`arXiv:2502.01945v3`、`arXiv:2306.13574v2`、`arXiv:1806.07862v1`
- SSOT（`~/.opencode/skills/heatload-coff-nist/scripts/{coeff_data,thermal_load}.py`）：**未修改**

*（本文件依 `sci-sediment` 四區塊沉澱；所有結論受 §1 假設、§3 邊界與 §4 降級約束。）*
