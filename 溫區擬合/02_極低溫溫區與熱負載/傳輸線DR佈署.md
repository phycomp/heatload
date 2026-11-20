在 Bluefors XLD400 稀釋冷凍機中，各溫區（包含 Still、CP 及 MXC）之間的 Cable length（纜線長度） 會依據實驗需求、線材種類以及您使用的側裝 (Side-loading) 或頂裝安裝座而有所不同。由於您的需求可能偏向於微波測試 (RF) 或高頻接線，以下為您整理這些溫區接線的關鍵資訊：

## 1. 溫區定義 (Temperature Stages)

* Still: 蒸餾器溫度約 ≈ 700 mK
* CP (Cold Plate): 冷板溫度約 ≈ 100 – 200 mK
* MXC (Mixing Chamber): 混合腔溫度約 ≈ 10 mK [1, 2] 

## 2. Cable Length (實體線材長度與考量)
實際的 Cable Length 取決於從上一溫區延伸下來的線段長度 (cable run)： [3] 

* 熱負載與線長： 在 CP 與 MXC 溫區之間，纜線長度通常較短，這會增加上層溫區的熱負載，需要透過適當的熱錨定 (thermal anchoring) 來將高頻/直流信號的熱量導出。 [1, 4, 5] 
* 總長度配置： 對於射頻 (RF) 佈線或 Thermocoax 等長線，從室溫 (RT) 到 MXC 總長度常配置為約 3 m，並在每個平臺 (包含 Still 和 CP) 進行金屬線軸固定。 [4, 6] 
* Below MXC（量子位元封裝區）： 在抵達 MXC 板後，連接至樣品盒 (Package holding the quantum processor) 的線段通常是等溫的，其長度會根據極低溫 PCB 或樣品座的實體空間客製化。 [3] 

## 3. 線材選用
為了在 Still、CP 到 MXC 之間保持微波性能同時抑制熱傳導，常用的線材包含：

