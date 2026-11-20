from streamlit import button, checkbox, columns, download_button, error, header, info, markdown, metric, number_input, pyplot, radio, slider, spinner, subheader, success, tabs, sidebar
from 智能UtilII import DesignConstraints, optimize_stripline_design
from matplotlib.pyplot import colorbar, subplots, tight_layout
from numpy import linspace
from json import dumps
# ============================================================
# 智能化設計優化器 UI 函數
# ============================================================
with sidebar:
    markdown("**📋 規格約束輸入**")

    markdown("<div style='color:#1f77b4;font-weight:bold;'>電氣規格</div>", unsafe_allow_html=True)
    target_Z0 = number_input("目標阻抗 Z₀ (Ω)", 40.0, 60.0, 50.0, 1.0, key="opt_z0")
    Z0_tol = number_input("阻抗容差 (±Ω)", 1.0, 10.0, 5.0, 0.5, key="opt_z0tol")
    max_NEXT = number_input("最大 NEXT (dB)", -80.0, -20.0, -40.0, 1.0, key="opt_next")
    max_FEXT = number_input("最大 FEXT (dB)", -80.0, -20.0, -40.0, 1.0, key="opt_fext")
    max_IL = number_input("最大插入損耗 (dB)", 0.5, 10.0, 3.0, 0.1, key="opt_il")

    markdown("<div style='color:#d62728;font-weight:bold;'>熱規格</div>", unsafe_allow_html=True)
    max_thermal = number_input("最大熱負載/通道 (μW)", 10.0, 1000.0, 200.0, 10.0, key="opt_thermal")
    temp_stage_opt = radio("溫度階段",
        ["300K → 40K", "40K → 4K", "4K → 1K", "1K → 100mK"], index=1, key="opt_temp", horizontal=True)

    markdown("<div style='color:#2ca02c;font-weight:bold;'>機械/製程規格</div>", unsafe_allow_html=True)
    max_thickness = number_input("最大總厚度 (mm)", 0.1, 2.0, 0.5, 0.05, key="opt_thick")
    n_ch_opt = radio("通道數", [4, 8, 16, 32], index=1, key="opt_ch", horizontal=True)
    freq_opt = number_input("工作頻率 (GHz)", 0.1, 20.0, 6.0, 0.1, key="opt_freq")
    length_opt = number_input("線長 (mm)", 100, 1500, 400, 50, key="opt_len")

    mat_opt = radio("導體材料", ["NbTi", "Ag", "Cu"], index=0, key="opt_mat", horizontal=True)

    run_optimize = button("🚀 執行優化", type="primary", use_container_width=True, key="btn_opt")


