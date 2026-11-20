import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

# 材料資料庫
materials_db = {
    "Delft Cri/oFlex® (Ag/Polyimide)": {
        "thermal_conductivity": lambda T: 0.5 if T < 10 else (2 if T < 100 else 10),
        "resistance": lambda T: 0.1 if T > 10 else 0.01,
        "attenuation": lambda T, f: 0.5 + 0.01*f,
        "crosstalk": -60,
        "flexible": True,
        "superconducting": False,
        "density": 256,
        "heat_load_per_channel": 4e-6,
        "color": "#FF6B6B"
    },
    "Maybell FLAX (NbTi)": {
        "thermal_conductivity": lambda T: 0.01 if T < 9.2 else 0.1,
        "resistance": lambda T: 0.001 if T < 9.2 else 10,
        "attenuation": lambda T, f: 0.1 if T < 9.2 else (1.5 + 0.05*f),
        "crosstalk": -40,
        "flexible": True,
        "superconducting": True,
        "tc": 9.2,
        "density": 128,
        "heat_load_per_channel": 5e-9,
        "color": "#4ECDC4"
    },
    "CryoCoax SC-086 (CuNi)": {
        "thermal_conductivity": lambda T: 0.15 if T < 10 else (1.5 if T < 100 else 20),
        "resistance": lambda T: 0.5,
        "attenuation": lambda T, f: 0.8 + 0.02*f,
        "crosstalk": -50,
        "flexible": False,
        "superconducting": False,
        "density": 32,
        "heat_load_per_channel": 10e-9,
        "color": "#45B7D1"
    },
    "CryoCoax SC-086 (NbTi-NbTi)": {
        "thermal_conductivity": lambda T: 0.005 if T < 9.2 else 0.05,
        "resistance": lambda T: 0.0001 if T < 9.2 else 5,
        "attenuation": lambda T, f: 0.05 if T < 9.2 else (1.0 + 0.03*f),
        "crosstalk": -45,
        "flexible": False,
        "superconducting": True,
        "tc": 9.2,
        "density": 32,
        "heat_load_per_channel": 2e-9,
        "color": "#96CEB4"
    },
    "Rosenberger 半剛性 (SS)": {
        "thermal_conductivity": lambda T: 0.009 if T < 10 else (0.1 if T < 100 else 1.2),
        "resistance": lambda T: 1.0,
        "attenuation": lambda T, f: 1.0 + 0.03*f,
        "crosstalk": -55,
        "flexible": False,
        "superconducting": False,
        "density": 16,
        "heat_load_per_channel": 50e-9,
        "color": "#FFEAA7"
    },
    "Rosenberger 半剛性 (NbTi)": {
        "thermal_conductivity": lambda T: 0.008 if T < 9.2 else 0.08,
        "resistance": lambda T: 0.0001 if T < 9.2 else 3,
        "attenuation": lambda T, f: 0.08 if T < 9.2 else (0.8 + 0.02*f),
        "crosstalk": -50,
        "flexible": False,
        "superconducting": True,
        "tc": 9.2,
        "density": 16,
        "heat_load_per_channel": 8e-9,
        "color": "#DDA0DD"
    }
}

def calculate_thermal_load(material, temps, length, n_channels):
    """計算各溫度級的熱負載"""
    mat = materials_db[material]
    heat_loads = []
    
    for i in range(len(temps)-1):
        T_hot = temps[i]
        T_cold = temps[i+1]
        T_avg = (T_hot + T_cold) / 2
        
        k = mat["thermal_conductivity"](T_avg)
        
        if mat.get("superconducting", False) and T_cold < mat.get("tc", 9.2):
            base_load = mat["heat_load_per_channel"] * (T_hot - T_cold) / 10
        else:
            base_load = mat["heat_load_per_channel"] * (T_hot - T_cold) / 0.1
        
        bundle_factor = np.ceil(n_channels / mat["density"])
        total_load = base_load * n_channels * length * bundle_factor
        
        heat_loads.append(max(total_load, 1e-12))
    
    return heat_loads

def calculate_crosstalk(material, n_channels, density, frequency=6):
    """計算鄰近通道串擾"""
    mat = materials_db[material]
    base_crosstalk = mat["crosstalk"]
    
    density_factor = n_channels / density
    crosstalk_db = base_crosstalk - 10 * np.log10(max(density_factor, 1))
    
    freq_factor = frequency / 6
    crosstalk_db -= 10 * np.log10(freq_factor)
    
    return crosstalk_db

def calculate_signal_integrity(material, temps, length, frequency=6):
    """計算訊號完整性指標"""
    mat = materials_db[material]
    T_qpu = temps[-1]
    
    att = mat["attenuation"](T_qpu, frequency) * length
    T_noise = T_qpu * (1 + 0.1 * att)
    SNR = 20 - att - 10 * np.log10(T_noise / 0.01)
    
    return {
        "attenuation_db": att,
        "noise_temp_K": T_noise,
        "SNR_db": SNR
    }

# 預設參數
temps = [300, 50, 4, 1, 0.1, 0.01]  # K
temp_labels = ['300K', '50K', '4K', '1K', '100mK', '10mK']
n_qubits = 100
n_channels = 100
cable_length = 0.3  # m
frequency = 6  # GHz

print("量子讀取架構模擬器 - 資料預處理完成")
print(f"量子位元數: {n_qubits}, 通道數: {n_channels}")
print(f"溫度級: {temp_labels}")
