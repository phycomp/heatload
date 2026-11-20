from streamlit import columns, header, markdown, number_input, pyplot, radio, set_page_config, sidebar, warning
from matplotlib.pyplot import subplots, tight_layout
from numpy import isnan, log, nan, pi, sqrt
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# ============================================================
# Delft CRI/oFlex3 CF3 – Stripline Impedance Calculator
# Inspired by Mantaro Impedance Calculators
# ============================================================

st.set_page_config(page_title="CRI/oFlex3 CF3 Impedance Calculator", layout="wide")

## ---- Custom CSS for Mantaro-like look ----
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.3rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #555;
        margin-bottom: 1.5rem;
    }
    .result-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.2rem;
        border-radius: 12px;
        text-align: center;
        margin: 0.5rem 0;
    }
    .result-value {
        font-size: 2.4rem;
        font-weight: 800;
        color: #fff;
    }
    .result-label {
        font-size: 0.9rem;
        color: rgba(255,255,255,0.85);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .param-card {
        background: black;
        border-radius: 10px;
        padding: 1rem;
        border-left: 4px solid #667eea;
        margin-bottom: 0.8rem;
    }
    .note-text {
        font-size: 0.8rem;
        color: #888;
        margin-top: 0.5rem;
    }
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: white;
        margin: 1.2rem 0 0.6rem 0;
        border-bottom: 2px solid #e0e0e0;
        padding-bottom: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

## ---- Sidebar: Input Parameters ----
with st.sidebar:
    st.header("📐 Input Parameters")
    
    unit = st.radio("Dimensional Units", ["mm", "mils"], index=0, horizontal=True)
    
    if unit == "mm":
        w_default, h_default, t_default = 0.19, 0.30, 0.01
        w_step, h_step, t_step = 0.001, 0.001, 0.001
        w_min, h_min, t_min = 0.01, 0.05, 0.001
        w_max, h_max, t_max = 2.0, 2.0, 0.1
    else:
        w_default, h_default, t_default = 7.5, 11.8, 0.4
        w_step, h_step, t_step = 0.05, 0.05, 0.01
        w_min, h_min, t_min = 0.4, 2.0, 0.04
        w_max, h_max, t_max = 80., 80., 4.
    
    w = st.number_input("w (trace width)", min_value=w_min, max_value=w_max, value=w_default, step=w_step, format="%.4f" if unit=="mm" else "%.2f")
    t = st.number_input("t (trace thickness)", min_value=t_min, max_value=t_max, value=t_default, step=t_step, format="%.4f" if unit=="mm" else "%.2f")
    h = st.number_input("h (total dielectric thickness)", min_value=h_min, max_value=h_max,
                        value=h_default, step=h_step, format="%.4f" if unit=="mm" else "%.2f")
    
#    st.markdown("---")
    er = st.number_input("εᵣ (relative dielectric constant)", min_value=1.0, max_value=20.0,
                         value=3.4, step=0.1, format="%.2f")
    
#    st.markdown("---")
    st.markdown("**CF3 Defaults**")
    st.markdown("- Total thickness: 0.30 mm")
    st.markdown("- Material: Polyimide (εᵣ≈3.4)")
    st.markdown("- Conductor: Silver (Ag)")
    st.markdown("- Type: Symmetric Stripline")
    st.markdown("- Impedance target: 50 Ω")
    
#    st.markdown("---")
    st.markdown('<div class="note-text">Note: 1 oz Cu ≈ 1.4 mils ≈ 0.03556 mm</div>', unsafe_allow_html=True)

## ---- Convert to mm for calculation ----
if unit == "mils":
    w_mm = w * 0.0254
    t_mm = t * 0.0254
    h_mm = h * 0.0254
else:
    w_mm, t_mm, h_mm = w, t, h

## ---- Impedance Calculation (Symmetric Stripline) ----
# Based on IPC-2141 / Wadell approximations for symmetric stripline
# Z0 = (30*pi/sqrt(er)) / (weff/h + Cf)
# where Cf = (2/pi)*ln(2) for zero thickness, modified for thickness

def calc_stripline_z0(w, t, h, er):
    """
    Symmetric stripline impedance approximation.
    Valid for w/h from 0.1 to 2.0 and t/h < 0.25.
    """
    if h <= 0 or w <= 0 or t < 0 or er <= 0:
        return np.nan
    
    # Effective width correction for finite thickness (from IPC-2141)
    if w / h > 1 / (2 * np.pi):
        delta_w = (t / np.pi) * (1 + np.log(4 * np.pi * w / t))
    else:
        delta_w = (t / np.pi) * (1 + np.log(2 * h / t))
    
    w_eff = w + delta_w
    
    # Fringing factor for symmetric stripline
    Cf = (2 / np.pi) * np.log(2)
    
    # Main impedance formula
    z0 = (30 * np.pi / np.sqrt(er)) / (w_eff / h + Cf)
    
    return z0

z0 = calc_stripline_z0(w_mm, t_mm, h_mm, er)

## ---- Propagation delay ----
tpd_ns_per_m = 3.333 * np.sqrt(er)  # ns/m
tpd_ps_per_mm = tpd_ns_per_m / 1e6  # ps/mm

## ---- Capacitance per unit length ----
if z0 > 0 and not np.isnan(z0):
    c_pf_per_mm = tpd_ps_per_mm / z0  # pF/mm (approx)
else:
    c_pf_per_mm = np.nan

## ---- Main Layout ----
col_left, col_right = st.columns([1, 1.6])

with col_left:
    st.markdown('<div class="section-header">📊 Calculation Results</div>', unsafe_allow_html=True)
    
    z0_display = f"{z0:.2f}" if not np.isnan(z0) else "—"
    
    st.markdown(f'''
    <div class="result-box">
        <div class="result-label">Characteristic Impedance Z₀</div>
        <div class="result-value">{z0_display} Ω</div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("**Propagation Delay**")
    st.markdown(f"- **Tpd** = {tpd_ps_per_mm:.3f} ps/mm = {tpd_ns_per_m:.3f} ns/m")
    
    st.markdown("**Capacitance**")
    st.markdown(f"- **C** ≈ {c_pf_per_mm:.4f} pF/mm")
    
#    #st.markdown("---")
    st.markdown('<div class="section-header">📋 Parameters Summary</div>', unsafe_allow_html=True)
    
    def param_row(label, val, unit_str):
        return f'<div class="param-card"><b>{label}</b><br><span style="font-size:1.1rem">{val} {unit_str}</span></div>'
    
    st.markdown(param_row("Trace Width (w)", f"{w:.4f}" if unit=="mm" else f"{w:.2f}", unit), unsafe_allow_html=True)
    st.markdown(param_row("Trace Thickness (t)", f"{t:.4f}" if unit=="mm" else f"{t:.2f}", unit), unsafe_allow_html=True)
    st.markdown(param_row("Dielectric Thickness (h)", f"{h:.4f}" if unit=="mm" else f"{h:.2f}", unit), unsafe_allow_html=True)
    st.markdown(param_row("Dielectric Constant (εᵣ)", f"{er:.2f}", ""), unsafe_allow_html=True)
    
    # Validity check
    wh_ratio = w_mm / h_mm if h_mm > 0 else 0
    th_ratio = t_mm / h_mm if h_mm > 0 else 0
    
#    #st.markdown("---")
    st.markdown('<div class="section-header">✅ Validity Check</div>', unsafe_allow_html=True)
    
    valid = True
    checks = []
    if not (0.1 <= wh_ratio <= 2.0):
        checks.append(f"⚠️ w/h = {wh_ratio:.3f} (valid: 0.1 – 2.0)")
        valid = False
    else:
        checks.append(f"✅ w/h = {wh_ratio:.3f}")
    
    if th_ratio >= 0.25:
        checks.append(f"⚠️ t/h = {th_ratio:.3f} (valid: < 0.25)")
        valid = False
    else:
        checks.append(f"✅ t/h = {th_ratio:.3f}")
    
    for c in checks:
        st.markdown(c)
    
    if not valid:
        st.warning("Results may be less accurate outside recommended ranges.")

## ---- Cross-Section Side View Drawing ----
with col_right:
    st.markdown('<div class="section-header">🔍 Cross-Section Side View</div>', unsafe_allow_html=True)
    
    fig, ax = plt.subplots(figsize=(10, 6), dpi=120)
    
    # Scaling for visualization (normalize so h fits nicely)
    scale = 1.0
    if h_mm > 0:
        scale = 3.0 / h_mm  # normalize to ~3 units tall
    
    h_vis = h_mm * scale
    w_vis = w_mm * scale
    t_vis = max(t_mm * scale, 0.08)  # minimum visual thickness
    
    # Center everything
    center_x = 5
    center_y = 3
    
    # Ground planes (top and bottom)
    gp_thickness = 0.15
    
    # Dielectric layers (polyimide - hatched)
    # Top dielectric
    top_dielectric = patches.Rectangle(
        (center_x - 3, center_y + t_vis/2),
        6, h_vis/2 - t_vis/2,
        linewidth=1.5, edgecolor='#333', facecolor='#e8d5b7',
        hatch='///', alpha=0.9
    )
    ax.add_patch(top_dielectric)
    
    # Bottom dielectric
    bottom_dielectric = patches.Rectangle(
        (center_x - 3, center_y - h_vis/2),
        6, h_vis/2 - t_vis/2,
        linewidth=1.5, edgecolor='#333', facecolor='#e8d5b7',
        hatch='///', alpha=0.9
    )
    ax.add_patch(bottom_dielectric)
    
    # Trace (silver conductor)
    trace = patches.Rectangle(
        (center_x - w_vis/2, center_y - t_vis/2),
        w_vis, t_vis,
        linewidth=2, edgecolor='#1a1a2e', facecolor='#c0c0c0',
        alpha=0.95, zorder=5
    )
    ax.add_patch(trace)
    
    # Top ground plane
    top_gp = patches.Rectangle(
        (center_x - 3, center_y + h_vis/2),
        6, gp_thickness,
        linewidth=1.5, edgecolor='#333', facecolor='#444',
        alpha=0.95, zorder=6
    )
    ax.add_patch(top_gp)
    
    # Bottom ground plane
    bottom_gp = patches.Rectangle(
        (center_x - 3, center_y - h_vis/2 - gp_thickness),
        6, gp_thickness,
        linewidth=1.5, edgecolor='#333', facecolor='#444',
        alpha=0.95, zorder=6
    )
    ax.add_patch(bottom_gp)
    
#    # ---- Dimension annotations ----
    arrow_style = dict(arrowstyle='<->', color='#d32f2f', lw=1.5)
    text_style = dict(fontsize=11, color='#d32f2f', fontweight='bold',
                      bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#d32f2f', alpha=0.9))
    
    # w annotation (above trace)
    ax.annotate('', xy=(center_x - w_vis/2, center_y + h_vis/2 + gp_thickness + 0.3),
                xytext=(center_x + w_vis/2, center_y + h_vis/2 + gp_thickness + 0.3),
                arrowprops=arrow_style)
    ax.text(center_x, center_y + h_vis/2 + gp_thickness + 0.55,
            f'w = {w:.4f} {unit}' if unit=="mm" else f'w = {w:.2f} {unit}',
            ha='center', va='bottom', **text_style)
    
    # h annotation (right side)
    ax.annotate('', xy=(center_x + 3.2, center_y - h_vis/2 - gp_thickness),
                xytext=(center_x + 3.2, center_y + h_vis/2 + gp_thickness),
                arrowprops=arrow_style)
    ax.text(center_x + 3.5, center_y,
            f'h = {h:.4f} {unit}' if unit=="mm" else f'h = {h:.2f} {unit}',
            ha='left', va='center', rotation=90, **text_style)
    
    # t annotation (left side of trace)
    ax.annotate('', xy=(center_x - w_vis/2 - 0.4, center_y - t_vis/2),
                xytext=(center_x - w_vis/2 - 0.4, center_y + t_vis/2),
                arrowprops=arrow_style)
    ax.text(center_x - w_vis/2 - 0.7, center_y,
            f't = {t:.4f} {unit}' if unit=="mm" else f't = {t:.2f} {unit}',
            ha='right', va='center', rotation=90, **text_style)
    
    # Labels for materials
    ax.text(center_x, center_y + h_vis/4 + t_vis/4, 'Polyimide\n(εᵣ = {:.2f})'.format(er),
            ha='center', va='center', fontsize=10, color='#666', style='italic')
    ax.text(center_x, center_y - h_vis/4 - t_vis/4, 'Polyimide\n(εᵣ = {:.2f})'.format(er),
            ha='center', va='center', fontsize=10, color='#666', style='italic')
    ax.text(center_x, center_y, 'Ag Trace', ha='center', va='center',
            fontsize=9, color='#1a1a2e', fontweight='bold', zorder=7)
    ax.text(center_x, center_y + h_vis/2 + gp_thickness/2, 'GND', ha='center', va='center',
            fontsize=9, color='white', fontweight='bold', zorder=7)
    ax.text(center_x, center_y - h_vis/2 - gp_thickness/2, 'GND', ha='center', va='center',
            fontsize=9, color='white', fontweight='bold', zorder=7)
    
    # Center line (dashed)
    ax.axhline(y=center_y, xmin=0.05, xmax=0.95, color='#999', linestyle='--', linewidth=0.8, alpha=0.5)
    
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.5)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Title
    ax.set_title(f'Symmetric Stripline Cross-Section  |  Z₀ ≈ {z0:.2f} Ω',
                 fontsize=13, fontweight='bold', color='#1a1a2e', pad=15)
    
    plt.tight_layout()
    st.pyplot(fig)
    
    st.markdown('<div class="note-text" style="text-align:center">Cross-section diagram auto-scales for visibility. Dimensions shown are actual values.</div>', unsafe_allow_html=True)

## ---- Formula Reference ----
##st.markdown("---")
st.markdown('<div class="section-header">📐 Formula Reference</div>', unsafe_allow_html=True)

st.markdown("""
**Symmetric Stripline Impedance** (approximation, IPC-2141 / Wadell):

$$
Z_0 = \\frac{30\\pi}{\\sqrt{\\varepsilon_r}} \\cdot \\frac{1}{\\frac{w_{eff}}{h} + C_f}
$$

where:
- $w_{eff} = w + \\Delta w$  (effective trace width with thickness correction)
- $C_f = \\frac{2}{\\pi} \\ln(2) \\approx 0.441$  (fringing capacitance factor)
- $\\Delta w = \\frac{t}{\\pi} \\left(1 + \\ln\\frac{4\\pi w}{t}\\right)$  for $w/h > \\frac{1}{2\\pi}$
- $\\Delta w = \\frac{t}{\\pi} \\left(1 + \\ln\\frac{2h}{t}\\right)$  for $w/h \\leq \\frac{1}{2\\pi}$

**Propagation Delay:**

$$
T_{pd} = 3.333 \\sqrt{\\varepsilon_r} \\quad \\text{[ns/m]}
$$

**Validity:** $0.1 \\leq w/h \\leq 2.0$  and  $t/h < 0.25$
""")

with sidebar:
  st.markdown("<div style='text-align:center; color:#888; font-size:0.8rem'>Inspired by Mantaro Engineering Calculators · Built for Delft CRI/oFlex®3 CF3</div>", unsafe_allow_html=True)
  st.markdown('<div class="sub-title">⚡ CRI/oFlex<sup>®</sup>3 CF3 Impedance Calculator</div>', unsafe_allow_html=True)
  st.markdown('<div class="sub-title">Symmetric Stripline · Polyimide & Silver (Ag) · DC – 10 GHz</div>', unsafe_allow_html=True)
