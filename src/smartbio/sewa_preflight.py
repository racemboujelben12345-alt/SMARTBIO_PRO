"""Fail-closed preflight checks for an authorized local SEWA export."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import pandas as pd

from .dataset_adapters import SEWA_CAMERA_COLUMNS, SEWA_MODALITIES


@dataclass(frozen=True)
class SewaPreflightReport:
    rows: int
    patients: int
    modalities_present: tuple[str, ...]
    modalities_missing: tuple[str, ...]
    target_cbc_available: int
    target_survey_only: int
    camera_metadata_available: dict[str, int]
    missing_quantitative_fields: tuple[str, ...]
    passed: bool
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


REQUIRED_QUANTITATIVE_FIELDS = (
    "device_model",
    "exposure_us",
    "iso",
    "white_balance_mode",
    "working_distance_mm",
    "incidence_angle_deg",
    "illumination",
)


def preflight_sewa(frame: pd.DataFrame) -> SewaPreflightReport:
    errors: list[str] = []
    if frame.empty:
        return SewaPreflightReport(
            0, 0, (), tuple(SEWA_MODALITIES), 0, 0, {},
            REQUIRED_QUANTITATIVE_FIELDS, False,
            ("SEWA export is empty.",),
        )
    if "patient_uuid" not in frame.columns:
        errors.append("Missing patient_uuid.")
        return SewaPreflightReport(
            len(frame), 0, (), tuple(SEWA_MODALITIES), 0, 0, {},
            REQUIRED_QUANTITATIVE_FIELDS, False, tuple(errors),
        )

    patients = frame["patient_uuid"].astype("string").str.strip()
    present = tuple(m for m, col in SEWA_MODALITIES.items()
                    if col in frame.columns and frame[col].notna().any())
    missing = tuple(m for m in SEWA_MODALITIES if m not in present)

    cbc = (
        pd.to_numeric(frame["cbc_hgb_g_dl"], errors="coerce")
        if "cbc_hgb_g_dl" in frame.columns
        else pd.Series([float("nan")] * len(frame), index=frame.index)
    )
    survey = (
        pd.to_numeric(frame["survey_haemoglobin"], errors="coerce")
        if "survey_haemoglobin" in frame.columns
        else pd.Series([float("nan")] * len(frame), index=frame.index)
    )

    camera_counts = {}
    for modality, column in SEWA_CAMERA_COLUMNS.items():
        camera_counts[modality] = int(
            frame[column].notna().sum() if column in frame.columns else 0
        )

    # These are deliberately reported as missing rather than synthesized.
    missing_fields = list(REQUIRED_QUANTITATIVE_FIELDS)
    errors.append(
        "Quantitative acquisition fields require row-level extraction/validation "
        "after canonicalization; preflight does not infer them."
    )

    if not cbc.notna().any() and not survey.notna().any():
        errors.append("No usable Hb target field found.")

    return SewaPreflightReport(
        rows=len(frame),
        patients=int(patients.nunique()),
        modalities_present=present,
        modalities_missing=missing,
        target_cbc_available=int(cbc.notna().sum()),
        target_survey_only=int((~cbc.notna() & survey.notna()).sum()),
        camera_metadata_available=camera_counts,
        missing_quantitative_fields=tuple(missing_fields),
        passed=False,
        errors=tuple(errors),
    )
