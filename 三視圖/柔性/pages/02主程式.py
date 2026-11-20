# 柔性線函式庫/應用程式/主程式.py
"""Streamlit 主應用程式 - 智慧三視圖系統"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import matplotlib.pyplot as plt

from 核心.佈局計算 import 佈局計算器
from 繪圖.前視II import 繪製前視
from 繪圖.側視 import 繪製側視
from 繪圖.上視 import 繪製上視
from 匯出.圖規格 import 匯出分頁


st.set_page_config(
    page_title="智慧三視圖系統",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化 session state
if '前視圖' not in st.session_state:
    st.session_state.前視圖 = None
if '側視圖' not in st.session_state:
    st.session_state.側視圖 = None
if '上視圖' not in st.session_state:
    st.session_state.上視圖 = None


def 重新繪製所有視圖(佈局, 字型縮放=None):
    """重新繪製所有視圖並存入 session_state"""
    st.session_state.前視圖 = 繪製前視(佈局, 字型縮放=字型縮放)
    st.session_state.側視圖 = 繪製側視(佈局, 字型縮放)
    st.session_state.上視圖 = 繪製上視(佈局, 字型縮放)


# 側邊欄
with st.sidebar:
    st.title("📐 智慧三視圖")
    st.markdown("---")
    
    st.subheader("⚙️ 參數設定")
    通道數 = st.slider("通道數", 2, 16, 8, 2)
    訊號間距 = st.slider("訊號間距 (mm)", 0.5, 5.0, 2.0, 0.2)
    訊號寬度um = st.slider("訊號寬度 (μm)", 10, 40, 35, 5)
    線總寬 = st.number_input("線總寬 (mm)", value=17.0, step=0.5, min_value=2.0)
    線長度 = st.number_input("線長度 (mm)", value=200, step=10, min_value=50)
    
    st.markdown("---")
    st.subheader("🔤 字型控制")
    字型縮放 = st.slider("字型縮放比例", 0.5, 2.0, 1.0, 0.1)
    st.caption(f"當前字型縮放: {字型縮放:.1f}x")
    
    st.markdown("---")
    st.subheader("📊 佈局資訊")
    
    # 建立佈局
    佈局 = 佈局計算器(
        通道數=通道數,
        訊號間距=訊號間距,
        訊號寬度um=訊號寬度um,
        線總寬=線總寬,
        線長度=線長度
    )
    
    col1, col2 = st.columns(2)
    col1.metric("通道數", 佈局.通道數)
    col2.metric("總寬度", f"{佈局.線總寬:.2f}mm")
    col1.metric("總厚度", f"{佈局.總厚度um}μm")
    col2.metric("線長度", f"{佈局.線長度}mm")
    col1.metric("訊號間距", f"{佈局.訊號間距}mm")
    col2.metric("鈮鈦比例", 佈局.鈮鈦比例)

# 主區域
st.title("📐 智慧三視圖系統")

# 選單
選項 = ["📐 前視圖", "📐 側視圖", "📐 上視圖", "📊 三視圖總覽", "📥 匯出 Excel"]
選取 = st.radio("選擇視圖", 選項, horizontal=True)

# 每次參數變更時重新繪製
重新繪製所有視圖(佈局, 字型縮放)

if 選取 == "📐 前視圖":
    st.subheader("🔲 前視圖 (GSG 7層橫截面)")
    if st.session_state.前視圖:
        st.pyplot(st.session_state.前視圖)
        plt.close(st.session_state.前視圖)

elif 選取 == "📐 側視圖":
    st.subheader("🔲 側視圖 (長度方向輪廓)")
    if st.session_state.側視圖:
        st.pyplot(st.session_state.側視圖)
        plt.close(st.session_state.側視圖)

elif 選取 == "📐 上視圖":
    st.subheader("🔲 上視圖 (平面佈局)")
    if st.session_state.上視圖:
        st.pyplot(st.session_state.上視圖)
        plt.close(st.session_state.上視圖)

elif 選取 == "📊 三視圖總覽":
    st.subheader("📊 三視圖總覽")
    
    col1, col2 = st.columns(2)
    with col1:
        st.caption("前視圖")
        if st.session_state.前視圖:
            st.pyplot(st.session_state.前視圖)
            plt.close(st.session_state.前視圖)
    
    with col2:
        st.caption("側視圖")
        if st.session_state.側視圖:
            st.pyplot(st.session_state.側視圖)
            plt.close(st.session_state.側視圖)
    
    st.caption("上視圖")
    if st.session_state.上視圖:
        st.pyplot(st.session_state.上視圖)
        plt.close(st.session_state.上視圖)

else:  # 匯出 Excel
    st.subheader("📥 匯出 Excel 規格書")
    
    st.markdown("""
    ### 匯出內容包含
    
    **1. 規格表** - 一般規格、電氣規格、材料規格、熱性能、機械規格
    
    **2. 前視圖** - GSG 7層橫截面，各層標註與厚度
    
    **3. 側視圖** - 長度方向輪廓，彎曲半徑標示
    
    **4. 上視圖** - 平面佈局，通道配置
    
    **5. 層疊結構** - 完整層疊結構表
    """)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info(f"📐 通道數: {佈局.通道數} | 總寬: {佈局.線總寬:.2f}mm | 總厚度: {佈局.總厚度um}μm")
    
    with col2:
        # if st.button("📊 產生並下載 Excel", type="primary", use_container_width=True):
        #   with st.spinner("正在產生 Excel 檔案，請稍候..."):
                # try:
        試算表 = 匯出分頁(
            佈局,
            st.session_state.前視圖,
            st.session_state.側視圖,
            st.session_state.上視圖,
            字型縮放
        )
        
        st.download_button(
            label="⬇️ 下載 UF1 柔性線材規格書.xlsx",
            data=試算表,
            file_name=f"UF1_{佈局.通道數}通道_{佈局.長寬高}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        st.success("✅ Excel 檔案已產生!")
                # except Exception as e:
                    # st.error(f"❌ 產生失敗: {e}")
   
