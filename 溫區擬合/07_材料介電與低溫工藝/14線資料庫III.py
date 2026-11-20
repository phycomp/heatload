from streamlit import button, checkbox, columns, dataframe, download_button, header, info, markdown, metric, multiselect, number_input, plotly_chart, radio, set_page_config, sidebar, slider, subheader, text_input, warning
from numpy import atleast_1d, cumsum, diff, log10, logspace, pi, zeros_like
from pandas import DataFrame
from plotly.graph_objects import Figure, Scatter
from streamlit import empty, pyplot
狀態=empty()
#import streamlit as st
#import numpy as np
from scipy import integrate
#import plotly.graph_objects as go
#import pandas as pd

set_page_config(
    page_title="NIST Cryogenic Materials Database",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# Custom CSS
# ============================================================
markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1565C0;
        margin-bottom: 0.3rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #555;
        margin-bottom: 1.5rem;
    }
    .nist-badge {
        background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 1rem;
    }
    .material-card {
        background: black;
        border-radius: 12px;
        padding: 1.2rem;
        border-left: 5px solid #1565C0;
        margin: 0.5rem 0;
    }
    .result-highlight {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.2rem;
        border-radius: 12px;
        text-align: center;
    }
    .result-big {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .result-small {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .info-box {
        background: #e3f2fd;
        border-left: 4px solid #2196F3;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    .warning-box {
        background: #fff3e0;
        border-left: 4px solid #FF9800;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# NIST Cryogenic Materials Database
# ============================================================

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
    T = atleast_1d(T)
    logT = log10(T)
    logk = sum(c * logT**i for i, c in enumerate(coeffs))
    return 10**logk


def compute_k_rational_copper(T, coeffs):
    T = atleast_1d(T)
    a, b, c, d, e, f, g, h, i = coeffs
    numerator = a + c * T**0.5 + e * T + g * T**1.5 + i * T**2
    denominator = 1 + b * T**0.5 + d * T + f * T**1.5 + h * T**2
    logk = numerator / denominator
    return 10**logk


def compute_thermal_conductivity(material_name, T):
    if material_name not in NIST_MATERIALS:
        return zeros_like(atleast_1d(T))

    mat = NIST_MATERIALS[material_name]
    tc = mat['thermal_conductivity']
    coeffs = tc['coeffs']
    eq_type = tc['equation_type']
    T_low = tc['T_low']
    T_high = tc['T_high']

    T = atleast_1d(T)
    result = zeros_like(T, dtype=float)
    mask = (T >= T_low) & (T <= T_high)

    if eq_type == 'log_polynomial':
        result[mask] = compute_k_log_polynomial(T[mask], coeffs)
    elif eq_type == 'rational_copper':
        result[mask] = compute_k_rational_copper(T[mask], coeffs)

    return result


COLOR_PALETTE = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
    '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5',
]


# ============================================================
# Main App
# ============================================================


def show_material_browser(T_range):
    subheader("Material Selection & Comparison")

    col1, col2, col3 = columns([1, 1, 1])
    with col1:
        show_metals = checkbox("Metals", True)
    with col2:
        show_nonmetals = checkbox("Non-metals", True)
    with col3:
        search_term = text_input("Search", "")

    filtered = {}
    for name, data in NIST_MATERIALS.items():
        cat = data['category']
        if cat == 'Metal' and not show_metals:
            continue
        if cat == 'Nonmetal' and not show_nonmetals:
            continue
        if search_term and search_term.lower() not in name.lower():
            continue
        filtered[name] = data

    selected = multiselect(
        "Select materials to plot",
        list(filtered.keys()),
        default=['Copper (OFHC) RRR=100', 'Stainless Steel 304 (UNS S30400)', 
                 'Polyimide (Kapton)', 'Teflon (PTFE)']
    )

    if not selected:
        warning("Please select at least one material.")
        return

    col1, col2 = columns(2)
    with col1:
        plot_type = radio("Plot Type", ["Log-Log", "Linear", "Semi-Log X", "Semi-Log Y"], horizontal=True)
    with col2:
        show_integral = checkbox("Show Thermal Integral", False)

    fig = Figure()

    for i, mat_name in enumerate(selected):
        color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
        k_vals = compute_thermal_conductivity(mat_name, T_range)

        fig.add_trace(Scatter(
            x=T_range, y=k_vals,
            mode='lines',
            line=dict(color=color, width=2.5),
            name=mat_name,
            hovertemplate='<b>%{fullData.name}</b><br>T: %{x:.2f} K<br>k: %{y:.4f} W/(m·K)<extra></extra>'
        ))

        if show_integral:
            integral = cumsum(k_vals) * diff(T_range, prepend=T_range[0])
            fig.add_trace(Scatter(
                x=T_range, y=integral,
                mode='lines',
                line=dict(color=color, width=1.5, dash='dash'),
                name=mat_name + " (integral)",
                yaxis='y2',
                visible='legendonly'
            ))

    x_type = 'log' if plot_type in ['Log-Log', 'Semi-Log X'] else 'linear'
    y_type = 'log' if plot_type in ['Log-Log', 'Semi-Log Y'] else 'linear'

    fig.update_layout(
        title=dict(text="Thermal Conductivity k(T) vs Temperature", font=dict(size=18)),
        xaxis=dict(title="Temperature (K)", type=x_type, showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
        yaxis=dict(title="k(T) [W/(m·K)]", type=y_type, showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
        height=600,
        template="plotly_white",
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )

    if show_integral:
        fig.update_layout(
            yaxis2=dict(title="Integral [W·K/(m·K)]", overlaying='y', side='right', showgrid=False)
        )

    plotly_chart(fig, use_container_width=True)

    # Data table
    subheader("Data Table")
    table_data = {"Temperature (K)": T_range[::10]}
    for mat_name in selected:
        k_vals = compute_thermal_conductivity(mat_name, T_range[::10])
        table_data[mat_name] = k_vals

    df = DataFrame(table_data)
    dataframe(df.style.format("{:.4f}"), use_container_width=True)

    csv = df.to_csv(index=False)
    download_button(label="Download CSV", data=csv, file_name="nist_thermal_conductivity.csv", mime="text/csv")

    # Material info cards
    subheader("Material Details")

    cols = columns(2)
    for i, mat_name in enumerate(selected):
        with cols[i % 2]:
            mat = NIST_MATERIALS[mat_name]
            tc = mat['thermal_conductivity']

            markdown(
                '<div class="material-card">'
                '<h4>' + mat_name + '</h4>'
                '<p><b>Category:</b> ' + mat['category'] + '</p>'
                '<p><b>Equation Type:</b> ' + tc['equation_type'] + '</p>'
                '<p><b>Valid Range:</b> ' + str(tc['T_low']) + ' - ' + str(tc['T_high']) + ' K</p>'
                '<p><b>Units:</b> ' + tc['units'] + '</p>'
                '</div>',
                unsafe_allow_html=True
            )


def show_heat_load_calculator():
    subheader("Cable Heat Load Calculator")
    markdown("Compute steady-state thermal conduction through cryogenic cables")

    col1, col2 = columns(2)

    with col1:
        markdown("#### Geometry")
        cable_type = radio("Cable Type", ["Ribbon", "Coaxial"], horizontal=True)
        num_traces = number_input("Number of Traces", 1, 100, 1)
        length_m = number_input("Cable Length (m)", 0.001, 10.0, 0.3048, 0.001)

        inner_d_um = number_input("Inner Conductor Diameter (μm)", 10.0, 1000.0, 127.0, 0.1)
        dielectric_t_um = number_input("Dielectric Thickness (μm)", 10.0, 2000.0, 63.5, 0.1)

        if cable_type == "Ribbon":
            pitch_um = number_input("Trace Pitch (μm)", 100.0, 10000.0, 3556.0, 0.1)
            foil_t_um = number_input("Foil Thickness (μm)", 1.0, 200.0, 25.4, 0.1)
            foil_sheets = number_input("Foil Sheets", 1, 10, 2)
        else:
            outer_d_um = number_input("Outer Conductor Diameter (μm)", 100.0, 5000.0, 1520.0, 0.1)
            outer_t_um = number_input("Outer Conductor Thickness (μm)", 10.0, 500.0, 150.0, 0.1)

    with col2:
        markdown("#### Materials")

        inner_mat = radio("Inner Conductor", [k for k, v in NIST_MATERIALS.items() if v['category'] == 'Metal'] , horizontal=True)
        dielectric_mat = radio("Dielectric", [k for k, v in NIST_MATERIALS.items() if v['category'] == 'Nonmetal'] , horizontal=True)
        outer_mat = radio("Outer Conductor", [k for k, v in NIST_MATERIALS.items() if v['category'] == 'Metal'] , horizontal=True)

        markdown("#### Temperature")
        T_cold = number_input("Cold End (K)", 0.05, 100.0, 1.0, 0.01)
        T_hot = number_input("Hot End (K)", 0.1, 300.0, 4.0, 0.1)

    #狀態.code([Q_inner, Q_outer, Q_diel])
    #if button("Calculate Heat Load", type="primary"):
    d_inner = inner_d_um * 1e-6
    t_dielectric = dielectric_t_um * 1e-6

    A_inner = pi * (d_inner / 2)**2
    d_outer_dielectric = d_inner + 2 * t_dielectric
    A_dielectric = pi * ((d_outer_dielectric / 2)**2 - (d_inner / 2)**2)

    if cable_type == "Ribbon":
        A_outer = (pitch_um * 1e-6) * (foil_t_um * 1e-6) * foil_sheets
    else:
        r_outer_inner = d_outer_dielectric / 2
        r_outer_outer = r_outer_inner + (outer_t_um * 1e-6)
        A_outer = pi * (r_outer_outer**2 - r_outer_inner**2)

    def thermal_integral(mat_name, T1, T2):
        result, _ = integrate.quad(
            lambda T: compute_thermal_conductivity(mat_name, T)[0],
            T1, T2, limit=100
        )
        return result

    Q_inner = (A_inner / length_m) * thermal_integral(inner_mat, T_cold, T_hot)
    Q_diel = (A_dielectric / length_m) * thermal_integral(dielectric_mat, T_cold, T_hot)
    Q_outer = (A_outer / length_m) * thermal_integral(outer_mat, T_cold, T_hot)

    Q_total = Q_inner + Q_diel + Q_outer
    狀態.code([Q_inner, Q_diel, Q_outer])
    Q_per_trace = Q_total / num_traces

    col1, col2, col3 = columns(3)
    with col1:
        markdown(
            '<div class="result-highlight">'
            '<div class="result-big">' + '{:.2f}'.format(Q_per_trace*1e9) + '</div>'
            '<div class="result-small">nW / trace</div>'
            '</div>',
            unsafe_allow_html=True
        )
    with col2:
        markdown(
            '<div class="result-highlight" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">'
            '<div class="result-big">' + '{:.2f}'.format(Q_total*1e9) + '</div>'
            '<div class="result-small">nW Total</div>'
            '</div>',
            unsafe_allow_html=True
        )
    with col3:
        markdown(
            '<div class="result-highlight" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">'
            '<div class="result-big">' + '{:.1f}'.format(Q_per_trace*1e12) + '</div>'
            '<div class="result-small">pW / trace</div>'
            '</div>',
            unsafe_allow_html=True
        )

    subheader("Component Breakdown")
    components = [
        ("Inner Conductor", Q_inner, A_inner),
        ("Dielectric", Q_diel, A_dielectric),
        ("Outer Conductor", Q_outer, A_outer)
    ]

    cols = columns(3)
    for i, (name, Q, A) in enumerate(components):
        with cols[i]:
            frac = Q / Q_total * 100 if Q_total > 0 else 0
            markdown(
                '<div class="material-card">'
                '<h4>' + name + '</h4>'
                '<p><b>' + '{:.3f}'.format(Q*1e9) + ' nW</b></p>'
                '<p>Area: ' + '{:.4f}'.format(A*1e6) + ' mm2</p>'
                '<p>Fraction: ' + '{:.1f}'.format(frac) + '%</p>'
                '</div>',
                unsafe_allow_html=True
            )


def show_database_info():
    subheader("Database Information")

    markdown(
        '<div class="info-box">'
        '<h4>NIST Cryogenic Materials Database</h4>'
        '<p>This database contains curve-fitted property data for materials commonly used in cryogenic systems, '
        'compiled by the NIST Thermophysical Properties of Hydrocarbons Group.</p>'
        '<p><b>Original Source:</b> <a href="https://trc.nigov/cryogenics/materials/materialproperties.htm" target="_blank">'
        'https://trc.nigov/cryogenics/materials/materialproperties.htm</a></p>'
        '</div>',
        unsafe_allow_html=True
    )

    markdown("#### Statistics")

    metals = [k for k, v in NIST_MATERIALS.items() if v['category'] == 'Metal']
    nonmetals = [k for k, v in NIST_MATERIALS.items() if v['category'] == 'Nonmetal']

    col1, col2, col3 = columns(3)
    with col1:
        metric("Total Materials", len(NIST_MATERIALS))
    with col2:
        metric("Metals", len(metals))
    with col3:
        metric("Non-metals", len(nonmetals))

    markdown("#### Equation Types")
    markdown(
        '**1. Log-Polynomial Fit (Standard)**<br>'
        'For most materials:<br>'
        'log10(k) = a + b*log10(T) + c*(log10 T)^2 + ... + i*(log10 T)^8<br><br>'
        '**2. Rational Polynomial (Copper only)**<br>'
        'For OFHC Copper with RRR dependence:<br>'
        'log10(k) = (a + c*T^0.5 + e*T + g*T^1.5 + i*T^2) / (1 + b*T^0.5 + d*T + f*T^1.5 + h*T^2)',
        unsafe_allow_html=True
    )

    markdown("#### References")
    markdown(
        '- Marquardt, E.D., Le, J.P., & Radebaugh, R. (2000). "Cryogenic Material Properties Database." '
        '11th International Cryocooler Conference, Keystone, CO.<br>'
        '- Bradley, P.E. et al. (2006). "Cryogenic Material Properties Database, Update 2006." '
        'ICEC 21, Prague.<br>'
        '- Simon, N.J., Drexler, E.S., & Reed, R.P. (1992). "Properties of Copper and Copper Alloys '
        'at Cryogenic Temperatures." NIST Monograph 177.',
        unsafe_allow_html=True
    )

    markdown("#### Complete Material List")

    data = []
    for name, info in NIST_MATERIALS.items():
        tc = info['thermal_conductivity']
        data.append({
            "Material": name,
            "Category": info['category'],
            "Equation": tc['equation_type'],
            "T_min (K)": tc['T_low'],
            "T_max (K)": tc['T_high'],
            "Units": tc['units']
        })

    df = DataFrame(data)
    dataframe(df, use_container_width=True)

with sidebar:
    T_min = number_input("Min Temperature (K)", 0.1, 100.0, 1.0, 0.1)
    T_max = number_input("Max Temperature (K)", 1.0, 300.0, 300.0, 1.0)
    n_points = slider("Plot Points", 50, 1000, 200)
    page = radio( "Select Page", ["Material Browser", "Heat Load Calculator", "Database Info"], horizontal=True)

    #markdown("---")

    T_range = logspace(log10(max(T_min, 0.1)), log10(T_max), n_points)

if page == "Material Browser": show_material_browser(T_range)
elif page == "Heat Load Calculator": show_heat_load_calculator()
else: show_database_info()


with sidebar:
    markdown('<div class="main-header">NIST Cryogenic Materials Database</div>', unsafe_allow_html=True)
    markdown('<div class="sub-header">Thermal Conductivity Browser & Heat Load Calculator</div>', unsafe_allow_html=True)
    markdown('<div class="nist-badge">Data Source: NIST TRC Cryogenics Division</div>', unsafe_allow_html=True)

    subheader("Navigation")

    #markdown("---")
    header("Global Settings")
    info("""
    NIST Fits:
    - Metals: 8th-order log-log polynomial
    - Copper: Special rational polynomial (RRR-dependent)
    - Non-metals: 8th-order log-log polynomial
    - Valid range: 4-300 K (material dependent)
    """)
    """
NIST Cryogenic Materials Database Browser
Streamlit app for visualizing thermal conductivity data from
https://trc.nigov/cryogenics/materials/materialproperties.htm

Features:
- 48 materials with NIST polynomial fits
- Interactive temperature range selection
- Log-log and linear plots
- Material comparison
- Data export
- Heat load calculator integration
"""

#if __name__ == "__main__": main()
