import numpy as np
import pandas as pd
import pytest

from smartbio.regression import (
    evaluate_predictions,
    fit_and_evaluate,
    make_baselines,
    regression_metrics,
)


def test_regression_metrics_perfect_prediction():
    m = regression_metrics([1, 2, 3], [1, 2, 3])
    assert m["mae"] == 0.0
    assert m["rmse"] == 0.0
    assert m["r2"] == 1.0
    assert m["pearson_r"] == 1.0
    assert m["bland_altman_bias"] == 0.0


def test_regression_metrics_reject_nonfinite():
    with pytest.raises(ValueError):
        regression_metrics([1, np.nan], [1, 2])


def test_baselines_are_defined():
    models = make_baselines()
    assert set(models) == {"linear", "ridge", "lasso", "random_forest", "gradient_boosting"}


def test_fit_and_evaluate_returns_all_baselines():
    rng = np.random.default_rng(42)
    X = rng.normal(size=(60, 4))
    y = 2.0 * X[:, 0] - 0.5 * X[:, 1] + rng.normal(0, 0.1, size=60)
    result = fit_and_evaluate(X[:45], y[:45], X[45:], y[45:])
    assert len(result) == 5
    assert set(result["model"]) == {"linear", "ridge", "lasso", "random_forest", "gradient_boosting"}
    assert (result["n"] == 15).all()
    assert result["mae"].notna().all()


def test_evaluate_predictions_contains_bland_altman_limits():
    result = evaluate_predictions([10, 11, 12, 13], [11, 10, 13, 12], model="demo")
    assert result.n == 4
    assert result.bland_altman_lower < result.bland_altman_upper
