"""Tests for the Fingertip Video Validation Engine v1."""

from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import pytest

from smartbio.fingertip_video_validation import validate_fingertip_videos


def _write_video(path: Path, frames: int = 4) -> None:
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        10.0,
        (32, 24),
    )
    if not writer.isOpened():
        pytest.skip("OpenCV MP4 writer is unavailable in this environment.")
    try:
        for i in range(frames):
            frame = np.full((24, 32, 3), i * 20, dtype=np.uint8)
            writer.write(frame)
    finally:
        writer.release()


def _manifest(path: str) -> pd.DataFrame:
    return pd.DataFrame([{
        "patient_id": "P001",
        "video_path": path,
        "hemoglobin_gdl": 11.2,
        "reference_measurement_id": "CBC-P001",
    }])


def test_valid_video_is_readable(tmp_path):
    video = tmp_path / "P001.mp4"
    _write_video(video)

    report = validate_fingertip_videos(_manifest(video.name), video_root=tmp_path)

    assert report.passed
    assert report.files_found == 1
    assert report.readable_videos == 1
    record = report.records[0]
    assert record.decoded_frame_count == 4
    assert record.fps == pytest.approx(10.0)
    assert record.width == 32
    assert record.height == 24
    assert record.sha256


def test_missing_video_fails_closed(tmp_path):
    report = validate_fingertip_videos(_manifest("missing.mp4"), video_root=tmp_path)

    assert not report.passed
    assert report.files_missing == 1
    assert report.records[0].exists is False


def test_duplicate_video_content_is_flagged(tmp_path):
    video_a = tmp_path / "P001.mp4"
    video_b = tmp_path / "P002.mp4"
    _write_video(video_a)
    video_b.write_bytes(video_a.read_bytes())

    frame = pd.concat([
        _manifest(video_a.name),
        _manifest(video_b.name).assign(
            patient_id="P002",
            reference_measurement_id="CBC-P002",
        ),
    ], ignore_index=True)

    report = validate_fingertip_videos(frame, video_root=tmp_path)

    assert not report.passed
    assert report.duplicate_files == 1
    assert report.records[1].duplicate_of == 0


def test_missing_manifest_field_is_rejected():
    frame = _manifest("P001.mp4").drop(columns=["reference_measurement_id"])

    with pytest.raises(ValueError, match="reference_measurement_id"):
        validate_fingertip_videos(frame)
