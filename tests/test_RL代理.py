import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

def test_RL環境建立():
    from 量傳線設計.核心.RL代理 import 建立環境
    env = 建立環境("CF3")
    assert env is not None
