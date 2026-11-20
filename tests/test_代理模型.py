import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

def test_代理模型訓練預測():
    from 量傳線設計.核心.代理模型 import 生成訓練資料, 訓練代理模型, 預測
    samples = 生成訓練資料("CF3", n=10)
    if len(samples) < 5:
        return
    model = 訓練代理模型(samples)
    params = samples[0][0]
    f1, f2 = 預測(model, params)
    assert isinstance(f1, float)
    assert isinstance(f2, float)
