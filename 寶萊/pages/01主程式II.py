from streamlit import button, cache_resource, caption, checkbox, columns, dataframe, error, expander, info, json, markdown, number_input, plotly_chart, radio, rerun, select_slider, session_state, set_page_config, sidebar, subheader, success, tabs, text_input, title
from plotly.graph_objects import Figure, Pie, Scatter
from numpy import linspace, sqrt
from json import load
from pandas import DataFrame
from sys import path
# ========== 6. 更新 app.py 加入模組 B ==========

#"""
#PCB Transmission Line Calculator — Phase 2
#Streamlit 主應用
#Phase 1: 阻抗計算 + 參數掃描
#Phase 2: 叠構損耗分析 (IL/RL) + 材料庫管理
#"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import json
from pathlib import Path

# ---------- 路徑設置 ----------
PROJECT_ROOT = Path(__file__).parent.parent
import sys
# path.insert(0, str(PROJECT_ROOT))

from modules.impedance.solver import forward_calc, inverse_calc
from modules.impedance.sweep import param_sweep, freq_sweep as imp_freq_sweep
from modules.stackup.materials import MaterialLibrary, Material
from modules.stackup.templates import TemplateLibrary, StackupTemplate
from modules.stackup.loss_models import (
    total_insertion_loss, return_loss, freq_sweep_il,
    conductor_loss_hammerstad, conductor_loss_huray, dielectric_loss
)
from util.project_io import save_project, load_project
#材料=PROJECT_ROOT/'data'/'materials.json'
#with open(材料) as fin:
#  data = json.load(fin)

# ---------- 頁面配置 ----------
set_page_config(
    page_title="PCB Transmission Line Calculator",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)
from streamlit import empty, pyplot
狀態=empty()
# mat_lib = MaterialLibrary(PROJECT_ROOT / "data")
# 狀態.code(mat_lib.list_all())
#['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__firstlineno__', '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__static_attributes__', '__str__', '__subclasshook__', '__weakref__', '_load_builtin', '_load_custom', '_materials', '_save_custom', 'add_custom', 'data_dir', 'delete_custom', 'get', 'list_all', 'list_builtin']

# ---------- 加載材料庫與模板庫 ----------
@cache_resource
def get_libraries():
    mat_lib = MaterialLibrary(PROJECT_ROOT / "data")
    tpl_lib = TemplateLibrary(PROJECT_ROOT / "data")
    return mat_lib, tpl_lib

