import sys, os
base = os.path.join(os.path.dirname(__file__), "..", "三視圖")

def _load(name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, os.path.join(base, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_切換視圖():
    mod = _load("組合")
    fig = mod.切換視圖("FPC", "側")
    assert fig is not None

def test_繪製視圖():
    mod = _load("組合")
    d = mod.繪製視圖("Uleam1", ["前視圖", "上視圖"])
    assert set(d.keys()) == {"前視圖", "上視圖"}

def test_批次繪製():
    mod = _load("組合")
    b = mod.批次繪製(["CF3", "FPC"])
    assert "CF3" in b and "FPC" in b

def test_規格顏色():
    mod = _load("規格")
    assert mod.FPC_SPEC["conductor_color"].startswith("#")
    assert mod.ULEAM1_SPEC["conductor_color"] == "#8B9CAD"
