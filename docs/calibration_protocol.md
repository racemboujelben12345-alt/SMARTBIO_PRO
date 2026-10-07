# Calibration protocol

SmartBio PRO treats calibration as a learned preprocessing stage between image/optical preprocessing and biomarker estimation.

## v1 scope

The implemented calibration engine provides:

- sRGB to linear-RGB conversion before quantitative color features;
- affine RGB calibration using paired observed/reference measurements;
- immutable calibration-model provenance;
- fit RMSE for auditing the calibration fit;
- explicit fit-partition control;
- relative optical-density computation through the existing biophysical guardrail layer.

## Leakage rule

Calibration parameters may be fitted only on:

- the training partition; or
- a dedicated calibration partition.

They must then be frozen before evaluation on validation, test, unseen-device, or external datasets.

The API rejects test and external as fit partitions. This is an engineering safeguard against calibration leakage.

## Acquisition requirements

A quantitative calibration campaign should record, at minimum:

- device model;
- exposure time;
- ISO;
- white-balance mode/settings;
- working distance;
- illumination state;
- ROI geometry;
- reference target/material;
- acquisition timestamp or campaign identifier.

A calibration reference must be acquired under controlled and reproducible geometry. A generic affine mapping does not make RGB values equivalent to calibrated spectral irradiance.

## Interpretation

Affine calibration is an empirical camera-response correction. It does not identify tissue chromophores and does not replace a spectrometer, calibrated color target, tissue optical model, or laboratory reference standard.

The next research layer is device-held-out validation of the calibrated features, followed by uncertainty and agreement analysis.
