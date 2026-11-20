from streamlit import checkbox, columns, info, markdown, metric, plotly_chart, pyplot, radio, set_page_config, sidebar, slider, subheader, tabs, title, write
from matplotlib.pyplot import tight_layout
from numpy import cos, full, linspace, log, pi, sin, sqrt
from plotly.graph_objects import Figure, Mesh3d, Scatter3d

# 建立完整的 Plotly 3D + 修正橫截面版本

"""
Cri/oFlex3 Stripline 動態多層結構視覺化 v4
改進：
1. 橫截面取消 equal aspect，使用獨立縮放 + 放大 Y 軸顯示區域
2. 立體透視改用 Plotly 真 3D 互動渲染，可旋轉/縮放/平移
3. 內嵌所有資料結構，無需外部模組
4. 支援 Streamlit 直接嵌入互動式 3D 圖表
"""

import streamlit as st
from dataclasses import dataclass
from typing import List, Dict, Tuple
import numpy as np

# ==================== 資料結構定義 ====================

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


# ==================== 輔助函數：建立 3D Box Mesh ====================

def create_box_mesh(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float,
                    color: str, opacity: float = 1.0, name: str = "") -> dict:
    """
    建立 Plotly Mesh3d 的 vertices 和 indices
    返回 dict 可直接傳入 go.Mesh3d(**dict)
    """
    # 8 個頂點
    x = [x0, x1, x1, x0, x0, x1, x1, x0]
    y = [y0, y0, y1, y1, y0, y0, y1, y1]
    z = [z0, z0, z0, z0, z1, z1, z1, z1]
    
    # 12 個三角形面 (每個矩形面拆成 2 個三角形)
    # 底面 (z=z0): 0-1-2, 0-2-3
    # 頂面 (z=z1): 4-6-5, 4-7-6
    # 前面 (y=y0): 0-5-1, 0-4-5
    # 後面 (y=y1): 2-7-3, 2-6-7
    # 左面 (x=x0): 0-7-4, 0-3-7
    # 右面 (x=x1): 1-5-6, 1-6-2
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
        hovertemplate=f"<b>{name}</b><br>x: %{{x:.3f}}<br>y: %{{y:.3f}}<br>z: %{{z:.3f}}<extra></extra>"
    )


def create_cylinder_mesh(center_x: float, center_y: float, center_z: float,
                         radius: float, height: float, color: str,
                         opacity: float = 0.8, name: str = "") -> dict:
    """
    建立 Plotly 圓柱體 Mesh3d (使用多邊形近似)
    """
    n_segments = 16
    theta = np.linspace(0, 2*np.pi, n_segments, endpoint=False)
    
    # 底部圓圈頂點
    x_bottom = center_x + radius * np.cos(theta)
    y_bottom = center_y + radius * np.sin(theta)
    z_bottom = np.full(n_segments, center_z - height/2)
    
    # 頂部圓圈頂點
    x_top = center_x + radius * np.cos(theta)
    y_top = center_y + radius * np.sin(theta)
    z_top = np.full(n_segments, center_z + height/2)
    
    # 合併所有頂點
    x = list(x_bottom) + list(x_top)
    y = list(y_bottom) + list(y_top)
    z = list(z_bottom) + list(z_top)
    
    # 三角形索引
    i_list, j_list, k_list = [], [], []
    
    # 側面 (每個矩形拆成 2 個三角形)
    for seg in range(n_segments):
        next_seg = (seg + 1) % n_segments
        # 三角形 1
        i_list.append(seg)
        j_list.append(next_seg)
        k_list.append(seg + n_segments)
        # 三角形 2
        i_list.append(next_seg)
        j_list.append(next_seg + n_segments)
        k_list.append(seg + n_segments)
    
    # 底面
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
        hovertemplate=f"<b>{name}</b><br>r: {radius*1e6:.1f}μm<br>h: {height*1e6:.1f}μm<extra></extra>"
    )


# ==================== 橫截面繪圖 (修正 Y 軸比例) ====================

