from streamlit import columns, subheader, title, write
import streamlit as st
from db import query
from constants import SOP_TYPES, DELAY_REASONS
from auth import require_login

st.title("仪表盘")
require_login()

total = query("SELECT COUNT(*) AS c FROM sop_instances")[0]["c"]
by_type = query("SELECT sop_type, COUNT(*) AS c FROM sop_instances GROUP BY sop_type")
on_sched = query("SELECT COUNT(*) AS c FROM sop_instances WHERE is_on_schedule=TRUE")[0]["c"]

col1, col2, col3 = st.columns(3)
col1.metric("SOP 总数", total)
col2.metric("如期完成", on_sched)
col3.metric("按期率", f"{(on_sched / total * 100):.1f}%" if total else "—")

st.subheader("按类型统计")
for row in by_type:
    st.write(f"{SOP_TYPES.get(row['sop_type'], row['sop_type'])}：{row['c']} 条")

st.subheader("最近延迟记录")
recent = query(
    """
    SELECT sop_code, sop_name, delay_reasons, delay_notes, plan_end, actual_end
    FROM sop_instances
    WHERE is_on_schedule=FALSE AND delay_reasons != '[]'::jsonb
    ORDER BY updated_at DESC LIMIT 10
    """
)
for r in recent:
    reasons = "、".join(DELAY_REASONS.get(x, x) for x in r["delay_reasons"])
    st.write(f"**{r['sop_code']}** {r['sop_name']} — {reasons} {r['delay_notes'] or ''}")

st.subheader("状态分布")
status_rows = query("SELECT status, COUNT(*) AS c FROM sop_instances GROUP BY status")
for r in status_rows:
    st.write(f"{r['status']}：{r['c']}")
