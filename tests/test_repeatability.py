import pandas as pd
import pytest

from smartbio.repeatability import analyze_repeatability


def test_repeatability_estimate():
    frame = pd.DataFrame({
        "patient_id": [1, 1, 2, 2, 3, 3],
        "device_model": ["A", "A", "A", "A", "B", "B"],
        "measurement_value": [10.0, 11.0, 20.0, 21.0, 30.0, 31.0],
    })
    report = analyze_repeatability(frame)
    assert report.n_repeated_subjects == 3
    assert report.n_devices == 2
    assert report.within_subject_sd == pytest.approx(1.0)
    assert report.repeatability_coefficient == pytest.approx(2.77)


def test_two_device_reproducibility_is_paired():
    frame = pd.DataFrame({
        "patient_id": [1, 1, 1, 1, 2, 2, 2, 2],
        "device_model": ["A", "A", "B", "B", "A", "A", "B", "B"],
        "measurement_value": [10.0, 10.2, 11.0, 11.2, 20.0, 20.1, 21.0, 21.1],
    })
    report = analyze_repeatability(frame)
    assert report.between_device_mean_bias == pytest.approx(1.0)
    assert report.between_device_loa_low is not None
    assert report.between_device_loa_high is not None


def test_missing_repeat_measurements_fail_closed():
    frame = pd.DataFrame({
        "patient_id": [1, 2, 3],
        "device_model": ["A", "A", "B"],
        "measurement_value": [10.0, 20.0, 30.0],
    })
    with pytest.raises(ValueError, match="two measurements"):
        analyze_repeatability(frame)


def test_non_numeric_measurement_fails_closed():
    frame = pd.DataFrame({
        "patient_id": [1, 1],
        "device_model": ["A", "A"],
        "measurement_value": ["bad", "10"],
    })
    with pytest.raises(ValueError, match="finite numeric"):
        analyze_repeatability(frame)
