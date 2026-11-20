
import numpy as np
import matplotlib.pyplot as plt

# ============================
# 物理常數
# ============================
h = 6.626e-34      # Planck 常數 (J·s)
k_B = 1.381e-23    # Boltzmann 常數 (J/K)
c = 3.0e8          # 光速 (m/s)

# ============================
# Delft cri/oFlex3 規格參數
# ============================
# 熱負載溫區: 10 mK ~ 350 mK
# 給定距離: 20 cm
T_cold = 0.010     # 10 mK (量子比特端)
T_hot = 0.350      # 350 mK (混合腔/高溫端)
L_given = 0.20     # 20 cm (給定傳輸線長度)

# ============================
# Transmon 量子比特參數
# ============================
f01 = 5.5e9        # 0→1 躍遷頻率 (Hz)
alpha = -250e6     # 非諧性 (Hz), 負值表示 transmon 特性
E01 = h * f01      # 0→1 躍遷能量 (J)
E12 = h * (f01 + abs(alpha))  # 1→2 躍遷能量 (J)

# ============================
# 退相干閾值定義
# ============================
# 量子計算要求: 熱佔據率 < 1%, 熱光子數 < 0.01
threshold_pop = 0.01
threshold_n_th = 0.01

# ============================
# 熱力學計算函數
# ============================
def thermal_population(E, T):
    """能級 E 相對於基態的熱佔據率 (Boltzmann 分布)"""
    if T <= 0:
        return 0.0
    return np.exp(-E / (k_B * T))

def thermal_photon_number(f, T):
    """頻率 f 對應諧振子的平均熱光子數 (Bose-Einstein 分布)"""
    if T <= 0:
        return 0.0
    x = h * f / (k_B * T)
    if x > 50:
        return 0.0
    return 1.0 / (np.exp(x) - 1.0)

# ============================
# 計算各溫度點的熱佔據率
# ============================
T_range = np.linspace(0.005, 0.400, 1000)  # 5 mK ~ 400 mK

pop_1 = np.array([thermal_population(E01, T) for T in T_range])
pop_2 = np.array([thermal_population(E12, T) for T in T_range])
n_th = np.array([thermal_photon_number(f01, T) for T in T_range])

# 找臨界溫度
T_critical_pop = None
T_critical_n_th = None
for i, T in enumerate(T_range):
    if pop_1[i] > threshold_pop and T_critical_pop is None:
        T_critical_pop = T
    if n_th[i] > threshold_n_th and T_critical_n_th is None:
        T_critical_n_th = T

print("=" * 60)
print("【Transmon 量子比特熱力學參數】")
print("=" * 60)
print(f"  0→1 躍遷頻率: {f01/1e9:.1f} GHz")
print(f"  1→2 躍遷頻率: {(f01 + abs(alpha))/1e9:.3f} GHz")
print(f"  非諧性 (α): {alpha/1e6:.0f} MHz")
print(f"  0→1 躍遷能量: {E01/(h*1e9):.1f} GHz·h")
print()
print(f"  退相干閾值 (熱佔據率 |1⟩): {threshold_pop*100:.0f}%")
print(f"  退相干閾值 (熱光子數): {threshold_n_th}")
print()
print(f"  臨界溫度 (熱佔據率超過 1%): {T_critical_pop*1000:.1f} mK")
print(f"  臨界溫度 (熱光子數超過 0.01): {T_critical_n_th*1000:.1f} mK")

# ============================
# 關鍵溫度點的熱佔據率
# ============================
print("\n" + "=" * 60)
print("【關鍵溫度點熱佔據分析】")
print("=" * 60)

for T_test in [0.010, 0.050, 0.100, 0.150, 0.200, 0.250, 0.300, 0.350]:
    p1 = thermal_population(E01, T_test)
    p2 = thermal_population(E12, T_test)
    nth = thermal_photon_number(f01, T_test)
    status = "✓ 安全" if p1 < threshold_pop and nth < threshold_n_th else "✗ 退相干風險"
    print(f"  T = {T_test*1000:>5.0f} mK:  |1⟩={p1:.6f} ({p1*100:.4f}%),  n_th={nth:.6f}  → {status}")

# ============================
# 傳輸線熱傳導模型
# ============================
print("\n" + "=" * 60)
print("【傳輸線熱傳導與長度回推】")
print("=" * 60)

