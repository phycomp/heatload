# Paper Card — Provenance as a measurable property (heatload-distill 最終論文)

> Source coverage: Full paper (Markdown manuscript)  
> Extraction confidence: High  
> Locator mode: structure-grounded  
> Primary analytical lens: review  
> Secondary analytical lens: methods  
> Context verification: Paper-only (references are verified metadata already present in the manuscript; no new external verification performed for this card)  
> Card completeness: Complete relative to supplied source  
> Source: `docs/heatload_distill_nature_manuscript.md`; card date 2026-11-20

## 01 Basic Information
- Title: *Provenance as a measurable property: rebuilding cryogenic thermal-conductivity data for superconducting interconnects*
- Authors/affiliations: **Not assessable** — no author list in supplied manuscript (Agent-drafted manuscript).
- Venue/year: Nature-style manuscript draft (generic journal), 2026-11-20. `[Paper: Metadata/header]`
- Paper type: review with a methods contribution (rebuilt DB + curve comparison). `[Analysis]`
- Field: cryogenic thermal conductivity, superconducting interconnects, data provenance.
- Keywords: given in manuscript. `[Paper: Abstract]`
- DOI/arXiv: none for this manuscript; references carry verified identifiers. `[Paper: References]`
- Code/data: `docs/nist_material_db_scraped.json`, `docs/nist_transmission_line_materials.json`, `docs/nist_transmission_line_curve_compare.json`, `docs/低溫傳輸線_新DB曲線對照.svg`. `[Paper: §4, §5]`
- Position in user's research: final integrated manuscript of the heatload-distill project. `[User]`

## 02 One-Sentence Summary
[Paper: Abstract] In cryogenic interconnect heat-load estimation, we show that a coefficient database can pass all structural and in-range checks while containing mis-assignments, and that rebuilding it from NIST and comparing under a shared nine-parameter model localises source infidelity (four exact matches, PTFE +358%, brass +986%) with a bounded provenance-verification workflow.

## 03 Research Question
- Concrete problem: fitted κ(T) coefficients are reused without provenance, valid range, or process dependence. `[Paper: §1.2]`
- Why it matters: nW-to-µW heat budgets determine dilution-refrigerator stage loads and qubit thermalisation. `[Paper: §1.1]`
- Why existing approaches insufficient: internal consistency checks do not detect mis-assignment or low-order placeholder fits. `[Paper: §1.2, §4.1]`
- Precise question: **Can internal validation of a conductivity database establish material reliability, or must coefficients be checked against the authoritative source under a common model?** `[Analysis from Paper: §1.3]`

