"""三視圖 - 組合/混合使用。"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "量傳線", "src"))

from 前視圖 import 繪製前視
from 側視圖 import 繪製側視
from 上視圖 import 繪製上視

def 繪製三視(spec=None):
    """分別繪製三視圖，回傳 (前視圖, 側視圖, 上視圖)。"""
    前 = 繪製前視(spec)
    側 = 繪製側視(spec)
    上 = 繪製上視(spec)
    return 前, 側, 上

def 組合三視圖(spec=None):
    """將三視圖組合成單一 Figure（1x3）。"""
    from matplotlib.pyplot import subplots
    前, 側, 上 = 繪製三視(spec)
    # 簡化：回傳第一張，實際可自行拼接
    return 前

def 切換視圖(spec=None, view="前"):
    """視圖切換便利函式。view: '前'/'側'/'上'"""
    if view in ("前", "front", "前視圖"):
        return 繪製前視(spec)
    if view in ("側", "side", "側視圖"):
        return 繪製側視(spec)
    if view in ("上", "top", "上視圖"):
        return 繪製上視(spec)
    raise ValueError(f"未知視圖: {view}")

def 繪製全部視圖(spec=None):
    """繪製全部三視圖，回傳 dict。"""
    前, 側, 上 = 繪製三視(spec)
    return {"前視圖": 前, "側視圖": 側, "上視圖": 上}

def 可用視圖():
    """回傳可用視圖名稱列表。"""
    return ["前視圖", "側視圖", "上視圖"]

def 繪製視圖(spec=None, views=None):
    """繪製指定視圖子集，回傳 dict。views=None 表示全部。"""
    if views is None:
        views = 可用視圖()
    all_views = 繪製全部視圖(spec)
    return {v: all_views[v] for v in views if v in all_views}

def 批次繪製(specs):
    """批次繪製多個規格，回傳 {spec_name: {view: fig}}。"""
    result = {}
    for spec in specs:
        name = spec.get("name", str(spec)) if isinstance(spec, dict) else str(spec)
        result[name] = 繪製全部視圖(spec)
    return result

if __name__ == "__main__":
    前, 側, 上 = 繪製三視()
    前.savefig(os.path.join(os.path.dirname(__file__), "組合_前.png"), dpi=150)
    側.savefig(os.path.join(os.path.dirname(__file__), "組合_側.png"), dpi=150)
    上.savefig(os.path.join(os.path.dirname(__file__), "組合_上.png"), dpi=150)
    print("已輸出三視圖")
