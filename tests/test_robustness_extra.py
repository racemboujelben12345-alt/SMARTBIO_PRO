import pytest
from smartbio.robustness import (
    grouped_regression,
    uncertainty_interval,
)


def test_grouped_regression_basic():
    y_true = [10, 20, 30, 40]
    y_pred = [11, 19, 31, 39]
    groups = ["A", "A", "B", "B"]

    result = grouped_regression(
        y_true,
        y_pred,
        groups,
    )

    assert result["A"]["n"] == 2
    assert result["B"]["n"] == 2


def test_grouped_regression_invalid_lengths():
    with pytest.raises(ValueError):
        grouped_regression(
            [1, 2],
            [1, 2],
            ["A"],
        )


def test_uncertainty_interval():
    lower, upper = uncertainty_interval(
        [10],
        [1],
    )

    assert lower[0] < 10
    assert upper[0] > 10


def test_uncertainty_interval_negative_uncertainty():
    with pytest.raises(ValueError):
        uncertainty_interval(
            [10],
            [-1],
        )