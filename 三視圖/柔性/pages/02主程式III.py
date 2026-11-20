from streamlit import button, caption, columns, dataframe, download_button, error, info, markdown, number_input, pyplot, radio, session_state, set_page_config, sidebar, slider, spinner, subheader, success, tabs, text_input, title, warning
from matplotlib.pyplot import close
from pandas import DataFrame, concat
from sys import path
from re import findall
# 柔性線函式庫/應用程式/主程式.py
"""Streamlit 主應用程式 - 智慧三視圖系統"""

import sys
import os
path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

from 核心.佈局計算 import 佈局計算器
from 繪圖.前視III import 繪製前視
from 繪圖.側視 import 繪製側視
from 繪圖.上視 import 繪製上視
from 匯出.圖規格II import 匯出分頁, 建立規格表格, 建立層疊表格
from 核心.層II import 取得層定義


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


def 規格資框(佈局):
    """建立規格DataFrame"""
    
    data = {"類別": [], "參數": [], "規格值": [], "單位": [], "備註": [], "公差": []}
    
    # 一般規格
    general_specs = [
        ["一般性", "產品名稱", "U-leam UF1", "", "仿照 Delft Circuits", ""],
        ["一般性", "通道數", 佈局.通道數, "ch", "並列通道", ""],
        ["一般性", "通道間距", 佈局.訊號間距, "mm", "標準設計", "±0.05"],
        ["一般性", "總寬度", f"{佈局.線總寬:.2f}", "mm", f"{佈局.通道數}ch × {佈局.訊號間距}mm", "±0.1"],
        ["一般性", "總厚度", 佈局.總厚度um, "um", "7層 GSG 結構", "±5"],
        ["一般性", "總長度", 佈局.線長度, "mm", "可客製化", "±1"],
        ["一般性", "線邊緣空白", f"{佈局.邊緣間距:.3f}", "mm", "符合5W/10H規則", ""],
        ["一般性", "最小彎曲半徑", 5, "mm", "動態彎曲", ""],
    ]
    
    # 電氣規格
    electrical_specs = [
        ["電氣", "特性阻抗", 50, "Ohm", "GSG 帶狀線設計", "±2"],
        ["電氣", "頻率範圍", "DC - 18", "GHz", "微波操作", ""],
        ["電氣", "插入損耗", "< 0.5", "dB/m", "@ 10GHz", ""],
        ["電氣", "回波損耗", "> 20", "dB", "@ 10GHz", ""],
        ["電氣", "串擾隔離", "< -60", "dB", "相鄰通道", ""],
        ["電氣", "傳播延遲", "~ 5.6", "ns/m", "Polyimide 介電", "±0.2"],
    ]
    
    # 層結構
    layer_specs = [
        ["層結構", "保護層上", 15, "um", "Polyimide", "±2"],
        ["層結構", "接地層上", 5, "um", "Ag/NbTi", "±0.5"],
        ["層結構", "介電層上", 129, "um", "Polyimide", "±3"],
        ["層結構", "訊號層厚度", 佈局.訊號厚度mm * 1000, "um", "Ag/NbTi", "±0.2"],
        ["層結構", "訊號層寬度", 佈局.訊號寬度mm * 1000, "um", "Ag/NbTi", "±10"],
        ["層結構", "介電層下", 129, "um", "Polyimide", "±3"],
        ["層結構", "接地層下", 5, "um", "Ag/NbTi", "±0.5"],
        ["層結構", "保護層下", 15, "um", "Polyimide", "±2"],
    ]
    
    # 材料規格
    material_specs = [
        ["材料", "導體材料", "Ag / NbTi", "", "銀/鈮鈦超導", ""],
        ["材料", "介電材料", "Polyimide", "", "聚酰亞胺", ""],
        ["材料", "鈮鈦比例", 佈局.鈮鈦比例, "%", "Nb:Ti 比例", "±1"],
        ["材料", "鈮鈦超導轉變溫度", "9.8", "K", "超導臨界溫度", "±0.1"],
        ["材料", "鈮鈦臨界電流密度", "2.5 × 10⁵", "A/cm²", "@ 4.2K, 5T", "±0.3 × 10⁵"],
        ["材料", "導體電阻率 (Ag)", 1.59, "μΩ·cm", "@ 300K", ""],
        ["材料", "導體電阻率 (Ag)", 0.3, "μΩ·cm", "@ 4.2K", "RRR > 100"],
        ["材料", "導體電阻率 (NbTi)", 50, "μΩ·cm", "@ 300K", ""],
        ["材料", "導體電阻率 (NbTi)", 0.5, "μΩ·cm", "@ 10K", "正常態"],
    ]

    # 熱性能
    thermal_specs = [
        ["熱性能", "熱負載 (Ag)", "< 125", "μW/ch", "@ 4-40K, L=0.2m", ""],
        ["熱性能", "熱負載 (NbTi)", "~ 20", "nW/ch", "@ 4K-9.8K, L=0.2m", ""],
        ["熱性能", "操作溫區", "4K~9.8K", "K", "4K 至 9.8K", ""],
    ]

    # 機械規格
    mechanical_specs = [
        ["機械", "連接器類型", "SMA (f) / SMP (m)", "", "直角/直線", ""],
        ["機械", "真空洩漏率", "< 10⁻⁶", "mbar·L/s", "整合式穿通", ""],
        ["機械", "彎曲壽命", "> 1000", "cycles", "R=5mm", ""],
        ["機械", "拉伸強度", "> 50", "N", "軸向拉力", ""],
        ["機械", "楊氏模量 (Polyimide)", "2.5", "GPa", "", ""],
        ["機械", "密度 (Polyimide)", "1.42", "g/cm³", "", ""],
    ]
   
    # 合併所有規格
    全規格 = (general_specs + electrical_specs + layer_specs + 
              material_specs + thermal_specs + mechanical_specs)
    
    for spec in 全規格:
        data["類別"].append(spec[0])
        data["參數"].append(spec[1])
        data["規格值"].append(spec[2])
        data["單位"].append(spec[3])
        data["備註"].append(spec[4])
        data["公差"].append(spec[5])
    
    # 取得類別順序（保留原始順序，去除重複）
    def 得出順序(列):
        新列 = []
        for 值 in 列:
            if 值 not in 新列:
                新列.append(值)
        return 新列
    
    類別順序 = 得出順序(data["類別"])
    
    # 建立 DataFrame 列表
    df_list = []
    for category in 類別順序:
        if category:
            mask = [c == category for c in data["類別"]]
            cat_df = DataFrame({
                "類別": [category] + [""] * (sum(mask) - 1),
                "參數": [data["參數"][i] for i in range(len(data["參數"])) if mask[i]],
                "規格值": [data["規格值"][i] for i in range(len(data["規格值"])) if mask[i]],
                "單位": [data["單位"][i] for i in range(len(data["單位"])) if mask[i]],
                "備註": [data["備註"][i] for i in range(len(data["備註"])) if mask[i]],
                "公差": [data["公差"][i] for i in range(len(data["公差"])) if mask[i]],
            })
            df_liappend(cat_df)
            # 加入分隔行（類別之間）
            if category != 類別順序[-1]:
                sep_df = DataFrame([["", "", "", "", "", ""]], 
                                     columns=["類別", "參數", "規格值", "單位", "備註", "公差"])
                df_liappend(sep_df)
    
    df = concat(df_list, ignore_index=True)
    return df


