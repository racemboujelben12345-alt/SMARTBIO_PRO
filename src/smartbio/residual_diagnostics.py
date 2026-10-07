"""Residual stratification and heteroscedasticity diagnostics.

Engineering/statistical diagnostics only. No clinical thresholds or
acceptance limits are defined by this module.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ResidualDiagnosticsReport:
    n_pairs: int
    n_rows: int
    mean_reference: float
    mean_measurement: float
    mean_residual: float
    residual_sd: float
    mae: float
    rmse: float
    mean_absolute_relative_error_percent: float
    residual_reference_spearman: float
    absolute_residual_reference_spearman: float
    absolute_relative_residual_reference_spearman: float
    absolute_residual_reference_slope: float
    stratified: tuple[dict[str, float], ...]

    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


def _paired(frame, reference_column, measurement_column, subject_column):
    required = {reference_column, measurement_column, subject_column}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("residual-diagnostics frame must not be empty.")
    df = frame[[reference_column, measurement_column, subject_column]].copy()
    for col in (reference_column, measurement_column):
        df[col] = pd.to_numeric(df[col], errors="coerce")
        values = df[col].to_numpy(float)
        if df[col].isna().any() or not np.isfinite(values).all():
            raise ValueError(f"{col} must contain finite numeric values.")
    if df[subject_column].isna().any():
        raise ValueError("subject identifiers must be present.")
    paired = df.groupby(subject_column, sort=True)[[reference_column, measurement_column]].mean().dropna()
    if len(paired) < 3:
        raise ValueError("at least three paired subjects are required.")
    return paired


def _spearman(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0:
        return float("nan")
    rx = pd.Series(x).rank(method="average").to_numpy(float)
    ry = pd.Series(y).rank(method="average").to_numpy(float)
    return float(np.corrcoef(rx, ry)[0, 1])


def _slope(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    centered = x - np.mean(x)
    denominator = float(np.sum(centered ** 2))
    if denominator == 0:
        return float("nan")
    return float(np.sum(centered * (y - np.mean(y))) / denominator)


def _stratify(reference, residual, n_bins):
    if n_bins < 2:
        raise ValueError("n_bins must be at least 2.")
    edges = np.unique(np.quantile(reference, np.linspace(0, 1, n_bins + 1)))
    if len(edges) < 3:
        raise ValueError("reference values must span at least two strata.")
    labels = pd.cut(reference, bins=edges, include_lowest=True, duplicates="drop")
    frame = pd.DataFrame({"reference": reference, "residual": residual, "bin": labels})
    rows = []
    for _, group in frame.groupby("bin", observed=True):
        r = group["residual"].to_numpy(float)
        x = group["reference"].to_numpy(float)
        rows.append({
            "n": float(len(group)),
            "reference_mean": float(np.mean(x)),
            "residual_mean": float(np.mean(r)),
            "residual_sd": float(np.std(r, ddof=1)) if len(r) >= 2 else float("nan"),
            "mae": float(np.mean(np.abs(r))),
        })
    return tuple(rows)


def analyze_residual_diagnostics(
    frame, *, reference_column="reference_value",
    measurement_column="measurement_value", subject_column="patient_id",
    n_bins=4,
):
    """Describe residual behavior across the reference-value range.

    Repeated observations are averaged within subject before diagnostics.
    Correlations, slopes and strata are descriptive diagnostics only.
    """
    paired = _paired(frame, reference_column, measurement_column, subject_column)
    reference = paired[reference_column].to_numpy(float)
    measurement = paired[measurement_column].to_numpy(float)
    residual = measurement - reference
    absolute_residual = np.abs(residual)
    if np.all(reference == 0):
        raise ValueError("reference values cannot all be zero.")
    relative_residual = residual / reference
    if not np.isfinite(relative_residual).all():
        raise ValueError("reference values must be non-zero for relative residual diagnostics.")
    return ResidualDiagnosticsReport(
        n_pairs=int(len(paired)),
        n_rows=int(len(frame)),
        mean_reference=float(np.mean(reference)),
        mean_measurement=float(np.mean(measurement)),
        mean_residual=float(np.mean(residual)),
        residual_sd=float(np.std(residual, ddof=1)),
        mae=float(np.mean(absolute_residual)),
        rmse=float(np.sqrt(np.mean(residual ** 2))),
        mean_absolute_relative_error_percent=float(np.mean(np.abs(relative_residual)) * 100),
        residual_reference_spearman=_spearman(reference, residual),
        absolute_residual_reference_spearman=_spearman(reference, absolute_residual),
        absolute_relative_residual_reference_spearman=_spearman(reference, np.abs(relative_residual)),
        absolute_residual_reference_slope=_slope(reference, absolute_residual),
        stratified=_stratify(reference, residual, n_bins),
    )
