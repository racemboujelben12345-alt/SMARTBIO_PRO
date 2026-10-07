"""Fail-closed preflight for the Fingertip Video Dataset.

The preflight validates only explicit manifest information. It never infers
patient IDs, Hb labels, or acquisition metadata from filenames or paper text.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import pandas as pd

from .acquisition import REQUIRED_QUANTITATIVE_FIELDS


REQUIRED_MANIFEST_FIELDS = {
    "patient_id",
    "video_path",
    "hemoglobin_gdl",
    "reference_measurement_id",
}


@dataclass(frozen=True)
class FingertipPreflightReport:
    rows: int
    patients: int
    videos_present: int
    videos_missing: int
    target_available: int
    provenance_complete: int
    missing_quantitative_fields: list[str]
    passed: bool
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def preflight_fingertip(frame: pd.DataFrame) -> FingertipPreflightReport:
    if frame.empty:
        return FingertipPreflightReport(
            0, 0, 0, 0, 0, 0,
            sorted(REQUIRED_QUANTITATIVE_FIELDS),
            False,
            ["Fingertip manifest is empty."],
        )

    missing = REQUIRED_MANIFEST_FIELDS - set(frame.columns)
    if missing:
        return FingertipPreflightReport(
            len(frame), 0, 0, 0, 0, 0,
            sorted(REQUIRED_QUANTITATIVE_FIELDS),
            False,
            [f"Missing explicit manifest fields: {sorted(missing)}"],
        )

    patients = frame["patient_id"].astype("string").str.strip()
    videos = frame["video_path"].astype("string").str.strip()
    reference_ids = frame["reference_measurement_id"].astype("string").str.strip()

    target = pd.to_numeric(frame["hemoglobin_gdl"], errors="coerce")
    target_available = int(target.notna().sum())
    provenance_complete = int(
        (patients.notna() & patients.ne("") &
         videos.notna() & videos.ne("") &
         reference_ids.notna() & reference_ids.ne("") &
         target.notna()).sum()
    )

    errors: list[str] = []
    if patients.eq("").any() or patients.isna().any():
        errors.append("patient_id contains missing or empty values.")
    if videos.eq("").any() or videos.isna().any():
        errors.append("video_path contains missing or empty values.")
    if target.isna().any():
        errors.append("hemoglobin_gdl contains missing or non-numeric values.")
    if reference_ids.eq("").any() or reference_ids.isna().any():
        errors.append("reference_measurement_id contains missing or empty values.")

    # These fields are intentionally not inferred from the paper or filenames.
    missing_quantitative = sorted(REQUIRED_QUANTITATIVE_FIELDS)
    errors.append(
        "Quantitative acquisition metadata are not accepted from filename inference "
        "or paper-level descriptions; explicit row-level values are required."
    )

    return FingertipPreflightReport(
        rows=len(frame),
        patients=int(patients.nunique(dropna=True)),
        videos_present=int((videos.notna() & videos.ne("")).sum()),
        videos_missing=int((videos.isna() | videos.eq("")).sum()),
        target_available=target_available,
        provenance_complete=provenance_complete,
        missing_quantitative_fields=missing_quantitative,
        passed=False,
        errors=errors,
    )
