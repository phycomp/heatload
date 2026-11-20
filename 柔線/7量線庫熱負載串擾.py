from matplotlib.pyplot import cm, savefig, subplots, tight_layout, figure
from streamlit import pyplot, sidebar, radio, text_input
from numpy import arange, linspace
from pandas import DataFrame

# Create a comprehensive comparison chart
#import matplotlib.pyplot as plt
#import numpy as np
#import pandas as pd

# Cable data based on research
cable_data = {
    'Manufacturer': ['Delft Circuits', 'Delft Circuits', 'Rigetti', 'Radiall', 'Rosenberger', 'Rosenberger', 'Amphenol RF'],
    'Model': ['Cri/oFlex 1', 'Cri/oFlex 2', 'High-Density Flex', 'Flex 5/50 S', 'RFlex 047', 'RFlex 402', 'SMP Flex'],
    'Type': ['Stripline Flex', 'Stripline Flex', 'Multi-channel Flex', 'Coaxial', 'Coaxial', 'Coaxial', 'Micro-coaxial'],
    'Impedance (Ω)': [50, 50, 50, 50, 50, 50, 50],
    'Freq Range (GHz)': ['DC-18', 'DC-26', 'DC-18', 'DC-4.5', 'DC-70', 'DC-60', 'DC-26.5'],
    'Thickness (mm)': [0.3, 0.3, 0.3, 2.6, 1.19, 3.58, 1.0],
    'Width (mm)': [1.0, 2.0, 2.5, 2.6, 1.19, 3.58, 1.0],
    'Bend Radius (mm)': [1.0, 2.0, 2.0, 30.0, 3.0, 8.0, 5.0],
    'Attenuation 6GHz (dB/m)': [22.0, 11.0, 10.0, 0.26, 0.45, 0.20, 0.55],
    'Attenuation 12GHz (dB/m)': [39.0, 16.0, 18.0, 0.48, 0.85, 0.38, 1.0],
    'Attenuation 18GHz (dB/m)': [55.0, 24.0, 28.0, 0.75, 1.2, 0.55, 1.45],
    'Crosstalk (dB)': [-60, -60, -60, -40, -100, -100, -60],
    'Thermal Load 4K (µW)': [250, 250, 200, 500, 400, 350, 450],
    'Thermal Load 10mK (nW)': [40, 40, 35, 100, 80, 70, 90],
    'Channels per Flex': [8, 8, 10, 1, 1, 1, 1],
    'Isolation (dB)': [-60, -60, -60, -40, -100, -100, -60],
    'Material': ['Polyimide+Ag', 'Polyimide+Ag/NbTi', 'Polyimide+SC', 'Cu+Sn braid', 'Ag-plated Cu', 'Ag-plated Cu', 'Ag-plated Cu'],
    'Dielectric': ['Kapton', 'Kapton', 'Polyimide', 'FEP/PTFE', 'PTFE', 'PTFE', 'PTFE'],
    'Phase Stability': ['Excellent', 'Excellent', 'Excellent', 'Good', 'Excellent', 'Excellent', 'Good'],
    'Operating Temp': ['4K-400K', '4K-400K', '10mK-300K', '-40°C to +105°C', '-55°C to +125°C', '-55°C to +125°C', '-65°C to +165°C'],
    'Connectors': ['SMA,SMP', 'SMA,SMP,SMPM', 'SMPM,Custom', 'SMA,N,TNC', 'SMA,2.92mm,WSMP', 'SMA,N,2.92mm', 'SMP,SMA,2.92mm']
}

資框 = DataFrame(cable_data)
資框
# Create visualization
fig, axes = subplots(2, 2, figsize=(16, 12))
fig.suptitle('Quantum Computing Flexible Cable Comparison', fontsize=16, fontweight='bold')

MENU, 表單=[], ['衰減', '熱負載', '彎曲串擾', '通道密度']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
if menu==len(表單): #
  pass
