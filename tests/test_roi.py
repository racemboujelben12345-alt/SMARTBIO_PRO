import numpy as np
import pytest

from smartbio.roi import ROIBox, crop, validate_roi_geometry, validate_roi_type


def test_roi_type_is_target_specific():
    validate_roi_type("hemoglobin", "conjunctiva")
    validate_roi_type("bilirubin", "forehead")
    with pytest.raises(ValueError):
        validate_roi_type("hemoglobin", "forehead")


def test_roi_geometry_accepts_valid_box():
    box = ROIBox(10, 10, 50, 50)
    validate_roi_geometry(
        box,
        image_width=100,
        image_height=100,
        min_width=8,
        min_height=8,
        min_area_fraction=0.01,
        max_area_fraction=0.95,
    )


def test_roi_geometry_rejects_tiny_box():
    with pytest.raises(ValueError, match="minimum"):
        validate_roi_geometry(
            ROIBox(1, 1, 5, 5),
            image_width=100,
            image_height=100,
        )


def test_roi_geometry_rejects_dominant_box():
    with pytest.raises(ValueError, match="area fraction"):
        validate_roi_geometry(
            ROIBox(0, 0, 100, 100),
            image_width=100,
            image_height=100,
            max_area_fraction=0.95,
        )


def test_crop_preserves_shape_and_values():
    image = np.arange(100 * 100 * 3, dtype=np.uint16).reshape(100, 100, 3)
    result = crop(image, ROIBox(10, 20, 30, 40))
    assert result.shape == (20, 20, 3)
    assert np.array_equal(result, image[20:40, 10:30])