mat_lib, tpl_lib = get_libraries()
MENU, 表單=[], ['', '', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  # menu=radio('表單', MENU, horizontal=True, index=0)
  # 本益比=slider("最高本益比(PE)", 0, 100, 25)
  # srch=text_input('搜尋', '')
# ---------- Sidebar ----------
  subheader("🔧 PCB 傳輸線工具箱")
  markdown("**Phase 2** — 阻抗計算 + 叠構損耗分析")
  page=radio("功能導航", ["📐 阻抗計算器", "📊 參數掃描", "📐 叠構損耗分析", "📋 材料庫管理", "💾 項目文件"], index=0, horizontal=True)
# mat_lib.list_all()
  markdown("### 📋 材料庫速覽")
  builtin_mats = mat_lib.list_builtin()
  if builtin_mats:
      mat_df = DataFrame([
          {
              "材料": name,
              "Dk": mat_lib.get(name).dk,
              "Df": mat_lib.get(name).df,
              "粗糙度": mat_lib.get(name).get_roughness_model(),
              "類別": mat_lib.get(name).category
          }
          for name in builtin_mats
      ])
      mat_df
    # dataframe(, use_container_width=True, hide_index=True)

# ---------- Session State 初始化 ----------
if "calc_history" not in session_state:
    session_state.calc_history = []
if "last_params" not in session_state:
    session_state.last_params = {}
if "custom_materials" not in session_state:
    session_state.custom_materials = {}


def store_params(section, data):
    session_state.last_params[section] = data


# ============================================================
#  Page 1: 阻抗計算器 (Phase 1, 不變)
# ============================================================
if page == "📐 阻抗計算器":
    title("📐 傳輸線阻抗計算器")
    markdown("基于 **Hammerstad-Jensen** (Microstrip) 與 **Wheeler** (Stripline) 公式")

    左, 右 = columns([2, 3])

    with 左:
        subheader("⚙️ 參數輸入")

        tline_type = radio("傳輸線類型", ["Microstrip", "Stripline"])
        mat_names = mat_lib.list_all()
        mat_name = radio("基材材料", mat_names, index=0)
        material = mat_lib.get(mat_name)
        er = material.dk
        caption(f"介電常數 Dk = **{er}** | 損耗因子 Df = **{material.df}**")

        c1, c2 = columns(2)
        with c1:
            w = number_input("線寬 w (mm)", min_value=0.001, value=0.300, step=0.010, format="%.3f")
            h = number_input("介質厚度 h (mm)", min_value=0.010, value=1.600, step=0.010, format="%.3f")
        with c2:
            t_um = number_input("銅厚 t (μm)", min_value=0.0, value=35.0, step=1.0)
            freq = number_input("頻率 (GHz)", min_value=0.0, value=1.0, step=0.1)

        t = t_um / 1000.0
        mode = radio("計算模式", ["正向計算", "反向計算"], horizontal=True)

        target_z0 = None
        if mode == "反向計算":
            target_z0 = number_input("目標阻抗 Z₀ (Ω)", min_value=10.0, max_value=200.0, value=50.0, step=0.1)

        do_freq_sweep = checkbox("顯示頻率掃描曲線 (0.1 ~ 10 GHz)", value=False)
        # calc_btn = button("🚀 執行計算", type="primary", use_container_width=True)

    with 右:
        subheader("📊 計算結果")

        # if calc_btn:
        if mode == "正向計算":
            z0, e_eff = forward_calc(tline_type, w, h, t, er, freq)
            store_params("impedance", {
                "tline_type": tline_type, "mat_name": mat_name, "w_mm": w,
                "h_mm": h, "t_um": t_um, "er": er, "freq_ghz": freq,
                "mode": "正向", "Z0": z0, "e_eff": e_eff
            })
            session_state.calc_history.append({
                "類型": tline_type, "模式": "正向", "w(mm)": w, "h(mm)": h,
                "t(μm)": t_um, "Z₀(Ω)": round(z0, 2), "εeff": round(e_eff, 3)
            })

            r1, r2, r3 = columns(3)
            r1.metric("特性阻抗 Z₀", f"{z0:.2f} Ω")
            r2.metric("有效介電常數 εeff", f"{e_eff:.3f}")
            if freq > 0:
                lambda_g = 300.0 / (freq * sqrt(e_eff))
                r3.metric("導波波長 λg", f"{lambda_g:.2f} mm")
            else:
                r3.metric("導波波長 λg", "N/A (DC)")

            if abs(z0 - 50.0) < 3.0:
                success("✅ 非常接近 50Ω 標準阻抗")
            elif abs(z0 - 50.0) < 10.0:
                info("ℹ️ 接近 50Ω，可微調幾何參數")
            elif z0 < 50.0:
                info("💡 提示：減小線寬 或 增加介質厚度 → 可提高阻抗")
            else:
                info("💡 提示：增加線寬 或 減小介質厚度 → 可降低阻抗")

            if do_freq_sweep:
                freqs = linspace(0.1, 10.0, 100)
                df_freq = imp_freq_sweep(tline_type, w, h, t, er, freqs)
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                    subplot_titles=("Z₀ vs 頻率", "εeff vs 頻率"),
                                    vertical_spacing=0.12)
                fig.add_trace(Scatter(x=df_freq["freq_ghz"], y=df_freq["Z0"],
                                           mode="lines", line=dict(color="#00bc8c", width=2)), row=1, col=1)
                fig.add_trace(Scatter(x=df_freq["freq_ghz"], y=df_freq["e_eff"],
                                           mode="lines", line=dict(color="#f39c12", width=2)), row=2, col=1)
                fig.update_xaxes(title_text="頻率 (GHz)", row=2, col=1)
                fig.update_yaxes(title_text="Z₀ (Ω)", row=1, col=1)
                fig.update_yaxes(title_text="εeff", row=2, col=1)
                fig.update_layout(height=520, showlegend=False, template="plotly_white")
                plotly_chart(fig, use_container_width=True)

        else:
            if target_z0 is None:
                target_z0 = 50.0
            w_calc = inverse_calc(tline_type, target_z0, h, t, er, freq)
            if w_calc:
                z0_verify, _ = forward_calc(tline_type, w_calc, h, t, er, freq)
                store_params("impedance", {
                    "tline_type": tline_type, "target_Z0": target_z0,
                    "w_mm": w_calc, "verified_Z0": z0_verify
                })
                success(f"所需線寬: **{w_calc * 1000:.2f} μm**")
                caption(f"驗證計算: Z₀ = {z0_verify:.2f} Ω")
            else:
                error("❌ 無法收斂到目標阻抗。請檢查參數範圍。")

        if session_state.calc_history:
            with expander("📜 最近計算歷史", expanded=False):
                hist_df = DataFrame(session_state.calc_history[-10:])
                dataframe(hist_df, use_container_width=True, hide_index=True)


