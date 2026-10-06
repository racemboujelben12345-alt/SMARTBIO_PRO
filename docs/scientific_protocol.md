# SmartBio PRO — Scientific Protocol

## 1. Acquisition
Record patient identifier, device/camera, flash state, exposure, ISO, white balance when available, distance/geometry, anatomical ROI and reference measurement.

## 2. Target-specific branch
**Hemoglobin:** conjunctiva and/or nail-bed.

**Bilirubin:** forehead, sternum and/or abdomen.

The two branches must not share an assumption that the same anatomical ROI or optical mechanism is optimal.

## 3. Optical quality control
Reject or flag acquisitions with severe clipping/saturation, excessive darkness, insufficient contrast or blur. Keep raw images unchanged; quality flags belong to metadata.

## 4. Ambient-light correction
Flash/no-flash subtraction is permitted only when the paired acquisitions have comparable camera state. If exposure, ISO or device differs, the pipeline fails closed instead of silently subtracting incompatible signals.

## 5. Feature extraction
Use RGB, HSV and Lab-derived statistics plus chromatic ratios as candidate features. Feature selection must be performed inside the training data to avoid test-set leakage.

## 6. Calibration
Fit calibration parameters only on training/calibration data. Never fit a calibration transform using the final test set.

## 7. Validation
Use patient-level partitions. For device generalization, hold out a device and remove from training every patient represented in that held-out device.

## 8. Evaluation
Report MAE, RMSE, R², bias, Bland–Altman limits of agreement, uncertainty coverage, device-wise performance and illumination-wise performance.

## 9. Interpretation
A strong correlation is not sufficient evidence of clinical agreement. The scientific claim must remain proportional to the reference data, sample size, acquisition protocol and external validation performed.


## 10. Biophysical model boundary

Tissue reflectance is treated as a coupled absorption/scattering problem. A Beer-Lambert relation may be used only as a relative or differential approximation under controlled conditions; it is not interpreted as a direct conversion from RGB intensity to chromophore concentration.

For a forward model, the absorption coefficient can be written as:

`mu_a(lambda) = sum_i epsilon_i(lambda) * c_i`

where `epsilon_i` are externally sourced extinction spectra and `c_i` are chromophore concentrations. Scattering is represented separately by `mu_s'` and wavelength-dependent pathlength effects. The repository intentionally does not hard-code biological extinction coefficients.

Because a phone camera normally provides three broad RGB channels, an unconstrained inversion of four or more chromophores is underdetermined. Any multi-chromophore model must therefore introduce additional wavelengths, priors, calibration constraints, or a validated physiological model. The software reports this identifiability limitation explicitly.

## 11. Camera physics

Quantitative acquisition should lock exposure, ISO, focus/working distance and white balance. RAW capture is preferred when available; JPEG/sRGB is allowed only as an explicitly characterized research input. Automatic white balance is rejected by the physics audit because it can change channel gains between images.

Flash/ambient correction is represented as `I_corrected = I_total - alpha(lambda) I_ambient`, where `alpha` is an experimentally calibrated channel gain. It is not assumed to be exactly one. Negative corrected values are retained as a diagnostic signal rather than silently clipped.

## 12. Reference strategy

For quantitative reflectance-style features, acquire a stable reference target or otherwise characterize the illumination/camera response. Without a reference and controlled geometry, the system should describe its outputs as empirical image features rather than absolute optical properties.

## 13. Target-specific biophysics

For Hb, the palpebral conjunctiva and nail bed are motivated by their vascularity and reduced melanin confounding, but real-world accuracy remains limited and must be established against laboratory Hb. Published smartphone studies demonstrate feasibility but also report non-trivial limits of agreement, so SmartBio must not present RGB estimation as a replacement for CBC.

For bilirubin, visible-light skin reflectance is confounded by hemoglobin and melanin; bilirubin has strong absorption in the blue region, but one RGB channel is not sufficient to isolate it robustly. Multi-wavelength/spectral approaches are therefore a scientific reference direction, while smartphone RGB is treated as an empirical screening hypothesis requiring calibration and validation.
