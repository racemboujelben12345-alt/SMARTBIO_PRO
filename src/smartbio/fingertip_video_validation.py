"""Validation engine for the Fingertip Video Dataset.

This layer validates physical video assets and their explicit manifest mapping.
It does not infer patient IDs, Hb values, or acquisition metadata.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
from typing import Any

import cv2
import pandas as pd


REQUIRED_MANIFEST_FIELDS = {
    "patient_id",
    "video_path",
    "hemoglobin_gdl",
    "reference_measurement_id",
}


@dataclass(frozen=True)
class VideoValidationRecord:
    manifest_index: int
    patient_id: str
    video_path: str
    exists: bool
    readable: bool
    fps: float | None
    duration_s: float | None
    reported_frame_count: int | None
    decoded_frame_count: int | None
    width: int | None
    height: int | None
    sha256: str | None
    duplicate_of: int | None
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FingertipVideoValidationReport:
    rows: int
    unique_patients: int
    files_found: int
    files_missing: int
    readable_videos: int
    unreadable_videos: int
    duplicate_files: int
    records: list[VideoValidationRecord]

    @property
    def passed(self) -> bool:
        return (
            self.rows > 0
            and self.files_missing == 0
            and self.unreadable_videos == 0
            and self.duplicate_files == 0
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["passed"] = self.passed
        return payload


def _sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_video_path(video_path: str, video_root: Path | None) -> Path:
    path = Path(video_path)
    if path.is_absolute() or video_root is None:
        return path
    return video_root / path


def _inspect_video(path: Path) -> tuple[bool, float | None, float | None, int | None, int | None, int | None, list[str]]:
    capture = cv2.VideoCapture(str(path))
    errors: list[str] = []
    try:
        if not capture.isOpened():
            return False, None, None, None, None, None, ["OpenCV could not open video."]

        fps_raw = float(capture.get(cv2.CAP_PROP_FPS))
        reported_raw = float(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        width_raw = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height_raw = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fps = fps_raw if fps_raw > 0 else None
        reported = int(round(reported_raw)) if reported_raw > 0 else None
        width = width_raw if width_raw > 0 else None
        height = height_raw if height_raw > 0 else None
        duration = (reported / fps) if reported is not None and fps is not None else None

        decoded = 0
        while True:
            ok, _ = capture.read()
            if not ok:
                break
            decoded += 1

        if decoded == 0:
            errors.append("Video opened but no decodable frames were found.")
        if reported is not None and decoded != reported:
            errors.append(
                f"Decoded frame count ({decoded}) differs from container metadata ({reported})."
            )
        if fps is None:
            errors.append("FPS metadata is missing or non-positive.")
        if width is None or height is None:
            errors.append("Video resolution metadata is missing or invalid.")

        readable = decoded > 0 and not any(
            "missing" in error.lower() or "could not open" in error.lower()
            for error in errors
        )
        return readable, fps, duration, reported, decoded, width, height, errors
    finally:
        capture.release()


def validate_fingertip_videos(
    manifest: pd.DataFrame,
    video_root: str | Path | None = None,
) -> FingertipVideoValidationReport:
    if manifest.empty:
        return FingertipVideoValidationReport(0, 0, 0, 0, 0, 0, 0, [])

    missing = REQUIRED_MANIFEST_FIELDS - set(manifest.columns)
    if missing:
        raise ValueError(f"Missing manifest fields: {sorted(missing)}")

    root = Path(video_root) if video_root is not None else None
    records: list[VideoValidationRecord] = []
    hashes: dict[str, int] = {}
    files_found = 0
    files_missing = 0
    readable_videos = 0
    unreadable_videos = 0
    duplicate_files = 0

    for index, row in manifest.iterrows():
        patient_id = str(row["patient_id"]).strip()
        raw_path = str(row["video_path"]).strip()
        path = _resolve_video_path(raw_path, root)
        errors: list[str] = []

        if not raw_path:
            files_missing += 1
            records.append(VideoValidationRecord(
                int(index), patient_id, raw_path, False, False,
                None, None, None, None, None, None, None, None,
                ["video_path is empty."]
            ))
            continue

        if not path.is_file():
            files_missing += 1
            records.append(VideoValidationRecord(
                int(index), patient_id, raw_path, False, False,
                None, None, None, None, None, None, None, None,
                [f"Video file not found: {path}"]
            ))
            continue

        files_found += 1
        file_hash = _sha256(path)
        duplicate_of = hashes.get(file_hash)
        if duplicate_of is not None:
            duplicate_files += 1
            errors.append(f"Duplicate file content matches manifest row {duplicate_of}.")
        else:
            hashes[file_hash] = int(index)

        try:
            (
                readable, fps, duration, reported, decoded, width, height, inspect_errors
            ) = _inspect_video(path)
        except Exception as exc:
            readable = False
            fps = duration = None
            reported = decoded = width = height = None
            inspect_errors = [f"Video inspection failed: {type(exc).__name__}: {exc}"]

        errors.extend(inspect_errors)
        if readable:
            readable_videos += 1
        else:
            unreadable_videos += 1

        records.append(VideoValidationRecord(
            int(index), patient_id, raw_path, True, readable,
            fps, duration, reported, decoded, width, height,
            file_hash, duplicate_of, errors
        ))

    return FingertipVideoValidationReport(
        rows=len(manifest),
        unique_patients=int(manifest["patient_id"].astype("string").nunique(dropna=True)),
        files_found=files_found,
        files_missing=files_missing,
        readable_videos=readable_videos,
        unreadable_videos=unreadable_videos,
        duplicate_files=duplicate_files,
        records=records,
    )
