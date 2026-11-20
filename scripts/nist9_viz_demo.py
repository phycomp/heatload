#!/usr/bin/env python3
"""Generate a self-contained visualization & demo HTML for NIST9 heatload refactor.

Inputs:
  - docs/polyfit_可靠度驗證.json (required)
  - heatload-coff-nist engine / core (optional, for sample curves & heatload)
Outputs:
  - docs/nist9_viz_data.json
  - docs/nist9_viz_demo.html
"""

from __future__ import annotations
import json, math, os, sys, importlib.util
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
RELIAB_JSON = DOCS / "polyfit_可靠度驗證.json"
OUT_DATA = DOCS / "nist9_viz_data.json"
OUT_HTML = DOCS / "nist9_viz_demo.html"
SKILL = Path("/home/sam/.opencode/skills/heatload-coff-nist/scripts")


def load_reliab():
    with open(RELIAB_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def load_core():
    # prefer local core by file
    core_path = ROOT / "src" / "量傳線設計" / "核心" / "熱負載NIST9.py"
    if core_path.exists():
        try:
            spec = importlib.util.spec_from_file_location(
                "熱負載NIST9_coreviz", core_path
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
        except Exception:
            pass
    # fallback to skill engine minimal
    if SKILL.exists():
        if str(SKILL) not in sys.path:
            sys.path.insert(0, str(SKILL))
        try:
            import coeff_data, thermal_load  # type: ignore

            return {"coeff_data": coeff_data, "thermal_load": thermal_load}
        except Exception:
            return None
    return None


def logspace(a, b, n):
    a = max(float(a), 1e-6)
    b = float(b)
    if n <= 1:
        return [a]
    la, lb = math.log10(a), math.log10(b)
    return [10 ** (la + (lb - la) * i / (n - 1)) for i in range(n)]


def compute_samples(core, reliab):
    samples = {
        "materials": [],
        "k_curves": [],
        "integral_curves": [],
        "heatload": None,
        "errors": [],
    }
    if core is None:
        samples["errors"].append(
            "NIST9 core/skill engine not available; sample curves/heatload omitted"
        )
        return samples
    # core module path
    if hasattr(core, "list_materials"):
        try:
            mats = core.list_materials("k(T)")
            kmats = [m["name"] for m in mats if m.get("coeffs") is not None]
            samples["materials"] = kmats[:12]
            pick = [
                m
                for m in [
                    "Polyimide (Kapton)",
                    "Stainless Steel 304 (UNS S30400)",
                    "Copper (OFHC) RRR=100",
                    "Teflon (PTFE)",
                ]
                if m in kmats
            ]
            if not pick:
                pick = kmats[:3]
            for m in pick:
                try:
                    kc = core.k_curve(material=m, t_min=4.0, t_max=300.0, n=80)
                    # downsample for embedding
                    idx = list(range(0, len(kc["T"]), max(1, len(kc["T"]) // 40)))
                    samples["k_curves"].append(
                        {
                            "material": m,
                            "T": [kc["T"][i] for i in idx],
                            "k": [kc["k"][i] for i in idx],
                        }
                    )
                    ic = core.integral_curve(material=m, t_cold=4.0, t_hot=300.0, n=80)
                    idxi = list(range(0, len(ic["T"]), max(1, len(ic["T"]) // 40)))
                    samples["integral_curves"].append(
                        {
                            "material": m,
                            "T": [ic["T"][i] for i in idxi],
                            "integral": [ic["integral"][i] for i in idxi],
                        }
                    )
                except Exception as e:
                    samples["errors"].append(f"{m}: {e}")
            base_mat = (
                "Polyimide (Kapton)"
                if "Polyimide (Kapton)" in kmats
                else (kmats[0] if kmats else None)
            )
            if base_mat:
                try:
                    samples["heatload"] = core.calculate_thermal_load(
                        material=base_mat,
                        stages=[300, 50, 4, 1, 0.1, 0.01],
                        geometry={
                            "width": 0.15,
                            "thickness": 1,
                            "length": [0.3, 0.3, 0.2, 0.2, 0.2],
                            "area_units": "mil",
                        },
                        attenuation=[0, 3, 6, 6, 6],
                        pin=1e-6,
                    )
                except Exception as e:
                    samples["errors"].append(f"heatload: {e}")
        except Exception as e:
            samples["errors"].append(str(e))
    else:
        # skill dict fallback: compute minimal curves
        try:
            cd = core["coeff_data"]
            tl = core["thermal_load"]
            names = [
                n
                for n in cd.list_materials()
                if cd.get_material(n).get("category") == "k(T)"
                and cd.get_material(n).get("coeffs")
            ]
            samples["materials"] = names[:12]
            pick = [
                m
                for m in [
                    "Polyimide (Kapton)",
                    "Stainless Steel 304 (UNS S30400)",
                    "Copper (OFHC) RRR=100",
                    "Teflon (PTFE)",
                ]
                if m in names
            ]
            for m in pick[:3]:
                rec = cd.get_material(cd.resolve(m))
                Ts = logspace(4, 300, 40)
                ks = [
                    float(
                        tl.k_of_T(
                            t, rec["coeffs"], rec.get("equation_type", "log_polynomial")
                        )
                    )
                    for t in Ts
                ]
                Is = [
                    0.0
                    if i == 0
                    else float(
                        tl.integrate_kappa(
                            4.0,
                            t,
                            rec["coeffs"],
                            rec.get("equation_type", "log_polynomial"),
                        )
                    )
                    for i, t in enumerate(Ts)
                ]
                samples["k_curves"].append({"material": m, "T": Ts, "k": ks})
                samples["integral_curves"].append(
                    {"material": m, "T": Ts, "integral": Is}
                )
        except Exception as e:
            samples["errors"].append(str(e))
    return samples


def build_data():
    reliab = load_reliab()
    core = load_core()
    samples = compute_samples(core, reliab)
    data = {
        "meta": {
            "title": "NIST 9 係數熱負載整合 — 視覺化與演示",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source": {
                "reliability": str(RELIAB_JSON),
                "engine": "heatload-coff-nist (coeff_data.py, thermal_load.py)",
            },
        },
        "decisions": [
            {
                "id": "D1",
                "v": "B",
                "desc": "整合至新平台 (src/量傳線設計/核心 + pages) 並處理 熱負載/pages",
            },
            {"id": "D2", "v": "D", "desc": "共用核心模組 + 重構/新增頁面 + 新模擬頁"},
            {
                "id": "D3",
                "v": "D",
                "desc": "κ(T)/∫κdT 曲線、材料比較、多溫區穩態熱負載、參數掃描/模擬",
            },
            {
                "id": "D4",
                "v": "A",
                "desc": "9 係數資料/引擎以 heatload-coff-nist 技能腳本為單一真相來源",
            },
            {"id": "D5", "v": "A", "desc": "保留原檔，新增共用層/新頁面與 legacy 備份"},
            {"id": "D6", "v": "C", "desc": "本輪完成實作與驗證"},
        ],
        "model": {
            "kappa": "log_polynomial: log10 κ = Σ c_n (log10 T)^n (或 Cu rational)",
            "q_solid": "Q_solid = Σ (A/L_i) ∫ κ(T) dT",
            "q_rf": "Q_rf = Σ P_in (1 - 10^(-α_i/10))",
            "policy": "僅用具來源固定 9 係數；NbTi(Cri/oFlex3)=runtime_polyfit, coeffs=null 不編造",
        },
        "deliverables": {
            "core": [
                "src/量傳線設計/核心/熱負載NIST9.py",
                "src/量傳線設計/核心/__init__.py",
                "熱負載/pages/_nist9_共用.py",
            ],
            "platform_pages": [
                "pages/20熱負載NIST9.py",
                "pages/4熱負載.py (擴充NIST9分頁)",
            ],
            "legacy_pages": [
                "熱負載/pages/10nist低溫庫.py (重構)",
                "熱負載/pages/10nist低溫庫_legacy.py",
                "熱負載/pages/30nist9_熱負載模擬.py",
                "熱負載/pages/31nist9_polyfit_可靠度.py",
                "熱負載/pages/16柔性八階擬合.py (保留)",
                "熱負載/pages/16柔性八階擬合_legacy.py",
            ],
            "docs_scripts": [
                "docs/NIST9熱負載整合說明.md",
                "docs/NIST9_視覺化規格.md",
                "docs/polyfit_可靠度驗證.md",
                "docs/polyfit_可靠度驗證.json",
                "scripts/validate_polyfit_reliability.py",
                "scripts/nist9_viz_demo.py",
            ],
        },
        "reliability": reliab,
        "samples": samples,
    }
    return data


def fmt_num(v):
    try:
        fv = float(v)
        if fv == 0:
            return "0"
        av = abs(fv)
        if av >= 1e4 or av < 1e-3:
            return f"{fv:.3e}"
        return f"{fv:.6g}"
    except Exception:
        return str(v)


def render_html(data):
    payload = json.dumps(data, ensure_ascii=False)
    # basic escaping for script tag
    payload = payload.replace("</", "<\\/")
    template = r"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>__TITLE__</title>
<style>
:root{{--bg:#0b1020;--panel:#121a33;--panel2:#182244;--text:#e8eefc;--muted:#a9b4d0;--accent:#6ea8fe;--accent2:#7ee787;--warn:#f2cc60;--bad:#ff7b72;--grid:#2a355f}}
*{{box-sizing:border-box}} body{{margin:0;font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,"Noto Sans TC",sans-serif;background:linear-gradient(180deg,#0b1020,#0e1530);color:var(--text)}}
header{{padding:20px 24px;border-bottom:1px solid #223;background:rgba(10,14,30,.7);position:sticky;top:0;backdrop-filter:blur(6px);z-index:5}}
h1{{margin:0;font-size:20px}} .sub{{color:var(--muted);font-size:13px;margin-top:4px}}
main{{padding:18px;max-width:1280px;margin:0 auto}}
nav{{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 18px}}
nav button{{background:var(--panel);color:var(--text);border:1px solid #2a355f;padding:8px 12px;border-radius:10px;cursor:pointer}}
nav button.active{{background:var(--panel2);border-color:var(--accent);color:#fff}}
section{{display:none}} section.active{{display:block}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}}
.card{{background:var(--panel);border:1px solid #243055;border-radius:14px;padding:14px}}
.card h3{{margin:0 0 8px 0;font-size:15px;color:#fff}}
.small{{color:var(--muted);font-size:12px}} .kpi{{font-size:22px;font-weight:700}}
table{{width:100%;border-collapse:collapse;font-size:13px}} th,td{{padding:8px;border-bottom:1px solid #26335a;vertical-align:top;text-align:left}} th{{color:#cfe1ff;font-weight:600}}
.tag{{display:inline-block;padding:2px 8px;border-radius:999px;font-size:12px;border:1px solid #345;background:#152042;margin-right:6px}}
.ok{{color:var(--accent2)}} .warn{{color:var(--warn)}} .bad{{color:var(--bad)}}
svg{{width:100%;height:auto;background:#0d1430;border:1px solid #243055;border-radius:12px}}
.legend{{display:flex;flex-wrap:wrap;gap:10px;margin-top:6px;font-size:12px;color:var(--muted)}}
.legend span{{display:inline-flex;align-items:center;gap:6px}} .sw{{width:12px;height:3px;border-radius:2px;display:inline-block}}
pre{{white-space:pre-wrap;background:#0d1430;border:1px solid #243055;padding:10px;border-radius:10px;color:#d7e3ff;overflow:auto}}
.flex{{display:flex;gap:12px;flex-wrap:wrap}} .flex>.card{{flex:1 1 360px}}
.mono{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
</style>
</head>
<body>
<header>
  <h1>NIST 9 係數熱負載整合 — 視覺化與演示</h1>
  <div class="sub">易懂規格 / 架構 / κ(T)·∫κdT / 熱負載 / polyfit 可靠度 · 產生時間: <span id="gen"></span></div>
</header>
<main>
  <nav id="nav"></nav>
  <section id="sec-overview"></section>
  <section id="sec-arch"></section>
  <section id="sec-curves"></section>
  <section id="sec-heatload"></section>
  <section id="sec-reliab"></section>
  <section id="sec-spec"></section>
</main>
<script>
const DATA = __PAYLOAD__;
const $ = (s,el=document)=>el.querySelector(s);
const fmt = (v)=>{{if(v===null||v===undefined) return ''; const n=Number(v); if(!isFinite(n)) return String(v); const a=Math.abs(n); if(a===0) return '0'; if(a>=1e4|| (a>0 && a<1e-3)) return n.toExponential(3); return String(Math.round(n*1e6)/1e6);}}
const sections=[['overview','總覽與決策'],['arch','架構與資料流'],['curves','κ(T) / ∫κdT / 比較'],['heatload','多溫區熱負載演示'],['reliab','polyfit 可靠度'],['spec','檔案與 API 規格']];
const nav=$('#nav'); sections.forEach((s,i)=>{{const b=document.createElement('button'); b.textContent=s[1]; b.dataset.sec=s[0]; b.onclick=()=>show(s[0]); if(i===0)b.classList.add('active'); nav.appendChild(b);}});
function show(id){{document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.sec===id)); sections.forEach(s=>$('#sec-'+s[0]).classList.toggle('active',s[0]===id));}}
$('#gen').textContent=DATA.meta.generated_at;

function card(title, body){{return `<div class="card"><h3>${{title}}</h3>${{body}}</div>`}}
function table(headers, rows){{let h='<table><thead><tr>'+headers.map(x=>`<th>${{x}}</th>`).join('')+'</tr></thead><tbody>'; rows.forEach(r=>{{h+='<tr>'+r.map(x=>`<td>${{x}}</td>`).join('')+'</tr>'}}); h+='</tbody></table>'; return h;}}

// overview
(function(){{const el=$('#sec-overview');
 const decRows=DATA.decisions.map(d=>[d.id, d.v, d.desc]);
 const m=DATA.model;
 const rel=DATA.reliability.baseline_noise1_seed42;
 el.innerHTML = `<div class="grid">`+
  card('決策規格 (固定)', table(['決策','值','規格意義'], decRows))+
  card('計算模型規格', `<div class="small">單一真相來源: <span class="mono">${{DATA.meta.source.engine}}</span></div><ul>
    <li><b>κ(T)</b>: ${{m.kappa}}</li>
    <li><b>Q_solid</b>: ${{m.q_solid}}</li>
    <li><b>Q_rf</b>: ${{m.q_rf}}</li>
    <li><b>政策</b>: ${{m.policy}}</li></ul>`)+
  card('可靠度快照 (baseline noise=1%, seed=42)', `<table><tr><th>材料</th><th>R²</th><th>RMSE(log10)</th><th>α</th><th>k(20mK)</th><th>∫₂³⁰⁰κdT</th></tr>
    <tr><td>Kapton</td><td>${{fmt(rel.kapton.r2)}}</td><td>${{fmt(rel.kapton.rmse_log10)}}</td><td>${{fmt(rel.kapton.alpha_extrap)}}</td><td>${{fmt(rel.kapton.k_at_20mK)}}</td><td>${{fmt(rel.kapton.integral_2_300K)}}</td></tr>
    <tr><td>NbTi</td><td>${{fmt(rel.nbti.r2)}}</td><td>${{fmt(rel.nbti.rmse_log10)}}</td><td>${{fmt(rel.nbti.alpha_extrap)}}</td><td>${{fmt(rel.nbti.k_at_20mK)}}</td><td>${{fmt(rel.nbti.integral_2_300K)}}</td></tr></table>
    <div class="small" style="margin-top:8px">擬合區間品質高、積分相對穩定；深低溫外推(k20mK/α)敏感。NbTi 無固定 9 係數(runtime_polyfit)。</div>`)
  +`</div>`;
}})();

// arch
(function(){{const el=$('#sec-arch');
 const d=DATA.deliverables;
 const list = (arr)=>'<ul>'+arr.map(x=>`<li class="mono">${{x}}</li>`).join('')+'</ul>';
 el.innerHTML = `<div class="flex">
  ${card('架構資料流（規格）', `<pre class="mono">[heatload-coff-nist SSOT]\n  coeff_data.py (54 材料, c0..c8, 來源/範圍)\n  thermal_load.py (κ, ∫κdT, Q_solid+Q_rf)\n            |\n            v\n[共用核心] 熱負載NIST9.py  +  熱負載/pages/_nist9_共用.py\n            |\n   +--------+---------+\n   v                  v\n[新平台 pages]    [熱負載/pages]\n 4(擴充), 20        10(重構, legacy), 30, 31, 16(保留)\n            |\n            v\n[驗證/演示] validate_polyfit_reliability.py -> md/json -> nist9_viz_demo.html</pre>
 <div class="small">D4=A 單一真相來源；D5=A 保留原檔/legacy；D3=D 曲線/比較/多溫區/掃描。</div>`)}
  ${card('交付清單', `<b>核心</b>${{list(d.core)}}<b>新平台頁面</b>${{list(d.platform_pages)}}<b>舊目錄整合(保留原檔)</b>${{list(d.legacy_pages)}}<b>文件/腳本</b>${{list(d.docs_scripts)}}`)}
 </div>`;
}})();

function log10(x){{return Math.log10(Math.max(x,1e-300));}}
function makeLogChart(series, opts){{ // series: {{name,T,k or integral,color}}
 const W=opts.w||860,H=opts.h||320,pad={{l:60,r:20,t:20,b:45}};
 const xs=[], ys=[]; series.forEach(s=>s.x.forEach(v=>xs.push(v))); series.forEach(s=>s.y.forEach(v=>v>0&&ys.push(v)));
 const xmin=Math.min(...xs), xmax=Math.max(...xs), ymin=Math.min(...ys), ymax=Math.max(...ys);
 const lx=v=>pad.l+(log10(v)-log10(xmin))/(log10(xmax)-log10(xmin)+1e-12)*(W-pad.l-pad.r);
 const ly=v=>pad.t+(1-(log10(v)-log10(ymin))/(log10(ymax)-log10(ymin)+1e-12))*(H-pad.t-pad.b);
 const colors=['#6ea8fe','#7ee787','#f2cc60','#ff7b72','#d2a8ff','#79c0ff'];
 let svg=`<svg viewBox="0 0 ${{W}} ${{H}}" preserveAspectRatio="xMidYMid meet">`;
 // grid
 for(let t=1;t<=1000;t*=10){{if(t<xmin||t>xmax)continue; const x=lx(t); svg+=`<line x1="${{x}}" y1="${{pad.t}}" x2="${{x}}" y2="${{H-pad.b}}" stroke="#223" stroke-width="1"/>`; svg+=`<text x="${{x}}" y="${{H-pad.b+16}}" fill="#8aa" font-size="10" text-anchor="middle">${{t}}</text>`;}}
 [1e-12,1e-10,1e-8,1e-6,1e-4,1e-2,1,1e2,1e4,1e6,1e8,1e10,1e12,1e14,1e16,1e18].forEach(v=>{{if(v<ymin||v>ymax) return; const y=ly(v); svg+=`<line x1="${{pad.l}}" y1="${{y}}" x2="${{W-pad.r}}" y2="${{y}}" stroke="#223" stroke-width="1"/>`; svg+=`<text x="${{pad.l-6}}" y="${{y+3}}" fill="#8aa" font-size="10" text-anchor="end">${{fmt(v)}}</text>`;}});
 svg+=`<rect x="${{pad.l}}" y="${{pad.t}}" width="${{W-pad.l-pad.r}}" height="${{H-pad.t-pad.b}}" fill="none" stroke="#345"/>`;
 series.forEach((s,si)=>{{const c=colors[si%colors.length]; let d=''; s.x.forEach((x,i)=>{{const y=s.y[i]; if(!(y>0)) return; const X=lx(x), Y=ly(y); d += (d? 'L':'M')+X+','+Y;}}); svg+=`<path d="${{d}}" fill="none" stroke="${{c}}" stroke-width="2"/>`; }});
 svg+=`<text x="${{W/2}}" y="${{H-6}}" fill="#cfe1ff" font-size="12" text-anchor="middle">${{opts.xlabel||'T (K)'}}</text>`;
 svg+=`<text x="14" y="${{H/2}}" fill="#cfe1ff" font-size="12" transform="rotate(-90 14 ${{H/2}})" text-anchor="middle">${{opts.ylabel||''}}</text>`;
 svg+=`</svg><div class="legend">`+series.map((s,si)=>`<span><i class="sw" style="background:${{colors[si%colors.length]}}"></i>${{s.name}}</span>`).join('')+`</div>`;
 return svg;
}}

function makeLinearBar(labels, values, opts){{const W=opts.w||860,H=opts.h||300,pad={{l:160,r:20,t:20,b:30}};
 const vmax=Math.max(...values.map(v=>Math.abs(v)||0),1e-12); const bw=(H-pad.t-pad.b)/Math.max(labels.length,1)*0.7;
 let svg=`<svg viewBox="0 0 ${{W}} ${{H}}">`;
 labels.forEach((lab,i)=>{{const y=pad.t + (i+0.5)*(H-pad.t-pad.b)/labels.length; const w=(Math.abs(values[i])/vmax)*(W-pad.l-pad.r); const c=values[i]>=0?'#6ea8fe':'#ff7b72';
  svg+=`<text x="${{pad.l-8}}" y="${{y+4}}" fill="#cfe1ff" font-size="12" text-anchor="end">${{lab}}</text>`;
  svg+=`<rect x="${{pad.l}}" y="${{y-bw/2}}" width="${{Math.max(w,1)}}" height="${{bw}}" fill="${{c}}" rx="4"/>`;
  svg+=`<text x="${{pad.l+w+6}}" y="${{y+4}}" fill="#a9b4d0" font-size="11">${{fmt(values[i])}}</text>`;}});
 svg+=`<line x1="${{pad.l}}" y1="${{pad.t-4}}" x2="${{pad.l}}" y2="${{H-pad.b+4}}" stroke="#345"/>`;
 svg+=`</svg>`; return svg; }}

// curves
(function(){{const el=$('#sec-curves'); const s=DATA.samples; if(!s.k_curves || !s.k_curves.length){{el.innerHTML=card('樣本資料','無可用引擎取樣：'+(s.errors||[]).join('; ')); return;}}
 const ks=s.k_curves.map(c=>({{name:c.material,x:c.T,y:c.k}}));
 const is=s.integral_curves.map(c=>({{name:c.material,x:c.T,y:c.integral}}));
 el.innerHTML = `<div class="flex">`+
  card('κ(T) 曲線 (4–300K, log-log)', makeLogChart(ks,{{ylabel:'κ(T) [W/m/K]'}}))+
  card('∫₄ᵀ κ(T)dT 累積曲線 (log-log)', makeLogChart(is,{{ylabel:'∫ κ(T)dT [W/m]'}}))+
 `</div><div class="card" style="margin-top:12px"><h3>說明</h3><div class="small">曲線由 NIST 9 係數引擎取樣（固定來源係數）。比較用於觀察材料熱導量級與溫度趨勢；設計計算須搭配幾何(A/L)、溫區與範圍政策。</div></div>`;
}})();

// heatload
(function(){{const el=$('#sec-heatload'); const hl=DATA.samples.heatload; if(!hl){{el.innerHTML=card('多溫區熱負載演示','無樣本熱負載資料：'+(DATA.samples.errors||[]).join('; ')); return;}}
 const rows=hl.stages.map((d,i)=>[`${{d.T_hot_K}}→${{d.T_cold_K}}`, fmt(d.solid_conduction_w), fmt(d.attenuator_dissipation_w), fmt(d.total_load_w)]);
 const labels=hl.stages.map(d=>`${{d.T_hot_K}}→${{d.T_cold_K}}K`);
 const vals=hl.stages.map(d=>d.total_load_w);
 el.innerHTML = `<div class="grid">`+
  card('示例條件與總量', `<div><span class="tag">材料: ${{hl.material}}</span><span class="tag">P_in: ${{fmt(hl.pin_W)}} W</span></div>
   <div style="margin-top:10px" class="grid">
    <div><div class="small">Total</div><div class="kpi">${{fmt(hl.total_load_w)}} W</div></div>
    <div><div class="small">Solid</div><div class="kpi ok">${{fmt(hl.solid_conduction_w)}} W</div></div>
    <div><div class="small">Atten/RF</div><div class="kpi warn">${{fmt(hl.attenuator_dissipation_w)}} W</div></div>
   </div><div class="small" style="margin-top:8px">幾何/溫區: 300-50-4-1-0.1-0.01K, width=0.15 mil, thickness=1 mil, L=[0.3,0.3,0.2,0.2,0.2] m, α=[0,3,6,6,6] dB</div>`)+
  card('各溫區分解 (W)', table(['溫區','Q_solid','Q_rf/atten','Total'], rows))+
 `</div><div class="card" style="margin-top:12px"><h3>各溫區總熱負載</h3>${{makeLinearBar(labels, vals, {{}})}}<div class="small">模型：Q_solid=Σ(A/L)∫κdT，Q_rf=Σ P_in(1-10^(-α/10))。實際設計請以頁面/核心 API 掃描參數。</div></div>`;
}})();

// reliability
(function(){{const el=$('#sec-reliab'); const R=DATA.reliability; const b=R.baseline_noise1_seed42; const s=R.sensitivity_noise_seed; const tc=b.nbti.tc_region;
 const sensRows=[['Kapton α', fmt(s.kapton.alpha_min)+' ~ '+fmt(s.kapton.alpha_max)],['Kapton k(20mK)', fmt(s.kapton.k20mK_min)+' ~ '+fmt(s.kapton.k20mK_max)],['Kapton ∫₂³⁰⁰κdT', fmt(s.kapton.integral_min)+' ~ '+fmt(s.kapton.integral_max)],['NbTi α', fmt(s.nbti.alpha_min)+' ~ '+fmt(s.nbti.alpha_max)],['NbTi k(20mK)', fmt(s.nbti.k20mK_min)+' ~ '+fmt(s.nbti.k20mK_max)],['NbTi ∫₂³⁰⁰κdT', fmt(s.nbti.integral_min)+' ~ '+fmt(s.nbti.integral_max)]];
 const tcRows=(tc.points||[]).map(p=>[fmt(p.T), fmt(p.resid_log10), fmt(p.ratio_k_kfit)]);
 const baseRows=[['Kapton', fmt(b.kapton.r2), fmt(b.kapton.rmse_log10), fmt(b.kapton.alpha_extrap), fmt(b.kapton.k_at_20mK), fmt(b.kapton.integral_2_300K)],['NbTi', fmt(b.nbti.r2), fmt(b.nbti.rmse_log10), fmt(b.nbti.alpha_extrap), fmt(b.nbti.k_at_20mK), fmt(b.nbti.integral_2_300K)]];
 const verdict = `<ul>
 <li><b>擬合區間</b>：R² 高但 Vandermonde 病態；NbTi 在 Tc~9.2K 有結構性殘差（全域 8 階近似）。</li>
 <li><b>係數/外推</b>：對 noise/seed 敏感；α 與 k(20mK) 跨擾動變動大，深低溫外推不可靠。</li>
 <li><b>積分</b>：擬合區間 ∫₂³⁰⁰κdT 相對穩定，適合區間熱負載估算。</li>
 <li><b>coeff_data 對照</b>：Kapton 有固定來源係數；NbTi 為 <span class="bad">runtime_polyfit / coeffs=null</span>（不可編造）。</li>
 </ul>`;
 el.innerHTML = `<div class="grid">`+
  card('Baseline (noise=1%, seed=42)', table(['材料','R²','RMSE(log10)','α','k(20mK)','∫₂³⁰⁰κdT'], baseRows))+
  card('擾動敏感度範圍 (noise/seed)', table(['指標','範圍'], sensRows))+
  card('NbTi Tc 區殘差 (結構性)', tcRows.length? table(['T (K)','resid log10(k/kfit)','ratio k/kfit'], tcRows):'<div class="small">無</div>')+
  card('可靠度結論與使用規則', verdict)+
 `</div>`;
}})();

// spec
(function(){{const el=$('#sec-spec');
 const apis=[['list_materials/get_material/resolve_material','查詢材料與 9 係數/來源/範圍'],['k_of_T / integrate_kappa','κ(T) 與溫區積分（log-spaced 梯形）'],['k_curve / integral_curve','κ(T)、∫κdT 曲線資料'],['compare_materials','多材料比較'],['calculate_thermal_load','多溫區 Q_solid + Q_rf 熱負載'],['sweep_parameter / sweep_materials_heatload','參數/材料掃描模擬']];
 const files=[
  ['核心','src/量傳線設計/核心/熱負載NIST9.py, __init__.py 匯出'],
  ['共用層','熱負載/pages/_nist9_共用.py (核心優先/技能 fallback)'],
  ['新平台頁','pages/20熱負載NIST9.py, pages/4熱負載.py(NIST9分頁)'],
  ['舊目錄頁','10nist低溫庫.py(重構)+legacy, 30nist9_熱負載模擬.py, 31nist9_polyfit_可靠度.py, 16保留+legacy'],
  ['驗證/演示','scripts/validate_polyfit_reliability.py, docs/polyfit_可靠度驗證.md/json, scripts/nist9_viz_demo.py -> docs/nist9_viz_demo.html']
 ];
 el.innerHTML = `<div class="flex">`+
  card('API 規格', table(['介面','用途'], apis))+
  card('檔案與交付規格', table(['類別','內容'], files))+
 `</div><div class="card" style="margin-top:12px"><h3>視覺化演示工具</h3><div class="small mono">python3 scripts/nist9_viz_demo.py  → docs/nist9_viz_data.json, docs/nist9_viz_demo.html (自包含離線)</div><pre class="mono">${{JSON.stringify({{meta:DATA.meta, samples_errors:DATA.samples.errors, materials_sample:(DATA.samples.materials||[]).slice(0,8)}}, null, 2)}}</pre></div>`;
}})();

show('overview');
</script>
</body>
</html>
"""
    # undo f-string brace escaping for JS/CSS
    template = template.replace("{{", "{").replace("}}", "}")
    html = template.replace("__TITLE__", data["meta"]["title"]).replace(
        "__PAYLOAD__", payload
    )
    return html


def main():
    if not RELIAB_JSON.exists():
        print(f"ERROR: missing {RELIAB_JSON}", file=sys.stderr)
        sys.exit(2)
    data = build_data()
    OUT_DATA.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    OUT_HTML.write_text(render_html(data), encoding="utf-8")
    print(f"WROTE {OUT_DATA}")
    print(f"WROTE {OUT_HTML}")
    print(
        f"samples: k_curves={len(data['samples'].get('k_curves', []))} integral={len(data['samples'].get('integral_curves', []))} heatload={'yes' if data['samples'].get('heatload') else 'no'}"
    )
    if data["samples"].get("errors"):
        print("sample_errors:", data["samples"]["errors"])


if __name__ == "__main__":
    main()
