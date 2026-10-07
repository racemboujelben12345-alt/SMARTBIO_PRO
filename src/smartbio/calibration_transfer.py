"""Calibration-transfer diagnostics for quantitative optical measurements.

Engineering/statistical diagnostics only. This module evaluates whether an
existing calibration model behaves consistently across declared technical
subgroups. It never fits or refits calibration coefficients.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CalibrationTransferResult:
    subgroup: str
    n_pairs: int
    mean_reference: float
    mean_measurement: float
    mean_bias: float
    mae: float
    rmse: float
    relative_bias_percent: float

    def to_dict(self):
        return self.__dict__.copy()


@dataclass(frozen=True)
class CalibrationTransferReport:
    n_rows: int
    n_pairs: int
    subgroup_column: str
    overall_mae: float
    overall_rmse: float
    subgroups: tuple[dict[str, object], ...]

    def to_dict(self):
        return self.__dict__.copy()


def _validate(frame, reference_column, measurement_column, subject_column, subgroup_column):
    required = {reference_column, measurement_column, subject_column, subgroup_column}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("calibration transfer frame must not be empty.")

    df = frame[[reference_column, measurement_column, subject_column, subgroup_column]].copy()
    for col in (reference_column, measurement_column):
        df[col] = pd.to_numeric(df[col], errors="coerce")
        values = df[col].to_numpy(float)
        if df[col].isna().any() or not np.isfinite(values).all():
            raise ValueError(f"{col} must contain finite numeric values.")
    if df[subject_column].isna().any() or df[subgroup_column].isna().any():
        raise ValueError("subject and subgroup identifiers must be present.")

    # Transfer diagnostics must not average a subject across technical subgroups.
    counts = df.groupby(subject_column)[subgroup_column].nunique()
    if (counts > 1).any():
        raise ValueError("each subject must belong to exactly one subgroup.")
    return df


def analyze_calibration_transfer(
    frame,
    *,
    reference_column="reference_value",
    measurement_column="calibrated_value",
    subject_column="patient_id",
    subgroup_column="device_model",
):
    """Assess an already-fitted calibration across declared subgroups.

    Repeated observations are averaged within subject. No calibration
    coefficients are estimated, changed, or selected by this function.
    """
    df = _validate(
        frame, reference_column, measurement_column,
        subject_column, subgroup_column,
    )
    paired = (
        df.groupby([subject_column, subgroup_column], sort=True)
        [[reference_column, measurement_column]]
        .mean()
        .reset_index()
    )
    if len(paired) < 3:
        raise ValueError("at least three paired subjects are required.")

    reference = paired[reference_column].to_numpy(float)
    measurement = paired[measurement_column].to_numpy(float)
    residual = measurement - reference
    overall_mae = float(np.mean(np.abs(residual)))
    overall_rmse = float(np.sqrt(np.mean(residual ** 2)))

    results = []
    for subgroup, group in paired.groupby(subgroup_column, sort=True):
        if len(group) < 2:
            raise ValueError(
                f"subgroup {subgroup!r} must contain at least two paired subjects."
            )
        x = group[reference_column].to_numpy(float)
        y = group[measurement_column].to_numpy(float)
        error = y - x
        mean_reference = float(np.mean(x))
        if mean_reference == 0:
            raise ValueError(f"subgroup {subgroup!r} has zero mean reference.")
        results.append(
            CalibrationTransferResult(
                subgroup=str(subgroup),
                n_pairs=int(len(group)),
                mean_reference=mean_reference,
                mean_measurement=float(np.mean(y)),
                mean_bias=float(np.mean(error)),
                mae=float(np.mean(np.abs(error))),
                rmse=float(np.sqrt(np.mean(error ** 2))),
                relative_bias_percent=float(np.mean(error) / mean_reference * 100),
            ).to_dict()
        )

    return CalibrationTransferReport(
        n_rows=int(len(frame)),
        n_pairs=int(len(paired)),
        subgroup_column=subgroup_column,
        overall_mae=overall_mae,
        overall_rmse=overall_rmse,
        subgroups=tuple(results),
    )
