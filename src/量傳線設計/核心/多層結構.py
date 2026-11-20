from matplotlib.pyplot import Circle, Polygon, Rectangle, subplots, tight_layout
from typing import List, Dict, Tuple
from dataclasses import dataclass
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


def 立體透視(geo: StriplineGeometry, pitch: float, length: float, n_channels: int, conductor_color='#D4AF37', dielectric_color='#C4B49A'):
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
    c_poly_dark = dielectric_color   # Polyimide 頂面/側面
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
                       conductor_color, 'black', '#F0E68C', alpha=0.9, zorder=3)
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


def 微帶動態橫截面(geo: StriplineGeometry, pitch: float, via_enabled: bool, via_diameter: float, via_density: float, n_channels: int, conductor_color='#D4AF37', dielectric_color='#C4B49A'): #draw_stripline_cross_section
    """
    繪製 Stripline 橫截面動態示意圖

    結構示意 (G-S-G 多層膜):

    ┌─────────────────────────────────────────┐  ← 上接地層 (Top GND)
    │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │
    ├─────────────────────────────────────────┤  ← 上介電層 (Polyimide)
    │     ═══════     ═══════     ═══════   │  ← 信號層 (Signal)
    │     S1    GND   S2    GND   S3        │
    ├─────────────────────────────────────────┤  ← 下介電層 (Polyimide)
    │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │
    └─────────────────────────────────────────┘  ← 下接地層 (Bottom GND)
         ↑_________↑
            pitch
    """
    fig, ax = subplots(figsize=(14, 6))

    # 尺寸轉換 (mm)
    w = geo.w  # 信號線寬
    h = geo.h  # 單層介電厚
    t = geo.t / 1000  # μm -> mm (導體厚)
    s = pitch  # 通道間距
    total_h = 2 * h + 3 * t  # 總厚度

    # 繪圖區域設定
    n_draw = min(n_channels, 6)  # 最多畫 6 個通道
    total_width = s * (n_draw + 0.5)
    margin = s * 0.3

    ax.set_xlim(-margin, total_width + margin)
    ax.set_ylim(-margin, total_h + margin)
    ax.set_aspect('equal')
    ax.axis('off')

    # 顏色定義
    colors = {
        'polyimide': '#E8DCC8',      # 淡棕色 (Polyimide)
        'ag_nbti': '#B8860B',        # 暗金色 (Ag/NbTi 導體)
        'via': '#8B4513',            # 深棕色 (Via)
        'text': '#2C3E50',           # 深藍灰 (文字)
        'dimension': '#E74C3C',      # 紅色 (尺寸線)
        'arrow': '#3498DB'           # 藍色 (箭頭)
    }

    # 繪製多層膜結構
    # 上接地層
    gnd_top = Rectangle((-margin/2, 2*h + 2*t), total_width + margin, t, 
                             facecolor=colors['ag_nbti'], edgecolor='black', linewidth=1.5)
    ax.add_patch(gnd_top)
    ax.text(total_width/2, 2*h + 2*t + t/2, 'Top GND (Ag/NbTi)', 
            ha='center', va='center', fontsize=9, color='white', fontweight='bold')

    # 上介電層
    dielectric_top = Rectangle((-margin/2, h + t), total_width + margin, h, 
                                    facecolor=colors['polyimide'], edgecolor='black', linewidth=1.5, alpha=0.7)
    ax.add_patch(dielectric_top)
    ax.text(-margin/2 + 0.1, h + t + h/2, 'Polyimide\nεr=3.4', 
            ha='left', va='center', fontsize=8, color=colors['text'])

    # 信號層 (多通道)
    for i in range(n_draw):
        x_center = s * (i + 0.5)
        sig = Rectangle((x_center - w/2, h + t - t/2), w, t, 
                            facecolor=colors['ag_nbti'], edgecolor='black', linewidth=1.5)
        ax.add_patch(sig)
        ax.text(x_center, h + t, f'S{i+1}', ha='center', va='center', 
                fontsize=8, color='white', fontweight='bold')

        # 接地分隔 (G-S-G)
        if i < n_draw - 1:
            gnd_sep_x = x_center + s/2
            gnd_sep = Rectangle((gnd_sep_x - w*0.3/2, h + t - t/2), w*0.3, t,
                                    facecolor=conductor_color, edgecolor='black', linewidth=1)
            ax.add_patch(gnd_sep)
            ax.text(gnd_sep_x, h + t, 'G', ha='center', va='center',
                    fontsize=7, color='white')

    # 下介電層
    dielectric_bottom = Rectangle((-margin/2, 0), total_width + margin, h, 
                                       facecolor=colors['polyimide'], edgecolor='black', linewidth=1.5, alpha=0.7)
    ax.add_patch(dielectric_bottom)
    ax.text(-margin/2 + 0.1, h/2, 'Polyimide\nεr=3.4', 
            ha='left', va='center', fontsize=8, color=colors['text'])

    # 下接地層
    gnd_bottom = Rectangle((-margin/2, -t), total_width + margin, t, 
                                facecolor=colors['ag_nbti'], edgecolor='black', linewidth=1.5)
    ax.add_patch(gnd_bottom)
    ax.text(total_width/2, -t/2, 'Bottom GND (Ag/NbTi)', 
            ha='center', va='center', fontsize=9, color='white', fontweight='bold')

    # Via Stitching (如果啟用)
    if via_enabled:
        via_spacing = 1.0 / via_density  # mm
        n_vias_x = int(total_width / via_spacing) + 1
        via_r = via_diameter / 2000  # μm -> mm (半徑)

        for i in range(n_vias_x):
            x_via = i * via_spacing
            if x_via > total_width:
                break
            # 上層 Via
            via_top = Circle((x_via, 2*h + 2*t - via_r), via_r, 
                                  facecolor=colors['via'], edgecolor='black', linewidth=1)
            ax.add_patch(via_top)
            # 下層 Via
            via_bottom = Circle((x_via, -t + via_r), via_r,
                                    facecolor=colors['via'], edgecolor='black', linewidth=1)
            ax.add_patch(via_bottom)
            # 連接線
            ax.plot([x_via, x_via], [2*h + 2*t - 2*via_r, -t + 2*via_r], 
                    color=colors['via'], linewidth=2, alpha=0.6)

        ax.text(total_width + margin*0.5, h + t, f'Via\nØ{via_diameter}μm\n{via_density}/mm', 
                ha='left', va='center', fontsize=8, color=colors['via'],
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # 尺寸標註 - 信號線寬度 w
    arrow_y = -margin * 0.6
    ax.annotate('', xy=(s*0.5 - w/2, arrow_y), xytext=(s*0.5 + w/2, arrow_y),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text(s*0.5, arrow_y - 0.15, f'w = {w*1000:.0f} μm', ha='center', va='top',
            fontsize=9, color=colors['dimension'], fontweight='bold')

    # 尺寸標註 - Pitch s
    arrow_y2 = -margin * 1.0
    ax.annotate('', xy=(s*0.5, arrow_y2), xytext=(s*1.5, arrow_y2),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text(s, arrow_y2 - 0.15, f'pitch = {s:.1f} mm', ha='center', va='top',
            fontsize=9, color=colors['dimension'], fontweight='bold')

    # 尺寸標註 - 介電厚度 h
    ax.annotate('', xy=(total_width + margin*0.4, h + t), xytext=(total_width + margin*0.4, 2*h + 2*t),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text(total_width + margin*0.6, 1.5*h + t, f'h = {h*1000:.0f} μm', ha='left', va='center',
            fontsize=9, color=colors['dimension'], fontweight='bold', rotation=90)

    # 尺寸標註 - 總厚度
    ax.annotate('', xy=(-margin*0.4, -t), xytext=(-margin*0.4, 2*h + 3*t),
                arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=1.5))
    ax.text(-margin*0.6, h + t, f'total = {total_h*1000:.0f} μm', ha='right', va='center',
            fontsize=9, color=colors['arrow'], fontweight='bold', rotation=90)

    # 標題
    ax.set_title(f'Cri/oFlex3 Stripline Cross-Section\n({n_channels} channels, G-S-G configuration)', 
                 fontsize=13, fontweight='bold', pad=20)

    # 圖例
    legend_elements = [
        Rectangle((0,0),1,1, facecolor=colors['ag_nbti'], edgecolor='black', label='Ag/NbTi Conductor'),
        Rectangle((0,0),1,1, facecolor=colors['polyimide'], edgecolor='black', alpha=0.7, label='Polyimide (εr=3.4)'),
        Circle((0,0), 0.1, facecolor=colors['via'], label='GND Via')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=8, framealpha=0.9)

    tight_layout()
    return fig


def 立體示意圖(geo: StriplineGeometry, pitch: float, length: float, n_channels: int, conductor_color='#D4AF37', dielectric_color='#C4B49A'): #draw_stripline_3d_schematic
    """
    繪製 Stripline 3D 立體示意圖 (簡化透視)
    """
    fig, ax = subplots(figsize=(14, 5))

    w = geo.w
    h = geo.h
    t = geo.t / 1000
    L = length / 10  # 縮放顯示
    s = pitch
    n_draw = min(n_channels, 4)

    # 透視參數
    skew = 0.3
    depth = L

    # 繪製上接地層 (3D 透視)
    for i in range(n_draw):
        x0 = s * i + 0.2
        # 上表面
        poly_top = Polygon([
            [x0, 2*h + 3*t],
            [x0 + w, 2*h + 3*t],
            [x0 + w + skew*depth, 2*h + 3*t + 0.1],
            [x0 + skew*depth, 2*h + 3*t + 0.1]
        ], facecolor='#B8860B', edgecolor='black', alpha=0.9)
        ax.add_patch(poly_top)

        # 信號線
        poly_sig = Polygon([
            [x0, h + t],
            [x0 + w, h + t],
            [x0 + w + skew*depth, h + t + 0.1],
            [x0 + skew*depth, h + t + 0.1]
        ], facecolor='#DAA520', edgecolor='black', alpha=0.9)
        ax.add_patch(poly_sig)

        # 下接地層
        poly_bot = Polygon([
            [x0, 0],
            [x0 + w, 0],
            [x0 + w + skew*depth, 0.1],
            [x0 + skew*depth, 0.1]
        ], facecolor='#B8860B', edgecolor='black', alpha=0.9)
        ax.add_patch(poly_bot)

        # 側面介電層線條
        ax.plot([x0, x0 + skew*depth], [2*h + 3*t, 2*h + 3*t + 0.1], 'k-', linewidth=0.5, alpha=0.3)
        ax.plot([x0, x0 + skew*depth], [0, 0.1], 'k-', linewidth=0.5, alpha=0.3)

    # 長度標註
    ax.annotate('', xy=(s*n_draw + 0.5, -0.3), xytext=(0.2, -0.3),
                arrowprops=dict(arrowstyle='<->', color='red', lw=2))
    ax.text(s*n_draw/2, -0.6, f'L = {length} mm', ha='center', va='top',
            fontsize=11, color='red', fontweight='bold')

    ax.set_xlim(-0.5, s*n_draw + 2)
    ax.set_ylim(-1, 2*h + 4*t + 0.5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Cri/oFlex3 Stripline 3D Perspective View\n(Multilayer Polyimide + Ag/NbTi)', 
                 fontsize=13, fontweight='bold')

    tight_layout()
    return fig



MENU, 表單=[], ['橫截面', '立體圖', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