def 重新繪製所有視圖(佈局, 字型縮放):
    """重新繪製所有視圖並存入 session_state"""
    session_state.前視圖 = 繪製前視(佈局, 字型縮放, 層定義=層疊構)
    session_state.側視圖 = 繪製側視(佈局, 字型縮放)
    session_state.上視圖 = 繪製上視(佈局, 字型縮放)
from streamlit import empty, pyplot
狀態=empty()
with sidebar: # 側邊欄
    # markdown("---")
    
    subheader("⚙️ 參數設定")
    通道數 = slider("通道數", 2, 16, 8, 2)
    訊號間距 = slider("訊號間距 (mm)", 0.5, 5.0, 2.0, 0.2)
    訊號寬度um = slider("訊號寬度 (μm)", 10, 40, 35, 5)
    線總寬 = number_input("線總寬 (mm)", value=17.0, step=0.5, min_value=2.0)
    線長度 = number_input("線長度 (mm)", value=200, step=10, min_value=50)
    
    # markdown("---")
    subheader("🔤 字型控制")
    字型縮放 = slider("字型縮放比例", 0.5, 2.0, 1.0, 0.1)
    caption(f"當前字型縮放: {字型縮放:.1f}x")
    
    # markdown("---")
    subheader("📊 佈局資訊")
    
    # 建立佈局
    佈局 = 佈局計算器(
        通道數=通道數,
        訊號間距=訊號間距,
        訊號寬度um=訊號寬度um,
        線總寬=線總寬,
        線長度=線長度
    )
    層疊構=["🔵 GSG 7層", "🟢 FPC 11層"]
    疊=radio('層疊構', 層疊構, horizontal=True, index=0)
    if 疊:
      疊=findall('\w+', 疊)[0]
      層疊構=取得層定義(規格類型=疊)   #取得層定義(規格類型='GSG')
      狀態.code(層疊構)

    col1, col2 = columns(2)
    col1.metric("通道數", 佈局.通道數)
    col2.metric("總寬度", f"{佈局.線總寬:.2f}mm")
    col1.metric("總厚度", f"{佈局.總厚度um}μm")
    col2.metric("線長度", f"{佈局.線長度}mm")
    col1.metric("訊號間距", f"{佈局.訊號間距}mm")
    col2.metric("鈮鈦比例", 佈局.鈮鈦比例)

