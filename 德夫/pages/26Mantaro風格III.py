from streamlit import code, columns, download_button, error, header, markdown, number_input, pyplot, radio, set_page_config, sidebar, success, tabs, warning
from matplotlib.pyplot import subplots, tight_layout
from numpy import datetime64, exp, isnan, log, nan, pi, sqrt
# Build the comprehensive enhanced Streamlit app
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from scipy.optimize import fsolve
import io

# ============================================================
# Delft CRI/oFlex3 CF3 - Enhanced Impedance Calculator
# Inspired by Mantaro Impedance Calculators
# Features: Forward calc, Reverse calc, Differential, Gerber export
# ============================================================

st.set_page_config(page_title="CRI/oFlex3 CF3 Calculator", layout="wide")

# ---- Custom CSS ----
st.markdown('''
<style>
    .main-title { font-size: 2.2rem; font-weight: 700; color: #1a1a2e; margin-bottom: 0.3rem; }
    .sub-title { font-size: 1.05rem; color: #555; margin-bottom: 1.5rem; }
    .result-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.2rem; border-radius: 12px; text-align: center; margin: 0.5rem 0; }
    .result-value { font-size: 2.4rem; font-weight: 800; color: #fff; }
    .result-label { font-size: 0.9rem; color: rgba(255,255,255,0.85); text-transform: uppercase; letter-spacing: 1px; }
    .param-card { background: #f8f9fa; border-radius: 10px; padding: 1rem; border-left: 4px solid #667eea; margin-bottom: 0.8rem; }
    .note-text { font-size: 0.8rem; color: #888; margin-top: 0.5rem; }
    .section-header { font-size: 1.1rem; font-weight: 600; color: white; margin: 1.2rem 0 0.6rem 0; border-bottom: 2px solid #e0e0e0; padding-bottom: 0.3rem; }
    .formula-box { background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 1rem; font-family: "Courier New", monospace; font-size: 0.95rem; line-height: 1.6; }
    .formula-title { font-weight: bold; color: #333; margin-bottom: 0.5rem; }
    .tab-content { padding-top: 1rem; }
</style>
''', unsafe_allow_html=True)

# ============================================================
# UNIT CONVERSION UTILS
# ============================================================
def to_mm(val, unit):
    return val * 0.0254 if unit == "mils" else val

def from_mm(val, unit):
    return val / 0.0254 if unit == "mils" else val

# ============================================================
# IMPEDANCE CALCULATIONS
# ============================================================
def delta_w(w, t, h):
    if w / h > 1 / (2 * np.pi):
        return (t / np.pi) * (1 + np.log(4 * np.pi * w / t))
    else:
        return (t / np.pi) * (1 + np.log(2 * h / t))

def weff(w, t, h):
    return w + delta_w(w, t, h)

def z0_stripline(w, t, h, er):
    if h <= 0 or w <= 0 or t < 0 or er <= 0:
        return np.nan
    w_eff = weff(w, t, h)
    Cf = (2 / np.pi) * np.log(2)
    return (30 * np.pi / np.sqrt(er)) / (w_eff / h + Cf)

def z0_diff_stripline(w, d, t, h, er):
    """Differential stripline impedance"""
    z0_single = z0_stripline(w, t, h, er)
    if np.isnan(z0_single):
        return np.nan
    # IPC-2141 approximation for differential stripline
    zd = 2 * z0_single * (1 - 0.347 * np.exp(-2.9 * d / (2 * h + t)))
    return zd

def solve_w_from_z0(target_z0, t, h, er):
    """Reverse solve trace width w from target Z0"""
    if target_z0 <= 0 or h <= 0 or er <= 0:
        return np.nan
    Cf = (2 / np.pi) * np.log(2)
    # From Z0 = (30*pi/sqrt(er)) / (weff/h + Cf)
    # weff/h + Cf = (30*pi/sqrt(er)) / Z0
    # weff = h * ((30*pi/sqrt(er))/Z0 - Cf)
    target_weff = h * ((30 * np.pi / np.sqrt(er)) / target_z0 - Cf)
    if target_weff <= 0:
        return np.nan
    # weff = w + delta_w(w,t,h), solve numerically
    def f(w):
        return weff(w, t, h) - target_weff
    try:
        w_sol = fsolve(f, target_weff * 0.8)[0]
        if w_sol > 0:
            return w_sol
        w_sol = fsolve(f, target_weff * 0.3)[0]
        return w_sol if w_sol > 0 else np.nan
    except:
        return np.nan

