from streamlit import button, cache_data, download_button, error, expander, file_uploader, session_state, set_page_config, subheader, success, text, text_input, warning, write, sidebar, columns, checkbox, radio, empty, pyplot
from core.presets import load_presets, save_presets
from core.sensitivity import all_sweeps, summarize
from core.model import edge_coupled_surface_microstrip_zdd
from core.validators import clamp_params
from core.history import add_history, clear_history
from core.units import to_um, from_um
from core.units import UNIT_TO_UM
from 輸出入.excel_reader import read_nominal_from_xlsx
from 輸出入.excel_writer import build_excel
from 輸出入.json_export import to_json
# from ui.sidebar import render_sidebar
from ui.nominal_inputs import render_nominal
from ui.sweep_settings import render_sweep
from ui.results_table import render_results
from ui.charts import render_charts
from ui.formula_view import render_formula
from ui.geometry_view import render_geometry
from pandas import DataFrame

set_page_config(page_title="ECSM Sensitivity", layout="wide")
MENU, 表單=[], ['幾何截面', '掃描結果', 'Preset', '重算', '匯出']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
狀態=empty()
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  presets = load_presets()
  # unit, taper_mode, preset_name = render_sidebar(presets)
  unit = radio("單位", list(UNIT_TO_UM.keys()), index=0, horizontal=True)
  taper_mode = radio("Taper 負值處理", ["A", "B"], index=0, help="A: W2=W1-MIN_TAPER；B: W2=W1", horizontal=True)
  preset_name = radio("Preset", list(presets.keys()), horizontal=True)

  # 上傳 xlsx
  uploaded = file_uploader("上傳既有 xlsx 讀 nominal", type=["xlsx"])
  if uploaded is not None:
      try:
          nom_loaded = read_nominal_from_xlsx(uploaded)
          success(f"已讀取 nominal：{nom_loaded}")
          if button("套用上傳 nominal"):
              session_state["uploaded_nominal"] = nom_loaded
      except Exception as e:
          error(f"讀取失敗：{e}")

  preset = session_state.get("uploaded_nominal", presets[preset_name])

  nominal_disp = render_nominal(preset, unit)
  cfg = render_sweep()
  狀態=empty()
  狀態.code(['cfg=', cfg])

if menu==len(表單):
  pass
elif menu==MENU[0]: #幾何截面
  if "nominal_um" in session_state:
    subheader("幾何截面")
    c1, c2 = columns([1, 3])
    with c1:
        show_dims = checkbox("顯示尺寸標註", value=True)
        show_grid = checkbox("顯示格線", value=False)
    render_geometry(
        session_state["nominal_um"],
        session_state["unit"],
        show_dims=show_dims,
        show_grid=show_grid,
    )

elif menu==MENU[1]: #
  # 顯示結果
  if "results" in session_state:
    render_results(session_state["results"], session_state["summary"])
    render_charts(session_state["results"], session_state["summary"])
    render_formula(session_state["results"], session_state["nominal_z"])
elif menu==MENU[2]: #
# Preset 儲存
  # with expander("Preset 管理"):
    new_name = text_input("新 preset 名稱")
    if button("儲存目前 nominal 為 preset"):
        if new_name:
            presets[new_name] = nominal_disp
            save_presets(presets)
            success(f"已儲存 {new_name}")
    if button("刪除目前 preset") and preset_name in presets:
        del presets[preset_name]
        save_presets(presets)
        warning("已刪除，重新整理後生效")

elif menu==MENU[3]: #
# 按 Calculate 才重算
  # if button("Calculate"):
    # 轉 µm
    nom_um = {k: (to_um(v, unit) if k != "Er1" else v) for k, v in nominal_disp.items()}
    nom_um, warns = clamp_params(nom_um, taper_mode)
    for w in warns:
        warning(w)

    @cache_data(show_spinner=False)
    def cached_sweeps(nom_tuple, cfg_tuple, taper_mode):
        nom = dict(nom_tuple)
        cfg = dict(cfg_tuple)
        return all_sweeps(nom, cfg, taper_mode)

    results = cached_sweeps(tuple(nom_um.items()), tuple(cfg.items()), taper_mode)
    z0 = edge_coupled_surface_microstrip_zdd(**nom_um)
    summary = summarize(results, z0)
    資框=DataFrame(summary)
    資框

    session_state["results"] = results
    session_state["summary"] = summary
    session_state["nominal_um"] = nom_um
    session_state["nominal_z"] = z0
    session_state["cfg"] = cfg
    session_state["unit"] = unit
    session_state["taper_mode"] = taper_mode
    add_history(session_state, nom_um, cfg, taper_mode, unit, results, summary)


elif menu==MENU[4]: #
    # 匯出
    subheader("匯出")
    xlsx_bytes = build_excel(
        session_state["nominal_um"],
        session_state["cfg"],
        session_state["results"],
        session_state["summary"],
        session_state["unit"],
    )
    download_button("下載 Excel", xlsx_bytes, file_name="ecsm_sensitivity.xlsx")
    json_str = to_json(
        session_state["nominal_um"],
        session_state["cfg"],
        session_state["taper_mode"],
        session_state["unit"],
        session_state["results"],
        session_state["summary"],
    )
    download_button("下載 JSON", json_str, file_name="ecsm_sensitivity.json")

# 歷史
    def 計算歷史():
    # with expander("計算歷史"):
      hist = session_state.get("history", [])
      write(f"共 {len(hist)} 筆")
      for i, h in enumerate(reversed(hist)):
          text(f"{h['time']} | unit={h['unit']} | taper={h['taper_mode']}")
      if button("清除歷史"):
          clear_history(session_state)
          success("已清除")
    計算歷史()

with sidebar:
  subheader("Edge-Coupled Surface Microstrip Sensitivity")
