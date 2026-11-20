from streamlit import button, column_config, columns, data_editor, header, info, markdown, metric, number_input, rerun, radio, session_state, set_page_config, slider, spinner, success, tabs, title, warning, sidebar, subheader, download_button, pyplot
from io import BytesIO
from base64 import b64encode
from datetime import datetime
from pandas import DataFrame
from numpy import linspace
from 數學模型擴展 import calc_symmetric_stripline, calc_diff_microstrip, inverse_engineering_meas_Dk, inverse_engineering_meas_W, calc_return_loss
from 數學模型 import calc_djordjevic_sarkar, calc_hammerstad_microstrip, calc_total_insertion_loss, 共平面1b1a
from matplotlib.pyplot import subplots
### 📂 檔案 2：`app_v2.py` (Streamlit 主程式重構與疊構管理) 此檔案引入了 **Tabs 分頁** 與 **`data_editor` 動態表格**，完美實現了 Polar 風格的疊構模板管理。

#"""
#Streamlit 高頻傳輸線模擬與逆工程平台 (Phase 2)
#引入：動態疊構管理 (Data Editor)、多截面支援、實測逆向工程。
#"""
# import streamlit as st
# import pandas as pd
# import numpy as np

# 導入模組 (假設已整合)
from 材質庫 import MATERIALS_DB, get_material_params
# from math_models_v2 import *

# ==========================================
# 1. 疊構模板與 Session State 管理
# ==========================================
def init_stackup():
    if "stackup" not in session_state:
        session_state.stackup = DataFrame([
            {"Layer": "C1 (Top)", "Type": "Copper", "Thickness_um": 35, "Material": "Copper", "Rz_um": 2.0},
            {"Layer": "D1 (PP)", "Type": "Dielectric", "Thickness_um": 200, "Material": "Rogers 4003C (High Freq)", "Rz_um": 0.0},
            {"Layer": "C2 (Inner)", "Type": "Copper", "Thickness_um": 35, "Material": "Copper", "Rz_um": 2.0},
            {"Layer": "D2 (Core)", "Type": "Dielectric", "Thickness_um": 800, "Material": "Isola 370HR (Mid Freq)", "Rz_um": 0.0},
            {"Layer": "C3 (Inner)", "Type": "Copper", "Thickness_um": 35, "Material": "Copper", "Rz_um": 2.0},
            {"Layer": "D3 (PP)", "Type": "Dielectric", "Thickness_um": 200, "Material": "Rogers 4003C (High Freq)", "Rz_um": 0.0},
            {"Layer": "C4 (Bot)", "Type": "Copper", "Thickness_um": 35, "Material": "Copper", "Rz_um": 2.0},
        ])

def load_template(template_name):
    if template_name == "4-Layer Rigid (Foil Build)":
        session_state.stackup = DataFrame([
            {"Layer": "C1", "Type": "Copper", "Thickness_um": 35, "Material": "Copper", "Rz_um": 2.0},
            {"Layer": "D1", "Type": "Dielectric", "Thickness_um": 200, "Material": "Isola 370HR (Mid Freq)", "Rz_um": 0.0},
            {"Layer": "C2", "Type": "Copper", "Thickness_um": 35, "Material": "Copper", "Rz_um": 2.0},
            {"Layer": "D2", "Type": "Dielectric", "Thickness_um": 800, "Material": "Isola 370HR (Mid Freq)", "Rz_um": 0.0},
            {"Layer": "C3", "Type": "Copper", "Thickness_um": 35, "Material": "Copper", "Rz_um": 2.0},
            {"Layer": "D3", "Type": "Dielectric", "Thickness_um": 200, "Material": "Isola 370HR (Mid Freq)", "Rz_um": 0.0},
            {"Layer": "C4", "Type": "Copper", "Thickness_um": 35, "Material": "Copper", "Rz_um": 2.0},
        ])
    elif template_name == "6-Layer Rigid (Core Build)":
        # 簡化模板，實際可擴充
        session_state.stackup = DataFrame([
            {"Layer": f"L{i+1}", "Type": "Copper" if i%2==0 else "Dielectric",
             "Thickness_um": 35 if i%2==0 else 200,
             "Material": "Copper" if not i%2 else "Shengyi S1000-2 (Standard FR4)",
             "Rz_um": 2.0 if not i%2 else 0.0} for i in range(11)
        ])

