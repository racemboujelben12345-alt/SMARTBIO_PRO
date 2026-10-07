# Scientific Experiment CLI

The scientific experiment engine executes one frozen quantitative benchmark from three
already validated CSV partitions: train, calibration, and frozen test.

## Preconditions

The CSVs must already satisfy the quantitative acquisition, target provenance, ROI,
identity, and partition contracts. This command does not infer missing metadata and
does not convert classification-only datasets into quantitative targets.

Required partition identity:
- patient_id
- image_id
- acquisition_id

Required target fields include:
- biomarker
- target_value
- target_unit

ROI/acquisition provenance is enforced by the downstream quantitative benchmark gate.

## Execution

Example:

```bash
PYTHONPATH=src python -m smartbio.cli scientific-experiment \
  --train data/quantitative/train.csv \
  --calibration data/quantitative/calibration.csv \
  --test data/quantitative/test.csv \
  --dataset experimental_ultrasound_placeholder \
  --dataset-version v1 \
  --split-protocol patient-level-train-calibration-frozen-test \
  --biomarker hemoglobin \
  --unit g/dL \
  --features mean_intensity,std_intensity,entropy \
  --model ridge \
  --calibration-id none \
  --alpha 0.10 \
  --bootstrap 2000 \
  --permutations 2000 \
  --output outputs/experiment/report.json
```

Do not use placeholder dataset names for a real study. The example only documents the
CLI contract.

## Scientific guarantees

- Model fitting uses train only.
- Split-conformal uncertainty uses calibration only.
- Frozen test is not used for model fitting, feature selection, calibration, or tuning.
- Patient, acquisition, and image/sample overlap is rejected.
- Quantitative benchmark, ROI, acquisition, and target provenance gates remain active.
- The output is an engineering/research benchmark, not a clinical validation claim.

## Abstention

No abstention threshold is assumed by default. If interval-width abstention is desired,
set `--max-interval-width` in the biomarker's declared unit. This threshold is an
engineering decision and must be documented; it is not a clinical decision threshold.
