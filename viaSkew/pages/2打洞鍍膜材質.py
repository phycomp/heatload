from matplotlib.pyplot import colorbar, figure, rcParams, savefig, show, suptitle, tight_layout
from numpy import degrees, linspace, log, log10, meshgrid, pi, real, sqrt, zeros_like
#import numpy as np
#import matplotlib.pyplot as plt
from scipy.special import jv, yv, kv, iv
from scipy.optimize import fsolve
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, Wedge, FancyArrowPatch
from matplotlib.collections import PatchCollection
from matplotlib.pyplot import rcParams, savefig, show, subplots, tight_layout
from streamlit import pyplot, radio, text_input, empty, sidebar

# 設定中文字型
rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

# ============================================
# Cri/oFlex 3 Via 製程與 TEM 模式模擬器
# ============================================

class CriOFlex3ViaSimulator:
    """
    Cri/oFlex 3 低溫超導柔性傳輸線 Via 製程模擬器
    包含：Via 結構、Coating 材質、TEM 模式電磁分析
    """
    
    def __init__(self):
        # === Cri/oFlex 3 基本參數 ===
        self.total_thickness_um = 300
        self.width_mm = 16
        self.n_channels = 8
        self.channel_pitch_um = 2000
        self.trace_width_um = 220
        self.trace_thickness_um = 6
        self.dielectric_thickness_um = 70
        
        # === Via 參數 ===
        self.via_diameter_um = 150
        self.via_depth_um = 151  # L2 (Top Ground) to L6 (Bottom Ground)
        self.via_pitch_mm = 10
        self.via_aspect_ratio = self.via_depth_um / self.via_diameter_um  # ~1:1
        
        # === 材料參數 ===
        self.substrate = "Polyimide"
        self.conductor = "NbTi"  # 超導版本
        self.T_c = 9.2  # K
        self.T_operation = 0.01  # 10 mK
        
        # 物理常數
        self.c = 299792458  # m/s
        self.mu0 = 4 * pi * 1e-7  # H/m
        self.epsilon0 = 8.854e-12  # F/m
        
    # ---------- Via Coating 材質選項 ----------
    
    def get_coating_materials(self):
        """定義適合低溫超導 Via coating 的材質"""
        materials = {
            "NbTi": {
                "type": "Superconducting",
                "Tc_K": 9.2,
                "resistivity_RT_uOhm_cm": 70,
                "resistivity_4K_uOhm_cm": 0,  # 超導態
                "thermal_conductivity_W_mK": 0.5,
                "deposition_method": "DC Magnetron Sputtering",
                "adhesion_to_PI": "Good (with Ti buffer)",
                "cryogenic_compatibility": "Excellent",
                "coating_challenge": "High aspect ratio coverage",
                "recommended_for": "Signal vias, Ground vias"
            },
            "TiN": {
                "type": "Superconducting",
                "Tc_K": 5.0,
                "resistivity_RT_uOhm_cm": 100,
                "resistivity_4K_uOhm_cm": 0,
                "thermal_conductivity_W_mK": 20,
                "deposition_method": "CVD / ALD",
                "adhesion_to_PI": "Excellent",
                "cryogenic_compatibility": "Excellent",
                "coating_challenge": "Conformal coating required",
                "recommended_for": "High aspect ratio vias, TSV"
            },
            "Nb": {
                "type": "Superconducting",
                "Tc_K": 9.2,
                "resistivity_RT_uOhm_cm": 15,
                "resistivity_4K_uOhm_cm": 0,
                "thermal_conductivity_W_mK": 50,
                "deposition_method": "DC Magnetron Sputtering",
                "adhesion_to_PI": "Good (with Cr buffer)",
                "cryogenic_compatibility": "Excellent",
                "coating_challenge": "Oxidation sensitive",
                "recommended_for": "Ground planes, Shielding"
            },
            "Al": {
                "type": "Superconducting",
                "Tc_K": 1.2,
                "resistivity_RT_uOhm_cm": 2.7,
                "resistivity_4K_uOhm_cm": 0,
                "thermal_conductivity_W_mK": 2000,
                "deposition_method": "Thermal Evaporation / E-beam",
                "adhesion_to_PI": "Excellent",
                "cryogenic_compatibility": "Good (T_c limitation)",
                "coating_challenge": "Soft, prone to scratching",
                "recommended_for": "Quantum bit interconnects"
            },
            "Ti": {
                "type": "Adhesion Buffer",
                "Tc_K": 0.4,
                "resistivity_RT_uOhm_cm": 43,
                "resistivity_4K_uOhm_cm": 0.5,
                "thermal_conductivity_W_mK": 22,
                "deposition_method": "DC Magnetron Sputtering",
                "adhesion_to_PI": "Excellent",
                "cryogenic_compatibility": "Good",
                "coating_challenge": "None",
                "recommended_for": "Adhesion layer, Barrier layer"
            },
            "Cr": {
                "type": "Adhesion Buffer",
                "Tc_K": 0,
                "resistivity_RT_uOhm_cm": 13,
                "resistivity_4K_uOhm_cm": 0.1,
                "thermal_conductivity_W_mK": 94,
                "deposition_method": "DC Magnetron Sputtering",
                "adhesion_to_PI": "Excellent",
                "cryogenic_compatibility": "Good",
                "coating_challenge": "None",
                "recommended_for": "Adhesion layer for Ag/Cu"
            },
            "Cu (Electroplated)": {
                "type": "Normal Conducting",
                "Tc_K": 0,
                "resistivity_RT_uOhm_cm": 1.7,
                "resistivity_4K_uOhm_cm": 0.02,
                "thermal_conductivity_W_mK": 400,
                "deposition_method": "Electroplating",
                "adhesion_to_PI": "Poor (needs seed layer)",
                "cryogenic_compatibility": "Good (residual resistance)",
                "coating_challenge": "Void formation in high aspect ratio",
                "recommended_for": "Room temp interconnects only"
            },
            "Conductive Carbon": {
                "type": "Seed Layer",
                "Tc_K": 0,
                "resistivity_RT_uOhm_cm": 10000,
                "resistivity_4K_uOhm_cm": 5000,
                "thermal_conductivity_W_mK": 10,
                "deposition_method": "Dip coating / Spray",
                "adhesion_to_PI": "Good",
                "cryogenic_compatibility": "Poor (high resistance)",
                "coating_challenge": "High resistance at low temp",
                "recommended_for": "Electroplating seed layer only"
            }
        }
        return materials
    
    # ---------- Via 製程模擬 ----------
    
    def via_fabrication_process(self):
        """模擬 Via 打孔與 Coating 製程流程"""
        process_steps = [
            {
                "step": 1,
                "name": "Laser Drilling",
                "description": "UV laser drill via holes through PI layers",
                "parameters": {
                    "laser_type": "UV (355 nm)",
                    "pulse_energy": "50 μJ",
                    "rep_rate": "100 kHz",
                    "drill_speed": "10 holes/sec",
                    "hole_diameter": "150 μm",
                    "aspect_ratio": "1:1"
                },
                "challenges": "Heat affected zone (HAZ) control, taper angle"
            },
            {
                "step": 2,
                "name": "Desmear & Cleaning",
                "description": "Remove debris and smooth via walls",
                "parameters": {
                    "method": "Plasma etching + chemical cleaning",
                    "plasma_gas": "O2/CF4 mixture",
                    "etch_rate": "0.1 μm/min",
                    "cleaning_solution": "Isopropyl alcohol"
                },
                "challenges": "Residue removal, surface activation"
            },
            {
                "step": 3,
                "name": "Adhesion Layer Deposition",
                "description": "Deposit Ti or Cr buffer layer",
                "parameters": {
                    "material": "Ti (20 nm) or Cr (20 nm)",
                    "method": "DC magnetron sputtering",
                    "power": "1 kW",
                    "pressure": "3 mTorr",
                    "uniformity": "±5%"
                },
                "challenges": "Conformal coating on via sidewalls"
            },
            {
                "step": 4,
                "name": "Superconducting Coating",
                "description": "Deposit NbTi or Nb superconducting layer",
                "parameters": {
                    "material": "NbTi (300 nm) or Nb (200 nm)",
                    "method": "DC/RF magnetron sputtering",
                    "power": "3-5 kW",
                    "substrate_temp": "< 150°C",
                    "thickness_uniformity": "±10%"
                },
                "challenges": "Step coverage on vertical walls, T_c uniformity"
            },
            {
                "step": 5,
                "name": "Capping Layer (Optional)",
                "description": "Protect superconducting layer from oxidation",
                "parameters": {
                    "material": "Au (50 nm) or TiN (20 nm)",
                    "method": "Sputtering or evaporation",
                    "purpose": "Oxidation protection"
                },
                "challenges": "Additional process complexity"
            },
            {
                "step": 6,
                "name": "Photolithography",
                "description": "Pattern via interconnects",
                "parameters": {
                    "photoresist": "Dry film, 20 μm",
                    "exposure": "i-line, 365 nm",
                    "resolution": "20 μm",
                    "alignment_accuracy": "±5 μm"
                },
                "challenges": "Registration accuracy, thick resist processing"
            },
            {
                "step": 7,
                "name": "Etching",
                "description": "Define via interconnect pattern",
                "parameters": {
                    "method": "ICP-RIE or wet etching",
                    "gas_mixture": "Cl2/BCl3 (for NbTi)",
                    "etch_rate": "50 nm/min",
                    "selectivity": "> 5:1"
                },
                "challenges": "Etch uniformity, sidewall profile"
            },
            {
                "step": 8,
                "name": "Post-processing",
                "description": "Clean and inspect",
                "parameters": {
                    "cleaning": "ACE + IPA + N2 dry",
                    "inspection": "SEM + electrical test",
                    "critical_current_test": "@ 4K"
                },
                "challenges": "Contamination control"
            }
        ]
        return process_steps
    
    # ---------- TEM 模式電磁分析 ----------
    
    def calculate_TEM_parameters(self, frequency_ghz, coating_material="NbTi"):
        """
        計算 TEM 模式電磁參數
        
        TEM (Transverse ElectroMagnetic) 模式特性：
        - E 場和 H 場完全垂直於傳播方向
        - 無截止頻率 (cutoff frequency = 0)
        - 相速度 v_p = c / sqrt(εr) (與頻率無關)
        - 特性阻抗 Z0 為常數
        """
        f = frequency_ghz * 1e9  # Hz
        
        # 介電參數
        epsilon_r = 3.2  # Polyimide @ 4K
        tan_delta = 0.003
        
        # 導體參數 (超導態)
        materials = self.get_coating_materials()
        mat = materials.get(coating_material, materials["NbTi"])
        
        # 超導表面阻抗 (London 理論)
        # Zs = j * ω * μ0 * λ_L (在 T << T_c 時)
        lambda_L = 40e-9  # London penetration depth (NbTi)
        omega = 2 * pi * f
        Zs = 1j * omega * self.mu0 * lambda_L  # Ω/□
        
        # 相速度
        v_p = self.c / sqrt(epsilon_r)
        
        # 波長
        lambda_g = v_p / f
        
        # 特性阻抗 (Stripline)
        w = self.trace_width_um * 1e-6
        h = self.dielectric_thickness_um * 1e-6
        t = self.trace_thickness_um * 1e-6
        
        # 有效寬度
        w_eff = w + (2 * t / pi) * log(1 + pi * w / t)
        Z0 = (94.15 / sqrt(epsilon_r)) / (w_eff / h + 0.441)
        
        # 衰減常數
        # 導體損耗 (超導態極低)
        alpha_c = real(Zs) / (Z0 * w) if real(Zs) > 0 else 1e-10
        
        # 介電損耗
        alpha_d = (pi * f / self.c) * sqrt(epsilon_r) * tan_delta
        
        # 總衰減
        alpha_total = alpha_c + alpha_d
        
        # 品質因數
        Q_c = pi * f * self.mu0 / real(Zs) if real(Zs) > 0 else 1e10
        Q_d = 1 / tan_delta
        Q_total = 1 / (1/Q_c + 1/Q_d)
        
        return {
            'frequency_ghz': frequency_ghz,
            'coating_material': coating_material,
            'epsilon_r': epsilon_r,
            'tan_delta': tan_delta,
            'Zs': Zs,
            'v_p': v_p,
            'lambda_g': lambda_g,
            'Z0': Z0,
            'alpha_c': alpha_c,
            'alpha_d': alpha_d,
            'alpha_total': alpha_total,
            'Q_c': Q_c,
            'Q_d': Q_d,
            'Q_total': Q_total,
            'lambda_L': lambda_L
        }
    
    def calculate_via_TEM_mode(self, via_diameter_um, coating_thickness_um, frequency_ghz):
        """
        計算 Via 結構中的 TEM 模式
        
        Via 可視為短段同軸傳輸線：
        - 內導體：Via 填充金屬
        - 外導體：接地層
        - 介質：Polyimide
        """
        a = (via_diameter_um / 2) * 1e-6  # 內半徑 (m)
        b = a + 500e-6  # 外半徑 (接地層距離)
        
        epsilon_r = 3.2
        f = frequency_ghz * 1e9
        
        # 同軸線特性阻抗
        Z0_via = (60 / sqrt(epsilon_r)) * log(b / a)
        
        # 相速度
        v_p = self.c / sqrt(epsilon_r)
        
        # Via 電長度 (假設深度 151 μm)
        L_via = 151e-6
        theta = 2 * pi * f * L_via / v_p  # rad
        
        # Via 電感 (近似)
        L_inductance = (self.mu0 / (2 * pi)) * L_via * log(b / a)
        
        # Via 電容 (近似)
        C_capacitance = (2 * pi * self.epsilon0 * epsilon_r * L_via) / log(b / a)
        
        # 串聯阻抗
        Z_via = 1j * omega * L_inductance + 1 / (1j * omega * C_capacitance)
        
        return {
            'Z0_via': Z0_via,
            'v_p': v_p,
            'theta_rad': theta,
            'L_inductance_H': L_inductance,
            'C_capacitance_F': C_capacitance,
            'electrical_length_deg': degrees(theta),
            'S11_dB': 20 * log10(abs((Z_via - 50) / (Z_via + 50)))
        }
