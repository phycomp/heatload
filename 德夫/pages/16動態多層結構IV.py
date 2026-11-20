from pyvista import Box, Cylinder, Plotter
# 測試 PyVista 3D 繪圖函數
import pyvista as pv
import numpy as np
from dataclasses import dataclass

@dataclass
class StriplineGeometry:
    w: float; t: float; h: float; s: float; L: float; n_channels: int

geo_test = StriplineGeometry(w=0.3, t=5, h=0.15, s=2.0, L=400, n_channels=8)

# 測試 PyVista 3D 繪圖
w = geo_test.w / 1000
h = geo_test.h / 1000
t = geo_test.t / 1e6
L = geo_test.L / 1000
s = geo_test.s / 1000
n_draw = 4

plotter = Plotter(off_screen=True, window_size=[1200, 800])
plotter.set_background('white')

z0, z1, z2, z3, z4, z5 = 0.0, t, t+h, t+h+t, t+h+t+h, t+h+t+h+t
total_w = s * n_draw
margin = s * 0.4

c_poly = [0.91, 0.86, 0.78]
c_ag = [0.72, 0.53, 0.04]
c_via = [0.55, 0.27, 0.07]
c_gnd_sep = [0.83, 0.69, 0.22]

# 下接地層
bottom_gnd = Box(bounds=[-margin/2, total_w+margin/2, 0, L, z0, z1])
plotter.add_mesh(bottom_gnd, color=c_ag, opacity=0.95, show_edges=True, edge_color='black')

# 下介電層
bottom_dielectric = Box(bounds=[-margin/2, total_w+margin/2, 0, L, z1, z2])
plotter.add_mesh(bottom_dielectric, color=c_poly, opacity=0.6, show_edges=True)

# 信號層
for i in range(n_draw):
    x_c = s * (i + 0.5)
    signal = Box(bounds=[x_c-w/2, x_c+w/2, 0, L, z2, z3])
    plotter.add_mesh(signal, color=c_ag, opacity=0.95, show_edges=True)
    if i < n_draw - 1:
        g_x = x_c + s/2
        g_w = min(w*0.25, s-w-0.00002)
        if g_w > 0.00001:
            gnd_sep = Box(bounds=[g_x-g_w/2, g_x+g_w/2, 0, L, z2, z3])
            plotter.add_mesh(gnd_sep, color=c_gnd_sep, opacity=0.9, show_edges=True)

# 上介電層
top_dielectric = Box(bounds=[-margin/2, total_w+margin/2, 0, L, z3, z4])
plotter.add_mesh(top_dielectric, color=c_poly, opacity=0.6, show_edges=True)

# 上接地層
top_gnd = Box(bounds=[-margin/2, total_w+margin/2, 0, L, z4, z5])
plotter.add_mesh(top_gnd, color=c_ag, opacity=0.95, show_edges=True)

# Via
via_r = min(150/2e6, t*0.4, h*0.3)
via_spacing = 1.0/2.0/1000
n_vias = int(total_w/via_spacing)+2
for i in range(n_vias):
    x_v = i*via_spacing
    if x_v > total_w+margin/2 or x_v < -margin/2: continue
    via_cyl = Cylinder(center=(x_v, L/2, z5/2), direction=(0,0,1), radius=via_r, height=z5)
    plotter.add_mesh(via_cyl, color=c_via, opacity=0.8, show_edges=True)

plotter.camera_position = [(total_w*1.5, -L*0.8, z5*3), (total_w/2, L/2, z5/2), (0,0,1)]
plotter.camera.zoom(0.8)
plotter.add_text("Cri/oFlex3 Stripline 3D View\\n8ch G-S-G | L=400mm", position='upper_edge', font_size=14)
plotter.add_axes(line_width=2)
plotter

#img = plotter.screenshot()
#plotter.close()
