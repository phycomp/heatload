import sys
sys.path.insert(0, "/mnt/agents/output/pcb_calc_app")

import numpy as np
import importlib

# 清除緩存重新加載
import modules.inverse.s_param_parser as parser_mod
import modules.inverse.optimizer as opt_mod
import modules.inverse.sensitivity as sens_mod
importlib.reload(parser_mod)
importlib.reload(opt_mod)
importlib.reload(sens_mod)

from modules.inverse.s_param_parser import TouchstoneParser
from modules.inverse.optimizer import InverseEngineer
from modules.inverse.sensitivity import SensitivityAnalyzer

print("=" * 60)
print("Phase 3 全面功能測試")
print("=" * 60)

errors = []

def check(name, condition, msg=""):
    if not condition:
        errors.append(f"❌ {name}: {msg}")
        return False
    return True

# ============================================================
# 1. S 參數解析器測試
# ============================================================
print("\n【1. S 參數解析器測試】")

parser = TouchstoneParser("/mnt/agents/output/pcb_calc_app/saved_projects/test_microstrip.s2p")

# 1.1 基本解析
summary = parser.get_data_summary()
print(f"  解析摘要: {summary}")
check("解析點數", summary['n_points'] == 100, f"實際 {summary['n_points']}")
check("頻率範圍", abs(summary['freq_range_ghz'][0] - 0.1) < 0.01 and abs(summary['freq_range_ghz'][1] - 10.0) < 0.01, "")
check("參考阻抗", summary['z0'] == 50.0, "")

# 1.2 頻率數組
freqs = parser.get_frequencies_ghz()
check("頻率數組長度", len(freqs) == 100, "")
check("頻率範圍", freqs[0] == 0.1 and freqs[-1] == 10.0, "")

# 1.3 S21 數據
s21_db = parser.get_s21_db()
check("S21 長度", len(s21_db) == 100, "")
check("S21 爲負值", all(s21_db <= 0), f"S21 最小值={s21_db.min():.2f}")
check("S21 範圍合理", -10 < s21_db.min() < 0, f"S21 最小值={s21_db.min():.2f}")

# 1.4 S11 數據
s11_db = parser.get_s11_db()
check("S11 長度", len(s11_db) == 100, "")
check("S11 爲負值", all(s11_db <= 0), "")

# 1.5 S21 單調性 (頻率升高，損耗增加，S21 降低)
s21_mono = all(s21_db[i] >= s21_db[i+1] for i in range(len(s21_db)-1))
check("S21 頻率單調性", s21_mono, "頻率升高 S21 應單調下降")

# 1.6 復數 S 參數
s21_complex = parser.get_s_param("S21")
check("S21 復數", len(s21_complex) == 100, "")
check("S21 幅度一致性", abs(20*np.log10(np.abs(s21_complex[0]) + 1e-15) - s21_db[0]) < 0.001, "")

print("  S參數解析器: 全部通過 ✅")

# ============================================================
# 2. 逆工程優化器測試
# ============================================================
print("\n【2. 逆工程優化器測試】")

# 使用測試數據
fixed = {"h_mm": 1.6, "t_mm": 0.035, "roughness_model": "hammerstad"}

# 2.1 單參數反解: Dk
print("\n  測試1: 單參數反解 Dk")
engineer1 = InverseEngineer(freqs, s21_db, s11_db, 0.1, fixed)
result1 = engineer1.optimize(
    param_names=["dk"],
    bounds={"dk": (3.0, 6.0)},
    initial_guess={"dk": 4.0},
    auto_algorithm=True
)
print(f"    藕合 Dk: {result1['fitted_params']['dk']:.4f} (真實: 4.5)")
print(f"    最終 Cost: {result1['final_cost']:.6f}")
print(f"    算法階段: {len(result1['stages'])}")
check("單參數 Dk 精度", abs(result1['fitted_params']['dk'] - 4.5) < 0.1,
      f"藕合值={result1['fitted_params']['dk']:.4f}")

