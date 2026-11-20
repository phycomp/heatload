# cf3_three_view.py
# 三視圖繪製模組

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, Circle
import numpy as np
from 傳輸線佈局 import LayoutCalculator


def draw_front_view(calc: CF3LayoutCalculator, figsize=(12, 6)):
    """
    繪製 CF3 前視圖 (GSG 截面)
    
    Args:
        calc: CF3LayoutCalculator 實例
        figsize: 圖形尺寸
    
    Returns:
        matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    ax.set_facecolor('white')
    
    # 標題
    ax.set_title(
        f'CF3 前視圖 (Front View) - {calc.n_channels} 通道\n'
        f'總寬度: {calc.target_total_width_mm:.3f} mm | 總厚度: {calc.total_thickness_mm:.3f} mm',
        fontsize=12, fontweight='bold'
    )
    
    # 計算各層位置
    total_w_mm = calc.target_total_width_mm
    layer_positions = calc.layer_positions
    
    # 層顏色對應
    layer_colors = {
        '保護層': '#E8D5C4',
        '接地層': '#8B9CAD',
        '介電層': '#C4956A',
        '訊號層': '#FFD700',
    }
    
    layer_edges = {
        '保護層': '#A0522D',
        '接地層': '#4A5568',
        '介電層': '#744210',
        '訊號層': '#B8860B',
    }
    
    # 繪製各層
    for i, pos in enumerate(layer_positions):
        y_bot = pos['y_bot_mm']
        y_top = pos['y_top_mm']
        thickness = pos['thickness_mm']
        
        # 確定層類別
        layer_type = '介電層'
        if '保護' in pos['name']:
            layer_type = '保護層'
        elif '接地' in pos['name']:
            layer_type = '接地層'
        elif '訊號' in pos['name']:
            layer_type = '訊號層'
        
        color = layer_colors[layer_type]
        edge = layer_edges[layer_type]
        
        # 繪製層矩形
        rect = Rectangle(
            (-total_w_mm/2, y_bot),
            total_w_mm, thickness,
            facecolor=color, edgecolor=edge,
            linewidth=1.5, alpha=0.9
        )
        ax.add_patch(rect)
        
        # 層名稱標註 (左側)
        label_y = (y_bot + y_top) / 2
        ax.text(
            -total_w_mm/2 - 0.5, label_y,
            pos['name'],
            ha='right', va='center',
            fontsize=8, fontweight='bold'
        )
        
        # 厚度標註 (右側)
        ax.annotate(
            '', xy=(total_w_mm/2 + 0.3, y_bot),
            xytext=(total_w_mm/2 + 0.3, y_top),
            arrowprops=dict(arrowstyle='<->', color='#2980B9', lw=1)
        )
        ax.text(
            total_w_mm/2 + 0.6, label_y,
            f'{pos["thickness_um"]:.0f}μm',
            ha='left', va='center',
            fontsize=7, color='#2980B9'
        )
        
        # 層間分隔線
        if i < len(layer_positions) - 1:
            ax.axhline(y=y_top, color='#CCCCCC', linewidth=0.5, linestyle=':')
    
    # 繪製訊號線 (在訊號層中)
    signal_idx = calc.signal_layer_idx
    signal_pos = layer_positions[signal_idx]
    y_signal_bot = signal_pos['y_bot_mm']
    y_signal_top = signal_pos['y_top_mm']
    signal_thick = signal_pos['thickness_mm']
    
    for ch in range(calc.n_channels):
        x_center = (ch - (calc.n_channels - 1) / 2) * calc.pitch_mm
        x_left = x_center - calc.signal_width_mm / 2
        
        # 訊號線
        rect = Rectangle(
            (x_left, y_signal_bot),
            calc.signal_width_mm, signal_thick,
            facecolor='#FFD700', edgecolor='#B8860B',
            linewidth=1.5
        )
        ax.add_patch(rect)
        
        # 通道編號
        ax.text(
            x_center, (y_signal_bot + y_signal_top) / 2,
            f'CH{ch+1}',
            ha='center', va='center',
            fontsize=6, fontweight='bold', color='#333'
        )
    
    # ===== Pitch 標註 =====
    if calc.n_channels >= 2:
        pitch_y = -calc.total_thickness_mm/2 - 0.2
        x1 = -calc.pitch_mm/2
        x2 = calc.pitch_mm/2
        
        ax.annotate(
            '', xy=(x1, pitch_y), xytext=(x2, pitch_y),
            arrowprops=dict(arrowstyle='<->', color='#E74C3C', lw=1.5)
        )
        ax.text(
            0, pitch_y - 0.05,
            f'Pitch = {calc.pitch_mm:.1f} mm',
            ha='center', va='top',
            fontsize=9, color='#E74C3C', fontweight='bold'
        )
    
    # ===== Clearance 標註 =====
    edge_margin = calc.edge_margin_mm
    if edge_margin > 0:
        clearance_y = -calc.total_thickness_mm/2 - 0.5
        ax.annotate(
            '', xy=(-total_w_mm/2, clearance_y),
            xytext=(-total_w_mm/2 + edge_margin, clearance_y),
            arrowprops=dict(arrowstyle='<->', color='#27AE60', lw=1.5)
        )
        ax.annotate(
            '', xy=(total_w_mm/2 - edge_margin, clearance_y),
            xytext=(total_w_mm/2, clearance_y),
            arrowprops=dict(arrowstyle='<->', color='#27AE60', lw=1.5)
        )
        ax.text(
            0, clearance_y - 0.05,
            f'Clearance = {edge_margin:.3f} mm (10H = {calc.clearance_10h:.3f} mm)',
            ha='center', va='top',
            fontsize=8, color='#27AE60'
        )
    
    # ===== 軸設定 =====
    margin = max(1.5, calc.total_thickness_mm * 2)
    ax.set_xlim(-total_w_mm/2 - 1.5, total_w_mm/2 + 1.5)
    ax.set_ylim(-calc.total_thickness_mm/2 - 0.8, calc.total_thickness_mm/2 + 0.2)
    ax.set_aspect('equal')
    ax.set_xlabel('寬度 (mm)', fontsize=10)
    ax.set_ylabel('厚度 (mm)', fontsize=10)
    ax.grid(True, alpha=0.15, linestyle='--')
    
    return fig


def draw_side_view(calc: CF3LayoutCalculator, length_mm: float = 400, figsize=(12, 6)):
    """
    繪製 CF3 側視圖 (長度方向)
    
    Args:
        calc: CF3LayoutCalculator 實例
        length_mm: 顯示長度 (mm)
        figsize: 圖形尺寸
    
    Returns:
        matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    ax.set_facecolor('white')
    
    # 標題
    ax.set_title(
        f'CF3 側視圖 (Side View) - {calc.n_channels} 通道\n'
        f'長度: {length_mm} mm | 厚度: {calc.total_thickness_mm:.3f} mm',
        fontsize=12, fontweight='bold'
    )
    
    # 主體輪廓
    half_thick = calc.total_thickness_mm / 2
    rect = Rectangle(
        (0, -half_thick),
        length_mm, calc.total_thickness_mm,
        facecolor='#C4956A', edgecolor='#8B6914',
        linewidth=1.5, alpha=0.85
    )
    ax.add_patch(rect)
    
    # 訊號層位置 (中心線)
    ax.axhline(y=0, color='#FFD700', linewidth=1.5, linestyle='--', alpha=0.7)
    ax.text(
        length_mm/2, 0.002,
        'Signal Layer',
        ha='center', va='bottom',
        fontsize=8, color='#B8860B', style='italic'
    )
    
    # 接地層位置 (上下邊界)
    ax.axhline(y=half_thick - 0.005, color='#8B9CAD', linewidth=1, linestyle=':', alpha=0.5)
    ax.axhline(y=-half_thick + 0.005, color='#8B9CAD', linewidth=1, linestyle=':', alpha=0.5)
    
    # ===== 長度標註 =====
    ax.annotate(
        '', xy=(0, -half_thick - 0.3),
        xytext=(length_mm, -half_thick - 0.3),
        arrowprops=dict(arrowstyle='<->', color='#E74C3C', lw=1.5)
    )
    ax.text(
        length_mm/2, -half_thick - 0.4,
        f'L = {length_mm} mm',
        ha='center', va='top',
        fontsize=10, color='#E74C3C', fontweight='bold'
    )
    
    # ===== 厚度標註 =====
    ax.annotate(
        '', xy=(length_mm + 0.5, -half_thick),
        xytext=(length_mm + 0.5, half_thick),
        arrowprops=dict(arrowstyle='<->', color='#2980B9', lw=1.5)
    )
    ax.text(
        length_mm + 0.8, 0,
        f't = {calc.total_thickness_mm:.3f} mm',
        ha='left', va='center',
        fontsize=9, color='#2980B9', fontweight='bold',
        rotation=90
    )
    
    # ===== 彎曲半徑標註 =====
    # 簡化彎曲示意
    ax.plot([length_mm*0.7, length_mm*0.7], [half_thick, half_thick + 0.2],
            color='#FF6B6B', linewidth=1, linestyle='--')
    ax.text(
        length_mm*0.7, half_thick + 0.3,
        'R ≥ 5 mm',
        ha='center', va='bottom',
        fontsize=8, color='#FF6B6B'
    )
    
    # ===== 軸設定 =====
    ax.set_xlim(-0.5, length_mm + 2.5)
    ax.set_ylim(-half_thick - 0.6, half_thick + 0.6)
    ax.set_aspect('equal')
    ax.set_xlabel('長度 (mm)', fontsize=10)
    ax.set_ylabel('厚度 (mm)', fontsize=10)
    ax.grid(True, alpha=0.15, linestyle='--')
    
    return fig


