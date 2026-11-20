# 溫區擬合 物理模型 — arXiv 文獻檢索與證據有界驗證報告

> **執行任務：** Task 7（Subsystem C：執行 `arxiv-search` 並彙整相關推論）  
> **檢索日期：** 2026-11-20  
> **檢索工具：** `python3 ~/.agents/skills/arxiv-search/arxiv_search.py`（Python 套件 `arxiv` 4.1.0，連線至 arXiv API 實時查詢 + 輔助 `arxiv.Client` 取得對應命中之 arXiv ID / 作者 / 日期 / DOI / 期刊 metadata）  
> **驗證對象：** `docs/溫區擬合_物理模型_來源萃取.md`、`docs/heatload-distill_paper.md` / `docs/heatload-distill_paper.zh.md`（Section 3.2）及 `docs/溫區擬合_物理模型_viz_spec.md` 所定義之「溫區擬合（Temperature-Zone Fitting / Stage-Wise Physical Calculation）」物理模型。  
> **全域約束（證據有界）：** 嚴格區分「**arXiv / 已驗證書目 metadata 支持**」與「**教科書標準物理 / 專案內部推導脈絡**」；不杜撰任何未經工具輸出或既有專案紀錄查核之引文、DOI 或實驗數據；嚴守 SSOT 決策 **D4=A**（54 筆材料中 53 筆固定係數，`NbTi (Cri/oFlex 3)` 為 `runtime_polyfit` 且 `coeffs=null`）。

---

## 查詢

本節完整記錄依計畫（Step 1）執行之 3 組必跑 CLI 查詢（Q1–Q3），以及為釐清 arXiv Lucene 括號語法影響與補強稀釋冷凍機分溫階熱錨/柔性傳輸線熱化文獻所執行之 3 組針對性追蹤查詢（Q4–Q6）。

### 1.1 查詢參數與命令總表

| 查詢編號 | 類型 | 執行命令 | 排序 (`--sort`) | 上限 (`--max-papers`) | 執行狀態與命中特徵 |
|---|---|---|---|---:|---|
| **Q1** | 計畫指定必跑 (Step 1.1) | `python3 ~/.agents/skills/arxiv-search/arxiv_search.py "cryogenic cable thermal load conduction integral kappa(T) dilution refrigerator stages" --max-papers 8 --sort relevance` | `relevance` | 8 | HTTP 200 成功返回 8 筆；因字串含括號 `kappa(T)` 觸發 arXiv API 預設布林/括號分組退化，返回高能物理大型合作組通用文獻（已於 Q4 移除括號重查對照）。 |
| **Q2** | 計畫指定必跑 (Step 1.2) | `python3 ~/.agents/skills/arxiv-search/arxiv_search.py "Wiedemann-Franz law low temperature thermal conductivity cryogenic interconnect" --max-papers 8 --sort relevance` | `relevance` | 8 | HTTP 200 成功返回 8 筆；直接命中低溫/極低溫 Wiedemann–Franz 定律有效性、超導體雜質散射、金屬奈米薄膜尺寸效應與電聲子解耦偽影文獻。 |
| **Q3** | 計畫指定必跑 (Step 1.3) | `python3 ~/.agents/skills/arxiv-search/arxiv_search.py "Raicu cryogenic thermal modeling microwave high density signaling coaxial cable" --max-papers 5 --sort relevance` | `relevance` | 5 | HTTP 200 成功返回 5 筆；精準命中 **Raicu et al. (2025)**（`arXiv:2502.01945v3`）、**Smith et al. (2020)**（`arXiv:2007.06496v1`）與 **Smith et al. (2023/2024)**（`arXiv:2306.13574v2`）。 |
| **Q4** | 語法對照追蹤（移除 Q1 括號 `kappa(T)`） | `python3 ~/.agents/skills/arxiv-search/arxiv_search.py "cryogenic cable thermal load conduction dilution refrigerator" --max-papers 8 --sort relevance` | `relevance` | 8 | HTTP 200 成功返回 8 筆；移除括號後恢復低溫領域精準度，命中 **Raicu et al. (2025)**（第 8 筆）、稀釋冷凍機毫克耳文微波功率熱轉移量測（`arXiv:2607.12751v1`）與 10 mK 熱耦合/高熱導隔振文獻。 |
| **Q5** | 針對性追蹤（百量子比特分溫階熱預算基準） | `python3 ~/.agents/skills/arxiv-search/arxiv_search.py "Engineering cryogenic setups for 100-qubit scale superconducting circuit systems" --max-papers 3 --sort relevance` | `relevance` | 3 | HTTP 200 成功返回 3 筆；首筆命中 **Krinner et al. (2019)**（`arXiv:1806.07862v1`, *EPJ Quantum Technology* 6, 2），為超導量子電腦稀釋冷凍機分溫階被動導熱與主動耗散熱預算之經典基準。 |
| **Q6** | 針對性追蹤（柔性微波排線與極低溫量子比特熱化） | `python3 ~/.agents/skills/arxiv-search/arxiv_search.py "flexible superconducting microwave cable thermal load dilution refrigerator" --max-papers 5 --sort relevance` | `relevance` | 5 | HTTP 200 成功返回 5 筆；命中 **Smith et al. (2020)**（`arXiv:2007.06496v1`）與 **Paluch et al. (2024)**（`arXiv:2410.01053v1`，以超導量子比特實測含分級衰減器之柔性微波帶狀線熱化與殘餘熱光子數）。 |

---

### 1.2 各組查詢命中結果與原始摘要節錄

