#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#from datetime import now
from datetime import datetime
from matplotlib.pyplot import axis, close, cm, figtext, figure, subplots, tight_layout, title
from numpy import linspace, mean
from json import dump
from pandas import DataFrame, ExcelWriter

# Create an advanced analysis report generator
"""
量子計算柔性傳輸線技術分析報告生成器
Quantum Computing Flex Cable Technical Analysis Report Generator
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import json
from typing import Dict, List
from dataclasses import asdict

class TechnicalReportGenerator:
    """技術報告生成器"""
    
    def __init__(self, cable_db):
        self.cable_db = cable_db
        self.report_data = {}
        
    def generate_full_report(self, output_file='quantum_flex_cable_report.pdf'):
        """生成完整技術報告"""
        with PdfPages(output_file) as pdf:
            # 封面
            self._create_cover_page(pdf)
            
            # 規格總覽
            self._create_specification_summary(pdf)
            
            # 衰減分析
            self._create_attenuation_analysis(pdf)
            
            # 熱分析
            self._create_thermal_analysis(pdf)
            
            # 串擾分析
            self._create_crosstalk_analysis(pdf)
            
            # 應用建議
            self._create_application_guide(pdf)
            
        print(f"✅ 技術報告已生成: {output_file}")
        
    def _create_cover_page(self, pdf):
        """創建封面"""
        fig = plt.figure(figsize=(8.5, 11))
        fig.suptitle('Quantum Computing Flexible Cable\nTechnical Analysis Report', 
                    fontsize=20, fontweight='bold', y=0.8)
        
        info_text = f"""
        Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        
        Covered Manufacturers:
        • Rigetti Computing
        • Delft Circuits
        • Amphenol RF
        • Radiall
        • Rosenberger
        
        Analysis Scope:
        • DC - 70 GHz Frequency Range
        • 4K to 400K Temperature Range
        • Crosstalk and Isolation
        • Thermal Load Assessment
        • Application Recommendations
        
        Version: 1.0
        """
        
        plt.figtext(0.5, 0.5, info_text, ha='center', va='center', 
                   fontsize=12, family='monospace')
        plt.axis('off')
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
    def _create_specification_summary(self, pdf):
        """規格總覽表"""
        fig, ax = plt.subplots(figsize=(11, 8.5))
        ax.axis('tight')
        ax.axis('off')
        
        # 準備表格數據
        table_data = []
        headers = ['Manufacturer', 'Model', 'Type', 'Freq Range', 'Z (Ω)', 
                  'Thickness', 'Bend R', 'Channels', 'Xtalk (dB)']
        
        for key, cable in self.cable_db.items():
            table_data.append([
                cable.manufacturer,
                cable.model,
                cable.cable_type,
                cable.freq_range,
                f"{cable.impedance}",
                f"{cable.thickness}mm",
                f"{cable.bend_radius}mm",
                f"{cable.channels_per_flex}",
                f"{cable.crosstalk_db}"
            ])
        
        table = ax.table(cellText=table_data, colLabels=headers,
                        cellLoc='center', loc='center',
                        colWidths=[0.15, 0.18, 0.15, 0.12, 0.08, 
                                  0.1, 0.1, 0.08, 0.1])
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 2)
        
        # 標題樣式
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#4472C4')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        plt.title('Cable Specifications Summary', fontsize=14, fontweight='bold', pad=20)
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
    def _create_attenuation_analysis(self, pdf):
        """衰減分析圖表"""
        fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
        fig.suptitle('Attenuation Analysis', fontsize=14, fontweight='bold')
        
        cables = list(self.cable_db.values())
        
        # 1. 6GHz衰減比較
        ax1 = axes[0, 0]
        names = [f"{c.manufacturer[:8]}\\n{c.model[:10]}" for c in cables]
        att_6g = [c.attenuation_6ghz for c in cables]
        colors = plt.cm.viridis(np.linspace(0, 1, len(cables)))
        ax1.barh(names, att_6g, color=colors)
        ax1.set_xlabel('Attenuation (dB/m) @ 6GHz')
        ax1.set_title('6GHz Attenuation Comparison')
        ax1.grid(True, alpha=0.3)
        
        # 2. 頻率響應曲線
        ax2 = axes[0, 1]
        freqs = [6, 12, 18]
        for cable in cables[:4]:  # 只顯示前4個避免混亂
            atts = [cable.attenuation_6ghz, cable.attenuation_12ghz, 
                   cable.attenuation_18ghz]
            ax2.plot(freqs, atts, marker='o', label=f"{cable.manufacturer} {cable.model}", 
                    linewidth=2)
        ax2.set_xlabel('Frequency (GHz)')
        ax2.set_ylabel('Attenuation (dB/m)')
        ax2.set_title('Frequency Response')
        ax2.legend(fontsize=8)
        ax2.grid(True, alpha=0.3)
        
        # 3. 材料類型vs衰減
        ax3 = axes[1, 0]
        material_groups = {}
        for cable in cables:
            mat = cable.material.split('+')[0]
            if mat not in material_groups:
                material_groups[mat] = []
            material_groups[mat].append(cable.attenuation_6ghz)
        
        mat_names = list(material_groups.keys())
        mat_atts = [np.mean(v) for v in material_groups.values()]
        ax3.bar(mat_names, mat_atts, color='skyblue')
        ax3.set_ylabel('Avg Attenuation (dB/m)')
        ax3.set_title('Attenuation by Material Type')
        ax3.tick_params(axis='x', rotation=45)
        ax3.grid(True, alpha=0.3)
        
        # 4. 通道密度vs衰減
        ax4 = axes[1, 1]
        channels = [c.channels_per_flex for c in cables]
        att_vals = [c.attenuation_6ghz for c in cables]
        ax4.scatter(channels, att_vals, s=100, alpha=0.6, c=range(len(cables)), 
                   cmap='plasma')
        ax4.set_xlabel('Channels per Flex')
        ax4.set_ylabel('Attenuation (dB/m) @ 6GHz')
        ax4.set_title('Channel Density vs Attenuation')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
    def _create_thermal_analysis(self, pdf):
        """熱分析圖表"""
        fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
        fig.suptitle('Thermal Load Analysis', fontsize=14, fontweight='bold')
        
        cables = list(self.cable_db.values())
        
        # 1. 4K熱負載
        ax1 = axes[0, 0]
        names = [c.model[:15] for c in cables]
        thermal_4k = [c.thermal_load_4k for c in cables]
        colors = plt.cm.coolwarm(np.linspace(0.2, 0.8, len(cables)))
        bars = ax1.bar(names, thermal_4k, color=colors)
        ax1.set_ylabel('Thermal Load (µW) @ 4K')
        ax1.set_title('4K Stage Thermal Load')
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)
        
        # 添加數值標籤
        for bar, val in zip(bars, thermal_4k):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.0f}', ha='center', va='bottom', fontsize=8)
        
        # 2. 10mK熱負載
        ax2 = axes[0, 1]
        thermal_10mk = [c.thermal_load_10mk for c in cables]
        ax2.barh(names, thermal_10mk, color='lightcoral')
        ax2.set_xlabel('Thermal Load (nW) @ 10mK')
        ax2.set_title('10mK Stage Thermal Load')
        ax2.grid(True, alpha=0.3)
        
        # 3. 熱負載比例
        ax3 = axes[1, 0]
        total_thermal = [c.thermal_load_4k + c.thermal_load_10mk/1000 for c in cables]
        ax3.pie(total_thermal, labels=[c.model[:10] for c in cables], 
               autopct='%1.1f%%', startangle=90)
        ax3.set_title('Relative Thermal Load Distribution')
        
        # 4. 通道數vs熱負載
        ax4 = axes[1, 1]
        channels = [c.channels_per_flex for c in cables]
        ax4.scatter(channels, thermal_4k, s=150, alpha=0.6, label='4K')
        ax4.scatter(channels, [t/10 for t in thermal_10mk], s=150, alpha=0.6, label='10mK/10')
        ax4.set_xlabel('Channels per Flex')
        ax4.set_ylabel('Thermal Load')
        ax4.set_title('Channel Count vs Thermal Load')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
    def _create_crosstalk_analysis(self, pdf):
        """串擾分析圖表"""
        fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
        fig.suptitle('Crosstalk and Isolation Analysis', fontsize=14, fontweight='bold')
        
        cables = list(self.cable_db.values())
        
        # 1. 串擾水平比較
        ax1 = axes[0, 0]
        names = [c.model[:12] for c in cables]
        xtalk = [c.crosstalk_db for c in cables]
        colors = ['green' if x <= -60 else 'orange' if x <= -40 else 'red' for x in xtalk]
        ax1.barh(names, xtalk, color=colors, alpha=0.7)
        ax1.set_xlabel('Crosstalk (dB)')
        ax1.set_title('Crosstalk Levels')
        ax1.axvline(x=-60, color='green', linestyle='--', alpha=0.5, label='Excellent')
        ax1.axvline(x=-40, color='orange', linestyle='--', alpha=0.5, label='Good')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 隔離度vs串擾
        ax2 = axes[0, 1]
        isolation = [c.isolation_db for c in cables]
        ax2.scatter(isolation, xtalk, s=150, alpha=0.6, c=range(len(cables)), cmap='viridis')
        ax2.set_xlabel('Isolation (dB)')
        ax2.set_ylabel('Crosstalk (dB)')
        ax2.set_title('Isolation vs Crosstalk')
        ax2.grid(True, alpha=0.3)
        
        # 3. 彎曲半徑vs串擾
        ax3 = axes[1, 0]
        bend_r = [c.bend_radius for c in cables]
        ax3.scatter(bend_r, xtalk, s=[c.channels_per_flex*30 for c in cables], 
                   alpha=0.6, c=range(len(cables)), cmap='plasma')
        ax3.set_xlabel('Bend Radius (mm)')
        ax3.set_ylabel('Crosstalk (dB)')
        ax3.set_title('Bend Radius vs Crosstalk (bubble=channels)')
        ax3.grid(True, alpha=0.3)
        
        # 4. 線材類型分布
        ax4 = axes[1, 1]
        types = {}
        for c in cables:
            t = c.cable_type
            types[t] = types.get(t, 0) + 1
        ax4.pie(types.values(), labels=types.keys(), autopct='%1.0f%%', 
               startangle=90)
        ax4.set_title('Cable Type Distribution')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
    def _create_application_guide(self, pdf):
        """應用建議指南"""
        fig = plt.figure(figsize=(8.5, 11))
        
        guide_text = """
        APPLICATION GUIDELINES
        ======================
        
        1. HIGH-DENSITY QUANTUM COMPUTING (1000+ qubits)
           Recommended: Delft Cri/oFlex 2, Rigetti High-Density Flex
           • 8-10 channels per flex reduces component count
           • Low thermal load (200-250 µW @ 4K)
           • Excellent crosstalk isolation (-60 dB)
           • Compatible with dilution refrigerators
        
        2. HIGH-FREQUENCY APPLICATIONS (>26 GHz)
           Recommended: Rosenberger RFlex 047/402
           • DC-70 GHz bandwidth
           • Excellent phase stability
           • Low attenuation at high frequencies
           • Suitable for qubit readout lines
        
        3. CRYOGENIC ENVIRONMENT (10mK - 4K)
           Recommended: Delft Cri/oFlex series, Rigetti Flex
           • Designed for cryogenic operation
           • Low thermal conductivity
           • Vibration isolation
           • Superconducting material options (NbTi)
        
        4. GENERAL PURPOSE LABORATORY
           Recommended: Amphenol SMP, Radiall Flex
           • Cost-effective solution
           • Good performance for room temperature
           • Wide connector compatibility
           • Rugged construction
        
        THERMAL DESIGN RECOMMENDATIONS
        ==============================
        • Keep 4K load <50% of cooler capacity
        • Keep 10mK load <20% of cooler capacity
        • Use superconducting cables where possible
        • Implement proper heat sinking at each stage
        
        CROSSTALK MITIGATION
        ====================
        • Maintain >1mm spacing between flex cables
        • Use ground planes effectively
        • Keep parallel lengths minimal
        • Consider shielded cables for sensitive lines
        
        CONNECTOR SELECTION
        ===================
        • SMP/Mini-SMP: High density, push-on
        • SMA: Standard, robust
        • 2.92mm/WSMP: High frequency
        • Custom: For specialized applications
        """
        
        plt.figtext(0.1, 0.95, guide_text, ha='left', va='top',
                   fontsize=10, family='monospace', linespacing=1.5)
        plt.axis('off')
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()

# Export functions
def export_to_json(cable_db, filename='cable_database.json'):
    """匯出線材資料庫為JSON"""
    data = {}
    for key, cable in cable_db.items():
        data[key] = asdict(cable)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ 資料庫已匯出至: {filename}")

def export_to_excel(cable_db, filename='cable_database.xlsx'):
    """匯出線材資料庫為Excel"""
    data = []
    for key, cable in cable_db.items():
        row = asdict(cable)
        row['connectors'] = ', '.join(row['connectors'])
        row['features'] = ', '.join(row['features'])
        data.append(row)
    
    df = pd.DataFrame(data)
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Cable Specifications', index=False)
        
        # 創建摘要工作表
        summary = df.groupby('manufacturer').agg({
            'model': 'count',
            'thermal_load_4k': 'mean',
            'crosstalk_db': 'mean'
        }).round(2)
        summary.to_excel(writer, sheet_name='Manufacturer Summary')
        
    print(f"✅ Excel報告已生成: {filename}")

if __name__ == "__main__":
    from crosstalk_calculator import get_cable_database
    
    print("="*60)
    print("技術報告生成器")
    print("="*60)
    
    cables = get_cable_database()
    
    # 生成PDF報告
    generator = TechnicalReportGenerator(cables)
    generator.generate_full_report('quantum_flex_cable_technical_report.pdf')
    
    # 匯出JSON
    export_to_json(cables, 'cable_database.json')
    
    # 匯出Excel (需要openpyxl)
    try:
        export_to_excel(cables, 'cable_database.xlsx')
    except ImportError:
        print("⚠️ 請安裝openpyxl以生成Excel報告: pip install openpyxl")
    
    print("\\n✅ 所有報告生成完成!")

#with open('/mnt/kimi/output/report_generator.py', 'w', encoding='utf-8') as f:
#    f.write(report_code)

#print("✅ 報告生成器已保存: /mnt/kimi/output/report_generator.py")
