"""Biophysical guardrails for smartphone tissue-optics experiments.

The module deliberately distinguishes physical models from empirical ML.  RGB
JPEG values are not treated as calibrated spectral irradiance.  Beer-Lambert
relations are used only as relative/forward models with explicit assumptions.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class AcquisitionPhysics:
    image_format: str = "unknown"
    bit_depth: int | None = None
    exposure_us: float | None = None
    iso: float | None = None
    white_balance_mode: str | None = None
    raw_available: bool = False
    working_distance_mm: float | None = None
    incidence_angle_deg: float | None = None


def srgb_to_linear(rgb, eps=1e-8):
    """Approximate inverse sRGB transfer; use only when input is sRGB encoded."""
    x = np.asarray(rgb, dtype=np.float64) / 255.0
    x = np.clip(x, 0.0, 1.0)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def validate_physical_capture(meta: dict, *, require_raw=False):
    """Return errors/warnings instead of silently assuming camera physics."""
    errors, warnings = [], []
    raw = meta.get("raw_available", False)
    if isinstance(raw, str):
        parsed = {"true": True, "1": True, "yes": True, "y": True,
                  "false": False, "0": False, "no": False, "n": False}.get(raw.strip().lower())
        if parsed is None:
            errors.append("raw_available must be a boolean or an accepted boolean string.")
        raw = parsed
    if require_raw and raw is not True:
        errors.append("RAW capture is required for this protocol.")
    if not meta.get("image_format"):
        warnings.append("image_format missing; JPEG/sRGB assumptions cannot be verified.")
    exposure = meta.get("exposure_us", meta.get("exposure"))
    iso = meta.get("iso")
    for name, value in (("exposure_us", exposure), ("iso", iso)):
        if value is None:
            errors.append(f"{name} is required for quantitative optical comparison.")
            continue
        try:
            value = float(value)
            if not np.isfinite(value):
                errors.append(f"{name} must be finite.")
            elif value <= 0:
                errors.append(f"{name} must be > 0.")
        except (TypeError, ValueError):
            errors.append(f"{name} must be numeric.")
    if meta.get("bit_depth") is not None:
        try:
            depth = float(meta["bit_depth"])
            if not np.isfinite(depth) or int(depth) != depth or depth < 8:
                errors.append("bit_depth must be a finite integer >= 8.")
        except (TypeError, ValueError):
            errors.append("bit_depth must be an integer.")
    wb = str(meta.get("white_balance_mode", "")).lower()
    if wb in {"", "auto", "awb"}:
        errors.append("Auto white balance is not acceptable for quantitative color comparison.")
    if meta.get("working_distance_mm") is None:
        warnings.append("working_distance_mm missing; illumination geometry is not controlled.")
    else:
        try:
            distance = float(meta["working_distance_mm"])
            if not np.isfinite(distance) or distance <= 0:
                errors.append("working_distance_mm must be finite and > 0.")
        except (TypeError, ValueError):
            errors.append("working_distance_mm must be numeric.")
    if meta.get("incidence_angle_deg") is None:
        warnings.append("incidence_angle_deg missing; illumination geometry is not controlled.")
    else:
        try:
            angle = float(meta["incidence_angle_deg"])
            if not np.isfinite(angle) or not 0 <= angle <= 90:
                errors.append("incidence_angle_deg must be finite and between 0 and 90 degrees.")
        except (TypeError, ValueError):
            errors.append("incidence_angle_deg must be numeric.")
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def relative_optical_density(sample, reference, eps=1e-6):
    """Compute relative OD = -ln(I/I0) after linearization.

    This is a *relative* optical-density feature, not an absolute tissue
    absorption coefficient.  A calibrated reference and stable geometry are
    required for quantitative interpretation.
    """
    s = srgb_to_linear(sample)
    r = srgb_to_linear(reference)
    if s.shape != r.shape or s.ndim < 1 or s.shape[-1] != 3:
        raise ValueError("sample/reference must have matching RGB shape.")
    if np.any(s <= 0) or np.any(r <= 0):
        raise ValueError("OD requires strictly positive linear intensities.")
    return -np.log(np.maximum(s, eps) / np.maximum(r, eps))


def chromaticity(rgb, eps=1e-9):
    x = np.asarray(rgb, dtype=np.float64)
    if x.ndim < 1 or x.shape[-1] != 3:
        raise ValueError("Expected RGB array with last dimension 3.")
    lin = srgb_to_linear(x)
    total = lin.sum(axis=-1, keepdims=True)
    return lin / np.maximum(total, eps)


def flash_ambient_correct(total, ambient, alpha=1.0):
    """Remove an estimated ambient component: I_corrected=I_total-alpha*I_ambient.

    alpha must be experimentally calibrated.  It is *not* inferred from the
    image because camera tone mapping, clipping and exposure can invalidate
    simple subtraction.
    """
    t, a = np.asarray(total, dtype=np.float64), np.asarray(ambient, dtype=np.float64)
    if t.shape != a.shape:
        raise ValueError("total and ambient images must have identical shapes.")
    if np.isscalar(alpha):
        alpha = np.full(3, float(alpha))
    alpha = np.asarray(alpha, dtype=float)
    if alpha.shape != (3,) or np.any(~np.isfinite(alpha)) or np.any(alpha < 0):
        raise ValueError("alpha must be three finite non-negative channel gains.")
    return t - a * alpha.reshape((1,) * (t.ndim - 1) + (3,))


def chromophore_absorption(concentrations, extinction_matrix):
    """Forward model mu_a(lambda) = sum_i epsilon_i(lambda)*c_i.

    `extinction_matrix` must be externally sourced spectral data in compatible
    units. No biological extinction coefficients are hard-coded here.
    """
    c = np.asarray(concentrations, dtype=float)
    E = np.asarray(extinction_matrix, dtype=float)
    if E.ndim != 2 or c.ndim != 1 or E.shape[1] != c.size:
        raise ValueError("extinction matrix shape must be [wavelengths, chromophores].")
    if not np.isfinite(c).all() or not np.isfinite(E).all() or np.any(c < 0):
        raise ValueError("Concentrations/extinction coefficients must be finite; concentrations non-negative.")
    return E @ c


def relative_attenuation(mu_a, mu_s, pathlength_cm):
    """Collimated first-order attenuation proxy using total attenuation mu_a+mu_s.

    This is NOT a diffuse-reflectance tissue model. The reduced scattering
    coefficient mu_s' must not be substituted here; diffuse reflectance
    requires an appropriate transport/diffusion or Monte-Carlo model.
    """
    mua = np.asarray(mu_a, dtype=float)
    mus = np.asarray(mu_s, dtype=float)
    if mua.shape != mus.shape or np.any(~np.isfinite(mua)) or np.any(~np.isfinite(mus)) or np.any(mua < 0) or np.any(mus < 0):
        raise ValueError("Invalid optical-property inputs.")
    try:
        path = float(pathlength_cm)
    except (TypeError, ValueError):
        raise ValueError("pathlength_cm must be numeric.")
    if not np.isfinite(path) or path <= 0:
        raise ValueError("pathlength_cm must be finite and > 0.")
    return np.exp(-(mua + mus) * path)


def identifiability_report(sensitivity_matrix, *, tolerance=1e-10):
    """Check whether channels contain enough independent information.

    A 3-channel RGB measurement cannot uniquely recover 4+ unconstrained
    chromophores. Conditioning is also reported because rank alone is not
    enough for stable inversion.
    """
    A = np.asarray(sensitivity_matrix, dtype=float)
    if A.ndim != 2 or min(A.shape) < 1 or not np.isfinite(A).all():
        raise ValueError("sensitivity_matrix must be a finite 2-D array.")
    rank = int(np.linalg.matrix_rank(A, tol=tolerance))
    cond = float(np.linalg.cond(A)) if min(A.shape) else float("inf")
    return {
        "channels": int(A.shape[0]),
        "parameters": int(A.shape[1]),
        "rank": rank,
        "full_column_rank": bool(rank == A.shape[1]),
        "condition_number": cond,
        "ill_conditioned": bool(not np.isfinite(cond) or cond > 1e3),
        "warning": ("Underdetermined chromophore inversion." if A.shape[0] < A.shape[1]
                    else "Ill-conditioned inversion; regularization/priors required." if not np.isfinite(cond) or cond > 1e3
                    else "No rank deficiency detected; external validation still required."),
    }
