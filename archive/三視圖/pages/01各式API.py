from matplotlib.pyplot import figure, rcParams, savefig, show
from numpy import cos, exp, linspace, log, meshgrid, sin, sqrt

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Polygon, Arc, Wedge, FancyArrowPatch, Ellipse, PathPatch
from matplotlib.path import Path
import matplotlib.patheffects as pe
from matplotlib.gridspec import GridSpec
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.transforms as transforms
import numpy as np
from streamlit import pyplot

plt.rcParams['font.family'] = ['WenQuanYi Zen Hei', 'Noto Sans CJK JP', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False
from streamlit import sidebar, radio, text_input, empty
MENU, 表單=[], ['形狀', '注解', '形變', '立體']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  狀態=empty()
  狀態.code([])
# ============================================================
# 進階 Matplotlib API 教學圖表
# ============================================================
from matplotlib.pyplot import rcParams, savefig, show, subplots, tight_layout
from streamlit import pyplot

# fig.suptitle('Advanced Matplotlib API Tutorial\n' 'Techniques Used in the Cri/oFlex 3 Three-View Drawing', fontsize=18, fontweight='bold', color='white', y=0.97)
if menu==len(表單):
  pass

elif menu==MENU[0]: #左上
  pass
  fig, ax1= subplots(figsize=(10, 6))
# ============================================================
# Panel 1: Patches & Shapes (左上)
# ============================================================
  # ax1 = fig.add_subplot(gs_outer[0, 0])
  ax1.set_facecolor('#16213e')
  ax1.set_xlim(0, 10)
  ax1.set_ylim(0, 10)
  ax1.set_aspect('equal')
  ax1.set_title('1. Patches & Custom Shapes', fontsize=13, color='#00d4ff', fontweight='bold', pad=10)

  # FancyBboxPatch - 圓角矩形帶陰影效果
  fancy = FancyBboxPatch((0.5, 7), 3, 2, boxstyle="round,pad=0.3,rounding_size=0.5", facecolor='#e94560', edgecolor='white', linewidth=2, alpha=0.9)
  ax1.add_patch(fancy)
  ax1.text(2, 8, 'FancyBboxPatch', ha='center', va='center', color='white', fontsize=9, fontweight='bold')

  # Rectangle - 基本矩形
  rect = Rectangle((4.5, 7), 2.5, 2, facecolor='#0f3460', edgecolor='#00d4ff', linewidth=2, linestyle='--')
  ax1.add_patch(rect)
  ax1.text(5.75, 8, 'Rectangle', ha='center', va='center', color='#00d4ff', fontsize=9)

  # Circle + Wedge
  circle = Circle((1.5, 4), 1.2, facecolor='#533483', edgecolor='white', linewidth=2, alpha=0.8)
  ax1.add_patch(circle)
  ax1.text(1.5, 4, 'Circle', ha='center', va='center', color='white', fontsize=9)

  wedge = Wedge((4.5, 4), 1.2, 30, 270, facecolor='#e94560', edgecolor='white', linewidth=2)
  ax1.add_patch(wedge)
  ax1.text(4.5, 4, 'Wedge', ha='center', va='center', color='white', fontsize=9)

  # Ellipse
  ellipse = Ellipse((7.5, 4), 2.5, 1.5, angle=30, facecolor='#16c79a', 
                     edgecolor='white', linewidth=2, alpha=0.8)
  ax1.add_patch(ellipse)
  ax1.text(7.5, 4, 'Ellipse', ha='center', va='center', color='white', fontsize=9)

  # Polygon (自定義多邊形)
  poly_coords = [(1, 0.5), (2.5, 2.5), (1, 3.5), (0, 2.5)]
  polygon = Polygon(poly_coords, facecolor='#f9a825', edgecolor='white', linewidth=2, alpha=0.85)
  ax1.add_patch(polygon)
  ax1.text(1, 2, 'Polygon', ha='center', va='center', color='white', fontsize=9, fontweight='bold')

  # Arc
  arc = Arc((4.5, 1.5), 3, 3, angle=0, theta1=0, theta2=180, 
            color='#ff6b6b', linewidth=3, linestyle='-.')
  ax1.add_patch(arc)
  ax1.text(4.5, 0.3, 'Arc', ha='center', va='center', color='#ff6b6b', fontsize=9)

  # PathPatch (貝茲曲線)
  verts = [(7, 0.5), (7.5, 2), (8.5, 2.5), (9, 1), (8, 0.5)]
  codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CLOSEPOLY]
  path = Path(verts, codes)
  path_patch = PathPatch(path, facecolor='#9c27b0', edgecolor='white', linewidth=2, alpha=0.8)
  ax1.add_patch(path_patch)
  ax1.text(8, 1.3, 'PathPatch\n(Bezier)', ha='center', va='center', color='white', fontsize=8)

  ax1.set_xticks([])
  ax1.set_yticks([])
  for spine in ax1.spines.values():
      spine.set_color('#444466')

