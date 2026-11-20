# Heatload-Distill Consolidated Paper (compiled, final edition 2026-11-20)

> **Final edition:** adds §9–10 (NIST rebuild, transmission-line materials, coefficient mis-assignments, in-range curve comparison). Previous compiled edition retained unchanged at `docs/heatload-distill_paper_consolidated.md`.

> **Compiled by:** `scripts/distill_paper_compile_viz.py` (topic-viz Format F).  
> **Compiled at:** 2026-11-20T07:42:03.739912+00:00  
> **Compile order:** abstract, citation, chapter, rawdata (Appendix A), reference.  
> **Appendix A:** SSOT raw coefficient reference data (54 entries: 48 `log_polynomial`, 5 `rational_copper`, 1 `runtime_polyfit`) embedded same-source for traceability only; `NbTi (Cri/oFlex 3)` is `runtime_polyfit` with `coeffs=null` and receives no coefficients.  
> **Policy:** Evidence-bounded, same-source; D4=A SSOT; no refit, no invented coefficients/claims. `NbTi (Cri/oFlex 3)` is `runtime_polyfit` with `coeffs=null` (excluded from fixed-coefficient numeric relations). Check latest *Cryogenics* scope/guidelines/APC/article type before submission.

## Abstract

Low-temperature thermal budgeting in cryogenic engineering—including conduction through supports and interconnects in dilution-refrigerator systems—commonly relies on fitted representations of material thermal conductivity κ(T), especially 9-coefficient log-log polynomials (c0..c8 / a..i) and source-specific rational/RRR forms for selected materials[^nist][^marquardt][^bradley][^simon1992][^flynn][^raicu2025]. Recent high-density superconducting cabling work illustrates the practical stakes: Smith *et al.* estimated a 5 nW per-trace conductive heat load from 1 K to 100 mK for a 1-ft flexible Nb-47 wt% Ti coaxial ribbon cable by combining literature thermal-conductivity values with cable cross sections, and compared this to commercial coaxial and NbTi-on-polyimide flex options[^smith2024]. Such nW-scale estimates depend directly on which κ(T) data and fits are used, over what ranges they are valid, and how extrapolations are handled.

This paper presents **Heatload-Distill**, a provenance-grounded review and reliability-aware workflow for using 9-coefficient κ(T) fits in cryogenic heat-load estimation. The workflow organizes practice into four traceable steps: (1) literature and material-database provenance, (2) physical/model interpretation of the 9 parameters and heat-load equations, (3) matrix/least-squares solution and numerical conditioning, and (4) polyfit reliability validation. It is anchored to a single source of truth (SSOT, decision D4=A) and same-source artifacts (`topic-viz` Format F: specification + snapshot + offline HTML/Excel with graceful degradation and error disclosure).

Using `docs/9coeff_4step_flow.json` and associated artifacts, we review 54 database entries (48 `log_polynomial`, 5 `rational_copper`, 1 `runtime_polyfit`) and 53 fixed-coefficient materials for numeric coefficient–material relations; `NbTi (Cri/oFlex 3)` is `runtime_polyfit` with `coeffs=null` and is excluded from fixed-coefficient numeric relations. Existing validation evidence (synthetic log-log cubic-spline generator, 8th-order `np.polyfit`, T=2–300 K, N=50 log-spaced points, perturbation study) shows that in-range integrated conductivity (∫₂³⁰⁰ κ dT) is comparatively stable under tested perturbations, whereas deep-low-temperature extrapolation (e.g., κ at 20 mK) is highly sensitive to perturbations and fitting/process choices and should be treated only as an order-of-magnitude indicator. The evidence also shows strong ill-conditioning of the raw power basis, material-specific structural residual near NbTi Tc under a global 8th-order fit, and a large discrepancy between stored and validation-fit Kapton coefficients (max |Δc|≈79.48). We conclude that trustworthy cryogenic heat-load estimates require traceable provenance, explicit validity ranges, conditioning-aware interpretation, and disclosed uncertainty rather than isolated extrapolated values or undocumented coefficients.

**Keywords:** cryogenics, cryogenic thermal conductivity, 9-coefficient fit, heat-load estimation, dilution refrigerator, provenance, numerical conditioning, polyfit reliability, review

## Citations and Provenance (compiled)

> Compiled from sedimented distill sources (same-source, evidence-bounded). No unverified bibliographic details added. Submission policies/scope/APC/article type for *Cryogenics* must be checked against the latest journal guidelines before submission.

### Target and submission context
- Requested target (from `docs/heatload-distill_期刊候選.md`): **Cryogenics (Elsevier)**; review + reliability-aware workflow, not new measurements/re-fitting.
- **投稿門檻（誠實揭露）**：不得宣稱新量測物性或重擬合係數；須明示 SSOT（D4=A）、54 筆/53 固定係數、`NbTi (Cri/oFlex 3)` 為 `runtime_polyfit` 且 `coeffs=null`、條件數依實作/定義/來源/範圍/縮放而異、深低溫外推（如 k@20 mK）僅量級示意、擬合區間 ∫κdT 在測試擾動下相對穩定（條件性）、Kapton 係數流程敏感性、Tc 區結構殘差、環境相依缺失（streamlit/matplotlib/altair/plotly/scipy/openpyxl 等）導致互動/視覺降級或未驗證項目。Smith et al. 僅作已驗證動機/脈絡引用，本稿不重算或獨立驗證其數值。

### Provenance and SSOT boundary (same-source)
- SSOT (D4=A): `~/.opencode/skills/heatload-coff-nist/scripts/coeff_data.py`, `~/.opencode/skills/heatload-coff-nist/scripts/thermal_load.py`
- Database: **54** entries total (raw rows: 54); equation types: `log_polynomial`=48, `rational_copper`=5, `runtime_polyfit`=1.
- Fixed-coefficient numeric relations set: **53**; `NbTi (Cri/oFlex 3)` is `runtime_polyfit` with `coeffs=null` (excluded from fixed-coefficient numeric relations, no invented coeffs).
- Same-source snapshot: `docs/9coeff_4step_flow.json` (generated_at: `2026-11-19T10:48:13`, errors: 0).

### Key verified references (from provenance snapshot)
- **Raicu et al. (2025) Cryogenic thermal modeling of microwave high density signaling** — `10.1140/epjqt/s40507-025-00427-1`: Table 4: k(T) 9-coeff fits (outer/dielectric/PTFE/inner). Table 6: rho(T) inner. PTFE coeffs sourced from NIST Cryogenics Index [9,10] per Table 4 note.
- **NIST Cryogenics Index of Material Properties** — `https://trc.nist.gov/cryogenics/materials/materialproperties.htm`: Cryogenic material property fits (a..i 9 coefficients) and valid ranges; primary database source for many entries.
- **NIST Cryogenics Material Properties: Equations** — `https://trc.nist.gov/cryogenics/materials/materialproperties.htm (equations)`: log-log polynomial form log10(y)=a+b(log10 T)+...+i(log10 T)^8 and related equation types.
- **Marquardt, Le & Radebaugh (2000) Cryogenic Material Properties Database** — `https://cryocooler.org/resources/Documents/C11/247.pdf`: Defines 9-parameter (a..i) cryogenic material property fits.
- **Bradley et al. (2006) Cryogenic Material Properties Database, Update 2006**: Database update (referenced by sources).
- **Simon, Drexler & Reed (1992) Properties of Copper and Copper Alloys at Cryogenic Temperatures**: OFHC Cu rational-form conductivity data/fits (RRR variants).
- **Flynn, Cryogenic Engineering**: Textbook basis for cryogenic heat load / multi-stage modeling (cited in skill overview).
- **Kapton (Cri/oFlex 3) 9-coeff (project-derived, documented source)** — `熱負載/推導柔性多項式耦合系數.md L138-166 / 16柔性八階擬合.py context`: Stored 7-sig-fig coeffs in coeff_data with stated provenance; used as fixed-coeff material entry (distinct from runtime_polyfit NbTi).
- **NbTi (Cri/oFlex 3) — no fixed coefficients** — `熱負載/pages/16柔性八階擬合.py`: NBTI_COEFFS not a numeric constant (runtime np.polyfit on simulated PPMS-like data, seed/noise dependent); coeff_data marks N/A runtime_polyfit (no invention).
- **Smith et al. (2024)** Improved Flexible Coaxial Ribbon Cable for High-Density Superconducting Arrays — `doi:10.1109/TASC.2024.3350516`, arXiv:2306.13574: verified motivating/comparison context only (literature κ(T)+cross-section heat-load estimation; reported 5 nW/trace 1 K→100 mK for 1-ft in cited work). Not re-computed or extended here.

