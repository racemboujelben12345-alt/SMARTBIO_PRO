import numpy as np
from PIL import Image
from smartbio.quality.gate import QualityGateConfig, assess_image

def test_assess_image_returns_expected_schema(tmp_path):
    path = tmp_path / "sample.jpg"
    Image.fromarray(np.tile(np.arange(100, dtype=np.uint8), (100, 1))).save(path)
    result = assess_image(path)
    assert {"mean_intensity", "dynamic_range", "saturation_ratio", "sharpness", "illum_cv", "flag_count", "quality_status"}.issubset(result)
    assert result["quality_status"] in {"PASS", "REVIEW", "FAIL"}

def test_thresholds_are_deterministic(tmp_path):
    path = tmp_path / "sample.jpg"
    Image.fromarray(np.zeros((100, 100), dtype=np.uint8)).save(path)
    config = QualityGateConfig(low_sharpness=1e9, high_illum_cv=0.0, high_saturation=0.0, low_dynamic_range=1e9)
    result = assess_image(path, config)
    assert result["flag_count"] == 4
    assert result["quality_status"] == "FAIL"
