# 柔性線函式庫/繪圖/側視.py
"""繪製側視圖 - 長度方向輪廓"""

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from numpy import abs, argmax, exp, linspace, sin

from .共用 import 主題顏色, 設定中文字型, 建立圖形, 計算字型大小


def 繪製側視(佈局, 字型縮放=1.0):
    """繪製側視圖
    
    參數:
        佈局: 佈局計算器實例
        字型縮放: 字型縮放比例 (0.5 ~ 2.0)
    """
    設定中文字型()
    
    n_ch = 佈局.通道數
    總寬 = 佈局.線總寬
    總厚mm = 佈局.總厚度mm
    總厚um = 佈局.總厚度um
    長度 = 佈局.線長度
    間距 = 佈局.訊號間距

    # 計算圖形尺寸
    圖寬 = max(14, 10 + 字型縮放 * 2)
    圖高 = max(7, 5 + 字型縮放 * 1.5)
    fig, ax = 建立圖形(圖寬, 圖高)

    # 標題
    fig.suptitle(f'U-leam UF1 側視 | {n_ch} 通道數 | 長度 {長度} mm',
                fontsize=14 * 字型縮放, fontweight='bold', color='white', y=0.96)

    # 連接器尺寸
    連接器長 = 12
    連接器高 = 6

    # 繪製彎曲的傳輸線
    t = linspace(0, 長度, 500)
    y_wave = 1.5 * sin(t / 60) * exp(-t / 400)
    半厚 = 總厚mm / 2

    # 主體
    ax.fill_between(t, y_wave + 半厚, y_wave - 半厚,
                   color='#C4956A', alpha=0.85, edgecolor='white', linewidth=1, zorder=2)
    ax.plot(t, y_wave + 半厚 - 0.015, 'w--', linewidth=0.6, alpha=0.5, zorder=3)
    ax.plot(t, y_wave - 半厚 + 0.015, 'w--', linewidth=0.6, alpha=0.5, zorder=3)
    ax.plot(t, y_wave, color='#FFD700', linewidth=1.2 * 字型縮放, alpha=0.9, zorder=4)

    # 左側連接器 (SMA/SMP)
    ax.add_patch(Rectangle((-連接器長, -連接器高/2), 連接器長, 連接器高,
                          facecolor='#B87333', edgecolor='white', linewidth=1.5, zorder=5))
    for j in range(4):
        ax.plot([-連接器長 + 2 + j*2.2, -連接器長 + 2 + j*2.2],
               [-連接器高/2, 連接器高/2], 'w-', linewidth=0.8, alpha=0.7, zorder=6)
    ax.add_patch(Rectangle((-連接器長 - 3, -0.15), 3, 0.3,
                          facecolor='#C0C0C0', edgecolor='white', zorder=5))

    # 右側連接器 (SMA/SMP)
    ax.add_patch(Rectangle((長度, -連接器高/2), 連接器長, 連接器高,
                          facecolor='#B87333', edgecolor='white', linewidth=1.5, zorder=5))
    for j in range(4):
        ax.plot([長度 + j*2.2, 長度 + j*2.2],
               [-連接器高/2, 連接器高/2], 'w-', linewidth=0.8, alpha=0.7, zorder=6)
    ax.add_patch(Rectangle((長度 + 連接器長, -0.15), 3, 0.3,
                          facecolor='#C0C0C0', edgecolor='white', zorder=5))

    # 彎曲半徑標註 (最大彎曲點)
    最大彎曲索引 = argmax(abs(y_wave))
    最大彎曲x = t[最大彎曲索引]
    最大彎曲y = y_wave[最大彎曲索引]
    
    ax.add_patch(Circle((最大彎曲x - 5, 最大彎曲y), 5, fill=False, 
                       edgecolor='#FF6B6B', linewidth=1.5 * 字型縮放, 
                       linestyle='--', zorder=7))
    
    註解字型 = max(9, 11 * 字型縮放)
    ax.annotate(f'R >= 5 mm', xy=(最大彎曲x - 5, 最大彎曲y + 6),
               fontsize=註解字型, color='#FF6B6B', ha='center', fontweight='bold')

    # 長度標註
    標籤字型 = max(10, 12 * 字型縮放)
    箭頭粗 = 1.8 * 字型縮放
    
    ax.annotate('', xy=(0, -連接器高/2 - 4), xytext=(長度, -連接器高/2 - 4),
               arrowprops=dict(arrowstyle='<->', color='#F85149', lw=箭頭粗))
    ax.text(長度/2, -連接器高/2 - 6, f'L = {長度} mm',
           ha='center', va='top', fontsize=標籤字型, color='#F85149', fontweight='bold')

    # 厚度標註 (右側)
    ax.annotate('', xy=(長度 + 連接器長 + 10, -半厚),
               xytext=(長度 + 連接器長 + 10, 半厚),
               arrowprops=dict(arrowstyle='<->', color='#58A6FF', 
                             lw=1.5 * 字型縮放))
    ax.text(長度 + 連接器長 + 14, 0,
           f't = {總厚um:.0f}um',
           ha='left', va='center', fontsize=註解字型 + 1,
           color='#58A6FF', fontweight='bold', rotation=90)

    # 資訊標籤
    間距字型 = max(10, 12 * 字型縮放)
    ax.text(長度/2, 連接器高/2 + 4,
           f'{n_ch} 通道 | Pitch {間距} mm | 總寬 {總寬} mm',
           ha='center', va='bottom', fontsize=間距字型,
           color='white', fontweight='bold',
           bbox=dict(boxstyle='round,pad=0.4', facecolor='#161B22',
                    edgecolor='#58A6FF', linewidth=1.5 * 字型縮放))

    # 軸設定
    ax.set_xlim(-20, 長度 + 連接器長 + 30)
    ax.set_ylim(-連接器高/2 - 12, 連接器高/2 + 12)
    ax.set_aspect('equal')
    ax.set_xlabel('長度 (mm)', color='white', fontsize=標籤字型)
    ax.set_ylabel('高度 (mm)', color='white', fontsize=標籤字型)
    ax.tick_params(colors='white', labelsize=標籤字型 - 2)

    ax.set_title('柔性傳輸線側視 | 彎曲半徑 >= 5mm | 連接器: SMA/SMP',
                fontsize=標籤字型, color='#58A6FF', fontweight='bold', pad=10)

    return fig


def 匯出側視圖png(佈局, 檔案名稱=None, 字型縮放=1.0):
    """匯出側視圖為 PNG 檔案"""
    fig = 繪製側視(佈局, 字型縮放=字型縮放)
    
    if 檔案名稱 is None:
        檔案名稱 = f"側視圖_{佈局.通道數}通道.png"
    
    fig.savefig(檔案名稱, dpi=200, bbox_inches='tight', facecolor='#0D1117')
    plt.close(fig)
    print(f"✅ 已匯出: {檔案名稱}")
    return 檔案名稱
