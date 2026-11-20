from matplotlib.pyplot import rcParams, rc
from matplotlib.font_manager import findfont, FontProperties, fontManager
from pathlib import Path
字型=['Noto Sans CJK JP']#'DejaVu Sans', , 'Noto Serif CJK TC', 'Noto Sans CJK TC', 'SimHei', 'WenQuanYi Micro Hei', 'Microsoft YaHei', 'WenQuanYi Zen Hei']

def 羅列字型():
  from matplotlib import font_manager
  font_set = {f.name for f in font_manager.fontManager.ttflist}
  for f in sorted(font_set):
      print(f)

def 中文字型():
  # /usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc: Noto Sans CJK TC:style=Bold
  font_paths = [
      #"/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",   # Ubuntu 裝 fonts-noto-cjk
      # '/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc',
      '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
      # '/usr/share/fonts/noto/NotoColorEmoji.ttf',
      #'/usr/share/fonts/noto-cjk/NotoSerifCJK-Regular.ttc'
      #'/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc',
      #'/usr/share/fonts/noto-cjk/NotoSansCJK-Medium.ttc',
      #'/usr/share/fonts/noto-cjk/NotoSerifCJK-Bold.ttc',
      # '/usr/share/fonts/TTF/ukai.ttc',
      # '/usr/share/fonts/wenquanyi/wqy-microhei/wqy-microhei.ttc',
      #"/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc",          # macOS 日黑=含中文
      #"C:/Windows/Fonts/msjh.ttc", # Win10 微軟正黑
  ]
  #: 
# findfont: Generic family 'sans-serif' not found because none of the following families were found: Segoe UI Emoji, sans-serif
  for 字型 in font_paths:
    中文字型 = FontProperties(fname=字型)
  rcParams['font.sans-serif'] = ['Noto Sans CJK JP']  #, 'Segoe UI Emoji', 'sans-serif']
  return 中文字型

  #font_file = next((p for p in font_paths if Path(p).exists()), None)
  #print(font_file)
  #if font_file:
  #    fontManager.addfont(font_file)
      #rcParams['font.family']='AR PL UKai TW MBE'#AR PL UKai TW' #WenQuanYi Micro Hei'   #文泉驛微米黑,WenQuanYi Micro Hei,文泉驿微米黑'#'WenQuanYi Micro Hei'#'文泉驛微米黑,,文泉驿微米黑'
      # rcParams['font.family'] = 'Noto Sans CJK JP'#:style=Regular'Noto Sans CJK JP'  #fc-list
def 配置中文():
  # rcParams['font.family'] = ['Noto Sans CJK JP']  #, 'Segoe UI Emoji', 'sans-serif']
  rcParams['font.sans-serif'] = ['Noto Sans CJK JP']  #, 'Segoe UI Emoji', 'sans-serif']
  # Try 'Segoe UI Emoji', 'Arial Unicode MS' (macOS), or 'Apple Color Emoji'
  # rcParams['font.sans-serif'] = ['Noto Sans CJK TC']
  #rcParams['axes.unicode_minus'] = False  # Fixes minus sign issues
  rcParams['axes.unicode_minus'] = False

def 配置字型():
  #for 字 in 字型:
  #  路徑=findfont(FontProperties(family=字))     #配置為系統默認
  #  print([路徑, 字])
  #  rcParams['font.family']=字
  #  rcParams['font.sans-serif']=[字]
  rcParams['axes.unicode_minus']=False
  #noto = findfont("Noto Sans CJK TC") or 
  noto=findfont("Noto Sans CJK JP")
  return noto
  print(noto)
  rc('font', family=FontProperties(fname=noto).get_name())
  #rc('mathtext', fontset='custom', rm=noto, it=noto, bf=noto)
  #rc('font', family='DejaVu Sans')
  #rc('mathtext', fontset='dejavusans')   # 連數學模式也一起改

#['/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc', 'Noto Sans CJK JP']
