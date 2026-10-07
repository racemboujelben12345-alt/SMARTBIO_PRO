# Temporal Stability & Drift v1

## Purpose

Characterize whether repeated measurements of a stable control or reference
condition remain temporally stable across acquisition sessions.

This is an engineering measurement-system layer. It does not establish
clinical acceptance limits, diagnostic performance, or clinical equivalence.

## Inputs

The analysis requires:

- measurement_value: numeric measurement under a declared control/reference condition.
- session_id: session identifier with a meaningful acquisition order.

At least two sessions are required.

## Reported quantities

- Baseline mean: mean measurement in the first ordered session.
- Session-mean CV: coefficient of variation across session means.
- Maximum absolute relative drift: largest absolute deviation of a session
  mean from the baseline, expressed as a percentage of the absolute baseline.
- Linear drift per session: least-squares slope of session means against
  session order.

## Scientific interpretation

The metrics quantify temporal behavior but do not define a pass/fail threshold.
Engineering acceptance limits must be specified prospectively from the declared
acquisition protocol, control material, intended use, and measurement uncertainty.

The control/reference condition should remain fixed across sessions. Changes in
device, illumination, geometry, operator, or calibration must be recorded as
provenance rather than silently interpreted as temporal drift.

The frozen test partition must not be used to tune temporal-stability thresholds.
