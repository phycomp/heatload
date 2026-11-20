"""三視圖 - 前視圖（獨立繪製，可混合使用）。"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "量傳線", "src"))

from 規格 import 取得規格, CF3_SPEC
from matplotlib.pyplot import subplots, tight_layout
from matplotlib.patches import Rectangle


def _尺寸(spec):
    n_ch = spec["channels"]
    pitch = spec["pitch_mm"]
    w = spec["line_width_um"] / 1000.0
    h = spec["dielectric_thickness_mm"]
    t = spec["signal_thickness_um"] / 1000.0
    total_w = spec["total_width_mm"]
    total_h = 2 * h + 3 * t
    return n_ch, pitch, w, h, t, total_w, total_h


def 繪製層(spec):
    """繪製前視圖的層結構，回傳 (fig, ax)。"""
    n_ch, pitch, w, h, t, total_w, total_h = _尺寸(spec)
    fig, ax = subplots(figsize=(10, 7))
    y0, y1, y2, y3, y4 = 0, t, t + h, t + h + t, t + h + t + h
    cond = spec.get("conductor_color", "#FFD700")
    diel = spec.get("dielectric_color", "#C4956A")
    # 接地層 (底/頂)
    ax.add_patch(Rectangle((0, y0), total_w, t, facecolor="#8B9CAD", edgecolor="#4A5568"))
    ax.add_patch(Rectangle((0, y4), total_w, t, facecolor="#8B9CAD", edgecolor="#4A5568"))
    # 介電層
    ax.add_patch(Rectangle((0, y1), total_w, h, facecolor=diel, edgecolor="#744210"))
    ax.add_patch(Rectangle((0, y3), total_w, h, facecolor=diel, edgecolor="#744210"))
    # 訊號線
    for i in range(n_ch):
        x = i * pitch
        ax.add_patch(Rectangle((x, y2), w, t, facecolor=cond, edgecolor="#B8860B"))
    ax.set_xlim(-0.5, total_w + 0.5)
    ax.set_ylim(-0.1, total_h + 0.1)
    return fig, ax, (y0, y1, y2, y3, y4)


def 繪製標註(ax, spec, ys):
    """繪製標註文字。"""
    n_ch, pitch, w, h, t, total_w, total_h = _尺寸(spec)
    y0, y1, y2, y3, y4 = ys
    ax.set_title(f"前視圖 Front View ({spec.get('name','')})  {n_ch}ch  w={w*1000:.0f}μm  h={h*1000:.0f}μm",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Z (mm)")


def 繪製尺寸標註(ax, spec):
    """繪製尺寸標註。"""
    n_ch, pitch, w, h, t, total_w, total_h = _尺寸(spec)
    ax.annotate(f"pitch={pitch}mm", xy=(total_w / 2, -0.05), fontsize=8, ha="center")


def 繪製前視(spec=None):
    """繪製前視圖，回傳 matplotlib Figure。spec 可為 str/dict。"""
    spec = 取得規格(spec) if spec is not None else CF3_SPEC
    if isinstance(spec, str):
        spec = 取得規格(spec)
    fig, ax, ys = 繪製層(spec)
    繪製標註(ax, spec, ys)
    繪製尺寸標註(ax, spec)
    ax.grid(True, alpha=0.3)
    tight_layout()
    return fig


# 保留常數相容
from 規格 import CF3_SPEC

if __name__ == "__main__":
    fig = 繪製前視("CF3")
    fig.savefig(os.path.join(os.path.dirname(__file__), "前視圖.png"), dpi=150)
    print("已輸出 前視圖.png")
