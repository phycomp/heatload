# Create specific crosstalk and thermal load calculation for CF3
print("="*80)
print("Cri/oFlex 3 串擾與熱負載詳細分析")
print("="*80)

# CF3 Specifications
cf3_specs = {
    'model': 'Cri/oFlex 3',
    'channels_per_flex': 8,
    'channel_pitch_mm': 2.0,  # 2mm pitch between channels
    'crosstalk_db_200mm': -40,  # at 200mm length
    'thermal_load_4k_uw': 125,  # per channel
    'thermal_load_10mk_nw': 20,  # per channel
    'length_4k_m': 0.4,  # typical length for 4K calculation
    'length_10mk_m': 0.2,  # typical length for 10mK calculation
}

print("\n📊 基本規格:")
print(f"  • 每Flex通道數: {cf3_specs['channels_per_flex']}")
print(f"  • 通道間距: {cf3_specs['channel_pitch_mm']} mm")
print(f"  • 典型4K段長度: {cf3_specs['length_4k_m']*1000} mm")
print(f"  • 典型10mK段長度: {cf3_specs['length_10mk_m']*1000} mm")

# Crosstalk calculation for different lengths
print("\n" + "="*80)
print("🔬 串擾分析 (Crosstalk Analysis)")
print("="*80)

lengths = [100, 200, 300, 400, 500]  # mm
print("\n耦合長度 vs 串擾水平:")
print(f"{'長度 (mm)':<12} {'預估 NEXT (dB)':<20} {'預估 FEXT (dB)':<20} {'評估':<20}")
print("-" * 72)

for L in lengths:
    # Crosstalk increases with length (20dB/decade approximation)
    # Reference: -40 dB at 200mm
    next_db = cf3_specs['crosstalk_db_200mm'] - 20 * np.log10(L / 200)
    fext_db = next_db - 6  # FEXT typically 6dB worse
    
    if next_db < -60:
        assessment = "✅ 優良 (量子計算適用)"
    elif next_db < -40:
        assessment = "⚠️ 中等 (一般應用)"
    else:
        assessment = "❌ 較差 (需改善)"
    
    print(f"{L:<12} {next_db:<20.1f} {fext_db:<20.1f} {assessment:<20}")

# Thermal load calculation for different system sizes
print("\n" + "="*80)
print("🌡️ 熱負載分析 (Thermal Load Analysis)")
print("="*80)

system_configs = [
    {'name': '小型系統', 'qubits': 50, 'lines_per_qubit': 4},
    {'name': '中型系統', 'qubits': 100, 'lines_per_qubit': 4},
    {'name': '大型系統', 'qubits': 1000, 'lines_per_qubit': 4},
    {'name': '超大型系統', 'qubits': 4000, 'lines_per_qubit': 4},
]

print("\n系統規模 vs 熱負載估算:")
print(f"{'系統類型':<12} {'量子比特':<12} {'總線路':<12} {'Flex數':<10} {'4K熱負載':<15} {'10mK熱負載':<15}")
print("-" * 90)

for config in system_configs:
    total_lines = config['qubits'] * config['lines_per_qubit']
    num_flexes = np.ceil(total_lines / cf3_specs['channels_per_flex'])
    
    # Calculate total thermal load
    total_thermal_4k = num_flexes * cf3_specs['channels_per_flex'] * cf3_specs['thermal_load_4k_uw'] / 1000  # mW
    total_thermal_10mk = num_flexes * cf3_specs['channels_per_flex'] * cf3_specs['thermal_load_10mk_nw'] / 1000  # µW
    
    print(f"{config['name']:<12} {config['qubits']:<12} {total_lines:<12} {int(num_flexes):<10} "
          f"{total_thermal_4k:<15.2f} mW {total_thermal_10mk:<15.2f} µW")

# Comparison with other cables
print("\n" + "="*80)
print("📈 與其他線材的比較")
print("="*80)

comparison_data = {
    'Cri/oFlex 3': {'channels': 8, 'thermal_4k': 125, 'xtalk': -40, 'freq': 'DC-10GHz'},
    'Cri/oFlex 2': {'channels': 8, 'thermal_4k': 250, 'xtalk': -60, 'freq': 'DC-26GHz'},
    'Rigetti Flex': {'channels': 10, 'thermal_4k': 200, 'xtalk': -60, 'freq': 'DC-18GHz'},
    'Rosenberger 047': {'channels': 1, 'thermal_4k': 400, 'xtalk': -100, 'freq': 'DC-70GHz'},
}

print("\n線材比較 (每通道):")
print(f"{'線材型號':<20} {'通道數':<10} {'4K熱負載':<15} {'串擾':<15} {'頻率範圍':<15}")
print("-" * 75)

for name, specs in comparison_data.items():
    marker = " ← CF3" if "CF3" in name else ""
    print(f"{name:<20} {specs['channels']:<10} {specs['thermal_4k']:<15} µW "
          f"{specs['xtalk']:<15} dB {specs['freq']:<15}{marker}")

# CF3 advantages
print("\n" + "="*80)
print("✨ Cri/oFlex 3 主要優勢")
print("="*80)
print("""
1. 【端到端整合】
   • 從室溫到毫開爾文的單一柔性基板
   • 整合真空穿透、熱錨點和微波濾波器
   • 減少連接點，提高可靠性

2. 【熱性能優異】
   • 每通道4K熱負載僅125 µW (比CF2降低50%)
   • 每通道10mK熱負載僅20 nW
   • 可選超導NbTi材料進一步降低損耗

3. 【高密度設計】
   • 每Flex 8通道，通道間距2mm
   • 單一loader可支援256通道 (BlueFors XLDsl)
   • 整個系統可擴展至1536通道

4. 【整合信號調節】
   • 內建分散式衰減器 (典型20dB @ 4K)
   • 整合低通濾波器和紅外濾波器
   • 減少外部元件數量10倍

5. 【機械可靠性】
   • 最小彎曲半徑5mm
   • 抗熱循環設計
   • 單片式結構，無微波斷點

6. 【應用優化】
   • Flux Bias線: DC-1GHz，優化偏置電流
   • Microwave Drive線: 6-8GHz，量子比特控制
   • Read-out線: 整合放大器和隔離器
""")

print("="*80)
