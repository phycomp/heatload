# io/excel_reader.py
import pandas as pd

def read_nominal_from_xlsx(file) -> dict:
    df = pd.read_excel(file, sheet_name="Sensitivity", header=None)
    # 原始 Excel：H4..M4 => row index 3, col 7..12
    H1 = float(df.iloc[3, 7])
    Er1 = float(df.iloc[3, 8])
    W1 = float(df.iloc[3, 9])
    W2 = float(df.iloc[3, 10])
    S1 = float(df.iloc[3, 11])
    T1 = float(df.iloc[3, 12])
    return {"H1": H1, "Er1": Er1, "W1": W1, "W2": W2, "S1": S1, "T1": T1}
