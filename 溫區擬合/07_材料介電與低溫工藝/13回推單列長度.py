from streamlit import empty, sidebar, radio, text_input, set_page_config, session_state, subheader, dataframe, columns, metric, number_input, success, caption, title, code
from pandas import DataFrame, notna
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
    AGGRID_AVAILABLE = True
except ImportError:
    AGGRID_AVAILABLE = False

# ============================================================
# 常數
# ============================================================
L0 = 2.45e-8
A_CH = 0.0635e-6       # 通道截面積 (m²)
A_SINGLE = 0.0127e-6   # 單根截面積 (m²)

# ============================================================
# 工具函式
# ============================================================
def 計算長度(L0, A, Th, Tc, Q, rho):
    """計算傳輸線長度 L = L₀ · A · (Th² - Tc²) / (2 · Q · ρ)"""
    if Q is not None and Q > 0 and rho is not None and rho > 0:
        return (L0 * A * (Th**2 - Tc**2)) / (2 * Q * rho)
    return None

def 回推熱負載(L0, A, Th, Tc, L_target, rho):
    """給定目標長度 L，回推所需熱負載 Q"""
    if L_target is not None and L_target > 0 and rho is not None and rho > 0:
        return (L0 * A * (Th**2 - Tc**2)) / (2 * L_target * rho)
    return None

def 回推電阻率(L0, A, Th, Tc, Q, L_target):
    """給定目標長度 L，回推所需電阻率 ρ"""
    if L_target is not None and L_target > 0 and Q is not None and Q > 0:
        return (L0 * A * (Th**2 - Tc**2)) / (2 * Q * L_target)
    return None

def 格式化熱負載(Q):
    """自動單位格式化熱負載"""
    if Q is None or Q <= 0:
        return "—"
    if Q >= 1e-3:
        return f"{Q * 1e3:.2f} mW"
    elif Q >= 1e-6:
        return f"{Q * 1e6:.2f} µW"
    elif Q >= 1e-9:
        return f"{Q * 1e9:.2f} nW"
    else:
        return f"{Q * 1e12:.2f} pW"

def 格式化長度(L):
    """自動單位格式化長度"""
    if L is None or L <= 0:
        return "—"
    if L >= 1:
        return f"{L:.2f} m"
    elif L >= 0.01:
        return f"{L * 100:.1f} cm"
    else:
        return f"{L * 1000:.1f} mm"

def 合理性評估(L_val, is_nbti=False):
    """評估長度合理性"""
    if L_val is None or L_val <= 0:
        return "—"
    if is_nbti:
        if L_val < 0.05:
            return "⚠️ 等效熱阻"
        return "—"
    if 0.1 <= L_val <= 2.0:
        return "✅ 合理"
    elif L_val < 0.1:
        return "⚠️ 較短"
    else:
        return "⚠️ 偏長"

# ============================================================
# 初始化溫區數據
# ============================================================
def get_initial_segments():
    """原始數據：每個溫區一行，Ag 與 NbTi 參數並列"""
    return [
        {"溫區": "300K → 50K",     "Th": 300.0, "Tc": 50.0,  "Q_ag": 2.7e-3,  "rho_ag": 1.6e-8,  "Q_nbti": None,       "rho_nbti": None},
        {"溫區": "50K → 4K",       "Th": 50.0,  "Tc": 4.0,   "Q_ag": 0.8e-3,  "rho_ag": 1.5e-8,  "Q_nbti": None,       "rho_nbti": None},
        {"溫區": "4K → 0.6K",      "Th": 4.0,   "Tc": 0.6,   "Q_ag": 5.4e-6,  "rho_ag": 1.5e-8,  "Q_nbti": 540e-9,     "rho_nbti": 6.5e-7},
        {"溫區": "0.6K → 100mK",   "Th": 0.6,   "Tc": 0.1,   "Q_ag": 290e-9,  "rho_ag": 1.5e-8,  "Q_nbti": 29e-9,      "rho_nbti": 6.5e-7},
        {"溫區": "100mK → 10mK",   "Th": 0.1,   "Tc": 0.01,  "Q_ag": 5.9e-9,  "rho_ag": 1.5e-8,  "Q_nbti": 590e-12,    "rho_nbti": 6.5e-7},
    ]