# ============================================================
# SIDEBAR INPUTS
# ============================================================
with st.sidebar:
    st.header("Global Settings")
    unit = st.radio("Dimensional Units", ["mm", "mils"], index=0, horizontal=True)
    
    if unit == "mm":
        w_default, h_default, t_default, d_default = 0.19, 0.30, 0.01, 0.15
        step_small, step_med = 0.001, 0.01
        min_w, max_w = 0.01, 2.0
        min_h, max_h = 0.05, 2.0
        min_t, max_t = 0.001, 0.1
        min_d, max_d = 0.01, 2.0
    else:
        w_default, h_default, t_default, d_default = 7.5, 11.8, 0.4, 5.9
        step_small, step_med = 0.05, 0.5
        min_w, max_w = 0.4, 80.
        min_h, max_h = 2.0, 80.
        min_t, max_t = 0.04, 4.
        min_d, max_d = 0.4, 80.
    
#    st.markdown("---")
    st.markdown("**CF3 Defaults**")
    st.markdown("- Total thickness: 0.30 mm")
    st.markdown("- Material: Polyimide (er~3.4)")
    st.markdown("- Conductor: Silver (Ag)")
    st.markdown("- Type: Symmetric Stripline")
    st.markdown("- Impedance target: 50 Ohm")
#    st.markdown("---")
    st.markdown('<div class="note-text">Note: 1 oz Cu = 1.4 mils = 0.03556 mm</div>', unsafe_allow_html=True)

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "1. Forward Calc (Z0 from w)",
    "2. Reverse Calc (w from Z0)",
    "3. Differential Pair",
    "4. Gerber Export"
])

# ============================================================
# TAB 1: FORWARD CALCULATION
# ============================================================
with tab1:
    st.markdown('<div class="section-header">Single-Ended Stripline Calculator</div>', unsafe_allow_html=True)
    
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        w = st.number_input("w (trace width)", min_value=min_w, max_value=max_w, value=w_default, step=step_small, format="%.4f" if unit=="mm" else "%.2f", key="t1_w")
        t = st.number_input("t (trace thickness)", min_value=min_t, max_value=max_t, value=t_default, step=step_small, format="%.4f" if unit=="mm" else "%.2f", key="t1_t")
    with col_in2:
        h = st.number_input("h (total dielectric thickness)", min_value=min_h, max_value=max_h,
                            value=h_default, step=step_small, format="%.4f" if unit=="mm" else "%.2f", key="t1_h")
        er = st.number_input("er (relative dielectric constant)", min_value=1.0, max_value=20.0,
                             value=3.4, step=0.1, format="%.2f", key="t1_er")
    
    w_mm, t_mm, h_mm = to_mm(w, unit), to_mm(t, unit), to_mm(h, unit)
    
    z0 = z0_stripline(w_mm, t_mm, h_mm, er)
    tpd_ns_per_m = 3.333 * np.sqrt(er)
    tpd_ps_per_mm = tpd_ns_per_m / 1e6
    c_pf_per_mm = tpd_ps_per_mm / z0 if z0 > 0 and not np.isnan(z0) else np.nan
    
    col_res, col_fig = st.columns([1, 1.8])
    
    with col_res:
        z0_display = f"{z0:.2f}" if not np.isnan(z0) else "-"
        st.markdown(f'''
        <div class="result-box">
            <div class="result-label">Characteristic Impedance Z0</div>
            <div class="result-value">{z0_display} Ohm</div>
        </div>
        ''', unsafe_allow_html=True)
        st.markdown(f"**Tpd** = {tpd_ps_per_mm:.3f} ps/mm = {tpd_ns_per_m:.3f} ns/m")
        st.markdown(f"**C** ~ {c_pf_per_mm:.4f} pF/mm")
        
        wh_ratio = w_mm / h_mm if h_mm > 0 else 0
        th_ratio = t_mm / h_mm if h_mm > 0 else 0
