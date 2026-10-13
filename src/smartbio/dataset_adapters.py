"""Dataset adapters for SmartBio PRO quantitative ingestion.

Adapters normalize dataset-specific metadata into the canonical schema without
inventing acquisition or target provenance. Missing or unverified state remains
explicit and therefore fails closed at the quantitative gate.
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

SEWA_SOURCE_MODALITIES = {
    "conjunctiva": "Anemia_Conjunctiva",
    "fingernails_open": "Anemia_Fingernails_Open",
    "fingernails_closed": "Anemia_Fingernails_Closed",
    "tongue": "Anemia_Tongue",
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


def _sewa_camera_value(
    source_row: Mapping[str, Any],
    modality: str,
    payload: Any,
    *,
    payload_keys: tuple[str, ...],
    flat_suffixes: tuple[str, ...],
) -> Any:
    """Read either legacy JSON camera metadata or published flattened SEWA fields."""
    value = _camera_value(payload, *payload_keys)
    if value is not None:
        return value

    source_modality = SEWA_SOURCE_MODALITIES[modality]
    return _first(
        source_row,
        *(f"cam_{source_modality}_{suffix}" for suffix in flat_suffixes),
    )


def _numeric(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if pd.notna(out) else None


def _illumination_from_flash_mode(value: Any) -> str | None:
    """Map only explicit, recognized flash states; unknown values stay unknown.

    Android Camera2 FLASH_MODE values are OFF=0, SINGLE=1, TORCH=2. Common
    textual representations are accepted too. This does not infer illumination
    from the mere presence of a metadata field.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return "flash" if value else "ambient"

    if isinstance(value, (int, float)):
        numeric = _numeric(value)
        if numeric == 0:
            return "ambient"
        if numeric in {1, 2}:
            return "flash"
        return None

    text = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    if text in {"0", "off", "false", "none", "flash_mode_off", "off_mode"}:
        return "ambient"
    if text in {
        "1", "2", "on", "true", "single", "torch", "flash",
        "flash_mode_single", "flash_mode_torch",
    }:
        return "flash"
    if text in {"ambient", "no_flash", "noflash", "natural_light"}:
        return "ambient"
    return None


def _explicit_illumination(value: Any) -> str | None:
    """Normalize a supplied illumination label without guessing missing values."""
    if value is None or pd.isna(value):
        return None
    text = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "flash": "flash",
        "ambient": "ambient",
        "no_flash": "ambient",
        "noflash": "ambient",
        "natural_light": "ambient",
        "controlled_led": "controlled_led",
        "reference": "reference",
    }
    return aliases.get(text)