# ==========================================
# 2. UI 佈局與 Tabs 管理
# ==========================================
set_page_config(page_title="高頻傳輸線模擬平台 V2", layout="wide")
title("📡 高頻傳輸線模擬與逆工程平台 (Phase 2)")

tab2, tab3, tab4, tab5 = tabs([
    # "📐 1. 截面阻抗與損耗計算",
    "🏗️ 2. 疊構管理與模板 (Stackup)",
    "🔄 3. 實測逆向工程 (TDR/VNA)",
    "📊 4. IL/RL 深度頻譜", "📑 5. 專業報告生成"
])
# 在 app_v3.py 的 Tab 1 區塊進行修改

# ... (前面的程式碼)

# ==========================================
# Tab 1: 截面阻抗計算 (整合 Phase 1 & 2)
# ==========================================
with sidebar:
    subheader("📐 截面阻抗與損耗計算")

    # 從疊構中自動提取參數 (簡化邏輯：假設計算 C1，參考平面為 C2)
    if len(session_state.stackup) >= 3:
        sig_layer = session_state.stackup.iloc[0]
        dielectric_layer = session_state.stackup.iloc[1]

        # col_s1, col_s2, col_s3 = columns(3)
        # with col_s1:
        section_type = radio("截面類型", ["Surface Microstrip", "Symmetric Stripline", "Differential Microstrip", "Offset Coplanar Waveguide (1B1A)"], horizontal=True)
        # with col_s2:
        W_mil = number_input("線寬 W (mil)", value=8.0, step=0.5)
        # with col_s3:
        if section_type == "Differential Microstrip":
            S_mil = number_input("線距 S (mil)", value=8.0, step=0.5)
        else:
            S_mil = 0.0

        # 單位轉換
        W = W_mil * 25.4e-6
        S = S_mil * 25.4e-6
        H = dielectric_layer["Thickness_um"] * 1e-6
        t = sig_layer["Thickness_um"] * 1e-6
        EF = slider("蝕刻因子 (EF)", 1.0, 10.0, 3.0)

        # 獲取材料參數 (簡化：直接取 Dk 標稱值)
        mat_name = dielectric_layer["Material"]
        # mat_params = get_material_params(mat_name)
        # 這裡為了演示，硬編碼一個 Dk
        Dk_map = {"Rogers 4003C (High Freq)": 3.55, "Isola 370HR (Mid Freq)": 4.00, "Shengyi S1000-2 (Standard FR4)": 4.50}
        Dk = Dk_map.get(mat_name, 4.2)
        Rz = sig_layer["Rz_um"]

        freq_GHz = slider("計算頻率 (GHz)", 4.0, 12.0, 10.0, 0.1)
        f = freq_GHz * 1e9

        # if button("🚀 計算截面參數"):
        if section_type == "Surface Microstrip":
            # 調用 Phase 1 的 calc_hammerstad_microstrip (此處省略 import，直接寫結果)
            Z0 = 50.0 # 佔位符
            info("Surface Microstrip 計算邏輯同 Phase 1...")
        elif section_type == "Symmetric Stripline":
            # 帶狀線需要上下兩個介質層，此處簡化假設對稱
            b = H * 2
            Z0, _ = calc_symmetric_stripline(W, b, t, Dk, EF)
            metric("對稱帶狀線阻抗 $Z_0$", f"{Z0:.2f} Ω")
        elif section_type == "Differential Microstrip":
            Z_diff, Z_se, _ = calc_diff_microstrip(W, S, H, t, Dk, EF)
            metric("差分阻抗 $Z_{diff}$", f"{Z_diff:.2f} Ω")
            metric("單端阻抗 $Z_{se}$", f"{Z_se:.2f} Ω")
        elif section_type == "Offset Coplanar Waveguide (1B1A)":
          def 共平面():
                markdown("#### 📊 Offset CPW 1B1A 參數 (參考 Mantaro/Polar)")
            # col_c1, col_c2, col_c3 = columns(3)

            # with col_c1:
                H1_um = number_input("Substrate 1 Height (H1) [um]", value=62.50*25.4, step=1.0, help="下基板厚度") # 預設 62.5 mil -> um
                Er1 = number_input("Substrate 1 Dielectric (Er1)", value=3.3000, step=0.01)
                W1_mil = number_input("Lower Trace Width (W1) [mil]", value=65.00, step=0.1, help="梯形截面底部寬度")

            # with col_c2:
                H2_um = number_input("Substrate 2 Height (H2) [um]", value=50.20*25.4, step=1.0, help="上基板厚度")
                Er2 = number_input("Substrate 2 Dielectric (Er2)", value=3.3000, step=0.01)
                W2_mil = number_input("Upper Trace Width (W2) [mil]", value=44.00, step=0.1, help="梯形截面頂部寬度")

            # with col_c3:
                D1_mil = number_input("Ground Strip Separation (D1) [mil]", value=171.00, step=0.1, help="接地帶內緣總距離")
                T1_mil = number_input("Trace Thickness (T1) [mil]", value=0.20, step=0.05, help="銅厚")

            # 計算按鈕
            # if button(" 計算 Offset CPW 阻抗"):
                # with spinner("正在進行保角變換計算..."):
                info(f"💡 **結構分析**: 信號線位於 H1/H2 交界處，梯形截面 (下寬 {W1_mil} mil, 上寬 {W2_mil} mil)。接地帶間距 {D1_mil} mil。")
                Z0_cpw, eps_eff_cpw = 共平面1b1a(H1_um, Er1, H2_um, Er2, W1_mil, W2_mil, D1_mil, T1_mil)
                return Z0_cpw, eps_eff_cpw
          Z0_cpw, eps_eff_cpw=共平面()
          markdown("### 🎯 Offset CPW 計算結果")
          res_col1, res_col2 = columns(2)
          res_col1.metric("特性阻抗 $Z_0$", f"{Z0_cpw:.2f} Ω")
          res_col2.metric("有效介電常數 $\epsilon_{eff}$", f"{eps_eff_cpw:.3f}")

