"""Leakage-safe regression baselines and agreement metrics for SmartBio.

Models are deliberately interpretable before deep learning. Pipelines fit all
transformations on training data only. This module evaluates quantitative
biomarker estimation; it does not establish clinical validity.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class RegressionResult:
    model: str
    mae: float
    rmse: float
    r2: float
    pearson_r: float
    bland_altman_bias: float
    bland_altman_lower: float
    bland_altman_upper: float
    n: int


def _validate_xy(y_true, y_pred) -> tuple[np.ndarray, np.ndarray]:
    y = np.asarray(y_true, dtype=float).reshape(-1)
    p = np.asarray(y_pred, dtype=float).reshape(-1)
    if y.shape != p.shape or y.size == 0:
        raise ValueError("y_true and y_pred must be non-empty arrays with equal length.")
    if not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError("y_true and y_pred must contain only finite values.")
    return y, p


def regression_metrics(y_true, y_pred) -> dict[str, float]:
    y, p = _validate_xy(y_true, y_pred)
    err = p - y
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err**2)))
    ss_res = float(np.sum(err**2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan")
    if y.size < 2 or np.std(y) == 0 or np.std(p) == 0:
        pearson = float("nan")
    else:
        pearson = float(np.corrcoef(y, p)[0, 1])

    mean_pair = (y + p) / 2.0
    diff = p - y
    bias = float(np.mean(diff))
    sd = float(np.std(diff, ddof=1)) if diff.size > 1 else float("nan")
    loa = 1.96 * sd if np.isfinite(sd) else float("nan")
    return {
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "pearson_r": pearson,
        "bland_altman_bias": bias,
        "bland_altman_lower": float(bias - loa),
        "bland_altman_upper": float(bias + loa),
        "mean_reference": float(np.mean(mean_pair)),
    }


def evaluate_predictions(y_true, y_pred, *, model: str) -> RegressionResult:
    m = regression_metrics(y_true, y_pred)
    return RegressionResult(
        model=model,
        mae=m["mae"],
        rmse=m["rmse"],
        r2=m["r2"],
        pearson_r=m["pearson_r"],
        bland_altman_bias=m["bland_altman_bias"],
        bland_altman_lower=m["bland_altman_lower"],
        bland_altman_upper=m["bland_altman_upper"],
        n=len(np.asarray(y_true).reshape(-1)),
    )


def make_baselines(*, random_state: int = 42) -> dict[str, object]:
    """Return frozen model definitions; fitting happens only on training data."""
    return {
        "linear": Pipeline([
            ("scale", StandardScaler()),
            ("model", LinearRegression()),
        ]),
        "ridge": Pipeline([
            ("scale", StandardScaler()),
            ("model", Ridge(alpha=1.0)),
        ]),
        "lasso": Pipeline([
            ("scale", StandardScaler()),
            ("model", Lasso(alpha=0.01, max_iter=10000)),
        ]),
        "random_forest": RandomForestRegressor(
            n_estimators=300, max_depth=None, min_samples_leaf=2,
            random_state=random_state, n_jobs=-1,
        ),
        "gradient_boosting": GradientBoostingRegressor(
            n_estimators=200, learning_rate=0.05, max_depth=2,
            random_state=random_state,
        ),
    }


def fit_and_evaluate(
    X_train,
    y_train,
    X_test,
    y_test,
    *,
    models: dict[str, object] | None = None,
) -> pd.DataFrame:
    """Fit on train only and evaluate once on a frozen test partition."""
    Xtr = np.asarray(X_train, dtype=float)
    Xte = np.asarray(X_test, dtype=float)
    ytr = np.asarray(y_train, dtype=float).reshape(-1)
    yte = np.asarray(y_test, dtype=float).reshape(-1)
    if Xtr.ndim != 2 or Xte.ndim != 2 or Xtr.shape[1] != Xte.shape[1]:
        raise ValueError("X_train/X_test must be 2D arrays with matching feature counts.")
    if len(Xtr) != len(ytr) or len(Xte) != len(yte):
        raise ValueError("Feature and target lengths must match.")
    if not np.isfinite(Xtr).all() or not np.isfinite(Xte).all():
        raise ValueError("Feature matrices must contain only finite values.")
    if not np.isfinite(ytr).all() or not np.isfinite(yte).all():
        raise ValueError("Targets must contain only finite values.")

    models = models or make_baselines()
    rows: list[dict[str, float | str | int]] = []
    for name, model in models.items():
        model.fit(Xtr, ytr)
        pred = model.predict(Xte)
        result = evaluate_predictions(yte, pred, model=name)
        rows.append(result.__dict__)
    return pd.DataFrame(rows).sort_values("mae").reset_index(drop=True)
