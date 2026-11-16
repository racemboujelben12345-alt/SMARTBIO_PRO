
import numpy as np
import pytest
from PIL import Image

from smartbio.quality.gate import QualityGateConfig, assess_image


def test_assess_image_returns_expected_schema(tmp_path):
    path = tmp_path / "sample.jpg"
    Image.fromarray(
        np.tile(np.arange(100, dtype=np.uint8), (100, 1))
    ).save(path)

    result = assess_image(path)

    expected = {
        "mean_intensity",
        "dynamic_range",
        "saturation_ratio",
        "sharpness",
        "illum_cv",
        "image_width",
        "image_height",
        "flag_count",
        "flag_insufficient_dimensions",
        "quality_status",
    }

    assert expected.issubset(result)
    assert result["image_width"] == 100
    assert result["image_height"] == 100
    assert result["quality_status"] in {"PASS", "REVIEW", "FAIL"}


def test_thresholds_are_deterministic(tmp_path):
    path = tmp_path / "sample.jpg"
    Image.fromarray(np.zeros((100, 100), dtype=np.uint8)).save(path)

    config = QualityGateConfig(
        low_sharpness=1e9,
        high_illum_cv=0.0,
        high_saturation=0.0,
        low_dynamic_range=1e9,
    )

    result = assess_image(path, config)

    assert result["flag_count"] == 4
    assert result["quality_status"] == "FAIL"


@pytest.mark.parametrize(
    "parameter,value",
    [
        ("low_sharpness", -1),
        ("high_illum_cv", -0.1),
        ("high_saturation", -0.1),
        ("low_dynamic_range", -1),
        ("low_sharpness", np.nan),
        ("high_illum_cv", np.inf),
        ("high_saturation", np.inf),
        ("low_dynamic_range", np.nan),
        ("high_saturation", 1.1),
    ],
)
def test_invalid_thresholds_are_rejected(parameter, value):
    with pytest.raises(ValueError):
        QualityGateConfig(**{parameter: value})


@pytest.mark.parametrize(
    "shape",
    [
        (5, 5),
        (8, 20),
        (20, 8),
    ],
)
def test_small_images_are_handled(tmp_path, shape):
    path = tmp_path / "small.png"
    Image.fromarray(
        np.full(shape, 120, dtype=np.uint8)
    ).save(path)

    result = assess_image(path)

    assert result["image_width"] == shape[1]
    assert result["image_height"] == shape[0]
    assert result["flag_insufficient_dimensions"] is True
    assert result["quality_status"] == "FAIL"