# ==========================================
# Tab 2: 疊構管理 (優先展示，因為這是 Phase 2 核心)
# ==========================================
with tab2:
    header("🏗️ PCB 疊構管理器 (Stackup Manager)")
    markdown("支援動態增刪層、修改材料與厚度。可一鍵載入 Polar 風格的標準模板。")

    col_t1, col_t2 = columns(2)
    with col_t1:
        if button("🔄 載入 4 層 Rigid 模板"):
            load_template("4-Layer Rigid (Foil Build)")
            rerun()
    with col_t2:
        if button("🔄 載入 6 層 Rigid 模板"):
            load_template("6-Layer Rigid (Core Build)")
            rerun()

    init_stackup()

    # 使用 data_editor 實現完美的表格編輯
    edited_stackup = data_editor(
        session_state.stackup,
        num_rows="dynamic", # 允許動態增刪行
        use_container_width=True,
        column_config={
            "Layer": column_config.TextColumn("層名稱", width="small"),
            "Type": column_config.SelectboxColumn("類型", options=["Copper", "Dielectric"], required=True),
            "Thickness_um": column_config.NumberColumn("厚度 (um)", min_value=1, step=5),
            "Material": column_config.SelectboxColumn("材料", options=["Copper", "Rogers 4003C (High Freq)", "Isola 370HR (Mid Freq)", "Shengyi S1000-2 (Standard FR4)"]),
            "Rz_um": column_config.NumberColumn("粗糙度 Rz (um)", min_value=0.0, step=0.5, help="僅銅層有效"),
        },
        hide_index=True,
        key="stackup_editor"
    )
    session_state.stackup = edited_stackup



