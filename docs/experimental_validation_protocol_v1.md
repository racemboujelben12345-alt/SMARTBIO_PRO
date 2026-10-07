# Experimental Validation Protocol v1

## 1. Purpose

This protocol defines the first **real-data experimental stage** of SmartBio PRO.

The objective is not to claim clinical performance. The objective is to test the central engineering hypothesis:

> Does controlled optical acquisition + calibration + image-quality gating reduce acquisition/device sensitivity and improve agreement with laboratory-referenced biomarker values?

The protocol is intentionally dataset-independent. It can be executed with a fully traceable local acquisition campaign or with an external dataset only when the quantitative provenance contract is satisfied.

## 2. Primary scientific question

For a fixed biomarker and anatomical ROI, does the following progression improve quantitative robustness?

**E0 — Raw optical features**
→ **E1 — sRGB linearization / calibrated features**
→ **E2 — quality-gated pipeline**
→ **E3 — device-held-out evaluation**
→ **E4 — uncertainty / abstention**
→ **E5 — external validation**

The primary comparison is paired: the same evaluation subjects/acquisitions must be evaluated through the competing pipeline variants.

## 3. Biomarker separation

Hb and bilirubin are independent experiments.

### Hb branch
- Reference: laboratory hemoglobin measurement.
- Unit: g/dL.
- Candidate ROI: conjunctiva or nailbed.
- No claim of anemia diagnosis is permitted from this protocol.

### Bilirubin branch
- Reference: laboratory total serum bilirubin (TSB) or another explicitly validated reference.
- Unit must be declared explicitly.
- Candidate ROI: forehead, sternum, or abdomen.
- Classification-only datasets are auxiliary evidence and cannot be converted into quantitative bilirubin labels.

No experiment may silently combine Hb and bilirubin records.

## 4. Acquisition design

A quantitative acquisition record must contain, at minimum:

- patient_id
- image_id
- acquisition_id
- biomarker
- target_value
- target_unit
- target_source
- reference_method
- reference_measurement_id
- reference_type
- device_model
- exposure_us
- iso
- white_balance_mode
- working_distance_mm
- incidence_angle_deg
- illumination

Recommended additional provenance:

- timestamp
- session_id
- operator_id or anonymized operator code
- image_format
- bit_depth
- raw_available
- flash_state
- camera_lens
- focus_state
- image_width
- image_height
- roi_type
- roi coordinates or deterministic ROI definition
- source_file_sha256

Missing quantitative acquisition fields are a **hard failure**, not an imputation opportunity.

## 5. Minimum campaign structure

When a controlled local campaign becomes possible, target the following structure as a design objective rather than a fabricated dataset:

| Role | Suggested minimum |
|---|---:|
| Baseline / training | 30 subjects |
| Calibration | 10 subjects |
| Frozen test | 10 subjects |
| Total | 50 subjects |

The 50-subject design is an engineering pilot target. It is not a clinical sample-size justification.

Subjects must remain disjoint between training, calibration and frozen test.

For device robustness, a stronger design is:

- device A: development/training + calibration
- device B: frozen test

If only one device is available, report device-held-out validation as **not executed**, never as implicitly satisfied.

## 6. Controlled acquisition matrix

For each subject/session, keep the biological state fixed while recording acquisition metadata.

Primary controlled variables:

1. device model
2. exposure
3. ISO
4. white balance
5. illumination
6. working distance
7. incidence angle
8. anatomical ROI
9. acquisition session

Do not deliberately vary all factors simultaneously. A controlled experiment must preserve interpretability.

Recommended perturbation stages:

### P0 — Reference condition
Fixed device, locked WB, controlled illumination, fixed geometry, fixed exposure/ISO.

### P1 — Illumination perturbation
Change illumination while keeping device, geometry and camera settings documented.

### P2 — Geometry perturbation
Change working distance and/or incidence angle within a documented engineering range.

### P3 — Device perturbation
Repeat the same protocol on a second device where possible.

The purpose is to measure sensitivity, not to manufacture a clinical challenge.

## 7. Pipeline variants

Every variant must use the same patient-level partitions.

### E0 — Raw baseline
Input: documented RGB-derived features.

No calibration fit.

### E1 — Calibration
Input: sRGB-linearized / calibrated features.

Calibration is fitted only on training or calibration data and then frozen.

### E2 — Quality-gated
Apply the deterministic quality gate without modifying raw images.

