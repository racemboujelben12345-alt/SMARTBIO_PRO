import pandas as pd
import pytest

from smartbio.fingertip_preflight import preflight_fingertip


def valid_manifest():
    return pd.DataFrame([
        {
            "patient_id": "P001",
            "video_path": "videos/P001.mp4",
            "hemoglobin_gdl": 10.2,
            "reference_measurement_id": "CBC-P001",
        },
        {
            "patient_id": "P002",
            "video_path": "videos/P002.mp4",
            "hemoglobin_gdl": 12.1,
            "reference_measurement_id": "CBC-P002",
        },
    ])


def test_fingertip_preflight_is_fail_closed_without_acquisition_metadata():
    report = preflight_fingertip(valid_manifest())

    assert report.rows == 2
    assert report.patients == 2
    assert report.target_available == 2
    assert report.provenance_complete == 2
    assert not report.passed
    assert report.missing_quantitative_fields


def test_fingertip_preflight_rejects_missing_manifest_fields():
    frame = valid_manifest().drop(columns=["reference_measurement_id"])

    report = preflight_fingertip(frame)

    assert not report.passed
    assert any("reference_measurement_id" in error for error in report.errors)


def test_fingertip_preflight_rejects_missing_target():
    frame = valid_manifest()
    frame["hemoglobin_gdl"] = frame["hemoglobin_gdl"].astype(object)
    frame.loc[0, "hemoglobin_gdl"] = "not-a-number"

    report = preflight_fingertip(frame)

    assert not report.passed
    assert any("hemoglobin_gdl" in error for error in report.errors)


def test_fingertip_preflight_empty():
    report = preflight_fingertip(pd.DataFrame())

    assert report.rows == 0
    assert not report.passed
    assert report.errors