# ==========================================
# Tab 3: 實測逆向工程 (Phase 2 新增)
# ==========================================
with tab3:
    header("🔄 實測逆向工程 (TDR / VNA 數據反推)")
    markdown("輸入實測數據，反推實際的物理參數偏差，用於評估 PCB 廠製造能力或板材真實 Dk。")

    mode_rev = radio("選擇反推場景", ["場景 A：實測阻抗反推實際 Dk", "場景 B：實測阻抗反推實際線寬 (評估蝕刻)"], horizontal=True)

    col_r1, col_r2 = columns(2)
    with col_r1:
        Z_meas = number_input("實測阻抗 $Z_{meas}$ (Ω)", value=48.5, step=0.1)
    with col_r2:
        if mode_rev.startswith("場景 A"):
            W_nominal_mil = number_input("設計線寬 (mil)", value=8.0)
        else:
            Dk_nominal = number_input("設計 Dk", value=4.2)

    H_mil_rev = number_input("介質厚度 H (mil)", value=8.0)
    t_mil_rev = number_input("銅厚 t (mil)", value=1.4)
    EF_rev = slider("蝕刻因子", 1.0, 10.0, 3.0)

    # if button("🔍 執行實測反推"):
    def 實測反推():
        H_rev = H_mil_rev * 25.4e-6
        t_rev = t_mil_rev * 25.4e-6

        if mode_rev.startswith("場景 A"):
            W_rev = W_nominal_mil * 25.4e-6
            # with spinner("正在反推實際 Dk..."):
            actual_Dk = inverse_engineering_meas_Dk(Z_meas, W_rev, H_rev, t_rev, EF_rev)
            if actual_Dk:
                success(f"✅ 反推成功！實際板材 Dk 約為: **{actual_Dk:.3f}**")
                warning(f"⚠️ 與設計值 (4.200) 相比，偏差: {((actual_Dk-4.2)/4.2)*100:.2f}%")
        else:
            # with spinner("正在反推實際線寬..."):
            actual_W = inverse_engineering_meas_W(Z_meas, H_rev, t_rev, Dk_nominal, EF_rev, 3e-6, 30e-6)
            if actual_W:
                actual_W_mil = actual_W / 25.4e-6
                success(f"✅ 反推成功！實際蝕刻後線寬約為: **{actual_W_mil:.2f} mil**")
    實測反推()

# app_v3.py (新增 Tab 4 & Tab 5 的邏輯)
# import matplotlib.pyplot as plt

# 在 tabs 中加入新分頁
# tab1, tab2, tab3, tab4, tab5 = tabs([
#     "📐 1. 截面阻抗", "🏗️ 2. 疊構管理", "🔄 3. 實測逆向",
#     "📊 4. IL/RL 深度頻譜", "📑 5. 專業報告生成"
# ])

# ==========================================
# Tab 4: IL/RL 深度頻譜分析
# ==========================================
with tab4:
    header("📊 IL / RL 深度頻譜分析 (4-12 GHz)")
    markdown("分析傳輸線在頻域上的插入損耗 (IL) 與回波損耗 (RL) 權衡。")

    col_f1, col_f2 = columns(2)
    with col_f1:
        Z_target_sys = number_input("系統目標阻抗 $Z_{target}$ (Ω)", value=50.0, step=1.0)
    with col_f2:
        freq_range = slider("頻率掃描範圍 (GHz)", 4.0, 12.0, (4.0, 12.0))

    # if button("🚀 生成 IL/RL 頻譜圖"):
    def 頻譜圖():
        # 假設這裡已經從 Tab 1 獲取了 W, H, t, Dk, EF, 材料參數等 (實際應用中需透過 session_state 傳遞)
        # 此處為演示邏輯，使用固定參數
        W_demo, H_demo, t_demo, EF_demo = 8e-6*25.4, 8e-6*25.4, 1.4e-6*25.4, 3.0
        mat_demo = get_material_params("Isola 370HR (Mid Freq)")

        freqs = linspace(freq_range[0]*1e9, freq_range[1]*1e9, 81)
        IL_data, RL_data = [], []

        for f in freqs:
            Dk_f, Df_f = calc_djordjevic_sarkar(f, mat_demo)
            Z0, _ = calc_hammerstad_microstrip(W_demo, H_demo, t_demo, Dk_f, EF_demo)
            il, _ = calc_total_insertion_loss(f, W_demo, H_demo, t_demo, Dk_f, Df_f, EF_demo, mat_demo["Rz_um"], mat_demo["rho"])
            rl = calc_return_loss(Z0, Z_target_sys)

            IL_data.append(il * 0.0254) # dB/in
            RL_data.append(rl)

        # 繪製雙 Y 軸圖表 (Matplotlib)
        fig, ax1 = subplots(figsize=(10, 5))
        color_il = 'tab:red'
        ax1.set_xlabel('Frequency (GHz)')
        ax1.set_ylabel('Insertion Loss (dB/in)', color=color_il)
        ax1.plot(freqs/1e9, IL_data, color=color_il, linewidth=2, label='IL (dB/in)')
        ax1.tick_params(axis='y', labelcolor=color_il)
        ax1.grid(True, linestyle='--', alpha=0.6)

        ax2 = ax1.twinx()
        color_rl = 'tab:blue'
        ax2.set_ylabel('Return Loss (dB)', color=color_rl)
        ax2.plot(freqs/1e9, RL_data, color=color_rl, linewidth=2, label='RL (dB)')
        ax2.tick_params(axis='y', labelcolor=color_rl)

        # 添加 RL 建議基準線 (例如 -10dB 或 -15dB)
        ax2.axhline(y=-15, color='gray', linestyle=':', label='RL Margin (-15dB)')

        fig.tight_layout()
        pyplot(fig)

        # 將圖表轉為 Base64 供報告使用
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_base64 = b64encode(buf.read()).decode('utf-8')
        session_state['report_img'] = img_base64
        session_state['report_freqs'] = freqs/1e9
        session_state['report_il'] = IL_data
        session_state['report_rl'] = RL_data
    頻譜圖()