#### (A) Q1 查詢結果（`2026-11-20` 實時輸出）
- **Query:** `"cryogenic cable thermal load conduction integral kappa(T) dilution refrigerator stages"` (`--max-papers 8 --sort relevance`)
- **檢索診斷說明：** arXiv Legacy API 將未加引號之括號子句 `kappa(T)` 解析為欄位/布林群組運算，導致相關性排序退化為帶 `(T)` 符號之高能物理文獻。茲據實記錄前 8 筆返回標題與 ID，並由 Q4（移除 `integral kappa(T)` 與 `stages`）完成無括號對照：
  1. `arXiv:1406.6311v4` (2014-06-24) — *The Physics of the B Factories* (A. J. Bevan et al., *Eur. Phys. J. C* 74 (2014) 3026, DOI: `10.1140/epjc/s10052-014-3026-9`)
  2. `arXiv:0901.0512v4` (2008-12-28) — *Expected Performance of the ATLAS Experiment - Detector, Trigger and Physics* (The ATLAS Collaboration)
  3. `arXiv:1610.08142v2` (2016-10-26) — *Measurement of forward $t\overline{t}$, $W+b\overline{b}$ and $W+c\overline{c}$ production in $pp$ collisions at $\sqrt{s}=8$ TeV* (LHCb collaboration, *Phys. Lett. B* 767 (2017) 110)
  4. `arXiv:1411.4413v2` (2014-11-17) — *Observation of the rare $B^0_s\to\mu^+\mu^-$ decay from the combined analysis of CMS and LHCb data* (CMS & LHCb Collaborations, *Nature* 522, 68–72 (2015))
  5. `arXiv:2601.07595v3` (2026-01-12) — *Deep Search for Joint Sources of Gravitational Waves and High-Energy Neutrinos with IceCube During the Third Observing Run of LIGO and Virgo* (IceCube Collaboration)
  6. `arXiv:2402.01568v3` (2024-02-02) — *Doping Liquid Argon with Xenon in ProtoDUNE Single-Phase: Effects on Scintillation Light* (DUNE Collaboration, *JINST* 19 P08005 (2024))
  7. `arXiv:2509.18817v2` (2025-09-23) — *Measurement of the $W \to \mu\nu_\mu$ cross-sections as a function of the muon transverse momentum in $pp$ collisions at 5.02 TeV* (LHCb collaboration, *JHEP* 03 (2026) 148)
  8. `arXiv:1710.05839v2` (2017-10-16) — *Search for High-energy Neutrinos from Binary Neutron Star Merger GW170817 with ANTARES, IceCube, and the Pierre Auger Observatory* (A. Albert et al.)

#### (B) Q2 查詢結果（`2026-11-20` 實時輸出）
- **Query:** `"Wiedemann-Franz law low temperature thermal conductivity cryogenic interconnect"` (`--max-papers 8 --sort relevance`)
- **命中清單與關鍵摘要節錄：**
  1. **`arXiv:2503.13968v1`** (2025-03-18) — *Comment on Unusual violation of the Wiedemann-Franz law at ultralow temperatures in topological compensated semimetals*
     - **Authors:** Kamran Behnia, Shiyan Li, Johnpierre Paglione, Louis Taillefer
     - **DOI / Journal:** `None` (arXiv preprint, `cond-mat.str-el`)
     - **Summary snippet:** *"Recently, Wang et al. [1] reported on an unusual violation of Wiedemann-Franz law in three semimetals. We compare their observations to our observations in a variety of systems, where the apparent WF law violations in the same temperature range arise as a consequence of electron-phonon decoupling. Given the empirical similarity of their data with these cases, the most plausible explanation for the reported violation is an experimental artefact."*
  2. **`arXiv:2309.01062v1`** (2023-09-03) — *Validation of the Wiedemann-Franz Law in solid and molten tungsten above 2000 K through thermal conductivity measurements via steady state temperature differential radiometry*
     - **Authors:** Milena Milich, Hunter B. Schonfeld, Konstantinos Boboridis, Davide Robba, Luka Vlahovic, Rudy Konings et al.
     - **Summary snippet:** *"We demonstrate that the thermal conductivity can be well described by application of Wiedemann-Franz Law to electrical resistivity data, thus suggesting the validity of Wiedemann-Franz Law to capture the electronic thermal conductivity of metals..."*
  3. **`arXiv:cond-mat/9509046v1`** (1995-09-08) — *Electronic thermal conductivity and the Wiedemann-Franz law for unconventional superconductors*
     - **Authors:** M. J. Graf, S.-K. Yip, J. A. Sauls, D. Rainer
     - **DOI / Journal:** `10.1103/PhysRevB.53.15147` | *Phys. Rev. B* 53 (1996) 15147
     - **Summary snippet:** *"We use the quasiclassical theory of superconductivity to calculate the electronic contribution to the thermal conductivity. The theory is formulated for low temperatures when heat transport is limited by electron scattering from random defects... For intermediate temperatures the Lorenz ratio deviates significantly from $L_S$, and is strongly dependent on the scattering cross section..."*
  4. **`arXiv:cond-mat/0607634v1`** (2006-07-25) — *Electronic thermal conductivity at high temperatures: Violation of the Wiedemann-Franz law in narrow band metals*
     - **Authors:** K. Vafayi, M. Calandra, O. Gunnarsson
     - **DOI / Journal:** `10.1103/PhysRevB.74.235116`
  5. **`arXiv:2412.01546v1`** (2024-12-02) — *Violation of the Wiedemann-Franz law and ultra-low thermal conductivity of Ti$_3$C$_2$T$_x$ MXene*
     - **Authors:** Yubin Huang, Jean Spiece, Tetiana Parker, Asaph Lee, Yury Gogotsi, Pascal Gehring
     - **DOI / Journal:** `10.1021/acsnano.4c08189` | *ACS Nano* 2024, 18, 47, 32491–32497
  6. **`arXiv:2306.04545v2`** (2023-06-07) — *Gravito-thermal transports, Onsager reciprocal relation and gravitational Wiedemann-Franz law*
     - **Authors:** Xin Hao, Song Liu, Liu Zhao (`10.1016/j.nuclphysb.2024.116497`, *Nucl. Phys. B* 1001 (2024) 116497)
  7. **`arXiv:2011.07707v1`** (2020-11-16) — *First-principles based analysis of thermal transport in metallic nanostructures: size effect and Wiedemann-Franz law*
     - **Authors:** Yue Hu, Shouhang Li, Hua Bao
     - **DOI / Journal:** `10.1103/PhysRevB.103.104301` | *Phys. Rev. B* 103, 104301 (2021)
     - **Summary snippet:** *"It is found that when the size of nanostructures is on the order of several tens of nanometers, the electronic/phonon thermal conductivity is smaller than the bulk value and decreases with size... By assuming that the grain boundary does not induce inelastic electron-phonon scattering, the Wiedemann-Franz law works well in both Au and W nanostructures if the Lorentz ratio is estimated using electronic thermal conductivity."*
  8. **`arXiv:cond-mat/0608143v2`** (2006-08-06) — *Thermal conductivity of Al-doped MgB2: Impurity scattering and the validity of the Wiedemann-Franz law*
     - **Authors:** A. V. Sologubenko, N. D. Zhigadlo, J. Karpinski, H. R. Ott
     - **DOI / Journal:** `10.1103/PhysRevB.74.184523` | *Phys. Rev. B* 74, 184523 (2006)
     - **Summary snippet:** *"We report data on the thermal conductivity K(T,H)... at temperatures between 0.5 and 50 K and in external magnetic fields between 0 and 70 kOe. The substitution of Al for Mg leads to a substantial reduction of the heat transport via electronic quasiparticles... confirms the validity of the Wiedemann-Franz law for both pure and doped MgB2 [in the normal/impurity-dominated limit]."*

