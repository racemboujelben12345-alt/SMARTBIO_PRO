import pandas as pd

from smartbio.sewa_preflight import preflight_sewa


def test_preflight_reports_metadata_without_inference():
    frame = pd.DataFrame([{
        "patient_uuid": "p1",
        "cbc_hgb_g_dl": 9.4,
        "image_conjunctiva": "p1/conj.jpg",
        "camera_meta_conjunctiva": "{}",
    }])
    report = preflight_sewa(frame)

    assert report.rows == 1
    assert report.patients == 1
    assert report.target_cbc_available == 1
    assert "conjunctiva" in report.modalities_present
    assert "working_distance_mm" in report.missing_quantitative_fields
    assert report.passed is False


def test_empty_export_fails_closed():
    report = preflight_sewa(pd.DataFrame())
    assert report.passed is False
    assert report.rows == 0
