# Uncertainty protocol v1

SmartBio reports uncertainty separately from point-estimation performance.

## Split-conformal intervals

A dedicated calibration partition is used to compute absolute residual scores
from a frozen prediction model. The conformal quantile is then frozen and
applied to validation, test, or external predictions without refitting.

For nominal miscoverage alpha, the interval is:

prediction +/- conformal quantile

This implementation is distribution-free under the exchangeability assumptions
of split conformal prediction. It is not a clinical confidence interval.

## Required reporting

Report:

- nominal coverage target (1 - alpha)
- empirical coverage
- mean and median interval width
- calibration sample count
- test/external sample count
- point-estimation MAE/RMSE
- subgroup/device coverage when enough data exist

Coverage alone is insufficient: very wide intervals can achieve high coverage.

## Abstention

The interval width can be used as an engineering abstention/repeat-acquisition
signal. The maximum-width threshold must be selected on training/calibration
data and frozen before test/external evaluation.

An abstention or repeat recommendation is not a clinical decision.

## Leakage controls

- The prediction model is fit without test/external data.
- The conformal quantile is fit only on the calibration partition.
- Test/external outcomes are never used to tune the interval.
- Device-held-out and patient-level separation remain mandatory.

## Scientific next step

The uncertainty layer must be evaluated on real quantitative Hb/TSB datasets
with verified patient identity, laboratory targets, acquisition metadata and
independent validation. The current public NJN classification asset cannot be
used to claim quantitative bilirubin uncertainty because its image-to-CSV
mapping is not validated.
