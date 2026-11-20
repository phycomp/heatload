from streamlit import button, columns, error, expander, info, json, subheader, success, text_area, warning, write, session_state
from json import JSONDecodeError, loads as jsnLoads, dumps as jsnDumps
from streamlit import multiselect, write, sidebar, radio, text_input, empty, subheader
from diff_viewer import diff_viewer
from deepdiff import DeepDiff
from pathlib import Path
def 細節():
  #col1, col2 = columns(2)

  #with col1:
  #    subheader("原始 JSON A")
  #    input_a = text_area("輸入 JSON A", value=jsnDumps(json1_default, indent=2), height=200)

  #with col2:
  #    subheader("原始 JSON B")
  #    input_b = text_area("輸入 JSON B", value=jsnDumps(json2_default, indent=2), height=200)

  # if button("比較結構"):
      # try:
  全森=session_state['全森']
  森前 = 全森[0]#jsnLoads(input_a)
  森後 = 全森[-1]#jsnLoads(input_b)
  
  # 進行結構與內容比對
  diff = DeepDiff(森前, 森後, ignore_order=True)
  
  狀態.code(diff.keys())
  #dict_keys(['values_changed'])
  #{'values_changed': {'root': {'new_value': '# 1. data/materials.json\nmaterials_json = """{\n  "FR-4": {"dk": 4.50, "df": 0.0200, "category": "standard"},\n  "FR-4_HighTg": {"dk": 4.40, "df": 0.0150, "category": "standard"},\n  "Rogers_RO4350B": {"dk": 3.66, "df": 0.0037, "category": "high_frequency"},\n  "Rogers_RO4003C": {"dk": 3.55, "df": 0.0027, "category": "high_frequency"},\n  "Megtron_6": {"dk": 3.70, "df": 0.0020, "category": "high_speed"},\n  "Isola_Itera_MW": {"dk": 3.45, "df": 0.0030, "category": "high_frequency"},\n  "Teflon_PTFE": {"dk": 2.10, "df": 0.0002, "category": "high_frequency"}\n}"""\n', 'old_value': '{\n  "FR-4": {\n    "dk": 4.50,\n    "df": 0.0200,\n    "dk_freq_coeff": {"type": "constant", "value": 4.50},\n    "df_freq_model": {"type": "constant", "value": 0.0200},\n    "copper_roughness": {"model": "hammerstad", "Rq_um": 1.5},\n    "category": "standard"\n  },\n  "FR-4_HighTg": {\n    "dk": 4.40,\n    "df": 0.0150,\n    "dk_freq_coeff": {"type": "constant", "value": 4.40},\n    "df_freq_model": {"type": "constant", "value": 0.0150},\n    "copper_roughness": {"model": "hammerstad", "Rq_um": 1.5},\n    "category": "standard"\n  },\n  "Rogers_RO4350B": {\n    "dk": 3.66,\n    "df": 0.0037,\n    "dk_freq_coeff": {"type": "constant", "value": 3.66},\n    "df_freq_model": {"type": "constant", "value": 0.0037},\n    "copper_roughness": {"model": "huray", "Rq_um": 0.8, "sphere_radius_um": 0.5},\n    "category": "high_frequency"\n  },\n  "Rogers_RO4003C": {\n    "dk": 3.55,\n    "df": 0.0027,\n    "dk_freq_coeff": {"type": "constant", "value": 3.55},\n    "df_freq_model": {"type": "constant", "value": 0.0027},\n    "copper_roughness": {"model": "huray", "Rq_um": 0.8, "sphere_radius_um": 0.5},\n    "category": "high_frequency"\n  },\n  "Megtron_6": {\n    "dk": 3.70,\n    "df": 0.0020,\n    "dk_freq_coeff": {"type": "constant", "value": 3.70},\n    "df_freq_model": {"type": "constant", "value": 0.0020},\n    "copper_roughness": {"model": "huray", "Rq_um": 0.6, "sphere_radius_um": 0.4},\n    "category": "high_speed"\n  },\n  "Isola_Itera_MW": {\n    "dk": 3.45,\n    "df": 0.0030,\n    "dk_freq_coeff": {"type": "constant", "value": 3.45},\n    "df_freq_model": {"type": "constant", "value": 0.0030},\n    "copper_roughness": {"model": "huray", "Rq_um": 0.8, "sphere_radius_um": 0.5},\n    "category": "high_frequency"\n  },\n  "Teflon_PTFE": {\n    "dk": 2.10,\n    "df": 0.0002,\n    "dk_freq_coeff": {"type": "constant", "value": 2.10},\n    "df_freq_model": {"type": "constant", "value": 0.0002},\n    "copper_roughness": {"model": "hammerstad", "Rq_um": 0.5},\n    "category": "high_frequency"\n  }\n}\n', 'diff': '--- \n+++ \n@@ -1,58 +1,10 @@\n-{\n-  "FR-4": {\n-    "dk": 4.50,\n-    "df": 0.0200,\n-    "dk_freq_coeff": {"type": "constant", "value": 4.50},\n-    "df_freq_model": {"type": "constant", "value": 0.0200},\n-    "copper_roughness": {"model": "hammerstad", "Rq_um": 1.5},\n-    "category": "standard"\n-  },\n-  "FR-4_HighTg": {\n-    "dk": 4.40,\n-    "df": 0.0150,\n-    "dk_freq_coeff": {"type": "constant", "value": 4.40},\n-    "df_freq_model": {"type": "constant", "value": 0.0150},\n-    "copper_roughness": {"model": "hammerstad", "Rq_um": 1.5},\n-    "category": "standard"\n-  },\n-  "Rogers_RO4350B": {\n-    "dk": 3.66,\n-    "df": 0.0037,\n-    "dk_freq_coeff": {"type": "constant", "value": 3.66},\n-    "df_freq_model": {"type": "constant", "value": 0.0037},\n-    "copper_roughness": {"model": "huray", "Rq_um": 0.8, "sphere_radius_um": 0.5},\n-    "category": "high_frequency"\n-  },\n-  "Rogers_RO4003C": {\n-    "dk": 3.55,\n-    "df": 0.0027,\n-    "dk_freq_coeff": {"type": "constant", "value": 3.55},\n-    "df_freq_model": {"type": "constant", "value": 0.0027},\n-    "copper_roughness": {"model": "huray", "Rq_um": 0.8, "sphere_radius_um": 0.5},\n-    "category": "high_frequency"\n-  },\n-  "Megtron_6": {\n-    "dk": 3.70,\n-    "df": 0.0020,\n-    "dk_freq_coeff": {"type": "constant", "value": 3.70},\n-    "df_freq_model": {"type": "constant", "value": 0.0020},\n-    "copper_roughness": {"model": "huray", "Rq_um": 0.6, "sphere_radius_um": 0.4},\n-    "category": "high_speed"\n-  },\n-  "Isola_Itera_MW": {\n-    "dk": 3.45,\n-    "df": 0.0030,\n-    "dk_freq_coeff": {"type": "constant", "value": 3.45},\n-    "df_freq_model": {"type": "constant", "value": 0.0030},\n-    "copper_roughness": {"model": "huray", "Rq_um": 0.8, "sphere_radius_um": 0.5},\n-    "category": "high_frequency"\n-  },\n-  "Teflon_PTFE": {\n-    "dk": 2.10,\n-    "df": 0.0002,\n-    "dk_freq_coeff": {"type": "constant", "value": 2.10},\n-    "df_freq_model": {"type": "constant", "value": 0.0002},\n-    "copper_roughness": {"model": "hammerstad", "Rq_um": 0.5},\n-    "category": "high_frequency"\n-  }\n-}\n+# 1. data/materials.json\n+materials_json = """{\n+  "FR-4": {"dk": 4.50, "df": 0.0200, "category": "standard"},\n+  "FR-4_HighTg": {"dk": 4.40, "df": 0.0150, "category": "standard"},\n+  "Rogers_RO4350B": {"dk": 3.66, "df": 0.0037, "category": "high_frequency"},\n+  "Rogers_RO4003C": {"dk": 3.55, "df": 0.0027, "category": "high_frequency"},\n+  "Megtron_6": {"dk": 3.70, "df": 0.0020, "category": "high_speed"},\n+  "Isola_Itera_MW": {"dk": 3.45, "df": 0.0030, "category": "high_frequency"},\n+  "Teflon_PTFE": {"dk": 2.10, "df": 0.0002, "category": "high_frequency"}\n+}"""'}}}
  subheader("分析結果")
  if not diff:
      success("兩者的 JSON 結構與內容完全相同！")
  else:
      # 分類顯示結構差異
      if 'dictionary_item_added' in diff:
          warning("新增的 Key（B 有，A 沒有）：")
          write(list(diff['dictionary_item_added']))
          
      if 'dictionary_item_removed' in diff:
          error("被刪除的 Key（A 有，B 沒有）：")
          write(list(diff['dictionary_item_removed']))
          
      if 'type_changes' in diff:
          info("資料型態/結構改變：")
          write(diff['type_changes'])

      # 顯示完整的差異樹狀結構
      # with expander("檢視完整 DeepDiff 物件"):
      json(diff.to_json())
                  
      #except json.JSONDecodeError:
      #    error("格式錯誤：請確保輸入的內容為有效的 JSON 格式。")
