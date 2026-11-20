# core/presets.py
import json, os

PRESET_FILE = "data/presets.json"

DEFAULT_PRESETS = {
    "Default": {"H1": 8.5, "Er1": 4.2, "W1": 12.0, "W2": 11.0, "S1": 9.0, "T1": 1.2},
    "Preset A": {"H1": 6.0, "Er1": 4.4, "W1": 8.0, "W2": 7.0, "S1": 6.0, "T1": 1.0},
}

def load_presets():
    if not os.path.exists(PRESET_FILE):
        save_presets(DEFAULT_PRESETS)
        return DEFAULT_PRESETS
    with open(PRESET_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_presets(presets):
    os.makedirs(os.path.dirname(PRESET_FILE), exist_ok=True)
    with open(PRESET_FILE, "w", encoding="utf-8") as f:
        json.dump(presets, f, indent=2, ensure_ascii=False)
