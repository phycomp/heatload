# ========== 4. 叠构模板管理模块 ==========

"""
叠构模板管理模块
加载 Polar 风格的叠构模板
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class StackupTemplate:
    def __init__(self, name: str, category: str, data: dict):
        self.name = name
        self.category = category
        self.description = data.get("description", "")
        self.layers = data.get("layers", [])
        self.total_thickness_um = data.get("total_thickness_um", 0)

    def get_signal_layers(self) -> List[dict]:
        return [l for l in self.layers if l.get("type") in ("signal",)]

    def get_plane_layers(self) -> List[dict]:
        return [l for l in self.layers if l.get("type") in ("plane",)]

    def get_dielectric_layers(self) -> List[dict]:
        return [l for l in self.layers if l.get("type") in ("prepreg", "core", "adhesive")]

    def get_layer_stack(self) -> List[dict]:
        return self.layers

    def get_total_thickness_mm(self) -> float:
        return self.total_thickness_um / 1000.0

    def get_layer_thickness_mm(self, layer_idx: int) -> float:
        if 0 <= layer_idx < len(self.layers):
            return self.layers[layer_idx].get("thickness_um", 0) / 1000.0
        return 0.0

    def get_layer_material_props(self, layer_idx: int) -> dict:
        if 0 <= layer_idx < len(self.layers):
            layer = self.layers[layer_idx]
            return {
                "dk": layer.get("dk", 4.5),
                "df": layer.get("df", 0.02),
                "material_name": layer.get("material", "FR-4")
            }
        return {"dk": 4.5, "df": 0.02, "material_name": "FR-4"}

    def find_signal_layer_position(self, layer_name: str) -> int:
        for i, layer in enumerate(self.layers):
            if layer.get("name") == layer_name and layer.get("type") == "signal":
                return i
        return -1

    def get_dielectric_thickness_above(self, signal_layer_idx: int) -> float:
        """获取信号层上方的介质总厚度 (mm)"""
        thickness_um = 0
        for i in range(signal_layer_idx - 1, -1, -1):
            if self.layers[i].get("type") in ("prepreg", "core", "adhesive"):
                thickness_um += self.layers[i].get("thickness_um", 0)
            elif self.layers[i].get("type") in ("signal", "plane"):
                break
        return thickness_um / 1000.0

    def get_dielectric_thickness_below(self, signal_layer_idx: int) -> float:
        """获取信号层下方的介质总厚度 (mm)"""
        thickness_um = 0
        for i in range(signal_layer_idx + 1, len(self.layers)):
            if self.layers[i].get("type") in ("prepreg", "core", "adhesive"):
                thickness_um += self.layers[i].get("thickness_um", 0)
            elif self.layers[i].get("type") in ("signal", "plane"):
                break
        return thickness_um / 1000.0

    def get_ground_reference(self, signal_layer_idx: int) -> Optional[int]:
        """找到信号层最近的参考平面层索引"""
        # 向上找
        for i in range(signal_layer_idx - 1, -1, -1):
            if self.layers[i].get("type") == "plane":
                return i
        # 向下找
        for i in range(signal_layer_idx + 1, len(self.layers)):
            if self.layers[i].get("type") == "plane":
                return i
        return None

    def to_dict(self) -> dict:
        return {
            "description": self.description,
            "layers": self.layers,
            "total_thickness_um": self.total_thickness_um
        }


class TemplateLibrary:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self._templates: Dict[str, StackupTemplate] = {}
        self._load_templates()

    def _load_templates(self):
        path = self.data_dir / "stackup_templates.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for category, templates in data.items():
                for name, template_data in templates.items():
                    self._templates[f"{category}/{name}"] = StackupTemplate(name, category, template_data)

    def get(self, full_name: str) -> Optional[StackupTemplate]:
        return self._templates.get(full_name)

    def list_all(self) -> List[str]:
        return sorted(self._templates.keys())

    def list_by_category(self, category: str) -> List[str]:
        return sorted([k for k in self._templates.keys() if k.startswith(f"{category}/")])

    def get_categories(self) -> List[str]:
        categories = set()
        for k in self._templates.keys():
            cat = k.split("/")[0]
            categories.add(cat)
        return sorted(categories)

    def get_template_names(self, category: str) -> List[str]:
        return sorted([k.split("/")[1] for k in self._templates.keys() if k.startswith(f"{category}/")])

#with open(f"{base}/modules/stackup/templates.py", "w", encoding="utf-8") as f:
#    f.write(templates_py)
#
#print("✅ templates.py 已创建")
