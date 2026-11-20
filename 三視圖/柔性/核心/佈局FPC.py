### `柔性線函式庫/核心/佈局計算.py`（更新支援新參數）

# 柔性線函式庫/核心/佈局計算.py
"""佈局計算器 - 支援 GSG 7層 與 FPC 12層"""

from .層FPC import 計算各層位置, 計算H1H2, 計算CableWidth, 全參數 #取得層定義,
from streamlit import session_state

class 佈局計算器:
    """佈局計算器 - 支援多種傳輸線規格"""

    def 額外(self, 預設):
    # if 規格類型 == 'FPC':
        self.H1, self.H2 = 計算H1H2(self.規格層)
        # 計算 Cable Width
        self.CableWidth = 計算CableWidth(self.規格層)
        self.GroundSpace = 預設.get('GroundSpace', 100.)
        self.PitchSMPM = 預設.get('Pitch_SMPM', 3560.)

    def __init__(self, 規格層=None, 通道數=8, 訊號寬度um=None, 線總寬=None, 線總長=None, 訊號厚度um=None, 鈦比例=53., 訊號單側間距um=None, GroundSpace=None): #訊號間距=None,

        # 預設 = 全參數.get(規格類型, 全參數['GSG'])

        # print(訊號寬度um)
        self.訊號寬度um = 訊號寬度um #if 訊號寬度um is not None else 預設['訊號寬度um']
        self.單元um=self.訊號寬度um+訊號單側間距um*2
        self.規格層 = 規格層
        self.通道數 = 通道數
        # self.訊號間距 = 訊號間距 if 訊號間距 is not None else 預設['訊號間距']
        self.線總寬um = 線總寬 #if 線總寬 is not None else 預設['線總寬']
        self.線總寬 = self.線總寬um/1000. #if 線總寬 is not None else 預設['線總寬']
        self.線總長 = 線總長 #if 線長度 is not None else 預設['線長度']
        self.訊號厚度um = 訊號厚度um  # if 訊號厚度um is not None else 預設['訊號厚度um']
        self.訊號間距um = self.單元um+GroundSpace #+self.訊號寬度um  # if 訊號厚度um is not None else 預設['訊號厚度um'] D1+100+D1+訊號寬度 亦即為unitCell+GroundSpace
        self.鈦比例 = 鈦比例

        # 取得對應的層定義
        # self.層定義 = 取得層定義(規格類型)
        # print(['規格層', self.規格層])
        self.層位置列表, self.線總厚um = 計算各層位置(self.規格層)

        #else:
        #    self.H1, self.H2 = 0, 0
        #    self.CableWidth = None
        #    self.GroundSpace = 0
        #    self.PitchSMPM = 0
        預設=session_state.FPC參數
        self.額外(預設) # 計算 H1, H2 (FPC 專用)

        # 計算衍生參數
        self.訊號寬度 = self.訊號寬度um / 1000.0
        self.訊號厚度 = self.訊號厚度um / 1000.0
        self.線總厚 = self.線總厚um / 1000.0
        self.鈮鈦比例 = f'{100 - self.鈦比例:.0f}:{self.鈦比例:.0f}'
        self.長寬高 = f'{self.線總長}mmx{self.線總寬:.0f}mmx{self.線總厚um:.1f}um'

        # 計算邊緣間距
        self.邊緣間距 = GroundSpace #(self.線總寬 - self.訊號間距 * (self.通道數 - 1) - self.訊號寬度mm) / 2.0
        self.左側間距 = self.邊緣間距
        self.右側間距 = self.邊緣間距
        self.總間距 = self.左側間距 + self.右側間距

        # 取得各層中心與厚度
        self.層中心列表 = [位置['中心mm'] for 位置 in self.層位置列表]
        self.層厚度列表 = [位置['厚度mm'] for 位置 in self.層位置列表]
        self.規格名稱=session_state.規格名稱
