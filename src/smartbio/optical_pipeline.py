"""Deterministic optical preprocessing for quantitative ROI analysis.

This module is deliberately conservative:
- anatomical ROI provenance is required upstream;
- 8-bit RGB/JPEG is treated as camera-encoded sRGB, not spectroscopy;
- saturated/clipped pixels are excluded from quantitative summaries;
- channel gains may only be applied when an explicit calibration provenance ID
  and three finite non-negative gains are supplied;
- no anatomical localization, denoising, color constancy, or learned transform
  is inferred here.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .biophysics import srgb_to_linear
from .optical import saturation_mask


@dataclass(frozen=True)
class OpticalPreprocessConfig:
    low_code: int = 1
    high_code: int = 254
    min_valid_fraction: float = 0.80
    clip_linear: bool = True

    def __post_init__(self) -> None:
        if not (0 <= self.low_code < self.high_code <= 255):
            raise ValueError("Invalid RGB clipping thresholds.")
        if not 0 < self.min_valid_fraction <= 1:
            raise ValueError("min_valid_fraction must be in (0, 1].")


@dataclass(frozen=True)
class OpticalPreprocessResult:
    linear_rgb: np.ndarray
    valid_mask: np.ndarray
    saturation_fraction: float
    valid_fraction: float
    quality_status: str
    calibration_id: str | None = None

    def summary(self) -> dict[str, object]:
        return {
            "saturation_fraction": self.saturation_fraction,
            "valid_fraction": self.valid_fraction,
            "quality_status": self.quality_status,
            "calibration_id": self.calibration_id,
        }


def _validate_rgb(rgb: np.ndarray) -> np.ndarray:
    x = np.asarray(rgb)
    if x.ndim != 3 or x.shape[-1] != 3 or x.shape[0] < 1 or x.shape[1] < 1:
        raise ValueError("Expected a non-empty HxWx3 RGB ROI.")
    x = x.astype(np.float64, copy=False)
    if not np.isfinite(x).all():
        raise ValueError("RGB ROI contains non-finite values.")
    if np.any(x < 0) or np.any(x > 255):
        raise ValueError("RGB values must be within [0, 255].")
    return x


def validate_channel_gains(gains) -> np.ndarray:
    g = np.asarray(gains, dtype=float)
    if g.shape != (3,) or not np.isfinite(g).all() or np.any(g < 0):
        raise ValueError("channel_gains must contain three finite non-negative values.")
    return g


def preprocess_roi(
    rgb,
    *,
    config: OpticalPreprocessConfig | None = None,
    channel_gains=None,
    calibration_id: str | None = None,
) -> OpticalPreprocessResult:
    """Linearize an explicit RGB ROI and produce a deterministic quality mask.

    Channel gains are optional. If supplied, an explicit non-empty calibration
    ID is mandatory so downstream reports cannot silently hide calibration.
    """
    cfg = config or OpticalPreprocessConfig()
    x = _validate_rgb(rgb)

    if channel_gains is not None and not str(calibration_id or "").strip():
        raise ValueError("calibration_id is required when channel_gains are supplied.")

    clipped = saturation_mask(x, low=cfg.low_code, high=cfg.high_code)
    valid = ~clipped.any(axis=-1)
    saturation_fraction = float(clipped.mean())
    valid_fraction = float(valid.mean())

    linear = srgb_to_linear(x)
    if channel_gains is not None:
        gains = validate_channel_gains(channel_gains)
        linear = linear * gains.reshape(1, 1, 3)

    if cfg.clip_linear:
        linear = np.maximum(linear, 0.0)

    status = "PASS" if valid_fraction >= cfg.min_valid_fraction else "FAIL"
    return OpticalPreprocessResult(
        linear_rgb=linear,
        valid_mask=valid,
        saturation_fraction=saturation_fraction,
        valid_fraction=valid_fraction,
        quality_status=status,
        calibration_id=(str(calibration_id).strip() if calibration_id else None),
    )


def masked_channel_summary(result: OpticalPreprocessResult) -> dict[str, float]:
    """Summarize only unsaturated pixels; never silently drop the quality flag."""
    if result.valid_fraction <= 0:
        raise ValueError("Cannot summarize an ROI with no valid pixels.")
    values = result.linear_rgb[result.valid_mask]
    return {
        "linear_r_mean": float(values[:, 0].mean()),
        "linear_g_mean": float(values[:, 1].mean()),
        "linear_b_mean": float(values[:, 2].mean()),
        "valid_fraction": result.valid_fraction,
        "saturation_fraction": result.saturation_fraction,
    }
