import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st
from 量傳線設計.核心.多層結構 import StriplineGeometry, 立體透視, 微帶動態橫截面, 立體示意圖

st.set_page_config(page_title="多層結構", layout="wide")
st.title("多層結構")

with st.sidebar:
    spec_name = st.selectbox("規格", ["CF3", "FPC", "Uleam1"], index=0)
    _COLORS = {"CF3": ("#D4AF37", "#C4B49A"), "FPC": ("#C0C0C0", "#D4A574"), "Uleam1": ("#8B9CAD", "#C4B49A")}
    cond_color, diel_color = _COLORS.get(spec_name, ("#D4AF37", "#C4B49A"))
    n_channels = st.radio("通道數", [4, 8, 16], index=1, horizontal=True)
    pitch = st.slider("Pitch (mm)", 0.5, 5.0, 2.0, 0.1)
    length = st.slider("長度 (mm)", 100, 1500, 400, 50)
    sig_width = st.slider("線寬 (μm)", 50, 500, 300, 10)
    sig_thickness = st.slider("導體厚度 (μm)", 1, 20, 5, 1)
    dielectric_thickness = st.slider("介電厚度 (μm)", 50, 300, 150, 10)
    n_layers = st.slider("介電層數 (疊構)", 1, 5, 1, 1)
    via_enabled = st.checkbox("Via Stitching", value=True)
    via_density = st.slider("Via 密度", 0.5, 5.0, 2.0, 0.1)
    via_diameter = st.slider("Via 直徑 (μm)", 50, 300, 150, 10)

geo = StriplineGeometry(w=sig_width/1000.0, t=sig_thickness, h=(dielectric_thickness*n_layers)/1000.0,
                        s=pitch, L=length, n_channels=n_channels)
view = st.radio("視圖", ["立體透視", "微帶橫截面", "立體示意圖"], horizontal=True)
if view == "立體透視":
    fig = 立體透視(geo, pitch, length, n_channels, conductor_color=cond_color, dielectric_color=diel_color)
elif view == "微帶橫截面":
    fig = 微帶動態橫截面(geo, pitch, via_enabled, via_diameter, via_density, n_channels, conductor_color=cond_color, dielectric_color=diel_color)
else:
    fig = 立體示意圖(geo, pitch, length, n_channels, conductor_color=cond_color, dielectric_color=diel_color)
st.pyplot(fig)
