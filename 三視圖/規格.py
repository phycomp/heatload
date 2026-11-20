"""三視圖共用規格定義。"""
CF3_SPEC = {
    "name": "CF3",
    "channels": 8,
    "pitch_mm": 2.0,
    "line_width_um": 35.0,
    "total_width_mm": 17.0,
    "length_mm": 200.0,
    "dielectric_thickness_mm": 0.129,
    "signal_thickness_um": 2.0,
    "conductor_color": "#FFD700",
    "dielectric_color": "#C4956A",
}

FPC_SPEC = {
    "name": "FPC",
    "channels": 16,
    "pitch_mm": 1.0,
    "line_width_um": 65.0,
    "total_width_mm": 17.0,
    "length_mm": 200.0,
    "dielectric_thickness_mm": 0.10,
    "signal_thickness_um": 0.2,
    "conductor_color": "#C0C0C0",
    "dielectric_color": "#D4A574",
}

ULEAM1_SPEC = {
    "name": "Uleam1",
    "channels": 8,
    "pitch_mm": 2.0,
    "line_width_um": 35.0,
    "total_width_mm": 17.0,
    "length_mm": 200.0,
    "dielectric_thickness_mm": 0.129,
    "signal_thickness_um": 2.0,
    "conductor_color": "#8B9CAD",  # NbTi 灰藍
    "dielectric_color": "#C4956A",
}

SPECS = {"CF3": CF3_SPEC, "FPC": FPC_SPEC, "Uleam1": ULEAM1_SPEC}

def 取得規格(name_or_spec):
    if isinstance(name_or_spec, str):
        base = SPECS.get(name_or_spec, CF3_SPEC).copy()
        return base
    if isinstance(name_or_spec, dict):
        merged = CF3_SPEC.copy()
        merged.update(name_or_spec)
        return merged
    # 嘗試從 傳輸線規格 模組轉換
    try:
        from 量傳線設計.核心.傳輸線規格 import 全部規格
        specs = 全部規格()
        if isinstance(name_or_spec, str) and name_or_spec in specs:
            s = specs[name_or_spec]
            base = CF3_SPEC.copy()
            base["name"] = s.名稱
            base["channels"] = s.通道數
            base["pitch_mm"] = s.pitch_mm
            base["total_width_mm"] = s.寬度_mm
            base["length_mm"] = s.長度_mm
            return base
    except Exception:
        pass
    return CF3_SPEC
