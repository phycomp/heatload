from streamlit import button, caption, columns, dataframe, download_button, error, expander, info, markdown, metric, number_input, progress, rerun, radio, session_state, set_page_config, sidebar, slider, spinner, subheader, success#, title
from pandas import DataFrame
from sys import path
# 柔性線函式庫/應用程式/驗證平台.py
"""Streamlit 驗證平台 - Delft cri/oFlex3 規格驗證 (完整版)"""

import sys
# import os
# path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# import streamlit as st
# import pandas as pd

from 核心.佈局計算II import 佈局計算器
from 核心.層II import 規格名稱, 預設參數
from 驗證.驗證器 import 執行完整驗證
from 驗證.電氣計算 import (計算特性阻抗, 計算傳播延遲, 計算插入損耗,
                          計算衰減頻譜, 計算串擾)
from 驗證.規格基準 import 取得原廠規格, 列出非官方規格
from 驗證.報告匯出 import 匯出驗證報告


set_page_config(
    page_title="Delft cri/oFlex3 驗證平台",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"
)

if '規格類型' not in session_state:
    session_state.規格類型 = 'GSG'


# ===== 側邊欄 =====
with sidebar:
    subheader("✅ 驗證平台")
    caption("Delft cri/oFlex3 規格驗證")
    markdown("---")
    
    subheader("🔀 規格選擇")
    
    col1, col2 = columns(2)
    with col1:
        if button("🔵 GSG 7層", use_container_width=True,
                     type="primary" if session_state.規格類型 == 'GSG' else "secondary"):
            session_state.規格類型 = 'GSG'
            rerun()
    with col2:
        if button("🟢 FPC 11層", use_container_width=True,
                     type="primary" if session_state.規格類型 == 'FPC' else "secondary"):
            session_state.規格類型 = 'FPC'
            rerun()
    
    目前規格 = session_state.規格類型
    caption(f"當前: {規格名稱[目前規格]}")
    # markdown("---")
    
    subheader("⚙️ 待驗證參數")
    
    預設 = 預設參數[目前規格]
    
    通道數 = slider("通道數", 2, 16, 8, 2)
    訊號間距 = slider("訊號間距 (mm)", 0.5, 5.0, 預設['訊號間距'], 0.1)
    訊號寬度um = slider("訊號寬度 (μm)", 10, 100, 預設['訊號寬度um'], 5)
    線總寬 = number_input("線總寬 (mm)", value=預設['線總寬'], step=0.5, min_value=2.0)
    線長度 = number_input("線長度 (mm)", value=預設['線長度'], step=10, min_value=50)
    
    # markdown("---")
    工作溫度 = radio("工作溫度", [300, 77, 4], format_func=lambda x: f"{x} K")
    
    # markdown("---")
    
    if button("🔍 執行驗證", type="primary", use_container_width=True):
        session_state.執行驗證 = True


    # ===== 主區域 =====
    subheader("✅ Delft cri/oFlex3 規格驗證平台")
    # ===== 建立佈局 =====
    佈局 = 佈局計算器(規格類型=目前規格, 通道數=通道數, 訊號間距=訊號間距, 訊號寬度um=訊號寬度um, 線總寬=線總寬, 線長度=線長度)

    info(f"📌 當前規格: **{佈局.規格名稱}** | 層數: {len(佈局.層定義)} | 總厚度: {佈局.總厚度um}μm | 總寬度: {佈局.線總寬:.2f}mm")



# ===== 電氣特性即時計算 =====
markdown("### 📊 電氣特性計算")

col1, col2, col3, col4 = columns(4)
with col1:
    Z0 = 計算特性阻抗(佈局, 工作溫度)
    metric("特性阻抗", f"{Z0:.1f} Ω",
              delta=f"{Z0-50:+.1f} Ω" if abs(Z0-50) > 5 else None,
              delta_color="inverse" if abs(Z0-50) > 5 else "normal")

with col2:
    tpd = 計算傳播延遲(佈局, 工作溫度)
    metric("傳播延遲", f"{tpd:.2f} ns/m",
              delta=f"{tpd-5.6:+.2f}" if abs(tpd-5.6) > 0.3 else None,
              delta_color="inverse" if abs(tpd-5.6) > 0.3 else "normal")

with col3:
    材料 = 'NbTi' if 目前規格 == 'FPC' else 'Ag'
    衰減 = 計算插入損耗(佈局, 10, 材料, 工作溫度)
    metric(f"插入損耗 @10GHz", f"{衰減:.2f} dB/m",
              delta=f"{衰減-0.5:+.2f}" if 衰減 > 0.5 else None,
              delta_color="inverse" if 衰減 > 0.5 else "normal")

