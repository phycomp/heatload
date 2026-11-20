# Microstrip 傳輸線 — 物理模型與解析公式推導

> **文件編號**: DOC-001-Microstrip  
> **層級**: Level 1（準靜態模型）  
> **日期**: 2026-09-05  
> **作者**: PCB Impedance Model Project  

---

## 目錄

1. [物理模型與幾何結構](#1-物理模型與幾何結構)
2. [基本假設與邊界條件](#2-基本假設與邊界條件)
3. [有效介電常數的物理意義](#3-有效介電常數的物理意義)
4. [Wheeler 保角映射法](#4-wheeler-保角映射法)
5. [Hammerstad-Jensen 公式](#5-hammerstad-jensen-公式)
6. [導體厚度修正](#6-導體厚度修正)
7. [頻散效應預告](#7-頻散效應預告)
8. [Python 實作](#8-python-實作)
9. [數值驗證](#9-數值驗證)
10. [參考文獻](#10-參考文獻)

---

## 1. 物理模型與幾何結構

### 1.1 結構示意

```
┌─────────────────────────────────────────┐
│              Air (ε₀, μ₀)               │  y = h
│                                         │
│    ████████████████████████████████     │  ← Signal trace
│    width = w, thickness = t             │  y = 0
│                                         │
├─────────────────────────────────────────┤
│                                         │
│           Dielectric Substrate          │
│         (ε₀εᵣ, μ₀), thickness = h       │
│                                         │
├─────────────────────────────────────────┤
│█████████████████████████████████████████│  ← Ground Plane
│              y = -h                     │
└─────────────────────────────────────────┘
```

### 1.2 坐標系統與參數定義

| 符號 | 名稱 | 單位 | 說明 |
|------|------|------|------|
| $w$ | 導體帶寬度 | mm / μm | 訊號線寬度 |
| $t$ | 導體厚度 | mm / μm | 銅箔厚度（1 oz ≈ 35 μm） |
| $h$ | 介質厚度 | mm / μm | 導體帶到接地平面距離 |
| $\varepsilon_r$ | 相對介電常數 | — | 基板材料參數（FR-4 ≈ 4.2） |
| $\varepsilon_{eff}$ | 有效介電常數 | — | 等效均勻介質的介電常數 |
| $Z_0$ | 特性阻抗 | Ω | 傳輸線特徵阻抗 |
| $\eta_0$ | 自由空間波阻抗 | Ω | $120\pi \approx 376.991\ \Omega$ |

### 1.3 關鍵物理特徵

1. **非均勻介質**：電場分佈同時存在於介質（$\varepsilon_r$）與空氣（$\varepsilon_r = 1$）中
2. **準 TEM 模**：當波長 $\lambda \gg h$ 時，可視為準靜態場分佈
3. **有效介電常數** $\varepsilon_{eff}$：描述等效均勻介質的介電特性，滿足 $1 < \varepsilon_{eff} < \varepsilon_r$

---

## 2. 基本假設與邊界條件

### 2.1 準靜態假設（Quasi-TEM Approximation）

當頻率足夠低，使得 $h \ll \lambda_g / 4$（$\lambda_g$ 為導波長），電磁場可視為靜態場分佈，傳播模式接近 TEM。

**條件**：

$$
f \ll \frac{c}{4h\sqrt{\varepsilon_r}}
$$

例如：$h = 1.6\ 	ext{mm}, \varepsilon_r = 4.2 \rightarrow f_{\text{max}} \approx 9\ 	ext{GHz}$

### 2.2 Level 1 無損耗假設

- 導體電導率 $\sigma \rightarrow \infty$（理想導體）
- 介質損耗 $	an \delta = 0$
- 暫不考慮表面粗糙度

### 2.3 邊界條件

| 位置 | 條件 | 數學表達 |
|------|------|----------|
| 接地平面 | 電位為零 | $\phi = 0$ （$y = -h$） |
| 導體帶 | 電位為 $V_0$ | $\phi = V_0$ （$y = 0, |x| \leq w/2$） |
| 介質-空氣界面 | 法向 $D$ 連續 | $\varepsilon_r E_y(0^-) = E_y(0^+)$ |

---

## 3. 有效介電常數的物理意義

由於 Microstrip 的場分佈同時存在於介質與空氣中，無法直接用單一介電常數描述。引入**有效介電常數** $\varepsilon_{eff}$：

### 3.1 定義

$$
\varepsilon_{eff} = \frac{C}{C_0}
$$

其中：
- $C$ = 實際結構（介質 + 空氣）的單位長度電容
- $C_0$ = 相同幾何但**空氣填充**時的單位長度電容

### 3.2 物理意義

$\varepsilon_{eff}$ 表示「等效均勻介質」的介電常數，使得：

$$
C = \varepsilon_{eff} \cdot C_0 = \varepsilon_{eff} \cdot \varepsilon_0 \cdot \left(\frac{C_0}{\varepsilon_0}\right)
$$

### 3.3 極限行為

| 極限 | 物理圖像 | 結果 |
|------|----------|------|
| $w/h \rightarrow \infty$ | 寬微帶線，近似平行板，場幾乎全在介質中 | $\varepsilon_{eff} \rightarrow \varepsilon_r$ |
| $w/h \rightarrow 0$ | 窄微帶線，近似細線，大量場在空氣中 | $\varepsilon_{eff} \rightarrow \dfrac{\varepsilon_r + 1}{2}$ |

---

## 4. Wheeler 保角映射法

### 4.1 核心思想

Wheeler (1965) 使用**保角映射（Conformal Mapping）**將 Microstrip 的複雜邊界轉換為可解析的幾何形狀。

透過 **Schwartz-Christoffel 變換**，將 $z$-平面的 Microstrip 截面映射到 $w$-平面的平行板電容器，從而解析求解電容。

### 4.2 推導步驟概述

**Step 1**：定義複平面 $z = x + jy$

邊界條件：
- 接地平面：$y = -h$
- 導體帶：$y = 0, |x| \leq w/2$
- 空氣界面：$y = 0, |x| > w/2$

**Step 2**：保角映射 $z \rightarrow \zeta$

使用**橢圓函數（Elliptic Functions）**將帶狀區域映射為上半平面。

**Step 3**：處理介質-空氣界面

Wheeler 的關鍵洞察：將問題分解為「空氣填充」和「介質填充」兩個子問題。

對於空氣填充的情況，映射後的平行板電容：

$$
C_{\text{air}} = \varepsilon_0 \cdot \frac{K(k')}{K(k)}
$$

其中 $K(k)$ 為**第一類完全橢圓積分**，$k$ 為模數。

**Step 4**：合成有效介電常數

Wheeler 引入**填充因子** $q$（$0 < q < 1$）：

$$
\varepsilon_{eff} = 1 + q \cdot (\varepsilon_r - 1)
$$

其中 $q$ 取決於幾何比 $w/h$：
- 寬線（$w/h \gg 1$）：$q \rightarrow 1, \varepsilon_{eff} \rightarrow \varepsilon_r$
- 窄線（$w/h \ll 1$）：$q \rightarrow 1/2, \varepsilon_{eff} \rightarrow (\varepsilon_r + 1)/2$

---

## 5. Hammerstad-Jensen 公式

Hammerstad & Jensen (1980) 基於 Wheeler 的保角映射結果，結合數值擬合，提出了工程上最廣泛使用的閉式解析公式。此公式被 **IPC-2141A**、**Polar Si8000**、**Mantaro** 等工具採用。

### 5.1 有效介電常數 $\varepsilon_{eff}$

$$
\varepsilon_{eff} = \frac{\varepsilon_r + 1}{2} + \frac{\varepsilon_r - 1}{2} \cdot F\left(\frac{w}{h}\right)
$$

其中 $F(w/h)$ 為**填充因子函數**：

**窄微帶線**（$w/h \leq 1$）：

$$
F\left(\frac{w}{h}\right) = \left(1 + \frac{12h}{w}\right)^{-1/2} + 0.04\left(1 - \frac{w}{h}\right)^2
$$

**寬微帶線**（$w/h \geq 1$）：

$$
F\left(\frac{w}{h}\right) = \left(1 + \frac{12h}{w}\right)^{-1/2}
$$

#### 物理意義

- $\dfrac{\varepsilon_r + 1}{2}$：「平均介電常數」——假設場均勻分佈於空氣與介質
- $\dfrac{\varepsilon_r - 1}{2} \cdot F(w/h)$：修正項——描述場集中於介質中的程度
- $F(w/h)$ 隨 $w/h$ 增大而增大（寬線場更集中在介質中）

### 5.2 特性阻抗 $Z_0$

自由空間波阻抗：

$$
\eta_0 = 120\pi \approx 376.991\ \Omega
$$

**窄微帶線**（$w/h \leq 1$）：

$$
Z_0 = \frac{\eta_0}{2\pi\sqrt{\varepsilon_{eff}}} \cdot \ln\left(\frac{8h}{w} + \frac{w}{4h}\right)
$$

**寬微帶線**（$w/h \geq 1$）：

$$
Z_0 = \frac{\eta_0}{\sqrt{\varepsilon_{eff}} \cdot \left[ \dfrac{w}{h} + 1.393 + 0.667 \cdot \ln\left(\dfrac{w}{h} + 1.444\right) \right]}
$$

### 5.3 極限行為驗證

| 極限 | $\varepsilon_{eff}$ | $Z_0$ | 驗證 |
|------|----------------------|-------|------|
| $w/h \rightarrow \infty$ | $\rightarrow \varepsilon_r$ | $\rightarrow \dfrac{\eta_0}{\sqrt{\varepsilon_r}} \cdot \dfrac{h}{w}$ | 平行板電容器公式 ✓ |
| $w/h \rightarrow 0$ | $\rightarrow \dfrac{\varepsilon_r + 1}{2}$ | $\rightarrow \dfrac{\eta_0}{2\pi\sqrt{\varepsilon_{eff}}} \ln\left(\dfrac{8h}{w}\right)$ | 圓柱導線近似 ✓ |

---

## 6. 導體厚度修正

當導體厚度 $t$ 不可忽略時（$t/h > 0.005$），需修正等效寬度。

### 6.1 原理

厚度增加了導體的「有效寬度」，因為邊緣場會繞過導體側面。

### 6.2 Wheeler 厚度修正公式

等效寬度：

$$
w_{\text{eff}} = w + \Delta w
$$

其中 $\Delta w$ 為寬度增量：

**寬線**（$w/h \geq 1/2\pi$）：

$$
\Delta w = \frac{t}{\pi} \cdot \left[ \ln\left(\frac{4\pi w}{t}\right) + 1 \right]
$$

**窄線**（$w/h \leq 1/2\pi$）：

$$
\Delta w = \frac{t}{\pi} \cdot \left[ \ln\left(\frac{2h}{t}\right) + 1 \right]
$$

### 6.3 修正後計算流程

1. 計算等效寬度 $w_{\text{eff}} = w + \Delta w$
2. 用 $w_{\text{eff}}$ 替代 $w$，代入 Hammerstad-Jensen 公式
3. 計算 $\varepsilon_{eff}(w_{\text{eff}}/h)$ 和 $Z_0(w_{\text{eff}}/h)$

> **注意**：厚度修正主要影響 $Z_0$，對 $\varepsilon_{eff}$ 影響較小。

---

## 7. 頻散效應預告（Level 3）

上述公式均為**準靜態**（$f \rightarrow 0$）結果。當頻率升高時：

- 有效介電常數變為頻率依賴：$\varepsilon_{eff}(f)$
- 當 $f \rightarrow \infty$，$\varepsilon_{eff}(f) \rightarrow \varepsilon_r$（所有場被「擠」入介質中）
- 特性阻抗隨頻率變化：$Z_0(f)$

### Kirschning-Jansen 頻散模型（1982）

$$
\varepsilon_{eff}(f) = \varepsilon_r - \frac{\varepsilon_r - \varepsilon_{eff}(0)}{1 + G(f/f_p)^2}
$$

其中 $f_p$ 為特徵頻率，$G$ 為與幾何相關的係數。

> 此為 **Level 3** 內容，將在後續章節詳細推導。

---

## 8. Python 實作

```python
import numpy as np

class MicrostripAnalytical:
    """
    Microstrip 傳輸線 Level 1 準靜態解析模型

    基於 Hammerstad-Jensen (1980) 公式，含 Wheeler 厚度修正
    """

    ETA_0 = 120 * np.pi  # 自由空間波阻抗 ≈ 376.991 Ω

    @classmethod
    def effective_dielectric_constant(cls, w_over_h: float, eps_r: float) -> float:
        """計算有效介電常數 ε_eff"""
        a = (eps_r + 1) / 2
        b = (eps_r - 1) / 2

        if w_over_h <= 1:
            F = (1 + 12 / w_over_h) ** (-0.5) + 0.04 * (1 - w_over_h) ** 2
        else:
            F = (1 + 12 / w_over_h) ** (-0.5)

        return a + b * F

    @classmethod
    def characteristic_impedance(cls, w_over_h: float, eps_eff: float) -> float:
        """計算特性阻抗 Z₀（假設零厚度）"""
        if w_over_h <= 1:
            Z0 = (cls.ETA_0 / (2 * np.pi * np.sqrt(eps_eff))) * \
                 np.log(8 / w_over_h + w_over_h / 4)
        else:
            Z0 = cls.ETA_0 / (np.sqrt(eps_eff) * \
                 (w_over_h + 1.393 + 0.667 * np.log(w_over_h + 1.444)))
        return Z0

    @classmethod
    def thickness_correction(cls, w: float, h: float, t: float) -> float:
        """Wheeler 厚度修正 — 計算等效寬度"""
        w_over_h = w / h
        if w_over_h >= 1 / (2 * np.pi):
            delta_w = (t / np.pi) * (np.log(4 * np.pi * w / t) + 1)
        else:
            delta_w = (t / np.pi) * (np.log(2 * h / t) + 1)
        return w + delta_w

    @classmethod
    def analyze(cls, w: float, h: float, t: float = 0, eps_r: float = 4.2) -> dict:
        """
        完整分析：計算 ε_eff 與 Z₀

        Parameters
        ----------
        w : float — 線寬 [mm] 或 [μm]
        h : float — 介質厚度 [mm] 或 [μm]
        t : float — 導體厚度 [mm] 或 [μm]，預設 0
        eps_r : float — 相對介電常數，預設 4.2 (FR-4)
        """
        w_eff = cls.thickness_correction(w, h, t) if t > 0 else w

        # 零厚度結果
        wh = w / h
        eps_eff = cls.effective_dielectric_constant(wh, eps_r)
        Z0 = cls.characteristic_impedance(wh, eps_eff)

        # 厚度修正結果
        wh_eff = w_eff / h
        eps_eff_corr = cls.effective_dielectric_constant(wh_eff, eps_r)
        Z0_corr = cls.characteristic_impedance(wh_eff, eps_eff_corr)

        return {
            'w_over_h': wh,
            'eps_eff': eps_eff,
            'Z0': Z0,
            'w_eff': w_eff,
            'eps_eff_corrected': eps_eff_corr,
            'Z0_corrected': Z0_corr,
            'delta_w': w_eff - w if t > 0 else 0
        }
```

---

## 9. 數值驗證

### 9.1 測試案例

| 案例 | $w$ [mm] | $h$ [mm] | $t$ [mm] | $\varepsilon_r$ | $w/h$ | $\varepsilon_{eff}$ | $Z_0$ [Ω] | $Z_{0,corr}$ [Ω] |
|------|----------|----------|----------|------------------|-------|----------------------|-----------|------------------|
| 50Ω 設計點 | 2.90 | 1.60 | 0.035 | 4.2 | 1.812 | 3.1796 | 52.95 | 52.02 |
| 窄線 | 0.30 | 0.20 | 0.018 | 4.2 | 1.500 | 3.1333 | 58.94 | 55.29 |
| 寬線 | 5.00 | 1.60 | 0.035 | 4.2 | 3.125 | 3.3273 | 37.36 | 36.88 |
| 零厚度對比 | 3.00 | 1.60 | 0.000 | 4.2 | 1.875 | 3.1882 | 51.90 | 51.90 |
| Rogers RO4350B | 0.60 | 0.20 | 0.018 | 3.66 | 3.000 | 2.9248 | 40.91 | 39.13 |

### 9.2 驗證結論

- **50Ω 設計點**：$w = 2.9\ 	ext{mm}, h = 1.6\ 	ext{mm}$ 時 $Z_0 \approx 52.95\ \Omega$（零厚度），修正後 $52.02\ \Omega$，與工程預期 $50\ \Omega$ 誤差 $< 6\%$
- **厚度修正效應**：窄線（$w/h \approx 1.5$）厚度修正影響較大（$\Delta Z_0 \approx -3.65\ \Omega$），寬線影響較小
- **極限行為**：$w/h \rightarrow \infty$ 時 $\varepsilon_{eff} \rightarrow \varepsilon_r$ 已驗證

### 9.3 視覺化驗證

<!---->

**圖 1（左上）**：特性阻抗 $Z_0$ vs 寬厚比 $w/h$，不同 $\varepsilon_r$  
**圖 2（右上）**：有效介電常數 $\varepsilon_{eff}$ vs 寬厚比 $w/h$  
**圖 3（左下）**：厚度修正對 $Z_0$ 的影響（FR-4, $h = 1.6\ 	ext{mm}$）  
**圖 4（右下）**：50Ω 設計曲線——線寬 vs 介質厚度

---

## 10. 參考文獻

1. **Wheeler, H. A.** (1965). "Transmission-line properties of parallel strips separated by a dielectric sheet." *IEEE Trans. Microwave Theory Tech.*, 13(2), 172-185.

2. **Hammerstad, E., & Jensen, O.** (1980). "Accurate models for microstrip computer-aided design." *IEEE MTT-S Int. Microwave Symp. Digest*, 407-409.

3. **Wadell, B. C.** (1991). *Transmission Line Design Handbook*. Artech House.

4. **IPC-2141A** (2004). "Controlled Impedance Circuit Boards and High Speed Logic Design."

5. **Kirschning, M., & Jensen, R. H.** (1982). "Accurate model for effective dielectric constant of microstrip with validity up to millimetre-wave frequencies." *Electronics Letters*, 18(6), 272-273.

6. **Mantaro** — Impedance Calculators: https://www.mantaro.com/resources/impedance-calculators.php

7. **Polar Instruments** — Speedstack PCB Layer Stackup Templates: https://www.polarinstruments.com/support/stackup/templates.html

---

> **下一章節預告**：Stripline（帶狀線）解析公式推導 — 從對稱結構的保角映射到 Wadell 公式
