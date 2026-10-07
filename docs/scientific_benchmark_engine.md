# Scientific Benchmark Engine v1

The benchmark engine is the final reporting layer for a frozen evaluation.

It does not fit models, select features, tune hyperparameters, or calibrate
uncertainty. Those operations must already have been completed inside the
appropriate development partitions.

## Inputs

- reference biomarker values
- frozen predictions
- patient identifiers
- experiment manifest hash

## Outputs

The report contains:

- MAE
- RMSE
- R²
- Pearson correlation
- Bland–Altman bias and limits of agreement
- patient-cluster bootstrap confidence intervals
- permutation-test results for MAE and RMSE
- row and patient counts
- manifest hash

## Scientific interpretation

The benchmark is an evaluation summary, not clinical validation. Confidence
intervals quantify sampling uncertainty under the selected bootstrap model.
Permutation tests assess the observed prediction-target pairing against a
permutation null; they do not establish clinical usefulness.

External validation remains a separate frozen evaluation and should be reported
with its own dataset identity and manifest.

## Reproducibility rule

A benchmark is uniquely tied to its experiment manifest hash. If dataset
version, split protocol, feature set, model, calibration, uncertainty setup,
or random seed changes, the experiment identity must change.
