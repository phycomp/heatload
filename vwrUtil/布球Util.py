from pyvista import Arrow, Line, Plotter, Sphere, Spline
from numpy import linspace, pi as π, column_stack, cos, sin, zeros_like, array
from 比特閘Util import state_to_bloch, state_to_bloch
# ==================== PyVista 3D 視覺化 (核心) ====================

def 布球(state, history=None, camera_pos=None):
    """
    建立 PyVista Plotter 物件，包含完整的 Bloch Sphere 場景
    """
    # 使用 off_screen=True 確保在無 GUI 環境也能渲染
    plotter = Plotter(window_size=[800, 800], off_screen=True)
    plotter.background_color = '#1a1a2e'

    # --- 繪製球體（半透明網格）
    sphere = Sphere(radius=1.0, theta_resolution=60, phi_resolution=60)
    plotter.add_mesh(sphere, opacity=0.12, color='lightblue',
                     smooth_shading=True, show_edges=False)

    # --- 繪製座標軸
    axis_len = 1.4
    line_width = 3

    # X 軸 (紅色) - |+⟩ / |-⟩
    x_axis = Line([-axis_len, 0, 0], [axis_len, 0, 0])
    plotter.add_mesh(x_axis, color='#ff6b6b', line_width=line_width)
    plotter.add_point_labels([[axis_len+0.1, 0, 0]], ['|+⟩'],
                            text_color='#ff6b6b', font_size=14, bold=True)
    plotter.add_point_labels([[-axis_len-0.1, 0, 0]], ['|-⟩'],
                            text_color='#ff6b6b', font_size=14, bold=True)

    # Y 軸 (綠色) - |+i⟩ / |-i⟩
    y_axis = Line([0, -axis_len, 0], [0, axis_len, 0])
    plotter.add_mesh(y_axis, color='#51cf66', line_width=line_width)
    plotter.add_point_labels([[0, axis_len+0.1, 0]], ['|+i⟩'],
                            text_color='#51cf66', font_size=14, bold=True)
    plotter.add_point_labels([[0, -axis_len-0.1, 0]], ['|-i⟩'],
                            text_color='#51cf66', font_size=14, bold=True)

    # Z 軸 (藍色) - |0⟩ / |1⟩
    z_axis = Line([0, 0, -axis_len], [0, 0, axis_len])
    plotter.add_mesh(z_axis, color='#339af0', line_width=line_width)
    plotter.add_point_labels([[0, 0, axis_len+0.1]], ['|0⟩'],
                            text_color='#339af0', font_size=14, bold=True)
    plotter.add_point_labels([[0, 0, -axis_len-0.1]], ['|1⟩'],
                            text_color='#339af0', font_size=14, bold=True)

    # --- 繪製赤道 (黃色虛線效果)
    theta = linspace(0, 2*π, 200)
    equator_points = column_stack([cos(theta), sin(theta), zeros_like(theta)])
    equator = Spline(equator_points, 200)
    plotter.add_mesh(equator, color='#ffd43b', line_width=2, opacity=0.6)

    # --- 繪製經線 (輔助線)
    for phi in [0, π/4, π/2, 3*π/4]:
        t = linspace(0, π, 100)
        meridian = column_stack([
            sin(t) * cos(phi),
            sin(t) * sin(phi),
            cos(t)
        ])
        meridian_line = Spline(meridian, 100)
        plotter.add_mesh(meridian_line, color='gray', line_width=1, opacity=0.3)

    # --- 繪製歷史軌跡
    if history and len(history) > 1:
        hist_points = []
        for hist_state in history:
            hx, hy, hz = state_to_bloch(hist_state[0], hist_state[1])
            hist_points.append([hx, hy, hz])

        hist_points = array(hist_points)
        # 使用 Tube 讓軌跡更有立體感
        if len(hist_points) >= 2:
            spline = Spline(hist_points, len(hist_points)*10)
            plotter.add_mesh(spline, color='#ff922b', line_width=4, opacity=0.7)

            # 歷史點標記
            for i, pt in enumerate(hist_points):
                if i % max(1, len(hist_points)//8) == 0 or i == len(hist_points)-1:
                    small_sphere = Sphere(radius=0.03, center=pt)
                    plotter.add_mesh(small_sphere, color='#ff922b', opacity=0.5)

    # --- 繪製當前狀態向量
    x, y, z = state_to_bloch(state[0], state[1])

    # 狀態向量箭頭 (從原點到球面)
    arrow = Arrow(start=[0, 0, 0], direction=[x, y, z],
                     tip_length=0.15, tip_radius=0.05, shaft_radius=0.02,
                     scale=1.0)
    plotter.add_mesh(arrow, color='#22b8cf', smooth_shading=True)

    # 狀態點 (發光效果)
    point_sphere = Sphere(radius=0.06, center=[x, y, z])
    plotter.add_mesh(point_sphere, color='#22b8cf', smooth_shading=True,
                     ambient=0.5, diffuse=0.5)

    # 外圍光暈
    glow = Sphere(radius=0.1, center=[x, y, z])
    plotter.add_mesh(glow, color='#22b8cf', opacity=0.2, smooth_shading=True)

    # --- 座標標籤
    label_text = f"({x:.3f}, {y:.3f}, {z:.3f})"
    plotter.add_point_labels([[x, y, z]], [label_text],
                            text_color='white', font_size=12,
                            shape_color='black', shape_opacity=0.7,
                            bold=True)

    # --- 相機設定
    if camera_pos is not None:
        plotter.camera_position = camera_pos
    else:
        plotter.camera_position = 'iso'

    plotter.enable_anti_aliasing()
    plotter.show_axes()

    return plotter


def render_bloch_sphere_to_image(state, history=None, camera_pos=None,
                                  image_size=(800, 800)):
    """
    核心函數：使用 PyVista API 將 3D 場景渲染為圖片
    方法：使用 plotter.screenshot() 或 plotter.to_image()
    """
    plotter = 布球(state, history, camera_pos)

    # 方法1: 使用 screenshot() 直接獲取 numpy array
    # 這是 PyVista 原生 API，不需要 GUI
    plotter.show(auto_close=False)  # 先 show 但不關閉
    img_array = plotter.screenshot(transparent_background=False,
                                  return_img=True,
                                  window_size=image_size)
    plotter.close()

    return img_array


def render_bloch_sphere_to_bytes(state, history=None, camera_pos=None,
                                    image_size=(800, 800), fmt='png'):
    """
    將 Bloch Sphere 渲染為 bytes，方便 Streamlit 顯示
    """
    plotter = 布球(state, history, camera_pos)

    # 使用 PyVista 的 to_image() 方法
    plotter.show(auto_close=False)

    # 截圖並保存到 BytesIO
    buf = BytesIO()
    plotter.screenshot(filename=buf, transparent_background=False,
                       window_size=image_size)
    buf.seek(0)
    plotter.close()

    return buf.getvalue()



