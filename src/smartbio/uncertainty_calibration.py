"""Diagnostics for frozen prediction-interval calibration.

Engineering/statistical uncertainty diagnostic; not a clinical confidence statement.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class IntervalCalibrationReport:
    n_rows: int
    n_subjects: int
    nominal_coverage: float
    observed_coverage: float
    coverage_error: float
    miss_rate: float
    mean_interval_width: float
    median_interval_width: float
    coverage_ci_low: float | None
    coverage_ci_high: float | None

    def to_dict(self) -> dict[str, float | int | None]:
        return {
            "n_rows": self.n_rows,
            "n_subjects": self.n_subjects,
            "nominal_coverage": self.nominal_coverage,
            "observed_coverage": self.observed_coverage,
            "coverage_error": self.coverage_error,
            "miss_rate": self.miss_rate,
            "mean_interval_width": self.mean_interval_width,
            "median_interval_width": self.median_interval_width,
            "coverage_ci_low": self.coverage_ci_low,
            "coverage_ci_high": self.coverage_ci_high,
        }


def _validate_inputs(y_true, lower, upper, subject_ids=None):
    y = np.asarray(y_true, dtype=float).reshape(-1)
    lo = np.asarray(lower, dtype=float).reshape(-1)
    hi = np.asarray(upper, dtype=float).reshape(-1)
    if y.size == 0 or y.shape != lo.shape or y.shape != hi.shape:
        raise ValueError("y_true, lower and upper must have equal non-zero length.")
    if not np.isfinite(y).all() or not np.isfinite(lo).all() or not np.isfinite(hi).all():
        raise ValueError("Interval inputs must be finite.")
    if np.any(lo > hi):
        raise ValueError("lower bounds cannot exceed upper bounds.")

    if subject_ids is None:
        subjects = None
    else:
        subjects = np.asarray(subject_ids, dtype=object).reshape(-1)
        if subjects.shape != y.shape:
            raise ValueError("subject_ids must have the same length as interval inputs.")
        if any(item is None for item in subjects):
            raise ValueError("subject_ids must not contain null values.")
        if any(isinstance(item, float) and np.isnan(item) for item in subjects):
            raise ValueError("subject_ids must not contain NaN values.")
    return y, lo, hi, subjects


def _bootstrap_coverage(y, lo, hi, subjects, *, n_bootstrap: int, seed: int):
    unique_subjects, inverse = np.unique(subjects, return_inverse=True)
    if unique_subjects.size < 2:
        raise ValueError("At least two subjects are required for bootstrap coverage inference.")
    if n_bootstrap < 2000:
        raise ValueError("n_bootstrap must be >= 2000 for production inference.")
    if seed < 0:
        raise ValueError("seed must be non-negative.")

    rng = np.random.default_rng(seed)
    covered = (y >= lo) & (y <= hi)
    by_subject = [covered[inverse == idx] for idx in range(unique_subjects.size)]
    draws = np.empty(n_bootstrap, dtype=float)
    for i in range(n_bootstrap):
        sampled = rng.integers(0, unique_subjects.size, size=unique_subjects.size)
        draws[i] = float(np.mean(np.concatenate([by_subject[idx] for idx in sampled])))
    return float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def analyze_interval_calibration(
    y_true,
    lower,
    upper,
    *,
    alpha: float,
    subject_ids=None,
    n_bootstrap: int = 2000,
    seed: int = 42,
) -> IntervalCalibrationReport:
    """Assess empirical coverage of frozen prediction intervals."""
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0,1).")
    y, lo, hi, subjects = _validate_inputs(y_true, lower, upper, subject_ids)
    covered = (y >= lo) & (y <= hi)
    widths = hi - lo

    if subjects is None:
        n_subjects = int(y.size)
        coverage_ci_low = None
        coverage_ci_high = None
    else:
        n_subjects = int(np.unique(subjects).size)
        coverage_ci_low, coverage_ci_high = _bootstrap_coverage(
            y, lo, hi, subjects, n_bootstrap=n_bootstrap, seed=seed
        )

    observed = float(np.mean(covered))
    nominal = float(1.0 - alpha)
    return IntervalCalibrationReport(
        n_rows=int(y.size),
        n_subjects=n_subjects,
        nominal_coverage=nominal,
        observed_coverage=observed,
        coverage_error=observed - nominal,
        miss_rate=float(1.0 - observed),
        mean_interval_width=float(np.mean(widths)),
        median_interval_width=float(np.median(widths)),
        coverage_ci_low=coverage_ci_low,
        coverage_ci_high=coverage_ci_high,
    )