### Source roles (as recorded in manuscript)
| Source | Role in this review | Notes |
|---|---|---|
| Raicu et al. (2025), *EPJ Quantum Technology* 12:124[^raicu2025] | Cryogenic thermal modeling context for microwave high-density signaling; upstream linkage recorded in project citations | Application context; not a source for new coefficients here |
| NIST Cryogenics Index of Material Properties[^nist] | Primary cryogenic material-property database reference | Upstream database/properties context |
| Marquardt et al. (2000)[^marquardt] | Cryogenic material properties database (11th International Cryocooler Conference), as recorded | Bibliographic details limited to project record |
| Bradley et al. (2006)[^bradley] | Cryogenic material properties database update (ICEC 21), as recorded | Bibliographic details limited to project record |
| Simon et al. (1992), NIST Monograph 177[^simon1992] | Properties of copper/copper alloys at cryogenic temperatures; supports OFHC copper source context (incl. `rational_copper` usage) | Source context for rational/RRR-related forms |
| Flynn, *Cryogenic Engineering*[^flynn] | Foundational cryogenic engineering/thermal-load modeling context, as recorded | Edition/publisher details not fully specified in project record |
| Smith et al. (2024), *IEEE Trans. Appl. Supercond.* / arXiv:2306.13574[^smith2024] | Verified application example of literature-based cryogenic cable heat-load estimation and material/cross-section comparison | Motivating context only; no re-computation performed here |
**Citation policy.** References are limited to sources already present in project provenance files plus the user-specified, programmatically verified Smith *et al.* paper (DOI/arXiv metadata/BibTeX retrieved). No unverified bibliographic details or external claims are added.

## Chapters (compiled)

## 1. Introduction
### 1.1 Cryogenic heat-load estimation and the role of κ(T) fits
Cryogenic systems for superconducting electronics and quantum technologies impose strict thermal budgets across temperature stages. A common engineering task is to estimate conductive heat flow $Q=\frac{A}{L}\int_{T_c}^{T_h}\kappa(T)\,dT$ for cables, supports, and interconnects, sometimes combined with dissipative terms. For many materials, κ(T) is represented by compact fitted forms—most prominently 9-coefficient log-log polynomials and, for selected cases such as OFHC copper, source-specific rational/RRR relations—distributed through cryogenic material databases and prior modeling work[^nist][^marquardt][^bradley][^simon1992][^flynn][^raicu2025].

The impact of these representations is concrete. In the context of high-density superconducting arrays, Smith *et al.* reported improved 53 wt% Nb–47 wt% Ti flexible coaxial ribbon cables (FLAX) and computed per-trace heat loads by summing literature κ(T) values for constituent materials weighted by cross section; for a 1-ft cable they estimated 5 nW per trace from 1 K to 100 mK (approximately half that of the smallest commercially available superconducting coax in their comparison), while also noting material-dependent tradeoffs and assumptions in such calculations (e.g., use of PTFE data to estimate PFA, geometry/material weighting, and extrapolation in κ(T) data)[^smith2024]. This exemplifies a broader pattern: nW- to µW-scale design decisions can hinge on coefficient choice, valid temperature range, and extrapolation behavior.

### 1.2 Problem: precision without traceability
The central difficulty in reuse is often not the availability of coefficients, but the loss of context: where coefficients came from, over which temperature range they are valid, how they were obtained or solved numerically, and when extrapolated values become unreliable. A heat-load number may appear precise while resting on undocumented provenance, out-of-range evaluation, ill-conditioned fitting, or process-dependent coefficients. For cryogenic engineering practice, this creates avoidable risk in comparison, budgeting, and communication.

### 1.3 Aim and scope
**Aim.** To review and integrate a provenance-grounded, reliability-aware workflow—**Heatload-Distill**—for using 9-coefficient κ(T) fits in cryogenic heat-load estimation, based on existing SSOT records and validation artifacts.

**In scope.** Provenance/database records (SSOT), model forms and parameter interpretation, matrix/least-squares conditioning considerations, reliability-validation results, and their implications for heat-load estimation practice, organized as a same-source auditable chain.

**Out of scope.** New experimental measurements, re-fitting of SSOT fixed coefficients, invention of missing coefficients, promotion of runtime-fitted results to fixed material properties, and claims beyond cited/validated evidence (including any re-computation of third-party cable designs).

### 1.4 Contributions
- **Provenance-grounded review for cryogenic practice.** We frame trustworthy 9-coefficient heat-load estimation as a traceable chain spanning source/database, model, numerical solution, and validation boundaries, motivated by real cryogenic interconnect heat-load estimation needs[^smith2024][^raicu2025].
- **Same-source integration workflow.** We consolidate a four-step workflow and artifacts (specification, snapshot, offline HTML/Excel, snapshot-driven interactive view) aligned with SSOT decisions (D1–D6, D4=A) and traceable outputs.
- **Evidence-based reliability interpretation.** We synthesize existing evidence on conditioning, perturbation sensitivity, in-range integral stability, deep-low-temperature extrapolation uncertainty, coefficient/process sensitivity, and material-specific model-structure residuals (NbTi near Tc), and translate these into conservative usage guidance.
- **Target-journal relevance.** We position the work as a cryogenic engineering methods/review contribution on traceable and reliability-aware use of κ(T) fit data for heat-load estimation, not as a new material-property dataset.

## 2. Provenance and SSOT as the Basis for Heat-Load Estimates
### 2.1 Why provenance matters in cryogenic interconnect comparisons
Heat-load comparisons across cable or interconnect technologies can be sensitive to material-property assumptions. Smith *et al.* explicitly computed thermal conductivity/heat-load contributions by combining literature κ(T) values with cross-sectional areas, used PTFE values to estimate PFA, and reported extrapolated regions in their comparison, while discussing conductor- vs dielectric-dominated regimes depending on material systems[^smith2024]. This does not invalidate such estimates; rather, it highlights that defensible comparison requires transparent source, range, and extrapolation handling—precisely the information a provenance-grounded workflow must preserve.