# ============================================================
#  Page 2: 參數掃描 (Phase 1, 不變)
# ============================================================
elif page == "📊 參數掃描":
    title("📊 單參數掃描分析")
    markdown("掃描單一幾何參數對特性阻抗 Z₀ 與有效介電常數 εeff 的影響")

    col_cfg, col_plot = columns([1, 2])

    mat_lib = MaterialLibrary(PROJECT_ROOT / "data")
    with col_cfg:
        subheader("⚙️ 掃描配置")
        tline_type = radio("傳輸線類型", ["Microstrip", "Stripline"], key="sweep_tline")
        mat_names = mat_lib.list_all()
        mat_name = radio("基材材料", mat_names, key="sweep_mat")
        material = mat_lib.get(mat_name)
        er = material.dk

        sweep_param = radio("掃描參數",
            ["w_mm", "h_mm", "t_um", "er"],
            format_func=lambda x: {"w_mm": "線寬 w (mm)", "h_mm": "介質厚度 h (mm)",
                                   "t_um": "銅厚 t (μm)", "er": "介電常數 Dk"}[x])

        c1, c2, c3 = columns(3)
        with c1:
            p_min = number_input("最小值", value=0.1 if sweep_param != "er" else 3.0, step=0.1)
        with c2:
            p_max = number_input("最大值", value=1.0 if sweep_param != "er" else 5.0, step=0.1)
        with c3:
            p_points = number_input("點數", min_value=10, max_value=500, value=50)

        markdown("---")
        subheader("🔒 固定參數")
        if sweep_param != "w_mm":
            w_fix = number_input("線寬 w (mm)", value=0.3, step=0.01, key="fix_w")
        else:
            w_fix = 0.3
        if sweep_param != "h_mm":
            h_fix = number_input("介質厚度 h (mm)", value=1.6, step=0.01, key="fix_h")
        else:
            h_fix = 1.6
        if sweep_param != "t_um":
            t_fix_um = number_input("銅厚 t (μm)", value=35.0, step=1.0, key="fix_t")
        else:
            t_fix_um = 35.0
        if sweep_param != "er":
            er_fix = er
            caption(f"固定 Dk = {er} ({mat_name})")
        else:
            er_fix = 4.5
        t_fix = t_fix_um / 1000.0
        freq_fix = number_input("頻率 (GHz)", value=1.0, step=0.1, key="sweep_freq")
        run_sweep = button("▶️ 開始掃描", type="primary", use_container_width=True)

    with col_plot:
        if run_sweep:
            sweep_vals = linspace(p_min, p_max, int(p_points))
            fixed = {"w": w_fix, "h": h_fix, "t": t_fix, "er": er_fix, "freq_ghz": freq_fix}
            df = param_sweep(tline_type, sweep_param, sweep_vals, fixed)

            param_label = {"w_mm": "線寬 w (mm)", "h_mm": "介質厚度 h (mm)",
                           "t_um": "銅厚 t (μm)", "er": "介電常數 Dk"}[sweep_param]

            fig = make_subplots(rows=1, cols=2,
                                subplot_titles=(f"Z₀ vs {param_label}", f"εeff vs {param_label}"))
            fig.add_trace(Scatter(x=df["param_val"], y=df["Z0"], mode="lines",
                                       line=dict(color="#3498db", width=2.5), fill="tozeroy",
                                       fillcolor="rgba(52,152,219,0.1)"), row=1, col=1)
            fig.add_trace(Scatter(x=df["param_val"], y=df["e_eff"], mode="lines",
                                       line=dict(color="#e74c3c", width=2.5), fill="tozeroy",
                                       fillcolor="rgba(231,76,60,0.1)"), row=1, col=2)
            fig.add_hline(y=50, line_dash="dash", line_color="gray",
                          annotation_text="50Ω", annotation_position="right", row=1, col=1)
            fig.update_xaxes(title_text=param_label)
            fig.update_yaxes(title_text="Z₀ (Ω)", row=1, col=1)
            fig.update_yaxes(title_text="εeff", row=1, col=2)
            fig.update_layout(template="plotly_white", showlegend=False, height=450)
            plotly_chart(fig, use_container_width=True)

            markdown("#### 🔑 關鍵統計")
            c1, c2, c3, c4 = columns(4)
            c1.metric("最小 Z₀", f"{df['Z0'].min():.2f} Ω")
            c2.metric("最大 Z₀", f"{df['Z0'].max():.2f} Ω")
            idx_50 = (df['Z0'] - 50.0).abs().idxmin()
            c3.metric(f"50Ω 對應 {param_label}", f"{df.loc[idx_50, 'param_val']:.3f}")
            c4.metric("該點實際 Z₀", f"{df.loc[idx_50, 'Z0']:.2f} Ω")

            with expander("📋 查看原始數據"):
                dataframe(df, use_container_width=True)


