"""Temporal stability and drift analysis for repeated control measurements.

This is an engineering monitoring layer. It does not define clinical
acceptance limits or prove clinical stability.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class TemporalStabilityReport:
    n_rows: int
    n_sessions: int
    baseline_mean: float
    session_mean_cv_percent: float
    max_abs_relative_drift_percent: float
    linear_drift_per_session: float

    def to_dict(self) -> dict[str, object]:
        return {
            "n_rows": self.n_rows,
            "n_sessions": self.n_sessions,
            "baseline_mean": self.baseline_mean,
            "session_mean_cv_percent": self.session_mean_cv_percent,
            "max_abs_relative_drift_percent": self.max_abs_relative_drift_percent,
            "linear_drift_per_session": self.linear_drift_per_session,
        }


def analyze_temporal_stability(
    frame,
    *,
    value_column: str = "measurement_value",
    session_column: str = "session_id",
) -> TemporalStabilityReport:
    required = {value_column, session_column}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("measurement frame must not be empty.")

    df = frame[[value_column, session_column]].copy()
    df[value_column] = pd.to_numeric(df[value_column], errors="coerce")
    if df[value_column].isna().any():
        raise ValueError("measurement values must be finite numeric values.")
    if not np.isfinite(df[value_column].to_numpy(float)).all():
        raise ValueError("measurement values must be finite.")
    if df[session_column].isna().any():
        raise ValueError("session identifiers must be present.")

    session_means = df.groupby(session_column, sort=True)[value_column].mean()
    if len(session_means) < 2:
        raise ValueError("at least two sessions are required.")

    means = session_means.to_numpy(float)
    baseline = float(means[0])
    if baseline == 0:
        raise ValueError("baseline mean must be non-zero for relative drift.")

    session_cv = (
        100.0 * float(np.std(means, ddof=1)) / abs(float(np.mean(means)))
    )
    relative_drift = 100.0 * (means - baseline) / abs(baseline)
    max_abs_drift = float(np.max(np.abs(relative_drift)))

    x = np.arange(len(means), dtype=float)
    slope = float(np.polyfit(x, means, 1)[0])

    return TemporalStabilityReport(
        n_rows=int(len(df)),
        n_sessions=int(len(session_means)),
        baseline_mean=baseline,
        session_mean_cv_percent=session_cv,
        max_abs_relative_drift_percent=max_abs_drift,
        linear_drift_per_session=slope,
    )
