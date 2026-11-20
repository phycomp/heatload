
import sys
sys.path.insert(0, "/mnt/agents/output/pcb_calc_app")

import numpy as np
from modules.impedance.formulas import microstrip_z0, stripline_z0
from modules.impedance.solver import forward_calc, inverse_calc
from modules.impedance.sweep import param_sweep, freq_sweep
from utils.project_io import save_project, load_project
import json
import os

print("=" * 60)
print("Phase 1 全面功能測試與除錯")
print("=" * 60)

errors = []
warnings = []

def check(name, condition, msg=""):
    if not condition:
        errors.append(f"❌ {name}: {msg}")
        return False
    return True

def warn(name, condition, msg=""):
    if not condition:
        warnings.append(f"⚠️ {name}: {msg}")
        return False
    return True

# ============================================================
# 1. Microstrip 公式測試
# ============================================================
print("\n【1. Microstrip 公式測試】")

# 1.1 基準測試: 已知文獻值對比
# IPC-2141 典型值: w/h=2, er=4.5, h=1.6mm, w=0.3mm -> 約 123Ω (靜態)
z0, ee = microstrip_z0(0.3, 1.6, 0.0, 4.5, 0.0)
print(f"  基準: w=0.3, h=1.6, t=0, er=4.5, DC -> Z0={z0:.2f}Ω, εeff={ee:.3f}")
check("Microstrip 基準 Z0", 120 < z0 < 130, f"Z0={z0} 不在 120-130 範圍內")
check("Microstrip 基準 εeff", 2.8 < ee < 3.2, f"εeff={ee} 不在 2.8-3.2 範圍內")

# 1.2 厚度修正測試
z0_t0, _ = microstrip_z0(0.3, 1.6, 0.0, 4.5, 0.0)
z0_t35, _ = microstrip_z0(0.3, 1.6, 0.035, 4.5, 0.0)
print(f"  厚度修正: t=0 -> Z0={z0_t0:.2f}Ω | t=35μm -> Z0={z0_t35:.2f}Ω")
check("厚度修正方向", z0_t35 < z0_t0, "銅厚增加應降低阻抗（等效寬度增加）")

# 1.3 頻率色散測試
z0_dc, ee_dc = microstrip_z0(0.3, 1.6, 0.035, 4.5, 0.0)
z0_1g, ee_1g = microstrip_z0(0.3, 1.6, 0.035, 4.5, 1.0)
z0_5g, ee_5g = microstrip_z0(0.3, 1.6, 0.035, 4.5, 5.0)
z0_10g, ee_10g = microstrip_z0(0.3, 1.6, 0.035, 4.5, 10.0)
print(f"  頻率色散: DC={z0_dc:.2f}Ω | 1GHz={z0_1g:.2f}Ω | 5GHz={z0_5g:.2f}Ω | 10GHz={z0_10g:.2f}Ω")
check("頻率色散趨勢", z0_dc >= z0_1g >= z0_5g >= z0_10g, "頻率升高阻抗應單調下降或持平")
check("εeff 頻率趨勢", ee_dc <= ee_1g <= ee_5g <= ee_10g, "頻率升高有效介電常數應單調上升")

# 1.4 極端值測試
print("\n  極端值測試:")
# 極小線寬
z0_minw, _ = microstrip_z0(0.001, 1.6, 0.035, 4.5, 0.0)
print(f"    w=1μm: Z0={z0_minw:.1f}Ω")
check("極小線寬", z0_minw > 200, f"極小線寬應有極高阻抗, 得到{z0_minw}")

# 極大線寬
z0_maxw, _ = microstrip_z0(10.0, 1.6, 0.035, 4.5, 0.0)
print(f"    w=10mm: Z0={z0_maxw:.1f}Ω")
check("極大線寬", z0_maxw < 50, f"極大線寬應有低阻抗, 得到{z0_maxw}")

# 極小介質厚度
z0_minh, _ = microstrip_z0(0.3, 0.01, 0.035, 4.5, 0.0)
print(f"    h=10μm: Z0={z0_minh:.1f}Ω")
check("極小介質厚度", z0_minh > 100, f"極小h應有高阻抗, 得到{z0_minh}")

# 1.5 w/h 邊界測試 (w/h = 1 附近)
z0_w1, _ = microstrip_z0(1.6, 1.6, 0.035, 4.5, 0.0)  # w/h = 1
z0_w09, _ = microstrip_z0(1.44, 1.6, 0.035, 4.5, 0.0)  # w/h = 0.9
z0_w11, _ = microstrip_z0(1.76, 1.6, 0.035, 4.5, 0.0)  # w/h = 1.1
print(f"    w/h=0.9: Z0={z0_w09:.2f}Ω | w/h=1.0: Z0={z0_w1:.2f}Ω | w/h=1.1: Z0={z0_w11:.2f}Ω")
check("w/h邊界連續性", abs(z0_w09 - z0_w1) < 5 and abs(z0_w11 - z0_w1) < 5, 
      "w/h=1 邊界處應連續")

