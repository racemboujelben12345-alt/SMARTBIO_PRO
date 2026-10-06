"""Calibration helpers with explicit optical-safety requirements."""
import numpy as np
from .optical import flash_minus_ambient, validate_pair_metadata

def flash_minus_no_flash(flash, no_flash, *, metadata=None, alpha=1.0):
    """Legacy alias; quantitative use requires matched acquisition metadata."""
    if metadata is None:
        raise ValueError("Quantitative flash/no-flash correction requires matched metadata; use optical.flash_minus_ambient().")
    return flash_minus_ambient(flash, no_flash, metadata=metadata, alpha=alpha)

def fit_affine(observed, reference):
    observed, reference = np.asarray(observed,float), np.asarray(reference,float)
    if observed.ndim != 2 or reference.ndim != 2 or observed.shape != reference.shape:
        raise ValueError("observed/reference must be matching 2D arrays.")
    if observed.shape[0] < 3:
        raise ValueError("At least 3 paired samples are required for affine calibration.")
    if not np.isfinite(observed).all() or not np.isfinite(reference).all():
        raise ValueError("Calibration data must be finite.")
    X = np.c_[observed, np.ones(len(observed))]
    coef, *_ = np.linalg.lstsq(X, reference, rcond=None)
    return coef

def apply_affine(values, coef):
    values = np.asarray(values,float)
    return np.c_[values, np.ones(len(values))] @ coef
