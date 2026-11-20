# 三視圖 API 使用與測試說明

## 視圖切換 API（三視圖/組合.py）

- `切換視圖(spec, view)`：依 view 名稱回傳單一 Figure
  - view 可為 "前"/"側"/"上" 或 "front"/"side"/"top" 或中文全名
- `繪製視圖(spec, views=None)`：繪製指定視圖子集，回傳 dict
- `繪製全部視圖(spec)`：回傳 `{"前視圖", "側視圖", "上視圖"}`
- `批次繪製(specs)`：批次繪製多個規格，回傳 `{spec_name: {view: fig}}`
- `可用視圖()`：回傳可用視圖名稱列表

## 規格

- 內建：`"CF3"`、`"FPC"`、`"Uleam1"`
- 自訂 dict：可覆蓋 `conductor_color`、`dielectric_color` 等欄位，未提供欄位使用 CF3 預設

## 測試

```bash
PYTHONPATH=src python -m pytest tests/test_三視圖API.py -q
```

## 範例

```python
import sys
sys.path.insert(0, "/home/sam/量傳線/三視圖")
from 組合 import 切換視圖, 繪製視圖, 批次繪製

fig = 切換視圖("FPC", "側")
d = 繪製視圖("Uleam1", ["前視圖", "上視圖"])
b = 批次繪製(["CF3", "FPC"])
```
PY