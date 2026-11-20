# DOC-003 PCB 傳輸線逆工程：合成公式推導與疊構映射

> **文件編號**: DOC-003-Synthesis-Derivations  
> **層級**: Level 1（準靜態合成模型，DOC-002 之逆問題）  
> **日期**: 2026-10-15  
> **狀態**: Phase A 首期交付（🟢🟡 章節推導完備；🟠🔴 方法定案，完整級數展開留待次期）  
> **配套程式庫**: `tl_synthesis.py`（Phase B，本文所有驗證數據由其產生）

## 0. 專案定義（決策樹共識定稿）

| 決策節點 | 定案 |
|---|---------|
| 交付物 | A 文件 → B Python 庫 → C Streamlit 工具 |
| 逆工程定義 | DOC-002 之外的可解析式／漸進式物理推導 |
| 截面範圍 | 最大範圍：傳輸線 9 項＋元件級 ≥4 項 |
| 疊構範圍 | Rigid＋HDI＋Flex-Rigid 全部（本期完成 Rigid，HDI/Flex-Rigid 見 §III.4） |
| 逆解方法學 | 🟢🟡 解析反函數；🟠 修正因子併入反演；🔴 牛頓迭代＋收斂資訊 |
| 驗證基準 | Mantaro 同源 ±1%；跨族／文獻 ±5%；三步驗證（反解→代回→第三方比對） |

## Part I — 反演方法論

### I.1 問題表述
- DOC-002 解正問題：幾何 **g** → 阻抗 Z₀ = F(**g**)。本文件解逆問題：給定目標 Z* 與固定參數 **c**（疊構決定），求 F(**g**; **c**) = Z*。
- 阻抗對幾何的依賴在本層級全部為**嚴格單調**（∂Z₀/∂w < 0，∂Z₀/∂h > 0），故解存在且唯一，反演合法。

### I.2 三級反演方法（對應 Q4 分級）
- **🟢🟡 級 — 解析反函數。** 本族公式皆為 $Z₀ = A(c) · ln[ B(c) / (.8w + t) ]$ 之形（A、B 與 w 無關）。對 w 解出： $w = ( B / e^{Z_*/A} − t ) / .8$ 一步反演，無迭代誤差，殘差僅含浮點捨入（驗證表實測 $<10^{-13}%$）。
- **🟠 級 — 修正因子併入反演。** 非對稱／寬邊／差分公式形如 $Z₀ = A · χ(c) · ln[B/(.8w+t)]$,  $χ ⊥ w χ$ 與待解變數 w 無關，故可**解析地**併入指數： $w = ( B / e^{Z^*/(A·χ)} − t ) / .8$
- 物理意義：修正因子改變的是「有效激勵強度」，不改變反演結構。此為本期對 🟠 級採用的方法；Lagrange 級數反轉的完整誤差界推導列為次期工作（見 §II.8 待辦）。
- **🔴 級 — 牛頓迭代。** 保角映射族的 Z₀ 是 w 的複合超越函數（tanh → 橢圓積分比），無閉式反函數。採 $w(n+1) = w(n) − (F(w(n)) − Z^*) / F'(w(n))$ （F' 以中心差分數值計，步長 $h_x = max(10^{-10}, 10^{-6}·|w(n)|)$）。收斂資訊隨解回報（迭代數、殘差）。實測：CPW 與差分帶狀線均 6 次迭代收斂至 $< 10^{-8}Ω$，與 DOC-002 §6.1 正向基準點吻合至 $10^{-13}%$。初始值選取：CPW 取 s₀ = w（k ≈ 1/3，遠離 k→1 的病態區）；差分帶狀線取 w₀ = b/4。

## Part II — 各截面合成推導

### II.1 Microstrip　🟢　[Mantaro 同源]

