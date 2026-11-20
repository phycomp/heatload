from streamlit import checkbox, columns, download_button, markdown, metric, pyplot, radio, set_page_config, sidebar, slider, subheader, table, tabs, session_state, json as stJSON, info, plotly_chart, warning
from matplotlib.pyplot import Circle, Polygon, Rectangle, subplots, tight_layout
from pandas import DataFrame, json_normalize
from numpy import exp, linspace, log, log10, mean, pi, sqrt, array
from json import dumps as jsnDumps
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Dict, List, Tuple
from fontUtil2 import 配置中文
配置中文()
import io
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from datetime import datetime

# ============================================================
# 物理常數與材料參數
# ============================================================

MU_0 = 4 * pi * 1e-7  # H/m 真空磁導率
EPS_0 = 8.854e-12  # F/m 真空介電常數
K_B = 1.381e-23  # J/K 玻爾茲曼常數
C_LIGHT = 3e8  # m/s 光速

# 材料熱導率參數 (W/m·K)
MATERIAL_THERMAL = {
    "Ag": {
        "type": "wiedemann_franz",
        "sigma": 6.3e7,
        "L0": 2.45e-8
    },
    "NbTi": {
        "type": "superconducting",
        "Tc": 9.2,
        "normal_k": 10,
        "sc_k": 0.001
    },
    "Polyimide": {
        "type": "power_law",
        "A": 0.155,
        "alpha": 1.0
    },
    "Cu": {
        "type": "wiedemann_franz",
        "sigma": 5.8e7,
        "L0": 2.45e-8
    }
}

# 介電常數與損耗
DIELECTRIC = {
    "Polyimide": {
        "εr": 3.4,
        "tan_delta_rt": 0.003,
        "tan_delta_4K": 3e-5,
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

def draw_all_views(geo: StriplineGeometry, pitch: float, length: float, 
                   via_enabled: bool, via_diameter: float, via_density: float, n_channels: int):
    """
    組合三視圖為單一圖表 - 直接在各子圖中繪製，避免複製問題
    """
    fig = plt.figure(figsize=(16, 12))
    
    w = geo.w
    h = geo.h
    t = geo.t / 1000
    s = pitch
    L = length
    n_draw = min(n_channels, 6)
    total_width = s * (n_draw + 0.5)
    margin = s * 0.3
    
    colors = {
        'polyimide': '#F5E6C8',
        'polyimide_edge': '#D4A574',
        'conductor': '#DAA520',
        'conductor_edge': '#8B6914',
        'gnd': '#C9A227',
        'via': '#A0522D',
        'text': '#2C3E50',
        'dimension': '#E74C3C',
        'arrow': '#2980B9',
        'signal_edge': '#8B6914'
    }
    
    # ===== 前視圖 (左上) =====
    ax1 = fig.add_subplot(2, 2, 1)
    
    y_bot_gnd = 0
    y_bot_die = t
    y_signal = t + h
    y_top_die = t + h + t
    y_top_gnd = t + h + t + h
    total_height = y_top_gnd + t
    
    ax1.set_xlim(-margin, total_width + margin)
    ax1.set_ylim(-margin * 0.5, total_height + margin * 1.5)
    ax1.set_aspect('equal')
    ax1.axis('off')
    
    # 下接地層
    gnd_bottom = Rectangle((0, y_bot_gnd), total_width, t,
                          facecolor=colors['gnd'], edgecolor=colors['conductor_edge'], linewidth=2)
    ax1.add_patch(gnd_bottom)
    ax1.text(total_width/2, y_bot_gnd + t/2, 'Bottom GND',
             ha='center', va='center', fontsize=9, color='white', fontweight='bold')
    
    # 下介電層
    die_bottom = Rectangle((0, y_bot_die), total_width, h,
                          facecolor=colors['polyimide'], edgecolor=colors['polyimide_edge'], 
                          linewidth=2, alpha=0.85)
    ax1.add_patch(die_bottom)
    
    # 信號層
    for i in range(n_draw):
        x_center = s * (i + 0.5)
        sig = Rectangle((x_center - w/2, y_signal - t/2), w, t,
                        facecolor=colors['conductor'], edgecolor=colors['conductor_edge'], linewidth=2)
        ax1.add_patch(sig)
        ax1.text(x_center, y_signal, f'S{i+1}', ha='center', va='center',
                 fontsize=8, color='white', fontweight='bold')
        
        if i < n_draw - 1:
            gnd_x = x_center + s/2
            gnd_w = w * 0.3
            gnd_sep = Rectangle((gnd_x - gnd_w/2, y_signal - t/2), gnd_w, t,
                               facecolor=colors['gnd'], edgecolor=colors['conductor_edge'], linewidth=1.5)
            ax1.add_patch(gnd_sep)
    
    # 上介電層
    die_top = Rectangle((0, y_top_die), total_width, h,
                        facecolor=colors['polyimide'], edgecolor=colors['polyimide_edge'],
                        linewidth=2, alpha=0.85)
    ax1.add_patch(die_top)
    
    # 上接地層
    gnd_top = Rectangle((0, y_top_gnd), total_width, t,
                        facecolor=colors['gnd'], edgecolor=colors['conductor_edge'], linewidth=2)
    ax1.add_patch(gnd_top)
    ax1.text(total_width/2, y_top_gnd + t/2, 'Top GND',
             ha='center', va='center', fontsize=9, color='white', fontweight='bold')
    
    # Via
    if via_enabled:
        via_spacing = 1.0 / via_density
        n_vias = int(total_width / via_spacing) + 1
        via_r = via_diameter / 2000
        for i in range(n_vias):
            x_via = i * via_spacing
            if x_via > total_width:
                break
            ax1.plot([x_via, x_via], [y_bot_gnd + t/2, y_top_gnd + t/2],
                     color=colors['via'], linewidth=2, alpha=0.7, linestyle='-')
            for y in [y_bot_gnd + t/2, y_top_gnd + t/2]:
                v = Circle((x_via, y), via_r, facecolor=colors['via'], edgecolor='black', linewidth=1)
                ax1.add_patch(v)
    
    # 尺寸標註
    ax1.annotate('', xy=(-margin*0.3, 0), xytext=(-margin*0.3, total_height),
                 arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax1.text(-margin*0.5, total_height/2, f'Total\n{total_height*1000:.0f}μm',
             ha='right', va='center', fontsize=8, color=colors['dimension'])
    
    ax1.annotate('', xy=(s*0.5 - w/2, -margin*0.2), xytext=(s*0.5 + w/2, -margin*0.2),
                 arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax1.text(s*0.5, -margin*0.35, f'w={w*1000:.0f}μm',
             ha='center', va='top', fontsize=8, color=colors['dimension'])
    
    ax1.annotate('', xy=(s*0.5, -margin*0.6), xytext=(s*1.5, -margin*0.6),
                 arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=1.5))
    ax1.text(s, -margin*0.8, f'pitch={s:.1f}mm',
             ha='center', va='top', fontsize=9, color=colors['arrow'], fontweight='bold')
    
    ax1.set_title('前視圖 (Cross-Section)', fontsize=12, fontweight='bold')
    
    # ===== 側視圖 (右上) =====
    ax2 = fig.add_subplot(2, 2, 2)
    
    margin2 = L * 0.02
    
    # 下接地層
    gnd_bottom2 = Rectangle((0, y_bot_gnd), L, t,
                           facecolor=colors['gnd'], edgecolor=colors['conductor_edge'], linewidth=1.5)
    ax2.add_patch(gnd_bottom2)
    
    # 下介電層
    die_bottom2 = Rectangle((0, y_bot_die), L, h,
                           facecolor=colors['polyimide'], edgecolor=colors['polyimide_edge'],
                           linewidth=1.5, alpha=0.85)
    ax2.add_patch(die_bottom2)
    
    # 信號層
    signal2 = Rectangle((0, y_signal - t/2), L, t,
                       facecolor=colors['conductor'], edgecolor=colors['conductor_edge'], linewidth=1.5)
    ax2.add_patch(signal2)
    ax2.text(L/2, y_signal, 'Signal', ha='center', va='center',
             fontsize=9, color='white', fontweight='bold')
    
    # 上介電層
    die_top2 = Rectangle((0, y_top_die), L, h,
                        facecolor=colors['polyimide'], edgecolor=colors['polyimide_edge'],
                        linewidth=1.5, alpha=0.85)
    ax2.add_patch(die_top2)
    
    # 上接地層
    gnd_top2 = Rectangle((0, y_top_gnd), L, t,
                        facecolor=colors['gnd'], edgecolor=colors['conductor_edge'], linewidth=1.5)
    ax2.add_patch(gnd_top2)
    
    # 標註
    label_x = L + margin2 * 5
    ax2.text(label_x, y_bot_gnd + t/2, 'GND', ha='left', va='center', fontsize=8, color=colors['text'])
    ax2.text(label_x, y_bot_die + h/2, 'Polyimide', ha='left', va='center', fontsize=8, color=colors['text'])
    ax2.text(label_x, y_signal, 'Signal', ha='left', va='center', fontsize=8, color=colors['text'])
    ax2.text(label_x, y_top_die + h/2, 'Polyimide', ha='left', va='center', fontsize=8, color=colors['text'])
    ax2.text(label_x, y_top_gnd + t/2, 'GND', ha='left', va='center', fontsize=8, color=colors['text'])
    
    # 長度標註
    ax2.annotate('', xy=(0, -margin2*2), xytext=(L, -margin2*2),
                 arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=1.5))
    ax2.text(L/2, -margin2*3, f'L = {L:.0f} mm', ha='center', va='top',
             fontsize=9, color=colors['arrow'], fontweight='bold')
    
    ax2.set_xlim(-margin2*5, L + margin2*8)
    ax2.set_ylim(-margin2*4, total_height + margin2*2)
    ax2.set_aspect('equal')
    ax2.axis('off')
    ax2.set_title('側視圖 (Side View)', fontsize=12, fontweight='bold')
    
    # ===== 上視圖 (左下) =====
    ax3 = fig.add_subplot(2, 2, 3)
    
    n_draw_top = min(n_channels, 8)
    total_width_top = s * n_draw_top + w * 2
    margin3 = s * 0.3
    
    for i in range(n_draw_top):
        x_center = s * (i + 0.5) + w * 0.5
        
        signal3 = Rectangle((x_center - w/2, 0), w, L,
                           facecolor=colors['conductor'], edgecolor=colors['signal_edge'], linewidth=1.5)
        ax3.add_patch(signal3)
        ax3.text(x_center, L/2, f'S{i+1}', ha='center', va='center',
                 fontsize=9, color='white', fontweight='bold', rotation=90)
        
        if i < n_draw_top - 1:
            gnd_x = x_center + s/2 - w*0.15
            gnd3 = Rectangle((gnd_x, 0), w*0.3, L,
                            facecolor=colors['gnd'], edgecolor=colors['signal_edge'], linewidth=1.5)
            ax3.add_patch(gnd3)
            ax3.text(gnd_x + w*0.15, L/2, 'G', ha='center', va='center',
                     fontsize=7, color='white', fontweight='bold', rotation=90)
    
    # 標註
    for i in range(n_draw_top):
        x_center = s * (i + 0.5) + w * 0.5
        ax3.text(x_center, -margin3*0.5, f'Ch{i+1}', ha='center', va='top',
                 fontsize=8, color=colors['text'])
    
    ax3.annotate('', xy=(0, -margin3*1.5), xytext=(total_width_top, -margin3*1.5),
                 arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=1.5))
    ax3.text(total_width_top/2, -margin3*2, f'總寬度 = {total_width_top:.1f} mm',
             ha='center', va='top', fontsize=9, color=colors['arrow'], fontweight='bold')
    
    ax3.annotate('', xy=(0, -margin3*3), xytext=(s + w, -margin3*3),
                 arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax3.text((s + w)/2, -margin3*3.5, f'pitch={s:.1f}mm',
             ha='center', va='top', fontsize=8, color=colors['dimension'])
    
    ax3.annotate('', xy=(total_width_top + margin3, 0), xytext=(total_width_top + margin3, L),
                 arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=1.5))
    ax3.text(total_width_top + margin3*2, L/2, f'L={L:.0f}mm',
             ha='left', va='center', fontsize=9, color=colors['arrow'], fontweight='bold')
    
    ax3.set_xlim(-margin3, total_width_top + margin3*4)
    ax3.set_ylim(-margin3*6, L + margin3)
    ax3.set_aspect('equal')
    ax3.axis('off')
    ax3.set_title('上視圖 (Top View)', fontsize=12, fontweight='bold')
    
    # ===== 圖例與說明 (右下) =====
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.axis('off')
    
    info_text = f"""
    📐 三視圖尺寸說明

    幾何參數：
    • 通道數: {n_channels}
    • Pitch: {pitch:.1f} mm
    • 長度 L: {length:.0f} mm
    • 信號線寬 w: {geo.w*1000:.0f} μm
    • 導體厚度 t: {geo.t:.0f} μm
    • 介電厚度 h: {geo.h*1000:.0f} μm

    結構層次 (由下到上)：
    1. Bottom GND (接地層)
    2. Polyimide 介電層 (εr=3.4)
    3. Signal + GND 分隔 (G-S-G)
    4. Polyimide 介電層 (εr=3.4)
    5. Top GND (接地層)

    {"✅ Via Stitching: 已啟用" if via_enabled else "❌ Via Stitching: 未啟用"}
    {"   Via 密度: " + str(via_density) + "/mm, 直徑: " + str(via_diameter) + "μm" if via_enabled else ""}

    材料：
    • 導體: {geo.n_channels}通道 Ag/NbTi
    • 介電: Polyimide (εr=3.4)
    """
    ax4.text(0.05, 0.95, info_text, fontsize=10, va='top', linespacing=1.6,
             bbox=dict(boxstyle='round', facecolor='#F0F0F0', alpha=0.9))
    
    plt.suptitle(f'Cri/oFlex3 傳輸線三視圖 (G-S-G Stripline, {n_channels}通道)',
                 fontsize=16, fontweight='bold', y=0.98)
    tight_layout()
    return fig

# ============================================================
# 修正繪圖函數 - 避免文字重疊
# ============================================================

def draw_side_view(geo: StriplineGeometry, length: float):
    """繪製側視圖 - 獨立圖形，修正文字重疊"""
    fig, ax = subplots(figsize=(14, 5))
    
    t = geo.t / 1000
    h = geo.h
    L = length
    
    y_bot_gnd, y_bot_die = 0, t
    y_signal = t + h
    y_top_die = t + h + t
    y_top_gnd = t + h + t + h
    total_height = y_top_gnd + t
    
    colors = {
        'gnd': '#C9A227', 'polyimide': '#F5E6C8',
        'polyimide_edge': '#D4A574', 'conductor': '#DAA520',
        'conductor_edge': '#8B6914', 'dimension': '#E74C3C',
        'arrow': '#2980B9'
    }
    
    margin = L * 0.02
    
    # 各層
    gnd_bottom = Rectangle((0, y_bot_gnd), L, t,
                          facecolor=colors['gnd'], edgecolor=colors['conductor_edge'], linewidth=1.5)
    ax.add_patch(gnd_bottom)
    die_bottom = Rectangle((0, y_bot_die), L, h,
                          facecolor=colors['polyimide'], edgecolor=colors['polyimide_edge'],
                          linewidth=1.5, alpha=0.85)
    ax.add_patch(die_bottom)
    signal = Rectangle((0, y_signal - t/2), L, t,
                      facecolor=colors['conductor'], edgecolor=colors['conductor_edge'], linewidth=1.5)
    ax.add_patch(signal)
    ax.text(L/2, y_signal, 'Signal Layer', ha='center', va='center',
            fontsize=9, color='white', fontweight='bold')
    die_top = Rectangle((0, y_top_die), L, h,
                       facecolor=colors['polyimide'], edgecolor=colors['polyimide_edge'],
                       linewidth=1.5, alpha=0.85)
    ax.add_patch(die_top)
    gnd_top = Rectangle((0, y_top_gnd), L, t,
                       facecolor=colors['gnd'], edgecolor=colors['conductor_edge'], linewidth=1.5)
    ax.add_patch(gnd_top)
    
    # 標註 - 調整位置避免重疊
    label_x = L + margin * 4
    labels = ['GND', 'Polyimide', 'Signal', 'Polyimide', 'GND']
    y_positions = [y_bot_gnd + t/2, y_bot_die + h/2, y_signal, y_top_die + h/2, y_top_gnd + t/2]
    for lbl, yp in zip(labels, y_positions):
        ax.text(label_x, yp, lbl, ha='left', va='center', fontsize=9, color='#2C3E50')
    
    # 尺寸標註
    ax.annotate('', xy=(0, -margin*2), xytext=(L, -margin*2),
                arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=2))
    ax.text(L/2, -margin*3, f'L = {L:.0f} mm', ha='center', va='top',
            fontsize=11, color=colors['arrow'], fontweight='bold')
    ax.annotate('', xy=(-margin*2, 0), xytext=(-margin*2, total_height),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=2))
    ax.text(-margin*3, total_height/2, f'Total\n{total_height*1000:.0f}μm',
            ha='right', va='center', fontsize=9, color=colors['dimension'])
    
    ax.set_xlim(-margin*5, L + margin*7)
    ax.set_ylim(-margin*4, total_height + margin*2)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f'側視圖 (Side View) - 長度 L = {L:.0f} mm', fontsize=14, fontweight='bold', pad=20)
    tight_layout()
    return fig