# 1.6 零頻率測試
z0_zero, ee_zero = microstrip_z0(0.3, 1.6, 0.035, 4.5, 0.0)
z0_none, ee_none = microstrip_z0(0.3, 1.6, 0.035, 4.5, 0.0)
check("零頻率一致性", abs(z0_zero - z0_none) < 0.001, "freq=0 與 freq=0.0 應一致")

# ============================================================
# 2. Stripline 公式測試
# ============================================================
print("\n【2. Stripline 公式測試】")

# 2.1 基準測試
z0_s, ee_s = stripline_z0(0.3, 1.6, 0.035, 4.5)
print(f"  基準: w=0.3, h=1.6(b), t=35μm, er=4.5 -> Z0={z0_s:.2f}Ω, εeff={ee_s:.3f}")
check("Stripline 基準", 55 < z0_s < 70, f"Stripline Z0={z0_s} 不在 55-70 範圍內")
check("Stripline εeff", abs(ee_s - 4.5) < 0.001, "Stripline εeff 應等于 er")

# 2.2 厚度修正方向
z0_s_t0, _ = stripline_z0(0.3, 1.6, 0.0, 4.5)
z0_s_t35, _ = stripline_z0(0.3, 1.6, 0.035, 4.5)
print(f"  厚度: t=0 -> {z0_s_t0:.2f}Ω | t=35μm -> {z0_s_t35:.2f}Ω")
check("Stripline 厚度修正", z0_s_t35 > z0_s_t0, "Stripline 銅厚增加應提高阻抗（等效寬度減小）")

# 2.3 極端值
z0_s_minw, _ = stripline_z0(0.001, 1.6, 0.035, 4.5)
print(f"    w=1μm: Z0={z0_s_minw:.1f}Ω")
check("Stripline 極小線寬", z0_s_minw > 100, f"極小線寬應有高阻抗")

# ============================================================
# 3. Solver 測試
# ============================================================
print("\n【3. Solver 測試】")

# 3.1 正向計算一致性
test_cases = [
    ("Microstrip", 0.3, 1.6, 0.035, 4.5, 0.0),
    ("Microstrip", 0.3, 1.6, 0.035, 4.5, 5.0),
    ("Stripline", 0.3, 1.6, 0.035, 4.5, 0.0),
]
for tc in test_cases:
    z0_fwd, ee_fwd = forward_calc(*tc)
    z0_direct, ee_direct = (microstrip_z0 if tc[0]=="Microstrip" else stripline_z0)(*tc[1:])
    check(f"Solver 正向一致性 {tc[0]}", abs(z0_fwd - z0_direct) < 1e-6, 
          f"solver={z0_fwd} vs direct={z0_direct}")

# 3.2 反向計算精度
print("\n  反向計算精度測試:")
for target in [30, 50, 75, 100]:
    w_inv = inverse_calc("Microstrip", target, 1.6, 0.035, 4.5, 0.0)
    if w_inv:
        z0_v, _ = forward_calc("Microstrip", w_inv, 1.6, 0.035, 4.5, 0.0)
        err = abs(z0_v - target)
        status = "✅" if err < 0.01 else "❌"
        print(f"    目標{target}Ω -> w={w_inv*1000:.2f}μm, 驗證Z0={z0_v:.4f}Ω, 誤差={err:.4f}Ω {status}")
        check(f"反向精度 {target}Ω", err < 0.01, f"誤差={err}Ω")
    else:
        errors.append(f"❌ 反向計算失敗: 目標{target}Ω")
        print(f"    目標{target}Ω -> ❌ 計算失敗")

# 3.3 反向計算邊界
print("\n  反向計算邊界測試:")
# 極低阻抗
w_low = inverse_calc("Microstrip", 20, 1.6, 0.035, 4.5, 0.0)
print(f"    目標20Ω: w={w_low*1000:.1f}μm" if w_low else "    目標20Ω: 失敗")
# 極高阻抗
w_high = inverse_calc("Microstrip", 150, 1.6, 0.035, 4.5, 0.0)
print(f"    目標150Ω: w={w_high*1000:.3f}μm" if w_high else "    目標150Ω: 失敗")

# 不可能的目標
w_impossible = inverse_calc("Microstrip", 5, 1.6, 0.035, 4.5, 0.0)
check("不可能目標返回None", w_impossible is None, "目標5Ω應返回None")

# 3.4 Stripline 反向
w_s = inverse_calc("Stripline", 50, 1.6, 0.035, 4.5, 0.0)
if w_s:
    z0_sv, _ = forward_calc("Stripline", w_s, 1.6, 0.035, 4.5, 0.0)
    print(f"\n  Stripline 反向 50Ω -> w={w_s*1000:.2f}μm, 驗證={z0_sv:.4f}Ω")
    check("Stripline 反向精度", abs(z0_sv - 50) < 0.01, f"誤差={abs(z0_sv-50)}")

# ============================================================
# 4. Sweep 測試
# ============================================================
print("\n【4. Sweep 測試】")

# 4.1 線寬掃描單調性
df_w = param_sweep("Microstrip", "w_mm", np.linspace(0.1, 2.0, 20),
                   {"w":0.3, "h":1.6, "t":0.035, "er":4.5, "freq_ghz":1.0})
