import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st
st.set_page_config(page_title="量傳線設計整合平台", layout="wide")
st.title("量傳線設計整合平台")
st.markdown("""
整合功能：
1. 規格產生器
2. 低溫超導
3. 三視圖
4. 熱負載
5. 整合元件
6. 三種傳輸線規格 (CF3 / FPC / Uleam1)
7. 其它 (串擾 / 電報員 / 波導 / 低通濾波器)
""")
st.info("請由左側頁面選單選擇功能。")
