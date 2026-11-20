from streamlit import checkbox, columns, download_button, markdown, metric, pyplot, radio, set_page_config, sidebar, slider, subheader, table, tabs, session_state, json as stJSON, info, plotly_chart
from matplotlib.pyplot import Circle, Polygon, Rectangle, subplots, tight_layout
from pandas import DataFrame, json_normalize
from numpy import exp, linspace, log, log10, mean, pi, sqrt
from json import dumps as jsnDumps
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Dict, List, Tuple
from fontUtil2 import 配置中文
配置中文()
#import json

# ============================================================
# 物理常數與材料參數
# ============================================================

MU_0 = 4 * pi * 1e-7  # H/m 真空磁導率

EPS_0 = 8.854e-12  # F/m 真空介電常數

K_B = 1.381e-23  # J/K 玻爾茲曼常數

# 材料熱導率參數 (W/m·K)
# 基於文獻數據擬合 Kapton
MATERIAL_THERMAL = {
    "Ag": {
        "type": "wiedemann_franz",
        "sigma": 6.3e7,      # S/m 電導率
        "L0": 2.45e-8       # W·Ω/K² 洛倫茲數 (Wiedemann-Franz law)
    },
    "NbTi": {
        "type": "superconducting",
        "Tc": 9.2,     # K
        "normal_k": 10, # 正常態熱導率
        "sc_k": 0.001   # 超導態 (極低)
    },
    "Polyimide": {
        "type": "power_law",
        "A": 0.155,
        "alpha": 1.0
    },
    "Cu": {
        "type": "wiedemann_franz",
        "sigma": 5.8e7,      # S/m 電導率
        "L0": 2.45e-8       # W·Ω/K² 洛倫茲數
    }
}

# 介電常數與損耗 Kapton
DIELECTRIC = {
    "Polyimide": {
        "εr": 3.4,
        "tan_delta_rt": .003,
        "tan_delta_4K": 3e-5,   # 文獻值 ~2.2e-5 @ 20mK
        "tan_delta_20mK": 2.2e-5
    }
}

# ============================================================
# 數據類別定義
# ============================================================


# ============================================================
# 功能 1: 介電質多層膜 Stripline 物理尺寸動態示意圖
# ============================================================

