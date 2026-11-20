from streamlit import sidebar, subheader, radio, slider, number_input, tabs, info
from numpy import linspace
from plotly.graph_objects import Figure, Scatter
from 撓性Util import calc_flexible_crosstalk_modification, calc_flexible_bending_effects

with sidebar: # ========== 新增: 側邊欄撓性參數設定 ==========
    subheader("🔧 撓性/彎曲設定")
#bend_enabled = checkbox("啟用彎曲模擬", value=False)
#if bend_enabled:
    bend_radius = slider("彎曲半徑 R (mm)", 1, 50, 10, 1)
    bend_angle = slider("彎曲角度 (°)", 0, 180, 90, 15)
    bend_location = radio( "彎曲位置", ["起始端", "中間", "末端", "多點彎曲"], horizontal=True)

    # 撓性循環測試
    flex_cycles = number_input( "預期彎曲循環次數", value=1000, min_value=1, max_value=1000000)
#else:
    bend_radius = 1000  # 直線近似
    bend_angle = 0
# ========== 新增: 撓性模擬結果標籤頁 ==========

tab5 = tabs(["🔸 撓性模擬"])   #["📊 儀表板", "⏱️ 時序分析", "🔗 串擾計算", "🧮 QEC資源", "🔸 撓性模擬"]

with tab5[0]:
    subheader("🔸 撓性傳輸線彎曲效應模擬")

    #if bend_enabled:
    # 執行撓性計算
    bend_info = calc_flexible_bending_effects( trace_width_um, dielectric_thick_um, epsilon_r, bend_radius, line_length_mm)

    bend_ct = calc_flexible_crosstalk_modification(params, bend_info, bend_radius)

    # 安全性檢查
    if bend_info['bend_safe']:
        success(f"✅ 彎曲安全: R={bend_radius}mm > R_critical={bend_info['R_critical_mm']:.2f}mm")
    else:
        error(f"❌ 彎曲危險: R={bend_radius}mm < R_critical={bend_info['R_critical_mm']:.2f}mm")

    # 關鍵指標
    col1, col2, col3, col4 = columns(4)
    col1.metric("外側應力", f"{bend_info['sigma_outer_MPa']:.2f} MPa")
    col2.metric("阻抗變化", f"{bend_info['delta_Z_pct']:+.2f}%")
    col3.metric("耦合係數變化", f"{bend_ct['crosstalk_penalty_dB']:+.2f} dB")
    col4.metric("疲勞壽命", f"{bend_info['fatigue_cycles']:,} 次")

    # 彎曲半徑掃描圖
    markdown("#### 📈 彎曲半徑對電氣特性影響")

    radii = linspace(2, 50, 100)
    delta_Z_list = []
    k_penalty_list = []
    fatigue_list = []

    for R in radii:
        info = calc_flexible_bending_effects(
            trace_width_um, dielectric_thick_um, epsilon_r, R, line_length_mm
        )
        delta_Z_liappend(info['delta_Z_pct'])
        fatigue_liappend(info['fatigue_cycles'])

        p_temp = params.copy()
        p_temp['trace_spacing'] = trace_spacing_um * 1e-6
        ct_mod = calc_flexible_crosstalk_modification(p_temp, info, R)
        k_penalty_liappend(ct_mod['crosstalk_penalty_dB'])

    fig_bend = Figure()
    fig_bend.add_trace(Scatter(x=radii, y=delta_Z_list, name='阻抗變化 %', line_color='blue'))
    fig_bend.add_trace(Scatter(x=radii, y=k_penalty_list, name='串擾懲罰 dB', line_color='red'))
    fig_bend.add_vline(x=bend_info['R_critical_mm'], line_dash="dash", line_color="orange", annotation_text="臨界彎曲半徑")
    fig_bend.update_layout(xaxis_title="彎曲半徑 (mm)", yaxis_title="變化量", height=350, template="plotly_white")
    plotly_chart(fig_bend, use_container_width=True)

    # 疲勞壽命圖
    markdown("#### 🔁 疲勞壽命 vs 彎曲半徑")

    fig_fatigue = Figure()
    fig_fatigue.add_trace(Scatter(x=radii, y=fatigue_list, mode='lines', name='預估循環次數', line_color='green'))
    fig_fatigue.add_hline(y=flex_cycles, line_dash="dot", line_color="gray", annotation_text=f"需求: {flex_cycles:,} 次")
    fig_fatigue.update_layout(xaxis_title="彎曲半徑 (mm)", yaxis_title="循環次數", yaxis_type="log", height=300, template="plotly_white")
    plotly_chart(fig_fatigue, use_container_width=True)

    # 彎曲位置效應
    markdown("#### 📍 彎曲位置對串擾影響")

    bend_positions = ["起始端", "中間", "末端", "多點彎曲"]
    position_impact = []

    for pos in bend_positions:
        if pos == "起始端":
            impact = bend_ct['crosstalk_penalty_dB'] * 0.3  # 影響較小
        elif pos == "中間":
            impact = bend_ct['crosstalk_penalty_dB'] * 1.0  # 影響最大
        elif pos == "末端":
            impact = bend_ct['crosstalk_penalty_dB'] * 0.4
        else:  # 多點
            impact = bend_ct['crosstalk_penalty_dB'] * 1.5

        position_impact.append(impact)

    fig_pos = bar(x=bend_positions, y=position_impact, labels={'x': '彎曲位置', 'y': '串擾懲罰 (dB)'}, color=position_impact, color_continuous_scale='RdYlGn_r')
    plotly_chart(fig_pos, use_container_width=True)

    # 設計建議
    markdown("#### 💡 撓性設計建議")

    recommendations = []
    if bend_info['R_critical_mm'] > bend_radius:
        recommendations.append("⚠️ 增加彎曲半徑至 ≥{:.1f}mm".format(bend_info['R_critical_mm']))
    if abs(bend_info['delta_Z_pct']) > 5:
        recommendations.append("⚠️ 阻抗變化 >5%, 建議加入阻抗補償結構")
    if bend_ct['crosstalk_penalty_dB'] > 3:
        recommendations.append("⚠️ 串擾懲罰 >3dB, 建議增加線間距或加入屏蔽")
    if bend_info['fatigue_cycles'] < flex_cycles:
        recommendations.append("⚠️ 疲勞壽命不足, 建議選用更厚介電層或更大彎曲半徑")

    if recommendations:
        for rec in recommendations:
            warning(rec)
    else:
        success("✅ 當前設計滿足所有撓性要求")

    #else:
    #   info("👈 請在側邊欄勾選 **啟用彎曲模擬** 以查看撓性效應分析")