#        st.markdown("---")
        st.markdown("**Validity Check**")
        if 0.1 <= wh_ratio <= 2.0:
            st.success(f"OK: w/h = {wh_ratio:.3f}")
        else:
            st.warning(f"w/h = {wh_ratio:.3f} (valid: 0.1 - 2.0)")
        if th_ratio < 0.25:
            st.success(f"OK: t/h = {th_ratio:.3f}")
        else:
            st.warning(f"t/h = {th_ratio:.3f} (valid: < 0.25)")
    
    with col_fig:
        # Draw cross-section with formula overlay (Mantaro style)
        fig, ax = plt.subplots(figsize=(11, 5.5), dpi=130)
        
        scale = 3.0 / h_mm if h_mm > 0 else 1.0
        h_vis = h_mm * scale
        w_vis = w_mm * scale
        t_vis = max(t_mm * scale, 0.08)
        cx, cy = 3.5, 2.8
        gp = 0.15
        
        # Dielectric
        ax.add_patch(patches.Rectangle((cx-2.5, cy+t_vis/2), 5, h_vis/2-t_vis/2, linewidth=1.5, edgecolor="#333", facecolor="#e8d5b7", hatch="///", alpha=0.9))
        ax.add_patch(patches.Rectangle((cx-2.5, cy-h_vis/2), 5, h_vis/2-t_vis/2, linewidth=1.5, edgecolor="#333", facecolor="#e8d5b7", hatch="///", alpha=0.9))
        # Trace
        ax.add_patch(patches.Rectangle((cx-w_vis/2, cy-t_vis/2), w_vis, t_vis, linewidth=2, edgecolor="#1a1a2e", facecolor="#c0c0c0", alpha=0.95, zorder=5))
        # GND
        ax.add_patch(patches.Rectangle((cx-2.5, cy+h_vis/2), 5, gp, linewidth=1.5, edgecolor="#333", facecolor="#444", alpha=0.95, zorder=6))
        ax.add_patch(patches.Rectangle((cx-2.5, cy-h_vis/2-gp), 5, gp, linewidth=1.5, edgecolor="#333", facecolor="#444", alpha=0.95, zorder=6))
        
        # Annotations
        arr = dict(arrowstyle="<->", color="#d32f2f", lw=1.5)
        txt = dict(fontsize=10, color="#d32f2f", fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#d32f2f", alpha=0.9))
        ax.annotate("", xy=(cx-w_vis/2, cy+h_vis/2+gp+0.25), xytext=(cx+w_vis/2, cy+h_vis/2+gp+0.25), arrowprops=arr)
        ax.text(cx, cy+h_vis/2+gp+0.5, f"w={w:.4f}{unit}" if unit=="mm" else f"w={w:.2f}{unit}", ha="center", va="bottom", **txt)
        ax.annotate("", xy=(cx+2.7, cy-h_vis/2-gp), xytext=(cx+2.7, cy+h_vis/2+gp), arrowprops=arr)
        ax.text(cx+3.0, cy, f"h={h:.4f}{unit}" if unit=="mm" else f"h={h:.2f}{unit}", ha="left", va="center", rotation=90, **txt)
        ax.annotate("", xy=(cx-w_vis/2-0.35, cy-t_vis/2), xytext=(cx-w_vis/2-0.35, cy+t_vis/2), arrowprops=arr)
        ax.text(cx-w_vis/2-0.6, cy, f"t={t:.4f}{unit}" if unit=="mm" else f"t={t:.2f}{unit}", ha="right", va="center", rotation=90, **txt)
        
        ax.text(cx, cy, "Ag", ha="center", va="center", fontsize=8, color="#1a1a2e", fontweight="bold", zorder=7)
        ax.text(cx, cy+h_vis/2+gp/2, "GND", ha="center", va="center", fontsize=8, color="white", fontweight="bold", zorder=7)
        ax.text(cx, cy-h_vis/2-gp/2, "GND", ha="center", va="center", fontsize=8, color="white", fontweight="bold", zorder=7)
        ax.axhline(y=cy, xmin=0.05, xmax=0.6, color="#999", linestyle="--", linewidth=0.7, alpha=0.5)
        
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 6)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(f"Cross-Section  |  Z0 = {z0:.2f} Ohm", fontsize=12, fontweight="bold", color="#1a1a2e", pad=10)
        
        # Formula panel on the right side of the figure
        formula_text = (
            "Symmetric Stripline (IPC-2141):\n"
            "\n"
            "Z0 = (30\u03c0 / \u221aer) / (weff/h + Cf)\n"
            "\n"
            "weff = w + \u0394w\n"
            "\n"
            "\u0394w = (t/\u03c0)(1 + ln(4\u03c0w/t))\n"
            "       for w/h > 1/(2\u03c0)\n"
            "\n"
            "\u0394w = (t/\u03c0)(1 + ln(2h/t))\n"
            "       for w/h \u2264 1/(2\u03c0)\n"
            "\n"
            "Cf = (2/\u03c0)ln(2) \u2248 0.441\n"
            "\n"
            "Tpd = 3.333\u00b7\u221aer  [ns/m]"
        )
        ax.text(6.8, 3.0, formula_text, fontsize=9, family="monospace",
                verticalalignment="center", bbox=dict(boxstyle="round,pad=0.5", facecolor="#f5f5f5", edgecolor="#ccc"))
        
        plt.tight_layout()
        st.pyplot(fig)

