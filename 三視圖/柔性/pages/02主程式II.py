from streamlit import button, caption, columns, dataframe, download_button, error, info, markdown, number_input, pyplot, radio, session_state, set_page_config, sidebar, slider, spinner, subheader, success, tabs, text_input, title, warning
from matplotlib.pyplot import close
from pandas import DataFrame
from sys import path
# 柔性線函式庫/應用程式/主程式.py
"""Streamlit 主應用程式 - 智慧三視圖系統"""

import sys
import os
# path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

from 核心.佈局計算 import 佈局計算器
from 繪圖.前視II import 繪製前視
from 繪圖.側視 import 繪製側視
from 繪圖.上視 import 繪製上視
from 匯出.圖規格II import 匯出分頁, 建立規格表格, 建立層疊表格

欄位 = ["類別", "參數", "規格值", "單位", "備註", "公差"]

set_page_config(
    page_title="智慧三視圖系統",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化 session state
if '前視圖' not in session_state:
    session_state.前視圖 = None
if '側視圖' not in session_state:
    session_state.側視圖 = None
if '上視圖' not in session_state:
    session_state.上視圖 = None


def 重新繪製所有視圖(佈局, 字型縮放):
    """重新繪製所有視圖並存入 session_state"""
    session_state.前視圖 = 繪製前視(佈局, 字型縮放=字型縮放)
    session_state.側視圖 = 繪製側視(佈局, 字型縮放)
    session_state.上視圖 = 繪製上視(佈局, 字型縮放)


# 側邊欄
傳輸線情境=['驅動', '讀取', '校正', '糾錯']
with sidebar:
    # subheader("📐 智慧三視圖")
    # markdown("---")
    subheader("⚙️ 參數設定")
    通道數 = slider("通道數", 2, 16, 8, 2)
    訊號間距 = slider("訊號間距 (mm)", 0.5, 5.0, 2.0, 0.2)
    訊號寬度um = slider("訊號寬度 (μm)", 10, 40, 35, 5)
    線總寬 = number_input("線總寬 (mm)", value=17.0, step=0.5, min_value=2.0)
    線長度 = number_input("線長度 (mm)", value=200, step=10, min_value=50)

    線情境=radio('線使用情境', 傳輸線情境, horizontal=True, index=1)
    # markdown("---")
    subheader("🔤 字型控制")
    字型縮放 = slider("字型縮放比例", 0.5, 2.0, 1.0, 0.1)
    caption(f"當前字型縮放: {字型縮放:.1f}x")

    # markdown("---")
    # subheader("📊 佈局資訊")

    # 建立佈局
    佈局 = 佈局計算器(通道數=通道數, 訊號間距=訊號間距, 訊號寬度um=訊號寬度um, 線總寬=線總寬, 線長度=線長度, 線情境=線情境)

    col1, col2 = columns(2)
    col1.metric("通道數", 佈局.通道數)
    col2.metric("總寬度", f"{佈局.線總寬:.0f}mm")
    col1.metric("總厚度", f"{佈局.總厚度um}μm")
    col2.metric("線長度", f"{佈局.線長度}mm")
    col1.metric("訊號間距", f"{佈局.訊號間距}mm")
    col2.metric("鈮鈦比例", 佈局.鈮鈦比例)

# 主區域
subheader("📐 智慧三視圖系統")

# 選單
選項 = ["📐 前視圖", "📐 側視圖", "📐 上視圖", "📊 三視圖總覽", "📥 匯出 Excel"]
選取 = radio("選擇視圖", 選項, horizontal=True)

# 每次參數變更時重新繪製
重新繪製所有視圖(佈局, 字型縮放)

if 選取 == "📐 前視圖":
    subheader("🔲 前視圖 (GSG 7層橫截面)")
    if session_state.前視圖:
        pyplot(session_state.前視圖)
        close(session_state.前視圖)

elif 選取 == "📐 側視圖":
    subheader("🔲 側視圖 (長度方向輪廓)")
    if session_state.側視圖:
        pyplot(session_state.側視圖)
        close(session_state.側視圖)

elif 選取 == "📐 上視圖":
    subheader("🔲 上視圖 (平面佈局)")
    if session_state.上視圖:
        pyplot(session_state.上視圖)
        close(session_state.上視圖)

elif 選取 == "📊 三視圖總覽":
    subheader("📊 三視圖總覽")

    col1, col2 = columns(2)
    with col1:
        caption("前視圖")
        if session_state.前視圖:
            pyplot(session_state.前視圖)
            close(session_state.前視圖)

    with col2:
        caption("側視圖")
        if session_state.側視圖:
            pyplot(session_state.側視圖)
            close(session_state.側視圖)

    caption("上視圖")
    if session_state.上視圖:
        pyplot(session_state.上視圖)
        close(session_state.上視圖)

else:  # 匯出 Excel
    subheader("📥 匯出 Excel 規格書")

    # ===== 預覽 Excel 各分頁內容 =====
    markdown("### 📋 Excel 分頁預覽")

    # 建立預覽資料
    規格資料 = 建立規格表格(佈局)
    層疊資料 = 建立層疊表格(佈局)

    # 轉為 DataFrame
    規格資框 = DataFrame(規格資料, columns=欄位)
    規格資框

    df_層疊 = DataFrame(層疊資料)

    # 使用 tabs 顯示各分頁預覽
    tab1, tab2, tab3, tab4, tab5 = tabs([
        "📋 規格表",
        "🔲 前視圖",
        "🔲 側視圖",
        "🔲 上視圖",
        "📚 層疊結構"
    ])

    with tab1:
        caption("規格表 (Sheet 1)")
        規格資框
        # dataframe(, use_container_width=True, hide_index=True)

        # 顯示統計摘要
        col1, col2, col3 = columns(3)
        col1.metric("規格項目總數", len(規格資框))
        col2.metric("類別數", 規格資框['類別'].nunique())
        col3.metric("含公差項目", len(規格資框[規格資框['公差'] != '-']))

    with tab2:
        caption("前視圖 (Sheet 2)")
        if session_state.前視圖:
            pyplot(session_state.前視圖)
            close(session_state.前視圖)
        else:
            warning("前視圖尚未生成")

    with tab3:
        caption("側視圖 (Sheet 3)")
        if session_state.側視圖:
            pyplot(session_state.側視圖)
            close(session_state.側視圖)
        else:
            warning("側視圖尚未生成")

    with tab4:
        caption("上視圖 (Sheet 4)")
        if session_state.上視圖:
            pyplot(session_state.上視圖)
            close(session_state.上視圖)
        else:
            warning("上視圖尚未生成")

    with tab5:
        caption("層疊結構 (Sheet 5)")

        # 層疊結構帶顏色標記
        def 層疊上色(df):
            """為層疊結構加上顏色標記"""
            顏色對照 = {
                '保護層下': '#E8D5C4',
                '保護層上': '#E8D5C4',
                '接地層下': '#8B9CAD',
                '接地層上': '#8B9CAD',
                '介電層下': '#C4956A',
                '介電層上': '#C4956A',
                '訊號線': '#FFD700',
            }

            styled = df.style.applymap(
                lambda x: f'background-color: {顏色對照.get(x, "white")}' if x in 顏色對照 else '',
                subset=['層名稱']
            )
            return styled

        dataframe(df_層疊, use_container_width=True, hide_index=True)

        # 層疊統計
        總厚度 = df_層疊[df_層疊['層號'] != '總計']['厚度um'].sum()
        col1, col2, col3 = columns(3)
        col1.metric("總層數", len(df_層疊) - 1)  # 扣除總計行
        col2.metric("總厚度", f"{總厚度} μm")
        col3.metric("訊號層", len(df_層疊[df_層疊['功能'] == '訊號傳輸']))

    markdown("---")

    # ===== 匯出按鈕區 =====
    markdown("### 📥 匯出設定")

    col1, col2, col3 = columns([2, 1, 1])
    with col1:
        info(f"📐 通道數: {佈局.通道數} | 總寬: {佈局.線總寬:.2f}mm | 總厚度: {佈局.總厚度um}μm")

    with col2:
        檔案名稱 = text_input(
            "檔案名稱",
            value=f"UF1_{佈局.通道數}通道_{佈局.長寬高}",
            key="excel_filename"
        )

    with col3:
        #if button("📊 產生並下載 Excel", type="primary", use_container_width=True):
        #    with spinner("正在產生 Excel 檔案，請稍候..."):
        #        try:
        試算表 = 匯出分頁(
            佈局,
            session_state.前視圖,
            session_state.側視圖,
            session_state.上視圖,
            字型縮放
        )

        download_button(
            label=f"⬇️ 下載 {檔案名稱}.xlsx",
            data=試算表,
            file_name=f"{檔案名稱}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        success("✅ Excel 檔案已產生!")
                #except Exception as e:
                #    error(f"❌ 產生失敗: {e}")