#### (C) Q3 查詢結果（`2026-11-20` 實時輸出）
- **Query:** `"Raicu cryogenic thermal modeling microwave high density signaling coaxial cable"` (`--max-papers 5 --sort relevance`)
- **命中清單與關鍵摘要節錄：**
  1. **`arXiv:2502.01945v3`** (2025-02-04, updated 2025-12-12) — *Cryogenic Thermal Modeling of Microwave High Density Signaling*
     - **Authors:** Naomi Raicu, Tom Hogan, Xian Wu, Mehrnoosh Vahidpour, David Snow, Matthew Hollister, Mark Field
     - **DOI / Journal:** `10.1140/epjqt/s40507-025-00427-1` | *EPJ Quantum Technol.* 12, 124 (2025)（專案 citations 另載 Zenodo dataset DOI: `10.5281/zenodo.15238913`）
     - **Summary snippet:** *"Superconducting quantum computers require microwave control lines running from room temperature to the mixing chamber of a dilution refrigerator. Adding more lines without preliminary thermal modeling to make predictions risks overwhelming the cooling power at each thermal stage. In this paper, we investigate the thermal load of SC-086/50-SCN-CN semi-rigid coaxial cable... experimentally measure the total thermal conductivity of a single cable as a function of the temperature from cryogenic to room temperature values. We also measure the cryogenic DC electrical resistance of the inner conductor as a function of temperature, allowing for the calculation of active thermal loads due to Ohmic heating. Fitting this data produces a numerical thermal conductivity function used to calculate the static heat loads due to thermal transfer within the wires resulting from a temperature gradient. The resistivity data is used to calculate active heat loads, and we use these fits in a cryogenic model of a superconducting quantum processor in a typical Bluefors XLD1000-SL dilution refrigerator..."*
  2. **`arXiv:2007.06496v1`** (2020-07-13) — *Flexible Coaxial Ribbon Cable for High-Density Superconducting Microwave Device Arrays*
     - **Authors:** Jennifer Pearl Smith, Benjamin A. Mazin, Alex B. Walter, Miguel Daal, J. I. Bailey, Clinton Bockstiegel, Nicholas Zobrist, Noah Swimmer, Sarah Steiger, Neelay Fruitwala
     - **DOI / Journal:** `10.1109/TASC.2020.3008591` | (*IEEE Trans. Appl. Supercond.*)
     - **Summary snippet:** *"Superconducting electronics often require high-density microwave interconnects capable of transporting signals between temperature stages with minimal loss, cross talk, and heat conduction. We report the design and fabrication of superconducting 53 wt% Nb-47 wt% Ti (Nb47Ti) FLexible coAXial ribbon cables (FLAX)... We estimate the heat load from 1 K to 90 mK to be 20 nW per trace, approximately half the computed load from the smallest commercially available superconducting coax from CryoCoax"*
  3. `arXiv:1312.3555v1` (2013-12-12) — *Prospects of Turbulence Studies in High-Energy Density Laser-Generated Plasma: Numerical Investigations in Two Dimensions* (T. Handy et al., 無關高能量密度電漿模擬)
  4. `arXiv:physics/0702198v1` (2007-02-23) — *Writhing Dynamics of Cables with Self-contact* (S. Goyal et al., 無關海底電纜力學)
  5. **`arXiv:2306.13574v2`** (2023-06-23, updated 2023-06-29) — *Improved Flexible Coaxial Ribbon Cable for High-Density Superconducting Arrays*
     - **Authors:** Jennifer Pearl Smith, Benjamin A. Mazin, Alirio Boaventura, Kyle J. Thompson, Miguel Daal
     - **DOI / Journal:** arXiv 欄位為 `None`；專案已驗證出版紀錄（`docs/heatload-distill_paper.md` `[^smith2024]`）為 *IEEE Transactions on Applied Superconductivity*, 34(2), 1–6 (2024), DOI: `10.1109/TASC.2024.3350516`
     - **Summary snippet:** *"Superconducting arrays often require specialized, high-density cryogenic cabling capable of transporting electrical signals across temperature stages with minimal loss, crosstalk, and thermal conductivity. We report improvements to the design and fabrication of previously published superconducting 53 wt% Nb-47 wt% Ti (Nb47Ti) FLexible coAXial ribbon cables (FLAX)... We increased the center conductor diameter from 0.003 inches to 0.005 inches which lowered the cable characteristic impedance from $\sim 60\ \Omega$ to $\sim 53\ \Omega$. This change had a negligible impact on the computed heat load which we estimate to be 5 nW per trace from 1 K to 100 mK with a 1-ft cable. This is approximately half the heat load calculated for the smallest commercially available superconducting coax... We compare key performance metrics with commercially available superconducting coax and NbTi-on-polyimide flex cables..."*

