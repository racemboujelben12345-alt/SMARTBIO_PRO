"""Deterministic, non-clinical image quality gate.

Thresholds are engineering audit starting points. They must be fitted from
training/calibration data before ML evaluation. Raw images are never modified.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from PIL import Image

_ILLUMINATION_GRID_SIZE = 10


@dataclass(frozen=True)
class QualityGateConfig:
    low_sharpness: float = 1454.422186
    high_illum_cv: float = 0.35052719712257385
    high_saturation: float = 0.010814
    low_dynamic_range: float = 172.0

    def __post_init__(self) -> None:
        for name in (
            "low_sharpness",
            "high_illum_cv",
            "high_saturation",
            "low_dynamic_range",
        ):
            try:
                value = float(getattr(self, name))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{name} must be a finite non-negative number.") from exc
            if not np.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be a finite non-negative number.")
            if name == "high_saturation" and value > 1:
                raise ValueError("high_saturation must be between 0 and 1.")
            object.__setattr__(self, name, value)

def _illumination_cv(gray: np.ndarray, grid: int = 10) -> float:
    h, w = gray.shape
    row_blocks = np.array_split(gray, min(grid, h), axis=0)
    means = [
        float(block.mean())
        for row in row_blocks
        for block in np.array_split(row, min(grid, w), axis=1)
    ]
    mean = float(np.mean(means))
    return float(np.std(means) / mean) if mean > 0 else float("inf")

def assess_image(path: str | Path, config: QualityGateConfig | None = None) -> dict:
    config = config or QualityGateConfig()
    path = Path(path)
    with Image.open(path) as image:
        rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
        gray = np.asarray(image.convert("L"), dtype=np.float32)
    low_clip = float(np.mean(rgb <= 5))
    high_clip = float(np.mean(rgb >= 250))
    p01, p99 = np.percentile(rgb, [1, 99])
    metrics = {
        "path": str(path), "mean_intensity": float(rgb.mean()),
        "std_intensity": float(rgb.std()), "p01": float(p01), "p99": float(p99),
        "dynamic_range": float(p99-p01), "low_clip_ratio": low_clip,
        "high_clip_ratio": high_clip, "saturation_ratio": low_clip+high_clip,
        "sharpness": float(gray.var()), "illum_cv": _illumination_cv(gray),
        "image_width": int(gray.shape[1]), "image_height": int(gray.shape[0]),
    }
    flags = {
        "flag_insufficient_dimensions": min(gray.shape) < _ILLUMINATION_GRID_SIZE,
        "flag_low_sharpness": metrics["sharpness"] < config.low_sharpness,
        "flag_high_illum_cv": metrics["illum_cv"] > config.high_illum_cv,
        "flag_high_saturation": metrics["saturation_ratio"] > config.high_saturation,
        "flag_low_dynamic_range": metrics["dynamic_range"] < config.low_dynamic_range,
    }
    metrics.update(flags)
    metrics["flag_count"] = int(sum(flags.values()))
    metrics["quality_status"] = ("PASS" if metrics["flag_count"] == 0 else
                                  "REVIEW" if metrics["flag_count"] == 1 else "FAIL")
    return metrics

def assess_paths(paths: Iterable[str | Path], config: QualityGateConfig | None = None) -> pd.DataFrame:
    return pd.DataFrame([assess_image(path, config) for path in paths])

