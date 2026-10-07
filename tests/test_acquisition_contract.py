import pytest

from smartbio.acquisition import AcquisitionContract, acquisition_gate, contract_from_row


def valid_row():
    return {
        "device_model": "ResearchPhone-A",
        "exposure_us": 8000,
        "iso": 100,
        "white_balance_mode": "locked",
        "working_distance_mm": 80,
        "incidence_angle_deg": 0,
        "illumination": "flash",
        "raw_available": True,
    }


def test_valid_acquisition_contract():
    contract = contract_from_row(valid_row())
    assert isinstance(contract, AcquisitionContract)
    assert contract.iso == 100


@pytest.mark.parametrize("field", [
    "device_model", "exposure_us", "iso", "white_balance_mode",
    "working_distance_mm", "incidence_angle_deg", "illumination",
])
def test_missing_quantitative_field_fails(field):
    row = valid_row()
    row[field] = None
    result = acquisition_gate(row)
    assert not result["valid"]
    assert any(field in error for error in result["errors"])


def test_auto_white_balance_fails_closed():
    row = valid_row()
    row["white_balance_mode"] = "auto"
    result = acquisition_gate(row)
    assert not result["valid"]


def test_invalid_angle_fails():
    row = valid_row()
    row["incidence_angle_deg"] = 91
    result = acquisition_gate(row)
    assert not result["valid"]


def test_invalid_illumination_is_rejected_by_contract():
    row = valid_row()
    row["illumination"] = "unknown"
    result = acquisition_gate(row)
    assert not result["valid"]


def test_no_imputation_of_missing_metadata():
    row = valid_row()
    row["iso"] = ""
    with pytest.raises(ValueError):
        contract_from_row(row)


def test_unlocked_white_balance_fails_closed():
    row = valid_row()
    row["white_balance_mode"] = "device_default"
    result = acquisition_gate(row)
    assert not result["valid"]
    assert any("locked/manual/fixed" in error for error in result["errors"])