elif menu==MENU[1]: #
  pass
  fig, ax2= subplots(figsize=(10, 6))
# ============================================================
# Panel 2: Annotations & Dimensions (右上)
# ============================================================
  # ax2 = fig.add_subplot(gs_outer[0, 1])
  ax2.set_facecolor('#16213e')
  ax2.set_xlim(0, 10)
  ax2.set_ylim(0, 10)
  ax2.set_aspect('equal')
  ax2.set_title('2. Annotations & Dimension Lines', fontsize=13, color='#00d4ff', fontweight='bold', pad=10)

  # 繪製一個示例物體
  obj = FancyBboxPatch((2, 3), 6, 4, boxstyle="round,pad=0.2",
                        facecolor='#0f3460', edgecolor='#00d4ff', linewidth=2)
  ax2.add_patch(obj)
  ax2.text(5, 5, 'Object', ha='center', va='center', color='white', fontsize=14, fontweight='bold')

  # 雙向箭頭尺寸標註 (水平)
  ax2.annotate('', xy=(2, 8.2), xytext=(8, 8.2),
               arrowprops=dict(arrowstyle='<->', color='#e94560', lw=2,
                              connectionstyle='arc3'))
  ax2.text(5, 8.6, 'Width = 6 units', ha='center', va='bottom', color='#e94560', 
           fontsize=10, fontweight='bold')

  # 雙向箭頭尺寸標註 (垂直)
  ax2.annotate('', xy=(8.5, 3), xytext=(8.5, 7),
               arrowprops=dict(arrowstyle='<->', color='#e94560', lw=2))
  ax2.text(8.8, 5, 'H = 4', ha='left', va='center', color='#e94560', 
           fontsize=10, fontweight='bold', rotation=90)

  # FancyArrowPatch 帶彎曲的箭頭
  ax2.annotate('FancyArrowPatch\nwith curved style', xy=(2, 5), xytext=(0.3, 8),
               arrowprops=dict(arrowstyle='->', color='#16c79a', lw=2,
                              connectionstyle='arc3,rad=0.3',
                              linestyle='--'),
               fontsize=9, color='#16c79a', ha='center')

  # 帶文字框的註解
  ax2.annotate('Text with bbox', xy=(5, 7), xytext=(1, 1.5),
               arrowprops=dict(arrowstyle='->', color='#f9a825', lw=1.5),
               fontsize=10, color='#f9a825',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='#1a1a2e', 
                        edgecolor='#f9a825', linewidth=1.5))

  # 使用 path_effects 的文字描邊
  t = ax2.text(5, 1.5, 'Path Effects: Glow Text', ha='center', va='center',
               fontsize=14, color='white', fontweight='bold')
  t.set_path_effects([pe.withStroke(linewidth=4, foreground='#e94560'),
                      pe.Normal()])

  # 帶連接線的標註點
  ax2.plot(5, 7, 'o', color='#ff6b6b', markersize=10)
  ax2.plot(2, 5, 's', color='#16c79a', markersize=10)

  ax2.set_xticks([])
  ax2.set_yticks([])
  for spine in ax2.spines.values():
      spine.set_color('#444466')

elif menu==MENU[2]: #
  pass
  fig, ax3= subplots(figsize=(10, 6))
