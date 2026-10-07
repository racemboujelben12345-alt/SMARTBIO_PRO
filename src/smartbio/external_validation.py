"""Leakage-safe external validation utilities for SmartBio.

External validation evaluates a completely frozen development pipeline on an
independent dataset/acquisition domain. No fitting, calibration, feature
selection, threshold tuning, or model selection is performed on the external
partition.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .regression import regression_metrics
from .uncertainty import interval_metrics


@dataclass(frozen=True)
class ExternalValidationContract:
    biomarker: str
    target_unit: str
    external_dataset: str
    n_records: int
    n_patients: int


def validate_external_partition(
    external: pd.DataFrame,
    *,
    development: pd.DataFrame,
    biomarker: str,
    target_unit: str,
    external_dataset: str,
) -> ExternalValidationContract:
    """Validate independence and target compatibility before external scoring."""
    required = {"patient_id", "biomarker", "target_unit", "dataset"}
    for name, frame in (("external", external), ("development", development)):
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"{name} missing required columns: {sorted(missing)}")

    if external.empty:
        raise ValueError("External partition must not be empty.")
    if not str(biomarker).strip() or not str(target_unit).strip() or not str(external_dataset).strip():
        raise ValueError("biomarker, target_unit and external_dataset must be non-empty.")

    if external["patient_id"].isna().any() or development["patient_id"].isna().any():
        raise ValueError("patient_id must be present for external validation.")

    if (external["biomarker"].astype(str) != str(biomarker)).any():
        raise ValueError("External biomarker does not match the declared biomarker.")
    if (external["target_unit"].astype(str) != str(target_unit)).any():
        raise ValueError("External target unit does not match the declared unit.")
    if (external["dataset"].astype(str) != str(external_dataset)).any():
        raise ValueError("External dataset identity does not match the declared dataset.")

    overlap = set(external["patient_id"]) & set(development["patient_id"])
    if overlap:
        raise ValueError(
            f"External validation has patient overlap with development data: {len(overlap)} patients."
        )

    return ExternalValidationContract(
        biomarker=str(biomarker),
        target_unit=str(target_unit),
        external_dataset=str(external_dataset),
        n_records=int(len(external)),
        n_patients=int(external["patient_id"].nunique()),
    )


def evaluate_frozen_external(
    y_true,
    y_pred,
    *,
    model: str,
    lower=None,
    upper=None,
) -> dict[str, float | int | str]:
    """Score frozen predictions; this function never fits or calibrates."""
    metrics = regression_metrics(y_true, y_pred)
    result: dict[str, float | int | str] = {"model": str(model), **metrics, "n": int(len(np.asarray(y_true).reshape(-1)))}

    if lower is not None or upper is not None:
        if lower is None or upper is None:
            raise ValueError("Both lower and upper are required for interval evaluation.")
        result.update(interval_metrics(y_true, lower, upper))

    return result
