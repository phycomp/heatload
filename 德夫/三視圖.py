# ============================================================
# 功能 1: 三視圖繪製 (前視、側視、上視)
# ============================================================

def draw_front_view(geo: StriplineGeometry, pitch: float, via_enabled: bool, 
                    via_diameter: float, via_density: float, n_channels: int):
    """
    繪製前視圖 (Cross-Section View) - YZ平面
    """
    fig, ax = subplots(figsize=(14, 8))
    
    w = geo.w  # mm
    h = geo.h  # mm
    t = geo.t / 1000  # μm -> mm
    s = pitch
    n_draw = min(n_channels, 6)
    total_width = s * (n_draw + 0.5)
    margin = s * 0.3
    
    colors = {
        'polyimide': '#F5E6C8',
        'polyimide_edge': '#D4A574',
        'conductor': '#DAA520',
        'conductor_edge': '#8B6914',
        'gnd': '#C9A227',
        'via': '#A0522D',
        'text': '#2C3E50',
        'dimension': '#E74C3C',
        'arrow': '#2980B9'
    }
    
    y_bot_gnd = 0
    y_bot_die = t
    y_signal = t + h
    y_top_die = t + h + t
    y_top_gnd = t + h + t + h
    total_height = y_top_gnd + t
    
    ax.set_xlim(-margin, total_width + margin)
    ax.set_ylim(-margin * 0.5, total_height + margin * 1.5)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # 下接地層
    gnd_bottom = Rectangle((0, y_bot_gnd), total_width, t,
                          facecolor=colors['gnd'], edgecolor=colors['conductor_edge'], linewidth=2)
    ax.add_patch(gnd_bottom)
    ax.text(total_width/2, y_bot_gnd + t/2, 'Bottom GND',
            ha='center', va='center', fontsize=10, color='white', fontweight='bold')
    
    # 下介電層
    die_bottom = Rectangle((0, y_bot_die), total_width, h,
                          facecolor=colors['polyimide'], edgecolor=colors['polyimide_edge'], 
                          linewidth=2, alpha=0.85)
    ax.add_patch(die_bottom)
    ax.text(-margin + 0.1, y_bot_die + h/2, 'Polyimide\nεr=3.4',
            ha='left', va='center', fontsize=9, color=colors['text'])
    
    # 信號層 + GND 分隔
    for i in range(n_draw):
        x_center = s * (i + 0.5)
        sig = Rectangle((x_center - w/2, y_signal - t/2), w, t,
                        facecolor=colors['conductor'], edgecolor=colors['conductor_edge'], linewidth=2)
        ax.add_patch(sig)
        ax.text(x_center, y_signal, f'S{i+1}', ha='center', va='center',
                fontsize=9, color='white', fontweight='bold')
        
        if i < n_draw - 1:
            gnd_x = x_center + s/2
            gnd_w = w * 0.3
            gnd_sep = Rectangle((gnd_x - gnd_w/2, y_signal - t/2), gnd_w, t,
                               facecolor=colors['gnd'], edgecolor=colors['conductor_edge'], linewidth=1.5)
            ax.add_patch(gnd_sep)
            ax.text(gnd_x, y_signal, 'G', ha='center', va='center',
                    fontsize=7, color='white', fontweight='bold')
    
    # 上介電層
    die_top = Rectangle((0, y_top_die), total_width, h,
                        facecolor=colors['polyimide'], edgecolor=colors['polyimide_edge'],
                        linewidth=2, alpha=0.85)
    ax.add_patch(die_top)
    ax.text(-margin + 0.1, y_top_die + h/2, 'Polyimide\nεr=3.4',
            ha='left', va='center', fontsize=9, color=colors['text'])
    
    # 上接地層
    gnd_top = Rectangle((0, y_top_gnd), total_width, t,
                        facecolor=colors['gnd'], edgecolor=colors['conductor_edge'], linewidth=2)
    ax.add_patch(gnd_top)
    ax.text(total_width/2, y_top_gnd + t/2, 'Top GND',
            ha='center', va='center', fontsize=10, color='white', fontweight='bold')
    
    # Via Stitching
    if via_enabled:
        via_spacing = 1.0 / via_density
        n_vias = int(total_width / via_spacing) + 1
        via_r = via_diameter / 2000
        
        for i in range(n_vias):
            x_via = i * via_spacing
            if x_via > total_width:
                break
            ax.plot([x_via, x_via], [y_bot_gnd + t/2, y_top_gnd + t/2],
                    color=colors['via'], linewidth=2.5, alpha=0.7, linestyle='-')
            for y in [y_bot_gnd + t/2, y_top_gnd + t/2]:
                v = Circle((x_via, y), via_r,
                          facecolor=colors['via'], edgecolor='black', linewidth=1)
                ax.add_patch(v)
    
    # 尺寸標註
    ax.annotate('', xy=(-margin*0.4, 0), xytext=(-margin*0.4, total_height),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=2))
    ax.text(-margin*0.6, total_height/2, f'Total\n{total_height*1000:.0f}μm',
            ha='right', va='center', fontsize=10, color=colors['dimension'], fontweight='bold')
    
    ax.annotate('', xy=(-margin*0.15, y_bot_die), xytext=(-margin*0.15, y_top_die - t),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text(-margin*0.35, (y_bot_die + y_top_die - t)/2, f'h\n{h*1000:.0f}μm',
            ha='right', va='center', fontsize=9, color=colors['dimension'])
    
    ax.annotate('', xy=(-margin*0.15, 0), xytext=(-margin*0.15, t),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text(-margin*0.35, t/2, f't\n{t*1000:.0f}μm',
            ha='right', va='center', fontsize=9, color=colors['dimension'])
    
    ax.annotate('', xy=(s*0.5 - w/2, -margin*0.2), xytext=(s*0.5 + w/2, -margin*0.2),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=2))
    ax.text(s*0.5, -margin*0.4, f'w={w*1000:.0f}μm',
            ha='center', va='top', fontsize=9, color=colors['dimension'])
    
    ax.annotate('', xy=(s*0.5, -margin*0.7), xytext=(s*1.5, -margin*0.7),
                arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=2))
    ax.text(s, -margin*0.9, f'pitch={s:.1f}mm',
            ha='center', va='top', fontsize=10, color=colors['arrow'], fontweight='bold')
    
    ax.set_title(f'前視圖 (Cross-Section) - {n_channels}通道 G-S-G 結構',
                 fontsize=14, fontweight='bold', pad=20)
    
    tight_layout()
    return fig


