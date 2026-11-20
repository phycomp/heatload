from streamlit import caption, column_config, columns, dataframe, divider, markdown, metric, set_page_config, success, sidebar, code
from pandas import DataFrame
from streamlit import empty, pyplot
狀態=empty()
#import streamlit as st
#import pandas as pd

# ============================================================
# Streamlit 版本: 計算結果 (核心)
# ============================================================

with sidebar:
    L0 = 2.45e-8 #羅倫茲常數
    A_ch = 0.0635e-6  # mm² to m²
    A_single = 0.0127e-6

    segments = [
        ("300K → 50K", 300, 50, 2.7e-3, 1.6e-8, None, None),
        ("50K → 4K", 50, 4, 0.8e-3, 1.5e-8, None, None),
        ("4K → 0.6K (Ag)", 4, 0.6, 5.4e-6, 1.5e-8, 540e-9, 6.5e-7),
        ("4K → 0.6K (NbTi)", 4, 0.6, None, None, 540e-9, 6.5e-7),
        ("0.6K → 100mK (Ag)", 0.6, 0.1, 290e-9, 1.5e-8, 29e-9, 6.5e-7),
        ("0.6K → 100mK (NbTi)", 0.6, 0.1, None, None, 29e-9, 6.5e-7),
        ("100mK → 10mK (Ag)", 0.1, 0.01, 5.9e-9, 1.5e-8, 590e-12, 6.5e-7),
        ("100mK → 10mK (NbTi)", 0.1, 0.01, None, None, 590e-12, 6.5e-7),
    ]
    #name, Th, Tc, Q_ag, rho_ag, Q_nbti, rho_nbti
    傳輸線=DataFrame(segments, columns=['材料', '高溫Th', '低溫Tc', '銀熱負載', '銀電阻', '鈮鈦熱負載', '鈮鈦電阻'])
    傳輸線
    #