* 超導線 (Superconducting Cables)： 常用於 4K 以下溫區（如 CP 到 MXC），能大幅降低 Ohmic heat load（歐姆熱負載）。 [1] 
* 高密度軟性微波線 (High-Density Flex Wiring / SC-086)： 用於不同溫區的信號傳輸，可利用 Bluefors 原廠的[測量基礎設施基礎件](https://bluefors.com/products/measurement-infrastructure/coaxial-wiring/)來配置與規劃各溫區間的熱錨。 [1, 6] 

為了更精準地協助您設計，請告訴我： 1. 您是要佈署 DC 迴路 還是 RF/微波線路？ 2. 您預計在各個溫區之間使用哪種線材類型（如 NbTi 超導線、SMA 同軸線或雙絞線）？ 3. 您是在規劃 Room Temperature (RT) 到 MXC 的整體佈局嗎？

1. [https://www.researchgate.net](https://www.researchgate.net/publication/397079265_Cryogenic_thermal_modeling_of_microwave_high_density_signaling)
2. [https://www.researchgate.net](https://www.researchgate.net/figure/a-Plates-of-the-Bluefors-LD-250-dilfridge-system-50-K-plate-i-i-40-K-4-K-plate_fig1_388715530)
3. [https://arxiv.org](https://arxiv.org/html/2502.01945v1)
4. [https://bluefors.com](https://bluefors.com/products/measurement-infrastructure/coaxial-wiring/)
5. [https://bluefors.com](https://bluefors.com/products/measurement-infrastructure/optical-fibers/)
6. [https://bluefors.com](https://bluefors.com/products/measurement-infrastructure/coaxial-wiring/)

規劃 Bluefors XLD400 稀釋冷凍機從室溫 (RT) 到混合腔 (MXC) 的整體佈局時，核心挑戰在於最大化信號傳輸品質（高頻頻寬/低雜訊）並同時最小化傳導熱負載 (Thermal Heat Load)。 [1, 2] 
若以標準的高頻/微波同軸線（Coaxial Wiring）佈局為例，Bluefors 原廠針對這段路徑提供的標準實體總長度通常為 3 公尺 ($\pm 5\%$)，並透過以下溫區分段與硬體配置來實現： [3] 

## 一、 溫區分段布局與線材選用
為了平衡熱導率，從 RT 到 MXC 必須在不同階段Stages切換線材材質： [1, 2] [1,2,3,4,5]

| 溫區分段 | 溫度區間 | 標準長度 | 推薦高頻線材材質 | 佈局目的/關鍵組件 |
|---|---|---|-------|--------|
| RT $\rightarrow$ 4K | 300 K $\rightarrow$ 4 K | 約1.9 m | SCuNi-CuNi白銅線 常用外徑.86mm | 抑制從室溫侵入的大量熱量 RT端通常接Feedthrough Box SMA |
| 4K $\rightarrow$ MXC | 4 K $\rightarrow$ 10 mK | 約1.5 m | NbTi-NbTi鈮鈦超導線 4K以下進入超導態 | 實現零電阻 無歐姆發熱 且超導體熱導率極低 保護極低溫區 |

💡 總長度備註 由於線路在各溫區需要繞過內部結構並進行熱錨定 Thermal Anchoring 分段實體長度之和1.9m + 1.5m 會略大於直線淨空距離，總實體線長約為3公尺 [3]

## 二、 核心硬體佈局元件

## 1. 熱錨定（Thermal Anchoring）與衰減器（Attenuators）

* 中心導體熱化： 同軸線的 PTFE 介電層會阻礙中心導體散熱。因此在 4K、Still、CP、MXC 每個平臺的隔板（Bulkhead）上，必須直接螺接低溫衰減器（Attenuators）或衰減器方塊（Attenuator Blocks），藉此迫使中心導體與該溫區冷盤達到熱平衡。 [1, 2] 
* 衰減配置範例（驅動線路 Drive Line）：
* 4K Stage: 0 dB 或 3 dB
   * Still Stage: -10 dB
   * CP Stage: 0 dB
   * MXC Stage: -20 dB（總衰減達 -30 到 -40 dB，以完全壓制來自 RT 的熱輻射雜訊）

## 2. 通道擴充選擇：LOS Port vs. Side-Loading (側裝)
XLD400 提供了極大的空間，您可以依據通道數量需求選擇兩種主流佈局：

* 傳統高直視度孔（LOS Ports）： 使用 KF40 或 ISO-K63 孔位安裝，適合傳統 SMA 接頭線組（單孔一般可容納 24 條 Thermocoax 或標準同軸線）。 [3, 6] 
* 高密度側裝模組（High-Density Wiring / Side-Loading）： 針對量子計算多通道（如 >100 條線）設計。它在室溫端使用氣密的多針接口，內部採用高密度軟板（Flex）或 0.86mm 陣列線，並在 MXC 端統一收納為 SMPM 整合式接頭，大幅節省 MXC 空間。 [2, 7] 

## 三、 整體設計檢核清單 (Checklist)

   1. 熱負載計算： 大量使用 2.19 mm 線材會對 4K 溫區造成過大熱負荷，高密度佈局時建議統一採用 0.86 mm 規格。
   2. 相位穩定度： 確保線材在降溫收縮後不會產生過大應力，標準線組皆有預留微幅彎曲半徑（Bending radius）。
   3. 紅外線屏蔽（IR Shielding）： 線路穿過各溫區防護罩（Shields）的開口必須妥善密封，防止室溫紅外線直接照射到 MXC 樣品區。 [1] 

為了進一步幫您確認這套 3 公尺的整體佈局： 1. 您目前的實驗需要佈署多少個 RF 通道？（這決定了您該用傳統 LOS 還是 High-Density 側裝） 2. 這條線路是量子位元的驅動線 (Drive)、讀取線 (Readout)，還是包含低頻直流的 Flux Bias 線？（不同用途的衰減器分配差異極大）


1. [coaxial-wiring](https://bluefors.com/products/measurement-infrastructure/coaxial-wiring/)
2. [high-density-wiring](https://bluefors.com/products/measurement-infrastructure/high-density-wiring/)
3. [coaxial-wiring](https://bluefors.com/products/measurement-infrastructure/coaxial-wiring/)
4. [components-of-DR](https://bluefors.com/stories/components-of-the-dilution-refrigerator-measurement-system/)
5. [xldsl-DR](https://bluefors.com/products/dilution-refrigerator-measurement-systems/xldsl-dilution-refrigerator-measurement-system/)
6. [preconfigured-systems](https://bluefors.com/products/dilution-refrigerator-measurement-systems/preconfigured-systems/)
7. [flex-wiring](https://bluefors.com/news/new-products-enhanced-cooling-high-density-flex-wiring-and-ld400sl/)

在 Bluefors XLD400 稀釋冷凍機上佈署 High-Density (HD) 側裝 (Side-loading) 模組來同時跑 Drive、Readout 與 Flux Bias，是目前超導量子計算（Superconducting Qubits）最主流的大規模擴充方案。 [1, 2] 
針對這三種性質截然不同的線路，不能直接混用同一種排線配置。以下為您拆解在 XLD400 側裝通道內，從室溫 (RT) 到混合腔 (MXC) 的整體佈局與衰減器（Attenuator）硬體配置： [1, 2] 

## 一、 三大線路的 High-Density 佈局架構
Bluefors 的高密度側裝系統（單個 Port 可容納多達 168 至 240 個通道）採用整合式衰減器方塊 (Attenuator Blocks)，並在 MXC 端統一輸出為高密度的 SMPM 多針接頭。 [1, 3, 4] 

```
【RT 端的 SMA/高密度接頭】 
       │ 
       ▼ (300K -> 4K Stage: 使用 SCuNi-CuNi 白銅同軸排線，抑制外部熱傳導)
【 4K Stage 】 ─── 設置 4K 熱錨定 / 基礎衰減 / Readout HEMT 放大器
       │ 
       ▼ (4K -> MXC Stage: 使用 NbTi-NbTi 超導同軸排線，達到零電阻發熱)
【 Still / CP Stage 】 ─── 分段熱錨定與分段衰減 (例如 Still 接 -10dB)
       │ 
       ▼
【 MXC Stage 】 ─── 最終衰減 (-20dB) / 紅外線濾波器 (IR Filters)
       │ 
       ▼ 【 輸出：SMPM 整合式接頭 】 ─── 直奔量子晶片樣品盒
```

## 二、 三大線路的細部配置與熱錨定需求
不同的線路在不同溫區的配置大不相同，必須進行物理隔離或在 Attenuator Block 中分區段規劃： [3] 
## 1. 量子位元驅動線 (Microwave Drive Lines)

* 功能： 傳輸微波脈衝（通常為 4–8 GHz）以控制 Qubit 狀態。 [5, 6] 
* 衰減器配置 (關鍵)： 為了徹底壓制室溫端侵入的熱輻射雜訊（Thermal Photon Noise），總衰減量通常需要 -30 dB 至 -40 dB。
* 4K Stage: 0 dB 或 -3 dB
   * Still Stage: -10 dB
   * MXC Stage: -20 dB (高密度衰減器方塊) [3, 7] 
* 硬體防護： 在 MXC 端必須加裝 紅外線濾波器 (IR Filters)，防止高能光子導致量子位元去同調。 [8] 

## 2. 讀取線 (Readout Lines) ── 區分「輸入」與「輸出」

* 讀取輸入 (Readout Input / Read-in)：
* 路徑與 Drive 類似，但因為信號是用來感應 Resonator，雜訊控制極嚴。
   * 衰減配置通常在 Still 分配 -10 dB，MXC 分配 -20 dB（總衰減約 -30 dB）。 [7] 
* 讀取輸出 (Readout Output / Read-out)：
* 絕對不能加衰減器！ 它是微弱的量子信號輸出路徑，目標是低損耗（Low loss）。
   * 4K Stage: 必須加裝高增益的 HEMT 低雜訊放大器。
   * MXC Stage: 必須串聯 隔離器 (Isolators / Circulators)，阻止 4K HEMT 放大器的熱雜訊反向回流到晶片。 [5, 6, 7] 

## 3. 低頻直流偏置線 (Flux Bias Lines / Fast Flux)

* 功能： 傳輸直流電流或快速電壓脈衝，用於調整 Qubit 的工作頻率（Z 控制）。 [5, 7] 
* 線材考量： 雖然它是低頻/直流，但為了保持脈衝的陡峭邊緣（高時序解析度），常採用 Lossy Lines（高損耗高頻同軸線） 或專門的 [Bluefors 雙絞線 (Twisted Pairs) 模組](https://bluefors.com/products/measurement-infrastructure/)。 [9, 10] 
* 衰減與濾波配置：
* 不需要像 Drive 那麼大的微波衰減，通常在 MXC 端配置 0 dB 或 低值衰減器 (-3 dB / -6 dB) 來做基本熱錨定。
   * 必須加裝 低通濾波器 (Low-pass Filters / RC or LC Filters)，徹底濾除高頻雜訊，同時允許直流與 Z 脈衝通過。 [3, 7] 

## 三、 High-Density 側裝的三種主流硬體選擇
在向 Bluefors 訂購或配置 XLD400 側裝模組時，目前有三種主要的技術路線可以完美容納上述線路：

   1. [Bluefors](https://bluefors.com/products/measurement-infrastructure/high-density-wiring/) 標準 Coaxial HDW (0.86 mm 系列)：
   使用一組組（每組 24 條線）的密裝同軸線。您可以劃分其中幾組走 Drive（配大衰減）、幾組走 Flux（配低通濾波/低衰減），各組在各溫區對接專屬的 SMPM 衰減器方塊。 [3] 
   2. Bluefors High-Density Flex Wiring (FPC 軟板技術)：
   這是近年推出的新技術，單個 Port 可高達 240 個通道，基於 Lossy lines 專利技術。它從 RT 到 MXC 是一體成型的連續軟板，大幅減少了中繼接頭，對 Drive 和 Flux 線的整合度極高。 [9] 
   3. Delft Circuits Cri/oFlex® 聯合方案：
   Bluefors 與 Delft Circuits 深度合作的整合方案。它利用平面微波電路（Stripline 設計）將衰減器、濾波器直接整合印製在軟排線上，單個側裝 Port 就能直接配置出 64、128 或 256 個包含 Drive 與 Flux 的混合通道，熱負載極低且完全免去手動熱錨定的麻煩。 [11, 12] 

為了協助您做最終的腔內空間與通道分配： 1. 您這套系統預計要對接的超導晶片是 幾個 Qubit 的架構？（例如：5-Qubit 架構通常需要 5 條 Drive、9 條 Flux 與 1 對 Readout） [7] 2. 您傾向採用 Bluefors 原廠的傳統同軸高密度線組 (Coaxial HDW)，還是更新型的一體式軟板 (Flex/FPC) 方案？ [3, 9] 


1. [high-density-wiring](https://bluefors.com/products/measurement-infrastructure/high-density-wiring/)
2. [cryogenic-infrastructure](https://bluefors.com/stories/cryogenic-measurement-infrastructure-for-quantum-computing/)
3. [high-density-wiring](https://bluefors.com/products/measurement-infrastructure/high-density-wiring/)
4. [ld400sl](https://bluefors.com/news/new-products-enhanced-cooling-high-density-flex-wiring-and-ld400sl/)
5. [2502.01945v2](https://arxiv.org/html/2502.01945v2)
6. [Nuutinen_Ville](https://www.theseus.fi/bitstream/10024/885236/2/Nuutinen_Ville.pdf)
7. [preconfigured](https://bluefors.com/products/dilution-refrigerator-measurement-systems/preconfigured-systems/)
8. [coaxial-wiring](https://bluefors.com/products/measurement-infrastructure/coaxial-wiring/)
9. [ld400sl](https://bluefors.com/news/new-products-enhanced-cooling-high-density-flex-wiring-and-ld400sl/)
10. [measurement-infrastructure](https://bluefors.com/products/measurement-infrastructure/)
11. [crioflex](https://bluefors.com/products/measurement-infrastructure/crioflex/)
12. [delft-bluefors-join-forces](https://delft-circuits.com/dc_news_article/delft-circuits-and-bluefors-join-forces/)

