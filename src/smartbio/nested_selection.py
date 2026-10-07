"""Leakage-safe nested cross-validation for model selection."""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from sklearn.base import clone
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupKFold, GridSearchCV


@dataclass(frozen=True)
class NestedCVResult:
    outer_mae: tuple[float, ...]
    outer_rmse: tuple[float, ...]
    mean_mae: float
    mean_rmse: float
    n_outer_folds: int


def nested_group_cv(
    X, y, groups, estimator, param_grid, *,
    outer_splits: int = 5,
    inner_splits: int = 4,
    scoring: str = "neg_mean_absolute_error",
) -> NestedCVResult:
    """Run nested CV with group-disjoint outer and inner folds."""
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float).reshape(-1)
    groups = np.asarray(groups).reshape(-1)
    if X.ndim != 2 or len(X) != len(y) or len(y) != len(groups) or len(y) == 0:
        raise ValueError("X, y, and groups must have compatible non-empty shapes.")
    if not np.isfinite(X).all() or not np.isfinite(y).all():
        raise ValueError("X and y must contain only finite values.")
    if outer_splits < 2 or inner_splits < 2:
        raise ValueError("outer_splits and inner_splits must be >= 2.")
    if len(np.unique(groups)) < max(outer_splits, inner_splits):
        raise ValueError("not enough unique groups for requested folds.")

    outer = GroupKFold(n_splits=outer_splits)
    inner = GroupKFold(n_splits=inner_splits)
    maes, rmses = [], []

    for train_idx, test_idx in outer.split(X, y, groups):
        search = GridSearchCV(
            estimator=clone(estimator),
            param_grid=param_grid,
            scoring=scoring,
            cv=inner,
            refit=True,
            n_jobs=-1,
            error_score="raise",
        )
        search.fit(X[train_idx], y[train_idx], groups=groups[train_idx])
        pred = search.predict(X[test_idx])
        maes.append(float(mean_absolute_error(y[test_idx], pred)))
        rmses.append(float(np.sqrt(mean_squared_error(y[test_idx], pred))))

    return NestedCVResult(
        outer_mae=tuple(maes),
        outer_rmse=tuple(rmses),
        mean_mae=float(np.mean(maes)),
        mean_rmse=float(np.mean(rmses)),
        n_outer_folds=outer_splits,
    )
