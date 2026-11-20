#!/usr/bin/env python3
"""驗證 16柔性八階擬合.py 中 polyfit 參數/流程的可靠度。

重點檢查（不依賴 scipy；若有 scipy 則額外做 CubicSpline 對照）:
- 資料生成與擬合設定: log10(T)-log10(k) 空間 8 階多項式, N=50, T∈[2,300]K
- 數值條件數 (Vandermonde)
- 擬合品質: R², RMSE, 殘差結構 (NbTi Tc 轉變區)
- 係數對噪聲/seed 的敏感度 (隨機性來源)
- 低溫外推可靠度: alpha = log10(k(Tmin))/log10(Tmin) vs 多項式導數, 20mK 推估敏感度
- 積分(2-300K)穩定度
- 與 heatload-coff-nist/coeff_data 中既有係數對照

結論: 係數在「同一擬合流程」下可重現, 但屬於對模擬資料/噪聲/轉變區建模假設敏感的經驗擬合參數;
Kapton 係數在擾動下相對穩定、NbTi 因 Tc 轉變與無固定真值更不可靠(技能中標為 runtime_polyfit)。
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path('/home/sam/.opencode/skills/heatload-coff-nist/scripts')
sys.path.insert(0, str(SKILL))
import coeff_data  # type: ignore

try:
    from scipy import interpolate  # type: ignore
    HAVE_SCIPY = True
except Exception:
    HAVE_SCIPY = False


def log_interp(T_nodes, k_nodes, T):
    lx = np.log10(np.asarray(T_nodes, float))
    ly = np.log10(np.asarray(k_nodes, float))
    lt = np.log10(np.asarray(T, float))
    return 10 ** np.interp(lt, lx, ly)


def build_generators(use_scipy=True):
    T_kapton_nodes = np.array([2, 4, 10, 20, 50, 100, 200, 300.0])
    k_kapton_nodes = np.array([0.0008, 0.002, 0.006, 0.015, 0.040, 0.075, 0.130, 0.155])
    T_nbti_nodes = np.array([2, 4, 8, 9, 9.2, 10, 20, 50, 100, 300.0])
    k_nbti_nodes = np.array([0.002, 0.008, 0.03, 0.10, 0.20, 0.50, 1.5, 4.0, 7.0, 10.0])

    if use_scipy and HAVE_SCIPY:
        cs_k = interpolate.CubicSpline(np.log10(T_kapton_nodes), np.log10(k_kapton_nodes))
        cs_n = interpolate.CubicSpline(np.log10(T_nbti_nodes), np.log10(k_nbti_nodes))
        def gen_kap(T):
            return 10 ** cs_k(np.log10(T))
        def gen_nbti(T):
            return 10 ** cs_n(np.log10(T))
        mode = 'scipy.CubicSpline(log-log)'
    else:
        def gen_kap(T):
            return log_interp(T_kapton_nodes, k_kapton_nodes, T)
        def gen_nbti(T):
            return log_interp(T_nbti_nodes, k_nbti_nodes, T)
        mode = 'numpy.interp(log-log) fallback'
    return gen_kap, gen_nbti, mode


def fit_once(kind='kap', noise_pct=1.0, seed=42, gen_kap=None, gen_nbti=None):
    rng = np.random.default_rng(seed)
    T = np.logspace(np.log10(2.0), np.log10(300.0), 50)
    if kind == 'kap':
        k_true = gen_kap(T)
    else:
        k_true = gen_nbti(T)
    k = k_true * (1 + rng.normal(0, noise_pct / 100.0, len(T)))
    x = np.log10(T)
    y = np.log10(k)
    coeffs_desc = np.polyfit(x, y, 8)
    asc = coeffs_desc[::-1]
    yfit = np.polyval(coeffs_desc, x)
    resid = y - yfit
    ss_res = np.sum(resid ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot else float('nan')
    rmse = float(np.sqrt(np.mean(resid ** 2)))
    T_min = float(T.min())
    x_min = math.log10(T_min)
    k_min = 10 ** float(np.polyval(coeffs_desc, x_min))
    alpha = math.log10(k_min) / x_min if x_min != 0 else float('nan')
    slope = float(np.polyval(np.polyder(coeffs_desc), x_min))

    def k_model(Tq):
        Tq = np.asarray(Tq, float)
        xq = np.log10(np.maximum(Tq, 1e-300))
        with np.errstate(over='ignore', under='ignore', invalid='ignore', divide='ignore'):
            lp = np.polyval(coeffs_desc, xq)
            lp = np.clip(lp, -300, 300)
            k_poly = 10 ** lp
            la = alpha * xq
            la = np.clip(la, -300, 300)
            k_ext = 10 ** la
        return np.where(Tq >= T_min, k_poly, k_ext)

    k20 = float(k_model(np.array([0.02]))[0])
    Tgrid = np.logspace(math.log10(2.0), math.log10(300.0), 5000)
    with np.errstate(over='ignore', under='ignore', invalid='ignore'):
        integ = float(np.trapezoid(k_model(Tgrid), Tgrid))

    tc_mask = (T >= 7.5) & (T <= 12.5)
    tc = {
        'max_abs_resid_log10': float(np.max(np.abs(resid[tc_mask]))) if (kind == 'nbti' and tc_mask.any()) else None,
        'points': []
    }
    if kind == 'nbti' and tc_mask.any():
        for Tv, rv in zip(T[tc_mask], resid[tc_mask]):
            tc['points'].append({'T': float(Tv), 'resid_log10': float(rv), 'ratio_k/kfit': float(10 ** rv)})

    return {
        'kind': kind, 'noise_pct': noise_pct, 'seed': seed,
        'r2': float(r2), 'rmse_log10': rmse,
        'alpha_extrap': float(alpha), 'poly_slope_at_Tmin': float(slope),
        'alpha_minus_slope': float(alpha - slope),
        'k_at_20mK': k20, 'integral_2_300K': integ,
        'coeffs_asc_c0_c8': [float(v) for v in asc],
        'tc_region': tc,
    }


def condition_report():
    T = np.logspace(np.log10(2.0), np.log10(300.0), 50)
    x = np.log10(T)
    V = np.vander(x, N=9, increasing=True)
    # scaled as polyfit would roughly benefit from centering; report raw and centered
    xc = (x - x.mean()) / (x.max() - x.min())
    Vc = np.vander(xc, N=9, increasing=True)
    return {
        'cond_V_raw': float(np.linalg.cond(V)),
        'cond_VTV_raw': float(np.linalg.cond(V.T @ V)),
        'cond_V_centered_scaled': float(np.linalg.cond(Vc)),
    }


def sensitivity(gen_kap, gen_nbti):
    out = {}
    noises = [0, 1, 2, 5]
    seeds = [1, 7, 42, 99, 123, 2024]
    for kind, key in [('kap', 'kapton'), ('nbti', 'nbti')]:
        rows = [fit_once(kind, n, s, gen_kap, gen_nbti) for n in noises for s in seeds]
        A = np.array([r['coeffs_asc_c0_c8'] for r in rows], float)
        mean = A.mean(axis=0)
        std = A.std(axis=0)
        rel = np.where(np.abs(mean) > 1e-12, std / np.abs(mean) * 100.0, np.nan)
        def _f(vals):
            arr = np.array(vals, float)
            arr = arr[np.isfinite(arr)]
            return arr
        r2s=_f([r['r2'] for r in rows]); rms=_f([r['rmse_log10'] for r in rows])
        al=_f([r['alpha_extrap'] for r in rows]); k20=_f([r['k_at_20mK'] for r in rows])
        it=_f([r['integral_2_300K'] for r in rows])
        out[key] = {
            'n_runs': len(rows),
            'r2_min': float(np.min(r2s)) if len(r2s) else None,
            'rmse_max': float(np.max(rms)) if len(rms) else None,
            'alpha_min': float(np.min(al)) if len(al) else None,
            'alpha_max': float(np.max(al)) if len(al) else None,
            'k20mK_min': float(np.min(k20)) if len(k20) else None,
            'k20mK_max': float(np.max(k20)) if len(k20) else None,
            'integral_min': float(np.min(it)) if len(it) else None,
            'integral_max': float(np.max(it)) if len(it) else None,
            'coeff_rel_std_pct_c0_c8': [None if (isinstance(x, float) and math.isnan(x)) else float(x) for x in rel],
            'coeff_mean_c0_c8': [float(x) for x in mean],
        }
    return out


def coeff_data_compare(base_kap):
    kap = coeff_data.get_material('Kapton (Cri/oFlex 3)')
    stored = np.array(kap['coeffs'], float)
    fitted = np.array(base_kap['coeffs_asc_c0_c8'], float)
    diff = fitted - stored
    # relative where meaningful
    with np.errstate(divide='ignore', invalid='ignore'):
        rel = np.where(np.abs(stored) > 1e-12, diff / stored * 100.0, np.nan)
    return {
        'stored_source': kap.get('source'),
        'stored_note': kap.get('note'),
        'stored_coeffs': stored.tolist(),
        'fitted_coeffs_noise1_seed42': fitted.tolist(),
        'abs_diff': diff.tolist(),
        'rel_diff_pct': [None if (isinstance(x, float) and (math.isnan(x) or math.isinf(x))) else float(x) for x in rel],
        'max_abs_diff': float(np.max(np.abs(diff))),
    }


def main():
    gen_kap, gen_nbti, gen_mode = build_generators(use_scipy=True)
    report = {
        'generator': gen_mode,
        'have_scipy': HAVE_SCIPY,
        'condition': condition_report(),
        'baseline_noise1_seed42': {
            'kapton': fit_once('kap', 1, 42, gen_kap, gen_nbti),
            'nbti': fit_once('nbti', 1, 42, gen_kap, gen_nbti),
        },
        'sensitivity_noise_seed': sensitivity(gen_kap, gen_nbti),
    }
    report['kapton_coeffdata_compare'] = coeff_data_compare(report['baseline_noise1_seed42']['kapton'])

    # NbTi availability in coeff_data
    nbti = coeff_data.get_material('NbTi (Cri/oFlex 3)')
    report['nbti_coeffdata_status'] = {
        'coeffs': nbti.get('coeffs'),
        'equation_type': nbti.get('equation_type'),
        'source': nbti.get('source'),
        'note': nbti.get('note'),
    }

    out_json = ROOT / 'docs' / 'polyfit_可靠度驗證.json'
    out_md = ROOT / 'docs' / 'polyfit_可靠度驗證.md'
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    b = report['baseline_noise1_seed42']
    s = report['sensitivity_noise_seed']
    md = []
    md.append('# polyfit 參數可靠度驗證 (16柔性八階擬合)\n')
    md.append(f"- 資料生成器: `{report['generator']}` (HAVE_SCIPY={report['have_scipy']})")
    md.append('- 擬合模型: `log10(k)=Σ c_n (log10 T)^n`, n=0..8, `np.polyfit(x,y,8)`; T=2..300K, N=50, log-spaced')
    md.append('- 低溫外推(程式實作): `T < Tmin` 時 `k(T)=T^alpha`, `alpha=log10(k_poly(Tmin))/log10(Tmin)`\n')
    c = report['condition']
    md.append('## 數值條件數\n')
    md.append(f"- cond(V)_raw = {c['cond_V_raw']:.3e}, cond(V^T V)_raw = {c['cond_VTV_raw']:.3e}")
    md.append(f"- cond(V_centered_scaled) = {c['cond_V_centered_scaled']:.3e} (polyfit 內部縮放可改善求解穩定性，但高階項仍具敏感性)\n")
    md.append('## 基準擬合 (noise=1%, seed=42)\n')
    for k in ['kapton','nbti']:
        r = b[k]
        md.append(f"### {k}")
        md.append(f"- R²={r['r2']:.6f}, RMSE(log10)={r['rmse_log10']:.6f}")
        md.append(f"- alpha_extrap={r['alpha_extrap']:.4f}, poly_slope@Tmin={r['poly_slope_at_Tmin']:.4f}, gap={r['alpha_minus_slope']:.4f}")
        md.append(f"- k(20mK)={r['k_at_20mK']:.4e} W/m/K (外推, 不確定性高), ∫_2^300 k dT={r['integral_2_300K']:.6e} W/m")
        if r['tc_region']['max_abs_resid_log10'] is not None:
            md.append(f"- NbTi Tc 區(7.5-12.5K) max |resid_log10|={r['tc_region']['max_abs_resid_log10']:.4f} (全域 8 階多項式難以精確描述轉變)")
        md.append('')
    md.append('## 噪聲/seed 敏感度 (noise∈{0,1,2,5}%, seeds=6, 每材料24次)\n')
    for k in ['kapton','nbti']:
        sk = s[k]
        md.append(f"### {k}")
        md.append(f"- R²_min={sk['r2_min']:.6f}, RMSE_max={sk['rmse_max']:.6f}")
        md.append(f"- alpha 範圍: [{sk['alpha_min']:.4f}, {sk['alpha_max']:.4f}]")
        md.append(f"- k(20mK) 範圍: [{sk['k20mK_min']:.3e}, {sk['k20mK_max']:.3e}] (跨數量級/大幅變動 ⇒ 外推不可靠)")
        md.append(f"- ∫_2^300 k dT 範圍: [{sk['integral_min']:.4e}, {sk['integral_max']:.4e}] (量測溫區積分相對穩定)")
        md.append(f"- 係數相對標準差% (c0..c8): {[None if v is None else round(v,2) for v in sk['coeff_rel_std_pct_c0_c8']]}")
        md.append('')
    md.append('## 與 coeff_data 對照\n')
    cmpk = report['kapton_coeffdata_compare']
    md.append('### Kapton (Cri/oFlex 3)')
    md.append(f"- 來源: {cmpk['stored_source']}")
    md.append(f"- noise=1,seed=42 擬合 vs 儲存係數 max |Δc| = {cmpk['max_abs_diff']:.4g} (生成器差異: 頁面用 scipy.CubicSpline, 本驗證預設 {report['generator']})")
    md.append('### NbTi (Cri/oFlex 3)')
    stn = report['nbti_coeffdata_status']
    md.append(f"- coeffs: {stn['coeffs']}, equation_type: {stn['equation_type']}")
    md.append(f"- 狀態: {stn['source']}")
    md.append('')
    md.append('## 可靠度結論\n')
    md.append('1. **數值可解但病態**: 原始 Vandermonde 條件數極大；`polyfit` 透過平移/縮放可穩定求解，但 8 階係數(特別高階/邊界外推相關項)對資料擾動敏感。')
    md.append('2. **擬合品質**: 在 2-300K 資料範圍內 R² 高、RMSE(log10) 小；但 NbTi 在 Tc~9.2K 轉變區存在結構性殘差，全域單一 8 階多項式屬近似。')
    md.append('3. **係數可靠度**: 係數會隨 `noise_pct` 與隨機種子改變(頁面行為)；Kapton 擾動下中等敏感，NbTi 係數變動較大且無固定權威數值。')
    md.append('4. **外推可靠度低**: `alpha` 與多項式端點導數落差大，且 `k(20mK)` 對擾動極敏感；低於 Tmin 的直線外推僅可作量級示意，不宜視為可靠物性參數。')
    md.append('5. **積分相對可靠**: 量測/擬合區間內 `∫κ dT` 對擾動較穩定，適合做區間熱負載估算；跨區/深低溫需保守解讀。')
    md.append('6. **工程建議**: 以 `heatload-coff-nist/coeff_data.py` 中具來源之固定係數作單一真相；對 NbTi/Cri-oFlex3 這類 runtime 擬合材料，必須明示資料來源與擬合條件，不可當固定 NIST 係數使用。')
    out_md.write_text('\n'.join(md), encoding='utf-8')

    print(json.dumps({
        'out_json': str(out_json),
        'out_md': str(out_md),
        'generator': gen_mode,
        'kapton_r2': b['kapton']['r2'],
        'nbti_r2': b['nbti']['r2'],
        'kapton_alpha_range': [s['kapton']['alpha_min'], s['kapton']['alpha_max']],
        'nbti_alpha_range': [s['nbti']['alpha_min'], s['nbti']['alpha_max']],
        'nbti_k20_range': [s['nbti']['k20mK_min'], s['nbti']['k20mK_max']],
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
