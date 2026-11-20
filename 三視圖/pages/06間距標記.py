from streamlit import caption, header, info, markdown, pyplot, set_page_config, sidebar, slider, subheader, title, toggle
from matplotlib.pyplot import subplots, tight_layout
from matplotlib.patches import Rectangle, Circle
# ============================================================
# 前視圖 - Pitch 標記優化
# ============================================================
from 傳輸線Util import StriplineGeometry
from 標註偵測 import LabelPlacementDetector

def 前視間距(geo: StriplineGeometry, pitch: float, via_enabled: bool, via_diameter: float, via_density: float, n_channels: int):
    """智慧型前視圖 - 優化 Pitch 標記"""
    
    w, h, t, s = geo.w, geo.h, geo.t / 1000, pitch
    total_w = s * n_channels
    total_h = 2 * h + 3 * t
    margin = 0.3
    font_size = _get_font_size(n_channels)
    
    y0, y1, y2, y3, y4 = 0, t, t + h, t + h + t, t + h + t + h
    t_um = t * 1000
    h_um = h * 1000
    
    # 顏色
    c_gnd = '#D4A017'
    c_gnd_edge = '#8B6914'
    c_poly = '#F5E6C8'
    c_poly_edge = '#D4A574'
    c_signal = '#2ECC71'
    c_via = '#A0522D'
    c_text = '#2C3E50'
    c_pitch = '#E74C3C'  # Pitch 使用紅色系
    
    # 創建標註位置偵測器
    detector = LabelPlacementDetector(total_w, total_h, n_channels)
    
    # 記錄傳輸線結構佔用區域
    structure_regions = [
        (-margin/2, y0, total_w + margin, t),  # Bottom GND
        (-margin/2, y1, total_w + margin, h),  # 下層介電
        (-margin/2, y2, total_w + margin, t),  # Signal
        (-margin/2, y3, total_w + margin, h),  # 上層介電
        (-margin/2, y4, total_w + margin, t),  # Top GND
    ]
    for region in structure_regions:
        detector.add_structure_region(*region)
    
    # 尋找 Layer 標註位置
    layer_pos = detector.find_best_label_position(2.8, 1.0, 'right' if n_channels <= 4 else 'bottom')
    # 尋找 Pitch 標註位置 (優先放在底部)
    pitch_pos = detector.find_best_label_position(2.0, 0.5, 'bottom')
    
    fig, ax = subplots(figsize=(10, 6))
    ax.set_title(
        f'前視圖 Front View (X-Z)  {n_channels}ch  w={w*1000:.0f}μm  h={h_um:.0f}μm  t={t_um:.0f}μm',
        fontsize=11, fontweight='bold')
    ax.set_xlabel('Width (mm)', fontsize=9)
    ax.set_ylabel('Height (mm)', fontsize=9)
    ax.set_xlim(-margin, total_w + margin + 2.5)
    ax.set_ylim(-2.8, total_h + 0.2)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.08, linestyle='--')
    
    # ===== 繪製傳輸線結構 =====
    # 1. Bottom GND
    ax.add_patch(Rectangle((-margin/2, y0), total_w + margin, t,
                           facecolor=c_gnd, edgecolor=c_gnd_edge, lw=1.5))
    ax.text(total_w/2, y0 + t/2, 'Bottom GND', ha='center', va='center',
            fontsize=font_size, color='white', fontweight='bold')
    
    # 2. 下層介電
    ax.add_patch(Rectangle((-margin/2, y1), total_w + margin, h,
                           facecolor=c_poly, edgecolor=c_poly_edge, lw=1.5, alpha=0.85))
    
    # 3. Signal Layer
    signal_w = _get_signal_width(w, s, n_channels)
    for i in range(n_channels):
        xc = s * (i + 0.5)
        # 信號線
        ax.add_patch(Rectangle((xc - signal_w/2, y2), signal_w, t,
                               facecolor=c_signal, edgecolor='#1A7A3A', lw=1.5))
        
        # 信號線標註
        if n_channels <= 8 or i % 2 == 0:
            label = f'S{i+1}'
            ax.text(xc, y2 + t/2, label, ha='center', va='center',
                    fontsize=font_size-1, color='white', fontweight='bold')
        
        # GND 線
        if i < n_channels - 1:
            gx = xc + s/2
            gw = signal_w * 0.25
            ax.add_patch(Rectangle((gx - gw/2, y2), gw, t,
                                   facecolor='#F39C12', edgecolor=c_gnd_edge, lw=1))
            if n_channels <= 6:
                ax.text(gx, y2 + t/2, 'G', ha='center', va='center',
                        fontsize=font_size-2, color='white', fontweight='bold')
    
    # 4. 上層介電
    ax.add_patch(Rectangle((-margin/2, y3), total_w + margin, h,
                           facecolor=c_poly, edgecolor=c_poly_edge, lw=1.5, alpha=0.85))
    
    # 5. Top GND
    ax.add_patch(Rectangle((-margin/2, y4), total_w + margin, t,
                           facecolor=c_gnd, edgecolor=c_gnd_edge, lw=1.5))
    ax.text(total_w/2, y4 + t/2, 'Top GND', ha='center', va='center',
            fontsize=font_size, color='white', fontweight='bold')
    
    # Via
    if via_enabled:
        vr = via_diameter / 2000
        step = max(1.0 / via_density, 1.0)
        for i in range(int(total_w / step) + 1):
            xv = i * step
            if xv > total_w:
                break
            ax.add_patch(Circle((xv, y0 + t/2), vr, facecolor=c_via, edgecolor='black', lw=0.8))
            ax.add_patch(Circle((xv, y4 + t/2), vr, facecolor=c_via, edgecolor='black', lw=0.8))
            ax.plot([xv, xv], [y0 + t/2 + vr, y4 + t/2 - vr], color=c_via, lw=1.5, alpha=0.6)
    
    # ===== Layer 標註 =====
    label_x, label_y = layer_pos
    layer_txt = (
        f'Top GND  t={t_um:.0f}μm\n'
        f'Polyimide  h={h_um:.0f}μm  εr=3.4\n'
        f'Signal  G-S-G\n'
        f'Polyimide  h={h_um:.0f}μm  εr=3.4\n'
        f'Bottom GND  t={t_um:.0f}μm'
    )
    
    ax.text(label_x, label_y, layer_txt, ha='center', va='center',
            fontsize=font_size, color='#8E44AD', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#F5EEF8',
                      edgecolor='#8E44AD', alpha=0.95, linewidth=1.5),
            linespacing=1.5)
    
    # ===== Pitch 標記 - 優化版本 =====
    pitch_x, pitch_y = pitch_pos
    
    # 確保 Pitch 標註在底部且不與 Layer 標註重疊
    if pitch_y > -0.5:  # 如果標註位置不夠低，強制放到底部
        pitch_y = -0.8
    
    # 檢查是否與 Layer 標註重疊
    if abs(pitch_x - label_x) < 1.5 and abs(pitch_y - label_y) < 0.8:
        pitch_x = total_w / 2  # 移到中央
        pitch_y = -0.8
    
    # 確保 Pitch 標註在安全範圍內
    if pitch_y < -2.5:
        pitch_y = -0.8
    
    # 繪製 Pitch 箭頭標記 (從第一個通道到第二個通道)
    # 使用標準的雙箭頭標記
    arrow_y = pitch_y
    arrow_start = s * 0.5  # 第一個通道中心
    arrow_end = s * 1.5    # 第二個通道中心
    
    # 繪製雙箭頭
    ax.annotate('', xy=(arrow_start, arrow_y), xytext=(arrow_end, arrow_y),
                arrowprops=dict(
                    arrowstyle='<->', 
                    color=c_pitch, 
                    lw=2,
                    shrinkA=2,
                    shrinkB=2,
                    connectionstyle="arc3,rad=0.0"
                ))
    
    # 標記箭頭端點
    ax.plot(arrow_start, arrow_y, 'o', color=c_pitch, markersize=4)
    ax.plot(arrow_end, arrow_y, 'o', color=c_pitch, markersize=4)
    
    # 繪製垂直虛線輔助線 (從 GND 層到信號層)
    ax.plot([arrow_start, arrow_start], [y0 + t, y2], 
            color=c_pitch, linestyle=':', linewidth=1, alpha=0.3)
    ax.plot([arrow_end, arrow_end], [y0 + t, y2], 
            color=c_pitch, linestyle=':', linewidth=1, alpha=0.3)
    
    # Pitch 數值標註 (放在箭頭上方)
    pitch_label_y = arrow_y + 0.15
    # 檢查標註位置是否與結構重疊
    if pitch_label_y > 0 and pitch_label_y < y1:
        pitch_label_y = y0 - 0.3  # 移到 GND 層下方
    
    ax.text((arrow_start + arrow_end) / 2, pitch_label_y, 
            f'pitch = {s:.1f} mm', 
            ha='center', va='bottom' if pitch_label_y > 0 else 'top',
            fontsize=font_size + 1, 
            color=c_pitch, 
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.15', 
                     facecolor='white', 
                     edgecolor=c_pitch, 
                     alpha=0.9,
                     linewidth=1.5))
    
    # 如果有多個通道，顯示多個 Pitch 標記的示意
    if n_channels > 3:
        # 在底部顯示 "..." 表示連續
        ax.text(total_w/2, arrow_y - 0.2, 
                '... 連續間距 ...', 
                ha='center', va='top',
                fontsize=font_size-1, 
                color='#7F8C8D',
                style='italic',
                alpha=0.6)
    
    # 額外標示：顯示總寬度對應的通道數
    ax.text(total_w/2, arrow_y - 0.5,
            f'總寬度 = {total_w:.1f} mm ({n_channels} channels)',
            ha='center', va='top',
            fontsize=font_size-1,
            color='#7F8C8D',
            bbox=dict(boxstyle='round,pad=0.1', 
                     facecolor='#F8F9FA', 
                     edgecolor='none',
                     alpha=0.7))
    
    # 個別通道位置標記 (簡化)
    if n_channels <= 8:
        for i in range(min(n_channels, 5)):  # 最多顯示5個
            xc = s * (i + 0.5)
            # 在底部畫小圓點標記通道位置
            ax.plot(xc, arrow_y - 0.05, 'o', color='#3498DB', markersize=3, alpha=0.5)
            if i < n_channels - 1 and i < 4:
                # 在通道間畫小箭頭
                mid_x = s * (i + 1)
                ax.annotate('', xy=(mid_x - 0.1, arrow_y - 0.05), 
                           xytext=(mid_x + 0.1, arrow_y - 0.05),
                           arrowprops=dict(arrowstyle='->', 
                                         color='#3498DB', 
                                         lw=0.8,
                                         alpha=0.3))
    
    tight_layout()
    return fig