def draw_top_view(geo: StriplineGeometry, pitch: float, length: float, n_channels: int):
    """繪製上視圖 - 獨立圖形，修正文字重疊"""
    fig, ax = subplots(figsize=(14, 8))
    
    w = geo.w
    s = pitch
    L = length
    n_draw = min(n_channels, 8)
    total_width = s * n_draw + w * 2
    
    colors = {
        'signal': '#DAA520', 'signal_edge': '#8B6914',
        'gnd': '#C9A227', 'gnd_edge': '#8B6914',
        'dimension': '#E74C3C', 'arrow': '#2980B9'
    }
    
    margin = s * 0.3
    
    for i in range(n_draw):
        x_center = s * (i + 0.5) + w * 0.5
        signal = Rectangle((x_center - w/2, 0), w, L,
                          facecolor=colors['signal'], edgecolor=colors['signal_edge'], linewidth=1.5)
        ax.add_patch(signal)
        ax.text(x_center, L/2, f'S{i+1}', ha='center', va='center',
                fontsize=10, color='white', fontweight='bold', rotation=90)
        if i < n_draw - 1:
            gnd_x = x_center + s/2 - w*0.15
            gnd = Rectangle((gnd_x, 0), w*0.3, L,
                           facecolor=colors['gnd'], edgecolor=colors['gnd_edge'], linewidth=1.5)
            ax.add_patch(gnd)
            ax.text(gnd_x + w*0.15, L/2, 'GND', ha='center', va='center',
                    fontsize=8, color='white', fontweight='bold', rotation=90)
    
    # 通道標註
    for i in range(n_draw):
        x_center = s * (i + 0.5) + w * 0.5
        ax.text(x_center, -margin*0.4, f'Ch{i+1}', ha='center', va='top', fontsize=8, color='#2C3E50')
    
    # 總寬度標註 - 放在圖形下方
    y_label = -margin * 1.8
    ax.annotate('', xy=(0, y_label), xytext=(total_width, y_label),
                arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=2))
    ax.text(total_width/2, y_label - margin*0.5, f'總寬度 = {total_width:.1f} mm',
            ha='center', va='top', fontsize=9, color=colors['arrow'], fontweight='bold')
    
    # Pitch 標註 - 放在更下方
    y_pitch = y_label - margin * 1.8
    ax.annotate('', xy=(0, y_pitch), xytext=(s + w, y_pitch),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text((s + w)/2, y_pitch - margin*0.4, f'pitch = {s:.1f}mm',
            ha='center', va='top', fontsize=9, color=colors['dimension'])
    
    # 長度標註 (右側)
    ax.annotate('', xy=(total_width + margin, 0), xytext=(total_width + margin, L),
                arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=2))
    ax.text(total_width + margin*2.5, L/2, f'L = {L:.0f}mm',
            ha='left', va='center', fontsize=10, color=colors['arrow'], fontweight='bold')
    
    ax.set_xlim(-margin, total_width + margin*4)
    ax.set_ylim(-margin*6, L + margin)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f'上視圖 (Top View) - {n_channels}通道佈線', fontsize=14, fontweight='bold', pad=20)
    tight_layout()
    return fig


