from skrf import Network
from streamlit import dataframe, sidebar, radio, text_input, empty, session_state
# load_pickle.py
from psycopg import connect as pgCnnct
from pickle import dumps as pcklDumps, loads as pcklLoads
from pathlib import Path
from pandas import DataFrame
from snpUtil import 繪製皮可, 取出日誌, 取出皮可, 網絡, 視皮可

MENU, 表單=[], ['匯入皮可', '視覺', '視皮可', '網絡']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  根=Path("~/Desktop/bk2測試/FAIL__20260106_153324")
if menu==len(表單): #
  pass
elif menu==MENU[3]: #
  with sidebar:
    鍵=radio('網絡', range(10), horizontal=True)
  if 鍵:
    net=網絡(pk=鍵)
    net
    視皮可(net)
elif menu==MENU[2]: #
  皮狀態=empty()
  try: 皮資=session_state['皮資']
  except:
    結果=取出皮可()
    皮資=session_state['皮資']=DataFrame(結果)
  with sidebar:
    皮號=radio('表單', 皮資['id'], horizontal=True, index=0)

  if 皮號:
    資框=皮資[皮資['id']==皮號]
    皮可=資框['皮可'].str
    #皮可=皮可.iloc[:, 0]
    資框['網絡'] = 資框['皮可'].apply(lambda b: pcklLoads(b) if b else None)
    資框
    #net=pcklLoads(皮可)
    #net
    #視皮可(資框)
    #皮狀態.code(len(眾皮可))
elif menu==MENU[1]: #
  資框=取出日誌()   #皮可
  with sidebar:
    路徑=radio('路徑', 資框['路徑'], horizontal=True)
  if 路徑:
    識別=資框[資框['路徑']==路徑]['id']
    皮資=取出皮可()
    #皮資.columns
    皮框=皮資[皮資['日誌_id'].isin(list(識別))]
    with sidebar:
      網絡=radio('網絡', 皮框['id'], horizontal=True)
    if 網絡:
      皮=皮框[皮框['id']==網絡][['檔', '皮可']]
      繪製皮可(皮)
      #視皮可(皮)
    #皮列 = 皮框.to_dict(orient='records')
    #dataframe(皮列)
elif menu==MENU[0]: #匯入皮可
  from 匯入摸石 import 主匯入
  主匯入(根)
  #conn=pgCnnct(**dbConfig)
  #with conn.cursor() as cur:
  #  for 檔 in 根.expanduser().rglob('*.s*p'):
  #    #buf = BytesIO(f.read_bytes())
  #    #buf.name = f.name          # 避開 AttributeError
  #    #net = Network(檔)
  #    #nets.append(net)
  #    #pk = 匯入皮可(cur, 檔)
  #    net = Network(檔)
  #    皮可 = pcklDumps(net)
  #    cur.execute(
  #        """INSERT INTO 皮可(檔, 皮可) VALUES (%s,%s)""",
  #        (檔.name, 皮可)
  #    )
  #conn.commit()
  # RETURNING id
  #狀態.code([f"✅ {檔.name} → id {pk}"])
  #return cur.fetchone()[0]
  #狀態.code(net.__dict__)
