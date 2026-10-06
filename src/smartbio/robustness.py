"""Grouped evaluation and uncertainty helpers."""
import numpy as np


def grouped_regression(y_true, y_pred, groups):
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_pred, dtype=float)
    g = np.asarray(groups)
    if not (len(y) == len(p) == len(g)):
        raise ValueError("y_true, y_pred and groups must have equal length.")
    out = {}
    for group in np.unique(g):
        m = g == group
        err = p[m] - y[m]
        out[str(group)] = {
            "n": int(m.sum()),
            "mae": float(np.mean(np.abs(err))),
            "rmse": float(np.sqrt(np.mean(err ** 2))),
            "bias": float(np.mean(err)),
        }
    return out


def uncertainty_interval(prediction, uncertainty, z=1.96):
    p = np.asarray(prediction, dtype=float)
    u = np.asarray(uncertainty, dtype=float)
    if p.shape != u.shape:
        raise ValueError("prediction and uncertainty must have matching shapes.")
    if np.any(u < 0):
        raise ValueError("Uncertainty must be non-negative.")
    return p - z * u, p + z * u
