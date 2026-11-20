from streamlit import Page, button, error, navigation, rerun, session_state, set_page_config, sidebar, stop, write
import streamlit as st

st.set_page_config(page_title="量子量測 SOP 平台", layout="wide")

# 探活：在導航渲染之前
try:
    from db import query
    query("SELECT 1")
except Exception as e:
    st.error(f"數據庫連接失敗，請檢查 secrets.toml：{e}")
    st.stop()

# 會話狀態初始化
defaults = {
    "logged_in": False,
    "username": None,
    "role": None,
    "selected_sop_id": None,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# 未登錄只顯示登錄頁
if not st.session_state.logged_in:
    from auth import render_login_form
    render_login_form()
    st.stop()

# 側邊欄用戶信息 + 登出
with st.sidebar:
    st.write(f"👤 {st.session_state.username}（{st.session_state.role}）")
    if st.button("登出"):
        from auth import logout
        logout()
        st.rerun()

# 導航
pages = {
    "總覽": [
        st.Page("pages/dashboard.py", title="儀表盤"),
        st.Page("pages/delay_analysis.py", title="延遲歸因"),
    ],
    "電性 SOP": [
        st.Page("pages/electrical_list.py", title="電性列表"),
        st.Page("pages/electrical_detail.py", title="電性詳情"),
    ],
    "熱負載 SOP": [
        st.Page("pages/thermal_list.py", title="熱負載列表"),
        st.Page("pages/thermal_detail.py", title="熱負載詳情"),
    ],
    "製程 SOP": [
        st.Page("pages/process_list.py", title="製程列表"),
        st.Page("pages/process_detail.py", title="製程詳情"),
    ],
    "管理": [
        st.Page("pages/template_admin.py", title="模板配置"),
    ],
}

pg = st.navigation(pages)
pg.run()