#### (D) Q4–Q6 針對性追蹤查詢關鍵命中（`2026-11-20` 實時輸出）
- **Q4（移除 `kappa(T)` 括號後之低溫傳導查詢）：**
  - 第 8 筆再次命中 **Raicu et al. (2025)** `arXiv:2502.01945v3`；
  - 第 4 筆命中 **`arXiv:2607.12751v1`** (2026-07-14, Paolo Panetta et al., *Traceable In Situ Microwave Power Measurement at the Cryogenic Device Plane in a Dilution Refrigerator*)：探討稀釋冷凍機內分散式衰減、阻抗失配與溫變微波元件下，利用可變溫階（VTS）與 20 dB 穿通衰減器之穩態溫度與熱暫態進行毫克耳文平面微波功率與直流電功率（AC/DC 替代）量測；
  - 第 1、2 筆命中 **`arXiv:1809.07162v1`** (D. Schmoranzer et al., *Thermal coupling of silicon oscillators in cryogen-free dilution refrigerators*, DOI: `10.1007/s10909-018-02122-1`) 與 **`arXiv:1810.06847v1`** (M. de Wit et al., *Vibration isolation with high thermal conductance for a cryogen-free dilution refrigerator*, *Rev. Sci. Instrum.* 90, 015112 (2019), DOI: `10.1063/1.5066618`)，記錄無液氦稀釋冷凍機在 10 mK 基溫與 100 mK 製冷功率（如 $113\ \mu\text{W}$ at 100 mK）下之熱耦合與輻射屏蔽敏感度。
- **Q5（百量子比特稀釋冷凍機分溫階熱錨與被動/主動熱負載基準）：**
  - 首筆命中 **`arXiv:1806.07862v1`** (2018-06-20) — *Engineering cryogenic setups for 100-qubit scale superconducting circuit systems*
    - **Authors:** Sebastian Krinner, Simon Storz, Philipp Kurpiers, Paul Magnard, Johannes Heinsoo, Raphael Keller, Janis Luetolf, Christopher Eichler, Andreas Wallraff
    - **DOI / Journal:** `10.1140/epjqt/s40507-019-0072-0` | *EPJ Quantum Technology* 6, 2 (2019)
    - **Summary snippet:** *"Here, we engineer an extensible cryogenic setup, which minimizes passive and active heat loads, while guaranteeing rapid qubit control and readout... The passive heat load of stainless steel and NbTi coaxial cables and the active load due to signal dissipation are measured, validating our robust and extensible concept for thermal anchoring of attenuators, cables, and other microwave components. Our results are important for managing the heat budget of future large-scale quantum computers based on superconducting circuits."*
- **Q6（柔性微波帶狀線在稀釋冷凍機中之分級衰減熱化與量子比特有效溫度）：**
  - 第 5 筆命中 **`arXiv:2410.01053v1`** (2024-10-01) — *Thermalization of a flexible microwave stripline measured by a superconducting qubit*
    - **Authors:** Patrick Paluch, Martin Spiecker, Nicolas Gosling, Viktor Adam, Jakob Kammhuber, Kiefer Vermeulen, Daniël Bouman, Wolfgang Wernsdorfer, Ioan M. Pop
    - **DOI / Journal:** `None` (arXiv preprint, `quant-ph`)
    - **Summary snippet:** *"With the demand for scalable cryogenic microwave circuitry continuously rising, recently developed flexible microwave striplines offer the tantalyzing perspective of increasing the cabling density by an order of magnitude without thermally overloading the cryostat. We use a superconducting quantum circuit to test the thermalization of input flex cables with integrated $60\,$dB of attenuation distributed at various temperature stages. From the measured decoherence rate of a superconducting fluxonium qubit, we estimate a residual population of the readout resonator below $3.5\cdot10^{-3}$ photons and we measure a $0.28\,$ms thermalization time for the flexible stripline attenuators. Furthermore, we confirm that the qubit reaches an effective temperature of $26.4\,$mK, close to the base temperature of the cryostat..."*

---

## 相關文獻與推論

為嚴守證據有界原則，下表將本次檢索獲得之 **arXiv 已驗證文獻** 與專案既有 **SSOT 上游資料庫 / 教科書參考** 並列，明確標示每項文獻之驗證層級與可推論範圍：

### 2.1 已驗證文獻與專案模型對照總表

