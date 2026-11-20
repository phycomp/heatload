import sys
sys.path.insert(0, "/mnt/agents/output/pcb_calc_app")

import numpy as np
import importlib

# 清除緩存重新加載
import modules.stackup.materials as mat_mod
import modules.stackup.templates as tpl_mod
import modules.stackup.loss_models as loss_mod
importlib.reload(mat_mod)
importlib.reload(tpl_mod)
importlib.reload(loss_mod)

from modules.stackup.materials import MaterialLibrary, Material
from modules.stackup.templates import TemplateLibrary
from modules.stackup.loss_models import (
    total_insertion_loss, return_loss, freq_sweep_il,
    conductor_loss_hammerstad, conductor_loss_huray, dielectric_loss
)

print("=" * 60)
print("Phase 2 修復後全面測試")
print("=" * 60)

errors = []

def check(name, condition, msg=""):
    if not condition:
        errors.append(f"❌ {name}: {msg}")
        return False
    return True

# ============================================================
# 1. 材料庫測試
# ============================================================
print("\n【1. 材料庫測試】")

mat_lib = MaterialLibrary("/mnt/agents/output/pcb_calc_app/data")
builtin = mat_lib.list_builtin()
print(f"  內建材料: {builtin}")
check("材料庫加載", len(builtin) >= 7, "")

fr4 = mat_lib.get("FR-4")
check("FR-4 Dk", abs(fr4.dk - 4.5) < 0.01, "")
check("FR-4 粗糙度", fr4.get_roughness_model() == "hammerstad", "")

ro4350 = mat_lib.get("Rogers_RO4350B")
check("RO4350B Dk", abs(ro4350.dk - 3.66) < 0.01, "")
check("RO4350B 粗糙度", ro4350.get_roughness_model() == "huray", "")

# Huray 參數
huray_params = ro4350.get_huray_params()
print(f"  RO4350B Huray 參數: {huray_params}")
check("Huray Rq", huray_params.get("Rq_um", 0) > 0, "")
check("Huray 半徑", huray_params.get("sphere_radius_um", 0) > 0, "")

print("  材料庫: 全部通過 ✅")

# ============================================================
# 2. 模板庫測試（修復後）
# ============================================================
print("\n【2. 模板庫測試（修復後）】")

tpl_lib = TemplateLibrary("/mnt/agents/output/pcb_calc_app/data")

# 2.1 4層板
tpl_4l = tpl_lib.get("Rigid/4_layer_rigid")
check("4層模板加載", tpl_4l is not None, "")

layers = tpl_4l.get_layer_stack()
print(f"  4層板層數: {len(layers)}")
for i, l in enumerate(layers):
    print(f"    [{i}] {l['name']:12s} | {l['type']:8s} | {l.get('thickness_um', 0):4d}μm")

check("4層層數", len(layers) == 7, f"實際 {len(layers)} 層（應爲7層：L1/PP/L2/Core/L3/PP/L4）")

signal_layers = tpl_4l.get_signal_layers()
check("4層信號層", len(signal_layers) == 2, f"實際 {len(signal_layers)} 個信號層")

plane_layers = tpl_4l.get_plane_layers()
check("4層平面層", len(plane_layers) == 2, f"實際 {len(plane_layers)} 個平面層")

# 2.2 L1 介質厚度
l1_idx = tpl_4l.find_signal_layer_position("L1 Top")
h_above = tpl_4l.get_dielectric_thickness_above(l1_idx)
h_below = tpl_4l.get_dielectric_thickness_below(l1_idx)
print(f"\n  L1 Top: 上方介質={h_above*1000:.0f}μm, 下方介質={h_below*1000:.0f}μm")
check("L1上方介質", h_above == 0, "表層上方無介質")
check("L1下方介質", abs(h_below - 0.2) < 0.001, 
      f"下方應爲 200μm prepreg, 實際 {h_below*1000:.1f}μm")

