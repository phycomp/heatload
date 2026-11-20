from numpy import pi, sqrt
from streamlit import empty, radio, text_input

# 保存完整的 RectangularWaveguide 類別
"""
RectangularWaveguide - 矩形波導

實現矩形波導的電磁特性計算，包括TE/TM模式分析。
注意：波導傳輸的是TE或TM模式，不是TEM模式。

Author: TEM Transmission Line Simulator
Date: 2026-03-24
"""

class RectangularWaveguide:
    """
    矩形波導 (Rectangular Waveguide)
    
    尺寸: 寬邊 a, 窄邊 b (a > b)
    主模式: TE10 (截止頻率最低)
    
    關鍵特性:
    - 截止頻率: fc = c / (2a√εr)
    - 導波波長: λg = λ0 / √(1 - (fc/f)²)
    - 相速度: vp = c/√εr / √(1 - (fc/f)²) > c
    - 群速度: vg = c/√εr * √(1 - (fc/f)²) < c
    - 特性阻抗: Z_TE = η / √(1 - (fc/f)²)
    
    等效傳輸線參數:
    雖然波導不是TEM模式，但可以用等效L、C參數描述：
    C_eq = 1/(Z0 * vp)
    L_eq = Z0 / vp
    """
    
    def __init__(self, a, b, freq, er=1.0):
        """
        初始化矩形波導
        
        Parameters:
        -----------
        a : float
            寬邊 (m)，決定截止頻率
        b : float
            窄邊 (m)，b < a
        freq : float
            工作頻率 (Hz)
        er : float, optional
            填充介質的相對介電常數，預設為1.0 (空氣)
        """
        self.a = a  # 寬邊 (m)
        self.b = b  # 窄邊 (m)
        self.freq = freq
        self.er = er
        
        # 物理常數
        self.c = 299792458      # 光速 (m/s)
        self.eta0 = 377         # 真空波阻抗 (Ω)
        self.mu0 = 4 * pi * 1e-7  # 真空磁導率 (H/m)
        self.eps0 = 8.854e-12   # 真空介電常數 (F/m)
        
    def cutoff_frequency_te10(self):
        """
        計算TE10模式的截止頻率
        
        TE10是最低階模式，截止頻率由寬邊a決定：
        fc = c / (2a√εr)
        
        Returns:
        --------
        fc : float
            截止頻率 (Hz)
        """
        return self.c / (2 * self.a * sqrt(self.er))
    
    def cutoff_wavelength_te10(self):
        """
        計算TE10模式的截止波長
        
        λc = 2a
        
        Returns:
        --------
        lambda_c : float
            截止波長 (m)
        """
        return 2 * self.a
    
    def guide_wavelength(self):
        """
        計算導波波長 λg
        
        導波波長大於自由空間波長：
        λg = λ0 / √(1 - (fc/f)²)
        
        Returns:
        --------
        lambda_g : float
            導波波長 (m)，若f ≤ fc則返回inf
        """
        fc = self.cutoff_frequency_te10()
        if self.freq <= fc:
            return float('inf')  # 截止
        lambda0 = self.c / (self.freq * sqrt(self.er))
        return lambda0 / sqrt(1 - (fc / self.freq)**2)
    
    def phase_constant(self):
        """
        計算相位常數 β
        
        β = √(k² - (π/a)²) = k√(1 - (fc/f)²)
        
        Returns:
        --------
        beta : float
            相位常數 (rad/m)，若f ≤ fc則返回0
        """
        fc = self.cutoff_frequency_te10()
        if self.freq <= fc:
            return 0
        k = 2 * pi * self.freq * sqrt(self.er) / self.c
        return sqrt(k**2 - (pi / self.a)**2)
    
    def characteristic_impedance_te10(self):
        """
        計算TE10模式的特性阻抗
        
        Z_TE = η / √(1 - (fc/f)²)
        
        注意：這是"波阻抗"，與TEM傳輸線的特性阻抗概念略有不同。
        它描述了橫向電場與橫向磁場的比值。
        
        Returns:
        --------
        Z_te : float
            TE10模式特性阻抗 (Ω)，若f ≤ fc則返回inf
        """
        fc = self.cutoff_frequency_te10()
        if self.freq <= fc:
            return float('inf')
        eta = self.eta0 / sqrt(self.er)
        return eta / sqrt(1 - (fc / self.freq)**2)
    
    def group_velocity(self):
        """
        計算群速度 vg = dω/dβ
        
        群速度是能量傳播速度，小於光速：
        vg = (c/√εr) * √(1 - (fc/f)²)
        
        Returns:
        --------
        vg : float
            群速度 (m/s)，若f ≤ fc則返回0
        """
        fc = self.cutoff_frequency_te10()
        if self.freq <= fc:
            return 0
        return (self.c / sqrt(self.er)) * sqrt(1 - (fc / self.freq)**2)
    
    def phase_velocity(self):
        """
        計算相速度 vp = ω/β
        
        相速度是等相位面傳播速度，大於光速：
        vp = (c/√εr) / √(1 - (fc/f)²)
        
        注意：相速度超光速不違反相對論，因為它不傳遞信息。
        
        Returns:
        --------
        vp : float
            相速度 (m/s)，若f ≤ fc則返回inf
        """
        fc = self.cutoff_frequency_te10()
        if self.freq <= fc:
            return float('inf')
        return (self.c / sqrt(self.er)) / sqrt(1 - (fc / self.freq)**2)
    
    def capacitance_per_meter(self):
        """
        計算波導的等效單位長度電容 C (F/m)
        
        理論基礎:
        雖然波導傳輸的是TE/TM模式而非TEM模式，但我們可以從
        傳輸線理論推導出等效的L、C參數。
        
        對於傳輸線:
        Z0 = √(L/C)  →  L = Z0² * C
        vp = 1/√(LC)  →  C = 1/(Z0 * vp)
        
        因此，波導的等效電容:
        C_eq = 1 / (Z_TE * vp)
             = √(1-(fc/f)²) / (η * c/√εr) * √(1-(fc/f)²)
             = (1-(fc/f)²) / (η * c/√εr)
        
        這個等效電容描述了波導中電場能量的儲存能力。
        
        Returns:
        --------
        C : float
            等效單位長度電容 (F/m)
            若頻率低於截止頻率，返回0 (無傳播)
            
        Notes:
        ------
        - 等效電容隨頻率變化，這是波導色散特性的體現
        - 在截止頻率處，C_eq → 0
        - 當 f >> fc，C_eq 趨近於常數
        """
        fc = self.cutoff_frequency_te10()
        
        # 截止檢查
        if self.freq <= fc:
            return 0.0
        
        # 獲取TE10模式參數
        Z_te = self.characteristic_impedance_te10()
        vp = self.phase_velocity()
        
        # 檢查有效性
        if Z_te == float('inf') or vp == 0 or vp == float('inf'):
            return 0.0
        
        # 計算等效電容: C = 1/(Z0 * vp)
        C_eq = 1.0 / (Z_te * vp)
        
        return C_eq
    
    def inductance_per_meter(self):
        """
        計算波導的等效單位長度電感 L (H/m)
        
        基於傳輸線理論:
        Z0 = √(L/C)  →  L = Z0² * C = Z0 / vp
        
        或者:
        L_eq = Z_TE / vp
             = [η/√(1-(fc/f)²)] / [(c/√εr)/√(1-(fc/f)²)]
             = η / (c/√εr)
             = μ0 * (a/b)  (對於TE10模式的近似)
        
        有趣的是，等效電感在TE10模式下近似為常數，
        而等效電容隨頻率變化。
        
        Returns:
        --------
        L : float
            等效單位長度電感 (H/m)
            若頻率低於截止頻率，返回0
            
        Notes:
        ------
        - 等效電感主要取決於波導的幾何尺寸和磁導率
        - 對於空氣填充波導，L_eq ≈ μ0 * (a/b) 是常數
        """
        fc = self.cutoff_frequency_te10()
        
        if self.freq <= fc:
            return 0.0
        
        Z_te = self.characteristic_impedance_te10()
        vp = self.phase_velocity()
        
        if Z_te == float('inf') or vp == 0 or vp == float('inf'):
            return 0.0
        
        # 計算等效電感: L = Z0 / vp
        L_eq = Z_te / vp
        
        return L_eq
    
    def get_equivalent_transmission_line_parameters(self):
        """
        獲取波導的等效傳輸線參數
        
        將波導視為等效傳輸線，返回L、C、Z0、vp等參數。
        這些參數在頻率高於截止頻率時才有物理意義。
        
        Returns:
        --------
        dict : 包含等效傳輸線參數的字典
            - L_per_m: 單位長度電感 (H/m)
            - C_per_m: 單位長度電容 (F/m)
            - Z0_ohm: 特性阻抗 (Ω)
            - vp_m_s: 相速度 (m/s)
            - vg_m_s: 群速度 (m/s)
            - fc_Hz: 截止頻率 (Hz)
            - is_propagating: 是否處於傳播狀態 (bool)
            
        Example:
        --------
        >>> wg = RectangularWaveguide(22.86e-3, 10.16e-3, 10e9)
        >>> params = wg.get_equivalent_transmission_line_parameters()
        >>> 狀態.code(f"L = {params['L_per_m']*1e9:.2f} nH/m")
        >>> 狀態.code(f"C = {params['C_per_m']*1e12:.2f} pF/m")
        """
        C = self.capacitance_per_meter()
        L = self.inductance_per_meter()
        Z0 = self.characteristic_impedance_te10()
        vp = self.phase_velocity()
        vg = self.group_velocity()
        fc = self.cutoff_frequency_te10()
        
        return {
            'L_per_m': L,           # H/m
            'C_per_m': C,           # F/m
            'Z0_ohm': Z0,           # Ω
            'vp_m_s': vp,           # m/s
            'vg_m_s': vg,           # m/s
            'fc_Hz': fc,            # Hz
            'is_propagating': self.freq > fc
        }
    
    def power_handling_capability(self, max_electric_field=3e6):
        """
        估算波導的功率容量
        
        基於波導內最大電場強度限制（擊穿場強）。
        
        Parameters:
        -----------
        max_electric_field : float
            最大允許電場強度 (V/m)
            空氣擊穿場強約 3 MV/m
            
        Returns:
        --------
        P_max : float
            最大傳輸功率 (W)
        """
        fc = self.cutoff_frequency_te10()
        if self.freq <= fc:
            return 0.0
        
        # TE10模式功率容量公式
        # P_max = (a * b * E_max²) / (4 * Z_TE)
        Z_te = self.characteristic_impedance_te10()
        P_max = (self.a * self.b * max_electric_field**2) / (4 * Z_te)
        
        return P_max


