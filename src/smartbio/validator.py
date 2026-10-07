import pandas as pd

REQUIRED = {"patient_id","image_id","image_path","source_dataset","biomarker","target_value","target_unit"}
ALLOWED_BIOMARKERS = {"hemoglobin","bilirubin"}
EXPECTED_UNITS = {"hemoglobin":"g/dL","bilirubin":"mg/dL"}

def validate_canonical(df, *, require_target_provenance=False, require_roi_provenance=False):
    errors, warnings = [], []
    missing = REQUIRED - set(df.columns)
    if missing:
        errors.append(f"Missing canonical columns: {sorted(missing)}")
        return {"valid": False,"errors":errors,"warnings":warnings}
    for c in ["patient_id","image_id","image_path","source_dataset","biomarker","target_unit"]:
        if df[c].isna().any(): errors.append(f"Missing values in {c}.")
        if df[c].astype(str).str.strip().eq("").any(): errors.append(f"Empty values in {c}.")
    target = pd.to_numeric(df["target_value"],errors="coerce")
    if target.isna().any(): errors.append("Missing/non-numeric target_value.")
    if not target.empty and (target < 0).any(): errors.append("Negative target_value.")
    bad = set(df["biomarker"].dropna().unique()) - ALLOWED_BIOMARKERS
    if bad: errors.append(f"Unknown biomarkers: {sorted(bad)}")
    for biomarker, unit in EXPECTED_UNITS.items():
        vals=df.loc[df["biomarker"]==biomarker,"target_unit"].dropna()
        if len(vals) and not set(vals.astype(str)) <= {unit}: errors.append(f"Unexpected unit for {biomarker}; expected {unit}.")
    if "roi_type" in df.columns:
        from .roi import TARGET_ROIS
        for biomarker, group in df.groupby("biomarker"):
            labels=group["roi_type"].dropna().astype(str).str.strip().str.lower()
            bad=set(labels)-TARGET_ROIS.get(str(biomarker).lower(),set())
            if bad: errors.append(f"Invalid ROI labels for {biomarker}: {sorted(bad)}")
    roi_cols=["roi_x0","roi_y0","roi_x1","roi_y1"]
    dimension_cols=["image_width","image_height"]
    if all(c in df.columns for c in roi_cols):
        roi_values=df[roi_cols].apply(pd.to_numeric,errors="coerce")
        if roi_values.isna().any(axis=1).any():
            warnings.append("Some records have incomplete ROI coordinates; feature extraction will fail closed for those records.")
        for c in roi_cols:
            if (roi_values[c].dropna()<0).any(): errors.append(f"Negative ROI coordinate in {c}.")
        if all(c in df.columns for c in dimension_cols):
            dims=df[dimension_cols].apply(pd.to_numeric,errors="coerce")
            if dims.isna().any(axis=1).any():
                warnings.append("Some records lack image dimensions required for ROI geometry validation.")
            from .roi import ROIBox, validate_roi_geometry
            for idx, row in df.iterrows():
                vals=roi_values.loc[idx]
                size=dims.loc[idx]
                if vals.isna().any() or size.isna().any():
                    continue
                try:
                    box=ROIBox(*(int(vals[c]) for c in roi_cols))
                    width,height=int(size["image_width"]),int(size["image_height"])
                    validate_roi_geometry(box,image_width=width,image_height=height)
                except (TypeError,ValueError,OverflowError) as exc:
                    errors.append(f"Invalid ROI geometry at row {idx}: {exc}")
    if require_roi_provenance:
        required_roi = {"roi_type", "roi_x0", "roi_y0", "roi_x1", "roi_y1", "image_width", "image_height"}
        missing_roi = required_roi - set(df.columns)
        if missing_roi:
            errors.append(f"Missing ROI provenance columns: {sorted(missing_roi)}")
        else:
            roi_labels = df["roi_type"].astype("string").str.strip()
            if roi_labels.isna().any() or roi_labels.eq("").any():
                errors.append("Incomplete ROI provenance: roi_type is required for quantitative data.")
            roi_values = df[list(["roi_x0", "roi_y0", "roi_x1", "roi_y1"])].apply(pd.to_numeric, errors="coerce")
            dims = df[["image_width", "image_height"]].apply(pd.to_numeric, errors="coerce")
            if roi_values.isna().any().any() or dims.isna().any().any():
                errors.append("Incomplete ROI provenance: explicit ROI coordinates and image dimensions are required.")

    if require_target_provenance:
        from .target_provenance import validate_target_provenance_frame
        biomarkers=set(df["biomarker"].dropna().astype(str).str.lower())
        units=set(df["target_unit"].dropna().astype(str))
        if len(biomarkers)!=1 or len(units)!=1:
            errors.append("Strict target provenance validation requires one biomarker and one target unit per frame.")
        else:
            p=validate_target_provenance_frame(df,expected_biomarker=next(iter(biomarkers)),expected_unit=next(iter(units)),require_unique_reference_measurements=False)
            if not p["valid"]: errors.extend(p["errors"])
            warnings.extend(p["warnings"])
    return {"valid":not errors,"errors":errors,"warnings":warnings}
