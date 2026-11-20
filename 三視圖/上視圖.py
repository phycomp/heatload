"""三視圖 - 上視圖（獨立繪製，可混合使用）。"""
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
    total_w = spec["total_width_mm"]
    L = spec["length_mm"]
    return n_ch, pitch, w, total_w, L


def 繪製層(spec):
    """繪製上視圖層結構，回傳 (fig, ax)。"""
    n_ch, pitch, w, total_w, L = _尺寸(spec)
    cond = spec.get("conductor_color", "#FFD700")
    fig, ax = subplots(figsize=(10, 6))
    for i in range(n_ch):
        ax.add_patch(Rectangle((0, i * pitch), L, w, facecolor=cond, edgecolor="#B8860B"))
    ax.set_xlim(0, L)
    ax.set_ylim(0, total_w)
    return fig, ax


def 繪製標註(ax, spec):
    """繪製標註文字。"""
    if ax is None:
        return
    n_ch, pitch, w, total_w, L = _尺寸(spec)
    ax.set_title(f"上視圖 Top View ({spec.get('name','')})  {n_ch}ch", fontsize=11, fontweight="bold")
    ax.set_xlabel("Length (mm)")
    ax.set_ylabel("Width (mm)")


def 繪製尺寸標註(ax, spec):
    """繪製尺寸標註。"""
    if ax is None:
        return
    n_ch, pitch, w, total_w, L = _尺寸(spec)
    ax.annotate(f"{n_ch}ch", xy=(L / 2, total_w + 0.5), fontsize=8, ha="center")


def 繪製上視(spec=None):
    """繪製上視圖，回傳 matplotlib Figure。"""
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
    fig = 繪製上視("CF3")
    fig.savefig(os.path.join(os.path.dirname(__file__), "上視圖.png"), dpi=150)
    print("已輸出 上視圖.png")
