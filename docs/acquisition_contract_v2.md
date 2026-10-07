# Acquisition Contract v2

## Purpose

Smartphone optical measurements are strongly affected by camera and acquisition
state. This contract provides a fail-closed metadata boundary before
quantitative feature extraction or calibration.

It records acquisition state; it does not infer missing values.

## Required quantitative state

- device model
- exposure time
- ISO
- white-balance mode
- working distance
- incidence angle
- illumination condition

For quantitative capture, missing state is an error.

## White balance

Automatic white balance is rejected. Quantitative experiments should use a
locked/manual/fixed white-balance state. The contract does not claim that a
locked white balance is spectrally calibrated.

## Illumination

Supported controlled labels are:

- flash
- ambient
- controlled_led
- reference

An unknown condition is not considered optically comparable.

## Geometry

Working distance must be positive and incidence angle must be within 0–90°.
These are acquisition metadata constraints, not clinical thresholds.

## RAW data

RAW availability is recorded but is not required by this contract. JPEG/RGB
data remain camera-encoded signals and are not treated as calibrated spectral
measurements.

## Leakage and reproducibility

The contract is metadata-only and contains no target-derived fitting. It must
be frozen before calibration/model fitting. A later experiment that changes
acquisition policy should receive a new experiment identity/manifest.

## Scientific limitation

Passing the acquisition contract means only that required acquisition metadata
are present and internally plausible. It does not establish image quality,
biological validity, analytical accuracy, clinical validity, or cross-device
generalization.
