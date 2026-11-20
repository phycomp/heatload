# 柔性線函式庫/繪圖/共用.py
"""繪圖共用設定 - 字型、顏色、主題"""

import matplotlib.pyplot as plt
from matplotlib import rcParams

# 深色主題顏色
主題顏色 = {
    '背景': '#0D1117',
    '文字': '#FFFFFF',
    '軸線': '#30363D',
    '強調': '#58A6FF',
    '警告': '#F85149',
    '訊號': '#FFD700',
    '接地': '#8B9CAD',
    '介電': '#C4956A',
    '保護': '#E8D5C4',
}

def 設定中文字型():
    """設定 matplotlib 中文字型"""
    try:
        rcParams['font.sans-serif'] = ['AR PL UKai CN', 'Noto Sans CJK TC', 'Microsoft JhengHei', 'SimHei']
        rcParams['axes.unicode_minus'] = False
    except:
        # 如果指定字型不存在，使用預設
        pass

def 取得字型大小(佈局, 類別):
    """根據佈局計算字型大小"""
    基準 = 12
    if 佈局.通道數 <= 4:
        基準 = 14
    elif 佈局.通道數 <= 8:
        基準 = 13
    elif 佈局.通道數 <= 12:
        基準 = 12
    else:
        基準 = 11

    大小對照 = {
        '標題': 基準 * 1.3,
        '標籤': 基準,
        '註解': 基準 * 0.85,
        '間距': 基準 * 0.95,
        '層': 基準,
    }
    return 大小對照.get(類別, 基準)

def 建立圖形(寬, 高):
    """建立深色主題圖形"""
    fig = plt.figure(figsize=(寬, 高), facecolor=主題顏色['背景'])
    ax = fig.add_subplot(111)
    ax.set_facecolor(主題顏色['背景'])
    for spine in ax.spines.values():
        spine.set_color(主題顏色['軸線'])
    return fig, ax

# ===== 新增：計算字型大小 =====
def 計算字型大小(層厚度列表, 字型縮放=1.0):
    """根據層厚度和字型縮放計算各層字型大小"""
    字型列表 = []
    for 厚度 in 層厚度列表:
        if 厚度 < 0.01:
            字型 = 8
        elif 厚度 < 0.02:
            字型 = 9
        elif 厚度 < 0.05:
            字型 = 10
        else:
            字型 = 11
        字型 = max(6, min(18, 字型 * 字型縮放))
        字型列表.append(字型)
    return 字型列表
