# 柔性線函式庫/繪圖/上視.py
"""繪製上視圖 - 支援 GSG 與 FPC"""

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from .共用 import 主題顏色, 設定中文字型, 建立圖形


def 繪製上視(佈局, 字型縮放=1.0):
    """繪製上視圖"""
    設定中文字型()

    n_ch = 佈局.通道數
    總寬 = 佈局.線總寬
    長度 = 佈局.線總長
    間距 = 佈局.訊號間距um
    訊號寬 = 佈局.訊號寬度
    層定義 = 佈局.規格層

    # 判斷是否為 FPC (有 Ground space)
    # is_FPC = 佈局.規格類型 == 'FPC'
    GroundSpace = 佈局.GroundSpace #if is_FPC else 0

    # 計算圖形尺寸
    圖寬 = max(14, 10 + 字型縮放 * 2)
    圖高 = max(8, 6 + 字型縮放 * 1.5)
    fig, ax = 建立圖形(圖寬, 圖高)

    # 標題
    fig.suptitle(f'U-leam UF1 上視 | {n_ch} 通道數 | {佈局.規格名稱}',
                fontsize=14 * 字型縮放, fontweight='bold', color='white', y=0.96)

    # 連接器尺寸
    連接器長 = 12
    連接器高 = max(6, 總寬 * 0.3)

    # 基板主體
    ax.add_patch(Rectangle((連接器長, -總寬/2), 長度, 總寬,
                          facecolor='#C4956A', edgecolor='white',
                          linewidth=1.5, alpha=0.9, zorder=2))

    # 訊號線
    線寬 = min(訊號寬, 間距 * 0.35)
    for i in range(n_ch):
        y = -總寬/2 + 間距/2 + i * 間距
        ax.add_patch(Rectangle((連接器長 + 5, y - 線寬/2), 長度 - 10, 線寬,
                              facecolor='#FFD700', edgecolor='#B8860B',
                              linewidth=0.5, alpha=0.85, zorder=3))

        # 通道編號
        字型 = max(8, 10 * 字型縮放)
        ax.text(連接器長 + 長度/2, y, f'CH{i+1}',
               ha='center', va='center', fontsize=字型,
               color='#333', fontweight='bold', zorder=4)

    # 左側連接器
    for i in range(n_ch):
        y = -總寬/2 + 間距/2 + i * 間距

        ax.add_patch(Rectangle((0, y - 連接器高/2), 連接器長, 連接器高,
                              facecolor='#B87333', edgecolor='white', linewidth=1, zorder=5))
        for j in range(3):
            ax.plot([連接器長 - 4 + j*2, 連接器長 - 4 + j*2],
                   [y - 連接器高/2, y + 連接器高/2], 'w-', linewidth=0.5, zorder=6)

    # 右側連接器
    for i in range(n_ch):
        y = -總寬/2 + 間距/2 + i * 間距

        ax.add_patch(Rectangle((連接器長 + 長度, y - 連接器高/2), 連接器長, 連接器高,
                              facecolor='#B87333', edgecolor='white', linewidth=1, zorder=5))
        for j in range(3):
            ax.plot([連接器長 + 長度 + j*2, 連接器長 + 長度 + j*2],
                   [y - 連接器高/2, y + 連接器高/2], 'w-', linewidth=0.5, zorder=6)

    # 長度標註
    標籤字型 = max(10, 12 * 字型縮放)
    箭頭粗 = 1.8 * 字型縮放

    ax.annotate('', xy=(連接器長, 總寬/2 + 8), xytext=(連接器長 + 長度, 總寬/2 + 8),
               arrowprops=dict(arrowstyle='<->', color='#F85149', lw=箭頭粗))
    ax.text(連接器長 + 長度/2, 總寬/2 + 10, f'L = {長度} mm',
           ha='center', va='bottom', color='#F85149', fontsize=標籤字型, fontweight='bold')

    # 寬度標註
    ax.annotate('', xy=(連接器長 + 長度 + 連接器長 + 8, -總寬/2),
               xytext=(連接器長 + 長度 + 連接器長 + 8, 總寬/2),
               arrowprops=dict(arrowstyle='<->', color='#F85149', lw=箭頭粗))
    註解字型 = max(9, 11 * 字型縮放)
    ax.text(連接器長 + 長度 + 連接器長 + 12, 0,
           f'W = {總寬:.3f} mm\n({n_ch}ch x {間距}mm)',
           ha='left', va='center', color='#F85149',
           fontsize=註解字型, rotation=90)

    # Pitch 標註
    if n_ch >= 2:
        y1 = -總寬/2 + 間距/2
        y2 = -總寬/2 + 間距/2 + 間距
        ax.annotate('', xy=(連接器長 + 長度/2, y1),
                   xytext=(連接器長 + 長度/2, y2),
                   arrowprops=dict(arrowstyle='<->', color='#3FB950', lw=箭頭粗))
        間距字型 = max(9, 11 * 字型縮放)
        ax.text(連接器長 + 長度/2 + 3, (y1 + y2)/2,
               f'Pitch = {間距}mm',
               ha='left', va='center', color='#3FB950', fontsize=間距字型)

    # 圖例
    圖例字型 = max(8, 10 * 字型縮放)
    圖例項目 = [
        ('#C4956A', '基板'),
        ('#FFD700', '訊號線 (NbTi)'),
        ('#B87333', 'SMA/SMP 連接器'),
    ]
    # if is_FPC:
    圖例項目.append(('#8B9CAD', f'Ground space: {GroundSpace}um'))

    for i, (顏色, 文字) in enumerate(圖例項目):
        x_pos = 0.02 + i * 0.22
        ax.add_patch(Rectangle((x_pos, 0.02), 0.03, 0.025,
                              facecolor=顏色, edgecolor='white',
                              linewidth=0.5, transform=ax.transAxes))
        ax.text(x_pos + 0.035, 0.032, 文字, transform=ax.transAxes,
               fontsize=圖例字型, color='#AAAAAA', va='center')

    # 軸設定
    右邊界 = 連接器長 + 長度 + 連接器長 + 35 + 5 * 字型縮放
    ax.set_xlim(-15, 右邊界)
    ax.set_ylim(-總寬/2 - 15, 總寬/2 + 18)
    ax.set_aspect('equal')
    ax.set_xlabel('長度 (mm)', color='white', fontsize=標籤字型)
    ax.set_ylabel('寬度 (mm)', color='white', fontsize=標籤字型)
    ax.tick_params(colors='white', labelsize=標籤字型 - 2)

    ax.set_title(f'{佈局.規格名稱} 上視 | 平行傳輸線',
                fontsize=標籤字型, color='#58A6FF', fontweight='bold', pad=10)

    return fig