with col4:
    串擾 = 計算串擾(佈局, 10, 佈局.線長度)
    metric("串擾 @10GHz", f"{串擾:.1f} dB",
              delta=f"{串擾+40:+.1f}" if 串擾 > -40 else None,
              delta_color="inverse" if 串擾 > -40 else "normal")


# ===== 衰減頻譜 =====
with expander("📈 衰減頻譜 (2/6/12/18 GHz)", expanded=False):
    頻譜_Ag = 計算衰減頻譜(佈局, 'Ag', 工作溫度)
    頻譜_NbTi = 計算衰減頻譜(佈局, 'NbTi', 工作溫度)
    
    頻譜_df = DataFrame({
        '頻率 (GHz)': list(頻譜_Ag.keys()),
        'Ag 衰減 (dB/m)': [f"{v:.2f}" for v in 頻譜_Ag.values()],
        'NbTi 衰減 (dB/m)': [f"{v:.2f}" for v in 頻譜_NbTi.values()],
    })
    dataframe(頻譜_df, use_container_width=True, hide_index=True)


# ===== 驗證結果 =====
# markdown("---")
markdown("### 🔍 驗證結果")

驗證結果 = 執行完整驗證(佈局, 目前規格)

# 統計
全部項目 = []
for 類別, 結果列表 in 驗證結果.items():
    for 項目 in 結果列表:
        全部項目.append(項目)

通過數 = sum(1 for 項目 in 全部項目 if 項目['通過'])
失敗數 = len(全部項目) - 通過數
通過率 = 通過數 / len(全部項目) * 100 if 全部項目 else 0

col1, col2, col3, col4 = columns(4)
col1.metric("總驗證項目", len(全部項目))
col2.metric("✅ 通過", 通過數)
col3.metric("❌ 失敗", 失敗數, delta=f"{失敗數}" if 失敗數 > 0 else None, delta_color="inverse")
col4.metric("通過率", f"{通過率:.1f}%")

progress(通過率 / 100, text=f"通過率: {通過率:.1f}%")


# ===== 各類別驗證結果 =====
for 類別, 結果列表 in 驗證結果.items():
    with expander(f"📋 {類別}驗證", expanded=(失敗數 > 0)):
        df = DataFrame(結果列表)
        
        if not df.empty:
            # 格式化
            df['結果'] = df['通過'].apply(lambda x: '✅ 通過' if x else '❌ 失敗')
            df['差異'] = df['差異'].apply(lambda x: f"{x:+.3f}" if isinstance(x, (int, float)) else x)
            
            # 顯示欄位
            display_cols = ['項目', '規格值', '原廠值', '單位', '公差', '差異', '結果']
            display_cols = [c for c in display_cols if c in df.columns]
            
            dataframe(df[display_cols], use_container_width=True, hide_index=True)


# ===== 失敗原因分析 =====
if 失敗數 > 0:
    markdown("---")
    markdown("### ⚠️ 驗證失敗原因分析")
    
    for 類別, 結果列表 in 驗證結果.items():
        失敗項目 = [項目 for 項目 in 結果列表 if not 項目['通過']]
        if 失敗項目:
            markdown(f"#### {類別}")
            for 項目 in 失敗項目:
                error(f"""
                **❌ {項目['項目']}**
                - 規格值: `{項目['規格值']} {項目['單位']}`
                - 原廠值: `{項目['原廠值']} {項目['單位']}`
                - 差異: `{項目['差異']:+.3f}` 
                - 允許公差: `{項目['公差']}`
                """)
else:
    success("🎉 所有驗證項目通過！規格符合 Delft cri/oFlex3 標準。")


# ===== 非官方規格清單 =====
markdown("---")
markdown("### 📋 非官方規格清單")
caption("以下規格未在 Delft cri/oFlex3 官方 Datasheet 中列出，為幾何推導或物理計算值。")

非官方 = 列出非官方規格(目前規格)
if 非官方:
    df_非官方 = DataFrame(非官方)
    dataframe(df_非官方, use_container_width=True, hide_index=True)
else:
    info("所有規格均為官方規格。")


# ===== 匯出報告 =====
markdown("---")
markdown("### 📥 匯出驗證報告")

col1, col2 = columns([3, 1])
with col1:
    info(f"📐 {佈局.規格名稱} | 驗證項目: {len(全部項目)} | 通過率: {通過率:.1f}%")

with col2:
    #if button("📊 產生驗證報告", type="primary", use_container_width=True):
    #    with spinner("正在產生驗證報告..."):
    #        try:
    報告 = 匯出驗證報告(佈局, 驗證結果)
    
    download_button(
        label="⬇️ 下載驗證報告.xlsx",
        data=報告,
        file_name=f"驗證報告_{目前規格}_{佈局.通道數}通道.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    success("✅ 驗證報告已產生!")
    #        except Exception as e:
    #            error(f"❌ 產生失敗: {e}")
