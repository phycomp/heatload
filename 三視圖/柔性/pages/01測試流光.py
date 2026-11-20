# 測試_前視圖_Streamlit.py
"""用 Streamlit 快速檢視前視圖"""

import sys
sys.path.insert(0, '.')

import streamlit as st
import matplotlib.pyplot as plt
from io import BytesIO

from 核心.佈局計算 import 佈局計算器
from 繪圖.前視 import 繪製前視


def 圖形轉bytes(fig):
    """將 matplotlib figure 轉為 bytes"""
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#0D1117')
    buf.seek(0)
    return buf


st.set_page_config(page_title="前視圖測試", layout="wide")

st.title("📐 前視圖繪製測試")

# 側邊欄參數
with st.sidebar:
    st.subheader("⚙️ 參數設定")
    通道數 = st.slider("通道數", 2, 16, 8, 2)
    訊號間距 = st.slider("訊號間距 (mm)", 0.5, 5.0, 2.0, 0.2)
    訊號寬度um = st.slider("訊號寬度 (μm)", 10, 40, 35, 5)
    線總寬 = st.number_input("線總寬 (mm)", value=17.0, step=0.5)
    
    st.markdown("---")
    st.caption(f"總厚度: 300μm (固定)")
    st.caption(f"層數: 7層 (GSG結構)")

# 主區域
col1, col2 = st.tabs(['前視圖', '疊構'])

with col1:
    st.subheader("🔲 前視圖")
    
    try:
        # 建立佈局
        佈局 = 佈局計算器(
            通道數=通道數,
            訊號間距=訊號間距,
            訊號寬度um=訊號寬度um,
            線總寬=線總寬
        )
        
        # 繪製
        fig = 繪製前視(佈局)
        
        # 顯示
        st.pyplot(fig)
        plt.close(fig)
        
    except Exception as e:
        st.error(f"繪製失敗: {e}")
        import traceback
        st.code(traceback.format_exc())

with col2:
    st.subheader("📊 佈局資訊")
    
    左, 右 = st.columns([3, 9])
    with 左:
        st.metric("通道數", 佈局.通道數)
        st.metric("總寬度", f"{佈局.線總寬:.2f} mm")
        st.metric("總厚度", f"{佈局.總厚度um} μm")
        st.metric("訊號間距", f"{佈局.訊號間距} mm")
        st.metric("訊號寬度", f"{佈局.訊號寬度mm*1000:.0f} μm")
        st.metric("鈮鈦比例", 佈局.鈮鈦比例)
        
    with 右:
        st.subheader("📋 層結構")
        
        from 核心.層 import 層定義
        層表格 = []
        for i, 層 in enumerate(層定義):
            層表格.append({
                "層": i+1,
                "名稱": 層['名稱'],
                "材料": 層['材料'],
                "厚度": f"{層['厚度um']}μm"
            })
        st.dataframe(層表格, use_container_width=True)
        
    #except Exception as e:
    #    st.error(f"顯示資訊失敗: {e}")
