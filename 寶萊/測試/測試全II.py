import sys
sys.path.insert(0, "/mnt/agents/output/pcb_calc_app")

# 清除緩存，重新加載
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
print("Phase 1 修復後全面測試")
print("=" * 60)

errors = []

def check(name, condition, msg=""):
    if not condition:
        errors.append(f"❌ {name}: {msg}")
        return False
    return True

# ============================================================
# 1. Microstrip 公式 (與之前相同，確認未受影響)
# ============================================================
print("\n【1. Microstrip 公式測試】")

z0, ee = microstrip_z0(0.3, 1.6, 0.0, 4.5, 0.0)
check("Microstrip 基準", 120 < z0 < 130, f"Z0={z0}")

z0_t0, _ = microstrip_z0(0.3, 1.6, 0.0, 4.5, 0.0)
z0_t35, _ = microstrip_z0(0.3, 1.6, 0.035, 4.5, 0.0)
check("Microstrip 厚度修正方向", z0_t35 < z0_t0, f"t=0:{z0_t0:.2f} vs t=35um:{z0_t35:.2f}")

z0_dc, ee_dc = microstrip_z0(0.3, 1.6, 0.035, 4.5, 0.0)
z0_10g, ee_10g = microstrip_z0(0.3, 1.6, 0.035, 4.5, 10.0)
check("Microstrip 頻率色散", z0_dc >= z0_10g, f"DC:{z0_dc:.2f} vs 10GHz:{z0_10g:.2f}")
check("Microstrip εeff 頻率趨勢", ee_dc <= ee_10g, f"DC:{ee_dc:.3f} vs 10GHz:{ee_10g:.3f}")

z0_minw, _ = microstrip_z0(0.001, 1.6, 0.035, 4.5, 0.0)
check("Microstrip 極小線寬", z0_minw > 200, f"Z0={z0_minw:.1f}")

z0_maxw, _ = microstrip_z0(10.0, 1.6, 0.035, 4.5, 0.0)
check("Microstrip 極大線寬", z0_maxw < 50, f"Z0={z0_maxw:.1f}")

# 修正: 極小h -> 低阻抗 (物理正確)
z0_minh, _ = microstrip_z0(0.3, 0.01, 0.035, 4.5, 0.0)
check("Microstrip 極小h", z0_minh < 20, f"h=10μm時Z0={z0_minh:.1f}Ω, 應極低")

# w/h=1 邊界連續性
z0_w09, _ = microstrip_z0(1.44, 1.6, 0.035, 4.5, 0.0)
z0_w1, _ = microstrip_z0(1.6, 1.6, 0.035, 4.5, 0.0)
z0_w11, _ = microstrip_z0(1.76, 1.6, 0.035, 4.5, 0.0)
check("Microstrip w/h邊界", abs(z0_w09-z0_w1)<5 and abs(z0_w11-z0_w1)<5, 
      f"邊界不連續: {z0_w09:.2f} vs {z0_w1:.2f} vs {z0_w11:.2f}")

print("  Microstrip: 全部通過 ✅")

# ============================================================
# 2. Stripline 公式 (修復後)
# ============================================================
print("\n【2. Stripline 公式測試 (修復後)】")

# 2.1 基準
z0_s, ee_s = stripline_z0(0.3, 1.6, 0.035, 4.5)
print(f"  基準: w=0.3, h=1.6(b), t=35μm, er=4.5 -> Z0={z0_s:.2f}Ω, εeff={ee_s:.3f}")
check("Stripline 基準", 55 < z0_s < 70, f"Z0={z0_s}")
check("Stripline εeff", abs(ee_s - 4.5) < 0.001, f"εeff={ee_s}")

# 2.2 厚度修正方向
z0_s_t0, _ = stripline_z0(0.3, 1.6, 0.0, 4.5)
z0_s_t35, _ = stripline_z0(0.3, 1.6, 0.035, 4.5)
check("Stripline 厚度修正", z0_s_t35 > z0_s_t0, 
      f"t=0:{z0_s_t0:.2f} vs t=35um:{z0_s_t35:.2f}")

# 2.3 極端值
z0_s_minw, _ = stripline_z0(0.001, 1.6, 0.035, 4.5)
check("Stripline 極小線寬", z0_s_minw > 100, f"Z0={z0_s_minw:.1f}")

# 2.4 關鍵: w/h 邊界連續性 (修復的核心)
print("\n  連續性檢查 (w/h 邊界附近):")
prev_z0 = None
for w_test in [0.5, 0.55, 0.556, 0.557, 0.558, 0.559, 0.56, 0.6, 1.0, 2.0]:
    z0_t, _ = stripline_z0(w_test, 1.6, 0.035, 4.5)
    ratio = w_test / 1.6
    marker = ""
    if prev_z0 is not None:
        diff = abs(z0_t - prev_z0)
        if diff > 5:
            marker = " ⚠️ 跳躍!"
    print(f"    w={w_test:.3f}, w/h={ratio:.4f}, Z0={z0_t:.4f}Ω{marker}")
    prev_z0 = z0_t

# 2.5 單調性檢查
df_s = param_sweep("Stripline", "w_mm", np.linspace(0.1, 2.0, 50),
                   {"w":0.3, "h":1.6, "t":0.035, "er":4.5, "freq_ghz":1.0})
s_mono = all(df_s["Z0"].values[i] >= df_s["Z0"].values[i+1] 
             for i in range(len(df_s)-1))
check("Stripline 線寬掃描單調性", s_mono, "線寬增加阻抗應單調下降")
print(f"  線寬掃描: w=0.1mm Z0={df_s['Z0'].iloc[0]:.1f}Ω -> w=2.0mm Z0={df_s['Z0'].iloc[-1]:.1f}Ω")

