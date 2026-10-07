# Dataset-Independent Validation Strategy v1

## Purpose

SmartBio PRO must remain scientifically executable even when an external dataset is inaccessible, delayed, restricted, or missing required provenance.

SEWA Rural and Fingertip Video are therefore optional external-validation candidates, not core runtime dependencies.

## Dataset roles

| Dataset | Role | Quantitative status | Dependency |
|---|---|---|---|
| Available public datasets with verified labels/provenance | Core development and benchmarking | Only where the quantitative contract passes | Required only for the corresponding experiment |
| SEWA Rural Anemia Dataset | Optional external Hb validation | Conditional on access and complete acquisition metadata | Optional |
| Fingertip Video Dataset | Optional external Hb validation | Conditional on explicit manifest and acquisition metadata | Optional |
| Neonatal jaundice image datasets | Bilirubin auxiliary/validation evidence | Dataset-specific; no assumed TSB mapping | Optional |

## Fail-closed policy

A dataset is not promoted into a quantitative experiment merely because files can be downloaded.

The dataset must provide, or the study must independently establish:

- explicit patient/sample identity;
- explicit target value and unit;
- traceable reference measurement;
- explicit acquisition metadata required by the quantitative contract;
- valid anatomical ROI definition;
- readable, integrity-checked assets;
- leakage-safe partitioning;
- provenance sufficient to reproduce the experiment.

If a required field is unavailable, the dataset remains available for non-quantitative inspection only and does not enter the quantitative benchmark.

## External dataset policy

SEWA and Fingertip must never be silently mixed into training data.

When available, they are introduced as separate experiments:

1. schema/provenance audit;
2. dataset-specific ingestion;
3. quantitative gate;
4. external validation;
5. subgroup/device robustness;
6. uncertainty evaluation.

A failed access request does not invalidate SmartBio PRO.

## Claims policy

Results are reported only for datasets and experiments actually executed.

The project must distinguish:

- implemented capability;
- dataset acquired;
- dataset validated;
- experiment executed;
- literature-reported result.

Literature results are never presented as SmartBio measurements.

## Scientific fallback

If an optional dataset is unavailable, development continues using datasets that satisfy the predefined contract.

The fallback does not relax:

- patient-level separation;
- calibration isolation;
- device-held-out evaluation where applicable;
- target provenance;
- acquisition metadata requirements;
- uncertainty reporting;
- agreement analysis;
- leakage auditing.

## Decision rule

Access availability changes the experiment set, not the scientific standard.

This makes SmartBio PRO dataset-independent at the architecture level while preserving strict provenance and validation requirements.
