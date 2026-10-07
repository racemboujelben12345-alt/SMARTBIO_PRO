"""Leakage-safe uncertainty estimation for SmartBio regression.

Split-conformal prediction intervals are calibrated on a dedicated calibration
partition and then frozen for test/external evaluation. This is an engineering
uncertainty layer, not a clinical confidence statement.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ConformalIntervalModel:
    alpha: float
    quantile: float
    n_calibration: int
    calibration_rmse: float
    fit_partition: str = "calibration"

    def __post_init__(self) -> None:
        if not 0 < self.alpha < 1:
            raise ValueError("alpha must be in (0,1).")
        if not np.isfinite(self.quantile) or self.quantile < 0:
            raise ValueError("quantile must be finite and non-negative.")
        if self.n_calibration < 1:
            raise ValueError("At least one calibration sample is required.")
        if not np.isfinite(self.calibration_rmse) or self.calibration_rmse < 0:
            raise ValueError("calibration_rmse must be finite and non-negative.")
        if self.fit_partition != "calibration":
            raise ValueError("Conformal uncertainty must be calibrated on the calibration partition.")


def _validate(y_true, y_pred):
    y = np.asarray(y_true, dtype=float).reshape(-1)
    p = np.asarray(y_pred, dtype=float).reshape(-1)
    if y.size == 0 or y.shape != p.shape:
        raise ValueError("Inputs must be non-empty arrays with equal length.")
    if not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError("Inputs must contain only finite values.")
    return y, p


def _conformal_quantile(scores: np.ndarray, alpha: float) -> float:
    n = scores.size
    rank = int(np.ceil((n + 1) * (1 - alpha)))
    rank = min(max(rank, 1), n)
    return float(np.sort(scores)[rank - 1])


def fit_split_conformal(y_calibration, pred_calibration, *, alpha=0.10) -> ConformalIntervalModel:
    y, p = _validate(y_calibration, pred_calibration)
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0,1).")
    residuals = np.abs(y - p)
    q = _conformal_quantile(residuals, alpha)
    rmse = float(np.sqrt(np.mean((y - p) ** 2)))
    return ConformalIntervalModel(
        alpha=float(alpha),
        quantile=q,
        n_calibration=int(y.size),
        calibration_rmse=rmse,
    )


def predict_interval(predictions, model: ConformalIntervalModel):
    pred = np.asarray(predictions, dtype=float).reshape(-1)
    if pred.size == 0 or not np.isfinite(pred).all():
        raise ValueError("predictions must be non-empty and finite.")
    return pred - model.quantile, pred + model.quantile


def interval_metrics(y_true, lower, upper) -> dict[str, float]:
    y = np.asarray(y_true, dtype=float).reshape(-1)
    lo = np.asarray(lower, dtype=float).reshape(-1)
    hi = np.asarray(upper, dtype=float).reshape(-1)
    if y.size == 0 or y.shape != lo.shape or y.shape != hi.shape:
        raise ValueError("y_true, lower and upper must have equal non-zero length.")
    if not np.isfinite(y).all() or not np.isfinite(lo).all() or not np.isfinite(hi).all():
        raise ValueError("Interval inputs must be finite.")
    if np.any(lo > hi):
        raise ValueError("lower bounds cannot exceed upper bounds.")
    covered = (y >= lo) & (y <= hi)
    widths = hi - lo
    return {
        "coverage": float(np.mean(covered)),
        "mean_interval_width": float(np.mean(widths)),
        "median_interval_width": float(np.median(widths)),
        "n": int(y.size),
    }


def abstention_mask(predictions, lower, upper, *, max_width):
    pred = np.asarray(predictions, dtype=float).reshape(-1)
    lo = np.asarray(lower, dtype=float).reshape(-1)
    hi = np.asarray(upper, dtype=float).reshape(-1)
    if pred.shape != lo.shape or pred.shape != hi.shape or pred.size == 0:
        raise ValueError("predictions and bounds must have equal non-zero length.")
    if not np.isfinite(pred).all() or not np.isfinite(lo).all() or not np.isfinite(hi).all():
        raise ValueError("Inputs must be finite.")
    if not np.isfinite(max_width) or max_width <= 0:
        raise ValueError("max_width must be finite and > 0.")
    if np.any(lo > hi):
        raise ValueError("lower bounds cannot exceed upper bounds.")
    return (hi - lo) > float(max_width)
