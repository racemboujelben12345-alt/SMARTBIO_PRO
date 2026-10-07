"""Repeatability and reproducibility analysis for SmartBio measurements.

This is an engineering measurement-quality layer. It does not establish
clinical agreement or diagnostic performance.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RepeatabilityReport:
    n_rows: int
    n_subjects: int
    n_repeated_subjects: int
    n_devices: int
    within_subject_sd: float
    repeatability_coefficient: float
    mean_within_subject_cv_percent: float
    between_device_mean_bias: float | None
    between_device_sd: float | None
    between_device_loa_low: float | None
    between_device_loa_high: float | None

    def to_dict(self) -> dict[str, object]:
        return {
            "n_rows": self.n_rows,
            "n_subjects": self.n_subjects,
            "n_repeated_subjects": self.n_repeated_subjects,
            "n_devices": self.n_devices,
            "within_subject_sd": self.within_subject_sd,
            "repeatability_coefficient": self.repeatability_coefficient,
            "mean_within_subject_cv_percent": self.mean_within_subject_cv_percent,
            "between_device_mean_bias": self.between_device_mean_bias,
            "between_device_sd": self.between_device_sd,
            "between_device_loa_low": self.between_device_loa_low,
            "between_device_loa_high": self.between_device_loa_high,
        }


def _validate_frame(frame, value_column, subject_column, device_column):
    required = {value_column, subject_column, device_column}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("measurement frame must not be empty.")
    out = frame[[value_column, subject_column, device_column]].copy()
    out[value_column] = pd.to_numeric(out[value_column], errors="coerce")
    if out[value_column].isna().any():
        raise ValueError("measurement values must be finite numeric values.")
    if out[subject_column].isna().any() or out[device_column].isna().any():
        raise ValueError("subject and device identifiers must be present.")
    if not np.isfinite(out[value_column].to_numpy(float)).all():
        raise ValueError("measurement values must be finite.")
    return out


def _paired_device_differences(frame, value_column, subject_column, device_column):
    means = (
        frame.groupby([subject_column, device_column], sort=True)[value_column]
        .mean().reset_index()
    )
    devices = sorted(means[device_column].astype(str).unique())
    if len(devices) != 2:
        return np.asarray([], dtype=float)
    pivot = means.pivot(index=subject_column, columns=device_column, values=value_column)
    pivot = pivot.dropna(subset=devices)
    if pivot.empty:
        return np.asarray([], dtype=float)
    return (pivot[devices[1]] - pivot[devices[0]]).to_numpy(float)


def analyze_repeatability(
    frame,
    *,
    value_column="measurement_value",
    subject_column="patient_id",
    device_column="device_model",
):
    """Estimate within-subject repeatability and paired two-device reproducibility."""
    df = _validate_frame(frame, value_column, subject_column, device_column)
    groups = df.groupby(subject_column, sort=True)[value_column]
    group_sizes = groups.size()
    n_repeated = int((group_sizes >= 2).sum())
    if n_repeated == 0:
        raise ValueError("at least one subject with two measurements is required.")

    within_sds = groups.agg(
        lambda x: float(np.std(x.to_numpy(float), ddof=1)) if len(x) >= 2 else np.nan
    ).dropna().to_numpy(float)
    if within_sds.size == 0:
        raise ValueError("within-subject variance could not be estimated.")
    within_sd = float(np.sqrt(np.mean(within_sds ** 2)))
    repeatability = float(2.77 * within_sd)

    cvs = []
    for _, values in groups:
        arr = values.to_numpy(float)
        if len(arr) >= 2 and np.mean(arr) != 0:
            cvs.append(100.0 * float(np.std(arr, ddof=1)) / abs(float(np.mean(arr))))
    mean_cv = float(np.mean(cvs)) if cvs else float("nan")

    n_devices = int(df[device_column].nunique())
    bias = sd = loa_low = loa_high = None
    if n_devices == 2:
        differences = _paired_device_differences(
            df, value_column, subject_column, device_column
        )
        if differences.size >= 2:
            bias = float(np.mean(differences))
            sd = float(np.std(differences, ddof=1))
            loa_low = float(bias - 1.96 * sd)
            loa_high = float(bias + 1.96 * sd)

    return RepeatabilityReport(
        n_rows=int(len(df)),
        n_subjects=int(df[subject_column].nunique()),
        n_repeated_subjects=n_repeated,
        n_devices=n_devices,
        within_subject_sd=within_sd,
        repeatability_coefficient=repeatability,
        mean_within_subject_cv_percent=mean_cv,
        between_device_mean_bias=bias,
        between_device_sd=sd,
        between_device_loa_low=loa_low,
        between_device_loa_high=loa_high,
    )
