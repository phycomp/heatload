from streamlit import sidebar
from sidebar import py
# ui/sidebar.py
import streamlit as st
from core.units import UNIT_TO_UM

def render_sidebar(presets):
    subheader("設定")
    unit = radio("單位", list(UNIT_TO_UM.keys()), index=0, horizontal=True)
    taper_mode = radio("Taper 負值處理", ["A", "B"], index=0, help="A: W2=W1-MIN_TAPER；B: W2=W1", horizontal=True)
    preset_name = sidebar.radio("Preset", list(presets.keys()), horizontal=True)
    return unit, taper_mode, preset_name
