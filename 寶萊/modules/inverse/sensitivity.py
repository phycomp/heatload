
# ========== 3. 敏感度分析模塊 ==========
"""
敏感度分析模塊
對藕合後的最優參數，逐一擾動并計算目標函數變化
"""
import numpy as np
from typing import Dict, List


class SensitivityAnalyzer:
    def __init__(self, cost_function: callable, param_names: List[str],
                 fitted_params: Dict[str, float], bounds: Dict[str, tuple]):
        """
        參數:
            cost_function: 目標函數 f(params_array) -> float
            param_names: 參數名列表
            fitted_params: 藕合後的最優參數值
            bounds: 各參數邊界
        """
        self.cost_fn = cost_function
        self.param_names = param_names
        self.fitted = fitted_params
        self.bounds = bounds
        self.base_cost = None

    def analyze(self, perturbation_pct: float = 0.05) -> List[dict]:
        """
        執行敏感度分析
        
        參數:
            perturbation_pct: 擾動百分比 (默認 5%)
        
        返回:
            List[dict]: 各參數的敏感度結果
        """
        # 基礎參數向量
        x_base = np.array([self.fitted[name] for name in self.param_names])
        self.base_cost = self.cost_fn(x_base)
        
        results = []
        
        for i, name in enumerate(self.param_names):
            bound_low, bound_high = self.bounds.get(name, (0, 100))
            param_range = bound_high - bound_low
            
            # 擾動量: 取 perturbation_pct 和絕對最小值的較大者
            delta = max(abs(x_base[i]) * perturbation_pct, param_range * 0.01)
            
            # 正向擾動
            x_plus = x_base.copy()
            x_plus[i] = min(x_base[i] + delta, bound_high)
            cost_plus = self.cost_fn(x_plus)
            
            # 負向擾動
            x_minus = x_base.copy()
            x_minus[i] = max(x_base[i] - delta, bound_low)
            cost_minus = self.cost_fn(x_minus)
            
            # 敏感度指標
            # 1. 絕對變化量
            delta_cost = max(abs(cost_plus - self.base_cost), abs(cost_minus - self.base_cost))
            
            # 2. 相對敏感度 (歸一化到參數範圍)
            normalized_sensitivity = delta_cost / (delta / param_range) if param_range > 0 else 0
            
            # 3. 方向性 (正向/負向哪個更敏感)
            direction = "+" if abs(cost_plus - self.base_cost) > abs(cost_minus - self.base_cost) else "-"
            
            results.append({
                "param": name,
                "fitted_value": float(x_base[i]),
                "delta": float(delta),
                "delta_cost": float(delta_cost),
                "normalized_sensitivity": float(normalized_sensitivity),
                "direction": direction,
                "cost_plus": float(cost_plus),
                "cost_minus": float(cost_minus),
                "base_cost": float(self.base_cost)
            })
        
        # 按敏感度排序
        results.sort(key=lambda x: x["normalized_sensitivity"], reverse=True)
        
        return results

    def get_sensitivity_ranking(self, perturbation_pct: float = 0.05) -> Dict[str, int]:
        """獲取參數敏感度排名"""
        results = self.analyze(perturbation_pct)
        return {r["param"]: i + 1 for i, r in enumerate(results)}

# with open(f"{base}/modules/inverse/sensitivity.py", "w", encoding="utf-8") as f:
    # f.write(sensitivity_py)

# print("✅ sensitivity.py 已創建")