# ============================================================
# 修正 Excel 匯出函數 - 各圖獨立放入，三視圖為欄位說明
# ============================================================

def export_to_excel(geo: StriplineGeometry, er: float, tan_d: float, Z0: float,
                    results: Dict, crosstalk: Dict, thermal: Dict, loss: Dict,
                    via_info: Dict,
                    conductor_material: str, dielectric_material: str,
                    temp_stage: str, frequency: float,
                    pitch: float, length: float, sig_width: float,
                    sig_thickness: float, dielectric_thickness: float,
                    n_channels: int, via_enabled: bool, via_density: float,
                    via_diameter: float, T_hot: float, T_cold: float) -> bytes:
    """
    匯出完整規格至 Excel：
    - 各視圖獨立放入不同工作表
    - 三視圖尺寸說明為欄位文字
    """
    from openpyxl.drawing.image import Image
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    import io
    
    wb = Workbook()
    
    # === Sheet 1: 設計規格 ===
    ws1 = wb.active
    ws1.title = "設計規格"
    
    ws1.merge_cells('A1:D1')
    ws1['A1'] = 'Cri/oFlex3 柔性傳輸線規格書'
    ws1['A1'].font = Font(size=16, bold=True)
    ws1['A1'].alignment = Alignment(horizontal='center')
    ws1['A3'] = f'生成時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    ws1['A3'].font = Font(size=10, italic=True)
    
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True)
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    
    params = [
        ('參數', '數值', '單位', '說明'),
        ('通道數', n_channels, 'ch', ''),
        ('通道間距 (Pitch)', pitch, 'mm', '中心到中心距離'),
        ('傳輸線長度', length, 'mm', ''),
        ('信號線寬度', sig_width, 'μm', '影響特性阻抗'),
        ('導體厚度', sig_thickness, 'μm', ''),
        ('單層介電厚度', dielectric_thickness, 'μm', ''),
        ('導體材料', conductor_material, '', 'Ag/NbTi/Cu'),
        ('介電材料', dielectric_material, '', 'Polyimide'),
        ('介電常數 εr', er, '', 'Polyimide'),
        ('損耗角 tan δ', f'{tan_d:.2e}', '', f'@{T_cold:.1f}K'),
        ('工作頻率', frequency, 'GHz', ''),
        ('溫度階段', temp_stage, '', f'{T_hot}K → {T_cold}K'),
        ('Via Stitching', '啟用' if via_enabled else '未啟用', '', ''),
        ('Via 密度', via_density if via_enabled else '-', '/mm', ''),
        ('Via 直徑', via_diameter if via_enabled else '-', 'μm', ''),
    ]
    
    for row_idx, row_data in enumerate(params, start=5):
        for col_idx, val in enumerate(row_data, start=1):
            cell = ws1.cell(row=row_idx, column=col_idx, value=val)
            cell.border = thin_border
            if row_idx == 5:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')
            else:
                if col_idx == 2:
                    cell.alignment = Alignment(horizontal='right')
                elif col_idx == 3:
                    cell.alignment = Alignment(horizontal='center')
    
    ws1.column_dimensions['A'].width = 20
    ws1.column_dimensions['B'].width = 18
    ws1.column_dimensions['C'].width = 12
    ws1.column_dimensions['D'].width = 30
    
    # === Sheet 2: 性能指標 ===
    ws2 = wb.create_sheet("性能指標")
    ws2['A1'] = '性能指標'
    ws2['A1'].font = Font(size=14, bold=True)
    
    perf_data = [
        ('指標', '數值', '單位', '狀態'),
        ('特性阻抗', f'{Z0:.1f}', 'Ω', '✅ 匹配' if 45 < Z0 < 55 else '⚠️ 不匹配'),
    ]
    
    if crosstalk:
        freq_label = f"@{crosstalk.get('頻率_GHz', frequency):.1f}GHz"
        perf_data.append(('近端串擾 (NEXT)', f"{crosstalk.get('近端串擾', 0):.1f}", f'dB/m {freq_label}',
                         '✅ 優良' if crosstalk.get('近端串擾', 0) < -40 else '⚠️ 需改善'))
        perf_data.append(('遠端串擾 (FEXT)', f"{crosstalk.get('遠端串擾', 0):.1f}", f'dB/m {freq_label}', ''))
        perf_data.append(('耦合係數 k', f"{crosstalk.get('耦合強度', 0):.4f}", '', ''))
    
    if thermal:
        perf_data.append(('總熱負載', f"{thermal.get('total_power_W', 0)*1e6:.2f}", 'μW', ''))
        perf_data.append(('每通道熱負載', f"{thermal.get('per_channel_uW', 0):.2f}", 'μW', ''))
        perf_data.append(('溫差 ΔT', f"{thermal.get('delta_T', 0):.1f}", 'K', ''))
    
    if loss:
        perf_data.append(('插入損耗', f"{loss.get('損耗', 0):.2f}", f'dB @ {frequency}GHz',
                         '✅ 優良' if loss.get('損耗', 0) < 3 else '⚠️ 偏高'))
    
    if via_info:
        perf_data.append(('Via 屏蔽改善', f"{via_info.get('遮蔽強度', 0):.1f}", 'dB', ''))
    
    for row_idx, row_data in enumerate(perf_data, start=3):
        for col_idx, val in enumerate(row_data, start=1):
            cell = ws2.cell(row=row_idx, column=col_idx, value=val)
            cell.border = thin_border
            if row_idx == 3:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')
    
    ws2.column_dimensions['A'].width = 25
    ws2.column_dimensions['B'].width = 18
    ws2.column_dimensions['C'].width = 20
    ws2.column_dimensions['D'].width = 20
    
    # === Sheet 3: 公式推導 ===
    ws3 = wb.create_sheet("公式推導")
    ws3['A1'] = '串擾推導公式與計算過程'
    ws3['A1'].font = Font(size=14, bold=True)
    
    formula_lines = [
        ('符號', '定義', '公式', '數值', '單位'),
        ('w', '信號線寬度', '', f'{geo.w*1000:.1f}', 'μm'),
        ('s', '通道間距', '', f'{geo.s*1000:.1f}', 'mm'),
        ('h', '介電厚度', '', f'{geo.h*1000:.1f}', 'μm'),
        ('L', '傳輸線長度', '', f'{geo.L:.1f}', 'mm'),
        ('εr', '相對介電常數', '', f'{er}', ''),
        ('f', '工作頻率', '', f'{frequency}', 'GHz'),
    ]
    
    if crosstalk:
        formula_lines.extend([
            ('Cs', '單位自電容', 'ε₀εr·w/h', f'{crosstalk.get("電容", 0):.4e}', 'F/m'),
            ('Cm', '單位互電容', 'ε₀εr·w/s·exp(-πs/2h)', f'{crosstalk.get("電容", 0):.4e}', 'F/m'),
            ('Ls', '單位自電感', 'μ₀·h/w', f'{crosstalk.get("電感", 0):.4e}', 'H/m'),
            ('Lm', '單位互電感', 'μ₀/2π·h·ln(1+2h/s)', f'{crosstalk.get("電感", 0):.4e}', 'H/m'),
            ('kc', '電容耦合係數', 'Cm/(Cs+Cm)', f'{crosstalk.get("耦合強度", 0):.4f}', ''),
            ('kL', '電感耦合係數', 'Lm/(Ls+Lm)', f'{crosstalk.get("耦合強度", 0):.4f}', ''),
            ('k', '綜合耦合係數', '½(kc+kL)', f'{crosstalk.get("耦合強度", 0):.4f}', ''),
            ('β', '相位常數', '2πf√εr/c', f'{crosstalk.get("相位常數", 0):.4e}', 'rad/m'),
            ('θ', '電長度', 'βL', f'{crosstalk.get("相位常數", 0) * geo.L/1000:.4f}', ''),
            ('NEXT', '近端串擾', '20log(kθ/2)', f'{crosstalk.get("近端串擾", 0):.2f}', f'dB/m @{frequency}GHz'),
            ('FEXT', '遠端串擾', '20log(kθ)', f'{crosstalk.get("遠端串擾", 0):.2f}', f'dB/m @{frequency}GHz'),
        ])
    
    for row_idx, row_data in enumerate(formula_lines, start=3):
        for col_idx, val in enumerate(row_data, start=1):
            cell = ws3.cell(row=row_idx, column=col_idx, value=val)
            cell.border = thin_border
            if row_idx == 3:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')
    
    ws3.column_dimensions['A'].width = 12
    ws3.column_dimensions['B'].width = 25
    ws3.column_dimensions['C'].width = 30
    ws3.column_dimensions['D'].width = 18
    ws3.column_dimensions['E'].width = 18
    
    # === Sheet 4: 三視圖尺寸說明 (欄位文字，非圖片) ===
    ws4 = wb.create_sheet("三視圖尺寸")
    ws4['A1'] = '三視圖尺寸說明'
    ws4['A1'].font = Font(size=14, bold=True)
    ws4.merge_cells('A1:D1')
    ws4['A1'].alignment = Alignment(horizontal='center')
    
    # 三視圖尺寸說明的標題列
    headers = ['視圖', '顯示內容', '關鍵尺寸', '說明']
    for col_idx, header in enumerate(headers, start=1):
        cell = ws4.cell(row=3, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', wrap_text=True)
        cell.border = thin_border
    
    # 資料列
    view_data = [
        ('前視圖', 'YZ平面 - 橫截面', 
         f'總厚度={2*geo.h*1000+3*geo.t:.0f}μm, w={geo.w*1000:.0f}μm, h={geo.h*1000:.0f}μm, t={geo.t:.0f}μm',
         '顯示GND-Polyimide-Signal-Polyimide-GND五層結構'),
        ('側視圖', 'XZ平面 - 長度方向', 
         f'總長度 L={geo.L:.0f}mm, 總厚度={2*geo.h*1000+3*geo.t:.0f}μm',
         '顯示各層沿長度方向的連續結構，包含Bottom GND、Polyimide、Signal、Polyimide、Top GND'),
        ('上視圖', 'XY平面 - 通道佈線', 
         f'{n_channels}通道, pitch={pitch:.1f}mm, w={geo.w*1000:.0f}μm, L={geo.L:.0f}mm',
         f'信號線(S)與GND分隔條交錯排列，總寬度={pitch*n_channels+geo.w*2:.1f}mm'),
    ]
    
    if via_enabled:
        view_data.append(
            ('Via Stitching', '垂直貫穿GND層', 
             f'密度={via_density}/mm, 直徑={via_diameter}μm, 間距={1.0/via_density:.1f}mm',
             '提供上下GND電氣連接與橫向屏蔽，降低通道間串擾')
        )
    
    for row_idx, row_data in enumerate(view_data, start=4):
        for col_idx, val in enumerate(row_data, start=1):
            cell = ws4.cell(row=row_idx, column=col_idx, value=val)
            cell.border = thin_border
            cell.alignment = Alignment(wrap_text=True, vertical='top')
    
    ws4.column_dimensions['A'].width = 18
    ws4.column_dimensions['B'].width = 25
    ws4.column_dimensions['C'].width = 40
    ws4.column_dimensions['D'].width = 35
    for row in range(4, 4 + len(view_data)):
        ws4.row_dimensions[row].height = 35
    
    # === Sheet 5: 前視圖 (獨立圖片) ===
    ws5 = wb.create_sheet("前視圖")
    ws5['A1'] = '前視圖 (Cross-Section)'
    ws5['A1'].font = Font(size=14, bold=True)
    ws5.merge_cells('A1:C1')
    ws5['A1'].alignment = Alignment(horizontal='center')
    
    fig_front = draw_front_view(geo, pitch, via_enabled, via_diameter, via_density, n_channels)
    img_buffer = io.BytesIO()
    fig_front.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
    img_buffer.seek(0)
    img = Image(img_buffer)
    img.width = 700
    img.height = 500
    ws5.add_image(img, 'A3')
    plt.close(fig_front)
    
    # === Sheet 6: 側視圖 (獨立圖片) ===
    ws6 = wb.create_sheet("側視圖")
    ws6['A1'] = '側視圖 (Side View)'
    ws6['A1'].font = Font(size=14, bold=True)
    ws6.merge_cells('A1:C1')
    ws6['A1'].alignment = Alignment(horizontal='center')
    
    fig_side = draw_side_view(geo, length)
    img_buffer = io.BytesIO()
    fig_side.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
    img_buffer.seek(0)
    img = Image(img_buffer)
    img.width = 700
    img.height = 400
    ws6.add_image(img, 'A3')
    plt.close(fig_side)
    
    # === Sheet 7: 上視圖 (獨立圖片) ===
    ws7 = wb.create_sheet("上視圖")
    ws7['A1'] = '上視圖 (Top View)'
    ws7['A1'].font = Font(size=14, bold=True)
    ws7.merge_cells('A1:C1')
    ws7['A1'].alignment = Alignment(horizontal='center')
    
    fig_top = draw_top_view(geo, pitch, length, n_channels)
    img_buffer = io.BytesIO()
    fig_top.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
    img_buffer.seek(0)
    img = Image(img_buffer)
    img.width = 700
    img.height = 500
    ws7.add_image(img, 'A3')
    plt.close(fig_top)
    
    # 寫入字節流
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()

# ============================================================
# 功能 2: 串擾推導公式展示
# ============================================================

def calc_crosstalk_derivation(geo: StriplineGeometry, er: float, f: float):
    """
    計算完整的串擾推導參數
    """
    w = geo.w / 1000  # mm -> m
    s = geo.s / 1000  # mm -> m
    h = geo.h / 1000  # mm -> m
    t = geo.t / 1e6   # μm -> m
    L = geo.L / 1000  # mm -> m

    eps = er * EPS_0

    # 1. 單位長度自電容 Cs
    Cs = eps * w / h

    # 2. 單位長度互電容 Cm
    Cm = eps * w / s * exp(-pi * s / (2 * h))

    # 3. 單位長度自電感 Ls
    Ls = MU_0 * h / w

    # 4. 單位長度互電感 Lm
    Lm = MU_0 * h / (2 * pi) * log(1 + 2 * h / s)

    # 5. 電容耦合係數
    kc = Cm / (Cs + Cm)

    # 6. 電感耦合係數
    kL = Lm / (Ls + Lm)

    # 7. 綜合耦合係數
    k = 0.5 * (kc + kL)

    # 8. 相位常數
    beta = 2 * pi * f * sqrt(er) / C_LIGHT

    # 9. 電長度
    theta = beta * L

    # 10. 近端串擾
    if theta < 1:
        NEXT_linear = k * theta / 2
    else:
        NEXT_linear = k / 2
    NEXT_db = 20 * log10(max(abs(NEXT_linear), 1e-12))

    # 11. 遠端串擾
    FEXT_linear = k * theta
    FEXT_db = 20 * log10(max(abs(FEXT_linear), 1e-12))

    return {
        "Cs": Cs, "Cm": Cm, "Ls": Ls, "Lm": Lm,
        "kc": kc, "kL": kL, "k": k,
        "beta": beta, "theta": theta,
        "NEXT_linear": NEXT_linear, "NEXT_db": NEXT_db,
        "FEXT_linear": FEXT_linear, "FEXT_db": FEXT_db,
        "w_m": w, "s_m": s, "h_m": h, "L_m": L
    }


def render_formula_section():
    """渲染完整的公式推導區塊"""
    formula_md = r"""
    ---

    ## 📐 串擾推導公式詳解

    ### 一、幾何與材料參數

    | 符號 | 定義 | 單位 |
    |------|------|------|
    | $w$ | 信號線寬度 | m |
    | $t$ | 導體厚度 | m |
    | $h$ | 單層介電厚度 (上下對稱) | m |
    | $s$ | 通道間距 (Pitch) | m |
    | $L$ | 傳輸線長度 | m |
    | $\epsilon_r$ | 相對介電常數 (Polyimide = 3.4) | — |
    | $\epsilon_0$ | 真空介電常數 = $8.854 \times 10^{-12}$ | F/m |
    | $\mu_0$ | 真空磁導率 = $4\pi \times 10^{-7}$ | H/m |
    | $f$ | 工作頻率 | Hz |
    | $c$ | 光速 = $3 \times 10^8$ | m/s |

    ---

    ### 二、單位長度電容

    #### 2.1 自電容 $C_s$ (Self-Capacitance)

    對於對稱 Stripline (Ground-Signal-Ground)，信號線與上下兩接地層形成平行板電容：

    $$
    C_s = \varepsilon_0 \varepsilon_r \cdot \frac{w}{h}
    $$

    **物理意義**：單位長度信號線對單一接地層的電容。

    ---

    #### 2.2 互電容 $C_m$ (Mutual Capacitance)

    相鄰信號線間的電容耦合，採用經驗衰減模型：

    $$
    C_m = \varepsilon_0 \varepsilon_r \cdot \frac{w}{s} \cdot \exp\left(-\frac{\pi s}{2h}\right)
    $$

    **物理意義**：$\exp\left(-\frac{\pi s}{2h}\right)$ 為介電屏蔽衰減項。

    ---

    ### 三、單位長度電感

    #### 3.1 自電感 $L_s$ (Self-Inductance)

    $$
    L_s = \mu_0 \cdot \frac{h}{w}
    $$

    ---

    #### 3.2 互電感 $L_m$ (Mutual Inductance)

    $$
    L_m = \frac{\mu_0}{2\pi} \cdot h \cdot \ln\left(1 + \frac{2h}{s}\right)
    $$

    ---

    ### 四、耦合係數

    #### 4.1 電容耦合係數 $k_c$

    $$
    k_c = \frac{C_m}{C_s + C_m}
    $$

    #### 4.2 電感耦合係數 $k_L$

    $$
    k_L = \frac{L_m}{L_s + L_m}
    $$

    #### 4.3 綜合耦合係數 $k$

    $$
    k = \frac{1}{2}(k_c + k_L)
    $$

    ---

    ### 五、傳播參數

    #### 5.1 相位常數 $\beta$

    $$
    \beta = \frac{2\pi f \sqrt{\varepsilon_r}}{c}
    $$

    #### 5.2 電長度 $\theta$

    $$
    \theta = \beta \cdot L
    $$

    ---

    ### 六、串擾公式

    #### 6.1 近端串擾 (NEXT)

    $$
    \text{NEXT}_{linear} = \begin{cases}
    \displaystyle\frac{k \cdot \theta}{2}, & \theta < 1 \\
    \displaystyle\frac{k}{2}, & \theta \geq 1
    \end{cases}
    $$

    $$
    \text{NEXT}_{dB} = 20 \log_{10}(\text{NEXT}_{linear})
    $$

    #### 6.2 遠端串擾 (FEXT)

    $$
    \text{FEXT}_{linear} = k \cdot \theta
    $$

    $$
    \text{FEXT}_{dB} = 20 \log_{10}(\text{FEXT}_{linear})
    $$

    ---
    """
    return formula_md


def show_formula_calculation(geo: StriplineGeometry, er: float, f: float):
    """顯示當前參數下的逐步計算過程"""
    calc = calc_crosstalk_derivation(geo, er, f)

    calc_md = rf"""
    ### 📊 當前參數逐步計算

    **輸入參數：**
    - $w$ = {calc['w_m']*1e6:.1f} μm = {calc['w_m']:.4e} m
    - $s$ = {calc['s_m']*1e3:.2f} mm = {calc['s_m']:.4e} m
    - $h$ = {calc['h_m']*1e6:.1f} μm = {calc['h_m']:.4e} m
    - $L$ = {calc['L_m']*1e3:.1f} mm = {calc['L_m']:.4e} m
    - $\varepsilon_r$ = {er}
    - $f$ = {f/1e9:.2f} GHz

    ---

    **Step 1: 單位長度自電容 $C_s$**

    $$
    C_s = \varepsilon_0 \varepsilon_r \frac{{w}}{{h}} = (8.854 \times 10^{{-12}}) \times {er} \times \frac{{{calc['w_m']:.4e}}}{{{calc['h_m']:.4e}}} = {calc['Cs']:.4e} \text{{ F/m}}
    $$

    **Step 2: 單位長度互電容 $C_m$**

    $$
    C_m = \varepsilon_0 \varepsilon_r \frac{{w}}{{s}} \exp\left(-\frac{{\pi s}}{{2h}}\right) = {calc['Cm']:.4e} \text{{ F/m}}
    $$

    **Step 3: 單位長度自電感 $L_s$**

    $$
    L_s = \mu_0 \frac{{h}}{{w}} = (4\pi \times 10^{{-7}}) \times \frac{{{calc['h_m']:.4e}}}{{{calc['w_m']:.4e}}} = {calc['Ls']:.4e} \text{{ H/m}}
    $$

    **Step 4: 單位長度互電感 $L_m$**

    $$
    L_m = \frac{{\mu_0}}{{2\pi}} h \ln\left(1 + \frac{{2h}}{{s}}\right) = {calc['Lm']:.4e} \text{{ H/m}}
    $$

    **Step 5: 耦合係數**

    $$
    k_c = \frac{{C_m}}{{C_s + C_m}} = {calc['kc']:.6f}
    $$

    $$
    k_L = \frac{{L_m}}{{L_s + L_m}} = {calc['kL']:.6f}
    $$

    $$
    k = \frac{{1}}{{2}}(k_c + k_L) = {calc['k']:.6f}
    $$

    **Step 6: 相位常數與電長度**

    $$
    \beta = \frac{{2\pi f \sqrt{{\varepsilon_r}}}}{{c}} = {calc['beta']:.4e} \text{{ rad/m}}
    $$

    $$
    \theta = \beta L = {calc['theta']:.4f}
    $$

    **Step 7: 串擾計算**

    {"$\theta < 1$ (電短線區)，使用線性公式：" if calc['theta'] < 1 else "$\theta \geq 1$ (電長線區)，使用飽和公式："}

    $$
    \text{{NEXT}}_{{linear}} = {calc['NEXT_linear']:.6e} \quad \Rightarrow \quad \text{{NEXT}}_{{dB}} = \mathbf{{{calc['NEXT_db']:.2f} \text{{ dB}}}}
    $$

    $$
    \text{{FEXT}}_{{linear}} = {calc['FEXT_linear']:.6e} \quad \Rightarrow \quad \text{{FEXT}}_{{dB}} = \mathbf{{{calc['FEXT_db']:.2f} \text{{ dB}}}}
    $$
    """
    return calc_md, calc


# ============================================================
# 計算核心函數
# ============================================================

def calc_stripline_impedance(geo: StriplineGeometry, er: float) -> float:
    """計算 Stripline 特性阻抗"""
    b = 2 * geo.h
    w = geo.w
    t = geo.t / 1000

    if w / b > 0.35:
        We = w + (t / pi) * (1 + log(2 * b / t))
    else:
        We = w - (b / (2 * pi)) * (1 - 0.5 * exp(-4 * pi * w / b)) * log(1 + 2 * t / b)

    Z0 = (30 * pi / sqrt(er)) * (b / We)
    return Z0


def calc_crosstalk_stripline(geo: StriplineGeometry, er: float, f: float) -> Dict[str, float]:
    """計算 Stripline 串擾"""
    w = geo.w
    s = geo.s
    h = geo.h
    L = geo.L / 1000

    eps = er * EPS_0

    C_self = eps * (w / (2 * h))
    Cm = eps * (w / 1000) / (s / 1000) * exp(-pi * s / (2 * h))
    L_self = MU_0 * (2 * h / w) * 1e-3
    Lm = MU_0 * (h / (2 * pi * s)) * 1e-3

    kc = Cm / (C_self + Cm) if (C_self + Cm) > 0 else 0
    kL = Lm / (L_self + Lm) if (L_self + Lm) > 0 else 0
    k = 0.5 * (kc + kL)

    beta = 2 * pi * f * sqrt(er) / C_LIGHT

    if beta * L < 1:
        next_linear = k * beta * L / 2
        NEXT_db = 20 * log10(max(next_linear, 1e-12))
    else:
        NEXT_db = 20 * log10(k / 2)

    fext_linear = k * beta * L
    FEXT_db = 20 * log10(max(fext_linear, 1e-12))

    return {
        "近端串擾": NEXT_db,
        "遠端串擾": FEXT_db,
        "耦合強度": k,
        "電容": Cm,
        "電感": Lm,
        "相位常數": beta
    }


def calc_thermal_conductivity(material: str, T: float) -> float:
    """計算材料在溫度 T 下的熱導率"""
    props = MATERIAL_THERMAL.get(material, None)
    if props is None:
        return 1.0

    if props["type"] == "superconducting":
        Tc = props["Tc"]
        if T < Tc * 0.5:
            return props["sc_k"]
        elif T < Tc:
            return props["sc_k"] + (props["normal_k"] - props["sc_k"]) * ((T - 0.5*Tc) / (0.5*Tc))
        else:
            return props["normal_k"]

    elif props["type"] == "power_law":
        A = props["A"]
        alpha = props["alpha"]
        return A * (T / 300) ** alpha

    elif props["type"] == "wiedemann_franz":
        return props["L0"] * props["sigma"] * T

    return 1.0


def calc_thermal_load(geo: StriplineGeometry, boundary: ThermalBoundary,
                      materials: MaterialStack) -> Dict[str, float]:
    """計算熱負載"""
    T_hot = boundary.T_hot
    T_cold = boundary.T_cold
    L_m = geo.L / 1000

    n_points = 100
    T_range = linspace(T_cold, T_hot, n_points)

    total_kA = 0
    for layer in materials.layers:
        mat = layer["material"]
        thickness = layer["thickness"] / 1e6
        width = layer["width"] / 1000
        area = thickness * width

        k_avg = mean([calc_thermal_conductivity(mat, T) for T in T_range])
        total_kA += k_avg * area

    delta_T = T_hot - T_cold
    P = total_kA * delta_T / L_m
    P_per_channel = P / geo.n_channels

    return {
        "total_power_W": P,
        "per_channel_W": P_per_channel,
        "per_channel_uW": P_per_channel * 1e6,
        "per_channel_nW": P_per_channel * 1e9,
        "kA_total": total_kA,
        "delta_T": delta_T
    }


def calc_insertion_loss(geo: StriplineGeometry, er: float, tan_delta: float,
                        f: float, material: str = "Ag", T: float = 300.0) -> float:
    """計算插入損耗"""
    w = geo.w / 1000
    t = geo.t / 1e6
    L = geo.L / 1000
    h = geo.h / 1000

    sigma_n = {"Ag": 6.3e7, "NbTi": 1e6, "Cu": 5.8e7}.get(material, 6.3e7)

    Tc = 9.2
    if material == "NbTi" and T < Tc:
        Rs_ref = 0.0012
        f_factor = (f / 6e9) ** 2

        if T < 0.5 * Tc:
            T_factor = max(0.001, (T / 4.0) ** 1.5)
            Rs = Rs_ref * f_factor * T_factor
        else:
            delta_s_n = sqrt(2 / (MU_0 * sigma_n * 2 * pi * f))
            Rs_normal = 1 / (sigma_n * delta_s_n)
            T_factor = (T / 4.0) ** 1.5
            Rs_sc = Rs_ref * f_factor * T_factor
            ratio = (T - 0.5 * Tc) / (0.5 * Tc)
            Rs = Rs_sc + (Rs_normal - Rs_sc) * ratio
    else:
        delta_s = sqrt(2 / (MU_0 * sigma_n * 2 * pi * f))
        Rs = 1 / (sigma_n * delta_s)

    Z0_actual = calc_stripline_impedance(geo, er)
    Z0_eff = max(Z0_actual, 1.0)

    alpha_c = Rs / (Z0_eff * w)
    alpha_c_db = alpha_c * 8.686

    alpha_d = (pi * f * sqrt(er) * tan_delta) / C_LIGHT
    alpha_d_db = alpha_d * 8.686

    total_loss_db = (alpha_c_db + alpha_d_db) * L
    return total_loss_db


def calc_via_impact(pitch: float, via_diameter: float, via_density: float) -> Dict:
    """計算 Via stitching 對串擾的改善"""
    via_spacing = 1.0 / via_density
    shielding_improvement = 20 * log10(1 + 0.5 * via_density * pitch)

    return {
        "打洞間距": via_spacing,
        "遮蔽強度": shielding_improvement,
        "推薦密度": min(2.0, 1.0 / (pitch / 4))
    }


# ============================================================
# 匯出功能 - Excel 格式 (含三視圖)
# ============================================================

def export_to_excel(geo: StriplineGeometry, er: float, tan_d: float, Z0: float,
                    results: Dict, crosstalk: Dict, thermal: Dict, loss: Dict,
                    via_info: Dict, fig_views: plt.Figure,
                    conductor_material: str, dielectric_material: str,
                    temp_stage: str, frequency: float,
                    pitch: float, length: float, sig_width: float,
                    sig_thickness: float, dielectric_thickness: float,
                    n_channels: int, via_enabled: bool, via_density: float,
                    via_diameter: float, T_hot: float, T_cold: float) -> bytes:
    """
    匯出完整規格至 Excel，包含：
    1. 設計參數 (含單位)
    2. 性能指標
    3. 公式推導過程
    4. 計算結果
    5. 三視圖
    """
    wb = Workbook()
    
    # === Sheet 1: 設計規格 ===
    ws1 = wb.active
    ws1.title = "設計規格"
    
    # 標題
    ws1.merge_cells('A1:D1')
    ws1['A1'] = 'Cri/oFlex3 柔性傳輸線規格書'
    ws1['A1'].font = Font(size=16, bold=True)
    ws1['A1'].alignment = Alignment(horizontal='center')
    
    # 生成時間
    ws1['A3'] = f'生成時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    ws1['A3'].font = Font(size=10, italic=True)
    
    # 設計參數表頭
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True)
    
    params = [
        ('參數', '數值', '單位', '說明'),
        ('通道數', n_channels, 'ch', ''),
        ('通道間距 (Pitch)', pitch, 'mm', '中心到中心距離'),
        ('傳輸線長度', length, 'mm', ''),
        ('信號線寬度', sig_width, 'μm', '影響特性阻抗'),
        ('導體厚度', sig_thickness, 'μm', ''),
        ('單層介電厚度', dielectric_thickness, 'μm', ''),
        ('導體材料', conductor_material, '', 'Ag/NbTi/Cu'),
        ('介電材料', dielectric_material, '', 'Polyimide'),
        ('介電常數 εr', er, '', 'Polyimide'),
        ('損耗角 tan δ', f'{tan_d:.2e}', '', f'@{T_cold:.1f}K'),
        ('工作頻率', frequency, 'GHz', ''),
        ('溫度階段', temp_stage, '', f'{T_hot}K → {T_cold}K'),
        ('Via Stitching', '啟用' if via_enabled else '未啟用', '', ''),
        ('Via 密度', via_density if via_enabled else '-', '/mm', ''),
        ('Via 直徑', via_diameter if via_enabled else '-', 'μm', ''),
    ]
    
    for row_idx, row_data in enumerate(params, start=5):
        for col_idx, val in enumerate(row_data, start=1):
            cell = ws1.cell(row=row_idx, column=col_idx, value=val)
            if row_idx == 5:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')
            else:
                if col_idx == 2:
                    cell.alignment = Alignment(horizontal='right')
                elif col_idx == 3:
                    cell.alignment = Alignment(horizontal='center')
    
    # 設定欄寬
    ws1.column_dimensions['A'].width = 20
    ws1.column_dimensions['B'].width = 18
    ws1.column_dimensions['C'].width = 12
    ws1.column_dimensions['D'].width = 30
    
    # === Sheet 2: 性能指標 ===
    ws2 = wb.create_sheet("性能指標")
    
    ws2['A1'] = '性能指標'
    ws2['A1'].font = Font(size=14, bold=True)
    
    perf_data = [
        ('指標', '數值', '單位', '狀態'),
        ('特性阻抗', f'{Z0:.1f}', 'Ω', '✅ 匹配' if 45 < Z0 < 55 else '⚠️ 不匹配'),
    ]
    
    if crosstalk:
        perf_data.append(('近端串擾 (NEXT)', f"{crosstalk.get('近端串擾', 0):.1f}", 'dB', 
                         '✅ 優良' if crosstalk.get('近端串擾', 0) < -40 else '⚠️ 需改善'))
        perf_data.append(('遠端串擾 (FEXT)', f"{crosstalk.get('遠端串擾', 0):.1f}", 'dB', ''))
        perf_data.append(('耦合係數 k', f"{crosstalk.get('耦合強度', 0):.4f}", '', ''))
    
    if thermal:
        perf_data.append(('總熱負載', f"{thermal.get('total_power_W', 0)*1e6:.2f}", 'μW', ''))
        perf_data.append(('每通道熱負載', f"{thermal.get('per_channel_uW', 0):.2f}", 'μW', ''))
        perf_data.append(('溫差 ΔT', f"{thermal.get('delta_T', 0):.1f}", 'K', ''))
    
    if loss:
        perf_data.append(('插入損耗', f"{loss.get('損耗', 0):.2f}", 'dB', 
                         '✅ 優良' if loss.get('損耗', 0) < 3 else '⚠️ 偏高'))
    
    if via_info:
        perf_data.append(('Via 屏蔽改善', f"{via_info.get('遮蔽強度', 0):.1f}", 'dB', ''))
    
    for row_idx, row_data in enumerate(perf_data, start=3):
        for col_idx, val in enumerate(row_data, start=1):
            cell = ws2.cell(row=row_idx, column=col_idx, value=val)
            if row_idx == 3:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')
    
    ws2.column_dimensions['A'].width = 25
    ws2.column_dimensions['B'].width = 18
    ws2.column_dimensions['C'].width = 12
    ws2.column_dimensions['D'].width = 20
    
    # === Sheet 3: 公式推導 ===
    ws3 = wb.create_sheet("公式推導")
    
    ws3['A1'] = '串擾推導公式與計算過程'
    ws3['A1'].font = Font(size=14, bold=True)
    
    formula_lines = [
        ('符號', '定義', '公式', '數值', '單位'),
        ('w', '信號線寬度', '', f'{geo.w*1000:.1f}', 'μm'),
        ('s', '通道間距', '', f'{geo.s*1000:.1f}', 'mm'),
        ('h', '介電厚度', '', f'{geo.h*1000:.1f}', 'μm'),
        ('L', '傳輸線長度', '', f'{geo.L:.1f}', 'mm'),
        ('εr', '相對介電常數', '', f'{er}', ''),
        ('f', '工作頻率', '', f'{frequency}', 'GHz'),
    ]
    
    # 如果有串擾計算結果
    if crosstalk:
        formula_lines.extend([
            ('Cs', '單位自電容', 'ε₀εr·w/h', f'{crosstalk.get("電容", 0):.4e}', 'F/m'),
            ('Cm', '單位互電容', 'ε₀εr·w/s·exp(-πs/2h)', f'{crosstalk.get("電容", 0):.4e}', 'F/m'),
            ('Ls', '單位自電感', 'μ₀·h/w', f'{crosstalk.get("電感", 0):.4e}', 'H/m'),
            ('Lm', '單位互電感', 'μ₀/2π·h·ln(1+2h/s)', f'{crosstalk.get("電感", 0):.4e}', 'H/m'),
            ('kc', '電容耦合係數', 'Cm/(Cs+Cm)', f'{crosstalk.get("耦合強度", 0):.4f}', ''),
            ('kL', '電感耦合係數', 'Lm/(Ls+Lm)', f'{crosstalk.get("耦合強度", 0):.4f}', ''),
            ('k', '綜合耦合係數', '½(kc+kL)', f'{crosstalk.get("耦合強度", 0):.4f}', ''),
            ('β', '相位常數', '2πf√εr/c', f'{crosstalk.get("相位常數", 0):.4e}', 'rad/m'),
            ('θ', '電長度', 'βL', f'{crosstalk.get("相位常數", 0) * geo.L/1000:.4f}', ''),
            ('NEXT', '近端串擾', '20log(kθ/2)', f'{crosstalk.get("近端串擾", 0):.2f}', 'dB'),
            ('FEXT', '遠端串擾', '20log(kθ)', f'{crosstalk.get("遠端串擾", 0):.2f}', 'dB'),
        ])
    
    for row_idx, row_data in enumerate(formula_lines, start=3):
        for col_idx, val in enumerate(row_data, start=1):
            cell = ws3.cell(row=row_idx, column=col_idx, value=val)
            if row_idx == 3:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')
    
    ws3.column_dimensions['A'].width = 12
    ws3.column_dimensions['B'].width = 25
    ws3.column_dimensions['C'].width = 30
    ws3.column_dimensions['D'].width = 18
    ws3.column_dimensions['E'].width = 12
    
    # === Sheet 4: 計算結果詳細 ===
    ws4 = wb.create_sheet("計算結果詳細")
    
    ws4['A1'] = '詳細計算結果'
    ws4['A1'].font = Font(size=14, bold=True)
    
    detail_data = [('項目', '數值', '單位')]
    
    detail_data.append(('特性阻抗 Z0', f'{Z0:.1f}', 'Ω'))
    
    if crosstalk:
        detail_data.append(('近端串擾 NEXT', f"{crosstalk.get('近端串擾', 0):.1f}", 'dB'))
        detail_data.append(('遠端串擾 FEXT', f"{crosstalk.get('遠端串擾', 0):.1f}", 'dB'))
        detail_data.append(('耦合強度 k', f"{crosstalk.get('耦合強度', 0):.4f}", ''))
    
    if thermal:
        detail_data.append(('總熱負載', f"{thermal.get('total_power_W', 0)*1e6:.2f}", 'μW'))
        detail_data.append(('每通道熱負載', f"{thermal.get('per_channel_uW', 0):.2f}", 'μW'))
        detail_data.append(('溫差 ΔT', f"{thermal.get('delta_T', 0):.1f}", 'K'))
    
    if loss:
        detail_data.append(('插入損耗', f"{loss.get('損耗', 0):.2f}", 'dB'))
    
    for row_idx, row_data in enumerate(detail_data, start=3):
        for col_idx, val in enumerate(row_data, start=1):
            cell = ws4.cell(row=row_idx, column=col_idx, value=val)
            if row_idx == 3:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')
    
    ws4.column_dimensions['A'].width = 25
    ws4.column_dimensions['B'].width = 18
    ws4.column_dimensions['C'].width = 12
    
    # === Sheet 5: 三視圖 ===
    ws5 = wb.create_sheet("三視圖")
    ws5['A1'] = '傳輸線三視圖'
    ws5['A1'].font = Font(size=14, bold=True)
    ws5.merge_cells('A1:C1')
    ws5['A1'].alignment = Alignment(horizontal='center')
    
    # 將圖保存為圖片並插入
    if fig_views is not None:
        img_buffer = io.BytesIO()
        fig_views.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        
        img = Image(img_buffer)
        img.width = 800
        img.height = 600
        ws5.add_image(img, 'A3')
    
    # 寫入字節流
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()


