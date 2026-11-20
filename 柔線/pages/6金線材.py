from numpy import mean
from pandas import DataFrame, Timestamp
# 修正工具函數中的語法錯誤
# app/utils.py
# 工具函數

import json
import numpy as np
from typing import Dict, List, Any, Optional
import pandas as pd

def format_frequency(frequency_hz: float) -> str:
    """格式化頻率顯示"""
    if frequency_hz >= 1e9:
        return f"{frequency_hz/1e9:.2f} GHz"
    elif frequency_hz >= 1e6:
        return f"{frequency_hz/1e6:.2f} MHz"
    elif frequency_hz >= 1e3:
        return f"{frequency_hz/1e3:.2f} kHz"
    else:
        return f"{frequency_hz:.2f} Hz"

def format_power_db(value_db: float) -> str:
    """格式化功率/衰減顯示"""
    if value_db >= 0:
        return f"+{value_db:.2f} dB"
    else:
        return f"{value_db:.2f} dB"

def parse_attenuation_json(attenuation_db_m: Optional[Dict]) -> pd.DataFrame:
    """解析衰減 JSON 數據為 DataFrame"""
    if not attenuation_db_m:
        return pd.DataFrame()
    
    data = []
    for freq_str, att in attenuation_db_m.items():
        freq_hz = float(freq_str)
        data.append({
            'Frequency (Hz)': freq_hz,
            'Frequency': format_frequency(freq_hz),
            'Attenuation (dB/m)': float(att)
        })
    
    df = pd.DataFrame(data)
    df = df.sort_values('Frequency (Hz)')
    return df

def parse_heat_load_json(heat_load_uw: Optional[Dict]) -> pd.DataFrame:
    """解析熱負載 JSON 數據為 DataFrame"""
    if not heat_load_uw:
        return pd.DataFrame()
    
    data = []
    for temp_str, load in heat_load_uw.items():
        temp_k = float(temp_str)
        data.append({
            'Temperature (K)': temp_k,
            'Heat Load (μW)': float(load)
        })
    
    df = pd.DataFrame(data)
    df = df.sort_values('Temperature (K)')
    return df

def get_cable_specifications_table(cable) -> pd.DataFrame:
    """生成線材規格表格"""
    specs = {
        '參數類別': [],
        '參數名稱': [],
        '數值': [],
        '單位': []
    }
    
    # 幾何參數
    if cable.outer_diameter_mm:
        specs['參數類別'].append('幾何')
        specs['參數名稱'].append('外徑')
        specs['數值'].append(f"{float(cable.outer_diameter_mm):.3f}")
        specs['單位'].append('mm')
    
    if cable.inner_conductor_diameter_mm:
        specs['參數類別'].append('幾何')
        specs['參數名稱'].append('內導體直徑')
        specs['數值'].append(f"{float(cable.inner_conductor_diameter_mm):.3f}")
        specs['單位'].append('mm')
    
    if cable.thickness_mm:
        specs['參數類別'].append('幾何')
        specs['參數名稱'].append('厚度')
        specs['數值'].append(f"{float(cable.thickness_mm):.3f}")
        specs['單位'].append('mm')
    
    # 電氣參數
    if cable.impedance_ohm:
        specs['參數類別'].append('電氣')
        specs['參數名稱'].append('特性阻抗')
        specs['數值'].append(f"{float(cable.impedance_ohm):.1f}")
        specs['單位'].append('Ω')
    
    if cable.capacitance_pf_m:
        specs['參數類別'].append('電氣')
        specs['參數名稱'].append('電容')
        specs['數值'].append(f"{float(cable.capacitance_pf_m):.2f}")
        specs['單位'].append('pF/m')
    
    if cable.inductance_nh_m:
        specs['參數類別'].append('電氣')
        specs['參數名稱'].append('電感')
        specs['數值'].append(f"{float(cable.inductance_nh_m):.2f}")
        specs['單位'].append('nH/m')
    
    if cable.velocity_factor_percent:
        specs['參數類別'].append('電氣')
        specs['參數名稱'].append('速度因子')
        specs['數值'].append(f"{float(cable.velocity_factor_percent):.1f}")
        specs['單位'].append('%')
    
    # 機械參數
    if cable.min_bending_radius_mm:
        specs['參數類別'].append('機械')
        specs['參數名稱'].append('最小彎曲半徑')
        specs['數值'].append(f"{float(cable.min_bending_radius_mm):.1f}")
        specs['單位'].append('mm')
    
    if cable.weight_g_m:
        specs['參數類別'].append('機械')
        specs['參數名稱'].append('重量')
        specs['數值'].append(f"{float(cable.weight_g_m):.2f}")
        specs['單位'].append('g/m')
    
    # 屏蔽效能
    if cable.shielding_effectiveness_db:
        specs['參數類別'].append('屏蔽')
        specs['參數名稱'].append('屏蔽效能')
        specs['數值'].append(f"{float(cable.shielding_effectiveness_db):.1f}")
        specs['單位'].append('dB')
    
    if cable.near_end_crosstalk_db:
        specs['參數類別'].append('串擾')
        specs['參數名稱'].append('近端串擾 (NEXT)')
        specs['數值'].append(f"{float(cable.near_end_crosstalk_db):.1f}")
        specs['單位'].append('dB')
    
    if cable.far_end_crosstalk_db:
        specs['參數類別'].append('串擾')
        specs['參數名稱'].append('遠端串擾 (FEXT)')
        specs['數值'].append(f"{float(cable.far_end_crosstalk_db):.1f}")
        specs['單位'].append('dB')
    
    return pd.DataFrame(specs)

