# 柔性線函式庫/繪圖/前視.py
"""繪製前視圖 - GSG 7層橫截面 (含重疊偵測)"""

import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from numpy import linspace

from 繪圖.共用 import 主題顏色, 設定中文字型, 建立圖形, 計算字型大小

def 計算適合字型(文字內容, 區域寬度mm, 字型縮放=1.0):
    """
    根據文字內容和區域寬度計算適合的字型大小，避免文字重疊

    參數:
        文字內容: 要顯示的文字
        區域寬度mm: 可用區域寬度 (mm)
        字型縮放: 字型縮放比例

    回傳:
        適合的字型大小 (pt)
    """
    # 估算每個字元的寬度 (mm/pt)
    字元寬度係數 = 0.6
    估算文字寬度 = len(文字內容) * 字元寬度係數

    # 根據可用寬度計算最大字型
    最大字型 = (區域寬度mm / 估算文字寬度) * 10 * 字型縮放 if 區域寬度mm > 0 else 8

    # 限制字型範圍
    最小字型 = 6 * 字型縮放
    最大字型 = 14 * 字型縮放

    return max(最小字型, min(最大字型, 最大字型))

def 偵測標籤重疊(層位置列表, 層厚度列表, 字型大小列表, 層定義=None):
    """
    偵測標籤是否重疊，回傳每個層應放置的位置 ('左' 或 '右')
    """
    標籤側邊 = ['左'] * len(層位置列表)
    標籤高度 = [字型 * 0.035 for 字型 in 字型大小列表]

    for i in range(len(層位置列表)):
        if i == 0:
            上一層間距 = float('inf')
        else:
            上一層間距 = 層位置列表[i] - 層位置列表[i-1]

        if i == len(層位置列表) - 1:
            下一層間距 = float('inf')
        else:
            下一層間距 = 層位置列表[i+1] - 層位置列表[i]

        目前標籤高 = 標籤高度[i]
        上一標籤高 = 標籤高度[i-1] if i > 0 else 0
        下一標籤高 = 標籤高度[i+1] if i < len(層位置列表) - 1 else 0

        與上一層重疊 = False
        if i > 0:
            可用空間 = 上一層間距
            需要空間 = (目前標籤高 + 上一標籤高) * 1.2
            if 可用空間 < 需要空間:
                與上一層重疊 = True

        與下一層重疊 = False
        if i < len(層位置列表) - 1:
            可用空間 = 下一層間距
            需要空間 = (目前標籤高 + 下一標籤高) * 1.2
            if 可用空間 < 需要空間:
                與下一層重疊 = True

        if 與上一層重疊 or 與下一層重疊:
            層名稱 = 層定義[i]['名稱']
            if '保護' in 層名稱 or '接地' in 層名稱:
                標籤側邊[i] = '右'

        if i == 0 and '保護' in 層定義[i]['名稱']:
            if 標籤側邊[-1] == '右':
                標籤側邊[i] = '右'

        if i > 0 and 標籤側邊[i] == '右' and 標籤側邊[i-1] == '右':
            if 層厚度列表[i] < 層厚度列表[i-1]:
                標籤側邊[i] = '左'
            else:
                標籤側邊[i-1] = '左'

    return 標籤側邊


