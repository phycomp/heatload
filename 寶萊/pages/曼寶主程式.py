# -*- coding: utf-8 -*-
from os.path import abspath, dirname
from streamlit import caption, columns, divider, error, header, info, set_page_config, sidebar, subheader, success, table, title, warning, write, radio, number_input, checkbox, markdown
from sys import path
from pathlib import Path
from glob import glob
#app.py — Phase C：PCB 阻抗合成互動工具（Streamlit）
#執行方式：  streamlit run app.py
#依賴：tl_synthesis.py（同目錄）
import sys
import os
path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import numpy as np
import tl_synthesis as tls

set_page_config(page_title="PCB 阻抗合成工具", page_icon="🔧", layout="wide")

SECTIONS = {
    "Microstrip 微帶線": "microstrip",
    "Embedded Microstrip 嵌入式微帶": "embedded_microstrip",
    "Stripline 帶狀線": "stripline",
    "Asymmetric Stripline 非對稱帶狀線": "asymmetric_stripline",
    "Broadside Coupled Stripline 寬邊耦合": "broadside_stripline",
    "Differential Microstrip 差分微帶": "diff_microstrip",
    "Differential Stripline 差分帶狀線(IPC)": "diff_stripline",
    "Differential Stripline 差分帶狀線(保角映射🔴迭代)": "diff_stripline_conformal",
    "CPW 共面波導(🔴迭代)": "cpw",
    "Coax 同軸": "coax",
    "Parallel Wire 平行雙線": "parallel_wire",
    "Plane Impedance 平面(L/C)": "plane",
    "Pad Capacitance 焊盤電容": "pad",
}

with sidebar:
  mode = radio("模式", ["單一截面合成", "疊構指派（Polar 模板）", "正向驗算", '物理推導'], horizontal=True)

# ----------------------------------------------------------------------
# if mode == "物理推導":
def 物理推導():
  MD=glob('交付/*.md')
  MD=sorted(MD)
  with sidebar:
    麥=radio('清單', MD, horizontal=True)
  if 麥:
    麥檔=Path(麥)
    markdown(麥檔.read_text())
if mode == "單一截面合成":
  左, 右=columns([2, 1])
  with sidebar:
    sel = radio("截面", list(SECTIONS), horizontal=True)
  with 左:
    物理推導()
  with 右:
    sec = SECTIONS[sel]
    subheader(f"合成：{sel}")

    c1, c2, c3 = columns(3)
    er = c1.number_input("介電常數 εᵣ", 1.0, 12.0, 4.2, 0.1)
    t = c2.number_input("銅厚 t (mm)", 0.0, 0.2, 0.035, 0.005)
    tgt = c3.number_input("目標阻抗 (Ω)", 10.0, 200.0, 50.0, 1.0)

    h = h1 = d = w_fix = b = None
    if sec not in ("coax", "parallel_wire", "plane", "pad"):
        h = number_input("介質厚度 h (mm)", 0.01, 5.0, 0.2, 0.01,
                                    help="Stripline 族：走線到平面距離")
    if sec in ("embedded_microstrip", "asymmetric_stripline", "broadside_stripline"):
        h1 = number_input("h₁ (mm)", 0.01, 5.0, 0.4, 0.01,
                                     help="Embedded: 上覆介質高 / Asym: 較厚側 / Broadside: 中心介質")
    if sec in ("diff_microstrip", "diff_stripline", "diff_stripline_conformal"):
        d = number_input("差分間距 d/s (mm)", 0.01, 3.0, 0.2, 0.01)
    if sec == "diff_stripline_conformal":
        b = number_input("平面間距 b (mm)", 0.02, 5.0, 0.4, 0.01)
    if sec in ("cpw", "coax"):
        w_fix = number_input("固定參數 w/dₒ (mm)", 0.01, 10.0, 0.3, 0.01,
                                        help="CPW: 槽寬 w（反解 s）/ Coax: 外徑 dₒ（反解 dᵢ）")
    if sec == "parallel_wire":
        d = number_input("線徑 d (mm)", 0.05, 5.0, 1.0, 0.05)
    if sec == "plane":
        wp = number_input("板寬 w (mm)", 1.0, 200.0, 10.0, 1.0)
    if sec == "pad":
        lp = number_input("焊盤長 l (mm)", 0.2, 20.0, 2.0, 0.1)
        hp = number_input("介質高 h (mm)", 0.05, 5.0, 0.2, 0.01)

    # if button("求解", type="primary"):
    # try:
    if sec == "plane":
        r = tls.plane_lc(wp, h, er)
        success(f"L = {r['L_nH_m']:.3f} nH/m　C = {r['C_pF_m']:.3f} pF/m　"
                 f"Z_plate = {r['Z_plate']:.2f} Ω　Tpd = {r['Tpd_ns_m']:.3f} ns/m")
    elif sec == "pad":
        cval = tls.pad_capacitance(w_fix if w_fix else 1.27, lp, hp, t, er)
        success(f"焊盤電容 C ≈ {cval:.3f} pF（Mantaro 半經驗式，w>h、l>h）")
    else:
        kw = dict(h=h, h1=h1, t=t, er=er, d=d, w=w_fix, b=b)
        kw = {k: v for k, v in kw.items() if v is not None}
        r = tls.solve(sec, tgt, **kw)
        geo = {k: v for k, v in r.items() if k.endswith("_mm")}
        success("反解幾何：" + "　".join(f"{k} = {v:.4f} mm" for k, v in geo.items()))
        m1, m2, m3 = columns(3)
        m1.metric("正算代回", f"{r['forward_check']:.3f} Ω")
        m2.metric("殘差", f"{r['residual_pct']:.2e} %")
        m3.metric("迭代數", r.get("iterations", "—"))
        if "tpd_ns_m" in r:
            info(f"傳播延遲 Tpd = {r['tpd_ns_m']:.3f} ns/m")
        if r["residual_pct"] > 1.0:
            warning("殘差超過 ±1%，請檢查適用域（如 w/h 範圍）")
        #except Exception as e:
        #    error(f"求解失敗：{e}")

