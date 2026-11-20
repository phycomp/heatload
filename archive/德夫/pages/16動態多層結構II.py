from streamlit import checkbox, columns, info, markdown, metric, pyplot, radio, set_page_config, sidebar, slider, subheader, tabs, title, write, text_input
from matplotlib.pyplot import tight_layout
from numpy import log, pi, sqrt
"""
Cri/oFlex3 Stripline 動態多層結構視覺化 v2
修正：橫截面比例、立體透視視角、Streamlit 介面整合
"""

import streamlit as st
from dataclasses import dataclass
from typing import List, Dict
import numpy as np

# ==================== 資料結構定義 (內嵌，避免模組導入問題) ====================

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
        """總厚度 = 2h + 3t (mm)"""
        return 2 * self.h + 3 * (self.t / 1000)

    @property
    def total_thickness_um(self) -> float:
        """總厚度 (μm)"""
        return self.total_thickness_mm * 1000


# ==================== 繪圖函數 ====================

def 橫截面(geo: StriplineGeometry, pitch: float, 
                                  via_enabled: bool, via_diameter: float, 
                                  via_density: float, n_channels: int):
    """
    繪製 Stripline 橫截面動態示意圖 (修正版)
    修正：使用獨立 X/Y 縮放，避免厚度/寬度比例極度失真
    """
    from matplotlib.pyplot import subplots, Rectangle, Circle
    from matplotlib.patches import Patch
    import matplotlib.pyplot as plt
    
    # 使用較大的圖形尺寸，並調整高度以顯示多層結構
    fig, ax = subplots(figsize=(18, 10))

    # 尺寸轉換
    w = geo.w              # 信號線寬 (mm)
    h = geo.h              # 單層介電厚 (mm)
    t = geo.t / 1000       # 導體厚 (μm -> mm)
    s = pitch              # 通道間距 (mm)
    total_h = 2 * h + 3 * t  # 總厚度 (mm)

    # 繪圖區域設定
    n_draw = min(n_channels, 8)
    total_width = s * n_draw
    margin = s * 0.5

    # 顏色定義
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

    # ========== 繪製多層膜結構 ==========
    
    # 1. 下接地層 (Bottom GND)
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
    ax.text(-margin/2 + 0.05, h/2, f'Polyimide\nεr=3.4\n{h*1000:.0f} μm', 
            ha='left', va='center', fontsize=9, color=colors['text'])

    # 3. 信號層 (多通道) + 接地分隔
    signal_y = h + t - t/2  # 信號層底部 y 座標 (修正：對齊介電層上緣)
    for i in range(n_draw):
        x_center = s * (i + 0.5)
        
        # 信號線
        sig = Rectangle((x_center - w/2, signal_y), w, t, 
                        facecolor=colors['ag_nbti'], edgecolor='black', linewidth=1.5)
        ax.add_patch(sig)
        ax.text(x_center, signal_y + t/2, f'S{i+1}', ha='center', va='center', 
                fontsize=10, color='white', fontweight='bold')

        # 接地分隔 (G-S-G)
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

    # 5. 上接地層 (Top GND)
    gnd_top = Rectangle((-margin/2, 2*h + 2*t), total_width + margin, t, 
                        facecolor=colors['ag_nbti'], edgecolor='black', linewidth=1.5)
    ax.add_patch(gnd_top)
    ax.text(total_width/2, 2*h + 2*t + t/2, 'Top GND (Ag/NbTi)', 
            ha='center', va='center', fontsize=11, color='white', fontweight='bold')

    # ========== Via Stitching ==========
    if via_enabled:
        via_spacing = 1.0 / via_density
        n_vias_x = int(total_width / via_spacing) + 2
        via_r = min(via_diameter / 2000, t * 0.4, h * 0.4)

        for i in range(n_vias_x):
            x_via = i * via_spacing
            if x_via > total_width + margin/2 or x_via < -margin/2:
                continue
                
            # 上層 Via
            via_top_y = 2*h + 2*t - via_r
            via_top = Circle((x_via, via_top_y), via_r, 
                             facecolor=colors['via'], edgecolor='black', linewidth=1)
            ax.add_patch(via_top)
            
            # 下層 Via
            via_bottom_y = -t + via_r
            via_bottom = Circle((x_via, via_bottom_y), via_r,
                                facecolor=colors['via'], edgecolor='black', linewidth=1)
            ax.add_patch(via_bottom)
            
            # 連接線
            ax.plot([x_via, x_via], [via_top_y - via_r, via_bottom_y + via_r], 
                    color=colors['via'], linewidth=2, alpha=0.6, linestyle='--')

        # Via 資訊標註
        ax.text(total_width + margin*0.3, h + t, 
                f'Via Stitching\\nØ{via_diameter} μm\\n{via_density} /mm', 
                ha='left', va='center', fontsize=9, color=colors['via'],
                bbox=dict(boxstyle='round,pad=0.3', facecolor='wheat', alpha=0.6, edgecolor=colors['via']))

    # ========== 尺寸標註 ==========
    
    # 信號線寬度 w
    arrow_y1 = -margin * 0.6
    ax.annotate('', xy=(s*0.5 - w/2, arrow_y1), xytext=(s*0.5 + w/2, arrow_y1),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text(s*0.5, arrow_y1 - 0.15, f'w = {w*1000:.0f} μm', ha='center', va='top',
            fontsize=10, color=colors['dimension'], fontweight='bold')

    # Pitch s
    arrow_y2 = -margin * 1.0
    ax.annotate('', xy=(s*0.5, arrow_y2), xytext=(s*1.5, arrow_y2),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text(s, arrow_y2 - 0.15, f'pitch = {s:.2f} mm', ha='center', va='top',
            fontsize=10, color=colors['dimension'], fontweight='bold')

    # 介電厚度 h
    dim_x = total_width + margin*0.3
    ax.annotate('', xy=(dim_x, h + t), xytext=(dim_x, 2*h + 2*t),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text(dim_x + 0.15, 1.5*h + 1.5*t, f'h = {h*1000:.0f} μm', ha='left', va='center',
            fontsize=10, color=colors['dimension'], fontweight='bold', rotation=90)

    # 導體厚度 t
    dim_x2 = total_width + margin*0.6
    ax.annotate('', xy=(dim_x2, 2*h + 2*t), xytext=(dim_x2, 2*h + 3*t),
                arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=1.5))
    ax.text(dim_x2 + 0.15, 2*h + 2.5*t, f't = {geo.t:.0f} μm', ha='left', va='center',
            fontsize=10, color=colors['arrow'], fontweight='bold', rotation=90)

    # 總厚度
    dim_x3 = -margin*0.4
    ax.annotate('', xy=(dim_x3, -t), xytext=(dim_x3, 2*h + 3*t),
                arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=1.5))
    ax.text(dim_x3 - 0.15, h + t, f'Total = {total_h*1000:.0f} μm', ha='right', va='center',
            fontsize=10, color=colors['arrow'], fontweight='bold', rotation=90)

    # ========== 標題與圖例 ==========
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

    # 修正：使用 auto 而非 equal，避免極端比例失真
    ax.set_xlim(-margin, total_width + margin * 1.5)
    ax.set_ylim(-margin * 1.5, total_h + margin * 2.5)
    ax.axis('off')

    plt.tight_layout()
    return fig


def 立體透視(geo: StriplineGeometry, pitch: float, length: float, n_channels: int, via_enabled: bool = True, via_diameter: float = 150, via_density: float = 2.0):
    """
    繪製 Stripline 3D 立體透視示意圖 (等角投影) - 修正版
    修正：調整深度縮放比例，避免過度傾斜
    """
    from matplotlib.pyplot import subplots, Rectangle, Circle, Polygon
    from matplotlib.patches import Patch
    import matplotlib.pyplot as plt
    
    fig, ax = subplots(figsize=(18, 10))

    w = geo.w
    h = geo.h
    t = geo.t / 1000
    # 修正：長度縮放比例調整，避免深度過大
    L = min(length / 8, total_w * 2.5) if (total_w := pitch * min(n_channels, 6)) else length / 8
    s = pitch
    n_draw = min(n_channels, 6)

    # 修正：等角投影參數調整，使視角更自然
    dx = 0.25 * L
    dy = 0.15 * L

    # 顏色定義
    c_poly = '#E8DCC8'
    c_poly_dark = '#C4B49A'
    c_ag = '#B8860B'
    c_ag_top = '#DAA520'
    c_ag_side = '#8B6914'
    c_via = '#8B4513'
    c_text = '#2C3E50'
    c_dim = '#E74C3C'
    c_arrow = '#3498DB'

    def draw_3d_block(x, y, w_blk, h_blk, d, face_c, edge_c='black', 
                      top_c=None, side_c=None, alpha=1.0, zorder=2):
        """繪製 3D 塊狀體：前立面 + 頂面 + 右側面"""
        if top_c is None:
            top_c = face_c
        if side_c is None:
            side_c = face_c
            
        rect = Rectangle((x, y), w_blk, h_blk,
                        facecolor=face_c, edgecolor=edge_c,
                        linewidth=1.2, alpha=alpha, zorder=zorder)
        ax.add_patch(rect)
        if d <= 0:
            return
            
        top = Polygon([
            [x, y + h_blk],
            [x + w_blk, y + h_blk],
            [x + w_blk + dx, y + h_blk + dy],
            [x + dx, y + h_blk + dy]
        ], facecolor=top_c, edgecolor=edge_c, linewidth=0.9, alpha=alpha, zorder=zorder-1)
        ax.add_patch(top)
        
        side = Polygon([
            [x + w_blk, y],
            [x + w_blk, y + h_blk],
            [x + w_blk + dx, y + h_blk + dy],
            [x + w_blk + dx, y + dy]
        ], facecolor=side_c, edgecolor=edge_c, linewidth=0.8, alpha=alpha*0.8, zorder=zorder-1)
        ax.add_patch(side)
        
        ax.plot([x, x + dx], [y, y + dy], color=edge_c, linewidth=0.6, alpha=0.4, zorder=zorder-1)
        ax.plot([x + w_blk, x + w_blk + dx], [y, y + dy],
                color=edge_c, linewidth=0.6, alpha=0.4, zorder=zorder-1)

    total_w = s * n_draw
    margin = s * 0.4

    # 層次 z 位置 (從下往上)
    z0 = 0.0
    z1 = t
    z2 = t + h
    z3 = t + h + t
    z4 = t + h + t + h
    z5 = t + h + t + h + t

    # 1. 下接地層
    draw_3d_block(-margin/2, z0, total_w + margin, t, L,
                  c_ag, 'black', c_ag_top, c_ag_side, alpha=0.95, zorder=2)
    ax.text(total_w/2, z0 + t/2, 'Bottom GND', ha='center', va='center',
            fontsize=9, color='white', fontweight='bold', zorder=3)

    # 2. 下介電層
    draw_3d_block(-margin/2, z1, total_w + margin, h, L,
                  c_poly, 'black', c_poly_dark, alpha=0.55, zorder=2)
    ax.text(-margin/2 - 0.2, z1 + h/2, f'Polyimide\\nεr=3.4\\n{h*1000:.0f}μm',
            ha='right', va='center', fontsize=8, color=c_text, zorder=3)

    # 3. 信號層 + 接地分隔
    for i in range(n_draw):
        x_c = s * (i + 0.5)
        draw_3d_block(x_c - w/2, z2, w, t, L,
                      c_ag, 'black', c_ag_top, c_ag_side, alpha=0.95, zorder=3)
        ax.text(x_c, z2 + t/2, f'S{i+1}', ha='center', va='center',
                fontsize=8, color='white', fontweight='bold', zorder=4)
        if i < n_draw - 1:
            g_x = x_c + s/2
            g_w = min(w * 0.25, s - w - 0.02)
            if g_w > 0.01:
                draw_3d_block(g_x - g_w/2, z2, g_w, t, L,
                              '#D4AF37', 'black', '#F0E68C', alpha=0.9, zorder=3)
                ax.text(g_x, z2 + t/2, 'G', ha='center', va='center',
                        fontsize=7, color='white', zorder=4)

    # 4. 上介電層
    draw_3d_block(-margin/2, z3, total_w + margin, h, L,
                  c_poly, 'black', c_poly_dark, alpha=0.55, zorder=2)
    ax.text(-margin/2 - 0.2, z3 + h/2, f'Polyimide\\nεr=3.4\\n{h*1000:.0f}μm',
            ha='right', va='center', fontsize=8, color=c_text, zorder=3)

    # 5. 上接地層
    draw_3d_block(-margin/2, z4, total_w + margin, t, L,
                  c_ag, 'black', c_ag_top, c_ag_side, alpha=0.95, zorder=2)
    ax.text(total_w/2, z4 + t/2, 'Top GND', ha='center', va='center',
            fontsize=9, color='white', fontweight='bold', zorder=3)

    # 6. Via Stitching
    if via_enabled:
        via_r = min(via_diameter / 2000, t * 0.4, h * 0.3)
        via_spacing = 1.0 / via_density
        n_vias = int(total_w / via_spacing) + 2
        
        for i in range(n_vias):
            x_v = i * via_spacing
            if x_v > total_w + margin/2 or x_v < -margin/2:
                continue
                
            v = Circle((x_v, z0 + t/2), via_r,
                       facecolor=c_via, edgecolor='black', linewidth=1, zorder=5)
            ax.add_patch(v)
            
            v_d = Circle((x_v + dx, z0 + t/2 + dy), via_r,
                         facecolor=c_via, edgecolor='black', linewidth=1, zorder=5)
            ax.add_patch(v_d)
            
            ax.plot([x_v, x_v + dx], [z0 + t/2, z0 + t/2 + dy],
                    color=c_via, linewidth=2, alpha=0.7, zorder=4)
            
            ax.plot([x_v, x_v], [z0 + t/2, z4 + t/2],
                    color=c_via, linewidth=1.5, linestyle='--', alpha=0.4, zorder=4)
            
            v_top = Circle((x_v, z4 + t/2), via_r,
                           facecolor=c_via, edgecolor='black', linewidth=1, zorder=5)
            ax.add_patch(v_top)

    # 尺寸標註
    ax.annotate('', xy=(-margin * 1.0, z0), xytext=(-margin * 1.0, z5),
                arrowprops=dict(arrowstyle='<->', color=c_dim, lw=1.5))
    ax.text(-margin * 1.3, z5/2, f'Total\\n{z5*1000:.0f} μm',
            ha='right', va='center', fontsize=10, color=c_dim, fontweight='bold')

    ax.annotate('', xy=(0, -margin * 0.8), xytext=(total_w + dx, -margin * 0.8 + dy),
                arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=1.5))
    ax.text(total_w/2 + dx/2, -margin * 1.0 + dy/2,
            f'L = {length} mm', ha='center', va='top',
            fontsize=11, color=c_arrow, fontweight='bold')

    ax.annotate('', xy=(0, z5 + margin*0.5), xytext=(total_w, z5 + margin*0.5),
                arrowprops=dict(arrowstyle='<->', color=c_arrow, lw=1.5))
    ax.text(total_w/2, z5 + margin*0.8, f'W = {total_w:.2f} mm ({n_channels} ch)',
            ha='center', va='bottom', fontsize=10, color=c_arrow, fontweight='bold')

    # 圖例
    legend_elements = [
        Patch(facecolor=c_ag, edgecolor='black', label='Ag/NbTi Conductor'),
        Patch(facecolor=c_poly, edgecolor='black', alpha=0.55, label='Polyimide (εr=3.4)'),
        Circle((0,0), 0.1, facecolor=c_via, label='GND Via')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9, framealpha=0.9)

    ax.set_title(f'Cri/oFlex3 Stripline 3D Perspective View\\n'
                 f'({n_channels} ch, G-S-G, L={length}mm, w={w*1000:.0f}μm, h={h*1000:.0f}μm)',
                 fontsize=14, fontweight='bold', pad=20)

    ax.set_xlim(-margin * 3, total_w + dx + margin * 1.5)
    ax.set_ylim(-margin * 1.5, z5 + dy + margin * 2)
    ax.axis('off')

    plt.tight_layout()
    return fig