Report:
- PASS
- REVIEW
- FAIL
- coverage after gating
- performance before and after gating

Do not hide failed acquisitions. Report their counts and reasons.

### E3 — Device-held-out
Train/develop on device A and evaluate once on device B.

No patient overlap.

### E4 — Uncertainty
Fit split-conformal uncertainty only on the calibration partition.

Report:
- empirical coverage
- target coverage level
- mean interval width
- median interval width
- abstention rate
- performance of accepted predictions

Wide intervals are information, not a failure to conceal.

## 8. Primary evaluation metrics

For quantitative estimation:

- MAE
- RMSE
- R²
- Pearson correlation
- Bland–Altman bias
- Bland–Altman limits of agreement

Correlation is never the primary proof of agreement.

For uncertainty:

- empirical coverage
- mean interval width
- median interval width
- abstention/repeat-acquisition rate

For robustness:

- performance by device
- performance by illumination condition
- performance by ROI
- performance by quality status
- performance by acquisition perturbation

Subgroup results must include sample counts.

## 9. Statistical plan

The frozen test partition is used once for final evaluation.

Confidence intervals must be cluster-aware at the patient level.

Production benchmark defaults:
- bootstrap: >= 2000 resamples
- permutation tests: >= 2000 permutations

Any reduced values used in unit tests must be explicitly labeled as test-only.

The primary ablation comparison is paired at the patient/acquisition level. When multiple images belong to one patient, inference must not treat those images as independent patients.

## 10. Leakage controls

The following are hard failures:

- patient appearing across train/calibration/test
- acquisition appearing across partitions
- image appearing across partitions
- calibration fitted on test/external data
- quality thresholds tuned using frozen test outcomes
- model selection using frozen test outcomes
- external dataset silently mixed into development data
- target/reference values inferred from filenames
- missing metadata filled by guesswork
- literature benchmark reported as SmartBio experimental performance

## 11. Biophysical interpretation

The model output is a predictor of a laboratory-referenced biomarker.

It is **not** interpreted as direct measurement of tissue chromophore concentration.

RGB/JPEG values are camera-encoded measurements. Tissue absorption, scattering, pathlength, illumination and camera response are confounders.

Relative optical density may be used only with an explicit reference and controlled geometry.

A four-chromophore unconstrained inversion from three RGB channels is not accepted.

## 12. Acceptance criteria for E0–E4

An experiment is considered technically executable only if:

- all quantitative provenance fields are present;
- patient-level partitions are disjoint;
- acquisition contracts pass;
- ROI contracts pass;
- target/reference provenance passes;
- predictions are frozen before test evaluation;
- benchmark statistics complete without leakage;
- uncertainty calibration is isolated from test data.

Scientific success is **not** defined as achieving a predetermined clinical accuracy threshold.

Instead, report whether calibration and quality gating produce a reproducible improvement or robustness trade-off relative to E0.

## 13. Required outputs

Each completed experiment should produce:

`experiment_manifest.json`
`acquisition_audit.json`
`quality_summary.csv`
`feature_provenance.json`
`predictions_E0.csv`
`predictions_E1.csv`
`predictions_E2.csv`
`benchmark_E0.json`
`benchmark_E1.json`
`benchmark_E2.json`
`uncertainty_E4.json`
`device_robustness.json`
`scientific_validation.json`
`claim_boundary.md`

The final report must distinguish:

1. implemented capability
2. acquired data
3. validated data
4. executed experiment
5. literature result

## 14. Stop conditions

Stop quantitative analysis if:

- reference measurements cannot be traced;
- acquisition metadata are incomplete;
- patient identity cannot be resolved;
- ROI provenance is ambiguous;
- duplicate/leakage checks fail;
- image integrity fails;
- calibration/test separation cannot be established;
- the dataset does not contain the target required by the experiment.

A smaller valid experiment is scientifically preferable to a larger contaminated experiment.

## 15. Next execution step

The next step after merging this protocol is **not deep learning**.

It is to create or acquire the first fully traceable quantitative acquisition table and run:

1. schema/provenance audit
2. acquisition gate
3. patient-level split
4. ROI validation
5. quality gate
6. E0 baseline
7. E1 calibration ablation
8. E2 quality-gating ablation
9. frozen benchmark
10. uncertainty calibration

Only after this chain passes should device-held-out robustness and external validation be executed.
