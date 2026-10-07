import pandas as pd
import pytest

from smartbio.quantitative_runner import run_quantitative_experiment


def frame():
    return pd.DataFrame({
        "patient_id": ["p1","p2","p3"],
        "image_id": ["i1","i2","i3"],
        "biomarker": ["hemoglobin"] * 3,
        "target_value": [10.0,11.0,12.0],
        "target_unit": ["g/dL"] * 3,
        "target_source": ["lab"] * 3,
        "reference_method": ["CBC"] * 3,
        "reference_measurement_id": ["r1","r2","r3"],
        "reference_type": ["laboratory"] * 3,
        "device_model": ["PhoneA"] * 3,
        "exposure_us": [10000] * 3,
        "iso": [100] * 3,
        "white_balance_mode": ["locked"] * 3,
        "working_distance_mm": [50.0] * 3,
        "incidence_angle_deg": [0.0] * 3,
        "illumination": ["flash"] * 3,
        "acquisition_id": ["a1","a2","a3"],
    })


def kwargs():
    return dict(
        dataset="synthetic-test",
        dataset_version="1",
        split_protocol="patient-level",
        feature_set="rgb",
        model="ridge",
        calibration_id="cal-v1",
        uncertainty_id="conformal-v1",
        expected_biomarker="hemoglobin",
        expected_unit="g/dL",
        n_bootstrap=200,
        n_permutations=200,
    )


def test_runner_passes_frozen_evaluation():
    result = run_quantitative_experiment(frame(), [10.2,10.8,12.1], **kwargs())
    assert result.passed
    assert result.benchmark is not None
    assert result.manifest_hash


def test_runner_fails_missing_acquisition_metadata():
    bad = frame().drop(columns=["iso"])
    result = run_quantitative_experiment(bad, [10.2,10.8,12.1], **kwargs())
    assert not result.passed
    assert any("acquisition" in e.lower() for e in result.preflight_errors)


def test_runner_fails_partition_overlap():
    f = frame()
    result = run_quantitative_experiment(
        f, [10.2,10.8,12.1], development_frame=f.copy(), **kwargs()
    )
    assert not result.passed
    assert any("overlap" in e.lower() for e in result.preflight_errors)


def test_runner_rejects_prediction_mismatch():
    with pytest.raises(ValueError):
        run_quantitative_experiment(frame(), [10.2,10.8], **kwargs())
