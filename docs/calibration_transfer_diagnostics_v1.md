# Calibration Transfer Diagnostics v1

## Purpose

This engineering/statistical layer evaluates whether an **already-fitted**
calibration behaves consistently across declared technical subgroups such as
device model or acquisition condition.

It is a diagnostic companion to the calibration engine and subgroup robustness
layer. It does not fit, refit, select, or tune calibration coefficients.

## Method

Repeated observations are averaged within subject. Each subject must belong to
exactly one declared subgroup. For every subgroup the module reports paired
sample count, reference and calibrated-measurement means, mean bias, MAE, RMSE,
and relative bias.

A subgroup must contain at least two paired subjects. This is a minimum
engineering diagnostic requirement, not a statistical sample-size justification.

## Leakage and interpretation

Calibration coefficients must have been fitted upstream using only the
permitted training/calibration partition. This module receives the resulting
measurements and only evaluates transfer behavior; it never accesses or
modifies calibration coefficients.

Differences between subgroups can indicate device sensitivity or acquisition
dependence, but can also reflect confounding by reference range, protocol,
season, operator, or population composition.

## Guardrails

This module does not:

- refit calibration on the evaluated subgroup;
- tune a frozen test set;
- define clinical acceptance limits or diagnostic thresholds;
- establish clinical equivalence;
- override leakage-safe train/calibration/test partitions;
- convert classification-only data into quantitative targets;
- claim direct Hb/bilirubin measurement from RGB/JPEG.

Subgroup labels and the provenance of the upstream calibration must be retained
with the experiment record.
