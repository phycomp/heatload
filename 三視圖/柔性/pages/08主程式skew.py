from os.path import abspath, dirname
from streamlit import button, caption, checkbox, code, columns, dataframe, download_button, error, info, markdown, metric, number_input, pyplot, radio, rerun, session_state, set_page_config, sidebar, slider, spinner, subheader, success, tabs, text_input, title
from matplotlib.pyplot import close
from pandas import DataFrame
from sys import path
# 柔性線函式庫/應用程式/主程式.py
"""Streamlit 主應用程式 - FPC 全規格 + 三視圖 + Excel 匯出"""

import sys
import os
# path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# import streamlit as st
# import matplotlib.pyplot as plt
# import pandas as pd

from 核心.佈局FPC import 佈局計算器
from 核心.層FPC import 全名稱, 全參數, 全層, 計算CableWidth
from 繪圖.前視FPC import 繪製前視
from 繪圖.側視FPC import 繪製側視
from 繪圖.上視FPC import 繪製上視
from 匯出.圖規格skew import 匯出分頁, 建立層疊表格, 全規格


set_page_config(
    page_title="FPC 傳輸線三視圖系統",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== 初始化 session state =====
if '前視圖' not in session_state:
    session_state.前視圖 = None
if '側視圖' not in session_state:
    session_state.側視圖 = None
if '上視圖' not in session_state:
    session_state.上視圖 = None
if '規格類型' not in session_state:
    session_state.規格類型 = 'FPC'

# 各自獨立的參數儲存
if 'GSG參數' not in session_state:
    session_state.GSG參數 = {
        '通道數': 8,
        '訊號間距': 2.0,
        '訊號寬度um': 35,
        '線總寬': 17.0,
        '線長度': 200,
    }
# if 'FPC參數' not in session_state:
# session_state.FPC參數 = { '通道數': 8, '訊號間距': .171, '訊號寬度um': 65., '訊號厚度um': 8., '線總寬': 4.156, '線總長': 150., }


# ===== 建立佈局 =====
def 佈局從參數(規格層, 參數):
    """從參數字典建立佈局計算器"""
    狀態.code(['參數', 參數])
    return 佈局計算器(
        # 規格類型=規格類型,
        規格層=規格層,
        通道數=參數['通道數'],
        訊號寬度um=參數['訊號寬度um'],
        訊號厚度um=參數['訊號厚度um'],
        訊號單側間距um=參數['訊號單側間距um'],
        線總寬=參數['線總寬'],
        線總長=參數['線總長'],
        GroundSpace=參數['GroundSpace']
    )


# ===== 繪製所有視圖 =====
def 重新繪製所有視圖(佈局, 字型縮放):
    """重新繪製所有視圖並存入 session_state"""
    狀態.code(['佈局', 佈局.__dict__])
    session_state.前視圖 = 繪製前視(佈局, 字型縮放)
    session_state.側視圖 = 繪製側視(佈局, 字型縮放)
    session_state.上視圖 = 繪製上視(佈局, 字型縮放)

from streamlit import empty, pyplot
狀態=empty()
# ===== 側邊欄 =====
with sidebar:
    title("📐 FPC 三視圖系統")
    # markdown("---")
    
    subheader("🔀 規格選擇")
    規格類型=radio('規格類型', ['FPC', 'GSG'], horizontal=True, index=0)
    
    #col1, col2 = columns(2)
    #with col1:
    #    if button("🔵 GSG 7層", use_container_width=True, type="primary" if session_state.規格類型 == 'GSG' else "secondary"):
    #        session_state.規格類型 = 'GSG'
    #        rerun()
    #with col2:
    #    if button("🟢 FPC 12層", use_container_width=True, type="primary" if session_state.規格類型 == 'FPC' else "secondary"):
    #        session_state.規格類型 = 'FPC'
    #        rerun()
    if 規格類型:
      session_state.規格類型 = 規格類型
      規格層=session_state.規格層=全層[f'{規格類型}層']
      規格參數=session_state.規格參數=全參數[規格類型]
      規格名稱=session_state.規格名稱=全名稱.get(規格類型)  #, '未知規格'
      狀態.code(['規格參數', 規格參數])
    
    # 規格類型 = session_state.規格類型
    caption(f"當前: {規格名稱}")
    # markdown("---")
    
    subheader("⚙️ 參數設定")
    
    # 規格參數 = session_state[f"{規格類型}參數"]
    # 預設 = 全參數[規格類型]
    
    if 規格類型 == 'GSG':
        caption("📐 GSG 7層參數")
        通道數 = slider("通道數", 2, 16, 規格參數['通道數'], 2, key="gsg_ch")
        訊號間距 = slider("訊號間距 (mm)", 0.5, 5.0, 規格參數['訊號間距'], 0.1, key="gsg_pitch")
        訊號寬度um = slider("訊號寬度 (μm)", 10, 100, 規格參數['訊號寬度um'], 5, key="gsg_width")
        線總寬 = number_input("線總寬 (mm)", value=規格參數['線總寬'], step=0.5, min_value=2.0, key="gsg_total_w")
        線長度 = number_input("線長度 (mm)", value=規格參數['線長度'], step=10, min_value=50, key="gsg_length")
        
        session_state.GSG參數 = {
            '通道數': 通道數, '訊號間距': 訊號間距, '訊號寬度um': 訊號寬度um,
            '線總寬': 線總寬, '線長度': 線長度,
        }
    else:
        caption("📐 FPC 12層參數")
        通道數 = slider("通道數", 2, 16, 規格參數['通道數'], 2, key="fpc_ch")
        訊號單側間距um = slider("訊號單側間距 (um)", .05, 1., 規格參數['訊號單側間距um'], 0.01, key="fpcPitch")
        訊號寬度um = slider("訊號寬度 (μm)", 10., 100., 規格參數['訊號寬度um'], 5., key="fpcWidth")
        GroundSpace = slider("GroundSpace (μm)", 100., 200., 規格參數['GroundSpace'], 10., key="fpcGroundSpace")
        訊號厚度um = slider("訊號厚度 (μm)", 2., 10., 規格參數['訊號厚度um'], 2., key="fpcHeight")
        # 線總寬 = number_input("線總寬 (mm)", value=規格參數['線總寬'], step=0.1, min_value=1.0, key="fpcTotalW")
        線總長 = number_input("線總長 (mm)", value=規格參數['線總長'], step=10., min_value=50., key="fpcLength")
        
        線總寬=8*訊號寬度um+9*GroundSpace+8*訊號單側間距um*2
        session_state.FPC參數 = {'通道數': 通道數, '訊號單側間距um': 訊號單側間距um, '訊號寬度um': 訊號寬度um, '訊號厚度um': 訊號厚度um, '線總寬': 線總寬, '線總長': 線總長, 'GroundSpace':GroundSpace}
        
        # Cable Width 計算顯示
        if checkbox("顯示 Cable Width 計算", value=True, key="show_cable"):
            cw = 計算CableWidth()
            caption("📏 Cable Width 計算")
            code(f"""
Ground space = {cw['GroundSpace']} μm
W1 (線寬)    = {cw['W1']} μm
D1 (間距)    = {cw['D1']} μm
─────────────────────────
8 × W1        = {cw['8*W1']} μm
8 × D1 × 2    = {cw['8*D1*2']} μm
9 × GND       = {cw['9*Ground space']} μm
─────────────────────────
Cable Width   = {cw['cable_width_um']} μm
              = {cw['cable_width_mm']:.3f} mm
Pitch (SMPM)  = {cw['Pitch_SMPM_mm']:.3f} mm
            """)
    
    markdown("---")
    subheader("🔤 字型控制")
    字型縮放 = slider("字型縮放比例", 0.5, 2.0, 1.0, 0.1)
    caption(f"當前字型縮放: {字型縮放:.1f}x")
    
    # 建立佈局
    規格參數 = session_state[f"{規格類型}參數"]
    佈局 = 佈局從參數(規格層, 規格參數)
    
    markdown("---")
    subheader("📊 佈局資訊")
    狀態.code(佈局.__dict__)
    
    col1, col2 = columns(2)
    col1.metric("層數", len(佈局.規格層))
    col2.metric("總厚度", f"{佈局.線總厚um:.1f}μm")
    col1.metric("總寬度", f"{佈局.線總寬:.3f}mm")
    col2.metric("通道數", 佈局.通道數)
    
    if 規格類型 == 'FPC':
        col1.metric("H1", f"{佈局.H1:.1f}μm")
        col2.metric("H2", f"{佈局.H2:.1f}μm")


# ===== 主區域 =====
title("📐 FPC 傳輸線三視圖系統")

info(f"📌 當前規格: **{佈局.規格名稱}** | 層數: {len(佈局.規格層)} | 總長度: {佈局.線總長:.1f}mm | 總寬度: {佈局.線總寬um:.0f}μm | 總厚度: {佈局.線總厚um:.0f}μm")

# 選單
選項 = ["📐 前視圖", "📐 側視圖", "📐 上視圖", "📊 三視圖總覽", "📥 匯出 Excel"]
選取 = radio("選擇視圖", 選項, horizontal=True)

# 重新繪製所有視圖
重新繪製所有視圖(佈局, 字型縮放)

# ===== 顯示對應視圖 =====
if 選取 == "📐 前視圖":
    subheader("🔲 前視圖")
    #if session_state.前視圖:
    #    pyplot(session_state.前視圖)
    #    close(session_state.前視圖)

elif 選取 == "📐 側視圖":
    subheader("🔲 側視圖")
    if session_state.側視圖:
        pyplot(session_state.側視圖)
        close(session_state.側視圖)

elif 選取 == "📐 上視圖":
    subheader("🔲 上視圖")
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
    markdown("### 📋 Excel 分頁預覽")
    
    # 建立預覽資料
    df_規格 = DataFrame(全規格(佈局, 規格類型), columns=["類別", "參數", "規格值", "單位", "備註", "公差"])
    層疊資料 = 建立層疊表格(佈局, 規格類型)
    df_層疊 = DataFrame(層疊資料)
    
    tab1, tab2, tab3, tab4, tab5, tab6 = tabs([
        "📋 全規格表", "🔲 前視圖", "🔲 側視圖", "🔲 上視圖", "📚 層疊結構", "📏 Cable Width"
    ])
    
    with tab1:
        caption("全規格表 (Sheet 1)")
        
        # 統計摘要
        col1, col2, col3, col4 = columns(4)
        col1.metric("規格項目總數", len(df_規格))
        col2.metric("類別數", df_規格['類別'].nunique())
        col3.metric("層數", len(佈局.規格層))
        col4.metric("總厚度", f"{佈局.線總厚um:.1f}μm")
        
        dataframe(df_規格, use_container_width=True, hide_index=True)
    
    with tab2:
        caption("前視圖 (Sheet 2)")
        if session_state.前視圖:
            # print('前視圖')
            code("前視圖 (Sheet 2)")
            #pyplot(session_state.前視圖)
            #close(session_state.前視圖)
    
    with tab3:
        caption("側視圖 (Sheet 3)")
        if session_state.側視圖:
            pyplot(session_state.側視圖)
            close(session_state.側視圖)
    
    with tab4:
        caption("上視圖 (Sheet 4)")
        if session_state.上視圖:
            pyplot(session_state.上視圖)
            close(session_state.上視圖)
    
    with tab5:
        caption("層疊結構 (Sheet 5)")
        dataframe(df_層疊, use_container_width=True, hide_index=True)
        
        總厚度 = df_層疊[df_層疊['層號'] != '總計']['厚度um'].sum()
        col1, col2, col3 = columns(3)
        col1.metric("總層數", len(df_層疊) - 1)
        col2.metric("總厚度", f"{總厚度:.1f} μm")
        col3.metric("訊號層", len(df_層疊[df_層疊['功能'] == '訊號傳輸']))
    
    with tab6:
        caption("Cable Width 計算 (Sheet 6)")
        if 規格類型 == 'FPC':
            cw = 計算CableWidth()
            
            col1, col2 = columns(2)
            with col1:
                metric("Ground space", f"{cw['GroundSpace']} μm")
                metric("W1 (線寬)", f"{cw['W1']} μm")
                metric("D1 (間距)", f"{cw['D1']} μm")
            with col2:
                metric("8 × W1", f"{cw['8*W1']} μm")
                metric("8 × D1 × 2", f"{cw['8*D1*2']} μm")
                metric("9 × Ground", f"{cw['9*Ground space']} μm")
            
            success(f"**Cable Width = {cw['cable_width_um']} μm = {cw['cable_width_mm']:.3f} mm**")
            info(f"**Pitch (SMPM) = {cw['Pitch_SMPM_mm']:.3f} mm**")
            
            calc_df = DataFrame([
                {"項目": "Ground space", "計算式": "-", "數值 (μm)": cw['GroundSpace']},
                {"項目": "line: W1", "計算式": "-", "數值 (μm)": cw['W1']},
                {"項目": "space: D1", "計算式": "-", "數值 (μm)": cw['D1']},
                {"項目": "8 × W1", "計算式": "8 × W1", "數值 (μm)": cw['8*W1']},
                {"項目": "8 × D1 × 2", "計算式": "8 × D1 × 2", "數值 (μm)": cw['8*D1*2']},
                {"項目": "8W1 + 8×D1×2", "計算式": "520 + 2736", "數值 (μm)": cw['8*W1'] + cw['8*D1*2']},
                {"項目": "9 × Ground space", "計算式": "9 × Ground", "數值 (μm)": cw['9*Ground space']},
                {"項目": "Cable Width", "計算式": "3256 + 900", "數值 (μm)": cw['cable_width_um']},
                {"項目": "1×W1 + 2×D1 + GND", "計算式": "65 + 342 + 100", "數值 (μm)": cw['W1'] + 2*cw['D1'] + cw['GroundSpace']},
                {"項目": "Pitch (SMPM)", "計算式": "-", "數值 (μm)": cw['Pitch_SMPM_um']},
            ])
            dataframe(calc_df, use_container_width=True, hide_index=True)
        else:
            info("Cable Width 計算僅適用於 FPC 規格。")
    
    markdown("---")
    
    # ===== 匯出按鈕 =====
    markdown("### 📥 匯出設定")
    
    col1, col2, col3 = columns([2, 1, 1])
    with col1:
        # info(f"📐 {佈局.規格名稱} | 通道數: {佈局.通道數} | 總寬: {佈局.線總寬:.3f}mm")
        code(f"通道數: {佈局.通道數}ch | 訊號間距: {佈局.訊號間距um}μm | 線總寬: {佈局.線總寬um:.3f}μm | 線總厚: {佈局.線總厚um:.1f}μm")
    
    with col2:
        檔案名稱 = text_input(
            "檔案名稱",
            value=f"UF1_{規格類型}_{佈局.通道數}通道_{佈局.長寬高}",
            key="excel_filename"
        )
    
    with col3:
        # if button("📊 產生並下載 Excel", type="primary", use_container_width=True):
            # with spinner("正在產生 Excel 檔案，請稍候..."):
                # try:
            試算表 = 匯出分頁(
                佈局,
                規格類型,
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
