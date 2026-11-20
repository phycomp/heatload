from streamlit import caption, code, dataframe, error, markdown, metric, number_input, pyplot, set_page_config, sidebar, slider, subheader, tabs, title, columns
# from matplotlib.pyplot import close
from sys import path
# 測試_前視圖_Streamlit.py
"""用 Streamlit 快速檢視前視圖 (含重疊偵測測試)"""

# import sys
# path.insert(0, '.')

# import streamlit as st
# import matplotlib.pyplot as plt
from io import BytesIO

from 核心.佈局計算 import 佈局計算器
from 繪圖.前視II import 繪製前視
from 繪圖.上視 import 繪製上視
from 繪圖.側視 import 繪製側視


set_page_config(page_title="前視圖測試", layout="wide")

title("📐 前視圖繪製測試 (含重疊偵測)")

# 側邊欄參數
with sidebar:
    subheader("⚙️ 參數設定")
    通道數 = slider("通道數", 2, 16, 8, 2)
    訊號間距 = slider("訊號間距 (mm)", 0.5, 5.0, 2.0, 0.2)
    訊號寬度um = slider("訊號寬度 (μm)", 10, 40, 35, 5)
    線總寬 = number_input("線總寬 (mm)", value=17.0, step=0.5)

    subheader("🔤 字型控制")
    字型縮放 = slider("字型縮放比例", 0.5, 2.0, 1.0, 0.1)
    caption(f"當前字型縮放: {字型縮放:.1f}x")

    markdown("---")
    caption("🔍 重疊偵測規則:")
    caption("• 當保護層或GND層與相鄰層標籤重疊時")
    caption("• 自動將保護層和GND層標籤移至右側")
    caption("• 避免上下標籤互相干擾")

# 主區域
前視, 側視, 上視, 疊構 = tabs(['前視', '側視', '上視', '疊構'])

with 前視:
    subheader("🔲 前視圖")
    
    try:
        # 建立佈局
        佈局 = 佈局計算器(
            通道數=通道數,
            訊號間距=訊號間距,
            訊號寬度um=訊號寬度um,
            線總寬=線總寬
        )
        
        # 繪製
        fig = 繪製前視(佈局, 字型縮放=字型縮放)
        
        # 顯示
        pyplot(fig)
        # close(fig)
        
    except Exception as e:
        error(f"繪製失敗: {e}")
        import traceback
        code(traceback.format_exc())
with 側視:  # 側視圖
    subheader("🔲 側視圖")
    fig = 繪製側視(佈局, 字型縮放=字型縮放)
    pyplot(fig)
    # close(fig)

with 上視:  # 上視圖
    subheader("🔲 上視圖")
    fig = 繪製上視(佈局, 字型縮放=字型縮放)
    pyplot(fig)
    # close(fig)

with 疊構:
    subheader("📊 佈局資訊")
    左, 右=columns(2)
    with 左:
        metric("通道數", 佈局.通道數)
        metric("總寬度", f"{佈局.線總寬:.2f} mm")
        metric("總厚度", f"{佈局.總厚度um} μm")
        metric("訊號間距", f"{佈局.訊號間距} mm")
        metric("訊號寬度", f"{佈局.訊號寬度mm*1000:.0f} μm")
        metric("鈮鈦比例", 佈局.鈮鈦比例)
        
        markdown("---")
    with 右:
        subheader("📋 層結構")
        
        from 核心.層 import 層定義
        層表格 = []
        for i, 層 in enumerate(層定義):
            層表格.append({
                "層": i+1,
                "名稱": 層['名稱'],
                "材料": 層['材料'],
                "厚度": f"{層['厚度um']}μm"
            })
        dataframe(層表格, use_container_width=True)
        
        markdown("---")
        subheader("🏷️ 標籤位置")
        from 繪圖.前視II import 偵測標籤重疊
        
        層中心 = [p['中心mm'] for p in 佈局.層位置列表]
        層厚度 = [p['厚度mm'] for p in 佈局.層位置列表]
        字型大小 = [11 if t > 0.02 else 9 for t in 層厚度]
        
        側邊 = 偵測標籤重疊(層中心, 層厚度, 字型大小)
        位置對照 = []
        for i, 層 in enumerate(層定義):
            位置對照.append({
                "層名稱": 層['名稱'],
                "標籤位置": "➡️ 右側" if 側邊[i] == '右' else "⬅️ 左側"
            })
        dataframe(位置對照, use_container_width=True)
        
    #except Exception as e:
    #    error(f"顯示資訊失敗: {e}")