# ============================================================
# Streamlit UI
# ============================================================

set_page_config(page_title="Cri/oFlex3 柔性傳輸線規格計算器 VI", page_icon="🔬", layout="wide", initial_sidebar_state="expanded")

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

# 初始化 session_state
if 'geo' not in session_state:
    session_state['geo'] = None
if 'results' not in session_state:
    session_state['results'] = {}
if 'crosstalk' not in session_state:
    session_state['crosstalk'] = {}
if 'thermal' not in session_state:
    session_state['thermal'] = {}
if 'loss' not in session_state:
    session_state['loss'] = {}
if 'via_info' not in session_state:
    session_state['via_info'] = {}
if 'fig_views' not in session_state:
    session_state['fig_views'] = None

# 側邊欄 - 參數輸入
with sidebar:
    subheader("⚙️ 設計參數")
    subheader("幾何結構")
    n_channels = radio("通道數", [4, 8, 16, 32], index=1, horizontal=True)
    pitch = slider("通道間距 Pitch (mm)", 0.5, 5.0, 2.0, 0.1)
    length = slider("傳輸線長度 (mm)", 100, 1500, 400, 50)
    sig_width = slider("信號線寬度 (μm)", 50, 500, 300, 10)
    sig_thickness = slider("導體厚度 (μm)", 1, 20, 5, 1)
    dielectric_thickness = slider("單層介電厚度 (μm)", 50, 300, 150, 10)

    subheader("材料選擇")
    conductor_material = radio("導體材料", ["Ag (銀)", "NbTi (超導)", "Cu (銅)"], index=1, horizontal=True)
    dielectric_material = radio("介電材料", ["Polyimide"], index=0, horizontal=True)

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