- 正向（IPC-2141A）$Z₀ = 87/\sqrt{εᵣ+1.41} · ln[ 5.98h / (.8w + t) ]$
- **推導**：令 $A = 87/\sqrt{εᵣ+1.41}$，則 $e^{Z^*/A} = 5.98h/(.8w+t)$，解出 $w = 7.48h / e^{Z*/A} − 1.25t = ( 5.98h / e^{Z*/A} − t ) / .8$
- 末式即 Mantaro 頁面所刊反函數，本文件給出完整推導鏈。適用域 $.1 ≤ w/h ≤ 3.$（反解後須回檢）。傳播延遲$T_{pd} = \sqrt{.475·εᵣ + .67}·3.333 ns/m$

### II.2 Stripline　🟢　[Mantaro 同源]
- 正向 $Z₀ = 60/\sqrt{εᵣ} · ln[1.9(2h+t) / (.8w+t)]$        （h = 走線到平面距離）
- **推導** 同 II.1 結構，$w = 1.9(2h+t) / e^{Z*·\sqrt{εᵣ/60} − t } / .8$
- 適用域$.1 ≤ w/h ≤ 2.、t/h < .25$。純 TEM $ε_{eff} = εᵣ$（DOC-002 §1.2），反解無$ε_{eff}$耦合問題——這是 Stripline 反演比 Microstrip 更乾淨的物理原因。

### II.3 Embedded Microstrip　🟡　[Mantaro 同源]

- 正向 $Z₀ = 60/\sqrt{ε_{eff}} · ln[5.98h / (.8w+t) ]$ 暨$ε_{eff} = εᵣ·(1 − e^{−1.55·h₁/h})$                   （適用$h₁/h ≥ 1.2$）
- **推導**：ε_eff 與 w 無關（上覆介質高度 h₁ 是疊構參數），直接沿用 II.1 結構$A = 60/\sqrt{ε_{eff}}$暨$w = ( 5.98h / e^{Z*/A} − t ) / .8$
- **物理註記**：極限 h₁→∞ 時$ε_{eff}→εᵣ$退回 II.2 結構（係數 60↔87/1.9 差異來自場形不同），漸進一致性成立。

### II.4 Asymmetric Stripline　🟠　[Mantaro 同源]
- 正向（h = 較薄側, h₁ = 較厚側） $Z₀ = 80/\sqrt{εᵣ} · ln[1.9(2h+t)/(.8w+t)] · (1 − h/4h₁)$
- **推導（修正因子併入法）**：$χ = 1 − h/(4h₁) ⊥ w$，由 I.2： $w = ( 1.9(2h+t) / e^{Z*·\sqrt{εᵣ}/80/χ} − t ) / .8$
- 物理詮釋：非對稱使場向薄側偏移，等效激勵降為 χ 倍；反演時把目標「放大」1/χ 即可。**一致性檢驗**：對稱極限 h₁→h 時$χ = 3/4 \quad 80χ = 60$，精確退回 II.2——通過。

### II.5 Broadside Coupled Stripline　🟠　[Mantaro 同源]
- 正向（h = 外側介質, h₁ = 中心介質）$Z₀ = 80/\sqrt{εᵣ} · ln[1.9(2h+t)/(.8w+t)] · (1 − h/4(h+h₁+t))$
- **推導**：$χ = 1 − h/4(h+h₁+t)$，同 II.4 併入法。極限 h₁→0 時$χ → 1 − h/4(2h+t)$，退化檢驗以數值驗證通過（殘差 < $10^{-13}$）。

### II.6 Differential Microstrip　🟡　[Mantaro 同源]

- 正向（d = 兩線間距）：$Zd = 174/\sqrt{εᵣ+1.41} · ln[5.98h/(.8w+t)] · (1 − 0.48·e^{−.96·d/h})$
- **推導（w 反解）**：$κ(d) = 1 − .48·e^{−.96d/h} ⊥ w， w = ( 5.98h / e^{ Z*·\sqrt{εᵣ+1.41} /174/κ } − t ) / .8$
- **推導（d 反解，From-Z₀ 版）**：由 Mantaro $Zd = 2Z₀·(1 − 0.48·e^{−.96d/h})$，對 d 解出指數函數的純代數反演：$d = −h/.96 · ln[1 − Z*/2/Z₀]$
- **定義域**：Z* < 2Z₀（否則無實數解，物理上即「此單端阻抗下間距再大都達不到該差分阻抗」）。邊界 Z*→2Z₀⁻ 時 d→∞，與「間距無限大 = 無耦合 = Zd = 2Z₀」一致。閉式解存在且唯一。

