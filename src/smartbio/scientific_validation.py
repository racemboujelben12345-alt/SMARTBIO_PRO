"""Research-grade scientific validation utilities for SmartBio.

This module adds statistical uncertainty and subgroup diagnostics around the
already-frozen prediction pipeline. It never fits a predictive model, selects
hyperparameters, or calibrates preprocessing.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .regression import regression_metrics


@dataclass(frozen=True)
class BootstrapCI:
    metric: str
    estimate: float
    lower: float
    upper: float
    confidence: float
    n: int
    n_bootstrap: int


def _validate_arrays(y_true, y_pred) -> tuple[np.ndarray, np.ndarray]:
    y = np.asarray(y_true, dtype=float).reshape(-1)
    p = np.asarray(y_pred, dtype=float).reshape(-1)
    if y.size == 0 or y.shape != p.shape:
        raise ValueError("y_true and y_pred must be non-empty arrays with equal length.")
    if not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError("y_true and y_pred must contain only finite values.")
    return y, p


def _metric_value(y_true: np.ndarray, y_pred: np.ndarray, metric: str) -> float:
    values = regression_metrics(y_true, y_pred)
    if metric not in {"mae", "rmse", "r2", "pearson_r"}:
        raise ValueError("metric must be one of: mae, rmse, r2, pearson_r.")
    return float(values[metric])


def bootstrap_metric_ci(
    y_true,
    y_pred,
    *,
    metric: str = "mae",
    confidence: float = 0.95,
    n_bootstrap: int = 2000,
    random_state: int = 42,
) -> BootstrapCI:
    """Estimate a percentile bootstrap CI without refitting any model."""
    y, p = _validate_arrays(y_true, y_pred)
    if not 0 < confidence < 1:
        raise ValueError("confidence must be in (0,1).")
    if n_bootstrap < 100:
        raise ValueError("n_bootstrap must be at least 100.")
    if random_state < 0:
        raise ValueError("random_state must be non-negative.")

    estimate = _metric_value(y, p, metric)
    rng = np.random.default_rng(random_state)
    samples = np.empty(n_bootstrap, dtype=float)

    for i in range(n_bootstrap):
        indices = rng.integers(0, y.size, size=y.size)
        samples[i] = _metric_value(y[indices], p[indices], metric)

    finite = samples[np.isfinite(samples)]
    if finite.size < max(10, n_bootstrap // 2):
        raise ValueError("Too few finite bootstrap replicates to estimate a CI.")

    tail = (1.0 - confidence) / 2.0
    lower, upper = np.quantile(finite, [tail, 1.0 - tail])
    return BootstrapCI(
        metric=metric,
        estimate=estimate,
        lower=float(lower),
        upper=float(upper),
        confidence=float(confidence),
        n=int(y.size),
        n_bootstrap=int(n_bootstrap),
    )


def assert_patient_disjoint(*partitions: pd.DataFrame, patient_col: str = "patient_id") -> None:
    """Reject patient overlap across development/test/external partitions."""
    if len(partitions) < 2:
        raise ValueError("At least two partitions are required.")
    patient_sets: list[set[str]] = []
    for i, frame in enumerate(partitions):
        if patient_col not in frame.columns:
            raise ValueError(f"partition {i} is missing required column '{patient_col}'.")
        if frame[patient_col].isna().any():
            raise ValueError(f"partition {i} contains missing patient IDs.")
        values = frame[patient_col].astype(str)
        if values.duplicated().any():
            raise ValueError(f"partition {i} contains duplicate patient IDs.")
        patient_sets.append(set(values))

    for i in range(len(patient_sets)):
        for j in range(i + 1, len(patient_sets)):
            overlap = patient_sets[i] & patient_sets[j]
            if overlap:
                raise ValueError(
                    f"patient overlap detected between partitions {i} and {j}: "
                    f"{len(overlap)} patient(s)."
                )


def subgroup_metrics(
    frame: pd.DataFrame,
    *,
    target_col: str,
    prediction_col: str,
    group_col: str,
    min_n: int = 10,
) -> pd.DataFrame:
    """Compute frozen-prediction performance by a predeclared subgroup."""
    required = {target_col, prediction_col, group_col}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    if min_n < 1:
        raise ValueError("min_n must be >= 1.")

    rows: list[dict[str, float | int | str]] = []
    for group, subset in frame.groupby(group_col, dropna=False, sort=True):
        if len(subset) < min_n:
            continue
        metrics = regression_metrics(subset[target_col], subset[prediction_col])
        rows.append({
            "group": str(group),
            "n": int(len(subset)),
            "mae": metrics["mae"],
            "rmse": metrics["rmse"],
            "r2": metrics["r2"],
            "pearson_r": metrics["pearson_r"],
            "bland_altman_bias": metrics["bland_altman_bias"],
            "bland_altman_lower": metrics["bland_altman_lower"],
            "bland_altman_upper": metrics["bland_altman_upper"],
        })
    columns = [
        "group", "n", "mae", "rmse", "r2", "pearson_r",
        "bland_altman_bias", "bland_altman_lower", "bland_altman_upper",
    ]
    return pd.DataFrame(rows, columns=columns).sort_values("group").reset_index(drop=True)
