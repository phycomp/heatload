# 柔性線函式庫/繪圖/前視.py
"""繪製前視圖 - GSG 7層橫截面"""

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from numpy import linspace

from 核心.層 import 層定義
from .共用 import 主題顏色, 設定中文字型, 建立圖形


def 繪製前視(佈局):
    """繪製前視圖"""
    設定中文字型()
    
    n_ch = 佈局.通道數
    總寬 = 佈局.線總寬
    層位置 = 佈局.層位置列表
    層中心 = 佈局.層中心列表
    層厚度 = 佈局.層厚度列表
    訊號寬 = 佈局.訊號寬度mm
    間距 = 佈局.訊號間距

    # 計算圖形尺寸
    圖寬 = max(12, 8 + n_ch * 0.5)
    圖高 = 6
    fig, ax = 建立圖形(圖寬, 圖高)

    # 標題
    fig.suptitle(f'U-leam UF1 前視 | {n_ch} 通道數 | GSG 7層疊構', 
                 fontsize=14, fontweight='bold', color='white', y=0.96)

    # 層名稱（完整與縮短）
    完整名稱 = ['保護層-底', '接地層-底', '介電層-下', f'訊號線(x{n_ch})', '介電層-上', '接地層-上', '保護層-上']
    短名稱 = ['保護-底', 'GND-底', '介電-下', '訊號', '介電-上', 'GND-上', '保護-上']

    # 繪製各層
    for i, (層, 位置) in enumerate(zip(層定義, 層位置)):
        下緣 = 位置['下緣mm']
        上緣 = 位置['上緣mm']
        厚度 = 位置['厚度mm']
        顏色 = 層['顏色']
        邊緣色 = 層['邊緣']
        是訊號 = 層['是訊號層']

        if 是訊號:
            # 訊號線
            線寬 = min(訊號寬, 間距 * 0.35)
            for ch in range(n_ch):
                x中心 = -總寬/2 + 間距/2 + ch * 間距
                ax.add_patch(Rectangle((x中心 - 線寬/2, 下緣), 線寬, 厚度,
                                      facecolor=顏色, edgecolor=邊緣色, linewidth=1.5, zorder=5))
                if n_ch <= 12:
                    ax.text(x中心, 下緣 + 厚度/2, str(ch+1), 
                           ha='center', va='center', fontsize=8, color='#333', fontweight='bold')
        else:
            # 一般層
            ax.add_patch(Rectangle((-總寬/2 - 2, 下緣), 總寬 + 4, 厚度,
                                  facecolor=顏色, edgecolor=邊緣色, linewidth=1.2, alpha=0.95, zorder=3))

            # 接地層紋理
            if '接地' in 層['名稱']:
                for j in range(int((總寬 + 4) / 0.3)):
                    x0 = -總寬/2 - 2 + j * 0.3
                    ax.plot([x0, x0 + 厚度*3], [下緣, 上緣],
                           color='#5A6B7D', linewidth=0.25, alpha=0.35)

        # 層標註 (左側)
        顯示名稱 = 短名稱[i] if 厚度 < 0.02 else 完整名稱[i]
        字型 = 10 if 厚度 < 0.02 else 12
        ax.text(-總寬/2 - 1.8, 位置['中心mm'], 顯示名稱,
               ha='right', va='center', fontsize=字型, color='white', fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.2', facecolor='#0D1117', 
                        edgecolor=顏色, linewidth=1.5, alpha=0.95))

        # 厚度標註 (右側)
        ax.annotate('', xy=(總寬/2 + 2, 下緣), xytext=(總寬/2 + 2, 上緣),
                   arrowprops=dict(arrowstyle='<->', color='#58A6FF', lw=1.2))
        ax.text(總寬/2 + 3.5, 位置['中心mm'], f'{位置["厚度um"]}um',
               ha='left', va='center', fontsize=9, color='#58A6FF', fontweight='bold')

        # 層間分隔線
        if i < len(層定義) - 1:
            ax.axhline(y=上緣, xmin=0.05, xmax=0.95, color='white',
                      linewidth=0.4, linestyle=':', alpha=0.25)

    # Pitch 標註
    if n_ch >= 2:
        x1 = -總寬/2 + 間距/2
        x2 = -總寬/2 + 間距/2 + 間距
        y_pitch = -0.1
        ax.annotate('', xy=(x1, y_pitch), xytext=(x2, y_pitch),
                   arrowprops=dict(arrowstyle='<->', color='#F85149', lw=2))
        ax.text((x1 + x2) / 2, y_pitch - 0.05, f'Pitch = {間距} mm',
               ha='center', va='top', fontsize=10, color='#F85149', fontweight='bold')

    # 總寬度標註
    y_width = -0.25
    ax.annotate('', xy=(-總寬/2, y_width), xytext=(總寬/2, y_width),
               arrowprops=dict(arrowstyle='<->', color='#F85149', lw=1.8))
    ax.text(0, y_width - 0.05, f'W={總寬:.1f}mm ({n_ch}ch x {間距}mm)',
           ha='center', va='top', fontsize=10, color='#F85149', fontweight='bold')

    # 訊號中心線
    ax.axhline(y=0, color='#FF6B6B', linewidth=1.2, linestyle='-.', alpha=0.5)
    ax.text(總寬/2 + 2, 0.01, 'Signal Center (Y=0)',
           ha='left', va='bottom', fontsize=9, color='#FF6B6B', style='italic')

    # 軸設定
    最小y = min(p['下緣mm'] for p in 層位置) - 0.04
    最大y = max(p['上緣mm'] for p in 層位置) + 0.04
    ax.set_xlim(-總寬/2 - 3, 總寬/2 + 6)
    ax.set_ylim(最小y - 0.02, 最大y + 0.02)
    ax.set_aspect('auto')
    ax.set_xlabel('寬度(mm)', color='white', fontsize=11)
    ax.set_ylabel('厚度(mm)', color='white', fontsize=11)
    ax.tick_params(colors='white', labelsize=9)

    # Y軸刻度（各層中心）
    y_ticks = [p['中心mm'] for p in 層位置]
    y_labels = [f'{p["中心mm"]*1000:.0f}um' for p in 層位置]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels, color='white', fontsize=9)

    plt.tight_layout()
    return fig