sim = CriOFlex3ViaSimulator()

fig = figure(figsize=(22, 18))
#
# ============================================
# 建立視覺化圖表
# ============================================
from streamlit import empty
MENU, 表單=[], ['立體圖', '材質比較', '打洞製程', 'TEM', '特性阻抗', '衰減常數', '等效電路', '品質因數', '總結']		#'鍍膜', '打洞', '', '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  freq_range = linspace(0.1, 20, 100)
  狀態=empty()
  狀態.code([])
if menu==len(表單): #
  pass
elif menu==MENU[8]:
  # ============================================
  # 圖 9: TEM 物理公式總結
  # ============================================
  fig, ax9= subplots(figsize=(10, 6))
  #ax9 = fig.add_subplot(3, 3, 9)
  ax9.axis('off')

  formula_text = r"""
  TEM Mode Characteristics:

  1. Field Structure:
     E⃗ = E_x x̂ + E_y ŷ  (Transverse only)
     H⃗ = H_x x̂ + H_y ŷ  (Transverse only)
     E_z = H_z = 0

  2. Phase Velocity:
     v_p = c / √ε_r  (Frequency independent)

  3. Characteristic Impedance:
     Z₀ = √(L' / C')
     
     For Stripline:
     Z₀ ≈ (94.15/√εᵣ) / (w_eff/h + 0.441)

  4. Attenuation (Superconducting):
     α_c ≈ 0  (R_s → 0 at T << T_c)
     α_d = (πf/c)√εᵣ tanδ
     
  5. Quality Factor:
     Q_c = ωL/R_s  (Superconducting: very high)
     Q_d = 1/tanδ
     Q_total = 1/(1/Q_c + 1/Q_d)

  6. Via TEM Model (Coaxial approximation):
     Z₀_via = (60/√εᵣ) ln(b/a)
     
     Where a = via radius, b = ground distance
  """

  ax9.text(0.05, 0.95, formula_text, transform=ax9.transAxes,
          fontsize=9, verticalalignment='top', family='monospace',
          bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

  ax9.set_title('TEM Mode Physics Formulas', fontsize=12, fontweight='bold')

  suptitle('Cri/oFlex 3 Low-Temperature Superconducting Via\nTEM Mode Electromagnetic Analysis', 
               fontsize=16, fontweight='bold', y=0.98)

  tight_layout()
  pyplot(fig)
elif menu==MENU[7]:
  fig, ax8= subplots(figsize=(10, 6))
  # ============================================
  # 圖 8: 品質因數 Q vs 頻率
  # ============================================
  #ax8 = fig.add_subplot(3, 3, 8)

  Q_total_values = []
  Q_c_values = []
  Q_d_values = []

  for f in freq_range:
      result = sim.calculate_TEM_parameters(f, "NbTi")
      Q_total_values.append(result['Q_total'])
      Q_c_values.append(result['Q_c'])
      Q_d_values.append(result['Q_d'])

  ax8.semilogy(freq_range, Q_total_values, 'b-', linewidth=2, label='Q_total')
  ax8.semilogy(freq_range, Q_c_values, 'g--', linewidth=1.5, label='Q_conductor')
  ax8.semilogy(freq_range, Q_d_values, 'r:', linewidth=1.5, label='Q_dielectric')
  ax8.set_xlabel('Frequency (GHz)', fontsize=10)
  ax8.set_ylabel('Quality Factor Q', fontsize=10)
  ax8.set_title('TEM Mode: Q Factor vs Frequency\n(NbTi @ 10 mK)', fontsize=12, fontweight='bold')
  ax8.legend()
  ax8.grid(True, alpha=0.3)
  pyplot(fig)

elif menu==MENU[6]:
  fig, ax7= subplots(figsize=(10, 6))
  # ============================================
  # 圖 7: Via 等效電路模型
  # ============================================
  #ax7 = fig.add_subplot(3, 3, 7)
  ax7.axis('off')

  # 繪製等效電路
  circuit_text = """
  Via Equivalent Circuit (TEM Mode):

          L_via
      ┌────/\/\/\────┐
      │             │
     ─┤             ├─
      │      │      │
      │     === C   │
      │      │      │
      │      │      │
     ─┤             ├─
      │             │
      └─────────────┘
      
  L_via ≈ μ₀/(2π) × L × ln(b/a)
  C_via ≈ 2πε₀εᵣ × L / ln(b/a)

  Where:
    a = via radius (75 μm)
    b = ground plane distance (575 μm)
    L = via depth (151 μm)
  """

  ax7.text(0.1, 0.9, circuit_text, transform=ax7.transAxes,
          fontsize=10, verticalalignment='top', family='monospace',
          bbox=dict(boxstyle='round', facecolor='lightcyan', alpha=0.8))

  ax7.set_title('Via TEM Equivalent Circuit', fontsize=12, fontweight='bold')
  pyplot(fig)

elif menu==MENU[5]:
  fig, ax6= subplots(figsize=(10, 6))
  # ============================================
  # 圖 6: 衰減常數 vs 頻率
  # ============================================
  #ax6 = fig.add_subplot(3, 3, 6)

  alpha_c_values = []
  alpha_d_values = []
  alpha_total_values = []

  for f in freq_range:
      result = sim.calculate_TEM_parameters(f, "NbTi")
      alpha_c_values.append(result['alpha_c'] * 8.686 * 100)  # dB/100m
      alpha_d_values.append(result['alpha_d'] * 8.686 * 100)
      alpha_total_values.append(result['alpha_total'] * 8.686 * 100)

  ax6.semilogy(freq_range, alpha_total_values, 'b-', linewidth=2, label='Total Loss')
  ax6.semilogy(freq_range, alpha_c_values, 'g--', linewidth=1.5, label='Conductor Loss (Superconducting)')
  ax6.semilogy(freq_range, alpha_d_values, 'r:', linewidth=1.5, label='Dielectric Loss')
  ax6.set_xlabel('Frequency (GHz)', fontsize=10)
  ax6.set_ylabel('Attenuation (dB/100m)', fontsize=10)
  ax6.set_title('TEM Mode: Attenuation vs Frequency\n(NbTi Superconducting)', fontsize=12, fontweight='bold')
  ax6.legend()
  ax6.grid(True, alpha=0.3)
  pyplot(fig)

elif menu==MENU[4]:
  fig, ax5= subplots(figsize=(10, 6))
  # ============================================
  # 圖 5: 特性阻抗 vs 頻率 (TEM 特性)
  # ============================================
  #ax5 = fig.add_subplot(3, 3, 5)

  Z0_values = []

  for f in freq_range:
      result = sim.calculate_TEM_parameters(f, "NbTi")
      Z0_values.append(result['Z0'])

  ax5.plot(freq_range, Z0_values, 'b-', linewidth=2, label='Z0 (TEM)')
  ax5.axhline(y=50, color='r', linestyle='--', label='Target: 50 Ω')
  ax5.set_xlabel('Frequency (GHz)', fontsize=10)
  ax5.set_ylabel('Characteristic Impedance (Ω)', fontsize=10)
  ax5.set_title('TEM Mode: Z0 vs Frequency\n(Non-dispersive)', fontsize=12, fontweight='bold')
  ax5.legend()
  ax5.grid(True, alpha=0.3)

  # 標註 TEM 特性
  ax5.text(10, max(Z0_values)*0.95, 'TEM Mode:\nZ0 = constant\n(No dispersion)', fontsize=10, bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
  pyplot(fig)

elif menu==MENU[3]:
  fig, ax4= subplots(figsize=(10, 6))
  # ============================================
  # 圖 4: TEM 模式電場分佈
  # ============================================
  #ax4 = fig.add_subplot(3, 3, 4)

  # 繪製 Stripline TEM 模式電場
  x = linspace(-2, 2, 100)
  y = linspace(-1.5, 1.5, 100)
  X, Y = meshgrid(x, y)

  # 中心導體位置 (normalized)
  conductor_width = 0.5
  conductor_thickness = 0.1

  # 電場分佈 (簡化模型)
  E_field = zeros_like(X)
  for i in range(len(x)):
      for j in range(len(y)):
          # 中心導體區域
          if abs(X[j, i]) < conductor_width/2 and abs(Y[j, i]) < conductor_thickness/2:
              E_field[j, i] = 0  # 導體內部
          else:
              # 電場衰減
              r = sqrt(X[j, i]**2 + Y[j, i]**2)
              E_field[j, i] = 1 / (r + 0.1)

  # 繪製電場等高線
  contour = ax4.contourf(X, Y, E_field, levels=20, cmap='RdYlBu_r')
  colorbar(contour, ax=ax4, label='|E| (normalized)')

  # 繪製導體邊界
  rect = Rectangle((-conductor_width/2, -conductor_thickness/2), 
                   conductor_width, conductor_thickness,
                   facecolor='gold', edgecolor='black', linewidth=2)
  ax4.add_patch(rect)

  # 繪製接地層
  ax4.axhline(y=-1, color='gray', linewidth=4, label='Ground Plane')
  ax4.axhline(y=1, color='gray', linewidth=4)

  ax4.set_xlabel('x (normalized)', fontsize=10)
  ax4.set_ylabel('y (normalized)', fontsize=10)
  ax4.set_title('TEM Mode E-Field Distribution\n(Stripline Cross-Section)', fontsize=12, fontweight='bold')
  ax4.set_aspect('equal')
  pyplot(fig)

elif menu==MENU[2]:
  fig, ax3= subplots(figsize=(10, 6))
  pass
  # ============================================
  # 圖 3: Via 製程流程
  # ============================================
  #ax3 = fig.add_subplot(3, 3, 3)
  ax3.axis('off')

  process = sim.via_fabrication_process()
  process_text = "Via Fabrication Process Flow:\n\n"
  for step in process[:5]:
      process_text += f"Step {step['step']}: {step['name']}\n"
      process_text += f"  → {step['description'][:40]}\n"

  ax3.text(0.05, 0.95, process_text, transform=ax3.transAxes,
          fontsize=9, verticalalignment='top', family='monospace',
          bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

  ax3.set_title('Via Fabrication Steps', fontsize=12, fontweight='bold')
  pyplot(fig)

elif menu==MENU[1]:
  fig, ax2= subplots(figsize=(10, 6))
  # ============================================
  # 圖 2: Coating 材質比較表
  # ============================================
  #ax2 = fig.add_subplot(3, 3, 2)
  ax2.axis('off')

  materials = sim.get_coating_materials()
  table_data = []
  for name, props in materials.items():
      if props['type'] in ['Superconducting', 'Adhesion Buffer']:
          table_data.append([
              name,
              props['type'][:4],
              f"{props['Tc_K']}",
              props['deposition_method'][:15],
              props['recommended_for'][:20]
          ])

  table = ax2.table(cellText=table_data,
                   colLabels=['Material', 'Type', 'Tc (K)', 'Deposition', 'Application'],
                   cellLoc='center',
                   loc='center',
                   colWidths=[0.2, 0.1, 0.1, 0.25, 0.35])
  table.auto_set_font_size(False)
  table.set_fontsize(8)
  table.scale(1, 2)

  # 標註超導材質
  for i, name in enumerate(materials.keys()):
      if materials[name]['type'] == 'Superconducting' and i < len(table_data):
          table[(i+1, 0)].set_facecolor('#E6F3FF')

  ax2.set_title('Coating Material Options\nfor Superconducting Vias', fontsize=12, fontweight='bold')
  pyplot(fig)

elif menu==MENU[0]:
  fig, ax1= subplots(figsize=(10, 6))
  pass
  # ============================================
  # 圖 1: Via 結構 3D 示意圖
  # ============================================
  #ax1 = fig.add_subplot(3, 3, 1)

  # 繪製 Via 剖面
  layers = [
      (0, 50, '#CD853F', 'Top Coverlay'),
      (50, 55, '#A9A9A9', 'Top Ground (5 μm)'),
      (55, 125, '#F4A460', 'Top Dielectric'),
      (125, 131, '#FFD700', 'Signal Layer'),
      (131, 201, '#F4A460', 'Bottom Dielectric'),
      (201, 206, '#A9A9A9', 'Bottom Ground (5 μm)'),
      (206, 256, '#CD853F', 'Bottom Coverlay'),
  ]

  for y_bottom, y_top, color, label in layers:
      rect = Rectangle((-0.3, y_bottom), 0.6, y_top - y_bottom, facecolor=color, edgecolor='black', linewidth=1)
      ax1.add_patch(rect)

  # Via 孔 (白色背景)
  via = Rectangle((-0.075, 55), 0.15, 151, facecolor='white', edgecolor='black', linewidth=2, hatch='///')
  ax1.add_patch(via)

  # Via Coating 層 (NbTi - 藍色)
  coating_inner = Rectangle((-0.065, 55), 0.13, 151, facecolor='#4169E1', edgecolor='black', linewidth=0.5, alpha=0.7)
  ax1.add_patch(coating_inner)

  # 標註 Coating
  ax1.annotate('NbTi Coating\n(300 nm)', xy=(0, 130), xytext=(0.5, 130), fontsize=9, color='blue', fontweight='bold', arrowprops=dict(arrowstyle='->', color='blue'))

  # 標註 Adhesion Layer
  ax1.annotate('Ti Buffer\n(20 nm)', xy=(0.065, 130), xytext=(0.5, 100), fontsize=8, color='green',
              arrowprops=dict(arrowstyle='->', color='green'))

  ax1.set_xlim(-0.8, 1.2)
  ax1.set_ylim(0, 280)
  ax1.set_xlabel('Width (mm)', fontsize=10)
  ax1.set_ylabel('Thickness (μm)', fontsize=10)
  ax1.set_title('Via Cross-Section Structure\n(Blind Via L2↔L6)', fontsize=12, fontweight='bold')
  ax1.set_aspect('auto')
  pyplot(fig)
#savefig('/mnt/agents/output/CF3_Via_TEM_Analysis.png', dpi=300, bbox_inches='tight')
#show()

#print("✓ Cri/oFlex 3 Via TEM 模式分析完成！")
