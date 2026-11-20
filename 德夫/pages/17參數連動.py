from streamlit import info, markdown, plotly_chart, pyplot, radio, set_page_config, sidebar, slider, subheader, tabs, title, checkbox, text_input
from numpy import cos, full, linspace, pi, sin
from matplotlib.pyplot import tight_layout
from plotly.graph_objects import Figure, Mesh3d, Scatter3d
from streamlit import empty
from dataclasses import dataclass

@dataclass
class StriplineGeometry:
    """Stripline 幾何參數"""
    w: float        # 信號線寬度 (mm)
    t: float        # 信號線厚度 (μm)
    h: float        # 介電層厚度 (mm) - 單層
    s: float        # 通道間距 pitch (mm)
    L: float        # 傳輸線長度 (mm)
    n_channels: int # 通道數

    @property
    def total_thickness_mm(self) -> float:
        return 2 * self.h + 3 * (self.t / 1000)

    @property
    def total_thickness_um(self) -> float:
        return self.total_thickness_mm * 1000

def create_box_mesh(x0: float, x1: float, y0: float, y1: float, 
                             z0: float, z1: float, color: str, 
                             opacity: float = 1.0, name: str = "",
                             flatshading: bool = True) -> dict:
    """
    改進版：建立 Plotly Mesh3d 的 vertices 和 indices
    新增 flatshading 選項改善視覺效果
    """
    # 8 個頂點
    x = [x0, x1, x1, x0, x0, x1, x1, x0]
    y = [y0, y0, y1, y1, y0, y0, y1, y1]
    z = [z0, z0, z0, z0, z1, z1, z1, z1]
    
    # 12 個三角形面
    i = [0, 0, 0, 1, 1, 2, 2, 3, 4, 4, 5, 6]
    j = [1, 2, 3, 4, 5, 3, 6, 7, 5, 7, 6, 7]
    k = [2, 3, 1, 5, 6, 6, 7, 4, 6, 0, 2, 3]
    
    return dict(
        x=x, y=y, z=z,
        i=i, j=j, k=k,
        color=color,
        opacity=opacity,
        name=name,
        showscale=False,
        flatshading=flatshading,  # 改進：啟用平面著色使邊緣更清晰
        lighting=dict(
            ambient=0.4,
            diffuse=0.8,
            fresnel=0.1,
            specular=0.2,
            roughness=0.5
        ),
        hovertemplate=(
            f"<b>{name}</b><br>"
            f"X: %{{x:.2e}} m<br>"
            f"Y: %{{y:.2e}} m<br>"
            f"Z: %{{z:.2e}} m<extra></extra>"
        )
    )


# ==================== 改進的 Cylinder Mesh 函數 ====================
def create_cylinder_mesh(center_x: float, center_y: float, center_z: float,
                                  radius: float, height: float, color: str,
                                  opacity: float = 0.8, name: str = "",
                                  n_segments: int = 24) -> dict:
    """
    改進版：建立 Plotly 圓柱體 Mesh3d
    增加 n_segments 參數控制平滑度
    """
    theta = linspace(0, 2*pi, n_segments, endpoint=False)
    
    # 底部圓圈頂點
    x_bottom = center_x + radius * cos(theta)
    y_bottom = center_y + radius * sin(theta)
    z_bottom = full(n_segments, center_z - height/2)
    
    # 頂部圓圈頂點
    x_top = center_x + radius * cos(theta)
    y_top = center_y + radius * sin(theta)
    z_top = full(n_segments, center_z + height/2)
    
    # 合併所有頂點
    x = list(x_bottom) + list(x_top)
    y = list(y_bottom) + list(y_top)
    z = list(z_bottom) + list(z_top)
    
    # 三角形索引
    i_list, j_list, k_list = [], [], []
    
    # 側面
    for seg in range(n_segments):
        next_seg = (seg + 1) % n_segments
        i_list.append(seg)
        j_list.append(next_seg)
        k_list.append(seg + n_segments)
        
        i_list.append(next_seg)
        j_list.append(next_seg + n_segments)
        k_list.append(seg + n_segments)
    
    # 底面（扇形三角剖分）
    for seg in range(1, n_segments - 1):
        i_list.append(0)
        j_list.append(seg)
        k_list.append(seg + 1)
    
    # 頂面
    for seg in range(1, n_segments - 1):
        i_list.append(n_segments)
        j_list.append(n_segments + seg + 1)
        k_list.append(n_segments + seg)
    
    return dict(
        x=x, y=y, z=z,
        i=i_list, j=j_list, k=k_list,
        color=color,
        opacity=opacity,
        name=name,
        showscale=False,
        flatshading=True,
        lighting=dict(
            ambient=0.5,
            diffuse=0.7,
            fresnel=0.1,
            specular=0.3,
            roughness=0.4
        ),
        hovertemplate=(
            f"<b>{name}</b><br>"
            f"Radius: {radius*1e6:.1f} μm<br>"
            f"Height: {height*1e6:.1f} μm<extra></extra>"
        )
    )
