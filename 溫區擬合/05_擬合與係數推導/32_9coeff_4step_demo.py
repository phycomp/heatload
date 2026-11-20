import runpy
from pathlib import Path

# Run the shared Streamlit demo tool (topic-viz, distill docs, 4-step flow)
ROOT = Path(__file__).resolve().parents[2]
runpy.run_path(str(ROOT / "scripts" / "9coeff_4step_streamlit_demo.py"), run_name="__main__")
