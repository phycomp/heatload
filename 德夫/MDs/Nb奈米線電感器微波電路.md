我已成功獲取論文內容。這篇論文是關於**可調諧超導納米電感器**的研究。讓我為您整理摘要並推導其中的核心物理公式。

## 📄 論文摘要

**標題：** Tunable superconducting nanoinductors（可調諧超導納米電感器）

**作者：** Anthony J Annunziata, Daniel F Santavicca, Luigi Frunzio 等（耶魯大學）

**摘要：**
本研究表徵了由超薄鈮（Nb）和氮化鈮（NbN）製成的納米線電感器（寬度約100 nm）。這些納米線在超導態下具有很大的**動態電感（kinetic inductance）**。動態電感與納米線長度呈線性關係，在2.5 K溫度下，NbN的典型值為 **1 nH/µm**，Nb為 **44 pH/µm**。研究測量了動態電感的溫度和電流依賴性，並與理論預測進行比較。這些納米線電感元件可應用於多種微波頻率超導電路，包括光子探測器、超材料、低損耗緊湊濾波器和量子比特。

## 🔬 核心物理公式推導

### 1. 動態電感的基本定義

動態電感 $L_K$ 源於載流子的動能，而非磁場能量。通過將庫珀對的總動能與等效電感能量相等：

$$n_s (lwd) \cdot m v^2 = \frac{1}{2} L_K I^2$$

其中：

- $n_s$：庫珀對密度
- $l, w, d$：納米線的長度、寬度、厚度
- $m$：庫珀對質量（$2m_e$）
- $v$：庫珀對平均速度
- $I$：超導電流

推導得到**動態電感基本公式**：

$${L_K = \frac{m}{2n_s e^2} \cdot \frac{l}{wd}}$$

### 2. Ginzburg-Landau（GL）理論 - 溫度依賴性

在GL理論中，庫珀對密度隨溫度變化：
$$n_s(T) \approx n_s(0)\left(1 - \frac{T}{T_c}\right)$$

代入基本公式，得到**溫度依賴的動態電感**：

$${L_K(T) = L_K(0) \cdot \frac{1}{1 - T/T_c}} \tag{1}$$

這適用於 $T \approx T_c$ 且電流較小的情況。

用GL磁穿透深度 $\lambda(T)$ 表示（其中 $\lambda^2(T) = \frac{m}{2\mu_0 n_s(T) e^2}$）：

$${L_K(T) = \mu_0 \lambda^2(T) \cdot \frac{l}{wd}} \tag{2}$$

### 3. GL理論 - 電流依賴性

庫珀對密度和電流可用相位梯度 $k$ 和相干長度 $\xi$ 表示：

$$L_K(k\xi) \approx L_K(0) \cdot \frac{1}{1 - 3k^2\xi^2}$$

$$\frac{I}{I_c} \approx k\xi - \frac{1}{3}(k\xi)^3 \tag{4}$$

通過數值求解這組方程，可得到 $L_K(I/I_c)$ 的關係。

### 4. BCS理論 - 更精確的溫度依賴性

在低频极限（$hf \ll k_B T$）下，使用Mattis-Bardeen複電導率公式：

$$\frac{\sigma_2}{\sigma_n} = \frac{\pi\Delta}{hf} \tanh\left(\frac{\Delta}{2k_B T}\right) \tag{5}$$

由於阻抗的虛部來自動態電感，推導出：

$${L_K = \left(\frac{l}{w}\right) \frac{R_{sq}}{2\pi^2 \Delta} \cdot \frac{1}{\tanh\left(\frac{\Delta}{2k_B T}\right)}} \tag{6}$$

其中：

- $R_{sq}$：正常態的薄層電阻
- $\Delta = \Delta(T)$：溫度依賴的超導能隙

**極限情況：**

- 當 $T \ll T_c$：使用 $\Delta(0) \approx 1.76 k_B T_c$
- 當 $T \approx T_c$：使用 $\Delta(T) \approx \Delta(0) \cdot 1.74\sqrt{1 - T/T_c}$

### 5. BCS理論 - 零溫下的電流依賴性

在零溫極限下：

$$\frac{L_K(I)}{L_K(0)} = \frac{\Delta_{00}}{\Delta(I)} \tag{7}$$

在**髒極限**（平均自由程 $\ll$ 相干長度）下，能隙和電流密度與相位梯度 $\zeta = Dk^2/(2\Delta)$ 的關係：

$$\Delta = \Delta_{00} e^{-\pi\zeta/4} \tag{8}$$

$$j = 2eN(0)Dk\Delta \left(\frac{\pi}{2} - \frac{2\zeta}{3}\right) \tag{9}$$

**臨界電流密度**（當 $\zeta = 0.300$ 時達到最大值）：

$${j_c = 1.491 \cdot eN(0)D\Delta_{00}^2} \tag{10}$$

電流比與 $\zeta$ 的關係：

$$\frac{I}{I_c} = 1.897 \cdot e^{-3\pi\zeta/8} \cdot \zeta \left(\frac{\pi}{2} - \frac{2\zeta}{3}\right) \tag{11}$$

**重要結果**：當 $I$ 接近 $I_c$ 時，$L_K(I)$ 達到最大值 $1.266 \cdot L_K(I=0)$。

### 6. 共振頻率測量公式

實驗中將納米線與電容 $C_0$ 並聯形成LC共振電路，通過測量共振頻率 $f_0$ 來確定電感：

$${f_0 = \frac{1}{2\pi\sqrt{L_K C_0}}} \tag{12}$$

由此可解出：
$$L_K = \frac{1}{(2\pi f_0)^2 C_0}$$

## 📊 實驗結果摘要

| 參數 | Nb納米線 | NbN納米線 |
|---|---|---|
| 寬度 $w$ | 100 nm | 130 nm |
| 電感密度 | 44 pH/µm | 1 nH/µm |
| 臨界溫度 $T_c$ | ~6.3 K | ~10 K |
| 自共振頻率 | ~56 GHz | ~37 GHz |

這篇論文為超導量子電路中的緊湊型高電感元件提供了完整的理論框架和實驗驗證，對於量子計算和超導微波電路設計具有重要意義。
