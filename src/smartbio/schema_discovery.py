import re
import pandas as pd

CANDIDATES = {
    "patient_id": [
        "patient_id","patientid","participant_id","participantid",
        "subject_id","subjectid","subject","participant"
    ],
    "image_path": [
        "image_path","imagepath","image_file","image_filename",
        "filepath","file_path","filename","image"
    ],
    "target_value": [
        "hb","hemoglobin","hemoglobin_value","hgb",
        "tsb","bilirubin","total_serum_bilirubin"
    ],
    "device_model": [
        "device","device_model","smartphone","phone_model","camera_model"
    ],
    "illumination": [
        "illumination","light_intensity","ambient_light","lighting","light"
    ],
}

def normalize(name):
    return re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower()).strip("_")

def normalized_columns(df):
    return {normalize(c): c for c in df.columns}

def find_candidates(df):
    cols = normalized_columns(df)
    return {
        logical: [cols[c] for c in candidates if c in cols]
        for logical, candidates in CANDIDATES.items()
    }

def discovery_report(df):
    return {
        "rows": len(df),
        "columns": list(df.columns),
        "candidates": find_candidates(df),
    }

def print_schema_report(df):
    r = discovery_report(df)
    print("=== SMARTBIO SCHEMA DISCOVERY ===")
    print(f"Rows: {r['rows']}")
    print(f"Columns: {len(r['columns'])}")
    for c in r["columns"]:
        print(f"  - {c}")
    print("\nCandidate mappings:")
    for k, v in r["candidates"].items():
        print(f"  {k}: {v or 'NOT FOUND'}")
    return r