# ==========================================
# Tab 5: 專業報告生成與匯出 (Markdown 版本)
# ==========================================
with tab5:
    header("📑 專業工程報告生成 (Markdown)")
    markdown("生成純文字 Markdown 報告，完美支援 LaTeX 公式與圖表嵌入，適合版本控制與技術文件管理。")

    # if button("📝 生成 Markdown 報告"):
    def 渲染():
        # 1. 獲取當前時間與參數
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        img_b64 = session_state.get('report_img', '')

        # 2. 使用 Raw String 定義 LaTeX 公式 (避免 f-string 的轉義災難)
        formula_impedance = r"$$ Z_0 = \frac{60}{\sqrt{\epsilon_{eff}}} \ln\left(\frac{8h}{w_{eq}} + 0.25\frac{w_{eq}}{h}\right) $$"
        formula_etch = r"$$ w_{eq} = \frac{w_{top} + (w_{top} - 2t/EF)}{2} $$"
        formula_roughness = r"$$ K_{sr} = 1 + \frac{2}{\pi} \arctan\left(1.4 \left(\frac{R_q}{\delta}\right)^2\right) $$"

        # 3. 構建 Markdown 內容
        md_content = session_state['報告內容']=f"""# 📡 高頻傳輸線模擬與逆工程分析報告

**報告生成時間:** {now}
**分析頻段:** 4.0 GHz - 12.0 GHz
**系統目標阻抗:** {Z_target_sys} Ω



## 1. 疊構與材料參數 (Stackup & Materials)

| 層別 | 類型 | 厚度 (um) | 材料 | 粗糙度 Rz (um) |
| :--- | :--- | :--- | :--- | :--- |
| C1 (Top) | Copper | 35 | Copper | 2.0 |
| D1 (PP) | Dielectric | 200 | Isola 370HR | - |
| C2 (Inner) | Copper | 35 | Copper | 2.0 |



## 2. 核心物理推導 (Physical Derivation)

**Hammerstad-Jensen 阻抗模型 (含梯形蝕刻修正):**

{formula_impedance}

其中等效線寬 $w_{{eq}}$ 考慮了蝕刻因子 $EF$:

{formula_etch}

**Hammerstad 粗糙度損耗修正:**

{formula_roughness}



## 3. IL / RL 頻譜分析結果

下圖展示了在 4-12 GHz 頻段內，考慮色散效應與表面粗糙度後的插入損耗 (IL) 與相對於 {Z_target_sys} Ω 系統阻抗的回波損耗 (RL)。

![IL/RL Spectrum](data:image/png;base64,{img_b64})



*Generated by Streamlit 高頻傳輸線模擬平台 (Phase 3) | Powered by Qwen3.7*
"""

    # 4. 在 Streamlit 網頁上直接預覽 Markdown 渲染結果
    markdown("### 📖 報告預覽")
    渲染()
    報告=session_state['報告內容']
    markdown(報告)

    # 5. 提供 Markdown 檔案下載
    download_button(
        label="📥 下載 Markdown 報告 (.md)",
        data=報告,
        file_name="Transmission_Line_Analysis_Report.md",
        mime="text/markdown"
    )
    success("✅ 報告已生成！您可以直接在上方預覽，或下載 `.md` 檔案。使用 Typora / Obsidian 等編輯器開啟即可看到完美的 LaTeX 公式與圖表。")
