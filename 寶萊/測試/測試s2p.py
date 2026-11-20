# 診斷 S 參數解析器問題

# 1. 檢查生成的 .s2p 文件內容
with open("/mnt/agents/output/pcb_calc_app/saved_projects/test_microstrip.s2p", "r") as f:
    content = f.read()

print("文件前 10 行:")
for i, line in enumerate(content.split("\n")[:10]):
    print(f"  [{i}] '{line}'")

print(f"\n總行數: {len(content.split(chr(10)))}")
print(f"文件大小: {len(content)} bytes")

# 2. 檢查解析器內部狀態
from modules.inverse.s_param_parser import TouchstoneParser

# 手動跟蹤解析
parser = TouchstoneParser("/mnt/agents/output/pcb_calc_app/saved_projects/test_microstrip.s2p")
print(f"\n解析器狀態:")
print(f"  freq_unit: {parser.freq_unit}")
print(f"  format: {parser.format}")
print(f"  n_ports: {parser.n_ports}")
print(f"  z0: {parser.reference_impedance}")
print(f"  _data: {parser._data}")
