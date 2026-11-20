## 一、CF3 規格電性與熱負載的物理推導

### 1.1 特性阻抗的物理推導

CF3 採用**帶狀線（Stripline）**結構，中心導體帶夾在兩接地平面之間的介電材料中。其特性阻抗 $Z_0$ 在 TEM 模態下由單位長度電感 $L$ 與電容 $C$ 決定：

$$
Z_0 = \sqrt{\frac{L}{C}}
$$

對於中心導體厚度 $t$ 不可忽略的帶狀線，Wheeler 給出了高精度近似公式：

$$
Z_0\sqrt{\varepsilon_r} = 30 \ln\left[1 + \frac{4}{\pi}\frac{b-t}{W}\left\{\frac{8}{\pi}\frac{b-t}{W} + \sqrt{\left(\frac{8}{\pi}\frac{b-t}{W}\right)^2 + 6.27}\right\}\right]
$$

其中 $b$ 為兩接地平面間距，$W$ 為中心導體寬度，$\varepsilon_r$ 為介電常數（Polyimide 約 3.3）。CF3 設計目標為 $Z_0 = 50\,\Omega$，這是透過精確控制 $W/b$ 比例來達成的。

### 1.2 傳播延遲的物理推導

傳播延遲由相位速度決定。對於 TEM 模態的帶狀線，相位速度為：

$$
v_p = \frac{c_0}{\sqrt{\varepsilon_r}}
$$

因此單位長度傳播延遲為：

$$
t_{pd} = \frac{1}{v_p} = \frac{\sqrt{\varepsilon_r}}{c_0}
$$

代入 Polyimide 的 $\varepsilon_r \approx 3.3$ 與 $c_0 = 3\times10^8$ m/s：

$$
t_{pd} = \frac{\sqrt{3.3}}{3\times10^8} \approx 5.6 \text{ ns/m}
$$

這解釋了 CF3 規格中傳播延遲約 5.6 ns/m 的來源。

### 1.3 衰減的物理推導

帶狀線的總衰減 $\alpha$ 由導體衰減 $\alpha_c$ 與介電衰減 $\alpha_d$ 組成：

$$
\alpha = \alpha_c + \alpha_d
$$

**介電衰減**來自介電材料的損耗正切 $\tan\delta$。對於 TEM 波，介電衰減為：

$$
\alpha_d = \frac{\pi\sqrt{\varepsilon_r}}{\lambda} \tan\delta \quad \text{(Np/m)}
$$

轉換為 dB/m 後：$\alpha_d \propto f \cdot \tan\delta$。這意味著介電衰減與頻率成正比。

**導體衰減**來自導體的表面電阻。當頻率升高時，電流集中在導體表面，集膚深度 $\delta_s$ 減小：

$$
\delta_s = \sqrt{\frac{\rho}{\pi f \mu_0}}
$$

表面電阻 $R_s = \rho/\delta_s \propto \sqrt{f}$，因此導體衰減 $\alpha_c \propto \sqrt{f}$。

CF3 的衰減數據（4 K 下：2 GHz=2 dB/m，6 GHz=5 dB/m，12 GHz=9 dB/m，18 GHz=16 dB/m） 反映了這種頻率依賴性。Ag 平台使用銀作為導體，銀在低溫下的電阻率極低（RRR > 100 時約 0.3 nΩ·m），因此導體損耗很小。CF3 的衰減主要由介電損耗貢獻，這也解釋了為何衰減大致與頻率線性相關。

### 1.4 熱負載的物理推導

CF3 規格中的熱負載數據為：

| 階段 | 溫差 ΔT | 長度 | 熱負載/通道 |
|------|---------|------|-------------|
| 4–40 K | 36 K | 0.4 m | < 125 μW |
| 10–350 mK | 340 mK | 0.2 m | ~ 20 nW |

**第一階段（4–40 K）**：熱負載主要由**電子熱傳導**貢獻。對於金屬導體，熱傳導遵循 Wiedemann-Franz 定律：

$$
\kappa = \frac{L_0 T}{\rho}
$$

其中 $L_0 = 2.44\times10^{-8}$ WΩ/K² 為洛倫兹數，$T$ 為溫度，$\rho$ 為電阻率。銀在低溫下電阻率極低（RRR > 100），因此熱導率雖高，但由於截面積非常小（訊號線厚度僅微米級），總熱傳導被大幅限制。此外，Polyimide 介電層的熱導率很低（約 0.12 W/m·K @ 300 K），進一步限制了熱洩漏。

熱負載 $Q$ 的估算：

$$
Q \approx \frac{\kappa A}{L} \Delta T
$$

其中 $A$ 為導體截面積，$L$ 為長度，$\Delta T$ 為溫差。CF3 的 Ag 線路每通道在 4–40 K、0.4 m 長度下熱負載 < 125 μW，反映了極小的截面積與銀的優異低溫性能。

**第二階段（10–350 mK）**：熱負載降至 nW 級別。這是由於：(1) 溫度極低時，金屬的熱導率進一步下降（電子-聲子散射減弱）；(2) 在 mK 溫度下，Polyimide 的熱導率極低；(3) 超導 NbTi 平台在 Tc = 9.8 K 以下進入超導態，電子熱傳導急劇降低。Delft Circuits 聲稱 NbTi 平台比 Ag 平台熱負載低 10 倍，這正是超導態的優勢。

