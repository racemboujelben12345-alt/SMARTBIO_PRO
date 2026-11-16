
"""Grouped evaluation and uncertainty helpers."""

import numpy as np


def _validate_finite_array(values, name):
    array = np.asarray(values, dtype=float)

    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional.")

    if len(array) == 0:
        raise ValueError(f"{name} must not be empty.")

    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values.")

    return array


def _validate_z(z):
    if not np.isscalar(z) or not np.isfinite(z) or z < 0:
        raise ValueError("z must be a finite non-negative scalar.")


def grouped_regression(y_true, y_pred, groups):
    y = _validate_finite_array(y_true, "y_true")
    p = _validate_finite_array(y_pred, "y_pred")
    g = np.asarray(groups)

    if g.ndim != 1 or not (len(y) == len(p) == len(g)):
        raise ValueError(
            "y_true, y_pred and groups must have equal lengths."
        )

    if np.any(np.equal(g, None)):
        raise ValueError("groups must not contain missing values.")

    out = {}

    for group in np.unique(g):
        mask = g == group
        err = p[mask] - y[mask]

        out[str(group)] = {
            "n": int(mask.sum()),
            "mae": float(np.mean(np.abs(err))),
            "rmse": float(np.sqrt(np.mean(err ** 2))),
            "bias": float(np.mean(err)),
        }

    return out


def uncertainty_interval(prediction, uncertainty, z=1.96):
    p = _validate_finite_array(prediction, "prediction")
    u = _validate_finite_array(uncertainty, "uncertainty")

    if p.shape != u.shape:
        raise ValueError(
            "prediction and uncertainty must have matching shapes."
        )

    if np.any(u < 0):
        raise ValueError("Uncertainty must be non-negative.")

    _validate_z(z)

    return p - z * u, p + z * u
