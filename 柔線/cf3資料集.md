# Update CSV file with CF3 data
import pandas as pd

# Read existing CSV
df = pd.read_csv('/mnt/kimi/output/quantum_flex_cable_specs.csv')

# Create CF3 row
cf3_data = {
    'Manufacturer': 'Delft Circuits',
    'Model': 'Cri/oFlex 3',
    'Type': 'Multi-channel Stripline Flex',
    'Impedance (Ω)': 50,
    'Freq Range (GHz)': 'DC-10',
    'Thickness (mm)': 0.3,
    'Width (mm)': 16.0,
    'Bend Radius (mm)': 5.0,
    'Attenuation 6GHz (dB/m)': 5.0,
    'Attenuation 12GHz (dB/m)': 9.0,
    'Attenuation 18GHz (dB/m)': 16.0,
    'Crosstalk (dB)': -40,
    'Thermal Load 4K (µW)': 125,
    'Thermal Load 10mK (nW)': 20,
    'Channels per Flex': 8,
    'Isolation (dB)': -40,
    'Material': 'Polyimide + Ag/NbTi',
    'Dielectric': 'Kapton',
    'Phase Stability': '<15 ps',
    'Operating Temp': '10mK - 400K',
    'Connectors': 'SMA, SMP, Tabbi®'
}

# Append to dataframe
df = pd.concat([df, pd.DataFrame([cf3_data])], ignore_index=True)

# Save back
df.to_csv('/mnt/kimi/output/quantum_flex_cable_specs.csv', index=False)
print("✅ Cri/oFlex 3 已加入 CSV 檔案")
print(f"\n📊 更新後的資料筆數: {len(df)}")
print("\n最新資料預覽:")
print(df[['Manufacturer', 'Model', 'Type', 'Freq Range (GHz)', 'Channels per Flex', 'Crosstalk (dB)']].tail(3))
