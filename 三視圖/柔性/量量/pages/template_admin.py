import streamlit as st
from db import query, execute
from auth import require_role, hash_password
from constants import ROLES, SOP_TYPES, DECISION_LABELS

st.title("模板配置与管理")
require_role("admin")

st.subheader("用户管理")
users = query("SELECT id, username, role, is_active FROM users ORDER BY id")
for u in users:
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    c1.write(u["username"])
    c2.write(u["role"])
    c3.write("启用" if u["is_active"] else "停用")
    if c4.button("切换状态", key=f"toggle_{u['id']}"):
        execute("UPDATE users SET is_active = NOT is_active WHERE id=%s", (u["id"],))
        st.rerun()

with st.form("add_user"):
    st.write("新增用户")
    nu = st.text_input("用户名")
    np = st.text_input("密码", type="password")
    nr = st.selectbox("角色", ROLES)
    if st.form_submit_button("创建"):
        execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
            (nu, hash_password(np), nr),
        )
        st.rerun()

st.subheader("Checklist 模板")
sop_type = st.selectbox(
    "SOP 类型", list(SOP_TYPES.keys()), format_func=lambda x: SOP_TYPES[x]
)
templates = query(
    """SELECT * FROM checklist_items
       WHERE sop_instance_id IN (SELECT id FROM sop_instances WHERE sop_type=%s)
       ORDER BY item_order""",
    (sop_type,),
)
for t in templates[:20]:
    st.write(f"#{t['item_order']} {t['description']} | {t['pass_criteria']}")

with st.form("add_template_item"):
    st.write("新增模板条目")
    target_sop = st.number_input("目标 SOP ID", min_value=1)
    order = st.number_input("顺序", min_value=1)
    desc = st.text_input("描述")
    dec = st.selectbox("关联决策", DECISION_LABELS)
    crit = st.text_input("通过标准")
    if st.form_submit_button("添加"):
        execute(
            """INSERT INTO checklist_items
               (sop_instance_id, item_order, description, related_decision, pass_criteria)
               VALUES (%s, %s, %s, %s, %s)""",
            (target_sop, order, desc, dec if dec != "无" else None, crit),
        )
        st.rerun()
