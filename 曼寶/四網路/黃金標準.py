import sys
sys.path.insert(0, str(base / 'backend'))
import importlib
import 傳輸線 as T
importlib.reload(T)

golden = T.design_microstrip(50.0, 1.6, 0.035, 4.2, method="ipc")
for k, v in golden.items():
    print(f"{k:>16}: {v}")

# 黃金標準對照
import math
checks = {
    "w (3.022 mm)": abs(golden["w_mm"] - 3.022) / 3.022,
    "Tpd (54.411)": abs(golden["tpd_ps_cm"] - 54.411) / 54.411,
    "L (2.721)": abs(golden["L_nH_cm"] - 2.721) / 2.721,
    "C (1.08821)": abs(golden["C_pF_cm"] - 1.08821) / 1.08821,
    "Rdc (1.626)": abs(golden["Rdc_mOhm_cm"] - 1.626) / 1.626,
}
print()
for k, err in checks.items():
    print(f"{k:>14} 誤差 = {err*100:.4f}%  {'PASS' if err <= 0.01 else 'FAIL'}")
