from streamlit import button, caption, columns, download_button, error, expander, header, latex, line_chart, markdown, metric, number_input, set_page_config, sidebar, slider, spinner, success, subheader, radio
from numpy import linspace, sqrt
from pandas import DataFrame
### 📂 檔案 3：`app.py` (Streamlit 主程式與 UI)
# 此檔案負責使用者互動、LaTeX 公式動態渲染（包含場論推導）、以及 CSV 匯出功能。
#"""
#Streamlit 高頻傳輸線模擬與逆工程平台 (Phase 1)
#"""
import streamlit as st
import pandas as pd
import numpy as np
import io

# 導入自定義模組
from 材質庫 import MATERIALS_DB, get_material_params
from 數學模型 import calc_djordjevic_sarkar, calc_hammerstad_microstrip, calc_total_insertion_loss, inverse_engineering

# ==========================================
# UI 佈局與側邊欄
# ==========================================
set_page_config(page_title="高頻傳輸線模擬平台", layout="wide")
subheader("📡 高頻傳輸線模擬與逆工程計算平台 (4-12 GHz)")

with sidebar:
# 側邊欄：模式與材料選擇
  subheader("⚙️ 系統設定")
  mode = radio("選擇計算模式", ["正向阻抗與損耗計算", "逆工程：目標阻抗反推線寬"])

  mat_name = radio("選擇板材材料", list(MATERIALS_DB.keys()))
  mat_params = get_material_params(mat_name)

  subheader("📏 幾何參數 (單位: mil)")
  H_mil = number_input("介質厚度 (H)", value=8.0, min_value=1.0, step=0.5)
  t_mil = number_input("銅厚 (t)", value=1.4, min_value=0.5, step=0.1) # 1oz = 1.4mil
  EF = slider("蝕刻因子 (Etch Factor)", min_value=1.0, max_value=10.0, value=3.0, step=0.5, help="1=完美矩形, 3~5=典型FR4蝕刻")

  # 單位轉換 (mil -> meter)
  H = H_mil * 25.4e-6
  t = t_mil * 25.4e-6

# ==========================================
# 主畫面：場論推導展示 (Q14)
# ==========================================
# with expander("📜 查看完整場論推導過程 (Maxwell to Hammerstad)"):
def 渲染():
    markdown(r"""1. 麥克斯韋方程組與波動方程式:
    $$
    \nabla \times \mathbf{E} = -j\omega\mu\mathbf{H}, \quad \nabla \times \mathbf{H} = j\omega\epsilon\mathbf{E} \\
    \nabla^2 \mathbf{E} + k^2 \mathbf{E} = 0 \quad (\text{其中 } k = \omega\sqrt{\mu\epsilon})
    $$
    """)
    markdown(r"""2. 微帶線邊界條件與準 TEM 波假設:
    由於介質非均勻，嚴格解需使用譜域法 (Spectral Domain)。
    工程上採用準 TEM (Quasi-TEM) 假設，定義有效介電常數 
    $$
    \epsilon_{eff} = \frac{\epsilon_r + 1}{2} + \frac{\epsilon_r - 1}{2} \left(1 + \frac{10h}{w}\right)^{-0.555}
    $$
    """)
    markdown(r"""3. Hammerstad-Jensen 阻抗公式 (含銅厚修正):
    $$
    Z_0 = \frac{60}{\sqrt{\epsilon_{eff}}} \ln\left(\frac{8h}{w_{eq}} + 0.25\frac{w_{eq}}{h}\right) \quad (\text{for } w/h \le 1)\\
    w_{eq} = w + \Delta w, \quad \Delta w = \frac{t}{\pi} \ln\left(1 + \frac{4}{t \coth(\sqrt{6.5w/h})}\right)
    $$
    """)
    markdown(r"""4. 梯形截面蝕刻修正 (Etch Factor):
    $$
    w_{eq\_etch} = \frac{w_{top} + w_{bot}}{2}, \quad w_{bot} = w_{top} - \frac{2t}{EF}
    $$
    """)
    markdown(r"""5. Hammerstad 粗糙度損耗模型:
    $$
    K_{sr} = 1 + \frac{2}{\pi} \arctan\left(1.4 \left(\frac{R_q}{\delta}\right)^2\right), \quad \delta = \sqrt{\frac{\rho}{\pi f \mu_0}}
    $$
    """)

