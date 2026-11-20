from numpy import cos, linspace, pi, sin
from matplotlib.pyplot import Line2D, figure, rcParams, savefig, show, tight_layout
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, Polygon, Wedge

def 俯視圖():
# ============================================
# 圖 3: 俯視圖 - 通道與 Via 佈局
# ============================================
  fig = figure(figsize=(20, 24)) # 建立大圖 (20x24)
  ax3 = fig.add_subplot(3, 2, 3)

  outer = Rectangle((0, 0), 400, 16, facecolor='#FFF8DC', edgecolor='black', linewidth=2.5) # 繪製外框
  ax3.add_patch(outer)

  for ch in range(8): # 繪製 8 條通道 (中心線，藍色)
      y = 1 + ch * 2
      ax3.plot([0, 400], [y, y], color='#1E90FF', linewidth=3, alpha=0.8, zorder=3)
      ax3.text(-8, y, f'CH{ch+1}', ha='right', va='center', fontsize=9, color='darkblue', fontweight='bold')

  via_y_positions = [1, 3, 5, 7, 9, 11, 13, 15] # 繪製 Via 陣列 (交錯式，紅色圓點)
  for row_idx in range(40):
      y_base = 5 + row_idx * 10
      if y_base > 395:
          break

      if row_idx % 2 == 0: # 交錯排列
          via_x = [1, 3, 5, 7, 9, 11, 13, 15]
          marker_color = '#FF4444'
      else:
          via_x = [3, 5, 7, 9, 11, 13]
          marker_color = '#FF8888'

      for vx in via_x:
          if vx <= 15:
              via = Circle((y_base, vx), 0.15, facecolor=marker_color, edgecolor='darkred', linewidth=0.5, alpha=0.7, zorder=4)
              ax3.add_patch(via)

  ax3.annotate('', xy=(0, -3), xytext=(400, -3), arrowprops=dict(arrowstyle='<->', color='green', lw=2.5)) # 標註長度
  ax3.text(200, -5, 'Length: 200 - 1000 mm (customizable)', ha='center', fontsize=11, color='green', fontweight='bold')

  ax3.annotate('', xy=(-12, 0), xytext=(-12, 16), arrowprops=dict(arrowstyle='<->', color='green', lw=2.5)) # 標註寬度
  ax3.text(-16, 8, 'Width: 16 mm', ha='center', fontsize=11, color='green', fontweight='bold', rotation=90, va='center')

  ax3.annotate('', xy=(30, 1), xytext=(30, 3), arrowprops=dict(arrowstyle='<->', color='purple', lw=2)) # 標註 Pitch
  ax3.text(33, 2, 'Pitch:\n2 mm', fontsize=9, color='purple', fontweight='bold', rotation=90, va='center')

  ax3.annotate('', xy=(45, 1), xytext=(55, 1), arrowprops=dict(arrowstyle='<->', color='orange', lw=2)) # 標註 Via Pitch
  ax3.text(50, 2.5, 'Via Pitch:\n10 mm', fontsize=9, color='orange', fontweight='bold', ha='center')

  ax3.set_xlim(-25, 430)
  ax3.set_ylim(-8, 22)
  ax3.set_xlabel('Length (mm)', fontsize=11)
  ax3.set_ylabel('Width (mm)', fontsize=11)
  ax3.set_title('Top View - Channel & Via Layout\n(8 Channels, Staggered Via Array)', fontsize=13, fontweight='bold')
  ax3.set_aspect('equal')

  legend_elements = [
      Line2D([0], [0], color='#1E90FF', linewidth=3, label='Signal Channel (8x)'),
      Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF4444', markersize=10, label='Via (Ground Connection)'),
  ] # 圖例
  ax3.legend(handles=legend_elements, loc='upper right', fontsize=10)
  return fig

def 挖洞():
# ============================================
# 圖 4: Via 詳細結構剖面放大圖
# ============================================
  fig = figure(figsize=(20, 24)) # 建立大圖 (20x24)
  ax4 = fig.add_subplot(3, 2, 4)