# ==================== 橫截面繪圖 (暗色主題 Dark Theme) ====================
def 截面暗(geo: StriplineGeometry, pitch: float, via_enabled: bool, via_diameter: float, via_density: float, n_channels: int, y_exaggeration: float = 3.0):
    """
    繪製 Stripline 橫截面動態示意圖 (暗色主題版)
    改進：暗色背景、高對比文字、淺色邊框、動態 Y 軸放大
    """
    from matplotlib.pyplot import subplots, Rectangle, Circle
    from matplotlib.patches import Patch
    import matplotlib.pyplot as plt
    
    # 計算合適的 figure size
    w = geo.w              # mm
    h = geo.h              # mm
    t = geo.t / 1000       # mm
    s = pitch              # mm
    total_h = 2 * h + 3 * t
    n_draw = n_channels    # 完全連動通道數
    total_width = s * n_draw
    margin = s * 0.5
    
    # 動態計算 Figure 寬度
    fig_width = max(12, n_channels * 1.5)
    fig_height = 8
    
    # 關鍵：設定暗色背景
    fig, ax = subplots(figsize=(fig_width, fig_height), facecolor='#121212')
    ax.set_facecolor('#1E1E1E')
    
    # 暗色主題配色方案 (高對比)
    colors = {
        'polyimide': '#A89B82',      # 調暗的卡其色 (避免在暗背景下太刺眼)
        'ag_nbti': '#D4AF37',        # 亮金屬色
        'via': '#E67E22',            # 亮橘色/銅色
        'text': '#F0F0F0',           # 亮白/淺灰 (主要文字)
        'dimension': '#FF4D4D',      # 亮紅 (尺寸標註)
        'arrow': '#4DA6FF',          # 亮藍 (箭頭/總厚度)
        'gnd_sep': '#2ECC71',        # 亮綠 (GND 分隔)
        'edge': '#CCCCCC',           # 淺灰邊框 (取代原本的 black)
        'bg_box': '#2C2C2C'          # 深色提示框背景
    }
    
    # 1. 下接地層
    gnd_bottom = Rectangle((-margin/2, -t), total_width + margin, t, 
                           facecolor=colors['ag_nbti'], edgecolor=colors['edge'], linewidth=1.5)
    ax.add_patch(gnd_bottom)
    ax.text(total_width/2, -t/2, 'Bottom GND (Ag/NbTi)', 
            ha='center', va='center', fontsize=11, color='red', fontweight='bold')
    
    # 2. 下介電層
    dielectric_bottom = Rectangle((-margin/2, 0), total_width + margin, h, 
                                  facecolor=colors['polyimide'], edgecolor=colors['edge'], 
                                  linewidth=1.5, alpha=0.8)
    ax.add_patch(dielectric_bottom)
    ax.text(-margin/2 + 0.05, h/2, f'Polyimide\nεr=3.4\n{h*1000:.0f} μm', 
            ha='left', va='center', fontsize=9, color=colors['text'])
    
    # 3. 信號層 + 接地分隔
    signal_y = h + t - t/2
    show_labels = n_draw <= 16 
    
    for i in range(n_draw):
        x_center = s * (i + 0.5)
        sig = Rectangle((x_center - w/2, signal_y), w, t, 
                        facecolor=colors['ag_nbti'], edgecolor=colors['edge'], linewidth=1.5)
        ax.add_patch(sig)
        
        if show_labels:
            ax.text(x_center, signal_y + t/2, f'S{i+1}', ha='center', va='center', 
                    fontsize=10, color='red', fontweight='bold')
                    
        if i < n_draw - 1:
            gnd_sep_x = x_center + s/2
            gnd_sep_w = min(w * 0.25, s - w - 0.02)
            if gnd_sep_w > 0.01:
                gnd_sep = Rectangle((gnd_sep_x - gnd_sep_w/2, signal_y), gnd_sep_w, t,
                                    facecolor=colors['gnd_sep'], edgecolor=colors['edge'], linewidth=1)
                ax.add_patch(gnd_sep)
                if show_labels:
                    ax.text(gnd_sep_x, signal_y + t/2, 'G', ha='center', va='center',
                            fontsize=8, color='red', fontweight='bold')
    
    # 4. 上介電層
    dielectric_top = Rectangle((-margin/2, h + t), total_width + margin, h, 
                               facecolor=colors['polyimide'], edgecolor=colors['edge'], 
                               linewidth=1.5, alpha=0.8)
    ax.add_patch(dielectric_top)
    ax.text(-margin/2 + 0.05, h + t + h/2, f'Polyimide\nεr=3.4\n{h*1000:.0f} μm', 
            ha='left', va='center', fontsize=9, color=colors['text'])
    
    # 5. 上接地層
    gnd_top = Rectangle((-margin/2, 2*h + 2*t), total_width + margin, t, 
                        facecolor=colors['ag_nbti'], edgecolor=colors['edge'], linewidth=1.5)
    ax.add_patch(gnd_top)
    ax.text(total_width/2, 2*h + 2*t + t/2, 'Top GND (Ag/NbTi)', 
            ha='center', va='center', fontsize=11, color='red', fontweight='bold')
    
    # Via Stitching
    if via_enabled:
        via_spacing = 1.0 / via_density
        n_vias_x = int(total_width / via_spacing) + 2
        via_r = min(via_diameter / 2000, t * 0.4, h * 0.4)
        for i in range(n_vias_x):
            x_via = i * via_spacing
            if x_via > total_width + margin/2 or x_via < -margin/2:
                continue
            via_top_y = 2*h + 2*t - via_r
            via_top = Circle((x_via, via_top_y), via_r, 
                             facecolor=colors['via'], edgecolor=colors['edge'], linewidth=1)
            ax.add_patch(via_top)
            via_bottom_y = -t + via_r
            via_bottom = Circle((x_via, via_bottom_y), via_r,
                                facecolor=colors['via'], edgecolor=colors['edge'], linewidth=1)
            ax.add_patch(via_bottom)
            ax.plot([x_via, x_via], [via_top_y - via_r, via_bottom_y + via_r], 
                    color=colors['via'], linewidth=2, alpha=0.7, linestyle='--')
        
        # 改進：深色背景提示框
        ax.text(total_width + margin*0.9, h + t, 
                f'Via Stitching\nØ{via_diameter} μm\n{via_density} /mm', 
                ha='left', va='center', fontsize=9, color=colors['text'],
                bbox=dict(boxstyle='round,pad=0.3', facecolor=colors['bg_box'], alpha=0.9, edgecolor=colors['via'], linewidth=1.5))
    
    # 尺寸標註 (使用高對比亮色)
    if n_draw <= 8:
        arrow_y1 = -margin * 0.6
        ax.annotate('', xy=(s*0.5 - w/2, arrow_y1), xytext=(s*0.5 + w/2, arrow_y1),
                    arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
        ax.text(s*0.5, arrow_y1 - 0.15, f'w = {w*1000:.0f} μm', ha='center', va='top',
                fontsize=10, color=colors['dimension'], fontweight='bold')
    
    dim_x = total_width + margin*0.3
    ax.annotate('', xy=(dim_x, h + t), xytext=(dim_x, 2*h + 2*t),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text(dim_x + 0.15, 1.5*h + 1.5*t, f'h = {h*1000:.0f} μm', ha='left', va='center',
            fontsize=10, color=colors['dimension'], fontweight='bold', rotation=90)
    
    dim_x2 = total_width + margin*0.7
    ax.annotate('', xy=(dim_x2, 2*h + 2*t), xytext=(dim_x2, 2*h + 3*t),
                arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=1.5))
    ax.text(dim_x2 + 0.15, 2*h + 2.5*t, f't = {geo.t:.0f} μm', ha='left', va='center',
            fontsize=10, color=colors['arrow'], fontweight='bold', rotation=90)
    
    dim_x3 = -margin*0.5
    ax.annotate('', xy=(dim_x3, -t), xytext=(dim_x3, 2*h + 3*t),
                arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=1.5))
    ax.text(dim_x3 - 0.15, h + t, f'Total = {total_h*1000:.0f} μm', ha='right', va='center',
            fontsize=10, color=colors['arrow'], fontweight='bold', rotation=90)
    
    # 標題 (亮色)
    ax.set_title(f'Cri/oFlex3 Stripline Cross-Section View ({n_channels} channels)\n'
                 f'G-S-G | w={w*1000:.0f}μm | h={h*1000:.0f}μm | t={geo.t:.0f}μm | pitch={s:.2f}mm', 
                 fontsize=14, fontweight='bold', pad=20, color=colors['text'])
    
    # 圖例 (暗色主題)
    legend_elements = [
        Patch(facecolor=colors['ag_nbti'], edgecolor=colors['edge'], label='Ag/NbTi Conductor'),
        Patch(facecolor=colors['polyimide'], edgecolor=colors['edge'], alpha=0.8, label='Polyimide Dielectric'),
        Patch(facecolor=colors['gnd_sep'], edgecolor=colors['edge'], label='GND Separation'),
        Circle((0,0), 0.1, facecolor=colors['via'], edgecolor=colors['edge'], label='GND Via')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9, framealpha=0.9, facecolor='#2C2C2C', edgecolor='#555555', labelcolor='red')#, title_color='red'), title_fontproperties={'titlecolor':'yellow'})#titlecolor='red')
    #ax.set_title({'color':'red', 'title':'Layer Legend'})
    #ax.get_title().set_color("red")
    #leg.get_title().set_color("darkblue")

    
    # 動態調整座標軸範圍
    ax.set_xlim(-margin, total_width + margin * 1.5)
    y_display_range = total_h * y_exaggeration
    ax.set_ylim(-y_display_range * 0.3, y_display_range * 0.7)
    ax.axis('off')
    
    # 添加比例尺提示 (暗色主題)
    ax.text(0.02, 0.02, 
            f'Note: Y-axis exaggerated {y_exaggeration}x for clarity\n'
            f'Actual aspect ratio: 1:{total_width/total_h:.1f}',
            transform=ax.transAxes, fontsize=8, color=colors['text'],
            bbox=dict(boxstyle='round,pad=0.3', facecolor=colors['bg_box'], alpha=0.9, edgecolor='#555555'),
            verticalalignment='bottom')
            
    plt.tight_layout()
    return fig

