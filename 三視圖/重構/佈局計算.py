LAYER_DEFS = [
    {'name': '保護層-底', 'thick_um': 15, 'material': 'Polyimide', 'color': '#E8D5C4', 'edge': '#A0522D', 'is_signal': False},
    {'name': '接地層-底', 'thick_um': 5, 'material': 'Ag/NbTi', 'color': '#8B9CAD', 'edge': '#4A5568', 'is_signal': False},
    {'name': '介電層-下', 'thick_um': 129, 'material': 'Polyimide', 'color': '#C4956A', 'edge': '#744210', 'is_signal': False},
    {'name': '訊號線', 'thick_um': 2, 'material': 'Ag/NbTi', 'color': '#FFD700', 'edge': '#B8860B', 'is_signal': True},
    {'name': '介電層-上', 'thick_um': 129, 'material': 'Polyimide', 'color': '#C4956A', 'edge': '#744210', 'is_signal': False},
    {'name': '接地層-上', 'thick_um': 5, 'material': 'Ag/NbTi', 'color': '#8B9CAD', 'edge': '#4A5568', 'is_signal': False},
    {'name': '保護層-上', 'thick_um': 15, 'material': 'Polyimide', 'color': '#E8D5C4', 'edge': '#A0522D', 'is_signal': False},
]

# ============================================================
# 2. 佈局計算器 - 優化字型大小
# ============================================================

