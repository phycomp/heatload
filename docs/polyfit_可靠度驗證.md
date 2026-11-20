# polyfit 參數可靠度驗證 (16柔性八階擬合)

- 資料生成器: `numpy.interp(log-log) fallback` (HAVE_SCIPY=False)
- 擬合模型: `log10(k)=Σ c_n (log10 T)^n`, n=0..8, `np.polyfit(x,y,8)`; T=2..300K, N=50, log-spaced
- 低溫外推(程式實作): `T < Tmin` 時 `k(T)=T^alpha`, `alpha=log10(k_poly(Tmin))/log10(Tmin)`

## 數值條件數

- cond(V)_raw = 1.309e+07, cond(V^T V)_raw = 1.713e+14
- cond(V_centered_scaled) = 5.256e+04 (polyfit 內部縮放可改善求解穩定性，但高階項仍具敏感性)

## 基準擬合 (noise=1%, seed=42)

### kapton
- R²=0.999961, RMSE(log10)=0.004398
- alpha_extrap=-10.2833, poly_slope@Tmin=1.1945, gap=-11.4778
- k(20mK)=2.9587e+17 W/m/K (外推, 不確定性高), ∫_2^300 k dT=2.854153e+01 W/m

### nbti
- R²=0.992615, RMSE(log10)=0.107797
- alpha_extrap=-9.3187, poly_slope@Tmin=8.0967, gap=-17.4154
- k(20mK)=6.7945e+15 W/m/K (外推, 不確定性高), ∫_2^300 k dT=2.099555e+03 W/m
- NbTi Tc 區(7.5-12.5K) max |resid_log10|=0.3375 (全域 8 階多項式難以精確描述轉變)

## 噪聲/seed 敏感度 (noise∈{0,1,2,5}%, seeds=6, 每材料24次)

### kapton
- R²_min=0.999138, RMSE_max=0.020562
- alpha 範圍: [-10.3621, -10.1745]
- k(20mK) 範圍: [1.932e+17, 4.026e+17] (跨數量級/大幅變動 ⇒ 外推不可靠)
- ∫_2^300 k dT 範圍: [2.8374e+01, 2.9124e+01] (量測溫區積分相對穩定)
- 係數相對標準差% (c0..c8): [13.14, 83.69, 52.34, 45.62, 41.74, 40.14, 40.4, 42.13, 45.05]

### nbti
- R²_min=0.991884, RMSE_max=0.112764
- alpha 範圍: [-9.3974, -9.2098]
- k(20mK) 範圍: [4.438e+15, 9.246e+15] (跨數量級/大幅變動 ⇒ 外推不可靠)
- ∫_2^300 k dT 範圍: [2.0844e+03, 2.1413e+03] (量測溫區積分相對穩定)
- 係數相對標準差% (c0..c8): [2.21, 2.51, 2.46, 2.49, 2.64, 2.94, 3.4, 4.06, 4.96]

## 與 coeff_data 對照

### Kapton (Cri/oFlex 3)
- 來源: 推導柔性多項式耦合系數.md L138-166 / 16柔性八階擬合.py（Cri/oFlex 3，7 位有效數字）
- noise=1,seed=42 擬合 vs 儲存係數 max |Δc| = 75.49 (生成器差異: 頁面用 scipy.CubicSpline, 本驗證預設 numpy.interp(log-log) fallback)
### NbTi (Cri/oFlex 3)
- coeffs: None, equation_type: runtime_polyfit
- 狀態: 讀不到固定數值：16柔性八階擬合.py 於執行期以 np.polyfit 對 seed=42 模擬 PPMS 資料擬合，且受 noise_pct 滑桿影響；原始檔未提供 NBTI_COEFFS 數字常數，故不填寫（不編造）

## 可靠度結論

1. **數值可解但病態**: 原始 Vandermonde 條件數極大；`polyfit` 透過平移/縮放可穩定求解，但 8 階係數(特別高階/邊界外推相關項)對資料擾動敏感。
2. **擬合品質**: 在 2-300K 資料範圍內 R² 高、RMSE(log10) 小；但 NbTi 在 Tc~9.2K 轉變區存在結構性殘差，全域單一 8 階多項式屬近似。
3. **係數可靠度**: 係數會隨 `noise_pct` 與隨機種子改變(頁面行為)；Kapton 擾動下中等敏感，NbTi 係數變動較大且無固定權威數值。
4. **外推可靠度低**: `alpha` 與多項式端點導數落差大，且 `k(20mK)` 對擾動極敏感；低於 Tmin 的直線外推僅可作量級示意，不宜視為可靠物性參數。
5. **積分相對可靠**: 量測/擬合區間內 `∫κ dT` 對擾動較穩定，適合做區間熱負載估算；跨區/深低溫需保守解讀。
6. **工程建議**: 以 `heatload-coff-nist/coeff_data.py` 中具來源之固定係數作單一真相；對 NbTi/Cri-oFlex3 這類 runtime 擬合材料，必須明示資料來源與擬合條件，不可當固定 NIST 係數使用。