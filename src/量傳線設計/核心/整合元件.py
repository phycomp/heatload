"""整合元件：連接器、濾波器、熱沉等。"""
from dataclasses import dataclass
from typing import List

@dataclass
class 元件:
    名稱: str
    類型: str
    規格: str = ""
    數量: int = 1

def 預設元件清單() -> List[元件]:
    return [
        元件("SMA 連接器", "連接器", "DC-18GHz", 2),
        元件("低通濾波器", "濾波器", "fc=8GHz", 1),
        元件("熱沉銅塊", "熱管理", "4K stage", 1),
        元件("NbTi 超導線", "導體", "Tc=9.2K", 1),
    ]

def 元件表() -> list:
    return [ (c.名稱, c.類型, c.規格, c.數量) for c in 預設元件清單() ]