class LayoutCalculator:
    """佈局計算器 - 確保文字清晰可讀"""

    def __init__(self, 通道數:int=8, 訊號間距:float=2, 訊號寬度:float=.035, 線總寬:float=17., 線長度:float=200, 訊號厚度:float=2., 鈦比例:float=53., 字型縮放:float=1.):
        self.層位置, self.線厚度μ = 各層位置(LAYER_DEFS)  # 計算層位置
        # _, self.線厚度μ = 各層位置(LAYER_DEFS)  # 計算層位置
        self.通道數 = 通道數
        self.線總寬=線總寬
        self.線長度 = 線長度
        self.線厚度m = self.線厚度μ / 1000

        self.訊號間距 = 訊號間距
        self.訊號寬度 = 訊號寬度/1000.
        self.訊號厚度 = 訊號厚度
        self.邊緣=(self.線總寬-self.訊號間距*(self.通道數-1)-self.訊號寬度)/2.  # 計算總寬度
        self.字型縮放 = 字型縮放
        self.鈮鈦比例=f'{100-鈦比例:.0f}:{鈦比例:.0f}'
        self.長寬高=f'{self.線長度}x{self.線總寬:.0f}x{self.線厚度m:.1f}'
        print(['長寬高', self.長寬高])
        # print(self.鈮鈦比例)

        # 計算字型大小 - 確保最小可讀尺寸
        self._calculate_font_sizes()

        # 計算佈局邊距
        self._calculate_margins()

        # 計算圖形尺寸
        self._calculate_figure_size()

        # 計算標註位置
        self._calculate_label_positions()

    def _calculate_font_sizes(self):
        """計算字型大小 - 確保清晰可讀"""

        # 1. 基礎字型 (根據通道數和總寬度)
        # 確保最小字型不小於8pt
        if self.通道數 <= 4:
            base = 14
        elif self.通道數 <= 8:
            base = 13
        elif self.通道數 <= 12:
            base = 12
        else:
            base = 11

        # 根據總寬度調整
        if self.線總寬 > 20:
            base = max(10, base - 1)
        elif self.線總寬 < 5:
            base = min(16, base + 1)

        # 應用縮放，確保最小字型
        self.base_font_size = max(10, base * self.字型縮放)

        # 2. 各層字型 (根據層間距)
        centers = [p['center_mm'] for p in self.層位置]
        self.layer_font_sizes = []

        for i in range(len(centers)):
            # 計算與相鄰層的最小間距 (mm)
            if i == 0:
                spacing = centers[i+1] - centers[i]
            elif i == len(centers) - 1:
                spacing = centers[i] - centers[i-1]
            else:
                spacing = min(centers[i] - centers[i-1], centers[i+1] - centers[i])

            # 根據間距調整 (間距單位mm)
            if spacing < 0.03:      # < 30um
                ratio = 0.65
            elif spacing < 0.05:    # < 50um
                ratio = 0.75
            elif spacing < 0.07:    # < 70um
                ratio = 0.82
            elif spacing < 0.10:    # < 100um
                ratio = 0.90
            elif spacing < 0.13:    # < 130um
                ratio = 0.95
            else:
                ratio = 1.0

            fs = self.base_font_size * ratio

            # 邊緣層稍大
            if i == 0 or i == len(centers) - 1:
                fs = min(self.base_font_size * 1.1, fs * 1.05)

            # 確保最小字型
            fs = max(8 * self.字型縮放, fs)
            fs = min(16 * self.字型縮放, fs)
            self.layer_font_sizes.append(fs)

    def _calculate_margins(self):
        """計算邊距 - 基於字型大小"""
        fs = self.字型縮放
        self.margins = {
            'left': max(2.0, 1.0 * fs),
            'right': max(3.5, 1.8 * fs),
            'top': max(0.5, 0.3 * fs),
            'bottom': max(1.5, 1.0 * fs),
        }

    def _calculate_figure_size(self):
        """計算圖形尺寸"""
        total_w = self.線總寬
        total_h = self.線厚度m
        margins = self.margins

        # 寬度: 總寬度 + 左右邊距 + 標註空間
        fig_width = total_w + margins['left'] + margins['right'] + 5 * self.字型縮放

        # 高度: 總高度 + 上下邊距 + Pitch標註空間
        fig_height = total_h + margins['top'] + margins['bottom'] + 2 * self.字型縮放

        # 確保最小尺寸
        fig_width = max(12, fig_width)
        fig_height = max(6, fig_height)

        self.figure_size = (fig_width, fig_height)

    def _calculate_label_positions(self):
        """計算標註位置 - 避免重疊"""
        total_w = self.線總寬
        total_h = self.線厚度m
        fs = self.字型縮放

        # 1. 層標註位置 (左側)
        self.layer_label_x = -total_w/2 - self.margins['left'] + 0.8

        # 2. 厚度標註位置 (右側)
        self.thick_label_x = total_w/2 + 2.5 * fs

        # 3. Pitch標註位置 (底部)
        self.pitch_y = -0.08 * fs

        # 4. 總厚度標註位置 (右側偏上)
        self.total_thick_x = total_w/2 + 4.5 * fs
        self.total_thick_y = 0

        # 5. 總寬度標註位置 (底部)
        self.total_width_y = -0.2 * fs

        # 6. Signal Center標註
        self.signal_center_x = total_w/2 + 0.5

    def get_font_size(self, category: str):
        """獲取各類別字型大小 - 確保清晰"""
        sizes = {
            'title': max(14, self.base_font_size * 1.3),
            'label': max(11, self.base_font_size),
            'annotation': max(9, self.base_font_size * 0.85),
            'pitch': max(10, self.base_font_size * 0.95),
            'layer': self.layer_font_sizes,
        }
        return sizes.get(category, self.base_font_size)

def 各層位置(layer_defs):
    """計算各層位置 (單位: mm)"""
    positions = []
    線厚度μ = sum(l['thick_um'] for l in layer_defs)

    signal_idx = next(i for i, l in enumerate(layer_defs) if l['is_signal'])
    signal_thick_um = layer_defs[signal_idx]['thick_um']

    center_from_bottom = sum(l['thick_um'] for l in layer_defs[:signal_idx]) + signal_thick_um/2

    cum_um = -center_from_bottom
    for layer in layer_defs:
        thick_um = layer['thick_um']
        y_bot_um = cum_um
        y_top_um = cum_um + thick_um
        positions.append({
            'y_bot_um': y_bot_um,
            'y_top_um': y_top_um,
            'y_bot_mm': y_bot_um / 1000,
            'y_top_mm': y_top_um / 1000,
            'center_mm': (y_bot_um + thick_um/2) / 1000,
            'thick_mm': thick_um / 1000,
            'thick_um': thick_um
        })
        cum_um += thick_um

    return positions, 線厚度μ