# 繪製 Via 剖面 (放大 10 倍)
  scale = 10

# 各層邊界 (從 bottom 到 top)
  layer_data = [
      (0, 0.05, '#CD853F', 'L7: Bottom Coverlay\n50 μm'),
      (0.05, 0.055, '#A9A9A9', 'L6: Bottom Ground\n5 μm'),
      (0.055, 0.125, '#F4A460', 'L5: Bottom Dielectric\n70 μm'),
      (0.125, 0.131, '#FFD700', 'L4: Signal Layer\n6 μm'),
      (0.131, 0.201, '#F4A460', 'L3: Top Dielectric\n70 μm'),
      (0.201, 0.206, '#A9A9A9', 'L2: Top Ground\n5 μm'),
      (0.206, 0.256, '#CD853F', 'L1: Top Coverlay\n50 μm'),
  ]

  for y_bottom, y_top, color, label in layer_data:
      rect = Rectangle((-0.3, y_bottom), 0.6, y_top - y_bottom,
                       facecolor=color, edgecolor='black', linewidth=1)
      ax4.add_patch(rect)

# Via 孔 (貫穿 L2-L6，避開 L4 訊號線)
  via_top = 0.206  # Top Ground bottom
  via_bottom = 0.055  # Bottom Ground top
  via_height = via_top - via_bottom

# Via 鑽孔 (白色)
  via_drill = Rectangle((-0.075, via_bottom), 0.15, via_height,
                        facecolor='white', edgecolor='black', linewidth=2, hatch='///')
  ax4.add_patch(via_drill)

# Via 電鍍填充 (銀色)
  via_plating = Rectangle((-0.065, via_bottom), 0.13, via_height,
                          facecolor='#C0C0C0', edgecolor='black', linewidth=1)
  ax4.add_patch(via_plating)

# 標註各層 (右側)
  for y_bottom, y_top, color, label in layer_data:
      ax4.text(0.45, (y_bottom + y_top)/2, label, fontsize=8, va='center', ha='left')

# Via 尺寸標註
  ax4.annotate('', xy=(-0.25, via_bottom), xytext=(-0.25, via_top),
              arrowprops=dict(arrowstyle='<->', color='red', lw=2))
  ax4.text(-0.32, (via_bottom + via_top)/2, f'Via Depth\n151 μm',
           fontsize=9, color='red', fontweight='bold', ha='center', va='center', rotation=90)

  ax4.annotate('', xy=(-0.075, via_bottom - 0.01), xytext=(0.075, via_bottom - 0.01),
              arrowprops=dict(arrowstyle='<->', color='blue', lw=2))
  ax4.text(0, via_bottom - 0.025, 'Ø150 μm', fontsize=9, color='blue',
           fontweight='bold', ha='center')

# 標註訊號線避開 Via
  ax4.text(0, 0.128, 'Signal Line\n(220 μm)', fontsize=8, ha='center',
           color='darkgoldenrod', fontweight='bold')

  ax4.set_xlim(-0.5, 1.2)
  ax4.set_ylim(-0.05, 0.3)
  ax4.set_xlabel('Width (mm)', fontsize=11)
  ax4.set_ylabel('Thickness (mm)', fontsize=11)
  ax4.set_title('Via Cross-Section Detail (10x Magnified)\n(Blind Via: L2 ↔ L6)',
                fontsize=13, fontweight='bold')
  ax4.set_aspect('auto')
  return fig

def 連接器端():
# ============================================
# 圖 5: 連接器端部細節 (SMA)
# ============================================
  fig = figure(figsize=(20, 24)) # 建立大圖 (20x24)
  ax5 = fig.add_subplot(3, 2, 5)

# 繪製端部放大圖 (SMA 連接器區域，長度 10mm)
  end_length = 10

