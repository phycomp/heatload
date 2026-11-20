import json
from pathlib import Path
import streamlit as st

st.set_page_config(page_title='polyfit 可靠度驗證', layout='wide')
st.title('polyfit 參數可靠度驗證 (16柔性八階擬合)')

root = Path(__file__).resolve().parents[2]
md_path = root / 'docs' / 'polyfit_可靠度驗證.md'
json_path = root / 'docs' / 'polyfit_可靠度驗證.json'

if md_path.exists():
    st.markdown(md_path.read_text(encoding='utf-8'))
else:
    st.warning(f'找不到報告: {md_path}，請先執行 scripts/validate_polyfit_reliability.py')

if json_path.exists():
    with st.expander('原始驗證 JSON'):
        data = json.loads(json_path.read_text(encoding='utf-8'))
        st.json(data)

st.info('重點: 16柔性八階擬合的 Kapton/NbTi 係數由模擬資料+np.polyfit 產生，對 noise/seed 與 Tc 轉變區敏感；NbTi 無固定 coeffs（heatload-coff-nist 標記 runtime_polyfit）。熱負載主計算請使用具來源之 NIST 9 係數材料。')
