# 柔性線函式庫/應用程式/主程式.py
"""Streamlit 主應用程式 - 支援 GSG 7層 與 FPC 11層 (各自獨立參數)"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

from 核心.佈局計算II import 佈局計算器
from 核心.層II import 規格名稱, 預設參數, 取得層定義
from 繪圖.前視II import 繪製前視
from 繪圖.側視 import 繪製側視
from 繪圖.上視 import 繪製上視
from 匯出.圖規格III import 匯出分頁, 建立層疊表格


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

# 各自獨立的參數儲存
if 'GSG_參數' not in st.session_state:
    st.session_state.GSG_參數 = {
        '通道數': 8,
        '訊號間距': 2.0,
        '訊號寬度um': 35,
        '線總寬': 17.0,
        '線長度': 200,
    }
if 'FPC_參數' not in st.session_state:
    st.session_state.FPC_參數 = {
        '通道數': 8,
        '訊號間距': 1.0,
        '訊號寬度um': 50,
        '線總寬': 10.0,
        '線長度': 150,
    }


def 規格資框(佈局):
    """建立規格DataFrame (根據規格類型動態調整)"""
    data = {"類別": [], "參數": [], "規格值": [], "單位": [], "備註": [], "公差": []}
    
    # 一般規格
    一般規格 = [
        ["一般規格", "產品名稱", "U-leam UF1", "", "仿照 Delft Circuits", ""],
        ["一般規格", "規格類型", 佈局.規格名稱, "", "", ""],
        ["一般規格", "通道數", 佈局.通道數, "ch", "並列通道", "±0.5"],
        ["一般規格", "通道間距", 佈局.訊號間距, "mm", "標準設計", "±0.05"],
        ["一般規格", "總寬度", f"{佈局.線總寬:.2f}", "mm", f"{佈局.通道數}ch × {佈局.訊號間距}mm", "±0.1"],
        ["一般規格", "總厚度", 佈局.總厚度um, "μm", f"{len(佈局.層定義)}層結構", "±5"],
        ["一般規格", "線長度", 佈局.線長度, "mm", "可客製化", "±1"],
        ["一般規格", "線邊緣空白", f"{佈局.邊緣:.3f}", "mm", "符合5W/10H規則", ""],
        ["一般規格", "最小彎曲半徑", 5, "mm", "動態彎曲", "-0/+1"],
    ]
    規格 = 一般規格
    
    # 層結構 (動態從層定義讀取)
    for 層 in 佈局.層定義:
        規格.append(["層結構", 層['名稱'], 層['厚度um'], "μm", 層['材料'], "±2"])
    
    # 材料規格
    材料規格 = [
        ["材料規格", "導體材料", "Ag/NbTi", "-", f"比例 {佈局.鈮鈦比例}", ""],
        ["材料規格", "介電材料", "Polyimide", "-", "低損耗", ""],
        ["材料規格", "保護層材料", "Polyimide", "-", "覆蓋層", ""],
        ["材料規格", "鈮鈦比例", 佈局.鈮鈦比例, "%", "Nb:Ti 比例", "±1"],
    ]
    規格.extend(材料規格)
    
    # 電氣規格
    電氣規格 = [
        ["電氣規格", "特性阻抗", 50, "Ω", "GSG 帶狀線設計", "±5"],
        ["電氣規格", "傳播延遲", 5.5, "ns/m", "Polyimide 介電", "±0.3"],
    ]
    規格.extend(電氣規格)
    
    # 熱性能
    熱性能 = [
        ["熱性能", "工作溫度 (最低)", -40, "°C", "最低工作溫度", ""],
        ["熱性能", "工作溫度 (最高)", 85, "°C", "最高工作溫度", ""],
    ]
    規格.extend(熱性能)
    
    # 機械規格
    機械規格 = [
        ["機械規格", "連接器", "SMA/SMP", "-", "兩端", ""],
    ]
    規格.extend(機械規格)
    
    for 項目 in 規格:
        data["類別"].append(項目[0])
        data["參數"].append(項目[1])
        data["規格值"].append(項目[2])
        data["單位"].append(項目[3])
        data["備註"].append(項目[4])
        data["公差"].append(項目[5])
    
    df = pd.DataFrame(data)
    return df


def 重新繪製所有視圖(佈局, 字型縮放):
    """重新繪製所有視圖並存入 session_state"""
    st.session_state.前視圖 = 繪製前視(佈局, 字型縮放)
    st.session_state.側視圖 = 繪製側視(佈局, 字型縮放)
    st.session_state.上視圖 = 繪製上視(佈局, 字型縮放)


def 建立佈局從參數(規格類型, 參數):
    """從參數字典建立佈局計算器"""
    return 佈局計算器(
        規格類型=規格類型,
        通道數=參數['通道數'],
        訊號間距=參數['訊號間距'],
        訊號寬度um=參數['訊號寬度um'],
        線總寬=參數['線總寬'],
        線長度=參數['線長度']
    )


# ===== 側邊欄 =====
with st.sidebar:
    st.title("📐 智慧三視圖")
    st.markdown("---")
    
    st.subheader("🔀 規格選擇")
    
    # 規格切換按鈕
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
    
    目前規格 = st.session_state.規格類型
    st.caption(f"當前: {規格名稱[目前規格]}")
    st.markdown("---")
    
    st.subheader("⚙️ 參數設定")
    
    # 根據規格類型顯示對應的參數設定
    目前參數 = st.session_state[f"{目前規格}_參數"]
    預設 = 預設參數[目前規格]
    
    # 使用頁籤方式顯示參數 (不同規格有獨立參數)
    if 目前規格 == 'GSG':
        with st.container():
            st.caption("📐 GSG 7層參數")
            通道數 = st.slider("通道數", 2, 16, 目前參數['通道數'], 2, key="gsg_ch")
            訊號間距 = st.slider("訊號間距 (mm)", 0.5, 5.0, 目前參數['訊號間距'], 0.1, key="gsg_pitch")
            訊號寬度um = st.slider("訊號寬度 (μm)", 10, 100, 目前參數['訊號寬度um'], 5, key="gsg_width")
            線總寬 = st.number_input("線總寬 (mm)", value=目前參數['線總寬'], step=0.5, min_value=2.0, key="gsg_total_w")
            線長度 = st.number_input("線長度 (mm)", value=目前參數['線長度'], step=10, min_value=50, key="gsg_length")
            
            # 儲存參數
            st.session_state.GSG_參數 = {
                '通道數': 通道數,
                '訊號間距': 訊號間距,
                '訊號寬度um': 訊號寬度um,
                '線總寬': 線總寬,
                '線長度': 線長度,
            }
    
    else:  # FPC
        with st.container():
            st.caption("📐 FPC 11層參數")
            通道數 = st.slider("通道數", 2, 16, 目前參數['通道數'], 2, key="fpc_ch")
            訊號間距 = st.slider("訊號間距 (mm)", 0.5, 5.0, 目前參數['訊號間距'], 0.1, key="fpc_pitch")
            訊號寬度um = st.slider("訊號寬度 (μm)", 10, 100, 目前參數['訊號寬度um'], 5, key="fpc_width")
            線總寬 = st.number_input("線總寬 (mm)", value=目前參數['線總寬'], step=0.5, min_value=2.0, key="fpc_total_w")
            線長度 = st.number_input("線長度 (mm)", value=目前參數['線長度'], step=10, min_value=50, key="fpc_length")
            
            # 儲存參數
            st.session_state.FPC_參數 = {
                '通道數': 通道數,
                '訊號間距': 訊號間距,
                '訊號寬度um': 訊號寬度um,
                '線總寬': 線總寬,
                '線長度': 線長度,
            }
    
    st.markdown("---")
    st.subheader("🔤 字型控制")
    字型縮放 = st.slider("字型縮放比例", 0.5, 2.0, 1.0, 0.1)
    st.caption(f"當前字型縮放: {字型縮放:.1f}x")
    
    # 建立佈局 (使用當前規格的參數)
    目前參數 = st.session_state[f"{目前規格}_參數"]
    佈局 = 建立佈局從參數(目前規格, 目前參數)
    
    st.markdown("---")
    st.subheader("📊 佈局資訊")
    
    col1, col2 = st.columns(2)
    col1.metric("規格", 佈局.規格名稱[:8] + "...")
    col2.metric("層數", len(佈局.層定義))
    col1.metric("總厚度", f"{佈局.總厚度um}μm")
    col2.metric("總寬度", f"{佈局.線總寬:.2f}mm")
    col1.metric("通道數", 佈局.通道數)
    col2.metric("鈮鈦比例", 佈局.鈮鈦比例)

# ===== 主區域 =====
st.title("📐 智慧三視圖系統")

# 顯示當前規格資訊
st.info(f"📌 當前規格: **{規格名稱[目前規格]}** | 層數: {len(佈局.層定義)} | 總厚度: {佈局.總厚度um}μm | 總寬度: {佈局.線總寬:.2f}mm")

# 選單
選項 = ["📐 前視圖", "📐 側視圖", "📐 上視圖", "📊 三視圖總覽", "📥 匯出 Excel"]
選取 = st.radio("選擇視圖", 選項, horizontal=True)

# 每次參數變更時重新繪製
重新繪製所有視圖(佈局, 字型縮放)

if 選取 == "📐 前視圖":
    st.subheader("🔲 前視圖")
    if st.session_state.前視圖:
        st.pyplot(st.session_state.前視圖)
        plt.close(st.session_state.前視圖)

elif 選取 == "📐 側視圖":
    st.subheader("🔲 側視圖")
    if st.session_state.側視圖:
        st.pyplot(st.session_state.側視圖)
        plt.close(st.session_state.側視圖)

elif 選取 == "📐 上視圖":
    st.subheader("🔲 上視圖")
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
    
    st.markdown("### 📋 Excel 分頁預覽")
    
    # 建立預覽資料
    df_規格 = 規格資框(佈局)
    層疊資料 = 建立層疊表格(佈局, 目前規格)
    df_層疊 = pd.DataFrame(層疊資料)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 規格表", 
        "🔲 前視圖", 
        "🔲 側視圖", 
        "🔲 上視圖", 
        "📚 層疊結構"
    ])
    
    with tab1:
        st.caption("規格表 (Sheet 1)")
        st.dataframe(df_規格, use_container_width=True, hide_index=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("規格項目總數", len(df_規格))
        col2.metric("類別數", df_規格[df_規格['類別'] != '']['類別'].nunique())
        col3.metric("含公差項目", len(df_規格[df_規格['公差'] != '-']))
    
    with tab2:
        st.caption("前視圖 (Sheet 2)")
        if st.session_state.前視圖:
            st.pyplot(st.session_state.前視圖)
            plt.close(st.session_state.前視圖)
    
    with tab3:
        st.caption("側視圖 (Sheet 3)")
        if st.session_state.側視圖:
            st.pyplot(st.session_state.側視圖)
            plt.close(st.session_state.側視圖)
    
    with tab4:
        st.caption("上視圖 (Sheet 4)")
        if st.session_state.上視圖:
            st.pyplot(st.session_state.上視圖)
            plt.close(st.session_state.上視圖)
    
    with tab5:
        st.caption("層疊結構 (Sheet 5)")
        st.dataframe(df_層疊, use_container_width=True, hide_index=True)
        
        總厚度 = df_層疊[df_層疊['層號'] != '總計']['厚度um'].sum()
        col1, col2, col3 = st.columns(3)
        col1.metric("總層數", len(df_層疊) - 1)
        col2.metric("總厚度", f"{總厚度} μm")
        col3.metric("訊號層", len(df_層疊[df_層疊['功能'] == '訊號傳輸']))
    
    st.markdown("---")
    
    # 匯出按鈕
    st.markdown("### 📥 匯出設定")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.info(f"📐 {佈局.規格名稱} | 通道數: {佈局.通道數} | 總寬: {佈局.線總寬:.2f}mm")
    
    with col2:
        檔案名稱 = st.text_input(
            "檔案名稱", 
            value=f"UF1_{目前規格}_{佈局.通道數}通道_{佈局.長寬高}",
            key="excel_filename"
        )
    
    with col3:
        if st.button("📊 產生並下載 Excel", type="primary", use_container_width=True):
            with st.spinner("正在產生 Excel 檔案，請稍候..."):
                try:
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
                except Exception as e:
                    st.error(f"❌ 產生失敗: {e}")