def draw_side_view(geo: StriplineGeometry, length: float):
    """繪製側視圖 (Side View) - XZ平面"""
    fig, ax = subplots(figsize=(14, 5))
    
    t = geo.t / 1000
    h = geo.h
    L = length
    
    y_bot_gnd = 0
    y_bot_die = t
    y_signal = t + h
    y_top_die = t + h + t
    y_top_gnd = t + h + t + h
    total_height = y_top_gnd + t
    
    colors = {
        'gnd': '#C9A227',
        'polyimide': '#F5E6C8',
        'polyimide_edge': '#D4A574',
        'conductor': '#DAA520',
        'conductor_edge': '#8B6914',
        'text': '#2C3E50',
        'dimension': '#E74C3C',
        'arrow': '#2980B9'
    }
    
    margin = L * 0.02
    
    # 下接地層
    gnd_bottom = Rectangle((0, y_bot_gnd), L, t,
                          facecolor=colors['gnd'], edgecolor=colors['conductor_edge'], linewidth=1.5)
    ax.add_patch(gnd_bottom)
    
    # 下介電層
    die_bottom = Rectangle((0, y_bot_die), L, h,
                          facecolor=colors['polyimide'], edgecolor=colors['polyimide_edge'],
                          linewidth=1.5, alpha=0.85)
    ax.add_patch(die_bottom)
    
    # 信號層
    signal = Rectangle((0, y_signal - t/2), L, t,
                      facecolor=colors['conductor'], edgecolor=colors['conductor_edge'], linewidth=1.5)
    ax.add_patch(signal)
    ax.text(L/2, y_signal, 'Signal Layer (連續)',
            ha='center', va='center', fontsize=10, color='white', fontweight='bold')
    
    # 上介電層
    die_top = Rectangle((0, y_top_die), L, h,
                       facecolor=colors['polyimide'], edgecolor=colors['polyimide_edge'],
                       linewidth=1.5, alpha=0.85)
    ax.add_patch(die_top)
    
    # 上接地層
    gnd_top = Rectangle((0, y_top_gnd), L, t,
                       facecolor=colors['gnd'], edgecolor=colors['conductor_edge'], linewidth=1.5)
    ax.add_patch(gnd_top)
    
    # 標註層名稱
    label_x = L + margin * 5
    ax.text(label_x, y_bot_gnd + t/2, 'Bottom GND', ha='left', va='center', fontsize=9, color=colors['text'])
    ax.text(label_x, y_bot_die + h/2, 'Polyimide', ha='left', va='center', fontsize=9, color=colors['text'])
    ax.text(label_x, y_signal, 'Signal', ha='left', va='center', fontsize=9, color=colors['text'])
    ax.text(label_x, y_top_die + h/2, 'Polyimide', ha='left', va='center', fontsize=9, color=colors['text'])
    ax.text(label_x, y_top_gnd + t/2, 'Top GND', ha='left', va='center', fontsize=9, color=colors['text'])
    
    # 長度標註
    ax.annotate('', xy=(0, -margin*2), xytext=(L, -margin*2),
                arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=2))
    ax.text(L/2, -margin*3, f'L = {L:.0f} mm', ha='center', va='top',
            fontsize=11, color=colors['arrow'], fontweight='bold')
    
    # 總厚度標註
    ax.annotate('', xy=(-margin*2, 0), xytext=(-margin*2, total_height),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=2))
    ax.text(-margin*3, total_height/2, f'Total\n{total_height*1000:.0f}μm',
            ha='right', va='center', fontsize=9, color=colors['dimension'])
    
    ax.set_xlim(-margin*5, L + margin*8)
    ax.set_ylim(-margin*4, total_height + margin*2)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f'側視圖 (Side View) - 長度 L = {L:.0f} mm', fontsize=14, fontweight='bold', pad=20)
    
    tight_layout()
    return fig


