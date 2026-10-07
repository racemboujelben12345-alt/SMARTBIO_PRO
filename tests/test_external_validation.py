from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from smartbio.external_validation import evaluate_frozen_external, validate_external_partition


def _frame(dataset: str, patients: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "patient_id": patients,
            "biomarker": ["hemoglobin"] * len(patients),
            "target_unit": ["g/dL"] * len(patients),
            "dataset": [dataset] * len(patients),
        }
    )


def test_external_contract_accepts_independent_matching_data():
    development = _frame("development", ["p1", "p2"])
    external = _frame("external_a", ["p3", "p4"])
    contract = validate_external_partition(
        external,
        development=development,
        biomarker="hemoglobin",
        target_unit="g/dL",
        external_dataset="external_a",
    )
    assert contract.n_records == 2
    assert contract.n_patients == 2


def test_external_contract_rejects_patient_overlap():
    development = _frame("development", ["p1", "p2"])
    external = _frame("external_a", ["p2", "p3"])
    with pytest.raises(ValueError, match="patient overlap"):
        validate_external_partition(
            external,
            development=development,
            biomarker="hemoglobin",
            target_unit="g/dL",
            external_dataset="external_a",
        )


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("biomarker", "bilirubin", "biomarker"),
        ("target_unit", "mmol/L", "target unit"),
        ("dataset", "wrong_dataset", "dataset identity"),
    ],
)
def test_external_contract_rejects_metadata_mismatch(column, value, message):
    development = _frame("development", ["p1"])
    external = _frame("external_a", ["p2"])
    external.loc[0, column] = value
    with pytest.raises(ValueError, match=message):
        validate_external_partition(
            external,
            development=development,
            biomarker="hemoglobin",
            target_unit="g/dL",
            external_dataset="external_a",
        )


def test_frozen_external_scoring_returns_regression_and_interval_metrics():
    out = evaluate_frozen_external(
        [10.0, 12.0, 14.0],
        [11.0, 11.0, 13.0],
        model="ridge",
        lower=[9.0, 10.0, 12.0],
        upper=[13.0, 12.0, 14.0],
    )
    assert out["model"] == "ridge"
    assert np.isclose(out["mae"], 1.0)
    assert np.isclose(out["rmse"], np.sqrt(2 / 3))
    assert np.isclose(out["coverage"], 2 / 3)
    assert out["n"] == 3
