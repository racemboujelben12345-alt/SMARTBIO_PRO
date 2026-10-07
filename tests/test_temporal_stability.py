import pandas as pd
import pytest

from smartbio.temporal_stability import analyze_temporal_stability


def test_temporal_stability_reports_stable_control():
    frame = pd.DataFrame({
        "session_id": [1, 1, 2, 2, 3, 3],
        "measurement_value": [10.0, 10.2, 10.1, 10.1, 10.0, 10.2],
    })
    report = analyze_temporal_stability(frame)
    assert report.n_sessions == 3
    assert report.baseline_mean == pytest.approx(10.1)
    assert report.max_abs_relative_drift_percent == pytest.approx(0.0)
    assert report.linear_drift_per_session == pytest.approx(0.0)


def test_temporal_stability_detects_monotonic_drift():
    frame = pd.DataFrame({
        "session_id": [1, 1, 2, 2, 3, 3],
        "measurement_value": [10.0, 10.0, 11.0, 11.0, 12.0, 12.0],
    })
    report = analyze_temporal_stability(frame)
    assert report.max_abs_relative_drift_percent == pytest.approx(20.0)
    assert report.linear_drift_per_session == pytest.approx(1.0)


def test_temporal_stability_requires_two_sessions():
    frame = pd.DataFrame({
        "session_id": [1, 1],
        "measurement_value": [10.0, 10.1],
    })
    with pytest.raises(ValueError, match="two sessions"):
        analyze_temporal_stability(frame)


def test_temporal_stability_rejects_zero_baseline():
    frame = pd.DataFrame({
        "session_id": [1, 2],
        "measurement_value": [0.0, 1.0],
    })
    with pytest.raises(ValueError, match="baseline mean"):
        analyze_temporal_stability(frame)