### 2.2 Source roles (as recorded in project provenance)
| Source | Role in this review | Notes |
|---|---|---|
| Raicu et al. (2025), *EPJ Quantum Technology* 12:124[^raicu2025] | Cryogenic thermal modeling context for microwave high-density signaling; upstream linkage recorded in project citations | Application context; not a source for new coefficients here |
| NIST Cryogenics Index of Material Properties[^nist] | Primary cryogenic material-property database reference | Upstream database/properties context |
| Marquardt et al. (2000)[^marquardt] | Cryogenic material properties database (11th International Cryocooler Conference), as recorded | Bibliographic details limited to project record |
| Bradley et al. (2006)[^bradley] | Cryogenic material properties database update (ICEC 21), as recorded | Bibliographic details limited to project record |
| Simon et al. (1992), NIST Monograph 177[^simon1992] | Properties of copper/copper alloys at cryogenic temperatures; supports OFHC copper source context (incl. `rational_copper` usage) | Source context for rational/RRR-related forms |
| Flynn, *Cryogenic Engineering*[^flynn] | Foundational cryogenic engineering/thermal-load modeling context, as recorded | Edition/publisher details not fully specified in project record |
| Smith et al. (2024), *IEEE Trans. Appl. Supercond.* / arXiv:2306.13574[^smith2024] | Verified application example of literature-based cryogenic cable heat-load estimation and material/cross-section comparison | Motivating context only; no re-computation performed here |

**Citation policy.** References are limited to sources already present in project provenance files plus the user-specified, programmatically verified Smith *et al.* paper (DOI/arXiv metadata/BibTeX retrieved). No unverified bibliographic details or external claims are added.

### 2.3 SSOT database, coverage, and boundaries
- **SSOT (D4=A):** `~/.opencode/skills/heatload-coff-nist/scripts/coeff_data.py` and `thermal_load.py` (paths and summary recorded in `docs/9coeff_4step_flow.json`).
- **Database composition:** 54 material entries total — 48 `log_polynomial`, 5 `rational_copper`, 1 `runtime_polyfit`.
- **Fixed-coefficient analysis set:** 53 materials used for numeric coefficient–material relations.
- **Runtime-fit exception:** `NbTi (Cri/oFlex 3)` is `runtime_polyfit` with `coeffs=null` (source/notes in snapshot: runtime `np.polyfit` on seed=42 simulated data affected by `noise_pct`; no stored numeric constant). It is therefore **excluded from fixed-coefficient numeric relations** and not assigned invented coefficients.
- **Raw traceability:** Step 1 artifacts retain all 54 raw rows (material, equation type, valid range, c0..c8/coeffs, source, notes) for row-level inspection.
- **Project decisions (D1–D6):** non-destructive integration (B,D,D,A,A,C) preserving legacy assets while adding shared core/pages/same-source artifacts (see `docs/NIST9熱負載整合說明.md`, `docs/NIST9_視覺化規格.md`).

## 3. Models and Numerical Formulation
### 3.1 Thermal-conductivity and heat-load models
For most materials, κ(T) is represented in log-log polynomial form:
$$
\log_{10}\kappa(T)=\sum_{n=0}^{8} c_n \left(\log_{10}T\right)^n
$$
Some materials (e.g., OFHC copper entries in SSOT) use source-specific rational/RRR-based forms (`rational_copper`)[^simon1992][^nist][^marquardt][^bradley].

A common stage-wise conductive heat-load model used in project artifacts is:
$$
Q_{solid}=\sum_i \frac{A}{L_i}\int_{T_{c,i}}^{T_{h,i}}\kappa(T)\,dT
$$
with optional dissipative terms represented in artifacts as $Q_{rf}=\sum_i P_{in}\left(1-10^{-\alpha_i/10}\right)$ when applicable. Out-of-range handling and optional low-temperature extrapolation (e.g., $k(T)\sim T^\alpha$ below fit range in validation implementation context) must be interpreted conservatively; extrapolated values are not equivalent to validated material properties[^flynn][^raicu2025].

### 3.2 Physical temperature-zone calculation for 溫區擬合 (stage-wise conduction and length back-calculation)
To connect the general stage-wise integral $Q_{solid}$ in Section 3.1 with practical cryogenic interconnect sizing and temperature-zone evaluation (`溫區擬合`, temperature-zone fitting and stage-wise physical calculation), project derivation notes (`docs/溫區擬合_物理模型_來源萃取.md`) decompose the physical calculation into four conditional layers:

1. **Steady 1D Fourier conduction and stage-wise integral context.** Under steady one-dimensional axial conduction without intermediate thermal anchors, lateral radiative exchange, or distributed internal heat generation along segment $i$ of length $L_i$ $[\text{m}]$ and effective cross-sectional area $A$ $[\text{m}^2]$, the conductive heat load $Q_i$ (or $P_i$) $[\text{W}]$ across temperature bounds $(T_{c,i}, T_{h,i})$ $[\text{K}]$ is governed by the nonlinear Fourier definite integral:
   $$
   Q_i = \frac{A}{L_i}\int_{T_{c,i}}^{T_{h,i}}\kappa(T)\,dT = \frac{A}{L_i}I_i, \qquad I_i = \int_{T_{c,i}}^{T_{h,i}}\kappa(T)\,dT \ \left[\text{W}\cdot\text{m}^{-1}\right]
   $$
   In project benchmark derivations (`~/量傳線/三視圖/柔性/驗證/對標CF3規格電性熱負載物理推導.md` and `~/量傳線/溫區擬合/03_熱傳導與熱導率模型/傅立葉導熱定律回推長度.md`), this stage-wise formulation is evaluated against sourced vendor reference stages—such as the $4\text{–}40\text{ K}$ stage ($\Delta T=36\text{ K}$, $L=0.4\text{ m}$, benchmark $<125\ \mu\text{W}/\text{ch}$) and the $10\text{–}350\text{ mK}$ stage ($\Delta T=340\text{ mK}$, $L=0.2\text{ m}$, benchmark $\sim 20\text{ nW}/\text{ch}$)—strictly as sourced specification/derivation context rather than new experimental measurements.

2. **Simplified special cases: constant/average $\kappa$ and Wiedemann–Franz ($\rho=\text{const}$) analytical limit.** Over a narrow temperature interval or for order-of-magnitude scaling, replacing $\kappa(T)$ by its interval average $\kappa_{avg}=\frac{1}{\Delta T}\int_{T_c}^{T_h}\kappa(T)\,dT$ yields the linear approximation $Q \approx \frac{\kappa_{avg}A}{L}\Delta T$ ($\Delta T = T_h - T_c$). For normal-state metals in the low-temperature elastic impurity-scattering regime where electrical resistivity is approximately constant ($\rho(T)\approx \rho_0=\text{const}$, electrical resistance $R=\rho L/A$), combining Fourier conduction with the Wiedemann–Franz law $\kappa_e(T) = L_0 T/\rho$ ($L_0 \approx 2.44\times 10^{-8}\ \text{W}\cdot\Omega\cdot\text{K}^{-2}$) gives the closed-form quadratic temperature relation (`~/量傳線/溫區擬合/03_熱傳導與熱導率模型/基礎推導熱負載.md`):
   $$
   Q = \frac{L_0 A}{2\rho L}\left(T_h^2 - T_c^2\right) = \frac{L_0 T_{avg}\Delta T}{R}, \qquad \kappa_{avg} = \frac{L_0 T_{avg}}{\rho}, \quad T_{avg}=\frac{T_h+T_c}{2}
   $$
   (with DC Joule heating $I^2 R$ additive when bias current $I$ is present, while microwave attenuation dissipation connects to $Q_{rf}$ in Section 3.1). This quadratic formula is strictly conditional: it does **not** apply to amorphous dielectric substrates such as polyimide/Kapton (dominated by phonon boundary and two-level-system scattering), nor to superconductors below their critical temperature (e.g., NbTi below $T_c \approx 9.2\text{–}9.8\text{ K}$, where Cooper-pair condensation suppresses electronic thermal conduction exponentially and invalidates the Wiedemann–Franz relation), nor to higher-temperature inelastic scattering regimes where $\rho(T)$ varies strongly (`~/量傳線/溫區擬合/04_溫區長度回推與約束/推導溫區公式.md`; piecewise power-law expressions in that note serve only as qualitative physical mechanism illustrations, whereas all formal calculations remain bound to the SSOT D4=A database in Section 2.3).

