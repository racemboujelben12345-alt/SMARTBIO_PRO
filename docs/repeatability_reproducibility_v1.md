# Repeatability and reproducibility v1

SmartBio includes an engineering measurement-quality layer for repeated
quantitative acquisitions.

## Purpose

Before interpreting model accuracy, acquisition stability should be
characterized. Repeated measurements of the same subject reveal measurement
noise that regression metrics alone cannot show.

## Analysis

The repeatability analysis requires a quantitative measurement, a subject
identifier, and a device identifier.

For subjects with at least two observations it estimates:

- within-subject standard deviation;
- repeatability coefficient = 2.77 times within-subject SD;
- mean within-subject coefficient of variation.

When exactly two devices are represented and subjects are paired across both
devices, it also reports paired-device mean bias, standard deviation, and 95%
limits of agreement.

The device comparison is restricted to paired subjects. Different subjects
measured on different devices are not treated as a device effect.

## Scientific interpretation

This is measurement-system characterization, not clinical validation. The
repeatability coefficient assumes approximately normal measurement error.
Limits of agreement describe observed paired differences and are not clinical
acceptance limits.

The analysis must be run under a declared acquisition protocol. It does not
permit changing thresholds after inspecting a frozen test set.
