# 柔性線函式庫/核心/佈局計算.py
"""佈局計算器 - 支援 GSG 7層 與 FPC 11層"""

from .層II import 取得層定義, 計算各層位置, 預設參數


class 佈局計算器:
    """佈局計算器 - 支援多種傳輸線規格"""

    def __init__(self, 規格類型='GSG', 通道數=8, 訊號間距=None, 訊號寬度um=None, 
                 線總寬=None, 線長度=None, 訊號厚度um=None, 鈦比例=53.0):
        
        # 取得預設參數
        預設 = 預設參數.get(規格類型, 預設參數['GSG'])
        
        # 使用傳入值或預設值
        self.規格類型 = 規格類型
        self.通道數 = 通道數
        self.訊號間距 = 訊號間距 if 訊號間距 is not None else 預設['訊號間距']
        self.訊號寬度um = 訊號寬度um if 訊號寬度um is not None else 預設['訊號寬度um']
        self.線總寬 = 線總寬 if 線總寬 is not None else 預設['線總寬']
        self.線長度 = 線長度 if 線長度 is not None else 預設['線長度']
        self.訊號厚度um = 訊號厚度um if 訊號厚度um is not None else 預設['訊號厚度um']
        self.鈦比例 = 鈦比例
        
        # 取得對應的層定義
        self.層定義 = 取得層定義(規格類型)
        self.層位置列表, self.總厚度um = 計算各層位置(self.層定義)
        
        # 計算衍生參數
        self.訊號寬度mm = self.訊號寬度um / 1000.0
        self.訊號厚度mm = self.訊號厚度um / 1000.0
        self.總厚度mm = self.總厚度um / 1000.0
        self.鈮鈦比例 = f'{100 - self.鈦比例:.0f}:{self.鈦比例:.0f}'
        self.長寬高 = f'{self.線長度}x{self.線總寬:.0f}x{self.總厚度mm:.1f}'
        
        # 計算邊緣間距
        self.邊緣間距 = (self.線總寬 - self.訊號間距 * (self.通道數 - 1) - self.訊號寬度mm) / 2.0
        self.左側間距 = self.邊緣間距
        self.右側間距 = self.邊緣間距
        self.總間距 = self.左側間距 + self.右側間距
        
        # 取得各層中心與厚度
        self.層中心列表 = [位置['中心mm'] for 位置 in self.層位置列表]
        self.層厚度列表 = [位置['厚度mm'] for 位置 in self.層位置列表]
        
        # 取得規格名稱
        from .層II import 規格名稱
        self.規格名稱 = 規格名稱.get(規格類型, '未知規格')
    
    def 取得層定義(self):
        """回傳當前使用的層定義"""
        return self.層定義