# ============================================================
# 主程式
# ============================================================
with sidebar:
    set_page_config(page_title="熱負載回推長度計算", page_icon="📊", layout="wide")

    if not AGGRID_AVAILABLE:
        error("❌ 尚未安裝 `streamlit-aggrid`，請先執行：")
        code("pip install streamlit-aggrid", language="bash")
        stop()
    # 初始化 session state
    if "segments" not in session_state:
        session_state.segments = get_initial_segments()

    # --------------------------------------------------------
    # 區塊 1：可編輯輸入參數 (AgGrid)
    # --------------------------------------------------------
    subheader("📝 輸入參數（可編輯）")
    df_input = DataFrame(session_state.segments)

    gb = GridOptionsBuilder.from_dataframe(df_input)
    gb.configure_column("溫區", editable=False, width=180, header_name="溫度段")
    gb.configure_column("Th",   editable=True,  type=["numericColumn"], width=100, header_name="Th (K)")
    gb.configure_column("Tc",   editable=True,  type=["numericColumn"], width=100, header_name="Tc (K)")
    gb.configure_column("Q_ag", editable=True,  type=["numericColumn"], width=150, header_name="Q_ag (熱負載)", valueFormatter="x.toExponential(2)")
    gb.configure_column("rho_ag", editable=True, type=["numericColumn"], width=150, header_name="ρ_ag (電阻率)", valueFormatter="x.toExponential(2)")
    gb.configure_column("Q_nbti", editable=True, type=["numericColumn"], width=150, header_name="Q_nbti (熱負載)", valueFormatter="x.toExponential(2)")
    gb.configure_column("rho_nbti", editable=True, type=["numericColumn"], width=150, header_name="ρ_nbti (電阻率)", valueFormatter="x.toExponential(2)")
    gb.configure_default_column(editable=True, resizable=True)
    grid_options = gb.build()

    grid_response = AgGrid(
        df_input,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,
        height=280,
        theme="streamlit",
        reload_data=False,
        key="input_grid",
    )

    # 取得編輯後的資料
    df_edited = grid_response["data"]

    # 同步回 session_state（避免刷新後遺失）
    session_state.segments = df_edited.to_dict("records")

