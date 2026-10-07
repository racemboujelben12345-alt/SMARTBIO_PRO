import numpy as np
import pandas as pd
import pytest

from smartbio.residual_diagnostics import analyze_residual_diagnostics


def test_residual_diagnostics_detects_range_dependent_error():
    reference = np.arange(10, dtype=float) + 5
    measurement = reference + 0.1 * reference
    frame = pd.DataFrame({
        "patient_id": range(10),
        "reference_value": reference,
        "measurement_value": measurement,
    })
    r = analyze_residual_diagnostics(frame, n_bins=4)
    assert r.n_pairs == 10
    assert r.mean_residual == pytest.approx(0.95)
    assert r.absolute_residual_reference_spearman > 0.9
    assert r.absolute_residual_reference_slope > 0
    assert len(r.stratified) == 4


def test_repeated_rows_are_averaged_before_diagnostics():
    frame = pd.DataFrame({
        "patient_id": [1, 1, 2, 2, 3, 3],
        "reference_value": [10., 10., 20., 20., 30., 30.],
        "measurement_value": [11., 9., 22., 18., 33., 27.],
    })
    r = analyze_residual_diagnostics(frame)
    assert r.n_rows == 6
    assert r.n_pairs == 3
    assert r.mean_residual == pytest.approx(0.0)
    assert r.mae == pytest.approx(0.0)


def test_relative_diagnostics_fail_on_zero_reference():
    frame = pd.DataFrame({
        "patient_id": [1, 2, 3],
        "reference_value": [0., 1., 2.],
        "measurement_value": [0., 1., 2.],
    })
    with pytest.raises(ValueError, match="non-zero"):
        analyze_residual_diagnostics(frame)


def test_too_few_subjects_fail_closed():
    frame = pd.DataFrame({
        "patient_id": [1, 2],
        "reference_value": [10., 20.],
        "measurement_value": [11., 21.],
    })
    with pytest.raises(ValueError, match="three paired"):
        analyze_residual_diagnostics(frame)


def test_zero_variance_reference_fails_closed_for_stratification():
    frame = pd.DataFrame({
        "patient_id": [1, 2, 3],
        "reference_value": [10., 10., 10.],
        "measurement_value": [11., 11., 11.],
    })
    with pytest.raises(ValueError, match="two strata"):
        analyze_residual_diagnostics(frame)
