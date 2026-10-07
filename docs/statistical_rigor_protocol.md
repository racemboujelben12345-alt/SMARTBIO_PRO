# Statistical Rigor & Reproducibility Protocol v1

## Scope

This layer strengthens evaluation after the predictive pipeline is frozen.
It adds:

- permutation-based null testing for regression error metrics
- deterministic experiment manifests with SHA-256 identity
- metadata-level leakage auditing

It does not fit models, tune hyperparameters, or modify test predictions.

## Permutation testing

Predictions are permuted relative to reference targets while preserving both
marginal distributions. The observed MAE/RMSE is compared with the null
distribution.

For MAE/RMSE, lower is better. The reported p-value is a Monte Carlo
permutation p-value with the +1 correction.

A small p-value means the observed pairing performs better than the chosen
permutation null. It does **not** establish clinical utility, causal validity,
or independence from all possible sources of bias.

## Experiment identity

Every benchmark should record:

- dataset and version
- split protocol
- feature set
- model
- calibration identifier
- uncertainty configuration
- random seed
- generated manifest hash

Changing any of these fields produces a different manifest identity.

## Leakage audit

Before evaluation, inspect:

- duplicate patient rows
- duplicate acquisition IDs
- patients observed on multiple devices

Cross-device patients must follow the existing device-held-out exclusion
protocol. Duplicate rows must be investigated rather than silently removed.

## Reporting rule

A benchmark report should present the point estimate together with:

1. bootstrap confidence interval,
2. permutation-test result where applicable,
3. sample/patient counts,
4. subgroup performance,
5. uncertainty coverage and interval width,
6. abstention rate when enabled,
7. manifest hash.

Statistical significance must never be presented as clinical validation.
