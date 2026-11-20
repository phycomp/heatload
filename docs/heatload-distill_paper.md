# Provenance-Grounded Use of 9-Coefficient Thermal Conductivity Fits for Cryogenic Heat-Load Estimation: A Review and Reliability-Aware Workflow

> **Document type:** Review / methods manuscript draft prepared for *Cryogenics* (Elsevier), grounded in existing sources, SSOT database records, same-source artifacts, and reliability-validation outputs.  
> **Format:** Markdown (this file). A LaTeX counterpart is maintained at `docs/heatload-distill_paper.tex` and should be synchronized and templated to current journal requirements before submission. Journal and submission notes: `docs/heatload-distill_期刊候選.md`.  
> **Date:** 2026-11-19 (same-source snapshot `docs/9coeff_4step_flow.json`, `generated_at`: `2026-11-19T10:48:13`, `errors: 0`).  
> **Scope statement:** This draft **does not** re-fit or invent coefficients, **does not** claim new material-property measurements, and **does not** introduce conclusions beyond cited/validated project evidence. All quantitative statements are tied to existing SSOT/provenance records and validation artifacts, with limitations and uncertainties stated explicitly. Submission suitability, article type, formatting, APC/open-access options, and policies must be checked against the latest *Cryogenics* guidelines before submission.

## Abstract
Low-temperature thermal budgeting in cryogenic engineering—including conduction through supports and interconnects in dilution-refrigerator systems—commonly relies on fitted representations of material thermal conductivity κ(T), especially 9-coefficient log-log polynomials (c0..c8 / a..i) and source-specific rational/RRR forms for selected materials[^nist][^marquardt][^bradley][^simon1992][^flynn][^raicu2025]. Recent high-density superconducting cabling work illustrates the practical stakes: Smith *et al.* estimated a 5 nW per-trace conductive heat load from 1 K to 100 mK for a 1-ft flexible Nb-47 wt% Ti coaxial ribbon cable by combining literature thermal-conductivity values with cable cross sections, and compared this to commercial coaxial and NbTi-on-polyimide flex options[^smith2024]. Such nW-scale estimates depend directly on which κ(T) data and fits are used, over what ranges they are valid, and how extrapolations are handled.

This paper presents **Heatload-Distill**, a provenance-grounded review and reliability-aware workflow for using 9-coefficient κ(T) fits in cryogenic heat-load estimation. The workflow organizes practice into four traceable steps: (1) literature and material-database provenance, (2) physical/model interpretation of the 9 parameters and heat-load equations, (3) matrix/least-squares solution and numerical conditioning, and (4) polyfit reliability validation. It is anchored to a single source of truth (SSOT, decision D4=A) and same-source artifacts (`topic-viz` Format F: specification + snapshot + offline HTML/Excel with graceful degradation and error disclosure).

Using `docs/9coeff_4step_flow.json` and associated artifacts, we review 54 database entries (48 `log_polynomial`, 5 `rational_copper`, 1 `runtime_polyfit`) and 53 fixed-coefficient materials for numeric coefficient–material relations; `NbTi (Cri/oFlex 3)` is `runtime_polyfit` with `coeffs=null` and is excluded from fixed-coefficient numeric relations. Existing validation evidence (synthetic log-log cubic-spline generator, 8th-order `np.polyfit`, T=2–300 K, N=50 log-spaced points, perturbation study) shows that in-range integrated conductivity (∫₂³⁰⁰ κ dT) is comparatively stable under tested perturbations, whereas deep-low-temperature extrapolation (e.g., κ at 20 mK) is highly sensitive to perturbations and fitting/process choices and should be treated only as an order-of-magnitude indicator. The evidence also shows strong ill-conditioning of the raw power basis, material-specific structural residual near NbTi Tc under a global 8th-order fit, and a large discrepancy between stored and validation-fit Kapton coefficients (max |Δc|≈79.48). We conclude that trustworthy cryogenic heat-load estimates require traceable provenance, explicit validity ranges, conditioning-aware interpretation, and disclosed uncertainty rather than isolated extrapolated values or undocumented coefficients.

**Keywords:** cryogenics, cryogenic thermal conductivity, 9-coefficient fit, heat-load estimation, dilution refrigerator, provenance, numerical conditioning, polyfit reliability, review

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

## Availability
- **Specification and same-source artifacts:** `docs/9coeff_4step_視覺化規格.md`, `docs/9coeff_4step_flow.json`, `docs/9coeff_4step_demo.html`, `docs/9coeff_4step_demo.xlsx`
- **Reliability validation:** `docs/polyfit_可靠度驗證.md`, `docs/polyfit_可靠度驗證.json`
- **Integration documentation:** `docs/NIST9熱負載整合說明.md`, `docs/NIST9_視覺化規格.md`
- **SSOT and provenance:** `~/.opencode/skills/heatload-coff-nist/scripts/{coeff_data,thermal_load}.py`, `~/.opencode/skills/heatload-coff-nist/references/citations.md`
- **Generation/display scripts:** `scripts/9coeff_4step_viz.py`, `scripts/9coeff_4step_streamlit_demo.py`, `scripts/validate_polyfit_reliability.py`
- **Journal candidates and submission notes:** `docs/heatload-distill_期刊候選.md`

## References
[^raicu2025]: Raicu, N., Hogan, T., Wu, X., Vahidpour, M., Snow, D., Hollister, M., & Field, M. (2025). *Cryogenic thermal modeling of microwave high density signaling*. EPJ Quantum Technology, 12:124. https://doi.org/10.1140/epjqt/s40507-025-00427-1 (Dataset: https://doi.org/10.5281/zenodo.15238913)
[^nist]: NIST Cryogenics Index of Material Properties. https://trc.nist.gov/cryogenics/materials/materialproperties.htm
[^marquardt]: Marquardt, E. D., Le, J. P., & Radebaugh, R. (2000). *Cryogenic Material Properties Database*. 11th International Cryocooler Conference. (Bibliographic details as recorded in project citations.)
[^bradley]: Bradley, P. E., et al. (2006). *Cryogenic Material Properties Database, Update 2006*. ICEC 21. (Bibliographic details as recorded in project citations.)
[^simon1992]: Simon, N. J., Drexler, E. S., & Reed, R. P. (1992). *Properties of Copper and Copper Alloys at Cryogenic Temperatures*. NIST Monograph 177. NIST.
[^flynn]: Flynn, T. M. *Cryogenic Engineering*. (Edition/publisher details not fully specified in project citations.)
[^smith2024]: Smith, J. P., Mazin, B. A., Boaventura, A., Thompson, K. J., & Daal, M. (2024). *Improved Flexible Coaxial Ribbon Cable for High-Density Superconducting Arrays*. IEEE Transactions on Applied Superconductivity, 34(2), 1–6. https://doi.org/10.1109/TASC.2024.3350516 (arXiv:2306.13574, https://arxiv.org/abs/2306.13574)
