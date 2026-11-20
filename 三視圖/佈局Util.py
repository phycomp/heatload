# ============================================================
# CF3 傳輸線佈局計算器 (LayoutCalculator)
# ============================================================

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


@dataclass
class LayerSpec:
    """層結構規格"""
    name: str           # 層名稱
    material: str       # 材料
    thickness_um: float # 厚度 (μm)
    is_signal: bool     # 是否為訊號層
    is_ground: bool     # 是否為接地層
    is_dielectric: bool # 是否為介電層


class CF3LayoutCalculator:
    """
    CF3 傳輸線佈局計算器
    
    基於 Delft cri/oFlex3 (CF3) 規格，計算：
    1. 層疊結構 (Stack-up)
    2. 傳輸線幾何尺寸
    3. Clearance 與間距
    4. 電氣性能參數
    """
    
    # ============================================================
    # 材料常數
    # ============================================================
    
    MATERIALS = {
        'Ag': {
            'name': 'Silver',
            'resistivity_300k': 1.59,      # μΩ·cm
            'resistivity_4k': 0.3,          # μΩ·cm (RRR > 100)
            'tc': None,                     # 非超導
        },
        'NbTi': {
            'name': 'Niobium-Titanium',
            'resistivity_300k': 50,         # μΩ·cm
            'resistivity_10k': 0.5,         # μΩ·cm
            'tc': 9.8,                      # K
            'nb_ratio': 47,                 # %
            'ti_ratio': 53,                 # %
        },
        'Polyimide': {
            'name': 'Polyimide',
            'epsilon_r': 3.4,               # 介電常數
            'thermal_conductivity': 0.12,   # W/m·K @ 300K
            'cte': 20,                      # ppm/K
            'density': 1.42,                # g/cm³
        }
    }
    
    # ============================================================
    # 層疊結構定義 (厚度單位: μm)
    # ============================================================
    
    LAYER_STACK = [
        LayerSpec('保護層 (上)', 'Polyimide', 15, False, False, True),
        LayerSpec('接地層 (上)', 'NbTi', 5, False, True, False),
        LayerSpec('介電層 (上)', 'Polyimide', 129, False, False, True),
        LayerSpec('訊號層', 'NbTi', 2, True, False, False),
        LayerSpec('介電層 (下)', 'Polyimide', 129, False, False, True),
        LayerSpec('接地層 (下)', 'NbTi', 5, False, True, False),
        LayerSpec('保護層 (下)', 'Polyimide', 15, False, False, True),
    ]
    
    # ============================================================
    # 初始化
    # ============================================================
    
    def __init__(self, 
                 n_channels: int = 8,
                 pitch_mm: float = 2.0,
                 signal_width_um: float = 35.0,
                 total_width_mm: Optional[float] = None,
                 conductor_material: str = 'NbTi',
                 target_impedance: float = 50.0,
                 use_5w_rule: bool = True,
                 use_10h_rule: bool = True):
        """
        初始化 CF3 佈局計算器
        
        Args:
            n_channels: 通道數 (預設 8)
            pitch_mm: 通道間距 (mm) (預設 2.0)
            signal_width_um: 訊號線寬度 (μm) (預設 35)
            total_width_mm: 目標總寬度 (mm) (若為 None 則自動計算)
            conductor_material: 導體材料 ('Ag' 或 'NbTi')
            target_impedance: 目標特性阻抗 (Ω)
            use_5w_rule: 是否套用 5W 規則
            use_10h_rule: 是否套用 10H 規則
        """
        self.n_channels = n_channels
        self.pitch_mm = pitch_mm
        self.signal_width_um = signal_width_um
        self.conductor_material = conductor_material
        self.target_impedance = target_impedance
        self.use_5w_rule = use_5w_rule
        self.use_10h_rule = use_10h_rule
        
        # 計算層疊結構
        self._calculate_stackup()
        
        # 計算幾何尺寸
        self._calculate_geometry(total_width_mm)
        
        # 計算 Clearance
        self._calculate_clearance()
        
        # 計算電氣性能
        self._calculate_electrical()
        
        # 計算熱性能
        self._calculate_thermal()
        
        # 計算阻抗
        self._calculate_impedance()
    
    # ============================================================
    # 層疊結構計算
    # ============================================================
    
    def _calculate_stackup(self):
        """計算層疊結構位置"""
        self.layer_positions = []
        cum_um = 0
        
        for i, layer in enumerate(self.LAYER_STACK):
            y_bot_um = cum_um
            y_top_um = cum_um + layer.thickness_um
            y_center_um = (y_bot_um + y_top_um) / 2
            
            self.layer_positions.append({
                'index': i,
                'name': layer.name,
                'material': layer.material,
                'thickness_um': layer.thickness_um,
                'thickness_mm': layer.thickness_um / 1000,
                'y_bot_um': y_bot_um,
                'y_top_um': y_top_um,
                'y_center_um': y_center_um,
                'y_bot_mm': y_bot_um / 1000,
                'y_top_mm': y_top_um / 1000,
                'y_center_mm': y_center_um / 1000,
                'is_signal': layer.is_signal,
                'is_ground': layer.is_ground,
                'is_dielectric': layer.is_dielectric,
            })
            cum_um += layer.thickness_um
        
        self.total_thickness_um = cum_um
        self.total_thickness_mm = cum_um / 1000
        
        # 找出訊號層索引
        self.signal_layer_idx = next(
            i for i, pos in enumerate(self.layer_positions) 
            if pos['is_signal']
        )
        self.signal_layer = self.layer_positions[self.signal_layer_idx]
        
        # 找出介電層
        self.dielectric_layers = [
            pos for pos in self.layer_positions 
            if pos['is_dielectric']
        ]
        self.dielectric_thickness_um = self.dielectric_layers[0]['thickness_um']
        self.dielectric_thickness_mm = self.dielectric_thickness_um / 1000
    
    # ============================================================
    # 幾何尺寸計算
    # ============================================================
    
    def _calculate_geometry(self, total_width_mm: Optional[float]):
        """計算幾何尺寸"""
        
        # 訊號線寬度
        self.signal_width_mm = self.signal_width_um / 1000
        
        # 基本總寬度 (不含 Clearance)
        self.base_total_width_mm = (self.n_channels - 1) * self.pitch_mm + self.signal_width_mm
        
        # 計算 5W 和 10H 規則值
        self.W = self.signal_width_mm
        self.H = self.dielectric_thickness_mm
        
        # 5W 規則: 通道間最小間距
        self.gap_5w = 5 * self.W if self.use_5w_rule else 0
        
        # 10H 規則: 邊緣最小 Clearance
        self.clearance_10h = 10 * self.H if self.use_10h_rule else 0
        
        # 計算建議總寬度
        self.recommended_total_width_mm = (
            self.base_total_width_mm + 2 * self.clearance_10h
        )
        
        # 設定目標總寬度
        if total_width_mm is not None:
            self.target_total_width_mm = total_width_mm
        else:
            self.target_total_width_mm = self.recommended_total_width_mm
        
        # 計算邊緣間距
        self.edge_margin_mm = (
            self.target_total_width_mm - self.base_total_width_mm
        ) / 2
        
        # 檢查是否符合 10H 規則
        self.meets_10h = self.edge_margin_mm >= self.clearance_10h
        
        # 計算通道間間距
        self.channel_gap_mm = self.pitch_mm - self.signal_width_mm
        self.meets_5w = self.channel_gap_mm >= self.gap_5w
        
        # 計算各通道位置
        self.channel_positions = []
        for i in range(self.n_channels):
            x_center = (i - (self.n_channels - 1) / 2) * self.pitch_mm
            x_left = x_center - self.signal_width_mm / 2
            x_right = x_center + self.signal_width_mm / 2
            self.channel_positions.append({
                'index': i,
                'x_center_mm': x_center,
                'x_left_mm': x_left,
                'x_right_mm': x_right,
            })
    
    # ============================================================
    # Clearance 計算
    # ============================================================
    
    def _calculate_clearance(self):
        """計算完整 Clearance 規格"""
        
        self.clearance = {
            # 基於 10H 規則
            '10h_min_mm': self.clearance_10h,
            '10h_min_um': self.clearance_10h * 1000,
            
            # 基於 5W 規則
            '5w_min_mm': self.gap_5w,
            '5w_min_um': self.gap_5w * 1000,
            
            # 實際設計值
            'edge_margin_mm': self.edge_margin_mm,
            'edge_margin_um': self.edge_margin_mm * 1000,
            'channel_gap_mm': self.channel_gap_mm,
            'channel_gap_um': self.channel_gap_mm * 1000,
            
            # 符合性檢查
            'meets_10h': self.meets_10h,
            'meets_5w': self.meets_5w,
        }
    
    # ============================================================
    # 電氣性能計算
    # ============================================================
    
    def _calculate_electrical(self):
        """計算電氣性能參數"""
        
        # 串擾估算 (基於通道間距)
        # 簡化模型: NEXT ≈ 20*log(K / (gap/ref_gap))
        ref_gap = 1.965  # CF3 標準間距 (mm)
        if self.channel_gap_mm > 0:
            crosstalk_factor = ref_gap / self.channel_gap_mm
            self.estimated_crosstalk_db = -40 + 20 * math.log10(crosstalk_factor)
        else:
            self.estimated_crosstalk_db = -40
        
        # 插入損耗估算 (簡化模型)
        # 基於 CF3 標準數據: 1.5 dB/m @ 6GHz @ 300K
        self.estimated_il_db_per_m = 1.5 * (self.signal_width_um / 35) ** (-0.5)
        
        # 傳播延遲
        self.propagation_delay_ns_per_m = 5.6  # Polyimide 典型值
        
        # 截止頻率 (簡化估算)
        self.cutoff_frequency_ghz = 18.0  # CF3 規格
    
    # ============================================================
    # 熱性能計算
    # ============================================================
    
    def _calculate_thermal(self):
        """計算熱性能參數"""
        
        # 基於 CF3 標準數據
        self.thermal = {
            'heat_load_ag_uw_per_ch': 125,      # μW/ch @ 4-40K
            'heat_load_nbti_nw_per_ch': 20,      # nW/ch @ 10-350mK
            'operating_temp_min_k': 0.001,       # 1 mK
            'operating_temp_max_k': 400,         # 400 K
        }
    
    # ============================================================
    # 阻抗計算
    # ============================================================
    
    def _calculate_impedance(self):
        """計算帶狀線阻抗"""
        
        # 帶狀線阻抗公式
        # Z0 = (60 / sqrt(εr)) * ln(4H / πW)
        
        epsilon_r = 3.4  # Polyimide
        H = self.dielectric_thickness_mm
        W = self.signal_width_mm
        
        if W > 0 and H > 0:
            z0 = (60 / math.sqrt(epsilon_r)) * math.log(4 * H / (math.pi * W))
        else:
            z0 = 50.0
        
        self.impedance = {
            'z0_ohm': z0,
            'target_ohm': self.target_impedance,
            'deviation_percent': (z0 - self.target_impedance) / self.target_impedance * 100,
            'epsilon_r': epsilon_r,
            'meets_spec': abs(z0 - self.target_impedance) <= 2.0,  # ±2Ω 規格
        }
    
    # ============================================================
    # 規格報告生成
    # ============================================================
    
    def get_summary(self) -> Dict:
        """獲取完整規格摘要"""
        
        return {
            'stackup': {
                'total_thickness_um': self.total_thickness_um,
                'total_thickness_mm': self.total_thickness_mm,
                'dielectric_thickness_um': self.dielectric_thickness_um,
                'signal_layer_thickness_um': self.signal_layer['thickness_um'],
                'layers': self.layer_positions,
            },
            'geometry': {
                'n_channels': self.n_channels,
                'pitch_mm': self.pitch_mm,
                'signal_width_um': self.signal_width_um,
                'signal_width_mm': self.signal_width_mm,
                'base_total_width_mm': self.base_total_width_mm,
                'target_total_width_mm': self.target_total_width_mm,
                'recommended_total_width_mm': self.recommended_total_width_mm,
                'edge_margin_mm': self.edge_margin_mm,
                'channel_gap_mm': self.channel_gap_mm,
                'channel_positions': self.channel_positions,
            },
            'clearance': self.clearance,
            'electrical': {
                'estimated_crosstalk_db': self.estimated_crosstalk_db,
                'estimated_il_db_per_m': self.estimated_il_db_per_m,
                'propagation_delay_ns_per_m': self.propagation_delay_ns_per_m,
                'cutoff_frequency_ghz': self.cutoff_frequency_ghz,
            },
            'thermal': self.thermal,
            'impedance': self.impedance,
        }
    
    def print_summary(self):
        """列印規格摘要"""
        summary = self.get_summary()
        輸入=str(summary)
        
        # 輸入+="=" * 70
        輸入+="CF3 傳輸線佈局規格摘要"
        輸入+="=" * 70
        
        輸入+="\n【層疊結構】"
        輸入+=f"  總厚度: {summary['stackup']['total_thickness_um']:.0f} μm ({summary['stackup']['total_thickness_mm']:.3f} mm)"
        輸入+=f"  介電層厚度: {summary['stackup']['dielectric_thickness_um']:.0f} μm"
        輸入+=f"  訊號層厚度: {summary['stackup']['signal_layer_thickness_um']:.0f} μm"
        
        輸入+="\n【幾何尺寸】"
        輸入+=f"  通道數: {summary['geometry']['n_channels']}"
        輸入+=f"  Pitch: {summary['geometry']['pitch_mm']:.3f} mm"
        輸入+=f"  訊號線寬度: {summary['geometry']['signal_width_um']:.0f} μm"
        輸入+=f"  基本總寬度: {summary['geometry']['base_total_width_mm']:.3f} mm"
        輸入+=f"  建議總寬度: {summary['geometry']['recommended_total_width_mm']:.3f} mm"
        輸入+=f"  目標總寬度: {summary['geometry']['target_total_width_mm']:.3f} mm"
        輸入+=f"  邊緣間距: {summary['geometry']['edge_margin_mm']:.3f} mm"
        
        輸入+="\n【Clearance】"
        輸入+=f"  10H 最小 Clearance: {summary['clearance']['10h_min_mm']:.3f} mm"
        輸入+=f"  5W 最小間距: {summary['clearance']['5w_min_mm']:.3f} mm"
        輸入+=f"  是否符合 10H: {summary['clearance']['meets_10h']}"
        輸入+=f"  是否符合 5W: {summary['clearance']['meets_5w']}"
        
        輸入+="\n【電氣性能】"
        輸入+=f"  估算串擾: {summary['electrical']['estimated_crosstalk_db']:.1f} dB"
        輸入+=f"  估算插入損耗: {summary['electrical']['estimated_il_db_per_m']:.2f} dB/m"
        輸入+=f"  傳播延遲: {summary['electrical']['propagation_delay_ns_per_m']:.1f} ns/m"
        
        輸入+="\n【阻抗】"
        輸入+=f"  目標阻抗: {summary['impedance']['target_ohm']:.1f} Ω"
        輸入+=f"  計算阻抗: {summary['impedance']['z0_ohm']:.1f} Ω"
        輸入+=f"  偏差: {summary['impedance']['deviation_percent']:.1f}%"
        輸入+=f"  符合規格: {summary['impedance']['meets_spec']}"
        
        # 輸入+="\n" + "=" * 70
        return 輸入

