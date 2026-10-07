# Residual Stratification & Heteroscedasticity Diagnostics v1

## Purpose

This module is an engineering/statistical diagnostic layer for quantitative
reference-vs-measurement data. It asks whether residual magnitude or relative
error changes across the reference-value range.

It complements measurement agreement, Deming/Passing–Bablok method comparison,
repeatability, temporal stability, and acquisition perturbation analysis.

## Diagnostics

For each subject, repeated observations are averaged before analysis.

The module reports:

- residual = measurement - reference;
- residual SD, MAE and RMSE;
- mean absolute relative error;
- Spearman association of residual with reference;
- Spearman association of absolute residual with reference;
- Spearman association of absolute relative residual with reference;
- descriptive slope of absolute residual versus reference;
- residual summaries stratified into reference-value quantile bins.

A growing absolute-residual association can indicate range-dependent error or
heteroscedastic behavior. The diagnostic is descriptive; it does not impose a
universal statistical cutoff.

## Interpretation

A useful pattern to inspect is:

- residual near zero across strata -> limited systematic range trend;
- residual mean changing across strata -> possible proportional/systematic error;
- residual SD or MAE increasing across strata -> possible heteroscedasticity;
- relative error decreasing while absolute error increases -> scale-dependent
  behavior that should not be summarized by one metric alone.

These diagnostics should be interpreted with Bland–Altman plots, method
comparison, uncertainty intervals, repeatability and acquisition metadata.

## Scientific guardrails

This module does not:

- define clinical acceptance limits;
- define diagnostic thresholds;
- declare clinical equivalence;
- tune a frozen test set;
- convert classification-only datasets into quantitative targets;
- replace laboratory reference measurements;
- claim that smartphone RGB/JPEG directly measures Hb or bilirubin.

Quantitative conclusions still require target provenance, ROI provenance,
leakage-safe partitions, controlled acquisition metadata, uncertainty analysis,
and independent/device-held-out validation.