# ============================================================
# TAB 2: REVERSE CALCULATION
# ============================================================
with tab2:
    st.markdown('<div class="section-header">Reverse Calculator: Find Trace Width from Target Z0</div>', unsafe_allow_html=True)
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        target_z0 = st.number_input("Target Z0 (Ohm)", min_value=1.0, max_value=500.0, value=50.0, step=1.0, format="%.1f", key="t2_z0")
        t_rev = st.number_input("t (trace thickness)", min_value=min_t, max_value=max_t,
                                value=t_default, step=step_small, format="%.4f" if unit=="mm" else "%.2f", key="t2_t")
    with col_r2:
        h_rev = st.number_input("h (total dielectric thickness)", min_value=min_h, max_value=max_h,
                                value=h_default, step=step_small, format="%.4f" if unit=="mm" else "%.2f", key="t2_h")
        er_rev = st.number_input("er (relative dielectric constant)", min_value=1.0, max_value=20.0,
                                 value=3.4, step=0.1, format="%.2f", key="t2_er")
    
    t_mm_r = to_mm(t_rev, unit)
    h_mm_r = to_mm(h_rev, unit)
    w_mm_calc = solve_w_from_z0(target_z0, t_mm_r, h_mm_r, er_rev)
    w_calc = from_mm(w_mm_calc, unit)
    
    col_res2, col_fig2 = st.columns([1, 1.8])
    
    with col_res2:
        if not np.isnan(w_mm_calc):
            z0_check = z0_stripline(w_mm_calc, t_mm_r, h_mm_r, er_rev)
            st.markdown(f'''
            <div class="result-box">
                <div class="result-label">Required Trace Width w</div>
                <div class="result-value">{w_calc:.4f} {unit}</div>
            </div>
            ''', unsafe_allow_html=True)
            st.markdown(f"**Verification:** Z0 = {z0_check:.2f} Ohm")
            st.markdown(f"**w/h ratio:** {w_mm_calc/h_mm_r:.3f}")
            
            # Sensitivity table
