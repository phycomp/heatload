# Regenerate the comparison chart with proper CF3 data
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Use the updated CSV
df = pd.read_csv('/mnt/kimi/output/quantum_flex_cable_specs.csv')

# Create comprehensive comparison
fig = plt.figure(figsize=(18, 14))
gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.35)

# 1. Attenuation comparison
ax1 = fig.add_subplot(gs[0, :2])
x = np.arange(len(df))
width = 0.25
bars1 = ax1.bar(x - width, df['Attenuation 6GHz (dB/m)'], width, label='6 GHz', alpha=0.8, color='skyblue')
bars2 = ax1.bar(x, df['Attenuation 12GHz (dB/m)'], width, label='12 GHz', alpha=0.8, color='lightcoral')
bars3 = ax1.bar(x + width, df['Attenuation 18GHz (dB/m)'], width, label='18 GHz', alpha=0.8, color='lightgreen')

# Highlight CF3
cf3_indices = df[df['Model'].str.contains('CF3', na=False)].index
for idx in cf3_indices:
    bars1[idx].set_color('red')
    bars1[idx].set_alpha(0.9)
    ax1.annotate('CF3', xy=(idx, df.iloc[idx]['Attenuation 6GHz (dB/m)']), 
                xytext=(0, 10), textcoords='offset points', ha='center', 
                fontweight='bold', color='red', fontsize=9)

ax1.set_xlabel('Cable Model', fontsize=11)
ax1.set_ylabel('Attenuation (dB/m)', fontsize=11)
ax1.set_title('Attenuation Comparison by Frequency (CF3 Highlighted)', fontweight='bold', fontsize=13)
ax1.set_xticks(x)
ax1.set_xticklabels(df['Model'], rotation=45, ha='right', fontsize=9)
ax1.legend()
ax1.grid(True, alpha=0.3)

# 2. Thermal load comparison
ax2 = fig.add_subplot(gs[0, 2])
colors = ['red' if 'CF3' in str(m) else 'lightblue' for m in df['Model']]
bars = ax2.barh(df['Model'], df['Thermal Load 4K (µW)'], color=colors, alpha=0.7)
ax2.set_xlabel('Thermal Load (µW) @ 4K', fontsize=10)
ax2.set_title('4K Thermal Load\n(CF3 in Red)', fontweight='bold', fontsize=11)
ax2.grid(True, alpha=0.3)

# Add value labels for CF3
cf3_row = df[df['Model'].str.contains('CF3', na=False)]
if not cf3_row.empty:
    idx = cf3_row.index[0]
    ax2.text(cf3_row.iloc[0]['Thermal Load 4K (µW)'] + 10, idx, 
             f"{cf3_row.iloc[0]['Thermal Load 4K (µW)']:.0f} µW", 
             va='center', fontweight='bold', color='red', fontsize=9)

# 3. Crosstalk vs Channel Density
ax3 = fig.add_subplot(gs[1, 0])
scatter = ax3.scatter(df['Channels per Flex'], df['Crosstalk (dB)'], 
                     s=300, alpha=0.6, c=range(len(df)), cmap='viridis', edgecolors='black')
ax3.set_xlabel('Channels per Flex', fontsize=11)
ax3.set_ylabel('Crosstalk (dB)', fontsize=11)
ax3.set_title('Channel Density vs Crosstalk', fontweight='bold', fontsize=11)
ax3.grid(True, alpha=0.3)

# Annotate all points
for idx, row in df.iterrows():
    ax3.annotate(str(row['Model'])[:8], 
                (row['Channels per Flex'], row['Crosstalk (dB)']),
                xytext=(5, 5), textcoords='offset points', fontsize=7, alpha=0.8)

# 4. Bend Radius comparison
ax4 = fig.add_subplot(gs[1, 1])
colors = ['red' if 'CF3' in str(m) else 'lightgreen' for m in df['Model']]
ax4.bar(range(len(df)), df['Bend Radius (mm)'], color=colors, alpha=0.7)
ax4.set_ylabel('Bend Radius (mm)', fontsize=11)
ax4.set_title('Flexibility (Bend Radius)\n(CF3 in Red)', fontweight='bold', fontsize=11)
ax4.set_xticks(range(len(df)))
ax4.set_xticklabels(df['Model'], rotation=45, ha='right', fontsize=8)
ax4.grid(True, alpha=0.3)