def adapt_sewa_metadata(
    frame: pd.DataFrame,
    *,
    modalities: tuple[str, ...] = tuple(SEWA_MODALITIES),
) -> pd.DataFrame:
    """Expand one-row-per-participant SEWA metadata into canonical image rows.

    Supports both the published flattened SEWA metadata columns and the earlier
    JSON-style camera metadata representation. CBC/venous Hb targets are labelled
    as laboratory references; only explicitly survey-named fallback fields are
    labelled self-reported. Missing acquisition state remains missing.
    """
    if frame.empty:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)

    records: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        source_row = row.to_dict()
        patient_value = _first(source_row, "participant_uuid", "patient_uuid", "Patient UUID")
        if patient_value is None or not str(patient_value).strip():
            raise ValueError("SEWA metadata requires a non-empty participant/patient UUID.")
        patient = str(patient_value).strip()

        cbc_hb = _first(source_row, "cbc_hgb_gdl", "cbc_hgb_g_dl")
        venous_hb = _first(source_row, "haemoglobin_gdl", "hemoglobin_gdl", "haemoglobin_g_dl")
        if cbc_hb is not None:
            hb = cbc_hb
            target_source = "SEWA Rural CBC"
            reference_method = "complete_blood_count"
            reference_id = f"{patient}:cbc_hgb"
            reference_type = "laboratory"
        elif venous_hb is not None:
            hb = venous_hb
            target_source = "SEWA Rural venous haemoglobin"
            reference_method = "venous_blood_draw"
            reference_id = f"{patient}:venous_hgb"
            reference_type = "laboratory"
        else:
            hb = _first(source_row, "survey_haemoglobin", "survey_hemoglobin", "survey_hgb_gdl")
            target_source = "SEWA Rural self-reported survey haemoglobin"
            reference_method = "survey_record"
            reference_id = f"{patient}:survey_hgb"
            reference_type = "self_reported"

        target = _numeric(hb)
        if target is None:
            continue

        device = _first(source_row, "device_model", "survey_device_modal")
        for modality in modalities:
            if modality not in SEWA_MODALITIES:
                raise ValueError(f"Unsupported SEWA modality: {modality!r}.")
            image = _image_path(source_row.get(SEWA_MODALITIES[modality]))
            if not image:
                continue

            camera = source_row.get(SEWA_CAMERA_COLUMNS[modality])
            exposure_ns = _sewa_camera_value(
                source_row, modality, camera,
                payload_keys=("android.sensor.exposureTime", "exposureTime"),
                flat_suffixes=("exposure_ns", "exposureTime"),
            )
            iso = _sewa_camera_value(
                source_row, modality, camera,
                payload_keys=("android.sensor.sensitivity", "sensitivity"),
                flat_suffixes=("iso", "sensitivity"),
            )
            awb_mode = _sewa_camera_value(
                source_row, modality, camera,
                payload_keys=("android.control.awbMode", "awb_mode", "awbMode"),
                flat_suffixes=("awb_mode", "awbMode"),
            )
            flash_mode = _sewa_camera_value(
                source_row, modality, camera,
                payload_keys=("android.flash.mode", "flash_mode", "flashMode"),
                flat_suffixes=("flash_mode", "flashMode"),
            )

            exposure_value = _numeric(exposure_ns)
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
                "reference_type": reference_type,
                "target_time_delta_min": None,
                "roi_type": "conjunctiva" if modality == "conjunctiva" else "nailbed" if modality.startswith("fingernails") else "tongue",
                "device_model": device,
                "illumination": _illumination_from_flash_mode(flash_mode),
                "acquisition_id": f"{patient}:{modality}",
                "exposure_us": None if exposure_value is None else exposure_value / 1000.0,
                "iso": _numeric(iso),
                "white_balance_mode": awb_mode,
                "working_distance_mm": None,
                "incidence_angle_deg": None,
                "image_format": Path(image).suffix.lower().lstrip(".") or None,
                "bit_depth": None,
                "raw_available": False,
            })

    return pd.DataFrame(records, columns=CANONICAL_COLUMNS)


def build_fingertip_manifest(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize an explicit Fingertip Video manifest.

    Patient identity, video path, target value and reference measurement ID are
    required. Reference method/type and illumination are copied only when
    explicitly supplied; absent values remain marked unknown rather than being
    inferred from the dataset name, target column, or filename.
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
        patient_value = row["patient_id"]
        video_value = row["video_path"]
        reference_value = row["reference_measurement_id"]
        patient = "" if pd.isna(patient_value) else str(patient_value).strip()
        video = "" if pd.isna(video_value) else str(video_value).strip()
        target = _numeric(row["hemoglobin_gdl"])
        reference_id = "" if pd.isna(reference_value) else str(reference_value).strip()
        if not patient or not video or target is None or not reference_id:
            raise ValueError("Fingertip manifest contains incomplete provenance.")

        supplied_target_source = _first(row.to_dict(), "target_source")
        supplied_reference_method = _first(row.to_dict(), "reference_method")
        supplied_reference_type = _first(row.to_dict(), "reference_type")
        supplied_illumination = _first(row.to_dict(), "illumination")

        records.append({
            "patient_id": patient,
            "image_id": f"{patient}:{Path(video).stem}",
            "image_path": video,
            "source_dataset": "Fingertip_Video_Dataset",
            "biomarker": "hemoglobin",
            "target_value": target,
            "target_unit": "g/dL",
            "target_source": supplied_target_source or "unverified supplied target",
            "reference_method": supplied_reference_method or "unspecified",
            "reference_measurement_id": reference_id,
            "reference_type": supplied_reference_type or "unknown",
            "target_time_delta_min": None,
            "roi_type": "fingertip",
            "device_model": _first(row.to_dict(), "device_model"),
            "illumination": _explicit_illumination(supplied_illumination),
            "acquisition_id": f"{patient}:{Path(video).stem}",
            "exposure_us": _numeric(_first(row.to_dict(), "exposure_us")),
            "iso": _numeric(_first(row.to_dict(), "iso")),
            "white_balance_mode": _first(row.to_dict(), "white_balance_mode"),
            "working_distance_mm": _numeric(_first(row.to_dict(), "working_distance_mm")),
            "incidence_angle_deg": _numeric(_first(row.to_dict(), "incidence_angle_deg")),
            "image_format": Path(video).suffix.lower().lstrip(".") or None,
            "bit_depth": None,
            "raw_available": False,
        })

    return pd.DataFrame(records, columns=CANONICAL_COLUMNS)
