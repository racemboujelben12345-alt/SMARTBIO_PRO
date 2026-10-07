"""Fail-closed orchestration for reproducible quantitative SmartBio experiments.

This runner validates experiment identity and evaluation provenance before any
benchmark is produced. It intentionally does not fit a model: model training,
feature extraction and calibration remain explicit upstream steps.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from .acquisition import acquisition_gate
from .benchmark_gate import BenchmarkGateReport, run_benchmark_gate
from .provenance_audit import audit_partitions
from .statistical_rigor import ExperimentManifest
from .target_provenance import validate_target_provenance_frame


@dataclass(frozen=True)
class QuantitativeRunReport:
    """Immutable end-to-end evaluation result with fail-closed preflight."""

    passed: bool
    manifest_hash: str
    preflight_errors: tuple[str, ...]
    warnings: tuple[str, ...]
    benchmark: BenchmarkGateReport | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "manifest_hash": self.manifest_hash,
            "preflight_errors": list(self.preflight_errors),
            "warnings": list(self.warnings),
            "benchmark": None if self.benchmark is None else self.benchmark.to_dict(),
        }


def _validate_partition(
    frame: pd.DataFrame,
    name: str,
    *,
    biomarker: str,
    unit: str,
) -> list[str]:
    errors: list[str] = []
    if frame.empty:
        return [f"{name} partition must not be empty."]

    provenance = validate_target_provenance_frame(
        frame,
        expected_biomarker=biomarker,
        expected_unit=unit,
        require_unique_reference_measurements=False,
    )
    if not provenance["valid"]:
        errors.extend(f"{name}: {e}" for e in provenance["errors"])

    required_identity = {"patient_id", "image_id", "acquisition_id"}
    missing = required_identity - set(frame.columns)
    if missing:
        errors.append(f"{name}: missing identity columns: {sorted(missing)}")

    for idx, row in frame.iterrows():
        result = acquisition_gate(row.to_dict(), quantitative=True)
        if not result["valid"]:
            errors.extend(f"{name} row {idx}: {e}" for e in result["errors"])
    return errors


def run_quantitative_experiment(
    evaluation_frame: pd.DataFrame,
    predictions: Sequence[float],
    *,
    dataset: str,
    dataset_version: str,
    split_protocol: str,
    feature_set: str,
    model: str,
    calibration_id: str,
    uncertainty_id: str,
    expected_biomarker: str,
    expected_unit: str,
    development_frame: pd.DataFrame | None = None,
    calibration_frame: pd.DataFrame | None = None,
    confidence: float = 0.95,
    n_bootstrap: int = 2000,
    n_permutations: int = 2000,
    random_seed: int = 42,
) -> QuantitativeRunReport:
    """Run the frozen quantitative evaluation stage after strict preflight.

    The supplied predictions must already come from a frozen pipeline trained
    outside the evaluation partition. This function never fits, calibrates, or
    tunes a model.
    """
    if evaluation_frame.empty:
        raise ValueError("evaluation_frame must not be empty.")
    pred = np.asarray(predictions, dtype=float).reshape(-1)
    if pred.size != len(evaluation_frame):
        raise ValueError("predictions must align with evaluation_frame.")
    if not np.isfinite(pred).all():
        raise ValueError("predictions must contain only finite values.")

    manifest = ExperimentManifest(
        dataset=str(dataset).strip(),
        dataset_version=str(dataset_version).strip(),
        split_protocol=str(split_protocol).strip(),
        feature_set=str(feature_set).strip(),
        model=str(model).strip(),
        calibration_id=str(calibration_id).strip(),
        uncertainty_id=str(uncertainty_id).strip(),
        random_seed=int(random_seed),
    )

    errors = _validate_partition(
        evaluation_frame,
        "evaluation",
        biomarker=expected_biomarker,
        unit=expected_unit,
    )
    warnings: list[str] = []

    partitions = {"evaluation": evaluation_frame}
    if development_frame is not None:
        errors.extend(
            _validate_partition(
                development_frame,
                "development",
                biomarker=expected_biomarker,
                unit=expected_unit,
            )
        )
        partitions["development"] = development_frame
    if calibration_frame is not None:
        errors.extend(
            _validate_partition(
                calibration_frame,
                "calibration",
                biomarker=expected_biomarker,
                unit=expected_unit,
            )
        )
        partitions["calibration"] = calibration_frame

    if len(partitions) >= 2:
        try:
            identity = audit_partitions(partitions, sample_col="image_id")
            if not identity.passed:
                errors.append("Partition identity overlap detected.")
                errors.extend(
                    f"patient overlap {k}: {v}"
                    for k, v in identity.patient_overlaps.items()
                )
                errors.extend(
                    f"acquisition overlap {k}: {v}"
                    for k, v in identity.acquisition_overlaps.items()
                )
                errors.extend(
                    f"sample overlap {k}: {v}"
                    for k, v in identity.sample_overlaps.items()
                )
        except (ValueError, KeyError) as exc:
            errors.append(f"Partition audit failed: {exc}")

    if errors:
        return QuantitativeRunReport(
            passed=False,
            manifest_hash=manifest.manifest_hash,
            preflight_errors=tuple(errors),
            warnings=tuple(warnings),
            benchmark=None,
        )

    benchmark = run_benchmark_gate(
        evaluation_frame,
        pred,
        manifest_hash=manifest.manifest_hash,
        expected_biomarker=expected_biomarker,
        expected_unit=expected_unit,
        development_frame=development_frame,
        calibration_frame=calibration_frame,
        confidence=confidence,
        n_bootstrap=n_bootstrap,
        n_permutations=n_permutations,
        random_state=random_seed,
    )
    return QuantitativeRunReport(
        passed=benchmark.passed,
        manifest_hash=manifest.manifest_hash,
        preflight_errors=benchmark.errors,
        warnings=tuple(benchmark.warnings),
        benchmark=benchmark,
    )