MENU, 表單=[], ['矩形波導', '', '']		#, '錯綜複雜', '二十四節氣' # 使用範例和測試
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
if menu==len(表單): #
  pass
elif menu==MENU[1]: #
  pass
elif menu==MENU[0]: #矩形波導
    矩形=empty()
    狀態.code("="*70)
    狀態="RectangularWaveguide 類別測試"
    狀態+="="*70+'\n'
    
    # WR-90 波導 (X波段標準)
    a = 22.86e-3  # 寬邊 22.86 mm
    b = 10.16e-3  # 窄邊 10.16 mm
    
    wg = RectangularWaveguide(a, b, 10e9)
    fc = wg.cutoff_frequency_te10()
    
    狀態.code(f"\\n波導型號: WR-90")
    狀態.code(f"尺寸: a = {a*1000:.2f} mm, b = {b*1000:.2f} mm")
    狀態.code(f"TE10 截止頻率: {fc/1e9:.3f} GHz")
    狀態.code(f"單模工作頻段: {fc/1e9:.1f} - {2*fc/1e9:.1f} GHz")
    
    # 測試不同頻率下的等效參數
    狀態.code("\\n" + "-"*70)
    狀態.code("頻率響應特性:")
    狀態.code("-"*70)
    狀態.code(f"{'頻率(GHz)':<12} {'C (pF/m)':<15} {'L (nH/m)':<15} {'Z0 (Ω)':<12} {'狀態':<10}")
    狀態.code("-"*70)
    
    test_freqs = [5e9, 6.557e9, 8e9, 10e9, 12e9, 15e9]
    
    for f in test_freqs:
        wg.freq = f
        C = wg.capacitance_per_meter()
        L = wg.inductance_per_meter()
        Z0 = wg.characteristic_impedance_te10()
        
        if f > fc:
            status = "傳播"
            C_pF = C * 1e12
            L_nH = L * 1e9
            Z0_val = Z0
        else:
            status = "截止"
            C_pF = 0
            L_nH = 0
            Z0_val = float('inf')
        
        矩形.code(f"{f/1e9:<12.3f} {C_pF:<15.3f} {L_nH:<15.3f} {Z0_val:<12.1f} {status:<10}")
    
    狀態+="-"*70+'\n'
    狀態+="n10 GHz 時的詳細參數:\n" # 詳細參數
    wg.freq = 10e9
    params = wg.get_equivalent_transmission_line_parameters()
    
    狀態+=f"  等效電容 C: {params['C_per_m']*1e12:.3f} pF/m\n"
    狀態+=f"  等效電感 L: {params['L_per_m']*1e9:.3f} nH/m\n"
    狀態+=f"  特性阻抗 Z0: {params['Z0_ohm']:.2f} Ω\n"
    狀態+=f"  相速度 vp: {params['vp_m_s']/1e6:.2f} Mm/s\n"
    狀態+=f"  群速度 vg: {params['vg_m_s']/1e6:.2f} Mm/s\n"
    狀態+=f"  導波波長 λg: {wg.guide_wavelength()*1000:.2f} mm\n"
    
    狀態+="n驗證 Z0 = √(L/C):\n" # 驗證
    Z0_calc = sqrt(params['L_per_m'] / params['C_per_m'])
    狀態+=f"  計算值: {Z0_calc:.2f} Ω"
    狀態+=f"  理論值: {params['Z0_ohm']:.2f} Ω"
    狀態+=f"  相對誤差: {abs(Z0_calc - params['Z0_ohm'])/params['Z0_ohm']*100:.6f}%"
    
    # 功率容量
    P_max = wg.power_handling_capability()
    狀態+=f"\\n功率容量 (空氣擊穿): {P_max/1000:.2f} kW\n"
    
    狀態+="\\n✅ 測試完成！\n"