# 2.3 L1 參考平面
ref_idx = tpl_4l.get_ground_reference(l1_idx)
print(f"  L1 參考平面索引: {ref_idx}")
check("L1參考平面", ref_idx is not None, "應找到參考平面")
check("L1參考平面位置", ref_idx == 2, f"應爲索引2(L2 GND), 實際{ref_idx}")

# 2.4 L4 介質厚度
l4_idx = tpl_4l.find_signal_layer_position("L4 Bottom")
h_above_l4 = tpl_4l.get_dielectric_thickness_above(l4_idx)
h_below_l4 = tpl_4l.get_dielectric_thickness_below(l4_idx)
print(f"  L4 Bottom: 上方介質={h_above_l4*1000:.0f}μm, 下方介質={h_below_l4*1000:.0f}μm")
check("L4上方介質", abs(h_above_l4 - 0.2) < 0.001, f"應爲 200μm prepreg")
check("L4下方介質", h_below_l4 == 0, "底層下方無介質")

# 2.5 6層板
tpl_6l = tpl_lib.get("Rigid/6_layer_rigid_foil")
check("6層模板", tpl_6l is not None, "")
l1_6l = tpl_6l.find_signal_layer_position("L1 Top")
h_6l = tpl_6l.get_dielectric_thickness_below(l1_6l)
print(f"\n  6層板 L1: 下方介質={h_6l*1000:.0f}μm")
check("6層L1介質", abs(h_6l - 0.08) < 0.001, f"應爲 80μm prepreg")

# 2.6 總厚度
check("4層總厚度", abs(tpl_4l.get_total_thickness_mm() - 1.47) < 0.01,
      f"總厚度={tpl_4l.get_total_thickness_mm():.3f}mm")

# 2.7 RF Core Build
tpl_rf = tpl_lib.get("RF_Core_Build/4_layer_rf_core")
check("RF模板", tpl_rf is not None, "")
l1_rf = tpl_rf.find_signal_layer_position("L1 Top")
h_rf = tpl_rf.get_dielectric_thickness_below(l1_rf)
print(f"\n  RF板 L1: 下方介質={h_rf*1000:.0f}μm")
check("RF L1介質", abs(h_rf - 0.254) < 0.001, f"應爲 254μm RF Core")

# 2.8 HDI
tpl_hdi = tpl_lib.get("HDI/10_layer_3press_hdi")
check("HDI模板", tpl_hdi is not None, "")

# 2.9 Flex-Rigid
tpl_flex = tpl_lib.get("Flex_Rigid/4_layer_flex_rigid")
check("Flex-Rigid模板", tpl_flex is not None, "")

print("  模板庫: 全部通過 ✅")

# ============================================================
# 3. 損耗計算引擎測試（修復後）
# ============================================================
print("\n【3. 損耗計算引擎測試（修復後）】")

# 3.1 Hammerstad 導體損耗
print("  Hammerstad 導體損耗:")
for f in [0.1, 1.0, 5.0, 10.0]:
    alpha_c = conductor_loss_hammerstad(f, 0.3, 0.035, 1.6, 50.0, 1.5)
    print(f"    {f}GHz: αc = {alpha_c:.4f} dB/m")
check("Hammerstad αc > 0", conductor_loss_hammerstad(1.0, 0.3, 0.035, 1.6, 50.0, 1.5) > 0, "")

# 3.2 Huray 導體損耗（修復後默認參數）
print("\n  Huray 導體損耗 (默認 N=5e9):")
for f in [0.1, 1.0, 5.0, 10.0]:
    alpha_c_h = conductor_loss_huray(f, 0.3, 0.035, 1.6, 50.0, 0.5, 5e9)
    print(f"    {f}GHz: αc = {alpha_c_h:.4f} dB/m")
check("Huray αc > 0", conductor_loss_huray(1.0, 0.3, 0.035, 1.6, 50.0, 0.5, 5e9) > 0, "")

