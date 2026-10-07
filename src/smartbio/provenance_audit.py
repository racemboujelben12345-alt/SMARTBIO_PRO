"""Partition-level provenance and leakage auditing.

The audit is deliberately fail-closed: development/evaluation partitions are
checked for patient, acquisition, and sample identity overlap before results
are considered valid.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
import pandas as pd


@dataclass(frozen=True)
class PartitionAudit:
    partitions: tuple[str, ...]
    patient_overlaps: dict[str, tuple[str, ...]]
    acquisition_overlaps: dict[str, tuple[str, ...]]
    sample_overlaps: dict[str, tuple[str, ...]]

    @property
    def passed(self) -> bool:
        return not (
            self.patient_overlaps
            or self.acquisition_overlaps
            or self.sample_overlaps
        )


def audit_partitions(
    partitions: Mapping[str, pd.DataFrame],
    *,
    patient_col: str = "patient_id",
    acquisition_col: str = "acquisition_id",
    sample_col: str = "sample_id",
) -> PartitionAudit:
    if len(partitions) < 2:
        raise ValueError("at least two partitions are required.")

    names = tuple(partitions.keys())
    sets: dict[str, dict[str, set]] = {}
    for name, frame in partitions.items():
        if frame.empty:
            raise ValueError(f"partition '{name}' is empty.")
        missing = {patient_col, acquisition_col, sample_col} - set(frame.columns)
        if missing:
            raise ValueError(f"partition '{name}' missing: {sorted(missing)}")
        sets[name] = {
            "patient": set(frame[patient_col].dropna()),
            "acquisition": set(frame[acquisition_col].dropna()),
            "sample": set(frame[sample_col].dropna()),
        }

    patient_overlaps: dict[str, tuple[str, ...]] = {}
    acquisition_overlaps: dict[str, tuple[str, ...]] = {}
    sample_overlaps: dict[str, tuple[str, ...]] = {}

    for i, left in enumerate(names):
        for right in names[i + 1:]:
            key = f"{left}__vs__{right}"
            po = sets[left]["patient"] & sets[right]["patient"]
            ao = sets[left]["acquisition"] & sets[right]["acquisition"]
            so = sets[left]["sample"] & sets[right]["sample"]
            if po:
                patient_overlaps[key] = tuple(sorted(map(str, po)))
            if ao:
                acquisition_overlaps[key] = tuple(sorted(map(str, ao)))
            if so:
                sample_overlaps[key] = tuple(sorted(map(str, so)))

    return PartitionAudit(
        partitions=names,
        patient_overlaps=patient_overlaps,
        acquisition_overlaps=acquisition_overlaps,
        sample_overlaps=sample_overlaps,
    )
