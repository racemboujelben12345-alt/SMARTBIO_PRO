from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from smartbio.scientific_validation import (
    assert_patient_disjoint,
    bootstrap_metric_ci,
    subgroup_metrics,
)


def test_bootstrap_ci_is_reproducible_and_contains_point_estimate():
    y = [10.0, 12.0, 14.0, 16.0, 18.0]
    p = [11.0, 11.0, 13.0, 17.0, 17.0]
    first = bootstrap_metric_ci(y, p, metric="mae", n_bootstrap=300, random_state=7)
    second = bootstrap_metric_ci(y, p, metric="mae", n_bootstrap=300, random_state=7)

    assert first == second
    assert first.lower <= first.estimate <= first.upper
    assert first.n == 5
    assert first.n_bootstrap == 300


def test_bootstrap_rejects_invalid_confidence():
    with pytest.raises(ValueError, match="confidence"):
        bootstrap_metric_ci([1, 2], [1, 2], confidence=1.0)


def test_patient_partitions_must_be_disjoint():
    a = pd.DataFrame({"patient_id": ["p1", "p2"]})
    b = pd.DataFrame({"patient_id": ["p3"]})
    c = pd.DataFrame({"patient_id": ["p2", "p4"]})

    assert_patient_disjoint(a, b)

    with pytest.raises(ValueError, match="patient overlap"):
        assert_patient_disjoint(a, c)


def test_subgroup_metrics_respects_minimum_sample_size():
    frame = pd.DataFrame(
        {
            "target": [10.0, 12.0, 14.0, 20.0],
            "prediction": [11.0, 11.0, 13.0, 21.0],
            "device": ["A", "A", "A", "B"],
        }
    )
    out = subgroup_metrics(
        frame,
        target_col="target",
        prediction_col="prediction",
        group_col="device",
        min_n=2,
    )

    assert list(out["group"]) == ["A"]
    assert int(out.loc[0, "n"]) == 3
    assert np.isclose(out.loc[0, "mae"], 1.0)