def draw_top_view(geo: StriplineGeometry, pitch: float, length: float, n_channels: int):
    """繪製上視圖 (Top View) - XY平面"""
    fig, ax = subplots(figsize=(14, 8))
    
    w = geo.w
    s = pitch
    L = length
    n_draw = min(n_channels, 8)
    total_width = s * n_draw + w * 2
    
    colors = {
        'signal': '#DAA520',
        'signal_edge': '#8B6914',
        'gnd': '#C9A227',
        'gnd_edge': '#8B6914',
        'text': '#2C3E50',
        'dimension': '#E74C3C',
        'arrow': '#2980B9'
    }
    
    margin = s * 0.3
    
    for i in range(n_draw):
        x_center = s * (i + 0.5) + w * 0.5
        
        signal = Rectangle((x_center - w/2, 0), w, L,
                          facecolor=colors['signal'], edgecolor=colors['signal_edge'], linewidth=1.5)
        ax.add_patch(signal)
        ax.text(x_center, L/2, f'S{i+1}', ha='center', va='center',
                fontsize=10, color='white', fontweight='bold', rotation=90)
        
        if i < n_draw - 1:
            gnd_x = x_center + s/2 - w*0.15
            gnd = Rectangle((gnd_x, 0), w*0.3, L,
                           facecolor=colors['gnd'], edgecolor=colors['gnd_edge'], linewidth=1.5)
            ax.add_patch(gnd)
            ax.text(gnd_x + w*0.15, L/2, 'GND', ha='center', va='center',
                    fontsize=8, color='white', fontweight='bold', rotation=90)
    
    # 標註
    for i in range(n_draw):
        x_center = s * (i + 0.5) + w * 0.5
        ax.text(x_center, -margin*0.5, f'Ch{i+1}', ha='center', va='top',
                fontsize=9, color=colors['text'])
    
    ax.annotate('', xy=(0, -margin*1.5), xytext=(total_width, -margin*1.5),
                arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=2))
    ax.text(total_width/2, -margin*2, f'總寬度 = {total_width:.1f} mm',
            ha='center', va='top', fontsize=10, color=colors['arrow'], fontweight='bold')
    
    ax.annotate('', xy=(0, -margin*3), xytext=(s + w, -margin*3),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text((s + w)/2, -margin*3.5, f'pitch = {s:.1f}mm',
            ha='center', va='top', fontsize=9, color=colors['dimension'])
    
    ax.annotate('', xy=(s*0.5 - w/2, -margin*4.5), xytext=(s*0.5 + w/2, -margin*4.5),
                arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax.text(s*0.5, -margin*5, f'w={w*1000:.0f}μm',
            ha='center', va='top', fontsize=9, color=colors['dimension'])
    
    ax.annotate('', xy=(total_width + margin, 0), xytext=(total_width + margin, L),
                arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=2))
    ax.text(total_width + margin*2, L/2, f'L = {L:.0f}mm',
            ha='left', va='center', fontsize=10, color=colors['arrow'], fontweight='bold')
    
    ax.set_xlim(-margin, total_width + margin*4)
    ax.set_ylim(-margin*6, L + margin)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f'上視圖 (Top View) - {n_channels}通道佈線', fontsize=14, fontweight='bold', pad=20)
    
    tight_layout()
    return fig