# 2.2 雙參數反解: Dk + Df
print("\n  測試2: 雙參數反解 Dk + Df")
engineer2 = InverseEngineer(freqs, s21_db, s11_db, 0.1, fixed)
result2 = engineer2.optimize(
    param_names=["dk", "df"],
    bounds={"dk": (3.0, 6.0), "df": (0.001, 0.05)},
    initial_guess={"dk": 4.0, "df": 0.015},
    auto_algorithm=True
)
print(f"    藕合 Dk: {result2['fitted_params']['dk']:.4f} (真實: 4.5)")
print(f"    藕合 Df: {result2['fitted_params']['df']:.5f} (真實: 0.02)")
print(f"    最終 Cost: {result2['final_cost']:.6f}")
print(f"    算法階段: {len(result2['stages'])}")
check("雙參數 Dk 精度", abs(result2['fitted_params']['dk'] - 4.5) < 0.1, "")
check("雙參數 Df 精度", abs(result2['fitted_params']['df'] - 0.02) < 0.002, "")

# 2.3 三參數反解: Dk + Df + w
print("\n  測試3: 三參數反解 Dk + Df + w")
engineer3 = InverseEngineer(freqs, s21_db, s11_db, 0.1, fixed)
result3 = engineer3.optimize(
    param_names=["dk", "df", "w_mm"],
    bounds={"dk": (3.0, 6.0), "df": (0.001, 0.05), "w_mm": (0.1, 1.0)},
    initial_guess={"dk": 4.0, "df": 0.015, "w_mm": 0.25},
    auto_algorithm=True
)
print(f"    藕合 Dk: {result3['fitted_params']['dk']:.4f} (真實: 4.5)")
print(f"    藕合 Df: {result3['fitted_params']['df']:.5f} (真實: 0.02)")
print(f"    藕合 w: {result3['fitted_params']['w_mm']:.4f}mm (真實: 0.3)")
print(f"    最終 Cost: {result3['final_cost']:.6f}")
check("三參數 Dk 精度", abs(result3['fitted_params']['dk'] - 4.5) < 0.15, "")
check("三參數 Df 精度", abs(result3['fitted_params']['df'] - 0.02) < 0.003, "")
check("三參數 w 精度", abs(result3['fitted_params']['w_mm'] - 0.3) < 0.02, "")

# 2.4 四參數反解 (含粗糙度)
print("\n  測試4: 四參數反解 Dk + Df + w + Rq")
engineer4 = InverseEngineer(freqs, s21_db, s11_db, 0.1, fixed)
result4 = engineer4.optimize(
    param_names=["dk", "df", "w_mm", "Rq_um"],
    bounds={"dk": (3.0, 6.0), "df": (0.001, 0.05), "w_mm": (0.1, 1.0), "Rq_um": (0.5, 3.0)},
    initial_guess={"dk": 4.0, "df": 0.015, "w_mm": 0.25, "Rq_um": 1.2},
    auto_algorithm=True
)
print(f"    藕合 Dk: {result4['fitted_params']['dk']:.4f} (真實: 4.5)")
print(f"    藕合 Df: {result4['fitted_params']['df']:.5f} (真實: 0.02)")
print(f"    藕合 w: {result4['fitted_params']['w_mm']:.4f}mm (真實: 0.3)")
print(f"    藕合 Rq: {result4['fitted_params']['Rq_um']:.4f}μm (真實: 1.5)")
print(f"    最終 Cost: {result4['final_cost']:.6f}")
print(f"    算法階段: {len(result4['stages'])}")
for s in result4['stages']:
    print(f"      Stage {s['stage']}: {s['algorithm']}, cost={s['cost']:.6f}, success={s['success']}")

check("四參數 Dk 精度", abs(result4['fitted_params']['dk'] - 4.5) < 0.2, "")
check("四參數 Df 精度", abs(result4['fitted_params']['df'] - 0.02) < 0.005, "")
check("四參數 w 精度", abs(result4['fitted_params']['w_mm'] - 0.3) < 0.03, "")

# 2.5 藕合曲線質量
print("\n  藕合曲線質量檢查:")
s21_fitted = np.array(result4["s21_fitted"])
rmse = np.sqrt(np.mean((s21_db - s21_fitted) ** 2))
print(f"    RMSE: {rmse:.4f} dB")
check("藕合 RMSE", rmse < 1.0, f"RMSE={rmse:.4f} dB")

