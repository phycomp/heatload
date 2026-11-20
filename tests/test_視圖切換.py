import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from 量傳線設計.核心.三視圖 import LayoutCalculator, 切換視圖, 繪製全部視圖

def test_切換視圖():
    佈局 = LayoutCalculator(通道數=8)
    for v in ["前", "側", "上"]:
        fig = 切換視圖(佈局, v, conductor_color="#FF00FF")
        assert fig is not None

def test_繪製全部視圖():
    佈局 = LayoutCalculator(通道數=8)
    d = 繪製全部視圖(佈局, conductor_color="#00FF00", dielectric_color="#0000FF")
    assert set(d.keys()) == {"前視圖", "側視圖", "上視圖"}
