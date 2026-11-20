#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from matplotlib.pyplot import savefig, subplots, tight_layout
from numpy import abs, ceil, interp, linspace, log, log10, pi, sqrt
# Create a standalone crosstalk calculation module
"""
量子計算柔性傳輸線串擾計算模組
Quantum Computing Flex Cable Crosstalk Calculator

支援以下供應商線材規格：
- Rigetti Computing
- Delft Circuits (Cri/oFlex系列)
- Amphenol RF
- Radiall
- Rosenberger

Author: AI Assistant
Date: 2026-04-15
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Dict, List, Tuple
import json

@dataclass
class CableSpec:
    """柔性傳輸線規格數據類"""
    manufacturer: str
    model: str
    cable_type: str
    impedance: float
    freq_range: str
    thickness: float  # mm
    width: float  # mm
    bend_radius: float  # mm
    material: str
    dielectric: str
    attenuation_6ghz: float  # dB/m
    attenuation_12ghz: float  # dB/m
    attenuation_18ghz: float  # dB/m
    crosstalk_db: float
    thermal_load_4k: float  # µW
    thermal_load_10mk: float  # nW
    channels_per_flex: int
    isolation_db: float
    phase_stability: str
    operating_temp: str
    connectors: List[str]
    features: List[str]

class CrosstalkCalculator:
    """串擾計算器類"""
    
    def __init__(self):
        self.epsilon_0 = 8.854e-12  # F/m
        self.mu_0 = 4 * np.pi * 1e-7  # H/m
        self.c = 3e8  # m/s
        
    def calculate_coupling_coefficients(self, s: float, h: float, w: float, 
                                       epsilon_r: float) -> Tuple[float, float, float, float]:
        """
        計算耦合傳輸線的電容和電感係數
        
        Args:
            s: 線間距 (m)
            h: 接地平面距離 (m)
            w: 線寬 (m)
            epsilon_r: 相對介電常數
            
        Returns:
            (C, Cm, L, Lm) 單位長度電容和電感
        """
        # 自電容 (簡化模型)
        c = (2 * np.pi * epsilon_r * self.epsilon_0) / np.log(2 * h / (w/2))
        
        # 互電容
        c_m = c * (h / (h + s)) * 0.1
        
        # 自電感
        l = self.mu_0 * h / w
        
        # 互電感
        l_m = l * (h / (h + s)) * 0.15
        
        return c, c_m, l, l_m
    
    def calculate_next(self, c_m: float, c: float, l_m: float, l: float) -> float:
        """
        計算近端串擾 (NEXT) 係數
        
        Formula: NEXT = 1/4 * (Cm/C + Lm/L)
        """
        return 0.25 * (c_m / c + l_m / l)
    
    def calculate_fext(self, c_m: float, c: float, l_m: float, l: float, 
                      v: float, length: float, rise_time: float) -> float:
        """
        計算遠端串擾 (FEXT) 係數
        
        Formula: FEXT = (Len/RT) * 1/(2v) * (Cm/C - Lm/L)
        """
        k_f = (1 / (2 * v)) * (c_m / c - l_m / l)
        return (length / rise_time) * k_f
    
    def analyze_cable(self, cable: CableSpec, parallel_length_mm: float, 
                     num_channels: int, freq_ghz: float) -> Dict:
        """
        分析特定線材的串擾特性
        
        Returns:
            包含串擾分析結果的字典
        """
        # 基於規格估算
        base_isolation = abs(cable.isolation_db)
        
        # 長度因子
        length_factor = 20 * np.log10(parallel_length_mm / 100)
        
        # 頻率因子
        freq_factor = 20 * np.log10(freq_ghz / 6)
        
        # 估算NEXT和FEXT
        estimated_next = -(base_isolation - length_factor - freq_factor)
        estimated_fext = estimated_next - 6  # FEXT通常比NEXT差6dB
        
        # 計算所需flex數量
        num_flexes = np.ceil(num_channels / cable.channels_per_flex)
        
        # 熱負載計算
        thermal_4k = num_flexes * cable.thermal_load_4k
        thermal_10mk = num_flexes * cable.thermal_load_10mk
        
        return {
            'cable_name': f"{cable.manufacturer} {cable.model}",
            'estimated_next_db': estimated_next,
            'estimated_fext_db': estimated_fext,
            'num_flexes_required': int(num_flexes),
            'thermal_load_4k_uw': thermal_4k,
            'thermal_load_10mk_nw': thermal_10mk,
            'isolation_db': cable.isolation_db,
            'attenuation_at_freq': self._get_attenuation_at_freq(cable, freq_ghz)
        }
    
    def _get_attenuation_at_freq(self, cable: CableSpec, freq_ghz: float) -> float:
        """根據頻率獲取衰減值 (簡化插值)"""
        freqs = [6, 12, 18]
        atts = [cable.attenuation_6ghz, cable.attenuation_12ghz, cable.attenuation_18ghz]
        
        if freq_ghz <= 6:
            return atts[0]
        elif freq_ghz >= 18:
            return atts[2] * (freq_ghz / 18)  # 外推
        else:
            return np.interp(freq_ghz, freqs, atts)
    
    def plot_crosstalk_analysis(self, spacing_range: Tuple[float, float], 
                               cable_width: float, cable_height: float,
                               epsilon_r: float, length: float, rise_time: float):
        """
        繪製串擾分析圖表
        """
        spacings = np.linspace(spacing_range[0], spacing_range[1], 100)
        next_vals = []
        fext_vals = []
        
        v = self.c / np.sqrt(epsilon_r)
        
        for s in spacings:
            c, c_m, l, l_m = self.calculate_coupling_coefficients(
                s/1000, cable_height/1000, cable_width/1000, epsilon_r
            )
            next_vals.append(abs(self.calculate_next(c_m, c, l_m, l)))
            fext_vals.append(abs(self.calculate_fext(c_m, c, l_m, l, v, length/1000, rise_time/1e12)))
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # 串擾vs間距
        ax1.semilogy(spacings, next_vals, 'b-', label='NEXT', linewidth=2)
        ax1.semilogy(spacings, fext_vals, 'r-', label='FEXT', linewidth=2)
        ax1.set_xlabel('Line Spacing (mm)')
        ax1.set_ylabel('Crosstalk Coefficient')
        ax1.set_title('Crosstalk vs Line Spacing')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 頻率響應
        freqs = np.linspace(0.1, 40, 100)
        next_freq = [next_vals[len(next_vals)//2] * (1 + f/10) for f in freqs]
        fext_freq = [fext_vals[len(fext_vals)//2] * (f/6) for f in freqs]
        
        ax2.plot(freqs, 20*np.log10(np.abs(next_freq)), 'b-', label='NEXT', linewidth=2)
        ax2.plot(freqs, 20*np.log10(np.abs(fext_freq)), 'r-', label='FEXT', linewidth=2)
        ax2.set_xlabel('Frequency (GHz)')
        ax2.set_ylabel('Crosstalk (dB)')
        ax2.set_title('Frequency Response')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig

def get_cable_database() -> Dict[str, CableSpec]:
    """獲取線材資料庫"""
    cables = {}
    
    # Delft Circuits Cri/oFlex 1
    cables["Delft_CF1"] = CableSpec(
        manufacturer="Delft Circuits",
        model="Cri/oFlex 1 (CF1)",
        cable_type="Stripline Flex",
        impedance=50.0,
        freq_range="DC - 18 GHz",
        thickness=0.3,
        width=1.0,
        bend_radius=1.0,
        material="Polyimide + Silver (Ag)",
        dielectric="Kapton® Polyimide",
        attenuation_6ghz=22.0,
        attenuation_12ghz=39.0,
        attenuation_18ghz=55.0,
        crosstalk_db=-60.0,
        thermal_load_4k=250.0,
        thermal_load_10mk=40.0,
        channels_per_flex=8,
        isolation_db=-60.0,
        phase_stability="Excellent (Cryogenic rated)",
        operating_temp="4K - 400K",
        connectors=["SMA", "SMP", "Mini-SMP"],
        features=["Ultra-flexible", "Vibration isolation", "UHV compatible", "Low thermal load"]
    )
    
    # Delft Circuits Cri/oFlex 2
    cables["Delft_CF2"] = CableSpec(
        manufacturer="Delft Circuits",
        model="Cri/oFlex 2 (CF2)",
        cable_type="Stripline Flex",
        impedance=50.0,
        freq_range="DC - 26 GHz",
        thickness=0.3,
        width=2.0,
        bend_radius=2.0,
        material="Polyimide + Silver (Ag) or NbTi",
        dielectric="Kapton® Polyimide",
        attenuation_6ghz=11.0,
        attenuation_12ghz=16.0,
        attenuation_18ghz=24.0,
        crosstalk_db=-60.0,
        thermal_load_4k=250.0,
        thermal_load_10mk=40.0,
        channels_per_flex=8,
        isolation_db=-60.0,
        phase_stability="Excellent (Phase stable)",
        operating_temp="4K - 400K",
        connectors=["SMA", "SMP", "Mini-SMP", "SMPM"],
        features=["High density", "Integrated filtering", "Superconducting option", "Modular"]
    )
    
    # Rigetti Flex
    cables["Rigetti_Flex"] = CableSpec(
        manufacturer="Rigetti Computing",
        model="High-Density Flex",
        cable_type="Multi-channel Flex",
        impedance=50.0,
        freq_range="DC - 18 GHz",
        thickness=0.3,
        width=2.5,
        bend_radius=2.0,
        material="Polyimide + Superconducting",
        dielectric="Polyimide",
        attenuation_6ghz=10.0,
        attenuation_12ghz=18.0,
        attenuation_18ghz=28.0,
        crosstalk_db=-60.0,
        thermal_load_4k=200.0,
        thermal_load_10mk=35.0,
        channels_per_flex=10,
        isolation_db=-60.0,
        phase_stability="<0.1% amplitude crosstalk",
        operating_temp="10mK - 300K",
        connectors=["SMPM", "Custom"],
        features=["3D signaling", "Integrated components", "Scalable", "Low loss"]
    )
    
    # Radiall Flexible
    cables["Radiall_Flex"] = CableSpec(
        manufacturer="Radiall",
        model="Flex 5/50 S",
        cable_type="Coaxial Flexible",
        impedance=50.0,
        freq_range="DC - 4.5 GHz",
        thickness=2.6,
        width=2.6,
        bend_radius=30.0,
        material="Copper + Tin-dipped braid",
        dielectric="FEP/PTFE",
        attenuation_6ghz=0.26,
        attenuation_12ghz=0.48,
        attenuation_18ghz=0.75,
        crosstalk_db=-40.0,
        thermal_load_4k=500.0,
        thermal_load_10mk=100.0,
        channels_per_flex=1,
        isolation_db=-40.0,
        phase_stability="Good",
        operating_temp="-40°C to +105°C",
        connectors=["SMA", "N", "TNC"],
        features=["Military grade", "Hand-formable option", "Foam PTFE technology"]
    )
    
    # Rosenberger RFlex 047
    cables["Rosenberger_047"] = CableSpec(
        manufacturer="Rosenberger",
        model="RFlex 047",
        cable_type="Ultra-flexible Coaxial",
        impedance=50.0,
        freq_range="DC - 70 GHz",
        thickness=1.19,
        width=1.19,
        bend_radius=3.0,
        material="Silver-plated copper",
        dielectric="PTFE",
        attenuation_6ghz=0.45,
        attenuation_12ghz=0.85,
        attenuation_18ghz=1.2,
        crosstalk_db=-100.0,
        thermal_load_4k=400.0,
        thermal_load_10mk=80.0,
        channels_per_flex=1,
        isolation_db=-100.0,
        phase_stability="Excellent (Test grade)",
        operating_temp="-55°C to +125°C",
        connectors=["SMA", "2.92mm", "Mini-SMP", "WSMP", "1.85mm"],
        features=["Quick-Lock", "Phase matched", "High frequency", "Low loss"]
    )
    
    # Rosenberger RFlex 402
    cables["Rosenberger_402"] = CableSpec(
        manufacturer="Rosenberger",
        model="RFlex 402",
        cable_type="Flexible Coaxial",
        impedance=50.0,
        freq_range="DC - 60 GHz",
        thickness=3.58,
        width=3.58,
        bend_radius=8.0,
        material="Silver-plated copper",
        dielectric="PTFE",
        attenuation_6ghz=0.20,
        attenuation_12ghz=0.38,
        attenuation_18ghz=0.55,
        crosstalk_db=-100.0,
        thermal_load_4k=350.0,
        thermal_load_10mk=70.0,
        channels_per_flex=1,
        isolation_db=-100.0,
        phase_stability="Excellent",
        operating_temp="-55°C to +125°C",
        connectors=["SMA", "N", "2.92mm"],
        features=["Low loss", "High power", "Rugged", "Test & measurement"]
    )
    
    # Amphenol RF
    cables["Amphenol_SMP"] = CableSpec(
        manufacturer="Amphenol RF",
        model="SMP Flex Assembly",
        cable_type="Micro-coaxial Flexible",
        impedance=50.0,
        freq_range="DC - 26.5 GHz",
        thickness=1.0,
        width=1.0,
        bend_radius=5.0,
        material="Silver-plated copper",
        dielectric="PTFE",
        attenuation_6ghz=0.55,
        attenuation_12ghz=1.0,
        attenuation_18ghz=1.45,
        crosstalk_db=-60.0,
        thermal_load_4k=450.0,
        thermal_load_10mk=90.0,
        channels_per_flex=1,
        isolation_db=-60.0,
        phase_stability="Good",
        operating_temp="-65°C to +165°C",
        connectors=["SMP", "SMA", "2.92mm"],
        features=["High vibration resistant", "Push-on mating", "Quantum computing rated"]
    )
    
    return cables

def main():
    """主函數 - 示例用法"""
    print("=" * 60)
    print("量子計算柔性傳輸線串擾計算器")
    print("Quantum Computing Flex Cable Crosstalk Calculator")
    print("=" * 60)
    
    # 初始化計算器
    calc = CrosstalkCalculator()
    
    # 獲取線材資料庫
    cables = get_cable_database()
    
    print("\\n📋 可用線材:")
    for key, cable in cables.items():
        print(f"  {key}: {cable.manufacturer} {cable.model} ({cable.cable_type})")
    
    # 示例分析
    print("\\n🔍 示例分析 - Delft Cri/oFlex 2:")
    cable = cables["Delft_CF2"]
    result = calc.analyze_cable(cable, parallel_length_mm=200, num_channels=64, freq_ghz=6)
    
    print(f"  線材: {result['cable_name']}")
    print(f"  預估 NEXT: {result['estimated_next_db']:.1f} dB")
    print(f"  預估 FEXT: {result['estimated_fext_db']:.1f} dB")
    print(f"  所需 Flex 數量: {result['num_flexes_required']}")
    print(f"  4K 熱負載: {result['thermal_load_4k_uw']:.1f} µW")
    print(f"  10mK 熱負載: {result['thermal_load_10mk_nw']:.1f} nW")
    print(f"  6GHz 衰減: {result['attenuation_at_freq']:.2f} dB/m")
    
    # 繪製分析圖
    print("\\n📊 生成串擾分析圖表...")
    fig = calc.plot_crosstalk_analysis(
        spacing_range=(0.1, 5.0),
        cable_width=0.5,
        cable_height=0.3,
        epsilon_r=3.4,
        length=200,
        rise_time=100e-12
    )
    plt.savefig('crosstalk_analysis.png', dpi=150, bbox_inches='tight')
    print("  圖表已保存至: crosstalk_analysis.png")
    
    print("\\n✅ 分析完成!")

if __name__ == "__main__":
    main()
'''

# Save standalone module
with open('/mnt/kimi/output/crosstalk_calculator.py', 'w', encoding='utf-8') as f:
    f.write(standalone_code)

print("✅ 獨立計算模組已保存至: /mnt/kimi/output/crosstalk_calculator.py")
print("\n📋 使用方式:")
print("1. 作為模組導入: from crosstalk_calculator import CrosstalkCalculator, get_cable_database")
print("2. 直接執行: python crosstalk_calculator.py")