# ============================================================
#  Page 3: 叠構損耗分析 (Phase 2 - 新增)
# ============================================================
elif page == "📐 叠構損耗分析":
    title("📐 叠構損耗分析 (IL / RL)")
    markdown("基于叠構模板計算 **Insertion Loss** 與 **Return Loss** | DC ~ 10 GHz")

    col_cfg, col_result = columns([1, 2])

    with col_cfg:
        subheader("⚙️ 叠構配置")

        # 模板選擇
        categories = tpl_lib.get_categories()
        category = radio("叠構類別", categories)
        template_names = tpl_lib.get_template_names(category)
        template_name = radio("模板", template_names)
        template = tpl_lib.get(f"{category}/{template_name}")

        if template:
            caption(f"📋 {template.description}")
            caption(f"總厚度: **{template.get_total_thickness_mm():.3f} mm**")

            # 信號層選擇
            signal_layers = template.get_signal_layers()
            signal_names = [l["name"] for l in signal_layers]
            selected_signal = radio("分析的信號層", signal_names)
            signal_idx = template.find_signal_layer_position(selected_signal)

            # 獲取該層的介質環境
            h_above = template.get_dielectric_thickness_above(signal_idx)
            h_below = template.get_dielectric_thickness_below(signal_idx)
            h_eff = h_above + h_below  # 簡化: 總介質厚度

            # 獲取介質材料屬性
            dielectric_props = template.get_layer_material_props(signal_idx + 1)
            template_dk = dielectric_props["dk"]
            template_df = dielectric_props["df"]

            markdown("---")
            subheader("🔧 傳輸線參數")

            # 材料覆蓋
            override_mat = checkbox("使用自定義材料覆蓋模板材料", value=False)
            if override_mat:
                mat_names = mat_lib.list_all()
                mat_name = radio("選擇材料", mat_names, key="loss_mat")
                material = mat_lib.get(mat_name)
                er = material.dk
                df_base = material.df
                roughness_model = material.get_roughness_model()
                roughness_params = material.get_huray_params() if roughness_model == "huray" else {"Rq_um": material.get_roughness_rq()}
            else:
                er = template_dk
                df_base = template_df
                roughness_model = "hammerstad"
                roughness_params = {"Rq_um": 1.5}
                caption(f"使用模板材料: Dk={er}, Df={df_base}")

            c1, c2 = columns(2)
            with c1:
                w = number_input("線寬 w (mm)", min_value=0.001, value=0.300, step=0.01, key="loss_w")
                t_um = number_input("銅厚 t (μm)", min_value=0.0, value=35.0, step=1.0, key="loss_t")
            with c2:
                trace_len = number_input("線長 (m)", min_value=0.001, value=0.100, step=0.01, format="%.3f")
                z0_target = number_input("目標阻抗 Z₀ (Ω)", min_value=10.0, max_value=200.0, value=50.0, step=0.1)

            t = t_um / 1000.0
            h = h_eff if h_eff > 0 else 1.6

            markdown("---")
            subheader("📊 損耗模型")

            roughness_model_sel = radio("粗糙度模型",
                ["hammerstad", "huray"],
                format_func=lambda x: {"hammerstad": "Hammerstad-Jensen", "huray": "Huray 雪球"}[x],
                index=0 if roughness_model == "hammerstad" else 1)

            if roughness_model_sel == "huray":
                r_sphere = number_input("雪球半徑 (μm)", min_value=0.1, value=0.5, step=0.1)
                roughness_params = {"sphere_radius_um": r_sphere}
            else:
                rq = number_input("粗糙度 Rq (μm)", min_value=0.1, value=1.5, step=0.1)
                roughness_params = {"Rq_um": rq}

            df_model = radio("Df 頻率模型",
                ["constant", "djordjevic", "linear"],
                format_func=lambda x: {"constant": "固定 Df", "djordjevic": "Djordjevic-Sarkar", "linear": "線性"}[x])

            freq_range = select_slider("頻率範圍",
                options=["0.1-1 GHz", "0.1-5 GHz", "0.1-10 GHz", "1-10 GHz"],
                value="0.1-10 GHz")

            calc_loss_btn = button("🚀 計算損耗", type="primary", use_container_width=True)

    with col_result:
        if template and calc_loss_btn:
            subheader("📊 損耗分析結果")

            # 解析頻率範圍
            if freq_range == "0.1-1 GHz":
                freqs = linspace(0.1, 1.0, 50)
            elif freq_range == "0.1-5 GHz":
                freqs = linspace(0.1, 5.0, 100)
            elif freq_range == "1-10 GHz":
                freqs = linspace(1.0, 10.0, 100)
            else:
                freqs = linspace(0.1, 10.0, 200)

            # 計算阻抗
            from modules.impedance.formulas import microstrip_z0
            z0_static, e_eff_static = microstrip_z0(w, h, t, er, 0.0)

            # 頻率掃描損耗
            results = {
                "freq_ghz": [],
                "IL_total_db": [],
                "IL_db_per_m": [],
                "alpha_c": [],
                "alpha_d": [],
                "RL_db": [],
                "Z0": [],
                "e_eff": []
            }

            for f in freqs:
                # 頻率相依 Df
                if df_model == "djordjevic":
                    df_f = df_base * (f / 1.0) ** 0.005
                elif df_model == "linear":
                    df_f = df_base + 0.001 * (f - 1.0)
                else:
                    df_f = df_base

                # 頻率相依 Dk (簡化)
                er_f = er

                # 阻抗 (頻率色散)
                z0_f, e_eff_f = microstrip_z0(w, h, t, er_f, f)

                # 損耗計算
                il = total_insertion_loss(f, w, t, h, er_f, df_f, z0_f, e_eff_f,
                                           roughness_model_sel, roughness_params, trace_len)

                # RL
                rl = return_loss(f, z0_f, z0_target, z0_target)

                results["freq_ghz"].append(f)
                results["IL_total_db"].append(il["IL_total_db"])
                results["IL_db_per_m"].append(il["IL_db_per_m"])
                results["alpha_c"].append(il["alpha_c_db_per_m"])
                results["alpha_d"].append(il["alpha_d_db_per_m"])
                results["RL_db"].append(rl)
                results["Z0"].append(z0_f)
                results["e_eff"].append(e_eff_f)

            df_loss = DataFrame(results)

            # 關鍵指標卡片
            idx_1g = (df_loss["freq_ghz"] - 1.0).abs().idxmin()
            idx_5g = (df_loss["freq_ghz"] - 5.0).abs().idxmin()
            idx_10g = (df_loss["freq_ghz"] - 10.0).abs().idxmin()

            c1, c2, c3 = columns(3)
            c1.metric("IL @ 1 GHz", f"{df_loss.loc[idx_1g, 'IL_total_db']:.3f} dB")
            c2.metric("IL @ 5 GHz", f"{df_loss.loc[idx_5g, 'IL_total_db']:.3f} dB")
            c3.metric("IL @ 10 GHz", f"{df_loss.loc[idx_10g, 'IL_total_db']:.3f} dB")

            # IL 圖表
            fig_il = Figure()
            fig_il.add_trace(Scatter(x=df_loss["freq_ghz"], y=df_loss["IL_total_db"],
                                         mode="lines", name="總 IL",
                                         line=dict(color="#e74c3c", width=2.5)))
            fig_il.add_trace(Scatter(x=df_loss["freq_ghz"],
                                         y=df_loss["alpha_c"] * trace_len,
                                         mode="lines", name="導體損耗",
                                         line=dict(color="#3498db", width=1.5, dash="dash")))
            fig_il.add_trace(Scatter(x=df_loss["freq_ghz"],
                                         y=df_loss["alpha_d"] * trace_len,
                                         mode="lines", name="介電損耗",
                                         line=dict(color="#2ecc71", width=1.5, dash="dash")))
            fig_il.update_layout(title="Insertion Loss vs 頻率",
                                 xaxis_title="頻率 (GHz)", yaxis_title="IL (dB)",
                                 template="plotly_white", height=400)
            plotly_chart(fig_il, use_container_width=True)

            # RL 圖表
            fig_rl = Figure()
            fig_rl.add_trace(Scatter(x=df_loss["freq_ghz"], y=df_loss["RL_db"],
                                        mode="lines", name="RL",
                                        line=dict(color="#9b59b6", width=2.5),
                                        fill="tozeroy", fillcolor="rgba(155,89,182,0.1)"))
            fig_rl.add_hline(y=20, line_dash="dash", line_color="red",
                             annotation_text="-20 dB 警戒線", annotation_position="right")
            fig_rl.update_layout(title="Return Loss vs 頻率",
                                 xaxis_title="頻率 (GHz)", yaxis_title="RL (dB)",
                                 template="plotly_white", height=350)
            plotly_chart(fig_rl, use_container_width=True)

            # 損耗組成餅圖 (在 5GHz)
            fig_pie = Figure(data=[Pie(
                labels=["導體損耗", "介電損耗"],
                values=[df_loss.loc[idx_5g, "alpha_c"] * trace_len,
                        df_loss.loc[idx_5g, "alpha_d"] * trace_len],
                hole=0.4,
                marker_colors=["#3498db", "#2ecc71"]
            )])
            fig_pie.update_layout(title=f"損耗組成 @ {df_loss.loc[idx_5g, 'freq_ghz']:.1f} GHz",
                                  template="plotly_white", height=300)
            plotly_chart(fig_pie, use_container_width=True)

            # 原始數據
            with expander("📋 查看原始數據"):
                display_df = df_loss[["freq_ghz", "Z0", "e_eff", "IL_total_db",
                                      "alpha_c", "alpha_d", "RL_db"]].copy()
                display_df.columns = ["頻率(GHz)", "Z0(Ω)", "εeff", "IL(dB)",
                                    "αc(dB/m)", "αd(dB/m)", "RL(dB)"]
                dataframe(display_df.round(4), use_container_width=True)

            # 保存參數
            store_params("loss_analysis", {
                "template": f"{category}/{template_name}",
                "signal_layer": selected_signal,
                "material": mat_name if override_mat else "template_default",
                "w_mm": w, "t_um": t_um, "trace_len_m": trace_len,
                "roughness_model": roughness_model_sel,
                "df_model": df_model
            })


