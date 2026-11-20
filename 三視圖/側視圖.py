"""三視圖 - 側視圖（獨立繪製，可混合使用）。"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "量傳線", "src"))

from 規格 import 取得規格
from matplotlib.pyplot import subplots, tight_layout
from matplotlib.patches import Rectangle


def _尺寸(spec):
    n_ch = spec["channels"]
    pitch = spec["pitch_mm"]
    w = spec["line_width_um"] / 1000.0
    h = spec["dielectric_thickness_mm"]
    t = spec["signal_thickness_um"] / 1000.0
    total_w = spec["total_width_mm"]
    L = spec["length_mm"]
    total_h = 2 * h + 3 * t
    return n_ch, pitch, w, h, t, total_w, L, total_h


def 繪製層(spec):
    """繪製側視圖層結構，回傳 (fig, ax)。"""
    n_ch, pitch, w, h, t, total_w, L, total_h = _尺寸(spec)
    cond = spec.get("conductor_color", "#FFD700")
    diel = spec.get("dielectric_color", "#C4956A")
    fig, ax = subplots(figsize=(10, 6))
    y0, y1, y2, y3, y4 = 0, t, t + h, t + h + t, t + h + t + h
    # 接地層 (底/頂)
    ax.add_patch(Rectangle((0, y0), L, t, facecolor="#8B9CAD", edgecolor="#4A5568"))
    ax.add_patch(Rectangle((0, y4), L, t, facecolor="#8B9CAD", edgecolor="#4A5568"))
    # 介電層
    ax.add_patch(Rectangle((0, y1), L, h, facecolor=diel, edgecolor="#744210", alpha=0.6))
    ax.add_patch(Rectangle((0, y3), L, h, facecolor=diel, edgecolor="#744210", alpha=0.6))
    # 訊號線
    ax.add_patch(Rectangle((0, y2), L, t, facecolor=cond, edgecolor="#B8860B"))
    ax.set_xlim(0, L)
    ax.set_ylim(-0.1, total_h + 0.1)
    return fig, ax


def 繪製標註(ax, spec):
    """繪製標註文字。"""
    if ax is None:
        return
    n_ch, pitch, w, h, t, total_w, L, total_h = _尺寸(spec)
    ax.set_title(f"側視圖 Side View ({spec.get('name','')})  L={L}mm", fontsize=11, fontweight="bold")
    ax.set_xlabel("Length (mm)")
    ax.set_ylabel("Z (mm)")


def 繪製尺寸標註(ax, spec):
    """繪製尺寸標註。"""
    if ax is None:
        return
    n_ch, pitch, w, h, t, total_w, L, total_h = _尺寸(spec)
    ax.annotate(f"L={L}mm", xy=(L / 2, total_h + 0.05), fontsize=8, ha="center")


def 繪製側視(spec=None):
    """繪製側視圖，回傳 matplotlib Figure。"""
    spec = 取得規格(spec) if spec is not None else 取得規格("CF3")
    if isinstance(spec, str):
        spec = 取得規格(spec)
    fig, ax = 繪製層(spec)
    繪製標註(ax, spec)
    繪製尺寸標註(ax, spec)
    ax.grid(True, alpha=0.3)
    tight_layout()
    return fig


if __name__ == "__main__":
    fig = 繪製側視("CF3")
    fig.savefig(os.path.join(os.path.dirname(__file__), "側視圖.png"), dpi=150)
    print("已輸出 側視圖.png")
