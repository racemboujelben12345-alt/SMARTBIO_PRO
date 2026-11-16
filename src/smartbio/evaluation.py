import numpy as np


def _validate_pair(y_true, y_pred, min_samples=1):
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_pred, dtype=float)

    if y.ndim != 1 or p.ndim != 1:
        raise ValueError("Inputs must be one-dimensional.")
    if len(y) != len(p):
        raise ValueError("Inputs must have equal length.")
    if len(y) < min_samples:
        raise ValueError(f"At least {min_samples} observations are required.")
    if not np.all(np.isfinite(y)) or not np.all(np.isfinite(p)):
        raise ValueError("Inputs must contain only finite values.")

    return y, p


def regression_metrics(y_true, y_pred):
    y, p = _validate_pair(y_true, y_pred)

    e = p - y
    ss_res = np.sum(e ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)

    pearson_r = (
        float(np.corrcoef(y, p)[0, 1])
        if len(y) > 1 and np.std(y) > 0 and np.std(p) > 0
        else float("nan")
    )

    return {
        "n": int(len(y)),
        "mae": float(np.mean(np.abs(e))),
        "rmse": float(np.sqrt(np.mean(e ** 2))),
        "r2": float(1 - ss_res / ss_tot) if ss_tot else float("nan"),
        "pearson_r": pearson_r,
        "bias": float(np.mean(e)),
    }


def bland_altman(y_true, y_pred):
    y, p = _validate_pair(y_true, y_pred, min_samples=2)

    d = p - y
    bias = d.mean()
    sd = d.std(ddof=1)

    return {
        "bias": float(bias),
        "loa_lower": float(bias - 1.96 * sd),
        "loa_upper": float(bias + 1.96 * sd),
    }


def coverage_under_uncertainty(y_true, pred, uncertainty, z=1.96):
    y, p = _validate_pair(y_true, pred)
    u = np.asarray(uncertainty, dtype=float)

    if u.ndim != 1 or u.shape != y.shape:
        raise ValueError("uncertainty must match the shape of y_true.")
    if not np.all(np.isfinite(u)) or np.any(u < 0):
        raise ValueError("Uncertainty must be finite and non-negative.")
    if not np.isfinite(z) or z < 0:
        raise ValueError("z must be finite and non-negative.")

    inside = np.abs(y - p) <= z * u
    return {"coverage": float(np.mean(inside)), "n": int(len(y))}
