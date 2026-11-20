# 柔性線函式庫/應用程式/主程式.py
"""Streamlit 主應用程式 - 支援 GSG 7層 與 FPC 11層"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

from 核心.佈局計算II import 佈局計算器
from 核心.層II import 規格名稱, 預設參數
from 繪圖.前視III import 繪製前視
from 繪圖.側視 import 繪製側視
from 繪圖.上視 import 繪製上視
from 匯出.圖規格II import 匯出分頁, 建立層疊表格


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
if '規格類型' not in st.session_state:
    st.session_state.規格類型 = 'GSG'


def 規格資框(佈局):
    """建立規格DataFrame (根據規格類型動態調整)"""
    # 此函數保持不變，但會根據佈局.規格類型調整內容
    # ... (完整實作參考之前版本)
    pass


def 重新繪製所有視圖(佈局, 字型縮放):
    """重新繪製所有視圖並存入 session_state"""
    st.session_state.前視圖 = 繪製前視(佈局, 字型縮放)
    st.session_state.側視圖 = 繪製側視(佈局, 字型縮放)
    st.session_state.上視圖 = 繪製上視(佈局, 字型縮放)


# 側邊欄
with st.sidebar:
    st.title("📐 智慧三視圖")
    st.markdown("---")
    
    st.subheader("🔀 規格選擇")
    
    # 按鈕切換規格
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔵 GSG 7層", use_container_width=True, 
                     type="primary" if st.session_state.規格類型 == 'GSG' else "secondary"):
            st.session_state.規格類型 = 'GSG'
            st.rerun()
    with col2:
        if st.button("🟢 FPC 11層", use_container_width=True,
                     type="primary" if st.session_state.規格類型 == 'FPC' else "secondary"):
            st.session_state.規格類型 = 'FPC'
            st.rerun()
    
    # 顯示當前規格名稱
    目前規格 = st.session_state.規格類型
    st.caption(f"當前: {規格名稱[目前規格]}")
    st.markdown("---")
    
    st.subheader("⚙️ 參數設定")
    
    # 根據規格類型取得預設值
    預設 = 預設參數[目前規格]
    
    通道數 = st.slider("通道數", 2, 16, 8, 2)
    訊號間距 = st.slider("訊號間距 (mm)", 0.5, 5.0, 預設['訊號間距'], 0.1)
    訊號寬度um = st.slider("訊號寬度 (μm)", 10, 100, 預設['訊號寬度um'], 5)
    線總寬 = st.number_input("線總寬 (mm)", value=預設['線總寬'], step=0.5, min_value=2.0)
    線長度 = st.number_input("線長度 (mm)", value=預設['線長度'], step=10, min_value=50)
    
    st.markdown("---")
    st.subheader("🔤 字型控制")
    字型縮放 = st.slider("字型縮放比例", 0.5, 2.0, 1.0, 0.1)
    st.caption(f"當前字型縮放: {字型縮放:.1f}x")
    
    st.markdown("---")
    st.subheader("📊 佈局資訊")
    
    # 建立佈局
    佈局 = 佈局計算器(
        規格類型=目前規格,
        通道數=通道數,
        訊號間距=訊號間距,
        訊號寬度um=訊號寬度um,
        線總寬=線總寬,
        線長度=線長度
    )
    
    col1, col2 = st.columns(2)
    col1.metric("規格", 佈局.規格名稱[:8] + "...")
    col2.metric("層數", len(佈局.層定義))
    col1.metric("總厚度", f"{佈局.總厚度um}μm")
    col2.metric("總寬度", f"{佈局.線總寬:.2f}mm")
    col1.metric("通道數", 佈局.通道數)
    col2.metric("鈮鈦比例", 佈局.鈮鈦比例)

# 主區域
st.title("📐 智慧三視圖系統")

# 顯示當前規格
st.info(f"📌 當前規格: **{規格名稱[目前規格]}** | 層數: {len(佈局.層定義)} | 總厚度: {佈局.總厚度um}μm")

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
    
    # ===== 預覽 Excel 各分頁內容 =====
    st.markdown("### 📋 Excel 分頁預覽")
    
    # 建立預覽資料
    規格資料 = 建立規格表格(佈局)
    層疊資料 = 建立層疊表格(佈局)
    
    # 轉為 DataFrame
    # df_規格 = pd.DataFrame(規格資料, columns=[])
    # df_層疊 = pd.DataFrame(層疊資料)
    df_規格 = 規格資框(佈局)  # ✅ 直接使用規格資框函數
    層疊資料 = 建立層疊表格(佈局)
    df_層疊 = pd.DataFrame(層疊資料)


    # 使用 tabs 顯示各分頁預覽
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 規格表", 
        "🔲 前視圖", 
        "🔲 側視圖", 
        "🔲 上視圖", 
        "📚 層疊結構"
    ])
    
    with tab1:
        st.caption("規格表 (Sheet 1)")
        
        # 顯示邊緣間距重點標示
        st.info(f"📏 邊緣間距: 左側 {佈局.左側間距*1000:.0f}μm | 右側 {佈局.右側間距*1000:.0f}μm | 總和 {佈局.總間距*1000:.0f}μm")
        
        df_規格
        # st.dataframe(, use_container_width=True, hide_index=True)
        
        # 顯示統計摘要
        col1, col2, col3 = st.columns(3)
        col1.metric("規格項目總數", len(df_規格))
        col2.metric("類別數", df_規格['類別'].nunique())
        col3.metric("含公差項目", len(df_規格[df_規格['公差'] != '-']))
    
    with tab2:
        st.caption("前視圖 (Sheet 2)")
        if st.session_state.前視圖:
            st.pyplot(st.session_state.前視圖)
            plt.close(st.session_state.前視圖)
        else:
            st.warning("前視圖尚未生成")
    
    with tab3:
        st.caption("側視圖 (Sheet 3)")
        if st.session_state.側視圖:
            st.pyplot(st.session_state.側視圖)
            plt.close(st.session_state.側視圖)
        else:
            st.warning("側視圖尚未生成")
    
    with tab4:
        st.caption("上視圖 (Sheet 4)")
        if st.session_state.上視圖:
            st.pyplot(st.session_state.上視圖)
            plt.close(st.session_state.上視圖)
        else:
            st.warning("上視圖尚未生成")
    
    with tab5:
        st.caption("層疊結構 (Sheet 5)")
        st.dataframe(df_層疊, use_container_width=True, hide_index=True)
        
        # 層疊統計
        總厚度 = df_層疊[df_層疊['層號'] != '總計']['厚度um'].sum()
        col1, col2, col3 = st.columns(3)
        col1.metric("總層數", len(df_層疊) - 1)
        col2.metric("總厚度", f"{總厚度} μm")
        col3.metric("訊號層", len(df_層疊[df_層疊['功能'] == '訊號傳輸']))
    
    st.markdown("---")
    
    # ===== 匯出按鈕區 =====
    st.markdown("### 📥 匯出設定")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.info(f"📐 通道數: {佈局.通道數} | 總寬: {佈局.線總寬:.2f}mm | 總厚度: {佈局.總厚度um}μm")
    
    with col2:
        檔案名稱 = st.text_input(
            "檔案名稱", 
            value=f"UF1_{佈局.通道數}通道_{佈局.長寬高}",
            key="excel_filename"
        )
    
    with col3:
        #if st.button("📊 產生並下載 Excel", type="primary", use_container_width=True):
        #    with st.spinner("正在產生 Excel 檔案，請稍候..."):
        #        try:
        試算表 = 匯出分頁(
            佈局,
            st.session_state.前視圖,
            st.session_state.側視圖,
            st.session_state.上視圖,
            字型縮放
        )
        
        st.download_button(
            label=f"⬇️ 下載 {檔案名稱}.xlsx",
            data=試算表,
            file_name=f"{檔案名稱}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        st.success("✅ Excel 檔案已產生!")
        #        except Exception as e:
        #            st.error(f"❌ 產生失敗: {e}")
