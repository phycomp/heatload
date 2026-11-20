from streamlit import caption, code, columns, dataframe, divider, error, info, markdown, metric, number_input, selectbox, session_state, set_page_config, stop, subheader, success, title, warning, sidebar, radio, text_input, code
from pandas import DataFrame, notna
import streamlit as st
import pandas as pd

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
    if L is None or L <= 0:
        return "—"
    if L >= 1:
        return f"{L:.2f} m"
    elif L >= 0.01:
        return f"{L * 100:.1f} cm"
    else:
        return f"{L * 1000:.1f} mm"

def 合理性評估(L_val, is_nbti=False):
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
set_page_config(page_title="熱負載回推長度計算", page_icon="📊", layout="wide")
with sidebar:
    if not AGGRID_AVAILABLE:
        error("❌ 尚未安裝 `streamlit-aggrid`，請先執行：")
        code("pip install streamlit-aggrid", language="bash")
        stop()

    title("📊 各溫區熱負載與回推長度計算")
    caption("計算公式: L = L₀ · A · (Tₕ² - Tc²) / (2 · Q · ρ)")
    markdown("---")

    # 初始化 session state
    if "segments" not in session_state:
        session_state.segments = get_initial_segments()

from streamlit import empty
with sidebar:
    subheader("📝 1. 輸入參數表（可編輯）—— 點選列以代入計算")
    df_input = DataFrame(session_state.segments)

    gb = GridOptionsBuilder.from_dataframe(df_input)
    gb.configure_column("溫區", editable=False, width=180, header_name="溫度段", pinned="left")
    gb.configure_column("Th",   editable=True,  type=["numericColumn"], width=100, header_name="Th (K)")
    gb.configure_column("Tc",   editable=True,  type=["numericColumn"], width=100, header_name="Tc (K)")
    gb.configure_column("Q_ag", editable=True,  type=["numericColumn"], width=150, header_name="Q_ag (W)", valueFormatter="x.toExponential(2)")
    gb.configure_column("rho_ag", editable=True, type=["numericColumn"], width=150, header_name="ρ_ag (Ω·m)", valueFormatter="x.toExponential(2)")
    gb.configure_column("Q_nbti", editable=True, type=["numericColumn"], width=150, header_name="Q_nbti (W)", valueFormatter="x.toExponential(2)")
    gb.configure_column("rho_nbti", editable=True, type=["numericColumn"], width=150, header_name="ρ_nbti (Ω·m)", valueFormatter="x.toExponential(2)")
    gb.configure_default_column(editable=True, resizable=True)

    # 啟用單列選擇（點整行即可選）
    gb.configure_selection(
        selection_mode="single",
        use_checkbox=False,
        pre_selected_rows=[],
    )

    grid_options = gb.build()

    grid_response = AgGrid(
        df_input,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED,   # 捕捉編輯 + 選擇變化
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,
        height=300,
        theme="streamlit",
        reload_data=False,
        key="input_grid",
    )

