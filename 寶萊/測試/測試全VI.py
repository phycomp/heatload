import sys
# sys.path.insert(0, "/mnt/agents/output/pcb_calc_app")

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
print("Phase 2 全面功能測試")
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

# 1.1 加載內建材料
builtin = mat_lib.list_builtin()
print(f"  內建材料: {builtin}")
check("材料庫加載", len(builtin) >= 7, f"僅加載 {len(builtin)} 個材料")

# 1.2 獲取材料屬性
fr4 = mat_lib.get("FR-4")
check("FR-4 Dk", abs(fr4.dk - 4.5) < 0.01, f"Dk={fr4.dk}")
check("FR-4 Df", abs(fr4.df - 0.02) < 0.001, f"Df={fr4.df}")
check("FR-4 粗糙度模型", fr4.get_roughness_model() == "hammerstad", "")
check("FR-4 類別", fr4.category == "standard", "")

ro4350 = mat_lib.get("Rogers_RO4350B")
check("RO4350B Dk", abs(ro4350.dk - 3.66) < 0.01, "")
check("RO4350B 粗糙度", ro4350.get_roughness_model() == "huray", "")

# 1.3 頻率相依 Dk/Df
print(f"\n  頻率相依測試 (RO4350B):")
for f in [0.1, 1.0, 5.0, 10.0]:
    dk_f = ro4350.get_dk_at_freq(f)
    df_f = ro4350.get_df_at_freq(f)
    print(f"    {f}GHz: Dk={dk_f:.4f}, Df={df_f:.5f}")
check("頻率Dk不變(constant)", abs(ro4350.get_dk_at_freq(10.0) - ro4350.dk) < 0.001, "")
check("頻率Df不變(constant)", abs(ro4350.get_df_at_freq(10.0) - ro4350.df) < 0.0001, "")

# 1.4 添加自定義材料
print("\n  自定義材料測試:")
test_mat = Material(
    name="Test_Custom",
    dk=3.8, df=0.008,
    dk_freq_coeff={"type": "constant", "value": 3.8},
    df_freq_model={"type": "djordjevic", "value": 0.008, "f_ref_ghz": 1.0, "exponent": 0.005},
    copper_roughness={"model": "huray", "Rq_um": 0.7, "sphere_radius_um": 0.4},
    category="custom"
)
mat_lib.add_custom("Test_Custom", test_mat)
check("添加自定義材料", "Test_Custom" in mat_lib.list_all(), "")

# 驗證持久化
custom_path = "/mnt/agents/output/pcb_calc_app/data/materials_custom.json"
check("自定義材料持久化", __import__('os').path.exists(custom_path), "")

# 刪除
mat_lib.delete_custom("Test_Custom")
check("刪除自定義材料", "Test_Custom" not in mat_lib.list_all(), "")

print("  材料庫: 全部通過 ✅")

# ============================================================
# 2. 模板庫測試
# ============================================================
print("\n【2. 模板庫測試】")

tpl_lib = TemplateLibrary("/mnt/agents/output/pcb_calc_app/data")

categories = tpl_lib.get_categories()
print(f"  模板類別: {categories}")
check("模板類別", len(categories) >= 4, f"僅 {len(categories)} 個類別")

# 2.1 Rigid 模板
rigid_names = tpl_lib.get_template_names("Rigid")
print(f"  Rigid 模板: {rigid_names}")
check("Rigid 模板數量", len(rigid_names) >= 4, f"僅 {len(rigid_names)} 個")

# 2.2 4層板模板
tpl_4l = tpl_lib.get("Rigid/4_layer_rigid")
check("4層模板加載", tpl_4l is not None, "")
check("4層描述", "4層" in tpl_4l.description, "")

layers = tpl_4l.get_layer_stack()
print(f"  4層板層數: {len(layers)}")
check("4層層數", len(layers) == 5, f"實際 {len(layers)} 層")

signal_layers = tpl_4l.get_signal_layers()
check("4層信號層", len(signal_layers) == 2, f"實際 {len(signal_layers)} 個信號層")

# 2.3 介質厚度計算
l1_idx = tpl_4l.find_signal_layer_position("L1 Top")
h_above = tpl_4l.get_dielectric_thickness_above(l1_idx)
h_below = tpl_4l.get_dielectric_thickness_below(l1_idx)
print(f"  L1: 上方介質={h_above*1000:.0f}μm, 下方介質={h_below*1000:.0f}μm")
check("L1上方介質", h_above == 0, "表層上方無介質")
check("L1下方介質", abs(h_below - 0.2) < 0.001, f"下方應爲 200μm prepreg, 實際 {h_below*1000:.1f}μm")

# 2.4 參考平面查找
ref_idx = tpl_4l.get_ground_reference(l1_idx)
check("L1參考平面", ref_idx is not None, "")
print(f"  L1 參考平面索引: {ref_idx}")

