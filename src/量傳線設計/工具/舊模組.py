"""載入舊版模組的工具（遷移過渡期使用）。"""
import importlib.util
import sys
import os

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

def 載入舊模組(相對路徑: str):
    """依 repo 相對路徑載入模組，回傳 module 或 None。"""
    full = os.path.join(_REPO, 相對路徑)
    if not os.path.exists(full):
        return None
    name = os.path.splitext(os.path.basename(full))[0]
    spec = importlib.util.spec_from_file_location(f"legacy_{name}", full)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    # 避免重複執行：若已載入則回傳
    if f"legacy_{name}" in sys.modules:
        return sys.modules[f"legacy_{name}"]
    try:
        spec.loader.exec_module(mod)
        sys.modules[f"legacy_{name}"] = mod
        return mod
    except Exception as e:
        print(f"[legacy] 載入 {相對路徑} 失敗: {e}")
        return None
