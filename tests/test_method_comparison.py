import numpy as np
import pandas as pd
import pytest

from smartbio.method_comparison import analyze_method_comparison


def test_method_comparison_recovers_near_identity_relationship():
    x = np.arange(10, dtype=float) + 10
    y = 1.05 * x + 0.4
    frame = pd.DataFrame({"patient_id": range(10), "reference_value": x, "measurement_value": y})
    r = analyze_method_comparison(frame, n_bootstrap=300, seed=42)
    assert r.n_pairs == 10
    assert r.deming_slope == pytest.approx(1.05, abs=0.02)
    assert r.deming_intercept == pytest.approx(0.4, abs=0.5)
    assert r.passing_bablok_slope == pytest.approx(1.05, abs=0.02)


def test_repeated_rows_are_averaged_before_comparison():
    frame = pd.DataFrame({
        "patient_id": [1, 1, 2, 2, 3, 3],
        "reference_value": [10., 12., 20., 20., 30., 30.],
        "measurement_value": [11., 13., 21., 19., 31., 29.],
    })
    r = analyze_method_comparison(frame, n_bootstrap=300)
    assert r.n_rows == 6
    assert r.n_pairs == 3
    assert r.mean_reference == pytest.approx(20.3333333333)


def test_invalid_variance_ratio_fails_closed():
    frame = pd.DataFrame({
        "patient_id": [1, 2, 3],
        "reference_value": [10., 20., 30.],
        "measurement_value": [11., 21., 31.],
    })
    with pytest.raises(ValueError, match="variance_ratio"):
        analyze_method_comparison(frame, variance_ratio=0)


def test_too_few_subjects_fail_closed():
    frame = pd.DataFrame({
        "patient_id": [1, 2],
        "reference_value": [10., 20.],
        "measurement_value": [11., 21.],
    })
    with pytest.raises(ValueError, match="three paired"):
        analyze_method_comparison(frame, n_bootstrap=300)


def test_constant_reference_fails_closed():
    frame = pd.DataFrame({
        "patient_id": [1, 2, 3],
        "reference_value": [10., 10., 10.],
        "measurement_value": [11., 12., 13.],
    })
    with pytest.raises(ValueError, match="non-zero variance"):
        analyze_method_comparison(frame, n_bootstrap=300)


def test_bootstrap_confidence_intervals_are_reproducible():
    frame = pd.DataFrame({
        "patient_id": range(1, 9),
        "reference_value": np.arange(8, dtype=float) + 10,
        "measurement_value": 1.02 * (np.arange(8, dtype=float) + 10) + 0.7,
    })
    a = analyze_method_comparison(frame, n_bootstrap=300, seed=123)
    b = analyze_method_comparison(frame, n_bootstrap=300, seed=123)
    assert a.deming_slope_ci_low == pytest.approx(b.deming_slope_ci_low)
    assert a.passing_bablok_intercept_ci_high == pytest.approx(b.passing_bablok_intercept_ci_high)
