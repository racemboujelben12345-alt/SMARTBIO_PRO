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
import numpy as np


@pytest.mark.parametrize(
    "y_true,y_pred,groups",
    [
        ([], [], []),
        ([1, 2], [1, 2], ["A"]),
        ([1, float("nan")], [1, 2], ["A", "B"]),
        ([1, 2], [1, float("inf")], ["A", "B"]),
    ],
)
def test_grouped_regression_rejects_invalid_inputs(
    y_true, y_pred, groups
):
    with pytest.raises(ValueError):
        grouped_regression(y_true, y_pred, groups)


@pytest.mark.parametrize(
    "prediction,uncertainty,z",
    [
        ([10], [float("nan")], 1.96),
        ([10], [float("inf")], 1.96),
        ([10], [1], -1),
        ([10], [1], float("inf")),
    ],
)
def test_uncertainty_interval_rejects_invalid_values(
    prediction, uncertainty, z
):
    with pytest.raises(ValueError):
        uncertainty_interval(prediction, uncertainty, z=z)


def test_uncertainty_interval_rejects_empty_inputs():
    with pytest.raises(ValueError):
        uncertainty_interval([], [])