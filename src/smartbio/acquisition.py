"""Acquisition-level controls for quantitative smartphone imaging."""
from __future__ import annotations

import numpy as np

REQUIRED_QUANTITATIVE_FIELDS = {
    "device_model", "exposure_us", "iso", "white_balance_mode",
    "working_distance_mm", "incidence_angle_deg", "illumination",
}


def acquisition_gate(row, *, quantitative=True):
    errors, warnings = [], []
    if quantitative:
        for key in REQUIRED_QUANTITATIVE_FIELDS:
            if key not in row or row[key] in (None, "", np.nan):
                errors.append(f"Missing quantitative acquisition field: {key}")
        if str(row.get("white_balance_mode", "")).lower() in {"auto", "awb"}:
            errors.append("Auto white balance must be disabled/locked.")
    if row.get("illumination") not in {"flash", "ambient", "controlled_led", "reference"}:
        warnings.append("Unknown illumination condition; optical comparability is not established.")
    return {"valid": not errors, "errors": errors, "warnings": warnings}
