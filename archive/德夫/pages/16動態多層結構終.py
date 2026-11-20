# 建立完整的 PyVista 3D Stripline 視覺化 + 修正橫截面

"""
Cri/oFlex3 Stripline 動態多層結構視覺化 v3
改進：
1. 橫截面取消 equal aspect，使用獨立縮放 + 放大 Y 軸顯示區域
2. 立體透視改用 PyVista 真 3D 渲染，避免 2D 投影失真
3. 內嵌所有資料結構，無需外部模組
"""

import streamlit as st
from dataclasses import dataclass
from typing import List, Dict
import numpy as np
import os

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

    # ========== 繪製多層膜結構 ==========
    
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

    # ========== Via Stitching ==========
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

    # ========== 尺寸標註 ==========
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

    # 關鍵修正：取消 equal aspect，設定合理的 Y 軸範圍以放大顯示多層結構
    ax.set_xlim(-margin, total_width + margin * 1.5)
    # Y 軸範圍設定為總厚度的約 8-10 倍，讓每層結構清晰可見
    y_display_range = total_h * 8
    ax.set_ylim(-y_display_range * 0.3, y_display_range * 0.7)
    ax.axis('off')

    plt.tight_layout()
    return fig


# ==================== PyVista 真 3D 立體透視 ====================

