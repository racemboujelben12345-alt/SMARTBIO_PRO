import numpy as np
import pytest

from smartbio.uncertainty import (
    abstention_mask,
    fit_split_conformal,
    interval_metrics,
    predict_interval,
)


def test_conformal_interval_is_frozen_and_symmetric():
    model = fit_split_conformal([10, 11, 12, 13], [9, 11, 13, 12], alpha=0.10)
    lo, hi = predict_interval([10, 12], model)
    assert np.allclose(hi - lo, 2 * model.quantile)
    assert model.fit_partition == "calibration"


def test_interval_metrics_reports_coverage_and_width():
    metrics = interval_metrics([10, 12, 14], [9, 11, 13], [11, 13, 15])
    assert metrics["coverage"] == 1.0
    assert metrics["mean_interval_width"] == 2.0
    assert metrics["n"] == 3


def test_abstention_flags_wide_intervals():
    mask = abstention_mask([10, 20], [9, 17], [11, 23], max_width=5)
    assert mask.tolist() == [False, True]


def test_invalid_alpha_is_rejected():
    with pytest.raises(ValueError):
        fit_split_conformal([1, 2], [1, 2], alpha=0)


def test_nonfinite_calibration_is_rejected():
    with pytest.raises(ValueError):
        fit_split_conformal([1, np.nan], [1, 2])