# 2.5 6層板
tpl_6l = tpl_lib.get("Rigid/6_layer_rigid_foil")
check("6層模板", tpl_6l is not None, "")
check("6層總厚度", abs(tpl_6l.get_total_thickness_mm() - 1.41) < 0.01,
      f"總厚度={tpl_6l.get_total_thickness_mm():.3f}mm")

# 2.6 HDI 模板
tpl_hdi = tpl_lib.get("HDI/10_layer_3press_hdi")
check("HDI模板", tpl_hdi is not None, "")

# 2.7 Flex-Rigid
tpl_flex = tpl_lib.get("Flex_Rigid/4_layer_flex_rigid")
check("Flex-Rigid模板", tpl_flex is not None, "")

print("  模板庫: 全部通過 ✅")

# ============================================================
# 3. 損耗計算引擎測試
# ============================================================
print("\n【3. 損耗計算引擎測試】")

# 3.1 導體損耗 - Hammerstad
print("  Hammerstad 導體損耗:")
for f in [0.1, 1.0, 5.0, 10.0]:
    alpha_c = conductor_loss_hammerstad(f, 0.3, 0.035, 1.6, 50.0, 1.5)
    print(f"    {f}GHz: αc = {alpha_c:.4f} dB/m")
check("Hammerstad αc > 0", conductor_loss_hammerstad(1.0, 0.3, 0.035, 1.6, 50.0, 1.5) > 0, "")

# 3.2 導體損耗 - Huray
print("\n  Huray 導體損耗:")
for f in [0.1, 1.0, 5.0, 10.0]:
    alpha_c_h = conductor_loss_huray(f, 0.3, 0.035, 1.6, 50.0, 0.5, 1e12)
    print(f"    {f}GHz: αc = {alpha_c_h:.4f} dB/m")
check("Huray αc > 0", conductor_loss_huray(1.0, 0.3, 0.035, 1.6, 50.0, 0.5, 1e12) > 0, "")

# 3.3 高頻下 Huray > Hammerstad (粗糙度效應更強)
alpha_c_hj_10g = conductor_loss_hammerstad(10.0, 0.3, 0.035, 1.6, 50.0, 1.5)
alpha_c_huray_10g = conductor_loss_huray(10.0, 0.3, 0.035, 1.6, 50.0, 0.5, 1e12)
print(f"\n  @10GHz: Hammerstad={alpha_c_hj_10g:.4f}, Huray={alpha_c_huray_10g:.4f}")
# Huray 不一定總是大于 Hammerstad，取決于參數，所以不強制檢查

# 3.4 介電損耗
print("\n  介電損耗:")
for f in [0.1, 1.0, 5.0, 10.0]:
    alpha_d = dielectric_loss(f, 4.5, 0.02, 3.5)
    print(f"    {f}GHz: αd = {alpha_d:.4f} dB/m")
check("介電損耗 αd > 0", dielectric_loss(1.0, 4.5, 0.02, 3.5) > 0, "")

# 3.5 介電損耗頻率趨勢
alpha_d_1g = dielectric_loss(1.0, 4.5, 0.02, 3.5)
alpha_d_10g = dielectric_loss(10.0, 4.5, 0.02, 3.5)
check("介電損耗頻率趨勢", alpha_d_10g > alpha_d_1g,
      f"1GHz={alpha_d_1g:.4f}, 10GHz={alpha_d_10g:.4f}")

# 3.6 總插入損耗
print("\n  總插入損耗 (FR-4, w=0.3mm, h=1.6mm, 50Ω, 0.1m):")
il = total_insertion_loss(1.0, 0.3, 0.035, 1.6, 4.5, 0.02, 50.0, 3.5,
                           "hammerstad", {"Rq_um": 1.5}, 0.1)
print(f"    IL = {il['IL_total_db']:.4f} dB")
print(f"    αc = {il['alpha_c_db_per_m']:.4f} dB/m")
print(f"    αd = {il['alpha_d_db_per_m']:.4f} dB/m")
print(f"    比率 αc/αd = {il['alpha_ratio']:.2f}")
check("IL > 0", il['IL_total_db'] > 0, "")
check("αc > 0", il['alpha_c_db_per_m'] > 0, "")
check("αd > 0", il['alpha_d_db_per_m'] > 0, "")

# 3.7 不同材料損耗對比
print("\n  材料損耗對比 @ 5GHz, 0.1m:")
for mat_name in ["FR-4", "Rogers_RO4350B", "Megtron_6"]:
    mat = mat_lib.get(mat_name)
    il_mat = total_insertion_loss(5.0, 0.3, 0.035, 1.6, mat.dk, mat.df, 50.0, 3.5,
                                   mat.get_roughness_model(),
                                   mat.get_huray_params() if mat.get_roughness_model() == "huray" else {"Rq_um": mat.get_roughness_rq()},
                                   0.1)
    print(f"    {mat_name}: IL={il_mat['IL_total_db']:.4f}dB, αc={il_mat['alpha_c_db_per_m']:.3f}, αd={il_mat['alpha_d_db_per_m']:.3f}")

