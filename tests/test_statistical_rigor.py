import numpy as np
import pandas as pd
import pytest

from smartbio.statistical_rigor import (
    ExperimentManifest,
    leakage_audit,
    permutation_test,
)


def test_permutation_test_is_reproducible_and_bounded():
    y = [10, 12, 14, 16, 18]
    p = [11, 11, 13, 17, 17]
    a = permutation_test(y, p, n_permutations=300, random_state=9)
    b = permutation_test(y, p, n_permutations=300, random_state=9)
    assert a == b
    assert 0 < a.p_value <= 1
    assert a.observed >= 0


def test_manifest_hash_is_deterministic():
    kwargs = dict(
        dataset="demo",
        dataset_version="v1",
        split_protocol="patient_holdout",
        feature_set="rgb_od",
        model="ridge",
        calibration_id="cal-v1",
        uncertainty_id="conformal-v1",
        random_seed=42,
    )
    a = ExperimentManifest.create(**kwargs)
    b = ExperimentManifest.create(**kwargs)
    assert a == b
    assert len(a.manifest_hash) == 64


def test_leakage_audit_reports_duplicates_and_cross_device_patients():
    frame = pd.DataFrame(
        {
            "patient_id": ["p1", "p1", "p2", "p3"],
            "device_model": ["A", "B", "A", "A"],
            "acquisition_id": ["a1", "a1", "a2", "a3"],
        }
    )
    out = leakage_audit(frame)
    assert out["n_rows"] == 4
    assert out["n_unique_patients"] == 3
    assert out["duplicate_patient_rows"] == 1
    assert out["duplicate_acquisition_rows"] == 1
    assert out["patients_seen_on_multiple_devices"] == 1


def test_invalid_metric_is_rejected():
    with pytest.raises(ValueError, match="metric"):
        permutation_test([1, 2], [1, 2], metric="r2")
