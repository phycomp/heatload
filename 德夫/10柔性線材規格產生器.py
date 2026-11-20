from streamlit import checkbox, columns, download_button, markdown, metric, pyplot, set_page_config, sidebar, slider, subheader, table, sidebar, radio, text_input, session_state
from matplotlib.pyplot import subplots
from numpy import exp, linspace, log, log10, mean, pi, sqrt
from json import dumps
from fontUtil2 import 配置中文
配置中文()

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Dict, List, Tuple
import json

# ============================================================
# 物理常數與材料參數
# ============================================================

# 真空磁導率
MU_0 = 4 * pi * 1e-7  # H/m

# 真空介電常數
EPS_0 = 8.854e-12  # F/m

# 玻爾茲曼常數
K_B = 1.381e-23  # J/K

# 材料熱導率參數 (W/m·K)
# 基於文獻數據擬合
MATERIAL_THERMAL = {
    "Ag": {
        "type": "power_law",
        "A": 420,      # 300K 參考值
        "alpha": 1.0,  # 高溫區
        "low_temp": {
            "A": 2000,
            "alpha": 2.5  # T < 20K
        }
    },
    "NbTi": {
        "type": "superconducting",
        "Tc": 9.2,     # K
        "normal_k": 10, # 正常態熱導率
        "sc_k": 0.001   # 超導態 (極低)
    },
    "Polyimide_Kapton": {
        "type": "power_law",
        "A": 0.155,
        "alpha": 1.0
    },
    "Cu": {
        "type": "power_law",
        "A": 400,
        "alpha": 1.0,
        "low_temp": {
            "A": 1500,
            "alpha": 2.3
        }
    }
}

# 介電常數與損耗
DIELECTRIC = {
    "Polyimide_Kapton": {
        "εr": 3.4,
        "tan_delta_rt": 0.003,
        "tan_delta_4K": 3e-5,   # 文獻值 ~2.2e-5 @ 20mK
        "tan_delta_20mK": 2.2e-5
    }
}

# ============================================================
# 數據類別定義
# ============================================================

@dataclass
class StriplineGeometry:
    """Stripline 幾何參數"""
    w: float        # 信號線寬度 (mm)
    t: float        # 信號線厚度 (μm)
    h: float        # 介電層厚度 (mm) 上下各一層
    s: float        # 通道間距 pitch (mm)
    L: float        # 傳輸線長度 (mm)
    n_channels: int # 通道數

@dataclass
class ThermalBoundary:
    """熱邊界條件"""
    T_hot: float    # 熱端溫度 (K)
    T_cold: float   # 冷端溫度 (K)
    stage: str      # 溫度階段標識

@dataclass
class MaterialStack:
    """多層膜結構"""
    layers: List[Dict]  # [{"material": str, "thickness": float, "width": float}]

# ============================================================
# 計算核心函數
# ============================================================

def calc_stripline_impedance(geo: StriplineGeometry, εr: float) -> float:
    """
    計算 Stripline 特性阻抗 (Wadell 公式)
    Z0 = (30π / sqrt(εr)) * (b / We)
    其中 b = 2h (總介電厚度), We = 有效寬度
    """
    b = 2 * geo.h  # 總介電厚度 mm
    w = geo.w
    t = geo.t / 1000  # μm -> mm

    # 有效寬度修正 (考慮厚度效應)
    if w / b > 0.35:
        We = w + (t / pi) * (1 + log(2 * b / t))
    else:
        We = w - (b / (2 * pi)) * (1 - 0.5 * exp(-4 * pi * w / b)) * log(1 + 2 * t / b)

    Z0 = (30 * pi / sqrt(εr)) * (b / We)
    return Z0

