# core/history.py
from datetime import datetime

def add_history(state, nominal, cfg, taper_mode, unit, results, summary):
    if "history" not in state:
        state.history = []
    state.history.append({
        "time": datetime.now().isoformat(timespec="seconds"),
        "nominal": dict(nominal),
        "config": dict(cfg),
        "taper_mode": taper_mode,
        "unit": unit,
        "results": results,
        "summary": summary,
    })

def clear_history(state):
    state.history = []
