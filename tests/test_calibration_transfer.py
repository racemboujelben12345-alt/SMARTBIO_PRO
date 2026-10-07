import pandas as pd
import pytest

from smartbio.calibration_transfer import analyze_calibration_transfer


def test_transfer_reports_subgroup_error_profiles():
    frame = pd.DataFrame({
        "patient_id": [1, 2, 3, 4, 5, 6],
        "reference_value": [10., 12., 14., 10., 12., 14.],
        "calibrated_value": [10., 12., 14., 11., 13., 15.],
        "device_model": ["A", "A", "A", "B", "B", "B"],
    })
    report = analyze_calibration_transfer(frame)
    assert report.n_pairs == 6
    assert report.overall_mae == pytest.approx(0.5)
    assert report.subgroups[0]["mean_bias"] == pytest.approx(0.0)
    assert report.subgroups[1]["mean_bias"] == pytest.approx(1.0)


def test_repeated_rows_are_averaged():
    frame = pd.DataFrame({
        "patient_id": [1, 1, 2, 3],
        "reference_value": [10., 10., 12., 14.],
        "calibrated_value": [11., 9., 13., 15.],
        "device_model": ["A", "A", "A", "A"],
    })
    report = analyze_calibration_transfer(frame)
    assert report.n_pairs == 3
    assert report.subgroups[0]["mean_bias"] == pytest.approx(0.6666666667)


def test_subject_cannot_change_subgroup():
    frame = pd.DataFrame({
        "patient_id": [1, 1, 2],
        "reference_value": [10., 10., 12.],
        "calibrated_value": [10., 11., 12.],
        "device_model": ["A", "B", "A"],
    })
    with pytest.raises(ValueError, match="exactly one subgroup"):
        analyze_calibration_transfer(frame)


def test_small_subgroup_fails_closed():
    frame = pd.DataFrame({
        "patient_id": [1, 2, 3],
        "reference_value": [10., 12., 14.],
        "calibrated_value": [10., 13., 15.],
        "device_model": ["A", "A", "B"],
    })
    with pytest.raises(ValueError, match="at least two"):
        analyze_calibration_transfer(frame)
