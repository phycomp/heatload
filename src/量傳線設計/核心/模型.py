"""共用資料模型（dataclasses）— 全功能共用的設計參數。"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class 層定義:
    名稱: str
    厚度_um: float
    材料: str
    顏色: str = "#CCCCCC"
    邊色: str = "#000000"
    是否訊號: bool = False


@dataclass
class 幾何參數:
    通道數: int = 8
    訊號間距_mm: float = 2.0
    訊號寬度_um: float = 35.0
    線總寬_mm: float = 17.0
    線長度_mm: float = 200.0
    訊號厚度_um: float = 2.0
    鈦比例: float = 53.0


@dataclass
class 熱邊界:
    熱端溫度_K: float = 300.0
    冷端溫度_K: float = 0.01
    階段: str = "50K"


@dataclass
class 材料堆疊:
    層: List[Dict] = field(default_factory=list)


@dataclass
class 設計結果:
    幾何: 幾何參數 = field(default_factory=幾何參數)
    備註: str = ""
    圖紙: Optional[bytes] = None
    規格表: Optional[object] = None
