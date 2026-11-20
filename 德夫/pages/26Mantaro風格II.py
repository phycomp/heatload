from streamlit import columns, header, markdown, number_input, pyplot, radio, set_page_config, sidebar, warning
from matplotlib.pyplot import subplots, tight_layout
from numpy import isnan, log, nan, pi as π, sqrt
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# ============================================================
# Delft CRI/oFlex3 CF3 - Stripline Impedance Calculator
# Inspired by Mantaro Impedance Calculators
# ============================================================

set_page_config(page_title="CRI/oFlex3 CF3 Impedance Calculator", layout="wide")

# ---- Custom CSS for Mantaro-like look ----
markdown('''
<style>
    .main-title { font-size: 2.2rem; font-weight: 700; color: #1a1a2e; margin-bottom: 0.3rem; }
    .sub-title { font-size: 1.05rem; color: #555; margin-bottom: 1.5rem; }
    .result-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.2rem; border-radius: 12px; text-align: center; margin: 0.5rem 0; }
    .result-value { font-size: 2.4rem; font-weight: 800; color: #fff; }
    .result-label { font-size: 0.9rem; color: rgba(255,255,255,0.85); text-transform: uppercase; letter-spacing: 1px; }
    .param-card { background: black; border-radius: 10px; padding: 1rem; border-left: 4px solid #667eea; margin-bottom: 0.8rem; }
    .note-text { font-size: 0.8rem; color: #888; margin-top: 0.5rem; }
    .section-header { font-size: 1.1rem; font-weight: 600; color: white; margin: 1.2rem 0 0.6rem 0; border-bottom: 2px solid #e0e0e0; padding-bottom: 0.3rem; }
</style>
''', unsafe_allow_html=True)


# ---- Sidebar: Input Parameters ----
with sidebar:
    header("Input Parameters")

    unit = radio("Dimensional Units", ["mm", "mils"], index=0, horizontal=True)

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

    w = number_input("w (trace width)", min_value=w_min, max_value=w_max, value=w_default, step=w_step, format="%.4f" if unit=="mm" else "%.2f")
    t = number_input("t (trace thickness)", min_value=t_min, max_value=t_max, value=t_default, step=t_step, format="%.4f" if unit=="mm" else "%.2f")
    h = number_input("h (total dielectric thickness)", min_value=h_min, max_value=h_max, value=h_default, step=h_step, format="%.4f" if unit=="mm" else "%.2f")

#    markdown("---")
    er = number_input("er (relative dielectric constant)", min_value=1.0, max_value=20.0, value=3.4, step=0.1, format="%.2f")

#    markdown("---")
    markdown("**CF3 Defaults**")
    markdown("- Total thickness: 0.30 mm")
    markdown("- Material: Polyimide (er~3.4)")
    markdown("- Conductor: Silver (Ag)")
    markdown("- Type: Symmetric Stripline")
    markdown("- Impedance target: 50 Ohm")

#    markdown("---")
    markdown('<div class="note-text">Note: 1 oz Cu = 1.4 mils = 0.03556 mm</div>', unsafe_allow_html=True)

# ---- Convert to mm for calculation ----
if unit == "mils":
    w_mm = w * 0.0254
    t_mm = t * 0.0254
    h_mm = h * 0.0254
else:
    w_mm, t_mm, h_mm = w, t, h

# ---- Impedance Calculation (Symmetric Stripline) ----
def calc_stripline_z0(w, t, h, er):
    if h <= 0 or w <= 0 or t < 0 or er <= 0:
        return nan
    if w / h > 1 / (2 * π):
        delta_w = (t / π) * (1 + log(4 * π * w / t))
    else:
        delta_w = (t / π) * (1 + log(2 * h / t))
    w_eff = w + delta_w
    Cf = (2 / π) * log(2)
    z0 = (30 * π / sqrt(er)) / (w_eff / h + Cf)
    return z0

z0 = calc_stripline_z0(w_mm, t_mm, h_mm, er)
tpd_ns_per_m = 3.333 * sqrt(er)
tpd_ps_per_mm = tpd_ns_per_m / 1e6
if z0 > 0 and not isnan(z0):
    c_pf_per_mm = tpd_ps_per_mm / z0
else:
    c_pf_per_mm = nan

# ---- Main Layout ----
col_left, col_right = columns([1, 1.6])

