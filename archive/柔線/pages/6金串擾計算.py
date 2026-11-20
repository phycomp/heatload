from numpy import arccosh, log, log10, logspace, pi, sqrt
# 建立串擾計算核心模組
# app/crosstalk_calculator.py
# 柔性傳輸線串擾計算引擎

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class CableGeometry:
    """線材幾何參數"""
    diameter_mm: float
    spacing_mm: float
    length_m: float
    twist_pitch_mm: Optional[float] = None
    
@dataclass
class ElectricalParams:
    """電氣參數"""
    impedance_ohm: float = 50.0
    capacitance_pf_m: float = 100.0
    inductance_nh_m: float = 250.0
    attenuation_db_m: float = 1.0
    velocity_factor: float = 0.7
    
@dataclass
class CrosstalkResult:
    """串擾計算結果"""
    frequency_hz: float
    near_end_crosstalk_db: float
    far_end_crosstalk_db: float
    coupling_coefficient: float
    power_sum_crosstalk_db: float
    alien_crosstalk_db: float
    calculation_params: Dict

class FlexibleCableCrosstalkCalculator:
    """
    柔性傳輸線串擾計算器
    
    支援多種串擾機制：
    1. 電容耦合 (Capacitive Coupling)
    2. 電感耦合 (Inductive Coupling)  
    3. 近端串擾 (NEXT)
    4. 遠端串擾 (FEXT)
    5. 異類串擾 (Alien Crosstalk)
    """
    
    def __init__(self, temperature_k: float = 300.0):
        self.temperature_k = temperature_k
        self.speed_of_light = 299792458  # m/s
        
    def calculate_capacitive_coupling(
        self, 
        geometry: CableGeometry,
        params1: ElectricalParams,
        params2: ElectricalParams,
        frequency_hz: float
    ) -> float:
        """
        計算電容耦合係數
        
        使用平行線電容耦合模型：
        Cc = π * ε0 * εr * L / arccosh(S/D)
        其中 S 是線間距，D 是線徑
        """
        epsilon_0 = 8.854e-12  # F/m
        epsilon_r = 3.5  # 聚酰亞胺相對介電常數
        
        S = geometry.spacing_mm * 1e-3  # 轉換為米
        D = geometry.diameter_mm * 1e-3
        L = geometry.length_m
        
        if S <= D:
            return 0.0
            
        # 計算耦合電容
        coupling_capacitance = (
            np.pi * epsilon_0 * epsilon_r * L / 
            np.arccosh(S / D)
        )
        
        # 計算耦合係數
        Z0 = np.sqrt(params1.inductance_nh_m * 1e-9 / (params1.capacitance_pf_m * 1e-12))
        omega = 2 * np.pi * frequency_hz
        
        coupling_coeff = omega * coupling_capacitance * Z0
        
        return coupling_coeff
    
    def calculate_inductive_coupling(
        self,
        geometry: CableGeometry,
        params1: ElectricalParams,
        params2: ElectricalParams,
        frequency_hz: float
    ) -> float:
        """
        計算電感耦合係數
        
        使用平行線互感模型
        """
        mu_0 = 4 * np.pi * 1e-7  # H/m
        
        S = geometry.spacing_mm * 1e-3
        D = geometry.diameter_mm * 1e-3
        L = geometry.length_m
        
        # 計算互感
        mutual_inductance = (
            mu_0 * L / (2 * np.pi) * 
            np.log(S / D + np.sqrt((S/D)**2 - 1))
        )
        
        # 計算耦合係數
        Z0 = np.sqrt(params1.inductance_nh_m * 1e-9 / (params1.capacitance_pf_m * 1e-12))
        omega = 2 * np.pi * frequency_hz
        
        coupling_coeff = omega * mutual_inductance / Z0
        
        return coupling_coeff
    
    def calculate_near_end_crosstalk(
        self,
        geometry: CableGeometry,
        params1: ElectricalParams,
        params2: ElectricalParams,
        frequency_hz: float,
        source_attenuation_db: float = 0.0
    ) -> float:
        """
        計算近端串擾 (NEXT)
        
        NEXT = 20 * log10(|V_near / V_source|)
        """
        # 電容和電感耦合的疊加
        cap_coupling = self.calculate_capacitive_coupling(
            geometry, params1, params2, frequency_hz
        )
        ind_coupling = self.calculate_inductive_coupling(
            geometry, params1, params2, frequency_hz
        )
        
        # 總耦合係數（考慮相位關係）
        total_coupling = np.sqrt(cap_coupling**2 + ind_coupling**2)
        
        # 轉換為 dB
        if total_coupling > 0:
            next_db = 20 * np.log10(total_coupling)
        else:
            next_db = -120  # 最小值
            
        # 考慮衰減影響
        next_db += source_attenuation_db * 0.5  # 近端只受一半長度影響
        
        return next_db
    
    def calculate_far_end_crosstalk(
        self,
        geometry: CableGeometry,
        params1: ElectricalParams,
        params2: ElectricalParams,
        frequency_hz: float,
        source_attenuation_db: float = 0.0
    ) -> float:
        """
        計算遠端串擾 (FEXT)
        
        FEXT = NEXT - 20 * log10(2 * π * f * L * sqrt(LC))
        """
        next_db = self.calculate_near_end_crosstalk(
            geometry, params1, params2, frequency_hz, source_attenuation_db
        )
        
        # 計算傳播延遲
        L = geometry.length_m
        velocity = self.speed_of_light * params1.velocity_factor
        
        # FEXT 衰減因子
        fext_factor = 2 * np.pi * frequency_hz * L / velocity
        
        if fext_factor > 0:
            fext_db = next_db - 20 * np.log10(fext_factor)
        else:
            fext_db = next_db - 40  # 預設衰減
            
        # 考慮全長衰減
        fext_db += source_attenuation_db
        
        return fext_db
    
    def calculate_alien_crosstalk(
        self,
        bundle_configs: List[Tuple[CableGeometry, ElectricalParams]],
        frequency_hz: float
    ) -> float:
        """
        計算異類串擾 (Alien Crosstalk)
        
        來自不同線束間的串擾
        """
        if len(bundle_configs) < 2:
            return -120.0
            
        total_power = 0.0
        
        # 計算所有線束對之間的串擾功率和
        for i in range(len(bundle_configs)):
            for j in range(i+1, len(bundle_configs)):
                geo1, params1 = bundle_configs[i]
                geo2, params2 = bundle_configs[j]
                
                # 使用平均間距
                avg_spacing = (geo1.spacing_mm + geo2.spacing_mm) / 2
                avg_geo = CableGeometry(
                    diameter_mm=(geo1.diameter_mm + geo2.diameter_mm) / 2,
                    spacing_mm=avg_spacing,
                    length_m=max(geo1.length_m, geo2.length_m)
                )
                
                fext = self.calculate_far_end_crosstalk(
                    avg_geo, params1, params2, frequency_hz
                )
                
                # 功率疊加
                total_power += 10 ** (fext / 10)
        
        # 轉換回 dB
        alien_xt_db = 10 * np.log10(total_power) if total_power > 0 else -120.0
        
        return alien_xt_db
    
    def simulate_frequency_sweep(
        self,
        geometry: CableGeometry,
        params1: ElectricalParams,
        params2: ElectricalParams,
        freq_start_hz: float,
        freq_end_hz: float,
        num_points: int = 100,
        bundle_configs: Optional[List[Tuple[CableGeometry, ElectricalParams]]] = None
    ) -> List[CrosstalkResult]:
        """
        執行頻率掃描模擬
        """
        frequencies = np.logspace(
            np.log10(freq_start_hz), 
            np.log10(freq_end_hz), 
            num_points
        )
        
        results = []
        
        # 計算源端衰減
        source_attenuation = params1.attenuation_db_m * geometry.length_m
        
        for freq in frequencies:
            next_db = self.calculate_near_end_crosstalk(
                geometry, params1, params2, freq, source_attenuation
            )
            fext_db = self.calculate_far_end_crosstalk(
                geometry, params1, params2, freq, source_attenuation
            )
            
            # 計算耦合係數
            cap_coupling = self.calculate_capacitive_coupling(
                geometry, params1, params2, freq
            )
            ind_coupling = self.calculate_inductive_coupling(
                geometry, params1, params2, freq
            )
            coupling_coeff = np.sqrt(cap_coupling**2 + ind_coupling**2)
            
            # 功率和串擾
            power_sum = 10 * np.log10(10**(next_db/10) + 10**(fext_db/10))
            
            # 異類串擾
            if bundle_configs:
                alien_db = self.calculate_alien_crosstalk(bundle_configs, freq)
            else:
                alien_db = -120.0
                
            result = CrosstalkResult(
                frequency_hz=freq,
                near_end_crosstalk_db=next_db,
                far_end_crosstalk_db=fext_db,
                coupling_coefficient=coupling_coeff,
                power_sum_crosstalk_db=power_sum,
                alien_crosstalk_db=alien_db,
                calculation_params={
                    'temperature_k': self.temperature_k,
                    'geometry': {
                        'diameter_mm': geometry.diameter_mm,
                        'spacing_mm': geometry.spacing_mm,
                        'length_m': geometry.length_m,
                        'twist_pitch_mm': geometry.twist_pitch_mm
                    },
                    'electrical_params': {
                        'impedance_ohm': params1.impedance_ohm,
                        'capacitance_pf_m': params1.capacitance_pf_m,
                        'inductance_nh_m': params1.inductance_nh_m,
                        'attenuation_db_m': params1.attenuation_db_m
                    }
                }
            )
            
            results.append(result)
            
        return results
    
    def calculate_thermal_noise(
        self, 
        frequency_hz: float, 
        bandwidth_hz: float,
        resistance_ohm: float = 50.0
    ) -> float:
        """
        計算熱雜訊功率 (Johnson-Nyquist Noise)
        
        Pn = 4 * k * T * R * B
        """
        k_boltzmann = 1.380649e-23  # J/K
        
        noise_power = (
            4 * k_boltzmann * self.temperature_k * 
            resistance_ohm * bandwidth_hz
        )
        
        # 轉換為 dBm
        noise_dbm = 10 * np.log10(noise_power / 0.001)
        
        return noise_dbm
    
    def estimate_signal_integrity(
        self,
        geometry: CableGeometry,
        params: ElectricalParams,
        frequency_hz: float,
        input_power_dbm: float = 0.0
    ) -> Dict:
        """
        估算信號完整性
        """
        # 計算衰減
        total_attenuation = params.attenuation_db_m * geometry.length_m
        
        # 輸出功率
        output_power = input_power_dbm - total_attenuation
        
        # 熱雜訊
        noise_dbm = self.calculate_thermal_noise(frequency_hz, 1e6)
        
        # SNR
        snr_db = output_power - noise_dbm
        
        return {
            'input_power_dbm': input_power_dbm,
            'output_power_dbm': output_power,
            'total_attenuation_db': total_attenuation,
            'thermal_noise_dbm': noise_dbm,
            'snr_db': snr_db,
            'signal_integrity_ok': snr_db > 20  # 通常需要 > 20 dB SNR
        }