3. **Ratio of thermal integrals and area-normalized length back-calculation.** Because multi-layer flexible cables contain composite conductor/dielectric cross sections whose effective area $A$ is difficult to decompose precisely from external datasheets alone, the derivation in `~/量傳線/溫區擬合/03_熱傳導與熱導率模型/傅立葉導熱定律回推長度.md` normalizes a target temperature zone ("$\text{image}$") against a reference zone ("$\text{ref}$") of **identical cross-sectional geometry and material stack-up** ($A_{image}=A_{ref}$):
   $$
   I_{ref}=\int_{T_{c,ref}}^{T_{h,ref}}\kappa(T)\,dT, \qquad I_{image}=\int_{T_{c,image}}^{T_{h,image}}\kappa(T)\,dT
   $$
   $$
   \frac{P_{image}}{P_{ref}} = \frac{L_{ref}}{L}\left(\frac{I_{image}}{I_{ref}}\right) \implies L = L_{ref}\left(\frac{P_{ref}}{P_{image}}\right)\left(\frac{I_{image}}{I_{ref}}\right)
   $$
   where $I_{image}/I_{ref}$ is the temperature-zone thermal-integral ratio (illustrated in the source note by expanding a $40\text{ K}\to 4\text{ K}$ reference stage with $L_{ref}=40\text{ cm}, P_{ref}=125\ \mu\text{W}$ to a $50\text{ K}\to 4\text{ K}$ target stage with an example integral ratio $I_{image}/I_{ref}=1.48$). This cancellation of $A$ fails whenever comparing heterogeneous stack-ups (e.g., a 7-layer $300\ \mu\text{m}$ GSG flex versus an 11-layer $144.1\ \mu\text{m}$ FPC with plated through-holes), in which case explicit layer-wise area ratios $\sum_k A_k\int\kappa_k(T)\,dT$ must be retained.

4. **Ultra-low-temperature profile assumptions, qubit decoherence threshold, and safe-length limitations.** In the millikelvin stage ($10\text{–}350\text{ mK}$), exploratory notes (`~/量傳線/溫區擬合/02_極低溫溫區與熱負載/crioFlex3回推量子比特溫區長度.md` and `~/量傳線/溫區擬合/04_溫區長度回推與約束/最大安全長度.md`) couple cable temperature profiles to a transmon thermal-excitation threshold. For a transmon with $f_{01}=5.5\text{ GHz}$ ($\alpha=-250\text{ MHz}$), requiring excited-state thermal occupancy $P_{|1\rangle}=\exp(-hf_{01}/k_B T)<1\%$ (or $n_{th}=[\exp(hf_{01}/k_B T)-1]^{-1}<0.01$) yields a critical temperature $T_{crit}\approx 57.6\text{ mK}$. Under a **simplified constant-$\kappa$, unanchored linear temperature profile** $T(x)=T_c+(T_h-T_c)(x/L)$ from $T_c=10\text{ mK}$ to $T_h=350\text{ mK}$, the cold-end region below $T_{crit}$ spans $x_{safe}=L(T_{crit}-T_c)/(T_h-T_c)\approx 2.8\text{ cm}$ for $L=20\text{ cm}$, and requiring a $x_{req}=5\text{ cm}$ safe zone back-calculates to $L_{new}=x_{req}(T_h-T_c)/(T_{crit}-T_c)\approx 35.7\text{ cm}$ (whereas an alternative exploratory assumption with distributed self-heating $\Delta T\propto L^2$ gives $L_{\max}\approx 7.5\text{ cm}$). These back-calculated lengths are highly sensitive to boundary assumptions: because $\kappa(T)$ varies strongly in the mK regime, steady flux conservation $\kappa(T)\frac{dT}{dx}=\text{const}$ produces a nonlinear temperature profile, practical dilution refrigerators enforce stage thermal anchoring and microwave filtering/attenuation rather than relying on an unanchored span, and SSOT polynomial fits (typically valid at $\ge 1\text{–}4\text{ K}$, with `NbTi (Cri/oFlex 3)` having `coeffs=null` as `runtime_polyfit`) cannot be extrapolated to $10\text{–}350\text{ mK}$ as validated material properties.

### 3.3 Least-squares/matrix view of 9-parameter fitting
With $x_i=\log_{10}T_i$ and $y_i=\log_{10}\kappa(T_i)$, the polynomial model can be written as
$$
y_i \approx \sum_{j=0}^{8} c_j x_i^j,\quad X_{i,j}=x_i^j,\quad y \approx Xc
$$
and solved by least squares (e.g., normal equations $X^T X c = X^T y$ or numerically more stable equivalents). Coefficients admit practical interpretation ($c_0$ scale, $c_1$ dominant trend, higher-order terms curvature/detail), but in a high-order monomial basis they are correlated and can be sensitive to noise, scaling, range, and implementation details; they should not be treated as independent microscopic constants.

### 3.4 Numerical conditioning
Raw monomial/Vandermonde-like bases for this fit are strongly ill-conditioned. Centering/scaling can improve conditioning, but reported condition numbers depend on implementation, definition, source data, temperature range, and scaling convention. Conditioning must therefore be reported and interpreted in context before drawing conclusions from coefficient values or derived extrapolations.

## 4. Heatload-Distill Workflow and Same-Source Artifacts
### 4.1 Artifact contract
- **Specification:** `docs/9coeff_4step_視覺化規格.md`
- **Same-source snapshot:** `docs/9coeff_4step_flow.json` (`errors: 0`, generated 2026-11-19T10:48:13)
- **Offline artifacts:** `docs/9coeff_4step_demo.html`, `docs/9coeff_4step_demo.xlsx`
- **Interactive view:** `scripts/9coeff_4step_streamlit_demo.py` (snapshot-driven, graceful degradation) and wrapper `熱負載/pages/32_9coeff_4step_demo.py`
- **Generator:** `scripts/9coeff_4step_viz.py`

### 4.2 Four-step traceability chain
| Step | Objective | Primary evidence/artifacts | Boundary |
|---|---|---|---|
| 1. Literature and material database | Fix provenance and inspectable inputs | 54 raw rows, provenance anchors, SSOT paths | `NbTi (Cri/oFlex 3)` explicitly marked `runtime_polyfit`, `coeffs=null` |
| 2. Physical/model derivation of 9 parameters | Explain how parameters enter κ(T) and heat-load models | Model forms, $Q_{solid}$/$Q_{rf}$, range/extrapolation rules | Out-of-range/extrapolation requires conservative interpretation |
| 3. Matrix solution of 9 parameters | Explain least-squares solution, conditioning, coefficient relations | Design-matrix/normal-equation view, conditioning/scaling caveats, 53-material fixed-coefficient relations | Condition numbers are context-dependent; NbTi excluded from fixed-coefficient numeric relations |
| 4. Polyfit reliability validation | Separate comparatively stable outputs from sensitive boundaries | `docs/polyfit_可靠度驗證.md/json`, snapshot Step 4 summary | Validation bounds credibility; it does not establish new material properties |

### 4.3 Non-destructive integration context
Following decisions D1–D5, shared core modules and pages were added/refactored (e.g., `src/量傳線設計/核心/熱負載NIST9.py`, new/updated pages and legacy backups) while preserving existing assets and aligning calculations/displays with SSOT. Offline artifacts are inspectable; interactive/visual outputs may degrade or remain unverified at runtime when dependencies (`streamlit`, plotting/scientific/Excel libraries) are unavailable.