with col_left:
    markdown('<div class="section-header">Calculation Results</div>', unsafe_allow_html=True)
    z0_display = f"{z0:.2f}" if not isnan(z0) else "-"

    result_html = '''
    <div class="result-box">
        <div class="result-label">Characteristic Impedance Z0</div>
        <div class="result-value">''' + z0_display + ''' Ohm</div>
    </div>
    '''
    markdown(result_html, unsafe_allow_html=True)

    markdown("**Propagation Delay**")
    markdown(f"- **Tpd** = {tpd_ps_per_mm:.3f} ps/mm = {tpd_ns_per_m:.3f} ns/m")
    markdown("**Capacitance**")
    markdown(f"- **C** ~ {c_pf_per_mm:.4f} pF/mm")
#    markdown("---")
    markdown('<div class="section-header">Parameters Summary</div>', unsafe_allow_html=True)

    def param_row(label, val, unit_str):
        return f'<div class="param-card"><b>{label}</b><br><span style="font-size:1.1rem">{val} {unit_str}</span></div>'

    markdown(param_row("Trace Width (w)", f"{w:.4f}" if unit=="mm" else f"{w:.2f}", unit), unsafe_allow_html=True)
    markdown(param_row("Trace Thickness (t)", f"{t:.4f}" if unit=="mm" else f"{t:.2f}", unit), unsafe_allow_html=True)
    markdown(param_row("Dielectric Thickness (h)", f"{h:.4f}" if unit=="mm" else f"{h:.2f}", unit), unsafe_allow_html=True)
    markdown(param_row("Dielectric Constant (er)", f"{er:.2f}", ""), unsafe_allow_html=True)

    wh_ratio = w_mm / h_mm if h_mm > 0 else 0
    th_ratio = t_mm / h_mm if h_mm > 0 else 0
#    markdown("---")
    markdown('<div class="section-header">Validity Check</div>', unsafe_allow_html=True)
    valid = True
    checks = []
    if not (0.1 <= wh_ratio <= 2.0):
        checks.append(f"w/h = {wh_ratio:.3f} (valid: 0.1 - 2.0)")
        valid = False
    else:
        checks.append(f"OK w/h = {wh_ratio:.3f}")
    if th_ratio >= 0.25:
        checks.append(f"t/h = {th_ratio:.3f} (valid: < 0.25)")
        valid = False
    else:
        checks.append(f"OK t/h = {th_ratio:.3f}")
    for c in checks:
        markdown(c)
    if not valid:
        warning("Results may be less accurate outside recommended ranges.")