def draw_stripline_cross_section(geo: StriplineGeometry, pitch: float, 
                                  via_enabled: bool, via_diameter: float, 
                                  via_density: float, n_channels: int):
    """
    繪製 Stripline 橫截面動態示意圖 (改良版)
    
    結構層次 (由下到上):
    ┌─────────────────────────────────────────┐  Layer 5: 上接地層 (Top GND)
    │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   │  t = 導體厚度
    ├─────────────────────────────────────────┤  Layer 4: 上介電層 (Polyimide)
    │                                         │  h = 介電厚度, εr=3.4
    │     ═══════     ═══════     ═══════     │  Layer 3: 信號層 (Signal) + GND分隔
    │     S1    GND   S2    GND   S3          │  w = 線寬, pitch = 通道間距
    │                                         │  t = 導體厚度
    ├─────────────────────────────────────────┤  Layer 2: 下介電層 (Polyimide)
    │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   │  h = 介電厚度, εr=3.4
    └─────────────────────────────────────────┘  Layer 1: 下接地層 (Bottom GND)
                                                      t = 導體厚度
    """
    fig, ax = subplots(figsize=(16, 8))

    # 尺寸轉換 (mm)
    w = geo.w  # 信號線寬 (mm)
    h = geo.h  # 單層介電厚 (mm)
    t = geo.t / 1000  # μm -> mm (導體厚)
    s = pitch  # 通道間距 (mm)
    total_h = 2 * h + 3 * t  # 總厚度

    # 繪圖區域設定
    n_draw = min(n_channels, 6)  # 最多畫 6 個通道
    total_width = s * (n_draw + 0.5)
    margin = s * 0.4
    right_label_x = total_width + margin * 1.2

    ax.set_xlim(-margin * 1.5, right_label_x + 0.8)
    ax.set_ylim(-margin * 1.5, total_h + margin * 1.2)
    ax.set_aspect('equal')
    ax.axis('off')

    # 顏色定義 (更鮮明)
    colors = {
        'polyimide': '#F5E6C8',      # 淡米黃 (Polyimide)
        'polyimide_edge': '#D4A574', # 介電層邊框色
        'ag_nbti': '#C9A227',        # 金色 (Ag/NbTi 導體)
        'ag_edge': '#8B6914',        # 導體邊框色
        'via': '#A0522D',            # 赭色 (Via)
        'text': '#2C3E50',           # 深藍灰 (文字)
        'label_bg': '#ECF0F1',       # 淺灰 (標註背景)
        'dimension': '#E74C3C',      # 紅色 (尺寸線)
        'arrow': '#2980B9',          # 深藍 (箭頭)
        'layer_line': '#7F8C8D'      # 灰色 (層次線)
    }

    # ── 繪製五層結構 ─────────────────────────────────────
    
    # Layer 1: 下接地層 (Bottom GND)
    y_bot_gnd = -t
    gnd_bottom = Rectangle((-margin/2, y_bot_gnd), total_width + margin, t, 
                           facecolor=colors['ag_nbti'], edgecolor=colors['ag_edge'], linewidth=2)
    ax.add_patch(gnd_bottom)
    ax.text(total_width/2, y_bot_gnd + t/2, 'Bottom GND', 
            ha='center', va='center', fontsize=10, color='white', fontweight='bold')
    # 右側標註
    ax.text(right_label_x, y_bot_gnd + t/2, 
            f'Layer 1: Bottom GND\n  Material: Ag/NbTi\n  Thickness t = {t*1000:.0f} μm',
            ha='left', va='center', fontsize=9, color=colors['text'],
            bbox=dict(boxstyle='round,pad=0.4', facecolor=colors['label_bg'], 
                     edgecolor=colors['ag_edge'], linewidth=1.5, alpha=0.95))

    # Layer 2: 下介電層
    y_bot_die = 0
    dielectric_bottom = Rectangle((-margin/2, y_bot_die), total_width + margin, h, 
                                 facecolor=colors['polyimide'], edgecolor=colors['polyimide_edge'], 
                                 linewidth=2, alpha=0.85)
    ax.add_patch(dielectric_bottom)
    ax.text(-margin/2 + 0.15, y_bot_die + h/2, 'Polyimide\nεr = 3.4\ntanδ = 3×10⁻⁵', 
            ha='left', va='center', fontsize=9, color=colors['text'], fontweight='bold')
    # 右側標註
    ax.text(right_label_x, y_bot_die + h/2, 
            f'Layer 2: Lower Dielectric\n  Material: Polyimide\n  Thickness h = {h*1000:.0f} μm',
            ha='left', va='center', fontsize=9, color=colors['text'],
            bbox=dict(boxstyle='round,pad=0.4', facecolor=colors['label_bg'], 
                     edgecolor=colors['polyimide_edge'], linewidth=1.5, alpha=0.95))

    # Layer 3: 信號層 + 接地分隔 (G-S-G)
    y_sig = h + t - t/2  # 信號層中心 y
    for i in range(n_draw):
        x_center = s * (i + 0.5)
        # 信號線
        sig = Rectangle((x_center - w/2, y_sig - t/2), w, t, 
                        facecolor=colors['ag_nbti'], edgecolor=colors['ag_edge'], linewidth=2)
        ax.add_patch(sig)
        ax.text(x_center, y_sig, f'S{i+1}', ha='center', va='center', 
                fontsize=9, color='white', fontweight='bold')

        # 接地分隔 (G-S-G)
        if i < n_draw - 1:
            gnd_sep_x = x_center + s/2
            gnd_w = w * 0.3
            gnd_sep = Rectangle((gnd_sep_x - gnd_w/2, y_sig - t/2), gnd_w, t,
                                facecolor='#D4AF37', edgecolor=colors['ag_edge'], linewidth=1.5)
            ax.add_patch(gnd_sep)
            ax.text(gnd_sep_x, y_sig, 'GND', ha='center', va='center',
                    fontsize=7, color='white', fontweight='bold')

    # 右側標註 (對齊信號層)
    ax.text(right_label_x, y_sig, 
            f'Layer 3: Signal Layer (G-S-G)\n  Signal: Ag/NbTi, w = {w*1000:.0f} μm\n  GND strip: w = {w*0.3*1000:.0f} μm\n  Pitch = {s:.1f} mm',
            ha='left', va='center', fontsize=9, color=colors['text'],
            bbox=dict(boxstyle='round,pad=0.4', facecolor=colors['label_bg'], 
                     edgecolor=colors['ag_edge'], linewidth=1.5, alpha=0.95))

    # Layer 4: 上介電層
    y_top_die = h + t
    dielectric_top = Rectangle((-margin/2, y_top_die), total_width + margin, h, 
                               facecolor=colors['polyimide'], edgecolor=colors['polyimide_edge'], 
                               linewidth=2, alpha=0.85)
    ax.add_patch(dielectric_top)
    ax.text(-margin/2 + 0.15, y_top_die + h/2, 'Polyimide\nεr = 3.4', 
            ha='left', va='center', fontsize=9, color=colors['text'], fontweight='bold')
    # 右側標註
    ax.text(right_label_x, y_top_die + h/2, 
            f'Layer 4: Upper Dielectric\n  Material: Polyimide\n  Thickness h = {h*1000:.0f} μm',
            ha='left', va='center', fontsize=9, color=colors['text'],
            bbox=dict(boxstyle='round,pad=0.4', facecolor=colors['label_bg'], 
                     edgecolor=colors['polyimide_edge'], linewidth=1.5, alpha=0.95))

    # Layer 5: 上接地層 (Top GND)
    y_top_gnd = 2*h + 2*t
    gnd_top = Rectangle((-margin/2, y_top_gnd), total_width + margin, t, 
                        facecolor=colors['ag_nbti'], edgecolor=colors['ag_edge'], linewidth=2)
    ax.add_patch(gnd_top)
    ax.text(total_width/2, y_top_gnd + t/2, 'Top GND', 
            ha='center', va='center', fontsize=10, color='white', fontweight='bold')
    # 右側標註
    ax.text(right_label_x, y_top_gnd + t/2, 
            f'Layer 5: Top GND\n  Material: Ag/NbTi\n  Thickness t = {t*1000:.0f} μm',
            ha='left', va='center', fontsize=9, color=colors['text'],
            bbox=dict(boxstyle='round,pad=0.4', facecolor=colors['label_bg'], 
                     edgecolor=colors['ag_edge'], linewidth=1.5, alpha=0.95))

    # ── 水平層次結構線 ─────────────────────────────────────
    # 畫出右側連接線標示層次
    layer_y = [y_bot_gnd, y_bot_die, y_sig - t/2, y_sig + t/2, y_top_die, y_top_gnd + t]
    for y in layer_y:
        ax.plot([total_width + margin*0.3, right_label_x - 0.1], [y, y], 
                color=colors['layer_line'], linewidth=0.8, linestyle='--', alpha=0.6)

    # ── Via Stitching (如果啟用) ─────────────────────────────
    if via_enabled:
        via_spacing = 1.0 / via_density  # mm
        n_vias_x = int(total_width / via_spacing) + 1
        via_r = via_diameter / 2000  # μm -> mm (半徑)

        for i in range(n_vias_x):
            x_via = i * via_spacing
            if x_via > total_width:
                break
            # 上層 Via (穿透 Top GND)
            via_top = Circle((x_via, y_top_gnd + t/2), via_r, 
                             facecolor=colors['via'], edgecolor='black', linewidth=1.5)
            ax.add_patch(via_top)
            # 下層 Via (穿透 Bottom GND)
            via_bottom = Circle((x_via, y_bot_gnd + t/2), via_r,
                                facecolor=colors['via'], edgecolor='black', linewidth=1.5)
            ax.add_patch(via_bottom)
            # 連接線 (穿過介電層)
            ax.plot([x_via, x_via], [y_bot_gnd + t/2 + via_r, y_top_gnd + t/2 - via_r], 
                    color=colors['via'], linewidth=2.5, linestyle='-', alpha=0.8)
            # 上延伸線 (超出 Top GND)
            ax.plot([x_via, x_via], [y_top_gnd + t/2 + via_r, y_top_gnd + t/2 + via_r + 0.05], 
                    color=colors['via'], linewidth=1.5, linestyle='--', alpha=0.5)
            # 下延伸線 (超出 Bottom GND)
            ax.plot([x_via, x_via], [y_bot_gnd + t/2 - via_r - 0.05, y_bot_gnd + t/2 - via_r], 
                    color=colors['via'], linewidth=1.5, linestyle='--', alpha=0.5)

        # Via 說明框
        ax.text(right_label_x, (y_top_gnd + y_bot_gnd + t)/2, 
                f'Via Stitching\n  Ø = {via_diameter} μm\n  Density = {via_density}/mm\n  Spacing = {via_spacing:.1f} mm\n  Function: GND connection\n  & lateral shielding',
                ha='left', va='center', fontsize=9, color=colors['via'],
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFF5E6', 
                         edgecolor=colors['via'], linewidth=2, alpha=0.95))

    # ── 尺寸標註 ─────────────────────────────────────────────
    
    # 導體厚度 t 標註 (在右側，用虛線引導)
    t_label_x = total_width + margin * 0.5
    ax.annotate('', xy=(t_label_x, y_top_gnd), xytext=(t_label_x, y_top_gnd + t),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text(t_label_x + 0.1, y_top_gnd + t/2, f't\n= {t*1000:.0f} μm', 
            ha='left', va='center', fontsize=9, color=colors['dimension'], fontweight='bold')

    # 介電厚度 h 標註 (右側上介電層)
    ax.annotate('', xy=(t_label_x, y_top_die), xytext=(t_label_x, y_top_gnd),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text(t_label_x + 0.1, (y_top_die + y_top_gnd)/2, f'h\n= {h*1000:.0f} μm', 
            ha='left', va='center', fontsize=9, color=colors['dimension'], fontweight='bold')

    # 介電厚度 h 標註 (右側下介電層)
    ax.annotate('', xy=(t_label_x, y_bot_die), xytext=(t_label_x, y_top_die - t),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text(t_label_x + 0.1, (y_bot_die + y_top_die - t)/2, f'h\n= {h*1000:.0f} μm', 
            ha='left', va='center', fontsize=9, color=colors['dimension'], fontweight='bold')

    # 信號線寬度 w 標註 (在第一個通道下方)
    arrow_y_w = y_bot_gnd - margin * 0.3
    ax.annotate('', xy=(s*0.5 - w/2, arrow_y_w), xytext=(s*0.5 + w/2, arrow_y_w),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=2))
    ax.text(s*0.5, arrow_y_w - 0.15, f'w = {w*1000:.0f} μm (Signal width)', 
            ha='center', va='top', fontsize=10, color=colors['dimension'], fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8, edgecolor=colors['dimension']))

    # Pitch s 標註 (在 w 下方)
    arrow_y_s = arrow_y_w - margin * 0.6
    ax.annotate('', xy=(s*0.5, arrow_y_s), xytext=(s*1.5, arrow_y_s),
                arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=2))
    ax.text(s, arrow_y_s - 0.15, f'pitch = {s:.1f} mm (Center-to-center)', 
            ha='center', va='top', fontsize=10, color=colors['arrow'], fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8, edgecolor=colors['arrow']))

    # 總厚度標註 (最左側)
    ax.annotate('', xy=(-margin*0.6, y_bot_gnd), xytext=(-margin*0.6, y_top_gnd + t),
                arrowprops=dict(arrowstyle='<->', color='#27AE60', lw=2))
    ax.text(-margin*0.8, (y_bot_gnd + y_top_gnd + t)/2, 
            f'Total\n= {total_h*1000:.0f} μm\n(5 layers)', 
            ha='right', va='center', fontsize=10, color='#27AE60', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#E8F8F5', alpha=0.9, edgecolor='#27AE60'))

    # ── 標題 ───────────────────────────────────────────────
    ax.set_title(f'Cri/oFlex3 Stripline Cross-Section  (五層 G-S-G 結構)\n'
                 f'{n_channels} channels  |  w={w*1000:.0f}μm  h={h*1000:.0f}μm  t={t*1000:.0f}μm  pitch={s:.1f}mm  |  εr=3.4', 
                 fontsize=13, fontweight='bold', pad=20, color=colors['text'])

    # ── 圖例 (增強版) ───────────────────────────────────────
    legend_elements = [
        Rectangle((0,0),1,1, facecolor=colors['ag_nbti'], edgecolor=colors['ag_edge'], linewidth=2, label='Layer 1/3/5: Ag/NbTi Conductor'),
        Rectangle((0,0),1,1, facecolor=colors['polyimide'], edgecolor=colors['polyimide_edge'], linewidth=2, alpha=0.85, label='Layer 2/4: Polyimide (εr=3.4, tanδ=3×10⁻⁵)'),
        Circle((0,0), 0.1, facecolor=colors['via'], edgecolor='black', linewidth=1.5, label='Via: GND Stitching (Cu-filled)')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9, framealpha=0.95, 
              edgecolor='gray', fancybox=True)

    tight_layout()
    return fig


def draw_stripline_3d_schematic(geo: StriplineGeometry, pitch: float, length: float, n_channels: int):
    """
    繪製 Stripline 3D 立體透視示意圖 (等角投影)
    展示完整多層膜結構的立體空間關係，包含介電層、導體層與 Via
    """
    fig, ax = subplots(figsize=(16, 8))

    w = geo.w  # mm
    h = geo.h  # mm
    t = geo.t / 1000  # μm -> mm
    L = length / 8  # 縮放顯示長度
    s = pitch
    n_draw = min(n_channels, 4)

    # 等角投影參數
    dx = 0.35 * L  # 深度在 x 方向的偏移
    dy = 0.20 * L  # 深度在 y 方向的偏移

    # 顏色定義
    c_poly = '#E8DCC8'        # 淡棕色 (Polyimide)
    c_poly_dark = '#C4B49A'   # Polyimide 頂面/側面
    c_ag = '#B8860B'          # 暗金色 (Ag/NbTi)
    c_ag_top = '#DAA520'      # 亮金色
    c_ag_side = '#8B6914'     # 側面
    c_via = '#8B4513'         # Via
    c_text = '#2C3E50'
    c_dim = '#E74C3C'
    c_arrow = '#3498DB'

    def draw_block(x, y, w_blk, h_blk, d, face_c, edge_c='black', top_c=None, alpha=1.0, zorder=2):
        """繪製 3D 塊狀體：前立面 + 頂面 + 右側面"""
        if top_c is None:
            top_c = face_c
        # 前立面
        rect = Rectangle((x, y), w_blk, h_blk,
                        facecolor=face_c, edgecolor=edge_c,
                        linewidth=1.2, alpha=alpha, zorder=zorder)
        ax.add_patch(rect)
        if d <= 0:
            return
        # 頂面
        top = Polygon([
            [x, y + h_blk],
            [x + w_blk, y + h_blk],
            [x + w_blk + dx, y + h_blk + dy],
            [x + dx, y + h_blk + dy]
        ], facecolor=top_c, edgecolor=edge_c, linewidth=0.9, alpha=alpha, zorder=zorder-1)
        ax.add_patch(top)
        # 右側面
        side = Polygon([
            [x + w_blk, y],
            [x + w_blk, y + h_blk],
            [x + w_blk + dx, y + h_blk + dy],
            [x + w_blk + dx, y + dy]
        ], facecolor=face_c, edgecolor=edge_c, linewidth=0.8, alpha=alpha*0.75, zorder=zorder-1)
        ax.add_patch(side)
        # 深度輪廓線
        ax.plot([x, x + dx], [y, y + dy], color=edge_c, linewidth=0.6, alpha=0.5, zorder=zorder-1)
        ax.plot([x + w_blk, x + w_blk + dx], [y, y + dy],
                color=edge_c, linewidth=0.6, alpha=0.5, zorder=zorder-1)

    total_w = s * n_draw
    margin = s * 0.3

    # 層次 z 位置 (從下往上)
    z0 = 0.0          # 下 GND 底
    z1 = t            # 下介電底
    z2 = t + h        # 信號底
    z3 = t + h + t    # 上介電底
    z4 = t + h + t + h  # 上 GND 底
    z5 = t + h + t + h + t  # 總高度

    # 1. 下接地層 (全寬)
    draw_block(-margin/2, z0, total_w + margin, t, L,
               c_ag, 'black', c_ag_top, alpha=0.95, zorder=2)
    ax.text(total_w/2, z0 + t/2, 'Bottom GND', ha='center', va='center',
            fontsize=8, color='white', fontweight='bold', zorder=3)

    # 2. 下介電層 (全寬)
    draw_block(-margin/2, z1, total_w + margin, h, L,
               c_poly, 'black', c_poly_dark, alpha=0.55, zorder=2)
    ax.text(-margin/2 - 0.15, z1 + h/2, 'Polyimide\nεr=3.4',
            ha='right', va='center', fontsize=8, color=c_text, zorder=3)

    # 3. 信號層 + 接地分隔
    for i in range(n_draw):
        x_c = s * (i + 0.5)
        # 信號線
        draw_block(x_c - w/2, z2, w, t, L,
                   c_ag, 'black', c_ag_top, alpha=0.95, zorder=3)
        ax.text(x_c, z2 + t/2, f'S{i+1}', ha='center', va='center',
                fontsize=8, color='white', fontweight='bold', zorder=4)
        # GND 分隔
        if i < n_draw - 1:
            g_x = x_c + s/2
            g_w = w * 0.3
            draw_block(g_x - g_w/2, z2, g_w, t, L,
                       '#D4AF37', 'black', '#F0E68C', alpha=0.9, zorder=3)
            ax.text(g_x, z2 + t/2, 'G', ha='center', va='center',
                    fontsize=7, color='white', zorder=4)

    # 4. 上介電層 (全寬)
    draw_block(-margin/2, z3, total_w + margin, h, L,
               c_poly, 'black', c_poly_dark, alpha=0.55, zorder=2)
    ax.text(-margin/2 - 0.15, z3 + h/2, 'Polyimide\nεr=3.4',
            ha='right', va='center', fontsize=8, color=c_text, zorder=3)

    # 5. 上接地層 (全寬)
    draw_block(-margin/2, z4, total_w + margin, t, L,
               c_ag, 'black', c_ag_top, alpha=0.95, zorder=2)
    ax.text(total_w/2, z4 + t/2, 'Top GND', ha='center', va='center',
            fontsize=8, color='white', fontweight='bold', zorder=3)

    # 6. Via Stitching (示意)
    via_r = 0.04  # mm
    via_spacing = 2.0  # mm
    n_vias = int(total_w / via_spacing) + 1
    for i in range(n_vias):
        x_v = i * via_spacing
        if x_v > total_w:
            break
        # 前立面 Via
        v = Circle((x_v, z0 + t/2), via_r,
                   facecolor=c_via, edgecolor='black', linewidth=1, zorder=5)
        ax.add_patch(v)
        # 深度方向 Via
        v_d = Circle((x_v + dx, z0 + t/2 + dy), via_r,
                     facecolor=c_via, edgecolor='black', linewidth=1, zorder=5)
        ax.add_patch(v_d)
        # 連接線
        ax.plot([x_v, x_v + dx], [z0 + t/2, z0 + t/2 + dy],
                color=c_via, linewidth=2, alpha=0.7, zorder=4)
        # 垂直連接 (Top GND 到 Bottom GND)
        ax.plot([x_v, x_v], [z0 + t/2, z4 + t/2],
                color=c_via, linewidth=1.5, linestyle='--', alpha=0.4, zorder=4)

    # 尺寸標註
    # 總厚度
    ax.annotate('', xy=(-margin * 0.9, z0), xytext=(-margin * 0.9, z5),
                arrowprops=dict(arrowstyle='<->', color=c_dim, lw=1.5))
    ax.text(-margin * 1.1, z5/2, f'total\n{z5*1000:.0f} μm',
            ha='right', va='center', fontsize=9, color=c_dim, fontweight='bold')

    # 長度標註
    ax.annotate('', xy=(0, -margin * 0.7), xytext=(total_w + dx, -margin * 0.7 + dy),
                arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=1.5))
    ax.text(total_w/2 + dx/2, -margin * 0.9 + dy/2,
            f'L = {length} mm', ha='center', va='top',
            fontsize=10, color=c_arrow, fontweight='bold')

    # 圖例
    legend_elements = [
        Rectangle((0,0),1,1, facecolor=c_ag, edgecolor='black', label='Ag/NbTi Conductor'),
        Rectangle((0,0),1,1, facecolor=c_poly, edgecolor='black', alpha=0.55, label='Polyimide (εr=3.4)'),
        Circle((0,0), 0.1, facecolor=c_via, label='GND Via')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9, framealpha=0.9)

    ax.set_title(f'Cri/oFlex3 Stripline 3D Perspective View\n({n_channels} ch, G-S-G, L={length}mm, εr=3.4)',
                 fontsize=13, fontweight='bold', pad=20)

    ax.set_xlim(-margin * 2.5, total_w + dx + margin)
    ax.set_ylim(-margin * 1.5, z5 + dy + margin)
    ax.set_aspect('equal')
    ax.axis('off')

    tight_layout()
    return fig




