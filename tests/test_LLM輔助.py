import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

def test_LLM輔助_啟發式():
    from 量傳線設計.核心.LLM輔助 import 生成參數
    p = 生成參數("低串擾設計", "CF3")
    assert "w" in p and "s" in p
    assert p["s"] > 100