# 柔性線本體
  flex_body = Rectangle((0, 0), end_length, 16, facecolor='#F4A460',
                        edgecolor='black', linewidth=1.5, alpha=0.3)
  ax5.add_patch(flex_body)

# 8 個 SMA 連接器排列
  for ch in range(8):
      x_center = 1 + ch * 2

      # 訊號焊盤 (2.5 x 2.0 mm) - 金色
      signal_pad = Rectangle((5 - 0.125, x_center - 0.1), 0.25, 0.2,
                             facecolor='#FFD700', edgecolor='black', linewidth=1.5)
      ax5.add_patch(signal_pad)

      # 接地焊盤 (3.0 x 2.0 mm) - 虛線框
      gnd_pad = Rectangle((5 - 0.175, x_center - 0.1), 0.35, 0.2,
                          facecolor='none', edgecolor='black', linewidth=1.5, linestyle='--')
      ax5.add_patch(gnd_pad)

      # Via 圍繞連接器 (4個 Via)
      for vy in [x_center - 0.25, x_center + 0.25]:
          for vx in [4.5, 5.5]:
              via = Circle((vx, vy), 0.075, facecolor='red', edgecolor='darkred', alpha=0.6)
              ax5.add_patch(via)

      # 通道標註
      ax5.text(5, x_center - 0.35, f'CH{ch+1}', ha='center', fontsize=8,
               fontweight='bold', color='darkblue')

# 繪製 SMA 連接器輪廓 (簡化)
  for ch in range(8):
      x_center = 1 + ch * 2
      # SMA 本體 (六角形簡化)
      sma_body = Rectangle((5.3, x_center - 0.2), 1.5, 0.4,
                           facecolor='#C0C0C0', edgecolor='black', linewidth=1)
      ax5.add_patch(sma_body)
      ax5.text(6.05, x_center, 'SMA', ha='center', va='center', fontsize=7, fontweight='bold')

# 標註尺寸
  ax5.annotate('', xy=(5, 0.5), xytext=(5, 2.5),
              arrowprops=dict(arrowstyle='<->', color='purple', lw=2))
  ax5.text(4.5, 1.5, 'Pitch:\n2 mm', fontsize=9, color='purple',
           fontweight='bold', ha='center', rotation=90, va='center')

  ax5.annotate('', xy=(4.825, 1), xytext=(5.175, 1),
              arrowprops=dict(arrowstyle='<->', color='green', lw=1.5))
  ax5.text(5, 0.6, '2.5 mm', fontsize=8, color='green', ha='center')

  ax5.set_xlim(3, 8)
  ax5.set_ylim(-1, 17)
  ax5.set_xlabel('Length (mm)', fontsize=11)
  ax5.set_ylabel('Width (mm)', fontsize=11)
  ax5.set_title('Connector End Detail\n(SMA Right-Angle, 8 Channels)',
                fontsize=13, fontweight='bold')
  ax5.set_aspect('equal')
  return fig

def 彎曲半徑():
# ============================================
# 圖 6: 彎曲半徑與安裝示意 + 尺寸總表
# ============================================
  fig = figure(figsize=(20, 24)) # 建立大圖 (20x24)
  ax6 = fig.add_subplot(3, 2, 6)

# 繪製彎曲示意
  theta = linspace(0, pi, 100)
  r = 5  # 最小彎曲半徑 5mm

  center_x = 10
  center_y = 8

# 直線段
  ax6.plot([0, center_x - r], [center_y, center_y], 'b-', linewidth=10, alpha=0.4, label='Straight')
  ax6.plot([center_x + r, 20], [center_y, center_y], 'b-', linewidth=10, alpha=0.4)

# 彎曲段 (180° U-turn)
  arc_x = center_x + r * cos(theta)
  arc_y = center_y + r * sin(theta)
  ax6.plot(arc_x, arc_y, 'r-', linewidth=10, alpha=0.5, label='Bend (R=5mm)')

