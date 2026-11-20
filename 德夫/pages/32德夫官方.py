from streamlit import pyplot
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
import numpy as np
from dataclasses import dataclass, field

# ============================================================
# 模組化參數類別
# ============================================================

@dataclass
class FlexLineParams:
    """Cri/oFlex3 柔性傳輸線參數 - 可動態調整"""
    length: float = 100.0
    width: float = 18.0
    thickness: float = 0.30
    num_channels: int = 8
    channel_pitch: float = 2.0
    channel_width: float = 0.15
    top_cover_thick: float = 0.02
    top_gnd_thick: float = 0.03
    dielectric_thick: float = 0.18
    bottom_gnd_thick: float = 0.03
    bottom_cover_thick: float = 0.02
    via_diameter: float = 0.08
    via_pitch: float = 1.0
    num_via_rows: int = 3
    dielectric_material: str = "Polyimide (Kapton)"
    conductor_material: str = "Silver (Ag)"
    cross_section_y_scale: float = 25.0
    colors: dict = field(default_factory=lambda: {
        'top_cover': '#E8DDD0',
        'top_gnd': '#B8B8B8',
        'dielectric': '#D4A574',
        'signal': '#FFD700',
        'bottom_gnd': '#B8B8B8',
        'bottom_cover': '#E8DDD0',
        'via_signal': '#E85D04',
        'via_gnd': '#4361EE',
        'outline': '#2D3436',
        'text': '#2D3436',
    })


