import sys, os
base = os.path.join(os.path.dirname(__file__), "..", "三視圖")

def _load(name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, os.path.join(base, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_前視圖():
    mod = _load("前視圖")
    fig = mod.繪製前視()
    assert fig is not None

def test_側視圖():
    mod = _load("側視圖")
    fig = mod.繪製側視()
    assert fig is not None

def test_上視圖():
    mod = _load("上視圖")
    fig = mod.繪製上視()
    assert fig is not None

def test_組合():
    mod = _load("組合")
    前, 側, 上 = mod.繪製三視()
    assert 前 is not None and 側 is not None and 上 is not None
