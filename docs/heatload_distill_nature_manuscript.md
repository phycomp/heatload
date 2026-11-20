# Provenance as a measurable property: rebuilding cryogenic thermal-conductivity data for superconducting interconnects

> **Draft type:** Nature-style research/review manuscript (initial submission material)  
> **Generated with:** `nature-writing` (axes: task=manuscript, paper_type=review, language=zh-to-en, journal=generic, sections=title/abstract/intro/related-work/method/experiments/discussion/conclusion)  
> **Date:** 2026-11-20  
> **Evidence boundary:** All claims derive from locally traceable SSOT records, NIST web-scraped coefficients, verified arXiv metadata, and in-range curve comparisons. No refitting, no new measurements, no invented coefficients or citations. `nature-shared` shared core was unavailable; compliant local `static/core` was used and this degradation is disclosed.

## Abstract

Cryogenic heat-load estimates for superconducting microwave interconnects depend on fitted thermal-conductivity functions κ(T), yet the provenance, valid range, and process dependence of the underlying coefficients are often lost when data are reused. We show that internal mathematical consistency of a coefficient database does not imply material reliability: a database of 53 fixed-coefficient entries passes all structural and in-range behavioural checks while containing three confirmed coefficient mis-assignments and multiple low-order idealized fits. By rebuilding an independent database from the NIST cryogenic material-properties website and comparing it against the existing source of truth under the same nine-parameter log-log model, we find that four entries match exactly (Kapton, stainless steel 304/304L/316) while others diverge substantially within their fitted ranges — PTFE by 358% at 293 K and brass by 986% at 77 K. We trace these divergences to low-order placeholder fits and to cross-assignments in which nylon inherits PTFE coefficients and Mylar inherits nylon coefficients. The result reframes data provenance as a measurable, auditable property rather than an assumption, and provides a bounded workflow for using cryogenic conductivity fits in nW-scale thermal budgeting.

**Keywords:** cryogenic thermal conductivity, provenance, heat-load estimation, dilution refrigerator, superconducting interconnects, numerical conditioning, data reliability

## 1. Introduction

### 1.1 Context and stakes

Superconducting quantum processors require microwave control lines spanning from room temperature to the millikelvin mixing chamber of a dilution refrigerator. Each line carries a passive conductive heat load whose magnitude, at the nW to µW scale, directly constrains the cooling power available at each stage. Recent high-density cabling efforts illustrate the point: Smith *et al.* reported approximately 5 nW per trace from 1 K to 100 mK for a 1-ft flexible Nb–47 wt% Ti coaxial ribbon cable (FLAX), roughly half the computed load of the smallest commercial superconducting coaxial cable [Smith 2024]. Such estimates are sensitive to which κ(T) data are used, over what temperature range, and how the fits behave outside that range.

### 1.2 The problem: consistency mistaken for reliability

Thermal conductivities across cryogenic to room temperature span several orders of magnitude and are commonly represented by compact fitted forms. The nine-coefficient log-log polynomial, log₁₀κ(T)=Σ cₙ(log₁₀T)ⁿ, and source-specific rational forms for high-purity copper, are distributed through cryogenic material databases and reused in heat-budget models. A database can be internally self-consistent — every curve positive, finite, smooth, and integrable — while still carrying coefficients that are mis-assigned, fitted over a different range, or idealized to a low-order placeholder. When such coefficients are reused without their provenance, a heat-load number can appear precise while resting on an undocumented source or an out-of-range evaluation.

### 1.3 Aim and scope

We treat provenance as an auditable property. Our aim is to determine whether the fixed-coefficient entries of a cryogenic conductivity database remain faithful to their authoritative source, and to identify the mechanisms by which self-consistent entries can nonetheless be unreliable. In scope: structural and in-range behavioural validation, source-level coefficient comparison against the NIST cryogenic material-properties website, and curve comparison under the same physical model. Out of scope: new measurements, re-fitting of coefficients, and claims about the correctness of any specific material's κ(T).

### 1.4 Contributions

