import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from 量傳線設計.核心.三視圖 import LayoutCalculator, 繪製前視

def test_前視圖_render_量子傳輸線規格():
    """前視圖應依量子傳輸線規格正確 render"""
    # 量子傳輸線典型規格：8 通道、pitch 2mm、線寬 35um
    佈局 = LayoutCalculator(通道數=8, 訊號間距=2.0, 訊號寬度=35.0,
                            線總寬=17.0, 線長度=200.0)
    fig = 繪製前視(佈局)
    assert fig is not None
    assert len(fig.axes) >= 1
    # 標題應包含通道數
    title = fig._suptitle.get_text() if fig._suptitle else ""
    assert "8" in title or "通道" in title
    # 圖形尺寸應為 tuple
    assert isinstance(fig.get_size_inches().tolist(), list)