# 主內容區
MENU = ['計算結果', '串擾', '熱負載', '插入損耗', '規格摘要', '三視圖', '推導公式']

menu = radio('功能選單', MENU, horizontal=True, index=0)

# 建立幾何結構
geo = StriplineGeometry(
    w=sig_width / 1000,
    t=sig_thickness,
    h=dielectric_thickness / 1000,
    s=pitch,
    L=length,
    n_channels=n_channels
)
session_state['geo'] = geo

# 介電參數
dielectric = DIELECTRIC["Polyimide"]
er = dielectric["εr"]
session_state['er'] = er

# 溫度邊界
temp_map = {
    "300K → 40K": (300, 40),
    "40K → 4K": (40, 4),
    "4K → 1K": (4, 1),
    "1K → 100mK": (1, 0.1),
    "RT → mK (全段)": (300, 0.01)
}
T_hot, T_cold = temp_map[temp_stage]
boundary = ThermalBoundary(T_hot=T_hot, T_cold=T_cold, stage=temp_stage)

# 材料堆疊
mat_name = conductor_material.split(" ")[0]
materials = MaterialStack(layers=[
    {"material": mat_name, "thickness": sig_thickness, "width": sig_width},
    {"material": "Polyimide", "thickness": dielectric_thickness * 2, "width": pitch * 0.8},
    {"material": mat_name, "thickness": sig_thickness, "width": pitch * 0.8}
])