# ============================================================
#  Page 4: 材料庫管理 (Phase 2 - 新增)
# ============================================================
elif page == "📋 材料庫管理":
    title("📋 材料庫管理")
    markdown("查看內建材料、添加自定義材料")

    tab_view, tab_add = tabs(["📖 查看材料", "➕ 添加自定義材料"])

    with tab_view:
        subheader("內建材料")
        builtin = mat_lib.list_builtin()
        builtin_data = []
        for name in builtin:
            m = mat_lib.get(name)
            builtin_data.append({
                "材料名": name,
                "Dk": m.dk,
                "Df": m.df,
                "粗糙度模型": m.get_roughness_model(),
                "Rq (μm)": m.get_roughness_rq(),
                "類別": m.category
            })
        dataframe(DataFrame(builtin_data), use_container_width=True, hide_index=True)

        subheader("自定義材料")
        custom = [k for k in mat_lib.list_all() if k not in builtin]
        if custom:
            custom_data = []
            for name in custom:
                m = mat_lib.get(name)
                custom_data.append({
                    "材料名": name,
                    "Dk": m.dk,
                    "Df": m.df,
                    "粗糙度模型": m.get_roughness_model(),
                    "類別": m.category
                })
            dataframe(DataFrame(custom_data), use_container_width=True, hide_index=True)

            del_name = radio("刪除自定義材料", custom)
            if button("🗑️ 刪除"):
                mat_lib.delete_custom(del_name)
                success(f"已刪除 {del_name}")
                rerun()
        else:
            info("暫無自定義材料")

    with tab_add:
        subheader("➕ 添加自定義材料")
        new_name = text_input("材料名稱")
        new_dk = number_input("Dk", min_value=1.0, value=4.5, step=0.01)
        new_df = number_input("Df", min_value=0.0, value=0.020, step=0.001, format="%.4f")
        new_rough_model = radio("粗糙度模型", ["hammerstad", "huray"])
        new_rq = number_input("Rq (μm)", min_value=0.1, value=1.5, step=0.1)

        new_mat = Material(
            name=new_name,
            dk=new_dk,
            df=new_df,
            dk_freq_coeff={"type": "constant", "value": new_dk},
            df_freq_model={"type": "constant", "value": new_df},
            copper_roughness={"model": new_rough_model, "Rq_um": new_rq},
            category="custom"
        )

        if button("💾 添加材料", type="primary"):
            if new_name and new_name not in mat_lib.list_all():
                mat_lib.add_custom(new_name, new_mat)
                success(f"✅ 已添加材料: {new_name}")
                rerun()
            else:
                error("材料名稱不能爲空或已存在")


