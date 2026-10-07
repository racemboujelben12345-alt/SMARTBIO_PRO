import pandas as pd

REQUIRED = {"patient_id","image_id","image_path","source_dataset","biomarker","target_value","target_unit"}
ALLOWED_BIOMARKERS = {"hemoglobin","bilirubin"}
EXPECTED_UNITS = {"hemoglobin":"g/dL","bilirubin":"mg/dL"}

def validate_canonical(df, *, require_target_provenance=False):
    errors, warnings = [], []
    missing = REQUIRED - set(df.columns)
    if missing:
        errors.append(f"Missing canonical columns: {sorted(missing)}")
        return {"valid": False, "errors": errors, "warnings": warnings}

    for c in ["patient_id","image_id","image_path","source_dataset","biomarker","target_unit"]:
        if df[c].isna().any(): errors.append(f"Missing values in {c}.")
        if df[c].astype(str).str.strip().eq("").any(): errors.append(f"Empty values in {c}.")

    target = pd.to_numeric(df["target_value"], errors="coerce")
    if target.isna().any(): errors.append("Missing/non-numeric target_value.")
    if not target.empty and (target < 0).any(): errors.append("Negative target_value.")

    bad_biomarkers = set(df["biomarker"].dropna().unique()) - ALLOWED_BIOMARKERS
    if bad_biomarkers: errors.append(f"Unknown biomarkers: {sorted(bad_biomarkers)}")
    for biomarker, unit in EXPECTED_UNITS.items():
        bad = df.loc[df["biomarker"] == biomarker, "target_unit"].dropna()
        if len(bad) and not set(bad.astype(str)) <= {unit}: errors.append(f"Unexpected unit for {biomarker}; expected {unit}.")

    if "roi_type" in df.columns:
        from .roi import TARGET_ROIS
        for biomarker, group in df.groupby("biomarker"):
            labels = group["roi_type"].dropna().astype(str).str.strip().str.lower()
            bad = set(labels) - TARGET_ROIS.get(str(biomarker).lower(), set())
            if bad: errors.append(f"Invalid ROI labels for {biomarker}: {sorted(bad)}")

    roi_cols = ["roi_x0","roi_y0","roi_x1","roi_y1"]
    if all(c in df.columns for c in roi_cols):
        if df[roi_cols].notna().any(axis=1).any() and df[roi_cols].isna().any(axis=1).any():
            warnings.append("Some records have incomplete ROI coordinates; feature extraction will fail closed for those records.")
        for c in roi_cols:
            vals = pd.to_numeric(df[c], errors="coerce").dropna()
            if (vals < 0).any(): errors.append(f"Negative ROI coordinate in {c}.")

    if require_target_provenance:
        from .target_provenance import validate_target_provenance_frame
        provenance = validate_target_provenance_frame(
            df, expected_biomarker=next(iter(set(df["biomarker"].dropna().astype(str).str.lower())), None),
            expected_unit=next(iter(set(df["target_unit"].dropna().astype(str))), None),
            require_unique_reference_measurements=False,
        )
        if not provenance["valid"]: errors.extend(provenance["errors"])
        warnings.extend(provenance["warnings"])

    return {"valid": not errors, "errors": errors, "warnings": warnings}