def 計算(grid_response):

    # 取得編輯後的資料與選中列
    df_edited = grid_response["data"]
    selected_rows = grid_response.get("selected_rows", [])

    code(dir(selected_rows))
    #['Q_ag', 'Q_nbti', 'T', 'Tc', 'Th', '_AXIS_LEN', '_AXIS_ORDERS', '_AXIS_TO_AXIS_NUMBER', '_HANDLED_TYPES', '__abs__', '__add__', '__and__', '__annotations__', '__array__', '__array_priority__', '__array_ufunc__', '__arrow_c_stream__', '__bool__', '__class__', '__contains__', '__copy__', '__dataframe__', '__deepcopy__', '__delattr__', '__delitem__', '__dict__', '__dir__', '__divmod__', '__doc__', '__eq__', '__finalize__', '__firstlineno__', '__floordiv__', '__format__', '__ge__', '__getattr__', '__getattribute__', '__getitem__', '__getstate__', '__gt__', '__hash__', '__iadd__', '__iand__', '__ifloordiv__', '__imod__', '__imul__', '__init__', '__init_subclass__', '__invert__', '__ior__', '__ipow__', '__isub__', '__iter__', '__itruediv__', '__ixor__', '__le__', '__len__', '__lt__', '__matmul__', '__mod__', '__module__', '__mul__', '__ne__', '__neg__', '__new__', '__or__', '__pandas_priority__', '__pos__', '__pow__', '__radd__', '__rand__', '__rdivmod__', '__reduce__', '__reduce_ex__', '__repr__', '__rfloordiv__', '__rmatmul__', '__rmod__', '__rmul__', '__ror__', '__round__', '__rpow__', '__rsub__', '__rtruediv__', '__rxor__', '__setattr__', '__setitem__', '__setstate__', '__sizeof__', '__static_attributes__', '__str__', '__sub__', '__subclasshook__', '__truediv__', '__weakref__', '__xor__', '_accessors', '_accum_func', '_agg_examples_doc', '_agg_see_also_doc', '_align_for_op', '_align_frame', '_align_series', '_append_internal', '_arith_method', '_arith_method_with_reindex', '_attrs', '_box_col_values', '_can_fast_transpose', '_check_copy_deprecation', '_check_inplace_and_allows_duplicate_labels', '_check_label_or_level_ambiguity', '_clip_with_one_bound', '_clip_with_scalar', '_cmp_method', '_combine_frame', '_consolidate', '_consolidate_inplace', '_construct_axes_dict', '_construct_result', '_constructor', '_constructor_from_mgr', '_constructor_sliced', '_constructor_sliced_from_mgr', '_dir_additions', '_dir_deletions', '_dispatch_frame_op', '_drop_axis', '_drop_labels_or_levels', '_ensure_valid_index', '_find_valid_index', '_flags', '_flex_arith_method', '_flex_cmp_method', '_from_arrays', '_from_mgr', '_get_agg_axis', '_get_axis', '_get_axis_name', '_get_axis_number', '_get_axis_resolvers', '_get_block_manager_axis', '_get_bool_data', '_get_cleaned_column_resolvers', '_get_column_array', '_get_index_resolvers', '_get_item', '_get_label_or_level_values', '_get_numeric_data', '_get_value', '_get_values_for_csv', '_getitem_bool_array', '_getitem_multilevel', '_getitem_slice', '_gotitem', '_hidden_attrs', '_indexed_same', '_info_axis', '_info_axis_name', '_info_axis_number', '_info_repr', '_init_mgr', '_inplace_method', '_internal_names', '_internal_names_set', '_is_homogeneous_type', '_is_label_or_level_reference', '_is_label_reference', '_is_level_reference', '_is_mixed_type', '_iset_item', '_iset_item_mgr', '_iset_not_inplace', '_iter_column_arrays', '_ixs', '_logical_func', '_logical_method', '_maybe_align_series_as_frame', '_metadata', '_mgr', '_min_count_stat_function', '_module_source', '_needs_reindex_multi', '_pad_or_backfill', '_reduce', '_reduce_axis1', '_reindex_axes', '_reindex_multi', '_reindex_with_indexers', '_rename', '_replace_columnwise', '_repr_data_resource_', '_repr_fits_horizontal_', '_repr_fits_vertical_', '_repr_html_', '_repr_latex_', '_reset_cache', '_sanitize_column', '_select_dtypes_indices', '_series', '_set_axis', '_set_axis_name', '_set_axis_nocheck', '_set_item', '_set_item_frame_value', '_set_item_mgr', '_set_value', '_setitem_array', '_setitem_frame', '_setitem_slice', '_shift_with_freq', '_should_reindex_frame_op', '_slice', '_stat_function', '_stat_function_ddof', '_to_dict_of_blocks', '_to_latex_via_styler', '_typ', '_update_inplace', '_validate_dtype', '_values', '_where', 'abs', 'add', 'add_prefix', 'add_suffix', 'agg', 'aggregate', 'align', 'all', 'any', 'apply', 'asfreq', 'asof', 'assign', 'astype', 'at', 'at_time', 'attrs', 'axes', 'between_time', 'bfill', 'boxplot', 'clip', 'columns', 'combine', 'combine_first', 'compare', 'convert_dtypes', 'copy', 'corr', 'corrwith', 'count', 'cov', 'cummax', 'cummin', 'cumprod', 'cumsum', 'describe', 'diff', 'div', 'divide', 'dot', 'drop', 'drop_duplicates', 'droplevel', 'dropna', 'dtypes', 'duplicated', 'empty', 'eq', 'equals', 'eval', 'ewm', 'expanding', 'explode', 'ffill', 'fillna', 'filter', 'first_valid_index', 'flags', 'floordiv', 'from_arrow', 'from_dict', 'from_records', 'ge', 'get', 'groupby', 'gt', 'head', 'hist', 'iat', 'idxmax', 'idxmin', 'iloc', 'index', 'infer_objects', 'info', 'insert', 'interpolate', 'isetitem', 'isin', 'isna', 'isnull', 'items', 'iterrows', 'itertuples', 'join', 'keys', 'kurt', 'kurtosis', 'last_valid_index', 'le', 'loc', 'lt', 'map', 'mask', 'max', 'mean', 'median', 'melt', 'memory_usage', 'merge', 'min', 'mod', 'mode', 'mul', 'multiply', 'ndim', 'ne', 'nlargest', 'notna', 'notnull', 'nsmallest', 'nunique', 'pct_change', 'pipe', 'pivot', 'pivot_table', 'plot', 'pop', 'pow', 'prod', 'product', 'quantile', 'query', 'radd', 'rank', 'rdiv', 'reindex', 'reindex_like', 'rename', 'rename_axis', 'reorder_levels', 'replace', 'resample', 'reset_index', 'rfloordiv', 'rho_ag', 'rho_nbti', 'rmod', 'rmul', 'rolling', 'round', 'rpow', 'rsub', 'rtruediv', 'sample', 'select_dtypes', 'sem', 'set_axis', 'set_flags', 'set_index', 'shape', 'shift', 'size', 'skew', 'sort_index', 'sort_values', 'squeeze', 'stack', 'std', 'style', 'sub', 'subtract', 'sum', 'swaplevel', 'tail', 'take', 'to_clipboard', 'to_csv', 'to_dict', 'to_excel', 'to_feather', 'to_hdf', 'to_html', 'to_iceberg', 'to_json', 'to_latex', 'to_markdown', 'to_numpy', 'to_orc', 'to_parquet', 'to_period', 'to_pickle', 'to_records', 'to_sql', 'to_stata', 'to_string', 'to_timestamp', 'to_xarray', 'to_xml', 'transform', 'transpose', 'truediv', 'truncate', 'tz_convert', 'tz_localize', 'unstack', 'update', 'value_counts', 'values', 'var', 'where', 'xs', '溫區']
    # 同步回 session_state
    session_state.segments = df_edited.to_dict("records")

    # 保留選中列到 session_state（避免 AgGrid key 刷新後遺失）
    if selected_rows is not None and len(selected_rows) > 0:
        session_state.selected_row = selected_rows#[0]

    selected_row = session_state.get("selected_row", None)

    markdown("---")

    # --------------------------------------------------------
    # 區塊 2：若選中列，顯示該列的「正推計算結果」與「回推面板」
    # --------------------------------------------------------
    if selected_row is not None:
        subheader("🎯 2. 已選溫區：正推計算結果")

        # 提取選中列參數
        zone_name = selected_row.get("溫區", "—")
        Th = float(selected_row.get("Th").iloc[0])
        Tc = float(selected_row.get("Tc").iloc[0])
        Q_ag = selected_row.get("Q_ag").iloc[0]
        rho_ag = selected_row.get("rho_ag").iloc[0]
        Q_nbti = selected_row.get("Q_nbti").iloc[0]
        rho_nbti = selected_row.get("rho_nbti").iloc[0]

        # 清理 NaN / None
        Q_ag = float(Q_ag) if Q_ag is not None and notna(Q_ag) and Q_ag > 0 else None
        rho_ag = float(rho_ag) if rho_ag is not None and notna(rho_ag) and rho_ag > 0 else None
        Q_nbti = float(Q_nbti) if Q_nbti is not None and notna(Q_nbti) and Q_nbti > 0 else None
        rho_nbti = float(rho_nbti) if rho_nbti is not None and notna(rho_nbti) and rho_nbti > 0 else None

        # 正推計算
        L_ag = 計算長度(L0, A_CH, Th, Tc, Q_ag, rho_ag)
        L_nbti = 計算長度(L0, A_CH, Th, Tc, Q_nbti, rho_nbti)
        L_single_ag = 計算長度(L0, A_SINGLE, Th, Tc, Q_ag, rho_ag)
        L_single_nbti = 計算長度(L0, A_SINGLE, Th, Tc, Q_nbti, rho_nbti)

        ratio = (L_ag / L_nbti) if (L_ag and L_nbti) else None
        assess_ag = 合理性評估(L_ag, is_nbti=False) if L_ag else None
        assess_nbti = 合理性評估(L_nbti, is_nbti=True) if L_nbti else None

        # 顯示正推結果卡片
        c1, c2, c3 = columns(3)
        with c1:
            markdown(f"**溫度段**：`{zone_name}`")
            markdown(f"**Th (K)**：{Th}")
            markdown(f"**Tc (K)**：{Tc}")
        with c2:
            markdown("#### Ag")
            markdown(f"- 熱負載 Q：{格式化熱負載(Q_ag)}")
            markdown(f"- 回推長度：{格式化長度(L_ag)}")
            markdown(f"- 單根長度：{格式化長度(L_single_ag)}")
            markdown(f"- 合理性：{assess_ag if assess_ag else '—'}")
        with c3:
            markdown("#### NbTi")
            markdown(f"- 熱負載 Q：{格式化熱負載(Q_nbti)}")
            markdown(f"- 回推長度：{格式化長度(L_nbti)}")
            markdown(f"- 單根長度：{格式化長度(L_single_nbti)}")
            markdown(f"- 合理性：{assess_nbti if assess_nbti else '—'}")
            if ratio:
                markdown(f"- 長度比(Ag/NbTi)：{ratio:.1f}×")

        markdown("---")

        # --------------------------------------------------------
        # 區塊 3：回推面板 — 用選中列參數代入
        # --------------------------------------------------------
        subheader("🔄 3. 回推計算 — 給定目標長度，求所需參數")

        col_mat, col_mode, col_val = columns([1, 1, 2])
        with col_mat:
            back_material = selectbox("材料", ["Ag", "NbTi"], key="back_mat")
        with col_mode:
            back_mode = selectbox("回推模式", ["回推 Q", "回推 ρ"], key="back_mode")
        with col_val:
            target_L = number_input(
                "目標長度 L_target (m)",
                value=0.5,
                min_value=0.0001,
                step=0.01,
                format="%.4f",
                key="back_L",
            )

        # 根據選擇的材料取對應參數
        if back_material == "Ag":
            Q_src = Q_ag
            rho_src = rho_ag
        else:
            Q_src = Q_nbti
            rho_src = rho_nbti

        markdown(f"**選中溫區**：`{zone_name}` ｜ **Th**={Th} K ｜ **Tc**={Tc} K ｜ **材料**={back_material}")

        if back_mode == "回推 Q":
            if rho_src and target_L > 0:
                Q_back = 回推熱負載(L0, A_CH, Th, Tc, target_L, rho_src)
                Q_single_back = 回推熱負載(L0, A_SINGLE, Th, Tc, target_L, rho_src)

                success(
                    f"📌 通道截面積 (A={A_CH:.4e} m²)：達到 **{target_L:.4f} m** 需要 **Q = {格式化熱負載(Q_back)}**"
                )
                success(
                    f"📌 單根截面積 (A_single={A_SINGLE:.4e} m²)：達到 **{target_L:.4f} m** 需要 **Q = {格式化熱負載(Q_single_back)}**"
                )
                caption(f"原始值：Q_channel = {Q_back:.4e} W ｜ Q_single = {Q_single_back:.4e} W")
            else:
                warning("⚠️ 該溫區無此材料的電阻率 ρ 數據，無法回推 Q")

        else:  # 回推 ρ
            if Q_src and target_L > 0:
                rho_back = 回推電阻率(L0, A_CH, Th, Tc, Q_src, target_L)
                rho_single_back = 回推電阻率(L0, A_SINGLE, Th, Tc, Q_src, target_L)

                success(
                    f"📌 通道截面積：達到 **{target_L:.4f} m** 需要 **ρ = {rho_back:.4e} Ω·m**"
                )
                success(
                    f"📌 單根截面積：達到 **{target_L:.4f} m** 需要 **ρ = {rho_single_back:.4e} Ω·m**"
                )
            else:
                warning("⚠️ 該溫區無此材料的熱負載 Q 數據，無法回推 ρ")

    else:
        info("👆 請點選上方表格的任一列，將自動代入該溫區參數進行計算。")

    markdown("---")

    # --------------------------------------------------------
    # 區塊 4：全表計算結果總覽
    # --------------------------------------------------------
    subheader("📋 4. 全表計算結果總覽")

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

        L_ag = 計算長度(L0, A_CH, Th, Tc, Q_ag, rho_ag)
        L_single = 計算長度(L0, A_SINGLE, Th, Tc, Q_ag, rho_ag)
        L_nbti = 計算長度(L0, A_CH, Th, Tc, Q_nbti, rho_nbti)

        if L_ag: cum_ag += L_ag
        if L_nbti: cum_nbti += L_nbti

        ratio = (L_ag / L_nbti) if (L_ag and L_nbti) else None
        assess = 合理性評估(L_ag, is_nbti=False) if L_ag else (合理性評估(L_nbti, is_nbti=True) if L_nbti else "—")

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

    divider()
    subheader("📐 累積長度")
    c1, c2 = columns(2)
    with c1:
        metric(label="Ag 累積長度", value=f"{cum_ag:.2f} m")
    with c2:
        metric(label="NbTi 累積長度", value=f"{cum_nbti:.3f} m")

    success("✅ 計算完成 — 點選表格列可即時代入回推")

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
elif menu==MENU[0]: #計算
    # --------------------------------------------------------
    # 區塊 1：可編輯輸入參數 (AgGrid) + 單選列
    # --------------------------------------------------------
    code(dir(grid_response))
    if grid_response:
      計算(grid_response)