# 標註彎曲半徑
  ax6.annotate('', xy=(center_x, center_y), xytext=(center_x, center_y + r),
              arrowprops=dict(arrowstyle='<->', color='green', lw=2.5))
  ax6.text(center_x + 0.8, center_y + r/2, 'R = 5 mm\n(Minimum)', fontsize=11,
           color='green', fontweight='bold', va='center')

# 標註 180° 旋轉長度
  ax6.annotate('', xy=(center_x - r, center_y - 1), xytext=(center_x + r, center_y - 1),
              arrowprops=dict(arrowstyle='<->', color='purple', lw=2))
  ax6.text(center_x, center_y - 2.5, '180° Rotation ≈ 10 mm', ha='center',
           fontsize=10, color='purple', fontweight='bold')

# 繪製通道截面示意 (右上角)
  for i in range(8):
      y_offset = 14 + i * 0.35
      rect = Rectangle((2, y_offset), 4, 0.25, facecolor='#FFD700',
                       edgecolor='black', linewidth=0.5)
      ax6.add_patch(rect)
      ax6.text(1.5, y_offset + 0.125, f'CH{i+1}', ha='right', va='center', fontsize=7)

  總尺寸 = """
  ┌─────────────────────────────────────┐
  │     CRI/OFLEX 3 DIMENSION SUMMARY   │
  ├─────────────────────────────────────┤
  │  Overall Dimensions                 │
  │    Length:     200 - 1000 mm        │
  │    Width:      16 mm                │
  │    Thickness:  0.30 mm (300 μm)     │
  ├─────────────────────────────────────┤
  │  Channel Specifications             │
  │    Channels:   8                    │
  │    Pitch:      2.00 mm              │
  │    Line Width: 220 μm               │
  │    Impedance:  50 Ω                 │
  ├─────────────────────────────────────┤
  │  Layer Stack-up (7 layers)          │
  │    L1: Top Coverlay     50 μm       │
  │    L2: Top Ground        5 μm       │
  │    L3: Top Dielectric   70 μm       │
  │    L4: Signal Layer      6 μm       │
  │    L5: Bottom Dielectric 70 μm      │
  │    L6: Bottom Ground     5 μm       │
  │    L7: Bottom Coverlay  50 μm       │
  ├─────────────────────────────────────┤
  │  Via Specifications                 │
  │    Type:       Blind Via (L2↔L6)    │
  │    Diameter:   150 μm               │
  │    Pitch:      10 mm (staggered)    │
  ├─────────────────────────────────────┤
  │  Mechanical                         │
  │    Min Bend R: 5 mm                 │
  │    Max Tensile: 50 N                │
  │    Vacuum Leak: < 10⁻⁶ mbar·L/s     │
  └─────────────────────────────────────┘
  """ # 尺寸總表 (文字框)

  #ax6.text(12, 10, 總尺寸, fontsize=9, family='monospace', verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

  ax6.set_xlim(-2, 28)
  ax6.set_ylim(-4, 20)
  ax6.set_xlabel('Length (mm)', fontsize=11)
  ax6.set_ylabel('Width (mm)', fontsize=11)
  ax6.set_title('Bend Radius & Dimension Summary', fontsize=13, fontweight='bold')
  ax6.set_aspect('equal')
  ax6.legend(loc='lower left', fontsize=10)
  return fig, 總尺寸

"""
tight_layout()
savefig('/mnt/agents/output/CF3_Dimension_Diagram_v2.png', dpi=300, bbox_inches='tight')
show()

print("✓ Cri/oFlex 3 完整尺寸示意圖已繪製完成！")
print("  包含：3D外觀、Stack-up剖面、俯視佈局、Via詳圖、連接器細節、彎曲示意")
"""

def 橫截面():
# ============================================
# 圖 2: 橫截面 Stack-up 詳圖
# ============================================
  fig = figure(figsize=(20, 24)) # 建立大圖 (20x24)
  ax2 = fig.add_subplot(3, 2, 2)