# ============================================================
# 功能 2: 串擾推導公式展示
# ============================================================

def show_crosstalk_derivation(geo: StriplineGeometry, er: float, f: float):
    """
    展示完整的串擾推導公式與計算過程
    """
    w = geo.w / 1000  # mm -> m
    s = geo.s / 1000   # mm -> m  
    h = geo.h / 1000   # mm -> m
    t = geo.t / 1e6    # μm -> m
    L = geo.L / 1000   # mm -> m

    eps = er * EPS_0

    # 計算實際數值
    # 1. 單位長度自電容 Cs
    # 平行板近似 (對稱 stripline, 上下各一接地層)
    Cs = eps * w / h  # F/m

    # 2. 單位長度互電容 Cm
    # 基於平行線耦合模型 (經驗公式)
    Cm = eps * w / s * exp(-pi * s / (2 * h))

    # 3. 單位長度自電感 Ls
    Ls = MU_0 * h / w

    # 4. 單位長度互電感 Lm
    Lm = MU_0 * h / (2 * pi) * log(1 + 2*h/s)

    # 5. 電容耦合係數
    kc = Cm / (Cs + Cm)

    # 6. 電感耦合係數
    kL = Lm / (Ls + Lm)

    # 7. 綜合耦合係數
    k = 0.5 * (kc + kL)

    # 8. 相位常數
    c = 3e8
    beta = 2 * pi * f * sqrt(er) / c

    # 9. 近端串擾 (NEXT)
    theta = beta * L
    if theta < 1:
        NEXT_linear = k * theta / 2
    else:
        NEXT_linear = k / 2
    近端串擾 = 20 * log10(max(abs(NEXT_linear), 1e-12))

    # 10. 遠端串擾 (FEXT)
    FEXT_linear = k * theta
    遠端串擾 = 20 * log10(max(abs(FEXT_linear), 1e-12))

    return {
        "Cs": Cs,
        "Cm": Cm,
        "Ls": Ls,
        "Lm": Lm,
        "kc": kc,
        "kL": kL,
        "k": k,
        "beta": beta,
        "theta": theta,
        "NEXT_linear": NEXT_linear,
        "近端串擾": 近端串擾,
        "FEXT_linear": FEXT_linear,
        "遠端串擾": 遠端串擾,
        "w_m": w,
        "s_m": s,
        "h_m": h,
        "L_m": L
    }


