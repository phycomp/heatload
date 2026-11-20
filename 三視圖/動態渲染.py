# ============================================================
# 動態字型管理器
# ============================================================

class 動態渲染:
    """動態字型管理器 - 支援全局縮放和層間距調整"""

    def __init__(self, scale_factor: float = 1.0):
        self.scale_factor = scale_factor
        self.base_font_size = 12
        self.layer_font_sizes = []
        self.title_font_size = 14
        self.label_font_size = 12
        self.annotation_font_size = 9
        self.pitch_font_size = 10

    def set_scale_factor(self, scale: float):
        """設定全局縮放因子"""
        self.scale_factor = max(0.5, min(2.0, scale))

    def calculate_layer_font_sizes(self, layer_positions: list, n_layers: int,
                                   min_spacing: float = None) -> list:
        """根據層間距計算每層字型大小"""
        font_sizes = []

        # 計算層間距
        if min_spacing is None:
            min_spacing = float('inf')
            for i in range(len(layer_positions) - 1):
                spacing = layer_positions[i+1] - layer_positions[i]
                if spacing < min_spacing:
                    min_spacing = spacing

        base_size = self.base_font_size * self.scale_factor

        for i, pos in enumerate(layer_positions):
            # 計算該層與相鄰層的最小間距
            if i == 0:
                spacing = layer_positions[i+1] - layer_positions[i]
            elif i == len(layer_positions) - 1:
                spacing = layer_positions[i] - layer_positions[i-1]
            else:
                spacing = min(layer_positions[i] - layer_positions[i-1],
                             layer_positions[i+1] - layer_positions[i])

            # 根據間距動態調整字型
            if spacing < 0.03:  # < 30um
                font_size = base_size * 0.55
            elif spacing < 0.05:  # < 50um
                font_size = base_size * 0.65
            elif spacing < 0.07:  # < 70um
                font_size = base_size * 0.75
            elif spacing < 0.10:  # < 100um
                font_size = base_size * 0.85
            elif spacing < 0.13:  # < 130um
                font_size = base_size * 0.95
            else:
                font_size = base_size

            # 邊緣層可稍大
            if i == 0 or i == len(layer_positions) - 1:
                font_size = min(base_size, font_size * 1.1)

            # 限制範圍
            font_size = max(6 * self.scale_factor, min(14 * self.scale_factor, font_size))
            font_sizes.append(font_size)

        # 層數多時整體縮小
        if n_layers > 6:
            font_sizes = [max(6 * self.scale_factor, fs * 0.9) for fs in font_sizes]

        self.layer_font_sizes = font_sizes
        return font_sizes

    def get_title_font_size(self) -> float:
        """獲取標題字型大小"""
        return self.title_font_size * self.scale_factor

    def get_label_font_size(self) -> float:
        """獲取標籤字型大小"""
        return self.label_font_size * self.scale_factor

    def get_annotation_font_size(self) -> float:
        """獲取註解字型大小"""
        return max(6, self.annotation_font_size * self.scale_factor)

    def get_pitch_font_size(self) -> float:
        """獲取Pitch標註字型大小"""
        return max(7, self.pitch_font_size * self.scale_factor)

    def get_layer_font_size(self, layer_index: int) -> float:
        """獲取特定層字型大小"""
        if layer_index < len(self.layer_font_sizes):
            return self.layer_font_sizes[layer_index]
        return self.base_font_size * self.scale_factor
