# ========== 4. 更新 app.py 加入 Phase 3 逆工程頁面 ==========

# 讀取現有 app.py
# with open(f"{base}/app.py", "r", encoding="utf-8") as f:
    # existing_app = f.read()

# 在 imports 部分加入 Phase 3 模塊
# import_section_end = existing_app.find("from utils.project_io import save_project, load_project")
from utils.project_io import save_project, load_project
from modules.inverse.s_param_parser import TouchstoneParser
from modules.inverse.optimizer import InverseEngineer
from modules.inverse.sensitivity import SensitivityAnalyzer'''

app_v3 = existing_app.replace(
    "from utils.project_io import save_project, load_project",
    new_imports
)

# 更新 Sidebar 導航
app_v3 = app_v3.replace(
    '''page = st.sidebar.radio(
    "功能導航",
    ["📐 阻抗計算器", "📊 參數掃描", "📐 叠構損耗分析", "📋 材料庫管理", "💾 項目文件"],
    index=0
)''',
    '''page = st.sidebar.radio(
    "功能導航",
    ["📐 阻抗計算器", "📊 參數掃描", "📐 叠構損耗分析", "🔬 逆工程解析", "📋 材料庫管理", "💾 項目文件"],
    index=0
)'''
)

# 在 Page 5 (材料庫管理) 之前插入逆工程頁面
inverse_page = '''

