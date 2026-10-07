# SEWA Local Ingestion v1

## Purpose

Provide a reproducible entry point for an authorized local export of the
SEWA Rural Anemia Dataset. The command operates only on files already present
on disk.

It does not:

- download or bypass the gated dataset;
- infer patient identity from filenames;
- invent working distance or incidence angle;
- infer a white-balance lock state;
- treat missing acquisition metadata as valid quantitative capture;
- redistribute source images or metadata.

## Input

Supported local metadata formats:

- Parquet (.parquet) — expected for the official participant table;
- CSV (.csv);
- JSON/JSONL (.json, .jsonl).

The input must contain the fields required by the SEWA adapter, including
patient_uuid and the modality image/camera metadata fields used by the adapter.

## Command

After obtaining authorized access and placing the export locally:

    PYTHONPATH=src python -m smartbio.cli ingest-sewa \
      --metadata data/raw/sewa/participants.parquet \
      --output data/processed/sewa/canonical.csv

The command writes canonical provenance-preserving metadata. It does not claim
that the resulting data are benchmark-ready.

## Next gates

Run the normal SmartBio validation sequence after ingestion:

1. canonical/provenance validation;
2. acquisition contract;
3. identity/leakage audit;
4. patient-level split;
5. explicit ROI;
6. quality audit;
7. biophysical feature extraction;
8. frozen calibration/model/uncertainty;
9. quantitative benchmark gate.

Because the published SEWA schema does not provide the full quantitative
geometry state required by the acquisition contract, the current adapter is
expected to remain NOT quantitatively benchmark-ready until approved geometry
and acquisition metadata are available.