## 04 Research Background and Development Path
[Paper-framed; external verification not performed for this card beyond manuscript's own verified identifiers]
- Stage 1 — fitted κ(T) forms distributed through cryogenic databases (NIST log-log 9-parameter; rational Cu). Limitation: provenance loss. `[Paper: §2]`
- Stage 2 — cable-specific heat-load studies: Smith FLAX (5 nW/trace), Raicu SC-086 coax, Krinner stainless/NbTi coax. Limitation: values depend on source, range, extrapolation. `[Paper: §2; refs Smith/Raicu/Krinner]`
- Stage 3 — reliability review: in-range integrals stable, deep-low-T extrapolation sensitive. Limitation: does not test coefficient identity. `[Paper: §5]`
- Paper's claimed position: make provenance measurable by source-level coefficient comparison. `[Paper: §1.4, §5]`

## 05 Core Pain Points Identified by the Paper

| Pain point | Manifestation | Cause / author explanation | Evidence |
|---|---|---|---|
| Consistency ≠ reliability | DB passes all structural checks yet mis-assigned | Internal tests cannot detect identity errors | `[Paper: §4.1, §4.2]` |
| Coefficient mis-assignment | Nylon carries PTFE coefficients; Mylar carries Nylon | Arrays copied across distinct upstream sources | `[Paper: §4.2]` |
| Low-order placeholder fits | brass c5–c8=0 → 986% in-range gap | idealised fit vs full 9th-order source fit | `[Paper: §4.3, §4.4]` |
| Process sensitivity | PTFE/Nylon κ differs across batches | chain entanglement/crystallinity/phonon scattering | `[Paper: §4.4; refs Zhou/Drobizhev/van Ostaay]` |

## 06 Core Idea
1. Surface method: rebuild an independent DB from NIST and compare coefficient arrays and curves under one model. `[Paper: §3, §4]`
2. Core insight: provenance is an auditable property, not an assumption; fidelity must be tested externally, not only internally. `[Paper: §1.3, §5]`
3. General lesson `[Analysis]`: any coefficient-based scientific database should attach source, range, and process conditions to each numeric entry and verify identity against the authority.

## 07 Method Overview
- Input: NIST website coefficient tables (42 material pages) + SSOT database (54 entries, 53 fixed). `[Paper: §3.1, §4]`
- Output: new DB JSON, comparison JSON, one four-panel curve figure. `[Paper: §4]`
- Modules: scraper (a-i + range + fit error), scope filter (transmission-line materials), curve comparator (common-range sampling), figure generator. `[Paper: §3.2, §4]`
- Feedback loop: none (no re-fitting / no optimisation). `[Paper: §3.2]`
- Assumptions: coefficients valid only within fitted range; 8th-order polynomial diverges outside; no raw points → no re-fit. `[Paper: §3.2, §5]`
- Flow: NIST pages → scraped a-i → cable-material subset → common-range κ comparison → mis-assignment flags → bounded guidance.

## 08 Core Module Breakdown

| Module | Function | Why needed | In/out | Supporting evidence | Removal effect |
|---|---|---|---|---|---|
| NIST scraper | extract a-i, ranges, errors | authoritative source | HTML→JSON | `[Paper: §4]` 42 pages | no external fidelity check |
| Scope filter | map materials→cable roles | focus on transmission lines | 42→9 entries | `[Paper: §3.2]` | generic, unfocused comparison |
| Curve comparator | same-model in-range curves | localise divergence | two DBs→flags/new_curve | `[Paper: §4.2, §4.3]` | cannot distinguish exact vs divergent |
| Common-range guard | exclude out-of-range T | prevent extrapolation artefact | sample_T_in_range | `[Paper: §3.2, §4.3]` brass 293K excluded | false huge gaps from divergence |

Effects are author-described, not measured ablations. `[Analysis]`

## 09 Essential Formulas and Symbols
- Log-log fit: log₁₀κ(T)=Σ_{n=0}⁸ cₙ(log₁₀T)ⁿ; c₀–c₈ coefficients, κ W m⁻¹ K⁻¹, T K. `[Paper: §3.1, Eq implied]`
- Rational Cu form: log₁₀κ=(a+c√T+eT+gT^1.5+iT²)/(1+b√T+dT+fT^1.5+hT²), 5 RRR variants. `[Paper: §3.1]`
- Stage-wise load: Q_solid=Σᵢ (A/Lᵢ)∫κ(T)dT; Q_rf=Σᵢ P_in(1−10^(−αᵢ/10)). `[Paper: §3.1]`
- Common-range rule: sample T only where both DBs' fitted ranges overlap. `[Paper: §3.2]`

## 10 Experimental Design and Evidence Chain
Design: no experiment; observational database audit. Materials: NIST 42 pages → 9 cable materials; SSOT 53 fixed entries. Metrics: coefficient exact match, κ ratio at in-range T. Protocol: common-range sampling. `[Paper: §3, §4]`

| Experiment (analysis) | Claim tested | Comparison | Result | Supported | Unsupported stronger | Source |
|---|---|---|---|---|---|---|
| Structural validation | DB self-consistent | 53 entries vs checks | all pass | internal integrity | material correctness | `[Paper: §4.1]` |
| Coefficient signature | mis-assignment | SSOT vs NIST arrays | Nylon←PTFE, Mylar←Nylon, Raicu←PTFE | cross-assignment | which is physically right | `[Paper: §4.2]` |
| In-range κ comparison | divergence | new DB vs SSOT, common range | 4 exact; PTFE +358%; brass +986%; Invar +742% | source infidelity | cable-specific correctness | `[Paper: §4.3]` |
| Mechanism attribution | cause of divergence | literature | polymer process-sensitivity; phonon exponent 2–5 | consistent explanation | causal proof for these entries | `[Paper: §4.4]` |

## 11 Correct Interpretation of the Conclusions
- Scope: coefficient fidelity and in-range behaviour only. `[Paper: §5]`
- No oracle ground truth: no raw measurements; cannot adjudicate correctness. `[Paper: §5]`
- No end-to-end deployment: does not re-compute a cable's heat load. `[Paper: §5]`
- Domain boundary: NIST-supported ranges ≥~4–300 K; mK extrapolation excluded. `[Paper: §3.2]`
- Uncertainty: specific cable values require cable-measured fits. `[Paper: §5]`
- Bounded restatement: the DB is internally coherent but not uniformly faithful; provenance verification is feasible and localises errors. `[Analysis from Paper: §6]`

## 12 Limitations Explicitly Acknowledged by the Authors
| Limitation | Manifestation | Author's future direction | Source |
|---|---|---|---|
| No raw measurement points | cannot re-fit or claim correctness | compare coefficients/curves only | `[Paper: §5]` |
| Range restriction | out-of-range excluded (brass 293K) | common-range sampling | `[Paper: §3.2, §4.3]` |
| Nature-shared core unavailable | local static core used | disclosure | `[Paper: header]` |
| Cable-specific values | generic NIST insufficient | use cable-measured fits | `[Paper: §5]` |

## 13 Critical Analysis `[Analysis]`
| Observation | Potential issue | Why matters | How to test | Basis |
|---|---|---|---|---|
| "mis-assignment" inferred from exact coefficient equality | equality could be a legitimate shared upstream fit | mislabels a valid entry | trace each entry's upstream commit | `[Paper: §4.2]` |
| +986% brass at 77K | low-order vs full fit; both may be valid for different purposes | overstates practical error | compare against cable-level heat load with each coefficient | `[Paper: §4.3]` |
| Structure-grounded card (no PDF) | no page pointers | reduces traceability granularity | supply PDF/source-map | card header |

No formal reviewer report intended.

## 14 Knowledge Learned
- Agent-derived knowledge candidates `[Analysis]`: (1) internal consistency and external fidelity are orthogonal axes of data trust; (2) coefficient identity can be audited by signature matching; (3) common-range guards prevent 8th-order extrapolation artefacts.

## 15 Connections to Existing Knowledge
- Consistent with Smith/Raicu/Krinner cable heat-load practice that source/range matter. `[Paper: §2; refs]`
- Consistent with Zhou 2019 (polymer κ band), Drobizhev 2017 (PTFE T²), van Ostaay 2018 (phonon exponent 2–5). `[Paper: §4.4; refs]`
- Extends prior reliability review (in-range stable, extrapolation sensitive) with coefficient identity check. `[Paper: §5]`

## 16 Research Ideas (Agent-derived candidates)
1. **Upstream-commit traceability audit** — from §13 observation; hypothesis: exact coefficient equality marks copy events; delta: version-level provenance; validation: git-history trace of coeff_data.py; possible failure mode: no commit history; innovation status: `unverified`.
2. **Cable-level sensitivity to coefficient choice** — from §13; hypothesis: mis-assigned coefficient shifts nW load materially; delta: propagate into Σ(Aₖ/L)∫κₖdT; validation: two coefficient sets on same geometry; possible failure mode: geometry dominates; innovation status: `unverified`.
3. **Multi-authority cross-check** — from §5 boundary; hypothesis: other databases diverge similarly; delta: add second authority; validation: same signature match; possible failure mode: authorities share upstream; innovation status: `prior-art search required`.

---
*Card generated with nature-paper-card; 16 sections in order; no §17/18.*