### II.7 Differential Stripline　🟡　[IPC 閉式]／🔴　[保角映射精確解]

- **IPC 閉式**： $Zd = 120/\sqrt{εᵣ} · ln[1.9(2h+t)/(.8w+t)] · (1 − 0.347·e^{−2.9d/(2h+t)})$ 反解同 II.6 結構（κ 定義不同）。
- **保角映射族（DOC-002 §4.5）**： $kₒ = \tanh{πw/2b} / \tanh{π(w+s)/2b}$ \quad $Z_{diff} = (120/\sqrt{εᵣ}) · K(kₒ')/K(kₒ)$
- w 同時出現在分子分母的 tanh 內，無閉式反函數 → 🔴 牛頓迭代（I.2 末段）。驗證：對 DOC-002 §6.1 基準（$w=.1, s=.1, b=.2 → 57.95Ω$）反解得 $w = .1000 mm$，6 次迭代收斂。

### II.8 CPW　🔴　[DOC2 保角映射族]
- 正向（DOC-002 §3.3–3.4）： $Z₀ = 30π/\sqrt{ε_{eff}} · K(k')/K(k) \quad  k = s/(s+2w)$
- k 經 Hilberg 近似後仍為 s 的超越函數，且$ε_{eff}$亦隨 s 變化（填充因子 q 含 k₁(s)）→ 雙重耦合，純牛頓。驗證：對 DOC-002 §6.1 基準（$s=.5, w=.3, h=1.6 → 78.33Ω$）反解得$s = .5001 mm$。**極限錨點**：h→∞ 時$ε_{eff}→(εᵣ+1)/2$可解析檢驗；w→∞ 時 k→0、Z₀→∞；迭代域避開 k→1（w→0 病態），初始值 s₀ = w 使 k₀ = 1/3，安全。
- **次期待辦（🟠/🔴 完整化）**：(1) II.4/II.5 的 Lagrange 級數反轉誤差界；(2) CPW 牛頓法的收斂域證明（Kantorovich 條件顯式檢驗）；(3) 厚度修正項 Δw(t) 與反解的聯立（目前 t 視為疊構固定參數）。

### II.9 元件級
- **Coax　🟢**： $Z₀ = 60/\sqrt{εᵣμᵣ} · ln[dₒ/dᵢ]$ → $dᵢ = dₒ·e^{−Z*·\sqrt{εᵣμᵣ}/60}$  （或反解 dₒ） 純 TEM 閉式，無適用域限制（dᵢ < dₒ 由定義域保證）。
- **Parallel Wire　🟢**： $Z₀ = 120/\sqrt{εᵣ} · acosh(s/d)$ → $s = d · \cosh{ Z*·\sqrt{εᵣ} / 120 }$
- 本文件唯一用到反雙曲函數族的反演 定義域 s > d 由 cosh ≥ 1 自動保證：$T{pd} = \sqrt{εᵣ}·3.333$ns/m。
- **Plane Impedance　🟢**：平行板 $L = μ₀μᵣ·h/w  (H/m) \quad  C = ε₀εᵣ·w/h  (F/m) \quad  Z_{plate} = η₀·h/w/\sqrt{εᵣ}   （適用 w ≫ h）$
- 「反解」依目標量而定：給定目標 L 反 $h = L·w/μ₀/μᵣ$；給定目標 $Z_{plate}$ 反 w。PDN 應用中 L 與迴路面積的線性關係使此反解為嚴格線性問題。
- **Pad Capacitance　🟡**（Mantaro 半經驗式，矩形焊盤含邊緣場，幾何 mm → pF）： $C = 8.854·εᵣ·(w−h)(l−h)/h + 26.4·(εᵣ+1.41)·(w+l) / ln[5.98h /(.8h+t) ]$
- 對 w 或 l 反解時，第一項為二次、第二項為線性分式，可化為單變數多項式求根（🟡 邊界）；本期以數值求根實作，解析化列次期。

## Part III — 疊構映射（Polar 模板 → 截面公式）

### III.1 映射規則（本文件的核心知識產出）

| 疊構情境 | 走線層 | 適用截面 | 物理依據 |
|---|---|---|---|
| Foil build 外層 | L1/Ln | Embedded Microstrip（上覆 solder mask＋prepreg） | 外層非裸空氣，$ε_{eff}$由 II.3 給出；本期簡化用 Microstrip（保守高估 ~2–4%） |
| Core build 外層 | L1/Ln | Microstrip（純） | 外層僅 solder mask 薄層 |
| 內層，兩側完整平面 | 任一內層 | Stripline | 純 TEM（II.2） |
| 內層，平面間距不等 | 依 h<h₁ 側 | Asymmetric Stripline | 場向薄側偏移（II.4） |
| HDI 微盲孔層 | L1–L2 等 | Embedded Microstrip＋適用域警示 | 介質極薄（~57µm），h₁/h 條件常不滿足 → 降級 🔴 |
| Flex 區段 | — | 模型提案等級（見 III.4） | 無 Mantaro/文獻基準 |

### III.2 Polar 6L foil build 完整映射範例

疊構序列（Polar 模板圖，總厚 1557.34µm）：

    Cu L1 | PP1651×2 | Cu L2(平面) | Core 400 | Cu L3
          | PP(1080/106/1080) | Cu L4 | Core 400 | Cu L5(平面) | PP1651×2 | Cu L6

| 訊號層 | 平面配置 | 截面 | h（µm） | 50Ω 線寬（驗證表） | Tpd (ns/m) |
|---|---|---|---|---|---|
| L1 | L2 平面 | Microstrip | 262 | 見附錄 A | 5.49 |
| L3 | L2/L4 | Stripline | 316.5（半間距） | 見附錄 A | 6.83 |
| L4 | L2/L4 | Stripline | 316.5 | 見附錄 A | 6.83 |
| L6 | L5 平面 | Microstrip | 262 | 見附錄 A | 5.49 |

### III.3 製造變異敏感度（風險對策：製造漂移）

- 對 Microstrip 閉式（II.1），偏導數有閉式：$∂Z₀/∂h = A/h,  ∂Z₀/∂εᵣ = −Z₀/2/(εᵣ+1.41),  ∂Z₀/∂w = −.8·A/(.8w+t)$
- 範例（50Ω 設計點，FR4）：介質厚度 +10% → Z₀ 約 +4.2%；εᵣ +.2 → Z₀ 約 −1.5%；線寬蝕刻 −10% → Z₀ 約 +3%。Stripline 由 II.2 同法推得（無 ε_eff 耦合，更穩健——高速設計偏愛內層的定量理由之一）。

### III.4 HDI / Flex-Rigid 狀態（Q3 範圍，本期方法定案）
- **HDI**：10L 3/4 press cycle 的盲孔區介質（~57µm）使 II.3 適用域 h₁/h ≥ 1.2 經常失效。方法定案：盲孔區**禁用閉式逆解**，降級為 🔴 迭代＋場解器標定；非盲孔區維持 II.2。
- **Flex-Rigid**：剛（FR4, εᵣ≈4.2）撓（PI, εᵣ≈3.2–3.4）交界阻抗不連續的漸進模型列為**模型提案**等級：以「雙區段各自套用 II.2／II.1＋交界處一階阻抗階躍 ΔZ ≈ Z₀·(εᵣ,FR4−εᵣ,PI)/(2εᵣ)」為零階近似，無第三方基準，置信度標註為低，待 Polar Speedstack 場解器比對後升級。

## 附錄 A — 數值驗證表（反解 → 正算代回 → 殘差）

| 案例 | 等級 | 公式族 | 目標 (Ω) | 代回 (Ω) | 殘差 (%) | 迭代數 |
|---|---|---|---|---|---|---|
| Microstrip 50Ω | 🟢 | IPC | 50.00 | 50.000 | 0.0e+00 | — |
| Stripline 50Ω | 🟢 | IPC | 50.00 | 50.000 | 0.0e+00 | — |
| Embedded Microstrip 50Ω | 🟡 | IPC | 50.00 | 50.000 | 0.0e+00 | — |
| Asymmetric Stripline 50Ω | 🟠 | IPC | 50.00 | 50.000 | 0.0e+00 | — |
| Broadside Stripline 50Ω | 🟠 | IPC | 50.00 | 50.000 | 0.0e+00 | — |
| Diff Microstrip Zd=100Ω | 🟡 | IPC | 100.00 | 100.000 | 0.0e+00 | — |
| Diff Stripline Zd=100Ω | 🟡 | IPC | 100.00 | 100.000 | 0.0e+00 | — |
| Coax 50Ω (do=3mm) | 🟢 | 解析 | 50.00 | 50.000 | 0.0e+00 | — |
| Parallel Wire 120Ω (d=1mm) | 🟢 | 解析 | 120.00 | 120.000 | 1.2e-14 | — |
| CPW 78.33Ω (s反解) | 🔴 | DOC2 | 78.33 | 78.330 | 3.6e-14 | 6 |
| Diff Stripline(保角) Zd=57.95Ω | 🔴 | DOC2 | 57.95 | 57.950 | 2.5e-14 | 6 |
| 6L_foil L1 50Ω | 🟢 | Stackup | 50.00 | 50.000 | 0.0e+00 | — |
| 6L_foil L3 50Ω | 🟢 | Stackup | 50.00 | 50.000 | 0.0e+00 | — |
| 6L_foil L4 50Ω | 🟢 | Stackup | 50.00 | 50.000 | 0.0e+00 | — |
| 6L_foil L6 50Ω | 🟢 | Stackup | 50.00 | 50.000 | 0.0e+00 | — |
| 6L_foil L3 Zd=100Ω | 🟡 | Stackup | 100.00 | 100.000 | 1.4e-14 | — |

**跨族獨立比對**（Q5 分級基準第二級）：IPC 反解 w = 3.022 mm（h = 1.6, εᵣ = 4.2, 50Ω）以 DOC-002 Hammerstad-Jensen 正向重算得 51.67Ω，偏差 **3.35%**，在 ±5% 容差內。兩公式族系統性差異的來源（IPC-2141A 為早期簡化式，HJ 含填充因子修正）已在 DOC-002 文獻表分類。

**驗收狀態**：全部 16 點通過；🟢🟡 級殘差 ≤ 1e-13 %（浮點極限）；🔴 級 6 次迭代收斂，與 DOC-002 §6.1 正向基準點重疊驗證（CPW 78.33Ω、Diff Stripline 57.95Ω）。

## 附錄 B — 與 Mantaro 計算器對照索引

| Mantaro 計算器 | 本文章節 | 庫函數 |
|---|---|---|
| Microstrip / From Zo | II.1 | `microstrip_z0/w` |
| Embedded Microstrip | II.3 | `embedded_microstrip_z0/w` |
| Stripline | II.2 | `stripline_z0/w` |
| Differential Microstrip / From Zo | II.6 | `diff_microstrip_zd/w/d` |
| Differential Stripline / From Zo | II.7 | `diff_stripline_zd/w` |
| Asymmetric Stripline | II.4 | `asymmetric_stripline_z0/w` |
| Broadside Coupled Stripline | II.5 | `broadside_stripline_z0/w` |
| Coaxial Line | II.9 | `coax_z0/di/do` |
| Parallel Wire | II.9 | `parallel_wire_z0/s` |
| Plane Impedance | II.9 | `plane_lc` |
| Rectangular Pad Capacitance | II.9 | `pad_capacitance` |
| CPW（Mantaro 無） | II.8 | `cpw_z0/cpw_solve_s` |

## 參考文獻

1. IPC-2141A (2004). *Controlled Impedance Circuit Boards and High Speed Logic Design.*
2. Mantaro Impedance Calculators — https://www.mantaro.com/resources/impedance-calculators.php
3. Polar Speedstack Templates — https://www.polarinstruments.com/support/stackup/templates.html
4. 承接 DOC-002 參考文獻 1–9（Wheeler, Hammerstad-Jensen, Wadell, Wen, Cohn 等）。
