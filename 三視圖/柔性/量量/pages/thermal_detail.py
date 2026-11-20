import json
import streamlit as st
from db import query, execute, write_audit
from constants import PROCEDURE_STATUS, CRITERIA_STATUS, DELAY_REASONS
from auth import require_login

st.title("热负载 SOP 详情")
require_login()

sop_id = st.session_state.get("selected_sop_id")
if not sop_id:
    st.warning("请从列表页选择一个 SOP")
    st.stop()

sop = query(
    """
    SELECT s.*, t.vacuum_leak_rate, t.cooldown_rate_k_per_min,
           t.static_load_mw, t.dynamic_load_mw
    FROM sop_instances s
    LEFT JOIN sop_thermal t ON s.id = t.sop_instance_id
    WHERE s.id=%s
    """,
    (sop_id,),
)[0]

st.subheader(f"{sop['sop_code']} — {sop['sop_name']}")
st.write(f"负责人：{sop['owner']} | 计划：{sop['plan_start']} ~ {sop['plan_end']}")

if st.session_state.role in ("executor", "admin"):
    with st.form("sop_meta"):
        col1, col2 = st.columns(2)
        actual_start = col1.date_input(
            "实际开始", value=sop["actual_start"] or sop["plan_start"]
        )
        actual_end = col2.date_input(
            "实际结束", value=sop["actual_end"] or sop["plan_end"]
        )
        on_sched = st.checkbox("如期完成", value=sop["is_on_schedule"])
        reasons = st.multiselect(
            "延迟原因",
            list(DELAY_REASONS.keys()),
            default=sop["delay_reasons"] or [],
            format_func=lambda x: DELAY_REASONS[x],
        )
        notes = st.text_area("延迟补充说明", value=sop["delay_notes"] or "")
        if st.form_submit_button("保存 SOP 信息"):
            execute(
                """UPDATE sop_instances
                   SET actual_start=%s, actual_end=%s, is_on_schedule=%s,
                       delay_reasons=%s::jsonb, delay_notes=%s, updated_at=NOW()
                   WHERE id=%s""",
                (
                    actual_start,
                    actual_end,
                    on_sched,
                    json.dumps(reasons),
                    notes,
                    sop_id,
                ),
            )
            st.rerun()

st.subheader("热负载参数")
if st.session_state.role in ("executor", "admin"):
    with st.form("thermal_fields"):
        c1, c2 = st.columns(2)
        leak = c1.number_input(
            "真空泄漏率", value=float(sop["vacuum_leak_rate"] or 0)
        )
        cool = c2.number_input(
            "降温速率 (K/min)", value=float(sop["cooldown_rate_k_per_min"] or 0)
        )
        stat = c1.number_input(
            "静态热负载 (mW)", value=float(sop["static_load_mw"] or 0)
        )
        dyn = c2.number_input(
            "动态热负载 (mW)", value=float(sop["dynamic_load_mw"] or 0)
        )
        if st.form_submit_button("保存热负载参数"):
            execute(
                """UPDATE sop_thermal
                   SET vacuum_leak_rate=%s, cooldown_rate_k_per_min=%s,
                       static_load_mw=%s, dynamic_load_mw=%s
                   WHERE sop_instance_id=%s""",
                (leak, cool, stat, dyn, sop_id),
            )
            st.rerun()

st.subheader("Checklist")
items = query(
    "SELECT * FROM checklist_items WHERE sop_instance_id=%s ORDER BY item_order",
    (sop_id,),
)

if not items:
    st.info("暂无 checklist 条目")
else:
    for item in items:
        with st.form(key=f"form_{item['id']}"):
            st.write(f"**#{item['item_order']} {item['description']}**")
            st.caption(
                f"通过标准：{item['pass_criteria']} | 关联：{item['related_decision'] or '无'}"
            )
            c1, c2 = st.columns(2)
            proc = c1.selectbox(
                "程序状态",
                PROCEDURE_STATUS,
                index=PROCEDURE_STATUS.index(item["procedure_status"]),
            )
            crit = c2.selectbox(
                "判据状态",
                CRITERIA_STATUS,
                index=CRITERIA_STATUS.index(item["criteria_status"]),
            )
            measured = st.text_input("实测值", value=item["measured_value"] or "")
            if st.form_submit_button("保存本条"):
                old = f"{item['procedure_status']}|{item['criteria_status']}|{item['measured_value']}"
                new = f"{proc}|{crit}|{measured}"
                execute(
                    """UPDATE checklist_items
                       SET procedure_status=%s, criteria_status=%s, measured_value=%s,
                           executor=%s, executed_at=NOW()
                       WHERE id=%s""",
                    (proc, crit, measured, st.session_state.username, item["id"]),
                )
                write_audit(
                    "checklist_items",
                    item["id"],
                    "status",
                    old,
                    new,
                    st.session_state.username,
                )
                st.rerun()
