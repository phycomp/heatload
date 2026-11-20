from pyvista import Plotter, PolyData, Sphere, global_theme, set_plot_theme, themes
from panel import panel
import streamlit.components.v1 as components
from streamlit import iframe
from tempfile import NamedTemporaryFile
from numpy import abs, arange, array, column_stack, cos, diag, eye, full, linspace, log, max, meshgrid, min, nan, random, zeros
# ============================================================
# 2. PyVista 3D 視覺化引擎
# ============================================================

class AttractorVisualizer:
    """混沌吸子 3D 視覺化引擎"""

    def __init__(self, attractor):
        self.attractor = attractor
        self.plotter = None

    def create_plotter(self, off_screen=True):
        """建立 PyVista 繪圖器"""
        self.plotter = Plotter(window_size=[1400, 1000], off_screen=off_screen)
        self.plotter.set_background('#0a0a0a')
        self.plotter.add_text(
            self.attractor.name,
            position='upper_edge',
            font_size=16,
            color='white',
            shadow=True
        )
        return self.plotter

    def add_mesh_item(self, mesh, color=None, scalars=None, cmap="viridis", opacity=1.0, smooth_shading=True, name=None):
        """新增單一 3D 物件至場景"""
        if mesh is None:
            return
        
        kwargs = {
            "smooth_shading": smooth_shading,
            "opacity": opacity
        }
        if name:
            kwargs["name"] = name
        if scalars and scalars in mesh.array_names:
            kwargs["scalars"] = scalars
            kwargs["cmap"] = cmap
        elif color:
            kwargs["color"] = color

        self.plotter.add_mesh(mesh, **kwargs)

    def add_mesh_bundle(self, bundle):
        """新增組合型 3D 物件包 (包含多個 Mesh 與獨立樣式)"""
        for item in bundle:
            self.add_mesh_item(
                mesh=item.get("mesh"),
                color=item.get("color"),
                scalars=item.get("scalars"),
                cmap=item.get("cmap", "viridis"),
                opacity=item.get("opacity", 1.0)
            )

    def plot_trajectory_3d(self, colormap='plasma', tube_radius=None,
                          glow_effect=True, show_axes=True):
        """
        繪製 3D 相空間軌跡

        Parameters:

        colormap : str
            顏色映射（時間演化）
        tube_radius : float or None
            Tube 半徑，None 則使用線條
        glow_effect : bool
            是否添加發光效果
        show_axes : bool
            是否顯示座標軸
        """
        traj = self.attractor.get_trajectory()
        t = self.attractor.get_time()

        if traj.shape[1] < 3:
            # 2D 系統：添加 z=0
            points = column_stack([traj[:, 0], traj[:, 1], zeros(len(traj))])
        else:
            points = traj[:, :3]

        # 建立 PolyData
        poly = PolyData(points)

        # 添加時間標量（用於顏色映射）
        poly["time"] = t

        # 建立連線（線條）
        lines = column_stack([
            full(len(points) - 1, 2),
            arange(len(points) - 1),
            arange(1, len(points))
        ])
        poly.lines = lines

        if tube_radius is not None:
            # Tube 渲染
            tube = poly.tube(radius=tube_radius, n_sides=12)
            self.plotter.add_mesh(
                tube,
                scalars="time",
                cmap=colormap,
                opacity=0.9,
                smooth_shading=True,
                show_scalar_bar=True,
                scalar_bar_args={
                    'title': 'Time',
                    'color': 'white',
                    'vertical': True,
                    'position_x': 0.02,
                    'position_y': 0.3,
                    'height': 0.4
                }
            )
        else:
            # 線條渲染（更快）
            self.plotter.add_mesh(
                poly,
                scalars="time",
                cmap=colormap,
                opacity=0.8,
                line_width=2,
                render_lines_as_tubes=True,
                show_scalar_bar=True,
                scalar_bar_args={
                    'title': 'Time',
                    'color': 'white',
                    'vertical': True
                }
            )

        if glow_effect:
            # 添加發光效果（使用較粗的半透明線條）
            glow_poly = PolyData(points)
            glow_lines = column_stack([
                full(len(points) - 1, 2),
                arange(len(points) - 1),
                arange(1, len(points))
            ])
            glow_poly.lines = glow_lines
            self.plotter.add_mesh(
                glow_poly,
                color='cyan',
                opacity=0.1,
                line_width=8,
                render_lines_as_tubes=True
            )

        if show_axes:
            self.plotter.add_axes(
                xlabel='X',
                ylabel='Y',
                zlabel='Z',
                color='white',
                line_width=2
            )

        # 添加網格
        self.plotter.show_grid(color='gray')  #, opacity=0.2)

        return self.plotter

    def plot_phase_portrait(self, colormap='viridis'):
        """繪製相空間投影（3個 2D 投影）"""
        traj = self.attractor.get_trajectory()

        if traj.shape[1] < 3:
            return self.plotter

        # 創建 3 個投影平面
        # XY 平面 (z = min_z - offset)
        z_min = min(traj[:, 2])
        offset = (max(traj[:, 2]) - z_min) * 0.3

        # XY 投影
        xy_points = traj[:, :3].copy()
        xy_points[:, 2] = z_min - offset
        xy_poly = PolyData(xy_points)
        xy_lines = column_stack([
            full(len(xy_points) - 1, 2),
            arange(len(xy_points) - 1),
            arange(1, len(xy_points))
        ])
        xy_poly.lines = xy_lines
        self.plotter.add_mesh(xy_poly, color='cyan', opacity=0.15, line_width=1)

        # XZ 投影
        y_min = min(traj[:, 1])
        xz_points = traj[:, :3].copy()
        xz_points[:, 1] = y_min - offset
        xz_poly = PolyData(xz_points)
        xz_lines = column_stack([
            full(len(xz_points) - 1, 2),
            arange(len(xz_points) - 1),
            arange(1, len(xz_points))
        ])
        xz_poly.lines = xz_lines
        self.plotter.add_mesh(xz_poly, color='magenta', opacity=0.15, line_width=1)

        # YZ 投影
        x_min = min(traj[:, 0])
        yz_points = traj[:, :3].copy()
        yz_points[:, 0] = x_min - offset
        yz_poly = PolyData(yz_points)
        yz_lines = column_stack([
            full(len(yz_points) - 1, 2),
            arange(len(yz_points) - 1),
            arange(1, len(yz_points))
        ])
        yz_poly.lines = yz_lines
        self.plotter.add_mesh(yz_poly, color='yellow', opacity=0.15, line_width=1)

        return self.plotter

    def animate_trajectory_growth(self, output_file='attractor_growth.mp4',
                                  fps=30, n_frames=None, colormap='plasma'):
        """
        動畫：軌跡生長效果

        Parameters:

        output_file : str
            輸出影片檔案
        fps : int
            幀率
        n_frames : int or None
            幀數，None 則根據軌跡長度自動計算
        """
        traj = self.attractor.get_trajectory()
        t = self.attractor.get_time()

        if traj.shape[1] < 3:
            points = column_stack([traj[:, 0], traj[:, 1], zeros(len(traj))])
        else:
            points = traj[:, :3]

        if n_frames is None:
            n_frames = min(len(points), 2000)

        step = max(1, len(points) // n_frames)

        self.plotter = Plotter(window_size=[1400, 1000], off_screen=True)
        self.plotter.set_background('#0a0a0a')
        self.plotter.add_text(self.attractor.name, position='upper_edge',
                             font_size=16, color='white')
        self.plotter.add_axes(xlabel='X', ylabel='Y', zlabel='Z', color='white')
        self.plotter.show_grid(color='gray', opacity=0.2)

        # 打開影片寫入
        self.plotter.open_movie(output_file, framerate=fps)

        actor = None

        for i in range(1, len(points), step):
            if actor is not None:
                self.plotter.remove_actor(actor)

            current_points = points[:i]
            current_t = t[:i]

            poly = PolyData(current_points)
            poly["time"] = current_t

            if len(current_points) > 1:
                lines = column_stack([
                    full(len(current_points) - 1, 2),
                    arange(len(current_points) - 1),
                    arange(1, len(current_points))
                ])
                poly.lines = lines

            actor = self.plotter.add_mesh(
                poly,
                scalars="time",
                cmap=colormap,
                opacity=0.9,
                line_width=3,
                render_lines_as_tubes=True,
                show_scalar_bar=False
            )

            # 添加當前點的標記
            if len(current_points) > 0:
                sphere = Sphere(radius=0.5, center=current_points[-1])
                self.plotter.add_mesh(sphere, color='white', opacity=0.8)

            self.plotter.write_frame()

        self.plotter.close()
        輸入+=f"✅ 動畫已儲存: {output_file}"
        return output_file

    def animate_particle_tracing(self, n_particles=20, output_file='particle_trace.mp4',
                                 fps=30, colormap='rainbow'):
        """
        動畫：多粒子追蹤效果

        從初始條件附近發射多個粒子，展示敏感依賴性
        """
        traj = self.attractor.get_trajectory()
        t = self.attractor.get_time()

        if traj.shape[1] < 3:
            points = column_stack([traj[:, 0], traj[:, 1], zeros(len(traj))])
        else:
            points = traj[:, :3]

        # 生成鄰近初始條件
        seed(42)
        perturbations = []
        for i in range(n_particles):
            eps = 0.01 * (i + 1)
            perturbed_y0 = self.attractor.y0 + randn(3) * eps
            perturbed = self.attractor.__class__(
                **self.attractor.params,
                initial_condition=perturbed_y0.tolist(),
                t_span=self.attractor.t_span,
                n_steps=self.attractor.n_steps
            )
            perturbed.integrgrate()
            p_traj = perturbed.get_trajectory()
            if p_traj.shape[1] < 3:
                p_points = column_stack([p_traj[:, 0], p_traj[:, 1], zeros(len(p_traj))])
            else:
                p_points = p_traj[:, :3]
            perturbations.append(p_points)

        n_frames = min(1000, len(points) // 10)
        step = max(1, len(points) // n_frames)

        self.plotter = Plotter(window_size=[1400, 1000], off_screen=True)
        self.plotter.set_background('#0a0a0a')
        self.plotter.add_text(f"{self.attractor.name} - Particle Tracing", position='upper_edge', font_size=16, color='white')
        self.plotter.add_axes(xlabel='X', ylabel='Y', zlabel='Z', color='white')

        self.plotter.open_movie(output_file, framerate=fps)

        colors = cm.get_cmap(colormap)(linspace(0, 1, n_particles))

        for frame_idx in range(0, n_frames):
            self.plotter.clear()
            self.plotter.add_text(f"{self.attractor.name} - Particle Tracing",
                                 position='upper_edge', font_size=16, color='white')
            self.plotter.add_axes(xlabel='X', ylabel='Y', zlabel='Z', color='white')

            i = min(frame_idx * step, len(points) - 1)

            # 繪製參考軌跡（半透明）
            ref_points = points[:i+1]
            if len(ref_points) > 1:
                ref_poly = PolyData(ref_points)
                ref_lines = column_stack([
                    full(len(ref_points) - 1, 2),
                    arange(len(ref_points) - 1),
                    arange(1, len(ref_points))
                ])
                ref_poly.lines = ref_lines
                self.plotter.add_mesh(ref_poly, color='white', opacity=0.2, line_width=1)

            # 繪製每個粒子
            for j, p_points in enumerate(perturbations):
                p_current = p_points[:i+1]
                if len(p_current) > 1:
                    p_poly = PolyData(p_current)
                    p_lines = column_stack([
                        full(len(p_current) - 1, 2),
                        arange(len(p_current) - 1),
                        arange(1, len(p_current))
                    ])
                    p_poly.lines = p_lines
                    color = colors[j][:3]
                    self.plotter.add_mesh(p_poly, color=color, opacity=0.7, line_width=2)

                # 當前位置標記
                if len(p_current) > 0:
                    sphere = Sphere(radius=0.3, center=p_current[-1])
                    self.plotter.add_mesh(sphere, color=color, opacity=0.9)

            self.plotter.write_frame()

        self.plotter.close()
        輸入+=f"✅ 粒子追蹤動畫已儲存: {output_file}"
        return output_file

    def 流光畫布(self, height=None):
        """完全避開 Thread/Pickle/Trame 限制，將 VTK 場景匯出為純 WebGL HTML"""
        self.plotter.reset_camera()

        # 使用 Panel 將 PyVista 視窗轉譯為純 HTML (最穩健方案)
        潘 = panel(self.plotter.ren_win)

        with NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            潘.save(tmp.name, embed=True)
            with open(tmp.name, 'r', encoding='utf-8') as fin:
              世界 = fin.read()

        components.html(世界, height=height, scrolling=True)  #width='stretch')  #
