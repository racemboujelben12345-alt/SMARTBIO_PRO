import pandas as pd
import pytest

from smartbio.provenance_audit import audit_partitions


def frame(patient, acquisition, sample):
    return pd.DataFrame({
        "patient_id": patient,
        "acquisition_id": acquisition,
        "sample_id": sample,
    })


def test_partition_audit_passes_when_identities_are_disjoint():
    out = audit_partitions({
        "train": frame(["p1", "p2"], ["a1", "a2"], ["s1", "s2"]),
        "test": frame(["p3"], ["a3"], ["s3"]),
    })
    assert out.passed


def test_partition_audit_detects_patient_and_sample_overlap():
    out = audit_partitions({
        "train": frame(["p1"], ["a1"], ["s1"]),
        "test": frame(["p1"], ["a2"], ["s1"]),
    })
    assert not out.passed
    assert "train__vs__test" in out.patient_overlaps
    assert "train__vs__test" in out.sample_overlaps
    assert "train__vs__test" not in out.acquisition_overlaps


def test_partition_audit_rejects_missing_columns():
    with pytest.raises(ValueError, match="missing"):
        audit_partitions({"train": pd.DataFrame({"patient_id": ["p1"]}), "test": pd.DataFrame()})
