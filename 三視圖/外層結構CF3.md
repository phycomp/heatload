  layer_labels = [ 'Ground Plane (Ag/NbTi)', 'Dielectric (Polyimide)' 'Signal Lines (x8)', 'Dielectric (Polyimide)', 'Ground Plane (Ag/NbTi)', ]
這正好是一個標準的對稱 Stripline（GSG）結構：
最上層：Ground Plane
上介電層：Polyimide
中間：Signal Lines
下介電層：Polyimide
最下層：Ground Plane
我需要繪制一個高質量的前視圖（橫截面），要求：
動態通道數（默認8，但可改）
以信號層爲中心對稱
每層有標注文字
工程圖風格，尺寸標注
展示 GSG 層叠結構
讓我設計代碼：
定義一個函數，接受 n_channels 參數
計算各層的位置（以信號層 y=0 爲中心對稱）
每層用不同顏色區分
標注文字放在左側或右側
添加尺寸標注線
層厚度分配（基于總厚度 0.3mm 的合理分配）：
Ground Plane: ~0.025 mm each
Dielectric (upper): ~0.1 mm
Signal Lines: ~0.05 mm (center)
Dielectric (lower): ~0.1 mm
Ground Plane: ~0.025 mm
總厚度 = 0.025 + 0.1 + 0.05 + 0.1 + 0.025 = 0.3 mm ✓
通道寬度：基于 2mm pitch，信號線寬度約 0.4mm
