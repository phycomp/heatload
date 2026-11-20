from streamlit import bar_chart, info, stop, subheader, title, write
from pandas import DataFrame
import streamlit as st
import pandas as pd
from db import query
from constants import DELAY_REASONS, SOP_TYPES
from auth import require_login

st.title("延迟归因分析")
require_login()

rows = query(
    "SELECT sop_type, delay_reasons, plan_end, actual_end FROM sop_instances WHERE is_on_schedule=FALSE"
)

records = []
for r in rows:
    for reason in r["delay_reasons"]:
        records.append(
            {
                "sop_type": r["sop_type"],
                "reason": reason,
                "reason_label": DELAY_REASONS.get(reason, reason),
            }
        )

if not records:
    st.info("暂无延迟记录")
    st.stop()

df = pd.DataFrame(records)

st.subheader("延迟原因频次")
freq = df.groupby("reason_label").size().sort_values(ascending=False)
st.bar_chart(freq)

st.subheader("按 SOP 类型分组")
for t, label in SOP_TYPES.items():
    sub = df[df["sop_type"] == t]
    if not sub.empty:
        st.write(f"**{label}**")
        st.write(sub.groupby("reason_label").size().sort_values(ascending=False))