# ============================================================
# Panel 3: Advanced Layouts & Transforms (左下)
# ============================================================
  # ax3 = fig.add_subplot(gs_outer[1, 0])
  ax3.set_facecolor('#16213e')
  ax3.set_xlim(0, 10)
  ax3.set_ylim(0, 10)
  ax3.set_aspect('equal')
  ax3.set_title('3. Transforms & Coordinate Systems', fontsize=13, color='#00d4ff', fontweight='bold', pad=10)

  # 數據座標系中的物件
  rect_data = Rectangle((1, 6), 3, 2, facecolor='#e94560', edgecolor='white', linewidth=2, alpha=0.8)
  ax3.add_patch(rect_data)
  ax3.text(2.5, 7, 'Data Coords', ha='center', va='center', color='white', fontsize=9)

  # 使用 transforms 在 axes 座標系中放置物件
  rect_axes = Rectangle((0.6, 0.6), 0.2, 0.15, 
                         transform=ax3.transAxes,
                         facecolor='#16c79a', edgecolor='white', linewidth=2)
  ax3.add_patch(rect_axes)
  ax3.text(0.7, 0.675, 'Axes Coords', transform=ax3.transAxes,
           ha='center', va='center', color='white', fontsize=8)

  # 使用 figure 座標系
  rect_fig = Rectangle((0.05, 0.05), 0.08, 0.06,
                        transform=fig.transFigure,
                        facecolor='#f9a825', edgecolor='white', linewidth=2)
  fig.patches.append(rect_fig)

  # 混合座標系標註
  ax3.annotate('Mixed transform\nannotation', xy=(7, 8), xytext=(0.85, 0.85),
               xycoords='data', textcoords='axes fraction',
               arrowprops=dict(arrowstyle='->', color='#ff6b6b', lw=1.5),
               fontsize=9, color='#ff6b6b', ha='center')

  # 自定義 colormap 示範
  n_bars = 8
  cmap = LinearSegmentedColormap.from_list('custom', ['#e94560', '#533483', '#0f3460', '#16c79a'])
  for i in range(n_bars):
      color = cmap(i / (n_bars - 1))
      bar = Rectangle((1 + i * 0.9, 1), 0.7, 1 + i * 0.3, 
                      facecolor=color, edgecolor='white', linewidth=0.5)
      ax3.add_patch(bar)

  ax3.text(5, 0.5, 'LinearSegmentedColormap', ha='center', va='top', 
           color='#00d4ff', fontsize=10)

  # fill_between 示範
  x = np.linspace(1, 9, 100)
  y1 = 3 + 0.5 * np.sin(x)
  y2 = 3 + 0.5 * np.sin(x) + 1
  ax3.fill_between(x, y1, y2, alpha=0.4, color='#f9a825', edgecolor='white', linewidth=0.5)
  ax3.text(5, 3.8, 'fill_between', ha='center', va='center', color='#f9a825', fontsize=9)

  ax3.set_xticks([])
  ax3.set_yticks([])
  for spine in ax3.spines.values():
      spine.set_color('#444466')

elif menu==MENU[3]: #
  pass
# ============================================================
# Panel 4: 3D + Table + Spine Customization (右下)
# ============================================================
# 使用 nested GridSpec
  fig = plt.figure(figsize=(20, 16), facecolor='#1a1a2e')