"""
with open('/mnt/kimi/output/rectangular_waveguide.py', 'w', encoding='utf-8') as f:
    f.write(rectangular_waveguide_code)

狀態.code("✅ RectangularWaveguide 類別已保存！")
狀態.code("文件位置: /mnt/kimi/output/rectangular_waveguide.py")
狀態.code("\n" + "="*70)
狀態.code("📋 capacitance_per_meter 方法說明")
狀態.code("="*70)

explanation = """
【方法名稱】capacitance_per_meter()

【功能】
計算矩形波導的等效單位長度電容 C (F/m)

【理論基礎】
雖然波導傳輸的是TE/TM模式而非TEM模式，但可以從傳輸線理論
推導出等效的L、C參數：

  傳輸線基本關係:
  ├─ Z0 = √(L/C)
  └─ vp = 1/√(LC)

  推導得:
  ├─ C = 1/(Z0 × vp)
  └─ L = Z0 / vp

【計算公式】
對於TE10模式:
  C_eq = 1 / (Z_TE × vp)
       = (1 - (fc/f)²) / (η × c/√εr)

其中:
  Z_TE = η / √(1 - (fc/f)²)  [TE10波阻抗]
  vp   = (c/√εr) / √(1 - (fc/f)²)  [相速度]
  η    = η0/√εr = 377/√εr Ω  [本徵阻抗]
  fc   = c/(2a√εr)  [截止頻率]

【返回值】
  float: 等效單位長度電容 (F/m)
         - f > fc: 正常值 (通常為 pF/m 級別)
         - f ≤ fc: 0 (截止狀態，無傳播)

【特性】
  ├─ 等效電容隨頻率變化 (色散特性)
  ├─ f → fc⁺ 時, C → 0
  ├─ f >> fc 時, C 趨近於常數
  └─ 與波導尺寸 a、b 和填充介質 εr 相關

【相關方法】
  ├─ inductance_per_meter(): 計算等效電感 L
  ├─ characteristic_impedance_te10(): TE10特性阻抗
  ├─ phase_velocity(): 相速度
  └─ get_equivalent_transmission_line_parameters(): 獲取所有等效參數
"""

狀態.code(explanation)

# 執行測試
狀態.code("\n" + "="*70)
狀態.code("執行測試驗證...")
狀態.code("="*70)

# 重新定義類別並測試
"""
exec(rectangular_waveguide_code)
