# Acquisition Perturbation Sensitivity v1

## Purpose

Quantify measurement sensitivity to declared acquisition perturbations such as
illumination, geometry, exposure settings, or device, while preserving a
within-subject paired design.

This is an engineering measurement-system characterization layer. It does not
define clinical acceptance limits, diagnostic thresholds, or clinical
equivalence.

## Design

For each subject, acquire a declared reference condition and one or more
perturbed conditions. The analysis:

1. averages repeated rows within each subject/condition;
2. pairs each perturbation with the same subject's reference measurement;
3. computes the perturbation-minus-reference difference;
4. reports mean bias and relative bias;
5. reports 95% limits of agreement when at least two paired subjects exist.

Subjects without both the reference and a given perturbation are excluded from
that specific paired comparison rather than being imputed.

## Scientific interpretation

The effect estimates acquisition sensitivity, not biological change. Therefore
the reference and perturbation acquisitions should be close enough in time that
the intended factor is the principal changed variable.

Recommended perturbation axes follow the acquisition contract:

- illumination;
- working distance / incidence geometry;
- exposure / ISO;
- device model.

These factors should be analyzed separately unless the experimental design
explicitly supports interaction analysis. Device, operator, calibration, and
session identifiers remain provenance variables.

No universal pass/fail threshold is defined by this module. Acceptance limits
must be prospective and justified by the intended use, measurement uncertainty,
and acquisition protocol.

The frozen test partition must not be used to tune perturbation thresholds.
