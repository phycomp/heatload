# ui/charts.py
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

def render_charts(results, summary):
    st.subheader("圖表")
    # 1. 各參數折線圖
    for name, rows in results.items():
        df = pd.DataFrame(rows)
        fig = px.line(df, x="offset", y="Zdiff", markers=True, title=f"{name} vs Zdiff")
        st.plotly_chart(fig, use_container_width=True)
    # 2. 全部同圖（normalized）
    fig = go.Figure()
    for name, rows in results.items():
        df = pd.DataFrame(rows)
        fig.add_trace(go.Scatter(x=df["offset"], y=df["rel_%"], mode="lines+markers", name=name))
    fig.update_layout(title="相對 nominal 變化 %", xaxis_title="offset", yaxis_title="rel_%")
    st.plotly_chart(fig, use_container_width=True)
    # 3. Tornado
    s = pd.DataFrame(summary)
    fig = px.bar(s, x="range", y="parameter", orientation="h", title="Tornado (Zdiff range)")
    st.plotly_chart(fig, use_container_width=True)
    # 4. 相對變化 bar
    fig = px.bar(s, x="parameter", y=["min_rel_%", "max_rel_%"], barmode="group",
                 title="相對變化 %")
    st.plotly_chart(fig, use_container_width=True)
