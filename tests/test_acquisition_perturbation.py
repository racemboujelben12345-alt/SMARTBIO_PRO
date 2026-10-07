import pandas as pd
import pytest

from smartbio.acquisition_perturbation import analyze_acquisition_perturbation


def test_paired_perturbation_effect():
    frame = pd.DataFrame({
        "patient_id": [1, 1, 2, 2, 3, 3],
        "perturbation": ["reference", "geometry_shift"] * 3,
        "measurement_value": [10.0, 11.0, 20.0, 22.0, 30.0, 33.0],
    })
    report = analyze_acquisition_perturbation(frame)
    effect = report.effects[0]
    assert effect.condition == "geometry_shift"
    assert effect.n_pairs == 3
    assert effect.mean_bias == pytest.approx(2.0)
    assert effect.relative_bias_percent == pytest.approx(10.0)
    assert effect.sd_bias == pytest.approx(1.0)
    assert effect.loa_low == pytest.approx(0.04)
    assert effect.loa_high == pytest.approx(3.96)


def test_repeated_rows_are_averaged_within_subject_condition():
    frame = pd.DataFrame({
        "patient_id": [1, 1, 1, 1],
        "perturbation": ["reference", "reference", "illumination_shift", "illumination_shift"],
        "measurement_value": [10.0, 12.0, 13.0, 15.0],
    })
    report = analyze_acquisition_perturbation(frame)
    assert report.effects[0].mean_bias == pytest.approx(3.0)
    assert report.effects[0].n_pairs == 1
    assert report.effects[0].sd_bias is None


def test_missing_reference_fails_closed():
    frame = pd.DataFrame({
        "patient_id": [1, 2],
        "perturbation": ["geometry_shift", "geometry_shift"],
        "measurement_value": [10.0, 11.0],
    })
    with pytest.raises(ValueError, match="reference condition"):
        analyze_acquisition_perturbation(frame)


def test_unpaired_condition_is_not_treated_as_effect():
    frame = pd.DataFrame({
        "patient_id": [1, 2, 2],
        "perturbation": ["reference", "reference", "device_B"],
        "measurement_value": [10.0, 20.0, 21.0],
    })
    with pytest.raises(ValueError, match="no paired"):
        analyze_acquisition_perturbation(
            frame, factor_column="perturbation"
        )
