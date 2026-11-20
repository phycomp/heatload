import numpy as np
from pyaedt import Hfss

MATERIAL_RECIPES = {
    "Nb":  {"contraction": -0.0014, "lambda_0": 85e-9,  "tc": 9.2},
    "NbN": {"contraction": -0.0009, "lambda_0": 200e-9, "tc": 16.0},
    "Ta":  {"contraction": -0.0020, "lambda_0": 50e-9,  "tc": 4.4}
}

PROCESS_KEY = "NbN"
recipe = MATERIAL_RECIPES[PROCESS_KEY]

W_LINE = 27.27 * (1.0 + recipe["contraction"])
W_PAD = 68.50 * (1.0 + recipe["contraction"])
H_SUB = 25.0 * (1.0 - 0.012)
L_LINE = 10000.0 * (1.0 + recipe["contraction"])
L_TAPER = 300.0 * (1.0 + recipe["contraction"])
L_PAD = 200.0 * (1.0 + recipe["contraction"])
T_FILM = 0.2

hfss = Hfss(specified_version="2023.2", non_graphical=False, new_desktop_session=True)
hfss.solution_type = "Modal"

sub_bottom = hfss.modeler.create_box([-250, 0, -H_SUB], [500, L_LINE, H_SUB], name="Substrate_Bottom", matname="Cryo_Kapton")
sub_top = hfss.modeler.create_box([-250, 0, T_FILM], [500, L_LINE, H_SUB], name="Substrate_Top", matname="Cryo_Kapton")

points_list = [
    [W_PAD/2, 0, 0], [W_PAD/2, L_PAD, 0], [W_LINE/2, L_PAD + L_TAPER, 0],
    [W_LINE/2, L_LINE - L_PAD - L_TAPER, 0], [W_PAD/2, L_LINE - L_PAD, 0], [W_PAD/2, L_LINE, 0],
    [-W_PAD/2, L_LINE, 0], [-W_PAD/2, L_LINE - L_PAD, 0], [-W_LINE/2, L_LINE - L_PAD - L_TAPER, 0],
    [-W_LINE/2, L_PAD + L_TAPER, 0], [-W_PAD/2, L_PAD, 0], [-W_PAD/2, 0, 0]
]
strip_sheet = hfss.modeler.create_polyline(points_list, cover_surface=True, name="Stripline_Core_Sheet")
strip_3d = hfss.modeler.extrude(strip_sheet, "Z", T_FILM)
strip_3d.material_name = "niobium"

omega_high = 2 * np.pi * 10e9
lambda_T = recipe["lambda_0"] / np.sqrt(1.0 - (0.010 / recipe["tc"])**4)
surface_reactance = omega_high * (4 * np.pi * 1e-7) * lambda_T
surface_resistance = 1e-7

hfss.assign_impedance_to_sheet("Stripline_Core_Sheet", resistance=surface_resistance, reactance=surface_reactance, is_layered=True)
print("HFSS 3D SIBC Model generated successfully.")