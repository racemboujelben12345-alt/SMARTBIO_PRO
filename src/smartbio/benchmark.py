"""Unified benchmark orchestration for frozen predictions.

This module composes existing validation primitives without fitting models or
changing predictions. It is intentionally explicit so every reported metric
can be traced to the same evaluation vectors and patient identifiers.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence
import json

import numpy as np

from .cluster_bootstrap import cluster_bootstrap_metric_ci
from .regression import regression_metrics
from .statistical_rigor import permutation_test


@dataclass(frozen=True)
class BenchmarkReport:
    n_rows: int
    n_patients: int
    metrics: dict[str, float]
    cluster_ci: dict[str, dict[str, float]]
    permutation: dict[str, dict[str, float]]
    manifest_hash: str

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


def build_benchmark_report(
    y_true,
    y_pred,
    patient_ids: Sequence,
    *,
    manifest_hash: str,
    confidence: float = 0.95,
    n_bootstrap: int = 2000,
    n_permutations: int = 2000,
    random_state: int = 42,
) -> BenchmarkReport:
    """Generate a reproducible statistical benchmark from frozen predictions."""
    y = np.asarray(y_true, dtype=float).reshape(-1)
    p = np.asarray(y_pred, dtype=float).reshape(-1)
    groups = np.asarray(patient_ids).reshape(-1)

    if not manifest_hash or not str(manifest_hash).strip():
        raise ValueError("manifest_hash must be non-empty.")
    if y.size == 0 or y.shape != p.shape or y.shape != groups.shape:
        raise ValueError("y_true, y_pred, and patient_ids must align.")
    if not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError("y_true and y_pred must contain only finite values.")

    metrics = regression_metrics(y, p)
    selected_metrics = {
        k: float(metrics[k])
        for k in (
            "mae",
            "rmse",
            "r2",
            "pearson_r",
            "bland_altman_bias",
            "bland_altman_lower",
            "bland_altman_upper",
        )
    }

    cluster_ci = {}
    for metric in ("mae", "rmse", "r2", "pearson_r"):
        ci = cluster_bootstrap_metric_ci(
            y, p, groups,
            metric=metric,
            confidence=confidence,
            n_bootstrap=n_bootstrap,
            random_state=random_state,
        )
        cluster_ci[metric] = {
            "estimate": ci.estimate,
            "lower": ci.lower,
            "upper": ci.upper,
        }

    permutation = {}
    for metric in ("mae", "rmse"):
        result = permutation_test(
            y, p,
            metric=metric,
            n_permutations=n_permutations,
            random_state=random_state,
        )
        permutation[metric] = {
            "observed": result.observed,
            "null_mean": result.null_mean,
            "null_std": result.null_std,
            "p_value": result.p_value,
        }

    return BenchmarkReport(
        n_rows=int(y.size),
        n_patients=int(np.unique(groups).size),
        metrics=selected_metrics,
        cluster_ci=cluster_ci,
        permutation=permutation,
        manifest_hash=str(manifest_hash),
    )