# 5. CF3 Detailed Specs Box
ax5 = fig.add_subplot(gs[1, 2])
ax5.axis('off')
cf3_specs = df[df['Model'].str.contains('CF3', na=False)]
if not cf3_specs.empty:
    specs = cf3_specs.iloc[0]
    spec_text = f"""
╔══════════════════════════════════════╗
║     Cri/oFlex 3 Specifications       ║
╠══════════════════════════════════════╣
  Type: {specs['Type'][:25]:25}
  Frequency: {specs['Freq Range (GHz)']}
  Channels: {specs['Channels per Flex']} per flex
  Thickness: {specs['Thickness (mm)']} mm
  Bend Radius: {specs['Bend Radius (mm)']} mm

  Thermal Performance:
  • 4K Load: {specs['Thermal Load 4K (µW)']} µW/ch
  • 10mK Load: {specs['Thermal Load 10mK (nW)']} nW/ch

  Electrical Performance:
  • Atten @ 6GHz: {specs['Attenuation 6GHz (dB/m)']} dB/m
  • Crosstalk: {specs['Crosstalk (dB)']} dB
  • Phase Match: {specs['Phase Stability']}

  Key Features:
  ✓ End-to-end I/O (RT to mK)
  ✓ Integrated attenuators
  ✓ Vacuum feedthrough
  ✓ Distributed filtering
  ✓ Monolithic design
  ✓ 50% lower thermal load
╚══════════════════════════════════════╝
"""
    ax5.text(0.05, 0.5, spec_text, fontsize=8, family='monospace', 
             verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# 6. Multi-dimensional radar chart
ax6 = fig.add_subplot(gs[2, :], projection='polar')

# Select key cables for comparison
cables_to_compare = ['Cri/oFlex 2', 'Cri/oFlex 3', 'High-Density Flex', 'RFlex 047']
filtered_df = df[df['Model'].isin(cables_to_compare)]

categories = ['Channel\nDensity', 'Thermal\nEfficiency', 'High Freq\nPerf', 
              'Flexibility', 'Isolation', 'Integration']
N = len(categories)

angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

colors = ['blue', 'red', 'green', 'orange']
for idx, (_, cable) in enumerate(filtered_df.iterrows()):
    # Calculate normalized scores (0-10)
    scores = [
        min(cable['Channels per Flex'] * 2, 10),  # Channel Density
        10 - (cable['Thermal Load 4K (µW)'] / 50),  # Thermal Efficiency
        10 - (cable['Attenuation 6GHz (dB/m)'] / 6),  # High Freq Performance
        max(0, 10 - (cable['Bend Radius (mm)'] / 3)),  # Flexibility
        min(abs(cable['Crosstalk (dB)']) / 10, 10),  # Isolation
        8 if 'Integrated' in str(cable['Type']) or 'CF3' in str(cable['Model']) else 5  # Integration
    ]
    scores += scores[:1]
    
    label = cable['Model']
    if 'CF3' in label:
        label += ' ⭐'
    
    ax6.plot(angles, scores, 'o-', linewidth=2.5 if 'CF3' in cable['Model'] else 1.5, 
            label=label, color=colors[idx])
    ax6.fill(angles, scores, alpha=0.2 if 'CF3' in cable['Model'] else 0.1, 
            color=colors[idx])

ax6.set_xticks(angles[:-1])
ax6.set_xticklabels(categories, fontsize=10)
ax6.set_ylim(0, 10)
ax6.set_title('Multi-Dimensional Comparison\n(CF3 = Red, highlighted)', 
             fontweight='bold', pad=20, fontsize=12)
ax6.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0), fontsize=9)
ax6.grid(True)

plt.suptitle('Quantum Computing Flexible Cable Analysis - Cri/oFlex 3 Edition\n', 
             fontsize=16, fontweight='bold', y=0.98)

plt.savefig('/mnt/kimi/output/cable_comparison_with_cf3.png', dpi=300, bbox_inches='tight')
print("✅ 更新版比較圖表已保存: /mnt/kimi/output/cable_comparison_with_cf3.png")
plt.show()

# Print summary
print("\n" + "="*80)
print("📊 Cri/oFlex 3 整合完成")
print("="*80)
print(f"\n總線材數量: {len(df)}")
print("\n包含線材:")
for _, row in df.iterrows():
    marker = " ⭐ NEW" if "CF3" in str(row['Model']) else ""
    print(f"  • {row['Manufacturer']} {row['Model']}{marker}")
