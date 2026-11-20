import asyncio
import sys
try:
    loop = asyncio.get_event_loop_policy().get_event_loop()
    loop.add_signal_handler = lambda *args, **kwargs: None
except Exception: pass
from pyvista import OFF_SCREEN

from pyvista import Arrow, Light, Line, Plotter, Sphere, lines_from_points, set_plot_theme, global_theme, OFF_SCREEN
from numpy import abs, arccos, arctan2, array, clip, column_stack, conj, cos, cross, diag, dot, exp, imag, linalg, linspace, ones_like, pi, radians, real, sin, sqrt, zeros_like
from streamlit.components.v1 import components as stHTML
#from tempfile import NamedTemporaryFile
OFF_SCREEN = True
# ============================================================
# 第一部分: PyVista 進階 API 範例
# ============================================================

class 維斯塔:
    """
    PyVista Bloch Sphere 進階 API 類別
    封裝所有 PyVista 3D 渲染功能
    """

    def __init__(self, window_size=(1000, 800), background='white'):
        """
        初始化 PyVista Plotter

        Parameters:

        window_size : tuple
            視窗大小 (寬, 高)
        background : str or tuple
            背景顏色
        """
        self.window_size = window_size
        self.background = background
        self.plotter = None
        self.meshes = {}  # 儲存所有 mesh 物件以便更新

    def create_scene(self, off_screen=True, notebook=False):
        """
        創建 3D 場景

        Parameters:

        off_screen : bool
            是否離屏渲染 (無視窗)
        notebook : bool
            是否在 Jupyter 中使用

        Returns:

        plotter : Plotter
            PyVista Plotter 實例
        """
        self.plotter = Plotter(
            off_screen=off_screen,
            window_size=self.window_size,
            notebook=notebook
        )

        set_plot_theme("document") # 設定主題

        if isinstance(self.background, str):
            self.plotter.set_background(self.background)
        else:
            self.plotter.set_background(self.background) # 設定背景

        self.plotter.camera_position = [
            (2.5, 2.5, 2.0),   # 相機位置
            (0, 0, 0),          # 焦點
            (0, 0, 1)           # 上方向
        ] # 設定相機

        self.plotter.enable_anti_aliasing('ssaa') # 啟用抗鋸齒

        return self.plotter

    def add_sphere_surface(self, radius=1.0, opacity=0.15, color='lightblue', theta_res=50, phi_res=50, smooth=True):
        """
        添加半透明球體表面

        Parameters:

        radius : float
            球體半徑
        opacity : float
            透明度 (0-1)
        color : str
            顏色名稱
        theta_res, phi_res : int
            經緯度解析度
        smooth : bool
            是否平滑著色
        """
        sphere = Sphere(
            radius=radius,
            theta_resolution=theta_res,
            phi_resolution=phi_res
        )

        mesh = self.plotter.add_mesh(sphere, opacity=opacity, color=color, smooth_shading=smooth, show_edges=False, name='sphere_surface')
        self.meshes['sphere'] = mesh
        return mesh

    def add_wireframe_grid(self, n_meridians=8, n_parallels=5, color='gray', opacity=0.3, line_width=1):
        """
        添加經緯線網格

        Parameters:

        n_meridians : int
            經線數量
        n_parallels : int
            緯線數量
        color : str
            線條顏色
        opacity : float
            線條透明度
        line_width : int
            線條寬度
        """
        # 經線 (Meridians)
        for phi in linspace(0, 2*pi, n_meridians, endpoint=False):
            theta_vals = linspace(0, pi, 50)
            x_line = sin(theta_vals) * cos(phi)
            y_line = sin(theta_vals) * sin(phi)
            z_line = cos(theta_vals)
            line_pts = column_stack([x_line, y_line, z_line])
            line = lines_from_points(line_pts)
            self.plotter.add_mesh(
                line, color=color, opacity=opacity,
                line_width=line_width, name=f'meridian_{phi:.2f}'
            )

        # 緯線 (Parallels)
        for theta in linspace(0.1, pi-0.1, n_parallels):
            phi_vals = linspace(0, 2*pi, 50)
            x_line = sin(theta) * cos(phi_vals)
            y_line = sin(theta) * sin(phi_vals)
            z_line = ones_like(phi_vals) * cos(theta)
            line_pts = column_stack([x_line, y_line, z_line])
            line = lines_from_points(line_pts)
            self.plotter.add_mesh(
                line, color=color, opacity=opacity,
                line_width=line_width, name=f'parallel_{theta:.2f}'
            )

    def add_axes(self, length=1.5, line_width=3,
                 x_color='blue', y_color='green', z_color='red',
                 show_labels=True, label_size=14):
        """
        添加 XYZ 座標軸

        Parameters:

        length : float
            軸長度
        line_width : int
            線條寬度
        x_color, y_color, z_color : str
            各軸顏色
        show_labels : bool
            是否顯示標籤
        label_size : int
            標籤字體大小
        """
        axes_data = [
            ((-length, 0, 0), (length, 0, 0), x_color, 'X', (length+0.15, 0, 0)),
            ((0, -length, 0), (0, length, 0), y_color, 'Y', (0, length+0.15, 0)),
            ((0, 0, -length), (0, 0, length), z_color, 'Z', (0, 0, length+0.15))
        ]

        for start, end, color, label, label_pos in axes_data:
            axis_line = Line(start, end)
            self.plotter.add_mesh(
                axis_line, color=color, line_width=line_width,
                name=f'axis_{label}'
            )

            if show_labels:
                self.plotter.add_point_labels(
                    [label_pos], [label],
                    text_color=color,
                    font_size=label_size,
                    bold=True,
                    name=f'label_{label}'
                )

    def add_state_vector(self, x, y, z, color='gold',
                         tip_length=0.15, tip_radius=0.05,
                         shaft_radius=0.02, show_label=True,
                         name='state_vector'):
        """
        添加量子態向量箭頭

        Parameters:

        x, y, z : float
            Bloch 球座標 (需正規化)
        color : str
            箭頭顏色
        tip_length, tip_radius, shaft_radius : float
            箭頭幾何參數
        show_label : bool
            是否顯示 |ψ⟩ 標籤
        name : str
            mesh 名稱 (用於更新)
        """
        # 正規化方向向量
        norm = sqrt(x**2 + y**2 + z**2)
        if norm > 1e-10:
            dx, dy, dz = x/norm, y/norm, z/norm
        else:
            dx, dy, dz = 0, 0, 1

        # 創建箭頭
        arrow = Arrow(
            start=(0, 0, 0),
            direction=(dx, dy, dz),
            tip_length=tip_length,
            tip_radius=tip_radius,
            shaft_radius=shaft_radius,
            scale=norm  # 縮放至實際 Bloch 向量長度
        )

        mesh = self.plotter.add_mesh(
            arrow, color=color, smooth_shading=True,
            name=f'{name}_arrow'
        )

        # 狀態點 (箭頭末端)
        end_point = Sphere(radius=0.05, center=(x, y, z))
        self.plotter.add_mesh(
            end_point, color='darkorange',
            name=f'{name}_point'
        )

        if show_label:
            self.plotter.add_point_labels(
                [(x+0.1, y+0.1, z+0.1)], ['|ψ⟩'],
                text_color='darkorange',
                font_size=12,
                name=f'{name}_label'
            )

        self.meshes[name] = {'arrow': arrow, 'point': end_point}
        return mesh

    def add_evolution_path(self, history, color='orange',
                           line_width=4, opacity=0.7,
                           show_points=True, point_size=0.03,
                           name='evolution'):
        """
        添加演化軌跡

        Parameters:

        history : list of tuple
            [(x1,y1,z1), (x2,y2,z2), ...] 演化歷史
        color : str
            軌跡顏色
        line_width : int
            線條寬度
        opacity : float
            透明度
        show_points : bool
            是否顯示軌跡點
        point_size : float
            軌跡點大小
        name : str
            mesh 名稱
        """
        if len(history) < 2:
            return None

        points = array(history)

        # 創建軌跡線
        line = lines_from_points(points)
        mesh = self.plotter.add_mesh(
            line, color=color, line_width=line_width,
            opacity=opacity, name=f'{name}_path'
        )

        # 軌跡點 (每 N 個點顯示一個)
        if show_points:
            n_points = len(history)
            step = max(1, n_points // 20)  # 最多顯示 20 個點

            for i in range(0, n_points, step):
                px, py, pz = history[i]
                point = Sphere(radius=point_size, center=(px, py, pz))
                self.plotter.add_mesh(
                    point, color=color, opacity=0.6,
                    name=f'{name}_point_{i}'
                )

        self.meshes[name] = mesh
        return mesh

    def add_great_circle(self, axis='z', color='purple',
                         opacity=0.4, line_width=2, name='great_circle'):
        """
        添加大圓 (Great Circle)

        Parameters:

        axis : str
            'x', 'y', or 'z' — 大圓所在平面法向量
        color : str
            線條顏色
        opacity : float
            透明度
        line_width : int
            線條寬度
        name : str
            mesh 名稱
        """
        theta_vals = linspace(0, 2*pi, 100)

        if axis == 'z':
            x_vals = cos(theta_vals)
            y_vals = sin(theta_vals)
            z_vals = zeros_like(theta_vals)
        elif axis == 'y':
            x_vals = cos(theta_vals)
            y_vals = zeros_like(theta_vals)
            z_vals = sin(theta_vals)
        elif axis == 'x':
            x_vals = zeros_like(theta_vals)
            y_vals = cos(theta_vals)
            z_vals = sin(theta_vals)

        points = column_stack([x_vals, y_vals, z_vals])
        line = lines_from_points(points)

        mesh = self.plotter.add_mesh(
            line, color=color, opacity=opacity,
            line_width=line_width, name=name
        )
        return mesh

    def add_equator(self, color='gray', opacity=0.5, line_width=2):
        """添加赤道線 (XY 平面大圓)"""
        return self.add_great_circle(axis='z', color=color,
                                     opacity=opacity, line_width=line_width,
                                     name='equator')

    def add_lighting(self, ambient=0.3, diffuse=0.7, specular=0.5):
        """
        添加進階光源設定

        Parameters:

        ambient : float
            環境光強度
        diffuse : float
            漫反射強度
        specular : float
            鏡面反射強度
        """
        # 添加多個光源以增強 3D 效果
        lights = [
            {'position': (5, 5, 5), 'color': 'white', 'intensity': 1.0},
            {'position': (-5, -5, 5), 'color': 'lightblue', 'intensity': 0.5},
            {'position': (0, 5, -5), 'color': 'purple', 'intensity': 0.3}
        ]

        for light_cfg in lights:
            light = Light(position=light_cfg['position'], color=light_cfg['color'], intensity=light_cfg['intensity'])
            self.plotter.add_light(light)

    def setup_camera_orbit(self, radius=3.0, n_frames=60,
                          elevation=30, target=(0,0,0)):
        """
        設定相機軌道 (用於動畫旋轉)

        Parameters:

        radius : float
            軌道半徑
        n_frames : int
            軌道幀數
        elevation : float
            仰角 (度)
        target : tuple
            焦點位置

        Returns:

        camera_positions : list
            每幀的相機位置列表
        """
        camera_positions = []
        for i in range(n_frames):
            angle = 2 * pi * i / n_frames
            x = radius * cos(angle) * cos(radians(elevation))
            y = radius * sin(angle) * cos(radians(elevation))
            z = radius * sin(radians(elevation))
            camera_positions.append([
                (x, y, z),
                target,
                (0, 0, 1)
            ])
        return camera_positions

    def render_frame(self, filename=None, return_img=True):
        """
        渲染單一幀

        Parameters:

        filename : str or None
            若提供則保存至檔案
        return_img : bool
            是否回傳圖片陣列

        Returns:

        img : ndarray or None
            圖片陣列 (若 return_img=True)
        """
        if filename:
            self.plotter.screenshot(filename)

        if return_img:
            return self.plotter.screenshot(return_img=True)
        return None

    def close(self):
        """關閉 Plotter 並釋放資源"""
        if self.plotter:
            self.plotter.close()
            self.plotter = None

    def 至流光(self):
      #with NamedTemporaryFile(suffix=".html", delete=False) as tf:
      #    html_path = tf.name
      #    self.plotter.export_html(html_path, backend="trame")   #
      global_theme.trame.jupyter_extension_enabled = False
      #global_theme.trame.jupyter_extension_enabled = False
      OFF_SCREEN = True
      內容 = self.plotter.export_html(None)

      #with open(html_path, "r", encoding="utf-8") as fin:
      #    內容 = fin.read()
      stHTML(內容, height=600, scrolling=False)