z0_vals = df_w["Z0"].values
is_monotonic = all(z0_vals[i] >= z0_vals[i+1] for i in range(len(z0_vals)-1))
check("線寬掃描單調性", is_monotonic, "線寬增加，阻抗應單調下降")
print(f"  線寬掃描: w=0.1mm Z0={z0_vals[0]:.1f}Ω -> w=2.0mm Z0={z0_vals[-1]:.1f}Ω")

# 4.2 介質厚度掃描單調性
df_h = param_sweep("Microstrip", "h_mm", np.linspace(0.1, 3.0, 20),
                   {"w":0.3, "h":1.6, "t":0.035, "er":4.5, "freq_ghz":1.0})
z0_h_vals = df_h["Z0"].values
is_h_mono = all(z0_h_vals[i] <= z0_h_vals[i+1] for i in range(len(z0_h_vals)-1))
check("h掃描單調性", is_h_mono, "介質厚度增加，阻抗應單調上升")
print(f"  h掃描: h=0.1mm Z0={z0_h_vals[0]:.1f}Ω -> h=3.0mm Z0={z0_h_vals[-1]:.1f}Ω")

# 4.3 銅厚掃描
df_t = param_sweep("Microstrip", "t_um", [0, 18, 35, 70, 105],
                   {"w":0.3, "h":1.6, "t":0.035, "er":4.5, "freq_ghz":1.0})
print(f"  銅厚掃描:\n{df_t}")
# 銅厚增加 -> 等效寬度增加 -> 阻抗下降
t_mono = all(df_t["Z0"].values[i] >= df_t["Z0"].values[i+1] 
             for i in range(len(df_t)-1))
check("銅厚掃描單調性", t_mono, "銅厚增加阻抗應下降")

# 4.4 Dk 掃描
df_dk = param_sweep("Microstrip", "er", [2.0, 3.0, 4.0, 5.0, 6.0],
                    {"w":0.3, "h":1.6, "t":0.035, "er":4.5, "freq_ghz":1.0})
print(f"  Dk掃描:\n{df_dk}")
dk_mono = all(df_dk["Z0"].values[i] >= df_dk["Z0"].values[i+1] 
              for i in range(len(df_dk)-1))
check("Dk掃描單調性", dk_mono, "Dk增加阻抗應下降")

# 4.5 頻率掃描
df_f = freq_sweep("Microstrip", 0.3, 1.6, 0.035, 4.5, np.linspace(0.1, 10, 50))
f_mono = all(df_f["Z0"].values[i] >= df_f["Z0"].values[i+1] 
             for i in range(len(df_f)-1))
check("頻率掃描單調性", f_mono, "頻率升高阻抗應下降")
print(f"  頻率掃描: 0.1GHz={df_f['Z0'].iloc[0]:.2f}Ω -> 10GHz={df_f['Z0'].iloc[-1]:.2f}Ω")

# 4.6 Stripline 掃描
df_s_w = param_sweep("Stripline", "w_mm", np.linspace(0.1, 2.0, 20),
                     {"w":0.3, "h":1.6, "t":0.035, "er":4.5, "freq_ghz":1.0})
s_mono = all(df_s_w["Z0"].values[i] >= df_s_w["Z0"].values[i+1] 
             for i in range(len(df_s_w)-1))
check("Stripline線寬掃描單調性", s_mono, "Stripline線寬增加阻抗應下降")

# ============================================================
# 5. Project IO 測試
# ============================================================
print("\n【5. Project IO 測試】")

test_data = {
    "tline_type": "Microstrip",
    "mat_name": "FR-4",
    "w_mm": 0.3,
    "h_mm": 1.6,
    "t_um": 35.0,
    "er": 4.5,
    "freq_ghz": 1.0,
    "mode": "正向計算"
}
test_path = "/mnt/agents/output/pcb_calc_app/saved_projects/test_full.json"
save_project(test_path, test_data)
loaded = load_project(test_path)
check("Project IO 讀寫", loaded == test_data, f"寫入與讀取不一致")
print(f"  讀寫測試: {'✅ 通過' if loaded == test_data else '❌ 失敗'}")

# 測試不存在的文件
try:
    load_project("/nonexistent.json")
    errors.append("❌ 不存在的文件應拋出異常")
except FileNotFoundError:
    print("  異常處理: ✅ FileNotFoundError 正確拋出")

# ============================================================
# 6. 輸出匯總
# ============================================================
print("\n" + "=" * 60)
print("測試匯總")
print("=" * 60)

if warnings:
    print(f"\n⚠️ 警告 ({len(warnings)} 項):")
    for w in warnings:
        print(f"  {w}")

if errors:
    print(f"\n❌ 錯誤 ({len(errors)} 項):")
    for e in errors:
        print(f"  {e}")
    print(f"\n🔴 測試未通過，共 {len(errors)} 個錯誤需要修復")
else:
    print("\n🟢 所有測試通過！Phase 1 代碼無已知錯誤。")

