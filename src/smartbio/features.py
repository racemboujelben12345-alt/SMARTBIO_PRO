"""Biophysical and color feature extraction for SmartBio optical acquisitions."""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .biophysics import chromaticity, relative_optical_density, srgb_to_linear


@dataclass(frozen=True)
class FeatureConfig:
    eps: float = 1e-8
    include_std: bool = True
    include_ratios: bool = True
    include_relative_od: bool = False


def _validate_rgb(rgb: np.ndarray) -> np.ndarray:
    x = np.asarray(rgb, dtype=float)
    if x.ndim != 3 or x.shape[-1] != 3:
        raise ValueError("Expected an RGB ROI with shape HxWx3.")
    if x.shape[0] < 1 or x.shape[1] < 1:
        raise ValueError("RGB ROI must not be empty.")
    if not np.isfinite(x).all():
        raise ValueError("RGB ROI contains non-finite values.")
    return np.clip(x, 0.0, 255.0)


def _safe_ratio(a: float, b: float, eps: float) -> float:
    if not np.isfinite(a) or not np.isfinite(b):
        raise ValueError("Ratio inputs must be finite.")
    return float(a / max(abs(b), eps))


def extract_biophysical_features(rgb, *, reference=None,
                                 config: FeatureConfig | None = None) -> dict[str, float]:
    """Extract interpretable ROI-level optical/color features."""
    config = config or FeatureConfig()
    if config.eps <= 0 or not np.isfinite(config.eps):
        raise ValueError("eps must be finite and > 0.")

    x = _validate_rgb(rgb)
    linear = srgb_to_linear(x)
    mean = linear.mean(axis=(0, 1))
    features = {
        "linear_r_mean": float(mean[0]),
        "linear_g_mean": float(mean[1]),
        "linear_b_mean": float(mean[2]),
        "linear_total_mean": float(mean.sum()),
    }

    if config.include_std:
        std = linear.std(axis=(0, 1))
        features.update({
            "linear_r_std": float(std[0]),
            "linear_g_std": float(std[1]),
            "linear_b_std": float(std[2]),
        })

    chroma = chromaticity(x, eps=config.eps).mean(axis=(0, 1))
    features.update({
        "chrom_r_mean": float(chroma[0]),
        "chrom_g_mean": float(chroma[1]),
        "chrom_b_mean": float(chroma[2]),
    })

    if config.include_ratios:
        features.update({
            "r_over_g": _safe_ratio(mean[0], mean[1], config.eps),
            "r_over_b": _safe_ratio(mean[0], mean[2], config.eps),
            "g_over_b": _safe_ratio(mean[1], mean[2], config.eps),
        })

    if config.include_relative_od:
        if reference is None:
            raise ValueError("reference is required when include_relative_od=True.")
        ref = _validate_rgb(reference)
        if ref.shape != x.shape:
            raise ValueError("reference must have the same shape as rgb.")
        od = relative_optical_density(x, ref, eps=config.eps)
        od_mean = od.mean(axis=(0, 1))
        features.update({
            "relative_od_r_mean": float(od_mean[0]),
            "relative_od_g_mean": float(od_mean[1]),
            "relative_od_b_mean": float(od_mean[2]),
        })

    if not np.isfinite(list(features.values())).all():
        raise ValueError("Feature extraction produced non-finite values.")
    return features