# 各層定義 (從上到下)
  layers = [
      ('L1: Top Coverlay', 'Polyimide', '#CD853F', 50),
      ('L2: Top Ground', 'Ag/NbTi', '#A9A9A9', 5),
      ('L3: Top Dielectric', 'Polyimide', '#F4A460', 70),
      ('L4: Signal Layer', 'Ag/NbTi', '#FFD700', 6),
      ('L5: Bottom Dielectric', 'Polyimide', '#F4A460', 70),
      ('L6: Bottom Ground', 'Ag/NbTi', '#A9A9A9', 5),
      ('L7: Bottom Coverlay', 'Polyimide', '#CD853F', 50),
  ]

# 繪製橫截面
  y_pos = 0
  layer_positions = []
  for i, (name, material, color, thickness) in enumerate(layers):
      thickness_mm = thickness / 1000
      rect = Rectangle((0, y_pos), 16, thickness_mm, facecolor=color, edgecolor='black', linewidth=1.5)
      ax2.add_patch(rect)

      ax2.text(16.5, y_pos + thickness_mm/2, f'{name}\n{material}  {thickness}μm', ha='left', va='center', fontsize=9, fontweight='bold') # 標註層名稱（右側）

      layer_positions.append((name, y_pos, y_pos + thickness_mm, thickness))
      y_pos += thickness_mm

# 繪製 8 條訊號線 (在 Signal Layer 內)
  signal_layer_idx = 3
  signal_y_bottom = layer_positions[signal_layer_idx][1]
  signal_y_top = layer_positions[signal_layer_idx][2]

  for ch in range(8):
      x_center = 1 + ch * 2  # 2mm pitch
      line_width_mm = 0.22  # 220 μm
      line_rect = Rectangle((x_center - line_width_mm/2, signal_y_bottom),
                            line_width_mm, signal_y_top - signal_y_bottom,
                            facecolor='#FFD700', edgecolor='black', linewidth=0.8)
      ax2.add_patch(line_rect)

      # 通道標註
      if ch < 4:  # 只標註前4條避免擁擠
          ax2.text(x_center, signal_y_top + 0.005, f'CH{ch+1}',
                  ha='center', va='bottom', fontsize=7, color='red', fontweight='bold')

# 繪製 Via (貫穿上接地層到訊號層)
  via_x_positions = [1, 3, 5, 7, 9, 11, 13, 15]
  for vx in via_x_positions:
      # Via 從 Top Ground 貫穿到 Bottom Ground
      via_bottom = layer_positions[1][1]  # Top Ground bottom
      via_top = layer_positions[5][2]      # Bottom Ground top
      via_height = via_top - via_bottom

      via = Rectangle((vx - 0.075, via_bottom), 0.15, via_height,
                      facecolor='white', edgecolor='black', linewidth=1.5, hatch='///')
      ax2.add_patch(via)

      # Via 填充（電鍍層）
      via_fill = Rectangle((vx - 0.065, via_bottom), 0.13, via_height,
                           facecolor='#C0C0C0', edgecolor='none')
      ax2.add_patch(via_fill)

# 總厚度標註（右側箭頭）
  ax2.annotate('', xy=(18.5, 0), xytext=(18.5, 0.3),
              arrowprops=dict(arrowstyle='<->', color='red', lw=2.5))
  ax2.text(19, 0.15, 'Total\n300 μm', fontsize=12, color='red', fontweight='bold',
           ha='center', va='center', rotation=90)

# 通道 Pitch 標註
  ax2.annotate('', xy=(1, -0.04), xytext=(3, -0.04),
              arrowprops=dict(arrowstyle='<->', color='blue', lw=1.5))
  ax2.text(2, -0.055, 'Pitch: 2 mm', ha='center', fontsize=9, color='blue', fontweight='bold')