# 輔助函數：從資料庫 Cable 物件建立計算參數
def cable_to_electrical_params(cable) -> ElectricalParams:
    """將資料庫 Cable 物件轉換為 ElectricalParams"""
    return ElectricalParams(
        impedance_ohm=float(cable.impedance_ohm) if cable.impedance_ohm else 50.0,
        capacitance_pf_m=float(cable.capacitance_pf_m) if cable.capacitance_pf_m else 100.0,
        inductance_nh_m=float(cable.inductance_nh_m) if cable.inductance_nh_m else 250.0,
        attenuation_db_m=1.0,  # 預設值，應從 attenuation_db_m JSON 解析
        velocity_factor=float(cable.velocity_factor_percent) / 100 if cable.velocity_factor_percent else 0.7
    )

def cable_to_geometry(cable, length_m: float = 1.0, spacing_mm: float = 1.0) -> CableGeometry:
    """將資料庫 Cable 物件轉換為 CableGeometry"""
    return CableGeometry(
        diameter_mm=float(cable.outer_diameter_mm) if cable.outer_diameter_mm else 1.0,
        spacing_mm=spacing_mm,
        length_m=length_m,
        twist_pitch_mm=None
    )

#with open('/mnt/kimi/output/flexible_cable_crosstalk_sim/app/crosstalk_calculator.py', 'w') as f:
#    f.write(crosstalk_calculator_code)
#
#print("✅ 串擾計算核心模組已建立")