with col_right:
    markdown('<div class="section-header">Cross-Section Side View</div>', unsafe_allow_html=True)
    fig, ax = subplots(figsize=(10, 6), dpi=120)
    scale = 3.0 / h_mm if h_mm > 0 else 1.0
    h_vis = h_mm * scale
    w_vis = w_mm * scale
    t_vis = max(t_mm * scale, 0.08)
    center_x = 5
    center_y = 3
    gp_thickness = 0.15

    top_dielectric = patches.Rectangle((center_x - 3, center_y + t_vis/2), 6, h_vis/2 - t_vis/2, linewidth=1.5, edgecolor="#333", facecolor="#e8d5b7", hatch="///", alpha=0.9)
    ax.add_patch(top_dielectric)
    bottom_dielectric = patches.Rectangle((center_x - 3, center_y - h_vis/2), 6, h_vis/2 - t_vis/2, linewidth=1.5, edgecolor="#333", facecolor="#e8d5b7", hatch="///", alpha=0.9)
    ax.add_patch(bottom_dielectric)
    trace = patches.Rectangle((center_x - w_vis/2, center_y - t_vis/2), w_vis, t_vis, linewidth=2, edgecolor="#1a1a2e", facecolor="#c0c0c0", alpha=0.95, zorder=5)
    ax.add_patch(trace)
    top_gp = patches.Rectangle((center_x - 3, center_y + h_vis/2), 6, gp_thickness, linewidth=1.5, edgecolor="#333", facecolor="#444", alpha=0.95, zorder=6)
    ax.add_patch(top_gp)
    bottom_gp = patches.Rectangle((center_x - 3, center_y - h_vis/2 - gp_thickness), 6, gp_thickness, linewidth=1.5, edgecolor="#333", facecolor="#444", alpha=0.95, zorder=6)
    ax.add_patch(bottom_gp)

    arrow_style = dict(arrowstyle="<->", color="#d32f2f", lw=1.5)
    text_style = dict(fontsize=11, color="#d32f2f", fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#d32f2f", alpha=0.9))

    ax.annotate("", xy=(center_x - w_vis/2, center_y + h_vis/2 + gp_thickness + 0.3), xytext=(center_x + w_vis/2, center_y + h_vis/2 + gp_thickness + 0.3), arrowprops=arrow_style)
    ax.text(center_x, center_y + h_vis/2 + gp_thickness + 0.55, f"w = {w:.4f} {unit}" if unit=="mm" else f"w = {w:.2f} {unit}", ha="center", va="bottom", **text_style)
    ax.annotate("", xy=(center_x + 3.2, center_y - h_vis/2 - gp_thickness), xytext=(center_x + 3.2, center_y + h_vis/2 + gp_thickness), arrowprops=arrow_style)
    ax.text(center_x + 3.5, center_y, f"h = {h:.4f} {unit}" if unit=="mm" else f"h = {h:.2f} {unit}", ha="left", va="center", rotation=90, **text_style)
    ax.annotate("", xy=(center_x - w_vis/2 - 0.4, center_y - t_vis/2), xytext=(center_x - w_vis/2 - 0.4, center_y + t_vis/2), arrowprops=arrow_style)
    ax.text(center_x - w_vis/2 - 0.7, center_y, f"t = {t:.4f} {unit}" if unit=="mm" else f"t = {t:.2f} {unit}", ha="right", va="center", rotation=90, **text_style)

    ax.text(center_x, center_y + h_vis/4 + t_vis/4, f"Polyimide\n(er = {er:.2f})", ha="center", va="center", fontsize=10, color="#666", style="italic")
    ax.text(center_x, center_y - h_vis/4 - t_vis/4, f"Polyimide\n(er = {er:.2f})", ha="center", va="center", fontsize=10, color="#666", style="italic")
    ax.text(center_x, center_y, "Ag Trace", ha="center", va="center", fontsize=9, color="#1a1a2e", fontweight="bold", zorder=7)
    ax.text(center_x, center_y + h_vis/2 + gp_thickness/2, "GND", ha="center", va="center", fontsize=9, color="white", fontweight="bold", zorder=7)
    ax.text(center_x, center_y - h_vis/2 - gp_thickness/2, "GND", ha="center", va="center", fontsize=9, color="white", fontweight="bold", zorder=7)
    ax.axhline(y=center_y, xmin=0.05, xmax=0.95, color="#999", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"Symmetric Stripline Cross-Section  |  Z0 ~ {z0:.2f} Ohm", fontsize=13, fontweight="bold", color="#1a1a2e", pad=15)
    tight_layout()
    pyplot(fig)
    markdown('<div class="note-text" style="text-align:center">Cross-section diagram auto-scales for visibility. Dimensions shown are actual values.</div>', unsafe_allow_html=True)

#markdown("---")
markdown('<div class="section-header">Formula Reference</div>', unsafe_allow_html=True)
markdown('''
**Symmetric Stripline Impedance** (approximation, IPC-2141 / Wadell):

Z0 = (30*π / sqrt(er)) * 1 / (weff/h + Cf)

where:
- weff = w + delta_w  (effective trace width with thickness correction)
- Cf = (2/π) * ln(2) ~ 0.441  (fringing capacitance factor)
- delta_w = (t/π) * (1 + ln(4*π*w/t))  for w/h > 1/(2*π)
- delta_w = (t/π) * (1 + ln(2*h/t))  for w/h <= 1/(2*π)

**Propagation Delay:**

Tpd = 3.333 * sqrt(er)  [ns/m]

**Validity:** 0.1 <= w/h <= 2.0  and  t/h < 0.25
''')
with sidebar:
  markdown("<div style='text-align:center; color:#888; font-size:0.8rem'>Inspired by Mantaro Engineering Calculators - Built for Delft CRI/oFlex3 CF3</div>", unsafe_allow_html=True)
  markdown('<div class="sub-title">CRI/oFlex<sup>3</sup> CF3 Impedance Calculator</div>', unsafe_allow_html=True)
  markdown('<div class="sub-title">Symmetric Stripline - Polyimide &amp; Silver (Ag) - DC to 10 GHz</div>', unsafe_allow_html=True)
