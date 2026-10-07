# Nested Model Selection Protocol v1

Model selection must not inspect the final evaluation data.

## Protocol

For each outer fold:

1. Hold out an outer patient-disjoint test fold.
2. Run all preprocessing and model selection only on the outer training data.
3. Use inner patient-grouped cross-validation to select hyperparameters.
4. Refit the selected estimator on the complete outer training fold.
5. Predict the untouched outer test fold.
6. Record MAE and RMSE.

The outer-fold predictions are then pooled for downstream confidence intervals,
permutation testing, Bland–Altman analysis, and subgroup analysis.

## Why nested CV

Choosing a model or hyperparameter using the same data later reported as
test performance produces optimistic estimates. Nested CV separates selection
from evaluation.

## Reproducibility

Record the feature set, model family, parameter grid, split strategy,
random seeds, dataset version, and experiment manifest hash.

## Medical-data rule

The grouping variable should normally be patient_id. Device-held-out
experiments remain a separate domain-shift evaluation and must not be replaced
by ordinary random cross-validation.
