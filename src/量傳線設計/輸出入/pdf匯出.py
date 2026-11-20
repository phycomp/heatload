"""PDF 匯出：將 matplotlib figure 存為 PDF bytes。"""
from io import BytesIO
from matplotlib.figure import Figure

def 圖轉pdf(fig) -> bytes:
    buf = BytesIO()
    fig.savefig(buf, format="pdf", bbox_inches="tight")
    buf.seek(0)
    return buf.getvalue()
