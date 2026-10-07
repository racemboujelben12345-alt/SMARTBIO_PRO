import numpy as np
import pandas as pd
import pytest

from smartbio.scientific_experiment import (
    ScientificExperimentConfig,
    run_scientific_experiment,
)


def _frame(start: int, n: int) -> pd.DataFrame:
    rows = []
    for i in range(start, start + n):
        target = 10.0 + 0.12 * i
        rows.append({
            "patient_id": f"p{i}",
            "image_id": f"img{i}",
            "acquisition_id": f"acq{i}",
            "biomarker": "hemoglobin",
            "target_value": target,
            "target_unit": "g/dL",
            "target_source": "lab",
            "reference_method": "CBC",
            "reference_measurement_id": f"ref{i}",
            "reference_type": "laboratory",
            "device_model": "PhoneA",
            "exposure_us": 10000,
            "iso": 100,
            "white_balance_mode": "locked",
            "working_distance_mm": 50.0,
            "incidence_angle_deg": 0.0,
            "illumination": "flash",
            "roi_type": "conjunctiva",
            "roi_x0": 10,
            "roi_y0": 10,
            "roi_x1": 100,
            "roi_y1": 100,
            "image_width": 200,
            "image_height": 200,
            "f1": 0.20 + 0.02 * i,
            "f2": 0.40 + 0.01 * i,
            "f3": 0.30 + 0.015 * i,
        })
    return pd.DataFrame(rows)


def _config() -> ScientificExperimentConfig:
    return ScientificExperimentConfig(
        dataset="synthetic-engine-test",
        dataset_version="1",
        split_protocol="patient-level-train-calibration-frozen-test",
        biomarker="hemoglobin",
        unit="g/dL",
        feature_columns=("f1", "f2", "f3"),
        model="ridge",
        calibration_id="none",
        alpha=0.10,
        random_seed=42,
    )


def test_scientific_engine_runs_frozen_test():
    report = run_scientific_experiment(
        _frame(0, 12),
        _frame(12, 8),
        _frame(20, 10),
        config=_config(),
        n_bootstrap=200,
        n_permutations=200,
    )
    assert report.manifest_hash
    assert report.n_train == 12
    assert report.n_calibration == 8
    assert report.n_test == 10
    assert report.test_metrics["mae"] >= 0
    assert 0 <= report.uncertainty["coverage"] <= 1
    assert report.uncertainty["conformal_quantile"] >= 0


def test_engine_rejects_test_leakage():
    train = _frame(0, 12)
    calibration = _frame(12, 8)
    test = _frame(20, 10)
    test.loc[0, "patient_id"] = train.loc[0, "patient_id"]
    with pytest.raises(ValueError, match="overlap"):
        run_scientific_experiment(
            train, calibration, test,
            config=_config(),
            n_bootstrap=100,
            n_permutations=100,
        )


def test_engine_requires_explicit_features():
    config = ScientificExperimentConfig(
        dataset="synthetic-engine-test",
        dataset_version="1",
        split_protocol="patient-level",
        biomarker="hemoglobin",
        unit="g/dL",
        feature_columns=("not_a_feature",),
    )
    with pytest.raises(ValueError, match="missing feature"):
        run_scientific_experiment(
            _frame(0, 6), _frame(6, 6), _frame(12, 6),
            config=config,
            n_bootstrap=100,
            n_permutations=100,
        )


def test_engine_requires_positive_abstention_width():
    with pytest.raises(ValueError, match="max_interval_width"):
        ScientificExperimentConfig(
            dataset="synthetic-engine-test",
            dataset_version="1",
            split_protocol="patient-level",
            biomarker="hemoglobin",
            unit="g/dL",
            feature_columns=("f1",),
            max_interval_width=0,
        )


def test_engine_abstention_policy_is_explicit():
    config = _config()
    report = run_scientific_experiment(
        _frame(0, 12),
        _frame(12, 8),
        _frame(20, 10),
        config=config,
        n_bootstrap=100,
        n_permutations=100,
    )
    assert report.abstained_test == 0
