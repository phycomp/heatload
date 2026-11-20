from matplotlib.pyplot import Line2D, figure, rcParams, savefig, show, tight_layout
from numpy import cos, linspace, pi, sin
from streamlit import pyplot, radio, text_input, sidebar, columns as CLMN, markdown, code
from matplotlib.pyplot import rcParams
import matplotlib.patches as patches
#import numpy as np
from cf3Util import 立體框架, 橫截面, 俯視圖, 挖洞, 連接器端, 彎曲半徑

rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans'] # 設定中文字型
rcParams['axes.unicode_minus'] = False

MENU, 表單=[], ['立體框架', '橫截面', '俯視圖', '挖洞', '連接器端', '彎曲半徑']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
if menu==len(表單): #
  pass
elif menu==MENU[5]: #
  fig, 總尺寸=彎曲半徑()
  左, 右=CLMN([4, 2])
  with 左:
    pyplot(fig)
  with 右:
    code(總尺寸)
elif menu==MENU[4]: #
  pass
  fig=連接器端()
  pyplot(fig)
elif menu==MENU[3]: #
  pass
  fig=挖洞()
  pyplot(fig)
elif menu==MENU[2]: #
  fig=俯視圖()
  pyplot(fig)
elif menu==MENU[1]: #
  fig=橫截面()
  pyplot(fig)
elif menu==MENU[0]: #['立體框架
  pass
  fig=立體框架()
  pyplot(fig)
