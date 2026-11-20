import streamlit as st
from db import query, execute, execute_returning
from auth import require_login

st.title("热负载 SOP 列表")
require_login()

if st.session_state.role in ("executor", "admin"):
    with st.expander("新建热负载 SOP"):
        with st.form("new_thermal"):
            code = st.text_input("SOP 编号（TH- 开头）")
            name = st.text_input("名称")
            owner = st.text_input("负责人", value=st.session_state.username)
            plan_start = st.date_input("计划开始")
            plan_end = st.date_input("计划结束")
            if st.form_submit_button("创建"):
                row = execute_returning(
                    """INSERT INTO sop_instances
                       (sop_code, sop_type, sop_name, owner, plan_start, plan_end)
                       VALUES (%s, 'thermal', %s, %s, %s, %s) RETURNING id""",
                    (code, name, owner, plan_start, plan_end),
                )
                execute(
                    "INSERT INTO sop_thermal (sop_instance_id) VALUES (%s)",
                    (row["id"],),
                )
                st.success(f"已创建 {code}")
                st.rerun()

rows = query(
    """
    SELECT s.id, s.sop_code, s.sop_name, s.owner, s.plan_start, s.plan_end,
           s.is_on_schedule, s.status
    FROM sop_instances s
    WHERE s.sop_type='thermal'
    ORDER BY s.plan_start DESC
    """
)

for r in rows:
    cols = st.columns([1, 2, 1, 1, 1, 1, 1])
    cols[0].write(r["sop_code"])
    cols[1].write(r["sop_name"])
    cols[2].write(r["owner"])
    cols[3].write(str(r["plan_end"]))
    cols[4].write("✅" if r["is_on_schedule"] else "❌")
    cols[5].write(r["status"])
    if cols[6].button("详情", key=f"det_{r['id']}"):
        st.session_state.selected_sop_id = r["id"]
        st.switch_page("pages/thermal_detail.py")
