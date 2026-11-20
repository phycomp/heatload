# 熱負載（舊版模組參考）

低溫傳輸線熱負載計算舊版程式與文件，保留作為參考。
新架構已遷移部分至 `src/量傳線設計/核心/熱負載*.py` 與 `pages/4,10,18,19,20`。

## NIST 9 係數整合 (D4=A, D5=A)
- 單一真相來源：`~/.opencode/skills/heatload-coff-nist/scripts/{coeff_data,thermal_load}.py`（54 材料、κ(T)/∫κdT、多溫區 `Q_solid=Σ(A/L)∫κdT` + 衰減器耗散）。
- 共用層：`pages/_nist9_共用.py`；新平台核心 `src/量傳線設計/核心/熱負載NIST9.py`。
- 新增/重構頁面（保留原檔）：`10nist低溫庫.py`（重構，備份 `10nist低溫庫_legacy.py`）、`30nist9_熱負載模擬.py`、`31nist9_polyfit_可靠度.py`；`16柔性八階擬合.py` 保留原 runtime polyfit（備份 `16柔性八階擬合_legacy.py`）。
- 驗證：`scripts/validate_polyfit_reliability.py` → `docs/polyfit_可靠度驗證.md/json`；整合說明見 `docs/NIST9熱負載整合說明.md`。

主要內容：
- 熱負載計算、回推溫區長度、FLAX/Raicu 模型、NIST 9 係數模擬/掃描、polyfit 可靠度驗證
- MDs/：技術文件
