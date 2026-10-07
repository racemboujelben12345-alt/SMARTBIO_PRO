# Method Comparison & Regression Agreement v1

## Purpose

This module evaluates whether a quantitative measurement method behaves
similarly to a paired reference method. It is an engineering/statistical
measurement-quality layer and is not a clinical equivalence or diagnostic
decision procedure.

It complements repeatability, temporal stability and drift, acquisition
perturbation sensitivity, and measurement agreement with Bland–Altman error
decomposition.

## Methods

### Deming regression

Deming regression estimates y = beta0 + beta1*x while allowing error in both
the reference and measurement axes.

The implementation uses a caller-supplied variance ratio:

lambda = sigma_measurement^2 / sigma_reference^2.

The default lambda=1 is an equal-error-variance engineering sensitivity
assumption. It is not learned from clinical data and must not be described as
a validated instrument-error ratio.

### Passing–Bablok

Passing–Bablok uses the median of finite pairwise slopes and the median
intercept. It is non-parametric and less dependent on ordinary least-squares
assumptions.

## Confidence intervals

Slope and intercept intervals are descriptive percentile bootstrap intervals
with a fixed seed. The default is 2000 subject-level resamples. Bootstrap
resampling is performed after repeated observations are averaged within subject.

These intervals are not clinical acceptance intervals.

## Input contract

Required columns:

- reference_value
- measurement_value
- patient_id

Repeated rows for a subject are averaged before method comparison. Subject
identity is therefore part of the statistical unit.

The analysis fails closed for missing columns, empty data, non-finite numeric
values, missing subject IDs, fewer than three paired subjects, zero reference
variance, invalid variance ratio, and insufficient valid bootstrap resamples.

## Interpretation

The identity relationship is represented by slope = 1 and intercept = 0.

Departure from these values is descriptive evidence of proportional and/or
constant systematic differences. It must be interpreted together with
Bland–Altman bias/limits of agreement, uncertainty, repeatability, and the
experimental acquisition context.

A strong correlation alone does not establish agreement.

## Scientific guardrails

This module does not:

- define clinical thresholds;
- declare clinical equivalence;
- tune a frozen test set;
- convert classification-only datasets into quantitative targets;
- claim that smartphone RGB/JPEG directly measures Hb or bilirubin;
- replace laboratory reference measurements.

For SmartBio, quantitative conclusions still require explicit target provenance,
acquisition metadata, ROI provenance, leakage-safe partitions, uncertainty
analysis, and independent/device-held-out validation.