# ==================== Streamlit 主程式 ====================

def main():
    st.set_page_config(page_title="Cri/oFlex3 Stripline Designer", layout="wide")
    st.title("🔬 Cri/oFlex3 Stripline 多層結構設計器")
    st.markdown("---")

with st.sidebar: # 側邊欄 - 參數輸入
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

# 建立幾何結構物件
geo = StriplineGeometry(
  w=sig_width / 1000,
  t=sig_thickness,
  h=dielectric_thickness / 1000,
  s=pitch,
  L=length,
  n_channels=n_channels
)
from streamlit import empty
MENU, 表單=[], ['橫截面', '立體圖', '規格摘要']
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
elif menu==MENU[0]: #立體圖
    # 主區域 - 分頁顯示
    tab1, tab2, tab3 = st.tabs(["📐 橫截面視圖", "🔲 立體透視圖", "📊 參數摘要"])

    with tab1:
        st.subheader("Stripline 橫截面 (Cross-Section)")
        fig_cross = 橫截面( geo, pitch, via_enabled, via_diameter, via_density, n_channels)
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
        st.subheader("Stripline 立體透視 (3D Perspective)")
        fig_3d = 立體透視(
            geo, pitch, length, n_channels, via_enabled, via_diameter, via_density
        )
        st.pyplot(fig_3d)
        
        st.info(f"""
        **3D 視圖參數：**
        - 結構：Ground-Signal-Ground (G-S-G) 多層膜
        - 導體材料：{conductor_material}
        - 介電材料：{dielectric_material} (εr ≈ 3.4)
        - 總寬度：{pitch * n_channels:.1f} mm
        - 總厚度：{geo.total_thickness_um:.0f} μm
        - 傳輸線長度：{length} mm
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