# GridSpec 巢狀佈局示範
  gs_outer = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.25, left=0.04, right=0.96, top=0.93, bottom=0.05)
  gs_nested = gs_outer[1, 1].subgridspec(2, 2, hspace=0.3, wspace=0.3)

  # 4a. 3D Surface
  ax4a = fig.add_subplot(gs_nested[0, 0], projection='3d')
  ax4a.set_facecolor('#16213e')

  X = np.linspace(-2, 2, 30)
  Y = np.linspace(-2, 2, 30)
  X, Y = np.meshgrid(X, Y)
  Z = np.sin(np.sqrt(X**2 + Y**2)) * np.exp(-0.3 * (X**2 + Y**2))

  surf = ax4a.plot_surface(X, Y, Z, cmap='plasma', alpha=0.9, 
                            edgecolor='none', shade=True, antialiased=True)
  ax4a.set_title('3D plot_surface', fontsize=11, color='#00d4ff', fontweight='bold', pad=5)
  ax4a.set_xlabel('X', color='white', fontsize=8)
  ax4a.set_ylabel('Y', color='white', fontsize=8)
  ax4a.set_zlabel('Z', color='white', fontsize=8)
  ax4a.tick_params(colors='white', labelsize=7)
  ax4a.view_init(elev=30, azim=-45)

  ax4a.xaxis.pane.fill = False
  ax4a.yaxis.pane.fill = False
  ax4a.zaxis.pane.fill = False
  for axis in [ax4a.xaxis, ax4a.yaxis, ax4a.zaxis]:
      axis.pane.set_edgecolor('#333355')

  # 4b. Table API
  ax4b = fig.add_subplot(gs_nested[0, 1])
  ax4b.set_facecolor('#16213e')
  ax4b.axis('off')
  ax4b.set_title('Table API', fontsize=11, color='#00d4ff', fontweight='bold', pad=5)

  table_data = [
      ['API', 'Usage'],
      ['GridSpec', 'Complex layouts'],
      ['FancyBboxPatch', 'Rounded rects'],
      ['annotate', 'Dimensions'],
      ['path_effects', 'Text glow'],
      ['fill_between', 'Area fills'],
      ['transAxes', 'Relative coords'],
  ]

  tbl = ax4b.table(cellText=table_data[1:], colLabels=table_data[0],
                    cellLoc='center', loc='center',
                    colColours=['#1a1a3a', '#1a1a3a'])
  tbl.auto_set_font_size(False)
  tbl.set_fontsize(9)
  tbl.scale(1.1, 1.6)

  for key in tbl.get_celld().keys():
      row, col = key
      cell = tbl.get_celld()[key]
      cell.set_edgecolor('#444466')
      cell.set_linewidth(1)
      if row == 0:
          cell.set_text_props(color='white', fontweight='bold')
          cell.set_facecolor('#2a2a5a')
      else:
          cell.set_text_props(color='#CCCCCC')
          cell.set_facecolor('#151530' if row % 2 == 0 else '#1a1a40')

  # 4c. Spine Customization
  ax4c = fig.add_subplot(gs_nested[1, 0])
  ax4c.set_facecolor('#16213e')

  x = np.linspace(0, 10, 100)
  ax4c.plot(x, np.sin(x), color='#e94560', linewidth=2, label='sin(x)')
  ax4c.plot(x, np.cos(x), color='#16c79a', linewidth=2, label='cos(x)')

  # 自定義 spine
  ax4c.spines['left'].set_color('#00d4ff')
  ax4c.spines['left'].set_linewidth(2)
  ax4c.spines['bottom'].set_color('#00d4ff')
  ax4c.spines['bottom'].set_linewidth(2)
  ax4c.spines['top'].set_visible(False)
  ax4c.spines['right'].set_visible(False)

  ax4c.tick_params(colors='white')
  ax4c.set_title('Spine Customization', fontsize=11, color='#00d4ff', fontweight='bold', pad=5)
  ax4c.legend(loc='upper right', facecolor='#1a1a3a', edgecolor='#444466', 
              labelcolor='white', fontsize=9)
  ax4c.set_xlabel('X axis', color='white')
  ax4c.set_ylabel('Y axis', color='white')

  # 4d. Inset Axes + Twin Axes
  ax4d = fig.add_subplot(gs_nested[1, 1])
  ax4d.set_facecolor('#16213e')

  x = np.linspace(0, 10, 100)
  line1 = ax4d.plot(x, np.exp(x/5), color='#e94560', linewidth=2, label='exp(x/5)')
  ax4d.set_xlabel('X', color='white')
  ax4d.set_ylabel('Exp Scale', color='#e94560')
  ax4d.tick_params(axis='y', colors='#e94560')

  # Twin axes
  ax4d_twin = ax4d.twinx()
  ax4d_twin.set_facecolor('#16213e')
  line2 = ax4d_twin.plot(x, np.log(x + 1), color='#16c79a', linewidth=2, linestyle='--', label='log(x+1)')
  ax4d_twin.set_ylabel('Log Scale', color='#16c79a')
  ax4d_twin.tick_params(axis='y', colors='#16c79a')

  # Inset axes
  from mpl_toolkits.axes_grid1.inset_locator import inset_axes
  ax_inset = inset_axes(ax4d, width="40%", height="40%", loc='upper left',
                         bbox_to_anchor=(0.05, 0.05, 0.9, 0.9),
                         bbox_transform=ax4d.transAxes)
  ax_inset.set_facecolor('#0f3460')
  ax_inset.plot(x, np.sin(x) * np.exp(-x/5), color='#f9a825', linewidth=1.5)
  ax_inset.set_title('Inset Axes', fontsize=8, color='white', pad=3)
  ax_inset.tick_params(colors='white', labelsize=6)
  ax_inset.set_xlim(0, 10)
  ax_inset.set_ylim(-0.8, 0.8)
  for spine in ax_inset.spines.values():
      spine.set_color('#444466')

  ax4d.set_title('Twin Axes + Inset', fontsize=11, color='#00d4ff', fontweight='bold', pad=5)
  ax4d.tick_params(axis='x', colors='white')

  # 合併圖例
  lines = line1 + line2
  labels = [l.get_label() for l in lines]
  ax4d.legend(lines, labels, loc='lower right', facecolor='#1a1a3a', edgecolor='#444466', labelcolor='white', fontsize=8)

pyplot(fig)
# plt.savefig('/mnt/agents/output/matplotlib_advanced_api.png', dpi=200, facecolor='#1a1a2e', edgecolor='none', bbox_inches='tight')
# plt.show()
# print("Advanced Matplotlib API tutorial saved!")
