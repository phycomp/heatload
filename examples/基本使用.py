import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from 量傳線設計.核心.規格產生器 import 產生規格書
from 量傳線設計.輸出入.excel匯出 import 試算表轉bytes
from 量傳線設計.核心.低溫超導 import 模擬NbTi串擾
from 量傳線設計.核心.熱負載 import 回推溫區長度

# 1. 產生規格書
佈局, 試算表 = 產生規格書(通道數=8, 訊號間距=2.0)
with open("spec.xlsx", "wb") as f:
    f.write(試算表轉bytes(試算表))
print("規格書已輸出 spec.xlsx")

# 2. NbTi 串擾
r = 模擬NbTi串擾(w_um=50, d_nm=100, s_um=100)
print("Z0 =", round(r["Z0"], 2), "Ohm")

# 3. 熱負載回推長度
L = 回推溫區長度(熱導率=0.1, 截面積=1e-6, 溫差=50.0, 熱負載_W=1e-6)
print("回推長度 L =", round(L, 4), "m")