def 截面(geo: StriplineGeometry, pitch: float, via_enabled: bool, via_diameter: float, via_density: float, n_channels: int):
    """
    繪製 Stripline 橫截面動態示意圖 (動態連動版)
    改進：移除 8 通道限制，動態調整 Figure 寬度與文字顯示
    """
    from matplotlib.pyplot import subplots, Rectangle, Circle
    from matplotlib.patches import Patch
    import matplotlib.pyplot as plt

    w = geo.w              # mm
    h = geo.h              # mm
    t = geo.t / 1000       # mm
    s = pitch              # mm
    total_h = 2 * h + 3 * t
    n_draw = n_channels    # 關鍵改進：不再限制為 8，完全連動
    total_width = s * n_draw
    margin = s * 0.5

    # 動態計算 Figure 寬度：每個通道分配約 1.5 英寸，最小 12 英寸
    fig_width = max(12, n_channels * 1.5)
    fig_height = 8
    fig, ax = subplots(figsize=(fig_width, fig_height))

    colors = {
        'polyimide': '#E8DCC8', 'ag_nbti': '#B8860B', 'via': '#8B4513',
        'text': '#2C3E50', 'dimension': '#E74C3C', 'arrow': '#3498DB', 'gnd_sep': '#D4AF37'
    }

    # 1. 下接地層
    gnd_bottom = Rectangle((-margin/2, -t), total_width + margin, t,
                           facecolor=colors['ag_nbti'], edgecolor='black', linewidth=1.5)
    ax.add_patch(gnd_bottom)
    ax.text(total_width/2, -t/2, 'Bottom GND (Ag/NbTi)',
            ha='center', va='center', fontsize=11, color='red', fontweight='bold')

    # 2. 下介電層
    dielectric_bottom = Rectangle((-margin/2, 0), total_width + margin, h,
                                  facecolor=colors['polyimide'], edgecolor='black',
                                  linewidth=1.5, alpha=0.7)
    ax.add_patch(dielectric_bottom)
    ax.text(-margin/2 + 0.05, h/2, f'Polyimide\nεr=3.4\n{h*1000:.0f} μm',
            ha='left', va='center', fontsize=9, color=colors['text'])

    # 3. 信號層 + 接地分隔
    signal_y = h + t - t/2
    # 改進：通道數 > 16 時隱藏文字標籤，避免擁擠
    show_labels = n_draw <= 16

    for i in range(n_draw):
        x_center = s * (i + 0.5)
        sig = Rectangle((x_center - w/2, signal_y), w, t,
                        facecolor=colors['ag_nbti'], edgecolor='black', linewidth=1.5)
        ax.add_patch(sig)

        if show_labels:
            ax.text(x_center, signal_y + t/2, f'S{i+1}', ha='center', va='center',
                    fontsize=10, color='red', fontweight='bold')

        if i < n_draw - 1:
            gnd_sep_x = x_center + s/2
            gnd_sep_w = min(w * 0.25, s - w - 0.02)
            if gnd_sep_w > 0.01:
                gnd_sep = Rectangle((gnd_sep_x - gnd_sep_w/2, signal_y), gnd_sep_w, t,
                                    facecolor=colors['gnd_sep'], edgecolor='black', linewidth=1)
                ax.add_patch(gnd_sep)
                if show_labels:
                    ax.text(gnd_sep_x, signal_y + t/2, 'G', ha='center', va='center',
                            fontsize=8, color='red', fontweight='bold')

    # 4. 上介電層
    dielectric_top = Rectangle((-margin/2, h + t), total_width + margin, h,
                               facecolor=colors['polyimide'], edgecolor='black',
                               linewidth=1.5, alpha=0.7)
    ax.add_patch(dielectric_top)
    ax.text(-margin/2 + 0.05, h + t + h/2, f'Polyimide\nεr=3.4\n{h*1000:.0f} μm',
            ha='left', va='center', fontsize=9, color=colors['text'])

    # 5. 上接地層
    gnd_top = Rectangle((-margin/2, 2*h + 2*t), total_width + margin, t,
                        facecolor=colors['ag_nbti'], edgecolor='black', linewidth=1.5)
    ax.add_patch(gnd_top)
    ax.text(total_width/2, 2*h + 2*t + t/2, 'Top GND (Ag/NbTi)',
            ha='center', va='center', fontsize=11, color='red', fontweight='bold')

    # Via Stitching
    if via_enabled:
        via_spacing = 1.0 / via_density
        n_vias_x = int(total_width / via_spacing) + 2
        via_r = min(via_diameter / 2000, t * 0.4, h * 0.4)
        for i in range(n_vias_x):
            x_via = i * via_spacing
            if x_via > total_width + margin/2 or x_via < -margin/2:
                continue
            via_top_y = 2*h + 2*t - via_r
            via_top = Circle((x_via, via_top_y), via_r,
                             facecolor=colors['via'], edgecolor='black', linewidth=1)
            ax.add_patch(via_top)
            via_bottom_y = -t + via_r
            via_bottom = Circle((x_via, via_bottom_y), via_r,
                                facecolor=colors['via'], edgecolor='black', linewidth=1)
            ax.add_patch(via_bottom)
            ax.plot([x_via, x_via], [via_top_y - via_r, via_bottom_y + via_r],
                    color=colors['via'], linewidth=2, alpha=0.6, linestyle='--')
        ax.text(total_width + margin*0.3, h + t,
                f'Via Stitching\nØ{via_diameter} μm\n{via_density} /mm',
                ha='left', va='center', fontsize=9, color=colors['via'],
                bbox=dict(boxstyle='round,pad=0.3', facecolor='wheat', alpha=0.6, edgecolor=colors['via']))

    # 尺寸標註 (簡化，避免過多通道時標註重疊)
    if n_draw <= 8:
        arrow_y1 = -margin * 0.6
        ax.annotate('', xy=(s*0.5 - w/2, arrow_y1), xytext=(s*0.5 + w/2, arrow_y1),
                    arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
        ax.text(s*0.5, arrow_y1 - 0.15, f'w = {w*1000:.0f} μm', ha='center', va='top',
                fontsize=10, color=colors['dimension'], fontweight='bold')

    dim_x = total_width + margin*0.3
    ax.annotate('', xy=(dim_x, h + t), xytext=(dim_x, 2*h + 2*t),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text(dim_x + 0.15, 1.5*h + 1.5*t, f'h = {h*1000:.0f} μm', ha='left', va='center',
            fontsize=10, color=colors['dimension'], fontweight='bold', rotation=90)

    # 標題與圖例
    ax.set_title(f'Cri/oFlex3 Stripline Cross-Section View ({n_channels} channels)\n'
                 f'G-S-G | w={w*1000:.0f}μm | h={h*1000:.0f}μm | t={geo.t:.0f}μm | pitch={s:.2f}mm',
                 fontsize=14, fontweight='bold', pad=20)

    legend_elements = [
        Patch(facecolor=colors['ag_nbti'], edgecolor='black', label='Ag/NbTi Conductor'),
        Patch(facecolor=colors['polyimide'], edgecolor='black', alpha=0.7, label='Polyimide Dielectric'),
        Patch(facecolor=colors['gnd_sep'], edgecolor='black', label='GND Separation'),
        Circle((0,0), 0.1, facecolor=colors['via'], label='GND Via')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9, framealpha=0.9)

    # 動態調整座標軸範圍
    ax.set_xlim(-margin, total_width + margin * 1.5)
    y_display_range = total_h * 8
    ax.set_ylim(-y_display_range * 0.3, y_display_range * 0.7)
    ax.axis('off')
    tight_layout()
    return fig

def draw_stripline_3d_plotly(geo: StriplineGeometry, pitch: float, length: float, n_channels: int, via_enabled: bool = True, via_diameter: float = 150, via_density: float = 2.0):
    """
    使用 Plotly 繪製互動式 3D Stripline 立體透視圖 (動態連動版)
    改進：移除 8 通道限制，動態計算 Aspect Ratio 保持真實長寬比例
    """
    import plotly.graph_objects as go

    w = geo.w / 1000; h = geo.h / 1000; t = geo.t / 1e6
    L = length / 1000; s = pitch / 1000
    n_draw = n_channels  # 關鍵改進：完全連動

    c_poly = '#E8DCC8'; c_ag = '#B8860B'; c_via = '#8B4513'; c_gnd_sep = '#D4AF37'
    meshes = []

    z0 = 0.0; z1 = t; z2 = t + h; z3 = t + h + t; z4 = t + h + t + h; z5 = t + h + t + h + t
    total_w = s * n_draw
    margin = s * 0.4

    # 1~5. 建立各層 Mesh (與原代碼相同，此處省略重複代碼，直接建立)
    meshes.append(Mesh3d(**create_box_mesh(-margin/2, total_w + margin/2, 0, L, z0, z1, color=c_ag, opacity=0.95, name="Bottom GND")))
    meshes.append(Mesh3d(**create_box_mesh(-margin/2, total_w + margin/2, 0, L, z1, z2, color=c_poly, opacity=0.6, name="Bottom Dielectric")))

    for i in range(n_draw):
        x_c = s * (i + 0.5)
        meshes.append(Mesh3d(**create_box_mesh(x_c - w/2, x_c + w/2, 0, L, z2, z3, color=c_ag, opacity=0.95, name=f"Signal S{i+1}" if n_draw <= 16 else f"Sig {i+1}")))
        if i < n_draw - 1:
            g_x = x_c + s/2; g_w = min(w * 0.25, s - w - 0.00002)
            if g_w > 0.00001:
                meshes.append(Mesh3d(**create_box_mesh(g_x - g_w/2, g_x + g_w/2, 0, L, z2, z3, color=c_gnd_sep, opacity=0.9, name="GND Sep")))

    meshes.append(Mesh3d(**create_box_mesh(-margin/2, total_w + margin/2, 0, L, z3, z4, color=c_poly, opacity=0.6, name="Top Dielectric")))
    meshes.append(Mesh3d(**create_box_mesh(-margin/2, total_w + margin/2, 0, L, z4, z5, color=c_ag, opacity=0.95, name="Top GND")))

    # 6. Via Stitching
    if via_enabled:
        via_r = min(via_diameter / 2e6, t * 0.4, h * 0.3)
        via_spacing = 1.0 / via_density / 1000
        n_vias = int(total_w / via_spacing) + 2
        for i in range(n_vias):
            x_v = i * via_spacing
            if x_v > total_w + margin/2 or x_v < -margin/2: continue
            meshes.append(Mesh3d(**create_cylinder_mesh(x_v, L/2, z5/2, via_r, z5, color=c_via, opacity=0.8, name="GND Via")))

    # 7. 尺寸標註線
    meshes.append(Scatter3d(x=[-margin, -margin], y=[0, 0], z=[z0, z5], mode='lines', line=dict(color='red', width=4), name='Thickness', hoverinfo='skip'))
    meshes.append(Scatter3d(x=[0, total_w], y=[-margin*2, -margin*2], z=[z0, z0], mode='lines', line=dict(color='blue', width=4), name='Width', hoverinfo='skip'))

    # 8. 建立 Figure
    fig = Figure(data=meshes)

    # 關鍵改進：動態計算 Aspect Ratio
    # 保持 X(寬) 和 Y(長) 的真實比例，Z(厚) 適度放大以便觀察
    if total_w > 0 and z5 > 0:
        # 讓 Z 軸在視覺上至少佔 X 軸的 1/4，避免太扁
        z_visual_scale = max(1.0, (total_w / z5) * 0.25)
        y_visual_scale = L / total_w if total_w > 0 else 1.0
    else:
        z_visual_scale = 1.0; y_visual_scale = 1.0

    fig.update_layout(
        title=dict(
            text=f'<b>Cri/oFlex3 3D View ({n_channels}ch)</b><br>'
                 f'<sup>L={length}mm | w={geo.w*1000:.0f}μm | h={geo.h*1000:.0f}μm | t={geo.t:.0f}μm</sup>',
            x=0.5, font=dict(size=16)
        ),
        scene=dict(
            xaxis=dict(title='Width (X)', showbackground=True, backgroundcolor='rgba(240,240,240,0.3)'),
            yaxis=dict(title='Length (Y)', showbackground=True, backgroundcolor='rgba(240,240,240,0.3)'),
            zaxis=dict(title='Thickness (Z)', showbackground=True, backgroundcolor='rgba(240,240,240,0.3)'),
            # 動態 Aspect Ratio：X=1, Y=真實長寬比, Z=動態放大
            aspectmode='manual',
            aspectratio=dict(x=1.0, y=y_visual_scale, z=z_visual_scale),
            camera=dict(eye=dict(x=1.5, y=-1.5, z=1.0), center=dict(x=0.0, y=0.0, z=0.0))
        ),
        showlegend=True,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor='rgba(255,255,255,0.8)',
                    font=dict(size=10 if n_channels > 8 else 12)), # 通道多時縮小圖例字體
        margin=dict(l=0, r=0, t=60, b=0),
        paper_bgcolor='red', height=700
    )
    return fig

set_page_config(page_title="Cri/oFlex3 Stripline Designer", layout="wide")
title("🔬 Cri/oFlex3 Stripline 多層結構設計器")

#with sidebar:
#    subheader("️ 設計參數")
#    markdown("**幾何結構**")
#    # 通道數選擇
#    n_channels = radio("通道數 (Channels)", [4, 8, 16, 32], index=1, horizontal=True)
#    pitch = slider("通道間距 Pitch (mm)", 0.5, 5.0, 2.0, 0.1)
#    length = slider("傳輸線長度 (mm)", 100, 1500, 400, 50)
with sidebar: # 側邊欄 - 參數輸入
  subheader("⚙️ 設計參數")
  
  markdown("**幾何結構**")
  n_channels = radio("通道數", [4, 8, 16, 32], index=1, horizontal=True, key='通道數')
  pitch = slider("通道間距 Pitch (mm)", 0.5, 5.0, 2.0, 0.1)
  length = slider("傳輸線長度 (mm)", 100, 1500, 400, 50)
  sig_width = slider("信號線寬度 (μm)", 50, 500, 300, 10)
  sig_thickness = slider("導體厚度 (μm)", 1, 20, 5, 1)
  dielectric_thickness = slider("單層介電厚度 (μm)", 50, 300, 150, 10)

  markdown("**材料選擇**")
  conductor_material = radio("導體材料", ["Ag (銀)", "NbTi (超導)", "Cu (銅)"], 
                                 index=1, horizontal=True)
  dielectric_material = radio("介電材料", ["Polyimide Kapton"], 
                                  index=0, horizontal=True)

  markdown("**Via 設計**")
  via_enabled = checkbox("啟用 Via Stitching", value=True)
  via_density = slider("Via 密度 (個/mm)", 0.5, 5.0, 2.0, 0.1)
  via_diameter = slider("Via 直徑 (μm)", 50, 300, 150, 10)

  markdown("**操作條件**")
  frequency = slider("工作頻率 (GHz)", 0.1, 20.0, 6.0, 0.1)
  temp_stage = radio("溫度階段", 
                        ["300K → 40K", "40K → 4K", "4K → 1K", "1K → 100mK", "RT → mK (全段)"], 
                        index=1, horizontal=True)

  markdown("**計算選項**")
  calc_crosstalk = checkbox("計算串擾", value=True)
  calc_thermal = checkbox("計算熱負載", value=True)
  calc_loss = checkbox("計算插入損耗", value=True)

# 建立幾何結構物件
geo = StriplineGeometry(
  w=sig_width / 1000,
  t=sig_thickness,
  h=dielectric_thickness / 1000,
  s=pitch,
  L=length,
  n_channels=n_channels
)

geo = StriplineGeometry( w=sig_width / 1000, t=sig_thickness, h=dielectric_thickness / 1000, s=pitch, L=length, n_channels=n_channels)


MENU, 表單=[], ['連動', '立體圖', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  狀態=empty()
  狀態.code([])
if menu==len(表單): #
  pass
elif menu==MENU[1]: #
  pass
elif menu==MENU[0]: #連動
  pass
  tab1, tab2, tab3 = tabs([" 橫截面視圖", " 3D 互動透視", " 參數摘要"])

  with tab1:
      subheader(f"Stripline 橫截面 (Cross-Section) - 當前顯示 {n_channels} 通道")
      info("💡 圖形寬度與通道數量動態連動，通道數 > 16 時自動隱藏標籤以防擁擠")
      fig_cross = 截面暗(geo, pitch, via_enabled, via_diameter, via_density, n_channels)
      pyplot(fig_cross, use_container_width=True) # 自動適應容器寬度

  with tab2:
      subheader(f"Stripline 3D 互動透視 - 當前顯示 {n_channels} 通道")
      info("💡 Aspect Ratio 已動態調整，保持真實長寬比例 | 可旋轉/縮放/平移")
      fig_3d = draw_stripline_3d_plotly(geo, pitch, length, n_channels, via_enabled, via_diameter, via_density)
      plotly_chart(fig_3d, use_container_width=True, height=700)
