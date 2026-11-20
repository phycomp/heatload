from streamlit import button, columns, markdown, number_input, plotly_chart, radio, rerun, selectbox, session_state, set_page_config, sidebar, slider
from numpy import fill_diagonal, max, mean, pi, sqrt, zeros
from plotly.graph_objects import Figure, Scatter, Scatter3d
from plotly.subplots import make_subplots
from dataclasses import dataclass

#import streamlit as st
#import numpy as np
#import plotly.graph_objects as go
#import plotly.express as px
#import pandas as pd
#from typing import List, Dict

set_page_config(page_title="Quantum Simulator Pro", page_icon="⚛️", layout="wide")

# ==========================================
# 主題系統
# ==========================================

THEMES = {
    'dark': {
        'bg': '#0e1117', 'bg_sec': '#1a1d24', 'text': '#fafafa', 'text_sec': '#a0a0a0',
        'accent': '#00d4ff', 'accent_sec': '#00ff88', 'warn': '#ffaa00', 'danger': '#ff006e',
        'gradient': 'linear-gradient(90deg, #00d4ff, #7b2cbf, #ff006e)',
        'card': 'rgba(26, 29, 36, 0.8)', 'border': 'rgba(0, 212, 255, 0.2)',
        'shadow': '0 8px 32px rgba(0, 212, 255, 0.1)', 'grid': 'rgba(255,255,255,0.1)',
        'plot_bg': 'rgba(0,0,0,0)', 'qubit_cols': ['#00d4ff', '#00ff88', '#ff006e']
    },
    'light': {
        'bg': '#ffffff', 'bg_sec': '#f5f5f5', 'text': '#1a1a2e', 'text_sec': '#4a4a6a',
        'accent': '#0066cc', 'accent_sec': '#00aa44', 'warn': '#ff8800', 'danger': '#cc0044',
        'gradient': 'linear-gradient(90deg, #0066cc, #663399, #cc0066)',
        'card': 'rgba(255, 255, 255, 0.9)', 'border': 'rgba(0, 102, 204, 0.2)',
        'shadow': '0 8px 32px rgba(0, 102, 204, 0.1)', 'grid': 'rgba(0,0,0,0.1)',
        'plot_bg': 'rgba(255,255,255,0)', 'qubit_cols': ['#0066cc', '#00aa44', '#cc0066']
    }
}

def get_theme():
    if 'theme' not in session_state:
        session_state['theme'] = 'dark'
    return THEMES[session_state['theme']]

def toggle_theme():
    session_state['theme'] = 'light' if session_state.get('theme', 'dark') == 'dark' else 'dark'
    rerun()

def gen_css(t):
    is_dark = session_state.get('theme', 'dark') == 'dark'
    return f"""
    <style>
        .stApp {{ background-color: {t['bg']}; }}
        .neon-title {{ font-size: 2.2rem; font-weight: bold; background: {t['gradient']}; 
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }}
        .neon-sub {{ font-size: 1rem; color: {t['text_sec']}; text-align: center; margin-bottom: 2rem; }}
        .glass-card {{ background: {t['card']}; backdrop-filter: blur(10px); border: 1px solid {t['border']}; 
        border-radius: 12px; padding: 1rem; text-align: center; transition: all 0.3s ease; }}
        .glass-card:hover {{ border-color: {t['accent']}; box-shadow: 0 0 20px {t['accent']}40; }}
        .glass-card h3 {{ color: {t['accent']}; font-size: 1.8rem; margin: 0; text-shadow: 0 0 10px {t['accent']}30; }}
        .glass-card p {{ color: {t['text_sec']}; font-size: 0.85rem; margin: 0.3rem 0 0 0; }}
        .section-bar {{ background: linear-gradient(90deg, {t['accent']}20, transparent); 
        border-left: 3px solid {t['accent']}; border-radius: 6px; padding: 0.8rem 1rem; 
        margin: 1rem 0; color: {t['text']}; font-weight: 500; }}
        .status-good {{ background: linear-gradient(135deg, {t['accent_sec']}15, {t['accent']}05); 
        border: 1px solid {t['accent_sec']}; border-radius: 10px; padding: 1rem; color: {t['text']}; }}
        .status-good h4 {{ color: {t['accent_sec']}; margin: 0 0 0.5rem 0; }}
        .status-warn {{ background: linear-gradient(135deg, {t['warn']}15, {t['danger']}05); 
        border: 1px solid {t['warn']}; border-radius: 10px; padding: 1rem; color: {t['text']}; }}
        .status-warn h4 {{ color: {t['warn']}; margin: 0 0 0.5rem 0; }}
        .info-box {{ background: linear-gradient(135deg, {t['accent']}10, {t['accent']}05); 
        border: 1px solid {t['border']}; border-radius: 12px; padding: 1.2rem; color: {t['text']}; }}
        .stButton > button {{ background: {t['accent']}; color: {'#0e1117' if is_dark else '#ffffff'}; 
        border: none; border-radius: 12px; padding: 0.75rem 2rem; font-weight: 600; box-shadow: {t['shadow']}; }}
        .stTabs [data-baseweb="tab-list"] {{ background-color: {t['card']}; border-radius: 12px; padding: 0.5rem; }}
        .stTabs [data-baseweb="tab"] {{ background-color: transparent; color: {t['text_sec']}; border-radius: 8px; }}
        .stTabs [aria-selected="true"] {{ background: {t['accent']}; color: {'#0e1117' if is_dark else '#ffffff'}; font-weight: 600; }}
    </style>
    """