## 5. Reliability Evidence Review (Kapton and NbTi Cases)
> **Evidence basis:** `docs/polyfit_可靠度驗證.md`, `docs/polyfit_可靠度驗證.json`, and `docs/9coeff_4step_flow.json` (Step 4). This section reviews existing validation outputs only.

### 5.1 Validation setup (as reported)
- Data generation: `scipy.CubicSpline(log-log)` (reported with `HAVE_SCIPY=True`)
- Fit: $\log_{10}(k)=\sum_{n=0}^{8} c_n (\log_{10}T)^n$, n=0..8 via `np.polyfit(x,y,8)`
- Sampling: T = 2–300 K, N = 50, log-spaced
- Low-temperature extrapolation in implementation: for $T < T_{min}$, $k(T)=T^\alpha$ (α defined from endpoint behavior)
- Perturbation study: noise ∈ {0,1,2,5}%, seeds = 6 (24 runs per material)

### 5.2 Conditioning and baseline results
| Quantity | Reported value / observation | Interpretation |
|---|---:|---|
| cond(V)_raw | 1.309×10^7 | Severe ill-conditioning of raw monomial basis |
| cond(V^T V)_raw | 1.713×10^14 | Amplified conditioning in normal-equation form |
| cond(V_centered_scaled) | 5.256×10^4 | Improved by centering/scaling in this setup; high-order sensitivity remains |

| Metric | Kapton (baseline, noise=1%, seed=42) | NbTi (baseline) | Interpretation |
|---|---:|---:|---|
| R² | 0.999976 | 0.990847 | Good in-range fit; lower for NbTi |
| RMSE (log10) | 0.003461 | 0.121327 | Larger residuals for NbTi |
| α_extrap | -10.2796 | -9.2815 | Implementation-defined extrapolation exponent |
| k(20 mK) [W/m/K] | 2.916×10^17 | 5.875×10^15 | Deep extrapolation, highly uncertain (indicator only) |
| ∫₂³⁰⁰ κ dT [W/m] | 28.907 | 2226.46 | Comparatively stable in-range integral in this validation |
| Tc-region max \|resid_log10\| | — | 0.492 (~7.5–12.5 K samples) | Structural residual near NbTi transition under global 8th-order polynomial |

### 5.3 Perturbation sensitivity and provenance checks
- **Kapton (24 runs):** k(20 mK) range 1.904×10^17–3.968×10^17 W/m/K; ∫₂³⁰⁰ κ dT range 28.737–29.497 W/m.
- **NbTi (24 runs):** k(20 mK) range 3.837×10^15–7.995×10^15 W/m/K; ∫₂³⁰⁰ κ dT range 2209.92–2271.26 W/m; Tc-region structural residual persists.
- **Interpretation:** Within the tested perturbation protocol, in-range integrals remained comparatively stable, while deep-low-temperature extrapolated k(20 mK) varied by roughly a factor of ~2 in reported runs but lies far outside the fit range and is sensitive to fitting/process choices. These extrapolated values should be treated only as conservative order-of-magnitude indicators, not reliable predictions. The result does **not** generalize to arbitrary materials, geometries, temperature ranges, or fitting pipelines.
- **Kapton coefficient provenance check:** Stored/source coefficients and validation-fit coefficients differ substantially (`max_abs_diff ≈ 79.48` in snapshot summary), consistent with process/generator dependence and reinforcing provenance requirements.
- **NbTi status:** SSOT records `runtime_polyfit` with `coeffs=null`; no fixed coefficient set is available or invented.

## 6. Discussion and Practical Guidance for Cryogenic Heat-Load Estimation
1. **Start from provenance and range, not coefficient availability.** As illustrated by cryogenic cable heat-load calculations based on literature κ(T) and geometry weighting[^smith2024], defensible estimates require explicit source, material mapping, and valid temperature intervals; `runtime_polyfit`/missing fixed coefficients must remain visible.
2. **Use integrals in-range when supported, treat extrapolation conservatively.** In the reported validation, ∫₂³⁰⁰ κ dT was comparatively stable under perturbations, while k(20 mK) was highly sensitive and far outside the fit range—suitable only as an order-of-magnitude indicator, not a reliable point prediction.
3. **Report numerical/fit context with coefficients.** High-order monomial fits are ill-conditioned (raw cond(V)=1.309×10^7, cond(V^T V)=1.713×10^14, centered/scaled 5.256×10^4 in this setup); condition numbers and coefficient values depend on implementation/definition/source/range/scaling.
4. **Acknowledge material/model limits.** NbTi exhibits structural residual near Tc under a global 8th-order polynomial, indicating that a single functional form may be inadequate in transition regions; this draft documents the limitation without proposing or fitting a replacement model.
5. **Preserve auditable artifacts.** Same-source specification/snapshot/offline outputs and disclosed errors/degradations (`errors: 0` in snapshot) support traceability; environment-dependent interactive verification should be reported rather than assumed.

## 7. Limitations
- This is a review/integration of existing project evidence, not a new experimental or re-fitting study.
- Database coverage and equation types are constrained by SSOT and upstream sources; full material/process uncertainty is not quantified.
- Reliability conclusions are conditional on the reported synthetic-data and perturbation protocol and do not generalize without further validation.
- Runtime verification of all interactive/visual components is environment-dependent; offline same-source artifacts are the primary auditable record in constrained environments.
- The motivating cable example (Smith *et al.*) is used only as verified context; this manuscript does not re-compute or independently validate third-party heat-load numbers.
- Journal suitability, article type, and submission requirements must be confirmed against current *Cryogenics* guidelines (see `docs/heatload-distill_期刊候選.md`).

## 8. Conclusion
Heatload-Distill consolidates provenance, modeling, numerical-solution context, and reliability evidence for 9-coefficient cryogenic κ(T) heat-load estimation into a four-step, same-source, auditable workflow. Evidence from SSOT records and validation artifacts supports a clear boundary for cryogenic engineering use: in-range integrated quantities can be comparatively stable under tested conditions, while deep-low-temperature extrapolations and high-order coefficients are sensitive to perturbations, process choices, and numerical conditioning, with material-specific structural residuals in transition regions (e.g., NbTi near Tc). Trustworthy heat-load estimates should therefore be based on traceable provenance, explicit validity ranges, and disclosed uncertainty—not on undocumented or isolated extrapolated values.


## 9. Rebuilding the Coefficient Database from NIST and Curve Comparison
> **New work (2026-11-20):** evidence-bounded; independent new DB, SSOT unchanged; no refit.

To test whether the SSOT fixed coefficients remain faithful to their authoritative source, an independent database was rebuilt from the NIST cryogenic material-properties website (`https://trc.nist.gov/cryogenics/materials/materialproperties.htm`, fetched 2026-11-20). A requests-based scraper retrieved 42 material pages, extracting thermal-conductivity a–i coefficients, data/equation ranges, and fit errors; seven pages without a conductivity table or returning 404 were recorded as `errors` and excluded without guessing values. Sources: `docs/nist_material_db_scraped.json`.

The scope was narrowed to cryogenic transmission-line materials — conductors/shields (OFHC Cu RRR variants, stainless steel 304/304L/316, BeCu, brass, Invar) and dielectrics (PTFE, polyimide/Kapton) — mapped to cable components from verified literature: SC-086/50-SCN-CN semi-rigid coax (C7150/Ag-C7150/PTFE; Raicu 2025), FLAX (Nb47Ti + PFA; Smith 2020/2024), Cri/oFlex 3 (NbTi + Kapton), and stainless/NbTi coax (Krinner 2019). C7150, Ag-coated C7150, PFA and NbTi have no NIST web entry and remain as SSOT literature-based entries. Sources: `docs/nist_transmission_line_materials.json` (9 cable-material entries).

