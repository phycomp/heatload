# io/json_export.py
import json

def to_json(nominal, cfg, taper_mode, unit, results, summary) -> str:
    return json.dumps({
        "nominal": nominal,
        "config": cfg,
        "taper_mode": taper_mode,
        "unit": unit,
        "results": results,
        "summary": summary,
    }, indent=2, ensure_ascii=False)
