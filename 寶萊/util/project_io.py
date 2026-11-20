# 8. utils/project_io.py
# 项目文件读写 (JSON)
import json
from datetime import datetime
from pathlib import Path


def save_project(filepath, data):
    """保存项目到 JSON"""
    project = {
        "version": "1.0",
        "created": datetime.now().isoformat(),
        "data": data
    }
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(project, f, indent=2, ensure_ascii=False)
    return True


def load_project(filepath):
    """从 JSON 加载项目"""
    with open(filepath, "r", encoding="utf-8") as f:
        project = json.load(f)
    return project.get("data", {})