def calc_crosstalk_stripline(geo: StriplineGeometry, εr: float, f: float) -> Dict[str, float]:
    """
    計算 Stripline 串擾 (近端 NEXT 與遠端 FEXT)

    基於耦合係數模型:
    - 電容耦合係數: kc = Cm / (Cs + Cm)
    - 電感耦合係數: kL = Lm / (Ls + Lm)

    對於對稱 stripline (G-S-G), 串擾主要由互容與互感決定
    """
    w = geo.w  # mm
    s = geo.s  # mm
    h = geo.h  # mm
    L = geo.L / 1000  # mm -> m

    # 介電常數
    eps = εr * EPS_0

    # 單位長度電容 (F/m) - 簡化模型
    # 對於寬度 w, 間距 s 的平行線
    C_self = eps * (w / (2 * h))  # 簡化自電容

    # 互容 (基於平行板近似修正)
    # Cm ~ eps * w / s * exp(-π*s/(2h))  (經驗公式)
    Cm = eps * (w / 1000) / (s / 1000) * exp(-pi * s / (2 * h))

    # 單位長度電感 (H/m)
    L_self = MU_0 * (2 * h / w) * 1e-3  # 簡化

    # 互感
    Lm = MU_0 * (h / (2 * pi * s)) * 1e-3

    # 耦合係數
    kc = Cm / (C_self + Cm) if (C_self + Cm) > 0 else 0
    kL = Lm / (L_self + Lm) if (L_self + Lm) > 0 else 0

    # 綜合耦合係數
    k = 0.5 * (kc + kL)

    # 相位常數
    c = 3e8  # m/s
    beta = 2 * pi * f * sqrt(εr) / c

    # 近端串擾 (NEXT) - dB
    # NEXT ≈ 20*log10(k * beta * L / 2) for weak coupling
    if beta * L < 1:
        next_linear = k * beta * L / 2
        NEXT_db = 20 * log10(max(next_linear, 1e-12))
    else:
        NEXT_db = 20 * log10(k / 2)

    # 遠端串擾 (FEXT) - dB
    # FEXT ∝ k * beta * L (與長度成正比)
    fext_linear = k * beta * L
    FEXT_db = 20 * log10(max(fext_linear, 1e-12))

    return {
        "NEXT_dB": NEXT_db,
        "FEXT_dB": FEXT_db,
        "coupling_k": k,
        "Cm_per_m": Cm,
        "Lm_per_m": Lm,
        "beta": beta
    }

def calc_thermal_conductivity(material: str, T: float) -> float:
    """
    計算材料在溫度 T 下的熱導率 (W/m·K)
    """
    props = MATERIAL_THERMAL.get(material, None)
    if props is None:
        return 1.0

    if props["type"] == "superconducting":
        Tc = props["Tc"]
        if T < Tc * 0.5:  # 超導態 (簡化)
            return props["sc_k"]
        elif T < Tc:
            # 過渡區
            return props["sc_k"] + (props["normal_k"] - props["sc_k"]) * ((T - 0.5*Tc) / (0.5*Tc))
        else:
            return props["normal_k"]

    elif props["type"] == "power_law":
        if "low_temp" in props and T < 20:
            A = props["low_temp"]["A"]
            alpha = props["low_temp"]["alpha"]
        else:
            A = props["A"]
            alpha = props["alpha"]
        return A * (T / 300) ** alpha

    return 1.0

def calc_thermal_load(geo: StriplineGeometry, boundary: ThermalBoundary, 
                      materials: MaterialStack) -> Dict[str, float]:
    """
    計算通過傳輸線的熱負載 (W)

    使用積分形式:
    P = (A/L) * ∫ k(T) dT

    對於多層結構，等效熱導為各層並聯
    """
    T_hot = boundary.T_hot
    T_cold = boundary.T_cold
    L_m = geo.L / 1000  # mm -> m

    # 數值積分計算熱導
    n_points = 100
    T_range = linspace(T_cold, T_hot, n_points)

    total_kA = 0  # 總熱導截面積積

    for layer in materials.layers:
        mat = layer["material"]
        thickness = layer["thickness"] / 1e6  # μm -> m
        width = layer["width"] / 1000  # mm -> m
        area = thickness * width

        # 計算該層的平均熱導率
        k_avg = mean([calc_thermal_conductivity(mat, T) for T in T_range])
        total_kA += k_avg * area

    # 熱流計算 (簡化線性梯度)
    # P = kA * ΔT / L
    delta_T = T_hot - T_cold
    P = total_kA * delta_T / L_m

    # 每通道熱負載
    P_per_channel = P / geo.n_channels

    return {
        "total_power_W": P,
        "per_channel_W": P_per_channel,
        "per_channel_uW": P_per_channel * 1e6,
        "per_channel_nW": P_per_channel * 1e9,
        "kA_total": total_kA,
        "delta_T": delta_T
    }

