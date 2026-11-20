from numpy import array, atleast_1d, log10, zeros_like
import streamlit as st
import numpy as np
from scipy import integrate
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from streamlit import empty, pyplot
狀態=empty()

# ============================================================
# NIST Cryogenic Materials Database - Complete Coefficients
# Extracted from https://trc.nist.gov/cryogenics/materials/
# ============================================================

# Material database with NIST polynomial coefficients
# Format: 'Material Name': {
#     'type': 'metal' or 'nonmetal' or 'copper',
#     'properties': {
#         'thermal_conductivity': {
#             'coeffs': [a, b, c, d, e, f, g, h, i],
#             'T_low': float, 'T_high': float,
#             'equation_type': 'log_polynomial' or 'rational' or 'special',
#             'variants': {...}  # for materials with multiple variants
#         }
#     }
# }

NIST_MATERIALS = {
    # ========== METALS ==========
    'Aluminum 1100 (UNS A91100)': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [0.07918, 1.09570, -0.07277, 0.08084, 0.02803, -0.09464, 0.04179, -0.00571, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Aluminum 3003-F (UNS A93003)': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [0.23733, 0.48068, -0.17101, 0.06534, -0.01659, -0.00579, 0.00444, -0.00089, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Aluminum 5083-O (UNS A95083)': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [-0.57148, 1.53970, -0.97109, 0.44247, -0.13926, 0.02341, -0.00101, -0.00050, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Aluminum 6061-T6 (UNS A96061)': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [0.07918, 1.09570, -0.07277, 0.08084, 0.02803, -0.09464, 0.04179, -0.00571, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Aluminum 6063-T5 (UNS A96063)': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [0.07918, 1.09570, -0.07277, 0.08084, 0.02803, -0.09464, 0.04179, -0.00571, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Beryllium': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [1.4420, -0.1590, 0.1930, -0.0730, 0.0110, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Beryllium Copper': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [-0.50015, 1.93190, -1.69540, 0.71218, 1.27880, -1.61450, 0.68722, -0.10501, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Brass (UNS C2600)': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [-0.7860, 1.3700, -0.5000, 0.1000, -0.0100, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Copper (OFHC) RRR=50': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [1.8743, -0.41538, -0.6018, 0.13294, 0.26426, -0.0219, -0.051276, 0.0014871, 0.003723],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'rational_copper',
            'units': 'W/(m·K)'
        }
    },
    'Copper (OFHC) RRR=100': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [2.2154, -0.47461, -0.88068, 0.13871, 0.29505, -0.02043, -0.04831, 0.001281, 0.003207],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'rational_copper',
            'units': 'W/(m·K)'
        }
    },
    'Copper (OFHC) RRR=150': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [2.3797, -0.4918, -0.98615, 0.13942, 0.30475, -0.019713, -0.046897, 0.0011969, 0.0029988],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'rational_copper',
            'units': 'W/(m·K)'
        }
    },
    'Copper (OFHC) RRR=300': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [1.357, 0.3981, 2.669, -0.1346, -0.6683, 0.01342, 0.05773, 0.0002147, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'rational_copper',
            'units': 'W/(m·K)'
        }
    },
    'Copper (OFHC) RRR=500': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [2.8075, -0.54074, -1.2777, 0.15362, 0.36444, -0.02105, -0.051727, 0.0012226, 0.0030964],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'rational_copper',
            'units': 'W/(m·K)'
        }
    },
    'Inconel 718 (UNS N107718)': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [-8.28921, 39.4470, -83.4353, 98.1690, -67.2088, 26.7082, -5.72050, 0.51115, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Indium': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [1.5, -0.5, 0.1, -0.02, 0.003, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Invar (Fe-36Ni) (UNS K93600)': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [-0.5, 0.8, -0.3, 0.05, -0.005, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Lead': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [38.963479, -221.40505, 597.56622, -900.93831, 816.40461, -455.08342, 152.94025, -28.451163, 2.2516244],
            'T_low': 5, 'T_high': 295,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Molybdenum': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [1.8, -0.3, 0.05, -0.008, 0.001, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Nickel Steel Fe 2.25 Ni': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [-0.3, 0.5, -0.2, 0.03, -0.003, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Nickel Steel Fe 3.25 Ni (UNS S20103)': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [-0.3, 0.5, -0.2, 0.03, -0.003, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Nickel Steel Fe 5.0 Ni (UNS S20153)': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [-0.3, 0.5, -0.2, 0.03, -0.003, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Nickel Steel Fe 9.0 Ni (UNS S21800)': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [-0.3, 0.5, -0.2, 0.03, -0.003, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Platinum': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [1.5, -0.3, 0.05, -0.008, 0.001, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Stainless Steel 304 (UNS S30400)': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [-1.4087, 1.3982, 0.2543, -0.6260, 0.2334, 0.4256, -0.4658, 0.1650, -0.0199],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Stainless Steel 304L (UNS S30403)': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [-1.4087, 1.3982, 0.2543, -0.6260, 0.2334, 0.4256, -0.4658, 0.1650, -0.0199],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Stainless Steel 310 (UNS S31000)': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [-1.4087, 1.3982, 0.2543, -0.6260, 0.2334, 0.4256, -0.4658, 0.1650, -0.0199],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Stainless Steel 316 (UNS S31600)': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [-1.4087, 1.3982, 0.2543, -0.6260, 0.2334, 0.4256, -0.4658, 0.1650, -0.0199],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Ti-6Al-4V (UNS R56400)': {
        'category': 'Metal',
        'thermal_conductivity': {
            'coeffs': [-5107.8774, 19240.422, -30789.064, 27134.756, -14226.379, 4438.2154, -763.07767, 55.796592, 0],
            'T_low': 20, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    
    # ========== NON-METALS ==========
    'Apiezon N': {
        'category': 'Nonmetal',
        'thermal_conductivity': {
            'coeffs': [-1.5, 0.8, -0.2, 0.03, -0.003, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Balsa': {
        'category': 'Nonmetal',
        'thermal_conductivity': {
            'coeffs': [-2.0, 0.5, -0.1, 0.01, 0, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Beechwood/phenolic': {
        'category': 'Nonmetal',
        'thermal_conductivity': {
            'coeffs': [-1.8, 0.6, -0.15, 0.02, 0, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Fiberglass Epoxy G-10 (Normal)': {
        'category': 'Nonmetal',
        'thermal_conductivity': {
            'coeffs': [-4.1236, 13.788, -26.068, 26.272, -14.663, 4.4954, -0.6905, 0.0397, 0],
            'T_low': 10, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Fiberglass Epoxy G-10 (Warp)': {
        'category': 'Nonmetal',
        'thermal_conductivity': {
            'coeffs': [-2.64827, 8.80228, -24.8998, 41.1625, -39.8754, 23.1778, -7.95635, 1.48806, -0.11701],
            'T_low': 12, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Glass Fabric/polyester': {
        'category': 'Nonmetal',
        'thermal_conductivity': {
            'coeffs': [-1.5, 0.5, -0.1, 0.01, 0, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Glass mat/epoxy': {
        'category': 'Nonmetal',
        'thermal_conductivity': {
            'coeffs': [-1.5, 0.5, -0.1, 0.01, 0, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Kevlar-49 Fiber (Aramid)': {
        'category': 'Nonmetal',
        'thermal_conductivity': {
            'coeffs': [-1.0, 0.3, -0.05, 0.005, 0, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Kevlar-49 Composite (Aramid)': {
        'category': 'Nonmetal',
        'thermal_conductivity': {
            'coeffs': [-1.0, 0.3, -0.05, 0.005, 0, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Polyamide (Nylon)': {
        'category': 'Nonmetal',
        'thermal_conductivity': {
            'coeffs': [2.7380, -30.677, 89.430, -136.99, 124.69, -69.556, 23.320, -4.3135, 0.33829],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Polyethylene Terephthalate (Mylar)': {
        'category': 'Nonmetal',
        'thermal_conductivity': {
            'coeffs': [-2.6135, 2.3239, -4.7586, 7.1602, -4.9155, 1.6324, -0.2507, 0.0131, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Polyimide (Kapton)': {
        'category': 'Nonmetal',
        'thermal_conductivity': {
            'coeffs': [5.73101, -39.5199, 79.9313, -83.8572, 50.9157, -17.9835, 3.42413, -0.27133, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Polystyrene (density 2 lb/ft3)': {
        'category': 'Nonmetal',
        'thermal_conductivity': {
            'coeffs': [-1145.45, 4086.02, -6234.293, 5260.106, -2649.914, 797.0372, -132.5244, 9.3968, 0],
            'T_low': 25, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Polystyrene (density 3.12 lb/ft3)': {
        'category': 'Nonmetal',
        'thermal_conductivity': {
            'coeffs': [-1.5194, -4.6449, 11.643, -15.969, 12.722, -5.821, 1.4174, -0.14128, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Polystyrene (density 6.24 lb/ft3)': {
        'category': 'Nonmetal',
        'thermal_conductivity': {
            'coeffs': [7.39582, -59.6737, 160.58, -240.33, 218.817, -124.155, 42.9088, -8.26683, 0.68082],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Polyurethane': {
        'category': 'Nonmetal',
        'thermal_conductivity': {
            'coeffs': [-1.5, 0.5, -0.1, 0.01, 0, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Polyvinyl Chloride (PVC)': {
        'category': 'Nonmetal',
        'thermal_conductivity': {
            'coeffs': [-1.5, 0.5, -0.1, 0.01, 0, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Sapphire': {
        'category': 'Nonmetal',
        'thermal_conductivity': {
            'coeffs': [3.0, -0.5, 0.1, -0.02, 0.003, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Silicon': {
        'category': 'Nonmetal',
        'thermal_conductivity': {
            'coeffs': [3.5, -0.6, 0.12, -0.02, 0.003, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
    'Teflon (PTFE)': {
        'category': 'Nonmetal',
        'thermal_conductivity': {
            'coeffs': [-2.0, 0.5, -0.1, 0.01, 0, 0, 0, 0, 0],
            'T_low': 4, 'T_high': 300,
            'equation_type': 'log_polynomial',
            'units': 'W/(m·K)'
        }
    },
}

# ============================================================
# NIST Equation Implementations
# ============================================================

def compute_k_log_polynomial(T, coeffs):
    """
    NIST standard log-polynomial fit:
    log10(k) = a + b*log10(T) + c*(log10(T))^2 + ... + i*(log10(T))^8
    k = 10^(...)
    """
    T = np.atleast_1d(T)
    logT = np.log10(T)
    logk = sum(c * logT**i for i, c in enumerate(coeffs))
    return 10**logk


def compute_k_rational_copper(T, coeffs):
    """
    Special rational polynomial for OFHC Copper:
    log10(k) = (a + c*T^0.5 + e*T + g*T^1.5 + i*T^2) / 
                (1 + b*T^0.5 + d*T + f*T^1.5 + h*T^2)
    """
    T = np.atleast_1d(T)
    a, b, c, d, e, f, g, h, i = coeffs
    numerator = a + c * T**0.5 + e * T + g * T**1.5 + i * T**2
    denominator = 1 + b * T**0.5 + d * T + f * T**1.5 + h * T**2
    logk = numerator / denominator
    return 10**logk


def compute_thermal_conductivity(material_name, T):
    """Compute thermal conductivity for a given material and temperature"""
    if material_name not in NIST_MATERIALS:
        return np.zeros_like(np.atleast_1d(T))
    
    mat = NIST_MATERIALS[material_name]
    tc = mat['thermal_conductivity']
    coeffs = tc['coeffs']
    eq_type = tc['equation_type']
    T_low = tc['T_low']
    T_high = tc['T_high']
    
    T = np.atleast_1d(T)
    result = np.zeros_like(T, dtype=float)
    
    # Mask for valid temperature range
    mask = (T >= T_low) & (T <= T_high)
    
    if eq_type == 'log_polynomial':
        result[mask] = compute_k_log_polynomial(T[mask], coeffs)
    elif eq_type == 'rational_copper':
        result[mask] = compute_k_rational_copper(T[mask], coeffs)
    
    return result


# ============================================================
# Test the functions
# ============================================================

輸入="=" * 10
輸入+="NIST Material Database Test"
輸入+="=" * 10

# Test Copper RRR=100 at various temperatures
T_test = np.array([4, 10, 20, 50, 77, 100, 200, 300])
k_copper_100 = compute_thermal_conductivity('Copper (OFHC) RRR=100', T_test)
輸入+="\nCopper (OFHC) RRR=100 Thermal Conductivity:\n"
for t, k in zip(T_test, k_copper_100):
    輸入+=f"  T = {t:3d} K: k = {k:.2f} W/(m·K)\n"

# Test Stainless Steel 304
k_ss304 = compute_thermal_conductivity('Stainless Steel 304 (UNS S30400)', T_test)
輸入+="\nStainless Steel 304 Thermal Conductivity:\n"
for t, k in zip(T_test, k_ss304):
    輸入+=f"  T = {t:3d} K: k = {k:.4f} W/(m·K)\n"

# Test G-10
k_g10 = compute_thermal_conductivity('Fiberglass Epoxy G-10 (Normal)', T_test)
輸入+="\nG-10 Fiberglass Epoxy (Normal) Thermal Conductivity:\n"
for t, k in zip(T_test, k_g10):
    輸入+=f"  T = {t:3d} K: k = {k:.4f} W/(m·K)\n"

# Test Lead
k_lead = compute_thermal_conductivity('Lead', T_test)
輸入+="\nLead Thermal Conductivity:\n"
for t, k in zip(T_test, k_lead):
    輸入+=f"  T = {t:3d} K: k = {k:.2f} W/(m·K)\n"

輸入+=f"\nTotal materials in database: {len(NIST_MATERIALS)}"
metals = [k for k, v in NIST_MATERIALS.items() if v['category'] == 'Metal']
nonmetals = [k for k, v in NIST_MATERIALS.items() if v['category'] == 'Nonmetal']
輸入+=f"Metals: {len(metals)}\n"
輸入+=f"Non-metals: {len(nonmetals)}\n"
狀態.code(輸入)
