# Partition Provenance & Leakage Audit v1

Every quantitative benchmark must establish that evaluation identities are
independent from development identities.

## Required identities

Each partition should carry patient_id, acquisition_id, and sample_id.

## Fail-closed checks

For every pair of partitions, the audit checks:

1. patient overlap
2. acquisition overlap
3. sample overlap

Any overlap is reported explicitly. A benchmark should not be interpreted as
valid until the cause is investigated and the partitioning decision is
documented.

## Why all three levels

Patient-level separation prevents repeated observations from crossing
partitions. Acquisition-level separation catches accidental reuse of a single
capture. Sample-level separation catches duplicated or copied records even when
patient metadata are incomplete.

This audit complements, rather than replaces, the device-held-out protocol and
external-validation contract.

## Provenance principle

Dataset transformations should preserve identity metadata. If an operation
removes or changes an identity field, that transformation must be documented
and the corresponding leakage audit repeated.
