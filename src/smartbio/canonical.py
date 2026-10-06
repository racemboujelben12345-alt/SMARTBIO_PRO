from pathlib import Path
import pandas as pd
from .schema import ColumnMapping
from .validator import validate_canonical


def build_canonical(raw, mapping, source_dataset, biomarker, target_unit):
    required_source = [mapping.patient_id, mapping.image_path, mapping.target_value]
    for source in required_source:
        if source not in raw.columns:
            raise KeyError(f"Mapped source column not found: {source}")

    result = pd.DataFrame()
    result["patient_id"] = raw[mapping.patient_id].astype("string").str.strip()
    result["image_path"] = raw[mapping.image_path].astype("string").str.strip()
    result["source_dataset"] = source_dataset
    result["biomarker"] = str(biomarker).strip().lower()
    result["target_value"] = pd.to_numeric(raw[mapping.target_value], errors="coerce")
    result["target_unit"] = str(target_unit).strip()

    if mapping.image_id:
        result["image_id"] = raw[mapping.image_id].astype("string").str.strip()
    else:
        result["image_id"] = [f"{pid}_{Path(path).stem}" for pid, path in zip(result["patient_id"], result["image_path"])]

    for out, source in [("roi_type", mapping.roi_type), ("device_model", mapping.device_model), ("illumination", mapping.illumination)]:
        result[out] = raw[source].astype("string").str.strip() if source else None

    if mapping.acquisition_id:
        result["acquisition_id"] = raw[mapping.acquisition_id].astype("string").str.strip()
    else:
        # Unique fallback per image; patient-only IDs collapse repeated acquisitions.
        result["acquisition_id"] = result["image_id"]

    for col in ("roi_x0", "roi_y0", "roi_x1", "roi_y1", "exposure_us", "iso", "working_distance_mm", "incidence_angle_deg", "bit_depth"):
        source = getattr(mapping, col)
        result[col] = pd.to_numeric(raw[source], errors="coerce") if source else None
    for col in ("white_balance_mode", "image_format", "raw_available"):
        source = getattr(mapping, col)
        result[col] = raw[source].astype("string").str.strip() if source else None

    report = validate_canonical(result)
    if not report["valid"]:
        raise ValueError("Canonical validation failed:\n" + "\n".join(report["errors"]))
    return result
