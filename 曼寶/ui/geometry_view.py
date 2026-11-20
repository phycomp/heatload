# ui/geometry_view.py
import plotly.graph_objects as go
import streamlit as st
from core.units import from_um

def render_geometry(nominal_um, unit, show_dims=True, show_grid=False):
    """
    nominal_um: dict，鍵為 H1, Er1, W1, W2, S1, T1，單位 µm
    unit: 顯示單位
    """
    H1 = from_um(nominal_um["H1"], unit)
    W1 = from_um(nominal_um["W1"], unit)
    W2 = from_um(nominal_um["W2"], unit)
    S1 = from_um(nominal_um["S1"], unit)
    T1 = from_um(nominal_um["T1"], unit)
    Er1 = nominal_um["Er1"]

    # 總寬度：左右各留 margin
    margin = max(W1, W2, S1) * 0.6
    total_width = margin + W1 + S1 + W2 + margin
    x0 = margin
    x1 = x0 + W1
    x2 = x1 + S1
    x3 = x2 + W2

    # 基板
    substrate = go.Scatter(
        x=[0, total_width, total_width, 0, 0],
        y=[0, 0, H1, H1, 0],
        fill="toself",
        fillcolor="rgba(180, 200, 230, 0.45)",
        line=dict(color="steelblue", width=1),
        name=f"Substrate Er={Er1}",
        hoverinfo="skip",
    )

    # Trace 1
    trace1 = go.Scatter(
        x=[x0, x1, x1, x0, x0],
        y=[H1, H1, H1 + T1, H1 + T1, H1],
        fill="toself",
        fillcolor="rgba(200, 80, 80, 0.75)",
        line=dict(color="darkred", width=1),
        name=f"Trace 1 (W1={W1:.3f} {unit})",
        hoverinfo="skip",
    )

    # Trace 2
    trace2 = go.Scatter(
        x=[x2, x3, x3, x2, x2],
        y=[H1, H1, H1 + T1, H1 + T1, H1],
        fill="toself",
        fillcolor="rgba(200, 80, 80, 0.75)",
        line=dict(color="darkred", width=1),
        name=f"Trace 2 (W2={W2:.3f} {unit})",
        hoverinfo="skip",
    )

    # Ground plane
    ground = go.Scatter(
        x=[0, total_width],
        y=[0, 0],
        mode="lines",
        line=dict(color="black", width=3),
        name="Ground",
        hoverinfo="skip",
    )

    # 尺寸標註
    annotations = []
    if show_dims:
        # H1
        annotations.append(dict(
            x=-margin * 0.25, y=H1 / 2,
            text=f"H1 = {H1:.3f} {unit}",
            showarrow=False, textangle=-90,
            font=dict(size=11, color="black"),
        ))
        # W1
        annotations.append(dict(
            x=(x0 + x1) / 2, y=H1 + T1 + T1 * 0.6,
            text=f"W1 = {W1:.3f} {unit}",
            showarrow=False, font=dict(size=11, color="darkred"),
        ))
        # W2
        annotations.append(dict(
            x=(x2 + x3) / 2, y=H1 + T1 + T1 * 0.6,
            text=f"W2 = {W2:.3f} {unit}",
            showarrow=False, font=dict(size=11, color="darkred"),
        ))
        # S1
        annotations.append(dict(
            x=(x1 + x2) / 2, y=H1 + T1 * 0.5,
            text=f"S1 = {S1:.3f} {unit}",
            showarrow=False, font=dict(size=11, color="green"),
        ))
        # T1
        annotations.append(dict(
            x=x3 + margin * 0.3, y=H1 + T1 / 2,
            text=f"T1 = {T1:.3f} {unit}",
            showarrow=False, font=dict(size=11, color="darkred"),
        ))
        # Er1
        annotations.append(dict(
            x=total_width / 2, y=H1 / 2,
            text=f"Er1 = {Er1}",
            showarrow=False, font=dict(size=12, color="steelblue"),
        ))
        # Taper
        taper = W1 - W2
        annotations.append(dict(
            x=total_width / 2, y=-H1 * 0.15,
            text=f"Taper = W1 - W2 = {taper:.3f} {unit}",
            showarrow=False, font=dict(size=11, color="purple"),
        ))

    fig = go.Figure(data=[substrate, trace1, trace2, ground])
    fig.update_layout(
        title="Edge-Coupled Surface Microstrip 橫截面",
        xaxis=dict(title=f"x ({unit})", scaleanchor="y", scaleratio=1,
                   showgrid=show_grid, zeroline=False),
        yaxis=dict(title=f"y ({unit})", showgrid=show_grid, zeroline=False),
        annotations=annotations,
        legend=dict(orientation="h", y=-0.15),
        height=520,
        margin=dict(l=40, r=40, t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)
    return fig
