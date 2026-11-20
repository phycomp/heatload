---
documentclass: article
geometry:
  - top=1.2cm
  - bottom=1.2cm
  - left=1.2cm
  - right=1.2cm
fontsize: 9pt
linestretch: 1.0
header-includes: |
  \usepackage{fvextra}
  \DefineVerbatimEnvironment{Highlighting}{Verbatim}{
    breaklines,
    breaksymbolleft={},
    commandchars=\\\{\}
  }
---
### 關於 NbTi 薄膜在聚醯亞胺（PI）基板上的沉積參數與微波損耗特性，以下是基於現有研究的詳細說明：

## 1. NbTi 薄膜沉積參數
在 PI（如 Kapton）這類柔性基板上沉積 NbTi，通常採用直流（DC）或射頻（RF）磁控共濺鍍技術。為了避免 PI 基板因高溫變形或釋放氣體，工藝通常維持在室溫下進行。 [1]

* 濺鍍功率 分靶共濺鍍 若使用獨立的 Nb 和 Ti 靶材，典型功率設定為 Nb (100 W) 與 Ti (100 W)，以獲得約 50:50 的原子比。
   * 合金靶材：若直接使用 NbTi 合金靶（如 50at% Nb - 50at% Ti），RF 功率通常設定在 70 W 左右。
* 工作氣壓與氣體 背景真空度：需達到 $2.6 \times 10^{-5}$ Pa 以下，以減少氧污染對超導溫度的影響。
   * 工作氣壓：通常使用高純度氬氣（Ar），氣壓維持在 0.4 Pa 至 1.0 Pa 之間。氣壓過高會導致薄膜結構疏鬆，影響臨界電流密度。
* 沉積速率與厚度 典型速率約為 10 nm/min。常見應用厚度為 150 nm 至 300 nm，此厚度範圍內薄膜能維持良好的連續性與超導性能。 [1, 2]

## 2. 極低溫下的微波損耗特性
NbTi 具有高臨界磁場（約 15 T）與適中的 $T_c$（~9.2 K），使其成為微波組件（如諧振器、傳輸線）的理想選擇。 [3]

* 低介電損耗：聚醯亞胺基板在極低溫（如 20 mK）下的介電損耗角正切（Loss Tangent）會顯著下降，僅為室溫下的 1/100，低至 $2.2 \times 10^{-5}$。這使得長距離（米級）的微波訊號傳輸成為可能。
* 高品質因子 (Q) 在 3 K 溫度下，工作頻率約為 6.8 GHz 的 NbTi 諧振器可以達到 Q > 10,000 的表現。
   * 薄膜厚度會影響動態電感（Kinetic Inductance），進而影響微波響應；較薄的薄膜（如 20 nm）雖然靈敏度高，但負載品質因子（$Q_L$）會因損耗增加而下降。
* 表面電阻與導體損耗 NbTi 基傳輸線在 4.2 K 下的插入損耗遠低於傳統銅（Cu）導線（<0.02 dB/cm vs 0.57 dB/cm）。
   * 注意介面層：若為了增加附著力而加入 Ti 底層或 Cu 保護層，會形成超導/正常金屬雙層結構，這會因鄰近效應增加表面電阻，進而提升微波損耗。 [4, 5, 6, 7, 8]

您是否正在規劃特定頻率（如 L-band 或 X-band）的元件設計，或需要針對微波共面波導 (CPW) 的阻抗匹配參數進行計算？

1. [https://iopscience.iop.org](https://iopscience.iop.org/article/10.1088/1402-4896/ad4690)
2. [https://www.nature.com](https://www.nature.com/articles/s41598-018-33442-7)
3. [https://infoscience.epfl.ch](https://infoscience.epfl.ch/server/api/core/bitstreams/1eb0c815-5df2-48f4-b3c2-ee339323d40c/content)
4. [https://www.researchgate.net](https://www.researchgate.net/publication/306116020_Cryogenic_microwave_characterization_of_Kapton_polyimide_using_superconducting_resonators)
5. [https://iopscience.iop.org](https://iopscience.iop.org/article/10.1088/0953-2048/29/8/084007)
6. [https://www.sciencedirect.com](https://www.sciencedirect.com/science/article/pii/S2590007223000333)
7. [https://arxiv.org](https://arxiv.org/pdf/2503.20416)
8. [https://www.researchgate.net](https://www.researchgate.net/publication/306116020_Cryogenic_microwave_characterization_of_Kapton_polyimide_using_superconducting_resonators)