def draw_all_views(geo: StriplineGeometry, pitch: float, length: float, 
                   via_enabled: bool, via_diameter: float, via_density: float, n_channels: int):
    """
    組合三視圖為單一圖表 - 直接在各子圖中繪製，避免複製問題
    """
    fig = plt.figure(figsize=(16, 12))
    
    w = geo.w
    h = geo.h
    t = geo.t / 1000
    s = pitch
    L = length
    n_draw = min(n_channels, 6)
    total_width = s * (n_draw + 0.5)
    margin = s * 0.3
    
    colors = {
        'polyimide': '#F5E6C8',
        'polyimide_edge': '#D4A574',
        'conductor': '#DAA520',
        'conductor_edge': '#8B6914',
        'gnd': '#C9A227',
        'via': '#A0522D',
        'text': '#2C3E50',
        'dimension': '#E74C3C',
        'arrow': '#2980B9',
        'signal_edge': '#8B6914'
    }
    
    # ===== 前視圖 (左上) =====
    ax1 = fig.add_subplot(2, 2, 1)
    
    y_bot_gnd = 0
    y_bot_die = t
    y_signal = t + h
    y_top_die = t + h + t
    y_top_gnd = t + h + t + h
    total_height = y_top_gnd + t
    
    ax1.set_xlim(-margin, total_width + margin)
    ax1.set_ylim(-margin * 0.5, total_height + margin * 1.5)
    ax1.set_aspect('equal')
    ax1.axis('off')
    
    # 下接地層
    gnd_bottom = Rectangle((0, y_bot_gnd), total_width, t,
                          facecolor=colors['gnd'], edgecolor=colors['conductor_edge'], linewidth=2)
    ax1.add_patch(gnd_bottom)
    ax1.text(total_width/2, y_bot_gnd + t/2, 'Bottom GND',
             ha='center', va='center', fontsize=9, color='white', fontweight='bold')
    
    # 下介電層
    die_bottom = Rectangle((0, y_bot_die), total_width, h,
                          facecolor=colors['polyimide'], edgecolor=colors['polyimide_edge'], 
                          linewidth=2, alpha=0.85)
    ax1.add_patch(die_bottom)
    
    # 信號層
    for i in range(n_draw):
        x_center = s * (i + 0.5)
        sig = Rectangle((x_center - w/2, y_signal - t/2), w, t,
                        facecolor=colors['conductor'], edgecolor=colors['conductor_edge'], linewidth=2)
        ax1.add_patch(sig)
        ax1.text(x_center, y_signal, f'S{i+1}', ha='center', va='center',
                 fontsize=8, color='white', fontweight='bold')
        
        if i < n_draw - 1:
            gnd_x = x_center + s/2
            gnd_w = w * 0.3
            gnd_sep = Rectangle((gnd_x - gnd_w/2, y_signal - t/2), gnd_w, t,
                               facecolor=colors['gnd'], edgecolor=colors['conductor_edge'], linewidth=1.5)
            ax1.add_patch(gnd_sep)
    
    # 上介電層
    die_top = Rectangle((0, y_top_die), total_width, h,
                        facecolor=colors['polyimide'], edgecolor=colors['polyimide_edge'],
                        linewidth=2, alpha=0.85)
    ax1.add_patch(die_top)
    
    # 上接地層
    gnd_top = Rectangle((0, y_top_gnd), total_width, t,
                        facecolor=colors['gnd'], edgecolor=colors['conductor_edge'], linewidth=2)
    ax1.add_patch(gnd_top)
    ax1.text(total_width/2, y_top_gnd + t/2, 'Top GND',
             ha='center', va='center', fontsize=9, color='white', fontweight='bold')
    
    # Via
    if via_enabled:
        via_spacing = 1.0 / via_density
        n_vias = int(total_width / via_spacing) + 1
        via_r = via_diameter / 2000
        for i in range(n_vias):
            x_via = i * via_spacing
            if x_via > total_width:
                break
            ax1.plot([x_via, x_via], [y_bot_gnd + t/2, y_top_gnd + t/2],
                     color=colors['via'], linewidth=2, alpha=0.7, linestyle='-')
            for y in [y_bot_gnd + t/2, y_top_gnd + t/2]:
                v = Circle((x_via, y), via_r, facecolor=colors['via'], edgecolor='black', linewidth=1)
                ax1.add_patch(v)
    
    # 尺寸標註
    ax1.annotate('', xy=(-margin*0.3, 0), xytext=(-margin*0.3, total_height),
                 arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax1.text(-margin*0.5, total_height/2, f'Total\n{total_height*1000:.0f}μm',
             ha='right', va='center', fontsize=8, color=colors['dimension'])
    
    ax1.annotate('', xy=(s*0.5 - w/2, -margin*0.2), xytext=(s*0.5 + w/2, -margin*0.2),
                 arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax1.text(s*0.5, -margin*0.35, f'w={w*1000:.0f}μm',
             ha='center', va='top', fontsize=8, color=colors['dimension'])
    
    ax1.annotate('', xy=(s*0.5, -margin*0.6), xytext=(s*1.5, -margin*0.6),
                 arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=1.5))
    ax1.text(s, -margin*0.8, f'pitch={s:.1f}mm',
             ha='center', va='top', fontsize=9, color=colors['arrow'], fontweight='bold')
    
    ax1.set_title('前視圖 (Cross-Section)', fontsize=12, fontweight='bold')
    
    # ===== 側視圖 (右上) =====
    ax2 = fig.add_subplot(2, 2, 2)
    
    margin2 = L * 0.02
    
    # 下接地層
    gnd_bottom2 = Rectangle((0, y_bot_gnd), L, t,
                           facecolor=colors['gnd'], edgecolor=colors['conductor_edge'], linewidth=1.5)
    ax2.add_patch(gnd_bottom2)
    
    # 下介電層
    die_bottom2 = Rectangle((0, y_bot_die), L, h,
                           facecolor=colors['polyimide'], edgecolor=colors['polyimide_edge'],
                           linewidth=1.5, alpha=0.85)
    ax2.add_patch(die_bottom2)
    
    # 信號層
    signal2 = Rectangle((0, y_signal - t/2), L, t,
                       facecolor=colors['conductor'], edgecolor=colors['conductor_edge'], linewidth=1.5)
    ax2.add_patch(signal2)
    ax2.text(L/2, y_signal, 'Signal', ha='center', va='center',
             fontsize=9, color='white', fontweight='bold')
    
    # 上介電層
    die_top2 = Rectangle((0, y_top_die), L, h,
                        facecolor=colors['polyimide'], edgecolor=colors['polyimide_edge'],
                        linewidth=1.5, alpha=0.85)
    ax2.add_patch(die_top2)
    
    # 上接地層
    gnd_top2 = Rectangle((0, y_top_gnd), L, t,
                        facecolor=colors['gnd'], edgecolor=colors['conductor_edge'], linewidth=1.5)
    ax2.add_patch(gnd_top2)
    
    # 標註
    label_x = L + margin2 * 5
    ax2.text(label_x, y_bot_gnd + t/2, 'GND', ha='left', va='center', fontsize=8, color=colors['text'])
    ax2.text(label_x, y_bot_die + h/2, 'Polyimide', ha='left', va='center', fontsize=8, color=colors['text'])
    ax2.text(label_x, y_signal, 'Signal', ha='left', va='center', fontsize=8, color=colors['text'])
    ax2.text(label_x, y_top_die + h/2, 'Polyimide', ha='left', va='center', fontsize=8, color=colors['text'])
    ax2.text(label_x, y_top_gnd + t/2, 'GND', ha='left', va='center', fontsize=8, color=colors['text'])
    
    # 長度標註
    ax2.annotate('', xy=(0, -margin2*2), xytext=(L, -margin2*2),
                 arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=1.5))
    ax2.text(L/2, -margin2*3, f'L = {L:.0f} mm', ha='center', va='top',
             fontsize=9, color=colors['arrow'], fontweight='bold')
    
    ax2.set_xlim(-margin2*5, L + margin2*8)
    ax2.set_ylim(-margin2*4, total_height + margin2*2)
    ax2.set_aspect('equal')
    ax2.axis('off')
    ax2.set_title('側視圖 (Side View)', fontsize=12, fontweight='bold')
    
    # ===== 上視圖 (左下) =====
    ax3 = fig.add_subplot(2, 2, 3)
    
    n_draw_top = min(n_channels, 8)
    total_width_top = s * n_draw_top + w * 2
    margin3 = s * 0.3
    
    for i in range(n_draw_top):
        x_center = s * (i + 0.5) + w * 0.5
        
        signal3 = Rectangle((x_center - w/2, 0), w, L,
                           facecolor=colors['conductor'], edgecolor=colors['signal_edge'], linewidth=1.5)
        ax3.add_patch(signal3)
        ax3.text(x_center, L/2, f'S{i+1}', ha='center', va='center',
                 fontsize=9, color='white', fontweight='bold', rotation=90)
        
        if i < n_draw_top - 1:
            gnd_x = x_center + s/2 - w*0.15
            gnd3 = Rectangle((gnd_x, 0), w*0.3, L,
                            facecolor=colors['gnd'], edgecolor=colors['gnd_edge'], linewidth=1.5)
            ax3.add_patch(gnd3)
            ax3.text(gnd_x + w*0.15, L/2, 'G', ha='center', va='center',
                     fontsize=7, color='white', fontweight='bold', rotation=90)
    
    # 標註
    for i in range(n_draw_top):
        x_center = s * (i + 0.5) + w * 0.5
        ax3.text(x_center, -margin3*0.5, f'Ch{i+1}', ha='center', va='top',
                 fontsize=8, color=colors['text'])
    
    ax3.annotate('', xy=(0, -margin3*1.5), xytext=(total_width_top, -margin3*1.5),
                 arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=1.5))
    ax3.text(total_width_top/2, -margin3*2, f'總寬度 = {total_width_top:.1f} mm',
             ha='center', va='top', fontsize=9, color=colors['arrow'], fontweight='bold')
    
    ax3.annotate('', xy=(0, -margin3*3), xytext=(s + w, -margin3*3),
                 arrowprops=dict(arrowstyle='<->', color=colors['dimension'], lw=1.5))
    ax3.text((s + w)/2, -margin3*3.5, f'pitch={s:.1f}mm',
             ha='center', va='top', fontsize=8, color=colors['dimension'])
    
    ax3.annotate('', xy=(total_width_top + margin3, 0), xytext=(total_width_top + margin3, L),
                 arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=1.5))
    ax3.text(total_width_top + margin3*2, L/2, f'L={L:.0f}mm',
             ha='left', va='center', fontsize=9, color=colors['arrow'], fontweight='bold')
    
    ax3.set_xlim(-margin3, total_width_top + margin3*4)
    ax3.set_ylim(-margin3*6, L + margin3)
    ax3.set_aspect('equal')
    ax3.axis('off')
    ax3.set_title('上視圖 (Top View)', fontsize=12, fontweight='bold')
    
    # ===== 圖例與說明 (右下) =====
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.axis('off')
    
    info_text = f"""
    📐 三視圖尺寸說明

    幾何參數：
    • 通道數: {n_channels}
    • Pitch: {pitch:.1f} mm
    • 長度 L: {length:.0f} mm
    • 信號線寬 w: {geo.w*1000:.0f} μm
    • 導體厚度 t: {geo.t:.0f} μm
    • 介電厚度 h: {geo.h*1000:.0f} μm

    結構層次 (由下到上)：
    1. Bottom GND (接地層)
    2. Polyimide 介電層 (εr=3.4)
    3. Signal + GND 分隔 (G-S-G)
    4. Polyimide 介電層 (εr=3.4)
    5. Top GND (接地層)

    {"✅ Via Stitching: 已啟用" if via_enabled else "❌ Via Stitching: 未啟用"}
    {"   Via 密度: " + str(via_density) + "/mm, 直徑: " + str(via_diameter) + "μm" if via_enabled else ""}

    材料：
    • 導體: {geo.n_channels}通道 Ag/NbTi
    • 介電: Polyimide (εr=3.4)
    """
    ax4.text(0.05, 0.95, info_text, fontsize=10, va='top', linespacing=1.6,
             bbox=dict(boxstyle='round', facecolor='#F0F0F0', alpha=0.9))
    
    plt.suptitle(f'Cri/oFlex3 傳輸線三視圖 (G-S-G Stripline, {n_channels}通道)',
                 fontsize=16, fontweight='bold', y=0.98)
    tight_layout()
    return fig