| 文獻識別 / 作者年份 | 標題與出版資訊（僅列已驗證 metadata） | 證據類別 | 核心方法與數據摘要（依 arXiv 摘要 / 專案已核對紀錄） | 對「溫區擬合」物理模型之推論意義 |
|---|---|---|---|---|
| **Raicu et al. (2025)**<br>`arXiv:2502.01945v3`<br>DOI: `10.1140/epjqt/s40507-025-00427-1` | *Cryogenic Thermal Modeling of Microwave High Density Signaling*, *EPJ Quantum Technol.* 12, 124 (2025)（Dataset: `10.5281/zenodo.15238913`） | **arXiv 實時命中 + 專案 SSOT 上游文獻** | 量測 SC-086/50-SCN-CN 半剛性同軸線低溫至室溫熱導率 $\kappa(T)$ 與內導體直流電阻率 $\rho(T)$；以 9 參數 log-log 多項式擬合 $\kappa(T)$（Table 4）與 $\rho(T)$（Table 6，$T<3.8\text{ K}$ 取常數 $9.928\times 10^{-9}\ \Omega\cdot\text{m}$），計算稀釋冷凍機（Bluefors XLD1000-SL）各溫階之靜態溫差傳導熱負載（static heat load）與主動歐姆耗散熱負載（active heat load），評估 100–225 qubits 擴展上限。 | 直接支持本模型將熱負載拆為**分溫階靜態傅立葉導熱積分** $Q_{\text{solid}}=\sum_i (A/L_i)\int \kappa(T)\,dT$ 與**主動耗散項**（直流歐姆熱 $I^2 R$ / 射頻衰減 $Q_{\text{rf}}$），且證實低溫金屬在殘餘散射區（如 $T<3.8\text{ K}$）以常數電阻率 $\rho\approx\rho_0$ 搭配 Wiedemann–Franz 關係作交叉建模之實務合理性。 |
| **Smith et al. (2023/2024)**<br>`arXiv:2306.13574v2`<br>DOI: `10.1109/TASC.2024.3350516` | *Improved Flexible Coaxial Ribbon Cable for High-Density Superconducting Arrays*, *IEEE Trans. Appl. Supercond.* 34(2), 1–6 (2024) | **arXiv 實時命中 + 專案已驗證期刊引用** | 設計 53 wt% Nb–47 wt% Ti（Nb47Ti）柔性同軸帶狀排線（FLAX）；估算 1-ft（$\approx 30.5\text{ cm}$）排線在 $1\text{ K}\to 100\text{ mK}$ 溫階之傳導熱負載為 **$5\text{ nW/trace}$**（約為最小商用超導同軸線之一半），並將微波損耗與商業 NbTi-on-polyimide 柔性排線對比。 | 支持在 $1\text{ K}\to 100\text{ mK}$ 極低溫區以各層材料截面積 $A_k$、線長 $L$ 與熱導率積分估算 nW 級每通道被動導熱負載（與專案 CF3 對標脈絡中 $350\text{ mK}\to 10\text{ mK}$ 之 $\sim 20\text{ nW/ch}$ 處於同一物理量級與建模框架）。 |
| **Smith et al. (2020)**<br>`arXiv:2007.06496v1`<br>DOI: `10.1109/TASC.2020.3008591` | *Flexible Coaxial Ribbon Cable for High-Density Superconducting Microwave Device Arrays*, *IEEE Trans. Appl. Supercond.* (2020) | **arXiv 實時命中** | 10 通道 Nb47Ti + PFA 介電質柔性同軸帶狀線（長 $30\text{ cm}$），計算 $1\text{ K}\to 90\text{ mK}$ 溫階每通道熱負載約 **$20\text{ nW/trace}$**，串音較舊型壓合 NbTi-on-Kapton 微帶線降低 $30\text{ dB}$。 | 提供複合超導導體（Nb47Ti）與高分子介電質（PFA / Kapton）多層排線在 $L=30\text{ cm}$、$1\text{ K}\to 90\text{ mK}$ 下之被動導熱基準（$20\text{ nW/trace}$），印證複合截面必須同時考量超導金屬與聚合物基材之導熱貢獻。 |
| **Krinner et al. (2019)**<br>`arXiv:1806.07862v1`<br>DOI: `10.1140/epjqt/s40507-019-0072-0` | *Engineering cryogenic setups for 100-qubit scale superconducting circuit systems*, *EPJ Quantum Technology* 6, 2 (2019) | **arXiv 實時命中** | 建立百量子比特級稀釋冷凍機之驅動線、磁通線與讀取線設計準則；量測不鏽鋼與 NbTi 同軸線之**被動傳導熱負載**與訊號耗散之**主動熱負載**，確立在各溫階對衰減器、電纜與微波元件進行**分級熱錨（thermal anchoring）**之標準架構。 | 強力支持分溫階熱預算（stage-wise heat budgeting）架構；同時從反面證實：實務上保護毫克耳文量子比特免受熱光子退相干，必須仰賴**各溫階熱錨與分級衰減器熱化**，而非單靠拉長一段未錨定（unanchored）懸空傳輸線。 |
| **Paluch et al. (2024)**<br>`arXiv:2410.01053v1` | *Thermalization of a flexible microwave stripline measured by a superconducting qubit* (2024 preprint) | **arXiv 實時命中** | 以超導 Fluxonium 量子比特退相干率實測配備 $60\text{ dB}$ **分溫階整合衰減器（integrated attenuation distributed at various temperature stages）**之柔性微波帶狀線熱化表現：讀取諧振器殘餘熱光子數 $<3.5\times 10^{-3}$，量子比特有效溫度達 $26.4\text{ mK}$（接近冷凍機基溫）。 | 直接對應本模型第 4 層（`M5_mk_qubit_safe_length`）：證實柔性微波排線在 mK 溫區與量子比特耦合時，控制殘餘熱光子數（$n_{\text{th}} \ll 0.01$）與有效溫度（$26.4\text{ mK} < T_{\text{crit}}\approx 57.6\text{ mK}$）的物理機制是**分溫階分佈式衰減器與熱錨熱化**，而非假設常數 $\kappa$ 的無熱錨線性溫度梯度回推。 |
| **Hu, Li & Bao (2021)**<br>`arXiv:2011.07707v1`<br>DOI: `10.1103/PhysRevB.103.104301` | *First-principles based analysis of thermal transport in metallic nanostructures: size effect and Wiedemann-Franz law*, *Phys. Rev. B* 103, 104301 (2021) | **arXiv 實時命中** | 結合第一原理與玻爾茲曼傳輸方程分析 Au / W 金屬奈米薄膜與奈米線：當特徵尺寸降至數十奈米（或薄膜受表面/晶界散射限制）時，電子與聲子熱導率均**顯著低於塊材（bulk）並隨尺寸減小而下降**；若晶界不引發非彈性電聲散射，以電子熱導估算之 Wiedemann–Franz 定律仍成立。 | 支持本模型對微米/次微米薄層導體（如 FPC $0.2\ \mu\text{m}$ 或 CF3 $2\ \mu\text{m}$ 訊號層與薄膜鍍層）之限制聲明：**薄膜尺寸與邊界散射會改變有效導熱與電阻率**，不可將未修正之塊材熱導率或異構幾何直接等同代換。 |
| **Sologubenko et al. (2006)**<br>`arXiv:cond-mat/0608143v2`<br>DOI: `10.1103/PhysRevB.74.184523`<br>& **Graf et al. (1996)**<br>`arXiv:cond-mat/9509046v1`<br>DOI: `10.1103/PhysRevB.53.15147` | *Thermal conductivity of Al-doped MgB2: Impurity scattering and the validity of the Wiedemann-Franz law*, *Phys. Rev. B* 74, 184523 (2006)；*Electronic thermal conductivity and the WF law for unconventional superconductors*, *Phys. Rev. B* 53, 15147 (1996) | **arXiv 實時命中** | 探討 $0.5\text{–}50\text{ K}$ 超導體與摻雜雜質散射對準粒子熱傳導之抑制，以及低溫缺陷彈性散射極限與中間溫度區 Lorenz 比對 Sommerfeld 值 $L_S=(\pi^2/3)(k_B/e)^2$ 之偏離。 | 支持本模型 `M3_wf_const_rho` 之適用邊界：Wiedemann–Franz 定律與 Sommerfeld 常數 $L_0\approx 2.44\times 10^{-8}\ \text{W}\Omega/\text{K}^2$ 僅在**正常態金屬低溫彈性雜質散射極限**成立；進入超導態（$T<T_c$ 庫柏對凝聚）或非彈性散射區時必須改用對應之超導/聲子熱導模型。 |
| **Behnia et al. (2025)**<br>`arXiv:2503.13968v1` | *Comment on Unusual violation of the Wiedemann-Franz law at ultralow temperatures in topological compensated semimetals* (2025 preprint) | **arXiv 實時命中** | 指出極低溫（mK 級）量測中看似違反 Wiedemann–Franz 定律的現象，常源於**電子–聲子解耦（electron-phonon decoupling）**導致之實驗量測偽影。 | 強化本模型在 $10\text{–}350\text{ mK}$ 極低溫區之不確定性邊界：在極低溫下電子溫度與晶格（聲子）溫度可能解耦，單純以巨觀單一溫度線性分布 $T(x)$ 外推量子比特端熱狀態存在顯著物理限制。 |
| **NIST 低溫材料庫 / Marquardt et al. (2000) / Bradley et al. (2006) / Simon et al. (1992) / Flynn** | NIST Cryogenics Material Properties Database (`trc.nist.gov`)；*11th Int. Cryocooler Conf.* (2000)；*ICEC 21* (2006)；*NIST Monograph 177* (1992)；*Cryogenic Engineering* | **專案已驗證 SSOT 上游資料庫與教科書（非本次 arXiv 命中）** | 定義 9 參數對數多項式 $\log_{10}\kappa(T)=\sum_{n=0}^{8}c_n(\log_{10}T)^n$、OFHC 銅 `rational_copper` 有理式、每個材料之有效溫度區間 `valid_range_K`（多數下限為 $1\text{–}4\text{ K}$），以及一維傅立葉穩態熱傳導積分基礎。 | 構成 SSOT **D4=A**（53 筆固定係數材料）之唯一數值根據；同時界定 $T < 1\text{–}4\text{ K}$ 無固定多項式擬合支撐，禁止將高溫多項式盲目外推至 mK 溫區。 |

