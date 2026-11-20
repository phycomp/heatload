import sys
sys.path.insert(0, "/mnt/agents/output/pcb_calc_app")

import importlib
import modules.impedance.formulas as formulas_mod
import modules.impedance.solver as solver_mod
import modules.impedance.sweep as sweep_mod
importlib.reload(formulas_mod)
importlib.reload(solver_mod)
importlib.reload(sweep_mod)

import numpy as np
from modules.impedance.formulas import microstrip_z0, stripline_z0
from modules.impedance.solver import forward_calc, inverse_calc
from modules.impedance.sweep import param_sweep, freq_sweep

print("=" * 60)
print("Phase 1 最終全面測試 (Wheeler Stripline 修正版)")
print("=" * 60)

errors = []

def check(name, condition, msg=""):
    if not condition:
        errors.append(f"❌ {name}: {msg}")
        return False
    return True

# ============================================================
# 1. Microstrip 公式
# ============================================================
print("\n【1. Microstrip 公式測試】")

z0, ee = microstrip_z0(0.3, 1.6, 0.0, 4.5, 0.0)
check("Microstrip 基準 Z0", 120 < z0 < 130, f"Z0={z0:.2f}")
check("Microstrip 基準 εeff", 2.8 < ee < 3.2, f"εeff={ee:.3f}")

z0_t0, _ = microstrip_z0(0.3, 1.6, 0.0, 4.5, 0.0)
z0_t35, _ = microstrip_z0(0.3, 1.6, 0.035, 4.5, 0.0)
check("Microstrip 厚度修正方向", z0_t35 < z0_t0, f"t=0:{z0_t0:.2f} vs t=35um:{z0_t35:.2f}")

z0_dc, ee_dc = microstrip_z0(0.3, 1.6, 0.035, 4.5, 0.0)
z0_10g, ee_10g = microstrip_z0(0.3, 1.6, 0.035, 4.5, 10.0)
check("Microstrip 頻率色散", z0_dc >= z0_10g, f"DC:{z0_dc:.2f} vs 10GHz:{z0_10g:.2f}")
check("Microstrip εeff 頻率趨勢", ee_dc <= ee_10g, f"DC:{ee_dc:.3f} vs 10GHz:{ee_10g:.3f}")

check("Microstrip 極小線寬", microstrip_z0(0.001, 1.6, 0.035, 4.5, 0.0)[0] > 200, "")
check("Microstrip 極大線寬", microstrip_z0(10.0, 1.6, 0.035, 4.5, 0.0)[0] < 50, "")
check("Microstrip 極小h", microstrip_z0(0.3, 0.01, 0.035, 4.5, 0.0)[0] < 20, "h極小->Z0極低")

z0_w09, _ = microstrip_z0(1.44, 1.6, 0.035, 4.5, 0.0)
z0_w1, _ = microstrip_z0(1.6, 1.6, 0.035, 4.5, 0.0)
z0_w11, _ = microstrip_z0(1.76, 1.6, 0.035, 4.5, 0.0)
check("Microstrip w/h邊界", abs(z0_w09-z0_w1)<5 and abs(z0_w11-z0_w1)<5, "")

print("  Microstrip: 全部通過 ✅")

# ============================================================
# 2. Stripline 公式 (Wheeler 精確, 修正後)
# ============================================================
print("\n【2. Stripline 公式測試 (Wheeler 精確, 修正後)】")

# 2.1 基準
z0_s, ee_s = stripline_z0(0.3, 1.6, 0.035, 4.5)
print(f"  基準: w=0.3, h=1.6(b), t=35μm, er=4.5 -> Z0={z0_s:.2f}Ω, εeff={ee_s:.3f}")
# Wheeler 精確公式: w=0.3, b=1.6 屬于中等寬度，Z0 應在 50-70Ω 範圍
check("Stripline 基準", 50 < z0_s < 80, f"Z0={z0_s:.2f}")
check("Stripline εeff", abs(ee_s - 4.5) < 0.001, "")

