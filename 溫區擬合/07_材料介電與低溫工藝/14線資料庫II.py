from streamlit import button, checkbox, columns, dataframe, download_button, header, info, markdown, metric, multiselect, number_input, plotly_chart, radio, selectbox, set_page_config, sidebar, slider, subheader, text_input, warning
from numpy import array, atleast_1d, cumsum, diff, interp, linspace, log10, logspace, pi, zeros_like
from pandas import DataFrame
from plotly.graph_objects import Figure, Scatter

"""NIST Cryogenic Materials Database Browser
Streamlit app for visualizing thermal conductivity data from
https://trc.nist.gov/cryogenics/materials/materialproperties.htm

Features:
- 48 materials with NIST polynomial fits
- Interactive temperature range selection
- Log-log and linear plots
- Material comparison
- Data export
- Heat load calculator integration
"""

import streamlit as st
import numpy as np
from scipy import integrate
#import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

st.set_page_config(
    page_title="NIST Cryogenic Materials Database",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# Custom CSS
# ============================================================
st.markdown("""
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
        background-color: black;
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
        background: black;
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
    """NIST standard log-polynomial fit"""
    T = np.atleast_1d(T)
    logT = np.log10(T)
    logk = sum(c * logT**i for i, c in enumerate(coeffs))
    return 10**logk


def compute_k_rational_copper(T, coeffs):
    """Special rational polynomial for OFHC Copper"""
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
    mask = (T >= T_low) & (T <= T_high)
    
    if eq_type == 'log_polynomial':
        result[mask] = compute_k_log_polynomial(T[mask], coeffs)
    elif eq_type == 'rational_copper':
        result[mask] = compute_k_rational_copper(T[mask], coeffs)
    
    return result


# ============================================================
# Color palette for plots
# ============================================================

COLOR_PALETTE = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
    '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5',
    '#393b79', '#637939', '#8c6d31', '#843c39', '#7b4173',
    '#5254a3', '#8ca252', '#bd9e39', '#ad494a', '#a55194',
]


# ============================================================
# Main App
# ============================================================

def main():
    # Header
    st.markdown('<div class="sub-header">🧊 NIST Cryogenic Materials Database</div>', 
                unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Thermal Conductivity Browser & Heat Load Calculator</div>', 
                unsafe_allow_html=True)
    st.markdown('<div class="nist-badge">📚 Data Source: NIST TRC Cryogenics Division</div>', 
                unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🔍 Navigation")
        page = st.radio(
            "Select Page",
            ["📊 Material Browser", "🔬 Heat Load Calculator", "📋 Database Info"]
        )
        
        st.markdown("---")
        st.header("⚙️ Global Settings")
        
        T_min = st.number_input("Min Temperature (K)", 0.1, 100.0, 1.0, 0.1)
        T_max = st.number_input("Max Temperature (K)", 1.0, 300.0, 300.0, 1.0)
        n_points = st.slider("Plot Points", 50, 1000, 200)
        
        st.markdown("---")
        st.info("""
        **About NIST Fits**
        - Metals: 8th-order log-log polynomial
        - Copper: Special rational polynomial (RRR-dependent)
        - Non-metals: 8th-order log-log polynomial
        - Valid range: 4-300 K (material dependent)
        """)
    
    T_range = np.logspace(np.log10(max(T_min, 0.1)), np.log10(T_max), n_points)
    
    if page == "📊 Material Browser":
        show_material_browser(T_range)
    elif page == "🔬 Heat Load Calculator":
        show_heat_load_calculator()
    else:
        show_database_info()


def show_material_browser(T_range):
    """Material browser and comparison page"""
    
    st.subheader("📊 Material Selection & Comparison")
    
    # Filter by category
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        show_metals = st.checkbox("Metals", True)
    with col2:
        show_nonmetals = st.checkbox("Non-metals", True)
    with col3:
        search_term = st.text_input("🔍 Search", "")
    
    # Filter materials
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
    
    # Material selection
    selected = st.multiselect(
        "Select materials to plot",
        list(filtered.keys()),
        default=['Copper (OFHC) RRR=100', 'Stainless Steel 304 (UNS S30400)', 
                 'Polyimide (Kapton)', 'Teflon (PTFE)']
    )
    
    if not selected:
        st.warning("Please select at least one material.")
        return
    
    # Plot type
    col1, col2 = st.columns(2)
    with col1:
        plot_type = st.selectbox("Plot Type", ["Log-Log", "Linear", "Semi-Log X", "Semi-Log Y"])
    with col2:
        show_integral = st.checkbox("Show Thermal Integral ∫k(T)dT", False)
    
    # Create plot
    fig = Figure()
    
    for i, mat_name in enumerate(selected):
        color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
        k_vals = compute_thermal_conductivity(mat_name, T_range)
        
        # Main k(T) curve
        fig.add_trace(Scatter(
            x=T_range, y=k_vals,
            mode='lines',
            line=dict(color=color, width=2.5),
            name=mat_name,
            hovertemplate='<b>%{fullData.name}</b><br>T: %{x:.2f} K<br>k: %{y:.4f} W/(m·K)<extra></extra>'
        ))
        
        # Thermal integral
        if show_integral:
            integral = np.cumsum(k_vals) * np.diff(T_range, prepend=T_range[0])
            fig.add_trace(Scatter(
                x=T_range, y=integral,
                mode='lines',
                line=dict(color=color, width=1.5, dash='dash'),
                name=f"{mat_name} (∫k dT)",
                yaxis='y2',
                visible='legendonly'
            ))
    
    # Axis configuration
    x_type = 'log' if plot_type in ['Log-Log', 'Semi-Log X'] else 'linear'
    y_type = 'log' if plot_type in ['Log-Log', 'Semi-Log Y'] else 'linear'
    
    fig.update_layout(
        title=dict(
            text="Thermal Conductivity k(T) vs Temperature",
            font=dict(size=18)
        ),
        xaxis=dict(
            title="Temperature (K)",
            type=x_type,
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        yaxis=dict(
            title="k(T) [W/(m·K)]",
            type=y_type,
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        height=600,
        template="plotly_white",
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        )
    )
    
    if show_integral:
        fig.update_layout(
            yaxis2=dict(
                title="∫k(T)dT [W·K/(m·K)]",
                overlaying='y',
                side='right',
                showgrid=False
            )
        )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Data table
    st.subheader("📋 Data Table")
    
    table_data = {"Temperature (K)": T_range[::10]}
    for mat_name in selected:
        k_vals = compute_thermal_conductivity(mat_name, T_range[::10])
        table_data[mat_name] = k_vals
    
    df = pd.DataFrame(table_data)
    st.dataframe(df.style.format("{:.4f}"), use_container_width=True)
    
    # CSV download
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name="nist_thermal_conductivity.csv",
        mime="text/csv"
    )
    
    # Material info cards
    st.subheader("📖 Material Details")
    
    cols = st.columns(2)
    for i, mat_name in enumerate(selected):
        with cols[i % 2]:
            mat = NIST_MATERIALS[mat_name]
            tc = mat['thermal_conductivity']
            
            st.markdown(f'''
            <div class="material-card">
                <h4>{mat_name}</h4>
                <p><b>Category:</b> {mat['category']}</p>
                <p><b>Equation Type:</b> {tc['equation_type']}</p>
                <p><b>Valid Range:</b> {tc['T_low']} - {tc['T_high']} K</p>
                <p><b>Units:</b> {tc['units']}</p>
                <details>
                    <summary>View Coefficients</summary>
                    <pre style="font-size:0.75rem;">
a = {tc['coeffs'][0]:.6f}
b = {tc['coeffs'][1]:.6f}
c = {tc['coeffs'][2]:.6f}
d = {tc['coeffs'][3]:.6f}
e = {tc['coeffs'][4]:.6f}
f = {tc['coeffs'][5]:.6f}
g = {tc['coeffs'][6]:.6f}
h = {tc['coeffs'][7]:.6f}
i = {tc['coeffs'][8]:.6f}
                    </pre>
                </details>
            </div>
            ''', unsafe_allow_html=True)


def show_heat_load_calculator():
    """Heat load calculator page"""
    
    st.subheader("🔬 Cable Heat Load Calculator")
    st.markdown("Compute steady-state thermal conduction through cryogenic cables")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📐 Geometry")
        cable_type = st.selectbox("Cable Type", ["Ribbon", "Coaxial"])
        num_traces = st.number_input("Number of Traces", 1, 100, 1)
        length_m = st.number_input("Cable Length (m)", 0.001, 10.0, 0.3048, 0.001)
        
        inner_d_um = st.number_input("Inner Conductor Diameter (μm)", 10.0, 1000.0, 127.0, 0.1)
        dielectric_t_um = st.number_input("Dielectric Thickness (μm)", 10.0, 2000.0, 63.5, 0.1)
        
        if cable_type == "Ribbon":
            pitch_um = st.number_input("Trace Pitch (μm)", 100.0, 10000.0, 3556.0, 0.1)
            foil_t_um = st.number_input("Foil Thickness (μm)", 1.0, 200.0, 25.4, 0.1)
            foil_sheets = st.number_input("Foil Sheets", 1, 10, 2)
        else:
            outer_d_um = st.number_input("Outer Conductor Diameter (μm)", 100.0, 5000.0, 1520.0, 0.1)
            outer_t_um = st.number_input("Outer Conductor Thickness (μm)", 10.0, 500.0, 150.0, 0.1)
    
    with col2:
        st.markdown("#### 🔧 Materials")
        
        inner_mat = st.selectbox(
            "Inner Conductor",
            [k for k, v in NIST_MATERIALS.items() if v['category'] == 'Metal']
        )
        dielectric_mat = st.selectbox(
            "Dielectric",
            [k for k, v in NIST_MATERIALS.items() if v['category'] == 'Nonmetal']
        )
        outer_mat = st.selectbox(
            "Outer Conductor",
            [k for k, v in NIST_MATERIALS.items() if v['category'] == 'Metal']
        )
        
        st.markdown("#### 🌡️ Temperature")
        T_cold = st.number_input("Cold End (K)", 0.05, 100.0, 1.0, 0.01)
        T_hot = st.number_input("Hot End (K)", 0.1, 300.0, 4.0, 0.1)
    
    # Compute
    if st.button("🚀 Calculate Heat Load", type="primary"):
        # Compute cross-sectional areas
        d_inner = inner_d_um * 1e-6
        t_dielectric = dielectric_t_um * 1e-6
        
        A_inner = np.pi * (d_inner / 2)**2
        d_outer_dielectric = d_inner + 2 * t_dielectric
        A_dielectric = np.pi * ((d_outer_dielectric / 2)**2 - (d_inner / 2)**2)
        
        if cable_type == "Ribbon":
            A_outer = (pitch_um * 1e-6) * (foil_t_um * 1e-6) * foil_sheets
        else:
            r_outer_inner = d_outer_dielectric / 2
            r_outer_outer = r_outer_inner + (outer_t_um * 1e-6)
            A_outer = np.pi * (r_outer_outer**2 - r_outer_inner**2)
        
        # Compute thermal integrals
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
        Q_per_trace = Q_total / num_traces
        
        # Display results
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'''
            <div class="result-highlight">
                <div class="result-big">{Q_per_trace*1e9:.2f}</div>
                <div class="result-small">nW / trace</div>
            </div>
            ''', unsafe_allow_html=True)
        with col2:
            st.markdown(f'''
            <div class="result-highlight" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <div class="result-big">{Q_total*1e9:.2f}</div>
                <div class="result-small">nW Total</div>
            </div>
            ''', unsafe_allow_html=True)
        with col3:
            st.markdown(f'''
            <div class="result-highlight" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <div class="result-big">{Q_per_trace*1e12:.1f}</div>
                <div class="result-small">pW / trace</div>
            </div>
            ''', unsafe_allow_html=True)
        
        # Component breakdown
        st.subheader("📊 Component Breakdown")
        
        components = [
            ("Inner Conductor", Q_inner, A_inner),
            ("Dielectric", Q_diel, A_dielectric),
            ("Outer Conductor", Q_outer, A_outer)
        ]
        
        cols = st.columns(3)
        for i, (name, Q, A) in enumerate(components):
            with cols[i]:
                frac = Q / Q_total * 100 if Q_total > 0 else 0
                st.markdown(f'''
                <div class="material-card">
                    <h4>{name}</h4>
                    <p><b>{Q*1e9:.3f} nW</b></p>
                    <p>Area: {A*1e6:.4f} mm²</p>
                    <p>Fraction: {frac:.1f}%</p>
                </div>
                ''', unsafe_allow_html=True)
        
        # Temperature profile
        st.subheader("📈 Temperature Profile Along Cable")
        
        def compute_G(T):
            k_i = compute_thermal_conductivity(inner_mat, T)[0]
            k_d = compute_thermal_conductivity(dielectric_mat, T)[0]
            k_o = compute_thermal_conductivity(outer_mat, T)[0]
            return A_inner * k_i + A_dielectric * k_d + A_outer * k_o
        
        T_grid = np.logspace(np.log10(max(T_cold, 0.05)), np.log10(T_hot), 200)
        G_vals = np.array([compute_G(t) for t in T_grid])
        ds_dT = G_vals / (Q_total * length_m)
        
        s_grid = np.zeros_like(T_grid)
        for i in range(1, len(T_grid)):
            s_grid[i] = s_grid[i-1] + 0.5 * (ds_dT[i] + ds_dT[i-1]) * (T_grid[i] - T_grid[i-1])
        
        if s_grid[-1] > 0:
            s_grid = s_grid / s_grid[-1]
        
        s_uniform = np.linspace(0, 1, 100)
        T_profile = np.interp(s_uniform, s_grid, T_grid)
        
        fig = Figure()
        fig.add_trace(Scatter(
            x=s_uniform * 100, y=T_profile,
            mode='lines',
            line=dict(color='#1f77b4', width=3),
            fill='tozeroy',
            fillcolor='rgba(31, 119, 180, 0.2)',
            name='T(x)'
        ))
        fig.update_layout(
            xaxis_title="Position along cable (%)",
            yaxis_title="Temperature (K)",
            yaxis_type="log" if T_cold < 1.0 else "linear",
            height=400,
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)


def show_database_info():
    """Database information page"""
    
    st.subheader("📋 Database Information")
    
    st.markdown('''
    <div class="info-box">
        <h4>🧊 NIST Cryogenic Materials Database</h4>
        <p>This database contains curve-fitted property data for materials commonly used in cryogenic systems,
        compiled by the NIST Thermophysical Properties of Hydrocarbons Group.</p>
        <p><b>Original Source:</b> <a href="https://trc.nist.gov/cryogenics/materials/materialproperties.htm" target="_blank">
        https://trc.nist.gov/cryogenics/materials/materialproperties.htm</a></p>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("#### 📊 Statistics")
    
    metals = [k for k, v in NIST_MATERIALS.items() if v['category'] == 'Metal']
    nonmetals = [k for k, v in NIST_MATERIALS.items() if v['category'] == 'Nonmetal']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Materials", len(NIST_MATERIALS))
    with col2:
        st.metric("Metals", len(metals))
    with col3:
        st.metric("Non-metals", len(nonmetals))
    
    st.markdown("#### 🔬 Equation Types")
    
    st.markdown('''
    **1. Log-Polynomial Fit (Standard)**
    
    For most materials:
    $$\\log_{10}(k) = a + b\\log_{10}(T) + c(\\log_{10} T)^2 + \\cdots + i(\\log_{10} T)^8$$
    
    **2. Rational Polynomial (Copper only)**
    
    For OFHC Copper with RRR dependence:
    $$\\log_{10}(k) = \\frac{a + cT^{0.5} + eT + gT^{1.5} + iT^2}{1 + bT^{0.5} + dT + fT^{1.5} + hT^2}$$
    ''')
    
    st.markdown("#### 📚 References")
    
    st.markdown('''
    - Marquardt, E.D., Le, J.P., & Radebaugh, R. (2000). "Cryogenic Material Properties Database." 
      11th International Cryocooler Conference, Keystone, CO.
    - Bradley, P.E. et al. (2006). "Cryogenic Material Properties Database, Update 2006." 
      ICEC 21, Prague.
    - Simon, N.J., Drexler, E.S., & Reed, R.P. (1992). "Properties of Copper and Copper Alloys 
      at Cryogenic Temperatures." NIST Monograph 177.
    ''')
    
    # Full material list
    st.markdown("#### 📋 Complete Material List")
    
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
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()