# 主區域

# 選單
選項 = ["📐 前視圖", "📐 側視圖", "📐 上視圖", "📊 三視圖總覽", "📥 匯出 Excel"]
選取 = radio("選擇視圖", 選項, horizontal=True)

# 每次參數變更時重新繪製
重新繪製所有視圖(佈局, 字型縮放)

if 選取 == "📐 前視圖":
    subheader("🔲 前視圖 (GSG 7層橫截面)")
    if session_state.前視圖:
        pyplot(session_state.前視圖)
        # close(session_state.前視圖)

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
    # df_規格 = DataFrame(規格資料, columns=[])
    # df_層疊 = DataFrame(層疊資料)
    df_規格 = 規格資框(佈局)  # ✅ 直接使用規格資框函數
    層疊資料 = 建立層疊表格(佈局)
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
        
        # 顯示邊緣間距重點標示
        info(f"📏 邊緣間距: 左側 {佈局.左側間距*1000:.0f}μm | 右側 {佈局.右側間距*1000:.0f}μm | 總和 {佈局.總間距*1000:.0f}μm")
        
        df_規格
        # dataframe(, use_container_width=True, hide_index=True)
        
        # 顯示統計摘要
        col1, col2, col3 = columns(3)
        col1.metric("規格項目總數", len(df_規格))
        col2.metric("類別數", df_規格['類別'].nunique())
        col3.metric("含公差項目", len(df_規格[df_規格['公差'] != '-']))
    
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
        dataframe(df_層疊, use_container_width=True, hide_index=True)
        
        # 層疊統計
        總厚度 = df_層疊[df_層疊['層號'] != '總計']['厚度um'].sum()
        col1, col2, col3 = columns(3)
        col1.metric("總層數", len(df_層疊) - 1)
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
        #        except Exception as e:
        #            error(f"❌ 產生失敗: {e}")
with sidebar:
    subheader("📐 智慧三視圖")
    # title("📐 智慧三視圖系統")