class CrioFlex3Drawer:
    """模組化 Cri/oFlex3 繪圖器"""
    
    def __init__(self, params: FlexLineParams = None):
        self.p = params or FlexLineParams()
        self.fig = None
    
    def _rect(self, ax, x, y, w, h, color, hatch=None, ec='#333', lw=0.8, alpha=0.9):
        r = Rectangle((x, y), w, h, facecolor=color, edgecolor=ec,
                     linewidth=lw, hatch=hatch, alpha=alpha)
        ax.add_patch(r)
        return r
    
    def draw_cross_section(self, ax):
        p = self.p
        ys = p.cross_section_y_scale
        W = p.width
        
        t_bc = p.bottom_cover_thick * ys
        t_bg = p.bottom_gnd_thick * ys
        t_d = p.dielectric_thick * ys
        t_tg = p.top_gnd_thick * ys
        t_tc = p.top_cover_thick * ys
        total_h = t_bc + t_bg + t_d + t_tg + t_tc
        y0 = -total_h / 2
        c = p.colors
        
        # 各層繪製
        y1 = y0 + t_bc
        self._rect(ax, -W/2, y0, W, t_bc, c['bottom_cover'])
        ax.text(-W/2 - 1.2, (y0+y1)/2, 'Bottom\nCover', ha='right', va='center',
               fontsize=6, fontweight='bold', color=c['text'])
        
        y2 = y1 + t_bg
        self._rect(ax, -W/2, y1, W, t_bg, c['bottom_gnd'], '///')
        ax.text(-W/2 - 1.2, (y1+y2)/2, 'Bottom\nGND', ha='right', va='center',
               fontsize=6, fontweight='bold', color=c['text'])
        
        y3 = y2 + t_d
        self._rect(ax, -W/2, y2, W, t_d, c['dielectric'])
        ax.text(-W/2 - 1.2, (y2+y3)/2, 'Dielectric\n(Kapton)', ha='right', va='center',
               fontsize=6, fontweight='bold', color=c['text'])
        
        # Signal lines
        sig_y = y2 + t_d/2 - 0.25
        start_x = -(p.num_channels - 1) * p.channel_pitch / 2
        for i in range(p.num_channels):
            x = start_x + i * p.channel_pitch
            self._rect(ax, x - p.channel_width/2, sig_y, p.channel_width, 0.5,
                      c['signal'], ec='#B8860B', lw=0.5)
            ax.text(x, sig_y + 0.65, f'Ch{i+1}', fontsize=5, ha='center', va='bottom',
                   color='#8B4513', fontweight='bold')
        
        # GND Vias
        via_ys = np.linspace(y2 + 0.4, y3 - 0.4, p.num_via_rows)
        for vy in via_ys:
            for vx in [-W/2 + 1.5, W/2 - 1.5]:
                ax.add_patch(Circle((vx, vy), p.via_diameter * ys / 2,
                          facecolor=c['via_gnd'], edgecolor='white', lw=0.3))
        
        y4 = y3 + t_tg
        self._rect(ax, -W/2, y3, W, t_tg, c['top_gnd'], '///')
        ax.text(-W/2 - 1.2, (y3+y4)/2, 'Top\nGND', ha='right', va='center',
               fontsize=6, fontweight='bold', color=c['text'])
        
        y5 = y4 + t_tc
        self._rect(ax, -W/2, y4, W, t_tc, c['top_cover'])
        ax.text(-W/2 - 1.2, (y4+y5)/2, 'Top\nCover', ha='right', va='center',
               fontsize=6, fontweight='bold', color=c['text'])
        
        # 外框線
        ax.plot([-W/2, W/2, W/2, -W/2, -W/2], [y0, y0, y5, y5, y0],
               color=c['outline'], lw=1.5)
        
        # 尺寸標註 - 寬度（下方）
        dim_y = y0 - 2.5
        ax.annotate('', xy=(W/2, dim_y), xytext=(-W/2, dim_y),
                   arrowprops=dict(arrowstyle='<->', color=c['text'], lw=0.8))
        ax.plot([-W/2, -W/2], [y0, dim_y], color=c['text'], lw=0.5)
        ax.plot([W/2, W/2], [y0, dim_y], color=c['text'], lw=0.5)
        ax.text(0, dim_y - 0.6, f'W = {W:.1f} mm', ha='center', va='top',
               fontsize=7, fontweight='bold', color=c['text'])
        
        # 尺寸標註 - 厚度（右側）
        dim_x = W/2 + 2.5
        ax.annotate('', xy=(dim_x, y5), xytext=(dim_x, y0),
                   arrowprops=dict(arrowstyle='<->', color=c['text'], lw=0.8))
        ax.plot([W/2, dim_x], [y0, y0], color=c['text'], lw=0.5)
        ax.plot([W/2, dim_x], [y5, y5], color=c['text'], lw=0.5)
        ax.text(dim_x + 0.5, (y0+y5)/2, f't = {p.thickness:.2f} mm',
               ha='left', va='center', fontsize=7, fontweight='bold', color=c['text'],
               rotation=90, rotation_mode='anchor')
        
        ax.set_xlim(-W/2 - 7, W/2 + 8)
        ax.set_ylim(y0 - 5, y5 + 4)
        ax.set_aspect('auto')
        ax.set_title('Cross-Section View (A-A\')', fontsize=10, fontweight='bold', pad=8)
        ax.axis('off')
    
    def draw_top_view(self, ax):
        p = self.p
        L, W = p.length, p.width
        c = p.colors
        
        # 外框
        flex = FancyBboxPatch((-L/2, -W/2), L, W,
                             boxstyle="round,pad=0,rounding_size=0.8",
                             facecolor=c['top_cover'], edgecolor=c['outline'],
                             lw=1.2, alpha=0.6)
        ax.add_patch(flex)
        
        # 內部介電層區域
        inner = FancyBboxPatch((-L/2 + 1, -W/2 + 0.5), L - 2, W - 1,
                              boxstyle="round,pad=0,rounding_size=0.3",
                              facecolor=c['dielectric'], edgecolor='#999',
                              lw=0.5, alpha=0.25)
        ax.add_patch(inner)
        
        # 訊號線
        start_y = -(p.num_channels - 1) * p.channel_pitch / 2
        for i in range(p.num_channels):
            y = start_y + i * p.channel_pitch
            self._rect(ax, -L/2 + 3, y - p.channel_width/2, L - 6, p.channel_width,
                      c['signal'], ec='#B8860B', lw=0.5)
            ax.text(-L/2 + 1.5, y, f'CH{i+1}', fontsize=6, ha='right', va='center',
                   color=c['text'], fontweight='bold')
            ax.text(L/2 - 1.5, y, f'CH{i+1}', fontsize=6, ha='left', va='center',
                   color=c['text'], fontweight='bold')
        
        # GND Via
        via_y = np.linspace(-W/2 + 1.2, W/2 - 1.2, 10)
        for x in [-L/2 + 2.5, L/2 - 2.5]:
            for y in via_y:
                ax.add_patch(Circle((x, y), p.via_diameter/2,
                          facecolor=c['via_gnd'], edgecolor='white', lw=0.3))
        
        # Signal Via
        via_x = np.linspace(-L/2 + 10, L/2 - 10, 3)
        for i in range(p.num_channels):
            y = start_y + i * p.channel_pitch
            for x in via_x:
                ax.add_patch(Circle((x, y), p.via_diameter/2.5,
                          facecolor=c['via_signal'], edgecolor='white', lw=0.2))
        
        # 尺寸標註 - 長度
        dim_y = -W/2 - 2.5
        ax.annotate('', xy=(L/2, dim_y), xytext=(-L/2, dim_y),
                   arrowprops=dict(arrowstyle='<->', color=c['text'], lw=1))
        ax.plot([-L/2, -L/2], [-W/2, dim_y], color=c['text'], lw=0.5)
        ax.plot([L/2, L/2], [-W/2, dim_y], color=c['text'], lw=0.5)
        ax.text(0, dim_y - 0.6, f'L = {L:.0f} mm', ha='center', va='top',
               fontsize=8, fontweight='bold', color=c['text'])
        
        # 尺寸標註 - 寬度
        dim_x = L/2 + 3
        ax.annotate('', xy=(dim_x, W/2), xytext=(dim_x, -W/2),
                   arrowprops=dict(arrowstyle='<->', color=c['text'], lw=1))
        ax.plot([L/2, dim_x], [-W/2, -W/2], color=c['text'], lw=0.5)
        ax.plot([L/2, dim_x], [W/2, W/2], color=c['text'], lw=0.5)
        ax.text(dim_x + 0.6, 0, f'W = {W:.1f} mm', ha='left', va='center',
               fontsize=8, fontweight='bold', color=c['text'], rotation=90)
        
        # 截面線
        ax.plot([0, 0], [-W/2 + 0.3, W/2 - 0.3], 'k--', lw=0.8, alpha=0.4)
        ax.text(0, -W/2 - 0.5, 'A', fontsize=9, ha='center', va='top',
               fontweight='bold', color=c['text'])
        ax.text(0, W/2 + 0.5, "A'", fontsize=9, ha='center', va='bottom',
               fontweight='bold', color=c['text'])
        
        ax.set_xlim(-L/2 - 8, L/2 + 10)
        ax.set_ylim(-W/2 - 6, W/2 + 5)
        ax.set_aspect('equal')
        ax.set_title('Top View', fontsize=10, fontweight='bold', pad=8)
        ax.axis('off')
    
    def draw_3d_stackup(self, ax):
        p = self.p
        c = p.colors
        
        layers = [
            (p.top_cover_thick * 60, c['top_cover'], 'Top Cover (PI)'),
            (p.top_gnd_thick * 60, c['top_gnd'], 'Top GND (Ag)'),
            (p.dielectric_thick * 60, c['dielectric'], 'Dielectric (PI)'),
            (p.bottom_gnd_thick * 60, c['bottom_gnd'], 'Bottom GND (Ag)'),
            (p.bottom_cover_thick * 60, c['bottom_cover'], 'Bottom Cover (PI)'),
        ]
        
        y_off = 0
        Ls = min(p.length, 50)
        Ws = p.width
        
        for thick, color, name in layers:
            xx, yy = np.meshgrid(np.linspace(-Ls/2, Ls/2, 12),
                                np.linspace(-Ws/2, Ws/2, 8))
            zz = np.full_like(xx, y_off)
            ax.plot_surface(xx, yy, zz, alpha=0.72, color=color,
                          edgecolor='#555', lw=0.15, antialiased=True)
            ax.text(Ls/2 + 2, 0, y_off + thick/2, name, fontsize=6, color='#333', va='center')
            y_off += thick + 2.5
        
        # Signal lines
        sig_z = layers[0][0] + layers[1][0] + layers[2][0]/2 + 2.5
        start_y = -(p.num_channels - 1) * p.channel_pitch / 2
        for i in range(p.num_channels):
            y = start_y + i * p.channel_pitch
            xl = np.linspace(-Ls/2 + 3, Ls/2 - 3, 25)
            yl = np.full_like(xl, y)
            zl = np.full_like(xl, sig_z)
            ax.plot(xl, yl, zl, color=c['signal'], lw=1.5)
        
        ax.set_xlabel('Length (mm)', fontsize=7)
        ax.set_ylabel('Width (mm)', fontsize=7)
        ax.set_zlabel('Layer (scaled)', fontsize=7)
        ax.set_title('3D Exploded Stack-up', fontsize=10, fontweight='bold', pad=10)
        ax.view_init(elev=20, azim=-50)
        ax.set_box_aspect([Ls/18, Ws/8, 1])
    
    def draw_legend(self, ax):
        p = self.p
        c = p.colors
        items = [
            (c['top_cover'], 'Polyimide Cover'),
            (c['top_gnd'], 'Ground Plane (Ag)'),
            (c['dielectric'], 'Dielectric (Kapton)'),
            (c['signal'], 'Signal Line (Ag)'),
            (c['via_gnd'], 'GND Via'),
            (c['via_signal'], 'Signal Via'),
        ]
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        ax.set_title('Legend', fontsize=9, fontweight='bold', color='#2D3436', pad=5)
        y = 0.88
        for color, label in items:
            ax.add_patch(Rectangle((0.05, y - 0.025), 0.08, 0.04,
                        facecolor=color, edgecolor='#333', lw=0.5,
                        transform=ax.transAxes))
            ax.text(0.16, y - 0.005, label, fontsize=7.5, va='center',
                   transform=ax.transAxes, color='#2D3436')
            y -= 0.12
    
    def draw_parameter_table(self, ax):
        p = self.p
        ax.axis('off')
        
        data = [
            ["Category", "Parameter", "Value", "Unit"],
            ["----------", "----------------------", "----------", "------"],
            ["Dimensions", "Total Length (L)", f"{p.length:.0f}", "mm"],
            ["", "Total Width (W)", f"{p.width:.1f}", "mm"],
            ["", "Total Thickness (t)", f"{p.thickness:.2f}", "mm"],
            ["", "Min. Bend Radius", "5", "mm"],
            ["Channels", "Channel Count", f"{p.num_channels}", "ch"],
            ["", "Channel Pitch", f"{p.channel_pitch:.1f}", "mm"],
            ["", "Signal Line Width", f"{p.channel_width*1000:.0f}", "um"],
            ["Layers", "Top Cover", f"{p.top_cover_thick*1000:.0f}", "um"],
            ["", "Top GND (Ag)", f"{p.top_gnd_thick*1000:.0f}", "um"],
            ["", "Dielectric", f"{p.dielectric_thick*1000:.0f}", "um"],
            ["", "Bottom GND (Ag)", f"{p.bottom_gnd_thick*1000:.0f}", "um"],
            ["", "Bottom Cover", f"{p.bottom_cover_thick*1000:.0f}", "um"],
            ["Via", "Via Diameter", f"{p.via_diameter*1000:.0f}", "um"],
            ["", "Via Pitch", f"{p.via_pitch:.1f}", "mm"],
            ["", "Via Rows", f"{p.num_via_rows}", "rows"],
            ["Material", "Dielectric", p.dielectric_material, ""],
            ["", "Conductor", p.conductor_material, ""],
            ["Electrical", "Impedance", "50", "Ohm"],
            ["", "Frequency", "DC ~ 10", "GHz"],
            ["", "Crosstalk", "-40", "dB"],
            ["Thermal", "Operating Temp", "10^-3 ~ 400", "K"],
            ["", "Heat Load/ch", "< 4", "uW"],
        ]
        
        table = ax.table(cellText=data, loc='center', cellLoc='center',
                        colWidths=[0.15, 0.30, 0.13, 0.10])
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.3)
        
        for i in range(len(data)):
            for j in range(4):
                cell = table[(i, j)]
                if i == 0:
                    cell.set_facecolor('#4A5568')
                    cell.set_text_props(color='white', fontweight='bold', fontsize=9)
                elif i == 1:
                    cell.set_facecolor('#E2E8F0')
                    cell.set_text_props(fontsize=5, color='#A0AEC0')
                elif data[i][0] != "":
                    cell.set_facecolor('#EDF2F7')
                    cell.set_text_props(fontweight='bold', color='#2D3748')
                else:
                    cell.set_facecolor('#FFFFFF')
                cell.set_edgecolor('#CBD5E0')
                cell.set_linewidth(0.5)
        
        # 表格標題放在上方，不與表格重疊
        ax.set_title('Cri/oFlex3 CF3 Specifications', fontsize=11,
                    fontweight='bold', color='#2D3748', pad=15)
    
    def draw_structure_note(self, ax):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        notes = [
            "Stack-up:", "",
            "  [5] Top Cover (PI)",
            "  [4] Top GND (Ag)",
            "  [3] Dielectric (PI)",
            "      + Signal Lines",
            "  [2] Bottom GND (Ag)",
            "  [1] Bottom Cover (PI)", "",
            "Features:",
            "  * Stripline topology",
            "  * 50 Ohm impedance",
            "  * Integrated filters",
            "  * Cryo-compatible",
            "  * Ultra-flexible",
        ]
        y = 0.95
        for note in notes:
            bold = note.startswith(('Stack', 'Features'))
            ax.text(0.05, y, note, fontsize=7.5, va='top',
                   fontweight='bold' if bold else 'normal',
                   color='#2D3748', family='monospace')
            y -= 0.058
    
    def draw_extra_info(self, ax):
        p = self.p
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        info = (
            f"Delft Circuits\n"
            f"Cri/oFlex3 CF3\n\n"
            f"Cryogenic RF\n"
            f"Flex Cable\n\n"
            f"Operating:\n"
            f"  10^-3 K ~ 400 K\n\n"
            f"Heat Load:\n"
            f"  < 4 uW/ch\n\n"
            f"Freq Range:\n"
            f"  DC ~ 10 GHz\n\n"
            f"Channels:\n"
            f"  {p.num_channels} ch\n\n"
            f"Pitch:\n"
            f"  {p.channel_pitch:.1f} mm"
        )
        ax.text(0.5, 0.5, info, fontsize=8, ha='center', va='center',
               color='#4A5568', family='monospace',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='#F7FAFC',
                        edgecolor='#CBD5E0', lw=1))
    
    def draw(self, figsize=(18, 14), save_path: str = None):
        p = self.p
        self.fig = plt.figure(figsize=figsize, facecolor='#FAFAFA')
        
        # 精確 gridspec 佈局
        gs = self.fig.add_gridspec(
            3, 3,
            height_ratios=[1.0, 1.0, 1.15],
            width_ratios=[1.0, 1.0, 0.28],
            hspace=0.32, wspace=0.28,
            left=0.05, right=0.96, top=0.91, bottom=0.04
        )
        
        self.fig.suptitle(
            f'Delft Cri/oFlex3 (CF3) Flexible Quantum Transmission Line\n'
            f'{p.num_channels}-Channel Stripline  |  {p.dielectric_material} + {p.conductor_material}  |  '
            f'L={p.length:.0f}mm x W={p.width:.1f}mm x t={p.thickness:.2f}mm',
            fontsize=13, fontweight='bold', color='#1A202C', y=0.97
        )
        
        # Row 0
        ax_cross = self.fig.add_subplot(gs[0, 0])
        self.draw_cross_section(ax_cross)
        
        ax_top = self.fig.add_subplot(gs[0, 1])
        self.draw_top_view(ax_top)
        
        ax_legend = self.fig.add_subplot(gs[0, 2])
        self.draw_legend(ax_legend)
        
        # Row 1
        ax_3d = self.fig.add_subplot(gs[1, :2], projection='3d')
        self.draw_3d_stackup(ax_3d)
        
        ax_note = self.fig.add_subplot(gs[1, 2])
        self.draw_structure_note(ax_note)
        
        # Row 2 - 參數表格置中於下方
        ax_table = self.fig.add_subplot(gs[2, :2])
        self.draw_parameter_table(ax_table)
        
        ax_extra = self.fig.add_subplot(gs[2, 2])
        self.draw_extra_info(ax_extra)
        
        #if save_path:
        #    plt.savefig(save_path, dpi=200, bbox_inches='tight',
        #               facecolor='#FAFAFA', edgecolor='none')
        
        #plt.show()
        return self.fig


# ============================================================
# 範例 1：標準 8 通道
# ============================================================
params1 = FlexLineParams(
    length=100, width=18.0, thickness=0.30,
    num_channels=8, channel_pitch=2.0, channel_width=0.15,
    dielectric_thick=0.18, top_gnd_thick=0.03, bottom_gnd_thick=0.03,
    top_cover_thick=0.02, bottom_cover_thick=0.02,
    via_diameter=0.08, via_pitch=1.0, num_via_rows=3,
    cross_section_y_scale=25.0,
)
drawer1 = CrioFlex3Drawer(params1)
圖 = drawer1.draw(figsize=(18, 14), save_path='/mnt/agents/output/crioflex3_cf3_standard_8ch.png')
pyplot(圖)
