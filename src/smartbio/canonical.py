from pathlib import Path
import pandas as pd
from .schema import ColumnMapping
from .validator import validate_canonical

def _parse_bool_series(values, name):
    mapping = {"true": True, "false": False, "1": True, "0": False, "yes": True, "no": False, "y": True, "n": False}
    out = []
    for value in values:
        if pd.isna(value):
            out.append(False)
            continue
        key = str(value).strip().lower()
        if key not in mapping:
            raise ValueError(f"Invalid boolean value for {name}: {value!r}")
        out.append(mapping[key])
    return pd.Series(out, index=values.index, dtype="boolean")

def _mapped_text(raw, source):
    if source:
        return raw[source].astype("string").str.strip()
    return pd.Series([pd.NA] * len(raw), index=raw.index, dtype="string")

def build_canonical(raw, mapping, source_dataset, biomarker, target_unit, *, require_target_provenance=False, require_roi_provenance=False):
    required_source = [mapping.patient_id, mapping.image_path, mapping.target_value]
    for source in required_source:
        if source not in raw.columns:
            raise KeyError(f"Mapped source column not found: {source}")
    result = pd.DataFrame(index=raw.index)
    result["patient_id"] = raw[mapping.patient_id].astype("string").str.strip()
    result["image_path"] = raw[mapping.image_path].astype("string").str.strip()
    result["source_dataset"] = str(source_dataset).strip()
    result["biomarker"] = str(biomarker).strip().lower()
    result["target_value"] = pd.to_numeric(raw[mapping.target_value], errors="coerce")
    result["target_unit"] = str(target_unit).strip()
    result["image_id"] = raw[mapping.image_id].astype("string").str.strip() if mapping.image_id else [f"{pid}_{Path(path).stem}" for pid, path in zip(result["patient_id"], result["image_path"])]
    for out in ("target_source","reference_method","reference_measurement_id","reference_type"):
        result[out] = _mapped_text(raw, getattr(mapping, out))
    result["target_time_delta_min"] = pd.to_numeric(raw[mapping.target_time_delta_min], errors="coerce") if mapping.target_time_delta_min else pd.Series([pd.NA] * len(raw), index=raw.index, dtype="Float64")
    for out, source in [("roi_type",mapping.roi_type),("device_model",mapping.device_model),("illumination",mapping.illumination)]:
        result[out] = _mapped_text(raw, source)
    result["acquisition_id"] = raw[mapping.acquisition_id].astype("string").str.strip() if mapping.acquisition_id else result["image_id"]
    for col in ("roi_x0","roi_y0","roi_x1","roi_y1","image_width","image_height","exposure_us","iso","working_distance_mm","incidence_angle_deg","bit_depth"):
        source = getattr(mapping,col)
        result[col] = pd.to_numeric(raw[source],errors="coerce") if source else None
    for col in ("white_balance_mode","image_format"):
        result[col] = _mapped_text(raw,getattr(mapping,col))
    result["raw_available"] = _parse_bool_series(raw[mapping.raw_available],"raw_available") if mapping.raw_available else False
    report = validate_canonical(result, require_target_provenance=require_target_provenance, require_roi_provenance=require_roi_provenance)
    if not report["valid"]:
        raise ValueError("Canonical validation failed:\n" + "\n".join(report["errors"]))
    return result