def 繪製前視(佈局, 字型縮放=1.0, 層定義=None):
    """繪製前視圖"""
    設定中文字型()

    n_ch = 佈局.通道數
    總寬 = 佈局.線總寬
    層位置 = 佈局.層位置列表
    層中心 = 佈局.層中心列表
    層厚度 = 佈局.層厚度列表
    訊號寬 = 佈局.訊號寬度mm
    間距 = 佈局.訊號間距
    左側間距 = 佈局.左側間距
    右側間距 = 佈局.右側間距

    # 計算字型大小
    字型大小列表 = []
    for i, 厚度 in enumerate(層厚度):
        if 厚度 < 0.01:
            字型 = 8
        elif 厚度 < 0.02:
            字型 = 9
        elif 厚度 < 0.05:
            字型 = 10
        else:
            字型 = 11
        字型 = max(6, min(18, 字型 * 字型縮放))
        字型大小列表.append(字型)

    # 偵測重疊並決定標籤側邊
    標籤側邊 = 偵測標籤重疊(層中心, 層厚度, 字型大小列表, 層定義=層定義)

    # 計算圖形尺寸
    圖寬 = max(12, 6 + n_ch * 0.4 + 6)
    圖高 = 6.5
    fig, ax = 建立圖形(圖寬, 圖高)

    # 標題
    fig.suptitle(f'U-leam UF1 前視 | {n_ch} 通道數 | GSG 7層疊構',
                 fontsize=14 * 字型縮放, fontweight='bold', color='white', y=0.96)

    # 層名稱（完整與縮短）
    完整名稱 = ['保護層下', '接地層下', '介電層下', f'訊號線(x{n_ch})', '介電層上', '接地層上', '保護層上']
    短名稱 = ['保護下', 'GND下', '介電下', '訊號', '介電上', 'GND上', '保護上']

    # 繪製各層
    for i, (層, 位置) in enumerate(zip(層定義, 層位置)):
        下緣 = 位置['下緣mm']
        上緣 = 位置['上緣mm']
        厚度 = 位置['厚度mm']
        顏色 = 層['顏色']
        邊緣色 = 層['邊緣']
        是訊號 = 層['是訊號層']
        中心 = 位置['中心mm']
        側邊 = 標籤側邊[i]
        字型 = 字型大小列表[i]

        if 是訊號:
            # 訊號線
            線寬 = min(訊號寬, 間距 * 0.35)
            for ch in range(n_ch):
                x中心 = -總寬/2 + 間距/2 + ch * 間距
                ax.add_patch(Rectangle((x中心 - 線寬/2, 下緣), 線寬, 厚度,
                                      facecolor=顏色, edgecolor=邊緣色, linewidth=1.5, zorder=5))
                if n_ch <= 12:
                    ax.text(x中心, 下緣 + 厚度/2, str(ch+1),
                           ha='center', va='center', fontsize=8 * 字型縮放,
                           color='#333', fontweight='bold')
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

            # 保護層紋理
            if '保護' in 層['名稱']:
                for dx in linspace(-總寬/2 - 1.5, 總寬/2 + 1.5, int((總寬+3)/0.8)):
                    for dy in linspace(下緣 + 厚度*0.2, 上緣 - 厚度*0.2, max(1, int(厚度/0.05))):
                        ax.plot(dx, dy, '.', color='#A0522D', markersize=1.2, alpha=0.25)

        # 層標註
        顯示名稱 = 短名稱[i] if 厚度 < 0.02 else 完整名稱[i]

        if 側邊 == '左':
            x位置 = -總寬/2 - 2.0
            ha = 'right'
            ax.plot([-總寬/2 - 1.2, x位置 + 0.5], [中心, 中心],
                   color=顏色, linewidth=0.5, linestyle=':', alpha=0.3)
        else:
            x位置 = 總寬/2 + 2.5
            ha = 'left'
            ax.plot([總寬/2 + 1.2, x位置 - 0.5], [中心, 中心],
                   color=顏色, linewidth=0.5, linestyle=':', alpha=0.3)

        ax.text(x位置, 中心, 顯示名稱,
               ha=ha, va='center', fontsize=字型, color='white', fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.2', facecolor='#0D1117',
                        edgecolor=顏色, linewidth=1.5, alpha=0.95))

        # 厚度標註
        if 側邊 == '左':
            厚度x = 總寬/2 + 2.0
            ax.annotate('', xy=(厚度x, 下緣), xytext=(厚度x, 上緣),
                       arrowprops=dict(arrowstyle='<->', color='#58A6FF', lw=1.2))
            ax.text(厚度x + 1.5, 中心, f'{位置["厚度um"]}um',
                   ha='left', va='center', fontsize=9 * 字型縮放,
                   color='#58A6FF', fontweight='bold')
        else:
            厚度x = 總寬/2 + 5.5
            ax.annotate('', xy=(厚度x, 下緣), xytext=(厚度x, 上緣),
                       arrowprops=dict(arrowstyle='<->', color='#58A6FF', lw=1.0))
            ax.text(厚度x + 1.2, 中心, f'{位置["厚度um"]}um',
                   ha='left', va='center', fontsize=8 * 字型縮放,
                   color='#58A6FF', fontweight='bold')

        # 層間分隔線
        if i < len(層定義) - 1:
            ax.axhline(y=上緣, xmin=0.05, xmax=0.95, color='white',
                      linewidth=0.4, linestyle=':', alpha=0.25)

    # ===== 計算訊號線實際繪製寬度 (與繪製迴圈保持一致) =====
    實際訊號線寬 = min(訊號寬, 間距 * 0.35)

    # ===== 三行標註 =====
    標註y_文字_上方 = -0.28    # 第一行：Pitch 文字（箭頭上方）
    標註y_箭頭 = -0.35         # 第二行：Pitch 箭頭
    標註y_文字_下方 = -0.42    # 第三行：左右側間距文字（箭頭下方）

    # ===== 計算各區域邊界（單位：mm） =====
    x_左緣 = -總寬/2
    x_右緣 = 總寬/2
    x_第一訊號左緣 = -總寬/2 + 間距/2 - 實際訊號線寬/2
    x_第一訊號中心 = -總寬/2 + 間距/2
    x_第二訊號中心 = -總寬/2 + 間距/2 + 間距
    x_最後訊號右緣 = -總寬/2 + 間距/2 + (n_ch - 1) * 間距 + 實際訊號線寬/2

    # 箭頭縮放參數
    箭頭縮放 = 字型縮放

    # ===== 左側間距標註 (綠色) - 僅第三行文字，無箭頭 =====
    if n_ch >= 1 and 左側間距 > 0.001:
        文字內容 = f'左側間距 {左側間距*1000:.0f}um'
        區域寬度 = x_第一訊號左緣 - x_左緣
        字型大小 = 計算適合字型(文字內容, 區域寬度, 字型縮放)

        # 第三行：文字（箭頭下方）
        ax.text((x_左緣 + x_第一訊號左緣) / 2, 標註y_文字_下方,
               文字內容, ha='center', va='top', fontsize=字型大小, 
               color='#3FB950', fontweight='bold', zorder=100)

    # ===== Pitch 標註 (藍色) - 第一行文字 + 第二行箭頭 =====
    if n_ch >= 2:
        箭頭距離 = x_第二訊號中心 - x_第一訊號中心
        if 箭頭距離 > 0.01:
            文字內容 = f'Pitch = {間距}mm'
            字型大小 = 計算適合字型(文字內容, 箭頭距離, 字型縮放)

            # 第一行：Pitch 文字（箭頭上方）
            ax.text((x_第一訊號中心 + x_第二訊號中心) / 2, 標註y_文字_上方,
                   文字內容, ha='center', va='bottom', fontsize=字型大小, 
                   color='#58A6FF', fontweight='bold', zorder=100)

            # 第二行：箭頭（從第一條訊號線中心 → 第二條訊號線中心）
            ax.annotate('', 
                       xy=(x_第二訊號中心, 標註y_箭頭),
                       xytext=(x_第一訊號中心, 標註y_箭頭),
                       arrowprops=dict(
                           arrowstyle='<->',
                           color='#58A6FF',
                           lw=4.0 * 箭頭縮放,
                           mutation_scale=35 * 箭頭縮放,
                           shrinkA=0,
                           shrinkB=0,
                       ),
                       zorder=100,
                       annotation_clip=False)

            # 垂直輔助線
            ax.plot([x_第一訊號中心, x_第一訊號中心], [0.001, 標註y_箭頭 + 0.005],
                   color='#58A6FF', linestyle=':', linewidth=1.0 * 字型縮放, alpha=0.4, zorder=50)
            ax.plot([x_第二訊號中心, x_第二訊號中心], [0.001, 標註y_箭頭 + 0.005],
                   color='#58A6FF', linestyle=':', linewidth=1.0 * 字型縮放, alpha=0.4, zorder=50)

    # ===== 右側間距標註 (紅色) - 僅第三行文字，無箭頭 =====
    if n_ch >= 1 and 右側間距 > 0.001:
        文字內容 = f'右側間距 {右側間距*1000:.0f}um'
        區域寬度 = x_右緣 - x_最後訊號右緣
        字型大小 = 計算適合字型(文字內容, 區域寬度, 字型縮放)

        # 第三行：文字（箭頭下方）
        ax.text((x_最後訊號右緣 + x_右緣) / 2, 標註y_文字_下方,
               文字內容, ha='center', va='top', fontsize=字型大小, 
               color='#FF6B6B', fontweight='bold', zorder=100)
    y_width = -0.48  # 從 -0.40 改為 -0.48，更靠近底部
    # ax.annotate('', xy=(-總寬/2, y_width), xytext=(總寬/2, y_width), arrowprops=dict(arrowstyle='<->', color='#F85149', lw=1.8 * 字型縮放))
    ax.text(0, y_width - 0.05, f'W={總寬:.1f}mm ({n_ch}ch x {間距}mm)',
           ha='center', va='top', fontsize=10 * 字型縮放,
           color='#F85149', fontweight='bold')
    # ===== 訊號中心線 =====
    ax.axhline(y=0, color='#FF6B6B', linewidth=1.2 * 字型縮放, linestyle='-.', alpha=0.5)
    ax.text(總寬/2 + 2, 0.01, 'Signal Center (Y=0)',
           ha='left', va='bottom', fontsize=9 * 字型縮放,
           color='#FF6B6B', style='italic')

    # ===== 軸設定 =====
    最小y = min(p['下緣mm'] for p in 層位置) - 0.06
    最大y = max(p['上緣mm'] for p in 層位置) + 0.04

    # 為底部標註預留空間（箭頭在 y=-0.35，文字在 y=-0.42）
    if 最小y > -0.50:
        最小y = -0.50

    有右側標籤 = '右' in 標籤側邊
    右邊界 = 總寬/2 + 8 if 有右側標籤 else 總寬/2 + 5.5

    ax.set_xlim(-總寬/2 - 3.5, 右邊界)
    ax.set_ylim(最小y - 0.02, 最大y + 0.02)
    ax.set_aspect('auto')
    ax.set_xlabel('寬度(mm)', color='white', fontsize=11 * 字型縮放)
    ax.set_ylabel('厚度(mm)', color='white', fontsize=11 * 字型縮放)
    ax.tick_params(colors='white', labelsize=9 * 字型縮放)

    # Y軸刻度
    y_ticks = [p['中心mm'] for p in 層位置]
    y_labels = [f'{p["中心mm"]*1000:.0f}um' for p in 層位置]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels, color='white', fontsize=9 * 字型縮放)

    plt.tight_layout()
    return fig


def 匯出前視圖png(佈局, 檔案名稱=None, 字型縮放=1.0):
    """匯出前視圖為 PNG 檔案"""
    fig = 繪製前視(佈局, 字型縮放=字型縮放)

    if 檔案名稱 is None:
        檔案名稱 = f"前視圖_{佈局.通道數}通道.png"

    fig.savefig(檔案名稱, dpi=200, bbox_inches='tight', facecolor='#0D1117')
    plt.close(fig)
    print(f"✅ 已匯出: {檔案名稱}")
    return 檔案名稱


def 顯示前視圖(佈局, 字型縮放=1.0):
    """顯示前視圖 (用於互動環境)"""
    fig = 繪製前視(佈局, 字型縮放=字型縮放)
    plt.show()
    return fig