---

## 對本物理模型之支持點

綜合上述 arXiv 檢索證據與專案 SSOT 溯源紀錄，本專案「溫區擬合」物理模型（`docs/溫區擬合_物理模型_來源萃取.md` 與論文 Section 3.2 之 `M1`–`M5`）獲得以下四項明確文獻支持：

1. **一維穩態非線性傅立葉導熱積分（`M1_fourier_integral`）與分溫階熱預算架構獲主流文獻直接支持：**
   - 無論是半剛性同軸線熱建模（**Raicu et al., 2025**, `arXiv:2502.01945v3`）、超導 Nb47Ti 柔性同軸帶狀線設計（**Smith et al., 2020 & 2024**, `arXiv:2007.06496v1`, `arXiv:2306.13574v2`），或百量子比特稀釋冷凍機熱工程基準（**Krinner et al., 2019**, `arXiv:1806.07862v1`），均將跨溫階傳輸線之靜態（被動）傳導熱負載建立於分溫階傅立葉積分 $Q_i = \frac{A}{L_i}\int_{T_{c,i}}^{T_{h,i}}\kappa(T)\,dT$（對複合截面為各材料層加總 $\sum_k \frac{A_k}{L_i}\int_{T_{c,i}}^{T_{h,i}}\kappa_k(T)\,dT$），並將其與主動歐姆/微波衰減耗散（$I^2 R$ 或 $Q_{\text{rf}}$）疊加後對照各溫階製冷功率（cooling power budget）。
   - 此外，**Smith et al. (2020, 2024)** 對 $1\text{ K}\to 90\text{–}100\text{ mK}$ 溫階、長 $\sim 30\text{ cm}$ 之超導柔性排線估算值（$20\text{ nW/trace}$ 至 $5\text{ nW/trace}$），與本專案推導筆記引述之 CF3 對標脈絡（$350\text{ mK}\to 10\text{ mK}$, $L=20\text{ cm}$, $\sim 20\text{ nW/ch}$）在物理量級與溫階積分邏輯上完全一致。

2. **熱導率 $\kappa(T)$ 之 9 參數對數多項式擬合與有效溫區內積分實務（SSOT D4=A）與最新同儕審查文獻完全對齊：**
   - **Raicu et al. (2025)**（`arXiv:2502.01945v3` / *EPJ Quantum Technol.* 12:124）明確採用與 NIST 低溫材料庫（**Marquardt et al., 2000**; **Bradley et al., 2006**）相同形式之 9 參數對數多項式擬合實驗量測與文獻材料之 $\kappa(T)$（Table 4，保留 7 位有效數字）及內導體 $\rho(T)$（Table 6），並於有效量測溫區（約 $2\text{–}300\text{ K}$）內積分計算稀釋冷凍機各溫階之靜態導熱負載。這直接驗證了本論文 Section 2.3 / 3.1 / 3.2 將計算錨定於 SSOT D4=A 並強調「擬合有效區間內積分穩定」之方法學正當性。