def draw_top_view(calc: CF3LayoutCalculator, length_mm: float = 400, figsize=(12, 8)):
    """
    繪製 CF3 上視圖 (平面佈局)
    
    Args:
        calc: CF3LayoutCalculator 實例
        length_mm: 顯示長度 (mm)
        figsize: 圖形尺寸
    
    Returns:
        matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    ax.set_facecolor('white')
    
    total_w_mm = calc.target_total_width_mm
    
    # 標題
    ax.set_title(
        f'CF3 上視圖 (Top View) - {calc.n_channels} 通道\n'
        f'總寬度: {total_w_mm:.3f} mm | 長度: {length_mm} mm',
        fontsize=12, fontweight='bold'
    )
    
    # 主體
    rect = Rectangle(
        (0, -total_w_mm/2),
        length_mm, total_w_mm,
        facecolor='#C4956A', edgecolor='#8B6914',
        linewidth=1.5, alpha=0.3
    )
    ax.add_patch(rect)
    
    # 訊號線
    for ch in range(calc.n_channels):
        y_center = (ch - (calc.n_channels - 1) / 2) * calc.pitch_mm
        y_bot = y_center - calc.signal_width_mm / 2
        y_top = y_center + calc.signal_width_mm / 2
        
        rect = Rectangle(
            (5, y_bot),
            length_mm - 10, calc.signal_width_mm,
            facecolor='#FFD700', edgecolor='#B8860B',
            linewidth=1, alpha=0.85
        )
        ax.add_patch(rect)
        
        # 通道標註
        ax.text(
            length_mm/2, y_center,
            f'CH{ch+1}',
            ha='center', va='center',
            fontsize=8, fontweight='bold', color='#333'
        )
    
    # ===== 寬度標註 =====
    ax.annotate(
        '', xy=(length_mm + 0.5, -total_w_mm/2),
        xytext=(length_mm + 0.5, total_w_mm/2),
        arrowprops=dict(arrowstyle='<->', color='#E74C3C', lw=1.5)
    )
    ax.text(
        length_mm + 0.8, 0,
        f'W = {total_w_mm:.3f} mm',
        ha='left', va='center',
        fontsize=9, color='#E74C3C', fontweight='bold',
        rotation=90
    )
    
    # ===== Pitch 標註 =====
    if calc.n_channels >= 2:
        y1 = -(calc.n_channels - 1) / 2 * calc.pitch_mm
        y2 = y1 + calc.pitch_mm
        ax.annotate(
            '', xy=(length_mm * 0.3, y1),
            xytext=(length_mm * 0.3, y2),
            arrowprops=dict(arrowstyle='<->', color='#27AE60', lw=1.2)
        )
        ax.text(
            length_mm * 0.3 + 0.5, (y1 + y2) / 2,
            f'Pitch = {calc.pitch_mm:.1f} mm',
            ha='left', va='center',
            fontsize=8, color='#27AE60'
        )
    
    # ===== 長度標註 =====
    ax.annotate(
        '', xy=(0, total_w_mm/2 + 0.5),
        xytext=(length_mm, total_w_mm/2 + 0.5),
        arrowprops=dict(arrowstyle='<->', color='#E74C3C', lw=1.5)
    )
    ax.text(
        length_mm/2, total_w_mm/2 + 0.7,
        f'L = {length_mm} mm',
        ha='center', va='bottom',
        fontsize=9, color='#E74C3C', fontweight='bold'
    )
    
    # ===== 軸設定 =====
    margin = max(1, total_w_mm * 0.3)
    ax.set_xlim(-2, length_mm + 3)
    ax.set_ylim(-total_w_mm/2 - margin, total_w_mm/2 + margin)
    ax.set_aspect('equal')
    ax.set_xlabel('長度 (mm)', fontsize=10)
    ax.set_ylabel('寬度 (mm)', fontsize=10)
    ax.grid(True, alpha=0.15, linestyle='--')
    
    return fig