elif menu==MENU[3]: #
  # 4. Channel density comparison
  #ax4 = axes[1, 1]
  fig=figure(figsize=(10, 8))
  ax4 = fig.add_subplot(2, 2, 2)
  colors = cm.Set3(linspace(0, 1, len(資框)))
  ax4.bar(資框['Model'], 資框['Channels per Flex'], color=colors, alpha=0.8)
  ax4.set_xlabel('Cable Model')
  ax4.set_ylabel('Channels per Flex')
  ax4.set_title('Channel Density Comparison')
  ax4.set_xticklabels(資框['Model'], rotation=45, ha='right', fontsize=8)
  ax4.grid(True, alpha=0.3)
  pyplot(fig)
elif menu==MENU[2]: #
  # 3. Bend radius vs Crosstalk
  fig=figure(figsize=(10, 8))
  ax3 = fig.add_subplot(2, 2, 1)
  #ax3 = axes[1, 0]
  scatter = ax3.scatter(資框['Bend Radius (mm)'], 資框['Crosstalk (dB)'], s=資框['Channels per Flex']*50, alpha=0.6, c=range(len(資框)), cmap='viridis')
  ax3.set_xlabel('Bend Radius (mm)')
  ax3.set_ylabel('Crosstalk (dB)')
  ax3.set_title('Bend Radius vs Crosstalk (bubble size = channels/flex)')
  ax3.grid(True, alpha=0.3)
  for i, txt in enumerate(資框['Model']):
      ax3.annotate(txt, (資框['Bend Radius (mm)'].iloc[i], 資框['Crosstalk (dB)'].iloc[i]), fontsize=7, ha='center')
  pyplot(fig)
elif menu==MENU[1]: #
  # 2. Thermal load comparison
  fig=figure(figsize=(10, 8))
  ax2 = fig.add_subplot(2, 2, 2)
  #ax2 = axes[0, 1]
  ax2.barh(資框['Model'], 資框['Thermal Load 4K (µW)'], alpha=0.7, label='4K Stage')
  ax2.set_xlabel('Thermal Load (µW)')
  ax2.set_title('Thermal Load at 4K Stage')
  ax2.grid(True, alpha=0.3)
  pyplot(fig)
elif menu==MENU[0]: #衰減
  # 1. Attenuation comparison
  fig=figure(figsize=(10, 8))
  ax1 = fig.add_subplot(2, 2, 1)
  #ax1 = axes[0, 0]
  x = arange(len(資框))
  width = 0.25
  ax1.bar(x - width, 資框['Attenuation 6GHz (dB/m)'], width, label='6 GHz', alpha=0.8)
  ax1.bar(x, 資框['Attenuation 12GHz (dB/m)'], width, label='12 GHz', alpha=0.8)
  ax1.bar(x + width, 資框['Attenuation 18GHz (dB/m)'], width, label='18 GHz', alpha=0.8)
  ax1.set_xlabel('Cable Model')
  ax1.set_ylabel('Attenuation (dB/m)')
  ax1.set_title('Attenuation vs Frequency')
  ax1.set_xticks(x)
  ax1.set_xticklabels(資框['Model'], rotation=45, ha='right', fontsize=8)
  ax1.legend()
  ax1.grid(True, alpha=0.3)
  pyplot(fig)
#tight_layout()
#savefig('/mnt/kimi/output/cable_comparison_chart.png', dpi=300, bbox_inches='tight')
#print("✅ 比較圖表已保存至: /mnt/kimi/output/cable_comparison_chart.png")

# Save detailed data to CSV
#資框.to_csv('/mnt/kimi/output/quantum_flex_cable_specs.csv', index=False, encoding='utf-8')
#print("✅ 詳細規格表已保存至: /mnt/kimi/output/quantum_flex_cable_specs.csv")

# Display summary
#print("\n📊 線材規格摘要:")
#print(資框[['Manufacturer', 'Model', 'Type', 'Freq Range (GHz)', 'Channels per Flex', 'Crosstalk (dB)']].to_string(index=False))

