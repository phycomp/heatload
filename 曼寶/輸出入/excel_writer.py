# io/excel_writer.py
import io
import pandas as pd

def build_excel(nominal, cfg, results, summary, unit) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        pd.DataFrame([nominal]).to_excel(writer, sheet_name="Nominal", index=False)
        pd.DataFrame([cfg]).to_excel(writer, sheet_name="Config", index=False)
        for name, rows in results.items():
            pd.DataFrame(rows).to_excel(writer, sheet_name=name[:31], index=False)
        pd.DataFrame(summary).to_excel(writer, sheet_name="Summary", index=False)
    return buf.getvalue()