- We establish that passing all structural and in-range checks is compatible with three confirmed coefficient mis-assignments, and identify the specific entries involved.
- We rebuild an independent, provenance-bearing database from the NIST website and compare it against the existing database under a shared nine-parameter model, localising divergences to their fitted ranges.
- We attribute the divergences to identifiable mechanisms — low-order placeholder fits and cross-assignment — rather than to generic "data quality" concerns.
- We translate these findings into a bounded usage rule for cryogenic heat-load estimation: in-range integrals are comparatively stable, whereas coefficient identity and process-dependent values require source verification.

## 2. Provenance as the basis of heat-load estimates

Heat-load comparisons across cable technologies are sensitive to material-property assumptions. Smith *et al.* combined literature κ(T) values with cross-sectional areas, used polytetrafluoroethylene (PTFE) data to estimate perfluoroalkoxy alkane (PFA), and reported extrapolated regions — explicitly discussing conductor- versus dielectric-dominated regimes [Smith 2020, 2024]. Raicu *et al.* measured the total thermal conductivity and inner-conductor resistivity of an SC-086/50-SCN-CN semi-rigid coaxial cable, fitted both with numerical functions, and computed stage-wise static and active loads in a dilution refrigerator [Raicu 2025]. Krinner *et al.* measured passive loads of stainless-steel and NbTi coaxial cables and established staged thermal anchoring as the practical basis of qubit protection [Krinner 2019]. These studies do not make provenance optional; they make transparent source, range, and extrapolation handling a precondition for defensible comparison.

The present work examines the single-source-of-truth (SSOT) database underlying earlier heat-budget artefacts: 54 entries comprising 48 `log_polynomial`, 5 `rational_copper`, and one `runtime_polyfit` entry (`NbTi (Cri/oFlex 3)`) with no fixed coefficients. Fifty-three entries carry fixed nine-coefficient sets. All fixed coefficients were previously verified as faithful transcriptions of upstream project files (48/48 NIST-derived, 4/4 Raicu, 1/1 Kapton). The question addressed here is different: faithful to a file is not the same as faithful to the authoritative source.

## 3. Model and validation framework

### 3.1 The fitted forms

For most materials, κ(T) follows the log-log polynomial log₁₀κ(T)=Σ_{n=0}^8 cₙ(log₁₀T)ⁿ, with κ in W m⁻¹ K⁻¹ and T in K. For oxygen-free high-conductivity (OFHC) copper, a rational/RRR form is used: log₁₀κ=(a+c√T+eT+gT^1.5+iT²)/(1+b√T+dT+fT^1.5+hT²), with five residual-resistivity-ratio (RRR) variants. The stage-wise conductive heat load is Q_solid=Σᵢ (A/Lᵢ)∫κ(T)dT, with optional attenuator dissipation Q_rf=Σᵢ P_in(1−10^(−αᵢ/10)).

### 3.2 Validation layers

Structural validation checks that each fixed entry has nine finite coefficients, a valid temperature range, and a legal equation type. In-range behavioural validation evaluates κ(T) at log-spaced points within each valid range, checking positivity, finiteness, smoothness, integrability, and the absence of rational-form poles. Source validation compares coefficient arrays against the authoritative files and, in this work, against the NIST website. Curve comparison evaluates the source database and the rebuilt database under the identical model at temperatures common to both fitted ranges; temperatures outside the common range are excluded so that 8th-order polynomial extrapolation cannot be mistaken for a fitted result.

## 4. Results

### 4.1 The database passes structural and behavioural validation

All 53 fixed-coefficient entries pass structural and in-range behavioural checks: coefficients are finite, ranges are valid, κ(T) is positive and smooth throughout each fitted range, integrals are finite, and none of the five rational copper variants has a pole in range. Source transcription is exact (48/48, 4/4, 1/1). By any internal criterion the database is self-consistent. This result is necessary but not sufficient: it establishes mathematical integrity, not material reliability.

### 4.2 Coefficient mis-assignments

Comparison against the NIST website reveals a chain of cross-assignments. The coefficients assigned to `Polyamide (Nylon)` are identical to the NIST coefficients for PTFE; those assigned to `Polyethylene Terephthalate (Mylar)` are identical to the NIST coefficients for Nylon; and the `Raicu dielectric (PTFE)` entry also carries the PTFE coefficients. On the NIST website, PTFE and Nylon have distinct nine-coefficient sets (a₀=2.738 versus a₀=−2.6135, respectively). The coincidence of coefficient arrays across materials with distinct upstream sources is therefore a mis-assignment, not a shared material property.

