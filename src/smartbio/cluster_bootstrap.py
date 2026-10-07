"""Cluster-aware statistical validation helpers.

For repeated measurements, patient-level resampling is preferred over naive
row bootstrap because all observations from a patient stay together.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .regression import regression_metrics


@dataclass(frozen=True)
class ClusterBootstrapCI:
    metric: str
    estimate: float
    lower: float
    upper: float
    confidence: float
    n_rows: int
    n_clusters: int
    n_bootstrap: int


def cluster_bootstrap_metric_ci(
    y_true,
    y_pred,
    groups,
    *,
    metric: str = "mae",
    confidence: float = 0.95,
    n_bootstrap: int = 2000,
    random_state: int = 42,
) -> ClusterBootstrapCI:
    """Bootstrap complete clusters and compute a percentile confidence interval."""
    y = np.asarray(y_true, dtype=float).reshape(-1)
    p = np.asarray(y_pred, dtype=float).reshape(-1)
    g = np.asarray(groups).reshape(-1)
    if y.size == 0 or y.shape != p.shape or y.shape != g.shape:
        raise ValueError("y_true, y_pred, and groups must have equal non-zero length.")
    if not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError("y_true and y_pred must contain only finite values.")
    if metric not in {"mae", "rmse", "r2", "pearson_r"}:
        raise ValueError("unsupported metric")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1.")
    if n_bootstrap < 200:
        raise ValueError("n_bootstrap must be at least 200.")
    if random_state < 0:
        raise ValueError("random_state must be non-negative.")
    if any(x is None or str(x).strip() == "" for x in g):
        raise ValueError("groups must contain valid identifiers.")

    unique = np.unique(g)
    rng = np.random.default_rng(random_state)
    values = np.empty(n_bootstrap, dtype=float)
    for i in range(n_bootstrap):
        sampled = rng.choice(unique, size=len(unique), replace=True)
        mask = np.concatenate([np.flatnonzero(g == cluster) for cluster in sampled])
        values[i] = regression_metrics(y[mask], p[mask])[metric]

    alpha = 1.0 - confidence
    return ClusterBootstrapCI(
        metric=metric,
        estimate=float(regression_metrics(y, p)[metric]),
        lower=float(np.quantile(values, alpha / 2)),
        upper=float(np.quantile(values, 1 - alpha / 2)),
        confidence=confidence,
        n_rows=int(y.size),
        n_clusters=int(len(unique)),
        n_bootstrap=n_bootstrap,
    )