def validate_crosstalk_result(
    next_db: float, 
    fext_db: float,
    application_type: str = 'quantum_computing'
) -> Dict[str, Any]:
    """
    驗證串擾結果是否符合應用要求
    """
    # 不同應用的串擾要求
    requirements = {
        'quantum_computing': {'next_max': -60, 'fext_max': -70, 'description': '量子計算'},
        '5g_base_station': {'next_max': -50, 'fext_max': -60, 'description': '5G 基地台'},
        'data_center': {'next_max': -40, 'fext_max': -50, 'description': '資料中心'},
        'aerospace': {'next_max': -45, 'fext_max': -55, 'description': '航太應用'},
        'test_measurement': {'next_max': -50, 'fext_max': -60, 'description': '測試量測'}
    }
    
    req = requirements.get(application_type, requirements['quantum_computing'])
    
    next_pass = next_db <= req['next_max']
    fext_pass = fext_db <= req['fext_max']
    
    return {
        'application': req['description'],
        'next_requirement_db': req['next_max'],
        'fext_requirement_db': req['fext_max'],
        'next_actual_db': next_db,
        'fext_actual_db': fext_db,
        'next_pass': next_pass,
        'fext_pass': fext_pass,
        'overall_pass': next_pass and fext_pass,
        'margin_next_db': req['next_max'] - next_db,
        'margin_fext_db': req['fext_max'] - fext_db
    }

def generate_simulation_report(
    results: List[Any],
    cable_name: str,
    temperature_k: float
) -> str:
    """生成模擬報告文字"""
    next_values = [r.near_end_crosstalk_db for r in results]
    fext_values = [r.far_end_crosstalk_db for r in results]
    coupling_values = [r.coupling_coefficient for r in results]
    
    report = f"""
# 柔性傳輸線串擾模擬報告

## 模擬設定
- **線材型號**: {cable_name}
- **溫度**: {temperature_k} K
- **頻率範圍**: {format_frequency(results[0].frequency_hz)} ~ {format_frequency(results[-1].frequency_hz)}
- **計算點數**: {len(results)}

## 串擾性能摘要

| 參數 | 最小值 | 最大值 | 平均值 |
|------|--------|--------|--------|
| 近端串擾 (NEXT) | {min(next_values):.2f} dB | {max(next_values):.2f} dB | {np.mean(next_values):.2f} dB |
| 遠端串擾 (FEXT) | {min(fext_values):.2f} dB | {max(fext_values):.2f} dB | {np.mean(fext_values):.2f} dB |
| 耦合係數 | {min(coupling_values):.6f} | {max(coupling_values):.6f} | {np.mean(coupling_values):.6f} |

## 合規性檢查

"""
    
    # 檢查各種應用場景
    for app_type in ['quantum_computing', '5g_base_station', 'data_center']:
        mid_idx = len(results) // 2
        validation = validate_crosstalk_result(
            results[mid_idx].near_end_crosstalk_db,
            results[mid_idx].far_end_crosstalk_db,
            app_type
        )
        
        status = "✅ 通過" if validation['overall_pass'] else "❌ 未通過"
        report += f"- **{validation['application']}**: {status}\n"
        report += f"  - NEXT: {validation['next_actual_db']:.2f} dB (要求 ≤ {validation['next_requirement_db']} dB)\n"
        report += f"  - FEXT: {validation['fext_actual_db']:.2f} dB (要求 ≤ {validation['fext_requirement_db']} dB)\n"
    
    report += "\n---\n*報告生成時間: " + pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S') + "*"
    
    return report

#with open('/mnt/kimi/output/flexible_cable_crosstalk_sim/app/utils.py', 'w') as f:
#    f.write(utils_code)
#
#print("✅ 工具函數已建立")

