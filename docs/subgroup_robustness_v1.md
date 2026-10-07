# Subgroup Robustness Diagnostics v1

## Purpose

This engineering/statistical layer checks whether quantitative measurement
error behaves differently across a declared subgroup such as device model,
acquisition condition, or other pre-specified technical factor.

It complements repeatability, perturbation sensitivity, measurement agreement,
method comparison, and residual stratification.

## Method

Repeated observations are averaged within subject. Each subject must have one
and only one subgroup in the analyzed frame. For every subgroup the module
reports paired sample count, reference and measurement means, mean bias, MAE,
RMSE, and relative bias.

A subgroup must contain at least two paired subjects. This is a minimum
engineering diagnostic requirement, not a statistical sample-size justification.

## Interpretation

Differences between subgroup error profiles can reveal device sensitivity,
acquisition dependence, or population/range imbalance. They should be
interpreted together with acquisition metadata and the residual/range
diagnostics.

A subgroup difference is not automatically a device effect: confounding
between device, acquisition protocol, reference range, season, operator, or
other factors must be investigated.

## Guardrails

This module does not:

- define clinical acceptance limits;
- define diagnostic thresholds;
- declare clinical equivalence;
- pool or silently reassign subjects across partitions;
- tune a frozen test set;
- convert classification-only data into quantitative targets;
- claim direct Hb/bilirubin measurement from RGB/JPEG.

Subgroup labels must be declared before analysis and their provenance must be
retained. For external/device-held-out validation, subgroup analysis must not
override the original leakage-safe partition.
