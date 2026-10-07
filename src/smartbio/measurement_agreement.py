"""Measurement agreement and paired error decomposition.

Engineering measurement-quality analysis only. This module does not define
clinical acceptance limits or clinical equivalence.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd

@dataclass(frozen=True)
class MeasurementAgreementReport:
    n_rows: int
    n_pairs: int
    n_subjects: int
    mean_reference: float
    mean_measurement: float
    mean_bias: float
    relative_bias_percent: float
    mae: float
    rmse: float
    error_sd: float | None
    loa_low: float | None
    loa_high: float | None
    systematic_error_fraction_percent: float

    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()

def analyze_measurement_agreement(frame, *, reference_column="reference_value",
    measurement_column="measurement_value", subject_column="patient_id"):
    required={reference_column,measurement_column,subject_column}
    missing=required-set(frame.columns)
    if missing: raise ValueError(f"missing required columns: {sorted(missing)}")
    if frame.empty: raise ValueError("measurement frame must not be empty.")
    df=frame[[reference_column,measurement_column,subject_column]].copy()
    for col in (reference_column,measurement_column):
        df[col]=pd.to_numeric(df[col],errors="coerce")
        values=df[col].to_numpy(float)
        if df[col].isna().any() or not np.isfinite(values).all():
            raise ValueError(f"{col} must contain finite numeric values.")
    if df[subject_column].isna().any():
        raise ValueError("subject identifiers must be present.")
    paired=(df.groupby(subject_column,sort=True)[[reference_column,measurement_column]]
              .mean().dropna())
    if paired.empty: raise ValueError("no paired subjects are available.")
    reference=paired[reference_column].to_numpy(float)
    measurement=paired[measurement_column].to_numpy(float)
    errors=measurement-reference
    mean_reference=float(np.mean(reference))
    if mean_reference==0: raise ValueError("mean reference must be non-zero for relative bias.")
    mean_measurement=float(np.mean(measurement))
    mean_bias=float(np.mean(errors))
    relative_bias=100.0*mean_bias/abs(mean_reference)
    mae=float(np.mean(np.abs(errors)))
    rmse=float(np.sqrt(np.mean(errors**2)))
    error_sd=loa_low=loa_high=None
    if len(errors)>=2:
        error_sd=float(np.std(errors,ddof=1))
        loa_low=mean_bias-1.96*error_sd
        loa_high=mean_bias+1.96*error_sd
    error_variance=float(np.var(errors,ddof=1)) if len(errors)>=2 else 0.0
    systematic_fraction=100.0*(mean_bias**2)/(mean_bias**2+error_variance) if (mean_bias!=0 or error_variance!=0) else 0.0
    return MeasurementAgreementReport(
        n_rows=int(len(df)), n_pairs=int(len(paired)), n_subjects=int(len(paired)),
        mean_reference=mean_reference, mean_measurement=mean_measurement,
        mean_bias=mean_bias, relative_bias_percent=float(relative_bias),
        mae=mae, rmse=rmse, error_sd=error_sd,
        loa_low=float(loa_low) if loa_low is not None else None,
        loa_high=float(loa_high) if loa_high is not None else None,
        systematic_error_fraction_percent=float(systematic_fraction))