def render_formula_section():
    """
    渲染完整的公式推導區塊 (Streamlit markdown)
    """
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

    ---

    ### 二、單位長度電容

    #### 2.1 自電容 $C_s$ (Self-Capacitance)

    對於對稱 Stripline (Ground-Signal-Ground)，信號線與上下兩接地層形成平行板電容：

    $$
    C_s = \varepsilon_0 \varepsilon_r \cdot \frac{w}{h}
    $$

    **物理意義**：單位長度信號線對單一接地層的電容。由於上下兩層並聯，總自電容為 $2C_s$。

    ---

    #### 2.2 互電容 $C_m$ (Mutual Capacitance)

    相鄰信號線間的電容耦合，採用經驗衰減模型：

    $$
    C_m = \varepsilon_0 \varepsilon_r \cdot \frac{w}{s} \cdot \exp\left(-\frac{\pi s}{2h}\right)
    $$

    **物理意義**：
    - $\frac{w}{s}$：幾何比例因子
    - $\exp\left(-\frac{\pi s}{2h}\right)$：介電屏蔽衰減項，$s \gg h$ 時快速衰減

    ---

    ### 三、單位長度電感

    #### 3.1 自電感 $L_s$ (Self-Inductance)

    $$
    L_s = \mu_0 \cdot \frac{h}{w}
    $$

    **物理意義**：信號線電流迴路 (Signal → GND) 的單位長度電感。

    ---

    #### 3.2 互電感 $L_m$ (Mutual Inductance)

    基於平行導線互感公式：

    $$
    L_m = \frac{\mu_0}{2\pi} \cdot h \cdot \ln\left(1 + \frac{2h}{s}\right)
    $$

    **物理意義**：相鄰通道電流產生的磁通耦合。

    ---

    ### 四、耦合係數

    #### 4.1 電容耦合係數 $k_c$

    $$
    k_c = \frac{C_m}{C_s + C_m}
    $$

    **物理意義**：互電容佔總電容的比例。$k_c \ll 1$ 為弱耦合條件。

    ---

    #### 4.2 電感耦合係數 $k_L$

    $$
    k_L = \frac{L_m}{L_s + L_m}
    $$

    **物理意義**：互電感佔總電感的比例。

    ---

    #### 4.3 綜合耦合係數 $k$

    對於對稱 Stripline，綜合耦合係數為電容與電感耦合的算術平均：

    $$
    k = \frac{1}{2}(k_c + k_L)
    $$

    ---

    ### 五、傳播參數

    #### 5.1 相位常數 $\beta$

    $$
    \beta = \frac{2\pi f \sqrt{\varepsilon_r}}{c} = \omega \sqrt{\varepsilon_r} / c
    $$

    其中 $c = 3 \times 10^8$ m/s 為光速。

    ---

    #### 5.2 電長度 $\theta$

    $$
    \theta = \beta \cdot L = \frac{2\pi f L \sqrt{\varepsilon_r}}{c}
    $$

    **判斷條件**：
    - $\theta \ll 1$：電短線，串擾與長度成正比
    - $\theta \approx 1$：需考慮分佈效應
    - $\theta \gg 1$：飽和區，串擾趨近耦合係數

    ---

    ### 六、串擾公式

    #### 6.1 近端串擾 (NEXT - Near-End Crosstalk)

    在弱耦合條件下 ($k \ll 1$)：

    $$
    \text{NEXT}_{linear} = \begin{cases}
    \displaystyle\frac{k \cdot \theta}{2}, & \theta < 1 \\
    \displaystyle\frac{k}{2}, & \theta \geq 1
    \end{cases}
    $$

    轉換為 dB：

    $$
    \text{NEXT}_{dB} = 20 \log_{10}(\text{NEXT}_{linear})
    $$

    **物理意義**：
    - 近端串擾為後向傳播的干擾波
    - 在電短線區 ($\theta < 1$)，與電長度 $\theta$ 成正比
    - 在電長線區飽和於 $k/2$

    ---

    #### 6.2 遠端串擾 (FEXT - Far-End Crosstalk)

    $$
    \text{FEXT}_{linear} = k \cdot \theta = k \cdot \frac{2\pi f L \sqrt{\varepsilon_r}}{c}
    $$

    轉換為 dB：

    $$
    \text{FEXT}_{dB} = 20 \log_{10}(\text{FEXT}_{linear})
    $$

    **物理意義**：
    - 遠端串擾為前向傳播的干擾波
    - 與電長度 $\theta$ 始終成正比
    - 高頻長線時 FEXT 通常大於 NEXT

    ---

    ### 七、Via Stitching 屏蔽改善

    接地 Via 提供額外的橫向接地路徑，改善屏蔽效能：

    $$
    \Delta S_{via} = 20 \log_{10}\left(1 + 0.5 \cdot \rho_{via} \cdot s\right)
    $$

    其中 $\rho_{via}$ 為 Via 密度 (個/mm)。

    改善後串擾：

    $$
    \text{NEXT}'_{dB} = \text{NEXT}_{dB} - \Delta S_{via}
    $$

    ---

    ### 八、設計準則

    | 指標 | 目標值 | 改善方法 |
    |------|--------|----------|
    | NEXT | < -40 dB | 增大 pitch、增加 via 密度、減小 $h$ |
    | FEXT | < -40 dB | 縮短線長、降低頻率、使用低 $\varepsilon_r$ 材料 |
    | $k$ | < 0.01 | $s > 3h$ 為經驗法則 |
    | $Z_0$ | 50 ± 5 Ω | 調整 $w/h$ 比例 |

    ---
    """
    return formula_md


def show_formula_calculation(geo: StriplineGeometry, er: float, f: float):
    """
    顯示當前參數下的逐步計算過程
    """
    calc = show_crosstalk_derivation(geo, er, f)

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
    k_c = \frac{{C_m}}{{C_s + C_m}} = \frac{{{calc['Cm']:.4e}}}{{{calc['Cs']:.4e} + {calc['Cm']:.4e}}} = {calc['kc']:.6f}
    $$

    $$
    k_L = \frac{{L_m}}{{L_s + L_m}} = \frac{{{calc['Lm']:.4e}}}{{{calc['Ls']:.4e} + {calc['Lm']:.4e}}} = {calc['kL']:.6f}
    $$

    $$
    k = \frac{{1}}{{2}}(k_c + k_L) = {calc['k']:.6f}
    $$

    **Step 6: 相位常數與電長度**

    $$
    \beta = \frac{{2\pi f \sqrt{{\varepsilon_r}}}}{{c}} = \frac{{2\pi \times {f:.3e} \times \sqrt{{{er}}}}}{{3 \times 10^8}} = {calc['beta']:.4e} \text{{ rad/m}}
    $$

    $$
    \theta = \beta L = {calc['beta']:.4e} \times {calc['L_m']:.4e} = {calc['theta']:.4f}
    $$

    **Step 7: 串擾計算**

    {"$\theta < 1$ (電短線區)，使用線性公式：" if calc['theta'] < 1 else "$\theta \geq 1$ (電長線區)，使用飽和公式："}

    $$
    \text{{NEXT}}_{{linear}} = {calc['NEXT_linear']:.6e} \quad \Rightarrow \quad \text{{NEXT}}_{{dB}} = 20\log_{{10}}({calc['NEXT_linear']:.6e}) = \mathbf{{{calc['近端串擾']:.2f} \text{{ dB}}}}
    $$

    $$
    \text{{FEXT}}_{{linear}} = {calc['FEXT_linear']:.6e} \quad \Rightarrow \quad \text{{FEXT}}_{{dB}} = 20\log_{{10}}({calc['FEXT_linear']:.6e}) = \mathbf{{{calc['遠端串擾']:.2f} \text{{ dB}}}}
    $$

    ---

    **驗證：**
    - $k \ll 1$？ {'✅ 是' if calc['k'] < 0.1 else '⚠️ 否，耦合過強'}
    - NEXT < -40 dB？ {'✅ 達標' if calc['近端串擾'] < -40 else '⚠️ 未達標'}
    - FEXT < -40 dB？ {'✅ 達標' if calc['遠端串擾'] < -40 else '⚠️ 未達標'}
    """

    return calc_md, calc


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

