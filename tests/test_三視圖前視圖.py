import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def test_三視圖前視圖_繪製():
    import importlib.util
    spec = importlib.util.spec_from_file_location("前視圖", os.path.join(os.path.dirname(__file__), "..", "三視圖", "前視圖.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fig = mod.繪製前視()
    assert fig is not None
    assert len(fig.axes) >= 1

def test_三視圖前視圖_CF3規格():
    import importlib.util
    spec = importlib.util.spec_from_file_location("前視圖", os.path.join(os.path.dirname(__file__), "..", "三視圖", "前視圖.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fig = mod.繪製前視(mod.CF3_SPEC)
    assert fig is not None
