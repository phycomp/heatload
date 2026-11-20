# Presubmission enquiry — Cryogenics (Elsevier)

> 用途：投稿前禮貌性詢問（presubmission enquiry），寄至 Cryogenics editorial office。
> 聯絡：（依 web 查證 2026-11-20）`cryogenics@elsevier.com`（Cryogenics 官方 editorial email）；或透過 Editorial Manager 投稿系統的 "Send E-mail" 功能聯繫 Editors/Editorial Team。
> 查證限制：Elsevier 阻擋 editorial-board 頁面抓取，無法確認現任 Editor-in-Chief 姓名；故不指名特定 editor，改用官方 email / 投稿系統（不編造人名）。
> 對應稿件：`docs/heatload_distill_submission.md`（EN Nature-style 主稿）、`docs/heatload_distill_submission.zh.md`（ZH 對應稿）；`docs/heatload-distill_submission_compiled.md` 為不同的延伸稿，投稿時擇一主稿。

---

**To:** cryogenics@elsevier.com
**Subject:** Presubmission enquiry — "Provenance as a measurable property: rebuilding cryogenic thermal-conductivity data for superconducting interconnects"

Dear Editors,

We are writing to enquire whether the manuscript entitled "Provenance as a measurable property: rebuilding cryogenic thermal-conductivity data for superconducting interconnects" would be a suitable fit for *Cryogenics*.

The manuscript addresses a practical problem in cryogenic heat-load estimation: fitted thermal-conductivity functions κ(T) are widely reused, but the provenance, valid range and process dependence of their coefficients are often lost. We treat provenance as an auditable property. We show that passing internal structural and in-range behavioural checks does not imply material reliability, and we localise failures by rebuilding an independent database from the NIST cryogenic material-properties website and comparing coefficient arrays and curves against the existing source of truth under a shared nine-parameter log-log model. The analysis identifies two suspected coefficient mis-assignments and several low-order placeholder fits, while four entries match the NIST generic fits (a statement of source fidelity, not material-specific validity). We translate these findings into a bounded workflow for using cryogenic conductivity fits in nW-scale thermal budgeting.

What is new is the reframing of data provenance as a measurable, auditable property, together with an evidence-bounded comparison workflow — not new measurements or re-fitted coefficients. The work should interest readers concerned with cryogenic material-property data, thermal modelling of superconducting interconnects, and reliable heat budgeting for dilution-refrigerator systems, which fall within the scope of *Cryogenics*.

The supporting rebuilt database is publicly available for reproducibility: [nist_transmission_line_materials.json](https://raw.githubusercontent.com/phycomp/heatload/main/docs/nist_transmission_line_materials.json) and [nist_material_db_scraped.json](https://raw.githubusercontent.com/phycomp/heatload/main/docs/nist_material_db_scraped.json). All claims are bounded: no new measurements, no re-fitting, and no invented coefficients or citations are claimed.

We would appreciate the Editors' view on suitability and the preferred article type before formal submission.

Thank you for your consideration.

Sincerely,

Chun Hsing Lu (呂俊興)
Uleam Inc., Taoyuan city, Taiwan
josh.lu@u-leam.com

---

## Assumptions or missing inputs

- **Contact:** verified official journal email `cryogenics@elsevier.com` and Editorial Manager "Send E-mail"; no specific Editor-in-Chief name (Elsevier board page blocked 400 → not invented).
- **Article type:** to be confirmed with the journal (review/methods); not asserted here.
- **Scope/APC/template:** must be checked against the latest *Cryogenics* guide for authors before formal submission.
- **Journal fit statement:** connected to the journal's stated scope (cryogenic materials/thermal properties, superconducting & quantum cryogenic technologies); not an unsupported priority claim.
