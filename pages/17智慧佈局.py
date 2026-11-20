import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st
from 量傳線設計.核心.智慧佈局 import (StriplineGeometry, draw_optimized_front_view,
                                    draw_optimized_side_view, draw_optimized_top_view,
                                    export_optimized_xlsx)

st.set_page_config(page_title="智慧佈局", layout="wide")
st.title("智慧佈局（深）")

with st.sidebar:
    spec_name = st.selectbox("規格", ["CF3", "FPC", "Uleam1"], index=0)
    _COLORS = {"CF3": ("#C9A227", "#D4A574"), "FPC": ("#C0C0C0", "#D4A574"), "Uleam1": ("#8B9CAD", "#C4956A")}
    cond_color, diel_color = _COLORS.get(spec_name, ("#C9A227", "#D4A574"))
    通道數 = st.radio("通道數", [4, 8, 16], index=1, horizontal=True)
    pitch = st.slider("Pitch (mm)", 0.5, 5.0, 2.0, 0.1)
    length = st.slider("長度 (mm)", 100, 1500, 400, 50)
    sig_width = st.slider("線寬 (μm)", 50, 500, 300, 10)
    sig_thickness = st.slider("導體厚度 (μm)", 1, 20, 5, 1)
    dielectric_thickness = st.slider("介電厚度 (μm)", 50, 300, 150, 10)
    n_layers = st.slider("介電層數 (疊構)", 1, 5, 1, 1)

geo = StriplineGeometry(w=sig_width/1000.0, t=sig_thickness, h=(dielectric_thickness*n_layers)/1000.0,
                        s=pitch, L=length, n_channels=通道數)
via_enabled = True
via_diameter = 150.0
via_density = 2.0
view = st.radio("視圖", ["前視圖", "側視圖", "上視圖", "匯出"], horizontal=True)
if view == "前視圖":
    fig = draw_optimized_front_view(geo, pitch, via_enabled, via_diameter, via_density, geo.n_channels,
                                    conductor_color=cond_color, dielectric_color=diel_color)
    st.pyplot(fig)
elif view == "側視圖":
    fig = draw_optimized_side_view(geo, pitch, length, via_enabled, via_diameter, via_density, geo.n_channels,
                                    conductor_color=cond_color, dielectric_color=diel_color)
    st.pyplot(fig)
elif view == "上視圖":
    fig = draw_optimized_top_view(geo, pitch, length, via_enabled, via_diameter, via_density, geo.n_channels,
                                  conductor_color=cond_color, dielectric_color=diel_color)
    st.pyplot(fig)
else:
    data = export_optimized_xlsx(geo, pitch, length, via_enabled, via_diameter, via_density,
                                 geo.n_channels, sig_width/1000.0, dielectric_thickness/1000.0)
    st.download_button("下載 Excel", data=data, file_name="smart.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