Under the same nine-parameter log-log model, the new DB and SSOT were compared at log-spaced temperatures restricted to their **common fitted range** — out-of-range points (e.g. 293 K for brass, valid only to 116 K) were excluded so that 8th-order polynomial extrapolation could not be mistaken for a fitted result. Results (`docs/nist_transmission_line_curve_compare.json`):
- **4/8 exact matches**: Kapton and stainless steel 304/304L/316 (0% difference at 293 K) — the SSOT coefficients are faithful to NIST for these entries.
- **Coefficient mis-assignments confirmed**: `Polyamide (Nylon)` carries the NIST PTFE coefficients (a₀=2.738 vs NIST Nylon a₀=−2.6135); `Polyethylene Terephthalate (Mylar)` carries the NIST Nylon coefficients; `Raicu dielectric (PTFE)` also carries the PTFE coefficients. Thirteen coefficient-signature flags in total identify such cross-assignments and shared low-order fits.
- **In-range divergence**: PTFE +357.6% at 293 K (SSOT low-order fit 0.0596 vs NIST full fit 0.2726 W m⁻¹ K⁻¹); brass +986.5% at 77 K (SSOT c₅–c₈=0 giving 3.66 vs NIST 39.8 W m⁻¹ K⁻¹, 77 K inside the 5–116 K range); Invar +742.1% at 293 K. These are fitted-range differences, not extrapolation artefacts.

Mechanistic interpretation (evidence-bounded): low-order placeholder fits (trailing zero coefficients) are idealized approximations suitable for order-of-magnitude screening, not material-specific comparison; cross-assignments arise when coefficient arrays are copied between entries with distinct upstream sources; and polymer κ is process-sensitive (Zhou 2019; Drobizhev 2017), while phonon power-law exponents in crystals depend on defect/stress distributions (van Ostaay 2018). The comparison does not determine which value is physically correct for a given cable and performs no re-fitting; it establishes source fidelity and in-range self-consistency only.

## 10. Implications for Heat-Load Estimation
> **New work (2026-11-20):** bounded usage guidance.

The rebuilt comparison adds a boundary to the earlier reliability review: in-range integrals were previously found comparatively stable under perturbation, whereas deep-low-temperature extrapolation was highly sensitive. This work shows that, even within the fitted range, coefficient identity and process dependence can shift κ by several fold. For a multi-layer flexible cable the passive load is Σₖ (Aₖ/L)∫κₖ(T)dT; a mis-assigned or idealized coefficient for one layer can bias the nW-scale total that governs qubit thermalisation. Conductor and dielectric values for a specific cable should therefore come from that cable's measured fits, with generic database values used only for screening. A supporting curve comparison figure is provided at `docs/低溫傳輸線_新DB曲線對照.svg` (four panels, exact/mismatch labelled, in-range only). Full interpretation: `docs/低溫傳輸線材料_新DB重建與曲線驗證.md`; concept validation: `docs/係數資料庫_自洽卻不可信_概念驗證.md`; significance/physical interpretation: `docs/低溫傳輸線資料庫重建_意義與物理解釋.md`.


## Appendix A. SSOT Raw Coefficient Reference Data (54 entries)

> **Role:** reference/appendix only — provenance context, **not new measurements and not a re-fit**; conclusions in the body are not rewritten by this appendix.  
> **Source (same-source):** SSOT D4=A snapshot `docs/9coeff_4step_flow.json` → `steps[id=1].database.raw_materials`, **54** rows in snapshot order.  
> **Breakdown:** 54 = `log_polynomial`=48, `rational_copper`=5, `runtime_polyfit`=1; **53** entries support fixed-coefficient numeric relations.  
> **Exclusion:** `NbTi (Cri/oFlex 3)` is `runtime_polyfit` with `coeffs=null` (produced at runtime by `np.polyfit`, sensitive to `noise_pct`); **no coefficients are assigned to it here**, and it stays excluded from fixed-coefficient numeric relations.  
> **Reading note:** `c0..c8` are transcribed verbatim per row for traceability only; `valid_range_K` is `null` in 54/54 rows (no range recorded in the SSOT, not back-filled). No row is new data, a re-fit, or an extrapolation licence.  
> **Rendering:** `|` inside cells is escaped, newlines flattened, and long `source`/`note` values truncated (`…`).