# 計算
Z0 = calc_stripline_impedance(geo, er)
session_state['Z0'] = Z0

crosstalk = {}
thermal = {}
loss = {}
via_info = {}

if calc_crosstalk:
    crosstalk = calc_crosstalk_stripline(geo, er, frequency * 1e9)
    session_state['crosstalk'] = crosstalk
    
    if via_enabled:
        via_info = calc_via_impact(pitch, via_diameter, via_density)
        session_state['via_info'] = via_info
        crosstalk["近端串擾"] -= via_info["遮蔽強度"]
        crosstalk["遠端串擾"] -= via_info["遮蔽強度"]

if calc_thermal:
    thermal = calc_thermal_load(geo, boundary, materials)
    session_state['thermal'] = thermal

if calc_loss:
    if T_cold < 1:
        tan_d = dielectric["tan_delta_20mK"]
    elif T_cold < 10:
        tan_d = dielectric["tan_delta_4K"]
    else:
        tan_d = dielectric["tan_delta_rt"]
    
    loss = calc_insertion_loss(geo, er, tan_d, frequency * 1e9, mat_name, T=T_cold)
    session_state['loss'] = {'損耗': loss}
    session_state['tan_d'] = tan_d

session_state['T_hot'] = T_hot
session_state['T_cold'] = T_cold
session_state['mat_name'] = mat_name

