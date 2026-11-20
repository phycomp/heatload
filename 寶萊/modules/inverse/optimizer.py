# ========== 2. 逆工程優化器 ==========

"""
逆工程優化器
從 S 參數反推物理參數

自動算法選擇策略:
  Stage 1: least_squares (快速初值)
  Stage 2: minimize L-BFGS-B (精修)
  Stage 3: differential_evolution (全局優化, fallback)
"""
import numpy as np
from numpy import sqrt, pi, log10
from scipy.optimize import least_squares, minimize, differential_evolution
from typing import Dict, List, Tuple, Callable, Optional

# 導入損耗模型
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from modules.stackup.loss_models import total_insertion_loss, return_loss
from modules.impedance.formulas import microstrip_z0


class InverseEngineer:
    def __init__(self, freqs_ghz: np.ndarray, s21_db_measured: np.ndarray,
                 s11_db_measured: Optional[np.ndarray] = None,
                 trace_length_m: float = 0.1,
                 fixed_params: dict = None):
        """
        參數:
            freqs_ghz: 測量頻率點 (GHz)
            s21_db_measured: 實測 S21 (dB)
            s11_db_measured: 實測 S11 (dB), 可選
            trace_length_m: 線長 (m)
            fixed_params: 固定參數 dict {h_mm, t_mm, er_guess, ...}
        """
        self.freqs = np.asarray(freqs_ghz)
        self.s21_db = np.asarray(s21_db_measured)
        self.s11_db = np.asarray(s11_db_measured) if s11_db_measured is not None else None
        self.L = trace_length_m
        self.fixed = fixed_params or {}

        # 默認固定參數
        self.h_mm = self.fixed.get("h_mm", 1.6)
        self.t_mm = self.fixed.get("t_mm", 0.035)
        self.roughness_model = self.fixed.get("roughness_model", "hammerstad")

    def _model_s21(self, params: np.ndarray, param_names: List[str]) -> np.ndarray:
        """
        根據當前參數計算理論 S21 (dB)
        
        params 順序對應 param_names:
        支持: "dk", "df", "w_mm", "Rq_um", "h_mm"
        """
        p = dict(zip(param_names, params))
        
        # 獲取參數值（優化變量或固定值）
        dk = p.get("dk", self.fixed.get("dk", 4.5))
        df = p.get("df", self.fixed.get("df", 0.02))
        w = p.get("w_mm", self.fixed.get("w_mm", 0.3))
        h = p.get("h_mm", self.h_mm)
        t = self.t_mm
        Rq = p.get("Rq_um", self.fixed.get("Rq_um", 1.5))
        
        # 計算阻抗和有效介電常數
        z0, e_eff = microstrip_z0(w, h, t, dk, 0.0)
        
        # 計算各頻率點的 IL
        s21_model = []
        for f in self.freqs:
            il = total_insertion_loss(f, w, t, h, dk, df, z0, e_eff,
                                       self.roughness_model, {"Rq_um": Rq}, self.L)
            s21_model.append(-il["IL_total_db"])  # S21 = -IL
        
        return np.array(s21_model)

    def _model_s11(self, params: np.ndarray, param_names: List[str]) -> np.ndarray:
        """計算理論 S11 (dB)"""
        p = dict(zip(param_names, params))
        w = p.get("w_mm", self.fixed.get("w_mm", 0.3))
        h = p.get("h_mm", self.h_mm)
        t = self.t_mm
        dk = p.get("dk", self.fixed.get("dk", 4.5))
        
        z0, _ = microstrip_z0(w, h, t, dk, 0.0)
        s11_model = []
        for f in self.freqs:
            rl = return_loss(f, z0, 50.0, 50.0)
            # RL 是正值，S11 是負值
            s11_model.append(-rl)
        return np.array(s11_model)

    def _residuals(self, params: np.ndarray, param_names: List[str],
                   weights: dict = None) -> np.ndarray:
        """殘差向量 (用于 least_squares)"""
        if weights is None:
            weights = {"s21": 1.0, "s11": 0.5}
        
        residuals = []
        
        # S21 殘差
        s21_model = self._model_s21(params, param_names)
        residuals.extend(weights["s21"] * (self.s21_db - s21_model))
        
        # S11 殘差 (如果有)
        if self.s11_db is not None:
            s11_model = self._model_s11(params, param_names)
            residuals.extend(weights["s11"] * (self.s11_db - s11_model))
        
        return np.array(residuals)

    def _cost_function(self, params: np.ndarray, param_names: List[str]) -> float:
        """目標函數 (用于 minimize)"""
        res = self._residuals(params, param_names)
        return np.sum(res ** 2)

    def optimize(self, param_names: List[str],
                 bounds: Dict[str, Tuple[float, float]],
                 initial_guess: Dict[str, float] = None,
                 auto_algorithm: bool = True) -> dict:
        """
        執行逆工程優化
        
        參數:
            param_names: 要優化的參數名列表 ["dk", "df", "w_mm", ...]
            bounds: 各參數邊界 {"dk": (3.0, 6.0), ...}
            initial_guess: 初始猜測 {"dk": 4.5, ...}
            auto_algorithm: 是否自動選擇算法
        
        返回:
            dict: 優化結果
        """
        n_params = len(param_names)
        
        # 構建初始猜測
        if initial_guess is None:
            initial_guess = {}
        x0 = []
        lb = []
        ub = []
        for name in param_names:
            guess = initial_guess.get(name, self.fixed.get(name, self._default_guess(name)))
            x0.append(guess)
            b = bounds.get(name, self._default_bounds(name))
            lb.append(b[0])
            ub.append(b[1])
        
        x0 = np.array(x0)
        lb = np.array(lb)
        ub = np.array(ub)
        
        result = {
            "param_names": param_names,
            "initial_guess": dict(zip(param_names, x0.tolist())),
            "stages": []
        }
        
        if auto_algorithm:
            # ===== Stage 1: least_squares (快速初值) =====
            try:
                res1 = least_squares(
                    lambda x: self._residuals(x, param_names),
                    x0, bounds=(lb, ub), method="trf",
                    max_nfev=500, ftol=1e-8, xtol=1e-8
                )
                x0 = res1.x
                cost1 = np.sum(res1.cost)
                result["stages"].append({
                    "stage": 1, "algorithm": "least_squares",
                    "cost": float(cost1), "nfev": res1.nfev,
                    "success": res1.success, "x": x0.tolist()
                })
            except Exception as e:
                result["stages"].append({"stage": 1, "error": str(e)})
            
            # ===== Stage 2: L-BFGS-B 精修 =====
            try:
                res2 = minimize(
                    lambda x: self._cost_function(x, param_names),
                    x0, method="L-BFGS-B",
                    bounds=list(zip(lb, ub)),
                    options={"maxiter": 1000, "ftol": 1e-9}
                )
                x0 = res2.x
                cost2 = res2.fun
                result["stages"].append({
                    "stage": 2, "algorithm": "L-BFGS-B",
                    "cost": float(cost2), "nfev": res2.nfev,
                    "success": res2.success, "x": x0.tolist()
                })
                
                # 判斷是否需要 Stage 3
                need_global = False
                if not res2.success:
                    need_global = True
                # 如果參數在邊界上，可能陷入局部最優
                for i, name in enumerate(param_names):
                    if abs(x0[i] - lb[i]) < 0.01 * (ub[i] - lb[i]) or \\
                       abs(x0[i] - ub[i]) < 0.01 * (ub[i] - lb[i]):
                        need_global = True
                        break
                
                # ===== Stage 3: differential_evolution (全局優化) =====
                if need_global:
                    res3 = differential_evolution(
                        lambda x: self._cost_function(x, param_names),
                        bounds=list(zip(lb, ub)),
                        maxiter=200, tol=1e-7, polish=True,
                        workers=-1, updating="deferred"
                    )
                    x0 = res3.x
                    result["stages"].append({
                        "stage": 3, "algorithm": "differential_evolution",
                        "cost": float(res3.fun), "nfev": res3.nfev,
                        "success": res3.success, "x": x0.tolist()
                    })
            except Exception as e:
                result["stages"].append({"stage": 2, "error": str(e)})
        else:
            # 僅使用 L-BFGS-B
            res = minimize(
                lambda x: self._cost_function(x, param_names),
                x0, method="L-BFGS-B",
                bounds=list(zip(lb, ub)),
                options={"maxiter": 1000}
            )
            x0 = res.x
            result["stages"].append({
                "stage": 1, "algorithm": "L-BFGS-B",
                "cost": float(res.fun), "nfev": res.nfev,
                "success": res.success, "x": x0.tolist()
            })
        
        # 最終結果
        fitted = dict(zip(param_names, x0.tolist()))
        result["fitted_params"] = fitted
        result["final_cost"] = float(self._cost_function(x0, param_names))
        
        # 計算藕合曲線
        result["s21_fitted"] = self._model_s21(x0, param_names).tolist()
        if self.s11_db is not None:
            result["s11_fitted"] = self._model_s11(x0, param_names).tolist()
        
        # 殘差
        result["s21_residual"] = (self.s21_db - np.array(result["s21_fitted"])).tolist()
        
        return result

    def _default_guess(self, param_name: str) -> float:
        defaults = {"dk": 4.5, "df": 0.02, "w_mm": 0.3, "Rq_um": 1.5, "h_mm": 1.6}
        return defaults.get(param_name, 1.0)

    def _default_bounds(self, param_name: str) -> Tuple[float, float]:
        bounds = {
            "dk": (2.0, 10.0),
            "df": (0.0001, 0.1),
            "w_mm": (0.01, 5.0),
            "Rq_um": (0.1, 5.0),
            "h_mm": (0.05, 5.0)
        }
        return bounds.get(param_name, (0.0, 100.0))

# with open(f"{base}/modules/inverse/optimizer.py", "w", encoding="utf-8") as f:
    # f.write(optimizer_py)

# print("✅ optimizer.py 已創建")