# ============================================================
#  Page 4: 逆工程解析 (Phase 3 - 新增)
# ============================================================
elif page == "🔬 逆工程解析":
    st.title("🔬 逆工程解析")
    st.markdown("從實測 S 參數反推傳輸線物理參數 | 自動算法選擇")

    col_cfg, col_result = st.columns([1, 2])

    with col_cfg:
        st.subheader("📁 數據上傳")
        uploaded_file = st.file_uploader("上傳 Touchstone 文件 (.s2p)", type=["s2p", "s1p", "s3p", "s4p"])

        if uploaded_file is not None:
            # 保存臨時文件
            temp_path = PROJECT_ROOT / "saved_projects" / "temp_sparam.s2p"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            try:
                parser = TouchstoneParser(str(temp_path))
                summary = parser.get_data_summary()

                st.success(f"✅ 解析成功: {summary['n_points']} 點, {summary['freq_range_ghz'][0]:.2f}-{summary['freq_range_ghz'][1]:.2f} GHz")
                st.caption(f"格式: {summary['format']}, 參考阻抗: {summary['z0']}Ω")
                st.caption(f"S21 範圍: {summary['s21_min_db']:.2f} ~ {summary['s21_max_db']:.2f} dB")

                freqs = parser.get_frequencies_ghz()
                s21_db = parser.get_s21_db()
                s11_db = parser.get_s11_db() if "S11" in parser._data["s_params"] else None

                st.markdown("---")
                st.subheader("⚙️ 優化配置")

                # 固定參數
                st.markdown("**固定參數**")
                c1, c2 = st.columns(2)
                with c1:
                    h_fixed = st.number_input("介質厚度 h (mm)", value=1.6, step=0.1, key="inv_h")
                    t_um_fixed = st.number_input("銅厚 t (μm)", value=35.0, step=1.0, key="inv_t")
                with c2:
                    trace_len = st.number_input("線長 (m)", value=0.1, step=0.01, format="%.3f", key="inv_len")
                    rough_model = st.selectbox("粗糙度模型", ["hammerstad", "huray"], key="inv_rough")

                st.markdown("---")
                st.subheader("🎯 反解參數選擇")

                # 選擇要反解的參數
                st.markdown("*勾選要優化的參數，其余使用固定值或初始猜測*")
                opt_dk = st.checkbox("介電常數 Dk", value=True)
                opt_df = st.checkbox("損耗因子 Df", value=True)
                opt_w = st.checkbox("線寬 w (mm)", value=False)
                opt_rq = st.checkbox("粗糙度 Rq (μm)", value=False)

                param_names = []
                initial_guess = {}
                bounds = {}

                if opt_dk:
                    param_names.append("dk")
                    initial_guess["dk"] = st.number_input("Dk 初始猜測", value=4.5, step=0.1, key="guess_dk")
                    bounds["dk"] = (st.number_input("Dk 下限", value=2.0, step=0.1, key="lb_dk"),
                                    st.number_input("Dk 上限", value=10.0, step=0.1, key="ub_dk"))

                if opt_df:
                    param_names.append("df")
                    initial_guess["df"] = st.number_input("Df 初始猜測", value=0.02, step=0.001, format="%.4f", key="guess_df")
                    bounds["df"] = (st.number_input("Df 下限", value=0.0001, step=0.0001, format="%.4f", key="lb_df"),
                                    st.number_input("Df 上限", value=0.1, step=0.001, format="%.4f", key="ub_df"))

                if opt_w:
                    param_names.append("w_mm")
                    initial_guess["w_mm"] = st.number_input("w 初始猜測 (mm)", value=0.3, step=0.01, key="guess_w")
                    bounds["w_mm"] = (st.number_input("w 下限", value=0.01, step=0.01, key="lb_w"),
                                      st.number_input("w 上限", value=5.0, step=0.1, key="ub_w"))

                if opt_rq:
                    param_names.append("Rq_um")
                    initial_guess["Rq_um"] = st.number_input("Rq 初始猜測 (μm)", value=1.5, step=0.1, key="guess_rq")
                    bounds["Rq_um"] = (st.number_input("Rq 下限", value=0.1, step=0.1, key="lb_rq"),
                                       st.number_input("Rq 上限", value=5.0, step=0.1, key="ub_rq"))

                auto_algo = st.checkbox("自動選擇優化算法 (推薦)", value=True)

                run_opt = st.button("🚀 開始逆工程", type="primary", use_container_width=True)

            except Exception as e:
                st.error(f"❌ 解析失敗: {e}")
                run_opt = False
                freqs = None
                s21_db = None
                s11_db = None
        else:
            st.info("請上傳 .s2p 文件以開始逆工程分析")
            run_opt = False
            freqs = None
            s21_db = None
            s11_db = None

    with col_result:
        if uploaded_file is not None and run_opt and param_names:
            st.subheader("📊 逆工程結果")

            with st.spinner("正在執行多階段優化..."):
                # 創建優化器
                fixed_params = {
                    "h_mm": h_fixed,
                    "t_mm": t_um_fixed / 1000.0,
                    "roughness_model": rough_model
                }

                engineer = InverseEngineer(freqs, s21_db, s11_db, trace_len, fixed_params)
                result = engineer.optimize(param_names, bounds, initial_guess, auto_algo)

            # 顯示優化過程
            with st.expander("🔍 優化過程詳情", expanded=False):
                for stage in result["stages"]:
                    st.write(f"**Stage {stage.get('stage', '?')}**: {stage.get('algorithm', 'N/A')}")
                    st.write(f"  - Cost: {stage.get('cost', 'N/A'):.6f}")
                    st.write(f"  - 迭代次數: {stage.get('nfev', 'N/A')}")
                    st.write(f"  - 成功: {'✅' if stage.get('success') else '❌'}")
                    if "x" in stage:
                        st.write(f"  - 參數: {dict(zip(param_names, [round(v, 4) for v in stage['x']]))}")

            # 藕合參數卡片
            st.markdown("#### 🎯 藕合參數")
            fitted = result["fitted_params"]
            cols = st.columns(len(fitted))
            for i, (k, v) in enumerate(fitted.items()):
                unit = {"dk": "", "df": "", "w_mm": "mm", "Rq_um": "μm", "h_mm": "mm"}.get(k, "")
                cols[i].metric(f"{k}", f"{v:.4f} {unit}")

            # 藕合質量
            final_cost = result["final_cost"]
            rmse = np.sqrt(final_cost / len(freqs))
            st.markdown(f"**藕合 RMSE**: {rmse:.4f} dB")

            if rmse < 0.5:
                st.success("✅ 藕合品質優秀 (RMSE < 0.5 dB)")
            elif rmse < 2.0:
                st.info("ℹ️ 藕合品質良好 (RMSE < 2 dB)")
            else:
                st.warning("⚠️ 藕合品質一般，建議檢查模型假設或增加反解參數")

            # 實測 vs 藕合 叠圖
            fig_fit = go.Figure()
            fig_fit.add_trace(go.Scatter(x=freqs, y=s21_db, mode="markers",
                                         name="實測 S21", marker=dict(size=6, color="#3498db")))
            fig_fit.add_trace(go.Scatter(x=freqs, y=result["s21_fitted"], mode="lines",
                                         name="藕合 S21", line=dict(color="#e74c3c", width=2)))
            if s11_db is not None and "s11_fitted" in result:
                fig_fit.add_trace(go.Scatter(x=freqs, y=s11_db, mode="markers",
                                             name="實測 S11", marker=dict(size=4, color="#2ecc71")))
                fig_fit.add_trace(go.Scatter(x=freqs, y=result["s11_fitted"], mode="lines",
                                             name="藕合 S11", line=dict(color="#f39c12", width=1.5, dash="dash")))
            fig_fit.update_layout(title="實測 vs 藕合 S 參數",
                                  xaxis_title="頻率 (GHz)", yaxis_title="S 參數 (dB)",
                                  template="plotly_white", height=450)
            st.plotly_chart(fig_fit, use_container_width=True)

            # 殘差分析
            fig_res = go.Figure()
            residuals = np.array(result["s21_residual"])
            fig_res.add_trace(go.Scatter(x=freqs, y=residuals, mode="lines",
                                         line=dict(color="#9b59b6", width=1.5),
                                         fill="tozeroy", fillcolor="rgba(155,89,182,0.2)"))
            fig_res.add_hline(y=0, line_dash="dash", line_color="gray")
            fig_res.add_hline(y=rmse, line_dash="dot", line_color="red",
                              annotation_text=f"+RMSE", annotation_position="right")
            fig_res.add_hline(y=-rmse, line_dash="dot", line_color="red",
                              annotation_text=f"-RMSE", annotation_position="right")
            fig_res.update_layout(title="S21 殘差分析",
                                  xaxis_title="頻率 (GHz)", yaxis_title="殘差 (dB)",
                                  template="plotly_white", height=300)
            st.plotly_chart(fig_res, use_container_width=True)

            # 殘差統計
            c1, c2, c3 = st.columns(3)
            c1.metric("殘差均值", f"{residuals.mean():.4f} dB")
            c2.metric("殘差標準差", f"{residuals.std():.4f} dB")
            c3.metric("最大絕對殘差", f"{np.abs(residuals).max():.4f} dB")

            # 敏感度分析
            if len(param_names) >= 2:
                st.markdown("---")
                st.subheader("📊 參數敏感度分析")

                with st.spinner("計算參數敏感度..."):
                    # 構建 cost function wrapper
                    def cost_wrapper(x):
                        return engineer._cost_function(x, param_names)

                    analyzer = SensitivityAnalyzer(cost_wrapper, param_names, fitted, bounds)
                    sens_results = analyzer.analyze(perturbation_pct=0.05)

                # 敏感度柱狀圖
                sens_df = pd.DataFrame(sens_results)
                fig_sens = go.Figure()
                fig_sens.add_trace(go.Bar(
                    x=sens_df["param"],
                    y=sens_df["normalized_sensitivity"],
                    marker_color=["#e74c3c" if s > np.mean(sens_df["normalized_sensitivity"]) else "#3498db"
                                  for s in sens_df["normalized_sensitivity"]]
                ))
                fig_sens.update_layout(title="參數敏感度排名 (歸一化)",
                                       xaxis_title="參數", yaxis_title="敏感度",
                                       template="plotly_white", height=350)
                st.plotly_chart(fig_sens, use_container_width=True)

                # 敏感度表格
                with st.expander("📋 敏感度詳細數據"):
                    display_sens = sens_df[["param", "fitted_value", "delta", "delta_cost",
                                            "normalized_sensitivity", "direction"]].copy()
                    display_sens.columns = ["參數", "藕合值", "擾動量", "Cost變化",
                                            "歸一化敏感度", "敏感方向"]
                    st.dataframe(display_sens.round(6), use_container_width=True, hide_index=True)

                # 參數耦合提示
                max_sens = sens_results[0]["normalized_sensitivity"]
                min_sens = sens_results[-1]["normalized_sensitivity"]
                if max_sens / min_sens > 10:
                    st.info("💡 提示: 參數敏感度差異大，低敏感度參數可能與高敏感度參數存在耦合，建議固定低敏感度參數後重新優化。")

            # 保存結果
            store_params("inverse", {
                "fitted_params": fitted,
                "rmse": rmse,
                "param_names": param_names,
                "trace_length": trace_len
            })

        elif uploaded_file is not None and run_opt and not param_names:
            st.warning("⚠️ 請至少選擇一個要反解的參數")
'''

# 找到插入點：在 "# ============================================================\n#  Page 4: 材料庫管理" 之前插入
insert_marker = "# ============================================================\n#  Page 4: 材料庫管理"
app_v3 = app_v3.replace(insert_marker, inverse_page + "\n" + insert_marker)

# 更新材料庫管理的頁碼
app_v3 = app_v3.replace("#  Page 4: 材料庫管理", "#  Page 5: 材料庫管理")
app_v3 = app_v3.replace("elif page == \"📋 材料庫管理\":", "elif page == \"📋 材料庫管理\":")

# 更新項目文件的頁碼
app_v3 = app_v3.replace("#  Page 5: 項目文件", "#  Page 6: 項目文件")

with open(f"{base}/app.py", "w", encoding="utf-8") as f:
    f.write(app_v3)

print("✅ app.py 已更新 (加入 Phase 3 逆工程解析頁面)")