# 假設傳輸線為同軸電纜 (典型超導量子計算用)
# 材料: NbTi 內導體 + CuNi 外屏蔽 (低熱導)
# 熱導率 κ 在低溫下近似 ~ T (Wiedemann-Franz 定律近似)
# 簡化模型: 熱流 Q = κ·A·ΔT/L
# 對於給定熱負載，溫度梯度與長度成反比

# 基於 Delft cri/oFlex3: 20cm 對應 ΔT = 340 mK (10mK → 350mK)
# 這意味著在 20cm 內溫度從 350mK 降到 10mK

# 回推邏輯:
# 若要在量子比特端 (T_cold = 10mK) 保持熱佔據率 < 1%
# 需要確保傳輸線上任何一點的溫度都不超過臨界溫度 T_critical
# 
# 但實際上，傳輸線是漸變溫度的。量子比特只關心「最熱端」耦合進來的熱噪聲。
# 在 dilution refrigerator 中，傳輸線會經過多個冷卻階段。
# cri/oFlex3 的 20cm 是指最後一段 (mixing chamber → 量子比特芯片)

# 熱光子數通過傳輸線的衰減:
# 若傳輸線有衰減 α_dB/m，則熱光子數衰減為 n_th_effective = n_th * 10^(-αL/10)
# 超導傳輸線在微波頻段的衰減極低 (~0.01 dB/m 或更低)

# 更關鍵的是: 熱輻射通過傳輸線的耦合
# 使用輻射熱傳導模型: Q_rad = σ·A·(T_hot^4 - T_cold^4) 不適用於此尺度
# 改用聲子熱傳導: Q_phonon = κ·A·ΔT/L

# 簡化假設: 線性溫度梯度
# T(x) = T_cold + (T_hot - T_cold) * (x/L)
# 其中 x=0 是量子比特端 (冷端), x=L 是混合腔端 (熱端)

# 對於超導同軸電纜，熱導率近似:
# κ ≈ κ_0 * T (低溫極限)
# 但為了簡化，我們使用線性近似

# 實際回推策略:
# 1. cri/oFlex3 的 20cm 已經是工程優化結果
# 2. 對於 transmon (5.5 GHz, -250 MHz 非諧性)，臨界溫度約 130 mK
# 3. 若混合腔溫度為 350 mK，需要確保傳輸線的熱隔離足夠
# 4. 或者，需要在中間加入額外的冷卻階段

# 計算不同長度下的等效熱光子數 (簡化模型)
# 假設傳輸線溫度線性分布，有效熱光子數為積分平均

def effective_thermal_photons(L, T_cold, T_hot, f):
    """
    計算長度 L 的傳輸線，溫度線性分布從 T_cold 到 T_hot
    對量子比特而言的等效熱光子數負載
    簡化: 取中點溫度對應的熱光子數 (保守估計)
    """
    T_mid = (T_cold + T_hot) / 2
    return thermal_photon_number(f, T_mid)

# 回推合適長度
# 目標: 量子比特端的等效熱負載對應的溫度 < T_critical
# 若混合腔端固定為 350 mK，需要傳輸線足夠長以降低熱耦合

# 使用熱阻模型:
# R_th = L / (κ·A)
# 對於給定熱流 Q，ΔT = Q·R_th = Q·L/(κ·A)
# 若 cri/oFlex3 的 20cm 對應 ΔT = 340 mK，則熱阻 R_th = 340mK / Q

# 對於 transmon，我們需要量子比特端溫度 < T_critical_pop (~130 mK)
# 若混合腔端仍為 350 mK，則 ΔT_max = 350 - 130 = 220 mK
# 由於 ΔT ∝ L，所需長度 L_required = L_given * (ΔT_max / ΔT_given)
# 但這過於簡化，因為熱導率隨溫度變化

# 更精確的考慮: 使用熱導積分
# 對於金屬，κ(T) ≈ κ_n * (T/T_n) (低溫極限)
# Q = (κ_n·A/T_n) * ∫ T dT / L = (κ_n·A/T_n) * (T_hot^2 - T_cold^2) / (2L)
# 因此 L ∝ (T_hot^2 - T_cold^2)

# 計算
T_crit = T_critical_pop  # ~130 mK

# 線性熱導模型 (簡化)
L_required_linear = L_given * (T_hot - T_crit) / (T_hot - T_cold)

# 二次熱導模型 (更準確，考慮 Wiedemann-Franz)
L_required_quadratic = L_given * (T_hot**2 - T_crit**2) / (T_hot**2 - T_cold**2)

