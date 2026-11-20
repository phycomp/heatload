# cf3_template_generator.py
# 技術圖紙樣板產生器

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors


def generate_technical_drawing(calc, front_path, side_path, top_path, output_pdf="CF3_Technical_Drawing.pdf"):
    """
    產生技術圖紙 PDF
    
    Args:
        calc: CF3LayoutCalculator 實例
        front_path: 前視圖 PNG 路徑
        side_path: 側視圖 PNG 路徑
        top_path: 上視圖 PNG 路徑
        output_pdf: 輸出 PDF 路徑
    """
    c = canvas.Canvas(output_pdf, pagesize=A4)
    width, height = A4
    
    # 標題區
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20*mm, height - 20*mm, "Delft cri/oFlex3 CF3 - Technical Drawing")
    
    c.setFont("Helvetica", 10)
    c.drawString(20*mm, height - 30*mm, f"Channels: {calc.n_channels}")
    c.drawString(20*mm, height - 35*mm, f"Total Width: {calc.target_total_width_mm:.3f} mm")
    c.drawString(20*mm, height - 40*mm, f"Total Thickness: {calc.total_thickness_mm:.3f} mm")
    c.drawString(20*mm, height - 45*mm, f"Impedance: {calc.impedance['z0_ohm']:.1f} Ω")
    c.drawString(20*mm, height - 50*mm, f"Crosstalk: {calc.estimated_crosstalk_db:.1f} dB")
    
    # 插入三視圖
    # 前視圖 (左上)
    c.drawImage(front_path, 20*mm, height - 120*mm, width=80*mm, height=60*mm)
    c.setFont("Helvetica", 8)
    c.drawString(20*mm, height - 125*mm, "Front View (X-Z)")
    
    # 側視圖 (右上)
    c.drawImage(side_path, 110*mm, height - 120*mm, width=80*mm, height=60*mm)
    c.drawString(110*mm, height - 125*mm, "Side View (Y-Z)")
    
    # 上視圖 (下半部)
    c.drawImage(top_path, 20*mm, height - 200*mm, width=170*mm, height=100*mm)
    c.drawString(20*mm, height - 205*mm, "Top View (X-Y)")
    
    c.save()
    print(f"✅ 技術圖紙已儲存: {output_pdf}")
