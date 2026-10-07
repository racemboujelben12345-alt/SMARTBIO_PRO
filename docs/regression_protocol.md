# Regression baseline protocol v1

This module is the first quantitative modeling layer after explicit ROI,
quality control, calibration and biophysical feature extraction.

## Baselines

The default benchmark contains:

1. Linear regression
2. Ridge regression
3. Lasso regression
4. Random forest regression
5. Gradient boosting regression

Linear models use a StandardScaler inside a scikit-learn pipeline so the
scaler is fitted on training data only. Tree models do not require scaling.

## Evaluation

For each frozen test partition report:

- MAE
- RMSE
- R²
- Pearson correlation
- Bland–Altman bias
- Bland–Altman 95% limits of agreement
- sample count

Correlation is descriptive only. It is not an agreement or clinical-validation
criterion.

## Leakage policy

- Patient-level partitioning is mandatory when repeated acquisitions exist.
- Calibration parameters must be frozen before validation/test evaluation.
- Feature selection and hyperparameter decisions must not use the test set.
- External datasets remain external.
- Device-held-out experiments must use the existing patient-safe split contract.

## Recommended experiment ladder

- E0: linear RGB features + linear regression
- E1: biophysical/color feature groups + Ridge
- E2: nonlinear baselines (random forest, gradient boosting)
- E3: uncertainty layer
- E4: unseen-device validation
- E5: independent external validation

Deep learning is intentionally deferred until these baselines establish whether
the engineered signal is reproducible.

## Scientific interpretation

A lower MAE on one dataset is not sufficient evidence of physiological
validity. Final claims require held-out patients, acquisition/device robustness,
uncertainty coverage, agreement analysis and independent validation against the
laboratory reference standard.