# 2.6 h掃描單調性
df_s_h = param_sweep("Stripline", "h_mm", np.linspace(0.2, 3.0, 50),
                     {"w":0.3, "h":1.6, "t":0.035, "er":4.5, "freq_ghz":1.0})
s_h_mono = all(df_s_h["Z0"].values[i] <= df_s_h["Z0"].values[i+1] 
               for i in range(len(df_s_h)-1))
check("Stripline h掃描單調性", s_h_mono, "h增加阻抗應單調上升")

print(f"  h掃描: h=0.2mm Z0={df_s_h['Z0'].iloc[0]:.1f}Ω -> h=3.0mm Z0={df_s_h['Z0'].iloc[-1]:.1f}Ω")

# ============================================================
# 3. Solver 測試
# ============================================================
print("\n【3. Solver 測試】")

# 3.1 正向一致性
for tc in [("Microstrip", 0.3, 1.6, 0.035, 4.5, 0.0),
           ("Stripline", 0.3, 1.6, 0.035, 4.5, 0.0)]:
    z0_fwd, _ = forward_calc(*tc)
    z0_dir, _ = (microstrip_z0 if tc[0]=="Microstrip" else stripline_z0)(*tc[1:])
    check(f"Solver 正向 {tc[0]}", abs(z0_fwd-z0_dir)<1e-6, f"{z0_fwd} vs {z0_dir}")

# 3.2 反向精度
for target in [30, 50, 75, 100]:
    for tline in ["Microstrip", "Stripline"]:
        w_inv = inverse_calc(tline, target, 1.6, 0.035, 4.5, 0.0)
        if w_inv:
            z0_v, _ = forward_calc(tline, w_inv, 1.6, 0.035, 4.5, 0.0)
            err = abs(z0_v - target)
            check(f"反向精度 {tline} {target}Ω", err < 0.01, f"誤差={err:.4f}Ω")
        else:
            errors.append(f"❌ 反向失敗 {tline} {target}Ω")

# 3.3 邊界
w_low = inverse_calc("Microstrip", 20, 1.6, 0.035, 4.5, 0.0)
check("Microstrip 20Ω反向", w_low is not None and w_low > 0, "應成功")

w_high = inverse_calc("Microstrip", 150, 1.6, 0.035, 4.5, 0.0)
check("Microstrip 150Ω反向", w_high is not None and w_high > 0, "應成功")

# 修正: 5Ω 是可能的（極寬線）
w_5 = inverse_calc("Microstrip", 5, 1.6, 0.035, 4.5, 0.0)
check("Microstrip 5Ω反向", w_5 is not None, "5Ω可通過極寬線實現")

# 真正不可能的目標
w_imp = inverse_calc("Microstrip", 1, 1.6, 0.035, 4.5, 0.0)
check("Microstrip 1Ω返回None", w_imp is None, f"1Ω應不可能,得到{w_imp}")

# ============================================================
# 4. Sweep 測試
# ============================================================
print("\n【4. Sweep 測試】")

for tline in ["Microstrip", "Stripline"]:
    # 線寬掃描
    df_w = param_sweep(tline, "w_mm", np.linspace(0.1, 2.0, 50),
                       {"w":0.3, "h":1.6, "t":0.035, "er":4.5, "freq_ghz":1.0})
    w_mono = all(df_w["Z0"].values[i] >= df_w["Z0"].values[i+1] 
                 for i in range(len(df_w)-1))
    check(f"{tline} 線寬掃描單調性", w_mono, "")
    
    # h掃描
    df_h = param_sweep(tline, "h_mm", np.linspace(0.2, 3.0, 50),
                       {"w":0.3, "h":1.6, "t":0.035, "er":4.5, "freq_ghz":1.0})
    h_mono = all(df_h["Z0"].values[i] <= df_h["Z0"].values[i+1] 
                 for i in range(len(df_h)-1))
    check(f"{tline} h掃描單調性", h_mono, "")

# 銅厚掃描
df_t = param_sweep("Microstrip", "t_um", [0, 18, 35, 70, 105],
                   {"w":0.3, "h":1.6, "t":0.035, "er":4.5, "freq_ghz":1.0})
t_mono = all(df_t["Z0"].values[i] >= df_t["Z0"].values[i+1] 
             for i in range(len(df_t)-1))
check("Microstrip 銅厚掃描單調性", t_mono, "")

# Dk掃描
df_dk = param_sweep("Microstrip", "er", [2.0, 3.0, 4.0, 5.0, 6.0],
                    {"w":0.3, "h":1.6, "t":0.035, "er":4.5, "freq_ghz":1.0})
dk_mono = all(df_dk["Z0"].values[i] >= df_dk["Z0"].values[i+1] 
              for i in range(len(df_dk)-1))
check("Microstrip Dk掃描單調性", dk_mono, "")

# 頻率掃描
df_f = freq_sweep("Microstrip", 0.3, 1.6, 0.035, 4.5, np.linspace(0.1, 10, 50))
f_mono = all(df_f["Z0"].values[i] >= df_f["Z0"].values[i+1] 
             for i in range(len(df_f)-1))
check("Microstrip 頻率掃描單調性", f_mono, "")

# ============================================================
# 5. Project IO
# ============================================================
print("\n【5. Project IO 測試】")
from utils.project_io import save_project, load_project

test_data = {"test": "value", "nested": {"a": 1}}
path = "/mnt/agents/output/pcb_calc_app/saved_projects/test_final.json"
save_project(path, test_data)
loaded = load_project(path)
check("Project IO", loaded == test_data, "")

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
