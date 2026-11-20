with open("/mnt/agents/output/pcb_calc_app/modules/impedance/sweep.py", "w", encoding="utf-8") as f:
    f.write(sweep_fixed2)

# 重新测试
from importlib import reload
import modules.impedance.sweep as sweep_mod
reload(sweep_mod)

df = sweep_mod.param_sweep("Microstrip", "t_um", [0, 18, 35, 70],
                            {"w":0.3, "h":1.6, "t":0.035, "er":4.5, "freq_ghz":1.0})
print("t_um 扫描结果 (修复后):")
print(df)

# 再测试 w_mm 扫描
df2 = sweep_mod.param_sweep("Microstrip", "w_mm", np.linspace(0.1, 1.0, 5),
                            {"w":0.3, "h":1.6, "t":0.035, "er":4.5, "freq_ghz":1.0})
print("\nw_mm 扫描结果:")
print(df2)

print("\n✅ sweep.py 最终修复完成")