def 回推長度():
    rows = []
    cum_ag_list = []
    cum_nbti_list = []

    for name, Th, Tc, Q_ag, rho_ag, Q_nbti, rho_nbti in segments:
        row_data = {
            "溫度段": name,
            "Th (K)": Th,
            "Tc (K)": Tc,
        }

        # Ag 計算
        L_ag_val = None
        L_single_val = None
        if Q_ag and rho_ag:
            L_ag = (L0 * A_ch * (Th**2 - Tc**2)) / (2 * Q_ag * rho_ag)
            L_ag_val = L_ag
            cum_ag_list.append(L_ag)

            # 熱負載 (自動單位)
            if Q_ag >= 1e-3:
                row_data["Ag 熱負載"] = f"{Q_ag * 1e3:.2f} mW"
            elif Q_ag >= 1e-6:
                row_data["Ag 熱負載"] = f"{Q_ag * 1e6:.2f} µW"
            elif Q_ag >= 1e-9:
                row_data["Ag 熱負載"] = f"{Q_ag * 1e9:.2f} nW"
            else:
                row_data["Ag 熱負載"] = f"{Q_ag * 1e12:.2f} pW"

            # 長度 (自動單位)
            if L_ag >= 1:
                row_data["Ag 回推長度"] = f"{L_ag:.2f} m"
            elif L_ag >= 0.01:
                row_data["Ag 回推長度"] = f"{L_ag * 100:.1f} cm"
            else:
                row_data["Ag 回推長度"] = f"{L_ag * 1000:.1f} mm"

            # 單根長度參考
            L_single = (L0 * A_single * (Th**2 - Tc**2)) / (2 * Q_ag * rho_ag)
            L_single_val = L_single
            if L_single >= 0.01:
                row_data["單根長度(參考)"] = f"{L_single * 100:.1f} cm"
            else:
                row_data["單根長度(參考)"] = f"{L_single * 1000:.1f} mm"
        else:
            row_data["Ag 熱負載"] = "—"
            row_data["Ag 回推長度"] = "—"
            row_data["單根長度(參考)"] = "—"

        # NbTi 計算
        L_nbti_val = None
        if Q_nbti and rho_nbti:
            L_nbti = (L0 * A_ch * (Th**2 - Tc**2)) / (2 * Q_nbti * rho_nbti)
            L_nbti_val = L_nbti
            cum_nbti_list.append(L_nbti)

            if Q_nbti >= 1e-6:
                row_data["NbTi 熱負載"] = f"{Q_nbti * 1e6:.2f} µW"
            elif Q_nbti >= 1e-9:
                row_data["NbTi 熱負載"] = f"{Q_nbti * 1e9:.2f} nW"
            else:
                row_data["NbTi 熱負載"] = f"{Q_nbti * 1e12:.2f} pW"

            if L_nbti >= 1:
                row_data["NbTi 回推長度"] = f"{L_nbti:.2f} m"
            elif L_nbti >= 0.01:
                row_data["NbTi 回推長度"] = f"{L_nbti * 100:.1f} cm"
            else:
                row_data["NbTi 回推長度"] = f"{L_nbti * 1000:.1f} mm"

            # 長度比
            if L_ag_val is not None:
                ratio = L_ag_val / L_nbti
                row_data["長度比(Ag/NbTi)"] = f"{ratio:.1f}×"
            else:
                row_data["長度比(Ag/NbTi)"] = "—"
        else:
            row_data["NbTi 熱負載"] = "—"
            row_data["NbTi 回推長度"] = "—"
            row_data["長度比(Ag/NbTi)"] = "—"

        # 合理性評估
        if L_ag_val is not None:
            if 0.1 <= L_ag_val <= 2.0:
                row_data["合理性評估"] = "✅ 合理"
            elif L_ag_val < 0.1:
                row_data["合理性評估"] = "⚠️ 較短"
            else:
                row_data["合理性評估"] = "⚠️ 偏長"
        elif L_nbti_val is not None:
            if L_nbti_val < 0.05:
                row_data["合理性評估"] = "⚠️ 等效熱阻"
            else:
                row_data["合理性評估"] = "—"
        else:
            row_data["合理性評估"] = "—"
        code(row_data)

        rows.append(row_data)

    rows
    # --- 建立 DataFrame ---
    df = DataFrame(rows)
    column_order = [
        "溫度段", "Th (K)", "Tc (K)",
        "Ag 熱負載", "Ag 回推長度",
        "NbTi 熱負載", "NbTi 回推長度",
        "長度比(Ag/NbTi)", "合理性評估", "單根長度(參考)"
    ]
    左, 右=columns([2, 8])
    with 左:
      傳輸線
    with 右:
      df = df[column_order]

      # --- 顯示表格 ---
      dataframe(
          df,
          use_container_width=True,
          hide_index=True,
          column_config={
              "溫度段": column_config.TextColumn("溫度段", width="medium"),
              "Th (K)": column_config.NumberColumn("Th (K)", format="%.1f"),
              "Tc (K)": column_config.NumberColumn("Tc (K)", format="%.2f"),
              "Ag 熱負載": column_config.TextColumn("Ag 熱負載", width="small"),
              "Ag 回推長度": column_config.TextColumn("Ag 回推長度", width="small"),
              "NbTi 熱負載": column_config.TextColumn("NbTi 熱負載", width="small"),
              "NbTi 回推長度": column_config.TextColumn("NbTi 回推長度", width="small"),
              "長度比(Ag/NbTi)": column_config.TextColumn("長度比(Ag/NbTi)", width="small"),
              "合理性評估": column_config.TextColumn("合理性評估", width="medium"),
              "單根長度(參考)": column_config.TextColumn("單根長度(參考)", width="small"),
          }
      )

    # --- 累積長度區 ---
    divider()
    markdown("### 📐 累積長度")

    狀態.code(['cum_ag_list', cum_ag_list])
    cum_ag = sum(cum_ag_list)
    cum_nbti = sum(cum_nbti_list)

    col1, col2 = columns(2)
    with col1:
        metric(label="Ag 累積長度", value=f"{cum_ag:.2f} m")
    with col2:
        metric(label="NbTi 累積長度", value=f"{cum_nbti:.3f} m")

    success("✅ 計算結果顯示完成")


# ============================================================
# Streamlit App 入口
# ============================================================
#if __name__ == "__main__":
set_page_config(page_title="熱負載計算結果", page_icon="📊", layout="wide")
回推長度()
with sidebar:
    markdown("## 📊 各溫度段熱負載與回推長度計算結果")
    caption("計算公式: L = L₀ · A_channel · (Tₕ² - Tc²) / (2 · Q · ρ)")

