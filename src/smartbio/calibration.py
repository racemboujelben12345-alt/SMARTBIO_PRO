"""Leakage-safe calibration utilities for smartphone optical measurements.

Calibration is an engineering preprocessing stage, not a clinical calibration.
Fits must be learned only from training/calibration partitions and applied
unchanged to validation, test, or external data.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .biophysics import relative_optical_density, srgb_to_linear
from .optical import flash_minus_ambient

_ALLOWED_FIT_PARTITIONS = {"train", "calibration"}


@dataclass(frozen=True)
class AffineCalibrationModel:
    """Immutable affine mapping from observed linear-RGB features to reference."""

    coefficients: np.ndarray
    n_samples: int
    n_features: int
    fit_partition: str
    fit_rmse: float

    def __post_init__(self) -> None:
        coef = np.asarray(self.coefficients, dtype=float)
        if coef.shape != (self.n_features + 1, self.n_features):
            raise ValueError("Invalid affine coefficient shape.")
        if not np.isfinite(coef).all():
            raise ValueError("Calibration coefficients must be finite.")
        if self.n_samples < 3:
            raise ValueError("At least 3 paired samples are required.")
        if self.fit_partition not in _ALLOWED_FIT_PARTITIONS:
            raise ValueError(
                "fit_partition must be 'train' or 'calibration'; "
                "test/external data cannot fit calibration."
            )
        if not np.isfinite(self.fit_rmse) or self.fit_rmse < 0:
            raise ValueError("fit_rmse must be finite and non-negative.")
        object.__setattr__(self, "coefficients", coef)


def linearize_srgb(rgb: np.ndarray) -> np.ndarray:
    """Convert sRGB-coded RGB values to linear RGB for optical feature work."""
    x = np.asarray(rgb, dtype=float)
    if x.ndim < 1 or x.shape[-1] != 3:
        raise ValueError("Expected RGB data with last dimension 3.")
    if not np.isfinite(x).all():
        raise ValueError("RGB data must be finite.")
    return srgb_to_linear(x)


def _validate_paired_arrays(observed, reference) -> tuple[np.ndarray, np.ndarray]:
    obs = np.asarray(observed, dtype=float)
    ref = np.asarray(reference, dtype=float)
    if obs.ndim != 2 or ref.ndim != 2 or obs.shape != ref.shape:
        raise ValueError("observed/reference must be matching 2D arrays.")
    if obs.shape[1] != 3:
        raise ValueError("Calibration currently expects three RGB features.")
    if obs.shape[0] < 3:
        raise ValueError("At least 3 paired samples are required for calibration.")
    if not np.isfinite(obs).all() or not np.isfinite(ref).all():
        raise ValueError("Calibration data must be finite.")
    return obs, ref


def fit_affine(observed, reference, *, fit_partition: str = "calibration") -> np.ndarray:
    """Fit an affine RGB mapping in linearized feature space."""
    obs, ref = _validate_paired_arrays(observed, reference)
    if fit_partition not in _ALLOWED_FIT_PARTITIONS:
        raise ValueError(
            "fit_partition must be 'train' or 'calibration'; "
            "test/external data cannot fit calibration."
        )
    X = np.c_[obs, np.ones(len(obs))]
    coef, *_ = np.linalg.lstsq(X, ref, rcond=None)
    return coef


def fit_affine_model(
    observed,
    reference,
    *,
    fit_partition: str = "calibration",
) -> AffineCalibrationModel:
    """Fit an auditable affine calibration model and record its provenance."""
    obs, ref = _validate_paired_arrays(observed, reference)
    coef = fit_affine(obs, ref, fit_partition=fit_partition)
    pred = np.c_[obs, np.ones(len(obs))] @ coef
    rmse = float(np.sqrt(np.mean((pred - ref) ** 2)))
    return AffineCalibrationModel(
        coefficients=coef,
        n_samples=int(len(obs)),
        n_features=int(obs.shape[1]),
        fit_partition=fit_partition,
        fit_rmse=rmse,
    )


def apply_affine(values, coef) -> np.ndarray:
    """Apply an existing affine calibration without refitting."""
    values = np.asarray(values, dtype=float)
    coef = np.asarray(coef, dtype=float)
    if values.ndim != 2 or values.shape[1] != 3:
        raise ValueError("values must be a 2D array with three RGB features.")
    if coef.shape != (4, 3):
        raise ValueError("coef must have shape (4, 3).")
    if not np.isfinite(values).all() or not np.isfinite(coef).all():
        raise ValueError("values and coef must be finite.")
    return np.c_[values, np.ones(len(values))] @ coef


def apply_affine_model(values, model: AffineCalibrationModel) -> np.ndarray:
    """Apply a fitted model; this function never modifies/refits the model."""
    if not isinstance(model, AffineCalibrationModel):
        raise TypeError("model must be an AffineCalibrationModel.")
    return apply_affine(values, model.coefficients)


def flash_minus_no_flash(flash, no_flash, *, metadata=None, alpha=1.0):
    """Legacy alias; quantitative use requires matched acquisition metadata."""
    if metadata is None:
        raise ValueError(
            "Quantitative flash/no-flash correction requires matched metadata; "
            "use optical.flash_minus_ambient()."
        )
    return flash_minus_ambient(flash, no_flash, metadata=metadata, alpha=alpha)


def relative_od(sample, reference):
    """Compute relative optical density after sRGB linearization.

    This is a relative feature requiring a valid reference and controlled
    acquisition geometry; it is not an absolute tissue absorption estimate.
    """
    return relative_optical_density(sample, reference)
