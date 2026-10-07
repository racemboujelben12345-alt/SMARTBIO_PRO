# Fingertip Video ingestion preflight v1

## Purpose

This preflight establishes a fail-closed entry point for the Fingertip Video
Dataset for non-invasive hemoglobin research.

It does **not** reproduce the published ResNet-18 results and does not treat
paper-level metadata as row-level acquisition metadata.

## Required explicit manifest

The ingestion manifest must explicitly provide:

- `patient_id`
- `video_path`
- `hemoglobin_gdl`
- `reference_measurement_id`

Patient IDs and Hb labels must not be inferred from filenames.

## Quantitative gate

The current quantitative acquisition contract additionally requires explicit
row-level values for device model, exposure, ISO, white-balance state, working
distance, incidence angle, and illumination.

If these values are unavailable, the dataset may be retained for exploratory
or methodological work, but the quantitative benchmark remains closed.

## Scientific workflow

1. Obtain the dataset under its access conditions.
2. Build an explicit manifest from the released records.
3. Run the preflight.
4. Validate video readability, duration, frame rate, and frame integrity.
5. Verify CBC/Hb provenance.
6. Create patient-level splits.
7. Extract the fingertip signal/ROI without patient leakage.
8. Apply quality gating.
9. Run engineered baselines before deep learning.
10. Evaluate uncertainty and, where metadata permit, device-held-out robustness.

Published ResNet-18 metrics are literature benchmarks only and must never be
reported as SmartBio PRO results.

## Current status

No dataset access is assumed by this module. Until actual released videos and
their explicit metadata are available, no quantitative result is claimed.