| # | material | category | equation_type | valid_range_K | c0 | c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 | source | note |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | Aluminum 1100 (UNS A91100) | Metal | log_polynomial | null | 0.07918 | 1.0957 | -0.07277 | 0.08084 | 0.02803 | -0.09464 | 0.04179 | -0.00571 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 2 | Aluminum 3003-F (UNS A93003) | Metal | log_polynomial | null | 0.23733 | 0.48068 | -0.17101 | 0.06534 | -0.01659 | -0.00579 | 0.00444 | -0.00089 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 3 | Aluminum 5083-O (UNS A95083) | Metal | log_polynomial | null | -0.57148 | 1.5397 | -0.97109 | 0.44247 | -0.13926 | 0.02341 | -0.00101 | -0.0005 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 4 | Aluminum 6061-T6 (UNS A96061) | Metal | log_polynomial | null | 0.07918 | 1.0957 | -0.07277 | 0.08084 | 0.02803 | -0.09464 | 0.04179 | -0.00571 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 5 | Aluminum 6063-T5 (UNS A96063) | Metal | log_polynomial | null | 0.07918 | 1.0957 | -0.07277 | 0.08084 | 0.02803 | -0.09464 | 0.04179 | -0.00571 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 6 | Beryllium | Metal | log_polynomial | null | 1.442 | -0.159 | 0.193 | -0.073 | 0.011 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 7 | Beryllium Copper | Metal | log_polynomial | null | -0.50015 | 1.9319 | -1.6954 | 0.71218 | 1.2788 | -1.6145 | 0.68722 | -0.10501 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 8 | Brass (UNS C2600) | Metal | log_polynomial | null | -0.786 | 1.37 | -0.5 | 0.1 | -0.01 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 9 | Copper (OFHC) RRR=50 | Metal | rational_copper | null | 1.8743 | -0.41538 | -0.6018 | 0.13294 | 0.26426 | -0.0219 | -0.051276 | 0.0014871 | 0.003723 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 10 | Copper (OFHC) RRR=100 | Metal | rational_copper | null | 2.2154 | -0.47461 | -0.88068 | 0.13871 | 0.29505 | -0.02043 | -0.04831 | 0.001281 | 0.003207 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 11 | Copper (OFHC) RRR=150 | Metal | rational_copper | null | 2.3797 | -0.4918 | -0.98615 | 0.13942 | 0.30475 | -0.019713 | -0.046897 | 0.0011969 | 0.0029988 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 12 | Copper (OFHC) RRR=300 | Metal | rational_copper | null | 1.357 | 0.3981 | 2.669 | -0.1346 | -0.6683 | 0.01342 | 0.05773 | 0.0002147 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 13 | Copper (OFHC) RRR=500 | Metal | rational_copper | null | 2.8075 | -0.54074 | -1.2777 | 0.15362 | 0.36444 | -0.02105 | -0.051727 | 0.0012226 | 0.0030964 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 14 | Inconel 718 (UNS N107718) | Metal | log_polynomial | null | -8.28921 | 39.447 | -83.4353 | 98.169 | -67.2088 | 26.7082 | -5.7205 | 0.51115 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 15 | Indium | Metal | log_polynomial | null | 1.5 | -0.5 | 0.1 | -0.02 | 0.003 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 16 | Invar (Fe-36Ni) (UNS K93600) | Metal | log_polynomial | null | -0.5 | 0.8 | -0.3 | 0.05 | -0.005 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 17 | Lead | Metal | log_polynomial | null | 38.963479 | -221.40505 | 597.56622 | -900.93831 | 816.40461 | -455.08342 | 152.94025 | -28.451163 | 2.2516244 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 18 | Molybdenum | Metal | log_polynomial | null | 1.8 | -0.3 | 0.05 | -0.008 | 0.001 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 19 | Nickel Steel Fe 2.25 Ni | Metal | log_polynomial | null | -0.3 | 0.5 | -0.2 | 0.03 | -0.003 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 20 | Nickel Steel Fe 3.25 Ni (UNS S20103) | Metal | log_polynomial | null | -0.3 | 0.5 | -0.2 | 0.03 | -0.003 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 21 | Nickel Steel Fe 5.0 Ni (UNS S20153) | Metal | log_polynomial | null | -0.3 | 0.5 | -0.2 | 0.03 | -0.003 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 22 | Nickel Steel Fe 9.0 Ni (UNS S21800) | Metal | log_polynomial | null | -0.3 | 0.5 | -0.2 | 0.03 | -0.003 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 23 | Platinum | Metal | log_polynomial | null | 1.5 | -0.3 | 0.05 | -0.008 | 0.001 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 24 | Stainless Steel 304 (UNS S30400) | Metal | log_polynomial | null | -1.4087 | 1.3982 | 0.2543 | -0.626 | 0.2334 | 0.4256 | -0.4658 | 0.165 | -0.0199 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 25 | Stainless Steel 304L (UNS S30403) | Metal | log_polynomial | null | -1.4087 | 1.3982 | 0.2543 | -0.626 | 0.2334 | 0.4256 | -0.4658 | 0.165 | -0.0199 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 26 | Stainless Steel 310 (UNS S31000) | Metal | log_polynomial | null | -1.4087 | 1.3982 | 0.2543 | -0.626 | 0.2334 | 0.4256 | -0.4658 | 0.165 | -0.0199 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 27 | Stainless Steel 316 (UNS S31600) | Metal | log_polynomial | null | -1.4087 | 1.3982 | 0.2543 | -0.626 | 0.2334 | 0.4256 | -0.4658 | 0.165 | -0.0199 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 28 | Ti-6Al-4V (UNS R56400) | Metal | log_polynomial | null | -5107.8774 | 19240.422 | -30789.064 | 27134.756 | -14226.379 | 4438.2154 | -763.07767 | 55.796592 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 29 | Apiezon N | Nonmetal | log_polynomial | null | -1.5 | 0.8 | -0.2 | 0.03 | -0.003 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 30 | Balsa | Nonmetal | log_polynomial | null | -2 | 0.5 | -0.1 | 0.01 | 0 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c4–c8=0（如實補 0） |
| 31 | Beechwood/phenolic | Nonmetal | log_polynomial | null | -1.8 | 0.6 | -0.15 | 0.02 | 0 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c4–c8=0（如實補 0） |
| 32 | Fiberglass Epoxy G-10 (Normal) | Nonmetal | log_polynomial | null | -4.1236 | 13.788 | -26.068 | 26.272 | -14.663 | 4.4954 | -0.6905 | 0.0397 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 33 | Fiberglass Epoxy G-10 (Warp) | Nonmetal | log_polynomial | null | -2.64827 | 8.80228 | -24.8998 | 41.1625 | -39.8754 | 23.1778 | -7.95635 | 1.48806 | -0.11701 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 34 | Glass Fabric/polyester | Nonmetal | log_polynomial | null | -1.5 | 0.5 | -0.1 | 0.01 | 0 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c4–c8=0（如實補 0） |
| 35 | Glass mat/epoxy | Nonmetal | log_polynomial | null | -1.5 | 0.5 | -0.1 | 0.01 | 0 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c4–c8=0（如實補 0） |
| 36 | Kevlar-49 Fiber (Aramid) | Nonmetal | log_polynomial | null | -1 | 0.3 | -0.05 | 0.005 | 0 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c4–c8=0（如實補 0） |
| 37 | Kevlar-49 Composite (Aramid) | Nonmetal | log_polynomial | null | -1 | 0.3 | -0.05 | 0.005 | 0 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c4–c8=0（如實補 0） |
| 38 | Polyamide (Nylon) | Nonmetal | log_polynomial | null | 2.738 | -30.677 | 89.43 | -136.99 | 124.69 | -69.556 | 23.32 | -4.3135 | 0.33829 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 39 | Polyethylene Terephthalate (Mylar) | Nonmetal | log_polynomial | null | -2.6135 | 2.3239 | -4.7586 | 7.1602 | -4.9155 | 1.6324 | -0.2507 | 0.0131 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 40 | Polyimide (Kapton) | Nonmetal | log_polynomial | null | 5.73101 | -39.5199 | 79.9313 | -83.8572 | 50.9157 | -17.9835 | 3.42413 | -0.27133 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 41 | Polystyrene (density 2 lb/ft3) | Nonmetal | log_polynomial | null | -1145.45 | 4086.02 | -6234.293 | 5260.106 | -2649.914 | 797.0372 | -132.5244 | 9.3968 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 42 | Polystyrene (density 3.12 lb/ft3) | Nonmetal | log_polynomial | null | -1.5194 | -4.6449 | 11.643 | -15.969 | 12.722 | -5.821 | 1.4174 | -0.14128 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c8=0 |
| 43 | Polystyrene (density 6.24 lb/ft3) | Nonmetal | log_polynomial | null | 7.39582 | -59.6737 | 160.58 | -240.33 | 218.817 | -124.155 | 42.9088 | -8.26683 | 0.68082 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… |  |
| 44 | Polyurethane | Nonmetal | log_polynomial | null | -1.5 | 0.5 | -0.1 | 0.01 | 0 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c4–c8=0（如實補 0） |
| 45 | Polyvinyl Chloride (PVC) | Nonmetal | log_polynomial | null | -1.5 | 0.5 | -0.1 | 0.01 | 0 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c4–c8=0（如實補 0） |
| 46 | Sapphire | Nonmetal | log_polynomial | null | 3 | -0.5 | 0.1 | -0.02 | 0.003 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 47 | Silicon | Nonmetal | log_polynomial | null | 3.5 | -0.6 | 0.12 | -0.02 | 0.003 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c5–c8=0（如實補 0） |
| 48 | Teflon (PTFE) | Nonmetal | log_polynomial | null | -2 | 0.5 | -0.1 | 0.01 | 0 | 0 | 0 | 0 | 0 | NIST Cryogenics Index of Material Properties（經 量傳線/熱負載/pages/10nist低溫庫.py）；Marquardt/Le/Radebaugh 2000、Bradle… | 原始低階擬合：c4–c8=0（如實補 0） |
| 49 | Raicu outer (C7150) | k(T) | log_polynomial | null | -3.198399 | 20.49947 | -66.11415 | 117.6898 | -121.4773 | 76.21467 | -28.74949 | 5.984756 | -0.5266892 | Raicu et al. 2025, EPJQT 12:124, Table 4 (k(T)) |  |
| 50 | Raicu dielectric (PTFE) | k(T) | log_polynomial | null | 2.738 | -30.677 | 89.43 | -136.99 | 124.69 | -69.556 | 23.32 | -4.3135 | 0.33829 | Raicu et al. 2025, EPJQT 12:124, Table 4 (k(T))；PTFE 源自 NIST DB [9,10] |  |
| 51 | Raicu inner (Ag-coated C7150) | k(T) | log_polynomial | null | -2.750003 | 25.84512 | -74.18405 | 113.5856 | -96.84387 | 46.38328 | -11.82451 | 1.321682 | -0.02456645 | Raicu et al. 2025, EPJQT 12:124, Table 4 (k(T)) |  |
| 52 | Raicu rho inner (Table 6) | rho(T) | log_polynomial | null | -8.327474 | 10.01214 | -52.83315 | 122.547 | -152.7599 | 109.0327 | -44.41614 | 9.598158 | -0.8539285 | Raicu et al. 2025, EPJQT 12:124, Table 6 (rho(T), ohm·m) |  |
| 53 | Kapton (Cri/oFlex 3) | k(T) | log_polynomial | null | -4.769084 | 10.92915 | -26.55324 | 36.1195 | -27.08454 | 11.58217 | -2.777787 | 0.3432157 | -0.01715343 | 推導柔性多項式耦合系數.md L138-166 / 16柔性八階擬合.py（Cri/oFlex 3，7 位有效數字） |  |
| 54 | NbTi (Cri/oFlex 3) | k(T) | runtime_polyfit | null | null (runtime_polyfit) | null (runtime_polyfit) | null (runtime_polyfit) | null (runtime_polyfit) | null (runtime_polyfit) | null (runtime_polyfit) | null (runtime_polyfit) | null (runtime_polyfit) | null (runtime_polyfit) | 讀不到固定數值：16柔性八階擬合.py 於執行期以 np.polyfit 對 seed=42 模擬 PPMS 資料擬合，且受 noise_pct 滑桿影響；原始檔未提供 NBTI_COEFFS 數字常數，故不填寫（不編… |  |

