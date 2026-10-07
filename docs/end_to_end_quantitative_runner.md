# End-to-end quantitative experiment runner

## Purpose

The quantitative runner is the orchestration boundary for a frozen SmartBio
biomarker-estimation evaluation. It turns the existing provenance, acquisition,
partition, manifest, and benchmark controls into one fail-closed entry point.

It does **not** fit, tune, or calibrate a model. Features, calibration, model
training, and uncertainty calibration must happen upstream on permitted
development/calibration data. The runner receives frozen predictions and audits
the evaluation boundary before reporting results.

## Protocol

1. Construct the canonical dataset with explicit column mapping.
2. Validate target provenance and acquisition metadata.
3. Define development/calibration/evaluation partitions at patient level.
4. Freeze preprocessing, feature set, calibration, model, and uncertainty.
5. Generate evaluation predictions without fitting on evaluation records.
6. Create the immutable experiment manifest.
7. Audit patient, acquisition, and sample identity across partitions.
8. Execute the quantitative benchmark gate.
9. Store the manifest hash together with the benchmark report.

## Fail-closed conditions

The runner rejects the experiment when target provenance, quantitative
acquisition metadata, required identity columns, prediction alignment, or
partition identity independence is invalid.

## Scientific interpretation

A passing run establishes protocol compliance and reproducible evaluation
identity. It does not establish clinical validity, regulatory acceptance,
population-wide generalization, or analytical equivalence to a laboratory
assay.

## Why predictions are supplied

Keeping model fitting outside the runner prevents accidental training leakage
and makes the evaluation boundary explicit. The same runner can therefore be
used with linear, tree-based, or future models without changing the benchmark
protocol.

## Reproducibility

The manifest hash encodes dataset/version, split protocol, feature set, model,
calibration identity, uncertainty identity, and random seed. Any change to
these experiment-defining inputs creates a different experiment identity.
