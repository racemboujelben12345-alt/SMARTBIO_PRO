# Dataset adapters v1

## Goal

Dataset adapters convert source-specific metadata into the SmartBio canonical
schema without weakening scientific validation.

## SEWA Rural

The SEWA adapter expands participant-level metadata into one row per available
clinical imaging modality. It uses the venous CBC Hb value as the primary
laboratory target when present and records the target provenance explicitly.

Camera2 exposure and ISO are parsed when present. White-balance state and
geometry are **not inferred**. The public dataset documentation does not expose
numeric working distance and incidence angle fields, so those remain missing
and the quantitative acquisition gate correctly fails closed until an approved
source supplies them.

The adapter does not download, redistribute, or modify gated raw data.

## Fingertip Video Dataset

The published work describes one-minute fingertip smartphone videos from 150
patients, with CBC laboratory Hb reference measurements. The adapter therefore
requires an explicit manifest containing patient identity, video path, Hb value,
and reference measurement ID.

It intentionally does not infer patient IDs or Hb labels from filenames. This is
important because video-level rows must remain linked to patient-level ground
truth without provenance shortcuts.

Reported results in the publication are literature benchmarks only; they are
not SmartBio measurements.

## Scientific status

An adapter output is an ingestion artifact, not a validated dataset. Before
quantitative benchmarking, the canonical output must pass target provenance,
acquisition, partition-identity, ROI and quality gates.