# ============================================================
# 各頁面內容
# ============================================================

if menu == '計算結果':
    subheader("📊 計算結果")
    
    cols = columns(3)
    with cols[0]:
        metric("特性阻抗", f"{Z0:.1f} Ω", 
               delta=f"{'✓ 匹配' if 45 < Z0 < 55 else '✗ 不匹配'}",
               delta_color="normal" if 45 < Z0 < 55 else "inverse")
    with cols[1]:
        metric("通道密度", f"{n_channels} ch", 
               delta=f"{n_channels/pitch:.1f} ch/mm")
    with cols[2]:
        effective_er = er
        v_phase = C_LIGHT / sqrt(effective_er)
        delay = (length / 1000) / v_phase * 1e9
        metric("傳輸延遲", f"{delay:.2f} ns")
    
    if calc_crosstalk and crosstalk:
        cols = columns(4)
        with cols[0]:
            metric("近端串擾 (NEXT)", f"{crosstalk.get('近端串擾', 0):.1f} dB",
                   delta="優良" if crosstalk.get('近端串擾', 0) < -40 else "需改善",
                   delta_color="normal" if crosstalk.get('近端串擾', 0) < -40 else "inverse")
        with cols[1]:
            metric("遠端串擾 (FEXT)", f"{crosstalk.get('遠端串擾', 0):.1f} dB")
        with cols[2]:
            metric("耦合係數 k", f"{crosstalk.get('耦合強度', 0):.4f}")
        with cols[3]:
            if via_enabled and via_info:
                metric("Via 屏蔽改善", f"{via_info.get('遮蔽強度', 0):.1f} dB")
    
    if calc_thermal and thermal:
        cols = columns(4)
        with cols[0]:
            metric("總熱負載", f"{thermal.get('total_power_W', 0)*1e6:.2f} μW")
        with cols[1]:
            metric("每通道熱負載", f"{thermal.get('per_channel_uW', 0):.2f} μW")
        with cols[2]:
            metric("溫差 ΔT", f"{thermal.get('delta_T', 0):.1f} K")
        with cols[3]:
            metric("等效 kA", f"{thermal.get('kA_total', 0)*1e6:.3f} μW·m/K")
    
    if calc_loss and loss:
        cols = columns(2)
        with cols[0]:
            metric(f"@{frequency} GHz 插入損耗", f"{loss:.2f} dB",
                   delta="優良" if loss < 3 else "偏高",
                   delta_color="normal" if loss < 3 else "inverse")
        with cols[1]:
            alpha_total = loss / (length / 1000)
            metric("衰減常數", f"{alpha_total:.2f} dB/m")

elif menu == '串擾':
    subheader("📡 串擾分析")
    
    if calc_crosstalk and crosstalk:
        cols = columns(4)
        with cols[0]:
            metric("近端串擾 (NEXT)", f"{crosstalk.get('近端串擾', 0):.1f} dB",
                   delta="優良" if crosstalk.get('近端串擾', 0) < -40 else "需改善",
                   delta_color="normal" if crosstalk.get('近端串擾', 0) < -40 else "inverse")
        with cols[1]:
            metric("遠端串擾 (FEXT)", f"{crosstalk.get('遠端串擾', 0):.1f} dB")
        with cols[2]:
            metric("耦合係數 k", f"{crosstalk.get('耦合強度', 0):.4f}")
        with cols[3]:
            if via_enabled and via_info:
                metric("Via 屏蔽改善", f"{via_info.get('遮蔽強度', 0):.1f} dB")
        
        # 串擾頻率響應圖
        markdown("<div class='highlight'>串擾頻率響應 (1-18 GHz)</div>", unsafe_allow_html=True)
        freqs = linspace(1, 18, 100) * 1e9
        next_vals = []
        fext_vals = []
        for f in freqs:
            ct_f = calc_crosstalk_stripline(geo, er, f)
            if via_enabled and via_info:
                ct_f["近端串擾"] -= via_info.get("遮蔽強度", 0)
                ct_f["遠端串擾"] -= via_info.get("遮蔽強度", 0)
            next_vals.append(ct_f["近端串擾"])
            fext_vals.append(ct_f["遠端串擾"])
        
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
    else:
        warning("請在側邊欄啟用『計算串擾』")

elif menu == '熱負載':
    subheader("🌡️ 熱負載分析")
    
    if calc_thermal and thermal:
        cols = columns(4)
        with cols[0]:
            metric("總熱負載", f"{thermal.get('total_power_W', 0)*1e6:.2f} μW")
        with cols[1]:
            metric("每通道熱負載", f"{thermal.get('per_channel_uW', 0):.2f} μW",
                   delta=f"{thermal.get('per_channel_nW', 0):.1f} nW",
                   delta_color="off")
        with cols[2]:
            metric("溫差 ΔT", f"{thermal.get('delta_T', 0):.1f} K")
        with cols[3]:
            metric("等效 kA", f"{thermal.get('kA_total', 0)*1e6:.3f} μW·m/K")
        
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
        colors_bar = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
        bars = ax2.bar(stage_names, powers, color=colors_bar, edgecolor='black', linewidth=1.2)
        ax2.set_ylabel("Heat Load per Channel (μW)", fontsize=12)
        ax2.set_title("Thermal Load Distribution Across Cryogenic Stages", fontsize=14)
        ax2.set_yscale('log')
        ax2.grid(True, alpha=0.3, axis='y')
        
        for bar, power in zip(bars, powers):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{power:.2f}',
                    ha='center', va='bottom', fontsize=10)
        
        pyplot(fig2)
        
        markdown("""
        <div class="highlight">
        <b>📋 與 Cri/oFlex3 官方規格比較:</b><br>
        • 官方標稱: 4K-40K, L=0.4m: < 125 μW/通道<br>
        • 官方標稱: 10mK-350mK, L=0.2m: ~ 20 nW/通道<br>
        • 本計算 NbTi 超導態: 大幅降低熱負載 (10× 改善)
        </div>
        """, unsafe_allow_html=True)
    else:
        warning("請在側邊欄啟用『計算熱負載』")