def calc_stripline_impedance(geo: StriplineGeometry, er: float) -> float:
    """
    計算 Stripline 特性阻抗 (Wadell 公式)
    Z0 = (30π / sqrt(er)) * (b / We)
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

    Z0 = (30 * pi / sqrt(er)) * (b / We)
    return Z0

def calc_crosstalk_stripline(geo: StriplineGeometry, er: float, f: float) -> Dict[str, float]:
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
    eps = er * EPS_0

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
    beta = 2 * pi * f * sqrt(er) / c

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
        "近端串擾": NEXT_db,
        "遠端串擾": FEXT_db,
        "耦合強度": k,
        "電容": Cm,
        "電感": Lm,
        "相位常數": beta
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

    elif props["type"] == "wiedemann_franz":
        # Wiedemann-Franz 定律: k = L0 * sigma * T
        # 適用於純金屬 (Ag, Cu) 在 T < 20K 的電子導熱主導區
        # 避免 low_temp power_law 在 mK 段嚴重低估的問題
        return props["L0"] * props["sigma"] * T

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

    狀態.code(materials)
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

def calc_insertion_loss(geo: StriplineGeometry, er: float, tan_delta: float, 
                        f: float, material: str = "Ag", T: float = 300.0) -> float:
    """
    計算插入損耗 (dB)

    包含:
    1. 導體損耗 (skin effect / superconducting surface resistance)
    2. 介電損耗
    
    修正 (2025-06): 
    - NbTi 超導態使用 Mattis-Bardeen 簡化模型 + Delft 官方數據校準
    - Ag/Cu 低溫使用 Wiedemann-Franz 熱導率
    - 使用實際計算特性阻抗而非固定 50Ω
    """
    w = geo.w / 1000  # mm -> m
    t = geo.t / 1e6   # μm -> m
    L = geo.L / 1000  # mm -> m
    h = geo.h / 1000  # mm -> m

    # 導體電導率 (正常態)
    sigma_n = {"Ag": 6.3e7, "NbTi": 1e6, "Cu": 5.8e7}.get(material, 6.3e7)

    # 表面電阻計算
    Tc = 9.2  # NbTi 臨界溫度
    if material == "NbTi" and T < Tc:
        # ============================================================
        # NbTi 超導表面電阻模型 (Mattis-Bardeen 簡化 + 官方數據校準)
        # ============================================================
        # Delft 官方數據: NbTi @ 6GHz, 4K → 1.5 dB/m (總損耗, 含連接器)
        # 純傳輸線段約 1.0-1.2 dB/m; 反推 Rs ≈ 0.0010-0.0013 Ω
        # 這裡校準到 Rs_ref = 0.0012 Ω @ 6GHz, 4K (純 stripline)
        # 
        # BCS 理論極限 (ħω << Δ): Rs ∝ ω²
        # 溫度依賴 (T < 0.5Tc): Rs ∝ (T/Tc)^1.5 (準粒子熱激發)
        # ============================================================
        Rs_ref = 0.0012       # Ω @ 6GHz, 4K
        f_factor = (f / 6e9) ** 2
        
        if T < 0.5 * Tc:  # T < 4.6K, 強超導態
            T_factor = max(0.001, (T / 4.0) ** 1.5)
            Rs = Rs_ref * f_factor * T_factor
        else:  # 4.6K ≤ T < 9.2K, 過渡區
            delta_s_n = sqrt(2 / (MU_0 * sigma_n * 2 * pi * f))
            Rs_normal = 1 / (sigma_n * delta_s_n)
            T_factor = (T / 4.0) ** 1.5
            Rs_sc = Rs_ref * f_factor * T_factor
            ratio = (T - 0.5 * Tc) / (0.5 * Tc)
            Rs = Rs_sc + (Rs_normal - Rs_sc) * ratio
    else:
        # 正常態趨膚效應
        delta_s = sqrt(2 / (MU_0 * sigma_n * 2 * pi * f))
        Rs = 1 / (sigma_n * delta_s)

    # 使用實際計算的特性阻抗 (而非固定 50Ω)
    Z0_actual = calc_stripline_impedance(geo, er)
    Z0_eff = max(Z0_actual, 1.0)  # 避免除以零

    # 導體損耗 (dB/m)
    alpha_c = Rs / (Z0_eff * w)  # Np/m
    alpha_c_db = alpha_c * 8.686  # dB/m

    # 介電損耗 (dB/m)
    # αd = (π * f * sqrt(er) * tanδ) / c
    c = 3e8
    alpha_d = (pi * f * sqrt(er) * tan_delta) / c  # Np/m
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
        "打洞間距": via_spacing,
        "遮蔽強度": shielding_improvement,
        "推薦密度": min(2.0, 1.0 / (pitch / 4))  # 推薦密度
    }

# ============================================================
# Streamlit UI
# ============================================================

#def main():
set_page_config(page_title="Cri/oFlex3 柔性傳輸線規格計算器 III", page_icon="🔬", layout="wide", initial_sidebar_state="expanded")

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
""", unsafe_allow_html=True) # 自定義 CSS
from streamlit import empty
MENU, 表單=[], ['計算結果', '串擾', '熱負載', '插入損耗', '規格摘要', '新增功能', '推導公式']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  #srch=text_input('搜尋', '預設值', placeholder='搜尋')
  狀態=empty()
  #狀態.code([])