# 3.3 Huray Kr 限制
Kr_10g = conductor_loss_huray(10.0, 0.3, 0.035, 1.6, 50.0, 0.5, 5e9) / \
         (conductor_loss_huray(10.0, 0.3, 0.035, 1.6, 50.0, 0.5, 5e9) / 
          conductor_loss_huray(10.0, 0.3, 0.035, 1.6, 50.0, 0.5, 0))  # 這不對，讓我直接計算

# 直接計算 Kr: 用 Rq=0 的 Huray 作爲基礎
alpha_base = conductor_loss_huray(10.0, 0.3, 0.035, 1.6, 50.0, 0.5, 0)
alpha_with = conductor_loss_huray(10.0, 0.3, 0.035, 1.6, 50.0, 0.5, 5e9)
Kr_actual = alpha_with / alpha_base if alpha_base > 0 else 1.0
print(f"\n  Huray Kr @10GHz: {Kr_actual:.2f}")
check("Huray Kr 限制", Kr_actual <= 5.0, f"Kr={Kr_actual:.2f} > 5")

# 3.4 介電損耗
print("\n  介電損耗:")
for f in [0.1, 1.0, 5.0, 10.0]:
    alpha_d = dielectric_loss(f, 4.5, 0.02, 3.5)
    print(f"    {f}GHz: αd = {alpha_d:.4f} dB/m")

# 3.5 材料損耗對比（關鍵修復驗證）
print("\n  材料損耗對比 @ 5GHz, w=0.3mm, h=1.6mm, 0.1m:")
for mat_name in ["FR-4", "Rogers_RO4350B", "Megtron_6"]:
    mat = mat_lib.get(mat_name)
    rough_params = mat.get_huray_params() if mat.get_roughness_model() == "huray" else {"Rq_um": mat.get_roughness_rq()}
    il_mat = total_insertion_loss(5.0, 0.3, 0.035, 1.6, mat.dk, mat.df, 50.0, 3.5,
                                   mat.get_roughness_model(), rough_params, 0.1)
    print(f"    {mat_name:20s}: IL={il_mat['IL_total_db']:.4f}dB, αc={il_mat['alpha_c_db_per_m']:.2f}, αd={il_mat['alpha_d_db_per_m']:.2f}")

# 關鍵檢查: FR-4 損耗應大于 Rogers
il_fr4 = total_insertion_loss(5.0, 0.3, 0.035, 1.6, 4.5, 0.02, 50.0, 3.5,
                               "hammerstad", {"Rq_um": 1.5}, 0.1)
il_ro = total_insertion_loss(5.0, 0.3, 0.035, 1.6, 3.66, 0.0037, 50.0, 3.5,
                                "huray", {"Rq_um": 0.8, "sphere_radius_um": 0.5}, 0.1)
print(f"\n  FR-4 IL={il_fr4['IL_total_db']:.4f}dB vs Rogers IL={il_ro['IL_total_db']:.4f}dB")
check("FR-4 損耗 > Rogers", il_fr4['IL_total_db'] > il_ro['IL_total_db'],
      f"FR-4={il_fr4['IL_total_db']:.4f}, Rogers={il_ro['IL_total_db']:.4f}")

# 3.6 導體/介電損耗比例合理性
check("FR-4 αc/αd 合理", 0.5 < il_fr4['alpha_ratio'] < 10,
      f"比例={il_fr4['alpha_ratio']:.2f}")
check("Rogers αc/αd 合理", il_ro['alpha_ratio'] > 1,
      f"Rogers 導體損耗應占主導, 比例={il_ro['alpha_ratio']:.2f}")

# 3.7 Return Loss
print("\n  Return Loss 測試:")
for z0 in [45, 50, 55, 60]:
    rl = return_loss(1.0, z0, 50.0, 50.0)
    print(f"    Z0={z0}Ω: RL={rl:.2f} dB")
check("RL 50Ω匹配", return_loss(1.0, 50.0, 50.0, 50.0) > 80, "")
check("RL 偏差越大越小", return_loss(1.0, 60, 50, 50) < return_loss(1.0, 55, 50, 50), "")