def draw_stripline_3d_pyvista(geo: StriplineGeometry, pitch: float, length: float, 
                               n_channels: int, via_enabled: bool = True,
                               via_diameter: float = 150, via_density: float = 2.0):
    """
    使用 PyVista 繪製真 3D Stripline 立體透視圖
    優勢：真正的 3D 渲染，可旋轉視角，無 2D 投影失真
    """
    import pyvista as pv
    
    w = geo.w / 1000          # mm -> m (PyVista 使用公尺單位)
    h = geo.h / 1000          # mm -> m
    t = geo.t / 1e6           # μm -> m
    L = length / 1000         # mm -> m
    s = pitch / 1000          # mm -> m
    n_draw = min(n_channels, 8)
    
    # 顏色定義 (RGB 0-1)
    c_poly = [0.91, 0.86, 0.78]      # Polyimide 淡棕
    c_ag = [0.72, 0.53, 0.04]        # Ag/NbTi 暗金
    c_via = [0.55, 0.27, 0.07]       # Via 深棕
    c_gnd_sep = [0.83, 0.69, 0.22]   # GND 分隔
    
    plotter = pv.Plotter(off_screen=True, window_size=[1200, 800])
    plotter.set_background('white')
    
    # 層次 z 位置 (從下往上，單位: m)
    z0 = 0.0
    z1 = t
    z2 = t + h
    z3 = t + h + t
    z4 = t + h + t + h
    z5 = t + h + t + h + t
    
    total_w = s * n_draw
    margin = s * 0.4
    
    # ========== 1. 下接地層 (Bottom GND) ==========
    bottom_gnd = pv.Box(
        bounds=[-margin/2, total_w + margin/2, 0, L, z0, z1]
    )
    plotter.add_mesh(bottom_gnd, color=c_ag, opacity=0.95, 
                     show_edges=True, edge_color='black', line_width=1)
    
    # ========== 2. 下介電層 ==========
    bottom_dielectric = pv.Box(
        bounds=[-margin/2, total_w + margin/2, 0, L, z1, z2]
    )
    plotter.add_mesh(bottom_dielectric, color=c_poly, opacity=0.6,
                     show_edges=True, edge_color='black', line_width=0.5)
    
    # ========== 3. 信號層 + 接地分隔 ==========
    for i in range(n_draw):
        x_center = s * (i + 0.5)
        # 信號線
        signal = pv.Box(
            bounds=[x_center - w/2, x_center + w/2, 0, L, z2, z3]
        )
        plotter.add_mesh(signal, color=c_ag, opacity=0.95,
                         show_edges=True, edge_color='black', line_width=1)
        
        # 接地分隔
        if i < n_draw - 1:
            gnd_sep_x = x_center + s/2
            gnd_sep_w = min(w * 0.25, s - w - 0.00002)
            if gnd_sep_w > 0.00001:
                gnd_sep = pv.Box(
                    bounds=[gnd_sep_x - gnd_sep_w/2, gnd_sep_x + gnd_sep_w/2, 0, L, z2, z3]
                )
                plotter.add_mesh(gnd_sep, color=c_gnd_sep, opacity=0.9,
                                 show_edges=True, edge_color='black', line_width=0.5)
    
    # ========== 4. 上介電層 ==========
    top_dielectric = pv.Box(
        bounds=[-margin/2, total_w + margin/2, 0, L, z3, z4]
    )
    plotter.add_mesh(top_dielectric, color=c_poly, opacity=0.6,
                     show_edges=True, edge_color='black', line_width=0.5)
    
    # ========== 5. 上接地層 (Top GND) ==========
    top_gnd = pv.Box(
        bounds=[-margin/2, total_w + margin/2, 0, L, z4, z5]
    )
    plotter.add_mesh(top_gnd, color=c_ag, opacity=0.95,
                     show_edges=True, edge_color='black', line_width=1)
    
    # ========== 6. Via Stitching ==========
    if via_enabled:
        via_r = min(via_diameter / 2e6, t * 0.4, h * 0.3)  # m
        via_spacing = 1.0 / via_density / 1000  # mm -> m
        n_vias = int(total_w / via_spacing) + 2
        
        for i in range(n_vias):
            x_v = i * via_spacing
            if x_v > total_w + margin/2 or x_v < -margin/2:
                continue
            
            # Via 圓柱 (貫穿全層)
            via_cylinder = pv.Cylinder(
                center=(x_v, L/2, z5/2),
                direction=(0, 0, 1),
                radius=via_r,
                height=z5
            )
            plotter.add_mesh(via_cylinder, color=c_via, opacity=0.8,
                             show_edges=True, edge_color='black', line_width=0.5)
    
    # ========== 7. 尺寸標註線 (使用線條) ==========
    # 總厚度標註
    plotter.add_lines(
        np.array([[-margin, 0, z0], [-margin, 0, z5]]),
        color='red', width=3
    )
    
    # 長度標註
    plotter.add_lines(
        np.array([[0, -margin*2, z0], [total_w, -margin*2, z0]]),
        color='blue', width=3
    )
    
    # ========== 8. 視角與標題 ==========
    plotter.camera_position = [
        (total_w * 1.5, -L * 0.8, z5 * 3),   # 相機位置
        (total_w / 2, L / 2, z5 / 2),         # 焦點
        (0, 0, 1)                              # 上方向
    ]
    plotter.camera.zoom(0.8)
    
    # 添加標題文字 (使用 3D 文字)
    plotter.add_text(
        f"Cri/oFlex3 Stripline 3D View\\n{n_channels}ch G-S-G | L={length}mm | w={geo.w*1000:.0f}μm | h={geo.h*1000:.0f}μm",
        position='upper_edge', font_size=14, color='black', font='arial'
    )
    
    # 添加座標軸標籤
    plotter.add_axes(line_width=2, color='black')
    
    # 截圖
    img = plotter.screenshot()
    plotter.close()
    
    return img


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

    tab1, tab2, tab3 = st.tabs(["📐 橫截面視圖", "🔲 3D 立體透視 (PyVista)", "📊 參數摘要"])

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
        st.subheader("Stripline 3D 立體透視 (PyVista 真 3D 渲染)")
        st.info("💡 使用 PyVista 進行真 3D 渲染，無 2D 投影失真")
        
        try:
            img_3d = draw_stripline_3d_pyvista(
                geo, pitch, length, n_channels, via_enabled, via_diameter, via_density
            )
            st.image(img_3d, use_container_width=True)
        except Exception as e:
            st.error(f"3D 渲染失敗: {e}")
            st.info("請確認 PyVista 已正確安裝。如無法使用，橫截面視圖已可完整展示結構。")

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
