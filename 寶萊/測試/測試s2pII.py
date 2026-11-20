# 調試 S 參數解析器

# 重新讀取文件并手動跟蹤解析
with open("/mnt/agents/output/pcb_calc_app/saved_projects/test_microstrip.s2p", "r") as f:
    lines = f.readlines()

print(f"總行數: {len(lines)}")

# 模藕解析器的預處理
data_lines = []
for i, line in enumerate(lines):
    stripped = line.strip()
    if not stripped or stripped.startswith("!"):
        continue
    if stripped.startswith("#"):
        print(f"Header line: '{stripped}'")
        continue
    data_lines.append(stripped)

print(f"數據行數: {len(data_lines)}")
print(f"第一數據行: '{data_lines[0]}'")
print(f"數據行字段數: {len(data_lines[0].split())}")

# 檢查所有值
all_values = []
for line in data_lines:
    vals = [float(x) for x in line.split() if x.strip()]
    all_values.extend(vals)

print(f"總數值數: {len(all_values)}")

# 檢查是否能被 9 整除
cols_per_row = 9
n_rows = len(all_values) // cols_per_row
print(f"期望行數: {n_rows}, 余數: {len(all_values) % cols_per_row}")

# 嘗試重組
if len(all_values) >= cols_per_row:
    data = np.array(all_values[:n_rows * cols_per_row]).reshape(n_rows, cols_per_row)
    print(f"重組後形狀: {data.shape}")
    print(f"頻率範圍: {data[:, 0].min():.2f} - {data[:, 0].max():.2f}")
else:
    print("ERROR: 數值不足以組成一行!")
