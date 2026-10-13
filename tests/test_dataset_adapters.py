import pandas as pd
import pytest

from smartbio.dataset_adapters import (
    adapt_sewa_metadata,
    build_fingertip_manifest,
)
from smartbio.target_provenance import validate_target_provenance


def _sewa_row(*, target_fields=None, camera_meta=None):
    row = {
        "patient_uuid": "p1",
        "cbc_hgb_g_dl": "9.4",
        "survey_device_modal": "Samsung S24",
        "image_conjunctiva": {"path": "p1/conj.jpeg"},
    }
    if target_fields:
        row.update(target_fields)
    if camera_meta is not None:
        row["camera_meta_conjunctiva"] = camera_meta
    return row


def test_sewa_adapter_expands_modalities_and_preserves_missing_physics():
    frame = pd.DataFrame([_sewa_row(camera_meta={
        "android.sensor.exposureTime": {"result": "8000000"},
        "android.sensor.sensitivity": {"result": "100"},
    })])
    out = adapt_sewa_metadata(frame)
    assert len(out) == 1
    assert out.iloc[0]["target_value"] == pytest.approx(9.4)
    assert out.iloc[0]["reference_type"] == "laboratory"
    assert out.iloc[0]["exposure_us"] == pytest.approx(8000)
    assert out.iloc[0]["iso"] == pytest.approx(100)
    assert pd.isna(out.iloc[0]["working_distance_mm"])
    assert pd.isna(out.iloc[0]["incidence_angle_deg"])
    assert pd.isna(out.iloc[0]["illumination"])


def test_sewa_adapter_supports_published_flattened_schema():
    frame = pd.DataFrame([{
        "participant_uuid": "participant-001",
        "haemoglobin_gdl": 10.1,
        "device_model": "Samsung Galaxy S24",
        "image_conjunctiva": "participants/participant-001/conj.jpeg",
        "cam_Anemia_Conjunctiva_exposure_ns": 9_995_000,
        "cam_Anemia_Conjunctiva_iso": 34,
        "cam_Anemia_Conjunctiva_awb_mode": "OFF",
        "cam_Anemia_Conjunctiva_flash_mode": 0,
    }])
    out = adapt_sewa_metadata(frame)
    assert len(out) == 1
    row = out.iloc[0]
    assert row["patient_id"] == "participant-001"
    assert row["target_value"] == pytest.approx(10.1)
    assert row["target_source"] == "SEWA Rural venous haemoglobin"
    assert row["reference_type"] == "laboratory"
    assert row["reference_method"] == "venous_blood_draw"
    assert row["exposure_us"] == pytest.approx(9995)
    assert row["iso"] == pytest.approx(34)
    assert row["illumination"] == "ambient"
    assert row["device_model"] == "Samsung Galaxy S24"


def test_sewa_cbc_target_takes_precedence_over_venous_hb_alias():
    frame = pd.DataFrame([_sewa_row(target_fields={"haemoglobin_gdl": 10.4})])
    out = adapt_sewa_metadata(frame)
    assert out.iloc[0]["target_value"] == pytest.approx(9.4)
    assert out.iloc[0]["reference_method"] == "complete_blood_count"


def test_sewa_requires_patient_identity():
    with pytest.raises(ValueError):
        adapt_sewa_metadata(pd.DataFrame([{"cbc_hgb_g_dl": 10}]))


@pytest.mark.parametrize(
    ("flash_value", "expected"),
    [(0, "ambient"), (1, "flash"), (2, "flash"), ("OFF", "ambient"),
     ("SINGLE", "flash"), ("unrecognized-mode", None)],
)
def test_sewa_flash_state_is_decoded_only_when_recognized(flash_value, expected):
    import json

    frame = pd.DataFrame([_sewa_row(camera_meta=json.dumps({
        "android.flash.mode": {"result": flash_value},
    }))])
    value = adapt_sewa_metadata(frame).iloc[0]["illumination"]
    if expected is None:
        assert pd.isna(value)
    else:
        assert value == expected


def test_sewa_survey_target_is_not_mislabeled_as_validated_reference():
    row = {
        "patient_uuid": "p2",
        "survey_haemoglobin": 11.2,
        "image_conjunctiva": {"path": "p2/conj.jpeg"},
    }
    out = adapt_sewa_metadata(pd.DataFrame([row]))
    assert out.iloc[0]["reference_type"] == "self_reported"
    assert out.iloc[0]["reference_method"] == "survey_record"
    validation = validate_target_provenance(out.iloc[0].to_dict())
    assert not validation["valid"]
    assert any("reference_type" in error for error in validation["errors"])


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
    assert out.iloc[0]["reference_type"] == "unknown"
    assert out.iloc[0]["reference_method"] == "unspecified"
    assert out.iloc[0]["target_source"] == "unverified supplied target"
    assert pd.isna(out.iloc[0]["illumination"])


def test_fingertip_preserves_explicit_reference_and_illumination():
    frame = pd.DataFrame([{
        "patient_id": "P01",
        "video_path": "clip01.mp4",
        "hemoglobin_gdl": 7.2,
        "reference_measurement_id": "cbc-P01",
        "target_source": "hospital CBC",
        "reference_method": "complete_blood_count",
        "reference_type": "laboratory",
        "illumination": "no-flash",
        "device_model": "Phone X",
        "exposure_us": 10000,
        "iso": 100,
        "white_balance_mode": "locked",
        "working_distance_mm": 50,
        "incidence_angle_deg": 0,
    }])
    out = build_fingertip_manifest(frame)
    assert out.iloc[0]["reference_type"] == "laboratory"
    assert out.iloc[0]["reference_method"] == "complete_blood_count"
    assert out.iloc[0]["illumination"] == "ambient"
    assert out.iloc[0]["device_model"] == "Phone X"
