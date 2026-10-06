from pathlib import Path
import hashlib
import pandas as pd
import numpy as np
import cv2
from PIL import Image

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def inventory(df):
    rows = []
    for _, r in df.iterrows():
        p = Path(r["image_path"])
        item = r.to_dict()
        item.update({
            "exists": p.exists(),
            "readable": False,
            "sha256": None,
            "width": None,
            "height": None,
        })
        if p.exists():
            try:
                with Image.open(p) as im:
                    item["width"], item["height"] = im.size
                    im.verify()
                item["readable"] = True
                item["sha256"] = sha256(p)
            except Exception:
                pass
        rows.append(item)
    return pd.DataFrame(rows)

def exact_duplicate_groups(inv):
    x = inv[inv["sha256"].notna()].copy()
    counts = x["sha256"].value_counts()
    return x[x["sha256"].isin(counts[counts > 1].index)].sort_values("sha256")

def quality(path, *, min_brightness=15.0, max_brightness=240.0, min_contrast=5.0, min_blur=20.0, max_saturation_fraction=0.25):
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"Unreadable image: {path}")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    brightness = float(gray.mean())
    contrast = float(gray.std())
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    dark_fraction = float(np.mean(gray <= 10))
    bright_fraction = float(np.mean(gray >= 245))
    saturation_fraction = float(np.mean(hsv[:,:,1] >= 250))
    return {
        "brightness": brightness,
        "contrast": contrast,
        "blur": blur,
        "dark_fraction": dark_fraction,
        "bright_fraction": bright_fraction,
        "saturation_fraction": saturation_fraction,
        "quality_flag_brightness": bool(min_brightness <= brightness <= max_brightness),
        "quality_flag_contrast": bool(contrast >= min_contrast),
        "quality_flag_blur": bool(blur >= min_blur),
        "quality_flag_saturation": bool(saturation_fraction <= max_saturation_fraction),
    }

def quality_audit(inv):
    rows = []
    for _, r in inv.iterrows():
        item = {"image_path": r["image_path"]}
        try:
            item.update(quality(r["image_path"]))
            item["quality_error"] = None
        except Exception as e:
            item["quality_error"] = str(e)
        rows.append(item)
    return pd.DataFrame(rows)

def missingness(df):
    return (
        df.isna().mean()
        .sort_values(ascending=False)
        .rename("missing_fraction")
        .reset_index()
        .rename(columns={"index":"column"})
    )

def target_summary(df):
    return (
        df.groupby(["biomarker","target_unit"])["target_value"]
        .agg(["count","min","max","mean","median","std"])
        .reset_index()
    )

def leakage_report(df):
    # Within one canonical dataset: patient must map consistently.
    counts = df.groupby("patient_id").size()
    duplicate_patients = int((counts > 1).sum())
    return {
        "patients": int(df["patient_id"].nunique()),
        "records": int(len(df)),
        "patients_with_multiple_records": duplicate_patients,
    }

def split_leakage(train, val, test):
    a, b, c = map(lambda x: set(x["patient_id"]), (train,val,test))
    return {
        "train_val_overlap": len(a & b),
        "train_test_overlap": len(a & c),
        "val_test_overlap": len(b & c),
        "passed": not (a & b or a & c or b & c),
    }

def audit_gate(inv, quality_df, exact_dups, split_report=None):
    checks = {
        "all_images_exist": bool(inv["exists"].all()) if len(inv) else False,
        "all_images_readable": bool(inv["readable"].all()) if len(inv) else False,
        "exact_duplicate_free": bool(len(exact_dups) == 0),
        "quality_extraction_complete": bool(
            quality_df["quality_error"].isna().all()
        ) if len(quality_df) else False,
    }
    quality_flags = [
        "quality_flag_brightness", "quality_flag_contrast",
        "quality_flag_blur", "quality_flag_saturation"
    ]
    if len(quality_df) and all(c in quality_df.columns for c in quality_flags):
        checks["optical_quality_gate"] = bool(quality_df[quality_flags].all(axis=1).all())
    else:
        checks["optical_quality_gate"] = False
    if split_report is not None:
        checks["patient_split_clean"] = bool(split_report["passed"])
    return checks, all(checks.values())
