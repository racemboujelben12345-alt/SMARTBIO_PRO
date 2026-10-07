import numpy as np
import pandas as pd
import pytest

from smartbio.device_robustness import (
    device_robustness_report,
    relative_mae_change,
    summarize_device_distribution,
    unseen_device_split,
)


def test_unseen_device_split_excludes_cross_device_patients():
    df = pd.DataFrame({
        "patient_id": ["p1", "p1", "p2", "p3"],
        "device_model": ["A", "C", "A", "B"],
    })
    result = unseen_device_split(df, "C")
    assert set(result.test["patient_id"]) == {"p1"}
    assert set(result.train["patient_id"]) == {"p2", "p3"}
    assert result.excluded_patients == 1


def test_unseen_device_split_requires_columns():
    with pytest.raises(ValueError):
        unseen_device_split(pd.DataFrame({"patient_id": ["p1"]}), "A")


def test_device_distribution():
    df = pd.DataFrame({"device_model": ["A", "A", "B"]})
    out = summarize_device_distribution(df)
    assert out["n"].tolist() == [2, 1]
    assert np.isclose(out["fraction"].sum(), 1.0)


def test_relative_mae_change():
    assert np.isclose(relative_mae_change(2.0, 3.0), 0.5)
    assert np.isinf(relative_mae_change(0.0, 1.0))


def test_device_report_compares_models():
    source = pd.DataFrame({"model": ["ridge"], "mae": [1.0], "rmse": [1.2], "r2": [0.8]})
    held = pd.DataFrame({"model": ["ridge"], "mae": [1.5], "rmse": [1.7], "r2": [0.6]})
    out = device_robustness_report(source, held)
    assert np.isclose(out.loc[0, "mae_relative_change"], 0.5)
    assert np.isclose(out.loc[0, "rmse_relative_change"], (1.7 - 1.2) / 1.2)
