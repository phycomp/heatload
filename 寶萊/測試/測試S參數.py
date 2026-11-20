
import numpy as np

# ========== 生成測試用 .s2p 文件 ==========
# 模藕一條 Microstrip 線的 S 參數
# 已知參數: Dk=4.5, Df=0.02, w=0.3mm, h=1.6mm, t=35um, L=0.1m

base = "/mnt/agents/output/pcb_calc_app"

# 使用 Phase 1/2 的模型生成 "真實" S 參數
import sys
sys.path.insert(0, base)

from modules.impedance.formulas import microstrip_z0
from modules.stackup.loss_models import total_insertion_loss, return_loss

# 真實參數
true_dk = 4.5
true_df = 0.02
true_w = 0.3  # mm
true_h = 1.6  # mm
true_t = 0.035  # mm
true_L = 0.1  # m
true_Rq = 1.5  # um

freqs_ghz = np.linspace(0.1, 10.0, 100)

s21_db_list = []
s11_db_list = []

for f in freqs_ghz:
    z0, e_eff = microstrip_z0(true_w, true_h, true_t, true_dk, f)
    il = total_insertion_loss(f, true_w, true_t, true_h, true_dk, true_df, z0, e_eff,
                               "hammerstad", {"Rq_um": true_Rq}, true_L)
    s21_db = -il["IL_total_db"]
    rl = return_loss(f, z0, 50.0, 50.0)
    s11_db = -rl
    s21_db_list.append(s21_db)
    s11_db_list.append(s11_db)

# 加入測量噪聲
np.random.seed(42)
noise_s21 = np.random.normal(0, 0.05, len(freqs_ghz))  # ±0.05 dB 噪聲
noise_s11 = np.random.normal(0, 0.2, len(freqs_ghz))   # ±0.2 dB 噪聲
s21_db_noisy = np.array(s21_db_list) + noise_s21
s11_db_noisy = np.array(s11_db_list) + noise_s11

# 寫入 Touchstone 格式 (.s2p)
s2p_content = "! Generated test data for Phase 3 inverse engineering\\n"
s2p_content += "! True params: Dk=4.5, Df=0.02, w=0.3mm, h=1.6mm, t=35um, L=0.1m\\n"
s2p_content += "# GHz S DB R 50.0\\n"

for i, f in enumerate(freqs_ghz):
    s21_mag = 10 ** (s21_db_noisy[i] / 20.0)
    s21_phase = -2 * np.pi * f * 1e9 * np.sqrt(4.5) / 3e8 * true_L  # 簡化相位
    s21_phase_deg = np.degrees(s21_phase) % 360
    
    s11_mag = 10 ** (s11_db_noisy[i] / 20.0)
    s11_phase_deg = 180.0 if s11_db_noisy[i] < -20 else 0.0  # 簡化
    
    # Touchstone 格式: freq S11_re S11_im S21_re S21_im S12_re S12_im S22_re S22_im
    # 對于 DB 格式: freq S11_mag(dB) S11_phase(deg) S21_mag(dB) S21_phase(deg) ...
    s2p_content += f"{f:.6f}   {s11_db_noisy[i]:.6f}   {s11_phase_deg:.6f}   {s21_db_noisy[i]:.6f}   {s21_phase_deg:.6f}   {s21_db_noisy[i]:.6f}   {s21_phase_deg:.6f}   {s11_db_noisy[i]:.6f}   {s11_phase_deg:.6f}\\n"

with open(f"{base}/saved_projects/test_microstrip.s2p", "w", encoding="utf-8") as f:
    f.write(s2p_content)

print(f"✅ 測試 S 參數文件已生成: {base}/saved_projects/test_microstrip.s2p")
print(f"   頻率範圍: {freqs_ghz[0]:.1f} - {freqs_ghz[-1]:.1f} GHz, {len(freqs_ghz)} 點")
print(f"   S21 範圍: {s21_db_noisy.min():.2f} ~ {s21_db_noisy.max():.2f} dB")
print(f"   S11 範圍: {s11_db_noisy.min():.2f} ~ {s11_db_noisy.max():.2f} dB")
