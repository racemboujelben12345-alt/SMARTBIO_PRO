"""Biophysical and color feature extraction for SmartBio optical acquisitions."""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
import cv2
import numpy as np
import pandas as pd

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


# Backward-compatible acquisition helpers retained from the previous feature API.
def load_rgb(path):
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Cannot read image: {path}")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def center_roi(image, fraction=0.60):
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0,1]")
    h, w = image.shape[:2]
    rh, rw = max(1, int(h * fraction)), max(1, int(w * fraction))
    y, x = (h - rh) // 2, (w - rw) // 2
    return image[y:y + rh, x:x + rw]


def roi_from_metadata(image, row):
    keys = ("roi_x0", "roi_y0", "roi_x1", "roi_y1")
    if all(k in row.index and pd.notna(row[k]) for k in keys):
        x0, y0, x1, y1 = [int(row[k]) for k in keys]
        h, w = image.shape[:2]
        if not (0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h):
            raise ValueError("Explicit ROI box is outside image bounds.")
        return image[y0:y1, x0:x1].copy()
    if "roi_type" in row.index and pd.notna(row.get("roi_type")):
        raise ValueError("roi_type is specified but ROI coordinates are missing; refusing to use a center ROI.")
    raise ValueError("Explicit ROI coordinates are required for scientific feature extraction.")


def extract(path, roi=None, roi_fraction=0.60, *, allow_demo_center_roi=False):
    """Legacy entry point; scientific default still requires an explicit ROI."""
    image = load_rgb(path)
    if roi is None:
        if not allow_demo_center_roi:
            raise ValueError("Explicit anatomical ROI is required; center ROI is demo-only and must be explicitly enabled.")
        rgb = center_roi(image, roi_fraction)
    else:
        rgb = roi
    return extract_biophysical_features(rgb)


def extract_dataset(metadata_csv, output_csv, *, require_explicit_roi=True):
    df = pd.read_csv(metadata_csv)
    if "image_path" not in df:
        raise ValueError("image_path is required.")
    rows = []
    for _, row in df.iterrows():
        item = row.to_dict()
        try:
            image = load_rgb(row["image_path"])
            if require_explicit_roi:
                roi = roi_from_metadata(image, row)
                item.update(extract_biophysical_features(roi))
            else:
                item.update(extract(row["image_path"], allow_demo_center_roi=True))
            item["feature_error"] = None
        except Exception as exc:
            item["feature_error"] = str(exc)
        rows.append(item)
    out = pd.DataFrame(rows)
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_csv, index=False)
    return out