### 4.3 In-range divergence under a common model

Evaluating both databases under the same model within their common fitted ranges gives a mixed picture. Kapton and stainless steel 304/304L/316 match exactly (0% difference at 293 K). PTFE differs by 358% at 293 K: the existing entry uses a low-order fit giving 0.0596 W m⁻¹ K⁻¹, whereas the NIST full ninth-order fit gives 0.2726 W m⁻¹ K⁻¹. Brass differs by 986% at 77 K, a temperature inside its 5–116 K fitted range: the existing entry has c₅–c₈=0 and yields 3.66 W m⁻¹ K⁻¹, whereas the NIST fit yields 39.8 W m⁻¹ K⁻¹. Invar differs by 742% at 293 K. These are in-range differences, not extrapolation artefacts; the comparison deliberately excludes out-of-range temperatures such as 293 K for brass.

### 4.4 Mechanistic interpretation

The divergences have identifiable causes. Low-order placeholder fits — coefficients with trailing zeros — are approximate idealizations adequate for order-of-magnitude screening but not for material-specific comparison. Cross-assignments arise when coefficient arrays are copied between entries whose source records differ. Process sensitivity explains why a single value cannot be universal: the thermal conductivity of amorphous polymers is governed by chain entanglement and crystallinity, giving a narrow 0.1–0.5 W m⁻¹ K⁻¹ band for bulk amorphous polymers [Zhou 2019], while PTFE measured at sub-kelvin temperatures follows a quadratic temperature dependence that varies with sample preparation [Drobizhev 2017]. For crystalline insulators such as sapphire, the low-temperature power-law exponent of phonon thermal conductivity depends on defect and stress distributions, spanning approximately 2–5 [van Ostaay 2018]. These findings are consistent with large, source-dependent variations in fitted coefficients.

## 5. Discussion

The central implication is that validation must distinguish internal consistency from external fidelity. A database can pass every structural and in-range behavioural test and still encode wrong material identities. The three confirmed mis-assignments and the low-order placeholder fits are not detectable by smoothness or positivity checks; they surface only when coefficients are compared against the authoritative source under the same model.

This result bears directly on cryogenic heat budgeting. In-range integrals were previously found comparatively stable under perturbation, while deep-low-temperature extrapolation was highly sensitive [Heatload-Distill reliability evidence]. The present analysis adds a further boundary: even within the fitted range, coefficient identity and process dependence can shift a value by several fold. For a multi-layer flexible cable, the passive load is a sum over constituent layers, Σₖ (Aₖ/L)∫κₖ(T)dT; using a mis-assigned or idealized coefficient for one layer can therefore bias the total load at the nW scale that determines qubit thermalisation. Practically, conductor and dielectric values for a specific cable — Nb47Ti and PFA for FLAX, NbTi and polyimide for Cri/oFlex 3, C7150 and PTFE for SC-086 — should come from that cable's measured fits, with generic database values used only for order-of-magnitude screening.

The workflow developed here is bounded. We compare coefficients and curves, not raw measurements: the NIST website provides fitted coefficients rather than measurement points, so no re-fitting or correctness claim is possible. We do not assert which value is right for a given cable; we establish whether an entry matches its authoritative source and whether it is self-consistent in range. The finding that four entries match exactly also cautions against over-correction — the existing database is not uniformly wrong, and the failures are localised to identifiable mechanisms.

## 6. Conclusion

We show that internal consistency of a cryogenic conductivity database is not sufficient for material reliability, and that provenance can be made measurable by rebuilding an independent database from the authoritative source and comparing coefficient arrays and curves under a shared physical model. Three coefficient mis-assignments and several low-order placeholder fits are identified, while four entries match exactly. The practical rule is narrow but consequential: use in-range integrals for screening, verify coefficient identity against the source before material-specific comparison, and never treat a fitted coefficient as a material constant independent of range and process.

## References (verified identifiers only)

