from streamlit import columns, expander, info, markdown, metric, plotly_chart, set_page_config, sidebar, subheader, table, tabs, warning, radio, text_input, slider, empty#, number_input
from numpy import e, exp, linspace, log, log10, pi, sqrt
from plotly.graph_objects import Figure, Scatter

#import streamlit as st
#import numpy as np
#import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Tuple, Optional
#import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 設定頁面配置
set_page_config(
    page_title="傳輸線模擬器 | Transmission Line Simulator",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義 CSS 樣式
markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .result-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 1rem 0;
    }
    .crosstalk-box {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: black;
        border-radius: 4px 4px 0px 0px;
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

@dataclass
class TransmissionLineParams:
    """傳輸線參數基類"""
    w: float  # 導帶寬度 (mm)
    h: float  # 基板厚度 (mm)
    t: float  # 導帶厚度 (mm)
    er: float  # 相對介電常數
    tan_delta: float  # 損耗角正切
    f: float  # 頻率 (GHz)
    length: float  # 線長 (mm)
    sigma: float = 5.8e7  # 導電率 (S/m), 銅

class MicrostripCalculator:
    """微帶線計算器 - 基於 Hammerstad-Jensen 模型"""

    @staticmethod
    def calculate(w: float, h: float, t: float, er: float, f: float) -> dict:
        """計算微帶線參數"""
        u = w / h

        # 有效介電常數計算
        a = 1 + (1/49) * log((u**4 + (u/52)**2) / (u**4 + 0.432)) +             (1/18.7) * log(1 + (u/18.1)**3)
        b = 0.564 * ((er - 0.9) / (er + 3))**0.053

        er_eff = (er + 1)/2 + (er - 1)/2 * (1 + 10/u)**(-a*b)

        # 特性阻抗計算
        Zf0 = 376.73  # 自由空間阻抗
        f_u = 6 + (2*pi - 6) * exp(-(30.666/u)**0.7528)
        Z0 = (Zf0 / (2*pi*sqrt(er_eff))) * log(f_u/u + sqrt(1 + (2/u)**2))

        # 厚度修正
        if t > 0:
            delta_w = (t/pi) * log(4*e*pi/t / sqrt((t/h)**2 + (1/pi)**2))
            w_eff = w + delta_w
            u_eff = w_eff / h
            # 重新計算
            a_eff = 1 + (1/49) * log((u_eff**4 + (u_eff/52)**2) / (u_eff**4 + 0.432)) +                 (1/18.7) * log(1 + (u_eff/18.1)**3)
            er_eff = (er + 1)/2 + (er - 1)/2 * (1 + 10/u_eff)**(-a_eff*b)
            f_u_eff = 6 + (2*pi - 6) * exp(-(30.666/u_eff)**0.7528)
            Z0 = (Zf0 / (2*pi*sqrt(er_eff))) * log(f_u_eff/u_eff + sqrt(1 + (2/u_eff)**2))

        # 色散修正
        fp = 0.5 * 3e8 / (h * 1e-3 * sqrt(er - 1))  # 單位轉換
        if f > 0:
            P1 = 0.27488 + (0.6315 + 0.525/(1+0.0157*f)**20) * u - 0.065683 * exp(-8.7513*u)
            P2 = 0.33622 * (1 - exp(-0.03442*er))
            P3 = 0.0363 * exp(-4.6*u) * (1 - exp(-(f/38.7)**4.97))
            P4 = 1 + 2.751 * (1 - exp(-(er/15.916)**8))

            Pf = P1 * P2 * ((0.1844 + P3*P4) * f)**1.5763
            er_eff_f = er - (er - er_eff) / (1 + Pf)
        else:
            er_eff_f = er_eff

        # 波長計算
        lambda_g = 300 / (f * sqrt(er_eff_f)) if f > 0 else float('inf')

        return {
            'Z0': Z0,
            'er_eff': er_eff_f,
            'lambda_g': lambda_g,
            'delay': sqrt(er_eff_f) / 3e8 * 1e9,  # ns/m
            'C': 1e12 / (Z0 * 3e8 * sqrt(er_eff_f)),  # pF/m
            'L': Z0**2 * 1e12 / (3e8 * sqrt(er_eff_f))  # nH/m
        }

class CPWCalculator:
    """共面波導計算器"""

    @staticmethod
    def calculate(w: float, s: float, h: float, t: float, er: float, f: float) -> dict:
        """計算CPW參數, w為中心導帶寬度, s為槽寬"""
        k = w / (w + 2*s)
        k_prime = sqrt(1 - k**2)

        # 橢圓積分近似
        if k < 0.707:
            K_Kp = (1/pi) * log(2*(1+sqrt(k_prime))/(1-sqrt(k_prime)))
        else:
            K_Kp = pi / log(2*(1+sqrt(k))/(1-sqrt(k)))

        # 有效介電常數 (準靜態)
        h_eff = h / (w + 2*s)
        if h_eff > 1:
            er_eff = (er + 1)/2
        else:
            q = 1 / (1 + 1.787*h_eff + 0.222*(h_eff)**3)
            er_eff = 1 + q * (er - 1)

        # 特性阻抗
        Z0 = (30 * pi / sqrt(er_eff)) * K_Kp

        # 厚度修正
        if t > 0:
            delta_w = (1.25*t/pi) * (1 + log(4*pi*w/t))
            w_eff = w + delta_w
            k_eff = w_eff / (w_eff + 2*s)
            if k_eff < 0.707:
                K_Kp_eff = (1/pi) * log(2*(1+sqrt(1-k_eff**2))/(1-k_eff))
            else:
                K_Kp_eff = pi / log(2*(1+sqrt(k_eff))/(1-sqrt(k_eff)))
            Z0 = (30 * pi / sqrt(er_eff)) * K_Kp_eff

        return {
            'Z0': Z0,
            'er_eff': er_eff,
            'lambda_g': 300 / (f * sqrt(er_eff)) if f > 0 else float('inf'),
            'delay': sqrt(er_eff) / 3e8 * 1e9,
            'C': 1e12 / (Z0 * 3e8 * sqrt(er_eff)),
            'L': Z0**2 * 1e12 / (3e8 * sqrt(er_eff))
        }

class DifferentialCalculator:
    """差分傳輸線計算器"""

    @staticmethod
    def calculate(w: float, s: float, h: float, t: float, er: float, f: float) -> dict:
        """計算邊緣耦合差分線參數"""
        # 單端參數
        single = MicrostripCalculator.calculate(w, h, t, er, f)

        # 耦合係數近似 (基於s/h比值)
        u = w / h
        g = s / h

        # 奇偶模阻抗計算 (簡化模型)
        # 耦合係數
        k = exp(-2.9 * g**0.35) if g > 0.1 else 0.8

        # 奇模阻抗
        Z0_odd = single['Z0'] * (1 - k)
        # 偶模阻抗  
        Z0_even = single['Z0'] * (1 + k)

        # 差分阻抗
        Z_diff = 2 * Z0_odd
        # 共模阻抗
        Z_comm = Z0_even / 2

        return {
            'Z0_single': single['Z0'],
            'Z0_odd': Z0_odd,
            'Z0_even': Z0_even,
            'Z_diff': Z_diff,
            'Z_comm': Z_comm,
            'er_eff': single['er_eff'],
            'k': k,
            'lambda_g': single['lambda_g'],
            'delay': single['delay'],
            'C_diff': single['C'] * (1 - k),
            'L_diff': single['L'] * (1 + k)
        }

class SingleEndCalculator:
    """單端傳輸線計算器"""

    @staticmethod
    def calculate(w: float, h: float, t: float, er: float, f: float) -> dict:
        """計算單端傳輸線參數"""
        return MicrostripCalculator.calculate(w, h, t, er, f)

class CrosstalkCalculator:
    """串擾計算器 - 計算 NEXT 和 FEXT"""

    @staticmethod
    def calculate_crosstalk(line_type: str, params: dict, aggressor_voltage: float = 1.0) -> dict:
        """
        計算串擾參數
        aggressor_voltage: 入侵線驅動電壓 (V)
        """
        if line_type == "microstrip":
            return CrosstalkCalculator._microstrip_crosstalk(params, aggressor_voltage)
        elif line_type == "cpw":
            return CrosstalkCalculator._cpw_crosstalk(params, aggressor_voltage)
        elif line_type == "differential":
            return CrosstalkCalculator._differential_crosstalk(params, aggressor_voltage)
        else:
            return CrosstalkCalculator._single_end_crosstalk(params, aggressor_voltage)

    @staticmethod
    def _microstrip_crosstalk(params: dict, V_aggressor: float) -> dict:
        """微帶線串擾計算"""
        w = params['w']
        s = params.get('spacing', w)  # 線間距
        h = params['h']
        length = params['length']
        er = params['er']

        # 計算互感和互容 (基於經驗公式)
        # 歸一化間距
        d_norm = s / h

        # 互容係數 (近似)
        Cm_norm = 1 / (1 + (d_norm/0.5)**2.5) * 0.1  # pF/mm
        Cm = Cm_norm * length  # pF

        # 互感係數 (近似)
        Lm_norm = 1 / (1 + (d_norm/0.3)**2) * 0.2  # nH/mm
        Lm = Lm_norm * length  # nH

        # 單端參數
        Z0 = params.get('Z0', 50)
        td = params.get('delay', 6.7) * length * 1e-9  # 延遲時間 (s)

        # 串擾係數
        Kc = Cm / (params.get('C', 100) * 1e-12 * length) if 'C' in params else 0.05
        Kl = Lm / (params.get('L', 400) * 1e-9 * length) if 'L' in params else 0.05

        # NEXT (近端串擾) - 電容和電感耦合疊加
        NEXT_coeff = (Kc + Kl) / 4
        NEXT_voltage = NEXT_coeff * V_aggressor * 1000  # mV
        NEXT_dB = 20 * log10(NEXT_coeff) if NEXT_coeff > 0 else -100

        # FEXT (遠端串擾) - 電容和電感耦合相減
        FEXT_coeff = (Kl - Kc) / 2 * length / 1000  # 長度相關
        FEXT_voltage = FEXT_coeff * V_aggressor * 1000  # mV
        FEXT_dB = 20 * log10(abs(FEXT_coeff)) if FEXT_coeff != 0 else -100

        return {
            'NEXT_voltage': NEXT_voltage,
            'NEXT_coeff': NEXT_coeff,
            'NEXT_dB': NEXT_dB,
            'FEXT_voltage': FEXT_voltage,
            'FEXT_coeff': FEXT_coeff,
            'FEXT_dB': FEXT_dB,
            'Cm': Cm,
            'Lm': Lm,
            'Kc': Kc,
            'Kl': Kl,
            'td': td * 1e9  # ns
        }

    @staticmethod
    def _cpw_crosstalk(params: dict, V_aggressor: float) -> dict:
        """CPW串擾計算"""
        # CPW串擾通常較小，因為屏蔽效應
        w = params['w']
        s = params.get('spacing', 3*w)
        length = params['length']

        # 簡化模型
        Z0 = params.get('Z0', 50)

        # CPW的串擾係數較小
        spacing_norm = s / w
        K_base = 0.02 / (1 + spacing_norm**2)

        NEXT_coeff = K_base
        FEXT_coeff = K_base * 0.5 * length / 1000

        return {
            'NEXT_voltage': NEXT_coeff * V_aggressor * 1000,
            'NEXT_coeff': NEXT_coeff,
            'NEXT_dB': 20 * log10(NEXT_coeff),
            'FEXT_voltage': FEXT_coeff * V_aggressor * 1000,
            'FEXT_coeff': FEXT_coeff,
            'FEXT_dB': 20 * log10(abs(FEXT_coeff)) if FEXT_coeff > 0 else -100,
            'Cm': 0.01 * length,
            'Lm': 0.02 * length,
            'Kc': K_base,
            'Kl': K_base,
            'td': params.get('delay', 6.7) * length * 1e-3
        }

    @staticmethod
    def _differential_crosstalk(params: dict, V_aggressor: float) -> dict:
        """差分對串擾計算"""
        # 差分對的串擾主要來自模式轉換
        k = params.get('k', 0.2)  # 耦合係數
        length = params['length']

        # 差分對串擾係數
        NEXT_coeff = k * 0.1
        FEXT_coeff = k * 0.05 * length / 1000

        return {
            'NEXT_voltage': NEXT_coeff * V_aggressor * 1000,
            'NEXT_coeff': NEXT_coeff,
            'NEXT_dB': 20 * log10(NEXT_coeff),
            'FEXT_voltage': FEXT_coeff * V_aggressor * 1000,
            'FEXT_coeff': FEXT_coeff,
            'FEXT_dB': 20 * log10(abs(FEXT_coeff)) if FEXT_coeff > 0 else -100,
            'Cm': params.get('C_diff', 50) * 0.1,
            'Lm': params.get('L_diff', 400) * 0.1,
            'Kc': k * 0.5,
            'Kl': k * 0.5,
            'td': params.get('delay', 6.7) * length * 1e-3
        }

    @staticmethod
    def _single_end_crosstalk(params: dict, V_aggressor: float) -> dict:
        """單端線串擾計算"""
        # 與微帶線相同
        return CrosstalkCalculator._microstrip_crosstalk(params, V_aggressor)

def create_geometry_visualization(line_type: str, params: dict):
    """創建傳輸線幾何結構可視化"""
    fig = Figure()

    if line_type == "microstrip":
        w, h, t = params['w'], params['h'], params['t']
        # 基板
        fig.add_shape(type="rect", x0=-2*w, y0=-h, x1=2*w, y1=0,
                     fillcolor="lightblue", opacity=0.5, line=dict(width=0))
        # 接地面
        fig.add_shape(type="rect", x0=-2*w, y0=-h-0.1, x1=2*w, y1=-h,
                     fillcolor="gray", line=dict(width=1))
        # 導帶
        fig.add_shape(type="rect", x0=-w/2, y0=0, x1=w/2, y1=t,
                     fillcolor="gold", line=dict(width=2, color="orange"))
        # 標註
        fig.add_annotation(x=0, y=t+0.2, text=f"w={w}mm", showarrow=False)
        fig.add_annotation(x=1.5*w, y=-h/2, text=f"h={h}mm", showarrow=True,
                          arrowhead=2, arrowside="start+end", ax=1.5*w, ay=0)

    elif line_type == "cpw":
        w, s, h = params['w'], params.get('s', 0.5), params['h']
        # 基板
        fig.add_shape(type="rect", x0=-2*(w+s), y0=-h, x1=2*(w+s), y1=0,
                     fillcolor="lightblue", opacity=0.5)
        # 中心導帶
        fig.add_shape(type="rect", x0=-w/2, y0=0, x1=w/2, y1=0.1,
                     fillcolor="gold", line=dict(width=2))
        # 側邊地
        fig.add_shape(type="rect", x0=-2*(w+s), y0=0, x1=-(w/2+s), y1=0.1,
                     fillcolor="gray", line=dict(width=1))
        fig.add_shape(type="rect", x0=(w/2+s), y0=0, x1=2*(w+s), y1=0.1,
                     fillcolor="gray", line=dict(width=1))
        # 標註
        fig.add_annotation(x=0, y=0.3, text=f"w={w}mm", showarrow=False)
        fig.add_annotation(x=0, y=-0.5, text=f"s={s}mm", showarrow=False)

    elif line_type == "differential":
        狀態.code([params]) #[{'w': 1.0, 'h': 1.6, 't': 0.035, 's': 0.5}]
        w, s, h = params['w'], params.get('s', None), params['h']
        # 基板
        fig.add_shape(type="rect", x0=-2*(w+s), y0=-h, x1=2*(w+s), y1=0,
                     fillcolor="lightblue", opacity=0.5)
        # 接地面
        fig.add_shape(type="rect", x0=-2*(w+s), y0=-h-0.1, x1=2*(w+s), y1=-h,
                     fillcolor="gray")
        # 兩條導帶
        fig.add_shape(type="rect", x0=-(w+s/2), y0=0, x1=-s/2, y1=0.1,
                     fillcolor="gold", line=dict(width=2))
        fig.add_shape(type="rect", x0=s/2, y0=0, x1=(w+s/2), y1=0.1,
                     fillcolor="gold", line=dict(width=2))
        # 標註
        fig.add_annotation(x=0, y=0.3, text=f"s={s}mm", showarrow=False)
        fig.add_annotation(x=-(w/2+s/2), y=0.3, text=f"w={w}mm", showarrow=False)

    elif line_type == "single_end":
        w, h = params['w'], params['h']
        # 與微帶線類似
        fig.add_shape(type="rect", x0=-2*w, y0=-h, x1=2*w, y1=0,
                     fillcolor="lightblue", opacity=0.5)
        fig.add_shape(type="rect", x0=-2*w, y0=-h-0.1, x1=2*w, y1=-h,
                     fillcolor="gray")
        fig.add_shape(type="rect", x0=-w/2, y0=0, x1=w/2, y1=0.1,
                     fillcolor="gold", line=dict(width=2))
        fig.add_annotation(x=0, y=0.3, text=f"Single End w={w}mm", showarrow=False)

    fig.update_layout(
        title="傳輸線幾何結構",
        xaxis=dict(range=[-3*max(params['w'], params.get('s', params['w'])), 
                         3*max(params['w'], params.get('s', params['w']))], showgrid=False),
        yaxis=dict(range=[-params['h']-0.5, 1], showgrid=False),
        height=400,
        showlegend=False
    )

    return fig

def plot_impedance_vs_frequency(line_type: str, params: dict):
    """繪製阻抗vs頻率曲線"""
    freqs = linspace(0.1, 20, 100)  # 0.1 to 20 GHz
    impedances = []
    er_effs = []

    w, h, t, er = params['w'], params['h'], params['t'], params['er']

    for f in freqs:
        if line_type == "microstrip":
            result = MicrostripCalculator.calculate(w, h, t, er, f)
        elif line_type == "cpw":
            s = params.get('s', 0.5)
            result = CPWCalculator.calculate(w, s, h, t, er, f)
        elif line_type == "differential":
            s = params.get('spacing', w)
            result = DifferentialCalculator.calculate(w, s, h, t, er, f)
            result['Z0'] = result['Z_diff']
        else:
            result = SingleEndCalculator.calculate(w, h, t, er, f)

        impedances.append(result.get('Z0', result.get('Z_diff', 50)))
        er_effs.append(result['er_eff'])

    fig = make_subplots(rows=2, cols=1, subplot_titles=('特性阻抗 vs 頻率', '有效介電常數 vs 頻率'))

    fig.add_trace(Scatter(x=freqs, y=impedances, mode='lines', name='Z0 (Ω)',
                            line=dict(color='#1f77b4', width=3)), row=1, col=1)
    fig.add_trace(Scatter(x=freqs, y=er_effs, mode='lines', name='εr,eff',
                            line=dict(color='#ff7f0e', width=3)), row=2, col=1)

    fig.update_xaxes(title_text="頻率 (GHz)", row=1, col=1)
    fig.update_xaxes(title_text="頻率 (GHz)", row=2, col=1)
    fig.update_yaxes(title_text="阻抗 (Ω)", row=1, col=1)
    fig.update_yaxes(title_text="有效介電常數", row=2, col=1)

    fig.update_layout(height=600, showlegend=True)

    return fig

def plot_crosstalk_vs_spacing(line_type: str, base_params: dict):
    """繪製串擾vs間距曲線"""
    spacings = linspace(0.1, 5, 50)  # 0.1 to 5 mm
    next_db = []
    fext_db = []

    for s in spacings:
        params = base_params.copy()
        params['spacing'] = s

        # 計算單端參數
        if line_type == "microstrip":
            line_result = MicrostripCalculator.calculate(
                base_params['w'], base_params['h'], base_params['t'], 
                base_params['er'], base_params['f']
            )
        else:
            line_result = SingleEndCalculator.calculate(
                base_params['w'], base_params['h'], base_params['t'],
                base_params['er'], base_params['f']
            )

        params.update(line_result)

        crosstalk = CrosstalkCalculator.calculate_crosstalk(line_type, params, 1.0)
        next_db.append(crosstalk['NEXT_dB'])
        fext_db.append(crosstalk['FEXT_dB'])

    fig = Figure()
    fig.add_trace(Scatter(x=spacings, y=next_db, mode='lines', name='NEXT (dB)',
                            line=dict(color='#d62728', width=3)))
    fig.add_trace(Scatter(x=spacings, y=fext_db, mode='lines', name='FEXT (dB)',
                            line=dict(color='#2ca02c', width=3)))

    fig.update_layout(
        title="串擾 vs 線間距",
        xaxis_title="線間距 s (mm)",
        yaxis_title="串擾 (dB)",
        height=500
    )

    return fig

MENU, 表單=[], ['模擬', '串擾', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
if menu==len(表單): #
  pass
elif menu==MENU[1]: #
  pass
elif menu==MENU[0]: #模擬
    #markdown('<h1 class="main-header">📡 高速傳輸線模擬器</h1>', unsafe_allow_html=True)
    #markdown('<p class="sub-header">Microstrip | CPW | Differential | Single End</p>', unsafe_allow_html=True)

    # 側邊欄參數設定
    with sidebar:
      subheader("⚙️ 參數設定")

      line_type = radio("選擇傳輸線類型", ["microstrip", "cpw", "differential", "single_end"],
          format_func=lambda x: {
              "microstrip": "🔷 微帶線 (Microstrip)",
              "cpw": "🔶 共面波導 (CPW)",
              "differential": "⚡ 差分對 (Differential)",
              "single_end": "➡️ 單端線 (Single End)"
          }[x], horizontal=True) # 傳輸線類型選擇

      markdown("---")

      subheader("📐 幾何參數") # 幾何參數
      w = slider("導帶寬度 w (mm)", 0.1, 5.0, 1.0, 0.1)
      h = slider("基板厚度 h (mm)", 0.1, 3.0, 1.6, 0.1)
      t = slider("導帶厚度 t (mm)", 0.0, 0.1, 0.035, 0.005)

      # 特殊參數
      if line_type in ["cpw", "differential"]:
          s = slider("槽寬/間距 s (mm)", 0.1, 5.0, 0.5, 0.1)
      else:
          s = w

      markdown("---")

      # 材料參數
      subheader("🔬 材料參數")
      er = slider("相對介電常數 εr", 1.0, 15.0, 4.3, 0.1)
      tan_delta = slider("損耗角 tan δ", 0.0001, 0.05, 0.02, 0.0001, format="%.4f")

      markdown("---")

      # 電氣參數
      subheader("⚡ 電氣參數")
      f = slider("頻率 f (GHz)", 0.1, 50.0, 1.0, 0.1)
      length = slider("線長 (mm)", 1.0, 500.0, 100.0, 1.0)

      # 串擾參數
      markdown("---")
      subheader("🔗 串擾分析")
      victim_spacing = slider("受害線間距 (mm)", 0.1, 10.0, 1.0, 0.1)
      aggressor_voltage = slider("入侵線電壓 (V)", 0.1, 5.0, 1.0, 0.1)

    tab1, tab2, tab3, tab4 = tabs([
        "📊 基本參數", 
        "📈 頻率響應", 
        "🔗 串擾分析",
        "🎨 結構可視化"
    ]) # 主頁面標籤

    # 計算傳輸線參數
    if line_type == "microstrip":
        result = MicrostripCalculator.calculate(w, h, t, er, f)
        result['Z0'] = result['Z0']
    elif line_type == "cpw":
        result = CPWCalculator.calculate(w, s, h, t, er, f)
    elif line_type == "differential":
        result = DifferentialCalculator.calculate(w, s, h, t, er, f)
    else:
        result = SingleEndCalculator.calculate(w, h, t, er, f)

    狀態=empty()
    with tab1: # Tab 1: 基本參數
        subheader("傳輸線基本參數")

        col1, col2, col3 = columns(3)
        狀態.code([result])

        with col1:
            metric("特性阻抗 Z₀", f"{result.get('Z0', result.get('Z_diff', 0)):.2f} Ω")
            metric("有效介電常數 εr,eff", f"{result['er_eff']:.3f}")

        with col2:
            metric("傳播延遲", f"{result['delay']:.2f} ns/m")
            metric("導波波長 λg", f"{result['lambda_g']:.2f} mm" if result['lambda_g'] != float('inf') else "∞")

        with col3:
            metric("單位電容 C", f"{result['C_diff']:.2f} pF/m")
            metric("單位電感 L", f"{result['L_diff']:.2f} nH/m")

        # 詳細參數表格
        subheader("詳細參數")

        if line_type == "differential":
            diff_data = {
                "參數": ["單端阻抗 Z₀", "奇模阻抗 Z₀,odd", "偶模阻抗 Z₀,even", 
                       "差分阻抗 Zdiff", "共模阻抗 Zcomm", "耦合係數 k"],
                "數值": [f"{result['Z0_single']:.2f} Ω", f"{result['Z0_odd']:.2f} Ω",
                       f"{result['Z0_even']:.2f} Ω", f"{result['Z_diff']:.2f} Ω",
                       f"{result['Z_comm']:.2f} Ω", f"{result['k']:.4f}"]
            }
            table(diff_data)

        # 物理公式說明
        with expander("📖 物理公式說明"):
            markdown("""
            ### Hammerstad-Jensen 微帶線模型

            **有效介電常數:**
            $$\varepsilon_{r,eff} = \frac{\varepsilon_r + 1}{2} + \frac{\varepsilon_r - 1}{2}(1 + \frac{10}{u})^{-a(u)b(\varepsilon_r)}$$

            **特性阻抗:**
            $$Z_0 = \frac{Z_{F0}}{2\pi\sqrt{\varepsilon_{r,eff}}} \ln\left[\frac{f(u)}{u} + \sqrt{1 + (\frac{2}{u})^2}\right]$$

            其中 $u = w/h$ 為寬高比，$Z_{F0} = 376.73 \Omega$ 為自由空間阻抗。

            ### 串擾基本原理

            **近端串擾 (NEXT):**
            $$V_{NEXT} = \frac{K_C + K_L}{4} V_{aggressor}$$

            **遠端串擾 (FEXT):**
            $$V_{FEXT} = \frac{K_L - K_C}{2} \frac{l}{t_r v} V_{aggressor}$$

            其中 $K_C$ 為電容耦合係數，$K_L$ 為電感耦合係數，$l$ 為耦合長度，$t_r$ 為上升時間。
            """)

    # Tab 2: 頻率響應
    with tab2:
        subheader("頻率響應分析")

        params = {'w': w, 'h': h, 't': t, 'er': er}
        if line_type in ['cpw', 'differential']:
            params['s'] = s

        fig = plot_impedance_vs_frequency(line_type, params)
        plotly_chart(fig, use_container_width=True)

        info("""
        **說明:** 上圖顯示了傳輸線特性阻抗和有效介電常數隨頻率的變化。
        由於色散效應，微帶線的參數會隨頻率升高而變化。
        """)

    # Tab 3: 串擾分析
    with tab3:
        subheader("串擾分析 (Crosstalk Analysis)")

        # 計算串擾
        crosstalk_params = {
            'w': w, 'h': h, 't': t, 'er': er, 'f': f, 'length': length,
            'spacing': victim_spacing, 'Z0': result.get('Z0', 50),
            'C': result['C_diff'], 'L': result['L_diff'], 'delay': result['delay']
        }

        if line_type == 'differential':
            crosstalk_params.update({
                'Z0': result['Z_diff'],
                'k': result['k'],
                'C_diff': result['C_diff'],
                'L_diff': result['L_diff']
            })

        crosstalk_result = CrosstalkCalculator.calculate_crosstalk(
            line_type, crosstalk_params, aggressor_voltage
        )

        col1, col2 = columns(2)

        with col1:
            markdown("<div class='crosstalk-box'>", unsafe_allow_html=True)
            subheader("🔴 近端串擾 (NEXT)")
            metric("NEXT 電壓", f"{crosstalk_result['NEXT_voltage']:.3f} mV")
            metric("NEXT 係數", f"{crosstalk_result['NEXT_coeff']:.4f}")
            metric("NEXT", f"{crosstalk_result['NEXT_dB']:.1f} dB")
            markdown("</div>", unsafe_allow_html=True)

            markdown("""
            **NEXT 特性:**
            - 與耦合長度無關（飽和效應）
            - 電容和電感耦合疊加
            - 持續時間 = 2 × 線延遲
            """)

        with col2:
            markdown("<div class='crosstalk-box'>", unsafe_allow_html=True)
            subheader("🟢 遠端串擾 (FEXT)")
            metric("FEXT 電壓", f"{crosstalk_result['FEXT_voltage']:.3f} mV")
            metric("FEXT 係數", f"{crosstalk_result['FEXT_coeff']:.4f}")
            metric("FEXT", f"{crosstalk_result['FEXT_dB']:.1f} dB")
            markdown("</div>", unsafe_allow_html=True)

            markdown("""
            **FEXT 特性:**
            - 與耦合長度成正比
            - 電容和電感耦合相減
            - 脈衝形式，與信號邊沿相同
            """)

        # 耦合參數
        subheader("耦合參數")
        col3, col4, col5, col6 = columns(4)
        with col3:
            metric("互容 Cm", f"{crosstalk_result['Cm']:.3f} pF")
        with col4:
            metric("互感 Lm", f"{crosstalk_result['Lm']:.3f} nH")
        with col5:
            metric("電容耦合 Kc", f"{crosstalk_result['Kc']:.4f}")
        with col6:
            metric("電感耦合 Kl", f"{crosstalk_result['Kl']:.4f}")

        # 串擾vs間距圖
        subheader("串擾 vs 線間距")
        base_params = {'w': w, 'h': h, 't': t, 'er': er, 'f': f, 'length': length}
        fig_xtalk = plot_crosstalk_vs_spacing(line_type, base_params)
        plotly_chart(fig_xtalk, use_container_width=True)

        warning("""
        **設計建議:**
        - 為了將 NEXT 控制在 -30dB 以下，線間距應至少為 3-5 倍線寬
        - FEXT 可通過減小耦合長度或增加線間距來降低
        - 差分對的緊密耦合可顯著降低對外部串擾的敏感度
        """)

    # Tab 4: 結構可視化
    with tab4:
        subheader("傳輸線結構可視化")

        viz_params = {'w': w, 'h': h, 't': t}
        if line_type in ['cpw', 'differential']:
            viz_params['s'] = s

        fig_viz = create_geometry_visualization(line_type, viz_params)
        plotly_chart(fig_viz, use_container_width=True)

        # 不同傳輸線的比較
        subheader("傳輸線類型比較")

        comparison_data = {
            "傳輸線類型": ["Microstrip", "CPW", "Differential", "Single End"],
            "特點": [
                "簡單結構，易於製造，適合高頻",
                "低輻射，易於並聯元件，阻抗控制精確",
                "共模抑制，抗干擾能力強",
                "最簡單，成本低，但抗干擾差"
            ],
            "典型應用": [
                "PCB 射頻電路",
                "毫米波電路，測試探針",
                "高速數字信號 (USB, PCIe)",
                "一般低速信號"
            ],
            "串擾敏感度": ["中", "低", "低", "高"]
        }

        table(comparison_data)

    # 頁腳
    markdown("---")
    markdown("""
    <div style='text-align: center; color: #666;'>
    <p>基於 Hammerstad-Jensen 微帶線模型 | 串擾計算基於耦合線理論</p>
    <p>⚠️ 本模擬器僅供參考，實際設計請使用專業電磁模擬軟體驗證</p>
    </div>""", unsafe_allow_html=True)

#if __name__ == "__main__": main()
