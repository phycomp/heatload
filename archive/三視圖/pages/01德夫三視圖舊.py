from matplotlib.pyplot import figure, rcParams, savefig, show
from numpy import abs, argmax, exp, linspace, meshgrid, sin, zeros_like
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Polygon
from matplotlib.gridspec import GridSpec
import matplotlib.patheffects as path_effects
import numpy as np
from matplotlib.pyplot import rcParams, savefig, show, subplots, tight_layout
from streamlit import pyplot

# 設置中文字體
plt.rcParams['font.family'] = ['WenQuanYi Zen Hei', 'Noto Sans CJK JP', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# Cri/oFlex 3 規格
# ============================================================
N_CHANNELS = 8
PITCH = 2.0
THICKNESS = 0.3
LENGTH = 400
BEND_RADIUS = 5
IMPEDANCE = 50

DIELECTRIC_THICKNESS = 0.25
GROUND_THICKNESS = 0.025
SIGNAL_WIDTH = 0.4
TOTAL_WIDTH = N_CHANNELS * PITCH

SMA_BODY_LEN = 12
SMA_BODY_DIA = 6
SMA_THREAD_LEN = 5

COLOR_POLYIMIDE = '#D4A574'
COLOR_SILVER = '#C0C0C0'
COLOR_GROUND = '#A8A8A8'
COLOR_SIGNAL = '#FFD700'
COLOR_CONNECTOR = '#B87333'
COLOR_FILTER = '#4A90D9'

# ============================================================
# 建立圖面
# ============================================================
# fig = plt.figure(figsize=(18, 14), facecolor='#0a0a1a')


# fig.suptitle('Delft Circuits  Cri/oFlex® 3  Quantum Transmission Line\n' 'Engineering Three-View Drawing with Advanced Matplotlib API', fontsize=16, fontweight='bold', color='white', y=0.97)
from streamlit import sidebar, radio, text_input, empty, pyplot
MENU, 表單=[], ['上視圖', '前視圖', '側視圖', '組態', '立體']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  狀態=empty()
  狀態.code([])
if menu==len(表單):
  pass
elif menu==MENU[0]: #上視圖
  pass
# ============================================================
# 1. TOP VIEW
# ============================================================
  fig, ax_top= subplots(figsize=(10, 6))
  # ax_top = fig.add_subplot(gs[0, :2])
  ax_top.set_facecolor('#0f0f2a')

  flex_rect = FancyBboxPatch((SMA_BODY_LEN, -TOTAL_WIDTH/2), LENGTH, TOTAL_WIDTH, boxstyle="square,pad=0", facecolor=COLOR_POLYIMIDE, edgecolor='white', linewidth=1.5, alpha=0.9)
  ax_top.add_patch(flex_rect)

  for i in range(N_CHANNELS):
      y = -TOTAL_WIDTH/2 + PITCH/2 + i * PITCH
      sig_line = Rectangle((SMA_BODY_LEN + 5, y - SIGNAL_WIDTH/2), LENGTH - 10, SIGNAL_WIDTH, facecolor=COLOR_SIGNAL, edgecolor='#B8860B', linewidth=0.5, alpha=0.85)
      ax_top.add_patch(sig_line)
      ax_top.text(SMA_BODY_LEN + LENGTH/2, y, f'CH{i+1}', ha='center', va='center', fontsize=7, color='#333', fontweight='bold')

  for i in range(N_CHANNELS):
      y = -TOTAL_WIDTH/2 + PITCH/2 + i * PITCH
      conn_body = Rectangle((0, y - SMA_BODY_DIA/2), SMA_BODY_LEN, SMA_BODY_DIA, facecolor=COLOR_CONNECTOR, edgecolor='white', linewidth=1)
      ax_top.add_patch(conn_body)
      for j in range(3):
          ax_top.plot([SMA_BODY_LEN - SMA_THREAD_LEN + j*2, SMA_BODY_LEN - SMA_THREAD_LEN + j*2], [y - SMA_BODY_DIA/2, y + SMA_BODY_DIA/2], 'w-', linewidth=0.5)
      pin = Rectangle((-3, y - 0.15), 3, 0.3, facecolor=COLOR_SILVER, edgecolor='white')
      ax_top.add_patch(pin)

  for i in range(N_CHANNELS):
      y = -TOTAL_WIDTH/2 + PITCH/2 + i * PITCH
      conn_body = Rectangle((SMA_BODY_LEN + LENGTH, y - SMA_BODY_DIA/2), SMA_BODY_LEN, SMA_BODY_DIA, facecolor=COLOR_CONNECTOR, edgecolor='white', linewidth=1)
      ax_top.add_patch(conn_body)
      for j in range(3):
          ax_top.plot([SMA_BODY_LEN + LENGTH + j*2, SMA_BODY_LEN + LENGTH + j*2], [y - SMA_BODY_DIA/2, y + SMA_BODY_DIA/2], 'w-', linewidth=0.5)
      pin = Rectangle((SMA_BODY_LEN + LENGTH + SMA_BODY_LEN, y - 0.15), 3, 0.3, facecolor=COLOR_SILVER, edgecolor='white')
      ax_top.add_patch(pin)

  filter_zone = Rectangle((SMA_BODY_LEN + LENGTH*0.3, -TOTAL_WIDTH/2 - 1), LENGTH*0.15, TOTAL_WIDTH + 2, facecolor=COLOR_FILTER, edgecolor='cyan', linewidth=1.5, linestyle='--', alpha=0.3)
  ax_top.add_patch(filter_zone)
  ax_top.text(SMA_BODY_LEN + LENGTH*0.375, TOTAL_WIDTH/2 + 3, 'Integrated Filters\n& Attenuators', ha='center', va='bottom', fontsize=8, color='cyan', style='italic')

  ax_top.annotate('', xy=(SMA_BODY_LEN, TOTAL_WIDTH/2 + 8), xytext=(SMA_BODY_LEN + LENGTH, TOTAL_WIDTH/2 + 8), arrowprops=dict(arrowstyle='<->', color='yellow', lw=1.5))
  ax_top.text(SMA_BODY_LEN + LENGTH/2, TOTAL_WIDTH/2 + 10, f'L = {LENGTH} mm', ha='center', va='bottom', color='yellow', fontsize=9)

  ax_top.annotate('', xy=(SMA_BODY_LEN + LENGTH + SMA_BODY_LEN + 8, -TOTAL_WIDTH/2),
                  xytext=(SMA_BODY_LEN + LENGTH + SMA_BODY_LEN + 8, TOTAL_WIDTH/2),
                  arrowprops=dict(arrowstyle='<->', color='yellow', lw=1.5))
  ax_top.text(SMA_BODY_LEN + LENGTH + SMA_BODY_LEN + 12, 0, 
              f'W = {TOTAL_WIDTH} mm\n(8 ch x {PITCH} mm)', 
              ha='left', va='center', color='yellow', fontsize=9, rotation=90)

  ax_top.annotate('', xy=(SMA_BODY_LEN + LENGTH/2, -TOTAL_WIDTH/2 + PITCH/2),
                  xytext=(SMA_BODY_LEN + LENGTH/2, -TOTAL_WIDTH/2 + PITCH/2 + PITCH),
                  arrowprops=dict(arrowstyle='<->', color='#FF6B6B', lw=1.2))
  ax_top.text(SMA_BODY_LEN + LENGTH/2 + 3, -TOTAL_WIDTH/2 + PITCH, 
              f'Pitch = {PITCH} mm', ha='left', va='center', color='#FF6B6B', fontsize=8)

  ax_top.set_xlim(-15, SMA_BODY_LEN + LENGTH + SMA_BODY_LEN + 35)
  ax_top.set_ylim(-TOTAL_WIDTH/2 - 15, TOTAL_WIDTH/2 + 18)
  ax_top.set_aspect('equal')
  ax_top.set_title('TOP VIEW  (Plan View)', fontsize=12, color='white', fontweight='bold', pad=10)
  ax_top.set_xlabel('Length (mm)', color='white')
  ax_top.set_ylabel('Width (mm)', color='white')
  ax_top.tick_params(colors='white')
  for spine in ax_top.spines.values():
      spine.set_color('white')

elif menu==MENU[1]: #
  pass
# ============================================================
# 2. FRONT VIEW
# ============================================================
  fig, ax_front= subplots(figsize=(10, 6))
  # ax_front = fig.add_subplot(gs[1, 0])
  ax_front.set_facecolor('#0f0f2a')

  ground_bottom = Rectangle((-TOTAL_WIDTH/2 - 2, -THICKNESS/2), 
                             TOTAL_WIDTH + 4, GROUND_THICKNESS,
                             facecolor=COLOR_GROUND, edgecolor='white', linewidth=1)
  ax_front.add_patch(ground_bottom)

  dielectric_bottom = Rectangle((-TOTAL_WIDTH/2, -THICKNESS/2 + GROUND_THICKNESS),
                                 TOTAL_WIDTH, DIELECTRIC_THICKNESS/2 - GROUND_THICKNESS,
                                 facecolor=COLOR_POLYIMIDE, edgecolor='white', linewidth=0.5, alpha=0.8)
  ax_front.add_patch(dielectric_bottom)

  for i in range(N_CHANNELS):
      x = -TOTAL_WIDTH/2 + PITCH/2 + i * PITCH
      signal = Rectangle((x - SIGNAL_WIDTH/2, -SIGNAL_WIDTH/2/3), 
                          SIGNAL_WIDTH, SIGNAL_WIDTH/1.5,
                          facecolor=COLOR_SIGNAL, edgecolor='#B8860B', linewidth=0.8)
      ax_front.add_patch(signal)

  dielectric_top = Rectangle((-TOTAL_WIDTH/2, SIGNAL_WIDTH/2/3),
                              TOTAL_WIDTH, DIELECTRIC_THICKNESS/2 - GROUND_THICKNESS,
                              facecolor=COLOR_POLYIMIDE, edgecolor='white', linewidth=0.5, alpha=0.8)
  ax_front.add_patch(dielectric_top)

  ground_top = Rectangle((-TOTAL_WIDTH/2 - 2, THICKNESS/2 - GROUND_THICKNESS),
                          TOTAL_WIDTH + 4, GROUND_THICKNESS,
                          facecolor=COLOR_GROUND, edgecolor='white', linewidth=1)
  ax_front.add_patch(ground_top)

  ax_front.annotate('', xy=(TOTAL_WIDTH/2 + 8, -THICKNESS/2),
                    xytext=(TOTAL_WIDTH/2 + 8, THICKNESS/2),
                    arrowprops=dict(arrowstyle='<->', color='yellow', lw=1.5))
  ax_front.text(TOTAL_WIDTH/2 + 12, 0, f't = {THICKNESS} mm', 
                ha='left', va='center', color='yellow', fontsize=9, rotation=90)

  layer_labels = [
      (THICKNESS/2 + 2.5, 'Ground Plane (Ag/NbTi)', COLOR_GROUND),
      (THICKNESS, 'Dielectric (Polyimide)', COLOR_POLYIMIDE),
      (0, 'Signal Lines (x8)', COLOR_SIGNAL),
      (-THICKNESS/4, 'Dielectric (Polyimide)', COLOR_POLYIMIDE),
      (-THICKNESS/2 - 1.5, 'Ground Plane (Ag/NbTi)', COLOR_GROUND),
  ]
  for y, label, color in layer_labels:
      ax_front.text(-TOTAL_WIDTH/2 - 12, y, label, ha='right', va='center', color=color, fontsize=8, fontweight='bold')

  ax_front.text(0, -THICKNESS/2 - 4, f'Z0 = {IMPEDANCE} Ohm (Stripline)', 
                ha='center', va='top', color='#00FF88', fontsize=10, fontweight='bold')

  ax_front.set_xlim(-TOTAL_WIDTH/2 - 20, TOTAL_WIDTH/2 + 20)
  ax_front.set_ylim(-THICKNESS/2 - 6, THICKNESS/2 + 6)
  ax_front.set_aspect('equal')
  ax_front.set_title('FRONT VIEW  (Cross-Section A-A)', fontsize=12, color='white', fontweight='bold', pad=10)
  ax_front.set_xlabel('Width (mm)', color='white')
  ax_front.set_ylabel('Thickness (mm)', color='white')
  ax_front.tick_params(colors='white')
  for spine in ax_front.spines.values():
      spine.set_color('white')

elif menu==MENU[2]: #
  pass
# ============================================================
# 3. SIDE VIEW
# ============================================================
  fig, ax_side= subplots(figsize=(10, 6))
  # ax_side = fig.add_subplot(gs[1, 1])
  ax_side.set_facecolor('#0f0f2a')

  t_side = np.linspace(0, LENGTH, 500)
  y_side = 2 * np.sin(t_side / 50) * np.exp(-t_side / 300)

  ax_side.fill_between(t_side + SMA_BODY_LEN, y_side + THICKNESS/2, y_side - THICKNESS/2,
                        color=COLOR_POLYIMIDE, alpha=0.9, edgecolor='white', linewidth=1)

  ax_side.plot(t_side + SMA_BODY_LEN, y_side + THICKNESS/2 - GROUND_THICKNESS, 
               'w--', linewidth=0.8, alpha=0.7)
  ax_side.plot(t_side + SMA_BODY_LEN, y_side - THICKNESS/2 + GROUND_THICKNESS, 
               'w--', linewidth=0.8, alpha=0.7)
  ax_side.plot(t_side + SMA_BODY_LEN, y_side, 
               color=COLOR_SIGNAL, linewidth=1.5, alpha=0.9)

  conn_l = Rectangle((0, -SMA_BODY_DIA/2), SMA_BODY_LEN, SMA_BODY_DIA,
                      facecolor=COLOR_CONNECTOR, edgecolor='white', linewidth=1)
  ax_side.add_patch(conn_l)
  conn_r = Rectangle((SMA_BODY_LEN + LENGTH, -SMA_BODY_DIA/2), SMA_BODY_LEN, SMA_BODY_DIA,
                      facecolor=COLOR_CONNECTOR, edgecolor='white', linewidth=1)
  ax_side.add_patch(conn_r)

  max_curve_idx = np.argmax(np.abs(y_side))
  mc_x = t_side[max_curve_idx] + SMA_BODY_LEN
  mc_y = y_side[max_curve_idx]
  circle = Circle((mc_x - BEND_RADIUS, mc_y), BEND_RADIUS, 
                  fill=False, edgecolor='#FF6B6B', linewidth=1.5, linestyle='--')
  ax_side.add_patch(circle)
  ax_side.annotate(f'R >= {BEND_RADIUS} mm', xy=(mc_x - BEND_RADIUS, mc_y + BEND_RADIUS + 2),
                   fontsize=8, color='#FF6B6B', ha='center')

  ax_side.annotate('', xy=(SMA_BODY_LEN, -SMA_BODY_DIA/2 - 5),
                    xytext=(SMA_BODY_LEN + LENGTH, -SMA_BODY_DIA/2 - 5),
                    arrowprops=dict(arrowstyle='<->', color='yellow', lw=1.5))
  ax_side.text(SMA_BODY_LEN + LENGTH/2, -SMA_BODY_DIA/2 - 8, 
               f'{LENGTH} mm', ha='center', va='top', color='yellow', fontsize=9)

  ax_side.set_xlim(-5, SMA_BODY_LEN + LENGTH + SMA_BODY_LEN + 10)
  ax_side.set_ylim(-SMA_BODY_DIA/2 - 12, SMA_BODY_DIA/2 + 10)
  ax_side.set_aspect('equal')
  ax_side.set_title('SIDE VIEW  (Profile)', fontsize=12, color='white', fontweight='bold', pad=10)
  ax_side.set_xlabel('Length (mm)', color='white')
  ax_side.set_ylabel('Height (mm)', color='white')
  ax_side.tick_params(colors='white')
  for spine in ax_side.spines.values():
      spine.set_color('white')

elif menu==MENU[3]: #
  pass
# ============================================================
# 4. SPEC TABLE
# ============================================================
  fig, ax_table= subplots(figsize=(10, 6))
  # ax_table = fig.add_subplot(gs[1, 2])
  ax_table.set_facecolor('#0f0f2a')
  ax_table.axis('off')

  spec_data = [
      ['Parameter', 'Value'],
      ['Channels', f'{N_CHANNELS}'],
      ['Pitch', f'{PITCH} mm'],
      ['Thickness', f'{THICKNESS} mm'],
      ['Length', f'200-1000 mm'],
      ['Bend Radius', f'>= {BEND_RADIUS} mm'],
      ['Impedance', f'{IMPEDANCE} Ohm'],
      ['Frequency', 'DC - 18 GHz'],
      ['Material', 'Polyimide + Ag/NbTi'],
      ['Line Type', 'Stripline'],
      ['Heat Load', '< 4 uW/ch @ 3K'],
      ['Connector', 'SMA / SMP'],
  ]

  table = ax_table.table(cellText=spec_data[1:], colLabels=spec_data[0],
                          cellLoc='center', loc='center',
                          colColours=['#1a1a3a', '#1a1a3a'])
  table.auto_set_font_size(False)
  table.set_fontsize(9)
  table.scale(1.2, 1.8)

  for i, key in enumerate(table.get_celld().keys()):
      row, col = key
      cell = table.get_celld()[key]
      cell.set_edgecolor('#444466')
      cell.set_linewidth(1)
      if row == 0:
          cell.set_text_props(color='white', fontweight='bold')
          cell.set_facecolor('#2a2a5a')
      else:
          cell.set_text_props(color='#CCCCCC')
          cell.set_facecolor('#151530' if row % 2 == 0 else '#1a1a40')

  ax_table.set_title('SPECIFICATIONS', fontsize=12, color='white', fontweight='bold', pad=10)

elif menu==MENU[4]: #
  pass
# ============================================================
# 5. 3D VIEW
# ============================================================
  #fig, ax_3d= subplots(figsize=(10, 6), projection='3d')
  fig = figure(figsize=(18, 14), facecolor='#0a0a1a')
  gs = GridSpec(3, 3, figure=fig, height_ratios=[1, 1.2, 0.8], width_ratios=[1.5, 1, 1], hspace=0.35, wspace=0.3, left=0.06, right=0.96, top=0.92, bottom=0.08)
  ax_3d = fig.add_subplot(gs[0, 2], projection='3d')
  ax_3d.set_facecolor('#0f0f2a')

  x_3d = np.linspace(0, LENGTH, 100)
  y_3d = np.linspace(-TOTAL_WIDTH/2, TOTAL_WIDTH/2, 20)
  X, Y = np.meshgrid(x_3d, y_3d)
  Z = np.zeros_like(X)
  Z += 0.5 * np.sin(X / 80) * np.exp(-X / 400)

  ax_3d.plot_surface(X, Y, Z + THICKNESS/2, 
                     color=COLOR_POLYIMIDE, alpha=0.8, 
                     edgecolor='none', shade=True)
  ax_3d.plot_surface(X, Y, Z - THICKNESS/2, 
                     color=COLOR_POLYIMIDE, alpha=0.8, 
                     edgecolor='none', shade=True)

  for i in range(N_CHANNELS):
      y_ch = -TOTAL_WIDTH/2 + PITCH/2 + i * PITCH
      z_ch = 0.5 * np.sin(x_3d / 80) * np.exp(-x_3d / 400)
      ax_3d.plot(x_3d, [y_ch]*len(x_3d), z_ch, 
                 color=COLOR_SIGNAL, linewidth=1.5, alpha=0.9)

  ax_3d.set_xlim(0, LENGTH)
  ax_3d.set_ylim(-TOTAL_WIDTH/2 - 2, TOTAL_WIDTH/2 + 2)
  ax_3d.set_zlim(-2, 2)
  ax_3d.set_title('3D PERSPECTIVE', fontsize=12, color='white', fontweight='bold', pad=10)
  ax_3d.set_xlabel('Length', color='white', fontsize=8)
  ax_3d.set_ylabel('Width', color='white', fontsize=8)
  ax_3d.set_zlabel('Height', color='white', fontsize=8)
  ax_3d.tick_params(colors='white', labelsize=7)
  ax_3d.view_init(elev=25, azim=-60)

  ax_3d.xaxis.pane.fill = False
  ax_3d.yaxis.pane.fill = False
  ax_3d.zaxis.pane.fill = False
  ax_3d.xaxis.pane.set_edgecolor('#333355')
  ax_3d.yaxis.pane.set_edgecolor('#333355')
  ax_3d.zaxis.pane.set_edgecolor('#333355')
  ax_3d.grid(True, color='#333355', alpha=0.3)

elif menu==MENU[5]: #
  pass
# ============================================================
# 6. Legend & Info
# ============================================================
  fig, ax_legend= subplots(figsize=(10, 6))
  # ax_legend = fig.add_subplot(gs[2, :])
  ax_legend.set_facecolor('#0f0f2a')
  ax_legend.axis('off')

  info_box = FancyBboxPatch((0.02, 0.1), 0.96, 0.8,
                             boxstyle="round,pad=0.02,rounding_size=0.02",
                             facecolor='#151530', edgecolor='#444466', linewidth=2,
                             transform=ax_legend.transAxes)
  ax_legend.add_patch(info_box)

  legend_text = (
      "Cri/oFlex(R) 3 Structure Description:\n"
      "  - Stripline transmission line: Center conductor (Ag/NbTi) sandwiched between two polyimide"
      " (Kapton) dielectric layers with ground planes above and below, forming 50 Ohm characteristic impedance.\n"
      "  - 8-channel parallel design: 2 mm pitch, total thickness only 0.3 mm, achieving extremely high-density I/O.\n"
      "  - Integrated filtering: Some channels include built-in attenuators and low-pass filters,"
      " reducing extra components and connection points.\n"
      "  - Ultra-low heat load: NbTi superconducting version has ~1/10 the thermal load of conventional coax,"
      " suitable for mK dilution refrigerators.\n"
      "  - Flexible design: Minimum bend radius 5 mm, can route through non-line-of-sight ports,"
      " simplifying cryogenic system wiring."
  )

  ax_legend.text(0.05, 0.85, legend_text, transform=ax_legend.transAxes,
                 fontsize=10, color='#CCCCCC', va='top', ha='left',
                 linespacing=1.6)

  legend_items = [
      (COLOR_POLYIMIDE, 'Polyimide (Kapton) Dielectric'),
      (COLOR_SIGNAL, 'Signal Conductor (Ag/NbTi)'),
      (COLOR_GROUND, 'Ground Plane (Ag/NbTi)'),
      (COLOR_CONNECTOR, 'SMA/SMP Connector'),
      (COLOR_FILTER, 'Integrated Filter Zone'),
  ]

  for i, (color, label) in enumerate(legend_items):
      x_pos = 0.05 + i * 0.19
      rect = Rectangle((x_pos, 0.15), 0.03, 0.08, 
                       facecolor=color, edgecolor='white', linewidth=0.5,
                       transform=ax_legend.transAxes)
      ax_legend.add_patch(rect)
      ax_legend.text(x_pos + 0.035, 0.19, label, transform=ax_legend.transAxes,
                     fontsize=8, color='#AAAAAA', va='center')

pyplot(fig)
# plt.savefig('/mnt/agents/output/crioflex3_three_view.png', dpi=200, facecolor='#0a0a1a', edgecolor='none', bbox_inches='tight')
# plt.show()
# print("Three-view drawing saved successfully!")
