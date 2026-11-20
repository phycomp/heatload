"""Excel 匯出輔助（直接回傳 bytes）。"""
from io import BytesIO

def 試算表轉bytes(wb):
    if isinstance(wb, (bytes, bytearray)):
        return bytes(wb)
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()
