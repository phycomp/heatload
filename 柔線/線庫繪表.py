from matplotlib.pyplot import figure, savefig, show, suptitle
from numpy import arange, pi
from pandas import read_csv
# Create a comprehensive comparison visualization including CF3
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Reload updated data
df = pd.read_csv('/mnt/kimi/output/quantum_flex_cable_specs.csv')

# Create comprehensive comparison chart with CF3
fig = plt.figure(figsize=(16, 12))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# 1. Attenuation comparison (including CF3)
ax1 = fig.add_subplot(gs[0, :2])
x = np.arange(len(df))
width = 0.25
ax1.bar(x - width, df['Attenuation 6GHz (dB/m)'], width, label='6 GHz', alpha=0.8, color='skyblue')
ax1.bar(x, df['Attenuation 12GHz (dB/m)'], width, label='12 GHz', alpha=0.8, color='lightcoral')
ax1.bar(x + width, df['Attenuation 18GHz (dB/m)'], width, label='18 GHz', alpha=0.8, color='lightgreen')
ax1.set_xlabel('Cable Model')
ax1.set_ylabel('Attenuation (dB/m)')
ax1.set_title('Attenuation Comparison (including Cri/oFlex 3)', fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(df['Model'], rotation=45, ha='right', fontsize=9)
ax1.legend()
ax1.grid(True, alpha=0.3)
# Highlight CF3
cf3_idx = df[df['Model'] == 'Cri/oFlex 3'].index[0]
ax1.axvline(x=cf3_idx, color='red', linestyle='--', alpha=0.5, label='CF3')

# 2. Thermal load comparison
ax2 = fig.add_subplot(gs[0, 2])
colors = ['red' if 'CF3' in m else 'lightblue' for m in df['Model']]
ax2.barh(df['Model'], df['Thermal Load 4K (µW)'], color=colors, alpha=0.7)
ax2.set_xlabel('Thermal Load (µW) @ 4K')
ax2.set_title('4K Thermal Load', fontweight='bold')
ax2.grid(True, alpha=0.3)

# 3. Crosstalk vs Channel Density
ax3 = fig.add_subplot(gs[1, 0])
scatter = ax3.scatter(df['Channels per Flex'], df['Crosstalk (dB)'], 
                     s=200, alpha=0.6, c=range(len(df)), cmap='viridis')
ax3.set_xlabel('Channels per Flex')
ax3.set_ylabel('Crosstalk (dB)')
ax3.set_title('Channel Density vs Crosstalk', fontweight='bold')
ax3.grid(True, alpha=0.3)
# Annotate CF3
cf3_row = df[df['Model'] == 'Cri/oFlex 3'].iloc[0]
ax3.annotate('CF3', (cf3_row['Channels per Flex'], cf3_row['Crosstalk (dB)']),
            xytext=(10, 10), textcoords='offset points', fontsize=10, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))

# 4. Bend Radius comparison
ax4 = fig.add_subplot(gs[1, 1])
colors = ['red' if 'CF3' in m else 'lightgreen' for m in df['Model']]
ax4.bar(df['Model'], df['Bend Radius (mm)'], color=colors, alpha=0.7)
ax4.set_ylabel('Bend Radius (mm)')
ax4.set_title('Flexibility (Bend Radius)', fontweight='bold')
ax4.set_xticklabels(df['Model'], rotation=45, ha='right', fontsize=8)
ax4.grid(True, alpha=0.3)

# 5. CF3 Detailed Specs
ax5 = fig.add_subplot(gs[1, 2])
ax5.axis('off')
cf3_specs = df[df['Model'] == 'Cri/oFlex 3'].iloc[0]
spec_text = f"""
Cri/oFlex 3 Specifications
{'='*30}

Type: {cf3_specs['Type']}
Frequency: {cf3_specs['Freq Range (GHz)']}
Channels: {cf3_specs['Channels per Flex']} per flex
Thickness: {cf3_specs['Thickness (mm)']} mm
Bend Radius: {cf3_specs['Bend Radius (mm)']} mm

Thermal Performance:
• 4K Load: {cf3_specs['Thermal Load 4K (µW)']} µW/ch
• 10mK Load: {cf3_specs['Thermal Load 10mK (nW)']} nW/ch

Electrical Performance:
• Attenuation @ 6GHz: {cf3_specs['Attenuation 6GHz (dB/m)']} dB/m
• Crosstalk: {cf3_specs['Crosstalk (dB)']} dB
• Phase Matching: {cf3_specs['Phase Stability']}

Key Features:
• End-to-end I/O (RT to mK)
• Integrated attenuators
• Vacuum feedthrough
• Distributed filtering
• Monolithic design
"""
ax5.text(0.1, 0.5, spec_text, fontsize=9, family='monospace', 
         verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# 6. Multi-dimensional radar chart for CF3 comparison
ax6 = fig.add_subplot(gs[2, :], projection='polar')

# Select cables for radar comparison
cables_to_compare = ['Cri/oFlex 2', 'Cri/oFlex 3', 'High-Density Flex', 'RFlex 047']
filtered_df = df[df['Model'].isin(cables_to_compare)]

categories = ['Channel Density', 'Thermal Efficiency', 'High Freq Performance', 
              'Flexibility', 'Isolation']
N = len(categories)

# Calculate scores (normalized 0-10)
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

colors = ['blue', 'red', 'green', 'orange']
for idx, (_, cable) in enumerate(filtered_df.iterrows()):
    scores = [
        min(cable['Channels per Flex'] / 2, 10),  # Channel Density
        10 - (cable['Thermal Load 4K (µW)'] / 50),  # Thermal Efficiency
        10 - (cable['Attenuation 6GHz (dB/m)'] / 5),  # High Freq Performance
        10 - (cable['Bend Radius (mm)'] / 3),  # Flexibility
        abs(cable['Crosstalk (dB)']) / 10  # Isolation
    ]
    scores += scores[:1]
    
    ax6.plot(angles, scores, 'o-', linewidth=2, label=cable['Model'], color=colors[idx])
    ax6.fill(angles, scores, alpha=0.15, color=colors[idx])

ax6.set_xticks(angles[:-1])
ax6.set_xticklabels(categories, fontsize=10)
ax6.set_ylim(0, 10)
ax6.set_title('Multi-Dimensional Comparison (CF3 highlighted)', fontweight='bold', pad=20)
ax6.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
ax6.grid(True)

plt.suptitle('Quantum Computing Flexible Cable Analysis - Cri/oFlex 3 Edition', 
             fontsize=16, fontweight='bold', y=0.98)

plt.savefig('/mnt/kimi/output/cable_comparison_with_cf3.png', dpi=300, bbox_inches='tight')
print("✅ 更新版比較圖表已保存: /mnt/kimi/output/cable_comparison_with_cf3.png")
plt.show()
