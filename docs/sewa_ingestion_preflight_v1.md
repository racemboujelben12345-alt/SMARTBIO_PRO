# SEWA Ingestion Preflight v1

The preflight is an **inventory and fail-closed readiness check**, not a
benchmark validator.

It reports:

- row and patient counts;
- available image modalities;
- CBC versus survey Hb availability;
- camera-metadata presence by modality;
- quantitative acquisition fields that still require explicit validation.

It intentionally does not infer working distance, incidence angle, white-balance
lock state, illumination state, or any other missing physical metadata.

A preflight report with `passed=false` is expected until the authorized export
contains sufficient information for the downstream acquisition contract.
