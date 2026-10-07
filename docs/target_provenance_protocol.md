# Target Provenance Protocol v1

## Purpose

A numeric Hb or bilirubin value is not automatically a trustworthy reference
target. Before quantitative benchmarking, SmartBio requires explicit provenance
for the measurement used as ground truth.

This protocol prevents silent target mapping, unit substitution, or use of an
untraceable reference value.

## Required provenance

Every benchmark-ready target record must identify:

- biomarker
- target unit
- target source
- reference method
- reference measurement ID
- reference type

reference_type is restricted to:

- laboratory
- validated_reference

An optional target_time_delta_min records the elapsed time between optical
acquisition and the reference measurement when that information is available.
The system never imputes this value.

## Fail-closed rules

The provenance gate rejects:

1. missing reference method;
2. missing reference measurement identity;
3. biomarker/unit mismatch against the experiment;
4. unsupported reference type;
5. invalid acquisition-to-reference time delta;
6. duplicated reference measurement IDs when independent target records are
   expected.

The gate does not decide whether a laboratory method is clinically superior.
That is a scientific study-design decision and must be documented separately.

## Hb and bilirubin

The contract deliberately does not hard-code a particular analyzer or assay.
For Hb, the project can record the actual laboratory reference method supplied by
the dataset. For bilirubin, the project can record the actual TSB/reference
method supplied by the dataset.

This avoids inventing biological ground-truth metadata that is absent from a
source dataset.

## Relationship to leakage control

Target provenance is complementary to patient, acquisition, sample and device
leakage audits. A reference measurement ID is an identity/provenance field; it
does not replace patient-level independence checks.

## Benchmark rule

A dataset may contain numeric targets while remaining not benchmark-ready until
the provenance contract passes.

Passing the contract does not establish analytical accuracy, clinical validity,
or regulatory validity.
