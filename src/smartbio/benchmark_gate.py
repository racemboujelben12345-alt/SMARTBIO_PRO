"""Fail-closed gate before quantitative benchmark reporting."""
from dataclasses import dataclass
from typing import Optional
import numpy as np
import pandas as pd
from .acquisition import acquisition_gate
from .benchmark import build_benchmark_report
from .provenance_audit import audit_partitions
from .target_provenance import validate_target_provenance_frame

@dataclass(frozen=True)
class BenchmarkGateReport:
    passed: bool
    errors: tuple[str,...]
    warnings: tuple[str,...]
    target_provenance_valid: bool
    acquisition_valid: bool
    partition_identity_valid: bool
    benchmark: Optional[object] = None

    def to_dict(self):
        return {
            "passed":self.passed,"errors":list(self.errors),"warnings":list(self.warnings),
            "target_provenance_valid":self.target_provenance_valid,
            "acquisition_valid":self.acquisition_valid,
            "partition_identity_valid":self.partition_identity_valid,
            "benchmark":None if self.benchmark is None else self.benchmark.to_dict(),
        }

def run_benchmark_gate(evaluation_frame,y_pred,*,manifest_hash,expected_biomarker,expected_unit,
                       development_frame=None,calibration_frame=None,confidence=.95,
                       n_bootstrap=2000,n_permutations=2000,random_state=42):
    if evaluation_frame.empty: raise ValueError("evaluation_frame must not be empty")
    if len(y_pred)!=len(evaluation_frame): raise ValueError("y_pred must align with evaluation_frame")
    errors=[]; warnings=[]
    tp=validate_target_provenance_frame(evaluation_frame,expected_biomarker=expected_biomarker,
        expected_unit=expected_unit,require_unique_reference_measurements=False)
    if not tp["valid"]: errors.extend(tp["errors"])
    warnings.extend(tp["warnings"])
    acq_errors=[]
    for idx,row in evaluation_frame.iterrows():
        a=acquisition_gate(row.to_dict(),quantitative=True)
        if not a["valid"]: acq_errors.extend([f"row {idx}: {e}" for e in a["errors"]])
        warnings.extend([f"row {idx}: {w}" for w in a["warnings"]])
    errors.extend(acq_errors)
    partition_ok=True
    partitions={"evaluation":evaluation_frame}
    if development_frame is not None: partitions["development"]=development_frame
    if calibration_frame is not None: partitions["calibration"]=calibration_frame
    if len(partitions)>1:
        try:
            audit=audit_partitions(partitions,sample_col="image_id")
            partition_ok=audit.passed
            if not partition_ok:
                errors.append("Partition identity overlap detected.")
                errors.extend(f"patient overlap {k}: {v}" for k,v in audit.patient_overlaps.items())
                errors.extend(f"acquisition overlap {k}: {v}" for k,v in audit.acquisition_overlaps.items())
                errors.extend(f"sample overlap {k}: {v}" for k,v in audit.sample_overlaps.items())
        except (ValueError,KeyError) as exc:
            partition_ok=False; errors.append(f"Partition audit failed: {exc}")
    if errors:
        return BenchmarkGateReport(False,tuple(errors),tuple(warnings),bool(tp["valid"]),not acq_errors,partition_ok)
    report=build_benchmark_report(evaluation_frame["target_value"].to_numpy(),np.asarray(y_pred,float),
        evaluation_frame["patient_id"].to_numpy(),manifest_hash=manifest_hash,confidence=confidence,
        n_bootstrap=n_bootstrap,n_permutations=n_permutations,random_state=random_state)
    return BenchmarkGateReport(True,tuple(),tuple(warnings),True,True,True,report)