def 比較結構(d, parent_key=''):
    """遞迴提取 JSON 的所有層級 key 路徑"""
    keys = set()
    if isinstance(d, dict):
        for k, v in d.items():
            current_key = f"{parent_key}.{k}" if parent_key else k
            keys.add(current_key)
            keys.update(extract_keys(v, current_key))
    elif isinstance(d, list):
        for item in d:
            keys.update(extract_keys(item, parent_key))
    return keys

# 使用方式
杰森=['materials.json', 'materials舊.json', 'stackup_templates.json', 'stackup_templates舊.json']
MENU, 表單=[], ['比較結構', '視覺化', '細節']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  杰=multiselect('比較', 杰森, default=杰森[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  狀態=empty()
  狀態.code([])
if menu==len(表單):
  pass
elif menu==MENU[0]: #比較結構
  pass
  if 杰:
    鍵=[]
    for 典 in 杰:
      鍵杰=比較結構(典)
      鍵.append(鍵杰)
      
    狀態.code(鍵)
    鍵前, 鍵後 = 鍵[0], 鍵[-1]
    後缺 = 鍵前 - 鍵後  # A 有，B 缺少
    後增 = 鍵後 - 鍵前    # B 新增的 key

    write("A 有但 B 缺少的 Key:", 後缺)
    write("B 新增的 Key:", 後增)
elif menu==MENU[1]: #

  if 杰:
    try:session_state['全森']=全森
    except:
      全森=[]
      for 森 in 杰:
        森=Path('data')/森
        全森.append(森.read_text())
      session_state['全森']=全森
  subheader("Visual JSON Diff")

  森前, 森後=全森[0], 全森[-1]
  杰前 = jsnDumps(森前, indent=2)
  杰後 = jsnDumps(森後, indent=2)

  # 視覺化比對畫面
  狀態.code(杰)
  diff_viewer(old_text=杰前, new_text=杰後, lang="json")
elif menu==MENU[2]: #
  pass
  細節()
