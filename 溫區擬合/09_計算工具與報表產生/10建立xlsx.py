from streamlit import session_state, sidebar, text_input, empty, radio

MENU, 表單=[], ['封面', '參數設定', '計算結果', 'CuNi比較', 'Al遮蔽', '物理推導', '等效熱阻']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
狀態=empty()
if menu==len(表單): #
  pass
elif menu==MENU[6]: #
  pass
elif menu==MENU[5]: #
  pass
elif menu==MENU[4]: #
  pass
elif menu==MENU[3]: #
  pass
  wb=session_state['wb']
  from CuNi比較 import CuNi比較
  wb=CuNi比較(wb)
  session_state['wb']=wb
  狀態.code('計算結果完成')
elif menu==MENU[2]: #
  wb=session_state['wb']
  from 計算結果 import 計算結果
  wb=計算結果(wb)
  session_state['wb']=wb
  狀態.code('計算結果完成')
elif menu==MENU[1]: #
  wb=session_state['wb']
  from 參數設定 import 參數設定
  wb=參數設定(wb)
  session_state['wb']=wb
  狀態.code('參數設定完成')
elif menu==MENU[0]: #封面
  pass
  from 封面說明 import wb
  session_state['wb']=wb
