import pandas as pd
import pytest

from smartbio.dataset_adapters import adapt_sewa_metadata, build_fingertip_manifest


def test_sewa_adapter_expands_modalities_and_preserves_missing_physics():
    frame = pd.DataFrame([{
        "patient_uuid": "p1",
        "cbc_hgb_g_dl": "9.4",
        "survey_device_modal": "Samsung S24",
        "image_conjunctiva": {"path": "p1/conj.jpeg"},
        "camera_meta_conjunctiva": '{"android.sensor.exposureTime": {"result": "8000000"}, "android.sensor.sensitivity": {"result": "100"}}',
    }])
    out = adapt_sewa_metadata(frame)
    assert len(out) == 1
    assert out.iloc[0]["target_value"] == pytest.approx(9.4)
    assert out.iloc[0]["exposure_us"] == pytest.approx(8000)
    assert out.iloc[0]["iso"] == pytest.approx(100)
    assert pd.isna(out.iloc[0]["working_distance_mm"])
    assert pd.isna(out.iloc[0]["incidence_angle_deg"])


def test_sewa_requires_patient_identity():
    with pytest.raises(ValueError):
        adapt_sewa_metadata(pd.DataFrame([{"cbc_hgb_g_dl": 10}]))


def test_fingertip_requires_explicit_manifest():
    with pytest.raises(ValueError):
        build_fingertip_manifest(pd.DataFrame([{"video_path": "x.mp4"}]))


def test_fingertip_never_infers_patient_from_filename():
    frame = pd.DataFrame([{
        "patient_id": "P01",
        "video_path": "patient_99.mp4",
        "hemoglobin_gdl": 7.2,
        "reference_measurement_id": "cbc-P01",
    }])
    out = build_fingertip_manifest(frame)
    assert out.iloc[0]["patient_id"] == "P01"
    assert out.iloc[0]["reference_measurement_id"] == "cbc-P01"
