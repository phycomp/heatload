from streamlit import button, caption, checkbox, code, columns, dataframe, download_button, error, info, markdown, metric, number_input, pyplot, radio, rerun, session_state, set_page_config, sidebar, slider, spinner, subheader, success, tabs, text_input
from matplotlib.pyplot import close
from pandas import DataFrame
from sys import path
# 柔性線函式庫/應用程式/主程式.py
"""Streamlit 主應用程式 - 支援 GSG 7層 與 FPC 12層"""

import sys
import os
path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

from 核心.佈局FPC import 佈局計算器
from 核心.層FPC import 全名稱, 全層, 全參數, 計算CableWidth #取得層定義, 
from 繪圖.前視FPC import 繪製前視
from 繪圖.側視FPC import 繪製側視
from 繪圖.上視FPC import 繪製上視
# from 匯出.匯出FPC import 匯出分頁, 建立層疊表格
from 匯出.圖規格II import 匯出分頁, 建立規格表格, 建立層疊表格


set_page_config(
    page_title="智慧三視圖系統",
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
    session_state.規格類型 = 'GSG'

# 各自獨立的參數儲存
if 'GSG參數' not in session_state:
    session_state.GSG參數 = {
        '通道數': 8,
        '訊號間距': 2.0,
        '訊號寬度um': 35,
        '線總寬': 17.0,
        '線長度': 200,
    }
if 'FPC參數' not in session_state:
    session_state.FPC參數 = {
        '通道數': 8,
        '訊號間距': 0.171,
        '訊號寬度um': 65,
        '線總寬': 4.156,
        '線長度': 150,
    }


# ===== 規格資框 =====
def 規格資框(佈局):
    """建立規格 DataFrame"""
    data = {"類別": [], "參數": [], "規格值": [], "單位": [], "備註": [], "公差": []}

    # 一般規格
    一般規格 = [
        ["一般規格", "產品名稱", "U-leam UF1", "", "仿照 Delft Circuits", ""],
        ["一般規格", "規格類型", 佈局.規格名稱, "", "", ""],
        ["一般規格", "通道數", 佈局.通道數, "ch", "並列通道", "±0.5"],
        ["一般規格", "通道間距", 佈局.訊號間距, "mm", "標準設計", "±0.05"],
        ["一般規格", "總寬度", f"{佈局.線總寬:.3f}", "mm", f"{佈局.通道數}ch × {佈局.訊號間距}mm", "±0.1"],
        ["一般規格", "總厚度", 佈局.總厚度um, "μm", f"{len(佈局.規格層)}層結構", "±5"],
        ["一般規格", "線長度", 佈局.線長度, "mm", "可客製化", "±1"],
        ["一般規格", "線邊緣空白", f"{佈局.邊緣:.4f}", "mm", "符合5W/10H規則", ""],
        ["一般規格", "最小彎曲半徑", 5 if 佈局.規格類型 == 'GSG' else 3, "mm", "動態彎曲", "-0/+1"],
        ["一般規格", "訊號寬度", 佈局.訊號寬度um, "μm", "W1", "±2"],
    ]
    規格 = 一般規格

    # FPC 專屬：Cable Width 計算
    if 佈局.規格類型 == 'FPC' and 佈局.CableWidth:
        cw = 佈局.CableWidth
        規格.append(["一般規格", "Ground space", cw['Ground space'], "μm", "接地間距", "±5"])
        規格.append(["一般規格", "W1 (線寬)", cw['W1'], "μm", "訊號線寬度", "±2"])
        規格.append(["一般規格", "D1 (間距)", cw['D1'], "μm", "相鄰通道間距", "±5"])
        規格.append(["一般規格", "Cable Width", f"{cw['cable_width_mm']:.3f}", "mm", f"= 8×W1 + 8×D1×2 + 9×GND", "±0.1"])
        規格.append(["一般規格", "Pitch (SMPM)", f"{cw['Pitch_SMPM_mm']:.3f}", "mm", "連接器間距", "±0.05"])

    # 層結構
    for 層 in 佈局.層定義:
        規格.append(["層結構", 層['名稱'], 層['厚度um'], "μm", 層['材料'], "±2"])

    # 層結構專屬：H1/H2
    if 佈局.規格類型 == 'FPC':
        規格.append(["層結構", "H1 (L1→L2)", f"{佈局.H1:.1f}", "μm", "L1 到 L2 中心距離", "±2"])
        規格.append(["層結構", "H2 (L2→L3)", f"{佈局.H2:.1f}", "μm", "L2 到 L3 中心距離", "±2"])

    # 材料規格
    材料規格 = [
        ["材料規格", "導體材料", "NbTi" if 佈局.規格類型 == 'FPC' else "Ag/NbTi", "-", f"比例 {佈局.鈮鈦比例}", ""],
        ["材料規格", "介電材料", "Polyimide" if 佈局.規格類型 == 'GSG' else "PI / PI glue", "-", "低損耗", ""],
        ["材料規格", "保護層材料", "Polyimide" if 佈局.規格類型 == 'GSG' else "PI / AD", "-", "覆蓋層", ""],
        ["材料規格", "鈮鈦比例", 佈局.鈮鈦比例, "%", "Nb:Ti 比例", "±1"],
    ]
    規格.extend(材料規格)

    # 電氣規格
    電氣規格 = [
        ["電氣規格", "特性阻抗", 50, "Ω", "帶狀線設計", "±5"],
        ["電氣規格", "傳播延遲", 5.6, "ns/m", "√εᵣ / c₀", "±0.3"],
        ["電氣規格", "工作頻率", "DC ~ 10", "GHz", "微波操作", ""],
    ]
    規格.extend(電氣規格)

    # 熱性能
    熱性能 = [
        ["熱性能", "工作溫度", "10⁻³ ~ 400", "K", "mK 至室溫", ""],
        ["熱性能", "熱負載 (Ag)", "< 125", "μW/ch", "@ΔT 4-40K, L=0.4m", ""],
        ["熱性能", "熱負載 (NbTi)", "~ 20", "nW/ch", "@ΔT 10-350mK, L=0.2m", ""],
    ]
    規格.extend(熱性能)

    # 機械規格
    機械規格 = [
        ["機械規格", "連接器", "SMA/SMP", "-", "兩端", ""],
        ["機械規格", "最大拉伸力", "> 50" if 佈局.規格類型 == 'GSG' else "> 30", "N", "軸向拉力", ""],
        ["機械規格", "真空洩漏率", "< 10⁻⁹", "mbar·L/s", "整合式穿通", ""],
    ]
    規格.extend(機械規格)

    for 項目 in 規格:
        data["類別"].append(項目[0])
        data["參數"].append(項目[1])
        data["規格值"].append(項目[2])
        data["單位"].append(項目[3])
        data["備註"].append(項目[4])
        data["公差"].append(項目[5])

    return DataFrame(data)


# ===== 繪製所有視圖 =====
def 重新繪製所有視圖(佈局, 字型縮放):
    """重新繪製所有視圖並存入 session_state"""
    session_state.前視圖 = 繪製前視(佈局, 字型縮放)
    session_state.側視圖 = 繪製側視(佈局, 字型縮放)
    session_state.上視圖 = 繪製上視(佈局, 字型縮放)


def 佈局從參數(規格層, 參數):
    """從參數字典建立佈局計算器"""
    return 佈局計算器(
        # 規格類型=規格類型,
        規格層=規格層,
        通道數=參數['通道數'],
        訊號間距=參數['訊號間距'],
        訊號寬度um=參數['訊號寬度um'],
        訊號厚度um=參數['訊號厚度um'],
        線總寬=參數['線總寬'],
        線長度=參數['線長度']
    )


# ===== 側邊欄 =====
with sidebar:
    subheader("📐 智慧三視圖")
    from streamlit import empty, pyplot
    狀態=empty()

    subheader("🔀 規格選擇")
    規格類型=radio('規格類型', ['FPC', 'GSG'], horizontal=True, index=0)
    # 取得規格名稱
    from 核心.層FPC import 全名稱
    if 規格類型:
      session_state.規格類型 = 規格類型
      規格層=session_state.規格層=全層[f'{規格類型}層']
      參數預設=session_state.參數預設=全參數[規格類型]
      規格名稱=session_state.規格名稱=全名稱.get(規格類型)  #, '未知規格'
      狀態.code(['參數預設', 參數預設])

    # col1, col2 = columns(2)
    # with col1:
        # if button("🔵 GSG 7層", use_container_width=True, type="primary" if session_state.規格類型 == 'GSG' else "secondary"):
            # rerun()
    #with col2:
    #    if button("🟢 FPC 12層", use_container_width=True,
    #                 type="primary" if session_state.規格類型 == 'FPC' else "secondary"):
    #        session_state.規格類型 = 'FPC'
    #        rerun()

    # 目前規格 = session_state.規格類型
    # caption(f"當前: {規格名稱[目前規格]}")
    # markdown("---")

    subheader("⚙️ 參數設定")

    # 目前參數 = session_state[f"{規格類型}_參數"]
    # 規格參數 = 預設參數[規格類型]

    # 根據規格類型顯示對應的參數
    if 規格類型 == 'GSG':
        caption("📐 GSG 7層參數")
        通道數 = slider("通道數", 2, 16, 目前參數['通道數'], 2, key="gsg_ch")
        訊號間距 = slider("訊號間距 (mm)", 0.5, 5.0, 目前參數['訊號間距'], 0.1, key="gsg_pitch")
        訊號寬度um = slider("訊號寬度 (μm)", 10, 100, 目前參數['訊號寬度um'], 5, key="gsg_width")
        線總寬 = number_input("線總寬 (mm)", value=目前參數['線總寬'], step=0.5, min_value=2.0, key="gsg_total_w")
        線長度 = number_input("線長度 (mm)", value=目前參數['線長度'], step=10, min_value=50, key="gsg_length")

        session_state.GSG參數 = {
            '通道數': 通道數, '訊號間距': 訊號間距, '訊號寬度um': 訊號寬度um,
            '線總寬': 線總寬, '線長度': 線長度,
        }
    else:
        caption("📐 FPC 12層參數")
        通道數 = slider("通道數", 2, 16, 8, 2, key="fpc_ch")  #規格參數['通道數']
        訊號間距 = slider("訊號間距 (mm)", 0.05, 1.0, 參數預設['訊號間距'], 0.01, key="fpc_pitch")
        訊號寬度um = slider("訊號寬度 (μm)", 10, 100, 參數預設['訊號寬度um'], 5, key="fpc_width")
        線總寬 = number_input("線總寬 (mm)", value=參數預設['線總寬'], step=0.1, min_value=1.0, key="fpc_total_w")
        線長度 = number_input("線長度 (mm)", value=參數預設['線長度'], step=10, min_value=50, key="fpc_length")

        # FPC參數=session_state.FPC參數 = 
        session_state.參數預設.update({
            '通道數': 通道數, '訊號間距': 訊號間距, '訊號寬度um': 訊號寬度um, '線總寬': 線總寬, '線長度': 線長度,
        })
        # 狀態.code(['FPC參數', FPC參數])

        # 顯示 Cable Width 計算
        if checkbox("顯示 Cable Width 計算", value=True, key="show_cable"):
            cw = 計算CableWidth(規格層=規格層)
            caption("📏 Cable Width 計算")
            code(f"""
Ground space = {cw['Ground space']} μm
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
    # 規格參數 = session_state[f"{規格類型}_參數"]
    佈局 = 佈局從參數(規格層, session_state.參數預設)

    markdown("---")
    subheader("📊 佈局資訊")

    col1, col2 = columns(2)
    col1.metric("層數", len(佈局.規格層))
    # col2.metric("總厚度", f"{佈局.總厚度um:.1f}μm")
    # col1.metric("總寬度", f"{佈局.線總寬:.3f}mm")
    # col2.metric("通道數", 佈局.通道數)

    if 規格類型 == 'FPC':
        col1.metric("H1", f"{佈局.H1:.1f}μm")
        col2.metric("H2", f"{佈局.H2:.1f}μm")


# ===== 主區域 =====
subheader("📐 智慧三視圖系統")

info(f"📌 當前規格: **{佈局.規格名稱}** | 層數: {len(佈局.規格層)} | 總厚度: {佈局.總厚度um:.1f}μm | 總寬度: {佈局.線總寬:.3f}mm")

# 選單
選項 = ["📐 前視圖", "📐 側視圖", "📐 上視圖", "📊 三視圖總覽", "📥 匯出 Excel"]
選取 = radio("選擇視圖", 選項, horizontal=True)

# 重新繪製所有視圖
重新繪製所有視圖(佈局, 字型縮放)

# ===== 顯示對應視圖 =====
if 選取 == "📐 前視圖":
    subheader("🔲 前視圖")
    if session_state.前視圖:
        pyplot(session_state.前視圖)
        # close(session_state.前視圖)

elif 選取 == "📐 側視圖":
    subheader("🔲 側視圖")
    if session_state.側視圖:
        pyplot(session_state.側視圖)
        # close(session_state.側視圖)

elif 選取 == "📐 上視圖":
    subheader("🔲 上視圖")
    if session_state.上視圖:
        pyplot(session_state.上視圖)
        # close(session_state.上視圖)

elif 選取 == "📊 三視圖總覽":
    subheader("📊 三視圖總覽")

    col1, col2 = columns(2)
    with col1:
        caption("前視圖")
        if session_state.前視圖:
            pyplot(session_state.前視圖)
            # close(session_state.前視圖)

    with col2:
        caption("側視圖")
        if session_state.側視圖:
            pyplot(session_state.側視圖)
            # close(session_state.側視圖)

    caption("上視圖")
    if session_state.上視圖:
        pyplot(session_state.上視圖)
        # close(session_state.上視圖)

else:  # 匯出 Excel
    subheader("📥 匯出 Excel 規格書")

    markdown("### 📋 Excel 分頁預覽")

    # 建立預覽資料
    df_規格 = 規格資框(佈局)
    層疊資料 = 建立層疊表格(佈局, 目前規格)
    df_層疊 = DataFrame(層疊資料)

    tab1, tab2, tab3, tab4, tab5, tab6 = tabs([
        "📋 規格表", "🔲 前視圖", "🔲 側視圖", "🔲 上視圖", "📚 層疊結構", "📏 Cable Width"
    ])

    with tab1:
        caption("規格表 (Sheet 1)")

        if 目前規格 == 'FPC' and 佈局.CableWidth:
            cw = 佈局.CableWidth
            info(f"📏 Cable Width: {cw['cable_width_mm']:.3f}mm | Ground: {cw['Ground space']}μm | W1: {cw['W1']}μm | D1: {cw['D1']}μm")
        else:
            info(f"📏 邊緣間距: 左側 {佈局.左側間距*1000:.1f}μm | 右側 {佈局.右側間距*1000:.1f}μm")

        dataframe(df_規格, use_container_width=True, hide_index=True)

        col1, col2, col3 = columns(3)
        col1.metric("規格項目總數", len(df_規格))
        col2.metric("類別數", df_規格[df_規格['類別'] != '']['類別'].nunique())
        col3.metric("含公差項目", len(df_規格[df_規格['公差'] != '']))

    with tab2:
        caption("前視圖 (Sheet 2)")
        if session_state.前視圖:
            pyplot(session_state.前視圖)
            close(session_state.前視圖)

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
        if 目前規格 == 'FPC' and 佈局.CableWidth:
            cw = 佈局.CableWidth
            markdown("### 📏 Cable Width 計算明細")

            col1, col2 = columns(2)
            with col1:
                metric("Ground space", f"{cw['Ground space']} μm")
                metric("W1 (線寬)", f"{cw['W1']} μm")
                metric("D1 (間距)", f"{cw['D1']} μm")
            with col2:
                metric("8 × W1", f"{cw['8*W1']} μm")
                metric("8 × D1 × 2", f"{cw['8*D1*2']} μm")
                metric("9 × Ground", f"{cw['9*Ground space']} μm")

            success(f"**Cable Width = {cw['cable_width_um']} μm = {cw['cable_width_mm']:.3f} mm**")
            info(f"**Pitch (SMPM) = {cw['Pitch_SMPM_mm']:.3f} mm**")

            # 顯示計算表
            calc_df = DataFrame([
                {"項目": "Ground space", "計算式": "-", "數值 (μm)": cw['Ground space']},
                {"項目": "line: W1", "計算式": "-", "數值 (μm)": cw['W1']},
                {"項目": "space: D1", "計算式": "-", "數值 (μm)": cw['D1']},
                {"項目": "8 × W1", "計算式": "8 × W1", "數值 (μm)": cw['8*W1']},
                {"項目": "8 × D1 × 2", "計算式": "8 × D1 × 2", "數值 (μm)": cw['8*D1*2']},
                {"項目": "8W1 + 8×D1×2", "計算式": "520 + 2736", "數值 (μm)": cw['8*W1'] + cw['8*D1*2']},
                {"項目": "9 × Ground space", "計算式": "9 × Ground", "數值 (μm)": cw['9*Ground space']},
                {"項目": "Cable Width", "計算式": "3256 + 900", "數值 (μm)": cw['cable_width_um']},
                {"項目": "1×W1 + 2×D1 + GND", "計算式": "65 + 342 + 100", "數值 (μm)": cw['W1'] + 2*cw['D1'] + cw['Ground space']},
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
        info(f"📐 {佈局.規格名稱} | 通道數: {佈局.通道數} | 總寬: {佈局.線總寬:.3f}mm")

    with col2:
        檔案名稱 = text_input(
            "檔案名稱",
            value=f"UF1_{目前規格}_{佈局.通道數}通道_{佈局.長寬高}",
            key="excel_filename"
        )

    with col3:
        if button("📊 產生並下載 Excel", type="primary", use_container_width=True):
            with spinner("正在產生 Excel 檔案，請稍候..."):
                try:
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
                except Exception as e:
                    error(f"❌ 產生失敗: {e}")