# ==========================================
# 核心類別
# ==========================================

@dataclass
class Qubit:
    id: int
    x: float
    y: float
    z: float
    freq: float
    layer: int
    params: Dict

class UnifiedSimulator:
    TYPES = {
        'Transmon': {'freq': 5.0, 'anharm': -0.3, 'size': 0.4, 'g_max': 50e6},
        'Fluxonium': {'freq': 0.5, 'anharm': 1.5, 'size': 0.6, 'g_max': 30e6},
        'Quarton': {'freq': 4.0, 'anharm': -1.2, 'size': 0.35, 'g_max': 80e6}
    }
    
    def __init__(self, mode: str, config: Dict):
        self.mode, self.config, self.qubits = mode, config, []
        self._build()
        self._compute()
    
    def _build(self):
        cfg, params, qid = self.config, self.TYPES[self.config['qubit_type']], 0
        for layer in range(cfg.get('n_layers', 1)):
            z = layer * cfg.get('layer_spacing', 0) if self.mode.startswith('3D') else 0
            for row in range(cfg['rows']):
                for col in range(cfg['cols']):
                    freq = params['freq'] + 0.1 * ((row + col + layer) % 2)
                    self.qubits.append(Qubit(qid, col*cfg['spacing'], row*cfg['spacing'], z, freq, layer, params))
                    qid += 1
        self.n_qubits = len(self.qubits)
    
    def _dist(self, q1, q2):
        return sqrt((q1.x-q2.x)**2 + (q1.y-q2.y)**2 + (q1.z-q2.z)**2)
    
    def _compute(self):
        n = self.n_qubits
        self.matrices = {}
        if self.mode.startswith('2D'):
            self.matrices['crosstalk'] = zeros((n, n))
            for i, q1 in enumerate(self.qubits):
                for j, q2 in enumerate(self.qubits):
                    if i < j:
                        d = self._dist(q1, q2)
                        g = q1.params['g_max'] * (q1.params['size'] / d) ** 3
                        self.matrices['crosstalk'][i,j] = g / 1e9
                        self.matrices['crosstalk'][j,i] = g / 1e9
        else:
            self.matrices['zz'] = zeros((n, n))
            for i, q1 in enumerate(self.qubits):
                for j, q2 in enumerate(self.qubits):
                    if i < j:
                        d = self._dist(q1, q2)
                        g = q1.params['g_max'] * (q1.params['size'] / d) ** 3
                        if q1.layer != q2.layer:
                            g *= 0.3
                        delta = abs(q1.freq - q2.freq) * 2 * pi * 1e9
                        alpha1 = abs(q1.params['anharm']) * 2 * pi * 1e9
                        alpha2 = abs(q2.params['anharm']) * 2 * pi * 1e9
                        if delta < 1e6:
                            delta = 1e6
                        num = 2 * g**2 * (alpha1 + alpha2)
                        den = delta**2 - ((alpha1 + alpha2)/2)**2
                        zz = num / den if abs(den) > 1e10 else 1e3
                        self.matrices['zz'][i,j] = abs(zz) / 1e3
                        self.matrices['zz'][j,i] = abs(zz) / 1e3
    
    def stats(self):
        if self.mode.startswith('2D'):
            ct = self.matrices['crosstalk'].copy()
            fill_diagonal(ct, 0)
            return {'max': max(ct), 'mean': mean(ct[ct > 0])}
        else:
            zz = self.matrices['zz'].copy()
            fill_diagonal(zz, 0)
            intra = [zz[i,j] for i in range(self.n_qubits) for j in range(i+1, self.n_qubits) if self.qubits[i].layer == self.qubits[j].layer]
            inter = [zz[i,j] for i in range(self.n_qubits) for j in range(i+1, self.n_qubits) if self.qubits[i].layer != self.qubits[j].layer]
            return {'max': max(zz), 'mean': mean(zz[zz > 0]), 'intra': mean(intra) if intra else 0, 'inter': mean(inter) if inter else 0}

def plot_2d(sim, t):
    fig = Figure()
    for q in sim.qubits:
        fig.add_trace(Scatter(x=[q.x], y=[q.y], mode='markers+text',
                                marker=dict(size=40, color=t['accent'], line=dict(width=2, color='white')),
                                text=str(q.id), textposition="middle center", textfont=dict(size=10, color='white')))
    fig.update_layout(paper_bgcolor=t['plot_bg'], plot_bgcolor=t['plot_bg'],
                     xaxis=dict(color=t['text'], gridcolor=t['grid']),
                     yaxis=dict(color=t['text'], gridcolor=t['grid']), showlegend=False, height=500)
    return fig

