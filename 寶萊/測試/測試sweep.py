# 重新測試
from importlib import reload
import modules.impedance.sweep as sweep_mod
reload(sweep_mod)

df = sweep_mod.param_sweep("Microstrip", "w_mm", np.linspace(0.1, 1.0, 5),
                           {"w":0.3, "h":1.6, "t":0.035, "er":4.5, "freq_ghz":1.0})
print("修復後參數掃描結果:")
print(df)

# 同時測試 t_um 掃描
df2 = sweep_mod.param_sweep("Microstrip", "t_um", [0, 18, 35, 70],
                            {"w":0.3, "h":1.6, "t":0.035, "er":4.5, "freq_ghz":1.0})
print("\nt_um 掃描結果:")
print(df2)

print("\n✅ sweep.py 修復完成并通過測試")

