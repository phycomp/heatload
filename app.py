import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
st.set_page_config(page_title="量傳線設計整合平台", layout="wide", initial_sidebar_state="expanded")
st.title("量傳線設計整合平台")
st.markdown("請由左側選單選擇功能模組。")