def plot_3d(sim, t):
    fig = Figure()
    for layer in range(sim.config.get('n_layers', 1)):
        qs = [q for q in sim.qubits if q.layer == layer]
        fig.add_trace(Scatter3d(x=[q.x for q in qs], y=[q.y for q in qs], z=[q.z for q in qs],
                                    mode='markers+text', marker=dict(size=6, color=t['qubit_cols'][layer % 3]),
                                    text=[str(q.id) for q in qs], name=f'Layer {layer}'))
    fig.update_layout(scene=dict(xaxis=dict(color=t['text']), yaxis=dict(color=t['text']), zaxis=dict(color=t['text'])),
                     paper_bgcolor=t['plot_bg'], height=600)
    return fig

#def main():
t = get_theme()
markdown(gen_css(t), unsafe_allow_html=True)

# 標題與主題切換
col_title, col_toggle = columns([6, 1])
with col_title:
    markdown('<div class="neon-title">⚛️ Quantum Simulator Pro</div>', unsafe_allow_html=True)
    markdown('<div class="neon-sub">2D/3D Crosstalk & ZZ Coupling Analysis</div>', unsafe_allow_html=True)
with col_toggle:
    icon = '🌙' if session_state.get('theme', 'dark') == 'dark' else '☀️'
    if button(icon, help=f"Switch to {'Light' if session_state.get('theme') == 'dark' else 'Dark'} Mode"):
        toggle_theme()

with sidebar:
    markdown(f"### 🎛️ Mode ({session_state.get('theme', 'dark').upper()})")
    mode = radio("", ['2D Static', '3D ZZ'], format_func=lambda x: f"{'📱' if x.startswith('2D') else '🧊'} {x}")
    markdown("---")
    markdown("### ⚙️ Config")
    qtype = selectbox("Qubit", list(UnifiedSimulator.TYPES.keys()))
    c1, c2 = columns(2)
    with c1: rows = number_input("Rows", 2, 10, 3)
    with c2: cols = number_input("Cols", 2, 10, 3)
    spacing = slider("Spacing (mm)", 0.5, 3.0, 1.0, 0.1)
    cfg = {'qubit_type': qtype, 'rows': rows, 'cols': cols, 'spacing': spacing, 'n_layers': 1}
    if mode == '3D ZZ':
        cfg['n_layers'] = slider("Layers", 1, 5, 2)
        cfg['layer_spacing'] = slider("Gap (mm)", 0.01, 0.5, 0.05, 0.01)
    #if button("🚀 Compute", use_container_width=True):
    session_state['sim'] = UnifiedSimulator(mode.replace(' ', '_').lower(), cfg)

if 'sim' in session_state:
    sim = session_state['sim']
    stats = sim.stats()
    markdown('<div class="section-bar">📊 Results</div>', unsafe_allow_html=True)
    
    if mode == '2D Static':
        c1, c2 = columns(2)
        with c1: markdown(f'<div class="glass-card"><h3>{stats["max"]:.4f}</h3><p>Max Crosstalk</p></div>', unsafe_allow_html=True)
        with c2: markdown(f'<div class="glass-card"><h3>{stats["mean"]:.4f}</h3><p>Mean Crosstalk</p></div>', unsafe_allow_html=True)
        if stats['max'] < 0.02: markdown('<div class="status-good"><h4>✅ Excellent</h4><p>Low crosstalk</p></div>', unsafe_allow_html=True)
        elif stats['max'] < 0.05: markdown('<div class="status-good"><h4>✓ Good</h4><p>Acceptable levels</p></div>', unsafe_allow_html=True)
        else: markdown('<div class="status-warn"><h4>⚠️ Warning</h4><p>High crosstalk</p></div>', unsafe_allow_html=True)
        markdown('<div class="section-bar">🎨 Layout</div>', unsafe_allow_html=True)
        plotly_chart(plot_2d(sim, t), use_container_width=True)
    else:
        c1, c2, c3, c4 = columns(4)
        for col, (k, l) in zip([c1,c2,c3,c4], [('max','Max ZZ'),('mean','Mean ZZ'),('intra','Intra'),('inter','Inter')]):
            with col: markdown(f'<div class="glass-card"><h3>{stats[k]:.2f}</h3><p>{l} (kHz)</p></div>', unsafe_allow_html=True)
        if stats['max'] < 10: markdown('<div class="status-good"><h4>✅ Excellent ZZ</h4><p>Well controlled</p></div>', unsafe_allow_html=True)
        elif stats['max'] < 50: markdown('<div class="status-good"><h4>✓ Good ZZ</h4><p>Acceptable</p></div>', unsafe_allow_html=True)
        else: markdown('<div class="status-warn"><h4>⚠️ High ZZ</h4><p>Needs attention</p></div>', unsafe_allow_html=True)
        markdown('<div class="section-bar">🎨 3D Layout</div>', unsafe_allow_html=True)
        plotly_chart(plot_3d(sim, t), use_container_width=True)
else:
    markdown('<div class="info-box"><h3>👋 Welcome</h3><p>Configure and click Compute to start analysis.</p></div>', unsafe_allow_html=True)
#if __name__ == "__main__": main()
