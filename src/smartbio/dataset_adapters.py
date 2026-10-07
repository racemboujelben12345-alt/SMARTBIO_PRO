"""Dataset adapters for SmartBio PRO quantitative ingestion.

Adapters normalize dataset-specific metadata into the canonical schema without
inventing acquisition or target provenance. Missing quantitative state remains
missing and therefore fails closed at the quantitative gate.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from .schema import CANONICAL_COLUMNS


SEWA_MODALITIES = {
    "conjunctiva": "image_conjunctiva",
    "fingernails_open": "image_fingernails_open",
    "fingernails_closed": "image_fingernails_closed",
    "tongue": "image_tongue",
}

SEWA_CAMERA_COLUMNS = {
    "conjunctiva": "camera_meta_conjunctiva",
    "fingernails_open": "camera_meta_fingernails_open",
    "fingernails_closed": "camera_meta_fingernails_closed",
    "tongue": "camera_meta_tongue",
}


def _first(row: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in row and pd.notna(row[name]) and str(row[name]).strip():
            return row[name]
    return None


def _image_path(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        path = value.get("path")
        return None if path is None else str(path)
    text = str(value).strip()
    return text or None


def _camera_value(payload: Any, *keys: str) -> Any:
    if payload is None or (isinstance(payload, float) and pd.isna(payload)):
        return None
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            return None
    if not isinstance(payload, Mapping):
        return None
    for key in keys:
        value = payload.get(key)
        if isinstance(value, Mapping):
            value = value.get("result", value.get("request"))
        if value is not None and str(value).strip() not in {"", "None", "null"}:
            return value
    return None


def _numeric(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if pd.notna(out) else None


def adapt_sewa_metadata(
    frame: pd.DataFrame,
    *,
    modalities: tuple[str, ...] = tuple(SEWA_MODALITIES),
) -> pd.DataFrame:
    """Expand one-row-per-participant SEWA metadata into canonical image rows.

    The adapter uses venous CBC Hb as the laboratory reference when available,
    falling back to survey Hb only as an explicitly labelled alternative source.
    It never fabricates geometry, white-balance lock state, or other acquisition
    metadata that are not present in the source.
    """
    required = {"patient_uuid"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"SEWA metadata missing columns: {sorted(missing)}")

    records: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        source_row = row.to_dict()
        patient = str(row["patient_uuid"]).strip()
        if not patient:
            raise ValueError("SEWA patient_uuid must be non-empty.")

        hb = _first(source_row, "cbc_hgb_g_dl", "haemoglobin_gdl", "survey_haemoglobin")
        target = _numeric(hb)
        if target is None:
            continue

        if _first(source_row, "cbc_hgb_g_dl") is not None:
            target_source = "SEWA Rural CBC"
            reference_method = "complete_blood_count"
            reference_id = f"{patient}:cbc_hgb"
        else:
            target_source = "SEWA Rural survey haemoglobin"
            reference_method = "survey_record"
            reference_id = f"{patient}:survey_hgb"

        device = _first(source_row, "survey_device_modal", "device_model")
        for modality in modalities:
            if modality not in SEWA_MODALITIES:
                raise ValueError(f"Unsupported SEWA modality: {modality!r}.")
            image = _image_path(source_row.get(SEWA_MODALITIES[modality]))
            if not image:
                continue

            camera = source_row.get(SEWA_CAMERA_COLUMNS[modality])
            exposure_ns = _camera_value(camera, "android.sensor.exposureTime", "exposureTime")
            iso = _camera_value(camera, "android.sensor.sensitivity", "sensitivity")
            awb_mode = _camera_value(
                camera,
                "android.control.awbMode",
                "awb_mode",
                "awbMode",
            )
            flash_mode = _camera_value(
                camera,
                "android.flash.mode",
                "flash_mode",
                "flashMode",
            )

            records.append({
                "patient_id": patient,
                "image_id": f"{patient}:{modality}",
                "image_path": image,
                "source_dataset": "SEWA_Rural_Anemia_Dataset",
                "biomarker": "hemoglobin",
                "target_value": target,
                "target_unit": "g/dL",
                "target_source": target_source,
                "reference_method": reference_method,
                "reference_measurement_id": reference_id,
                "reference_type": "laboratory" if reference_method == "complete_blood_count" else "validated_reference",
                "target_time_delta_min": None,
                "roi_type": "conjunctiva" if modality == "conjunctiva" else "nailbed" if modality.startswith("fingernails") else "tongue",
                "device_model": device,
                "illumination": "flash" if flash_mode is not None else None,
                "acquisition_id": f"{patient}:{modality}",
                "exposure_us": None if exposure_ns is None else _numeric(exposure_ns) / 1000.0,
                "iso": _numeric(iso),
                "white_balance_mode": awb_mode,
                "working_distance_mm": None,
                "incidence_angle_deg": None,
                "image_format": Path(image).suffix.lower().lstrip(".") or None,
                "bit_depth": None,
                "raw_available": False,
            })

    result = pd.DataFrame(records, columns=CANONICAL_COLUMNS)
    return result


def build_fingertip_manifest(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize an explicit Fingertip Video manifest.

    Because the public dataset does not publish a canonical machine-readable
    acquisition schema alongside the paper, filenames are never interpreted as
    patient IDs or Hb labels. The caller must provide explicit columns.
    """
    required = {
        "patient_id",
        "video_path",
        "hemoglobin_gdl",
        "reference_measurement_id",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(
            "Fingertip manifest requires explicit columns: "
            + ", ".join(sorted(missing))
        )

    records: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        patient = str(row["patient_id"]).strip()
        video = str(row["video_path"]).strip()
        target = _numeric(row["hemoglobin_gdl"])
        reference_id = str(row["reference_measurement_id"]).strip()
        if not patient or not video or target is None or not reference_id:
            raise ValueError("Fingertip manifest contains incomplete provenance.")

        records.append({
            "patient_id": patient,
            "image_id": f"{patient}:{Path(video).stem}",
            "image_path": video,
            "source_dataset": "Fingertip_Video_Dataset",
            "biomarker": "hemoglobin",
            "target_value": target,
            "target_unit": "g/dL",
            "target_source": "laboratory CBC",
            "reference_method": "complete_blood_count",
            "reference_measurement_id": reference_id,
            "reference_type": "laboratory",
            "target_time_delta_min": None,
            "roi_type": "fingertip",
            "device_model": None,
            "illumination": "flash",
            "acquisition_id": f"{patient}:{Path(video).stem}",
            "exposure_us": None,
            "iso": None,
            "white_balance_mode": None,
            "working_distance_mm": None,
            "incidence_angle_deg": None,
            "image_format": Path(video).suffix.lower().lstrip(".") or None,
            "bit_depth": None,
            "raw_available": False,
        })

    return pd.DataFrame(records, columns=CANONICAL_COLUMNS)