# 線寬標註
  ax2.annotate('', xy=(1 - 0.11, signal_y_bottom - 0.02), xytext=(1 + 0.11, signal_y_bottom - 0.02),
              arrowprops=dict(arrowstyle='<->', color='purple', lw=1.5))
  ax2.text(1, signal_y_bottom - 0.035, '220 μm', ha='center', fontsize=8, color='purple')

  ax2.set_xlim(-1, 21)
  ax2.set_ylim(-0.08, 0.38)
  ax2.set_xlabel('Width (mm)', fontsize=11)
  ax2.set_ylabel('Thickness (mm)', fontsize=11)
  ax2.set_title('Cross-Section Stack-up Detail\n(7-Layer Structure)', fontsize=13, fontweight='bold')
  ax2.set_aspect('auto')
  return fig

def 立體框架():

# ============================================
# 圖 1: 整體外觀 3D 示意圖
# ============================================
  fig = figure(figsize=(20, 24)) # 建立大圖 (20x24)
  ax1 = fig.add_subplot(3, 2, 1, projection='3d')

  length = 400  # mm Cri/oFlex 3 尺寸
  width = 16    # mm
  height = 0.3  # mm

  bottom_corners = [
      [0, 0, 0],
      [length, 0, 0],
      [length, width, 0],
      [0, width, 0]
  ] # 繪製主體框架 底面四個角
  top_corners = [
      [0, 0, height],
      [length, 0, height],
      [length, width, height],
      [0, width, height]
  ] # 頂面四個角

  ax1.add_collection3d(Poly3DCollection([bottom_corners], alpha=0.2, facecolor='blue', edgecolor='navy')) # 繪製底面
  ax1.add_collection3d(Poly3DCollection([top_corners], alpha=0.4, facecolor='cyan', edgecolor='red', linewidth=2)) # 繪製頂面

  for i in range(4): # 繪製側邊線
      next_i = (i + 1) % 4
      ax1.plot3D([bottom_corners[i][0], bottom_corners[next_i][0]], [bottom_corners[i][1], bottom_corners[next_i][1]], [bottom_corners[i][2], bottom_corners[next_i][2]], 'navy', alpha=0.5) # 底面邊
      ax1.plot3D([top_corners[i][0], top_corners[next_i][0]], [top_corners[i][1], top_corners[next_i][1]], [top_corners[i][2], top_corners[next_i][2]], 'red', linewidth=2) # 頂面邊
      ax1.plot3D([bottom_corners[i][0], top_corners[i][0]], [bottom_corners[i][1], top_corners[i][1]], [bottom_corners[i][2], top_corners[i][2]], 'green', alpha=0.7) # 垂直邊

  ax1.text(length/2, -3, height/2, f'Length: {length} mm', fontsize=11, ha='center', color='darkblue', fontweight='bold') # 標註尺寸
  ax1.text(length+15, width/2, height/2, f'Width: {width} mm', fontsize=11, ha='center', color='darkblue', fontweight='bold', rotation=90)
  ax1.text(-20, width/2, height/2, f'Thickness: {height} mm', fontsize=11, ha='center', color='darkred', fontweight='bold', rotation=90)

  for ch in range(8): # 標註 8 通道
      y_pos = 1 + ch * 2
      ax1.plot3D([length/2, length/2], [y_pos, y_pos], [height, height+0.05], 'orange', linewidth=2)
      ax1.text(length/2, y_pos, height+0.08, f'CH{ch+1}', fontsize=8, ha='center', color='darkorange')

  ax1.set_xlabel('Length (mm)', fontsize=11)
  ax1.set_ylabel('Width (mm)', fontsize=11)
  ax1.set_zlabel('Thickness (mm)', fontsize=11)
  ax1.set_title('Cri/oFlex 3 - 3D Overall View\n(400mm × 16mm × 0.3mm)', fontsize=13, fontweight='bold')
  ax1.set_xlim(-30, 460)
  ax1.set_ylim(-5, 25)
  ax1.set_zlim(-0.1, 0.6)
  return fig
