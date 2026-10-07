"""Method-comparison regression for paired measurement data.

Engineering/statistical method-comparison only. This module does not define
clinical acceptance limits, diagnostic thresholds, or equivalence.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class MethodComparisonReport:
    n_pairs: int
    n_rows: int
    mean_reference: float
    mean_measurement: float
    deming_slope: float
    deming_intercept: float
    deming_slope_ci_low: float
    deming_slope_ci_high: float
    deming_intercept_ci_low: float
    deming_intercept_ci_high: float
    passing_bablok_slope: float
    passing_bablok_intercept: float
    passing_bablok_slope_ci_low: float
    passing_bablok_slope_ci_high: float
    passing_bablok_intercept_ci_low: float
    passing_bablok_intercept_ci_high: float
    variance_ratio: float

    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


def _paired(frame, reference_column, measurement_column, subject_column):
    required = {reference_column, measurement_column, subject_column}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("method-comparison frame must not be empty.")
    df = frame[[reference_column, measurement_column, subject_column]].copy()
    for col in (reference_column, measurement_column):
        df[col] = pd.to_numeric(df[col], errors="coerce")
        values = df[col].to_numpy(float)
        if df[col].isna().any() or not np.isfinite(values).all():
            raise ValueError(f"{col} must contain finite numeric values.")
    if df[subject_column].isna().any():
        raise ValueError("subject identifiers must be present.")
    paired = (
        df.groupby(subject_column, sort=True)[[reference_column, measurement_column]]
        .mean().dropna()
    )
    if len(paired) < 3:
        raise ValueError("at least three paired subjects are required.")
    return paired


def _deming(x, y, variance_ratio):
    if not np.isfinite(variance_ratio) or variance_ratio <= 0:
        raise ValueError("variance_ratio must be finite and greater than zero.")
    xbar, ybar = float(np.mean(x)), float(np.mean(y))
    sxx = float(np.sum((x - xbar) ** 2) / (len(x) - 1))
    syy = float(np.sum((y - ybar) ** 2) / (len(y) - 1))
    sxy = float(np.sum((x - xbar) * (y - ybar)) / (len(x) - 1))
    if sxx == 0:
        raise ValueError("reference values must have non-zero variance.")
    if sxy == 0:
        raise ValueError("reference and measurement covariance must be non-zero.")
    delta = syy - variance_ratio * sxx
    slope = (delta + np.sqrt(delta * delta + 4 * variance_ratio * sxy * sxy)) / (2 * sxy)
    return float(slope), float(ybar - slope * xbar)


def _passing_bablok(x, y):
    slopes = []
    for i in range(len(x) - 1):
        dx, dy = x[i + 1:] - x[i], y[i + 1:] - y[i]
        valid = dx != 0
        slopes.extend((dy[valid] / dx[valid]).tolist())
    if not slopes:
        raise ValueError("Passing-Bablok requires at least one finite pairwise slope.")
    slope = float(np.median(np.asarray(slopes, dtype=float)))
    return slope, float(np.median(y - slope * x))


def _bootstrap_ci(x, y, estimator, n_bootstrap, seed):
    if n_bootstrap < 200:
        raise ValueError("n_bootstrap must be at least 200.")
    rng = np.random.default_rng(seed)
    estimates, n, attempts = [], len(x), 0
    while len(estimates) < n_bootstrap and attempts < n_bootstrap * 5:
        attempts += 1
        idx = rng.integers(0, n, size=n)
        try:
            estimates.append(estimator(x[idx], y[idx]))
        except ValueError:
            continue
    if len(estimates) < n_bootstrap:
        raise ValueError("insufficient valid bootstrap resamples for confidence intervals.")
    arr = np.asarray(estimates, dtype=float)
    return (
        float(np.quantile(arr[:, 0], 0.025)),
        float(np.quantile(arr[:, 0], 0.975)),
        float(np.quantile(arr[:, 1], 0.025)),
        float(np.quantile(arr[:, 1], 0.975)),
    )


def analyze_method_comparison(
    frame, *, reference_column="reference_value",
    measurement_column="measurement_value", subject_column="patient_id",
    variance_ratio=1.0, n_bootstrap=2000, seed=42
):
    """Analyze paired reference-vs-measurement method comparison.

    variance_ratio is sigma_measurement^2 / sigma_reference^2. The default
    equal-error setting is an engineering sensitivity assumption, not a
    learned or clinical parameter.
    """
    paired = _paired(frame, reference_column, measurement_column, subject_column)
    x = paired[reference_column].to_numpy(float)
    y = paired[measurement_column].to_numpy(float)
    deming = lambda a, b: _deming(a, b, variance_ratio)
    ds, di = deming(x, y)
    ps, pi = _passing_bablok(x, y)
    dc = _bootstrap_ci(x, y, deming, n_bootstrap, seed)
    pc = _bootstrap_ci(x, y, _passing_bablok, n_bootstrap, seed + 1)
    return MethodComparisonReport(
        n_pairs=int(len(paired)), n_rows=int(len(frame)),
        mean_reference=float(np.mean(x)), mean_measurement=float(np.mean(y)),
        deming_slope=ds, deming_intercept=di,
        deming_slope_ci_low=dc[0], deming_slope_ci_high=dc[1],
        deming_intercept_ci_low=dc[2], deming_intercept_ci_high=dc[3],
        passing_bablok_slope=ps, passing_bablok_intercept=pi,
        passing_bablok_slope_ci_low=pc[0], passing_bablok_slope_ci_high=pc[1],
        passing_bablok_intercept_ci_low=pc[2], passing_bablok_intercept_ci_high=pc[3],
        variance_ratio=float(variance_ratio),
    )
