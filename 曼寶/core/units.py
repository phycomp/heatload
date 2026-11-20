# core/units.py
UM_PER_MIL = 25.4
UM_PER_MM = 1000.0

UNIT_TO_UM = {
    "mil": UM_PER_MIL,
    "um": 1.0,
    "µm": 1.0,
    "mm": UM_PER_MM,
}

def to_um(value: float, unit: str) -> float:
    return value * UNIT_TO_UM[unit]

def from_um(value_um: float, unit: str) -> float:
    return value_um / UNIT_TO_UM[unit]