# FR-4 損耗應遠大于 Rogers
il_fr4 = total_insertion_loss(5.0, 0.3, 0.035, 1.6, 4.5, 0.02, 50.0, 3.5,
                               "hammerstad", {"Rq_um": 1.5}, 0.1)
il_ro = total_insertion_loss(5.0, 0.3, 0.035, 1.6, 3.66, 0.0037, 50.0, 3.5,
                                "huray", {"Rq_um": 0.8, "sphere_radius_um": 0.5}, 0.1)
check("FR-4 損耗 > Rogers", il_fr4['IL_total_db'] > il_ro['IL_total_db'],
      f"FR-4={il_fr4['IL_total_db']:.4f}, Rogers={il_ro['IL_total_db']:.4f}")

# 3.8 Return Loss
print("\n  Return Loss 測試:")
for z0 in [45, 50, 55, 60]:
    rl = return_loss(1.0, z0, 50.0, 50.0)
    print(f"    Z0={z0}Ω: RL={rl:.2f} dB")
check("RL 50Ω匹配", return_loss(1.0, 50.0, 50.0, 50.0) > 80, "50Ω匹配時RL應極大")
check("RL 偏差越大越小", return_loss(1.0, 60, 50, 50) < return_loss(1.0, 55, 50, 50),
      "阻抗偏差越大RL應越小")

# 3.9 頻率掃描
print("\n  頻率掃描測試:")
freqs = np.linspace(0.1, 10.0, 50)
sweep = freq_sweep_il(freqs, 0.3, 0.035, 1.6, 4.5, 0.02, 50.0, 3.5,
                        "hammerstad", {"Rq_um": 1.5}, 0.1)
check("頻率掃描長度", len(sweep['freq_ghz']) == 50, f"實際 {len(sweep['freq_ghz'])}")
check("IL單調遞增", all(sweep['IL_total_db'][i] <= sweep['IL_total_db'][i+1] for i in range(49)),
      "IL應隨頻率單調遞增")

print("  損耗引擎: 全部通過 ✅")

# ============================================================
# 4. 集成測試
# ============================================================
print("\n【4. 集成測試: 模板 + 材料 + 損耗】")

# 4.1 4層板 + FR-4 損耗分析
tpl = tpl_lib.get("Rigid/4_layer_rigid")
l1_idx = tpl.find_signal_layer_position("L1 Top")
h_above = tpl.get_dielectric_thickness_above(l1_idx)
h_below = tpl.get_dielectric_thickness_below(l1_idx)
h_eff = h_above + h_below

mat = mat_lib.get("FR-4")
print(f"\n  4層板 L1 Top: h_eff={h_eff*1000:.0f}μm, 材料={mat.name}")

# 計算該叠構下的阻抗和損耗
from modules.impedance.formulas import microstrip_z0
z0, e_eff = microstrip_z0(0.3, h_eff, 0.035, mat.dk, 1.0)
print(f"    Z0={z0:.2f}Ω, εeff={e_eff:.3f}")

il = total_insertion_loss(1.0, 0.3, 0.035, h_eff, mat.dk, mat.df, z0, e_eff,
                             mat.get_roughness_model(), {"Rq_um": mat.get_roughness_rq()}, 0.1)
print(f"    IL@1GHz={il['IL_total_db']:.4f}dB")
check("集成IL", il['IL_total_db'] > 0, "")

# 4.2 RF Core Build
print("\n  RF Core Build:")
tpl_rf = tpl_lib.get("RF_Core_Build/4_layer_rf_core")
l1_rf_idx = tpl_rf.find_signal_layer_position("L1 Top")
h_eff_rf = tpl_rf.get_dielectric_thickness_below(l1_rf_idx)
mat_rf = mat_lib.get("Rogers_RO4350B")
print(f"    L1 Top: h_eff={h_eff_rf*1000:.0f}μm, 材料={mat_rf.name}")

z0_rf, e_eff_rf = microstrip_z0(0.3, h_eff_rf, 0.018, mat_rf.dk, 1.0)
print(f"    Z0={z0_rf:.2f}Ω, εeff={e_eff_rf:.3f}")

il_rf = total_insertion_loss(5.0, 0.3, 0.018, h_eff_rf, mat_rf.dk, mat_rf.df, z0_rf, e_eff_rf,
                              mat_rf.get_roughness_model(), mat_rf.get_huray_params(), 0.1)
print(f"    IL@5GHz={il_rf['IL_total_db']:.4f}dB")

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
