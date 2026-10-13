import numpy as np
import pandas as pd
import pytest

from smartbio.validator import validate_canonical


def _canonical_row(target_value):
    return {
        "patient_id": "P001",
        "image_id": "P001-image-01",
        "image_path": "images/P001.jpg",
        "source_dataset": "test-fixture",
        "biomarker": "hemoglobin",
        "target_value": target_value,
        "target_unit": "g/dL",
    }


def test_canonical_validator_accepts_finite_nonnegative_target():
    result = validate_canonical(pd.DataFrame([_canonical_row(12.3)]))
    assert result["valid"], result["errors"]


@pytest.mark.parametrize("value", [np.inf, -np.inf])
def test_canonical_validator_rejects_infinite_target(value):
    result = validate_canonical(pd.DataFrame([_canonical_row(value)]))
    assert not result["valid"]
    assert any("Non-finite target_value" in error for error in result["errors"])


def test_canonical_validator_rejects_nan_target():
    result = validate_canonical(pd.DataFrame([_canonical_row(np.nan)]))
    assert not result["valid"]
    assert any("Missing/non-numeric target_value" in error for error in result["errors"])
