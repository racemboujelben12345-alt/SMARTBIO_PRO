import numpy as np
import pytest

from smartbio.calibration import (
    AffineCalibrationModel,
    apply_affine_model,
    fit_affine,
    fit_affine_model,
    linearize_srgb,
    relative_od,
)


def test_linearize_srgb_is_bounded_and_monotonic():
    x = np.array([[0.0, 64.0, 128.0], [192.0, 255.0, 32.0]])
    y = linearize_srgb(x)
    assert y.shape == x.shape
    assert np.all((y >= 0.0) & (y <= 1.0))
    assert np.all(np.diff(y[0]) > 0)


def test_affine_fit_requires_train_or_calibration_partition():
    observed = np.array([
        [0.10, 0.20, 0.30],
        [0.20, 0.30, 0.40],
        [0.30, 0.40, 0.50],
    ])
    with pytest.raises(ValueError, match="test/external"):
        fit_affine(observed, observed, fit_partition="test")


def test_affine_model_records_provenance_and_fit_error():
    observed = np.array([
        [0.10, 0.20, 0.30],
        [0.20, 0.30, 0.40],
        [0.30, 0.40, 0.50],
        [0.40, 0.50, 0.60],
    ])
    reference = observed * 1.1 + 0.01
    model = fit_affine_model(observed, reference, fit_partition="calibration")

    assert isinstance(model, AffineCalibrationModel)
    assert model.n_samples == 4
    assert model.n_features == 3
    assert model.fit_partition == "calibration"
    assert model.fit_rmse < 1e-10


def test_apply_affine_model_does_not_refit():
    observed = np.array([
        [0.10, 0.20, 0.30],
        [0.20, 0.30, 0.40],
        [0.30, 0.40, 0.50],
        [0.40, 0.50, 0.60],
    ])
    reference = observed * 1.1 + 0.01
    model = fit_affine_model(observed, reference, fit_partition="train")
    new_values = np.array([[0.15, 0.25, 0.35]])
    predicted = apply_affine_model(new_values, model)

    assert predicted.shape == (1, 3)
    assert np.allclose(predicted, new_values * 1.1 + 0.01, atol=1e-10)


def test_affine_fit_requires_three_paired_samples():
    with pytest.raises(ValueError, match="At least 3"):
        fit_affine(np.ones((2, 3)), np.ones((2, 3)))


def test_affine_fit_rejects_nonfinite_values():
    observed = np.array([
        [0.10, 0.20, 0.30],
        [0.20, np.nan, 0.40],
        [0.30, 0.40, 0.50],
    ])
    with pytest.raises(ValueError, match="finite"):
        fit_affine(observed, observed)


def test_relative_od_requires_positive_reference():
    sample = np.full((2, 2, 3), 100.0)
    reference = np.zeros((2, 2, 3))
    with pytest.raises(ValueError):
        relative_od(sample, reference)
