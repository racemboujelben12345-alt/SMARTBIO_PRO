# ROI and acquisition contract

SmartBio PRO does not treat an arbitrary image crop as a validated anatomical ROI.

## ROI policy

Each biomarker has an explicit set of allowed anatomical targets. v1 uses deterministic ROI boxes supplied by the acquisition/annotation layer.

The ROI contract validates:

- target-specific anatomical label;
- image bounds;
- minimum width and height;
- minimum and maximum image-area fraction;
- deterministic cropping without modifying the source image.

Automatic anatomical localization is intentionally out of scope until a detector can be validated independently.

## Why this matters

Quantitative color features are highly sensitive to background, specular highlights, hair, shadows, and surrounding tissue. A reproducible ROI contract reduces an important source of acquisition variance without pretending that the crop itself is clinically validated.

## Acquisition metadata

A quantitative acquisition record should retain:

- biomarker branch;
- anatomical ROI type;
- device model;
- exposure/ISO when available;
- white-balance state;
- illumination state;
- working distance;
- incidence/pose information when available;
- acquisition identifier;
- reference/calibration identifier;
- quality-gate result.

These fields are provenance, not optional decoration. They are required later for device-held-out and acquisition-condition robustness analysis.