# ============================================================
#  Page 5: 項目文件
# ============================================================
elif page == "💾 項目文件":
    title("💾 項目文件管理")

    tab_save, tab_load = tabs(["💾 保存項目", "📂 加載項目"])

    with tab_save:
        subheader("保存當前參數到 JSON")
        if session_state.last_params:
            json(session_state.last_params, expanded=False)
            filename = text_input("文件名", value="project_001.json")
            if button("💾 保存", type="primary"):
                save_path = PROJECT_ROOT / "saved_projects" / filename
                save_project(str(save_path), session_state.last_params)
                success(f"✅ 已保存: `{save_path}`")
        else:
            info("請先執行一次計算，才能保存參數。")

    with tab_load:
        subheader("加載歷史項目")
        saved_dir = PROJECT_ROOT / "saved_projects"
        if saved_dir.exists():
            files = sorted([f for f in saved_dir.glob("*.json")])
            if files:
                selected = radio("選擇項目文件", [f.name for f in files])
                if button("📂 加載"):
                    data = load_project(str(saved_dir / selected))
                    session_state.last_params = data
                    success("✅ 項目已加載！")
                    json(data)
            else:
                info("暫無保存的項目文件。")
        else:
            info("暫無保存的項目文件。")

# with open(f"{base}/app.py", "w", encoding="utf-8") as f:
    # f.write(app_v2)

# 更新 requirements.txt
#req_v2 = """streamlit>=1.28.0
#plotly>=5.18.0
#pandas>=2.0.0
#numpy>=1.24.0
#scipy>=1.11.0"""

# with open(f"{base}/requirements.txt", "w", encoding="utf-8") as f:
    # f.write(req_v2)

# print("✅ app.py Phase 2 已更新")
# print("✅ requirements.txt 已更新")
