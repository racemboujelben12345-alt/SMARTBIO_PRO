# Agreement bootstrap inference v1

## Purpose

This module adds patient-level bootstrap uncertainty intervals to paired
measurement-agreement metrics. It is an engineering/statistical inference
layer and does not define clinical acceptance limits, equivalence, or
diagnostic thresholds.

## Method

Repeated observations are first averaged within subject, matching the
measurement-agreement contract. Subjects are then resampled with replacement
as the bootstrap unit, preventing repeated images from acting as independent
patients.

The report provides percentile confidence intervals for:

- mean bias
- MAE
- RMSE
- Bland–Altman lower and upper limits of agreement

Defaults are 2,000 bootstrap replicates, 95% confidence, and seed 42.

## Interpretation

Intervals quantify sampling uncertainty in the observed agreement metrics.
They do not establish clinical validity or interchangeability. Clinical
acceptance limits must come from an independent scientific/clinical protocol.
