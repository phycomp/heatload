from streamlit import info, json, session_state, success, empty
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

# 1. 建立 GridOptions + onSelectionChanged 回呼
def 分頁(資框):
  gb = GridOptionsBuilder.from_dataframe(資框)
  gb.configure_selection(selection_mode="single", use_checkbox=True)

  # 2. JavaScript：點選後把整列資料傳回 Streamlit
  js_code = JsCode("""
  function onSelectionChanged(event) {
      var selectedRows = gridOptions.api.getSelectedRows();
      if (selectedRows.length > 0) {
          // 把整列資料傳回 Streamlit（透過 streamlit-aggrid 的自訂事件）
          window.parent.postMessage({type: 'SET_SELECTION', row: selectedRows[0]}, '*');
      }
  }
  """)

  gb.configure_grid_options(onSelectionChanged=js_code)

  # 3. 監聽自訂事件（取出點選的 row）
  selected = None
  if "aggrid_selection" not in session_state:
      session_state.aggrid_selection = None

  # 監聽自訂事件（透過 components.v1.html 監聽）
  import streamlit.components.v1 as components
  components.html("""
  <script>
  window.addEventListener('message', function(event) {
      if (event.data.type === 'SET_SELECTION') {
          window.parent.postMessage({type: 'streamlit:setComponentValue', value: event.data.row}, '*');
      }
  });
  </script>
  """, height=0)

  grid_response = AgGrid(
      資框,
      gridOptions=gb.build(),
      height=300,
      allow_unsafe_jscode=True,
      key="my_grid"
  )

  狀態=empty()
  #if grid_response.selected_rows.all():
  if grid_response.selected_rows is not None and len(grid_response.selected_rows) > 0:
      #狀態.code(grid_response.selected_rows)
      return grid_response.selected_rows
      #Network(selected)
      #success("✅ 你點選的列：")
      #json(selected)          # 完整 row 資料
      #pack_sn = selected.get("pack_sn")
      #info(f"pack_sn = {pack_sn}")
