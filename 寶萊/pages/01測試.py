import sys
sys.path.insert(0, "/mnt/agents/output/pcb_calc_app")

# 测试 formulas
from modules.impedance.formulas import microstrip_z0, stripline_z0

# Microstrip 测试: FR-4, w=0.3mm, h=1.6mm, t=35um
z0, ee = microstrip_z0(0.3, 1.6, 0.035, 4.5, 0.0)
print(f"Microstrip 静态: Z0={z0:.2f}Ω, εeff={ee:.3f}")

# 频率扫描
z0_f, ee_f = microstrip_z0(0.3, 1.6, 0.035, 4.5, 5.0)
print(f"Microstrip @5GHz: Z0={z0_f:.2f}Ω, εeff={ee_f:.3f}")

# Stripline 测试
z0_s, ee_s = stripline_z0(0.3, 1.6, 0.035, 4.5)
print(f"Stripline 静态: Z0={z0_s:.2f}Ω, εeff={ee_s:.3f}")

# 测试 solver
from modules.impedance.solver import forward_calc, inverse_calc

z0_fwd, ee_fwd = forward_calc("Microstrip", 0.3, 1.6, 0.035, 4.5, 1.0)
print(f"\nSolver 正向: Z0={z0_fwd:.2f}Ω")

w_inv = inverse_calc("Microstrip", 50.0, 1.6, 0.035, 4.5, 0.0)
print(f"Solver 反向 (目标50Ω): w={w_inv*1000:.2f}μm")

# 验证
z0_verify, _ = forward_calc("Microstrip", w_inv, 1.6, 0.035, 4.5, 0.0)
print(f"验证: Z0={z0_verify:.2f}Ω")

# 测试 sweep
from modules.impedance.sweep import param_sweep, freq_sweep
import numpy as np

df = param_sweep("Microstrip", "w_mm", np.linspace(0.1, 1.0, 5),
                 {"w":0.3, "h":1.6, "t":0.035, "er":4.5, "freq_ghz":1.0})
print(f"\n参数扫描结果:\n{df}")

df_f = freq_sweep("Microstrip", 0.3, 1.6, 0.035, 4.5, [0.1, 1, 5, 10])
print(f"\n频率扫描结果:\n{df_f}")

# 测试 project_io
from utils.project_io import save_project, load_project
test_data = {"test": "hello", "value": 42}
save_project("/mnt/agents/output/pcb_calc_app/saved_projects/test.json", test_data)
loaded = load_project("/mnt/agents/output/pcb_calc_app/saved_projects/test.json")
print(f"\nProject IO 测试: {loaded}")

print("\n✅ 所有模块测试通过！")
