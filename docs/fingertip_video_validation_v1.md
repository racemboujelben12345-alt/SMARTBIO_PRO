# Fingertip Video Validation Engine v1

## Purpose

Validate the physical video assets referenced by an explicit Fingertip manifest before any temporal signal extraction or Hb modelling.

The engine is deliberately fail-closed. It never infers patient identifiers, Hb values, reference measurements, or acquisition metadata from filenames or paper-level descriptions.

## Checks

For every manifest row:

- manifest-required fields are present
- referenced video file exists
- SHA-256 content hash is recorded
- duplicate file content is flagged
- OpenCV can open the video
- at least one frame is decodable
- FPS is positive
- resolution is valid
- container-reported frame count is recorded
- fully decoded frame count is recorded
- decoded/container frame-count disagreement is reported
- duration is calculated only from explicit FPS and container frame count

The overall validation passes only when all referenced files exist, all videos are readable, and no duplicate file content is present.

## CLI

```bash
PYTHONPATH=src python -m smartbio.cli fingertip-video-validate \
  --manifest data/raw/fingertip_video/manifest.csv \
  --video-root data/raw/fingertip_video \
  --output outputs/fingertip/video_validation
```

Outputs:

- `validation.json`: machine-readable aggregate report
- `records.json`: row-level validation records

## Scientific boundary

A valid video is not automatically a quantitatively valid acquisition. This engine does not establish:

- CBC provenance correctness beyond the manifest contract
- patient-level split validity
- controlled illumination
- exposure/ISO/white-balance metadata
- working distance or incidence angle
- ROI quality
- temporal PPG signal quality
- Hb model validity

Those remain downstream gates.