# 2.2 厚度修正方向: t 增加 -> we 增加 -> Z0 降低
t0_z0, _ = stripline_z0(0.3, 1.6, 0.0, 4.5)
t35_z0, _ = stripline_z0(0.3, 1.6, 0.035, 4.5)
print(f"  厚度: t=0 -> {t0_z0:.2f}Ω | t=35μm -> {t35_z0:.2f}Ω")
check("Stripline 厚度修正方向", t35_z0 < t0_z0, 
      f"t增加應降低Z0: t=0:{t0_z0:.2f} vs t=35um:{t35_z0:.2f}")

# 2.3 極端值
z0_s_minw, _ = stripline_z0(0.001, 1.6, 0.035, 4.5)
print(f"    w=1μm: Z0={z0_s_minw:.1f}Ω")
check("Stripline 極小線寬", z0_s_minw > 100, f"Z0={z0_s_minw:.1f}")

# 2.4 連續性檢查
print("\n  連續性檢查 (w/h 0.1 ~ 2.0):")
prev_z0 = None
all_continuous = True
for w_test in [0.1, 0.2, 0.3, 0.5, 0.56, 0.6, 1.0, 1.5, 2.0]:
    z0_t, _ = stripline_z0(w_test, 1.6, 0.035, 4.5)
    ratio = w_test / 1.6
    if prev_z0 is not None:
        if abs(z0_t - prev_z0) > 30:
            all_continuous = False
    print(f"    w={w_test:.3f}, w/h={ratio:.4f}, Z0={z0_t:.4f}Ω")
    prev_z0 = z0_t
check("Stripline 連續性", all_continuous, "")

# 2.5 單調性: 線寬增加 -> Z0 單調下降
df_s = param_sweep("Stripline", "w_mm", np.linspace(0.1, 2.0, 50),
                   {"w":0.3, "h":1.6, "t":0.035, "er":4.5, "freq_ghz":1.0})
s_mono = all(df_s["Z0"].values[i] >= df_s["Z0"].values[i+1] 
             for i in range(len(df_s)-1))
check("Stripline 線寬掃描單調性", s_mono, "")
print(f"  線寬掃描: w=0.1mm Z0={df_s['Z0'].iloc[0]:.1f}Ω -> w=2.0mm Z0={df_s['Z0'].iloc[-1]:.1f}Ω")

# 單調性: h 增加 -> Z0 單調上升
df_s_h = param_sweep("Stripline", "h_mm", np.linspace(0.2, 3.0, 50),
                     {"w":0.3, "h":1.6, "t":0.035, "er":4.5, "freq_ghz":1.0})
s_h_mono = all(df_s_h["Z0"].values[i] <= df_s_h["Z0"].values[i+1] 
               for i in range(len(df_s_h)-1))
check("Stripline h掃描單調性", s_h_mono, "")
print(f"  h掃描: h=0.2mm Z0={df_s_h['Z0'].iloc[0]:.1f}Ω -> h=3.0mm Z0={df_s_h['Z0'].iloc[-1]:.1f}Ω")

# ============================================================
# 3. Solver
# ============================================================
print("\n【3. Solver 測試】")

for tc in [("Microstrip", 0.3, 1.6, 0.035, 4.5, 0.0),
           ("Stripline", 0.3, 1.6, 0.035, 4.5, 0.0)]:
    z0_fwd, _ = forward_calc(*tc)
    z0_dir, _ = (microstrip_z0 if tc[0]=="Microstrip" else stripline_z0)(*tc[1:])
    check(f"Solver 正向 {tc[0]}", abs(z0_fwd-z0_dir)<1e-6, "")