def _get_signal_width(w: float, s: float, n_channels: int) -> float:
    """計算信號線寬度"""
    max_width = s * 0.35
    if n_channels > 8:
        return min(w, max_width * 0.8)
    return min(w, max_width)


def _get_font_size(n_channels: int) -> float:
    """根據通道數獲取字體大小"""
    if n_channels <= 4:
        return 9
    elif n_channels <= 8:
        return 8
    else:
        return 7


# ============================================================
# 主程式 - 使用智慧型前視圖
# ============================================================

def main():
    set_page_config(
        page_title="智慧型三視圖系統",
        page_icon="📐",
        layout="wide"
    )

    title("📐 智慧型三視圖系統")
    markdown("*主動偵測空白區域 · 優化 Pitch 標記*")
    markdown("---")

    with sidebar:
        header("⚙️ 參數設定")
        
        sig_width = slider("信號線寬度 w (μm)", 50, 500, 200, step=10)
        sig_thickness = slider("信號線厚度 t (μm)", 1, 20, 5, step=1)
        dielectric_thickness = slider("介電層厚度 h (μm)", 10, 200, 50, step=5)
        pitch = slider("通道間距 pitch (mm)", 0.5, 5.0, 1.5, step=0.1)
        length = slider("傳輸線長度 L (mm)", 10, 200, 50, step=5)
        n_channels = slider("通道數", 2, 16, 8, step=2)

        markdown("---")
        header("🔩 Via 設定")
        via_enabled = toggle("啟用 Via", value=True)
        via_diameter = slider("Via 直徑 (μm)", 50, 500, 200, step=10,
                                  disabled=not via_enabled)
        via_density = slider("Via 密度 (個/mm)", 0.5, 5.0, 2.0, step=0.1,
                                 disabled=not via_enabled)

        markdown("---")
        total_w = pitch * n_channels
        total_h = 2 * dielectric_thickness + 3 * sig_thickness
        info(f"""
        **即時資訊**
        - 總寬度：{total_w:.1f} mm
        - 總厚度：{total_h:.0f} μm
        - 通道數：{n_channels} ch
        - Pitch：{pitch:.1f} mm
        """)

    geo = StriplineGeometry(
        w=sig_width / 1000,
        t=sig_thickness,
        h=dielectric_thickness / 1000,
        s=pitch,
        L=length,
        n_channels=n_channels
    )

    # 顯示前視圖
    subheader("🔲 前視圖 Front View (X-Z)")
    fig = 前視間距(geo, pitch, via_enabled, via_diameter, via_density, n_channels)
    pyplot(fig)
    
    markdown("---")
    caption("""
    **Pitch 標記說明：**
    - 紅色雙箭頭標示通道間距 (pitch)
    - 顯示 pitch 數值 (單位: mm)
    - 自動放置在視圖底部空白區域
    - 避免與傳輸線結構重疊
    """)

    markdown("---")
    caption("智慧型前視圖系統 | 優化 Pitch 標記")


if __name__ == "__main__":
    main()
