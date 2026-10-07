import pandas as pd
import pytest

from smartbio.subgroup_robustness import analyze_subgroup_robustness


def test_device_subgroups_report_separate_error_profiles():
    frame = pd.DataFrame({
        "patient_id": [1, 2, 3, 4, 5, 6],
        "reference_value": [10., 12., 14., 10., 12., 14.],
        "measurement_value": [10., 12., 14., 11., 13., 15.],
        "device_model": ["A", "A", "A", "B", "B", "B"],
    })
    report = analyze_subgroup_robustness(frame)
    assert report.n_pairs == 6
    assert report.overall_mae == pytest.approx(0.5)
    assert len(report.subgroups) == 2
    assert report.subgroups[0]["mean_bias"] == pytest.approx(0.0)
    assert report.subgroups[1]["mean_bias"] == pytest.approx(1.0)


def test_repeated_rows_are_averaged():
    frame = pd.DataFrame({
        "patient_id": [1, 1, 2, 3, 4],
        "reference_value": [10., 10., 12., 14., 16.],
        "measurement_value": [11., 9., 13., 15., 17.],
        "device_model": ["A", "A", "A", "A", "A"],
    })
    report = analyze_subgroup_robustness(frame)
    assert report.n_pairs == 4
    assert report.subgroups[0]["mean_bias"] == pytest.approx(0.5)


def test_subject_cannot_change_subgroup():
    frame = pd.DataFrame({
        "patient_id": [1, 1, 2],
        "reference_value": [10., 10., 12.],
        "measurement_value": [10., 11., 12.],
        "device_model": ["A", "B", "A"],
    })
    with pytest.raises(ValueError, match="multiple subgroups"):
        analyze_subgroup_robustness(frame)


def test_small_subgroup_fails_closed():
    frame = pd.DataFrame({
        "patient_id": [1, 2, 3],
        "reference_value": [10., 12., 14.],
        "measurement_value": [10., 13., 15.],
        "device_model": ["A", "A", "B"],
    })
    with pytest.raises(ValueError, match="at least two"):
        analyze_subgroup_robustness(frame)
