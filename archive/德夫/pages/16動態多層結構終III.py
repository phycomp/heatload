from numpy import cos, full, linspace, pi, sin
from matplotlib.pyplot import subplots, Rectangle, Circle, tight_layout
from matplotlib.patches import Patch
import matplotlib.pyplot as plt
from streamlit import pyplot, sidebar, radio, text_input, subheader, slider, markdown, checkbox, plotly_chart
from streamlit import empty
from dataclasses import dataclass
from plotly.graph_objects import Mesh3d, Scatter3d, Figure

def create_box_mesh(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float,
                    color: str, opacity: float = 1.0, name: str = "") -> dict:
    """
    建立 Plotly Mesh3d 的 vertices 和 indices
    返回 dict 可直接傳入 Mesh3d(**dict)
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
import plotly.graph_objects as go

#if __name__ == "__main__":
    # 建立一個 1x1x1 的立方體
    #box_mesh = create_box_mesh( x0=0, x1=1, y0=0, y1=1, z0=0, z1=1, color='B8860B', opacity=0.8, name="Test Box")
    
    #fig = Figure(data=[Mesh3d(**box_mesh)])
    #fig.update_layout( title="3D Box Mesh 測試", scene=dict(aspectmode='cube'), height=600)
    #fig.show()
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

# ==================== 橫截面繪圖 (修正 aspect 比例) ====================
def 橫截面(geo: StriplineGeometry, pitch: float, via_enabled: bool, via_diameter: float, via_density: float, n_channels: int):
  """
  繪製 Stripline 橫截面動態示意圖 (修正 aspect 比例版)
  關鍵修正：使用 equal aspect 保持真實比例
  """
  w = geo.w              # mm
  h = geo.h              # mm
  t = geo.t / 1000       # mm
  s = pitch              # mm
  total_h = 2 * h + 3 * t
  n_draw = min(n_channels, 8)
  total_width = s * n_draw
  margin = s * 0.5

  # 計算真實比例，設定合適的 figure size
  aspect_ratio = total_width / total_h
  fig_width = 16
  fig_height = max(6, fig_width / aspect_ratio * 0.6)  # 稍微壓縮高度以便於顯示

  fig, ax = subplots(figsize=(fig_width, fig_height))

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
  gnd_bottom = Rectangle((-margin/2, -t), total_width + margin, t, facecolor=colors['ag_nbti'], edgecolor='black', linewidth=1.5)
  ax.add_patch(gnd_bottom)
  ax.text(total_width/2, -t/2, 'Bottom GND (Ag/NbTi)', ha='center', va='center', fontsize=11, color='white', fontweight='bold')

  # 2. 下介電層
  dielectric_bottom = Rectangle((-margin/2, 0), total_width + margin, h, facecolor=colors['polyimide'], edgecolor='black', linewidth=1.5, alpha=0.7)
  ax.add_patch(dielectric_bottom)
  ax.text(-margin/2 + 0.05, h/2, f'Polyimide\nεr=3.4\n{h*1000:.0f} μm', ha='left', va='center', fontsize=9, color=colors['text'])

  # 3. 信號層 + 接地分隔
  signal_y = h + t - t/2
  for i in range(n_draw):
      x_center = s * (i + 0.5)
      sig = Rectangle((x_center - w/2, signal_y), w, t, facecolor=colors['ag_nbti'], edgecolor='black', linewidth=1.5)
      ax.add_patch(sig)
      ax.text(x_center, signal_y + t/2, f'S{i+1}', ha='center', va='center', fontsize=10, color='white', fontweight='bold')
      if i < n_draw - 1:
          gnd_sep_x = x_center + s/2
          gnd_sep_w = min(w * 0.25, s - w - 0.02)
          if gnd_sep_w > 0.01:
              gnd_sep = Rectangle((gnd_sep_x - gnd_sep_w/2, signal_y), gnd_sep_w, t, facecolor=colors['gnd_sep'], edgecolor='black', linewidth=1)
              ax.add_patch(gnd_sep)
              ax.text(gnd_sep_x, signal_y + t/2, 'G', ha='center', va='center', fontsize=8, color='white', fontweight='bold')

  # 4. 上介電層
  dielectric_top = Rectangle((-margin/2, h + t), total_width + margin, h, facecolor=colors['polyimide'], edgecolor='black', linewidth=1.5, alpha=0.7)
  ax.add_patch(dielectric_top)
  ax.text(-margin/2 + 0.05, h + t + h/2, f'Polyimide\nεr=3.4\n{h*1000:.0f} μm', 
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
              f'Via Stitching\nØ{via_diameter} μm\n{via_density} /mm', 
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
  ax.set_title(f'Cri/oFlex3 Stripline Cross-Section View\n'
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

  # 關鍵修正：使用 equal aspect 保持真實比例
  ax.set_aspect('equal')
  ax.set_xlim(-margin*1.5, total_width + margin * 2)
  ax.set_ylim(-t*3, 2*h + 3*t + t*2)

  tight_layout()
  return fig


# ==================== Plotly 3D 立體透視 (修正 aspect 比例) ====================
def 立體(geo: StriplineGeometry, pitch: float, length: float, n_channels: int, via_enabled: bool = True, via_diameter: float = 150, via_density: float = 2.0):
  """
  使用 Plotly 繪製互動式 3D Stripline 立體透視圖 (修正 aspect 比例)
  關鍵修正：使用真實比例，不再誇張 Z 軸
  """

  w = geo.w / 1000          # mm -> m
  h = geo.h / 1000          # mm -> m
  t = geo.t / 1e6           # μm -> m
  L = length / 1000         # mm -> m
  s = pitch / 1000          # mm -> m
  n_draw = min(n_channels, 8)

  # 顏色定義
  c_poly = '#E8DCC8'
  c_ag = '#B8860B'
  c_via = '#8B4513'
  c_gnd_sep = '#D4AF37'

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
  meshes.append(Mesh3d(**create_box_mesh(
      -margin/2, total_w + margin/2, 0, L, z0, z1,
      color=c_ag, opacity=0.95, name="Bottom GND"
  )))

  # ========== 2. 下介電層 ==========
  meshes.append(Mesh3d(**create_box_mesh(
      -margin/2, total_w + margin/2, 0, L, z1, z2,
      color=c_poly, opacity=0.6, name="Bottom Dielectric"
  )))

  # ========== 3. 信號層 + 接地分隔 ==========
  for i in range(n_draw):
      x_c = s * (i + 0.5)
      # 信號線
      meshes.append(Mesh3d(**create_box_mesh(
          x_c - w/2, x_c + w/2, 0, L, z2, z3,
          color=c_ag, opacity=0.95, name=f"Signal S{i+1}"
      )))
      # 接地分隔
      if i < n_draw - 1:
          g_x = x_c + s/2
          g_w = min(w * 0.25, s - w - 0.00002)
          if g_w > 0.00001:
              meshes.append(Mesh3d(**create_box_mesh(
                  g_x - g_w/2, g_x + g_w/2, 0, L, z2, z3,
                  color=c_gnd_sep, opacity=0.9, name="GND Separation"
              )))

  # ========== 4. 上介電層 ==========
  meshes.append(Mesh3d(**create_box_mesh(
      -margin/2, total_w + margin/2, 0, L, z3, z4,
      color=c_poly, opacity=0.6, name="Top Dielectric"
  )))

  # ========== 5. 上接地層 ==========
  meshes.append(Mesh3d(**create_box_mesh(
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
          meshes.append(Mesh3d(**create_cylinder_mesh(
              x_v, L/2, z5/2, via_r, z5,
              color=c_via, opacity=0.8, name="GND Via"
          )))

  # ========== 7. 尺寸標註線 (Scatter3d) ==========
  # 總厚度標註線
  meshes.append(Scatter3d(
      x=[-margin, -margin], y=[0, 0], z=[z0, z5],
      mode='lines', line=dict(color='red', width=6),
      name='Total Thickness', hoverinfo='skip'
  ))
  # 長度標註線
  meshes.append(Scatter3d(
      x=[0, total_w], y=[-margin*2, -margin*2], z=[z0, z0],
      mode='lines', line=dict(color='blue', width=6),
      name='Length', hoverinfo='skip'
  ))
  # 寬度標註線
  meshes.append(Scatter3d(
      x=[0, total_w], y=[L + margin, L + margin], z=[z5, z5],
      mode='lines', line=dict(color='green', width=6),
      name='Width', hoverinfo='skip'
  ))

  # ========== 8. 建立 Figure ==========
  fig = Figure(data=meshes)

  # 計算真實比例
  # 由於厚度通常遠小於寬度和長度，我們使用 data 模式讓 Plotly 自動處理
  # 但為了可視化效果，可以適度放大 Z 軸（最多 3-5 倍，而非 15 倍）
  z_exaggeration = min(5.0, max(1.0, total_w / z5 * 0.3))

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
          # 關鍵修正：使用 data 模式保持真實比例
          aspectmode='data',
          camera=dict(
              eye=dict(x=2.0, y=-2.0, z=1.5),
              center=dict(x=0.0, y=0.0, z=0.0)
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
with sidebar:
    subheader("⚙️ 設計參數")
    
    markdown("**幾何結構**")
    n_channels = radio("通道數", [4, 8, 16, 32], index=1, horizontal=True)
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

def 改進立體圖(geo: StriplineGeometry, pitch: float, length: float,
                             n_channels: int, via_enabled: bool = True,
                             via_diameter: float = 150, via_density: float = 2.0,
                             show_exploded: bool = False, 
                             z_exaggeration: float = 3.0):
    """
    使用 Plotly 繪製互動式 3D Stripline 立體透視圖（改進版）
    
    改進重點：
    1. 可調 Z 軸放大倍數（預設 3 倍，而非 15 倍）
    2. 支援 exploded view（爆炸圖）顯示各層
    3. 優化相機角度和光照
    4. 改善薄層可視性
    5. 增強材質和透明度效果
    """
    import plotly.graph_objects as go
    from plotly.figure_factory import create_trisurf
    
    # 單位轉換
    w = geo.w / 1000          # mm -> m
    h = geo.h / 1000          # mm -> m
    t = geo.t / 1e6           # μm -> m
    L = length / 1000         # mm -> m
    s = pitch / 1000          # mm -> m
    n_draw = min(n_channels, 8)
    
    # 顏色定義（改進：使用更鮮明的顏色）
    c_poly = '#D4C5A9'        # Polyimide - 調整為更明顯的米色
    c_ag = '#B8860B'          # Ag/NbTi 暗金
    c_via = '#8B4513'         # Via 深棕
    c_gnd_sep = '#FFD700'     # GND 分隔 - 改用金色更明顯
    
    meshes = []
    
    # 層次 z 位置 (m)
    z0 = 0.0
    z1 = t
    z2 = t + h
    z3 = t + h + t
    z4 = t + h + t + h
    z5 = t + h + t + h + t
    
    total_w = s * n_draw
    margin = s * 0.3
    
    # 計算爆炸圖偏移量
    if show_exploded:
        explode_offset = [0, z1*5, z2*3, z3*5, z4*3, z5*5]
    else:
        explode_offset = [0, 0, 0, 0, 0, 0]
    
    # ========== 1. 下接地層 ==========
    meshes.append(go.Mesh3d(**create_box_mesh_improved(
        -margin/2, total_w + margin/2, 0, L, 
        z0 + explode_offset[0], z1 + explode_offset[0],
        color=c_ag, opacity=0.95, name="Bottom GND",
        flatshading=True
    )))
    
    # ========== 2. 下介電層（改進透明度）==========
    meshes.append(go.Mesh3d(**create_box_mesh_improved(
        -margin/2, total_w + margin/2, 0, L, 
        z1 + explode_offset[1], z2 + explode_offset[1],
        color=c_poly, opacity=0.5, name="Bottom Dielectric",
        flatshading=False
    )))
    
    # ========== 3. 信號層 + 接地分隔 ==========
    for i in range(n_draw):
        x_c = s * (i + 0.5)
        # 信號線（使用更亮的顏色）
        meshes.append(go.Mesh3d(**create_box_mesh_improved(
            x_c - w/2, x_c + w/2, 0, L, 
            z2 + explode_offset[2], z3 + explode_offset[2],
            color=c_ag, opacity=1.0, name=f"Signal S{i+1}",
            flatshading=True
        )))
        
        # 接地分隔
        if i < n_draw - 1:
            g_x = x_c + s/2
            g_w = min(w * 0.25, s - w - 0.00002)
            if g_w > 0.00001:
                meshes.append(go.Mesh3d(**create_box_mesh_improved(
                    g_x - g_w/2, g_x + g_w/2, 0, L, 
                    z2 + explode_offset[2], z3 + explode_offset[2],
                    color=c_gnd_sep, opacity=0.9, name="GND Separation",
                    flatshading=True
                )))
    
    # ========== 4. 上介電層 ==========
    meshes.append(go.Mesh3d(**create_box_mesh_improved(
        -margin/2, total_w + margin/2, 0, L, 
        z3 + explode_offset[3], z4 + explode_offset[3],
        color=c_poly, opacity=0.5, name="Top Dielectric",
        flatshading=False
    )))
    
    # ========== 5. 上接地層 ==========
    meshes.append(go.Mesh3d(**create_box_mesh_improved(
        -margin/2, total_w + margin/2, 0, L, 
        z4 + explode_offset[4], z5 + explode_offset[4],
        color=c_ag, opacity=0.95, name="Top GND",
        flatshading=True
    )))
    
    # ========== 6. Via Stitching（改進圓柱渲染）==========
    if via_enabled:
        via_r = min(via_diameter / 2e6, t * 0.4, h * 0.3)
        via_spacing = 1.0 / via_density / 1000
        n_vias = int(total_w / via_spacing) + 2
        
        # 計算 via 的 Z 中心（考慮爆炸圖）
        via_z_center = z5/2 + (explode_offset[4] + explode_offset[0])/2
        via_height = z5 + (explode_offset[4] - explode_offset[0])
        
        for i in range(n_vias):
            x_v = i * via_spacing
            if x_v > total_w + margin/2 or x_v < -margin/2:
                continue
            meshes.append(go.Mesh3d(**create_cylinder_mesh_improved(
                x_v, L/2, via_z_center, via_r, via_height,
                color=c_via, opacity=0.85, name="GND Via",
                n_segments=24  # 增加段數使圓柱更平滑
            )))
    
    # ========== 7. 改進的尺寸標註 ==========
    # 總厚度標註線
    meshes.append(go.Scatter3d(
        x=[-margin*1.5, -margin*1.5], y=[0, 0], 
        z=[z0 + explode_offset[0], z5 + explode_offset[4]],
        mode='lines+text',
        line=dict(color='#E74C3C', width=5, dash='dash'),
        text=['', f'Total Thickness<br>{(z5*1e6):.0f} μm'],
        textposition='middle right',
        name='Total Thickness',
        hoverinfo='skip'
    ))
    
    # 長度標註線
    meshes.append(go.Scatter3d(
        x=[0, total_w], y=[-margin*2, -margin*2], 
        z=[z0 + explode_offset[0], z0 + explode_offset[0]],
        mode='lines+text',
        line=dict(color='#3498DB', width=5),
        text=['', f'Length<br>{L*1000:.0f} mm'],
        textposition='top center',
        name='Length',
        hoverinfo='skip'
    ))
    
    # ========== 8. 建立 Figure ==========
    fig = go.Figure(data=meshes)
    
    # 計算合理的 aspect ratio
    # 關鍵改進：使用適度的 Z 軸放大（3-5 倍），而非 15 倍
    z_scale = min(z_exaggeration, max(1.0, total_w / z5 * 0.5))
    
    # 設定 3D 場景（改進版）
    fig.update_layout(
        title=dict(
            text=f'<b>Cri/oFlex3 Stripline 3D Interactive View</b><br>'
                 f'<sup style="color:#666">{n_channels}ch G-S-G | '
                 f'L={length}mm | w={geo.w*1000:.0f}μm | '
                 f'h={geo.h*1000:.0f}μm | t={geo.t:.0f}μm | '
                 f'Z-scale: {z_scale:.1f}x</sup>',
            x=0.5, 
            font=dict(size=18, family="Arial Black")
        ),
        scene=dict(
            xaxis=dict(
                title=dict(
                    text='Width (X) [m]',
                    font=dict(size=14, color='#2C3E50')
                ),
                showbackground=True,
                backgroundcolor='rgba(245,245,245,0.5)',
                gridcolor='rgba(200,200,200,0.5)',
                showspikes=True,
                spikecolor='rgba(100,100,100,0.5)',
                spikethickness=1
            ),
            yaxis=dict(
                title=dict(
                    text='Length (Y) [m]',
                    font=dict(size=14, color='#2C3E50')
                ),
                showbackground=True,
                backgroundcolor='rgba(245,245,245,0.5)',
                gridcolor='rgba(200,200,200,0.5)',
                showspikes=True,
                spikecolor='rgba(100,100,100,0.5)',
                spikethickness=1
            ),
            zaxis=dict(
                title=dict(
                    text='Thickness (Z) [m] ' + f'(×{z_scale:.1f})',
                    font=dict(size=14, color='#2C3E50')
                ),
                showbackground=True,
                backgroundcolor='rgba(245,245,245,0.5)',
                gridcolor='rgba(200,200,200,0.5)',
                showspikes=True,
                spikecolor='rgba(100,100,100,0.5)',
                spikethickness=1
            ),
            # 關鍵改進：使用 manual aspect ratio 但更合理的比例
            aspectmode='manual',
            aspectratio=dict(
                x=1.0,           # X 軸基準
                y=max(0.3, L/total_w * 0.8),  # Y 軸根據實際長寬比
                z=z_scale        # Z 軸適度放大
            ),
            # 改進的相機角度（等軸測視角）
            camera=dict(
                eye=dict(x=1.5, y=-1.8, z=1.2),
                center=dict(x=0.0, y=0.0, z=0.0),
                up=dict(x=0, y=0, z=1)
            ),
            bgcolor='rgba(255,255,255,0.95)'
        ),
        showlegend=True,
        legend=dict(
            yanchor="top", y=0.98,
            xanchor="left", x=0.01,
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='rgba(0,0,0,0.2)',
            borderwidth=1,
            font=dict(size=11)
        ),
        margin=dict(l=0, r=0, t=80, b=0),
        paper_bgcolor='white',
        plot_bgcolor='white',
        height=750,
        hovermode='closest'
    )
    
    return fig


# ==================== 改進的 Box Mesh 函數 ====================
def create_box_mesh_improved(x0: float, x1: float, y0: float, y1: float, 
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
def create_cylinder_mesh_improved(center_x: float, center_y: float, center_z: float,
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
MENU, 表單=[], ['橫截面', '立體圖', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  狀態=empty()
  狀態.code([])
  狀態=empty()
  狀態.code([])
geo = StriplineGeometry(
    w=sig_width / 1000,
    t=sig_thickness,
    h=dielectric_thickness / 1000,
    s=pitch,
    L=length,
    n_channels=n_channels)
if menu==len(表單): #
  pass
elif menu==MENU[1]: #
  立體素 = 改進立體圖( geo, pitch, length, n_channels, via_enabled, via_diameter, via_density)
  plotly_chart(立體素, use_container_width=True, height=700)
  #pyplot(fig)
elif menu==MENU[0]: #立體圖
  pass
  fig=橫截面(geo, pitch, via_enabled, via_diameter, via_density, n_channels)
  pyplot(fig)