3. **Wiedemann–Franz 定律結合常數殘餘電阻率（`M3_wf_const_rho`）作為正常態金屬低溫電子熱導解析模型具堅實物理依據：**
   - **Sologubenko et al. (2006)**（`arXiv:cond-mat/0608143v2`）、**Graf et al. (1996)**（`arXiv:cond-mat/9509046v1`）與 **Hu et al. (2021)**（`arXiv:2011.07707v1`）均確認：當金屬處於低溫彈性雜質/缺陷散射主導區時，電子熱導率與電導率遵循 Wiedemann–Franz 定律 $\kappa_e(T) = L_0 T/\rho$（$L_0 = (\pi^2/3)(k_B/e)^2 \approx 2.44\times 10^{-8}\ \text{W}\Omega/\text{K}^2$）。
   - **Raicu et al. (2025)** 亦在 $T < 3.8\text{ K}$ 區間將內導體直流電阻率取為常數殘餘值（$\rho_0 = 9.928\times 10^{-9}\ \Omega\cdot\text{m}$）。在此 $\rho(T)\approx\rho_0=\text{const}$ 條件下，一維傅立葉積分嚴格化約為本模型之平方差解析式 $Q = \frac{L_0 A}{2\rho_0 L}(T_h^2 - T_c^2) = \frac{L_0 T_{\text{avg}}\Delta T}{R}$。

4. **極低溫量子比特熱激發退相干指標與「必須依賴分級熱錨/衰減器熱化」之邊界判斷獲實驗文獻直接證實：**
   - **Paluch et al. (2024)**（`arXiv:2410.01053v1`）直接以超導量子比特（Fluxonium）退相干率量測柔性微波帶狀線之熱化，並以讀取諧振器殘餘熱光子數（$<3.5\times 10^{-3}$）與量子比特有效溫度（$26.4\text{ mK}$）作為熱化成功與否的定量判準。這證實了本模型以玻色–愛因斯坦熱光子佔據率 $n_{\text{th}}(T) < 0.01$（對應 $5.5\text{ GHz}$ Transmon 臨界溫度 $T_{\text{crit}}\approx 57.6\text{ mK}$）評估極低溫熱影響的物理合理性；同時該文獻透過**在各溫階分佈整合 $60\text{ dB}$ 衰減器**達成熱化，完全印證本論文 Section 3.2 第 4 點與 `docs/溫區擬合_物理模型_來源萃取.md` 所列之核心限制——實務上絕非單靠拉長無熱錨懸空排線來維持量子比特低溫。

---

## 限制與不確定性

本節明確劃定外部文獻支持之邊界，並區分**文獻已驗證事實**與**專案內部假設相依推導（assumption-dependent project derivations）**：

1. **「溫區熱導積分比消去截面積 $A$ 之長度回推公式（`M4_integral_ratio_backcalc`）」與「mK 級線性溫度分布安全長度回推（`M5_mk_qubit_safe_length`：$2.8\text{ cm}$ / $35.7\text{ cm}$ / $7.5\text{ cm}$）」屬於專案內部代數推導，非 arXiv 文獻通用定律：**
   - 公式 $L = L_{\text{ref}}\left(\frac{P_{\text{ref}}}{P_{\text{image}}}\right)\left(\frac{I_{\text{image}}}{I_{\text{ref}}}\right)$ 是由標準傅立葉積分 $P = \frac{A}{L}I$ 在**同構橫截面假設（$A_{\text{image}} = A_{\text{ref}}$）**下相除消去 $A$ 的正確代數推論（記載於專案筆記 `傅立葉導熱定律回推長度.md`，含 $40\text{ K}\to 4\text{ K}$ 對 $50\text{ K}\to 4\text{ K}$ 示例比值 $1.48$），但並非出自 Smith 或 Raicu 等外部文獻之特定經驗公式。
   - 一旦比較異構排線（例如 CF3 7 層 $300\ \mu\text{m}$ GSG 結構對比含導通孔之 FPC 11 層 $144.1\ \mu\text{m}$ 結構），各層導體與介電質截面積 $A_k$ 比例完全不同，**消去 $A$ 之前提失效**，必須回歸 **Raicu et al. (2025)** 與 **Smith et al. (2020, 2024)** 所採用的分層面積加權積分 $\sum_k \frac{A_k}{L}\int\kappa_k(T)\,dT$。

2. **線性溫度分布 $T(x) = T_c + (T_h - T_c)(x/L)$ 在極低溫區（$10\text{–}350\text{ mK}$）為高度簡化假設，不可作為硬體設計定論：**
   - 線性 $T(x)$ 僅在熱導率 $\kappa(T)=\text{const}$ 且無中間熱錨、無內熱源時成立。然而在極低溫區，無論是金屬（$\kappa \propto T$）、介電質（$\kappa \propto T^\beta, \beta\approx 1\text{–}2$）或超導體（電子導熱指數衰減、聲子受邊界散射主導），$\kappa(T)$ 均隨溫度強烈變化；一維穩態熱流守恆 $\kappa(T)\frac{dT}{dx} = \text{const}$ 必然產生**非線性（凹向下）溫度分布** $T(x)$，使冷端附近溫度梯度更陡、熱端附近更平緩。
   - 更重要的是，如 **Krinner et al. (2019)**（`arXiv:1806.07862v1`）與 **Paluch et al. (2024)**（`arXiv:2410.01053v1`）所示，稀釋冷凍機實務透過多級熱錨（Still / Cold Plate / Mixing Chamber）與分佈式衰減器將排線與電磁場分段熱化，且在極低溫下還存在電子–聲子解耦效應（**Behnia et al., 2025**, `arXiv:2503.13968v1`）。因此，專案筆記由線性 $T(x)$ 算出的 $x_{\text{safe}}\approx 2.8\text{ cm}$、延長總長 $L_{\text{new}}\approx 35.7\text{ cm}$ 以及二次自發熱假設 $\Delta T\propto L^2$ 算出的 $L_{\max}\approx 7.5\text{ cm}$，**僅能定位為展示邊界條件敏感度的教學/探索示例**。

