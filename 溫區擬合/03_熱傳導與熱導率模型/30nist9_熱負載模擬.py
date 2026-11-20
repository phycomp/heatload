import sys, os
from pathlib import Path

# use shared helper in same folder (D4=A, D5=A)
sys.path.insert(0, str(Path(__file__).parent))
import _nist9_共用 as n9  # noqa: E402

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title='NIST9 熱負載模擬', layout='wide')
st.title('NIST 9 係數 熱負載模擬 (heatload-coff-nist 引擎)')
st.caption('單一真相來源: ~/.opencode/skills/heatload-coff-nist/scripts (coeff_data.py, thermal_load.py)')

mats_all = n9.list_materials()
mat_names = [m['name'] for m in mats_all]
k_mats = [m['name'] for m in mats_all if m.get('category','k(T)') == 'k(T)']
if not k_mats:
    k_mats = mat_names

with st.sidebar:
    st.subheader('材料/係數')
    mat = st.selectbox('材料 (κ(T))', k_mats, index=k_mats.index('Polyimide (Kapton)') if 'Polyimide (Kapton)' in k_mats else 0)
    m = n9.get_material(mat)
    st.write({'equation_type': m.get('equation_type'), 'T_low': m.get('t_low'), 'T_high': m.get('t_high'), 'category': m.get('category')})
    st.caption(m.get('note',''))
    extrap = st.checkbox('低溫外推 (T < T_low 以 k~T^alpha)', value=False)
    st.subheader('幾何/溫區')
    stages_s = st.text_input('溫區 stages (K, 高->低, 逗號分隔)', '300,50,4,1,0.1,0.01')
    width = st.number_input('寬 width', value=0.15, format='%.6f')
    thickness = st.number_input('厚 thickness', value=1.0, format='%.6f')
    area_units = st.selectbox('面積單位 (width*thickness)', ['mil','m'], index=0)
    length_s = st.text_input('各段長度 length (m, 逗號; 1值=全段同長)', '0.3')
    st.subheader('RF/衰減')
    pin = st.number_input('P_in (W)', value=1e-6, format='%.3e')
    atten_s = st.text_input('各段衰減 alpha dB (逗號; 1值=全段同值)', '0,3,6,6,6')

def parse_floats(s):
    return [float(x.strip()) for x in s.split(',') if x.strip()!='']

stages = parse_floats(stages_s)
lengths = parse_floats(length_s)
attens = parse_floats(atten_s)

tabs = st.tabs(['κ(T) 曲線', '積分 ∫κdT', '多溫區熱負載模擬', '材料比較', '參數掃描模擬'])

with tabs[0]:
    tmin = st.number_input('T_min (K)', value=float(m.get('t_low') or 1.0), key='k_tmin')
    tmax = st.number_input('T_max (K)', value=float(m.get('t_high') or 300.0), key='k_tmax')
    cur = n9.k_curve(material=mat, t_min=tmin, t_max=tmax, n=400, extrapolate=extrap)
    fig, ax = plt.subplots()
    ax.loglog(cur['T'], cur['k'])
    ax.set_xlabel('T (K)'); ax.set_ylabel('κ(T) [W/m/K]'); ax.grid(True, which='both', alpha=0.3)
    ax.set_title(mat)
    st.pyplot(fig)
    st.dataframe(pd.DataFrame({'T(K)': cur['T'], 'k(W/m/K)': cur['k']}), height=250)

with tabs[1]:
    tc = st.number_input('T_cold (K)', value=min(stages) if stages else 4.0, key='i_tc')
    th = st.number_input('T_hot (K)', value=max(stages) if stages else 300.0, key='i_th')
    ic = n9.integral_curve(material=mat, t_cold=tc, t_hot=th, n=300, extrapolate=extrap)
    fig, ax = plt.subplots()
    ax.semilogx(ic['T'], ic['integral'])
    ax.set_xlabel('T (K)'); ax.set_ylabel('∫ κ(T)dT (W/m)'); ax.grid(True, which='both', alpha=0.3)
    st.pyplot(fig)

with tabs[2]:
    geom = {'width': width, 'thickness': thickness, 'length': lengths[0] if len(lengths)==1 else lengths, 'area_units': area_units}
    try:
        res = n9.calculate_thermal_load(material=mat, stages=stages, geometry=geom, attenuation=attens[0] if len(attens)==1 else attens, pin=pin, extrapolate_low_t=extrap)
        c1,c2,c3 = st.columns(3)
        c1.metric('total_load_w', f"{res['total_load_w']:.4e}")
        c2.metric('solid_conduction_w', f"{res['solid_conduction_w']:.4e}")
        c3.metric('attenuator_dissipation_w', f"{res['attenuator_dissipation_w']:.4e}")
        st.json({k:v for k,v in res.items() if k!='stages'})
        st.subheader('逐溫區明細')
        st.dataframe(pd.DataFrame(res['stages']))
        df = pd.DataFrame(res['stages'])
        fig, ax = plt.subplots()
        labels = [f"{d['hot']}->{d['cold']}K" for d in res['stages']]
        ax.bar(labels, df['solid_w'], label='Q_solid')
        ax.bar(labels, df['rf_w'], bottom=df['solid_w'], label='Q_rf')
        ax.set_ylabel('W'); ax.set_yscale('log'); ax.legend(); ax.grid(True, alpha=0.3, axis='y')
        st.pyplot(fig)
    except Exception as e:
        st.error(str(e))

