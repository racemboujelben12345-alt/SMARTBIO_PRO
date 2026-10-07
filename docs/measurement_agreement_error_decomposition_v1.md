# Measurement Agreement & Error Decomposition v1

This engineering layer characterizes paired agreement before interpreting biomarker-model performance. It separates observed paired error into systematic bias and random dispersion.

## Design
Each subject contributes a reference value and a corresponding measurement-system result. Multiple rows for a subject are averaged before agreement is calculated. Error is measurement minus reference.

## Report
The report contains paired counts, means, mean bias, relative bias, MAE, RMSE, error SD, approximate 95% limits of agreement, and a descriptive systematic-error fraction.

## Guardrails
Required columns, finite numeric values, non-null subject IDs, and subject-level pairing are enforced. Zero mean reference is rejected for relative bias. No clinical threshold or clinical equivalence claim is defined.

## Interpretation
Small bias with wide limits of agreement suggests limited systematic offset but substantial random variability. Large bias with narrow dispersion suggests a more systematic offset.

This module complements repeatability, temporal stability, acquisition perturbation sensitivity, uncertainty coverage, and device-held-out validation. It does not claim that smartphone RGB/JPEG directly measures hemoglobin or bilirubin.