*Appendix row count: 54 (`log_polynomial`=48, `rational_copper`=5, `runtime_polyfit`=1); 53 fixed-coefficient entries; 1 `runtime_polyfit` excluded.*

## References (compiled)
[^raicu2025]: Raicu, N., Hogan, T., Wu, X., Vahidpour, M., Snow, D., Hollister, M., & Field, M. (2025). *Cryogenic thermal modeling of microwave high density signaling*. EPJ Quantum Technology, 12:124. https://doi.org/10.1140/epjqt/s40507-025-00427-1 (Dataset: https://doi.org/10.5281/zenodo.15238913)
[^nist]: NIST Cryogenics Index of Material Properties. https://trc.nist.gov/cryogenics/materials/materialproperties.htm
[^marquardt]: Marquardt, E. D., Le, J. P., & Radebaugh, R. (2000). *Cryogenic Material Properties Database*. 11th International Cryocooler Conference. (Bibliographic details as recorded in project citations.)
[^bradley]: Bradley, P. E., et al. (2006). *Cryogenic Material Properties Database, Update 2006*. ICEC 21. (Bibliographic details as recorded in project citations.)
[^simon1992]: Simon, N. J., Drexler, E. S., & Reed, R. P. (1992). *Properties of Copper and Copper Alloys at Cryogenic Temperatures*. NIST Monograph 177. NIST.
[^flynn]: Flynn, T. M. *Cryogenic Engineering*. (Edition/publisher details not fully specified in project citations.)
[^smith2024]: Smith, J. P., Mazin, B. A., Boaventura, A., Thompson, K. J., & Daal, M. (2024). *Improved Flexible Coaxial Ribbon Cable for High-Density Superconducting Arrays*. IEEE Transactions on Applied Superconductivity, 34(2), 1–6. https://doi.org/10.1109/TASC.2024.3350516 (arXiv:2306.13574, https://arxiv.org/abs/2306.13574)

## Availability and Source Artifacts (compiled)

Primary sedimented distill paper documents and same-source artifacts used for compilation:
- `/home/sam/量傳線/docs/heatload-distill_paper.md` (ok)
- `/home/sam/量傳線/docs/heatload-distill_paper.tex` (ok)
- `/home/sam/量傳線/docs/heatload-distill_paper.zh.md` (ok)
- `/home/sam/量傳線/docs/heatload-distill_paper.zh.tex` (ok)
- `/home/sam/量傳線/docs/heatload-distill_期刊候選.md` (ok)
- `/home/sam/量傳線/docs/9coeff_4step_flow.json` (ok)
- `/home/sam/量傳線/docs/polyfit_可靠度驗證.json` (ok)
- `/home/sam/量傳線/docs/polyfit_可靠度驗證.md` (ok)
- `/home/sam/量傳線/docs/9coeff_4step_視覺化規格.md` (ok)
- `/home/sam/量傳線/docs/NIST9熱負載整合說明.md` (ok)
- `/home/sam/Context/20261119T120029--paper-heatload-distill__paper.org` (ok)
- `/home/sam/Context/20261119T120029--paper-heatload-distill__paper-map.md` (ok)
- `/home/sam/.opencode/skills/heatload-coff-nist/references/citations.md` (ok)
- `/home/sam/量傳線/docs/9coeff_4step_flow.json` (ok)
- `/home/sam/量傳線/docs/9coeff_4step_視覺化規格.md` (ok)
- `/home/sam/量傳線/docs/9coeff_4step_demo.html` (ok)
- `/home/sam/量傳線/docs/9coeff_4step_demo.xlsx` (ok)
- `/home/sam/量傳線/docs/溫區擬合_科學成果沉澱.md` (ok)
- `/home/sam/量傳線/docs/溫區擬合_物理模型_來源萃取.md` (ok)
- `/home/sam/量傳線/docs/溫區擬合_物理模型_arxiv驗證.md` (ok)
- `/home/sam/量傳線/docs/溫區擬合_物理模型_viz_spec.md` (ok)
- `/home/sam/量傳線/docs/溫區擬合_物理模型_fitting示意圖.svg` (ok)

Key artifacts: `docs/heatload-distill_paper.md/.tex` (EN), `docs/heatload-distill_paper.zh.md/.tex` (ZH, aligned in sections/logic/content/tables/values/formulas/citations/boundaries), `docs/heatload-distill_期刊候選.md`, `docs/9coeff_4step_flow.json`, `docs/polyfit_可靠度驗證.md/.json`, ljg-paper org/map, `docs/9coeff_4step_視覺化規格.md`, `docs/NIST9熱負載整合說明.md`, SSOT/provenance under `~/.opencode/skills/heatload-coff-nist/`.

**Limitations/gaps (not resolved by this compilation):** consolidated/sections currently compiled from EN sedimented source (ZH pairing tracked as same-source input but not merged into compiled text); raw SSOT data is embedded only as **Appendix A / `rawdata` reference** (same-source, 54 rows: 48 `log_polynomial` + 5 `rational_copper` + 1 `runtime_polyfit`; `NbTi (Cri/oFlex 3)` `runtime_polyfit` with `coeffs=null` excluded and given no coefficients) — it is provenance context, not new measurement or re-fit, and its `valid_range_K` fields are `null` wherever the SSOT records no range; `提昇論文品質.md` stale/unverified; TS ljg-paper validator unavailable in this environment; missing `streamlit/matplotlib/altair/plotly/scipy/openpyxl` for some interactive/runtime visuals; actual *Cryogenics* submission formatting/APC/scope must be checked externally; `.tex`/`.zh.tex` not templated to current journal class; ZH LaTeX (xeCJK/CJK fonts) compilation unverified; 溫區擬合同源 viz snapshot/demo (Task 5: viz_data/json/html/xlsx generator) not yet produced—compiled platform demonstrates fitting via sediment doc + inline SVG + doc-listed examples (degraded, evidence-bounded).