with sidebar: # 側邊欄 - 參數輸入
    subheader("⚙️ 設計參數")
    subheader("幾何結構")
    n_channels = radio("通道數", [4, 8, 16, 32], index=1, horizontal=True)
    pitch = slider("通道間距 Pitch (mm)", 0.5, 5.0, 2.0, 0.1)
    length = slider("傳輸線長度 (mm)", 100, 1500, 400, 50)
    sig_width = slider("信號線寬度 (μm)", 50, 500, 300, 10)
    sig_thickness = slider("導體厚度 (μm)", 1, 20, 5, 1)
    dielectric_thickness = slider("單層介電厚度 (μm)", 50, 300, 150, 10)

    subheader("材料選擇")
    conductor_material = radio("導體材料", ["Ag (銀)", "NbTi (超導)", "Cu (銅)"], index=1 , horizontal=True)
    dielectric_material = radio("介電材料", ["Polyimide"], index=0 , horizontal=True) # Kapton

    subheader("Via 設計")
    via_enabled = checkbox("啟用 Via Stitching", value=True)
    via_density = slider("Via 密度 (個/mm)", 0.5, 5.0, 2.0, 0.1)
    via_diameter = slider("Via 直徑 (μm)", 50, 300, 150, 10)

    subheader("操作條件")
    frequency = slider("工作頻率 (GHz)", 0.1, 20.0, 6.0, 0.1)
    temp_stage = radio( "溫度階段", ["300K → 40K", "40K → 4K", "4K → 1K", "1K → 100mK", "RT → mK (全段)"], index=1, horizontal=True)

    subheader("計算選項")
    calc_crosstalk = checkbox("計算串擾", value=True)
    calc_thermal = checkbox("計算熱負載", value=True)
    calc_loss = checkbox("計算插入損耗", value=True)

    # 主內容區
    #col1, col2 = columns([2, 1])

    #with col1:
if menu==len(表單): #
  pass
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
        ) # 建立幾何結構
        else: geo=session_state['geo']
        dielectric = DIELECTRIC["Polyimide"] # 介電參數 _Kapton
        εr=session_state['εr']=dielectric["εr"]

        # 介電參數
        dielectric = DIELECTRIC["Polyimide"]  #_Kapton
        #er = dielectric["er"]
        εr=session_state['εr']=dielectric["εr"]

        # 溫度邊界
        temp_map = {
            "300K → 40K": (300, 40),
            "40K → 4K": (40, 4),
            "4K → 1K": (4, 1),
            "1K → 100mK": (1, .1),
            "RT → mK (全段)": (300, .01)
        }
        T_hot, T_cold = temp_map[temp_stage]
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
        串擾, 打洞, 熱負載, 損耗={}, {}, {}, {}

        # 1. 特性阻抗
        Z0 = session_state['Z0']=calc_stripline_impedance(geo, εr)

        # 2. 串擾計算
        if calc_crosstalk:
            crosstalk = calc_crosstalk_stripline(geo, εr, frequency * 1e9)
            串擾["串擾"] = crosstalk

            # Via 影響
            if via_enabled:
                via_info = calc_via_impact(pitch, via_diameter, via_density)
                打洞['打洞']=via_info
                #results["via"] = via_info
                crosstalk["近端串擾"] -= via_info["遮蔽強度"]
                crosstalk["遠端串擾"] -= via_info["遮蔽強度"]

        # 3. 熱負載計算
        if calc_thermal:
            thermal = calc_thermal_load(geo, boundary, materials)
            熱負載['熱負載'] = thermal

        # 4. 插入損耗
        if calc_loss:
            # 根據溫度選擇損耗角
            if T_cold < 1:
                tan_d = dielectric["tan_delta_20mK"]
            elif T_cold < 10:
                tan_d = dielectric["tan_delta_4K"]
            else:
                tan_d = dielectric["tan_delta_rt"]

            loss = calc_insertion_loss(geo, εr, tan_d, frequency * 1e9, mat_name, T=T_cold)
            #results['損耗'] = loss
            損耗['損耗'] = loss

        # 顯示結果
        # 阻抗卡片
        session_state['results']=results
        session_state['tan_d']=tan_d
        session_state['T_cold']=T_cold
        session_state['T_hot']=T_hot
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
        session_state['串擾']=串擾
        session_state['打洞']=打洞
        session_state['熱負載']=熱負載
        session_state['損耗']=損耗