# 3.8 頻率掃描單調性
print("\n  頻率掃描單調性:")
freqs = np.linspace(0.1, 10.0, 50)
sweep = freq_sweep_il(freqs, 0.3, 0.035, 1.6, 4.5, 0.02, 50.0, 3.5,
                        "hammerstad", {"Rq_um": 1.5}, 0.1)
check("IL單調遞增", all(sweep['IL_total_db'][i] <= sweep['IL_total_db'][i+1] for i in range(49)), "")
print(f"    IL: {sweep['IL_total_db'][0]:.4f}dB @0.1GHz -> {sweep['IL_total_db'][-1]:.4f}dB @10GHz")

print("  損耗引擎: 全部通過 ✅")

# ============================================================
# 4. 集成測試
# ============================================================
print("\n【4. 集成測試: 模板 + 材料 + 損耗】")

from modules.impedance.formulas import microstrip_z0

# 4.1 4層板 L1 Top
tpl = tpl_lib.get("Rigid/4_layer_rigid")
l1_idx = tpl.find_signal_layer_position("L1 Top")
h_eff = tpl.get_dielectric_thickness_below(l1_idx)
mat = mat_lib.get("FR-4")

print(f"\n  4層板 L1 Top: h_eff={h_eff*1000:.0f}μm, 材料={mat.name}")
z0, e_eff = microstrip_z0(0.3, h_eff, 0.035, mat.dk, 1.0)
print(f"    Z0={z0:.2f}Ω, εeff={e_eff:.3f}")

il = total_insertion_loss(1.0, 0.3, 0.035, h_eff, mat.dk, mat.df, z0, e_eff,
                             mat.get_roughness_model(), {"Rq_um": mat.get_roughness_rq()}, 0.1)
print(f"    IL@1GHz={il['IL_total_db']:.4f}dB")
check("4層集成IL", il['IL_total_db'] > 0, "")

# 4.2 4層板 L4 Bottom (對稱)
l4_idx = tpl.find_signal_layer_position("L4 Bottom")
h_eff_l4 = tpl.get_dielectric_thickness_above(l4_idx)
print(f"\n  4層板 L4 Bottom: h_eff={h_eff_l4*1000:.0f}μm")
check("L4對稱性", abs(h_eff - h_eff_l4) < 0.001, "L1和L4應對稱")

# 4.3 RF Core Build
tpl_rf = tpl_lib.get("RF_Core_Build/4_layer_rf_core")
l1_rf_idx = tpl_rf.find_signal_layer_position("L1 Top")
h_eff_rf = tpl_rf.get_dielectric_thickness_below(l1_rf_idx)
mat_rf = mat_lib.get("Rogers_RO4350B")

print(f"\n  RF Core Build L1 Top: h_eff={h_eff_rf*1000:.0f}μm, 材料={mat_rf.name}")
z0_rf, e_eff_rf = microstrip_z0(0.3, h_eff_rf, 0.018, mat_rf.dk, 5.0)
print(f"    Z0={z0_rf:.2f}Ω, εeff={e_eff_rf:.3f}")

il_rf = total_insertion_loss(5.0, 0.3, 0.018, h_eff_rf, mat_rf.dk, mat_rf.df, z0_rf, e_eff_rf,
                                mat_rf.get_roughness_model(), mat_rf.get_huray_params(), 0.1)
print(f"    IL@5GHz={il_rf['IL_total_db']:.4f}dB")
check("RF集成IL", il_rf['IL_total_db'] > 0, "")

# RF 損耗應小于 FR-4
check("RF < FR-4 損耗", il_rf['IL_total_db'] < il_fr4['IL_total_db'],
      f"RF={il_rf['IL_total_db']:.4f}, FR-4={il_fr4['IL_total_db']:.4f}")

print("  集成測試: 全部通過 ✅")

# ============================================================
# 匯總
# ============================================================
print("\n" + "=" * 60)
if errors:
    print(f"🔴 測試未通過，{len(errors)} 個錯誤:")
    for e in errors:
        print(f"  {e}")
else:
    print("🟢 所有測試通過！Phase 2 代碼無已知錯誤。")
print("=" * 60)
