import numpy as np
import pytest

from smartbio.optical_pipeline import (
    OpticalPreprocessConfig,
    masked_channel_summary,
    preprocess_roi,
)


def rgb(value=128, shape=(10, 10, 3)):
    return np.full(shape, value, dtype=np.uint8)


def test_preprocess_linearizes_without_changing_shape():
    result = preprocess_roi(rgb())
    assert result.linear_rgb.shape == (10, 10, 3)
    assert result.valid_mask.shape == (10, 10)
    assert result.quality_status == "PASS"
    assert result.valid_fraction == 1.0


def test_saturated_pixels_are_masked_not_silently_used():
    image = rgb()
    image[0, 0] = [255, 100, 100]
    result = preprocess_roi(image)
    assert result.valid_fraction == pytest.approx(0.99)
    assert result.saturation_fraction == pytest.approx(0.01)
    summary = masked_channel_summary(result)
    assert summary["valid_fraction"] == pytest.approx(0.99)


def test_quality_fails_when_too_many_pixels_are_clipped():
    image = rgb()
    image[:5] = 255
    result = preprocess_roi(
        image,
        config=OpticalPreprocessConfig(min_valid_fraction=0.60),
    )
    assert result.quality_status == "FAIL"


def test_calibration_requires_explicit_provenance():
    with pytest.raises(ValueError, match="calibration_id"):
        preprocess_roi(rgb(), channel_gains=[1, 1, 1])


def test_channel_gains_are_applied_after_linearization():
    result = preprocess_roi(
        rgb(128),
        channel_gains=[2.0, 1.0, 0.5],
        calibration_id="cal-v1",
    )
    assert result.calibration_id == "cal-v1"
    assert result.linear_rgb[0, 0, 0] == pytest.approx(
        result.linear_rgb[0, 0, 1] * 2.0
    )
    assert result.linear_rgb[0, 0, 2] == pytest.approx(
        result.linear_rgb[0, 0, 1] * 0.5
    )


def test_invalid_rgb_range_is_rejected():
    image = rgb().astype(float)
    image[0, 0, 0] = 300
    with pytest.raises(ValueError, match=r"\[0, 255\]"):
        preprocess_roi(image)
