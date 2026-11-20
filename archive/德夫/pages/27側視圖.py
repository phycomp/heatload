from matplotlib.pyplot import savefig, show, subplots, suptitle, tight_layout
# Let's also create a quick preview image to show what the app looks like
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from streamlit import sidebar, radio, text_input, empty, pyplot
MENU, 表單=[], ['側視', '', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
狀態=empty()
#狀態.code([])
if menu==len(表單):
  pass
elif menu==MENU[0]: #側視
  fig, axes = subplots(1, 3, figsize=(18, 5.5), dpi=120)

  # Common params
  w_mm, t_mm, h_mm, d_mm, er = 0.19, 0.01, 0.30, 0.15, 3.4
  scale = 3.0 / h_mm
  gp = 0.15

  for idx, (ax, title, is_diff) in enumerate(zip(axes, 
      ["Tab 1: Forward Calc\nZ0 = 50.12 Ohm", 
       "Tab 2: Reverse Calc\nTarget Z0 = 50 Ohm → w = 0.19 mm", 
       "Tab 3: Differential\nZd = 85.43 Ohm"], 
      [False, False, True])):
      
      h_vis = h_mm * scale
      w_vis = w_mm * scale
      t_vis = max(t_mm * scale, 0.08)
      d_vis = d_mm * scale
      cx, cy = 3.5, 2.8
      
      # Dielectric
      ax.add_patch(patches.Rectangle((cx-2.5, cy+t_vis/2), 5, h_vis/2-t_vis/2, linewidth=1.5, edgecolor="#333", facecolor="#e8d5b7", hatch="///", alpha=0.9))
      ax.add_patch(patches.Rectangle((cx-2.5, cy-h_vis/2), 5, h_vis/2-t_vis/2, linewidth=1.5, edgecolor="#333", facecolor="#e8d5b7", hatch="///", alpha=0.9))
      
      if is_diff:
          ax.add_patch(patches.Rectangle((cx-d_vis/2-w_vis, cy-t_vis/2), w_vis, t_vis, linewidth=2, edgecolor="#1a1a2e", facecolor="#c0c0c0", alpha=0.95, zorder=5))
          ax.add_patch(patches.Rectangle((cx+d_vis/2, cy-t_vis/2), w_vis, t_vis, linewidth=2, edgecolor="#1a1a2e", facecolor="#c0c0c0", alpha=0.95, zorder=5))
      else:
          ax.add_patch(patches.Rectangle((cx-w_vis/2, cy-t_vis/2), w_vis, t_vis, linewidth=2, edgecolor="#1a1a2e", facecolor="#c0c0c0", alpha=0.95, zorder=5))
      
      # GND
      ax.add_patch(patches.Rectangle((cx-2.5, cy+h_vis/2), 5, gp, linewidth=1.5, edgecolor="#333", facecolor="#444", alpha=0.95, zorder=6))
      ax.add_patch(patches.Rectangle((cx-2.5, cy-h_vis/2-gp), 5, gp, linewidth=1.5, edgecolor="#333", facecolor="#444", alpha=0.95, zorder=6))
      
      ax.set_xlim(0, 10)
      ax.set_ylim(0, 6)
      ax.set_aspect("equal")
      ax.axis("off")
      ax.set_title(title, fontsize=11, fontweight="bold", color="#1a1a2e", pad=10)

  suptitle("CRI/oFlex3 CF3 Calculator Preview - All 3 Diagram Types", fontsize=14, fontweight="bold", y=1.02)
  tight_layout()
  #savefig('/mnt/agents/output/cf3_preview.png', dpi=150, bbox_inches='tight', facecolor='white')
  #show()
  print("Preview saved!")
  pyplot(fig)
elif menu==MENU[1]: #
  pass
elif menu==MENU[2]: #
  pass
