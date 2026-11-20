 我來查詢 Light Fluxonium 與 Heavy Fluxonium 的具體參數範圍。  
根據文獻資料，我為您整理 **Light Fluxonium** 與 **Heavy Fluxonium** 的詳細參數對比：

---

## 定義與分界

| 類型 | 定義條件 | 物理特徵 |
|------|----------|----------|
| **Light Fluxonium** | $E_L \ll E_J, E_C$ 或 $E_J/E_C \sim 1-10$ | 頻譜較線性，對磁通噪音較不敏感，類似「輕」粒子行為  |
| **Heavy Fluxonium** | $E_J \gg E_L, E_C$ 且 $E_J/E_C \gg 10$ | 相位波函數局域於單一勢阱，磁通子（Fluxon）態長壽命，強非諧性  |

**關鍵分界**：$E_J/E_C \approx 10$ 是重要門檻 
- $E_J/E_C < 10$：偏向 Light regime
- $E_J/E_C > 10-20$：進入 Heavy regime
- $E_J/E_C \gg 20$：Deep Heavy regime（如 50-100）

---

## 典型參數對比

### Light Fluxonium

| 參數 | 典型值 | 說明 |
|------|--------|------|
| **$E_J/h$** | 4–8 GHz | Josephson 能量  |
| **$E_C/h$** | 1–3 GHz | 充電能量較大（電容較小） |
| **$E_L/h$** | 0.5–1.5 GHz | 電感能量  |
| **$E_J/E_C$** | **2–10** | Light regime 定義範圍  |
| **$E_J/E_L$** | 2–10 | 決定勢阱數量  |
| **驅動頻率 $f_{01}$** | **0.5–2 GHz** | 在 Sweet spot ($\Phi_{ext}/2\pi=0.5$) 頻率較低  |
| **高階躍遷** | 4–8 GHz | $|g\rangle \to |h\rangle$ 或 $|e\rangle \to |f\rangle$ 躍遷  |

**實例** ：
- $E_J/h = 4.75$ GHz, $E_C/h = 1.25$ GHz, $E_L/h = 1.5$ GHz
- $E_J/E_C \approx 3.8$（Light regime）
- Sweet spot 頻率 $\sim$ 500 MHz–1 GHz

---

### Heavy Fluxonium

| 參數 | 典型值 | 說明 |
|------|--------|------|
| **$E_J/h$** | 6–17 GHz | 大 Josephson 能量  |
| **$E_C/h$** | **0.2–0.8 GHz** | 充電能量很小（大電容） |
| **$E_L/h$** | **0.2–0.5 GHz** | 小電感能量  |
| **$E_J/E_C$** | **20–100+** | Heavy regime 核心條件  |
| **$E_J/E_L$** | 10–40 | 確保相位局域化  |
| **驅動頻率 $f_{01}$** | **10–500 MHz** | 在 Sweet spot 頻率極低（指數壓抑） |
| **高階躍遷** | **4–9 GHz** | Plasmon-like 躍遷用於讀取  |

**實例** ：
- $E_J/h = 8.97$ GHz, $E_C/h = 0.46$ GHz, $E_L/h = 0.24$ GHz（$E_J/E_C \approx 19$）
- $E_J/h = 17$ GHz, $E_C/h = 0.8$ GHz, $E_L/h = 2.8$ GHz（$E_J/E_C \approx 21$）
- Sweet spot 頻率可低至 **15–100 MHz** 

---

## 讀取頻率與功率

### 讀取頻率

| 類型 | 讀取策略 | 頻率範圍 |
|------|----------|----------|
| **Light Fluxonium** | 直接讀取 $f_{01}$ 或利用高階躍遷 | **4–8 GHz**（與共振腔耦合） |
| **Heavy Fluxonium** | 主要利用高階 Plasmon 躍遷（$|g\rangle \to |h\rangle$ 或 $|e\rangle \to |f\rangle$）作為輔助讀取  | **4–9 GHz**  |

**Heavy Fluxonium 特殊之處**：
- 基態躍遷 $f_{01}$ 僅數十 MHz，無法直接與微波共振腔耦合
- 利用 **$f_{gh} \approx f_{ef} \approx \sqrt{8E_C E_J}/h \sim 4-8$ GHz** 進行態讀取 
- 例如：$E_J=8.97$ GHz, $E_C=0.46$ GHz $\to \sqrt{8 \times 8.97 \times 0.46} \approx 5.7$ GHz

### 輸入功率

| 參數 | 典型值 | 說明 |
|------|--------|------|
| **讀取功率（晶片端）** | **-120 至 -100 dBm** | 單量子位元讀取  |
| **多量子位元系統** | **-110 至 -100 dBm** | 每量子位元功率  |
| **驅動功率（單量子閘）** | **-80 dBm** | 快速單量子閘操作  |
| **Fluxonium 低頻驅動** | 需額外放大 | 室溫放大器 +43 dBm 輸出  |

**注意**：Heavy Fluxonium 在 Sweet spot 操作時 $f_{01} \sim 100$ MHz，需要：
1. **室溫大功率放大器**（如 Mini-Circuits ZHL-20W-13+，+43 dBm）
2. 或利用 **Flux pulse** 將量子位元調離 Sweet spot 進行快速操作 

---

## 總結比較表

| 特性 | Light Fluxonium | Heavy Fluxonium |
|------|-----------------|-----------------|
| **$E_J/E_C$** | 2–10 | 20–100+ |
| **$E_C/h$** | 1–3 GHz | 0.2–0.8 GHz |
| **$E_L/h$** | 0.5–1.5 GHz | 0.2–0.5 GHz |
| **$f_{01}$ @ sweet spot** | 0.5–2 GHz | 10–500 MHz |
| **操作優勢** | 頻率較高，直接操控較易 | T1 極長（>250 μs），磁通噪音免疫  |
| **操作挑戰** | 對磁通噪音較敏感 | 需低頻或輔助態讀取，操控複雜 |
| **讀取頻率** | 4–8 GHz | 4–9 GHz（利用高階躍遷）|
| **讀取功率** | -120 ~ -100 dBm | -120 ~ -100 dBm |

**設計哲學**：
- **Light**：平衡頻率與操控性，適合快速閘操作
- **Heavy**：最大化相干時間，適合量子記憶體與高精度計算
