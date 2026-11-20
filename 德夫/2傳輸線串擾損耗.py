from streamlit import checkbox, columns, header, info, markdown, metric, number_input, plotly_chart, radio, set_page_config, sidebar, subheader, tabs, text_input, empty
from numpy import array, cos, cosh, e, exp, linspace, log, log10, logspace, meshgrid, nan, pi, sin, sinh, sqrt, zeros_like
from plotly.graph_objects import Figure, Heatmap, Scatter
#Contourpolar, Contourpolar
# 建立Streamlit應用程式代碼

#import streamlit as st
#import numpy as np
#import matplotlib.pyplot as plt
from scipy.special import ellipk, ellipe
#import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 頁面配置
set_page_config(
    page_title="TEM電磁傳輸線模擬器",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義CSS樣式
markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #ff7f0e;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #ff7f0e;
        padding-bottom: 0.5rem;
    }
    .formula-box {
        background-color: black;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
        font-family: 'Courier New', monospace;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: black;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: purple;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 物理公式實現 ====================

class TEMTransmissionLine:
    """TEM傳輸線基礎類"""
    def __init__(self, freq, er=4.3, tan_delta=0.02):
        self.freq = freq
        self.omega = 2 * pi * freq
        self.er = er
        self.tan_delta = tan_delta
        self.c = 299792458
        self.mu0 = 4 * pi * 1e-7
        self.eps0 = 8.854e-12
        self.eps = self.eps0 * self.er
        self.mu = self.mu0
        
    def phase_velocity(self):
        return self.c / sqrt(self.er)
    
    def wavelength(self):
        return self.phase_velocity() / self.freq

class CoaxialLine(TEMTransmissionLine):
    """同軸線"""
    def __init__(self, a, b, freq, er=2.1, tan_delta=0.0002):
        super().__init__(freq, er, tan_delta)
        self.a = a
        self.b = b
        
    def characteristic_impedance(self):
        return (60 / sqrt(self.er)) * log(self.b / self.a)
    
    def capacitance_per_meter(self):
        return (2 * pi * self.eps) / log(self.b / self.a)
    
    def inductance_per_meter(self):
        return (self.mu / (2 * pi)) * log(self.b / self.a)
    
    def conductor_loss(self, sigma=5.8e7):
        Rs = sqrt(pi * self.freq * self.mu / sigma)
        Z0 = self.characteristic_impedance()
        return (Rs / (4 * pi * Z0)) * (1/self.a + 1/self.b)
    
    def dielectric_loss(self):
        return (pi * self.freq * sqrt(self.er) * self.tan_delta) / self.c
    
    def total_attenuation_db(self, sigma=5.8e7):
        alpha_total = self.conductor_loss(sigma) + self.dielectric_loss()
        return 20 * log10(exp(1)) * alpha_total

class MicrostripLine(TEMTransmissionLine):
    """微帶線"""
    def __init__(self, w, h, t, freq, er=4.3, tan_delta=0.02):
        super().__init__(freq, er, tan_delta)
        self.w = w
        self.h = h
        self.t = t
        
    def effective_dielectric_constant(self):
        w_h = self.w / self.h
        if w_h <= 1:
            F = 1 / sqrt(1 + 12 * self.h / self.w)
        else:
            F = 1 / sqrt(1 + 12 * self.h / self.w)
        
        a = (self.er + 1) / 2
        b = (self.er - 1) / 2
        
        if self.t > 0:
            delta_w = (self.t / self.h) * (1 + 1/cosh(sqrt(self.er - 1))) / pi
            w_eff = self.w / self.h + delta_w
        else:
            w_eff = self.w / self.h
            
        F = 1 / sqrt(1 + 12 / w_eff)
        er_eff = a + b * F
        
        # 頻率色散修正
        if self.freq > 1e9:
            f_GHz = self.freq / 1e9
            P1 = 0.27488 + (0.6315 + 0.525 / ((1 + 0.0157*f_GHz)**20)) * (self.w/self.h)
            P1 = P1 - 0.065683 * exp(-8.7513 * self.w/self.h)
            P2 = 0.33622 * (1 - exp(-0.03442 * self.er))
            P3 = 0.0363 * exp(-4.6 * self.w/self.h) * (1 - exp(-(self.w/self.h/0.038)**1.4))
            P4 = 1 + 2.751 * (1 - exp(-(self.er/15.916)**8))
            M = P1 * P2 * ((0.1844 + P3 * P4) * 10 * f_GHz)**1.5763
            er_eff = self.er - (self.er - er_eff) / (1 + M)
            
        return er_eff
    
    def characteristic_impedance(self):
        er_eff = self.effective_dielectric_constant()
        w_h = self.w / self.h
        
        if w_h <= 1:
            Z0 = (60 / sqrt(er_eff)) * log(8 / w_h + 0.25 * w_h)
        else:
            Z0 = (120 * pi / sqrt(er_eff)) / (w_h + 1.393 + 0.667 * log(w_h + 1.444))
        
        return Z0
    
    def capacitance_per_meter(self):
        Z0 = self.characteristic_impedance()
        er_eff = self.effective_dielectric_constant()
        return sqrt(self.eps0 * self.er * self.mu0) / Z0
    
    def inductance_per_meter(self):
        Z0 = self.characteristic_impedance()
        er_eff = self.effective_dielectric_constant()
        return Z0 * sqrt(self.eps0 * self.er * self.mu0)
    
    def phase_velocity(self):
        er_eff = self.effective_dielectric_constant()
        return self.c / sqrt(er_eff)

class Stripline(TEMTransmissionLine):
    """帶狀線"""
    def __init__(self, w, b, t, freq, er=4.3, tan_delta=0.02):
        super().__init__(freq, er, tan_delta)
        self.w = w
        self.b = b
        self.t = t
        
    def effective_width(self):
        if self.t > 0:
            delta_w = (self.t / pi) * log(4 * e / 
                     sqrt((self.t / self.b)**2 + (1 / pi)**2 * (self.t / self.w)**2))
            return self.w - delta_w
        return self.w
    
    def characteristic_impedance(self):
        w_eff = self.effective_width()
        if w_eff / self.b > 0.35:
            Z0 = (30 * pi / sqrt(self.er)) * (self.b / (w_eff + 0.441 * self.b))
        else:
            Z0 = (60 / sqrt(self.er)) * log(8 * self.b / (pi * w_eff))
        return Z0
    
    def capacitance_per_meter(self):
        Z0 = self.characteristic_impedance()
        return sqrt(self.eps * self.mu) / Z0
    
    def inductance_per_meter(self):
        Z0 = self.characteristic_impedance()
        return Z0 * sqrt(self.eps * self.mu)

class CPWLine(TEMTransmissionLine):
    """共面波導"""
    def __init__(self, w, s, h, freq, er=10.2, tan_delta=0.0002):
        super().__init__(freq, er, tan_delta)
        self.w = w
        self.s = s
        self.h = h
        
    def geometric_ratio(self):
        return self.w / (self.w + 2 * self.s)
    
    def effective_dielectric_constant(self):
        k = self.geometric_ratio()
        k1 = sinh(pi * self.w / (4 * self.h)) / sinh(pi * (self.w + 2*self.s) / (4 * self.h))
        q = ellipk(k) * ellipe(k1) / (ellipe(k) * ellipk(k1))
        er_eff = 1 + q * (self.er - 1)
        return er_eff
    
    def characteristic_impedance(self):
        k = self.geometric_ratio()
        k_prime = sqrt(1 - k**2)
        K_k = ellipk(k)
        K_kp = ellipk(k_prime)
        er_eff = self.effective_dielectric_constant()
        Z0 = (30 * pi / sqrt(er_eff)) * (K_kp / K_k)
        return Z0

class RectangularWaveguide:
    """矩形波導"""
    def __init__(self, a, b, freq, er=1.0):
        self.a = a
        self.b = b
        self.freq = freq
        self.er = er
        self.c = 299792458
        self.eta0 = 377
        
    def cutoff_frequency_te10(self):
        return self.c / (2 * self.a * sqrt(self.er))
    
    def guide_wavelength(self):
        fc = self.cutoff_frequency_te10()
        if self.freq <= fc:
            return float('inf')
        lambda0 = self.c / (self.freq * sqrt(self.er))
        return lambda0 / sqrt(1 - (fc / self.freq)**2)
    
    def phase_constant(self):
        fc = self.cutoff_frequency_te10()
        if self.freq <= fc:
            return 0
        k = 2 * pi * self.freq * sqrt(self.er) / self.c
        return sqrt(k**2 - (pi / self.a)**2)
    
    def characteristic_impedance_te10(self):
        fc = self.cutoff_frequency_te10()
        if self.freq <= fc:
            return float('inf')
        eta = self.eta0 / sqrt(self.er)
        return eta / sqrt(1 - (fc / self.freq)**2)
    
    def phase_velocity(self):
        fc = self.cutoff_frequency_te10()
        if self.freq <= fc:
            return float('inf')
        return (self.c / sqrt(self.er)) / sqrt(1 - (fc / self.freq)**2)
    def capacitance_per_meter(self):
        return (2 * pi * self.eps) / log(self.b / self.a)

class CrosstalkCalculator:
    """
    串擾計算器 (Crosstalk Calculator)
    
    完整實現傳輸線串擾分析，包括：
    - 近端串擾 (NEXT)
    - 遠端串擾 (FEXT)
    - 插入損耗 (IL)
    - 回波損耗 (RL)
    """
    
    def __init__(self, line, spacing, coupling_length):
        """
        初始化串擾計算器
        
        Parameters:
        -----------
        line : TransmissionLine object
            傳輸線物件 (Microstrip, Stripline, Coaxial等)
        spacing : float
            線間距 s (m)
        coupling_length : float
            耦合長度 l (m)
        """
        self.line = line
        self.s = spacing
        self.l = coupling_length
        
    def mutual_capacitance(self):
        """
        計算互電容 Cm (F/m)
        
        對於微帶線的近似公式 (基於Akhtarzad方法)
        """
        if hasattr(self.line, 'w') and hasattr(self.line, 'h'):
            h = self.line.h
            w = self.line.w
            s = self.s
            er = self.line.er
            
            # 簡化模型: 互電容與幾何尺寸和介電常數相關
            Cm = (self.line.eps0 * (1 + er) / 2) * (w / s) * exp(-s / h)
            return Cm
        return 0.0
    
    def mutual_inductance(self):
        """
        計算互電感 Lm (H/m)
        
        基於兩平行導線的互感公式
        """
        if hasattr(self.line, 'h'):
            h = self.line.h
            s = self.s
            # 互電感近似公式
            Lm = (self.line.mu0 / (2 * pi)) * log(1 + (h / s)**2)
            return Lm
        return 0.0
    
    def calculate_next(self):
        """
        計算近端串擾 (Near-End Crosstalk, NEXT) - dB
        
        對於弱耦合、匹配端接的情況:
        NEXT ≈ 20*log10((Kc + Kl) / 4)
        
        Returns:
        --------
        NEXT_db : float
            近端串擾值 (dB)，負值表示衰減
        Kc : float
            電容耦合係數
        Kl : float
            電感耦合係數
        """
        C = self.line.capacitance_per_meter()
        L = self.line.inductance_per_meter()
        
        if C == 0 or L == 0:
            return -100, 0, 0  # 無耦合時返回極小值
        
        Cm = self.mutual_capacitance()
        Lm = self.mutual_inductance()
        
        # 耦合係數
        Kc = Cm / C  # 電容耦合係數
        Kl = Lm / L  # 電感耦合係數
        
        # NEXT 電壓比 (弱耦合近似)
        # 近端串擾是電容耦合和電感耦合的疊加
        Vnext_ratio = (Kc + Kl) / 4
        
        # 轉換為dB (負值表示串擾小於主信號)
        if Vnext_ratio > 0:
            NEXT_db = 20 * log10(Vnext_ratio)
        else:
            NEXT_db = -100  # 極小值
        
        return NEXT_db, Kc, Kl
    
    def calculate_fext(self):
        """
        計算遠端串擾 (Far-End Crosstalk, FEXT) - dB
        
        對於弱耦合:
        FEXT ≈ 20*log10((Kc - Kl) * l * f / (2*vp))
        
        Returns:
        --------
        FEXT_db : float
            遠端串擾值 (dB)
        Kc : float
            電容耦合係數
        Kl : float
            電感耦合係數
        """
        C = self.line.capacitance_per_meter()
        L = self.line.inductance_per_meter()
        vp = self.line.phase_velocity()
        
        if C == 0 or L == 0 or vp == 0:
            return -100, 0, 0
        
        Cm = self.mutual_capacitance()
        Lm = self.mutual_inductance()
        
        # 耦合係數
        Kc = Cm / C
        Kl = Lm / L
        
        # FEXT 電壓比 (與耦合長度和頻率成正比)
        # 遠端串擾是電容耦合和電感耦合的相減
        Vfext_ratio = (Kc - Kl) * self.l * self.line.freq / (2 * vp)
        
        # 轉換為dB
        if abs(Vfext_ratio) > 0:
            FEXT_db = 20 * log10(abs(Vfext_ratio))
        else:
            FEXT_db = -100
        
        return FEXT_db, Kc, Kl
    
    def insertion_loss(self, length=None, sigma=5.8e7):
        """
        計算插入損耗 (Insertion Loss, IL) - dB
        
        IL = α_total * l * 8.686 (Np轉dB)
        
        插入損耗包含：
        1. 導體損耗 (趨膚效應)
        2. 介質損耗 (tan δ)
        3. 輻射損耗 (開放結構如微帶線)
        
        Parameters:
        -----------
        length : float, optional
            傳輸線長度 (m)，若未指定則使用耦合長度
        sigma : float
            導體電導率 (S/m)，銅預設為5.8e7
            
        Returns:
        --------
        IL_db : float
            插入損耗 (dB)，正值表示衰減
        """
        if length is None:
            length = self.l
            
        # 總衰減常數 (Np/m)
        alpha_total = 0.0
        
        # 1. 導體損耗 (如果傳輸線有此方法)
        if hasattr(self.line, 'conductor_loss'):
            alpha_c = self.line.conductor_loss(sigma)
            alpha_total += alpha_c
        elif hasattr(self.line, 'alpha_conductor'):
            alpha_total += self.line.alpha_conductor
            
        # 2. 介質損耗
        if hasattr(self.line, 'dielectric_loss'):
            alpha_d = self.line.dielectric_loss()
            alpha_total += alpha_d
        elif hasattr(self.line, 'alpha_dielectric'):
            alpha_total += self.line.alpha_dielectric
        else:
            # 通用介質損耗計算
            # αd = (π * f * √εr * tanδ) / c
            alpha_d = (pi * self.line.freq * 
                      sqrt(self.line.er) * self.line.tan_delta) / self.line.c
            alpha_total += alpha_d
        
        # 3. 輻射損耗 (僅開放結構如微帶線)
        if hasattr(self.line, 'radiation_loss'):
            alpha_total += self.line.radiation_loss()
        elif hasattr(self.line, 'w') and hasattr(self.line, 'h'):
            # 檢查是否為微帶線 (有w和h但沒有b，b是帶狀線的參數)
            if not hasattr(self.line, 'b'):
                # 微帶線輻射損耗近似 (高頻時顯著)
                h = self.line.h
                w = self.line.w
                f = self.line.freq
                c = self.line.c
                
                # 計算有效介電常數
                if hasattr(self.line, 'effective_dielectric_constant'):
                    er_eff = self.line.effective_dielectric_constant()
                else:
                    er_eff = self.line.er
                
                # 輻射損耗近似公式 (高頻時考慮)
                if f > 1e9:
                    lambda0 = c / f
                    # 簡化公式
                    alpha_rad = (pi**2 * (er_eff - 1) * (w/h)**2) / (3 * lambda0**2)
                    alpha_total += alpha_rad
        
        # Np 轉換為 dB (1 Np = 8.686 dB)
        IL_db = alpha_total * length * 8.686
        
        return IL_db
    
    def return_loss(self, Z_load=None, Z_source=None):
        """
        計算回波損耗 (Return Loss, RL) - dB
        
        RL = -20*log10(|Γ|)
        
        其中反射係數 Γ = (ZL - Z0) / (ZL + Z0)
        
        Parameters:
        -----------
        Z_load : float, optional
            負載阻抗 (Ω)，預設為匹配 (Z0)
        Z_source : float, optional
            源阻抗 (Ω)，預設為匹配 (Z0)
            
        Returns:
        --------
        RL_db : float
            回波損耗 (dB)，正值表示反射小
            - 匹配時: RL → ∞ (理想情況)
            - 完全反射: RL = 0 dB
        """
        Z0 = self.line.characteristic_impedance()
        
        # 若未指定負載阻抗，假設匹配
        if Z_load is None:
            Z_load = Z0
        if Z_source is None:
            Z_source = Z0
            
        # 計算反射係數 Γ
        # 考慮源阻抗和負載阻抗的不匹配
        if Z0 + Z_load == 0:
            gamma = 1.0  # 避免除以零
        else:
            gamma = (Z_load - Z0) / (Z_load + Z0)
        
        # 回波損耗 (dB)
        # RL = -20*log10(|Γ|)
        # 當 |Γ| = 0 (完全匹配), RL → ∞
        # 當 |Γ| = 1 (完全反射), RL = 0
        abs_gamma = abs(gamma)
        
        if abs_gamma < 1e-10:
            RL_db = 100.0  # 近似無限大
        else:
            RL_db = -20 * log10(abs_gamma)
        
        return RL_db
    
    def calculate_all_parameters(self, length=None, Z_load=None, sigma=5.8e7):
        """
        計算所有串擾和損耗參數
        
        Parameters:
        -----------
        length : float, optional
            傳輸線長度 (m)
        Z_load : float, optional
            負載阻抗 (Ω)
        sigma : float
            導體電導率 (S/m)
            
        Returns:
        --------
        dict : 包含所有計算結果的字典
        """
        NEXT, Kc, Kl = self.calculate_next()
        FEXT, _, _ = self.calculate_fext()
        IL = self.insertion_loss(length, sigma)
        RL = self.return_loss(Z_load)
        
        return {
            'NEXT_dB': NEXT,
            'FEXT_dB': FEXT,
            'IL_dB': IL,
            'RL_dB': RL,
            'Kc': Kc,
            'Kl': Kl,
            'coupling_length_m': self.l,
            'spacing_m': self.s,
            'Z0_ohm': self.line.characteristic_impedance()
        }

MATERIALS = {
    'Kapton (聚醯亞胺)': {'er': 3.4, 'tan_delta': 0.002},
    'PTFE (聚四氟乙烯)': {'er': 2.1, 'tan_delta': 0.0002},
    'FR-4': {'er': 4.3, 'tan_delta': 0.02},
    'Rogers RO4350B': {'er': 3.66, 'tan_delta': 0.0037},
    'Alumina (氧化鋁)': {'er': 9.8, 'tan_delta': 0.0001},
    'Silicon': {'er': 11.9, 'tan_delta': 0.004}
} # 材料數據庫

# ==================== Streamlit UI ====================

MENU, 表單=[], ['串擾', '損耗', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
if menu==len(表單): #
  pass
elif menu==MENU[1]: #
  pass
elif menu==MENU[0]: #串擾
    markdown('<h1 class="main-header">⚡ TEM電磁傳輸線模擬器</h1>', unsafe_allow_html=True)
    
    傳輸線=["同軸線 (Coaxial)", "微帶線 (Microstrip)", "帶狀線 (Stripline)", "共面波導 (CPW)", "矩形波導 (Waveguide)"]
    with sidebar: # 側邊欄
        subheader("🔧 參數設定")
        
        freq_unit = radio("頻率單位", ["GHz", "MHz", "kHz"], index=0) # 頻率設定
        freq_val = number_input(f"頻率 ({freq_unit})", min_value=0.1, max_value=1000.0, value=1.0, step=0.1)
        freq = freq_val * {'GHz': 1e9, 'MHz': 1e6, 'kHz': 1e3}[freq_unit]
        
        subheader("材料選擇") # 材料選擇
        介電 = radio("介電材料", list(MATERIALS.keys()), index=2)
        er = MATERIALS[介電]['er']
        tan_delta = MATERIALS[介電]['tan_delta']
        線類型 = radio("選擇傳輸線類型", ["同軸線 (Coaxial)", "微帶線 (Microstrip)", "帶狀線 (Stripline)", "共面波導 (CPW)", "矩形波導 (Waveguide)"], horizontal=True)
        
        col1, col2 = columns(2)
        with col1:
            metric("εr", f"{er}")
        with col2:
            metric("tan δ", f"{tan_delta}")
        
        # 自定義材料
        use_custom = checkbox("使用自定義材料")
        if use_custom:
            er = number_input("相對介電常數 εr", min_value=1.0, max_value=100.0, value=er, step=0.1)
            tan_delta = number_input("損耗角正切 tan δ", min_value=0.00001, max_value=1.0, value=tan_delta, format="%.5f")
    
    # 主內容區
    tab1, tab2, tab3, tab4, tab5 = tabs([
        "📊 傳輸線計算", 
        "🔀 串擾分析", 
        "📈 頻率響應", 
        "📐 場分佈", 
        "📖 物理公式"
    ])
    # Tab 1: 傳輸線計算
    with tab1:
        markdown('<h2 class="section-header">傳輸線參數計算</h2>', unsafe_allow_html=True)
        
        
        col_params, col_results = columns([1, 1])
        
        with col_params:
            subheader("幾何參數")
            
            if 線類型 == "同軸線 (Coaxial)":
                a_mm = number_input("內導體半徑 a (mm)", min_value=0.1, max_value=50.0, value=1.0, step=0.1)
                b_mm = number_input("外導體內徑 b (mm)", min_value=0.5, max_value=100.0, value=3.5, step=0.1)
                a, b = a_mm/1000, b_mm/1000
                line = CoaxialLine(a, b, freq, er, tan_delta)
                
            elif 線類型 == "微帶線 (Microstrip)":
                w_mm = number_input("導帶寬度 w (mm)", min_value=0.1, max_value=50.0, value=2.0, step=0.1)
                h_mm = number_input("介質厚度 h (mm)", min_value=0.1, max_value=10.0, value=1.6, step=0.1)
                t_um = number_input("導帶厚度 t (μm)", min_value=0.0, max_value=100.0, value=35.0, step=1.0)
                w, h, t = w_mm/1000, h_mm/1000, t_um/1e6
                line = MicrostripLine(w, h, t, freq, er, tan_delta)
                
            elif 線類型 == "帶狀線 (Stripline)":
                w_mm = number_input("導帶寬度 w (mm)", min_value=0.1, max_value=50.0, value=2.0, step=0.1)
                b_mm = number_input("總厚度 b (mm)", min_value=0.2, max_value=20.0, value=3.2, step=0.1)
                t_um = number_input("導帶厚度 t (μm)", min_value=0.0, max_value=100.0, value=35.0, step=1.0)
                w, b, t = w_mm/1000, b_mm/1000, t_um/1e6
                line = Stripline(w, b, t, freq, er, tan_delta)
                
            elif 線類型 == "共面波導 (CPW)":
                w_mm = number_input("中心導帶寬度 w (mm)", min_value=0.1, max_value=50.0, value=2.0, step=0.1)
                s_mm = number_input("間隙寬度 s (mm)", min_value=0.1, max_value=50.0, value=0.5, step=0.1)
                h_mm = number_input("介質厚度 h (mm)", min_value=0.1, max_value=10.0, value=1.6, step=0.1)
                w, s, h = w_mm/1000, s_mm/1000, h_mm/1000
                line = CPWLine(w, s, h, freq, er, tan_delta)
                
            else:  # 矩形波導
                a_mm = number_input("寬邊 a (mm)", min_value=10.0, max_value=500.0, value=22.86, step=0.1)
                b_mm = number_input("窄邊 b (mm)", min_value=5.0, max_value=250.0, value=10.16, step=0.1)
                a, b = a_mm/1000, b_mm/1000
                line = RectangularWaveguide(a, b, freq, er)
        
        with col_results:
            subheader("計算結果")
            
            if 線類型 != "矩形波導 (Waveguide)":
                Z0 = line.characteristic_impedance()
                vp = line.phase_velocity()
                wavelength = line.wavelength()
                
                # 顯示結果
                metric("特性阻抗 Z₀", f"{Z0:.2f} Ω")
                metric("相速度 vp", f"{vp/1e6:.2f} Mm/s")
                metric("波長 λ", f"{wavelength*1000:.2f} mm")
                
                if hasattr(line, 'effective_dielectric_constant'):
                    er_eff = line.effective_dielectric_constant()
                    metric("有效介電常數 εeff", f"{er_eff:.3f}")
                
                if isinstance(line, CoaxialLine):
                    atten = line.total_attenuation_db()
                    metric("衰減常數", f"{atten*1000:.4f} dB/km")
                    
            else:
                fc = line.cutoff_frequency_te10()
                Z0 = line.characteristic_impedance_te10()
                lambda_g = line.guide_wavelength()
                vp = line.phase_velocity()
                
                metric("截止頻率 fc", f"{fc/1e9:.3f} GHz")
                metric("特性阻抗 Z₀ (TE₁₀)", f"{Z0:.2f} Ω" if Z0 != float('inf') else "∞ (截止)")
                metric("導波波長 λg", f"{lambda_g*1000:.2f} mm" if lambda_g != float('inf') else "∞")
                metric("相速度 vp", f"{vp/1e6:.2f} Mm/s" if vp != float('inf') else "∞")
    
    # Tab 2: 串擾分析
    with tab2:
        markdown('<h2 class="section-header">串擾分析 (Crosstalk)</h2>', unsafe_allow_html=True)
        
        if 線類型 in 傳輸線:#["微帶線 (Microstrip)", "帶狀線 (Stripline)"]:
            col_xtalk1, col_xtalk2 = columns([1, 1])
            
            with col_xtalk1:
                subheader("耦合參數")
                s_mm = number_input("線間距 s (mm)", min_value=0.1, max_value=50.0, value=2.0, step=0.1)
                l_cm = number_input("耦合長度 (cm)", min_value=0.1, max_value=100.0, value=10.0, step=0.5)
                
                s = s_mm / 1000
                l = l_cm / 100
                
                calc = CrosstalkCalculator(line, s, l)
                NEXT, Kc, Kl = calc.calculate_next()
                FEXT, _, _ = calc.calculate_fext()
                
            with col_xtalk2:
                subheader("串擾結果")
                
                # 顯示耦合係數
                col_k1, col_k2 = columns(2)
                with col_k1:
                    metric("電容耦合係數 Kc", f"{Kc:.4f}")
                with col_k2:
                    metric("電感耦合係數 Kl", f"{Kl:.4f}")
                
                # 顯示串擾值
                metric("近端串擾 NEXT", f"{NEXT:.2f} dB")
                metric("遠端串擾 FEXT", f"{FEXT:.2f} dB")
                
                # 插入損耗和回波損耗
                if hasattr(line, 'total_attenuation_db'):
                    IL = line.total_attenuation_db() * l
                    metric(f"插入損耗 IL ({l_cm}cm)", f"{IL:.4f} dB")
                
                RL = calc.return_loss()
                metric("回波損耗 RL (匹配)", f"{RL:.2f} dB")
            
            # 串擾 vs 頻率圖
            subheader("串擾頻率響應")
            freqs = logspace(6, 11, 100)  # 1 MHz to 100 GHz
            
            next_vals = []
            fext_vals = []
            
            for f in freqs:
                if   線類型 == "同軸線 (Coaxial)":
                    temp_line = CoaxialLine(line.a, line.b, f, er, tan_delta)
                elif 線類型 == "微帶線 (Microstrip)":
                    temp_line = MicrostripLine(line.w, line.h, line.t, f, er, tan_delta)
                #elif 線類型 == "微帶線 (Microstrip)":
                elif 線類型 == "帶狀線 (Stripline)":
                    temp_line = Stripline(line.w, line.b, line.t, f, er, tan_delta)
                elif 線類型 == "共面波導 (CPW)":
                    temp_line = CPWLine(w, s, h, freq, er, tan_delta)
                    #z0_vals.append(temp.characteristic_impedance())
                    #atten_vals.append(temp.total_attenuation_db())
                    #er_eff_vals.append(er)
                else:
                    temp_line = RectangularWaveguide(a, b, freq, er)
                
                temp_calc = CrosstalkCalculator(temp_line, s, l)
                n, _, _ = temp_calc.calculate_next()
                x, _, _ = temp_calc.calculate_fext()
                next_vals.append(n)
                fext_vals.append(x)
            
            fig_xtalk = Figure()
            fig_xtalk.add_trace(Scatter(x=freqs/1e9, y=next_vals, mode='lines', name='NEXT', line=dict(color='red', width=2)))
            fig_xtalk.add_trace(Scatter(x=freqs/1e9, y=fext_vals, mode='lines', name='FEXT', line=dict(color='blue', width=2)))
            fig_xtalk.update_layout(
                xaxis_title='頻率 (GHz)',
                yaxis_title='串擾 (dB)',
                xaxis_type='log',
                title='串擾 vs 頻率',
                template='plotly_white'
            )
            plotly_chart(fig_xtalk, use_container_width=True)
            
        else:
            info("串擾分析目前僅支援微帶線和帶狀線。請在左側選擇相應的傳輸線類型。")
    
    # Tab 3: 頻率響應
    with tab3:
        markdown('<h2 class="section-header">頻率響應分析</h2>', unsafe_allow_html=True)
        
        freqs = logspace(6, 11, 200)
        
        if 線類型 != "矩形波導 (Waveguide)":
            z0_vals = []
            er_eff_vals = []
            atten_vals = []
            
            for f in freqs:
                if 線類型 == "同軸線 (Coaxial)":
                    temp = CoaxialLine(line.a, line.b, f, er, tan_delta)
                    z0_vals.append(temp.characteristic_impedance())
                    atten_vals.append(temp.total_attenuation_db())
                    er_eff_vals.append(er)
                elif 線類型 == "微帶線 (Microstrip)":
                    temp = MicrostripLine(line.w, line.h, line.t, f, er, tan_delta)
                    z0_vals.append(temp.characteristic_impedance())
                    er_eff_vals.append(temp.effective_dielectric_constant())
                    atten_vals.append(0)
                elif 線類型 == "帶狀線 (Stripline)":
                    temp = Stripline(line.w, line.b, line.t, f, er, tan_delta)
                    z0_vals.append(temp.characteristic_impedance())
                    er_eff_vals.append(er)
                    atten_vals.append(0)
                elif 線類型 == "共面波導 (CPW)":
                    temp = CPWLine(line.w, line.s, line.h, f, er, tan_delta)
                    z0_vals.append(temp.characteristic_impedance())
                    er_eff_vals.append(temp.effective_dielectric_constant())
                    atten_vals.append(0)
            
            col_f1, col_f2 = columns(2)
            
            with col_f1:
                # 特性阻抗 vs 頻率
                fig_z0 = Figure()
                fig_z0.add_trace(Scatter(x=freqs/1e9, y=z0_vals, mode='lines', line=dict(color='purple', width=2)))
                fig_z0.update_layout(
                    xaxis_title='頻率 (GHz)',
                    yaxis_title='特性阻抗 Z₀ (Ω)',
                    xaxis_type='log',
                    title='特性阻抗 vs 頻率',
                    template='plotly_white'
                )
                plotly_chart(fig_z0, use_container_width=True)
            
            with col_f2:
                # 有效介電常數 vs 頻率
                fig_er = Figure()
                fig_er.add_trace(Scatter(x=freqs/1e9, y=er_eff_vals, mode='lines', line=dict(color='green', width=2)))
                fig_er.update_layout(
                    xaxis_title='頻率 (GHz)',
                    yaxis_title='有效介電常數 εeff',
                    xaxis_type='log',
                    title='有效介電常數 vs 頻率 (色散效應)',
                    template='plotly_white'
                )
                plotly_chart(fig_er, use_container_width=True)
            
            # 衰減 (僅同軸線)
            if 線類型 == "同軸線 (Coaxial)":
                fig_att = Figure()
                fig_att.add_trace(Scatter(x=freqs/1e9, y=array(atten_vals)*1000, mode='lines', line=dict(color='orange', width=2)))
                fig_att.update_layout(
                    xaxis_title='頻率 (GHz)',
                    yaxis_title='衰減 (dB/km)',
                    xaxis_type='log',
                    yaxis_type='log',
                    title='衰減常數 vs 頻率',
                    template='plotly_white'
                )
                plotly_chart(fig_att, use_container_width=True)
                
        else:
            # 波導頻率響應
            z0_vals = []
            lambda_g_vals = []
            vp_vals = []
            
            for f in freqs:
                temp = RectangularWaveguide(line.a, line.b, f, er)
                z0_vals.append(temp.characteristic_impedance_te10())
                lambda_g_vals.append(temp.guide_wavelength())
                vp_vals.append(temp.phase_velocity())
            
            # 轉換無窮大為NaN以便繪圖
            z0_vals = [z if z != float('inf') else nan for z in z0_vals]
            lambda_g_vals = [lg if lg != float('inf') else nan for lg in lambda_g_vals]
            vp_vals = [vp if vp != float('inf') else nan for vp in vp_vals]
            
            fig_wg = make_subplots(rows=2, cols=2, subplot_titles=('特性阻抗', '導波波長', '相速度', '截止頻率'))
            
            fig_wg.add_trace(Scatter(x=freqs/1e9, y=z0_vals, mode='lines'), row=1, col=1)
            fig_wg.add_trace(Scatter(x=freqs/1e9, y=array(lambda_g_vals)*1000, mode='lines'), row=1, col=2)
            fig_wg.add_trace(Scatter(x=freqs/1e9, y=array(vp_vals)/1e6, mode='lines'), row=2, col=1)
            
            fc = line.cutoff_frequency_te10()
            fig_wg.add_vline(x=fc/1e9, line_dash="dash", line_color="red", row=1, col=1)
            fig_wg.add_vline(x=fc/1e9, line_dash="dash", line_color="red", row=1, col=2)
            fig_wg.add_vline(x=fc/1e9, line_dash="dash", line_color="red", row=2, col=1)
            
            fig_wg.update_layout(height=600, template='plotly_white', showlegend=False)
            fig_wg.update_xaxes(type='log')
            plotly_chart(fig_wg, use_container_width=True)
            
            info(f"紅色虛線標示 TE₁₀ 截止頻率: {fc/1e9:.3f} GHz")
    
    # Tab 4: 場分佈
    with tab4:
        markdown('<h2 class="section-header">電磁場分佈</h2>', unsafe_allow_html=True)
        
        if 線類型 == "同軸線 (Coaxial)":
            subheader("同軸線 TEM 場分佈")
            
            r = linspace(line.a, line.b, 100)
            theta = linspace(0, 2*pi, 100)
            R, Theta = meshgrid(r, theta)
            
            # TEM模式: E ∝ 1/r, H ∝ 1/r
            E_r = 1 / R
            H_theta = 1 / R
            
            fig_field = make_subplots(rows=1, cols=2, specs=[[{'type': 'polar'}, {'type': 'polar'}]],
                                     subplot_titles=('電場 E (徑向)', '磁場 H (角向)'))
            
            #fig_field.add_trace(Contourpolar(r=R.flatten(), theta=Theta.flatten()*180/pi, z=E_r.flatten(), colorscale='Reds', name='E field'), row=1, col=1)
            #fig_field.add_trace(Contourpolar(r=R.flatten(), theta=Theta.flatten()*180/pi, z=H_theta.flatten(), colorscale='Blues', name='H field'), row=1, col=2)
            
            fig_field.update_layout(height=500, template='plotly_white')
            plotly_chart(fig_field, use_container_width=True)
            
            markdown("""
            **同軸線 TEM 模式特性:**
            - 電場 E: 純徑向分佈，E ∝ 1/r
            - 磁場 H: 純角向分佈，H ∝ 1/r
            - 波阻抗: Z₀ = E/H = √(μ/ε) ≈ 377/√εᵣ Ω
            """)
            
        elif 線類型 == "矩形波導 (Waveguide)":
            subheader("矩形波導 TE₁₀ 場分佈")
            
            x = linspace(0, line.a, 50)
            z = linspace(0, 2*line.a, 50)
            X, Z = meshgrid(x, z)
            
            # TE10 模式場分佈
            k = pi / line.a
            beta = line.phase_constant()
            
            Ey = sin(k * X) * cos(beta * Z) if beta > 0 else sin(k * X)
            Hx = -beta * sin(k * X) * sin(beta * Z) if beta > 0 else zeros_like(X)
            Hz = k * cos(k * X) * cos(beta * Z) if beta > 0 else k * cos(k * X)
            
            fig_wg_field = make_subplots(rows=2, cols=2, subplot_titles=('Ey', 'Hx', 'Hz', '場線圖'))
            
            fig_wg_field.add_trace(Heatmap(x=x*1000, y=z*1000, z=Ey, colorscale='RdBu', zmid=0), row=1, col=1)
            fig_wg_field.add_trace(Heatmap(x=x*1000, y=z*1000, z=Hx, colorscale='RdBu', zmid=0), row=1, col=2)
            fig_wg_field.add_trace(Heatmap(x=x*1000, y=z*1000, z=Hz, colorscale='RdBu', zmid=0), row=2, col=1)
            
            # 簡化的場線圖
            fig_wg_field.add_trace(Scatter(x=[0, line.a*1000, line.a*1000, 0, 0], 
                                              y=[0, 0, line.b*1000, line.b*1000, 0],
                                              mode='lines', line=dict(color='black', width=2)), row=2, col=2)
            
            fig_wg_field.update_layout(height=700, template='plotly_white')
            plotly_chart(fig_wg_field, use_container_width=True)
            
        else:
            info("場分佈可視化目前支援同軸線和矩形波導。其他傳輸線的場分佈需要使用全波模擬工具如HFSS或COMSOL。")
    
    # Tab 5: 物理公式
    with tab5:
        markdown('<h2 class="section-header">物理公式推導</h2>', unsafe_allow_html=True)
        
        formula_sections = {
            "TEM 基本理論": """
            **TEM (Transverse Electromagnetic) 波假設:**

            - $E_z = 0$, $H_z = 0$ (無縱向場分量)
            - 傳播常數: $\\gamma = \\alpha + j\\beta = j\\omega\\sqrt{\\mu\\epsilon}$
            - 相速度: $v_p = \\frac{1}{\\sqrt{\\mu\\epsilon}} = \\frac{c}{\\sqrt{\\epsilon_r}}$
            - 波長: $\\lambda = \\frac{v_p}{f} = \\frac{c}{f\\sqrt{\\epsilon_r}}$
            - 波阻抗: $\\eta = \\sqrt{\\frac{\\mu}{\\epsilon}} = \\frac{377}{\\sqrt{\\epsilon_r}}$ Ω
            """,
            
            "同軸線 (Coaxial)": """
            **電容:** $C = \\frac{2\\pi\\epsilon}{\\ln(b/a)}$ (F/m)
            
            **電感:** $L = \\frac{\\mu}{2\\pi}\\ln(b/a)$ (H/m)
            
            **特性阻抗:** $Z_0 = \\frac{1}{2\\pi}\\sqrt{\\frac{\\mu}{\\epsilon}}\\ln\\frac{b}{a} = \\frac{60}{\\sqrt{\\epsilon_r}}\\ln\\frac{b}{a}$ (Ω)
            
            **衰減:**
            - 導體損耗: $\\alpha_c = \\frac{R_s}{4\\pi Z_0}(\\frac{1}{a} + \\frac{1}{b})$ (Np/m)
            - 介質損耗: $\\alpha_d = \\frac{\\pi f \\sqrt{\\epsilon_r} \\tan\\delta}{c}$ (Np/m)
            """,
            
            "微帶線 (Microstrip)": """
            **有效介電常數 (Wheeler-Hammerstad):**
            
            $\\epsilon_{eff} = \\frac{\\epsilon_r + 1}{2} + \\frac{\\epsilon_r - 1}{2}(1 + \\frac{12h}{w})^{-0.5}$
            
            **特性阻抗:**
            
            窄帶 $(w/h \\leq 1)$:
            $Z_0 = \\frac{60}{\\sqrt{\\epsilon_{eff}}}\\ln(\\frac{8h}{w} + \\frac{w}{4h})$
            
            寬帶 $(w/h \\geq 1)$:
            $Z_0 = \\frac{120\\pi}{\\sqrt{\\epsilon_{eff}}[w/h + 1.393 + 0.667\\ln(w/h + 1.444)]}$
            
            **色散修正 (Kirschning-Jansen):**
            
            $\\epsilon_{eff}(f) = \\epsilon_r - \\frac{\\epsilon_r - \\epsilon_{eff}(0)}{1 + M}$
            """,
            
            "共面波導 (CPW)": """
            **幾何比:** $k = \\frac{w}{w + 2s}$
            
            **特性阻抗:** $Z_0 = \\frac{30\\pi}{\\sqrt{\\epsilon_{eff}}}\\frac{K(k')}{K(k)}$
            
            其中 $K(k)$ 為第一類完全橢圓積分，$k' = \\sqrt{1-k^2}$
            
            **有效介電常數:**
            
            $\\epsilon_{eff} = 1 + q(\\epsilon_r - 1)$
            
            其中 $q = \\frac{K(k)K(k_1')}{K'(k)K(k_1)}$ 為填充因子
            """,
            
            "串擾理論": """
            **耦合係數:**
            
            電容耦合: $K_c = \\frac{C_m}{C}$
            
            電感耦合: $K_L = \\frac{L_m}{L}$
            
            **近端串擾 (NEXT):**
            
            $NEXT = 20\\log_{10}(\\frac{K_c + K_L}{4})$ (dB)
            
            **遠端串擾 (FEXT):**
            
            $FEXT = 20\\log_{10}(\\frac{(K_c - K_L)lf}{2v_p})$ (dB)
            
            **插入損耗 (IL):**
            
            $IL = 8.686 \\alpha l$ (dB)
            
            **回波損耗 (RL):**
            
            $RL = -20\\log_{10}|\\Gamma| = -20\\log_{10}|\\frac{Z_L - Z_0}{Z_L + Z_0}|$ (dB)
            """
        }
        
        selected_formula = radio("選擇公式類別", list(formula_sections.keys()), horizontal=True)
        #公式=empty()
        #公式.
        markdown(rf'{formula_sections[selected_formula]}', unsafe_allow_html=True)

#if __name__ == "__main__": main()<div class="formula-box"></div>

# 保存文件
#with open('/mnt/kimi/output/tem_transmission_line_simulator.py', 'w', encoding='utf-8') as f:
#    f.write(streamlit_code)
#
#print("✅ Streamlit 模擬器代碼已生成！")
#print("\n文件位置: /mnt/kimi/output/tem_transmission_line_simulator.py")
#print("\n使用方法:")
#print("1. 安裝依賴: pip install streamlit numpy scipy matplotlib plotly")
#print("2. 運行: streamlit run tem_transmission_line_simulator.py")
#print("\n功能特色:")
#print("• 支援 5 種傳輸線類型")
#print("• 6 種介電材料 (Kapton, PTFE, FR-4等)")
#print("• 完整的串擾分析 (NEXT/FEXT/IL/RL)")
#print("• 頻率響應與色散效應")
#print("• 場分佈可視化")
#print("• 物理公式推導說明")