def render_optimizer_section():
    """渲染智能化設計優化器 UI 區塊"""
    markdown("---")
    header("🧠 智能化設計優化器")

    opt_tab1, opt_tab2 = tabs([
        "🔧 逆向設計：規格 → 尺寸",
        "🧪 材料/Via 優化：參數 → IL/RL"
    ])

    # ========== Tab 1: 逆向設計 ==========
    with opt_tab1:
        subheader("🔧 逆向設計優化器")
        markdown("給定電氣/熱/機械規格約束，自動找出最優 Stripline 尺寸")

        col_spec, col_result = columns([1, 2])

        with col_result:
            if run_optimize:
                with spinner("正在執行多目標優化 (Differential Evolution)..."):
                    constraints = DesignConstraints(
                        target_Z0=target_Z0, Z0_tolerance=Z0_tol,
                        max_NEXT_dB=max_NEXT, max_FEXT_dB=max_FEXT,
                        max_IL_dB=max_IL, max_thermal_per_channel_uW=max_thermal,
                        max_total_thickness_mm=max_thickness, n_channels=n_ch_opt,
                        frequency_GHz=freq_opt, length_mm=length_opt,
                        temperature_stage=temp_stage_opt, conductor=mat_opt
                    )
                    result = optimize_stripline_design(constraints)

                if result["success"]:
                    success("✅ 優化成功！")

                    markdown("### 📐 最優設計參數")
                    params = result["optimal_params"]
                    perf = result["performance"]

                    cols = columns(4)
                    with cols[0]:
                        metric("線寬 w", f"{params['w_mm']*1000:.1f} μm")
                    with cols[1]:
                        metric("介電厚 h", f"{params['h_mm']*1000:.1f} μm")
                    with cols[2]:
                        metric("Pitch s", f"{params['s_mm']:.2f} mm")
                    with cols[3]:
                        metric("導體厚 t", f"{params['t_um']:.1f} μm")

                    markdown("### 📊 性能預測")
                    cols2 = columns(4)
                    with cols2[0]:
                        delta_Z0 = abs(perf["Z0"] - target_Z0)
                        metric("特性阻抗", f"{perf['Z0']:.2f} Ω",
                                 delta=f"±{delta_Z0:.2f}Ω",
                                 delta_color="normal" if delta_Z0 < Z0_tol else "inverse")
                    with cols2[1]:
                        metric("NEXT", f"{perf['NEXT_dB']:.1f} dB",
                                 delta="OK" if perf['NEXT_dB'] < max_NEXT else "FAIL",
                                 delta_color="normal" if perf['NEXT_dB'] < max_NEXT else "inverse")
                    with cols2[2]:
                        metric("FEXT", f"{perf['FEXT_dB']:.1f} dB",
                                 delta="OK" if perf['FEXT_dB'] < max_FEXT else "FAIL",
                                 delta_color="normal" if perf['FEXT_dB'] < max_FEXT else "inverse")
                    with cols2[3]:
                        metric("熱負載", f"{perf['thermal_per_channel_uW']:.1f} μW",
                                 delta="OK" if perf['thermal_per_channel_uW'] < max_thermal else "FAIL",
                                 delta_color="normal" if perf['thermal_per_channel_uW'] < max_thermal else "inverse")

                    cols3 = columns(3)
                    with cols3[0]:
                        metric("插入損耗", f"{perf['IL_dB']:.2f} dB")
                    with cols3[1]:
                        metric("總厚度", f"{perf['total_thickness_mm']:.3f} mm")
                    with cols3[2]:
                        metric("迭代次數", f"{result['n_iterations']}")

                    # 設計空間掃描
                    markdown("### 🔍 設計空間 Pareto 分析")
                    with spinner("掃描設計空間..."):
                        df_scan = scan_design_space(constraints, n_points=12)

                    if not df_scan.empty:
                        fig_pareto, axes = subplots(1, 3, figsize=(15, 4))

                        sc1 = axes[0].scatter(df_scan['w_mm']*1000, df_scan['s_mm'],
                                              c=df_scan['Z0'], cmap='RdYlGn_r',
                                              s=50, edgecolors='black', linewidth=0.5)
                        axes[0].scatter(params['w_mm']*1000, params['s_mm'],
                                       c='red', s=200, marker='*', edgecolors='black', linewidth=2,
                                       label='Optimal', zorder=5)
                        axes[0].set_xlabel("Trace Width (μm)")
                        axes[0].set_ylabel("Pitch (mm)")
                        axes[0].set_title("Characteristic Impedance Z₀")
                        colorbar(sc1, ax=axes[0], label="Z₀ (Ω)")
                        axes[0].legend()

                        sc2 = axes[1].scatter(df_scan['w_mm']*1000, df_scan['s_mm'],
                                              c=df_scan['NEXT_dB'], cmap='RdYlGn',
                                              s=50, edgecolors='black', linewidth=0.5)
                        axes[1].scatter(params['w_mm']*1000, params['s_mm'],
                                       c='red', s=200, marker='*', edgecolors='black', linewidth=2,
                                       label='Optimal', zorder=5)
                        axes[1].axhline(y=max_NEXT, color='red', linestyle='--', alpha=0.5)
                        axes[1].set_xlabel("Trace Width (μm)")
                        axes[1].set_ylabel("Pitch (mm)")
                        axes[1].set_title("Near-End Crosstalk (NEXT)")
                        colorbar(sc2, ax=axes[1], label="NEXT (dB)")
                        axes[1].legend()

                        sc3 = axes[2].scatter(df_scan['w_mm']*1000, df_scan['s_mm'],
                                              c=df_scan['thermal_per_channel_uW'], cmap='YlOrRd',
                                              s=50, edgecolors='black', linewidth=0.5)
                        axes[2].scatter(params['w_mm']*1000, params['s_mm'],
                                       c='red', s=200, marker='*', edgecolors='black', linewidth=2,
                                       label='Optimal', zorder=5)
                        axes[2].set_xlabel("Trace Width (μm)")
                        axes[2].set_ylabel("Pitch (mm)")
                        axes[2].set_title("Thermal Load per Channel")
                        colorbar(sc3, ax=axes[2], label="μW")
                        axes[2].legend()

                        tight_layout()
                        pyplot(fig_pareto)

                    # 匯出
                    markdown("### 📥 匯出最優設計")
                    optimal_design = {
                        "optimization_method": "Differential Evolution",
                        "constraints": {"target_Z0": target_Z0, "max_NEXT_dB": max_NEXT,
                                       "max_FEXT_dB": max_FEXT, "max_IL_dB": max_IL,
                                       "max_thermal_uW": max_thermal, "max_thickness_mm": max_thickness},
                        "optimal_dimensions": params,
                        "predicted_performance": {k: v for k, v in peitems() if k != "params"}
                    }
                    download_button("下載最優設計 JSON",
                        data=json.dumps(optimal_design, indent=2, default=str),
                        file_name="optimal_stripline_design.json", mime="application/json")
                else:
                    error("❌ 優化失敗，請放寬約束條件後重試")
            else:
                info("👈 請在左側輸入規格約束，然後點擊「執行優化」")

    # ========== Tab 2: 材料/Via 優化 ==========
    with opt_tab2:
        subheader("🧪 材料與 Via 參數優化")
        markdown("給定材料介電係數、多層膜間距、Via 參數，計算 IL/RL 並優化")

        col_mat, col_ilrl = columns([1, 2])

        with col_mat:
            markdown("**🔬 材料參數輸入**")

            markdown("<div style='color:#1f77b4;font-weight:bold;'>介電材料</div>", unsafe_allow_html=True)
            er_input = number_input("相對介電常數 εr", 1.5, 10.0, 3.4, 0.1, key="mv_er")
            tan_rt = number_input("室溫損耗角 tanδ", 0.0001, 0.1, 0.003, 0.0001, format="%.4f", key="mv_tanrt")
            tan_4k = number_input("4K 損耗角 tanδ", 1e-6, 0.01, 3e-5, 1e-6, format="%.6f", key="mv_tan4k")
            tan_20mk = number_input("20mK 損耗角 tanδ", 1e-7, 0.001, 2.2e-5, 1e-7, format="%.7f", key="mv_tan20mk")
            n_dielectric = slider("介電層數", 1, 6, 2, 1, key="mv_nlayer")
            dielectric_thick = number_input("單層介電厚度 (μm)", 25.0, 500.0, 150.0, 5.0, key="mv_dthick")

            markdown("<div style='color:#ff7f0e;font-weight:bold;'>Via 設計</div>", unsafe_allow_html=True)
            via_en = checkbox("啟用 Via", value=True, key="mv_viaen")
            via_d = number_input("Via 直徑 (μm)", 50.0, 500.0, 150.0, 10.0, key="mv_viad")
            via_den = slider("Via 密度 (個/mm)", 0.5, 5.0, 2.0, 0.1, key="mv_viaden")

            markdown("<div style='color:#2ca02c;font-weight:bold;'>導體</div>", unsafe_allow_html=True)
            mat_ilrl = radio("導體", ["NbTi", "Ag", "Cu"], index=0, key="mv_mat", horizontal=True)
            cond_thick = number_input("導體厚度 (μm)", 1.0, 50.0, 5.0, 0.5, key="mv_cthick")
            roughness = number_input("表面粗糙度 (μm)", 0.1, 5.0, 0.5, 0.1, key="mv_rough")

            markdown("<div style='color:#d62728;font-weight:bold;'>幾何與操作</div>", unsafe_allow_html=True)
            w_ilrl = number_input("線寬 (μm)", 50.0, 500.0, 150.0, 10.0, key="mv_w")
            p_ilrl = number_input("Pitch (mm)", 0.5, 5.0, 2.0, 0.1, key="mv_p")
            l_ilrl = number_input("線長 (mm)", 100.0, 1500.0, 400.0, 50.0, key="mv_l")
            f_ilrl = number_input("頻率 (GHz)", 0.1, 20.0, 6.0, 0.1, key="mv_f")
            T_ilrl = number_input("溫度 (K)", 0.01, 300.0, 4.0, 1.0, key="mv_t")

            calc_ilrl = button("🔬 計算 IL/RL", type="primary", use_container_width=True, key="btn_calc_ilrl")

            markdown("---")
            markdown("**🎯 自動優化**")
            target_il = number_input("目標 IL (dB)", 0.1, 5.0, 2.0, 0.1, key="mv_til")
            target_rl = number_input("目標 RL (dB)", 10.0, 40.0, 20.0, 1.0, key="mv_trl")
            auto_opt = button("🚀 自動優化材料/Via", type="secondary", use_container_width=True, key="btn_autopt")

        with col_ilrl:
            if calc_ilrl:
                specs = MaterialViaSpecs(
                    er=er_input, tan_delta_rt=tan_rt, tan_delta_4K=tan_4k, tan_delta_20mK=tan_20mk,
                    n_dielectric_layers=n_dielectric, dielectric_thickness_um=dielectric_thick,
                    via_enabled=via_en, via_diameter_um=via_d, via_density_per_mm=via_den,
                    conductor_material=mat_ilrl, conductor_thickness_um=cond_thick,
                    conductor_roughness_um=roughness, trace_width_um=w_ilrl,
                    pitch_mm=p_ilrl, length_mm=l_ilrl, frequency_GHz=f_ilrl, temperature_K=T_ilrl
                )
                result_ilrl = calc_multilayer_loss(specs)

                success("✅ 計算完成！")

                markdown("### 📊 S 參數預測")
                cols_ilrl = columns(4)
                with cols_ilrl[0]:
                    metric("插入損耗 IL", f"{result_ilrl['IL_total_dB']:.3f} dB",
                             delta=f"含Via: {result_ilrl['IL_with_via_dB']:.3f} dB", delta_color="off")
                with cols_ilrl[1]:
                    metric("反射損耗 RL", f"{result_ilrl['RL_dB']:.1f} dB",
                             delta=f"含Via: {result_ilrl['RL_with_via_dB']:.1f} dB", delta_color="off")
                with cols_ilrl[2]:
                    metric("特性阻抗", f"{result_ilrl['Z0_ohm']:.2f} Ω")
                with cols_ilrl[3]:
                    metric("有效損耗角", f"{result_ilrl['tan_delta_effective']:.2e}")

                # 損耗分解
                markdown("### 📉 損耗分解")
                breakdown = result_ilrl['loss_breakdown']
                fig_breakdown, ax_break = subplots(figsize=(8, 4))
                labels = ['Conductor Loss', 'Dielectric Loss', 'Radiation Loss']
                sizes = [breakdown['conductor_pct'], breakdown['dielectric_pct'], breakdown['radiation_pct']]
                colors = ['#ff9999', '#66b3ff', '#99ff99']
                bars = ax_break.bar(labels, sizes, color=colors, edgecolor='black', linewidth=1.5)
                ax_break.set_ylabel("Percentage (%)")
                ax_break.set_title(f"Loss Breakdown @ {f_ilrl} GHz, {T_ilrl}K")
                ax_break.set_ylim(0, max(sizes) * 1.2)
                for bar, size in zip(bars, sizes):
                    height = bar.get_height()
                    ax_break.text(bar.get_x() + bar.get_width()/2., height,
                                 f'{size:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
                pyplot(fig_breakdown)

                # 頻率響應
                markdown("### 📈 IL/RL 頻率響應")
                freqs_scan = linspace(0.1, 20, 100)
                il_scan = []
                rl_scan = []
                for f_s in freqs_scan:
                    s_temp = MaterialViaSpecs(
                        er=er_input, tan_delta_rt=tan_rt, tan_delta_4K=tan_4k, tan_delta_20mK=tan_20mk,
                        n_dielectric_layers=n_dielectric, dielectric_thickness_um=dielectric_thick,
                        via_enabled=via_en, via_diameter_um=via_d, via_density_per_mm=via_den,
                        conductor_material=mat_ilrl, conductor_thickness_um=cond_thick,
                        conductor_roughness_um=roughness, trace_width_um=w_ilrl,
                        pitch_mm=p_ilrl, length_mm=l_ilrl, frequency_GHz=f_s, temperature_K=T_ilrl
                    )
                    r_s = calc_multilayer_loss(s_temp)
                    il_scan.append(r_s['IL_total_dB'])
                    rl_scan.append(r_s['RL_dB'])

                fig_freq, ax_freq = subplots(figsize=(10, 5))
                ax_freq.plot(freqs_scan, il_scan, 'b-', linewidth=2, label='Insertion Loss (S21)')
                ax_freq.plot(freqs_scan, rl_scan, 'r--', linewidth=2, label='Return Loss (S11)')
                ax_freq.axvline(x=f_ilrl, color='green', linestyle=':', alpha=0.7, label=f'Design Freq {f_ilrl} GHz')
                ax_freq.set_xlabel("Frequency (GHz)", fontsize=12)
                ax_freq.set_ylabel("Magnitude (dB)", fontsize=12)
                ax_freq.set_title(f"S-Parameters vs Frequency ({mat_ilrl}, {T_ilrl}K, L={l_ilrl}mm)", fontsize=13)
                ax_freq.legend(fontsize=11)
                ax_freq.grid(True, alpha=0.3)
                ax_freq.set_ylim(-30, 5)
                pyplot(fig_freq)

            elif auto_opt:
                with spinner("正在執行材料/Via 自動優化..."):
                    base_specs = MaterialViaSpecs(
                        er=er_input, tan_delta_rt=tan_rt, tan_delta_4K=tan_4k, tan_delta_20mK=tan_20mk,
                        n_dielectric_layers=n_dielectric, dielectric_thickness_um=dielectric_thick,
                        via_enabled=via_en, via_diameter_um=via_d, via_density_per_mm=via_den,
                        conductor_material=mat_ilrl, conductor_thickness_um=cond_thick,
                        conductor_roughness_um=roughness, trace_width_um=w_ilrl,
                        pitch_mm=p_ilrl, length_mm=l_ilrl, frequency_GHz=f_ilrl, temperature_K=T_ilrl
                    )
                    opt_result = optimize_material_via(base_specs, target_IL_dB=target_il, target_RL_dB=target_rl)

                success("✅ 材料/Via 優化完成！")
                opt_s = opt_result["optimal_specs"]
                opt_p = opt_result["performance"]

                markdown("### 🎯 最優材料/Via 參數")
                opt_cols = columns(4)
                with opt_cols[0]:
                    metric("最優 εr", f"{opt_s.er:.2f}")
                with opt_cols[1]:
                    metric("最優介電厚", f"{opt_s.dielectric_thickness_um:.1f} μm")
                with opt_cols[2]:
                    metric("最優 Via 密度", f"{opt_s.via_density_per_mm:.2f}/mm")
                with opt_cols[3]:
                    metric("最優導體厚", f"{opt_s.conductor_thickness_um:.1f} μm")

                markdown("### 📊 優化後性能")
                perf_cols = columns(3)
                with perf_cols[0]:
                    metric("IL", f"{opt_p['IL_total_dB']:.3f} dB", delta=f"目標: {target_il} dB")
                with perf_cols[1]:
                    metric("RL", f"{opt_p['RL_dB']:.1f} dB", delta=f"目標: {target_rl} dB")
                with perf_cols[2]:
                    metric("Z₀", f"{opt_p['Z0_ohm']:.2f} Ω")

            else:
                info("👈 請輸入材料與 Via 參數，然後點擊「計算 IL/RL」或「自動優化」")
render_optimizer_section()