3. **Wiedemann–Franz 定律（`M3_wf_const_rho`）與薄膜/超導/介電質材料之適用限制：**
   - **非晶介電質基材（Polyimide / Kapton / PTFE / PFA）：** 無自由電子，熱傳導由聲子邊界散射與雙能階系統（TLS）主導，Wiedemann–Franz 定律完全不適用。
   - **超導態導體（如 NbTi 於 $T < T_c \approx 9.2\text{–}9.8\text{ K}$）：** 庫柏對凝聚不傳遞熵與熱量，準粒子電子熱導隨 $\exp(-\Delta/k_B T)$ 指數衰減，零電阻（$\rho\to 0$）下套用 $\kappa = L_0 T/\rho$ 會導致發散之物理錯誤。
   - **微米/奈米薄膜尺寸效應：** 如 **Hu et al. (2021)**（`arXiv:2011.07707v1`）所示，當金屬薄膜厚度縮減至次微米/數十奈米尺度時，表面與晶界散射會同時壓低有效熱導率並改變聲子與電子貢獻比例；因此薄層柔性排線（如 $0.2\ \mu\text{m}$ 或 $2\ \mu\text{m}$ 導體層）若直接套用塊材（bulk）RRR 或塊材 $\kappa(T)$ 曲線，將引入高估導熱之系統性偏差。

4. **SSOT（D4=A）擬合溫度範圍與深低溫外推不確定性：**
   - SSOT 資料庫（`coeff_data.py` / `thermal_load.py`）與 **Raicu et al. (2025)** Table 4 之 9 參數 log-log 多項式有效範圍大多止於 $\ge 1\text{–}4\text{ K}$（例如 Raicu C7150 外導體為 $2.0\text{–}297.6\text{ K}$、PTFE 為 $4\text{–}300\text{ K}$、內導體為 $2.3\text{–}292.6\text{ K}$；Raicu 對 $<2\text{ K}$ 係採最低溫數據點向原點線性延伸，而非直接外推 8 階多項式）。
   - 如本專案 `docs/polyfit_可靠度驗證.json` 與論文 Section 5 所證實，若將 $\ge 2\text{ K}$ 之 8 階多項式或端點冪次直接外推至 $20\text{ mK}$，數值會失真至 $10^{15}\text{–}10^{17}\ \text{W}\cdot\text{m}^{-1}\cdot\text{K}^{-1}$ 並隨微擾劇烈跳動；同時 SSOT 中 `NbTi (Cri/oFlex 3)` 為 `runtime_polyfit`（`coeffs=null`），在 $T_c$ 附近亦存在全域多項式結構殘差。因此，任何 $10\text{–}350\text{ mK}$ 區間之定量熱負載估算均不得依賴 SSOT 8 階多項式盲目外推。

5. **檢索工具與覆蓋範圍限制：**
   - `arxiv_search.py` 僅查詢 arXiv 預印本庫之標題/摘要/作者 metadata，不包含未上傳至 arXiv 之傳統低溫工程期刊或商業規格書（如 NIST Monograph 177、ICEC 會議論文、Delft Circuits Cri/oFlex® 產品資料表）；且 arXiv API 對含括號之查詢詞（如 Q1 之 `kappa(T)`）會觸發布林分組退化，實務上需如 Q4 移除特殊括號字元方可獲得準確排序。

---

## 結論（證據有界）

基於本次 `arxiv-search` 實時檢索（Q1–Q6）與專案 SSOT 溯源核對，針對「溫區擬合」物理模型得出以下證據有界結論：

1. **核心模型 $Q = \frac{A}{L}\int_{T_c}^{T_h}\kappa(T)\,dT$ 與分溫階熱預算（stage-wise heat budgeting）、以及在低溫正常態金屬彈性雜質散射條件下使用 Wiedemann–Franz 定律（$\kappa_e = L_0 T/\rho$）作為電子熱導關係，均為標準固態/低溫物理，且與當代超導量子計算低溫佈線熱建模文獻實務（如 Raicu et al. 2025 `arXiv:2502.01945v3`、Krinner et al. 2019 `arXiv:1806.07862v1`、Smith et al. 2020/2024 `arXiv:2007.06496v1` / `arXiv:2306.13574v2`）完全一致。**
2. **溫區積分比消去面積之長度回推公式 $L = L_{\text{ref}}(P_{\text{ref}}/P_{\text{image}})(I_{\text{image}}/I_{\text{ref}})$ 與極低溫（$10\text{–}350\text{ mK}$）線性溫度分布安全長度回推（$2.8\text{ cm}$ / $35.7\text{ cm}$ / $7.5\text{ cm}$），均屬於高度依賴前提假設之專案內部簡化推演（assumption-dependent simplifications）：** 前者嚴格受限於「同構橫截面與相同材料層疊（$A_{\text{image}}=A_{\text{ref}}$）」；後者則忽略了極低溫 $\kappa(T)$ 強烈非線性、電子–聲子解耦，以及實務稀釋冷凍機必備之分級熱錨與分佈式衰減器熱化機制（如 Paluch et al. 2024 `arXiv:2410.01053v1` 與 Krinner et al. 2019 所示）。
3. **工程校核原則：** 任何實際排線長度設計與跨溫區熱負載評估，均須回歸有效溫度範圍（`valid_range_K`）內之分層 $\kappa_k(T)$ 定積分 $\sum_k \frac{A_k}{L}\int_{T_c}^{T_h}\kappa_k(T)\,dT$，並結合實際熱錨配置、微波衰減自發熱（$Q_{\text{rf}}$）與薄膜/超導相變邊界條件進行校核；嚴禁將 SSOT $\ge 1\text{–}4\text{ K}$ 多項式外推至毫克耳文溫區或將線性溫度分布回推值當作通用硬體規格定論。