elif menu == '插入損耗':
    subheader("📉 插入損耗")
    
    if calc_loss and loss:
        cols = columns(2)
        with cols[0]:
            metric(f"@{frequency} GHz 插入損耗", f"{loss:.2f} dB",
                   delta="優良" if loss < 3 else "偏高",
                   delta_color="normal" if loss < 3 else "inverse")
        with cols[1]:
            alpha_total = loss / (length / 1000)
            metric("衰減常數", f"{alpha_total:.2f} dB/m")
        
        # 損耗頻率響應
        markdown("<div class='highlight'>插入損耗頻率響應</div>", unsafe_allow_html=True)
        freqs_loss = linspace(0.1, 20, 200) * 1e9
        losses = []
        for f in freqs_loss:
            l = calc_insertion_loss(geo, er, tan_d, f, mat_name, T=T_cold)
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
    else:
        warning("請在側邊欄啟用『計算插入損耗』")

elif menu == '規格摘要':
    subheader("📋 規格摘要")
    
    col_left, col_right = columns(2)
    
    with col_left:
        subheader("設計參數")
        spec_data = {
            "參數": ["通道數", "Pitch", "長度", "線寬", "導體厚", "介電厚", 
                     "導體材料", "介電材料", "介電常數 εr", "損耗角 tan δ"],
            "數值": [
                f"{n_channels} ch",
                f"{pitch} mm",
                f"{length} mm",
                f"{sig_width} μm",
                f"{sig_thickness} μm",
                f"{dielectric_thickness} μm",
                conductor_material,
                dielectric_material,
                f"{er}",
                f"{tan_d:.2e} (@ {T_cold:.1f}K)"
            ]
        }
        table(spec_data)
        
        subheader("性能指標")
        perf_data = {}
        if calc_crosstalk and crosstalk:
            perf_data["串擾 (NEXT)"] = f"{crosstalk.get('近端串擾', 0):.1f} dB"
            perf_data["串擾 (FEXT)"] = f"{crosstalk.get('遠端串擾', 0):.1f} dB"
        if calc_thermal and thermal:
            perf_data["熱負載/通道"] = f"{thermal.get('per_channel_uW', 0):.2f} μW"
        if calc_loss and loss:
            perf_data["插入損耗"] = f"{loss:.2f} dB"
        perf_data["特性阻抗"] = f"{Z0:.1f} Ω"
        
        perf_df = {"指標": list(perf_data.keys()), "數值": list(perf_data.values())}
        table(perf_df)
        
        subheader("💡 設計建議")
        suggestions = []
        
        if Z0 < 45 or Z0 > 55:
            suggestions.append(f"⚠️ 阻抗 {Z0:.1f}Ω 偏離 50Ω 目標，建議調整線寬至 {150 * 50/Z0:.0f}μm")
        else:
            suggestions.append("✅ 阻抗匹配良好")
        
        if calc_crosstalk and crosstalk:
            if crosstalk.get('近端串擾', 0) > -40:
                suggestions.append(f"⚠️ 串擾偏高，建議增加 pitch 至 {pitch * 1.5:.1f}mm 或增加 via 密度")
            else:
                suggestions.append("✅ 串擾性能優良")
        
        if calc_thermal and thermal:
            if mat_name == "NbTi" and T_cold < 9.2:
                suggestions.append("✅ NbTi 超導態運行，熱負載極低")
            elif thermal.get('per_channel_uW', 0) > 200:
                suggestions.append("⚠️ 熱負載偏高，建議使用 NbTi 或縮短長度")
            else:
                suggestions.append("✅ 熱負載在合理範圍")
        
        if via_enabled:
            suggestions.append(f"✅ Via stitching 密度 {via_density}/mm 提供良好屏蔽")
        
        for s in suggestions:
            markdown(f"<div style='margin: 5px 0;'>{s}</div>", unsafe_allow_html=True)
    
    with col_right:
        subheader("📥 匯出結果")
        
        # 產生三視圖
        fig_views = draw_all_views(geo, pitch, length, via_enabled, via_diameter, via_density, n_channels)
        session_state['fig_views'] = fig_views
        pyplot(fig_views, width='stretch')
        
        # 匯出按鈕
        if st.button("📤 匯出 Excel 規格書 (含三視圖)", width='stretch'):
            with st.spinner("正在產生 Excel 檔案..."):
                excel_data = export_to_excel(
                    geo, er, tan_d, Z0,
                    session_state['results'], crosstalk, thermal, 
                    {'損耗': loss} if loss else {},
                    via_info, fig_views,
                    conductor_material, dielectric_material,
                    temp_stage, frequency,
                    pitch, length, sig_width,
                    sig_thickness, dielectric_thickness,
                    n_channels, via_enabled, via_density,
                    via_diameter, T_hot, T_cold
                )
                
                download_button(
                    label="📥 下載 Excel 規格書",
                    data=excel_data,
                    file_name=f"crioflex3_spec_{length}mm_{n_channels}ch_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width='stretch'
                )
                st.success("✅ Excel 檔案生成完成！")

elif menu == '三視圖':
    subheader("📐 三視圖 (前視/側視/上視)")
    
    info("💡 三視圖根據當前設計參數動態生成，顯示傳輸線的幾何結構")
    
    fig_views = draw_all_views(geo, pitch, length, via_enabled, via_diameter, via_density, n_channels)
    session_state['fig_views'] = fig_views
    pyplot(fig_views, width='stretch')
    
    # 顯示尺寸說明
    markdown("""
    <div style="background-color:black; padding:18px; border-radius:10px; margin-top:12px;">
    <h4 style="color:white; margin-top:0;">📐 三視圖說明</h4>
    <table style="width:100%; border-collapse:collapse; font-size:13px;">
    <tr style="background-color:black;">
        <td style="border:1px solid #BDC3C7; padding:8px; width:15%;"><b>視圖</b></td>
        <td style="border:1px solid #BDC3C7; padding:8px; width:25%;"><b>顯示內容</b></td>
        <td style="border:1px solid #BDC3C7; padding:8px; width:60%;"><b>關鍵尺寸</b></td>
    </tr>
    <tr>
        <td style="border:1px solid #BDC3C7; padding:8px;">前視圖</td>
        <td style="border:1px solid #BDC3C7; padding:8px;">YZ平面 - 橫截面</td>
        <td style="border:1px solid #BDC3C7; padding:8px;">層結構: GND-Polyimide-Signal-Polyimide-GND, 顯示 w, h, t, pitch</td>
    </tr>
    <tr>
        <td style="border:1px solid #BDC3C7; padding:8px;">側視圖</td>
        <td style="border:1px solid #BDC3C7; padding:8px;">XZ平面 - 長度方向</td>
        <td style="border:1px solid #BDC3C7; padding:8px;">顯示總長度 L 及各層連續結構</td>
    </tr>
    <tr>
        <td style="border:1px solid #BDC3C7; padding:8px;">上視圖</td>
        <td style="border:1px solid #BDC3C7; padding:8px;">XY平面 - 通道佈線</td>
        <td style="border:1px solid #BDC3C7; padding:8px;">信號線 (S) 與 GND 分隔條排列</td>
    </tr>
    </table>
    </div>
    """, unsafe_allow_html=True)

elif menu == '推導公式':
    subheader("📐 串擾推導公式與計算過程")
    
    formula_tab1, formula_tab2 = tabs(["📖 完整推導", "🔢 當前參數逐步計算"])
    
    with formula_tab1:
        markdown(render_formula_section())
    
    with formula_tab2:
        calc_md, calc_vals = show_formula_calculation(geo, er, frequency * 1e9)
        markdown(calc_md)
        
        # 顯示計算結果摘要表
        subheader("計算結果摘要")
        result_df = {
            "參數": [
                "單位長度自電容 Cs",
                "單位長度互電容 Cm",
                "單位長度自電感 Ls",
                "單位長度互電感 Lm",
                "電容耦合係數 kc",
                "電感耦合係數 kL",
                "綜合耦合係數 k",
                "相位常數 β",
                "電長度 θ",
                "近端串擾 NEXT",
                "遠端串擾 FEXT"
            ],
            "數值": [
                f"{calc_vals['Cs']:.4e} F/m",
                f"{calc_vals['Cm']:.4e} F/m",
                f"{calc_vals['Ls']:.4e} H/m",
                f"{calc_vals['Lm']:.4e} H/m",
                f"{calc_vals['kc']:.6f}",
                f"{calc_vals['kL']:.6f}",
                f"{calc_vals['k']:.6f}",
                f"{calc_vals['beta']:.4e} rad/m",
                f"{calc_vals['theta']:.4f}",
                f"{calc_vals['NEXT_db']:.2f} dB",
                f"{calc_vals['FEXT_db']:.2f} dB"
            ]
        }
        table(result_df)

# 側邊欄底部資訊
with sidebar:
    #st.sidebar.markdown("---")
    markdown("**技術參數基準 (Delft Circuits Cri/oFlex3):**")
    markdown("""
    - 通道數: 8 channels/flex
    - 厚度: 0.3 mm
    - Pitch: 2 mm
    - 材料: Polyimide + Ag/NbTi
    - 線型: Stripline (G-S-G)
    - 阻抗: 50 Ω
    - 頻率: DC ~ 18 GHz
    - 彎曲半徑: 5 mm
    - 長度: 200 ~ 1000 mm
    """)
    markdown('<div class="sub-header">🔬 Cri/oFlex3 柔性傳輸線規格計算器 VI</div>', unsafe_allow_html=True)
    markdown('<div class="sub-header">NbTi/Ag + Polyimide 多層膜 Stripline 串擾與熱負載分析 (v6.0)</div>', unsafe_allow_html=True)
    #"""
    #Cri/oFlex3 柔性傳輸線規格計算器 VI
    #=====================================
    #針對 NbTi/Ag + Polyimide 多層膜柔性 stripline 的串擾與熱負載計算工具

    #新增功能:
    #- 三視圖 (前視/側視/上視) 動態產生
    #- Excel 匯出 (含三視圖、公式推導、單位)
    #"""