渲染()
# ==========================================
# 邏輯分支：正向計算 vs 逆工程
# ==========================================
if mode == "正向阻抗與損耗計算":
    header("📈 正向阻抗與損耗計算")
    col1, col2 = columns(2)

    with col1:
        W_mil = number_input("線寬 (W) [mil]", value=10.0, min_value=1.0, step=0.5)
        W = W_mil * 25.4e-6

    with col2:
        freq_GHz = slider("計算頻率 (GHz)", 4.0, 12.0, 8.0, 0.1)
        f = freq_GHz * 1e9

    # 計算色散 Dk/Df
    Dk_f, Df_f = calc_djordjevic_sarkar(f, mat_params)

    # 計算阻抗
    Z0, eps_eff = calc_hammerstad_microstrip(W, H, t, Dk_f, EF)

    # 計算損耗
    IL_dB_m, _ = calc_total_insertion_loss(f, W, H, t, Dk_f, Df_f, EF, mat_params["Rz_um"], mat_params["rho"])
    IL_dB_in = IL_dB_m * 0.0254 # 轉換為 dB/inch

    markdown("### 🎯 計算結果")
    res_col1, res_col2, res_col3 = columns(3)
    res_col1.metric("特性阻抗 $Z_0$", f"{Z0:.2f} Ω")
    res_col2.metric("有效介電常數 $\epsilon_{eff}$", f"{eps_eff:.3f}")
    res_col3.metric("插入損耗 $IL$ (dB/in)", f"{IL_dB_in:.3f} dB/in @ {freq_GHz} GHz")

    markdown("### 📝 參數代入步驟")
    markdown(rf"""$D_k({freq_GHz}\text{{GHz}}) = {Dk_f:.3f}, \quad D_f({freq_GHz}\text{{GHz}}) = {Df_f:.4f}$""")
    markdown(rf"$W_{{eq}} = {W_mil} - \frac{{{t_mil}}}{{{EF}}} = {W_mil - t_mil/EF:.2f} \text{{ mil}}$")
    markdown(rf"$Z_0 = \frac{{60}}{{\sqrt{{{eps_eff:.3f}}}}} \ln\left(\dots\right) = {Z0:.2f} \Omega$")

    # 損耗頻譜掃描 (CSV 匯出準備)
    markdown("### 📊 損耗頻譜掃描 (4-12 GHz)")
    freqs = linspace(4e9, 12e9, 81)
    IL_data = []
    for f_scan in freqs:
        Dk_s, Df_s = calc_djordjevic_sarkar(f_scan, mat_params)
        il, _ = calc_total_insertion_loss(f_scan, W, H, t, Dk_s, Df_s, EF, mat_params["Rz_um"], mat_params["rho"])
        IL_data.append({"Freq_GHz": f_scan/1e9, "IL_dB_in": il * 0.0254})

    df = DataFrame(IL_data)
    line_chart(df.set_index("Freq_GHz"), y="IL_dB_in", x_label="Frequency (GHz)", y_label="Insertion Loss (dB/in)")

    # CSV 匯出 (Q9)
    csv = df.to_csv(index=False).encode('utf-8')
    download_button("📥 匯出損耗掃描數據 (CSV)", csv, "IL_Sweep_Data.csv", "text/csv")


elif mode == "逆工程：目標阻抗反推線寬":
    header("🔄 逆工程：目標阻抗反推線寬")
    markdown("給定目標阻抗與疊構，使用 Scipy 優化器反推最佳線寬，並嚴格限制在製造工藝邊界內。")

    target_Z = number_input("目標阻抗 $Z_0$ (Ω)", value=50.0, min_value=10.0, max_value=150.0)
    freq_GHz = slider("參考頻率 (GHz)", 4.0, 12.0, 10.0, 0.1)
    f = freq_GHz * 1e9

    markdown("#### 🏭 製造工藝邊界約束 (Q13)")
    col_b1, col_b2 = columns(2)
    with col_b1:
        W_min_mil = number_input("最小線寬 (mil)", value=3.0, min_value=1.0)
    with col_b2:
        W_max_mil = number_input("最大線寬 (mil)", value=30.0, min_value=5.0)

    W_min = W_min_mil * 25.4e-6
    W_max = W_max_mil * 25.4e-6

    if button("🚀 執行逆工程計算"):
        Dk_f, _ = calc_djordjevic_sarkar(f, mat_params)

        with spinner("正在使用 Scipy L-BFGS-B 優化器求解..."):
            W_opt, error = inverse_engineering(target_Z, H, t, Dk_f, EF, W_min, W_max)

        if W_opt is not None:
            W_opt_mil = W_opt / 25.4e-6
            success(f"✅ 最佳線寬求解成功！")
            metric("建議線寬 (W)", f"{W_opt_mil:.2f} mil")
            metric("驗證阻抗", f"{target_Z + sqrt(error):.2f} Ω")

            markdown("### 📝 逆工程數學推導步驟")
            latex(r"\text{目標函數: } \min_{W} \left( Z_0(W) - Z_{target} \right)^2")
            latex(r"\text{約束條件: } W_{min} \le W \le W_{max}")
            latex(f"\text{初始猜測值: } W_0 = H = {H_mil} \text{{ mil}}")
            latex(f"\text{最終收斂值: } W_{{opt}} = {W_opt_mil:.2f} \text{{ mil}}")
        else:
            error("❌ 優化失敗，請檢查目標阻抗是否在物理可行範圍內。")

with sidebar:
# markdown("---")
  caption("Developed by Qwen3.7 | Phase 1 Implementation | 2026-09-15")
