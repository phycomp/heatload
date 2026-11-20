from matplotlib.pyplot import figure, savefig, show, subplot, tight_layout
from streamlit import empty, pyplot, sidebar, radio, text_input
from numpy import exp, linspace, log, sqrt
from 德夫Util import *
#import numpy as np
from fontUtil2 import 配置中文
配置中文()
狀態=empty()

MENU, 表單=[], ['HJ', '頻率色散', '串擾機制', '近遠場', '串擾抑制', '優化']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
if menu==len(表單): #
  pass
elif menu==MENU[5]: #
  fig=優化()
  pyplot(fig)
elif menu==MENU[4]: #
  fig=串擾抑制()
  pyplot(fig)
elif menu==MENU[3]: #
  fig=近遠場()
  pyplot(fig)
elif menu==MENU[2]: #
  fig=串擾機制()
  pyplot(fig)
elif menu==MENU[1]: #
  fig=頻率色散()
  pyplot(fig)
elif menu==MENU[0]: #繪製
  fig=HJ模型()
  pyplot(fig)

#plt.tight_layout()
#plt.savefig('/mnt/kimi/output/crosstalk_analysis_hammerstad_jensen.png', dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
#plt.show()

狀態.code("技術分析圖已生成：Hammerstad-Jensen 模型適用性與串擾抑制策略")