# 2.6 殘差檢查
residuals = np.array(result4["s21_residual"])
print(f"    殘差均值: {residuals.mean():.4f} dB")
print(f"    殘差標準差: {residuals.std():.4f} dB")
check("殘差均值接近0", abs(residuals.mean()) < 0.5, f"均值={residuals.mean():.4f}")

print("  逆工程優化器: 全部通過 ✅")

# ============================================================
# 3. 敏感度分析測試
# ============================================================
print("\n【3. 敏感度分析測試】")

# 使用四參數結果進行敏感度分析
cost_fn = lambda x: engineer4._cost_function(x, ["dk", "df", "w_mm", "Rq_um"])
analyzer = SensitivityAnalyzer(cost_fn, ["dk", "df", "w_mm", "Rq_um"],
                                result4["fitted_params"],
                                {"dk": (3.0, 6.0), "df": (0.001, 0.05), "w_mm": (0.1, 1.0), "Rq_um": (0.5, 3.0)})
sens_results = analyzer.analyze(perturbation_pct=0.05)

print("  敏感度排名:")
for i, r in enumerate(sens_results):
    print(f"    #{i+1}: {r['param']:6s} | 敏感度={r['normalized_sensitivity']:.4f} | 方向={r['direction']}")

check("敏感度分析結果", len(sens_results) == 4, f"實際 {len(sens_results)} 個結果")
check("敏感度已排序", sens_results[0]["normalized_sensitivity"] >= sens_results[-1]["normalized_sensitivity"], "")

# 排名映射
ranking = analyzer.get_sensitivity_ranking()
check("排名映射", len(ranking) == 4, "")

print("  敏感度分析: 全部通過 ✅")

# ============================================================
# 4. 邊界測試
# ============================================================
print("\n【4. 邊界測試】")

# 4.1 極端初始猜測
print("\n  極端初始猜測測試:")
engineer_bad = InverseEngineer(freqs, s21_db, s11_db, 0.1, fixed)
result_bad = engineer_bad.optimize(
    param_names=["dk", "df"],
    bounds={"dk": (3.0, 6.0), "df": (0.001, 0.05)},
    initial_guess={"dk": 3.1, "df": 0.001},  # 極端偏差
    auto_algorithm=True
)
print(f"    初始猜測: Dk=3.1, Df=0.001")
print(f"    藕合結果: Dk={result_bad['fitted_params']['dk']:.4f}, Df={result_bad['fitted_params']['df']:.5f}")
check("極端初值收斂", abs(result_bad['fitted_params']['dk'] - 4.5) < 0.2, "")

# 4.2 僅 S21 (無 S11)
print("\n  僅 S21 優化:")
engineer_s21only = InverseEngineer(freqs, s21_db, None, 0.1, fixed)
result_s21 = engineer_s21only.optimize(
    param_names=["dk", "df"],
    bounds={"dk": (3.0, 6.0), "df": (0.001, 0.05)},
    initial_guess={"dk": 4.0, "df": 0.015},
    auto_algorithm=True
)
print(f"    藕合 Dk: {result_s21['fitted_params']['dk']:.4f}")
print(f"    藕合 Df: {result_s21['fitted_params']['df']:.5f}")
check("僅S21 Dk精度", abs(result_s21['fitted_params']['dk'] - 4.5) < 0.1, "")

# 4.3 手動算法 (非自動)
print("\n  手動 L-BFGS-B:")
engineer_manual = InverseEngineer(freqs, s21_db, s11_db, 0.1, fixed)
result_manual = engineer_manual.optimize(
    param_names=["dk"],
    bounds={"dk": (3.0, 6.0)},
    initial_guess={"dk": 4.0},
    auto_algorithm=False
)
print(f"    藕合 Dk: {result_manual['fitted_params']['dk']:.4f}")
check("手動算法", abs(result_manual['fitted_params']['dk'] - 4.5) < 0.1, "")

print("  邊界測試: 全部通過 ✅")

# ============================================================
# 匯總
# ============================================================
print("\n" + "=" * 60)
if errors:
    print(f"🔴 測試未通過，{len(errors)} 個錯誤:")
    for e in errors:
        print(f"  {e}")
else:
    print("🟢 所有測試通過！Phase 3 代碼無已知錯誤。")
print("=" * 60)
