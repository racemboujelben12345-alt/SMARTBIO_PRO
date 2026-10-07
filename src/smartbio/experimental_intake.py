"""Fail-closed experimental intake and data-integrity audit.

This layer validates a quantitative acquisition manifest against local assets
without inventing missing metadata. It is intentionally independent of any
biomarker model.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

import pandas as pd

from .roi import ROIBox, validate_roi_geometry, validate_roi_type

REQUIRED_COLUMNS = {
    "patient_id", "image_id", "image_path", "source_dataset", "biomarker",
    "target_value", "target_unit", "target_source", "reference_method",
    "reference_measurement_id", "reference_type", "roi_type", "device_model",
    "illumination", "acquisition_id", "exposure_us", "iso",
    "white_balance_mode", "working_distance_mm", "incidence_angle_deg",
    "image_width", "image_height", "roi_x0", "roi_y0", "roi_x1", "roi_y1",
}

QUANTITATIVE_FIELDS = {
    "device_model", "exposure_us", "iso", "white_balance_mode",
    "working_distance_mm", "incidence_angle_deg", "illumination",
}


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _missing(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def audit_experimental_intake(
    frame: pd.DataFrame,
    *,
    data_root: str | Path | None = None,
    require_assets: bool = True,
    expected_biomarker: str | None = None,
    expected_unit: str | None = None,
) -> dict[str, object]:
    """Audit manifest structure, provenance, assets, duplicates and hashes.

    The function does not infer IDs, targets, acquisition settings or geometry.
    Missing quantitative metadata is always an error when running a quantitative
    experiment.
    """
    if frame.empty:
        raise ValueError("Experimental intake manifest must not be empty.")

    errors: list[str] = []
    warnings: list[str] = []
    missing_columns = REQUIRED_COLUMNS - set(frame.columns)
    if missing_columns:
        errors.append(f"Missing manifest columns: {sorted(missing_columns)}")
        return {"passed": False, "errors": errors, "warnings": warnings, "n_rows": len(frame)}

    root = Path(data_root) if data_root is not None else None
    resolved_paths: list[Path | None] = []
    hashes: list[str | None] = []

    for idx, row in frame.iterrows():
        prefix = f"row {idx}"

        for field in (
            "patient_id", "image_id", "source_dataset", "biomarker",
            "target_unit", "target_source", "reference_method",
            "reference_measurement_id", "reference_type", "roi_type",
            "device_model", "illumination", "acquisition_id",
        ):
            if _missing(row[field]):
                errors.append(f"{prefix}: missing required field {field}")

        if expected_biomarker and str(row["biomarker"]).strip().lower() != expected_biomarker.lower():
            errors.append(f"{prefix}: biomarker mismatch")
        if expected_unit and str(row["target_unit"]).strip() != expected_unit:
            errors.append(f"{prefix}: target unit mismatch")

        try:
            target = float(row["target_value"])
            if not pd.notna(target):
                raise ValueError
        except (TypeError, ValueError):
            errors.append(f"{prefix}: target_value is not numeric")

        for field in ("exposure_us", "iso", "working_distance_mm", "incidence_angle_deg"):
            if _missing(row[field]):
                errors.append(f"{prefix}: missing quantitative field {field}")
            else:
                try:
                    value = float(row[field])
                    if not pd.notna(value) or value < 0:
                        raise ValueError
                except (TypeError, ValueError):
                    errors.append(f"{prefix}: invalid numeric field {field}")

        if _missing(row["white_balance_mode"]):
            errors.append(f"{prefix}: white_balance_mode is missing")
        elif str(row["white_balance_mode"]).strip().lower() in {"auto", "awb", "automatic"}:
            errors.append(f"{prefix}: automatic white balance is not allowed")

        if str(row["illumination"]).strip().lower() not in {"flash", "ambient", "controlled_led", "reference"}:
            errors.append(f"{prefix}: unsupported illumination")

        # ROI provenance is quantitative metadata, not an optional annotation.
        # Validate target-specific ROI type and explicit geometry against the
        # declared image dimensions; never infer or repair missing coordinates.
        try:
            validate_roi_type(str(row["biomarker"]).strip().lower(), str(row["roi_type"]).strip().lower())
        except ValueError as exc:
            errors.append(f"{prefix}: invalid ROI type: {exc}")
        try:
            width = int(row["image_width"])
            height = int(row["image_height"])
            box = ROIBox(
                int(row["roi_x0"]), int(row["roi_y0"]),
                int(row["roi_x1"]), int(row["roi_y1"]),
            )
            validate_roi_geometry(box, image_width=width, image_height=height)
        except (TypeError, ValueError, OverflowError) as exc:
            errors.append(f"{prefix}: invalid ROI geometry: {exc}")

        path_value = str(row["image_path"]).strip()
        path = Path(path_value)
        if root is not None and not path.is_absolute():
            path = root / path
        resolved_paths.append(path)

        if require_assets:
            if not path.exists():
                errors.append(f"{prefix}: asset does not exist: {path}")
                hashes.append(None)
            elif not path.is_file():
                errors.append(f"{prefix}: asset is not a file: {path}")
                hashes.append(None)
            else:
                try:
                    hashes.append(sha256_file(path))
                except OSError as exc:
                    errors.append(f"{prefix}: cannot hash asset: {exc}")
                    hashes.append(None)
        else:
            hashes.append(None)

    # Patient and reference IDs are repeatable across image records.
    # One acquisition event may also produce multiple image/ROI records.
    # image_id identifies one manifest asset record and must be unique.
    duplicated = frame["image_id"].astype("string").str.strip().duplicated(keep=False)
    if duplicated.any():
        errors.append("Duplicate identity values in image_id")

    valid_hashes = [h for h in hashes if h]
    if len(valid_hashes) != len(set(valid_hashes)):
        errors.append("Duplicate asset SHA-256 detected")

    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "n_rows": int(len(frame)),
        "n_unique_patients": int(frame["patient_id"].astype("string").nunique()),
        "n_unique_assets": int(len(set(valid_hashes))),
        "resolved_paths": [str(p) if p is not None else None for p in resolved_paths],
        "sha256": hashes,
    }
