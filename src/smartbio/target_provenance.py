"""Fail-closed provenance controls for quantitative biomarker targets.

A target value is not considered benchmark-ready merely because it is numeric.
This module requires an explicit reference measurement identity and method so
Hb/bilirubin targets can be traced back to their reference source.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
import pandas as pd

REQUIRED_TARGET_PROVENANCE_FIELDS = {
    "biomarker",
    "target_unit",
    "target_source",
    "reference_method",
    "reference_measurement_id",
}

ALLOWED_REFERENCE_TYPES = {"laboratory", "validated_reference"}


@dataclass(frozen=True)
class TargetProvenanceContract:
    """Immutable declaration of the reference provenance of one target."""

    biomarker: str
    target_unit: str
    target_source: str
    reference_method: str
    reference_measurement_id: str
    reference_type: str = "laboratory"
    target_time_delta_min: float | None = None

    def __post_init__(self) -> None:
        for name in (
            "biomarker",
            "target_unit",
            "target_source",
            "reference_method",
            "reference_measurement_id",
        ):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} must be non-empty.")

        reference_type = str(self.reference_type).strip().lower()
        if reference_type not in ALLOWED_REFERENCE_TYPES:
            raise ValueError(
                "reference_type must be 'laboratory' or 'validated_reference'."
            )

        if self.target_time_delta_min is not None:
            delta = float(self.target_time_delta_min)
            if not np.isfinite(delta) or delta < 0:
                raise ValueError(
                    "target_time_delta_min must be finite and non-negative."
                )


def _missing(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def validate_target_provenance(
    row: Mapping,
    *,
    expected_biomarker: str | None = None,
    expected_unit: str | None = None,
) -> dict[str, object]:
    """Validate target provenance for one record without inferring metadata."""
    errors: list[str] = []
    warnings: list[str] = []

    for field in sorted(REQUIRED_TARGET_PROVENANCE_FIELDS):
        if field not in row or _missing(row[field]):
            errors.append(f"Missing target provenance field: {field}")

    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings}

    biomarker = str(row["biomarker"]).strip().lower()
    unit = str(row["target_unit"]).strip()
    reference_type = str(row.get("reference_type", "laboratory")).strip().lower()

    if expected_biomarker is not None and biomarker != str(expected_biomarker).strip().lower():
        errors.append(
            f"Biomarker mismatch: expected {expected_biomarker!r}, got {biomarker!r}."
        )

    if expected_unit is not None and unit != str(expected_unit).strip():
        errors.append(
            f"Target unit mismatch: expected {expected_unit!r}, got {unit!r}."
        )

    if reference_type not in ALLOWED_REFERENCE_TYPES:
        errors.append(f"Unsupported reference_type: {reference_type!r}.")

    delta = row.get("target_time_delta_min")
    if delta is not None and not _missing(delta):
        try:
            value = float(delta)
            if not np.isfinite(value) or value < 0:
                errors.append("target_time_delta_min must be finite and non-negative.")
        except (TypeError, ValueError):
            errors.append("target_time_delta_min must be numeric.")

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def validate_target_provenance_frame(
    frame: pd.DataFrame,
    *,
    expected_biomarker: str | None = None,
    expected_unit: str | None = None,
    require_unique_reference_measurements: bool = True,
) -> dict[str, object]:
    """Fail closed on target provenance before quantitative benchmarking."""
    if frame.empty:
        raise ValueError("frame must not be empty.")

    missing = REQUIRED_TARGET_PROVENANCE_FIELDS - set(frame.columns)
    if missing:
        return {
            "valid": False,
            "errors": [f"Missing target provenance columns: {sorted(missing)}"],
            "warnings": [],
            "n_rows": int(len(frame)),
        }

    errors: list[str] = []
    warnings: list[str] = []

    for idx, row in frame.iterrows():
        result = validate_target_provenance(
            row,
            expected_biomarker=expected_biomarker,
            expected_unit=expected_unit,
        )
        if not result["valid"]:
            errors.extend([f"row {idx}: {e}" for e in result["errors"]])

    if require_unique_reference_measurements:
        ids = frame["reference_measurement_id"].astype("string").str.strip()
        duplicated = ids[ids.duplicated(keep=False)]
        if not duplicated.empty:
            errors.append(
                "reference_measurement_id is duplicated; one reference measurement "
                "must not silently represent multiple independent target records."
            )

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "n_rows": int(len(frame)),
        "n_reference_measurements": int(
            frame["reference_measurement_id"].astype("string").nunique()
        ),
    }


def contract_from_row(row: Mapping) -> TargetProvenanceContract:
    """Build an immutable target contract; never infer missing provenance."""
    result = validate_target_provenance(row)
    if not result["valid"]:
        raise ValueError(
            "Target provenance contract failed: " + "; ".join(result["errors"])
        )

    delta = row.get("target_time_delta_min")
    return TargetProvenanceContract(
        biomarker=str(row["biomarker"]).strip().lower(),
        target_unit=str(row["target_unit"]).strip(),
        target_source=str(row["target_source"]).strip(),
        reference_method=str(row["reference_method"]).strip(),
        reference_measurement_id=str(row["reference_measurement_id"]).strip(),
        reference_type=str(row.get("reference_type", "laboratory")).strip().lower(),
        target_time_delta_min=None if _missing(delta) else float(delta),
    )
