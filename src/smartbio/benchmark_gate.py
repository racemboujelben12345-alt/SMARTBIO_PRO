"""Fail-closed gate for quantitative benchmark readiness."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import numpy as np
import pandas as pd

from .acquisition import acquisition_gate
from .benchmark import build_benchmark_report
from .provenance_audit import audit_partitions
from .target_provenance import validate_target_provenance_frame

@dataclass(frozen=True)
class BenchmarkGateReport:
    passed: bool
    n_rows: int
    n_patients: int
    target_provenance_valid: bool
    acquisition_valid: bool
    partition_identity_valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    benchmark: object | None = None

    def to_dict(self):
        payload = asdict(self)
        payload["benchmark"] = self.benchmark.to_dict() if self.benchmark is not None else None
        return payload

def _check_acquisition(frame):
    errors=[]; warnings=[]
    for idx,row in frame.iterrows():
        result=acquisition_gate(row.to_dict(), quantitative=True)
        if not result["valid"]: errors.extend([f"row {idx}: {e}" for e in result["errors"]])
        warnings.extend([f"row {idx}: {w}" for w in result["warnings"]])
    return errors,warnings

def assert_benchmark_ready(
    evaluation_frame: pd.DataFrame,
    y_pred,
    *,
    manifest_hash: str,
    expected_biomarker: str,
    expected_unit: str,
    development_frame: pd.DataFrame | None = None,
    calibration_frame: pd.DataFrame | None = None,
    confidence: float = .95,
    n_bootstrap: int = 2000,
    n_permutations: int = 2000,
    random_state: int = 42,
):
    """Validate provenance/acquisition/partition identity, then benchmark frozen predictions."""
    if evaluation_frame.empty: raise ValueError("evaluation_frame must not be empty.")
    if len(y_pred) != len(evaluation_frame): raise ValueError("y_pred must align with evaluation_frame.")
    errors=[]; warnings=[]
    tp=validate_target_provenance_frame(
        evaluation_frame, expected_biomarker=expected_biomarker,
        expected_unit=expected_unit, require_unique_reference_measurements=False)
    if not tp["valid"]: errors.extend(tp["errors"])
    warnings.extend(tp["warnings"])

    ae,aw=_check_acquisition(evaluation_frame); errors.extend(ae); warnings.extend(aw)

    partitions={"evaluation":evaluation_frame}
    if development_frame is not None: partitions["development"]=development_frame
    if calibration_frame is not None: partitions["calibration"]=calibration_frame]
    partition_ok=True
    if len(partitions)>=2:
        try:
            pa=audit_partitions(partitions, sample_col="image_id")
            partition_ok=pa.passed
            if not partition_ok:
                errors.append("Partition identity overlap detected.")
                errors.extend([f"patient overlap {k}: {v}" for k,v in pa.patient_overlaps.items()])
                errors.extend([f"acquisition overlap {k}: {v}" for k,v in pa.acquisition_overlaps.items()])
                errors.extend([f"sample overlap {k}: {v}" for k,v in pa.sample_overlaps.items()])
        except (ValueError, KeyError) as exc:
            partition_ok=False; errors.append(f"Partition audit failed: {exc}")

    if errors:
        return BenchmarkGateReport(False,len(evaluation_frame),int(evaluation_frame["patient_id"].nunique()),
            bool(tp["valid"]),not ae,bool(partition_ok),tuple(errors),tuple(warnings),None)

    report=build_benchmark_report(
        evaluation_frame["target_value"].to_numpy(), np.asarray(y_pred,float),
        evaluation_frame["patient_id"].to_numpy(), manifest_hash=manifest_hash,
        confidence=confidence,n_bootstrap=n_bootstrap,n_permutations=n_permutations,
        random_state=random_state)
    return BenchmarkGateReport(True,len(evaluation_frame),int(evaluation_frame["patient_id"].nunique()),
        True,True,True,tuple(),tuple(warnings),report)
