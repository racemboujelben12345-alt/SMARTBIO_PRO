from smartbio.evaluation import (
    regression_metrics,
    bland_altman,
    coverage_under_uncertainty,
)

def test_regression_metrics_perfect_prediction():
    y_true = [1, 2, 3, 4]
    y_pred = [1, 2, 3, 4]

    m = regression_metrics(y_true, y_pred)

    assert m["n"] == 4
    assert m["mae"] == 0.0
    assert m["rmse"] == 0.0
    assert m["bias"] == 0.0


def test_bland_altman_perfect_prediction():
    y_true = [1, 2, 3]
    y_pred = [1, 2, 3]

    result = bland_altman(y_true, y_pred)

    assert result["bias"] == 0.0
    assert result["loa_lower"] == 0.0
    assert result["loa_upper"] == 0.0


def test_coverage_under_uncertainty():
    y_true = [10, 20, 30]
    pred = [11, 19, 29]
    uncertainty = [1, 1, 1]

    result = coverage_under_uncertainty(
        y_true,
        pred,
        uncertainty,
        z=1.96,
    )

    assert result["coverage"] == 1.0
    assert result["n"] == 3