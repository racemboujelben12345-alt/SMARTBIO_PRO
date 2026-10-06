from pathlib import Path
from .biophysics import srgb_to_linear, chromaticity
import cv2
import numpy as np
import pandas as pd


def load_rgb(path):
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Cannot read image: {path}")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def center_roi(image, fraction=0.60):
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0,1]")
    h, w = image.shape[:2]
    rh, rw = max(1, int(h*fraction)), max(1, int(w*fraction))
    y, x = (h-rh)//2, (w-rw)//2
    return image[y:y+rh, x:x+rw]


def roi_from_metadata(image, row):
    """Use an explicit ROI box when present; center ROI is legacy/demo only."""
    keys = ("roi_x0", "roi_y0", "roi_x1", "roi_y1")
    if all(k in row.index and pd.notna(row[k]) for k in keys):
        vals = [int(row[k]) for k in keys]
        x0, y0, x1, y1 = vals
        h, w = image.shape[:2]
        if not (0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h):
            raise ValueError("Explicit ROI box is outside image bounds.")
        return image[y0:y1, x0:x1].copy()
    if row.get("roi_type") not in (None, "", np.nan):
        # Anatomical label without coordinates must not silently become a center ROI.
        if pd.notna(row.get("roi_type")):
            raise ValueError("roi_type is specified but ROI coordinates are missing; refusing to use a center ROI.")
    raise ValueError("Explicit ROI coordinates are required for scientific feature extraction.")


def robust_stats(x, prefix):
    x = np.asarray(x, dtype=np.float32).ravel()
    if x.size == 0 or not np.isfinite(x).all():
        raise ValueError("ROI contains no finite pixels.")
    return {
        f"{prefix}_mean": float(np.mean(x)),
        f"{prefix}_std": float(np.std(x)),
        f"{prefix}_median": float(np.median(x)),
        f"{prefix}_p05": float(np.percentile(x,5)),
        f"{prefix}_p25": float(np.percentile(x,25)),
        f"{prefix}_p75": float(np.percentile(x,75)),
        f"{prefix}_p95": float(np.percentile(x,95)),
    }


def extract(path, roi=None, roi_fraction=0.60, *, allow_demo_center_roi=False):
    image = load_rgb(path)
    if roi is None:
        if not allow_demo_center_roi:
            raise ValueError("Explicit anatomical ROI is required; center ROI is demo-only and must be explicitly enabled.")
        rgb = center_roi(image, roi_fraction)
    else:
        rgb = roi
    if rgb.size == 0:
        raise ValueError("ROI is empty.")
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    channels = {
        "r":rgb[:,:,0], "g":rgb[:,:,1], "b":rgb[:,:,2],
        "h":hsv[:,:,0], "s":hsv[:,:,1], "v":hsv[:,:,2],
        "l":lab[:,:,0], "a":lab[:,:,1], "b_lab":lab[:,:,2],
    }
    out = {}
    for k, v in channels.items():
        out.update(robust_stats(v, k))
    # Use linearized channels for ratio/chromaticity features; do not treat sRGB codes as irradiance.
    linear = srgb_to_linear(rgb)
    r,g,b = [linear[:,:,i].astype(np.float32) for i in range(3)]
    eps = 1e-6
    total = r+g+b+eps
    out.update({
        "r_over_g": float(np.mean(r/(g+eps))),
        "r_over_b": float(np.mean(r/(b+eps))),
        "g_over_b": float(np.mean(g/(b+eps))),
        "r_chromaticity": float(np.mean(r/total)),
        "g_chromaticity": float(np.mean(g/total)),
        "b_chromaticity": float(np.mean(b/total)),
        "linear_mean_intensity": float(np.mean(linear)),
        "linear_saturation_fraction": float(np.mean(np.any((rgb <= 1) | (rgb >= 254), axis=-1))),
    })
    return out


def extract_dataset(metadata_csv, output_csv, *, require_explicit_roi=True):
    df = pd.read_csv(metadata_csv)
    if "image_path" not in df:
        raise ValueError("image_path is required.")
    rows = []
    for _, row in df.iterrows():
        item = row.to_dict()
        try:
            image = load_rgb(row["image_path"])
            if require_explicit_roi:
                roi = roi_from_metadata(image, row)
                item.update(extract(row["image_path"], roi=roi))
            else:
                item.update(extract(row["image_path"], allow_demo_center_roi=True))
            item["feature_error"] = None
        except Exception as exc:
            item["feature_error"] = str(exc)
        rows.append(item)
    out = pd.DataFrame(rows)
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_csv, index=False)
    return out
