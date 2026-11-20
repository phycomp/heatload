from dataclasses import dataclass
@dataclass
class StriplineGeometry:
    """Stripline 幾何參數"""
    w: float        # 信號線寬度 (mm)
    t: float        # 信號線厚度 (μm)
    h: float        # 介電層厚度 (mm) 上下各一層
    s: float        # 通道間距 pitch (mm)
    L: float        # 傳輸線長度 (mm)
    n_channels: int # 通道數

@dataclass
class ThermalBoundary:
    """熱邊界條件"""
    T_hot: float    # 熱端溫度 (K)
    T_cold: float   # 冷端溫度 (K)
    stage: str      # 溫度階段標識

@dataclass
class MaterialStack:
    """多層膜結構"""
    layers: List[Dict]  # [{"material": str, "thickness": float, "width": float}]
