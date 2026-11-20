# PCB Transmission Line Calculator — Phase 1 Streamlit 主应用
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import json
from pathlib import Path

# ---------- 路径设置 ----------
PROJECT_ROOT = Path(__file__).parent
import sys
sys.path.insert(0, str(PROJECT_ROOT))

from modules.impedance.solver import forward_calc, inverse_calc
from modules.impedance.sweep import param_sweep, freq_sweep
from utils.project_io import save_project, load_project

# ---------- 页面配置 ----------
st.set_page_config(
    page_title="PCB Transmission Line Calculator",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- 加载材料库 ----------
@st.cache_data
def load_materials():
    mat_path = PROJECT_ROOT / "data" / "materials.json"
    if mat_path.exists():
        with open(mat_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

materials = load_materials()

# ---------- Sidebar ----------
st.sidebar.title("🔧 PCB 传输线工具箱")
st.sidebar.markdown("**Phase 1** — 阻抗计算与参数扫描")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "功能导航",
    ["📐 阻抗计算器", "📊 参数扫描", "💾 项目文件"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 材料库速览")
if materials:
    mat_df = pd.DataFrame([
        {"材料": k, "Dk": v["dk"], "Df": v["df"], "类别": v.get("category", "")}
        for k, v in materials.items()
    ])
    st.sidebar.dataframe(mat_df, use_container_width=True, hide_index=True)

# ---------- Session State 初始化 ----------
if "calc_history" not in st.session_state:
    st.session_state.calc_history = []

if "last_params" not in st.session_state:
    st.session_state.last_params = {}


def store_params(tline_type, mat_name, w, h, t_um, er, freq, mode, extra=None):
    d = {
        "tline_type": tline_type,
        "mat_name": mat_name,
        "w_mm": w,
        "h_mm": h,
        "t_um": t_um,
        "er": er,
        "freq_ghz": freq,
        "mode": mode
    }
    if extra:
        d.update(extra)
    st.session_state.last_params = d


# ============================================================
#  Page 1: 阻抗计算器
# ============================================================
if page == "📐 阻抗计算器":
    st.title("📐 传输线阻抗计算器")
    st.markdown(
        "基于 **Hammerstad-Jensen** (Microstrip) 与 **IPC-2141 / Wheeler** (Stripline) 经典公式"
    )

    col_input, col_result = st.columns([2, 3])

    with col_input:
        st.subheader("⚙️ 参数输入")

        tline_type = st.selectbox(
            "传输线类型",
            ["Microstrip", "Stripline"],
            help="Microstrip = 表层微带线 | Stripline = 对称带状线"
        )

        mat_name = st.selectbox("基材材料", list(materials.keys()), index=0)
        er = materials[mat_name]["dk"]
        st.caption(
            f"介电常数 Dk = **{er}** | 损耗因子 Df = **{materials[mat_name]['df']}**"
        )

        c1, c2 = st.columns(2)
        with c1:
            w = st.number_input(
                "线宽 w (mm)", min_value=0.001, value=0.300, step=0.010, format="%.3f"
            )
            h = st.number_input(
                "介质厚度 h (mm)", min_value=0.010, value=1.600, step=0.010, format="%.3f"
            )
        with c2:
            t_um = st.number_input("铜厚 t (μm)", min_value=0.0, value=35.0, step=1.0)
            freq = st.number_input("频率 (GHz)", min_value=0.0, value=1.0, step=0.1)

        t = t_um / 1000.0  # mm

        mode = st.radio("计算模式", ["正向计算", "反向计算"], horizontal=True)

        # 反向计算额外输入
        target_z0 = None
        if mode == "反向计算":
            target_z0 = st.number_input(
                "目标阻抗 Z₀ (Ω)", min_value=10.0, max_value=200.0, value=50.0, step=0.1
            )

        do_freq_sweep = st.checkbox("显示频率扫描曲线 (0.1 ~ 10 GHz)", value=False)

        calc_btn = st.button("🚀 执行计算", type="primary", use_container_width=True)

    # ---------- 结果区 ----------
    with col_result:
        st.subheader("📊 计算结果")

        if calc_btn:
            if mode == "正向计算":
                z0, e_eff = forward_calc(tline_type, w, h, t, er, freq)

                store_params(tline_type, mat_name, w, h, t_um, er, freq, mode)
                st.session_state.calc_history.append({
                    "类型": tline_type,
                    "模式": "正向",
                    "w(mm)": w,
                    "h(mm)": h,
                    "t(μm)": t_um,
                    "Z₀(Ω)": round(z0, 2),
                    "εeff": round(e_eff, 3)
                })

                # 指标卡片
                r1, r2, r3 = st.columns(3)
                r1.metric("特性阻抗 Z₀", f"{z0:.2f} Ω")
                r2.metric("有效介电常数 εeff", f"{e_eff:.3f}")
                if freq > 0:
                    lambda_g = 300.0 / (freq * np.sqrt(e_eff))
                    r3.metric("导波波长 λg", f"{lambda_g:.2f} mm")
                else:
                    r3.metric("导波波长 λg", "N/A (DC)")

                # 设计建议
                if abs(z0 - 50.0) < 3.0:
                    st.success("✅ 非常接近 50Ω 标准阻抗")
                elif abs(z0 - 50.0) < 10.0:
                    st.info("ℹ️ 接近 50Ω，可微调几何参数")
                elif z0 < 50.0:
                    st.info("💡 提示：减小线宽 或 增加介质厚度 → 可提高阻抗")
                else:
                    st.info("💡 提示：增加线宽 或 减小介质厚度 → 可降低阻抗")

                # 频率扫描图
                if do_freq_sweep:
                    freqs = np.linspace(0.1, 10.0, 100)
                    df_freq = freq_sweep(tline_type, w, h, t, er, freqs)

                    fig = make_subplots(
                        rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=("Z₀ vs 频率", "εeff vs 频率"),
                        vertical_spacing=0.12
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df_freq["freq_ghz"], y=df_freq["Z0"],
                            mode="lines", line=dict(color="#00bc8c", width=2),
                            name="Z₀"
                        ), row=1, col=1
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df_freq["freq_ghz"], y=df_freq["e_eff"],
                            mode="lines", line=dict(color="#f39c12", width=2),
                            name="εeff"
                        ), row=2, col=1
                    )
                    fig.update_xaxes(title_text="频率 (GHz)", row=2, col=1)
                    fig.update_yaxes(title_text="Z₀ (Ω)", row=1, col=1)
                    fig.update_yaxes(title_text="εeff", row=2, col=1)
                    fig.update_layout(
                        height=520, showlegend=False, template="plotly_white",
                        margin=dict(l=60, r=40, t=60, b=40)
                    )
                    st.plotly_chart(fig, use_container_width=True)

            else:  # 反向计算
                if target_z0 is None:
                    target_z0 = 50.0

                w_calc = inverse_calc(tline_type, target_z0, h, t, er, freq)

                if w_calc:
                    z0_verify, _ = forward_calc(tline_type, w_calc, h, t, er, freq)

                    store_params(
                        tline_type, mat_name, w_calc, h, t_um, er, freq, mode,
                        extra={"target_Z0": target_z0, "verified_Z0": round(z0_verify, 2)}
                    )
                    st.session_state.calc_history.append({
                        "类型": tline_type,
                        "模式": "反向",
                        "目标Z₀": target_z0,
                        "w(mm)": round(w_calc, 4),
                        "h(mm)": h,
                        "t(μm)": t_um,
                        "验证Z₀": round(z0_verify, 2)
                    })

                    st.success(f"所需线宽: **{w_calc * 1000:.2f} μm**  ({w_calc:.4f} mm)")
                    st.caption(f"验证计算: Z₀ = {z0_verify:.2f} Ω")

                    # 50Ω 设计建议
                    st.info(
                        f"以 **{mat_name}** (Dk={er}) 在 **{h}mm** 介质上实现 **{target_z0}Ω** "
                        f"{tline_type}，建议线宽 ≈ **{w_calc*1000:.0f} μm**"
                    )
                else:
                    st.error(
                        "❌ 无法收敛到目标阻抗。请检查：\\n"
                        "• 介质厚度是否过小\\n"
                        "• 目标阻抗是否在物理可实现范围内 (通常 20~150Ω)\\n"
                        "• 铜厚是否过大导致等效宽度异常"
                    )

        # 计算历史
        if st.session_state.calc_history:
            with st.expander("📜 最近计算历史 (最近 10 笔)", expanded=False):
                hist_df = pd.DataFrame(st.session_state.calc_history[-10:])
                st.dataframe(hist_df, use_container_width=True, hide_index=True)


# ============================================================
#  Page 2: 参数扫描
# ============================================================
elif page == "📊 参数扫描":
    st.title("📊 单参数扫描分析")
    st.markdown("扫描单一几何参数对特性阻抗 Z₀ 与有效介电常数 εeff 的影响")

    col_cfg, col_plot = st.columns([1, 2])

    with col_cfg:
        st.subheader("⚙️ 扫描配置")

        tline_type = st.selectbox(
            "传输线类型", ["Microstrip", "Stripline"], key="sweep_tline"
        )
        mat_name = st.selectbox(
            "基材材料", list(materials.keys()), key="sweep_mat"
        )
        er = materials[mat_name]["dk"]

        sweep_param = st.selectbox(
            "扫描参数",
            ["w_mm", "h_mm", "t_um", "er"],
            format_func=lambda x: {
                "w_mm": "线宽 w (mm)",
                "h_mm": "介质厚度 h (mm)",
                "t_um": "铜厚 t (μm)",
                "er": "介电常数 Dk"
            }[x]
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            default_min = 0.1 if sweep_param != "er" else 3.0
            p_min = st.number_input("最小值", value=default_min, step=0.1)
        with c2:
            default_max = 1.0 if sweep_param != "er" else 5.0
            p_max = st.number_input("最大值", value=default_max, step=0.1)
        with c3:
            p_points = st.number_input("点数", min_value=10, max_value=500, value=50)

        st.markdown("---")
        st.subheader("🔒 固定参数")

        # 根据扫描参数显示/隐藏固定输入
        if sweep_param != "w_mm":
            w_fix = st.number_input("线宽 w (mm)", value=0.3, step=0.01, key="fix_w")
        else:
            w_fix = 0.3

        if sweep_param != "h_mm":
            h_fix = st.number_input("介质厚度 h (mm)", value=1.6, step=0.01, key="fix_h")
        else:
            h_fix = 1.6

        if sweep_param != "t_um":
            t_fix_um = st.number_input("铜厚 t (μm)", value=35.0, step=1.0, key="fix_t")
        else:
            t_fix_um = 35.0

        if sweep_param != "er":
            er_fix = er
            st.caption(f"固定 Dk = {er} ({mat_name})")
        else:
            er_fix = 4.5

        t_fix = t_fix_um / 1000.0
        freq_fix = st.number_input("频率 (GHz)", value=1.0, step=0.1, key="sweep_freq")

        run_sweep = st.button("▶️ 开始扫描", type="primary", use_container_width=True)

    # ---------- 绘图区 ----------
    with col_plot:
        if run_sweep:
            sweep_vals = np.linspace(p_min, p_max, int(p_points))

            fixed = {
                "w": w_fix, "h": h_fix, "t": t_fix,
                "er": er_fix, "freq_ghz": freq_fix
            }

            # 执行扫描
            results = []
            for val in sweep_vals:
                p = dict(fixed)
                if sweep_param == "w_mm":
                    p["w"] = val
                elif sweep_param == "h_mm":
                    p["h"] = val
                elif sweep_param == "t_um":
                    p["t"] = val / 1000.0
                elif sweep_param == "er":
                    p["er"] = val

                z0, e_eff = forward_calc(
                    tline_type, p["w"], p["h"], p["t"], p["er"], p["freq_ghz"]
                )
                results.append({"param_val": val, "Z0": z0, "e_eff": e_eff})

            df = pd.DataFrame(results)

            # Plotly 图表
            param_label = {
                "w_mm": "线宽 w (mm)",
                "h_mm": "介质厚度 h (mm)",
                "t_um": "铜厚 t (μm)",
                "er": "介电常数 Dk"
            }[sweep_param]

            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=(f"Z₀ vs {param_label}", f"εeff vs {param_label}")
            )
            fig.add_trace(
                go.Scatter(
                    x=df["param_val"], y=df["Z0"], mode="lines",
                    line=dict(color="#3498db", width=2.5), fill="tozeroy",
                    fillcolor="rgba(52,152,219,0.1)"
                ), row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df["param_val"], y=df["e_eff"], mode="lines",
                    line=dict(color="#e74c3c", width=2.5), fill="tozeroy",
                    fillcolor="rgba(231,76,60,0.1)"
                ), row=1, col=2
            )

            # 50Ω 参考线
            fig.add_hline(
                y=50, line_dash="dash", line_color="gray",
                annotation_text="50Ω", annotation_position="right",
                row=1, col=1
            )

            fig.update_xaxes(title_text=param_label)
            fig.update_yaxes(title_text="Z₀ (Ω)", row=1, col=1)
            fig.update_yaxes(title_text="εeff", row=1, col=2)
            fig.update_layout(
                template="plotly_white", showlegend=False,
                height=450, margin=dict(l=60, r=40, t=60, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)

            # 关键统计
            st.markdown("#### 🔑 关键统计")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("最小 Z₀", f"{df['Z0'].min():.2f} Ω")
            c2.metric("最大 Z₀", f"{df['Z0'].max():.2f} Ω")

            # 最接近 50Ω 的点
            idx_50 = (df['Z0'] - 50.0).abs().idxmin()
            closest_val = df.loc[idx_50, 'param_val']
            closest_z0 = df.loc[idx_50, 'Z0']
            c3.metric(f"50Ω 对应 {param_label}", f"{closest_val:.3f}")
            c4.metric("该点实际 Z₀", f"{closest_z0:.2f} Ω")

            # 原始数据
            with st.expander("📋 查看原始数据"):
                st.dataframe(df, use_container_width=True)


# ============================================================
#  Page 3: 项目文件
# ============================================================
elif page == "💾 项目文件":
    st.title("💾 项目文件管理")
    st.markdown("保存 / 加载计算参数，便于复现与分享")

    tab_save, tab_load = st.tabs(["💾 保存项目", "📂 加载项目"])

    with tab_save:
        st.subheader("保存当前参数到 JSON")
        if st.session_state.last_params:
            st.json(st.session_state.last_params, expanded=False)
            filename = st.text_input("文件名", value="project_001.json")
            if st.button("💾 保存", type="primary"):
                save_path = PROJECT_ROOT / "saved_projects" / filename
                save_project(str(save_path), st.session_state.last_params)
                st.success(f"✅ 已保存: `{save_path}`")
        else:
            st.info("请先执行一次计算，才能保存参数。")

    with tab_load:
        st.subheader("加载历史项目")
        saved_dir = PROJECT_ROOT / "saved_projects"
        if saved_dir.exists():
            files = sorted([f for f in saved_dir.glob("*.json")])
            if files:
                selected = st.selectbox("选择项目文件", [f.name for f in files])
                if st.button("📂 加载"):
                    data = load_project(str(saved_dir / selected))
                    st.session_state.last_params = data
                    st.success("✅ 项目已加载到内存！")
                    st.json(data)
                    st.info("提示：切换到「阻抗计算器」页面即可看到已加载的参数。")
            else:
                st.info("暂无保存的项目文件。")
        else:
            st.info("暂无保存的项目文件。")
'''

