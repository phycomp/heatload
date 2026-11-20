import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st
from 量傳線設計.核心.三視圖 import LayoutCalculator, 繪制三視, 規格資框, 層疊結構, 匯出分頁
from 量傳線設計.輸出入.excel匯出 import 試算表轉bytes

st.set_page_config(page_title="三視圖", layout="wide")
st.title("三視圖")

with st.sidebar:
    st.subheader("參數設定")
    spec_name = st.selectbox("規格", ["CF3", "FPC", "Uleam1"], index=0)
    通道數 = st.slider("通道數", 2, 16, 8, 2)
    訊號間距 = st.slider("Pitch (mm)", 0.5, 5.0, 2.0, 0.2)
    訊號寬度 = st.slider("訊號寬度 (μm)", 10, 40, 35, 5)
    線總寬 = st.slider("線總寬 (mm)", 10.0, 30.0, 17.0, 1.0)
    線長度 = st.slider("線長度 (mm)", 50.0, 500.0, 200.0, 10.0)

# 規格顏色
_SPEC_COLORS = {
    "CF3": ("#FFD700", "#C4956A"),
    "FPC": ("#C0C0C0", "#D4A574"),
    "Uleam1": ("#8B9CAD", "#C4956A"),
}
cond_color, diel_color = _SPEC_COLORS.get(spec_name, ("#FFD700", "#C4956A"))

佈局 = LayoutCalculator(通道數=通道數, 訊號間距=訊號間距, 訊號寬度=訊號寬度,
                        線總寬=線總寬, 線長度=線長度)
前視圖, 側視圖, 上視圖 = 繪制三視(佈局, conductor_color=cond_color, dielectric_color=diel_color)

menu = st.radio("選擇視圖", ["前視圖", "側視圖", "上視圖", "匯出"], horizontal=True)
if menu == "前視圖":
    st.pyplot(前視圖)
elif menu == "側視圖":
    st.pyplot(側視圖)
elif menu == "上視圖":
    st.pyplot(上視圖)
else:
    st.dataframe(規格資框(佈局))
    st.dataframe(層疊結構(佈局))
    試算表 = 匯出分頁(佈局, 前視圖, 側視圖, 上視圖, 規格=規格資框(佈局), 層疊=層疊結構(佈局))
    st.download_button("下載 Excel 規格書", data=試算表轉bytes(試算表),
                       file_name="spec.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
