import numpy as np
import pytest

from smartbio.features import FeatureConfig, extract_biophysical_features


def test_feature_extraction_is_deterministic():
    rng = np.random.default_rng(42)
    roi = rng.integers(20, 240, size=(32, 24, 3), dtype=np.uint8)
    assert extract_biophysical_features(roi) == extract_biophysical_features(roi)


def test_feature_keys_and_finite_values():
    roi = np.full((10, 10, 3), 128, dtype=np.uint8)
    out = extract_biophysical_features(roi)
    assert {"linear_r_mean", "linear_g_mean", "linear_b_mean",
            "chrom_r_mean", "chrom_g_mean", "chrom_b_mean",
            "r_over_g", "r_over_b", "g_over_b"} <= set(out)
    assert np.isfinite(list(out.values())).all()


def test_relative_od_requires_reference():
    roi = np.full((8, 8, 3), 100, dtype=np.uint8)
    with pytest.raises(ValueError, match="reference"):
        extract_biophysical_features(roi, config=FeatureConfig(include_relative_od=True))


def test_relative_od_with_matched_reference():
    roi = np.full((8, 8, 3), 120, dtype=np.uint8)
    ref = np.full((8, 8, 3), 180, dtype=np.uint8)
    out = extract_biophysical_features(
        roi, reference=ref, config=FeatureConfig(include_relative_od=True)
    )
    assert out["relative_od_r_mean"] > 0


def test_invalid_shape_rejected():
    with pytest.raises(ValueError):
        extract_biophysical_features(np.zeros((10, 10)))


def test_nonfinite_input_rejected():
    roi = np.zeros((4, 4, 3), dtype=float)
    roi[0, 0, 0] = np.nan
    with pytest.raises(ValueError):
        extract_biophysical_features(roi)
