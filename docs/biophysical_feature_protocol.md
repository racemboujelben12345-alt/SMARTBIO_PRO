# Biophysical feature protocol v1

This layer converts an explicit anatomical ROI into interpretable optical and
color features. It is an engineering feature layer, not a clinical biomarker
inversion.

## Feature groups

- **Linear RGB:** sRGB-coded images are linearized before quantitative color operations.
- **Chromaticity:** each linear channel is divided by total linear RGB energy.
  This can reduce sensitivity to common multiplicative intensity changes but
  may also remove useful intensity information.
- **Channel ratios:** R/G, R/B and G/B are dimensionless color features.
- **Relative optical density:** -ln(I/I0) is available only with an explicit
  matched reference image. This is a relative feature, not an absolute
  absorption coefficient.

## Physical guardrails

- JPEG/sRGB values are not calibrated spectral irradiance.
- No extinction coefficients are hard-coded.
- No absolute hemoglobin or bilirubin concentration is inferred here.
- Reference features require controlled geometry and a valid reference.
- Acquisition metadata and the Quality Gate remain upstream requirements.
- Feature extraction never modifies source images.
- Hb and bilirubin remain separate modeling branches.

## Identifiability

RGB provides at most three measured channels. An unconstrained four-or-more
chromophore inversion is therefore underdetermined. Future inversion must
report rank and conditioning and use externally sourced optical constants.

## Experimental comparison plan

E0: linear RGB baseline.
E1: linear RGB + chromaticity.
E2: linear RGB + channel ratios.
E3: E1/E2 + acquisition-quality covariates.
E4: reference-based relative OD only when a valid reference campaign exists.

All transformations and feature-selection decisions must be learned or fixed
using training/calibration data only; validation, test and external data use
the frozen pipeline.

A predictive gain is not by itself evidence of a physiological mechanism.
Performance, uncertainty, device-held-out robustness and external validation
must be reported separately.
