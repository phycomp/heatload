# ========== 3. 材料库管理模块 ==========

"""
材料库管理模块
支持内建材料 + 用户自订材料
"""
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Optional, List


@dataclass
class Material:
    name: str
    dk: float
    df: float
    dk_freq_coeff: dict
    df_freq_model: dict
    copper_roughness: dict
    category: str

    def get_dk_at_freq(self, freq_ghz: float) -> float:
        """获取指定频率下的 Dk (频率相依)"""
        model = self.dk_freq_coeff.get("type", "constant")
        if model == "constant":
            return self.dk
        elif model == "djordjevic":
            # Djordjevic-Sarkar 模型简化版
            f_ref = self.dk_freq_coeff.get("f_ref_ghz", 1.0)
            dk_ref = self.dk_freq_coeff.get("value", self.dk)
            n = self.dk_freq_coeff.get("exponent", -0.02)
            return dk_ref * (freq_ghz / f_ref) ** n
        elif model == "linear":
            slope = self.dk_freq_coeff.get("slope", 0.0)
            f_ref = self.dk_freq_coeff.get("f_ref_ghz", 1.0)
            return self.dk + slope * (freq_ghz - f_ref)
        return self.dk

    def get_df_at_freq(self, freq_ghz: float) -> float:
        """获取指定频率下的 Df (频率相依)"""
        model = self.df_freq_model.get("type", "constant")
        if model == "constant":
            return self.df
        elif model == "djordjevic":
            f_ref = self.df_freq_model.get("f_ref_ghz", 1.0)
            df_ref = self.df_freq_model.get("value", self.df)
            n = self.df_freq_model.get("exponent", 0.005)
            return df_ref * (freq_ghz / f_ref) ** n
        elif model == "linear":
            slope = self.df_freq_model.get("slope", 0.0)
            f_ref = self.df_freq_model.get("f_ref_ghz", 1.0)
            return self.df + slope * (freq_ghz - f_ref)
        return self.df

    def get_roughness_model(self) -> str:
        return self.copper_roughness.get("model", "hammerstad")

    def get_roughness_rq(self) -> float:
        return self.copper_roughness.get("Rq_um", 1.5)

    def get_huray_params(self) -> dict:
        return {
            "Rq_um": self.copper_roughness.get("Rq_um", 1.5),
            "sphere_radius_um": self.copper_roughness.get("sphere_radius_um", 0.5)
        }

    def to_dict(self) -> dict:
        return {
            "dk": self.dk,
            "df": self.df,
            "dk_freq_coeff": self.dk_freq_coeff,
            "df_freq_model": self.df_freq_model,
            "copper_roughness": self.copper_roughness,
            "category": self.category
        }

    @classmethod
    def from_dict(cls, name: str, data: dict) -> "Material":
        return cls(
            name=name,
            dk=data.get("dk", 4.5),
            df=data.get("df", 0.02),
            dk_freq_coeff=data.get("dk_freq_coeff", {"type": "constant", "value": data.get("dk", 4.5)}),
            df_freq_model=data.get("df_freq_model", {"type": "constant", "value": data.get("df", 0.02)}),
            copper_roughness=data.get("copper_roughness", {"model": "hammerstad", "Rq_um": 1.5}),
            category=data.get("category", "standard")
        )


class MaterialLibrary:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self._materials: Dict[str, Material] = {}
        self._load_builtin()
        self._load_custom()

    def _load_builtin(self):
        path = self.data_dir / "materials.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for name, props in data.items():
                self._materials[name] = Material.from_dict(name, props)

    def _load_custom(self):
        path = self.data_dir / "materials_custom.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for name, props in data.items():
                self._materials[name] = Material.from_dict(name, props)

    def get(self, name: str) -> Optional[Material]:
        return self._materials.get(name)

    def list_all(self) -> List[str]:
        return sorted(self._materials.keys())

    def list_builtin(self) -> List[str]:
        path = self.data_dir / "materials.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return sorted(json.load(f).keys())
        return []

    def add_custom(self, name: str, material: Material):
        self._materials[name] = material
        self._save_custom()

    def delete_custom(self, name: str):
        if name in self._materials:
            del self._materials[name]
            self._save_custom()

    def _save_custom(self):
        builtin_names = set(self.list_builtin())
        custom = {k: v.to_dict() for k, v in self._materials.items() if k not in builtin_names}
        path = self.data_dir / "materials_custom.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(custom, f, indent=2, ensure_ascii=False)

#with open(f"{base}/modules/stackup/materials.py", "w", encoding="utf-8") as f:
#    f.write(materials_py)

# print("✅ materials.py 已创建")
