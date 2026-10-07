"""Tests for uncertainty calibration diagnostics."""

import pytest

from smartbio.uncertainty_calibration import analyze_interval_calibration


def test_interval_calibration_reports_nominal_and_observed_coverage():
    report = analyze_interval_calibration(
        [1.0, 2.0, 3.0, 4.0],
        [0.0, 1.5, 3.5, 3.0],
        [2.0, 2.5, 4.0, 4.5],
        alpha=0.25,
    )
    assert report.nominal_coverage == pytest.approx(0.75)
    assert report.observed_coverage == pytest.approx(0.75)
    assert report.coverage_error == pytest.approx(0.0)
    assert report.mean_interval_width == pytest.approx(1.25)


def test_subject_bootstrap_is_deterministic():
    args = dict(
        y_true=[1.0, 1.1, 2.0, 2.1, 3.0, 3.1],
        lower=[0.0] * 6,
        upper=[1.05, 1.05, 2.05, 2.05, 3.05, 3.05],
        alpha=0.10,
        subject_ids=["a", "a", "b", "b", "c", "c"],
        n_bootstrap=2000,
        seed=42,
    )
    first = analyze_interval_calibration(**args)
    second = analyze_interval_calibration(**args)
    assert first.n_subjects == 3
    assert first.coverage_ci_low == pytest.approx(second.coverage_ci_low)
    assert first.coverage_ci_high == pytest.approx(second.coverage_ci_high)


def test_invalid_bounds_and_alpha_fail_closed():
    with pytest.raises(ValueError, match="lower bounds"):
        analyze_interval_calibration([1], [2], [1], alpha=0.1)
    with pytest.raises(ValueError, match="alpha"):
        analyze_interval_calibration([1], [0], [2], alpha=1.0)


def test_bootstrap_requires_production_minimum_and_multiple_subjects():
    with pytest.raises(ValueError, match=">= 2000"):
        analyze_interval_calibration(
            [1, 2], [0, 1], [2, 3], alpha=0.1,
            subject_ids=["a", "b"], n_bootstrap=100,
        )
    with pytest.raises(ValueError, match="At least two subjects"):
        analyze_interval_calibration(
            [1, 2], [0, 0], [3, 3], alpha=0.1,
            subject_ids=["a", "a"], n_bootstrap=2000,
        )