def calc_insertion_loss(geo: StriplineGeometry, εr: float, tan_delta: float, 
                        f: float, material: str = "Ag") -> float:
    """
    計算插入損耗 (dB)

    包含:
    1. 導體損耗 (skin effect)
    2. 介電損耗
    """
    w = geo.w / 1000  # mm -> m
    t = geo.t / 1e6   # μm -> m
    L = geo.L / 1000  # mm -> m
    h = geo.h / 1000  # mm -> m

    # 導體電導率
    sigma = {"Ag": 6.3e7, "NbTi": 1e6, "Cu": 5.8e7}.get(material, 6.3e7)

    # 趨膚深度
    delta_s = sqrt(2 / (MU_0 * sigma * 2 * pi * f))

    # 導體損耗 (dB/m) - 簡化公式
    # αc = Rs / (Z0 * w) 
    Rs = 1 / (sigma * delta_s)  # 表面電阻
    Z0 = 50  # 假設匹配
    alpha_c = Rs / (Z0 * w)  # Np/m
    alpha_c_db = alpha_c * 8.686  # dB/m

    # 介電損耗 (dB/m)
    # αd = (π * f * sqrt(εr) * tanδ) / c
    c = 3e8
    alpha_d = (pi * f * sqrt(εr) * tan_delta) / c  # Np/m
    alpha_d_db = alpha_d * 8.686  # dB/m

    total_loss_db = (alpha_c_db + alpha_d_db) * L

    return total_loss_db

def calc_via_impact(pitch: float, via_diameter: float, via_density: float) -> Dict:
    """
    計算 Via stitching 對串擾的改善

    via_density: vias per mm
    """
    # Via 間距
    via_spacing = 1.0 / via_density  # mm

    # 屏蔽效能改善 (經驗公式)
    # 更密集的 via 提供更好的接地連續性
    shielding_improvement = 20 * log10(1 + 0.5 * via_density * pitch)

    return {
        "via_spacing_mm": via_spacing,
        "shielding_improvement_dB": shielding_improvement,
        "recommended_density": min(2.0, 1.0 / (pitch / 4))  # 推薦密度
    }

set_page_config( page_title="Cri/oFlex3 柔性傳輸線規格計算器", page_icon="🔬", layout="wide", initial_sidebar_state="expanded")

markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4;
    margin-bottom: 0.5rem;
}
.sub-header {
    font-size: 1.2rem;
    color: #666;
    margin-bottom: 2rem;
}
.metric-card {
    background-color: #f0f2f6;
    border-radius: 10px;
    padding: 20px;
    margin: 10px 0;
}
.highlight {
    background-color: black;
    border-left: 4px solid #1f77b4;
    padding: 15px;
    margin: 15px 0;
}
</style>
""", unsafe_allow_html=True)

from streamlit import empty
MENU, 表單=[], ['計算結果', '串擾', '熱負載', '插入損耗', '規格摘要']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  #srch=text_input('搜尋', '預設值', placeholder='搜尋')
  狀態=empty()
  #狀態.code([])

with sidebar:   # 側邊欄 - 參數輸入
    subheader("⚙️ 設計參數")
    subheader("幾何結構")
    n_channels = radio("通道數", [4, 8, 16, 32], index=1, horizontal=True)
    pitch = slider("通道間距 Pitch (mm)", 0.5, 5.0, 2.0, 0.1)
    length = slider("傳輸線長度 (mm)", 100, 1500, 400, 50)
    sig_width = slider("信號線寬度 (μm)", 50, 500, 150, 10)
    sig_thickness = slider("導體厚度 (μm)", 1, 20, 5, 1)
    dielectric_thickness = slider("單層介電厚度 (μm)", 50, 300, 150, 10)

    subheader("材料選擇")
    conductor_material = radio("導體材料", ["Ag (銀)", "NbTi (超導)", "Cu (銅)"], index=1 , horizontal=True)
    dielectric_material = radio("介電材料", ["Polyimide Kapton"], index=0 , horizontal=True)

    subheader("Via 設計")
    via_enabled = checkbox("啟用 Via Stitching", value=True)
    via_density = slider("Via 密度 (個/mm)", 0.5, 5.0, 2.0, 0.1)
    via_diameter = slider("Via 直徑 (μm)", 50, 300, 150, 10)

    subheader("操作條件")
    frequency = slider("工作頻率 (GHz)", 0.1, 20.0, 6.0, 0.1)
    temp_stage = radio("溫度階段", ["300K → 40K", "40K → 4K", "4K → 1K", "1K → 100mK", "RT → mK (全段)"], index=1, horizontal=True)

    subheader("計算選項")
    calc_crosstalk = checkbox("計算串擾", value=True)
    calc_thermal = checkbox("計算熱負載", value=True)
    calc_loss = checkbox("計算插入損耗", value=True)

if menu==len(表單): #
  pass
elif menu==MENU[4]: #
    results=session_state['results']
    geo=session_state['geo']
    tan_d=session_state['tan_d']
    Z0=session_state['Z0']
    mat_name=session_state['mat_name']
    T_cold=session_state['T_cold']
    T_hot=session_state['T_hot']
    subheader("📋 規格摘要")

    # 設計規格表
    subheader("設計參數")
    spec_data = {
        "參數": ["通道數", "Pitch", "長度", "線寬", "導體厚", "介電厚", "導體材料", "介電材料"],
        "數值": [
            f"{n_channels} ch",
            f"{pitch} mm",
            f"{length} mm",
            f"{sig_width} μm",
            f"{sig_thickness} μm",
            f"{dielectric_thickness} μm",
            conductor_material,
            dielectric_material
        ]
    }
    table(spec_data)

    # 性能指標
    subheader("性能指標")
    perf_data = {}
    if calc_crosstalk and "crosstalk" in results:
        perf_data["串擾 (NEXT)"] = f"{results['crosstalk']['NEXT_dB']:.1f} dB"
    if calc_thermal and "thermal" in results:
        perf_data["熱負載/通道"] = f"{results['thermal']['per_channel_uW']:.2f} μW"
    if calc_loss and "loss" in results:
        perf_data["插入損耗"] = f"{results['loss']:.2f} dB"
    perf_data["特性阻抗"] = f"{Z0:.1f} Ω"

    perf_df = {"指標": list(perf_data.keys()), "數值": list(perf_data.values())}
    table(perf_df)

    # 設計建議
    subheader("💡 設計建議")
    suggestions = []

    if Z0 < 45 or Z0 > 55:
        suggestions.append(f"⚠️ 阻抗 {Z0:.1f}Ω 偏離 50Ω 目標，建議調整線寬至 {150 * 50/Z0:.0f}μm")
    else:
        suggestions.append("✅ 阻抗匹配良好")

    if calc_crosstalk and "crosstalk" in results:
        if results['crosstalk']['NEXT_dB'] > -40:
            suggestions.append(f"⚠️ 串擾偏高，建議增加 pitch 至 {pitch * 1.5:.1f}mm 或增加 via 密度")
        else:
            suggestions.append("✅ 串擾性能優良")

    if calc_thermal and "thermal" in results:
        if mat_name == "NbTi" and T_cold < 9.2:
            suggestions.append("✅ NbTi 超導態運行，熱負載極低")
        elif results['thermal']['per_channel_uW'] > 200:
            suggestions.append("⚠️ 熱負載偏高，建議使用 NbTi 或縮短長度")
        else:
            suggestions.append("✅ 熱負載在合理範圍")

    if via_enabled:
        suggestions.append(f"✅ Via stitching 密度 {via_density}/mm 提供良好屏蔽")

    for s in suggestions:
        markdown(f"<div style='margin: 5px 0;'>{s}</div>", unsafe_allow_html=True)

    # 匯出按鈕
    subheader("📥 匯出結果")
    export_data = {
        "geometry": {
            "n_channels": n_channels,
            "pitch_mm": pitch,
            "length_mm": length,
            "signal_width_um": sig_width,
            "conductor_thickness_um": sig_thickness,
            "dielectric_thickness_um": dielectric_thickness
        },
        "materials": {
            "conductor": conductor_material,
            "dielectric": dielectric_material
        },
        "results": results,
        "impedance_ohm": Z0
    }

    json_str = json.dumps(export_data, indent=2, default=str)
    download_button(
        label="下載 JSON 規格檔",
        data=json_str,
        file_name=f"crioflex3_spec_{length}mm_{n_channels}ch.json",
        mime="application/json"
    )
elif menu==MENU[3]: #
    results=session_state['results']
    geo=session_state['geo']
    εr=session_state['εr']
    tan_d=session_state['tan_d']
    mat_name=session_state['mat_name']
    # 插入損耗
    if calc_loss and "loss" in results:
        subheader("📉 插入損耗")
        cols = columns(2) #插入損耗
        with cols[0]:
            metric(f"@{frequency} GHz 插入損耗", f"{results['loss']:.2f} dB",
                     delta="優良" if results['loss'] < 3 else "偏高",
                     delta_color="normal" if results['loss'] < 3 else "inverse")
        with cols[1]:
            # 計算衰減常數
            alpha_total = results['loss'] / (length / 1000)
            metric("衰減常數", f"{alpha_total:.2f} dB/m")

        # 損耗頻率響應
        markdown("<div class='highlight'>插入損耗頻率響應</div>", unsafe_allow_html=True)
        freqs_loss = linspace(0.1, 20, 200) * 1e9
        losses = []
        for f in freqs_loss:
            l = calc_insertion_loss(geo, εr, tan_d, f, mat_name)
            losses.append(l)

        fig3, ax3 = subplots(figsize=(10, 4))
        ax3.plot(freqs_loss/1e9, losses, 'purple', linewidth=2)
        ax3.axvline(x=frequency, color='red', linestyle='--', alpha=0.7, label=f'設計頻率 {frequency} GHz')
        ax3.set_xlabel("Frequency (GHz)", fontsize=12)
        ax3.set_ylabel("Insertion Loss (dB)", fontsize=12)
        ax3.set_title(f"Insertion Loss vs Frequency ({mat_name}, L={length}mm)", fontsize=14)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        pyplot(fig3)

elif menu==MENU[2]: #
    results=session_state['results']
    geo=session_state['geo']
    materials=session_state['materials']
    # 熱負載卡片
    if calc_thermal and "thermal" in results:
        subheader("🌡️ 熱負載分析")
        th = results["thermal"]
        cols = columns(4)
        with cols[0]:
            metric("總熱負載", f"{th['total_power_W']*1e6:.2f} μW")
        with cols[1]:
            metric("每通道熱負載", f"{th['per_channel_uW']:.2f} μW",
                     delta=f"{th['per_channel_nW']:.1f} nW",
                     delta_color="off")
        with cols[2]:
            metric("溫差 ΔT", f"{th['delta_T']:.1f} K")
        with cols[3]:
            metric("等效 kA", f"{th['kA_total']*1e6:.3f} μW·m/K")

        # 熱負載溫度依賴圖
        markdown("<div class='highlight'>各溫度階段熱負載分佈</div>", unsafe_allow_html=True)
        stages = [(300, 40), (40, 4), (4, 1), (1, 0.1)]
        stage_names = ["300K→40K", "40K→4K", "4K→1K", "1K→100mK"]
        powers = []
        for Th, Tc in stages:
            b = ThermalBoundary(Th, Tc, "")
            p = calc_thermal_load(geo, b, materials)
            powers.append(p["per_channel_uW"])

        fig2, ax2 = subplots(figsize=(10, 4))
        colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
        bars = ax2.bar(stage_names, powers, color=colors, edgecolor='black', linewidth=1.2)
        ax2.set_ylabel("Heat Load per Channel (μW)", fontsize=12)
        ax2.set_title("Thermal Load Distribution Across Cryogenic Stages", fontsize=14)
        ax2.set_yscale('log')
        ax2.grid(True, alpha=0.3, axis='y')

        # 在柱狀圖上標註數值
        for bar, power in zip(bars, powers):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{power:.2f}',
                    ha='center', va='bottom', fontsize=10)

        pyplot(fig2)

        # 與 Cri/oFlex3 官方數據比較
        markdown("""
        <div class="highlight">
        <b>📋 與 Cri/oFlex3 官方規格比較:</b><br>
        • 官方標稱: 4K-40K, L=0.4m: < 125 μW/通道<br>
        • 官方標稱: 10mK-350mK, L=0.2m: ~ 20 nW/通道<br>
        • 本計算 NbTi 超導態: 大幅降低熱負載 (10× 改善)
        </div>
        """, unsafe_allow_html=True)
elif menu==MENU[1]: #
    results=session_state['results']
    geo=session_state['geo']
    εr=session_state['εr']
    # 串擾卡片
    if calc_crosstalk and "crosstalk" in results:
        subheader("📡 串擾分析")
        ct = results["crosstalk"]
        cols = columns(4)
        with cols[0]:
            metric("近端串擾 (NEXT)", f"{ct['NEXT_dB']:.1f} dB",
                     delta="優良" if ct['NEXT_dB'] < -40 else "需改善",
                     delta_color="normal" if ct['NEXT_dB'] < -40 else "inverse")
        with cols[1]:
            metric("遠端串擾 (FEXT)", f"{ct['FEXT_dB']:.1f} dB")
        with cols[2]:
            metric("耦合係數 k", f"{ct['coupling_k']:.4f}")
        with cols[3]:
            if via_enabled and "via" in results:
                metric("Via 屏蔽改善", f"{results['via']['shielding_improvement_dB']:.1f} dB")

        # 串擾頻率響應圖
        markdown("<div class='highlight'>串擾頻率響應 (1-18 GHz)</div>", unsafe_allow_html=True)
        freqs = linspace(1, 18, 100) * 1e9
        next_vals = []
        fext_vals = []
        for f in freqs:
            ct_f = calc_crosstalk_stripline(geo, εr, f)
            if via_enabled and "via" in results:
                ct_f["NEXT_dB"] -= results["via"]["shielding_improvement_dB"]
                ct_f["FEXT_dB"] -= results["via"]["shielding_improvement_dB"]
            next_vals.append(ct_f["NEXT_dB"])
            fext_vals.append(ct_f["FEXT_dB"])

        fig, ax = subplots(figsize=(10, 4))
        ax.plot(freqs/1e9, next_vals, 'b-', linewidth=2, label='NEXT (近端)')
        ax.plot(freqs/1e9, fext_vals, 'r--', linewidth=2, label='FEXT (遠端)')
        ax.axhline(y=-40, color='g', linestyle=':', alpha=0.7, label='-40 dB 目標')
        ax.axhline(y=-60, color='orange', linestyle=':', alpha=0.7, label='-60 dB 目標')
        ax.set_xlabel("Frequency (GHz)", fontsize=12)
        ax.set_ylabel("Crosstalk (dB)", fontsize=12)
        ax.set_title("Cri/oFlex3 Stripline Crosstalk vs Frequency", fontsize=14)
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(-100, -20)
        pyplot(fig)

elif menu==MENU[0]: #規格
    subheader("📊 計算結果")

    if 'geo' not in session_state: # 建立幾何結構
      geo=session_state['geo']=StriplineGeometry(
        w=sig_width / 1000,  # μm -> mm
        t=sig_thickness,
        h=dielectric_thickness / 1000,  # μm -> mm
        s=pitch,
        L=length,
        n_channels=n_channels
    )
    else: geo=session_state['geo']
    dielectric = DIELECTRIC["Polyimide_Kapton"] # 介電參數
    εr=session_state['εr']=dielectric["εr"]

    # 溫度邊界
    temp_map = {
        "300K → 40K": (300, 40),
        "40K → 4K": (40, 4),
        "4K → 1K": (4, 1),
        "1K → 100mK": (1, 0.1),
        "RT → mK (全段)": (300, 0.01)
    }
    T_hot, T_cold = temp_map[temp_stage]
    session_state['T_cold']=T_cold
    session_state['T_hot']=T_hot
    boundary = ThermalBoundary(T_hot=T_hot, T_cold=T_cold, stage=temp_stage)

    # 材料堆疊 (Cri/oFlex3 典型結構)
    mat_name = session_state['mat_name']=conductor_material.split(" ")[0]
    materials = session_state['materials']=MaterialStack(layers=[
        {"material": mat_name, "thickness": sig_thickness, "width": sig_width},
        {"material": "Polyimide_Kapton", "thickness": dielectric_thickness * 2, "width": pitch * 0.8},
        {"material": mat_name, "thickness": sig_thickness, "width": pitch * 0.8}  # 接地層
    ])

    # 計算結果容器
    results = {}

    # 1. 特性阻抗
    Z0 = session_state['Z0']=calc_stripline_impedance(geo, εr)

    # 2. 串擾計算
    if calc_crosstalk:
        crosstalk = calc_crosstalk_stripline(geo, εr, frequency * 1e9)
        results["crosstalk"] = crosstalk

        # Via 影響
        if via_enabled:
            via_info = calc_via_impact(pitch, via_diameter, via_density)
            results["via"] = via_info
            crosstalk["NEXT_dB"] -= via_info["shielding_improvement_dB"]
            crosstalk["FEXT_dB"] -= via_info["shielding_improvement_dB"]

    # 3. 熱負載計算
    if calc_thermal:
        thermal = calc_thermal_load(geo, boundary, materials)
        results["thermal"] = thermal

    # 4. 插入損耗
    if calc_loss:
        # 根據溫度選擇損耗角
        if T_cold < 1:
            tan_d = dielectric["tan_delta_20mK"]
        elif T_cold < 10:
            tan_d = dielectric["tan_delta_4K"]
        else:
            tan_d = dielectric["tan_delta_rt"]

        loss = calc_insertion_loss(geo, εr, tan_d, frequency * 1e9, mat_name)
        results["loss"] = loss
    if 'results' not in session_state:
      session_state['results']=results
    session_state['tan_d']=tan_d
    # 顯示結果 特性阻抗, 通道密度, 傳輸延遲
    # 阻抗卡片
    subheader("📐 傳輸線特性")
    cols = columns(3)
    with cols[0]:
        metric("特性阻抗", f"{Z0:.1f} Ω", 
                 delta=f"{'✓ 匹配' if 45 < Z0 < 55 else '✗ 不匹配'}",
                 delta_color="normal" if 45 < Z0 < 55 else "inverse")
    with cols[1]:
        metric("通道密度", f"{n_channels} ch", 
                 delta=f"{n_channels/pitch:.1f} ch/mm")
    with cols[2]:
        effective_er = εr
        v_phase = 3e8 / sqrt(effective_er)
        delay = (length / 1000) / v_phase * 1e9
        metric("傳輸延遲", f"{delay:.2f} ns")

with sidebar:
    markdown('<div class="main-header">🔬 Cri/oFlex3 柔性傳輸線規格計算器</div>', unsafe_allow_html=True)
    markdown('<div class="sub-header">NbTi/Ag + Polyimide 多層膜 Stripline 串擾與熱負載分析</div>', unsafe_allow_html=True)
    """
Cri/oFlex3 柔性傳輸線規格計算器
=====================================
針對 NbTi/Ag + Polyimide 多層膜柔性 stripline 的串擾與熱負載計算工具

技術參數基準 (Delft Circuits Cri/oFlex3):
- 通道數: 8 channels/flex
- 厚度: 0.3 mm
- Pitch: 2 mm
- 材料: Polyimide + Ag/NbTi
- 線型: Stripline (G-S-G)
- 阻抗: 50 Ω
- 頻率: DC ~ 18 GHz
- 彎曲半徑: 5 mm
- 長度: 200 ~ 1000 mm
"""



#if __name__ == "__main__": main()