- Smith, J. P. *et al.* (2024). Improved Flexible Coaxial Ribbon Cable for High-Density Superconducting Arrays. *IEEE Trans. Appl. Supercond.* 34(2). DOI 10.1109/TASC.2024.3350516; arXiv:2306.13574.
- Smith, J. P. *et al.* (2020). Flexible Coaxial Ribbon Cable for High-Density Superconducting Microwave Device Arrays. DOI 10.1109/TASC.2020.3008591; arXiv:2007.06496.
- Raicu, N. *et al.* (2025). Cryogenic Thermal Modeling of Microwave High Density Signaling. *EPJ Quantum Technol.* 12:124. DOI 10.1140/epjqt/s40507-025-00427-1; arXiv:2502.01945.
- Krinner, S. *et al.* (2019). Engineering cryogenic setups for 100-qubit scale superconducting circuit systems. *EPJ Quantum Technol.* 6:2. DOI 10.1140/epjqt/s40507-019-0072-0; arXiv:1806.07862.
- Zhou, J. *et al.* (2019). A Thermal Resistance Network Model for Heat Conduction of Amorphous Polymers. *Phys. Rev. Materials* 4, 015601. DOI 10.1103/PhysRevMaterials.4.015601; arXiv:1909.07607.
- Drobizhev, A. *et al.* (2017). Thermal conductivity measurements of PTFE and Al₂O₃ ceramic at sub-Kelvin temperatures. *Cryogenics* 85, 63–70. DOI 10.1016/j.cryogenics.2017.05.008; arXiv:1612.02514.
- van Ostaay, J. A. M. & Mukhin, S. I. (2018). Phonon-kink scattering effect on the low temperature thermal transport in solids. *Low Temp. Phys.* 44(6), 747–757. DOI 10.1063/1.5037562; arXiv:1805.02019.
- NIST Cryogenic Material Properties. https://trc.nist.gov/cryogenics/materials/materialproperties.htm

---

## Chinese notes on structure and intent（中文結構說明）

- **主張**：本文主張「溯源可被量化」— 用重建資料庫＋同模型對帳，把「資料可信」從假設變成可稽核性質。這是 argument chain 的 core claim。
- **為何是 review 類型**：本文按機制分組綜合（還原→錯位→低階擬合→製程敏感），而非逐篇列文獻；貢獻是方法學與邊界，不是新量測。
- **Results 配置**：4.1–4.4 按「自洽→錯位→偏差→機制」排序，最強證據（4.2 錯位鏈、4.3 範圍內偏差）在 Discussion 之前；作法/邊界置 §3，[]> 避免堆在開頭。
- **動詞校準**：觀察用 show/find，機制用 is consistent with，避免 proved/unprecedented 等未受支持的詞。
- **邊界**：明確寫「不重擬合、不判對錯、只判是否與權威源一致且區間自洽」；外用 Brass 293 K 的比較已排除。

## Section outline

1. Introduction — context, consistency-vs-reliability problem, aim, contributions
2. Provenance as the basis — prior cable studies and the SSOT database
3. Model and validation framework — fitted forms, four validation layers
4. Results — self-consistency, mis-assignments, in-range divergence, mechanism
5. Discussion — implications for heat budgeting, bounded workflow
6. Conclusion — narrow operational rule

## Assumptions or missing inputs

- Journal not specified; `generic` used. Nature-family framing can be applied on request.
- `nature-shared` shared core unavailable; local `static/core` used, degradation disclosed.
- Raw κ(T) measurement points unavailable; no re-fitting or correctness claim is made.

## Claim-evidence map

- Claim: three confirmed mis-assignments → Evidence: NIST coefficient arrays vs SSOT entries | Status: supported
- Claim: PTFE +358% / brass +986% in range → Evidence: curve_compare.json in common range | Status: supported
- Claim: polymer κ process-sensitive → Evidence: Zhou 2019, Drobizhev 2017 (verified metadata) | Status: supported
- Claim: phonon exponent 2–5 → Evidence: van Ostaay 2018 | Status: supported

## Why this structure

- Review argument chain: scope → organizing principle → synthesis by mechanism → stance → outlook.
- Results precede Discussion; claims kept near supporting data.
- Boundary stated explicitly to prevent over-claiming.

## To redirect me

Name the section or claim that is off and I will revise only that, keeping the rest.