def 計算():
    # --------------------------------------------------------
    # 區塊 2：計算結果（回推長度）
    # --------------------------------------------------------
    subheader("📐 回推計算結果")

    results = []
    cum_ag = 0.0
    cum_nbti = 0.0

    for _, row in df_edited.iterrows():
        Th = row["Th"]
        Tc = row["Tc"]
        Q_ag = row["Q_ag"] if notna(row["Q_ag"]) and row["Q_ag"] > 0 else None
        rho_ag = row["rho_ag"] if notna(row["rho_ag"]) and row["rho_ag"] > 0 else None
        Q_nbti = row["Q_nbti"] if notna(row["Q_nbti"]) and row["Q_nbti"] > 0 else None
        rho_nbti = row["rho_nbti"] if notna(row["rho_nbti"]) and row["rho_nbti"] > 0 else None

        # Ag 計算
        L_ag = 計算長度(L0, A_CH, Th, Tc, Q_ag, rho_ag)
        code(L_ag)
        L_single = 計算長度(L0, A_SINGLE, Th, Tc, Q_ag, rho_ag)
        if L_ag:
            cum_ag += L_ag

        # NbTi 計算
        L_nbti = 計算長度(L0, A_CH, Th, Tc, Q_nbti, rho_nbti)
        if L_nbti:
            cum_nbti += L_nbti

        # 長度比
        ratio = (L_ag / L_nbti) if (L_ag and L_nbti) else None

        # 合理性
        if L_ag is not None:
            assess = 合理性評估(L_ag, is_nbti=False)
        elif L_nbti is not None:
            assess = 合理性評估(L_nbti, is_nbti=True)
        else:
            assess = "—"

        results.append({
            "溫度段": row["溫區"],
            "Th (K)": Th,
            "Tc (K)": Tc,
            "Ag 熱負載": 格式化熱負載(Q_ag),
            "Ag 回推長度": 格式化長度(L_ag),
            "NbTi 熱負載": 格式化熱負載(Q_nbti),
            "NbTi 回推長度": 格式化長度(L_nbti),
            "長度比(Ag/NbTi)": f"{ratio:.1f}×" if ratio else "—",
            "合理性評估": assess,
            "單根長度(參考)": 格式化長度(L_single),
        })

    df_results = DataFrame(results)
    dataframe(df_results, use_container_width=True, hide_index=True)

    # --------------------------------------------------------
    # 區塊 3：累積長度
    # --------------------------------------------------------
    #divider()
    subheader("📐 累積長度")
    c1, c2 = columns(2)
    with c1:
        metric(label="Ag 累積長度", value=f"{cum_ag:.2f} m")
    with c2:
        metric(label="NbTi 累積長度", value=f"{cum_nbti:.3f} m")
    # --------------------------------------------------------
    # 區塊 4：反向回推 — 給定目標長度，反推參數
    # --------------------------------------------------------
    #divider()
    subheader("🔄 反向回推：給定目標長度，計算所需熱負載 Q")

    col1, col2, col3, col4 = columns([2, 1, 1, 1])
    with col1:
        selected_zone = radio( "選擇溫區", options=[r["溫度段"] for r in results], key="back_zone", horizontal=True)
    with col2:
        material = radio("材料", ["Ag", "NbTi"], key="back_mat")
    with col3:
        target_L = number_input(
            "目標長度 (m)",
            value=0.5,
            min_value=0.0,
            step=0.01,
            format="%.3f",
            key="back_L",
        )
    with col4:
        back_mode = radio("回推模式", ["回推 Q", "回推 ρ"], key="back_mode")

    # 找到對應溫區參數
    zone_params = next(
        (s for s in session_state.segments if s["溫區"] == selected_zone),
        None,
    )

    if zone_params:
        高溫=Th = zone_params["Th"]
        低溫=Tc = zone_params["Tc"]

        if material == "Ag":
            Q = zone_params["Q_ag"] if notna(zone_params["Q_ag"]) and zone_params["Q_ag"] > 0 else None
            rho = zone_params["rho_ag"] if notna(zone_params["rho_ag"]) and zone_params["rho_ag"] > 0 else None
        else:
            Q = zone_params["Q_nbti"] if notna(zone_params["Q_nbti"]) and zone_params["Q_nbti"] > 0 else None
            rho = zone_params["rho_nbti"] if notna(zone_params["rho_nbti"]) and zone_params["rho_nbti"] > 0 else None
        電阻, 熱負載=rho, Q
        #高溫, 低溫 = zone_params["Th"], zone_params["Tc"]
        code(['L0*A_CH*(高溫**2-低溫**2)/2./電阻/熱負載', L0*A_CH*(高溫**2-低溫**2)/2./電阻/熱負載])

        if back_mode == "回推 Q":
            if rho and target_L > 0:
                Q_back = 回推熱負載(L0, A_CH, Th, Tc, target_L, rho)
                success(
                    f"📌 **{selected_zone}** 使用 **{material}** 要達到 **{target_L:.3f} m**，"
                    f"所需熱負載 **Q = {格式化熱負載(Q_back)}**"
                )
                # 顯示原始科學記號
                caption(f"原始值: Q = {Q_back:.4e} W")
            else:
                warning("⚠️ 該溫區沒有電阻率 ρ 數據，無法回推 Q")

        else:  # 回推 ρ
            if Q and target_L > 0:
                rho_back = 回推電阻率(L0, A_CH, Th, Tc, Q, target_L)
                success(
                    f"📌 **{selected_zone}** 使用 **{material}** 要達到 **{target_L:.3f} m**，"
                    f"所需電阻率 **ρ = {rho_back:.4e} Ω·m**"
                )
            else:
                warning("⚠️ 該溫區沒有熱負載 Q 數據，無法回推 ρ")

    # --------------------------------------------------------
    # 區塊 5：單列（單根）傳輸線長度回推
    # --------------------------------------------------------
    #divider()
    subheader("🔧 單列（單根）傳輸線長度回推")
    caption("使用單根截面積 A_single = 0.0127 mm² 計算")

    col_a, col_b, col_c = columns([2, 1, 1])
    with col_a:
        single_zone = radio( "選擇溫區", [r["溫度段"] for r in results], key="single_zone", horizontal=True)
    with col_b:
        single_mat = radio("材料", ["Ag", "NbTi"], key="single_mat")
    with col_c:
        single_L = number_input(
            "目標單根長度 (m)",
            value=0.1,
            min_value=0.0,
            step=0.01,
            format="%.3f",
            key="single_L",
        )

    single_params = next(
        (s for s in session_state.segments if s["溫區"] == single_zone),
        None,
    )

    if single_params:
        Th = single_params["Th"]
        Tc = single_params["Tc"]

        if single_mat == "Ag":
            rho_s = single_params["rho_ag"] if notna(single_params["rho_ag"]) and single_params["rho_ag"] > 0 else None
        else:
            rho_s = single_params["rho_nbti"] if notna(single_params["rho_nbti"]) and single_params["rho_nbti"] > 0 else None

        if rho_s and single_L > 0:
            Q_single = 回推熱負載(L0, A_SINGLE, Th, Tc, single_L, rho_s)
            success(
                f"📌 **{single_zone}** 單根 **{single_mat}** 要達到 **{single_L:.3f} m**，"
                f"所需熱負載 **Q = {格式化熱負載(Q_single)}**"
            )
            caption(f"原始值: Q = {Q_single:.4e} W")
        else:
            warning("⚠️ 該溫區沒有所選材料的電阻率數據")

    success("✅ 計算完成")

MENU, 表單=[], ['計算', '', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  狀態=empty()
  狀態.code([])
if menu==len(表單): #
  pass
elif menu==MENU[1]: #
  pass
  計算長度()
elif menu==MENU[0]: #
  計算()

with sidebar:
    title("📊 各溫區熱負載與回推長度計算")
    caption("計算公式: L = L₀ · A · (Tₕ² - Tc²) / (2 · Q · ρ)")

