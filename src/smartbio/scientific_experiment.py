"""Manifest-driven scientific experiment execution for SmartBio.

This module turns validated quantitative tables into a reproducible, leakage-safe
train/calibration/frozen-test experiment. It intentionally uses explicit feature
columns and existing baseline/uncertainty/statistical primitives.

This is an engineering/research execution layer, not a clinical validation tool.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd

from .provenance_audit import audit_partitions
from .quantitative_runner import run_quantitative_experiment
from .regression import make_baselines
from .uncertainty import fit_split_conformal, interval_metrics, predict_interval


@dataclass(frozen=True)
class ScientificExperimentConfig:
    """Immutable configuration for one reproducible quantitative experiment."""

    dataset: str
    dataset_version: str
    split_protocol: str
    biomarker: str
    unit: str
    feature_columns: tuple[str, ...]
    model: str = "ridge"
    calibration_id: str = "none"
    alpha: float = 0.10
    max_interval_width: float | None = None
    random_seed: int = 42

    def __post_init__(self) -> None:
        if not str(self.dataset).strip() or not str(self.dataset_version).strip():
            raise ValueError("dataset and dataset_version must be non-empty.")
        if not str(self.split_protocol).strip():
            raise ValueError("split_protocol must be non-empty.")
        if self.biomarker not in {"hemoglobin", "bilirubin"}:
            raise ValueError("biomarker must be 'hemoglobin' or 'bilirubin'.")
        if not str(self.unit).strip():
            raise ValueError("unit must be non-empty.")
        if not self.feature_columns:
            raise ValueError("At least one explicit feature column is required.")
        if len(set(self.feature_columns)) != len(self.feature_columns):
            raise ValueError("feature_columns must be unique.")
        if not 0 < self.alpha < 1:
            raise ValueError("alpha must be in (0,1).")
        if self.max_interval_width is not None and (
            not np.isfinite(self.max_interval_width) or self.max_interval_width <= 0
        ):
            raise ValueError("max_interval_width must be finite and > 0 when provided.")
        if self.random_seed < 0:
            raise ValueError("random_seed must be non-negative.")


@dataclass(frozen=True)
class ScientificExperimentReport:
    """Complete result of one frozen-test experiment."""

    manifest_hash: str
    dataset: str
    dataset_version: str
    biomarker: str
    unit: str
    model: str
    feature_columns: tuple[str, ...]
    n_train: int
    n_calibration: int
    n_test: int
    n_test_patients: int
    test_metrics: dict[str, float]
    uncertainty: dict[str, float]
    abstained_test: int

    def to_dict(self) -> dict[str, object]:
        return {
            "manifest_hash": self.manifest_hash,
            "dataset": self.dataset,
            "dataset_version": self.dataset_version,
            "biomarker": self.biomarker,
            "unit": self.unit,
            "model": self.model,
            "feature_columns": list(self.feature_columns),
            "n_train": self.n_train,
            "n_calibration": self.n_calibration,
            "n_test": self.n_test,
            "n_test_patients": self.n_test_patients,
            "test_metrics": self.test_metrics,
            "uncertainty": self.uncertainty,
            "abstained_test": self.abstained_test,
            "max_interval_width": self.max_interval_width,
        }


def _validate_features(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = set(columns) - set(frame.columns)
    if missing:
        raise ValueError(f"{name}: missing feature columns: {sorted(missing)}")
    values = frame[list(columns)].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError(f"{name}: selected features must be finite numeric values.")


def _validate_targets(frame: pd.DataFrame, *, biomarker: str, unit: str, name: str) -> None:
    required = {"patient_id", "image_id", "acquisition_id", "target_value", "biomarker", "target_unit"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{name}: missing required experiment columns: {sorted(missing)}")
    if not (frame["biomarker"].astype(str).str.strip().str.lower() == biomarker).all():
        raise ValueError(f"{name}: biomarker does not match experiment configuration.")
    if not (frame["target_unit"].astype(str).str.strip() == unit).all():
        raise ValueError(f"{name}: target unit does not match experiment configuration.")
    target = pd.to_numeric(frame["target_value"], errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(target).all():
        raise ValueError(f"{name}: target_value must be finite numeric values.")


def run_scientific_experiment(
    train: pd.DataFrame,
    calibration: pd.DataFrame,
    test: pd.DataFrame,
    *,
    config: ScientificExperimentConfig,
    n_bootstrap: int = 2000,
    n_permutations: int = 2000,
) -> ScientificExperimentReport:
    """Fit on development data, calibrate uncertainty once, and evaluate frozen test.

    No feature selection, model selection, calibration, or threshold tuning is
    performed on the frozen test partition.
    """
    partitions = {"train": train, "calibration": calibration, "test": test}
    for name, frame in partitions.items():
        if frame.empty:
            raise ValueError(f"{name} partition must not be empty.")
        _validate_targets(frame, biomarker=config.biomarker, unit=config.unit, name=name)
        _validate_features(frame, config.feature_columns, name)

    identity = audit_partitions(partitions, sample_col="image_id")
    if not identity.passed:
        raise ValueError("Patient/acquisition/sample overlap detected between partitions.")

    models = make_baselines(random_state=config.random_seed)
    if config.model not in models:
        raise ValueError(f"Unknown baseline model: {config.model}")
    model = models[config.model]

    x_train = train[list(config.feature_columns)].to_numpy(dtype=float)
    y_train = train["target_value"].to_numpy(dtype=float)
    x_cal = calibration[list(config.feature_columns)].to_numpy(dtype=float)
    y_cal = calibration["target_value"].to_numpy(dtype=float)
    x_test = test[list(config.feature_columns)].to_numpy(dtype=float)
    y_test = test["target_value"].to_numpy(dtype=float)

    model.fit(x_train, y_train)
    pred_cal = np.asarray(model.predict(x_cal), dtype=float)
    pred_test = np.asarray(model.predict(x_test), dtype=float)

    conformal = fit_split_conformal(y_cal, pred_cal, alpha=config.alpha)
    lower, upper = predict_interval(pred_test, conformal)
    uncertainty = interval_metrics(y_test, lower, upper)

    evaluation = run_quantitative_experiment(
        test,
        pred_test,
        dataset=config.dataset,
        dataset_version=config.dataset_version,
        split_protocol=config.split_protocol,
        feature_set=",".join(config.feature_columns),
        model=config.model,
        calibration_id=config.calibration_id,
        uncertainty_id=f"split-conformal-alpha-{config.alpha:g}",
        expected_biomarker=config.biomarker,
        expected_unit=config.unit,
        development_frame=train,
        calibration_frame=calibration,
        n_bootstrap=n_bootstrap,
        n_permutations=n_permutations,
        random_seed=config.random_seed,
    )
    if not evaluation.passed or evaluation.benchmark is None:
        raise ValueError(
            "Scientific benchmark gate failed: "
            + "; ".join(evaluation.preflight_errors)
        )

    if config.max_interval_width is None:
        abstained = 0
    else:
        abstained = int(np.sum((upper - lower) > config.max_interval_width))

    return ScientificExperimentReport(
        manifest_hash=evaluation.manifest_hash,
        dataset=config.dataset,
        dataset_version=config.dataset_version,
        biomarker=config.biomarker,
        unit=config.unit,
        model=config.model,
        feature_columns=tuple(config.feature_columns),
        n_train=len(train),
        n_calibration=len(calibration),
        n_test=len(test),
        n_test_patients=int(test["patient_id"].nunique()),
        test_metrics=dict(evaluation.benchmark.benchmark.metrics),
        uncertainty={
            **uncertainty,
            "conformal_alpha": float(conformal.alpha),
            "conformal_quantile": float(conformal.quantile),
            "calibration_rmse": float(conformal.calibration_rmse),
            "calibration_n": int(conformal.n_calibration),
        },
        abstained_test=abstained,
    )
