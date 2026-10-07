import pandas as pd
import pytest

from smartbio.target_provenance import (
    TargetProvenanceContract,
    contract_from_row,
    validate_target_provenance,
    validate_target_provenance_frame,
)


def valid_row():
    return {
        "biomarker": "hemoglobin",
        "target_unit": "g/dL",
        "target_source": "SEWA Rural clinical record",
        "reference_method": "laboratory hemoglobin measurement",
        "reference_measurement_id": "LAB-001",
        "reference_type": "laboratory",
        "target_time_delta_min": 12.0,
    }


def test_valid_contract_is_immutable():
    contract = TargetProvenanceContract(**valid_row())
    assert contract.biomarker == "hemoglobin"
    with pytest.raises(Exception):
        contract.reference_method = "other"


def test_missing_reference_method_fails_closed():
    row = valid_row()
    row["reference_method"] = ""
    result = validate_target_provenance(row)
    assert not result["valid"]
    assert any("reference_method" in error for error in result["errors"])


def test_biomarker_and_unit_mismatch_are_rejected():
    result = validate_target_provenance(
        valid_row(),
        expected_biomarker="bilirubin",
        expected_unit="mg/dL",
    )
    assert not result["valid"]
    assert len(result["errors"]) == 2


def test_invalid_reference_type_is_rejected():
    row = valid_row()
    row["reference_type"] = "unknown"
    result = validate_target_provenance(row)
    assert not result["valid"]


def test_negative_time_delta_is_rejected():
    row = valid_row()
    row["target_time_delta_min"] = -1
    result = validate_target_provenance(row)
    assert not result["valid"]


def test_frame_requires_all_provenance_columns():
    frame = pd.DataFrame([valid_row()]).drop(columns=["reference_method"])
    result = validate_target_provenance_frame(frame)
    assert not result["valid"]


def test_frame_rejects_duplicate_reference_measurements():
    first = valid_row()
    second = valid_row()
    second["target_source"] = "same source"
    result = validate_target_provenance_frame(pd.DataFrame([first, second]))
    assert not result["valid"]
    assert any("duplicated" in error for error in result["errors"])


def test_contract_from_row_rejects_missing_metadata():
    row = valid_row()
    del row["reference_measurement_id"]
    with pytest.raises(ValueError, match="Target provenance contract failed"):
        contract_from_row(row)
