import pandas as pd
import pytest

from smartbio.experimental_intake import audit_experimental_intake


def valid_row():
    return {
        "patient_id": "P01", "image_id": "I01", "image_path": "img.jpg",
        "source_dataset": "local", "biomarker": "hemoglobin", "target_value": 12.3,
        "target_unit": "g/dL", "target_source": "lab", "reference_method": "CBC",
        "reference_measurement_id": "R01", "reference_type": "laboratory",
        "roi_type": "conjunctiva", "device_model": "Device-A", "illumination": "flash",
        "acquisition_id": "A01", "exposure_us": 10000, "iso": 100,
        "white_balance_mode": "locked", "working_distance_mm": 100,
        "incidence_angle_deg": 0,
    }


def test_missing_quantitative_metadata_fails(tmp_path):
    row = valid_row()
    row["iso"] = None
    frame = pd.DataFrame([row])
    report = audit_experimental_intake(frame, data_root=tmp_path, require_assets=False)
    assert not report["passed"]
    assert any("iso" in e for e in report["errors"])


def test_auto_white_balance_fails(tmp_path):
    row = valid_row()
    row["white_balance_mode"] = "auto"
    report = audit_experimental_intake(pd.DataFrame([row]), data_root=tmp_path, require_assets=False)
    assert not report["passed"]


def test_missing_asset_fails(tmp_path):
    report = audit_experimental_intake(pd.DataFrame([valid_row()]), data_root=tmp_path)
    assert not report["passed"]
    assert any("asset does not exist" in e for e in report["errors"])


def test_repeated_patient_reference_and_acquisition_are_allowed(tmp_path):
    first = valid_row()
    second = valid_row()
    second["image_id"] = "I02"
    frame = pd.DataFrame([first, second])
    report = audit_experimental_intake(frame, data_root=tmp_path, require_assets=False)
    assert report["passed"]


def test_duplicate_image_identity_fails(tmp_path):
    first = valid_row()
    second = valid_row()
    frame = pd.DataFrame([first, second])
    report = audit_experimental_intake(frame, data_root=tmp_path, require_assets=False)
    assert not report["passed"]
    assert any("Duplicate identity values in image_id" in e for e in report["errors"])