print(f"\n  Delft cri/oFlex3 給定參數:")
print(f"    溫區: {T_cold*1000:.0f} mK → {T_hot*1000:.0f} mK")
print(f"    傳輸線長度: {L_given*100:.0f} cm")
print(f"    溫差: {(T_hot - T_cold)*1000:.0f} mK")
print()
print(f"  Transmon 臨界溫度 (熱佔據率 < 1%): {T_crit*1000:.1f} mK")
print()
print(f"  【回推合適傳輸線長度】")
print(f"    線性熱導模型: {L_required_linear*100:.1f} cm")
print(f"    二次熱導模型 (Wiedemann-Franz): {L_required_quadratic*100:.1f} cm")

# ============================
# 另一種回推: 基於熱光子數閾值
# ============================
T_crit_nth = T_critical_n_th  # ~66 mK (更嚴格)
L_required_nth_linear = L_given * (T_hot - T_crit_nth) / (T_hot - T_cold)
L_required_nth_quad = L_given * (T_hot**2 - T_crit_nth**2) / (T_hot**2 - T_cold**2)

print(f"\n  基於熱光子數閾值 (n_th < 0.01, T_crit = {T_crit_nth*1000:.1f} mK):")
print(f"    線性熱導模型: {L_required_nth_linear*100:.1f} cm")
print(f"    二次熱導模型: {L_required_nth_quad*100:.1f} cm")

# ============================
# 實際工程考量
# ============================
print("\n" + "=" * 60)
print("【工程實務考量】")
print("=" * 60)
print("""
  1. 上述計算假設傳輸線為純熱導路徑，但實際上:
     - 微波傳輸線同時承載信號和熱噪聲
     - 需要考慮衰減帶來的額外熱負載 (dissipation)
     
  2. 實際稀釋製冷機中，傳輸線會經過多個冷卻階段:
     - 50K 階段 (PT 冷頭)
     - 4K 階段 (He 槽)
     - Still 階段 (~700 mK)
     - Mixing Chamber (~10-20 mK)
     
  3. cri/oFlex3 的 20cm 是最後一段 (MC → 芯片)，
     這段傳輸線本身溫度已接近 10 mK，
     350 mK 是指傳輸線「可承受的熱端溫度」。
     
  4. 對於 transmon，關鍵不是傳輸線長度，而是:
     - 傳輸線的微波衰減 (決定熱光子耦合效率)
     - 濾波器設計 (帶通/低通濾波器截斷高頻熱噪聲)
     - 熱化質量 (thermalization mass) 的設計
""")

# ============================
# 繪製示意圖
# ============================
fig = plt.figure(figsize=(16, 12))

# --- 圖 1: 熱佔據率 vs 溫度 ---
ax1 = fig.add_subplot(2, 2, 1)
ax1.semilogy(T_range * 1000, pop_1, 'b-', linewidth=2.5, label='$|1\\rangle$ population')
ax1.semilogy(T_range * 1000, pop_2, 'r--', linewidth=2, label='$|2\\rangle$ population')
ax1.axhline(y=threshold_pop, color='gray', linestyle=':', linewidth=2, label=f'1% threshold')
ax1.axvline(x=T_critical_pop*1000, color='green', linestyle='--', alpha=0.8, linewidth=2)
ax1.axvline(x=T_critical_n_th*1000, color='orange', linestyle='--', alpha=0.8, linewidth=2)
ax1.set_xlabel('Temperature (mK)', fontsize=13)
ax1.set_ylabel('Thermal Population', fontsize=13)
ax1.set_title('Transmon Thermal Population vs Temperature\n(f₀₁ = 5.5 GHz, α = -250 MHz)', fontsize=14)
ax1.legend(fontsize=11, loc='lower right')
ax1.grid(True, alpha=0.3)
ax1.set_xlim([0, 350])
ax1.set_ylim([1e-8, 1])

# 標註臨界溫度
ax1.annotate(f'T_crit(pop) = {T_critical_pop*1000:.1f} mK', 
             xy=(T_critical_pop*1000, threshold_pop), 
             xytext=(T_critical_pop*1000 + 40, threshold_pop * 3),
             fontsize=10, color='green',
             arrowprops=dict(arrowstyle='->', color='green'))
ax1.annotate(f'T_crit(n_th) = {T_critical_n_th*1000:.1f} mK', 
             xy=(T_critical_n_th*1000, threshold_pop), 
             xytext=(T_critical_n_th*1000 + 40, threshold_pop * 0.3),
             fontsize=10, color='orange',
             arrowprops=dict(arrowstyle='->', color='orange'))