# ----------------------------------------------------------------------
elif mode == "疊構指派（Polar 模板）":
    with sidebar:
      subheader("疊構指派：Polar 模板 → 各層線寬")
      tpl = radio("模板", list(tls.TEMPLATES), format_func=lambda k: f"{k} — {tls.TEMPLATES[k]['desc']}", horizontal=True)
      subheader(tls.TEMPLATES[tpl]["desc"])
      caption(f"總厚 {tls.TEMPLATES[tpl]['total_um']} µm｜訊號層 "
                 f"{tls.TEMPLATES[tpl]['signal_layers']}｜平面層 {tls.TEMPLATES[tpl]['plane_layers']}")
      er = number_input("介電常數 εᵣ", 1.0, 12.0, 4.2, 0.1)

      tgt = number_input("目標單端阻抗 (Ω)", 10.0, 150.0, 50.0, 1.0)
      diff_mode = checkbox("差分模式")
      d_sp = number_input("差分間距 d (mm)", 0.01, 3.0, 0.2, 0.01) if diff_mode else None

    write("各訊號層求解結果：")
    rows = []
    sk = tls.Stackup.from_polar_template(tpl)
    for lay in tls.TEMPLATES[tpl]["signal_layers"]:
        try:
            if diff_mode:
                r = sk.assign(lay, target_zd=tgt * 2, d=d_sp)
            else:
                r = sk.assign(lay, target_z0=tgt)
            rows.append(dict(層=lay, 截面=r["section"], 線寬_mm=round(r["w_mm"], 4),
                             代回=f"{r['forward_check']:.2f}Ω",
                             殘差=f"{r['residual_pct']:.1e}%",
                             Tpd=f"{r['tpd_ns_m']:.2f} ns/m"))
        except Exception as e:
            rows.append(dict(層=lay, 截面="—", 線寬_mm="—", 代回="—",
                             殘差=str(e)[:30], Tpd="—"))
    table(rows)
    caption("⚠ 製造敏感度：參閱 DOC-003 §III.3。Foil build 外層實為 Embedded Microstrip，"
               "此處以 Microstrip 近似（保守高估 2–4%）。")

# ----------------------------------------------------------------------
else:  # 正向驗算
    header("正向驗算：幾何 → 阻抗")
    sel = radio("截面", ["Microstrip", "Stripline", "CPW", "Coax", "Parallel Wire"], horizontal=True)
    c1, c2, c3 = columns(3)
    er = c1.number_input("εᵣ", 1.0, 12.0, 4.2, 0.1)
    if sel == "Microstrip":
        w = c2.number_input("w (mm)", 0.01, 10.0, 2.9, 0.01)
        h = c3.number_input("h (mm)", 0.01, 5.0, 1.6, 0.01)
        t = number_input("t (mm)", 0.0, 0.2, 0.035, 0.005)
        z_ipc = tls.microstrip_z0(w, h, t, er)
        z_hj, eeff = tls.microstrip_hj_z0(w, h, er)
        success(f"IPC-2141A: {z_ipc:.2f} Ω　|　Hammerstad-Jensen: {z_hj:.2f} Ω"
                   f"（ε_eff={eeff:.3f}）　|　Tpd={tls.microstrip_tpd(er):.2f} ns/m")
    elif sel == "Stripline":
        w = c2.number_input("w (mm)", 0.01, 10.0, 0.15, 0.01)
        h = c3.number_input("h=到平面距離 (mm)", 0.01, 5.0, 0.2, 0.01)
        t = number_input("t (mm)", 0.0, 0.2, 0.035, 0.005)
        success(f"Stripline: {tls.stripline_z0(w, h, t, er):.2f} Ω　Tpd={tls.stripline_tpd(er):.2f} ns/m")
    elif sel == "CPW":
        s = c2.number_input("s (mm)", 0.01, 10.0, 0.5, 0.01)
        w = c3.number_input("槽寬 w (mm)", 0.01, 10.0, 0.3, 0.01)
        h = number_input("h (mm, >10×d視為無限)", 0.01, 10.0, 1.6, 0.01)
        z, eeff = tls.cpw_z0(s, w, h, er)
        success(f"CPW: {z:.2f} Ω（ε_eff={eeff:.3f}, DOC-002 §6.1 基準=78.33Ω）")
    elif sel == "Coax":
        di = c2.number_input("dᵢ (mm)", 0.01, 50.0, 1.0, 0.1)
        do = c3.number_input("dₒ (mm)", 0.02, 100.0, 3.0, 0.1)
        success(f"Coax: {tls.coax_z0(di, do, er):.2f} Ω")
    else:
        s = c2.number_input("間距 s (mm)", 0.05, 50.0, 2.0, 0.1)
        d = c3.number_input("線徑 d (mm)", 0.01, 10.0, 1.0, 0.05)
        success(f"Parallel Wire: {tls.parallel_wire_z0(s, d, er):.2f} Ω")

with sidebar:
  caption("文件：DOC-002（正向模型）→ DOC-003（本工具之合成推導）｜"
           "驗證基準：Mantaro 同源 ±1%，跨族 ±5%（IPC vs HJ 實測 3.35%）")
  subheader("🔧 PCB 傳輸線合成工具（DOC-003 配套）")
  caption("目標阻抗 → 線寬/間距　|　公式族：IPC-2141A / Mantaro 閉式＋DOC-002 保角映射　|　驗證殘差 ≤ 1e-13%")
