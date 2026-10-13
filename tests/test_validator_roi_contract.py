import pandas as pd
import pytest

from smartbio.validator import validate_canonical


def _row(roi_type):
    return {
        "patient_id": "P001",
        "image_id": "P001-image-01",
        "image_path": "images/P001.jpg",
        "source_dataset": "test-fixture",
        "biomarker": "hemoglobin",
        "target_value": 12.3,
        "target_unit": "g/dL",
        "roi_type": roi_type,
        "roi_x0": 10,
        "roi_y0": 10,
        "roi_x1": 50,
        "roi_y1": 50,
        "image_width": 100,
        "image_height": 100,
    }


def test_exploratory_tongue_roi_is_preserved_for_ingestion_with_warning():
    result = validate_canonical(pd.DataFrame([_row("tongue")]))
    assert result["valid"], result["errors"]
    assert any("not quantitatively approved" in warning for warning in result["warnings"])


def test_exploratory_tongue_roi_is_rejected_for_quantitative_use():
    result = validate_canonical(
        pd.DataFrame([_row("tongue")]),
        require_roi_provenance=True,
    )
    assert not result["valid"]
    assert any("not quantitatively approved" in error for error in result["errors"])


def test_unknown_roi_label_is_rejected_even_during_ingestion():
    result = validate_canonical(pd.DataFrame([_row("unknown-body-part")]))
    assert not result["valid"]
    assert any("Invalid ROI labels" in error for error in result["errors"])


def test_approved_conjunctiva_roi_passes_strict_roi_gate():
    result = validate_canonical(
        pd.DataFrame([_row("conjunctiva")]),
        require_roi_provenance=True,
    )
    assert result["valid"], result["errors"]


@pytest.mark.parametrize(
    ("field", "value"),
    [("roi_x0", 10.5), ("image_width", 100.5), ("image_height", float("inf"))],
)
def test_fractional_or_nonfinite_roi_geometry_is_not_truncated(field, value):
    row = _row("conjunctiva")
    row[field] = value
    result = validate_canonical(
        pd.DataFrame([row]),
        require_roi_provenance=True,
    )
    assert not result["valid"]
    assert any("must be finite integers" in error for error in result["errors"])
