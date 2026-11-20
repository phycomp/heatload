# NIST 9 係數熱負載整合與 polyfit 可靠度說明

## 範圍與決策
- D1=B: 整合至新平台 (`src/量傳線設計/核心/` + `pages/`) 並處理 `熱負載/pages/`
- D2=D: 共用核心計算模組 + 重構/新增頁面 + 新模擬頁
- D3=D: κ(T)/∫κdT 曲線、材料比較、多溫區穩態熱負載 (`Q_solid=Σ(A/L)∫κdT` + 衰減器耗散)、參數掃描/模擬
- D4=A: 9 係數資料與引擎以 `~/.opencode/skills/heatload-coff-nist/scripts/{coeff_data,thermal_load}.py` 為單一真相來源
- D5=A: 保留原始檔，新增共用層/新頁面（不破壞性取代）
- D6=C: 本輪完成實作與驗證

## 單一真相來源 (NIST 9 係數)
- `~/.opencode/skills/heatload-coff-nist/scripts/coeff_data.py`: 54 材料、`c0..c8`、`equation_type` (`log_polynomial`/`rational_copper`)、有效溫度範圍、來源與備註（不重擬合、不編造）。
- `~/.opencode/skills/heatload-coff-nist/scripts/thermal_load.py`: κ(T)、`integrate_kappa`(log-spaced 梯形)、`calculate_thermal_load` (多溫區 `Q_solid + Q_rf`)，無 `scipy` 依賴。
- 模型:
  - $\log_{10}\kappa(T)=\sum_{n=0}^{8} c_n (\log_{10}T)^n$ 或 OFHC Cu rational 形式
  - $Q_{solid}=\sum_i (A/L_i)\int_{T_{c,i}}^{T_{h,i}}\kappa(T)dT$
  - $Q_{rf}=\sum_i P_{in}(1-10^{-\alpha_i/10})$
- 範圍外預設 0；可選低溫 $k(T)\sim T^\alpha$ 外推（可能高估，須保守解讀）。

## 新增/重構交付
### 共用核心
- `src/量傳線設計/核心/熱負載NIST9.py`: 對技能引擎的薄封裝，提供材料查詢、κ(T)/積分/曲線、材料比較、多溫區熱負載、參數與材料掃描。
- `src/量傳線設計/核心/__init__.py`: 匯出 NIST9 API。
- `熱負載/pages/_nist9_共用.py`: 舊目錄頁面共用層（優先以檔案路徑載入新平台核心，避免套件 `__init__` 副作用；失敗則 fallback 技能腳本）。

### 頁面 (保留原檔)
- `熱負載/pages/10nist低溫庫.py`: 重構為使用 NIST9 引擎（54 材料、9 係數、κ(T)/∫κdT/比較/熱負載估算）。原檔備份 `10nist低溫庫_legacy.py`。
- `熱負載/pages/30nist9_熱負載模擬.py`: 新增模擬頁（κ(T)/∫κdT 曲線、材料比較、多溫區穩態熱負載、參數/材料掃描）。
- `熱負載/pages/31nist9_polyfit_可靠度.py`: 顯示 polyfit 可靠度驗證報告/JSON。
- `pages/20熱負載NIST9.py`: 新平台整合模擬頁（完整 D3 功能）。
- `pages/4熱負載.py`: 保留原功能並新增「NIST 9 係數模擬」分頁（非破壞性擴充）。
- `熱負載/pages/16柔性八階擬合.py`: 保留原檔（runtime polyfit 行為）；原檔備份 `16柔性八階擬合_legacy.py`，可靠度以報告/頁面呈現。

## polyfit 參數可靠度驗證 (重點: `熱負載/pages/16柔性八階擬合.py`)
- 驗證腳本: `scripts/validate_polyfit_reliability.py`
- 報告: `docs/polyfit_可靠度驗證.md`, `docs/polyfit_可靠度驗證.json`
- 方法: 重現頁面邏輯 `log10(T)-log10(k)` 8 階 `np.polyfit`、N=50、T∈[2,300]K、`noise_pct`/seed 擾動、低溫 `k(T)=T^alpha` 外推；檢查條件數、R²/RMSE、Tc 區殘差、係數/α/k(20mK)/∫κdT 敏感度，並與 `coeff_data` 對照。
- 主要結論:
  1. 2-300K 擬合品質高（Kapton R²≈0.99996, NbTi R²≈0.9926, noise=1%/seed=42），但 Vandermonde 高度病態；NbTi 在 Tc~9.2K 有結構性殘差（全域 8 階多項式近似）。
  2. 係數對 `noise_pct`/seed 敏感（頁面即具隨機性）；Kapton 中等敏感，NbTi 變動較大且無固定權威數值。
  3. 低溫外推不可靠：`alpha` 與端點多項式導數落差大，`k(20mK)` 對擾動可跨數量級；<Tmin 外推僅可作量級示意。
  4. 積分相對穩定：擬合區間 `∫_2^300 κ dT` 對擾動變動較小，適合區間熱負載估算；深低溫/跨區需保守。
  5. `coeff_data`: `Kapton (Cri/oFlex 3)` 有固定係數與來源；`NbTi (Cri/oFlex 3)` 為 `runtime_polyfit`、`coeffs=null`（不可編造）。頁面擬合係數 ≠ 固定 NIST 係數。

## 使用建議
- 熱負載主計算/模擬優先使用具來源之 NIST 9 係數材料與 `熱負載NIST9`/技能引擎。
- 對 runtime 擬合材料（如 NbTi Cri/oFlex3）必須明示資料來源、擬合條件與 seed/noise，不可視為固定物性係數。
- 驗證: `python3 scripts/validate_polyfit_reliability.py`；核心 smoke: 以檔案載入 `src/量傳線設計/核心/熱負載NIST9.py` 測試 `k_curve/calculate_thermal_load/compare_materials/sweep_parameter`。