# --- 圖 2: 熱光子數 vs 溫度 ---
ax2 = fig.add_subplot(2, 2, 2)
ax2.semilogy(T_range * 1000, n_th, 'purple', linewidth=2.5, label='$n_{th}$')
ax2.axhline(y=threshold_n_th, color='gray', linestyle=':', linewidth=2, label=f'$n_{{th}}$ = 0.01 threshold')
ax2.axvline(x=T_critical_n_th*1000, color='orange', linestyle='--', alpha=0.8, linewidth=2)
ax2.set_xlabel('Temperature (mK)', fontsize=13)
ax2.set_ylabel('Average Thermal Photon Number', fontsize=13)
ax2.set_title('Thermal Photon Number vs Temperature\n(f₀₁ = 5.5 GHz)', fontsize=14)
ax2.legend(fontsize=11, loc='lower right')
ax2.grid(True, alpha=0.3)
ax2.set_xlim([0, 350])
ax2.set_ylim([1e-8, 10])

# --- 圖 3: 傳輸線溫度分布示意圖 ---
ax3 = fig.add_subplot(2, 2, 3)

# 繪製不同長度下的溫度分布
lengths = [0.20, L_required_linear, L_required_quadratic, L_required_nth_quad]
labels = ['cri/oFlex3 (20 cm)', 'Linear model', 'Quadratic model', 'Strict (n_th < 0.01)']
colors = ['red', 'blue', 'green', 'purple']
linestyles = ['-', '--', '-.', ':']

for L, label, color, ls in zip(lengths, labels, colors, linestyles):
    x = np.linspace(0, L, 100)
    # 線性溫度分布 (簡化)
    T_dist = T_cold + (T_hot - T_cold) * (x / L)
    ax3.plot(x * 100, T_dist * 1000, color=color, linestyle=ls, linewidth=2.5, label=label)

ax3.axhline(y=T_critical_pop*1000, color='green', linestyle='--', alpha=0.5, linewidth=1.5)
ax3.axhline(y=T_critical_n_th*1000, color='orange', linestyle='--', alpha=0.5, linewidth=1.5)
ax3.axhspan(T_critical_n_th*1000, T_critical_pop*1000, alpha=0.1, color='yellow')
ax3.set_xlabel('Distance from Qubit (cm)', fontsize=13)
ax3.set_ylabel('Temperature (mK)', fontsize=13)
ax3.set_title('Transmission Line Temperature Profile\n(Linear Approximation)', fontsize=14)
ax3.legend(fontsize=10, loc='upper left')
ax3.grid(True, alpha=0.3)
ax3.set_xlim([0, max(lengths)*100 * 1.1])
ax3.set_ylim([0, 400])

# 標註區域
ax3.text(max(lengths)*100 * 0.55, (T_critical_pop*1000 + T_critical_n_th*1000)/2, 
         'Marginal Zone', fontsize=10, color='darkgoldenrod', ha='center', va='center')
ax3.text(max(lengths)*100 * 0.55, T_critical_n_th*1000/2, 
         'Safe Zone\n(n_th < 0.01)', fontsize=10, color='green', ha='center', va='center')

# --- 圖 4: 合適長度回推總結 ---
ax4 = fig.add_subplot(2, 2, 4)

# 繪製長度需求比較
categories = ['cri/oFlex3\n(Original)', 'Linear\n(Pop < 1%)', 'Quadratic\n(Pop < 1%)', 'Linear\n(n_th < 0.01)', 'Quadratic\n(n_th < 0.01)']
lengths_cm = [L_given*100, L_required_linear*100, L_required_quadratic*100, 
              L_required_nth_linear*100, L_required_nth_quad*100]
colors_bar = ['red', 'skyblue', 'lightgreen', 'coral', 'plum']

bars = ax4.bar(categories, lengths_cm, color=colors_bar, edgecolor='black', linewidth=1.5)
ax4.axhline(y=L_given*100, color='red', linestyle='--', alpha=0.7, linewidth=2, label='cri/oFlex3 (20 cm)')
ax4.set_ylabel('Required Length (cm)', fontsize=13)
ax4.set_title('Transmission Line Length Requirement\nfor Transmon Coherence', fontsize=14)
ax4.legend(fontsize=11)
ax4.grid(True, alpha=0.3, axis='y')

# 在柱子上標註數值
for bar, val in zip(bars, lengths_cm):
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
             f'{val:.1f} cm', ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('/mnt/agents/output/transmon_transmission_line_analysis.png', dpi=180, bbox_inches='tight')
plt.show()

print("\n✅ 示意圖已儲存至 /mnt/agents/output/transmon_transmission_line_analysis.png")