elif menu==MENU[1]:
        results=session_state['results']
        geo=session_state['geo']
        εr=session_state['εr']
        串擾=session_state['串擾']
        打洞=session_state['打洞']
        熱負載=session_state['熱負載']
        損耗=session_state['損耗']
        # 串擾卡片
        if calc_crosstalk:
            subheader("📡 串擾分析")
            ct = 串擾["串擾"]
            cols = columns(4)
            with cols[0]:
                metric("近端串擾 (NEXT)", f"{ct['近端串擾']:.1f} dB",
                         delta="優良" if ct['近端串擾'] < -40 else "需改善",
                         delta_color="normal" if ct['近端串擾'] < -40 else "inverse")
            with cols[1]:
                metric("遠端串擾 (FEXT)", f"{ct['遠端串擾']:.1f} dB")
            with cols[2]:
                metric("耦合係數 k", f"{ct['耦合強度']:.4f}")
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
                    ct_f["近端串擾"] -= results["via"]["shielding_improvement_dB"]
                    ct_f["遠端串擾"] -= results["via"]["shielding_improvement_dB"]
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

elif menu==MENU[2]: #
        results=session_state['results']
        geo=session_state['geo']
        #εr=session_state['εr']
        materials=session_state['materials']
        串擾=session_state['串擾']
        打洞=session_state['打洞']
        熱負載=session_state['熱負載']
        損耗=session_state['損耗']
        # 熱負載卡片
        if calc_thermal:
            subheader("🌡️ 熱負載分析")
            th = 熱負載['熱負載']
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

elif menu==MENU[3]: #
        results=session_state['results']
        geo=session_state['geo']
        εr=session_state['εr']
        tan_d=session_state['tan_d']
        mat_name=session_state['mat_name']
        T_cold=session_state['T_cold']
        串擾=session_state['串擾']
        打洞=session_state['打洞']
        熱負載=session_state['熱負載']
        損耗=session_state['損耗']
        # 插入損耗
        if calc_loss: # and '損耗' in results
            subheader("📉 插入損耗")
            cols = columns(2)
            with cols[0]:
                metric(f"@{frequency} GHz 插入損耗", f"{損耗['損耗']:.2f} dB",
                         delta="優良" if 損耗['損耗'] < 3 else "偏高",
                         delta_color="normal" if 損耗['損耗'] < 3 else "inverse")
            with cols[1]:
                # 計算衰減常數
                alpha_total = 損耗['損耗'] / (length / 1000)
                metric("衰減常數", f"{alpha_total:.2f} dB/m")

            # 損耗頻率響應
            markdown("<div class='highlight'>插入損耗頻率響應</div>", unsafe_allow_html=True)
            freqs_loss = linspace(0.1, 20, 200) * 1e9
            losses = []
            for f in freqs_loss:
                l = calc_insertion_loss(geo, εr, tan_d, f, mat_name, T=T_cold)
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

elif menu==MENU[4]: #
  subheader("📋 規格摘要")
  results=session_state['results']
  geo=session_state['geo']
  εr=session_state['εr']
  tan_d=session_state['tan_d']
  Z0=session_state['Z0']
  mat_name=session_state['mat_name']
  T_cold=session_state['T_cold']
  T_hot=session_state['T_hot']
  串擾=session_state['串擾']
  打洞=session_state['打洞']
  熱負載=session_state['熱負載']
  損耗=session_state['損耗']
  左, 右=columns(2)
  with 左:
    subheader("設計參數") # 設計規格表
    spec_data = {
        "參數": ["通道數", "Pitch", "長度", "線寬", "導體厚", "介電厚", "導體材料", "介電材料", "介電常數 εr", "損耗角 tan δ"],
        "數值": [
            f"{n_channels} ch",
            f"{pitch} mm",
            f"{length} mm",
            f"{sig_width} μm",
            f"{sig_thickness} μm",
            f"{dielectric_thickness} μm",
            conductor_material,
            dielectric_material,
            f"{εr} (Polyimide)",
            f"{tan_d:.2e} (@ {T_cold}K)"
        ]
    }
    #狀態.code(spec_data)
    table(spec_data)

    subheader("性能指標") # 性能指標
    perf_data = {}
    if calc_crosstalk and 串擾:
        ct = 串擾["串擾"]
        perf_data["串擾 (NEXT)"] = f"{ct['近端串擾']:.1f} dB"
    if calc_thermal and 熱負載:
        th = 熱負載['熱負載']
        perf_data["熱負載/通道"] = f"{th['per_channel_uW']:.2f} μW"
    if calc_loss and 損耗:
        perf_data["插入損耗"] = f"{損耗['損耗']:.2f} dB"
    perf_data["特性阻抗"] = f"{Z0:.1f} Ω"

    perf_df = {"指標": list(perf_data.keys()), "數值": list(perf_data.values())}
    table(perf_df)

    subheader("💡 設計建議") # 設計建議
    suggestions = []

    if Z0 < 45 or Z0 > 55:
        suggestions.append(f"⚠️ 阻抗 {Z0:.1f}Ω 偏離 50Ω 目標，建議調整線寬至 {150 * 50/Z0:.0f}μm")
    else:
        suggestions.append("✅ 阻抗匹配良好")

    if calc_crosstalk and 串擾:
        ct = 串擾["串擾"]
        if ct['近端串擾'] > -40:
            suggestions.append(f"⚠️ 串擾偏高，建議增加 pitch 至 {pitch * 1.5:.1f}mm 或增加 via 密度")
        else:
            suggestions.append("✅ 串擾性能優良")

    if calc_thermal and 熱負載:
        th = 熱負載['熱負載']
        if mat_name == "NbTi" and T_cold < 9.2:
            suggestions.append("✅ NbTi 超導態運行，熱負載極低")
        elif th['per_channel_uW'] > 200:
            suggestions.append("⚠️ 熱負載偏高，建議使用 NbTi 或縮短長度")
        else:
            suggestions.append("✅ 熱負載在合理範圍")

    if via_enabled:
        suggestions.append(f"✅ Via stitching 密度 {via_density}/mm 提供良好屏蔽")

    for s in suggestions:
        markdown(f"<div style='margin: 5px 0;'>{s}</div>", unsafe_allow_html=True)

  with 右:
    subheader("📥 匯出結果") # 匯出按鈕
    export_data = {
        "幾何尺寸": {
            "通道": n_channels,
            "間距": pitch,
            "傳輸線長度": length,
            "訊號寬度": sig_width,
            "導體厚度": sig_thickness,
            "單層介電厚度": dielectric_thickness
        },
        "materials": {
            "導電體": conductor_material,
            "介電質": dielectric_material
        },
        "介電特性": {
            "介電常數_εr": εr,
            "損耗角_tanδ": tan_d,
            "工作溫度_冷端_K": T_cold,
            "工作溫度_熱端_K": T_hot
        },
        #"計算結果": results,
        #'熱負載':熱負載,
        #'損耗':損耗,
        #'串擾':串擾,
        #'打洞':打洞,
        "阻抗": Z0
    }
    export_data.update(熱負載)
    export_data.update(損耗)
    export_data.update(串擾)
    export_data.update(打洞)

    資框=DataFrame(export_data)
    #資框.T
    杰森 = jsnDumps(export_data, indent=2, default=str, ensure_ascii=False)
  #左, 右=columns(2)
  #with 左:
  #  stJSON(export_data)
  #with 右:
    資框 = json_normalize([export_data])
    資框.T
    download_button(label="下載 JSON 規格檔", data=杰森, file_name=f"crioflex3_spec_{length}mm_{n_channels}ch.json", mime="application/json")