def draw_stripline_cross_section(geo: StriplineGeometry, pitch: float, 
                                  via_enabled: bool, via_diameter: float, 
                                  via_density: float, n_channels: int):
    """
    繪製 Stripline 橫截面動態示意圖 (修正版)
    關鍵修正：取消 equal aspect，使用獨立縮放 + 放大 Y 軸顯示區域
    """
    from matplotlib.pyplot import subplots, Rectangle, Circle
    from matplotlib.patches import Patch
    import matplotlib.pyplot as plt
    
    fig, ax = subplots(figsize=(18, 10))

    w = geo.w              # mm
    h = geo.h              # mm
    t = geo.t / 1000       # mm
    s = pitch              # mm
    total_h = 2 * h + 3 * t

    n_draw = min(n_channels, 8)
    total_width = s * n_draw
    margin = s * 0.5

    colors = {
        'polyimide': '#E8DCC8',
        'polyimide_dark': '#C4B49A',
        'ag_nbti': '#B8860B',
        'ag_nbti_light': '#DAA520',
        'via': '#8B4513',
        'text': '#2C3E50',
        'dimension': '#E74C3C',
        'arrow': '#3498DB',
        'gnd_sep': '#D4AF37'
    }

    # 1. 下接地層
    gnd_bottom = Rectangle((-margin/2, -t), total_width + margin, t, 
                           facecolor=colors['ag_nbti'], edgecolor='black', linewidth=1.5)
    ax.add_patch(gnd_bottom)
    ax.text(total_width/2, -t/2, 'Bottom GND (Ag/NbTi)', 
            ha='center', va='center', fontsize=11, color='white', fontweight='bold')

    # 2. 下介電層
    dielectric_bottom = Rectangle((-margin/2, 0), total_width + margin, h, 
                                  facecolor=colors['polyimide'], edgecolor='black', 
                                  linewidth=1.5, alpha=0.7)
    ax.add_patch(dielectric_bottom)
    ax.text(-margin/2 + 0.05, h/2, f'Polyimide\\nεr=3.4\\n{h*1000:.0f} μm', 
            ha='left', va='center', fontsize=9, color=colors['text'])

    # 3. 信號層 + 接地分隔
    signal_y = h + t - t/2
    for i in range(n_draw):
        x_center = s * (i + 0.5)
        sig = Rectangle((x_center - w/2, signal_y), w, t, 
                        facecolor=colors['ag_nbti'], edgecolor='black', linewidth=1.5)
        ax.add_patch(sig)
        ax.text(x_center, signal_y + t/2, f'S{i+1}', ha='center', va='center', 
                fontsize=10, color='white', fontweight='bold')

        if i < n_draw - 1:
            gnd_sep_x = x_center + s/2
            gnd_sep_w = min(w * 0.25, s - w - 0.02)
            if gnd_sep_w > 0.01:
                gnd_sep = Rectangle((gnd_sep_x - gnd_sep_w/2, signal_y), gnd_sep_w, t,
                                    facecolor=colors['gnd_sep'], edgecolor='black', linewidth=1)
                ax.add_patch(gnd_sep)
                ax.text(gnd_sep_x, signal_y + t/2, 'G', ha='center', va='center',
                        fontsize=8, color='white', fontweight='bold')

    # 4. 上介電層
    dielectric_top = Rectangle((-margin/2, h + t), total_width + margin, h, 
                               facecolor=colors['polyimide'], edgecolor='black', 
                               linewidth=1.5, alpha=0.7)
    ax.add_patch(dielectric_top)
    ax.text(-margin/2 + 0.05, h + t + h/2, f'Polyimide\\nεr=3.4\\n{h*1000:.0f} μm', 
            ha='left', va='center', fontsize=9, color=colors['text'])

    # 5. 上接地層
    gnd_top = Rectangle((-margin/2, 2*h + 2*t), total_width + margin, t, 
                        facecolor=colors['ag_nbti'], edgecolor='black', linewidth=1.5)
    ax.add_patch(gnd_top)
    ax.text(total_width/2, 2*h + 2*t + t/2, 'Top GND (Ag/NbTi)', 
            ha='center', va='center', fontsize=11, color='white', fontweight='bold')

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
                f'Via Stitching\\nØ{via_diameter} μm\\n{via_density} /mm', 
                ha='left', va='center', fontsize=9, color=colors['via'],
                bbox=dict(boxstyle='round,pad=0.3', facecolor='wheat', alpha=0.6, edgecolor=colors['via']))

    # 尺寸標註
    arrow_y1 = -margin * 0.6
    ax.annotate('', xy=(s*0.5 - w/2, arrow_y1), xytext=(s*0.5 + w/2, arrow_y1),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text(s*0.5, arrow_y1 - 0.15, f'w = {w*1000:.0f} μm', ha='center', va='top',
            fontsize=10, color=colors['dimension'], fontweight='bold')

    arrow_y2 = -margin * 1.0
    ax.annotate('', xy=(s*0.5, arrow_y2), xytext=(s*1.5, arrow_y2),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text(s, arrow_y2 - 0.15, f'pitch = {s:.2f} mm', ha='center', va='top',
            fontsize=10, color=colors['dimension'], fontweight='bold')

    dim_x = total_width + margin*0.3
    ax.annotate('', xy=(dim_x, h + t), xytext=(dim_x, 2*h + 2*t),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text(dim_x + 0.15, 1.5*h + 1.5*t, f'h = {h*1000:.0f} μm', ha='left', va='center',
            fontsize=10, color=colors['dimension'], fontweight='bold', rotation=90)

    dim_x2 = total_width + margin*0.6
    ax.annotate('', xy=(dim_x2, 2*h + 2*t), xytext=(dim_x2, 2*h + 3*t),
                arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=1.5))
    ax.text(dim_x2 + 0.15, 2*h + 2.5*t, f't = {geo.t:.0f} μm', ha='left', va='center',
            fontsize=10, color=colors['arrow'], fontweight='bold', rotation=90)

    dim_x3 = -margin*0.4
    ax.annotate('', xy=(dim_x3, -t), xytext=(dim_x3, 2*h + 3*t),
                arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=1.5))
    ax.text(dim_x3 - 0.15, h + t, f'Total = {total_h*1000:.0f} μm', ha='right', va='center',
            fontsize=10, color=colors['arrow'], fontweight='bold', rotation=90)

    # 標題與圖例
    ax.set_title(f'Cri/oFlex3 Stripline Cross-Section View\\n'
                 f'({n_channels} channels, G-S-G, w={w*1000:.0f}μm, h={h*1000:.0f}μm, t={geo.t:.0f}μm)', 
                 fontsize=14, fontweight='bold', pad=20)

    legend_elements = [
        Patch(facecolor=colors['ag_nbti'], edgecolor='black', label='Ag/NbTi Conductor (GND/Signal)'),
        Patch(facecolor=colors['polyimide'], edgecolor='black', alpha=0.7, label='Polyimide Dielectric (εr=3.4)'),
        Patch(facecolor=colors['gnd_sep'], edgecolor='black', label='GND Separation'),
        Circle((0,0), 0.1, facecolor=colors['via'], label='GND Via')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9, 
              framealpha=0.9, title='Layer Legend')

    # 關鍵修正：取消 equal aspect，設定合理的 Y 軸範圍
    ax.set_xlim(-margin, total_width + margin * 1.5)
    y_display_range = total_h * 8
    ax.set_ylim(-y_display_range * 0.3, y_display_range * 0.7)
    ax.axis('off')

    plt.tight_layout()
    return fig


# ==================== Plotly 3D 立體透視 (互動式) ====================

def draw_stripline_3d_plotly(geo: StriplineGeometry, pitch: float, length: float, 
                              n_channels: int, via_enabled: bool = True,
                              via_diameter: float = 150, via_density: float = 2.0):
    """
    使用 Plotly 繪製互動式 3D Stripline 立體透視圖
    優勢：真 3D 渲染，可旋轉/縮放/平移，Streamlit 原生支援
    """
    import plotly.graph_objects as go
    
    w = geo.w / 1000          # mm -> m
    h = geo.h / 1000          # mm -> m
    t = geo.t / 1e6           # μm -> m
    L = length / 1000         # mm -> m
    s = pitch / 1000          # mm -> m
    n_draw = min(n_channels, 8)
    
    # 顏色定義 (Plotly 支援的顏色名稱或 hex)
    c_poly = '#E8DCC8'        # Polyimide 淡棕
    c_ag = '#B8860B'          # Ag/NbTi 暗金
    c_via = '#8B4513'         # Via 深棕
    c_gnd_sep = '#D4AF37'     # GND 分隔
    
    meshes = []
    
    # 層次 z 位置 (m)
    z0 = 0.0
    z1 = t
    z2 = t + h
    z3 = t + h + t
    z4 = t + h + t + h
    z5 = t + h + t + h + t
    
    total_w = s * n_draw
    margin = s * 0.4
    
    # ========== 1. 下接地層 ==========
    meshes.append(go.Mesh3d(**create_box_mesh(
        -margin/2, total_w + margin/2, 0, L, z0, z1,
        color=c_ag, opacity=0.95, name="Bottom GND"
    )))
    
    # ========== 2. 下介電層 ==========
    meshes.append(go.Mesh3d(**create_box_mesh(
        -margin/2, total_w + margin/2, 0, L, z1, z2,
        color=c_poly, opacity=0.6, name="Bottom Dielectric"
    )))
    
    # ========== 3. 信號層 + 接地分隔 ==========
    for i in range(n_draw):
        x_c = s * (i + 0.5)
        # 信號線
        meshes.append(go.Mesh3d(**create_box_mesh(
            x_c - w/2, x_c + w/2, 0, L, z2, z3,
            color=c_ag, opacity=0.95, name=f"Signal S{i+1}"
        )))
        
        # 接地分隔
        if i < n_draw - 1:
            g_x = x_c + s/2
            g_w = min(w * 0.25, s - w - 0.00002)
            if g_w > 0.00001:
                meshes.append(go.Mesh3d(**create_box_mesh(
                    g_x - g_w/2, g_x + g_w/2, 0, L, z2, z3,
                    color=c_gnd_sep, opacity=0.9, name="GND Separation"
                )))
    
    # ========== 4. 上介電層 ==========
    meshes.append(go.Mesh3d(**create_box_mesh(
        -margin/2, total_w + margin/2, 0, L, z3, z4,
        color=c_poly, opacity=0.6, name="Top Dielectric"
    )))
    
    # ========== 5. 上接地層 ==========
    meshes.append(go.Mesh3d(**create_box_mesh(
        -margin/2, total_w + margin/2, 0, L, z4, z5,
        color=c_ag, opacity=0.95, name="Top GND"
    )))
    
    # ========== 6. Via Stitching (圓柱) ==========
    if via_enabled:
        via_r = min(via_diameter / 2e6, t * 0.4, h * 0.3)
        via_spacing = 1.0 / via_density / 1000
        n_vias = int(total_w / via_spacing) + 2
        
        for i in range(n_vias):
            x_v = i * via_spacing
            if x_v > total_w + margin/2 or x_v < -margin/2:
                continue
            
            meshes.append(go.Mesh3d(**create_cylinder_mesh(
                x_v, L/2, z5/2, via_r, z5,
                color=c_via, opacity=0.8, name="GND Via"
            )))
    
    # ========== 7. 尺寸標註線 (Scatter3d) ==========
    # 總厚度標註線
    meshes.append(go.Scatter3d(
        x=[-margin, -margin], y=[0, 0], z=[z0, z5],
        mode='lines', line=dict(color='red', width=6),
        name='Total Thickness', hoverinfo='skip'
    ))
    
    # 長度標註線
    meshes.append(go.Scatter3d(
        x=[0, total_w], y=[-margin*2, -margin*2], z=[z0, z0],
        mode='lines', line=dict(color='blue', width=6),
        name='Length', hoverinfo='skip'
    ))
    
    # 寬度標註線
    meshes.append(go.Scatter3d(
        x=[0, total_w], y=[L + margin, L + margin], z=[z5, z5],
        mode='lines', line=dict(color='green', width=6),
        name='Width', hoverinfo='skip'
    ))
    
    # ========== 8. 建立 Figure ==========
    fig = go.Figure(data=meshes)
    
    # 設定 3D 場景
    fig.update_layout(
        title=dict(
            text=f'Cri/oFlex3 Stripline 3D Interactive View<br>'
                 f'<sup>{n_channels}ch G-S-G | L={length}mm | w={geo.w*1000:.0f}μm | h={geo.h*1000:.0f}μm | t={geo.t:.0f}μm</sup>',
            x=0.5, font=dict(size=16)
        ),
        scene=dict(
            xaxis=dict(
                title='Width (m)',
                showbackground=True,
                backgroundcolor='rgba(240,240,240,0.3)',
                gridcolor='rgba(200,200,200,0.3)',
                showspikes=False
            ),
            yaxis=dict(
                title='Length (m)',
                showbackground=True,
                backgroundcolor='rgba(240,240,240,0.3)',
                gridcolor='rgba(200,200,200,0.3)',
                showspikes=False
            ),
            zaxis=dict(
                title='Thickness (m)',
                showbackground=True,
                backgroundcolor='rgba(240,240,240,0.3)',
                gridcolor='rgba(200,200,200,0.3)',
                showspikes=False
            ),
            aspectmode='manual',
            aspectratio=dict(x=total_w*2, y=L*0.5, z=z5*15),  # 放大 z 軸以顯示層次
            camera=dict(
                eye=dict(x=1.8, y=-1.5, z=1.2),
                center=dict(x=0.3, y=0.3, z=0.1)
            )
        ),
        showlegend=True,
        legend=dict(
            yanchor="top", y=0.99,
            xanchor="left", x=0.01,
            bgcolor='rgba(255,255,255,0.8)'
        ),
        margin=dict(l=0, r=0, t=60, b=0),
        paper_bgcolor='white',
        plot_bgcolor='white',
        height=700
    )
    
    return fig


# ==================== Streamlit 主程式 ====================

def main():
    st.set_page_config(page_title="Cri/oFlex3 Stripline Designer", layout="wide")
    st.title("🔬 Cri/oFlex3 Stripline 多層結構設計器")
    st.markdown("---")

    with st.sidebar:
        st.subheader("⚙️ 設計參數")
        
        st.markdown("**幾何結構**")
        n_channels = st.radio("通道數", [4, 8, 16, 32], index=1, horizontal=True)
        pitch = st.slider("通道間距 Pitch (mm)", 0.5, 5.0, 2.0, 0.1)
        length = st.slider("傳輸線長度 (mm)", 100, 1500, 400, 50)
        sig_width = st.slider("信號線寬度 (μm)", 50, 500, 300, 10)
        sig_thickness = st.slider("導體厚度 (μm)", 1, 20, 5, 1)
        dielectric_thickness = st.slider("單層介電厚度 (μm)", 50, 300, 150, 10)

        st.markdown("**材料選擇**")
        conductor_material = st.radio("導體材料", ["Ag (銀)", "NbTi (超導)", "Cu (銅)"], 
                                       index=1, horizontal=True)
        dielectric_material = st.radio("介電材料", ["Polyimide Kapton"], 
                                        index=0, horizontal=True)

        st.markdown("**Via 設計**")
        via_enabled = st.checkbox("啟用 Via Stitching", value=True)
        via_density = st.slider("Via 密度 (個/mm)", 0.5, 5.0, 2.0, 0.1)
        via_diameter = st.slider("Via 直徑 (μm)", 50, 300, 150, 10)

        st.markdown("**操作條件**")
        frequency = st.slider("工作頻率 (GHz)", 0.1, 20.0, 6.0, 0.1)
        temp_stage = st.radio("溫度階段", 
                              ["300K → 40K", "40K → 4K", "4K → 1K", "1K → 100mK", "RT → mK (全段)"], 
                              index=1, horizontal=True)

        st.markdown("**計算選項**")
        calc_crosstalk = st.checkbox("計算串擾", value=True)
        calc_thermal = st.checkbox("計算熱負載", value=True)
        calc_loss = st.checkbox("計算插入損耗", value=True)

    geo = StriplineGeometry(
        w=sig_width / 1000,
        t=sig_thickness,
        h=dielectric_thickness / 1000,
        s=pitch,
        L=length,
        n_channels=n_channels
    )

    tab1, tab2, tab3 = st.tabs(["📐 橫截面視圖", "🔲 3D 互動透視 (Plotly)", "📊 參數摘要"])

    with tab1:
        st.subheader("Stripline 橫截面 (Cross-Section)")
        st.info("💡 此視圖已修正 Y 軸比例，多層結構清晰可見")
        fig_cross = draw_stripline_cross_section(
            geo, pitch, via_enabled, via_diameter, via_density, n_channels
        )
        st.pyplot(fig_cross)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("信號線寬", f"{sig_width} μm")
            st.metric("導體厚度", f"{sig_thickness} μm")
        with col2:
            st.metric("介電厚度", f"{dielectric_thickness} μm")
            st.metric("總厚度", f"{geo.total_thickness_um:.0f} μm")
        with col3:
            st.metric("通道間距", f"{pitch} mm")
            st.metric("通道數", f"{n_channels}")

    with tab2:
        st.subheader("Stripline 3D 互動透視 (Plotly)")
        st.info("💡 可旋轉、縮放、平移的互動式 3D 模型 | 點擊圖例可隱藏/顯示圖層")
        
        fig_3d = draw_stripline_3d_plotly(
            geo, pitch, length, n_channels, via_enabled, via_diameter, via_density
        )
        st.plotly_chart(fig_3d, use_container_width=True, height=700)
        
        st.markdown("""
        **操作說明：**
        - 🖱️ **左鍵拖曳**：旋轉視角
        - 🖱️ **右鍵拖曳**：平移畫面
        - 🖱️ **滾輪**：縮放
        - 📋 **圖例點擊**：隱藏/顯示特定圖層
        - 🔍 **懸停**：查看各點座標與尺寸
        """)

    with tab3:
        st.subheader("📋 設計參數摘要")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**幾何參數**")
            st.write(f"- **通道數 (n)**: {n_channels}")
            st.write(f"- **通道間距 (s)**: {pitch} mm")
            st.write(f"- **信號線寬 (w)**: {sig_width} μm ({geo.w:.3f} mm)")
            st.write(f"- **導體厚度 (t)**: {sig_thickness} μm ({geo.t/1000:.4f} mm)")
            st.write(f"- **介電厚度 (h)**: {dielectric_thickness} μm ({geo.h:.3f} mm)")
            st.write(f"- **傳輸線長度 (L)**: {length} mm")
            st.write(f"- **總厚度**: {geo.total_thickness_um:.1f} μm")
        
        with col2:
            st.markdown("**材料與操作條件**")
            st.write(f"- **導體**: {conductor_material}")
            st.write(f"- **介電質**: {dielectric_material}")
            st.write(f"- **工作頻率**: {frequency} GHz")
            st.write(f"- **溫度階段**: {temp_stage}")
            
            st.markdown("**Via 設計**")
            if via_enabled:
                st.write(f"- **Via 直徑**: {via_diameter} μm")
                st.write(f"- **Via 密度**: {via_density} 個/mm")
                st.write(f"- **Via 間距**: {1.0/via_density:.2f} mm")
            else:
                st.write("- Via Stitching: 未啟用")

        st.markdown("---")
        st.subheader("⚡ 特性阻抗估算 (簡化)")
        
        er = 3.4
        w_eff = geo.w + 1.25 * geo.t / 1000
        if w_eff > 0 and geo.h > 0:
            z0_approx = (60 / np.sqrt(er)) * np.log(4 * geo.h / (0.67 * np.pi * w_eff * (0.8 + geo.t/1000/geo.w)))
            z0_approx = max(10, min(200, z0_approx))
            
            st.write(f"""
            使用簡化 Stripline 公式估算：
            - **特性阻抗 Z₀ ≈ {z0_approx:.1f} Ω**
            - 相對介電常數 εr = {er}
            - 有效線寬 weff = {w_eff*1000:.1f} μm
            """)
        
        st.markdown("---")
        st.subheader("🔧 計算選項")
        opts = []
        if calc_crosstalk: opts.append("串擾分析")
        if calc_thermal: opts.append("熱負載分析")
        if calc_loss: opts.append("插入損耗分析")
        if opts:
            st.write(f"已啟用：{', '.join(opts)}")
        else:
            st.write("未啟用任何計算選項")


if __name__ == "__main__":
    main()