#            st.markdown("---")
            st.markdown("**Sensitivity ±10% on w**")
            for pct in [-10, -5, 0, 5, 10]:
                w_test = w_mm_calc * (1 + pct/100)
                z_test = z0_stripline(w_test, t_mm_r, h_mm_r, er_rev)
                st.markdown(f"w {pct:+d}% → Z0 = {z_test:.2f} Ohm")
        else:
            st.error("No valid solution found. Check target Z0 and dielectric parameters.")
    
    with col_fig2:
        if not np.isnan(w_mm_calc):
            fig2, ax2 = plt.subplots(figsize=(11, 5.5), dpi=130)
            scale = 3.0 / h_mm_r if h_mm_r > 0 else 1.0
            h_vis = h_mm_r * scale
            w_vis = w_mm_calc * scale
            t_vis = max(t_mm_r * scale, 0.08)
            cx, cy = 3.5, 2.8
            gp = 0.15
            
            ax2.add_patch(patches.Rectangle((cx-2.5, cy+t_vis/2), 5, h_vis/2-t_vis/2, linewidth=1.5, edgecolor="#333", facecolor="#e8d5b7", hatch="///", alpha=0.9))
            ax2.add_patch(patches.Rectangle((cx-2.5, cy-h_vis/2), 5, h_vis/2-t_vis/2, linewidth=1.5, edgecolor="#333", facecolor="#e8d5b7", hatch="///", alpha=0.9))
            ax2.add_patch(patches.Rectangle((cx-w_vis/2, cy-t_vis/2), w_vis, t_vis, linewidth=2, edgecolor="#1a1a2e", facecolor="#c0c0c0", alpha=0.95, zorder=5))
            ax2.add_patch(patches.Rectangle((cx-2.5, cy+h_vis/2), 5, gp, linewidth=1.5, edgecolor="#333", facecolor="#444", alpha=0.95, zorder=6))
            ax2.add_patch(patches.Rectangle((cx-2.5, cy-h_vis/2-gp), 5, gp, linewidth=1.5, edgecolor="#333", facecolor="#444", alpha=0.95, zorder=6))
            
            arr = dict(arrowstyle="<->", color="#d32f2f", lw=1.5)
            txt = dict(fontsize=10, color="#d32f2f", fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#d32f2f", alpha=0.9))
            ax2.annotate("", xy=(cx-w_vis/2, cy+h_vis/2+gp+0.25), xytext=(cx+w_vis/2, cy+h_vis/2+gp+0.25), arrowprops=arr)
            ax2.text(cx, cy+h_vis/2+gp+0.5, f"w={w_calc:.4f}{unit}" if unit=="mm" else f"w={w_calc:.2f}{unit}", ha="center", va="bottom", **txt)
            ax2.annotate("", xy=(cx+2.7, cy-h_vis/2-gp), xytext=(cx+2.7, cy+h_vis/2+gp), arrowprops=arr)
            ax2.text(cx+3.0, cy, f"h={h_rev:.4f}{unit}" if unit=="mm" else f"h={h_rev:.2f}{unit}", ha="left", va="center", rotation=90, **txt)
            ax2.annotate("", xy=(cx-w_vis/2-0.35, cy-t_vis/2), xytext=(cx-w_vis/2-0.35, cy+t_vis/2), arrowprops=arr)
            ax2.text(cx-w_vis/2-0.6, cy, f"t={t_rev:.4f}{unit}" if unit=="mm" else f"t={t_rev:.2f}{unit}", ha="right", va="center", rotation=90, **txt)
            
            ax2.text(cx, cy, "Ag", ha="center", va="center", fontsize=8, color="#1a1a2e", fontweight="bold", zorder=7)
            ax2.text(cx, cy+h_vis/2+gp/2, "GND", ha="center", va="center", fontsize=8, color="white", fontweight="bold", zorder=7)
            ax2.text(cx, cy-h_vis/2-gp/2, "GND", ha="center", va="center", fontsize=8, color="white", fontweight="bold", zorder=7)
            ax2.axhline(y=cy, xmin=0.05, xmax=0.6, color="#999", linestyle="--", linewidth=0.7, alpha=0.5)
            
            ax2.set_xlim(0, 10)
            ax2.set_ylim(0, 6)
            ax2.set_aspect("equal")
            ax2.axis("off")
            ax2.set_title(f"Reverse Design  |  Target Z0 = {target_z0:.1f} Ohm", fontsize=12, fontweight="bold", color="#1a1a2e", pad=10)
            
            formula_text = (
                "Reverse Formula:\n"
                "\n"
                "weff = h * [(30\u03c0/\u221aer)/Z0 - Cf]\n"
                "\n"
                "Solve: weff(w,t,h) - weff_target = 0\n"
                "\n"
                "Cf = (2/\u03c0)ln(2) \u2248 0.441\n"
                "\n"
                "\u0394w = (t/\u03c0)(1+ln(4\u03c0w/t))\n"
                "       or (t/\u03c0)(1+ln(2h/t))"
            )
            ax2.text(6.8, 3.0, formula_text, fontsize=9, family="monospace",
                    verticalalignment="center", bbox=dict(boxstyle="round,pad=0.5", facecolor="#f5f5f5", edgecolor="#ccc"))
            
            plt.tight_layout()
            st.pyplot(fig2)

# ============================================================
# TAB 3: DIFFERENTIAL PAIR
# ============================================================
with tab3:
    st.markdown('<div class="section-header">Differential Stripline Calculator</div>', unsafe_allow_html=True)
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        w_d = st.number_input("w (trace width)", min_value=min_w, max_value=max_w,
                              value=w_default, step=step_small, format="%.4f" if unit=="mm" else "%.2f", key="t3_w")
        d_d = st.number_input("d (trace separation)", min_value=min_d, max_value=max_d,
                              value=d_default, step=step_small, format="%.4f" if unit=="mm" else "%.2f", key="t3_d")
        t_d = st.number_input("t (trace thickness)", min_value=min_t, max_value=max_t,
                              value=t_default, step=step_small, format="%.4f" if unit=="mm" else "%.2f", key="t3_t")
    with col_d2:
        h_d = st.number_input("h (total dielectric thickness)", min_value=min_h, max_value=max_h,
                              value=h_default, step=step_small, format="%.4f" if unit=="mm" else "%.2f", key="t3_h")
        er_d = st.number_input("er (relative dielectric constant)", min_value=1.0, max_value=20.0,
                               value=3.4, step=0.1, format="%.2f", key="t3_er")
    
    w_mm_d = to_mm(w_d, unit)
    d_mm_d = to_mm(d_d, unit)
    t_mm_d = to_mm(t_d, unit)
    h_mm_d = to_mm(h_d, unit)
    
    z0_single = z0_stripline(w_mm_d, t_mm_d, h_mm_d, er_d)
    zd = z0_diff_stripline(w_mm_d, d_mm_d, t_mm_d, h_mm_d, er_d)
    
    col_res3, col_fig3 = st.columns([1, 1.8])
    
    with col_res3:
        z0_d_display = f"{z0_single:.2f}" if not np.isnan(z0_single) else "-"
        zd_display = f"{zd:.2f}" if not np.isnan(zd) else "-"
        st.markdown(f'''
        <div class="result-box">
            <div class="result-label">Single-Ended Z0</div>
            <div class="result-value">{z0_d_display} Ohm</div>
        </div>
        ''', unsafe_allow_html=True)
        st.markdown(f'''
        <div class="result-box" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
            <div class="result-label">Differential Impedance Zd</div>
            <div class="result-value">{zd_display} Ohm</div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown(f"**Coupling factor:** {zd/(2*z0_single):.4f}")
        
        wh_d = w_mm_d / h_mm_d if h_mm_d > 0 else 0
        th_d = t_mm_d / h_mm_d if h_mm_d > 0 else 0
#        st.markdown("---")
        st.markdown("**Validity Check**")
        if 0.1 <= wh_d <= 2.0:
            st.success(f"OK: w/h = {wh_d:.3f}")
        else:
            st.warning(f"w/h = {wh_d:.3f} (valid: 0.1 - 2.0)")
        if th_d < 0.25:
            st.success(f"OK: t/h = {th_d:.3f}")
        else:
            st.warning(f"t/h = {th_d:.3f} (valid: < 0.25)")
    
    with col_fig3:
        fig3, ax3 = plt.subplots(figsize=(11, 5.5), dpi=130)
        scale = 3.0 / h_mm_d if h_mm_d > 0 else 1.0
        h_vis = h_mm_d * scale
        w_vis = w_mm_d * scale
        t_vis = max(t_mm_d * scale, 0.08)
        d_vis = d_mm_d * scale
        cx, cy = 3.5, 2.8
        gp = 0.15
        
        # Dielectric
        ax3.add_patch(patches.Rectangle((cx-2.5, cy+t_vis/2), 5, h_vis/2-t_vis/2, linewidth=1.5, edgecolor="#333", facecolor="#e8d5b7", hatch="///", alpha=0.9))
        ax3.add_patch(patches.Rectangle((cx-2.5, cy-h_vis/2), 5, h_vis/2-t_vis/2, linewidth=1.5, edgecolor="#333", facecolor="#e8d5b7", hatch="///", alpha=0.9))
        
        # Two traces
        ax3.add_patch(patches.Rectangle((cx-d_vis/2-w_vis, cy-t_vis/2), w_vis, t_vis, linewidth=2, edgecolor="#1a1a2e", facecolor="#c0c0c0", alpha=0.95, zorder=5))
        ax3.add_patch(patches.Rectangle((cx+d_vis/2, cy-t_vis/2), w_vis, t_vis, linewidth=2, edgecolor="#1a1a2e", facecolor="#c0c0c0", alpha=0.95, zorder=5))
        
        # GND
        ax3.add_patch(patches.Rectangle((cx-2.5, cy+h_vis/2), 5, gp, linewidth=1.5, edgecolor="#333", facecolor="#444", alpha=0.95, zorder=6))
        ax3.add_patch(patches.Rectangle((cx-2.5, cy-h_vis/2-gp), 5, gp, linewidth=1.5, edgecolor="#333", facecolor="#444", alpha=0.95, zorder=6))
        
        arr = dict(arrowstyle="<->", color="#d32f2f", lw=1.5)
        txt = dict(fontsize=10, color="#d32f2f", fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#d32f2f", alpha=0.9))
        
        # w annotations
        ax3.annotate("", xy=(cx-d_vis/2-w_vis, cy+h_vis/2+gp+0.25), xytext=(cx-d_vis/2, cy+h_vis/2+gp+0.25), arrowprops=arr)
        ax3.text(cx-d_vis/2-w_vis/2, cy+h_vis/2+gp+0.5, f"w={w_d:.4f}{unit}" if unit=="mm" else f"w={w_d:.2f}{unit}", ha="center", va="bottom", **txt)
        ax3.annotate("", xy=(cx+d_vis/2, cy+h_vis/2+gp+0.25), xytext=(cx+d_vis/2+w_vis, cy+h_vis/2+gp+0.25), arrowprops=arr)
        ax3.text(cx+d_vis/2+w_vis/2, cy+h_vis/2+gp+0.5, f"w={w_d:.4f}{unit}" if unit=="mm" else f"w={w_d:.2f}{unit}", ha="center", va="bottom", **txt)
        
        # d annotation
        ax3.annotate("", xy=(cx-d_vis/2, cy+h_vis/2+gp+0.9), xytext=(cx+d_vis/2, cy+h_vis/2+gp+0.9), arrowprops=arr)
        ax3.text(cx, cy+h_vis/2+gp+1.15, f"d={d_d:.4f}{unit}" if unit=="mm" else f"d={d_d:.2f}{unit}", ha="center", va="bottom", **txt)
        
        # h annotation
        ax3.annotate("", xy=(cx+2.7, cy-h_vis/2-gp), xytext=(cx+2.7, cy+h_vis/2+gp), arrowprops=arr)
        ax3.text(cx+3.0, cy, f"h={h_d:.4f}{unit}" if unit=="mm" else f"h={h_d:.2f}{unit}", ha="left", va="center", rotation=90, **txt)
        
        ax3.text(cx, cy, "Ag", ha="center", va="center", fontsize=8, color="#1a1a2e", fontweight="bold", zorder=7)
        ax3.text(cx, cy+h_vis/2+gp/2, "GND", ha="center", va="center", fontsize=8, color="white", fontweight="bold", zorder=7)
        ax3.text(cx, cy-h_vis/2-gp/2, "GND", ha="center", va="center", fontsize=8, color="white", fontweight="bold", zorder=7)
        ax3.axhline(y=cy, xmin=0.05, xmax=0.6, color="#999", linestyle="--", linewidth=0.7, alpha=0.5)
        
        ax3.set_xlim(0, 10)
        ax3.set_ylim(0, 6.5)
        ax3.set_aspect("equal")
        ax3.axis("off")
        ax3.set_title(f"Differential Stripline  |  Zd = {zd:.2f} Ohm", fontsize=12, fontweight="bold", color="#1a1a2e", pad=10)
        
        formula_text = (
            "Differential Stripline:\n"
            "\n"
            "Zd = 2\u00b7Z0\u00b7[1 - 0.347\u00b7exp(-2.9d/(2h+t))]\n"
            "\n"
            "Z0 = (30\u03c0/\u221aer)/(weff/h+Cf)\n"
            "\n"
            "Coupling decreases as d increases.\n"
            "\n"
            "For large d: Zd \u2192 2\u00b7Z0\n"
            "(uncoupled differential pair)"
        )
        ax3.text(6.8, 3.0, formula_text, fontsize=9, family="monospace",
                verticalalignment="center", bbox=dict(boxstyle="round,pad=0.5", facecolor="#f5f5f5", edgecolor="#ccc"))
        
        plt.tight_layout()
        st.pyplot(fig3)

# ============================================================
# TAB 4: GERBER EXPORT
# ============================================================
with tab4:
    st.markdown('<div class="section-header">Gerber Specification Export</div>', unsafe_allow_html=True)
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        w_g = st.number_input("w (trace width)", min_value=min_w, max_value=max_w,
                              value=w_default, step=step_small, format="%.4f" if unit=="mm" else "%.2f", key="t4_w")
        t_g = st.number_input("t (trace thickness)", min_value=min_t, max_value=max_t,
                              value=t_default, step=step_small, format="%.4f" if unit=="mm" else "%.2f", key="t4_t")
        d_g = st.number_input("d (trace separation, diff only)", min_value=0.0, max_value=max_d,
                              value=0.0, step=step_small, format="%.4f" if unit=="mm" else "%.2f", key="t4_d")
    with col_g2:
        h_g = st.number_input("h (total dielectric thickness)", min_value=min_h, max_value=max_h,
                              value=h_default, step=step_small, format="%.4f" if unit=="mm" else "%.2f", key="t4_h")
        er_g = st.number_input("er (relative dielectric constant)", min_value=1.0, max_value=20.0,
                               value=3.4, step=0.1, format="%.2f", key="t4_er")
    
    w_mm_g = to_mm(w_g, unit)
    t_mm_g = to_mm(t_g, unit)
    d_mm_g = to_mm(d_g, unit)
    h_mm_g = to_mm(h_g, unit)
    
    z0_g = z0_stripline(w_mm_g, t_mm_g, h_mm_g, er_g)
    zd_g = z0_diff_stripline(w_mm_g, d_mm_g, t_mm_g, h_mm_g, er_g) if d_mm_g > 0 else np.nan
    
    is_diff = d_mm_g > 0
    
#    st.markdown("---")
    st.markdown("**Calculated Impedance**")
    st.markdown(f"- Single-ended Z0 = {z0_g:.2f} Ohm")
    if is_diff:
        st.markdown(f"- Differential Zd = {zd_g:.2f} Ohm")
    
#    st.markdown("---")
    st.markdown("**Export Options**")
    
    export_format = st.radio("Export Format", ["Gerber RS-274X Snippet", "Design Spec Sheet (TXT)", "CSV Parameters"], horizontal=True)
    
    if export_format == "Gerber RS-274X Snippet":
        gerber = f"""; Gerber RS-274X Snippet for CRI/oFlex3 CF3
; Generated by CF3 Impedance Calculator
; Material: Polyimide (er={er_g:.2f})
; Conductor: Silver (Ag)
; Total Dielectric Thickness: {h_g:.4f} {unit}
; Trace Thickness: {t_g:.4f} {unit}
; Trace Width: {w_g:.4f} {unit}
; Single-Ended Impedance: {z0_g:.2f} Ohm
"""
        if is_diff:
            gerber += f"; Trace Separation: {d_g:.4f} {unit}\n"
            gerber += f"; Differential Impedance: {zd_g:.2f} Ohm\n"
        gerber += f"""
; Aperture for trace
%ADD10R,{w_g:.4f}X{w_g:.4f}*%

; Trace segment (example)
G01*
D10*
X0Y0D02*
X10000Y0D01*
M02*
"""
        st.code(gerber, language="text")
        st.download_button("Download .gbr snippet", gerber, file_name="cf3_trace.gbr", mime="text/plain")
    
    elif export_format == "Design Spec Sheet (TXT)":
        spec = f"""=============================================
CRI/oFlex3 CF3 Design Specification Sheet
=============================================
Generated: {np.datetime64('today')}

MATERIAL
--------
Substrate:      Polyimide
Dielectric Constant (er): {er_g:.2f}
Total Thickness (h):      {h_g:.4f} {unit}  ({h_mm_g:.4f} mm)

CONDUCTOR
---------
Material:       Silver (Ag)
Trace Width (w):          {w_g:.4f} {unit}  ({w_mm_g:.4f} mm)
Trace Thickness (t):      {t_g:.4f} {unit}  ({t_mm_g:.4f} mm)
"""
        if is_diff:
            spec += f"Trace Separation (d):     {d_g:.4f} {unit}  ({d_mm_g:.4f} mm)\n"
        spec += f"""
ELECTRICAL
----------
Single-Ended Z0:          {z0_g:.2f} Ohm
"""
        if is_diff:
            spec += f"Differential Zd:            {zd_g:.2f} Ohm\n"
        spec += f"""Propagation Delay (Tpd):  {3.333*np.sqrt(er_g):.3f} ns/m

VALIDITY CHECK
--------------
w/h ratio: {w_mm_g/h_mm_g:.3f}  {'PASS' if 0.1 <= w_mm_g/h_mm_g <= 2.0 else 'FAIL'} (valid: 0.1 - 2.0)
t/h ratio: {t_mm_g/h_mm_g:.3f}  {'PASS' if t_mm_g/h_mm_g < 0.25 else 'FAIL'} (valid: < 0.25)

NOTES
-----
- Valid for DC to 10 GHz operation
- Symmetric stripline configuration
- Ground planes on both sides of dielectric
=============================================
"""
        st.code(spec, language="text")
        st.download_button("Download Spec Sheet", spec, file_name="cf3_design_spec.txt", mime="text/plain")
    
    else:  # CSV
        import csv
        import io as bio
        csv_buffer = bio.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["Parameter", "Value", "Unit", "Value_mm"])
        writer.writerow(["Trace Width (w)", f"{w_g:.4f}", unit, f"{w_mm_g:.4f}"])
        writer.writerow(["Trace Thickness (t)", f"{t_g:.4f}", unit, f"{t_mm_g:.4f}"])
        writer.writerow(["Dielectric Thickness (h)", f"{h_g:.4f}", unit, f"{h_mm_g:.4f}"])
        writer.writerow(["Trace Separation (d)", f"{d_g:.4f}", unit, f"{d_mm_g:.4f}"])
        writer.writerow(["Dielectric Constant (er)", f"{er_g:.2f}", "", ""])
        writer.writerow(["Single-Ended Z0", f"{z0_g:.2f}", "Ohm", ""])
        if is_diff:
            writer.writerow(["Differential Zd", f"{zd_g:.2f}", "Ohm", ""])
        writer.writerow(["Propagation Delay", f"{3.333*np.sqrt(er_g):.3f}", "ns/m", ""])
        csv_data = csv_buffer.getvalue()
        st.code(csv_data, language="csv")
        st.download_button("Download CSV", csv_data, file_name="cf3_parameters.csv", mime="text/csv")

with sidebar:
  st.markdown("<div style='text-align:center; color:#888; font-size:0.8rem'>Inspired by Mantaro Engineering Calculators - Built for Delft CRI/oFlex3 CF3</div>", unsafe_allow_html=True)
  st.markdown('<div class="sub-title">CRI/oFlex<sup>3</sup> CF3 Impedance Calculator</div>', unsafe_allow_html=True)
  st.markdown('<div class="sub-title">Symmetric Stripline - Polyimide &amp; Silver (Ag) - DC to 10 GHz</div>', unsafe_allow_html=True)