elif menu==MENU[5]: # ========== 新增功能 1: 動態示意圖 ==========
  from 德夫傳輸線II import StriplineGeometry, 截面暗, draw_stripline_3d_plotly
  subheader("🔍 物理結構動態示意圖")
  geo=session_state['geo']
  εr=session_state['εr']

  tab1, tab2 = tabs(["📐 橫截面 (Cross-Section)", "📦 立體透視 (3D View)"])

  geo = StriplineGeometry( w=sig_width / 1000, t=sig_thickness, h=dielectric_thickness / 1000, s=pitch, L=length, n_channels=n_channels)
  with tab1:
      #fig_cross = draw_stripline_cross_section(geo, pitch, via_enabled, via_diameter, via_density, n_channels)
      #pyplot(fig_cross)
      fig_cross = 截面暗(geo, pitch, via_enabled, via_diameter, via_density, n_channels)
      pyplot(fig_cross, use_container_width=True) # 自動適應容器寬度

      markdown("""
      <div style="background-color:black; padding:18px; border-radius:10px; margin-top:12px; border:2px solid #BDC3C7;">
      <h4 style="color:#2C3E50; margin-top:0;">📐 五層結構說明 (G-S-G Stripline)</h4>
      <table style="width:100%; border-collapse:collapse; font-size:13px; background-color:black;">
      <tr style="background-color:black;">
          <td style="border:1px solid #BDC3C7; padding:8px; width:15%;"><b>層次</b></td>
          <td style="border:1px solid #BDC3C7; padding:8px; width:25%;"><b>名稱</b></td>
          <td style="border:1px solid #BDC3C7; padding:8px; width:30%;"><b>材料</b></td>
          <td style="border:1px solid #BDC3C7; padding:8px; width:30%;"><b>功能 / 參數</b></td>
      </tr>
      <tr style="background-color:black;">
          <td style="border:1px solid #BDC3C7; padding:8px;"><b>Layer 5</b></td>
          <td style="border:1px solid #BDC3C7; padding:8px;">Top GND</td>
          <td style="border:1px solid #BDC3C7; padding:8px;">Ag / NbTi (金色)</td>
          <td style="border:1px solid #BDC3C7; padding:8px;">上接地屏蔽層，厚度 <b>t</b></td>
      </tr>
      <tr style="background-color:black;">
          <td style="border:1px solid #BDC3C7; padding:8px;"><b>Layer 4</b></td>
          <td style="border:1px solid #BDC3C7; padding:8px;">Upper Dielectric</td>
          <td style="border:1px solid #BDC3C7; padding:8px;">Polyimide (淡米黃)</td>
          <td style="border:1px solid #BDC3C7; padding:8px;">上介電層，厚度 <b>h</b>，εr=3.4</td>
      </tr>
      <tr style="background-color:black;">
          <td style="border:1px solid #BDC3C7; padding:8px;"><b>Layer 3</b></td>
          <td style="border:1px solid #BDC3C7; padding:8px;">Signal Layer</td>
          <td style="border:1px solid #BDC3C7; padding:8px;">Ag / NbTi (金色)</td>
          <td style="border:1px solid #BDC3C7; padding:8px;">信號線寬 <b>w</b> + GND 分隔條</td>
      </tr>
      <tr style="background-color:black;">
          <td style="border:1px solid #BDC3C7; padding:8px;"><b>Layer 2</b></td>
          <td style="border:1px solid #BDC3C7; padding:8px;">Lower Dielectric</td>
          <td style="border:1px solid #BDC3C7; padding:8px;">Polyimide (淡米黃)</td>
          <td style="border:1px solid #BDC3C7; padding:8px;">下介電層，厚度 <b>h</b>，εr=3.4</td>
      </tr>
      <tr style="background-color:black;">
          <td style="border:1px solid #BDC3C7; padding:8px;"><b>Layer 1</b></td>
          <td style="border:1px solid #BDC3C7; padding:8px;">Bottom GND</td>
          <td style="border:1px solid #BDC3C7; padding:8px;">Ag / NbTi (金色)</td>
          <td style="border:1px solid #BDC3C7; padding:8px;">下接地屏蔽層，厚度 <b>t</b></td>
      </tr>
      </table>
      <br>
      <b style="color:#E74C3C;">🔑 關鍵尺寸：</b>
      <ul style="margin:5px 0; padding-left:20px;">
          <li><b style="color:#E74C3C;">w</b> = 信號線寬度 (Signal width) — 影響特性阻抗</li>
          <li><b style="color:#E74C3C;">h</b> = 單層介電厚度 (Dielectric thickness) — 上下各一層</li>
          <li><b style="color:#E74C3C;">t</b> = 導體厚度 (Conductor thickness) — 三層導體相同</li>
          <li><b style="color:#2980B9;">pitch</b> = 通道間距 (Center-to-center) — 影響串擾</li>
          <li><b style="color:#27AE60;">Total</b> = 2h + 3t = 總厚度 (~0.3 mm)</li>
      </ul>
      <b style="color:#A0522D;">🔩 Via Stitching：</b>
      <ul style="margin:5px 0; padding-left:20px;">
          <li>縱向貫穿上/下接地層的金屬通孔</li>
          <li>功能：提供上下 GND 的電氣連接 + 橫向電磁屏蔽</li>
          <li>密度越高，通道間串擾越低</li>
      </ul>
      </div>
      """, unsafe_allow_html=True)

  with tab2:
      #fig_3d = draw_stripline_3d_schematic(geo, pitch, length, n_channels)
      #pyplot(fig_3d)
      subheader(f"Stripline 3D 互動透視 - 當前顯示 {n_channels} 通道")
      info("💡 Aspect Ratio 已動態調整，保持真實長寬比例 | 可旋轉/縮放/平移")
      fig_3d = draw_stripline_3d_plotly(geo, pitch, length, n_channels, via_enabled, via_diameter, via_density)
      plotly_chart(fig_3d, use_container_width=True, height=700)

elif menu==MENU[6]:
        # ========== 新增功能 2: 推導公式展示 ==========
        geo=session_state['geo']
        εr=session_state['εr']
        subheader("📐 串擾推導公式與計算過程")

        formula_tab1, formula_tab2, 公式摘要 = tabs(["📖 完整推導", "🔢 當前參數逐步計算", '公式摘要'])

        with formula_tab1:
            markdown(render_formula_section())

        with formula_tab2:
            calc_md, calc_vals = show_formula_calculation(geo, εr, frequency * 1e9)
            markdown(calc_md)

        with 公式摘要:
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
                    f"{calc_vals['近端串擾']:.2f} dB",
                    f"{calc_vals['遠端串擾']:.2f} dB"
                ]
            }
            資框=DataFrame(result_df)
            資框




with sidebar:
    markdown('<div class="main-header">🔬 Cri/oFlex3 柔性傳輸線規格計算器 III</div>', unsafe_allow_html=True) # 標題區
    markdown('<div class="sub-header">NbTi/Ag + Polyimide 多層膜 Stripline 串擾與熱負載分析 (v3.0)</div>', unsafe_allow_html=True)
    """Cri/oFlex3 柔性傳輸線規格計算器 III
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
