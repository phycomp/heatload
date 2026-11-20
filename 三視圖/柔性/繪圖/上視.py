# 柔性線函式庫/繪圖/上視.py
"""繪製上視圖 - 平面佈局"""

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from .共用 import 主題顏色, 設定中文字型, 建立圖形


def 繪製上視(佈局, 字型縮放=1.0):
    """繪製上視圖
    
    參數:
        佈局: 佈局計算器實例
        字型縮放: 字型縮放比例 (0.5 ~ 2.0)
    """
    設定中文字型()
    
    n_ch = 佈局.通道數
    總寬 = 佈局.線總寬
    長度 = 佈局.線長度
    間距 = 佈局.訊號間距
    訊號寬mm = 佈局.訊號寬度mm

    # 計算圖形尺寸
    圖寬 = max(14, 10 + 字型縮放 * 2)
    圖高 = max(8, 6 + 字型縮放 * 1.5)
    fig, ax = 建立圖形(圖寬, 圖高)

    # 標題
    fig.suptitle(f'U-leam UF1 上視 | {n_ch} 通道數 | 長度 {長度} mm',
                fontsize=14 * 字型縮放, fontweight='bold', color='white', y=0.96)

    # 連接器尺寸
    連接器長 = 12
    連接器高 = 6

    # 基板主體
    ax.add_patch(Rectangle((連接器長, -總寬/2), 長度, 總寬,
                          facecolor='#C4956A', edgecolor='white',
                          linewidth=1.5, alpha=0.9, zorder=2))

    # 訊號線
    線寬 = min(訊號寬mm, 間距 * 0.35)
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

    # 左側連接器 (各通道獨立)
    for i in range(n_ch):
        y = -總寬/2 + 間距/2 + i * 間距
        
        ax.add_patch(Rectangle((0, y - 連接器高/2), 連接器長, 連接器高,
                              facecolor='#B87333', edgecolor='white', linewidth=1, zorder=5))
        for j in range(3):
            ax.plot([連接器長 - 4 + j*2, 連接器長 - 4 + j*2],
                   [y - 連接器高/2, y + 連接器高/2], 'w-', linewidth=0.5, zorder=6)
        ax.add_patch(Rectangle((-3, y - 0.15), 3, 0.3,
                              facecolor='#C0C0C0', edgecolor='white', zorder=5))

    # 右側連接器 (各通道獨立)
    for i in range(n_ch):
        y = -總寬/2 + 間距/2 + i * 間距
        
        ax.add_patch(Rectangle((連接器長 + 長度, y - 連接器高/2), 連接器長, 連接器高,
                              facecolor='#B87333', edgecolor='white', linewidth=1, zorder=5))
        for j in range(3):
            ax.plot([連接器長 + 長度 + j*2, 連接器長 + 長度 + j*2],
                   [y - 連接器高/2, y + 連接器高/2], 'w-', linewidth=0.5, zorder=6)
        ax.add_patch(Rectangle((連接器長 + 長度 + 連接器長, y - 0.15), 3, 0.3,
                              facecolor='#C0C0C0', edgecolor='white', zorder=5))

    # 濾波器/衰減器區域標示
    ax.add_patch(Rectangle((連接器長 + 長度*0.3, -總寬/2 - 1), 長度*0.15, 總寬 + 2,
                          facecolor='#4A90D9', edgecolor='cyan', linewidth=1.5,
                          linestyle='--', alpha=0.25, zorder=1))
    字型 = max(9, 11 * 字型縮放)
    ax.text(連接器長 + 長度*0.375, 總寬/2 + 3,
           '整合濾波器\n& 衰減器',
           ha='center', va='bottom', fontsize=字型,
           color='cyan', style='italic')

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
           f'W = {總寬:.1f} mm\n({n_ch}ch x {間距} mm)',
           ha='left', va='center', color='#F85149',
           fontsize=註解字型, rotation=90)

    # Pitch標註 (僅在通道數>=2時顯示)
    if n_ch >= 2:
        y1 = -總寬/2 + 間距/2
        y2 = -總寬/2 + 間距/2 + 間距
        ax.annotate('', xy=(連接器長 + 長度/2, y1),
                   xytext=(連接器長 + 長度/2, y2),
                   arrowprops=dict(arrowstyle='<->', color='#3FB950', lw=箭頭粗))
        間距字型 = max(9, 11 * 字型縮放)
        ax.text(連接器長 + 長度/2 + 3, (y1 + y2)/2,
               f'Pitch = {間距} mm',
               ha='left', va='center', color='#3FB950', fontsize=間距字型)

    # 圖例
    圖例字型 = max(8, 10 * 字型縮放)
    圖例項目 = [
        ('#C4956A', '聚醯亞胺基板'),
        ('#FFD700', '訊號線 (Ag/NbTi)'),
        ('#B87333', 'SMA/SMP 連接器'),
        ('#4A90D9', '濾波器/衰減器區域')
    ]
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

    ax.set_title('平面佈局 | 平行傳輸線 | 整合濾波器',
                fontsize=標籤字型, color='#58A6FF', fontweight='bold', pad=10)

    return fig


def 匯出上視圖png(佈局, 檔案名稱=None, 字型縮放=1.0):
    """匯出上視圖為 PNG 檔案"""
    fig = 繪製上視(佈局, 字型縮放=字型縮放)
    
    if 檔案名稱 is None:
        檔案名稱 = f"上視圖_{佈局.通道數}通道.png"
    
    fig.savefig(檔案名稱, dpi=200, bbox_inches='tight', facecolor='#0D1117')
    plt.close(fig)
    print(f"✅ 已匯出: {檔案名稱}")
    return 檔案名稱