with tabs[3]:
    defaults = [x for x in ['Copper (OFHC) RRR=100','Stainless Steel 304 (UNS S30400)','Polyimide (Kapton)','Teflon (PTFE)'] if x in k_mats]
    if not defaults:
        defaults = k_mats[:4]
    sel = st.multiselect('比較材料', k_mats, default=defaults)
    cmin = st.number_input('比較 T_min (K)', value=4.0, key='cmin')
    cmax = st.number_input('比較 T_max (K)', value=300.0, key='cmax')
    if sel:
        comp = n9.compare_materials(sel, t_min=cmin, t_max=cmax, n=300, extrapolate=extrap)
        fig, ax = plt.subplots()
        for c in comp:
            if 'error' in c: continue
            ax.loglog(c['T'], c['k'], label=c['material'])
        ax.legend(fontsize=8); ax.grid(True, which='both', alpha=0.3); ax.set_xlabel('T (K)'); ax.set_ylabel('κ(T)')
        st.pyplot(fig)
        rows = []
        for c in comp:
            if 'error' in c: rows.append({'material':c['material'], 'error':c['error']})
        if rows: st.dataframe(pd.DataFrame(rows))

with tabs[4]:
    st.markdown('掃描單一參數 (length/width/thickness/pin/attenuation) 或掃描材料，輸出熱負載。')
    base_geom = {'width': width, 'thickness': thickness, 'length': lengths[0] if lengths else 0.3, 'area_units': area_units}
    base = {'material': mat, 'stages': stages, 'geometry': base_geom, 'attenuation': attens[0] if len(attens)==1 else attens, 'pin': pin, 'extrapolate_low_t': extrap}
    mode = st.radio('掃描類型', ['參數掃描','材料掃描'], horizontal=True)
    if mode=='參數掃描':
        param = st.selectbox('參數', ['length','width','thickness','pin','attenuation'])
        vs = st.text_input('值列表 (逗號分隔)', '0.1,0.2,0.3,0.5,1.0')
        if st.button('執行掃描'):
            vals = parse_floats(vs)
            res = n9.sweep_parameter(base, param, vals)
            rows = []
            for r in res:
                rows.append({
                    param: r.get('_sweep_value'),
                    'total_load_w': r.get('total_load_w'),
                    'solid_conduction_w': r.get('solid_conduction_w'),
                    'attenuator_dissipation_w': r.get('attenuator_dissipation_w'),
                    'error': r.get('error')
                })
            df = pd.DataFrame(rows)
            st.dataframe(df)
            if 'total_load_w' in df and df['total_load_w'].notna().any():
                fig, ax = plt.subplots()
                ax.plot(df[param], df['total_load_w'], 'o-')
                ax.set_xlabel(param); ax.set_ylabel('total_load_w'); ax.grid(True, alpha=0.3)
                st.pyplot(fig)
    else:
        selm = st.multiselect('掃描材料', k_mats, default=defaults, key='swm')
        if st.button('執行材料掃描'):
            res = n9.sweep_materials_heatload(selm, stages=stages, geometry=base_geom, attenuation=attens[0] if len(attens)==1 else attens, pin=pin, extrapolate_low_t=extrap)
            rows = []
            for r in res:
                rows.append({'material': r.get('_sweep_material', r.get('material')), 'total_load_w': r.get('total_load_w'), 'solid_conduction_w': r.get('solid_conduction_w'), 'error': r.get('error')})
            df = pd.DataFrame(rows).sort_values('total_load_w', na_position='last')
            st.dataframe(df)
            if df['total_load_w'].notna().any():
                fig, ax = plt.subplots()
                ax.barh(df['material'].astype(str), df['total_load_w'])
                ax.set_xscale('log'); ax.set_xlabel('total_load_w'); ax.grid(True, alpha=0.3, axis='x')
                st.pyplot(fig)

with st.expander('引擎/限制說明'):
    st.markdown(r'''
- κ(T): NIST/Raicu 9 係數 (c0..c8) log-polynomial / OFHC Cu rational；**不重擬合、不編造**。
- 熱負載: $Q_{solid}=\sum (A/L)\int \kappa(T)dT$ (log-spaced 梯形) + $Q_{rf}=\sum P_{in}(1-10^{-\alpha/10})$。
- 有效範圍外預設回傳 0；可選低溫 `k(T)~T^alpha` 外推(可能高估)。
- `NbTi (Cri/oFlex 3)` 在來源中為 runtime 擬合、無固定係數，coeff_data 不提供固定值；請以實測/明確擬合條件另行提供 coeffs。
- polyfit 可靠度驗證報告: `docs/polyfit_可靠度驗證.md`。
''')
