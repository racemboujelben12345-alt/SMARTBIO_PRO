# SmartBio PRO — Biophysics Notes

## Why this layer exists

A smartphone image is not a direct measurement of blood concentration. The camera records a device-dependent, spectrally integrated signal after illumination, tissue absorption, tissue scattering, optics, sensor response, exposure, white balance and image processing.

For tissue, a useful first-order forward relation is:

`mu_a(lambda) = sum_i epsilon_i(lambda) c_i`

but the detected reflectance/intensity also depends on scattering and photon pathlength. Therefore SmartBio uses Beer-Lambert-type equations only as controlled relative/forward models. It does not invert raw RGB directly into an absolute concentration.

## Absorption + scattering

For a simplified attenuation proxy:

`I/I0 ~= exp(-(mu_a + mu_s') L)`

where `mu_a` is absorption, `mu_s'` is reduced scattering and `L` is an effective pathlength. This is intentionally labeled a proxy: diffuse tissue reflectance requires a transport model and geometry-dependent boundary conditions.

## RGB identifiability

RGB gives at most three independent channel measurements. If the unknowns are HbO2, Hb, bilirubin and melanin, there are four chromophore concentrations. Without additional spectral channels or strong physiological priors, the inverse problem is underdetermined. `identifiability_report()` makes this limitation explicit.

## Camera physics

For quantitative work: lock exposure, ISO, focus/working distance and white balance; record illumination and geometry; prefer RAW when possible; and characterize the camera response. JPEG/sRGB can be used for research experiments, but its nonlinear encoding and device processing must not be confused with radiometric intensity.

## Flash and ambient

If `I_total` contains flash + ambient and `I_ambient` measures ambient alone, a practical differential model is:

`I_flash ~= I_total - alpha(lambda) I_ambient`

The channel gain `alpha(lambda)` must be calibrated because exposure, sensor response, timing, clipping and camera processing can make `alpha != 1`. Negative values are diagnostically useful and should not be silently clipped during scientific analysis.

## Target-specific implications

### Hemoglobin

The palpebral conjunctiva and nail bed are scientifically motivated because they can reduce melanin interference compared with ordinary pigmented skin, and smartphone studies have demonstrated feasibility. However, published real-world results show non-trivial error/limits of agreement; SmartBio therefore treats Hb estimation as a screening research problem, not a replacement for laboratory Hb.

### Bilirubin

Bilirubin has strong visible absorption toward the blue region, but skin reflectance also contains hemoglobin and melanin contributions. Robust transcutaneous bilirubinometry therefore uses multi-wavelength information and calibration. Smartphone RGB is a hypothesis-generating low-cost modality, not a full spectrometer.

## References

1. Oshina I, Spigulis J. *Beer–Lambert law for optical tissue diagnostics: current state of the art and the main limitations.* Journal of Biomedical Optics. 2021. DOI: 10.1117/1.JBO.26.10.100901.
2. Zhang et al. *Prediction of anemia and estimation of hemoglobin concentration using a smartphone camera.* 2021. PMCID: PMC8279386.
3. *Prediction of anemia in real-time using a smartphone camera processing conjunctival images.* 2024. PMCID: PMC11090304.
4. *Measuring and imaging of transcutaneous bilirubin, hemoglobin, and melanin based on diffuse reflectance spectroscopy.* 2023. PMCID: PMC10616887.
5. *Signal Quality in Continuous Transcutaneous Bilirubinometry.* 2024. PMCID: PMC11435595.
6. *Medical photography using mobile devices.* 2022. PMCID: PMC9465817.
