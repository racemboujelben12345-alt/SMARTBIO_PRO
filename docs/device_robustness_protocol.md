# Device-held-out robustness protocol v1

Device robustness is evaluated as a domain-shift experiment, not as an
ordinary random test split.

## Primary experiment

Select one smartphone/device model as an unseen device.

1. Build the training set from other devices.
2. Remove every patient who appears on the held-out device from training.
3. Fit preprocessing, calibration, model selection and uncertainty calibration
   using training/calibration data only.
4. Freeze the complete pipeline.
5. Evaluate once on the held-out device.
6. Repeat for each device with adequate sample size.

## Why patient exclusion matters

A patient may have acquisitions on multiple devices. Leaving that patient in
training would permit patient-specific appearance to leak into the unseen
device test and make robustness look better than it is.

## Report

For every held-out device report:

- sample count
- excluded cross-device patients
- MAE, RMSE, R2 and Pearson r
- Bland–Altman bias and 95% limits
- uncertainty coverage and interval width
- abstention rate
- relative MAE/RMSE change from the source-device evaluation
- acquisition-condition distribution

Do not declare a device "robust" from one split or one metric.

## Interpretation

Performance degradation is evidence of domain shift, not automatically model
failure. Investigate exposure, ISO, white balance, working distance, illumination,
ROI geometry, compression and device-specific color processing before proposing
correction.

Synthetic brightness scaling is not a substitute for real unseen-device data.

## Scientific status

This module provides split construction and reporting utilities. It does not
create device data, claim clinical generalization, or establish regulatory
equivalence between smartphones.
