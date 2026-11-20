"""三種傳輸線規格：CF3 / FPC / Uleam1。"""
from dataclasses import dataclass, field, asdict
from typing import Dict

@dataclass
class 傳輸線規格:
    名稱: str
    類型: str
    通道數: int = 8
    pitch_mm: float = 2.0
    寬度_mm: float = 17.0
    厚度_um: float = 300.0
    長度_mm: float = 200.0
    阻抗_ohm: float = 50.0
    頻率_GHz: str = "DC-18"
    備註: str = ""

CF3 = 傳輸線規格("CF3", "柔性Strip (CrioFlex)", 通道數=8, pitch_mm=2.0, 厚度_um=300, 備註="Delft CrioFlex 3")
FPC = 傳輸線規格("FPC", "柔性印刷電路", 通道數=16, pitch_mm=1.0, 厚度_um=200, 備註="FPC 高密度")
Uleam1 = 傳輸線規格("Uleam1", "超導 (NbTi/Ag)", 通道數=8, pitch_mm=2.0, 厚度_um=300, 阻抗_ohm=50, 備註="U-leam UF1")

def 全部規格() -> Dict[str, 傳輸線規格]:
    return {"CF3": CF3, "FPC": FPC, "Uleam1": Uleam1}

def 規格轉dict(spec: 傳輸線規格) -> dict:
    return asdict(spec)