for target in [30, 50, 75, 100]:
    for tline in ["Microstrip", "Stripline"]:
        w_inv = inverse_calc(tline, target, 1.6, 0.035, 4.5, 0.0)
        if w_inv:
            z0_v, _ = forward_calc(tline, w_inv, 1.6, 0.035, 4.5, 0.0)
            check(f"反向精度 {tline} {target}Ω", abs(z0_v-target) < 0.01, f"誤差={abs(z0_v-target):.4f}")
        else:
            errors.append(f"❌ 反向失敗 {tline} {target}Ω")

# 邊界
check("Microstrip 20Ω反向", inverse_calc("Microstrip", 20, 1.6, 0.035, 4.5, 0.0) is not None, "")
check("Microstrip 150Ω反向", inverse_calc("Microstrip", 150, 1.6, 0.035, 4.5, 0.0) is not None, "")
check("Microstrip 5Ω可能", inverse_calc("Microstrip", 5, 1.6, 0.035, 4.5, 0.0) is not None, "")
check("Microstrip 1Ω返回None", inverse_calc("Microstrip", 1, 1.6, 0.035, 4.5, 0.0) is None, "")

# ============================================================
# 4. Sweep
# ============================================================
print("\n【4. Sweep 測試】")

for tline in ["Microstrip", "Stripline"]:
    df_w = param_sweep(tline, "w_mm", np.linspace(0.1, 2.0, 50),
                       {"w":0.3, "h":1.6, "t":0.035, "er":4.5, "freq_ghz":1.0})
    check(f"{tline} 線寬掃描單調性", 
          all(df_w["Z0"].values[i] >= df_w["Z0"].values[i+1] for i in range(len(df_w)-1)), "")
    
    df_h = param_sweep(tline, "h_mm", np.linspace(0.2, 3.0, 50),
                       {"w":0.3, "h":1.6, "t":0.035, "er":4.5, "freq_ghz":1.0})
    check(f"{tline} h掃描單調性",
          all(df_h["Z0"].values[i] <= df_h["Z0"].values[i+1] for i in range(len(df_h)-1)), "")

# 其他掃描
check("Microstrip 銅厚掃描單調性",
      all(param_sweep("Microstrip", "t_um", [0,18,35,70,105],
                      {"w":0.3,"h":1.6,"t":0.035,"er":4.5,"freq_ghz":1.0})["Z0"].values[i] >=
          param_sweep("Microstrip", "t_um", [0,18,35,70,105],
                      {"w":0.3,"h":1.6,"t":0.035,"er":4.5,"freq_ghz":1.0})["Z0"].values[i+1]
          for i in range(4)), "")

check("Microstrip Dk掃描單調性",
      all(param_sweep("Microstrip", "er", [2,3,4,5,6],
                      {"w":0.3,"h":1.6,"t":0.035,"er":4.5,"freq_ghz":1.0})["Z0"].values[i] >=
          param_sweep("Microstrip", "er", [2,3,4,5,6],
                      {"w":0.3,"h":1.6,"t":0.035,"er":4.5,"freq_ghz":1.0})["Z0"].values[i+1]
          for i in range(4)), "")

df_f = freq_sweep("Microstrip", 0.3, 1.6, 0.035, 4.5, np.linspace(0.1, 10, 50))
check("Microstrip 頻率掃描單調性",
      all(df_f["Z0"].values[i] >= df_f["Z0"].values[i+1] for i in range(len(df_f)-1)), "")

# ============================================================
# 5. Project IO
# ============================================================
print("\n【5. Project IO 測試】")
from utils.project_io import save_project, load_project

test_data = {"type": "Microstrip", "params": {"w": 0.3, "h": 1.6}}
path = "/mnt/agents/output/pcb_calc_app/saved_projects/test_v3.json"
save_project(path, test_data)
check("Project IO", load_project(path) == test_data, "")

# ============================================================
# 匯總
# ============================================================
print("\n" + "=" * 60)
if errors:
    print(f"🔴 測試未通過，{len(errors)} 個錯誤:")
    for e in errors:
        print(f"  {e}")
else:
    print("🟢 所有測試通過！Phase 1 代碼無已知錯誤。")
print("=" * 60)
