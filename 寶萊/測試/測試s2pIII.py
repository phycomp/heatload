
# 問題: 文件中的 \n 是字面量而非換行符。重新生成正確的 .s2p 文件

import numpy as np

base = "/mnt/agents/output/pcb_calc_app"

from modules.impedance.formulas import microstrip_z0
from modules.stackup.loss_models import total_insertion_loss, return_loss

# 真實參數
true_dk = 4.5
true_df = 0.02
true_w = 0.3
true_h = 1.6
true_t = 0.035
true_L = 0.1
true_Rq = 1.5

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

np.random.seed(42)
noise_s21 = np.random.normal(0, 0.05, len(freqs_ghz))
noise_s11 = np.random.normal(0, 0.2, len(freqs_ghz))
s21_db_noisy = np.array(s21_db_list) + noise_s21
s11_db_noisy = np.array(s11_db_list) + noise_s11

# 使用列表逐行構建，確保正確的換行符
lines = []
lines.append("! Generated test data for Phase 3 inverse engineering")
lines.append("! True params: Dk=4.5, Df=0.02, w=0.3mm, h=1.6mm, t=35um, L=0.1m")
lines.append("# GHz S DB R 50.0")

for i, f in enumerate(freqs_ghz):
    s21_mag = 10 ** (s21_db_noisy[i] / 20.0)
    s21_phase = -2 * np.pi * f * 1e9 * np.sqrt(4.5) / 3e8 * true_L
    s21_phase_deg = np.degrees(s21_phase) % 360
    
    s11_mag = 10 ** (s11_db_noisy[i] / 20.0)
    s11_phase_deg = 180.0 if s11_db_noisy[i] < -20 else 0.0
    
    line = f"{f:.6f}   {s11_db_noisy[i]:.6f}   {s11_phase_deg:.6f}   {s21_db_noisy[i]:.6f}   {s21_phase_deg:.6f}   {s21_db_noisy[i]:.6f}   {s21_phase_deg:.6f}   {s11_db_noisy[i]:.6f}   {s11_phase_deg:.6f}"
    lines.append(line)

# 使用 join 確保正確的換行符
s2p_content = "\n".join(lines)

with open(f"{base}/saved_projects/test_microstrip.s2p", "w", encoding="utf-8", newline="\n") as f:
    f.write(s2p_content)

# 驗證
with open(f"{base}/saved_projects/test_microstrip.s2p", "r") as f:
    read_lines = f.readlines()

print(f"驗證 - 總行數: {len(read_lines)}")
print(f"驗證 - 第一行: '{read_lines[0].strip()}'")
print(f"驗證 - 第二行: '{read_lines[1].strip()}'")
print(f"驗證 - 第三行: '{read_lines[2].strip()}'")
print(f"驗證 - 第四行: '{read_lines[3].strip()}'")
print(f"驗證 - 最後行: '{read_lines[-1].strip()}'")
