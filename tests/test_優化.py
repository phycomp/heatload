import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

def test_評估設計_CF3():
    from 量傳線設計.核心.優化 import 評估設計
    params = {"w": 35, "s": 100, "h": 0.129, "t": 2, "pitch": 2.0}
    f1, f2 = 評估設計(params, "CF3")
    assert isinstance(f1, float)
    assert isinstance(f2, float)

def test_多目標優化_CF3():
    from 量傳線設計.核心.優化 import 多目標優化
    trials = 多目標優化("CF3", n_trials=5)
    assert len(trials) >= 1

def test_多目標優化_proxy():
    from 量傳線設計.核心.優化 import 多目標優化
    trials = 多目標優化("CF3", n_trials=5, use_proxy=True)
    assert len(trials) >= 1
